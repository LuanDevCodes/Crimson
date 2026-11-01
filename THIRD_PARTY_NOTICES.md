# Third-Party Notices & Open Source Licenses

Project **Crimson** relies on open-source software and graphical assets created by the community. This document lists the third-party components, their licenses, and their respective repositories.

---

## 1. Software Libraries & Engines

| Component | License | Repository / Source |
|---|---|---|
| **yt-dlp** | The Unlicense (Public Domain) | [https://github.com/yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp) |
| **PySide6 (Qt for Python)** | LGPLv3 / GPLv3 | [https://wiki.qt.io/Qt_for_Python](https://wiki.qt.io/Qt_for_Python) |
| **Pillow (PIL Fork)** | MIT-CMU License | [https://github.com/python-pillow/Pillow](https://github.com/python-pillow/Pillow) |
| **FFmpeg (BtbN Builds)** | GPLv2+ / LGPLv2.1+ | [https://github.com/BtbN/FFmpeg-Builds](https://github.com/BtbN/FFmpeg-Builds) |

> **Note on FFmpeg & PySide6 Distribution:**
> - On Linux, Crimson invokes the system's externally installed `ffmpeg` binary via standard process execution (`subprocess`) and does not bundle FFmpeg inside the binary.
> - When distributing pre-compiled Windows archives containing `ffmpeg.exe` builds compiled with `--enable-gpl` (such as BtbN GPL builds), the combined distribution is subject to the terms of the **GNU General Public License (GPLv3)**, which guarantees users access to the complete source code of Crimson and the corresponding FFmpeg source repository.

---

## 2. Graphical Icons (Flaticon)

All interface icons located in the `Icons/` directory are third-party assets used under the Flaticon Free License with author attribution.

> **Important License Clarification on Icons:**  
> These graphical icon assets are **not** licensed under the GNU General Public License v3.0 (GPLv3). They remain the intellectual property of their respective creators on Flaticon. Any redistribution, modification, or reuse of these icon files must comply with Flaticon's licensing terms and author attribution requirements.

Author attributions:
- **Question mark** — created by [Magnific - Flaticon](https://www.flaticon.com/br/icones-gratis/ponto-de-interrogacao)
- **Trash** — created by [Mayor Icons - Flaticon](https://www.flaticon.com/br/icones-gratis/desperdicio)
- **Resume / Play** — created by [sonnycandra - Flaticon](https://www.flaticon.com/br/icones-gratis/botao-play)
- **Pause** — created by [Slidicon - Flaticon](https://www.flaticon.com/br/icones-gratis/pausa)
- **Settings** — created by [Pixel perfect - Flaticon](https://www.flaticon.com/br/icones-gratis/configuracoes)
- **Community** — created by [Soremba - Flaticon](https://www.flaticon.com/br/icones-gratis/comunidade)
- **Github** — created by [riajulislam - Flaticon](https://www.flaticon.com/br/icones-gratis/github)
- **Clean / Broom** — created by [Us and Up - Flaticon](https://www.flaticon.com/br/icones-gratis/vassoura)