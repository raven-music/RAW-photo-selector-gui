import sys
import shutil
import argparse
import rawpy
import numpy as np
from pathlib import Path
from tkinter import Tk, Label, filedialog
from PIL import Image, ImageTk, ImageOps


# --- Settings ---
SUPPORTED_RAW_EXTS = {'.cr2', '.nef', '.arw', '.raf', '.rw2', '.dng', '.orf'}
JPEG_EXTS = {'.jpg', '.jpeg'}


## --- Path Handling ---
def clean_path(path_str: str) -> Path:
    cleaned = path_str.strip('"').strip("'")
    return Path(cleaned)

def parse_args():
    parser = argparse.ArgumentParser(
        description="Select photos and copy associated RAW files."
    )

    parser.add_argument(
        "photo_folder",
        type=clean_path,
        nargs="?",
        help="Path to folder containing JPEG previews and RAW files"
    )

    return parser.parse_args()

def get_base_dir(path: Path) -> Path:
    base_dir = path.expanduser().resolve()

    if not base_dir.exists() or not base_dir.is_dir():
        raise ValueError(f"Invalid directory: {base_dir}")

    return base_dir

def get_output_dir(base_dir: Path) -> Path:
    output_dir = base_dir / "selection"
    output_dir.mkdir(exist_ok=True)
    return output_dir

def select_folder_dialog() -> Path:
    root = Tk()
    root.withdraw()

    folder = filedialog.askdirectory(title="Select photo folder")

    root.destroy()

    if not folder:
        print("No folder selected.")
        sys.exit(1)

    return Path(folder)


class ImageSelector:
    def __init__(self, master, base_dir, output_dir):
        self.master = master
        self.base_dir = base_dir
        self.output_dir = output_dir

        self.current_img = None
        self.resize_job = None
        self.master.bind("<Configure>", self.on_resize)

        self.preview_files = self.create_preview_map(self.base_dir)

        self.index = 0

        self.label = Label(master)
        self.label.pack()

        self.instructions = Label(
            master,
            text="[←] Back    [Space] Like    [→] Skip",
            font=("Arial", 16)
        )
        self.instructions.pack(pady=10)

        self.status_label = Label(
            master,
            text="",
            font=("Arial", 24),
            fg="#00ff88"
        )

        # place over image (center)
        self.status_label.place(relx=0.98, rely=0.95, anchor="se")
        self.status_label.lower()  # hide behind initially

        master.bind('<Left>', lambda e: self.prev_image())
        master.bind('<Right>', lambda e: self.next_image())
        master.bind('<space>', lambda e: self.like_image())
        master.bind('<Up>', lambda e: self.like_image())

        # WASD navigation
        master.bind('a', lambda e: self.prev_image())
        master.bind('d', lambda e: self.next_image())
        master.bind('w', lambda e: self.like_image())
        master.bind('s', lambda e: self.next_image())
        self.show_image()

    def create_preview_map(self, base_dir: Path) -> list:
        files = list(base_dir.iterdir())

        jpeg_map = {p.stem: p for p in files if p.suffix.lower() in JPEG_EXTS}
        raw_map = {p.stem: p for p in files if p.suffix.lower() in SUPPORTED_RAW_EXTS}

        preview_map = {}

        # prefer JPEG
        for stem, jpeg in jpeg_map.items():
            preview_map[stem] = jpeg

        # fallback to RAW if no JPEG
        for stem, raw in raw_map.items():
            if stem not in preview_map:
                preview_map[stem] = raw

        preview_files = sorted(preview_map.values())

        return preview_files

    def show_image(self) -> None:
        if self.index < 0:
            self.index = 0

        if self.index >= len(self.preview_files):
            self.label.config(text="All done!", font=("Arial", 72))
            self.label.place(relx=0.5, rely=0.5, anchor="center")
            self.instructions.config(text="")
            return

        image_path = self.preview_files[self.index]

        if image_path.suffix.lower() in SUPPORTED_RAW_EXTS:
            try:
                with rawpy.imread(str(image_path)) as raw:
                    rgb = raw.postprocess(use_camera_wb=True, half_size=True)
                img = Image.fromarray(rgb)
            except Exception as e:
                print(f"RAW decode failed: {image_path} ({e})")
                self.show_status("RAW error")
                self.next_image()
                return
        else:
            with Image.open(image_path) as img:
                img = ImageOps.exif_transpose(img)
                img = img.copy()

        self.current_img = img

        self.render_image()

    def render_image(self) -> None:
        if self.current_img is None:
            return

        window_w = self.master.winfo_width()
        window_h = self.master.winfo_height()

        # reserve space for instructions/buttons
        max_w = window_w - 20
        max_h = window_h - 120

        if max_w <= 0 or max_h <= 0:
            return

        img = self.current_img.copy()
        img.thumbnail((max_w, max_h))

        self.photo = ImageTk.PhotoImage(img)
        self.label.config(image=self.photo)

    def on_resize(self, event) -> None:
        if self.resize_job is not None:
            self.master.after_cancel(self.resize_job)

        # wait 300 ms after last resize event
        self.resize_job = self.master.after(300, self.render_image)\
        
    def show_status(self, text, duration=800) -> None:
        self.status_label.config(text=text)
        self.status_label.place(relx=0.97, rely=0.95, anchor="se")
        self.master.after(duration, self.status_label.place_forget)

    def like_image(self) -> None:
        image_path = self.preview_files[self.index]
        stem = image_path.stem

        if image_path.suffix.lower() in SUPPORTED_RAW_EXTS:
            shutil.copy2(image_path, self.output_dir / image_path.name)
            self.show_status("✔ Saved")
        else:
            for ext in SUPPORTED_RAW_EXTS:
                raw_file = self.base_dir / f"{stem}{ext}"
                if raw_file.exists():
                    shutil.copy2(raw_file, self.output_dir / raw_file.name)
                    self.show_status("✔ Saved")
                    break
            else:
                self.show_status("No RAW")

    def next_image(self) -> None:
        if self.index < len(self.preview_files) - 1:
            self.index += 1
        self.show_image()

    def prev_image(self):
        if self.index > 0:
            self.index -= 1
        self.show_image()

def main() -> None:
    args = parse_args()

    photo_folder = args.photo_folder or select_folder_dialog()

    try:
        base_dir = get_base_dir(photo_folder)
    except ValueError as e:
        print(e)
        sys.exit(1)

    output_dir = get_output_dir(base_dir)

    root = Tk()
    root.title("RAW Image Selector")
    root.geometry("1600x1000")
    root.minsize(800, 600)

    app = ImageSelector(root, base_dir, output_dir)
    root.mainloop()


if __name__ == "__main__":
    main()