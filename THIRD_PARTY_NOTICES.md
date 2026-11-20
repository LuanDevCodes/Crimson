# Third-Party Notices & Open Source Licenses

Project **Crimson** relies on open-source software and graphical assets created by the community. This document lists the third-party components, their licenses, and where their source code can be obtained.

---

## 0. Crimson

Copyright (C) 2026 LuanDevCodes

Crimson is free software: you can redistribute it and/or modify it under the terms of the **GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version** (see [LICENSE](LICENSE)).

Crimson is distributed in the hope that it will be useful, but **WITHOUT ANY WARRANTY**; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

Corresponding source code: [https://github.com/LuanDevCodes/Crimson](https://github.com/LuanDevCodes/Crimson) (each release has a matching Git tag).

---

## 1. Software Libraries & Engines

The full license texts are in the [`licenses/`](licenses) folder, which is also shipped inside the pre-compiled Windows and Linux executables.

| Component | License | License file | Source |
|---|---|---|---|
| **yt-dlp** | Unlicense | `licenses/yt-dlp-LICENSE.txt` | [github.com/yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp) |
| **yt-dlp-ejs** | Unlicense AND MIT AND ISC | `licenses/yt-dlp-ejs-LICENSE.txt` | [github.com/yt-dlp/ejs](https://github.com/yt-dlp/ejs) |
| **PySide6 / Shiboken6 (Qt for Python)** | LGPL-3.0-only (used under the LGPL) | `licenses/PySide6-Qt-LGPL-3.0.txt` + [LICENSE](LICENSE) (GPL-3.0 text referenced by the LGPL) | [code.qt.io/pyside](https://code.qt.io/cgit/pyside/pyside-setup.git/) |
| **Pillow** (includes libjpeg, zlib, libpng, FreeType, etc.) | MIT-CMU (+ bundled library licenses) | `licenses/Pillow-LICENSE.txt` | [github.com/python-pillow/Pillow](https://github.com/python-pillow/Pillow) |
| **certifi** | MPL-2.0 | `licenses/certifi-LICENSE.txt` | [github.com/certifi/python-certifi](https://github.com/certifi/python-certifi) |
| **requests** | Apache-2.0 | `licenses/requests-LICENSE.txt`, `licenses/requests-NOTICE.txt` | [github.com/psf/requests](https://github.com/psf/requests) |
| **urllib3** | MIT | `licenses/urllib3-LICENSE.txt` | [github.com/urllib3/urllib3](https://github.com/urllib3/urllib3) |
| **idna** | BSD-3-Clause | `licenses/idna-LICENSE.txt` | [github.com/kjd/idna](https://github.com/kjd/idna) |
| **charset-normalizer** | MIT | `licenses/charset-normalizer-LICENSE.txt` | [github.com/jawah/charset_normalizer](https://github.com/jawah/charset_normalizer) |
| **brotli** | MIT | `licenses/brotli-LICENSE.txt` | [github.com/google/brotli](https://github.com/google/brotli) |
| **mutagen** | GPL-2.0-or-later | `licenses/mutagen-COPYING.txt` | [github.com/quodlibet/mutagen](https://github.com/quodlibet/mutagen) |
| **pycryptodomex** | BSD-2-Clause / Public Domain | `licenses/pycryptodomex-LICENSE.txt` | [github.com/Legrandin/pycryptodome](https://github.com/Legrandin/pycryptodome) |
| **websockets** | BSD-3-Clause | `licenses/websockets-LICENSE.txt` | [github.com/python-websockets/websockets](https://github.com/python-websockets/websockets) |
| **curl_cffi** (bundles libcurl-impersonate) | MIT (+ bundled library licenses) | `licenses/curl_cffi-LICENSE.txt` | [github.com/lexiforest/curl_cffi](https://github.com/lexiforest/curl_cffi) |
| **cffi** | MIT-0 | `licenses/cffi-LICENSE.txt` | [github.com/python-cffi/cffi](https://github.com/python-cffi/cffi) |
| **pycparser** | BSD-3-Clause | `licenses/pycparser-LICENSE.txt` | [github.com/eliben/pycparser](https://github.com/eliben/pycparser) |
| **FFmpeg (BtbN Builds, Windows only)** | GPL-3.0-or-later (GPL build) | see section 3 | see section 3 |

> **Notes:**
> - Qt itself contains third-party components with their own licenses, listed at [doc.qt.io/qt-6/licenses-used-in-qt.html](https://doc.qt.io/qt-6/licenses-used-in-qt.html).
> - curl_cffi ships a build of libcurl-impersonate (curl, BoringSSL, nghttp2, brotli, zstd and others); their licenses are listed in the curl_cffi and [curl-impersonate](https://github.com/lexiforest/curl-impersonate) repositories.
> - The Python packages above are only bundled inside the pre-compiled executables (PyInstaller). When Crimson is installed with `pip`, Meson or Flatpak, they are installed separately with their own license files.

---

## 2. Graphical Assets

### Interface icons: Material Symbols (Google)
The interface icons in `crimson/Icons/` (question mark, delete, play, pause, settings, groups, cleaning, folder, refresh and insert text) are **[Material Symbols](https://github.com/google/material-design-icons)** by Google, rounded style, licensed under the **Apache License 2.0** (`licenses/Material-Symbols-Apache-2.0.txt`). They were converted from SVG to PNG; the app recolors them at runtime to match the active theme.

### GitHub logo
`crimson/Icons/github.png` and `crimson/Icons/github_branco.png` are the official GitHub Invertocat logo (black and white versions, the white one used on dark themes), downloaded from [brand.github.com](https://brand.github.com/), converted from SVG to PNG and used unmodified only to link to GitHub repositories. The GitHub logo is a trademark of GitHub, Inc. and is **not** covered by Crimson's GPL license; its use follows GitHub's logo guidelines.

### Application icon
`crimson/Icons/Crimson.svg` and `crimson/Icons/Crimson.png` were created by LuanDevCodes and are distributed under the same license as Crimson (GPL-3.0-or-later).

---

## 3. FFmpeg (pre-compiled Windows executable only)

- **Linux (pip, Meson, Flatpak and the Linux executable):** Crimson does not bundle FFmpeg. It runs the `ffmpeg` program already installed on the system as a separate process.
- **Windows executable (`Crimson.exe`):** it bundles `ffmpeg.exe` from the **BtbN FFmpeg-Builds** project, GPL variant (`win64-gpl`). This build is licensed under the **GNU General Public License version 3 or later**, because it is compiled with `--enable-gpl --enable-version3`.

**Corresponding source code for the bundled FFmpeg:** each Crimson Windows release states the exact FFmpeg build it contains (file `FFMPEG_VERSION.txt` generated by `Compile_project/Windows.bat`) and attaches the matching FFmpeg source archive to the same GitHub release. The build scripts used by BtbN, including the exact versions of every library compiled into FFmpeg, are available at [github.com/BtbN/FFmpeg-Builds](https://github.com/BtbN/FFmpeg-Builds). The FFmpeg source code is also available at [ffmpeg.org/download.html](https://ffmpeg.org/download.html).
