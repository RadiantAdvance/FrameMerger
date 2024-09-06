import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import cv2
import os
import json
import subprocess
import threading

class VideoConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image to Video Converter")
        
        # Set the app icon for the window and taskbar
        self.set_window_icon('icon.png')

        self.preset_file = 'presets.json'
        self.framerate_preset_file = 'framerate_presets.json'
        self.codec_presets = self.load_presets(self.preset_file)
        self.framerate_presets = self.load_presets(self.framerate_preset_file)

        self.image_folder_var = tk.StringVar()
        self.output_folder_var = tk.StringVar()
        self.output_filename_var = tk.StringVar()
        self.framerate_var = tk.StringVar()
        self.codec_var = tk.StringVar()
        self.progress_var = tk.DoubleVar(value=0)

        self.create_styles()
        self.check_ffmpeg_installation()
        self.create_widgets()
        self.update_codec_dropdown()
        self.update_framerate_dropdown()

    def set_window_icon(self, icon_path):
        """Sets the window and taskbar icon."""
        icon = tk.PhotoImage(file=icon_path)
        self.root.iconphoto(True, icon)


    def create_styles(self):
        style = ttk.Style()
        style.configure('TButton', bootstyle='primary')

    def load_presets(self, file_path):
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                return json.load(file)
        return {}

    def save_presets(self, presets, file_path):
        with open(file_path, 'w') as file:
            json.dump(presets, file)

    def check_ffmpeg_installation(self):
        try:
            subprocess.run(["ffmpeg", "-version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except (subprocess.CalledProcessError, FileNotFoundError):
            messagebox.showwarning("Warning", "FFmpeg is not installed. Please install FFmpeg to use this application.")

    def convert_images_to_video(self, image_folder, output_file, frame_rate=30, ffmpeg_command=""):
        images = self.get_sorted_images(image_folder)
        if not images:
            messagebox.showerror("Error", "No images found in the selected folder.")
            self.progress_var.set(0)
            return

        temp_video = 'temp_video.mp4'
        self.create_temp_video(image_folder, images, frame_rate, temp_video)

        ffmpeg_command = ffmpeg_command.replace("input", temp_video).replace("output", output_file)
        subprocess.run(ffmpeg_command, shell=True)
        os.remove(temp_video)

        self.progress_var.set(100)
        messagebox.showinfo("Success", "Video created successfully!")

    def get_sorted_images(self, folder):
        images = [img for img in os.listdir(folder) if img.endswith((".png", ".jpg", ".jpeg"))]
        images.sort()
        return images

    def create_temp_video(self, folder, images, frame_rate, output_file):
        frame = cv2.imread(os.path.join(folder, images[0]))
        height, width, layers = frame.shape
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video = cv2.VideoWriter(output_file, fourcc, frame_rate, (width, height))

        total_images = len(images)
        for index, image in enumerate(images):
            img_path = os.path.join(folder, image)
            frame = cv2.imread(img_path)
            video.write(frame)
            self.progress_var.set((index + 1) / total_images * 50)

        video.release()

    def select_image_file(self):
        file_selected = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg")])
        if file_selected:
            folder_selected = os.path.dirname(file_selected)
            self.image_folder_var.set(folder_selected)

    def select_output_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.output_folder_var.set(folder_selected)

    def start_conversion(self):
        thread = threading.Thread(target=self.create_video, daemon=True)
        thread.start()

    def create_video(self):
        image_folder = self.image_folder_var.get()
        output_folder = self.output_folder_var.get()
        output_filename = self.output_filename_var.get()
        frame_rate = int(self.framerate_presets.get(self.framerate_var.get(), 30))
        ffmpeg_command = self.codec_presets.get(self.codec_var.get(), "")

        if not image_folder or not output_folder or not output_filename:
            messagebox.showerror("Error", "Please select image folder, output folder, and enter output file name.")
            self.progress_var.set(0)
            return

        output_file = self.ensure_correct_extension(output_folder, output_filename, ffmpeg_command)

        self.convert_images_to_video(image_folder, output_file, frame_rate, ffmpeg_command)

    def ensure_correct_extension(self, output_folder, output_filename, ffmpeg_command):
        ext = self.extract_extension(ffmpeg_command)
        if not output_filename.lower().endswith(ext.lower()):
            output_filename = os.path.splitext(output_filename)[0] + ext
        return os.path.join(output_folder, output_filename)

    def extract_extension(self, ffmpeg_command):
        ext_start = ffmpeg_command.rfind('.') + 1
        ext = '.' + ffmpeg_command[ext_start:].strip().split(' ')[0]
        if ext:
            return ext
        return '.mp4'

    def open_settings(self):
        settings_window = ttk.Toplevel(self.root)
        settings_window.title("Settings")

        def add_preset(preset_type):
            preset_name = simpledialog.askstring("Input", f"{preset_type.capitalize()} preset name:", parent=settings_window)
            if preset_name:
                if preset_type == 'codec':
                    preset_command = simpledialog.askstring("Input", "FFmpeg command:", parent=settings_window)
                    if preset_command:
                        self.codec_presets[preset_name] = preset_command
                        self.save_presets(self.codec_presets, self.preset_file)
                        self.update_codec_dropdown()
                elif preset_type == 'framerate':
                    framerate_value = simpledialog.askstring("Input", "Framerate value:", parent=settings_window)
                    if framerate_value:
                        self.framerate_presets[preset_name] = framerate_value
                        self.save_presets(self.framerate_presets, self.framerate_preset_file)
                        self.update_framerate_dropdown()

        ttk.Button(settings_window, text="Add Codec Preset", command=lambda: add_preset('codec')).pack(pady=10)
        ttk.Button(settings_window, text="Add Framerate Preset", command=lambda: add_preset('framerate')).pack(pady=10)
        ttk.Button(settings_window, text="Close", command=settings_window.destroy).pack(pady=10)

    def update_codec_dropdown(self):
        codecs = list(self.codec_presets.keys())
        self.codec_dropdown['menu'].delete(0, 'end')
        for codec in codecs:
            self.codec_dropdown['menu'].add_command(label=codec, command=lambda value=codec: self.set_codec(value))
        if codecs:
            self.set_codec(codecs[0])

    def update_framerate_dropdown(self):
        framerates = list(self.framerate_presets.keys())
        self.framerate_dropdown['menu'].delete(0, 'end')
        for framerate in framerates:
            self.framerate_dropdown['menu'].add_command(label=framerate, command=tk._setit(self.framerate_var, framerate))
        if framerates:
            self.framerate_var.set(framerates[0])

    def set_codec(self, value):
        self.codec_var.set(value)
        ffmpeg_command = self.codec_presets.get(value, "")
        ext = self.extract_extension(ffmpeg_command)
        output_filename = self.output_filename_var.get()
        if output_filename and not output_filename.lower().endswith(ext):
            self.output_filename_var.set(os.path.splitext(output_filename)[0] + ext)

    def create_widgets(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Exit", command=self.root.quit)

        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Settings", command=self.open_settings)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About")

        frame = ttk.Frame(self.root, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        image_frame = ttk.Labelframe(frame, text="Image Sequence", padding="10")
        image_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)

        ttk.Entry(image_frame, textvariable=self.image_folder_var, width=50).grid(row=0, column=0, padx=10, pady=10)
        ttk.Button(image_frame, text="Browse", command=self.select_image_file, style='TButton').grid(row=0, column=1, padx=10, pady=10)

        output_frame = ttk.Labelframe(frame, text="Output Settings", padding="10")
        output_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)

        ttk.Label(output_frame, text="Output Folder:").grid(row=1, column=0, padx=10, pady=10)
        ttk.Entry(output_frame, textvariable=self.output_folder_var, width=50).grid(row=1, column=1, padx=10, pady=10)
        ttk.Button(output_frame, text="Browse", command=self.select_output_folder, style='TButton').grid(row=1, column=2, padx=10, pady=10)

        ttk.Label(output_frame, text="Output File Name:").grid(row=2, column=0, padx=10, pady=10)
        ttk.Entry(output_frame, textvariable=self.output_filename_var, width=50).grid(row=2, column=1, padx=10, pady=10)

        settings_frame = ttk.Labelframe(frame, text="Conversion Settings", padding="10")
        settings_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)

        ttk.Label(settings_frame, text="Frame Rate:").grid(row=3, column=0, padx=10, pady=10)
        self.framerate_dropdown = ttk.OptionMenu(settings_frame, self.framerate_var, *self.framerate_presets.keys())
        self.framerate_dropdown.grid(row=3, column=1, padx=10, pady=10, sticky="w")

        ttk.Label(settings_frame, text="Codec:").grid(row=4, column=0, padx=10, pady=10)
        self.codec_dropdown = ttk.OptionMenu(settings_frame, self.codec_var, *self.codec_presets.keys())
        self.codec_dropdown.grid(row=4, column=1, padx=10, pady=10, sticky="w")

        ttk.Button(frame, text="Convert to Video", command=self.start_conversion, style='TButton').grid(row=3, column=0, pady=20)

        ttk.Progressbar(frame, variable=self.progress_var, maximum=100).grid(row=5, column=0, padx=10, pady=10, sticky="we")

if __name__ == "__main__":
    root = ttk.Window(themename="cosmo")
    app = VideoConverterApp(root)
    root.mainloop()
