# Project CARS 1 - Mod Pack Installer for Linux (CachyOS / Arch / Proton)

> 🇮🇹 **[Versione italiana disponibile qui](README_IT.md)**

[![OS - CachyOS / Arch Linux](https://img.shields.io/badge/OS-CachyOS%20%7C%20Arch%20Linux-blue?logo=archlinux)](https://cachyos.org)
[![Proton - Compatible](https://img.shields.io/badge/Compatibility-Steam%20Proton-brightgreen?logo=steam)](https://github.com/ValveSoftware/Proton)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-yellow?logo=python)](https://www.python.org/)
[![License - MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An automated tool to safely and cleanly install, manage, and uninstall the community **Ultimate Mod Pack** (and add-on vehicle mods) for **Project CARS 1** on **Linux (CachyOS, Arch, SteamOS / Steam Deck, Ubuntu)** running via **Steam Proton**.

---

## 📥 Mod Pack Download & Original References

The original mod pack was curated, configured, and tested by [**Random12multi**](https://www.reddit.com/user/Random12multi/):
- 🌐 **Official Reddit Thread**: [r/pcars: I made a mod pack for Project CARS 1 that adds 50+ cars...](https://www.reddit.com/r/pcars/comments/82u8kb/i_made_a_mod_pack_for_project_cars_1_that_adds_50/)
- 💾 **Mod Pack Download (MediaFire, ~6.5 GB)**: [Project Cars 1 Ultimate Mod Pack.rar](http://www.mediafire.com/file/31sbfx1sm8tdxpk/Project%20Cars%201%20Ultimate%20Mod%20Pack.rar)
- 👤 **Mod Pack Author**: [u/Random12multi on Reddit](https://www.reddit.com/user/Random12multi/)

---

## 🎯 The Problem Solved (Linux & Case-Sensitivity)

On Windows (NTFS), the file system is case-insensitive. Legacy modding tools like **JSGME** (JoneSoft Generic Mod Enabler) create and overwrite directory trees without regard to uppercase or lowercase names.

On Linux (Btrfs / ext4), files and directories are **strictly case-sensitive**. Extracting or copying mod files with folder paths like `vehicles/...`, `audio/...`, or `gui/...` into the game directory results in duplicate, parallel directories alongside the game's native `Vehicles/`, `Audio/`, and `GUI/`. Under Proton/Wine, this causes the game engine to fail to resolve 3D models, textures, liveries, and audio banks, resulting in missing vehicles or instant game crashes.

### Key Features of this Installer:
1. **Recursive Case-Insensitive Path Resolution**: Automatically inspects existing game directories on disk and routes all files into the existing canonical folders (e.g. `Vehicles/`, `Audio/`, `GUI/`, `Render/`) without creating duplicate case variants.
2. **Instant Copy-on-Write (Btrfs / XFS reflink)**: Takes advantage of modern Linux filesystems (such as Btrfs on CachyOS) to copy over 20,000 files in seconds with zero initial disk space duplication.
3. **Automated Vanilla Backup**: Automatically detects and backs up only the genuine vanilla game files that are overwritten (18 boot & GUI files) into `.backup_vanilla/`.
4. **1-Click Clean Uninstallation**: Reverts the game back to 100% untouched vanilla state, deleting all mod additions and restoring original files.
5. **Auto Steam Detection**: Finds your `pCars` installation across native Steam libraries and Flatpak distributions.

---

## 🚀 Requirements

- **Operating System**: CachyOS, Arch Linux, SteamOS / Steam Deck, or any modern Linux distribution with Steam.
- **Python**: 3.8 or higher (pre-installed on CachyOS and Arch).
- **Project CARS 1**: Steam version (GOTY edition v11.2 / 64-bit recommended).
- **Proton**: `proton-cachyos`, `Proton Experimental`, or `Proton GE / Hotfix`.

---

## 📦 Quick Start

### 1. Clone this repository
```bash
git clone https://github.com/davidetsf-oss/cars1-mod-pack-installer-cachyos.git
cd cars1-mod-pack-installer-cachyos
```

### 2. Download and extract the Mod Pack
Download the archive from the [MediaFire link](http://www.mediafire.com/file/31sbfx1sm8tdxpk/Project%20Cars%201%20Ultimate%20Mod%20Pack.rar) and extract it. The installer will automatically scan common locations such as:
- The current working directory
- `~/Scaricati/Project Cars 1 Ultimate Mod Pack`
- `~/Downloads/Project Cars 1 Ultimate Mod Pack`

*(You can also pass a custom source path using `--source`)*.

### 3. Run the installer
```bash
./install.sh
```
*Or with explicit paths:*
```bash
python3 pcars_mod_installer.py install --source "/path/to/ModPack" --target "/path/to/pCars"
```

---

## 🛠️ CLI Commands & Utilities

| Command | Description |
|---|---|
| `./list.sh` | Lists all available cars grouped by brand and category, showing installation status |
| `./install.sh` | Starts installation (prompts whether to install all or choose via interactive menu) |
| `./install.sh --all` | Directly installs all 56 mods (70+ cars) |
| `./install.sh --interactive` | Interactive terminal UI menu to pick cars by brand, category, or individual vehicle |
| `./install.sh --brand ferrari,porsche` | Selectively installs only specified brands (e.g. Ferrari, Porsche, Audi, BMW...) |
| `./install.sh --category gt3,gt1` | Selectively installs only specified classes (GT3, GT1, Hypercars, Tuners...) |
| `./status.sh` | Displays current mod status, active cars list, and installation date |
| `./uninstall.sh` | Interactive uninstallation prompt (choose between full or selective removal) |
| `./uninstall.sh --all` | Uninstalls everything and restores the game back to 100% untouched vanilla state |
| `./uninstall.sh --interactive` | Interactive menu to choose specific cars to remove while keeping others |
| `./uninstall.sh --brand <brand>` | Removes only cars of a specific brand (e.g. `./uninstall.sh --brand ferrari`) |
| `python3 pcars_mod_installer.py install --dry-run` | Simulates actions without writing changes to disk |

---

## 🏎️ Vehicle Roster (70+ Cars Included)

The pack configures 56 distinct mod categories in the tested dependency order (`JSGME.ini`), including:
- **Ferrari**: 250 GTO, 458 Italia, 488 GT3, 599 GTB, 812 Superfast, F40 '87, F430 Scuderia, F430C GT3, LaFerrari.
- **Porsche**: 911R '16, 918 Spyder, 997 GT3 Cup, GT3RS '16.
- **McLaren**: 650S GT3, 688HS, P1 GTR.
- **Lamborghini**: Gallardo LP560-4, Huracán GT3, Murciélago R-SV GT1.
- **Audi**: A4 DTM, R8 LMS 2015, R8 Spyder V10, S3, RS4.
- **FIA GT1 Pack**: Maserati MC12, Ford GT GT1, Corvette C6.R, Aston Martin DBR9, Nissan GT-R GT1, Lamborghini Murciélago.
- **JDM & Tuners**: Toyota Supra (Stage 1 & 4), Nissan Skyline R34 Tuner, Silvia S15 Tuner, Mazda RX-7 Spirit R, Honda S2000 AP1.
- **Hot Hatch Class & GT3 Class Expansion**.

---

## 🎮 How to Play in Game

1. Launch **Project CARS** normally from your Steam Library.
2. Navigate to **Quick Race** or **Free Practice**.
3. Select your car: all custom vehicles appear with functional Motec displays, cockpit views, and custom engine sounds.
4. For multi-class racing with custom AI opponents, choose the corresponding class or custom categories.

> [!WARNING]
> Official Career Mode does not recognize unofficial community class tags and may conflict with custom grid configurations. It is strongly recommended to enjoy modded vehicles in **Quick Race**, **Custom Race Weekend**, and **Time Trial** modes.

---

## 📂 Project Architecture

```
├── pcars_mod_installer.py  # Core Python engine (Steam auto-detect, CoW reflink, case-folding resolution)
├── install.sh              # Quick Bash wrapper for installation
├── uninstall.sh            # Quick Bash wrapper for uninstallation
├── status.sh               # Quick Bash wrapper for status inspection
├── LICENSE                 # MIT License
├── README.md               # English documentation (default)
└── README_IT.md            # Italian documentation
```

---

## ⚖️ License & Acknowledgements

- **Installer Tool**: Released under the [MIT License](LICENSE).
- **Mod Pack Curator**: Curated and packed by [Random12multi](https://www.reddit.com/user/Random12multi/) ([Reddit Thread](https://www.reddit.com/r/pcars/comments/82u8kb/i_made_a_mod_pack_for_project_cars_1_that_adds_50/) | [MediaFire](http://www.mediafire.com/file/31sbfx1sm8tdxpk/Project%20Cars%201%20Ultimate%20Mod%20Pack.rar)).
- **Mod Assets**: 3D vehicle models, sounds, physics configurations, and skins belong to their respective creators within the Project CARS modding community (Slightly Mad Studios, ThunderFlash, JDougNY, KAOS Modding Team, and individual contributors).
