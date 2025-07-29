import os
import sys
import winreg
import platform
import shutil
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from PIL import Image

from PySide6.QtCore import Qt, QThread, Signal, QByteArray
from PySide6.QtGui import (
    QIcon,
    QDragEnterEvent,
    QDropEvent,
    QPalette,
    QPixmap,
    QPainter,
)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QSlider,
    QCheckBox,
    QMessageBox,
    QFormLayout,
    QComboBox,
    QInputDialog,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QProgressBar,
    QGroupBox,
    QSpinBox,
    QTextEdit,
    QSizePolicy,
    QLineEdit,
)


def is_windows_light_theme():
    """Check if Windows is using light theme via registry, fallback to palette brightness."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize",
        )
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        return value == 1  # 1 = Light, 0 = Dark
    except Exception:
        # Fallback: Use palette brightness
        palette = QApplication.instance().palette()
        window_color = palette.color(
            QPalette.ColorGroup.Active, QPalette.ColorRole.Window
        )
        brightness = (
            window_color.red() * 0.299
            + window_color.green() * 0.587
            + window_color.blue() * 0.114
        )
        return brightness > 127.5


def get_resources_folder():
    """Get the resources folder in LocalAppData"""
    if platform.system() != "Windows":
        # Fallback for non-Windows systems
        return Path(__file__).parent / "resources"

    local_appdata = os.getenv("LOCALAPPDATA")
    if local_appdata is None:
        local_appdata = str(Path.home() / "AppData" / "Local")

    resources_path = Path(local_appdata) / "MMImageOptimizer" / "resources"

    # If resources folder doesn't exist, fall back to local resources
    if not resources_path.exists():
        return Path(__file__).parent / "resources"

    return resources_path


def get_localappdata_folder():
    global local_appdata
    if platform.system() != "Windows":
        local_appdata = None
        return None

    path_str = os.getenv("LOCALAPPDATA")
    if path_str is None:
        path_str = str(Path.home() / "AppData" / "Local")

    try:
        path = Path(path_str).resolve()
        if path.is_dir():
            local_appdata = path
            return local_appdata
        else:
            local_appdata = None
            return None
    except Exception:
        local_appdata = None
        return None


# Use pathlib for robust path handling
RESOURCES_DIR = get_resources_folder()
MAGICK = RESOURCES_DIR / "magick.exe"
CWEBP = RESOURCES_DIR / "cwebp.exe"
AVIFENC = RESOURCES_DIR / "avifenc.exe"
CJPEGLI = RESOURCES_DIR / "cjpegli.exe"
OXIPNG = RESOURCES_DIR / "oxipng.exe"
PNGQUANT = RESOURCES_DIR / "pngquant.exe"
EXIFTOOL = RESOURCES_DIR / "exiftool.exe"

FORMATS = ["PNG", "JPEG", "WebP", "AVIF"]

MOHSENI_LOGO = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256"><rect width="256" height="256" rx="64" fill="#0f52ba"/><path d="M63.9,79.1c-3.7-5.4-9.9-8.7-16.4-8.7h-15.9l13.7,17.8h2.3c.7,0,1.3.3,1.6.9l47.1,69.4c12,17.5,35.9,22,53.4,9.9,3.9-2.7,7.3-6,9.9-9.9l47.1-69.4c.1-.2.3-.4.5-.5.9-.6,2.1-.4,2.7.5v63.7c0,8.2-6.7,14.9-14.9,14.9h-7.3v17.8h7.3c18.1,0,32.7-14.6,32.7-32.7v-63.7c-.5-10.8-9.6-19.1-20.4-18.7-6.2.3-11.9,3.5-15.4,8.7l-47.2,69.6c-1.4,1.9-3,3.6-4.9,4.9-9.3,6.6-22.2,4.4-28.8-4.9l-47.2-69.6h0ZM46,152.9v-34l-17.8,24v10c0,18.1,14.6,32.7,32.7,32.7h7.3v-17.8h-7.3c-8.2,0-14.9-6.7-14.9-14.9Z" fill="#fff"/></svg>"""
ICON_FOLDER_INPUT = """<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-6">
  <path stroke-linecap="round" stroke-linejoin="round" d="M12 10.5v6m3-3H9m4.06-7.19-2.12-2.12a1.5 1.5 0 0 0-1.061-.44H4.5A2.25 2.25 0 0 0 2.25 6v12a2.25 2.25 0 0 0 2.25 2.25h15A2.25 2.25 0 0 0 21.75 18V9a2.25 2.25 0 0 0-2.25-2.25h-5.379a1.5 1.5 0 0 1-1.06-.44Z" />
</svg>
"""
ICON_FOLDER_OUTPUT = """<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-6">
  <path stroke-linecap="round" stroke-linejoin="round" d="m9 13.5 3 3m0 0 3-3m-3 3v-6m1.06-4.19-2.12-2.12a1.5 1.5 0 0 0-1.061-.44H4.5A2.25 2.25 0 0 0 2.25 6v12a2.25 2.25 0 0 0 2.25 2.25h15A2.25 2.25 0 0 0 21.75 18V9a2.25 2.25 0 0 0-2.25-2.25h-5.379a1.5 1.5 0 0 1-1.06-.44Z" />
</svg>
"""
ICON_FOLDER_OPEN = """<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-6">
  <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 6H5.25A2.25 2.25 0 0 0 3 8.25v10.5A2.25 2.25 0 0 0 5.25 21h10.5A2.25 2.25 0 0 0 18 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
</svg>
"""
ICON_UPLOAD = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 68 24" fill="none" stroke-width="1.5" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="M27.53 20.83l-4.5-4.5m0 0l4.5-4.5m-4.5 4.5h13.5m0-13.5l4.5 4.5m0 0l-4.5 4.5m4.5-4.5h-13.5m-10 6.75v-2.62c0-1.86-1.51-3.38-3.38-3.38h-1.5a1.12 1.12 0 0 1-1.12-1.12h0v-1.5c0-1.86-1.51-3.38-3.38-3.38H6.27m3.76 9v6m3-3h-6m1.5-12H3.65A1.12 1.12 0 0 0 2.53 3.2v17.25a1.12 1.12 0 0 0 1.12 1.12H16.4a1.12 1.12 0 0 0 1.12-1.12v-9.37c0-4.97-4.03-9-9-9zm47.19 8.53v6m3-3h-6m4.06-7.19L54.66 4.3a1.5 1.5 0 0 0-1.06-.44h-5.38c-1.24 0-2.25 1.01-2.25 2.25v12c0 1.24 1.01 2.25 2.25 2.25h15c1.24 0 2.25-1.01 2.25-2.25v-9c0-1.24-1.01-2.25-2.25-2.25h-5.38a1.5 1.5 0 0 1-1.06-.44h0z"/></svg>"""
ICON_RESOLUTION_MINUS = """<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-6">
  <path stroke-linecap="round" stroke-linejoin="round" d="M15 12H9m12 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
</svg>
"""
ICON_RESOLUTION_PLUS = """<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-6">
  <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v6m3-3H9m12 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
</svg>
"""
ICON_RUN_PROCESS = """<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-6">
  <path stroke-linecap="round" stroke-linejoin="round" d="M15.59 14.37a6 6 0 0 1-5.84 7.38v-4.8m5.84-2.58a14.98 14.98 0 0 0 6.16-12.12A14.98 14.98 0 0 0 9.631 8.41m5.96 5.96a14.926 14.926 0 0 1-5.841 2.58m-.119-8.54a6 6 0 0 0-7.381 5.84h4.8m2.581-5.84a14.927 14.927 0 0 0-2.58 5.84m2.699 2.7c-.103.021-.207.041-.311.06a15.09 15.09 0 0 1-2.448-2.448 14.9 14.9 0 0 1 .06-.312m-2.24 2.39a4.493 4.493 0 0 0-1.757 4.306 4.493 4.493 0 0 0 4.306-1.758M16.5 9a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0Z" />
</svg>
"""


def svg_to_icon(svg_str, color="#181818", size=(24, 24), type="icon"):
    # Get device pixel ratio for high-DPI screens
    app = QApplication.instance()
    dpr = app.devicePixelRatio() if app else 1
    # Render at higher resolution for better quality
    render_size = (int(size[0] * dpr), int(size[1] * dpr))
    svg_colored = svg_str.replace("currentColor", color)
    svg_bytes = QByteArray(svg_colored.encode("utf-8"))
    renderer = QSvgRenderer(svg_bytes)
    pixmap = QPixmap(render_size[0], render_size[1])
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    renderer.render(painter)
    painter.end()
    pixmap.setDevicePixelRatio(dpr)
    if type == "icon":
        return QIcon(pixmap)
    else:
        return pixmap


def detect_gpu_acceleration():
    """Detect if GPU acceleration is available for ImageMagick"""
    try:
        result = subprocess.run(
            [str(MAGICK), "-list", "configure"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        output = result.stdout.lower()

        # Check for OpenCL or CUDA support
        has_opencl = "opencl" in output
        has_cuda = "cuda" in output

        return {
            "available": has_opencl or has_cuda,
            "opencl": has_opencl,
            "cuda": has_cuda,
        }
    except:
        return {"available": False, "opencl": False, "cuda": False}


def get_optimal_thread_count():
    """Get optimal thread count for processing"""
    cpu_count = os.cpu_count() or 4
    # Use 75% of available cores, minimum 1, maximum 8
    return max(1, min(8, int(cpu_count * 0.75)))


def should_resize(input_img_path, target_size):
    img = Image.open(input_img_path)
    width, height = img.size

    # Pixel value
    if isinstance(target_size, int):
        # Don't upscale: skip if target size is larger than original
        if target_size >= min(width, height):
            return False
        else:
            return True

    # Percentage string, e.g., "50%"
    if isinstance(target_size, str) and target_size.endswith("%"):
        try:
            pct = float(target_size.rstrip("%"))
            if pct <= 0:
                return False
            new_w = int(width * pct / 100)
            new_h = int(height * pct / 100)
            # Don't upscale
            if new_w >= width or new_h >= height:
                return False
            else:
                return True
        except Exception:
            return False

    # Float < 1, treat as percent
    if isinstance(target_size, float) and 0 < target_size < 1:
        new_w = int(width * target_size)
        new_h = int(height * target_size)
        if new_w >= width or new_h >= height:
            return False
        else:
            return True

    # fallback
    return False


def validate_resize_input(val):
    val = str(val).strip().replace(" ", "")

    # Blank or missing input becomes default
    if not val:
        return 256

    # Handle percentage like '0%' or '105%'
    if val.endswith("%"):
        pct_str = val[:-1]
        try:
            pct_val = float(pct_str)
        except Exception:
            pct_val = 100  # fallback
        # Clamp between 1 and 100
        pct_val = max(1, min(pct_val, 100))
        return f"{int(pct_val)}%" if pct_val.is_integer() else f"{pct_val:.2f}%"

    # Accept float <1 as percent (e.g. 0.5 means 50%)
    try:
        float_val = float(val)
        if 0 < float_val < 1:
            pct_val = float_val * 100
            pct_val = max(1, min(pct_val, 100))
            return f"{int(pct_val)}%" if pct_val.is_integer() else f"{pct_val:.2f}%"
        # Otherwise, treat as pixel size
        n = int(round(float_val))
        # Clamp to safe range
        n = max(2, min(n, 10000))
        return n
    except Exception:
        return 256  # fallback default


class FileStats:
    """Class to track file size statistics"""

    def __init__(self):
        self.original_size = 0
        self.optimized_size = 0
        self.files_processed = 0

    def add_file(self, original_size, optimized_size):
        self.original_size += original_size
        self.optimized_size += optimized_size
        self.files_processed += 1

    def get_compression_ratio(self):
        if self.original_size == 0:
            return 0
        return ((self.original_size - self.optimized_size) / self.original_size) * 100

    def get_size_saved(self):
        return self.original_size - self.optimized_size

    def format_size(self, size_bytes):
        """Format size in human readable format"""
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"


def call(args, progress_callback=None, use_gpu=False):
    """Helper to call subprocess silently without console windows"""
    # Convert Path objects to strings for subprocess
    str_args = [str(arg) for arg in args]

    # Add GPU acceleration if available and requested
    if use_gpu and str_args[0].endswith("magick.exe"):
        # Insert GPU acceleration flags after magick command
        gpu_info = detect_gpu_acceleration()
        if gpu_info["available"]:
            if gpu_info["opencl"]:
                str_args.insert(1, "-define")
                str_args.insert(2, "accelerate:auto-threshold=1")
            # Note: CUDA support would require different flags based on ImageMagick build

    # Configure subprocess to run silently (no console window)
    startupinfo = None
    if platform.system() == "Windows":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE

    result = subprocess.run(
        str_args,
        check=True,
        startupinfo=startupinfo,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    if progress_callback:
        progress_callback()

    return result


class ImageProcessor:
    """Class to handle individual image processing with GPU support"""

    def __init__(self, use_gpu=False):
        self.use_gpu = use_gpu

    def process_single_image(
        self,
        file_path,
        tmp_dir,
        base_name,
        resolutions,
        formats,
        qmap,
        qlossless_map,
        strip_meta,
        output_dir,
    ):
        """Process a single image and return statistics"""
        stats = FileStats()
        original_size = file_path.stat().st_size
        errors = []

        # Normalize to PNG
        try:
            normalized = self.normalize_to_png(file_path, tmp_dir, base_name)
        except Exception as e:
            errors.append(f"Normalize to PNG failed: {file_path.name} ({e})")
            stats.errors = errors
            return stats

        if strip_meta:
            try:
                # Strip metadata using exiftool
                call([EXIFTOOL, "-all=", "-overwrite_original", str(normalized)])
            except Exception as e:
                errors.append(f"Metadata strip failed: {file_path.name} ({e})")

        # Resize step
        try:
            resized = self.pyramidal_resize(normalized, tmp_dir, base_name, resolutions)
        except Exception as e:
            errors.append(f"Resize failed: {file_path.name} ({e})")
            stats.errors = errors
            return stats

        # Process each resolution and format
        for res in resolutions:
            size = res["size"]
            source_png = resized[size]
            filename_base = base_name if size == "original" else f"{base_name}_{size}"

            if "PNG" in formats:
                try:
                    png_out = output_dir / f"{filename_base}.png"
                    if png_out.exists():
                        if not self.ask_overwrite(png_out):
                            continue
                    shutil.copyfile(source_png, png_out)
                    self.encode_png(
                        source_png,
                        png_out,
                        qmap.get("PNG", 82),
                        qlossless_map.get("PNG", True),
                    )
                    optimized_size = png_out.stat().st_size
                    stats.add_file(original_size, optimized_size)
                except Exception as e:
                    errors.append(f"PNG: {filename_base}.png ({e})")

            if "WebP" in formats:
                try:
                    webp_out = output_dir / f"{filename_base}.webp"
                    if webp_out.exists():
                        if not self.ask_overwrite(webp_out):
                            continue
                    self.encode_webp(source_png, webp_out, qmap.get("WebP", 82))
                    optimized_size = webp_out.stat().st_size
                    stats.add_file(original_size, optimized_size)
                except Exception as e:
                    errors.append(f"WebP: {filename_base}.webp ({e})")

            if "AVIF" in formats:
                try:
                    avif_out = output_dir / f"{filename_base}.avif"
                    if avif_out.exists():
                        if not self.ask_overwrite(avif_out):
                            continue
                    self.encode_avif(source_png, avif_out, qmap.get("AVIF", 65))
                    optimized_size = avif_out.stat().st_size
                    stats.add_file(original_size, optimized_size)
                except Exception as e:
                    errors.append(f"AVIF: {filename_base}.avif ({e})")

            if "JPEG" in formats:
                try:
                    jpg_out = output_dir / f"{filename_base}.jpg"
                    if jpg_out.exists():
                        if not self.ask_overwrite(jpg_out):
                            continue
                    self.encode_jpegli(
                        source_png,
                        jpg_out,
                        qmap.get("JPEG", 82),
                        qlossless_map.get("JPEG", False),
                    )
                    optimized_size = jpg_out.stat().st_size
                    stats.add_file(original_size, optimized_size)
                except Exception as e:
                    errors.append(f"JPEG: {filename_base}.jpg ({e})")

        stats.errors = errors
        return stats

    def normalize_to_png(self, input_path, tmp_dir, base_name):
        out_png = tmp_dir / f"{base_name}_norm.png"
        if input_path.suffix.lower() == ".png":
            shutil.copyfile(input_path, out_png)
        else:
            cmd = [MAGICK, input_path, out_png]
            call(cmd, use_gpu=self.use_gpu)
        return out_png

    def sort_res_modes(self, res_modes):
        def key_fn(r):
            size = r.get("size")
            if isinstance(size, str) and size.endswith("%"):
                return float(size.rstrip("%"))
            try:
                return float(size)
            except (TypeError, ValueError):
                return float("inf")

        return sorted(res_modes, key=key_fn, reverse=True)

    def pyramidal_resize(
        self,
        input_path,
        tmp_dir,
        base_name,
        res_modes,
    ):
        intermediates = []
        original_img = input_path

        # Handle "original" mode - no resizing
        if len(res_modes) == 1 and res_modes[0].get("size") == "original":
            out_path = tmp_dir / f"{base_name}_original.png"
            shutil.copyfile(original_img, out_path)
            intermediates.append(("original", out_path))
            return dict(intermediates)

        # Handle normal resizing - each resize works from the original image
        sorted_modes = self.sort_res_modes(res_modes)

        for r in sorted_modes:
            size = r["size"]
            mode = r.get("mode", "fit")
            out_path = tmp_dir / f"{base_name}_{size}.png"

            if not should_resize(original_img, size):
                continue

            # Pixel resize (int)
            if isinstance(size, int):
                if mode == "fit":
                    resize_str = f"{size}x{size}"
                elif mode == "crop":
                    resize_str = f"{size}x{size}^"
                    # For crop mode, add gravity and extent
                    cmd = [
                        MAGICK,
                        original_img,
                        "-colorspace",
                        "RGB",
                        "-filter",
                        "RobidouxSharp",
                        "-resize",
                        resize_str,
                        "-gravity",
                        "center",
                        "-extent",
                        f"{size}x{size}",
                        "-colorspace",
                        "sRGB",
                        out_path,
                    ]
                elif mode == "width":
                    resize_str = f"{size}x"
                elif mode == "height":
                    resize_str = f"x{size}"
                else:
                    raise ValueError(f"Unknown resize mode: {mode}")

                # For non-crop modes, use standard command
                if mode != "crop":
                    cmd = [
                        MAGICK,
                        original_img,
                        "-colorspace",
                        "RGB",
                        "-filter",
                        "RobidouxSharp",
                        "-resize",
                        resize_str,
                        "-colorspace",
                        "sRGB",
                        out_path,
                    ]

            # Percent resize (str like "50%")
            elif isinstance(size, str) and size.endswith("%"):
                resize_str = size
                cmd = [
                    MAGICK,
                    original_img,
                    "-colorspace",
                    "RGB",
                    "-filter",
                    "RobidouxSharp",
                    "-resize",
                    resize_str,
                    "-colorspace",
                    "sRGB",
                    out_path,
                ]
            else:
                raise ValueError(f"Unsupported size format: {size}")

            call(cmd, use_gpu=self.use_gpu)
            intermediates.append((size, out_path))

        return dict(intermediates)

    def encode_webp(self, in_png, out_path, quality):
        cmd = [CWEBP, "-q", str(quality), in_png, "-o", out_path]
        call(cmd)

    def encode_avif(self, in_png, out_path, quality):
        cmd = [AVIFENC, "-q", str(quality), "--speed", "2", in_png, out_path]
        call(cmd)

    def encode_jpegli(
        self, in_png, out_path, quality=None, lossless=False, chroma_444=False
    ):
        """Encode JPEG with jpegli (cjpegli) CLI."""
        cmd = [str(CJPEGLI), str(in_png), str(out_path)]

        if lossless:
            cmd += ["--distance", "1.0"]
        elif quality is not None:
            cmd += ["--quality", str(quality)]
        else:
            cmd += ["--quality", "82"]

        if chroma_444:
            cmd += ["--chroma_subsampling=444"]

        # Remove empty strings (for safety)
        cmd = [arg for arg in cmd if arg]

        call(cmd)

    def encode_png(self, in_png, out_path, quality=None, lossless=True):
        oxi_cmd = [
            OXIPNG,
            "--opt",
            "max",
            "--zopfli",
            "--force",
            "--out",
            out_path,
            in_png,
            "--timeout",
            "30",
            "--interlace",
            "0",
        ]
        if not lossless:
            oxi_cmd.append("--scale16")
        call(oxi_cmd)

        if not lossless:
            # If not lossless, use pngquant for further optimization
            if quality is None:
                quality = 82
            pq_cmd = [
                PNGQUANT,
                "--quality",
                f"{max(quality-15, 50)}-{quality}",
                "--speed",
                "1",
                "--output",
                out_path,
                "--force",
                out_path,
            ]
            call(pq_cmd)


class ProcessingThread(QThread):
    """Thread for multi-threaded image processing"""

    progress_updated = Signal(int, int)  # current, total
    status_updated = Signal(str)
    stats_updated = Signal(object)  # FileStats object
    finished = Signal()
    error_occurred = Signal(str)

    def __init__(
        self,
        processor,
        input_sources,
        output_dir,
        resolutions,
        formats,
        qmap,
        qlossless_map,
        strip_meta,
        recursive,
        thread_count,
        use_gpu,
    ):
        super().__init__()
        self.processor = processor
        self.input_sources = input_sources
        self.output_dir = Path(output_dir)
        self.resolutions = resolutions
        self.formats = formats
        self.qmap = qmap
        self.qlossless_map = qlossless_map
        self.strip_meta = strip_meta
        self.recursive = recursive
        self.thread_count = thread_count
        self.use_gpu = use_gpu
        self.total_stats = FileStats()

    def run(self):
        try:
            self.process_images_multithreaded()
            self.finished.emit()
        except Exception as e:
            self.error_occurred.emit(str(e))

    def gather_image_files(self, sources, recursive=False):
        """Given a list of Path objects (files or folders), return a flat list of image files"""
        exts = {
            ".jpg",
            ".jpeg",
            ".png",
            ".webp",
            ".avif",
            ".gif",
            ".bmp",
            ".tiff",
            ".tif",
            ".heic",
            ".heif",
            ".dds",
            ".j2c",
            ".j2k",
            ".jp2",
            ".jpe",
            ".jxl",
            ".png24",
            ".png32",
            ".png48",
            ".png64",
            ".png16",
            ".png8",
            ".psd",
            ".tga",
            ".ico",
        }
        image_files = []
        for src in sources:
            src = Path(src)
            if src.is_dir():
                if recursive:
                    for ext in exts:
                        image_files.extend(src.rglob(f"*{ext}"))
                        image_files.extend(src.rglob(f"*{ext.upper()}"))
                else:
                    for f in src.iterdir():
                        if f.is_file() and f.suffix.lower() in exts:
                            image_files.append(f)
            elif src.is_file() and src.suffix.lower() in exts:
                image_files.append(src)
        return image_files

    def process_images_multithreaded(self):
        """Process images using multiple threads"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        tmp_dir = self.output_dir / "_tmp"
        tmp_dir.mkdir(parents=True, exist_ok=True)

        self.status_updated.emit("Gathering image files...")
        image_files = self.gather_image_files(self.input_sources, self.recursive)
        total_files = len(image_files)

        if total_files == 0:
            self.status_updated.emit("No image files found")
            return

        self.status_updated.emit(
            f"Found {total_files} images. Starting multi-threaded processing..."
        )

        # Create individual tmp directories for each thread to avoid conflicts
        thread_tmp_dirs = []
        for i in range(self.thread_count):
            thread_tmp_dir = tmp_dir / f"thread_{i}"
            thread_tmp_dir.mkdir(exist_ok=True)
            thread_tmp_dirs.append(thread_tmp_dir)

        completed_files = 0

        # Process images using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=self.thread_count) as executor:
            # Create processor instances for each thread
            processors = [
                ImageProcessor(self.use_gpu) for _ in range(self.thread_count)
            ]

            # Submit all tasks
            futures = []
            for i, file_path in enumerate(image_files):
                thread_id = i % self.thread_count
                processor = processors[thread_id]
                thread_tmp_dir = thread_tmp_dirs[thread_id]

                future = executor.submit(
                    processor.process_single_image,
                    file_path,
                    thread_tmp_dir,
                    file_path.stem,
                    self.resolutions,
                    self.formats,
                    self.qmap,
                    self.qlossless_map,
                    self.strip_meta,
                    self.output_dir,
                )
                futures.append((future, file_path.name))

            # Process completed tasks
            for future, filename in futures:
                try:
                    stats = future.result()
                    self.total_stats.original_size += stats.original_size
                    self.total_stats.optimized_size += stats.optimized_size
                    self.total_stats.files_processed += 1

                    completed_files += 1
                    self.progress_updated.emit(completed_files, total_files)
                    self.status_updated.emit(
                        f"Processed: {filename} ({completed_files}/{total_files})"
                    )
                    self.stats_updated.emit(self.total_stats)

                except Exception as e:
                    self.status_updated.emit(f"Error processing {filename}: {str(e)}")

        # Cleanup
        shutil.rmtree(tmp_dir)


class DragDropLabel(QLabel):
    """Label that supports drag and drop for folders/files"""

    files_dropped = Signal(list)

    def __init__(self, text=""):
        super().__init__(text)
        self.setAcceptDrops(True)
        self.setMinimumHeight(50)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.apply_default_style()
        QApplication.instance().paletteChanged.connect(self.apply_default_style)

    def apply_drag_over_style(self):
        is_light = is_windows_light_theme()
        if is_light:
            border_color = "#0078d7"
            bg_color = "rgba(0,120,215,0.08)"
            color = "#181818"
        else:
            border_color = "#3a96dd"
            bg_color = "rgba(58,150,221,0.18)"
            color = "#ffffff"
        self.setStyleSheet(
            f"""
            QLabel {{
                border: 2px dashed {border_color};
                border-radius: 8px;
                padding: 5px;
                background-color: {bg_color};
                color: {color};
                font-weight: 500;
            }}
            """
        )

    def apply_default_style(self):
        is_light = is_windows_light_theme()
        if is_light:
            border_color = "#888"
            bg_color = "rgba(255,255,255,0.95)"
            text_color = "#222"
            hover_border = "#0078d7"
            hover_bg = "rgba(0,120,215,0.08)"
        else:
            border_color = "#444"
            bg_color = "rgba(30,30,30,0.95)"
            text_color = "#eee"
            hover_border = "#3a96dd"
            hover_bg = "rgba(58,150,221,0.18)"

        self.setStyleSheet(
            f"""
            QLabel {{
                border: 2px dashed {border_color};
                border-radius: 8px;
                padding: 5px;
                background-color: {bg_color};
                color: {text_color};
                font-weight: 500;
            }}
            QLabel:hover {{
                border-color: {hover_border};
                background-color: {hover_bg};
            }}
            """
        )

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            paths = [Path(url.toLocalFile()) for url in event.mimeData().urls()]
            # Accept if at least one is a file or folder
            if any(path.is_file() or path.is_dir() for path in paths):
                event.acceptProposedAction()
                self.apply_drag_over_style()
                return
        event.ignore()

    def dragLeaveEvent(self, event):
        self.apply_default_style()

    def dropEvent(self, event: QDropEvent):
        paths = [Path(url.toLocalFile()) for url in event.mimeData().urls()]
        accepted = [str(p) for p in paths if p.exists()]
        if accepted:
            self.files_dropped.emit(accepted)
            event.acceptProposedAction()
        self.apply_default_style()


class MainWin(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MMImageOptimizer - Mohammadreza Mohseni")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        self.setWindowIcon(svg_to_icon(MOHSENI_LOGO, type="icon"))
        self.overwrite_policy = None

        self.input_dir = ""
        self.output_dir = ""
        self.processing_thread = None
        self.gpu_info = detect_gpu_acceleration()
        self.process_completed = False

        QApplication.instance().paletteChanged.connect(self.apply_icon_style)
        self.apply_icon_style()
        self.initUI()

    def initUI(self):
        initial_icon_color = "#181818" if is_windows_light_theme() else "#ffffff"
        layout = QVBoxLayout(self)

        # Folder selectors group with drag & drop
        folder_group = QGroupBox("Input/Output Folders (Drag & Drop Supported)")

        # Input folder with drag & drop
        input_layout = QVBoxLayout()
        input_header = QHBoxLayout()
        input_header.addWidget(QLabel("Input Files or Folders:"))
        self.btnIn = QPushButton()
        self.btnIn.setIcon(
            svg_to_icon(
                ICON_FOLDER_INPUT, color=initial_icon_color, size=(20, 20), type="icon"
            )
        )
        self.btnIn.setFixedSize(32, 32)
        self.btnIn.clicked.connect(self.pickInput)
        input_header.addWidget(self.btnIn)
        input_layout.addLayout(input_header)

        self.inLabel = DragDropLabel()
        self.inLabel.setPixmap(
            svg_to_icon(
                ICON_UPLOAD, color=initial_icon_color, size=(68, 24), type="pixmap"
            )
        )
        self.inLabel.setToolTip(
            "Drop images/folders or browse to select files or folder."
        )
        self.inLabel.setMaximumHeight(50)
        self.inLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.inLabel.files_dropped.connect(self.set_input_files)
        input_layout.addWidget(self.inLabel)

        # Recursive checkbox
        self.recursiveCheck = QCheckBox("Include subfolders recursively")
        self.recursiveCheck.setChecked(False)
        self.recursiveCheck.setFixedHeight(16)
        self.recursiveCheck.setToolTip("Process images in subfolders as well")

        input_widget = QWidget()
        input_widget.setLayout(input_layout)

        # Output folder with drag & drop
        output_layout = QVBoxLayout()
        output_header = QHBoxLayout()
        output_header.addWidget(QLabel("Output Folder:"))
        openOutBtn = QPushButton()
        openOutBtn.setIcon(
            svg_to_icon(
                ICON_FOLDER_OPEN, color=initial_icon_color, size=(20, 20), type="icon"
            )
        )
        openOutBtn.setFixedSize(32, 32)
        openOutBtn.setToolTip("Open the output folder in Explorer")
        openOutBtn.clicked.connect(self.open_output_folder)
        output_header.addWidget(openOutBtn)
        btnOut = QPushButton()
        btnOut.setIcon(
            svg_to_icon(
                ICON_FOLDER_INPUT, color=initial_icon_color, size=(20, 20), type="icon"
            )
        )
        btnOut.setFixedSize(32, 32)
        btnOut.setToolTip("Select output folder for optimized images")
        btnOut.clicked.connect(self.pickOutput)
        output_header.addWidget(btnOut)
        output_layout.addLayout(output_header)

        self.outLabel = DragDropLabel()
        self.outLabel.setPixmap(
            svg_to_icon(
                ICON_FOLDER_OUTPUT,
                color=initial_icon_color,
                size=(24, 24),
                type="pixmap",
            )
        )
        self.outLabel.setToolTip(
            "Drop or select the folder for optimized output images."
        )
        self.outLabel.setMaximumHeight(50)
        self.outLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.outLabel.files_dropped.connect(
            lambda paths: self.set_output_folder(paths[0]) if paths else None
        )
        output_layout.addWidget(self.outLabel)
        output_widget = QWidget()
        output_widget.setLayout(output_layout)

        input_widget.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        output_widget.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed
        )
        input_widget.setContentsMargins(0, 0, 0, 0)
        output_widget.setContentsMargins(0, 0, 0, 0)

        side_by_side = QHBoxLayout()
        side_by_side.addWidget(input_widget)
        side_by_side.addWidget(output_widget)
        side_by_side.setStretch(0, 1)
        side_by_side.setStretch(1, 1)

        folder_layout = QVBoxLayout(folder_group)
        folder_layout.addLayout(side_by_side)
        folder_layout.addWidget(self.recursiveCheck)
        folder_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        folder_group.setLayout(folder_layout)
        layout.addWidget(folder_group)

        # Performance settings group
        extra_group = QGroupBox("Extra Options")
        extra_layout = QHBoxLayout(extra_group)

        # Thread count and GPU in one row
        self.thread_count_spin = QSpinBox()
        self.thread_count_spin.setRange(1, 16)
        self.thread_count_spin.setValue(get_optimal_thread_count())
        self.thread_count_spin.setToolTip("Number of parallel processing threads")
        self.thread_count_spin.setFixedWidth(80)
        thread_label = QLabel("Processing Threads:")
        thread_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        extra_layout.addWidget(thread_label)
        extra_layout.addWidget(self.thread_count_spin)
        extra_layout.addWidget(QLabel(f"(Optimal: {get_optimal_thread_count()})"))

        self.gpu_check = QCheckBox("Enable GPU Acceleration")
        self.gpu_check.setChecked(self.gpu_info["available"])
        self.gpu_check.setEnabled(self.gpu_info["available"])
        if self.gpu_info["available"]:
            gpu_text = "GPU acceleration available"
            if self.gpu_info["opencl"]:
                gpu_text += " (OpenCL)"
            if self.gpu_info["cuda"]:
                gpu_text += " (CUDA)"
        else:
            gpu_text = "GPU acceleration not available"
        self.gpu_check.setToolTip(gpu_text)
        extra_layout.addSpacing(30)
        extra_layout.addWidget(self.gpu_check)

        self.stripMeta_check = QCheckBox("Strip Metadata")
        self.stripMeta_check.setChecked(True)
        extra_layout.addWidget(self.stripMeta_check)
        self.stripMeta_check.setToolTip(
            "If checked, removes metadata from output images to reduce size."
        )
        extra_layout.addSpacing(30)

        extra_layout.addStretch(1)

        layout.addWidget(extra_group)

        # Output formats group
        formats_group = QGroupBox("Output Formats and Quality")
        formats_layout = QFormLayout(formats_group)
        self.formatChecks = {}
        self.qualityWidgets = {}
        self.losslessWidgets = {}

        for fmt in FORMATS:
            row = QHBoxLayout()
            cb = QCheckBox(text="")
            cb.setChecked(fmt in ["JPEG"])
            self.formatChecks[fmt] = cb
            cb.setFixedWidth(30)
            cb.setToolTip(f"Enable {fmt} output format")
            cb.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            row.addWidget(cb)

            if fmt == "PNG":
                q = QSlider(Qt.Orientation.Horizontal)
                q.setRange(50, 100)
                q.setValue(82)
            elif fmt == "JPEG":
                q = QSlider(Qt.Orientation.Horizontal)
                q.setRange(50, 100)
                q.setValue(85)
            elif fmt == "WebP":
                q = QSlider(Qt.Orientation.Horizontal)
                q.setRange(50, 100)
                q.setValue(82)
            elif fmt == "AVIF":
                q = QSlider(Qt.Orientation.Horizontal)
                q.setRange(30, 100)
                q.setValue(65)

            q.setTickInterval(1)
            q.setToolTip(f"{fmt} quality")
            q.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

            self.qualityWidgets[fmt] = q
            row.addWidget(q)

            quality_label = QLabel(str(q.value()))
            quality_label.setFixedWidth(20)
            quality_label.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            row.addWidget(quality_label)
            q.valueChanged.connect(
                lambda val, label=quality_label: label.setText(str(val))
            )

            if fmt == "JPEG" or fmt == "PNG":
                lossless = QCheckBox("Lossless")
                lossless.setToolTip(f"{fmt} lossless mode")
                lossless.setChecked(fmt == "PNG")
                lossless.setEnabled(True)
                lossless.stateChanged.connect(
                    lambda state, f=fmt: self.update_quality_slider_states()
                )
            else:
                lossless = QCheckBox("")
                lossless.setChecked(False)
                lossless.setEnabled(False)
            lossless.setFixedWidth(63)
            lossless.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            row.addWidget(lossless)
            self.losslessWidgets[fmt] = lossless
            formats_layout.addRow(fmt, row)

        layout.addWidget(formats_group)
        self.update_quality_slider_states()

        # --- Place Output Resolutions and Processing (Progress) side by side ---
        main_hbox = QHBoxLayout()

        # Resolutions group
        res_group = QGroupBox("Output Resolutions")
        res_layout = QVBoxLayout(res_group)

        # Add/Remove buttons on top
        btns_layout = QHBoxLayout()
        self.NoResize = QCheckBox("No Resize")
        self.NoResize.setChecked(True)
        self.NoResize.setToolTip(
            "If checked, disables resizing and keeps images at their original size."
        )
        btns_layout.addWidget(self.NoResize)
        btnAddRes = QPushButton()
        btnAddRes.setFixedSize(28, 28)
        btnAddRes.setIcon(
            svg_to_icon(
                ICON_RESOLUTION_PLUS,
                color=initial_icon_color,
                size=(20, 20),
                type="icon",
            )
        )
        btnAddRes.clicked.connect(self.addResDialog)
        btnDelRes = QPushButton()
        btnDelRes.setFixedSize(28, 28)
        btnDelRes.setIcon(
            svg_to_icon(
                ICON_RESOLUTION_MINUS,
                color=initial_icon_color,
                size=(20, 20),
                type="icon",
            )
        )

        btnDelRes.clicked.connect(self.delRes)
        btns_layout.addWidget(btnAddRes)
        btns_layout.addWidget(btnDelRes)
        self.btnAddRes = btnAddRes
        self.btnDelRes = btnDelRes
        btnAddRes.setToolTip("Add a new resolution")
        btnDelRes.setToolTip("Remove selected resolution(s)")
        self.NoResize.stateChanged.connect(self.toggle_resize_controls)
        btns_layout.addStretch(1)
        res_layout.addLayout(btns_layout)

        # Table below buttons
        self.resTable = QTableWidget(0, 2)
        self.resTable.setHorizontalHeaderLabels(["Size", "Mode"])
        self.resTable.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.resTable.verticalHeader().setVisible(False)
        self.resTable.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.resTable.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked)
        res_layout.addWidget(self.resTable)
        self.resTable.itemChanged.connect(self.on_res_table_item_changed)
        self.toggle_resize_controls(2)

        # Add default rows
        for size, mode in [(256, "fit"), ("50%", "fit")]:
            self.addResRow(size, mode)

        # Processing (Progress & Statistics) group
        progress_group = QGroupBox("Processing")
        progress_layout = QVBoxLayout(progress_group)

        self.status_label = QLabel("Ready")
        self.status_label.setFixedHeight(20)
        progress_layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(20)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.progress_bar.setToolTip("Shows the progress of current batch processing.")
        progress_layout.addWidget(self.progress_bar)

        # Statistics display
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setVisible(True)
        self.stats_text.setToolTip("Summary of file sizes and compression ratio.")
        # Make the stats area expand as the group grows
        self.stats_text.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        progress_layout.addWidget(self.stats_text, stretch=2)

        # Start button (large, inside progress group)
        self.btnGo = QPushButton("Start Optimization")
        self.btnGo.setIcon(
            svg_to_icon(
                ICON_RUN_PROCESS, color=initial_icon_color, size=(42, 42), type="icon"
            )
        )
        self.btnGo.setFixedHeight(48)
        self.btnGo.setToolTip(
            "Start processing the selected images with the specified settings."
        )
        self.btnGo.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.btnGo.clicked.connect(self.runProcess)
        progress_layout.addWidget(self.btnGo)

        # Add both groups to main_hbox
        main_hbox.addWidget(res_group, 2)
        main_hbox.addWidget(progress_group, 3)
        layout.addLayout(main_hbox)

    def ask_overwrite(self, file_path):
        if self.overwrite_policy == "overwrite_all":
            return True
        elif self.overwrite_policy == "skip_all":
            return False

        msg = QMessageBox(self)
        msg.setWindowTitle("File Exists")
        msg.setText(f"Output file already exists:\n{file_path}\nOverwrite?")
        overwrite = msg.addButton("Overwrite", QMessageBox.YesRole)
        skip = msg.addButton("Skip", QMessageBox.NoRole)
        overwrite_all = msg.addButton("Overwrite All", QMessageBox.AcceptRole)
        skip_all = msg.addButton("Skip All", QMessageBox.RejectRole)
        msg.setIcon(QMessageBox.Warning)
        msg.exec()

        clicked = msg.clickedButton()
        if clicked == overwrite:
            return True
        elif clicked == overwrite_all:
            self.overwrite_policy = "overwrite_all"
            return True
        elif clicked == skip:
            return False
        elif clicked == skip_all:
            self.overwrite_policy = "skip_all"
            return False
        return False

    def apply_icon_style(self):
        is_light = is_windows_light_theme()
        text_color = "#181818" if is_light else "#ffffff"
        self.setStyleSheet(f"* {{ color: {text_color}; }}")

    def open_output_folder(self):
        if self.output_dir and Path(self.output_dir).exists():
            import subprocess, platform

            folder = str(self.output_dir)
            if platform.system() == "Windows":
                subprocess.Popen(f'explorer "{folder}"')
            else:
                subprocess.Popen(["xdg-open", folder])

    def set_input_files(self, file_paths):
        self.input_files = file_paths
        files = [f for f in file_paths if Path(f).is_file()]
        folders = [f for f in file_paths if Path(f).is_dir()]
        if files and folders:
            msg = f"{len(files)} files + {len(folders)} folders selected"
        elif files:
            msg = f"{len(files)} files selected"
        elif folders:
            short_name = self.format_path_short(folders[0])
            msg = (
                f"Folder: {short_name}"
                if len(folders) == 1
                else f"{len(folders)} folders selected"
            )
        else:
            msg = "No valid file/folder selected"
        self.inLabel.setText(msg)

    def format_path_short(self, path, maxlen=48):
        path = str(path)
        if len(path) <= maxlen:
            return path
        return "..." + path[-maxlen:]

    def set_output_folder(self, folder_path):
        """Set output folder from drag & drop"""
        if isinstance(folder_path, list) and len(folder_path) == 1:
            folder_path = folder_path[0]
        if isinstance(folder_path, str):
            folder_path = Path(folder_path)
        if isinstance(folder_path, Path):
            folder_path = folder_path.resolve()
        if not isinstance(folder_path, str):
            folder_path = str(folder_path)
        # Validate folder path
        if not folder_path:
            self.output_dir = ""
            self.outLabel.setText("Output: Not set")
            self.outLabel.setToolTip("No output folder selected")
            return
        if folder_path and Path(folder_path).is_dir():
            self.output_dir = folder_path
            short_path = self.format_path_short(folder_path)
            self.outLabel.setText(f"Output: {short_path}")
            self.outLabel.setToolTip(f"Output folder: {folder_path}")
        else:
            self.output_dir = ""

    def pickInput(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Image(s)",
            "",
            "Images (*.png *.jpg *.jpeg *.webp *.avif *.tif *.tiff)",
        )
        if files:
            self.set_input_files(files)
            return
        folder = QFileDialog.getExistingDirectory(self, "Select Input Folder")
        if folder:
            self.set_input_files([folder])

    def pickOutput(self):
        d = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if d:
            self.set_output_folder(d)

    def update_quality_slider_states(self):
        # PNG & JPEG only
        for fmt in ["PNG", "JPEG"]:
            if fmt in self.qualityWidgets:
                q_slider = self.qualityWidgets[fmt]
                q_slider.setEnabled(not self.losslessWidgets[fmt].isChecked())

    def toggle_resize_controls(self, state):
        if state == 0:
            is_checked = False
        else:
            is_checked = True
        self.resTable.setDisabled(is_checked)
        self.btnAddRes.setDisabled(is_checked)
        self.btnDelRes.setDisabled(is_checked)

    def on_res_table_item_changed(self, item):
        col = item.column()
        if col != 0:
            return
        val = item.text()
        try:
            valid = validate_resize_input(val)
            item.setText(str(valid))
        except ValueError:
            pass

    def addResRow(self, size=256, mode="fit"):
        row = self.resTable.rowCount()
        self.resTable.insertRow(row)
        item = QTableWidgetItem(str(size))
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.resTable.setItem(row, 0, item)
        cb = QComboBox()
        cb.addItems(["fit", "crop", "width", "height"])
        cb.setCurrentText(mode)
        self.resTable.setCellWidget(row, 1, cb)

    def addResDialog(self):
        n, ok = QInputDialog.getText(
            self,
            "Add Resolution",
            "Enter pixel size (2-10000) or percent (1-100%):",
            QLineEdit.Normal,
            text="256",
        )
        if not ok or not n:
            return
        try:
            n_valid = validate_resize_input(n)
        except ValueError as e:
            QMessageBox.critical(self, "Invalid Resolution", str(e))
            return
        self.addResRow(n_valid, "fit")

    def delRes(self):
        selected = self.resTable.selectionModel().selectedRows()
        for idx in sorted([s.row() for s in selected], reverse=True):
            self.resTable.removeRow(idx)

    def get_pixel_size(input_width, input_height, size):
        """Convert size to pixels if needed (handles % or int)."""
        if isinstance(size, str) and size.endswith("%"):
            percent = float(size.rstrip("%")) / 100.0
            base = max(input_width, input_height)
            return int(base * percent)
        else:
            return int(size)

    def runProcess(self):
        # Gather user choices
        input_is_folder = bool(self.input_dir)
        input_is_files = hasattr(self, "input_files") and self.input_files
        if not (input_is_folder or input_is_files):
            QMessageBox.critical(
                self, "Error", "Please select input file(s) or an input folder!"
            )
            return

        if not self.output_dir:
            QMessageBox.critical(self, "Error", "Please select an output folder!")
            return

        formats = [fmt for fmt, cb in self.formatChecks.items() if cb.isChecked()]
        if not formats:
            QMessageBox.critical(
                self, "Error", "Please select at least one output format."
            )
            return

        if self.NoResize.isChecked():
            res_modes = [{"size": "original", "mode": "original"}]
        else:
            res_modes = []
            seen = set()
            for row in range(self.resTable.rowCount()):
                size_item = self.resTable.item(row, 0)
                mode_cb = self.resTable.cellWidget(row, 1)
                size_str = size_item.text().strip()
                try:
                    size = validate_resize_input(size_str)
                    if size in seen:
                        continue
                    seen.add(size)
                    mode = mode_cb.currentText()
                    res_modes.append({"size": size, "mode": mode})
                except ValueError as e:
                    QMessageBox.critical(self, "Error", f"Row {row+1}: {e}")
                    return

        # Normalize input_source: always a list of Path objects
        if hasattr(self, "input_files") and self.input_files:
            input_source = [Path(f) for f in self.input_files if Path(f).exists()]
        elif self.input_dir:
            d = Path(self.input_dir)
            if d.exists() and d.is_dir():
                input_source = [d]
            else:
                QMessageBox.critical(
                    self, "Error", "Input folder does not exist or is not a folder!"
                )
                return
        else:
            QMessageBox.critical(
                self, "Error", "Please select input file(s) or folder!"
            )
            return

        if not input_source:
            QMessageBox.critical(
                self, "Error", "No valid input file(s) or folder found!"
            )
            return

        if hasattr(self, "output_dir") and not self.output_dir:
            QMessageBox.critical(self, "Error", "Please select an output folder!")
            return
        if not Path(self.output_dir).exists():
            QMessageBox.critical(self, "Error", "Output folder does not exist!")
            return
        if not Path(self.output_dir).is_dir():
            QMessageBox.critical(self, "Error", "Output must be a folder!")
            return
        # Ensure input_source is always a list of Path objects
        input_source = (
            input_source if isinstance(input_source, list) else [input_source]
        )

        if not res_modes:
            QMessageBox.critical(self, "Error", "Please set at least one resolution.")
            return

        # Per-format quality and settings
        qmap = {fmt: self.qualityWidgets[fmt].value() for fmt in formats}
        # Lossless settings
        qlossless_map = {fmt: self.losslessWidgets[fmt].isChecked() for fmt in formats}
        # Strip metadata option
        strip_meta = self.stripMeta_check.isChecked()
        recursive = self.recursiveCheck.isChecked()
        thread_count = self.thread_count_spin.value()
        use_gpu = self.gpu_check.isChecked() and self.gpu_info["available"]

        # Start processing in thread
        self.btnGo.setEnabled(False)
        self.status_label.setText("Preparing multi-threaded processing...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.stats_text.setVisible(True)
        self.stats_text.clear()
        self.process_completed = False  # Reset guard flag at start

        # Clean up previous thread if it exists
        if self.processing_thread is not None:
            try:
                self.processing_thread.finished.disconnect(self.processing_finished)
            except TypeError:
                pass
            try:
                self.processing_thread.progress_updated.disconnect(self.update_progress)
            except TypeError:
                pass
            try:
                self.processing_thread.status_updated.disconnect(self.update_status)
            except TypeError:
                pass
            try:
                self.processing_thread.stats_updated.disconnect(self.update_stats)
            except TypeError:
                pass
            try:
                self.processing_thread.error_occurred.disconnect(self.processing_error)
            except TypeError:
                pass
            self.processing_thread.deleteLater()
            self.processing_thread = None

        # Create and configure processor
        processor = ImageProcessor(use_gpu)

        self.processing_thread = ProcessingThread(
            processor,
            input_source,
            self.output_dir,
            res_modes,
            formats,
            qmap,
            qlossless_map,
            strip_meta,
            recursive,
            thread_count,
            use_gpu,
        )
        self.processing_thread.progress_updated.connect(self.update_progress)
        self.processing_thread.status_updated.connect(self.update_status)
        self.processing_thread.stats_updated.connect(self.update_stats)
        self.processing_thread.finished.connect(self.processing_finished)
        self.processing_thread.error_occurred.connect(self.processing_error)
        self.processing_thread.start()

    def update_progress(self, current, total):
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar.setValue(percentage)

    def update_status(self, status):
        self.status_label.setText(status)

    def update_stats(self, stats: FileStats):
        """Update statistics display"""
        compression_ratio = stats.get_compression_ratio()
        size_saved = stats.get_size_saved()

        stats_text = f"""
            Files Processed: {stats.files_processed}
            Original Size: {stats.format_size(stats.original_size)}
            Optimized Size: {stats.format_size(stats.optimized_size)}
            Size Saved: {stats.format_size(size_saved)}
            Compression Ratio: {compression_ratio:.1f}%
        """.strip()

        self.stats_text.setPlainText(stats_text)
        # Collect errors for summary
        if not hasattr(self, "all_errors"):
            self.all_errors = []
        if hasattr(stats, "errors") and stats.errors:
            self.all_errors.extend(stats.errors)

    def processing_finished(self):
        if not self.process_completed:
            # Show error summary if any
            if hasattr(self, "all_errors") and self.all_errors:
                msg = "Some files could not be processed:\n\n" + "\n".join(
                    self.all_errors
                )
                QMessageBox.warning(self, "Processing Errors", msg)
                self.all_errors = []
            self.process_completed = True
            self.btnGo.setEnabled(True)
            self.progress_bar.setVisible(False)
            self.status_label.setText(
                "Multi-threaded optimization completed successfully!"
            )
            QMessageBox.information(
                self,
                "Success",
                "Image optimization completed!\nCheck the statistics for compression details.",
            )

    def processing_error(self, error_msg):
        self.btnGo.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Error occurred during processing")
        QMessageBox.critical(self, "Error", f"Processing failed: {error_msg}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(svg_to_icon(MOHSENI_LOGO, type="icon"))

    win = MainWin()
    win.show()
    sys.exit(app.exec())
