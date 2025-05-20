import cv2
import os
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from pathlib import Path
import threading
import platform
import subprocess

# === Main Processing Function ===
def speed_up_video(input_path, output_path, speed_factor, progress_callback=None):
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise RuntimeError("Failed to open video.")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    input_fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    if speed_factor <= 0.0:
        raise ValueError("Speed factor must be > 0")

    output_fps = input_fps * speed_factor
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, output_fps, (width, height))

    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if speed_factor >= 1.0:
            if int(frame_count % speed_factor) == 0:
                out.write(frame)
        else:
            out.write(frame)

        frame_count += 1
        if progress_callback:
            percent = int((frame_count / total_frames) * 100)
            progress_callback(min(percent, 100))

    cap.release()
    out.release()

    if progress_callback:
        progress_callback(100)

# === Utility ===
def format_duration(seconds):
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:02}:{m:02}:{s:02}"

def estimate_file_size(width, height, fps, duration_seconds, bitrate_mbps=2.5):
    return round(bitrate_mbps * duration_seconds / 8, 2)  # MB

def open_folder_containing(file_path):
    folder = os.path.dirname(file_path)
    try:
        if platform.system() == "Windows":
            os.startfile(folder)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", folder])
        else:
            subprocess.Popen(["xdg-open", folder])
    except Exception as e:
        print(f"⚠️ Could not open folder: {e}")

# === GUI Setup ===
class VideoSpeedGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🎬 Video Speed Changer")
        self.root.geometry("480x380")
        self.video_path = None
        self.root.configure(bg="#eaf2f8")

        # === Widgets ===
        tk.Label(root, text="🎞️ Select a video file:", font=('Helvetica', 12, "bold"),
                 bg="#eaf2f8", fg="#1f4e79").pack(pady=5)
        tk.Button(root, text="Browse", command=self.browse_file,
                  bg="#4CAF50", fg="white", font=("Helvetica", 10, "bold")).pack(pady=2)

        self.file_label = tk.Label(root, text="No file selected",
                                   font=('Helvetica', 9, 'italic'), bg="#eaf2f8", fg="#555")
        self.file_label.pack(pady=(0, 10))

        tk.Label(root, text="⏩ Choose speed multiplier:", font=('Helvetica', 12, "bold"),
                 bg="#eaf2f8", fg="#1f4e79").pack(pady=10)
        self.speed_var = tk.StringVar(value="2.0")
        self.speed_menu = ttk.Combobox(
            root,
            textvariable=self.speed_var,
            values=['0.25', '0.5', '0.75', '1.0', '2.0', '3.0', '5.0', '10.0'],
            state="readonly"
        )
        self.speed_menu.pack()

        self.progress_bar = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
        self.progress_bar.pack(pady=15)
        self.progress_label = tk.Label(root, text="Conversion: 0%", font=('Helvetica', 10), bg="#eaf2f8")
        self.progress_label.pack()

        tk.Button(root, text="🚀 Convert and Save", command=self.start_conversion,
                  bg="#1e88e5", fg="white", font=("Helvetica", 10, "bold")).pack(pady=20)

    def browse_file(self):
        self.video_path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv")]
        )
        if self.video_path:
            filename = Path(self.video_path).name
            duration_sec, duration_str = self.get_video_duration(self.video_path)
            size_estimate = self.get_estimated_size(self.video_path, duration_sec)
            self.file_label.config(text=f"📁 {filename} — Duration: {duration_str} — Estimated: ~{size_estimate} MB")
            messagebox.showinfo("✅ File Selected", f"Selected: {filename}")

    def get_video_duration(self, path):
        try:
            cap = cv2.VideoCapture(path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            cap.release()
            if fps > 0 and total_frames > 0:
                duration = total_frames / fps
                return duration, format_duration(duration)
        except:
            pass
        return 0, "Unknown"

    def get_estimated_size(self, path, duration_sec):
        try:
            cap = cv2.VideoCapture(path)
            width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            cap.release()
            if width > 0 and height > 0 and duration_sec > 0:
                return estimate_file_size(width, height, 30, duration_sec)
        except:
            pass
        return "?"

    def update_progress(self, value):
        self.progress_bar["value"] = value
        self.progress_label.config(text=f"Conversion: {value}%")
        self.root.update_idletasks()

    def start_conversion(self):
        if not self.video_path:
            messagebox.showerror("❌ Error", "Please select a video file first.")
            return

        try:
            speed = float(self.speed_var.get())
            if speed <= 0.0:
                raise ValueError("Speed must be greater than 0.")
        except Exception:
            messagebox.showerror("❌ Error", "Invalid speed multiplier.")
            return

        default_name = Path(self.video_path).stem + f"_x{speed}.mp4"
        output_path = filedialog.asksaveasfilename(
            defaultextension=".mp4",
            initialfile=default_name,
            filetypes=[("MP4 Video", "*.mp4")]
        )
        if not output_path:
            return

        self.progress_bar["value"] = 0
        self.progress_label.config(text="Conversion: 0%")
        self.speed_menu.config(state="disabled")

        def safe_update(val):
            self.root.after(0, lambda: self.update_progress(val))

        def run_conversion():
            try:
                speed_up_video(self.video_path, output_path, speed, progress_callback=safe_update)
                self.root.after(0, lambda: messagebox.showinfo("✅ Success", f"Saved: {output_path}"))
                self.root.after(500, lambda: open_folder_containing(output_path))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("❌ Error", str(e)))
            finally:
                self.root.after(0, lambda: self.speed_menu.config(state="readonly"))
                self.root.after(0, lambda: self.update_progress(0))

        threading.Thread(target=run_conversion, daemon=True).start()

# === Run the App ===
if __name__ == "__main__":
    root = tk.Tk()

    # 🔹 ICON SETUP
    icon_path = os.path.join(os.path.dirname(__file__), "assets", "app_icon.png")
    if platform.system() != "Windows":
        if os.path.exists(icon_path):
            root.iconphoto(True, tk.PhotoImage(file=icon_path))
    else:
        ico_path = os.path.join(os.path.dirname(__file__), "assets", "app_icon.ico")
        if os.path.exists(ico_path):
            root.iconbitmap(ico_path)

    app = VideoSpeedGUI(root)
    root.mainloop()

