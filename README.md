# MM Image Optimizer

![GitHub release (latest by date)](https://img.shields.io/github/v/release/mohseni-mr/MMImageOptimizer?style=for-the-badge)
![GitHub stars](https://img.shields.io/github/stars/mohseni-mr/MMImageOptimizer?style=for-the-badge)
![GitHub issues](https://img.shields.io/github/issues/mohseni-mr/MMImageOptimizer?style=for-the-badge)
![License](https://img.shields.io/github/license/mohseni-mr/MMImageOptimizer?style=for-the-badge)

---

<p align="center">
    <img width="96" alt="MM Image Optimizer Logo" src='https://raw.githubusercontent.com/mohseni-mr/MMImageOptimizer/refs/heads/main/mohseni.ico'/>
</p>

<h1 align="center">MM Image Optimizer</h1>

<p align="center">The Ultimate Free & Fast Image Optimizer for Windows</p>

---

## 🚀 Features

- **Batch optimize images** for web, apps, and archives
- **Drag & drop** folders or files
- **No resize** or advanced multi-resolution output
- **PNG, JPEG, WebP, AVIF** for output
- **Multiple output option**
- **Lossless & lossy modes**
- **Metadata stripping** for privacy & size
- **Multi-threaded** for maximum speed
- **GPU acceleration** (if available)
- **Modern, easy-to-use interface**
- **Professional Windows installer**
- **No telemetry, no ads, 100% free**

---

## 🖼️ Who is this for?

- **Regular users:**
  - Want to shrink images for email, web, or storage
  - Need a simple, safe, and fast tool
  - Don't want to mess with settings or command lines
- **Photographers, designers, developers:**
  - Need advanced control over quality, format, and size
  - Want batch processing and automation
  - Care about image quality and file size

---

## 📥 Download & Install

<a href="https://mohs.one/imgop">
  <img src="https://img.shields.io/badge/Direct%20Download-Cloudflare%20R2-blue?style=for-the-badge" alt="Direct Download"/>
</a>

**[Download the latest release from GitHub](https://github.com/mohseni-mr/MMImageOptimizer/releases/latest)**

or use the always-latest direct link:

👉 **[https://mohs.one/imgop](https://mohs.one/imgop)**

1. Download and run the installer (`MMImageOptimizer_Setup.exe`)
2. The app will be installed to:
   - `C:\Users\<username>\AppData\Local\MMImageOptimizer`
   - You **cannot change the install folder** (for reliability)
3. Optionally create Start Menu, Desktop, or Quick Launch shortcuts
4. Launch from Start Menu, Desktop, or the installed folder

> **No admin rights required!**

---

## 🛠️ How to Use

1. **Open MM Image Optimizer**
2. **Drag & drop** images or folders, or use the folder/file picker
3. **Choose output folder**
4. **Select output formats** (PNG, JPEG, WebP, AVIF)
5. **Set quality, lossless/lossy, and resolutions**
6. **Click "Start Optimization"**
7. Wait for the batch to finish. See stats and error summary at the end.

### Tips

- Use "No Resize" for original size, or add custom resolutions (e.g., 256px, 50%)
- Enable "Strip Metadata" for privacy and smaller files
- Enable GPU acceleration if available for faster processing

---

## 📦 Supported Formats & Tech

- **Input:** PNG, JPEG, WebP, AVIF, TIFF, BMP, GIF, and more
- **Output:** PNG, JPEG (jpegli), WebP, AVIF
- **Resizing:** Multi-resolution, fit/crop/width/height modes
- **Metadata:** Optionally strip all EXIF/IPTC/XMP
- **Threading:** Multi-core, multi-threaded batch processing
- **GPU:** OpenCL/CUDA acceleration for ImageMagick (if available for resizing)

## 📦 Supported Formats & Tech

### <span style="color:#4169e1;font-weight:bold">Supported Input Formats</span>

<details>
<summary><b>Click to see full list</b></summary>

<ul>
  <li><b>PNG</b> (.png, .png8, .png16, .png24, .png32, .png48, .png64)</li>
  <li><b>JPEG</b> (.jpg, .jpeg, .jpe)</li>
  <li><b>WebP</b> (.webp)</li>
  <li><b>AVIF</b> (.avif)</li>
  <li><b>BMP</b> (.bmp)</li>
  <li><b>GIF</b> (.gif)</li>
  <li><b>TIFF</b> (.tif, .tiff)</li>
  <li><b>HEIC/HEIF</b> (.heic, .heif)</li>
  <li><b>JPEG 2000</b> (.jp2, .j2k, .j2c)</li>
  <li><b>JPEG XL</b> (.jxl)</li>
  <li><b>DDS</b> (.dds)</li>
  <li><b>PSD</b> (.psd)</li>
  <li><b>TGA</b> (.tga)</li>
  <li><b>ICO</b> (.ico)</li>
</ul>

<i>And many more common raster image formats supported by ImageMagick.</i>

</details>

- **Output:** PNG, JPEG (jpegli), WebP, AVIF
- **Resizing:** Multi-resolution, fit/crop/width/height modes
- **Metadata:** Optionally strip all EXIF/IPTC/XMP
- **Threading:** Multi-core, multi-threaded batch processing
- **GPU:** OpenCL/CUDA acceleration for ImageMagick (if available)
  - [oxipng](https://github.com/shssoichiro/oxipng) (for PNG optimization)
  - [pngquant](https://pngquant.org/) (for lossy PNG)
  - [exiftool](https://exiftool.org/) (for metadata removal)
- **Installer:** Built with [Inno Setup](https://jrsoftware.org/isinfo.php)
- **GUI:** Built with [PySide6 (Qt for Python)](https://doc.qt.io/qtforpython/)
- **Portable binaries** are bundled in the installer for reliability
- **No internet required** after install

---

## 📝 Credits & Acknowledgments

- **ImageMagick** — [imagemagick.org](https://imagemagick.org/)
- **jpegli** — [github.com/google/jpegli](https://github.com/google/jpegli)
- **libwebp/cwebp** — [developers.google.com/speed/webp](https://developers.google.com/speed/webp)
- **libavif/avifenc** — [github.com/AOMediaCodec/libavif](https://github.com/AOMediaCodec/libavif)
- **oxipng** — [github.com/shssoichiro/oxipng](https://github.com/shssoichiro/oxipng)
- **pngquant** — [pngquant.org](https://pngquant.org/)
- **exiftool** — [exiftool.org](https://exiftool.org/)
- **PySide6** — [doc.qt.io/qtforpython/](https://doc.qt.io/qtforpython/)
- **Inno Setup** — [jrsoftware.org/isinfo.php](https://jrsoftware.org/isinfo.php)

> All trademarks and copyrights belong to their respective owners. This project simply bundles and orchestrates these tools for user convenience.

---

## 💡 FAQ

**Q: Why can't I change the install folder?**

> For reliability, all binaries are loaded from a fixed path. This avoids path issues and makes support easier.

**Q: Is this really free?**

> Yes! 100% free, no ads, no telemetry, no registration.

**Q: Is my data private?**

> Yes. All processing is local. No files are uploaded or tracked.

**Q: Can I use this for commercial work?**

> Yes, but see the licenses of the bundled tools for any restrictions.

---

## 🧑‍💻 For Developers

- **Source code:** See [`main.py`](main.py)
- **Installer script:** See [`setup.iss`](setup.iss)
- **Requirements:** See [`requirements.txt`](requirements.txt)
- **How to build:**
  1. Install Python 3.10+ and PySide6
  2. Build the app with Nuitka or PyInstaller (see `compile-nuitka.bat`)
  3. Use Inno Setup to package the installer
- **Contributions welcome!**

---

## 📣 Connect

- [Author Website](https://mohsenicreative.com)
- [GitHub Issues](https://github.com/mohseni-mr/MMImageOptimizer/issues)
- [Releases](https://github.com/mohseni-mr/MMImageOptimizer/releases)

---

---

## 📝 License

This project is licensed under the **GNU General Public License v3.0 or later (GPLv3+)**. See [`LICENSE.txt`](LICENSE.txt) for full terms.

> **Note:** Bundled binaries (ImageMagick, jpegli, cwebp, avifenc, oxipng, pngquant, exiftool, etc.) are distributed under their respective open source licenses. Please refer to their official sites for more information.

---

<p align="center">
  <b>MM Image Optimizer — Fast, Free, and Professional Image Optimization for Everyone!</b>
</p>
