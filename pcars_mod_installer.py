#!/usr/bin/env python3
"""
Project CARS 1 - Mod Pack Installer & Manager for Linux (CachyOS / Arch / Proton)
================================================================================
Author: Davide & Antigravity (AI Assistant)
License: MIT

Mod Pack Credits & References:
- Author: Random12multi (https://www.reddit.com/user/Random12multi/)
- Reddit Thread: https://www.reddit.com/r/pcars/comments/82u8kb/i_made_a_mod_pack_for_project_cars_1_that_adds_50/
- Mod Pack Download: http://www.mediafire.com/file/31sbfx1sm8tdxpk/Project%20Cars%201%20Ultimate%20Mod%20Pack.rar
"""

import os
import sys
import re
import json
import shutil
import argparse
import subprocess
from datetime import datetime

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def colorize(text, color):
    if sys.stdout.isatty():
        return f"{color}{text}{Colors.END}"
    return text

def find_steam_libraries():
    """Finds all Steam library folders from libraryfolders.vdf across known Steam paths."""
    vdf_candidates = [
        os.path.expanduser("~/.local/share/Steam/steamapps/libraryfolders.vdf"),
        os.path.expanduser("~/.steam/steam/steamapps/libraryfolders.vdf"),
        os.path.expanduser("~/.var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps/libraryfolders.vdf"),
    ]
    libraries = set()
    for vdf in vdf_candidates:
        if os.path.isfile(vdf):
            try:
                with open(vdf, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        match = re.search(r'"path"\s+"([^"]+)"', line)
                        if match:
                            path = match.group(1).replace("\\\\", "/")
                            if os.path.isdir(path):
                                libraries.add(path)
            except Exception:
                pass
    for p in [
        os.path.expanduser("~/.local/share/Steam"),
        os.path.expanduser("~/.steam/steam"),
        os.path.expanduser("~/.var/app/com.valvesoftware.Steam/.local/share/Steam")
    ]:
        if os.path.isdir(p):
            libraries.add(p)
    return list(libraries)

def auto_detect_game_path():
    """Detects the Project CARS installation path on the system."""
    for lib in find_steam_libraries():
        candidate = os.path.join(lib, "steamapps", "common", "pCars")
        if os.path.isdir(candidate) and (
            os.path.isfile(os.path.join(candidate, "pCARS64.exe")) or
            os.path.isfile(os.path.join(candidate, "pCARS.exe"))
        ):
            return candidate
    return None

def auto_detect_mod_source():
    """Tries to find where the Ultimate Mod Pack is stored."""
    candidates = [
        os.getcwd(),
        os.path.dirname(os.path.abspath(__file__)),
        os.path.expanduser("~/Scaricati/Project Cars 1 Ultimate Mod Pack"),
        os.path.expanduser("~/Downloads/Project Cars 1 Ultimate Mod Pack"),
        os.path.expanduser("~/Scaricati/Ultimate Mod Pack"),
        os.path.expanduser("~/Downloads/Ultimate Mod Pack"),
    ]
    for c in candidates:
        if os.path.isdir(os.path.join(c, "MODS")) and os.path.isfile(os.path.join(c, "mods.txt")):
            return c
    return None

def parse_mod_order(source_dir):
    """Parses mod order from JSGME.ini or falls back to directory listing."""
    ini_path = os.path.join(source_dir, "MODS", "JSGME.ini")
    if os.path.exists(ini_path):
        mods = []
        try:
            with open(ini_path, "r", encoding="utf-8", errors="ignore") as f:
                in_mods = False
                for line in f:
                    line = line.strip()
                    if line == "[MODS]":
                        in_mods = True
                        continue
                    if in_mods:
                        if line.startswith("["):
                            break
                        if "=" in line:
                            mod_name, idx = line.split("=", 1)
                            mods.append((int(idx), mod_name.strip()))
            mods.sort()
            return [m for _, m in mods]
        except Exception:
            pass
    mods_dir = os.path.join(source_dir, "MODS")
    subdirs = [d for d in os.listdir(mods_dir) if not d.startswith("!") and os.path.isdir(os.path.join(mods_dir, d))]
    if "Custom_Grid_Tool" in subdirs:
        subdirs.remove("Custom_Grid_Tool")
        return ["Custom_Grid_Tool"] + sorted(subdirs)
    return sorted(subdirs)

def classify_mod(name):
    """Classifies a mod into Brand and Category."""
    low = name.lower()
    if "custom_grid_tool" in low:
        return ("Core Engine", "Core")

    # Brand
    if "ferrari" in low: brand = "Ferrari"
    elif "porsche" in low or "ruf" in low: brand = "Porsche / RUF"
    elif "mclaren" in low: brand = "McLaren"
    elif "lambo" in low: brand = "Lamborghini"
    elif "audi" in low: brand = "Audi"
    elif "bmw" in low or "alpina" in low: brand = "BMW"
    elif "nissan" in low: brand = "Nissan"
    elif "toyota" in low: brand = "Toyota"
    elif "aston" in low: brand = "Aston Martin"
    elif "mercedes" in low: brand = "Mercedes-Benz"
    elif "ford" in low: brand = "Ford"
    elif "lotus" in low: brand = "Lotus"
    elif "mazda" in low: brand = "Mazda"
    elif "honda" in low: brand = "Honda"
    elif "corvette" in low or "chevrolet" in low: brand = "Chevrolet"
    elif "lexus" in low: brand = "Lexus"
    elif "maserati" in low: brand = "Maserati"
    elif "pagani" in low: brand = "Pagani"
    elif "renault" in low: brand = "Renault"
    elif "fia gt1" in low: brand = "FIA GT1"
    elif "hot hatch" in low: brand = "Hot Hatch"
    else: brand = "Other"

    # Category
    if "gt3" in low: cat = "GT3"
    elif "gt1" in low: cat = "GT1"
    elif "dtm" in low: cat = "Touring / DTM"
    elif "tuner" in low or "spirit_r" in low or "s2000" in low or "xtrem" in low or "x tune" in low: cat = "Tuner / JDM"
    elif "hot hatch" in low: cat = "Hot Hatch"
    elif "250 gto" in low or "f40" in low: cat = "Classics"
    elif "laferrari" in low or "p1" in low or "918" in low or "812" in low or "599" in low or "zonda" in low or "lfa" in low or "slr" in low: cat = "Hypercars"
    else: cat = "Sports / GT"

    return (brand, cat)

def resolve_case_insensitive_path(base_dir, rel_path):
    """
    Given a base directory and a relative path (e.g. 'vehicles/audi/car.crd'),
    resolves each segment against existing files/directories on disk case-insensitively.
    """
    parts = os.path.normpath(rel_path).split(os.sep)
    current_path = base_dir
    resolved_parts = []
    for part in parts:
        if part in (".", ""):
            continue
        part_lower = part.lower()
        matched = False
        if os.path.exists(current_path):
            try:
                for entry in os.listdir(current_path):
                    if entry.lower() == part_lower:
                        current_path = os.path.join(current_path, entry)
                        resolved_parts.append(entry)
                        matched = True
                        break
            except Exception:
                pass
        if not matched:
            current_path = os.path.join(current_path, part)
            resolved_parts.append(part)
    return current_path, os.path.join(*resolved_parts)

def fast_copy(src, dest, dry_run=False):
    """Reflink (Copy-on-Write) fast copy on Btrfs/XFS/ZFS with fallback to copy2."""
    if dry_run:
        return True
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    try:
        ret = subprocess.run(["cp", "--reflink=auto", "-p", src, dest], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if ret.returncode == 0:
            return True
    except Exception:
        pass
    shutil.copy2(src, dest)
    return True

def parse_mods_txt_mapping(source_dir, all_mods):
    """Maps each CRD entry in mods.txt to the specific mod that provides it."""
    mods_txt_path = os.path.join(source_dir, "mods.txt")
    if not os.path.isfile(mods_txt_path):
        return "", [], {}

    with open(mods_txt_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    header_match = re.match(r'^(.*?)(?=[vV]ehicles[^\n]+\.crd)', content, re.DOTALL)
    header = header_match.group(1) if header_match else ""
    entries = re.findall(r'([vV]ehicles[^\n]+\.crd.*?(?=[vV]ehicles[^\n]+\.crd|\Z))', content, re.DOTALL)

    crd_to_mod = {}
    for m in all_mods:
        m_dir = os.path.join(source_dir, "MODS", m)
        if not os.path.isdir(m_dir): continue
        for root, _, files in os.walk(m_dir):
            for file in files:
                if file.lower().endswith('.crd'):
                    crd_to_mod[file.lower()] = m

    entry_to_mod = {}
    for e in entries:
        first_line = e.strip().split("\n")[0]
        crd = re.split(r"[\\/]", first_line)[-1].strip().lower()
        if crd in crd_to_mod:
            entry_to_mod[e.strip()] = crd_to_mod[crd]

    return header, entries, entry_to_mod

def generate_filtered_mods_txt(header, entries, entry_to_mod, active_mods):
    """Generates mods.txt content containing only entries for active mods."""
    active_set = set(active_mods)
    selected_blocks = []
    for e in entries:
        e_clean = e.strip()
        mod_owner = entry_to_mod.get(e_clean)
        if mod_owner and mod_owner in active_set:
            selected_blocks.append(e_clean)
    return header.strip() + "\n\n" + "\n\n".join(selected_blocks) + "\n"

def load_manifest(target_dir):
    """Loads existing manifest from target_dir."""
    manifest_path = os.path.join(target_dir, ".modpack_manifest.json")
    if os.path.isfile(manifest_path):
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return None

def save_manifest(target_dir, manifest_data):
    """Saves manifest to target_dir."""
    manifest_path = os.path.join(target_dir, ".modpack_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

def write_uninstaller_script(target_dir):
    """Writes a standalone bash uninstaller into the game directory."""
    uninstaller_path = os.path.join(target_dir, "uninstall_mods.sh")
    with open(uninstaller_path, "w", encoding="utf-8") as f:
        f.write("""#!/usr/bin/env bash
# Project CARS 1 Standalone Uninstaller
set -e
GAME_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST="$GAME_DIR/.modpack_manifest.json"
BACKUP_DIR="$GAME_DIR/.backup_vanilla"

if [ ! -f "$MANIFEST" ]; then
    echo "Errore: Nessun manifest mod trovato in $MANIFEST"
    exit 1
fi

echo "Ripristino dei file di gioco vanilla originali..."
python3 -c "
import os, json, shutil

game_dir = '$GAME_DIR'
manifest_path = '$MANIFEST'
backup_dir = '$BACKUP_DIR'

with open(manifest_path, 'r') as f:
    manifest = json.load(f)

# 1. Restore vanilla backups
backed_up = manifest.get('backed_up_vanilla_files', {})
if isinstance(backed_up, list):
    for orig_rel in backed_up:
        b_file = os.path.join(backup_dir, orig_rel)
        t_file = os.path.join(game_dir, orig_rel)
        if os.path.exists(b_file):
            shutil.copy2(b_file, t_file)
elif isinstance(backed_up, dict):
    for low, orig_rel in backed_up.items():
        b_file = os.path.join(backup_dir, orig_rel)
        t_file = os.path.join(game_dir, orig_rel)
        if os.path.exists(b_file):
            shutil.copy2(b_file, t_file)

# 2. Remove mod files
vanilla_lows = set(backed_up.keys() if isinstance(backed_up, dict) else [f.lower() for f in backed_up])

# Collect all files to remove
to_remove = set()
if 'mod_files' in manifest:
    for files in manifest['mod_files'].values():
        to_remove.update(files)
if 'installed_files' in manifest:
    to_remove.update(manifest['installed_files'])

for f_rel in to_remove:
    if f_rel.lower() not in vanilla_lows:
        full = os.path.join(game_dir, f_rel)
        if os.path.isfile(full):
            try: os.remove(full)
            except Exception: pass

for cfg in ['mods.txt', 'tiremod.rg']:
    full = os.path.join(game_dir, cfg)
    if os.path.isfile(full):
        try: os.remove(full)
        except Exception: pass

# Remove empty dirs
for root, dirs, files in os.walk(game_dir, topdown=False):
    if root == game_dir: continue
    if not os.listdir(root):
        try: os.rmdir(root)
        except Exception: pass

shutil.rmtree(backup_dir, ignore_errors=True)
if os.path.exists(manifest_path): os.remove(manifest_path)
print('Disinstallazione completata! Il gioco è tornato 100% vanilla.')
"
rm -f "$GAME_DIR/uninstall_mods.sh"
""")
    os.chmod(uninstaller_path, 0o755)

# -----------------------------------------------------------------------------
# COMMAND: LIST
# -----------------------------------------------------------------------------
def cmd_list(source_dir, target_dir):
    """Lists all available mods grouped by brand and category, showing installed status."""
    all_mods = parse_mod_order(source_dir)
    manifest = load_manifest(target_dir) if target_dir else None
    active_mods = set(manifest.get("active_mods", manifest.get("mods", []))) if manifest else set()

    print(colorize("\n" + "=" * 78, Colors.BOLD))
    print(colorize("  Catalogo Mod Auto Project CARS 1 (Ultimate Mod Pack)", Colors.BOLD + Colors.CYAN))
    print(colorize("=" * 78, Colors.BOLD))

    # Group by brand
    brands = {}
    for idx, m in enumerate(all_mods, 1):
        brand, cat = classify_mod(m)
        brands.setdefault(brand, []).append((idx, m, cat))

    total_installed = 0
    for brand, items in sorted(brands.items()):
        print(f"\n{colorize(brand, Colors.BOLD + Colors.YELLOW)}:")
        for idx, m, cat in items:
            is_inst = m in active_mods
            if is_inst: total_installed += 1
            status_tag = colorize("[INSTALLATA]", Colors.GREEN + Colors.BOLD) if is_inst else colorize("[NON INSTALLATA]", Colors.BLUE)
            print(f"  [{idx:2d}] {m:48}  {cat:18} {status_tag}")

    print("\n" + "-" * 78)
    print(f"Totale Mod Disponibili: {len(all_mods)} | Attualmente Installate: {colorize(str(total_installed), Colors.GREEN + Colors.BOLD)}")
    print("-" * 78)
    return 0

# -----------------------------------------------------------------------------
# COMMAND: STATUS
# -----------------------------------------------------------------------------
def cmd_status(target_dir):
    """Checks the current mod status of Project CARS."""
    print(colorize("\n[ Controllo Stato Mod ]", Colors.BOLD + Colors.CYAN))
    if not target_dir or not os.path.isdir(target_dir):
        print(colorize(f"Cartella di gioco non valida: {target_dir}", Colors.RED))
        return 1

    manifest = load_manifest(target_dir)
    backup_dir = os.path.join(target_dir, ".backup_vanilla")

    if manifest:
        active = manifest.get("active_mods", manifest.get("mods", []))
        installed_at = manifest.get("installed_at", "Sconosciuto")
        backed_up = len(manifest.get("backed_up_vanilla_files", {}))
        
        # Calculate total files
        if "mod_files" in manifest:
            total_files = len(set(f for flist in manifest["mod_files"].values() for f in flist))
        else:
            total_files = len(manifest.get("installed_files", []))

        print(f"Stato:              {colorize('MOD PACK ATTIVO', Colors.GREEN + Colors.BOLD)}")
        print(f"Data installazione: {installed_at}")
        print(f"Mod attive:         {len(active)}")
        print(f"File gestiti:       {total_files}")
        print(f"File vanilla backup:{backed_up} (in {backup_dir})")
        print(f"Disinstallatore:    {os.path.join(target_dir, 'uninstall_mods.sh')}")

        if active:
            print(f"\nAuto e mod attualmente attive:")
            for m in active:
                b, c = classify_mod(m)
                print(f"  ✔ {m} ({b} - {c})")
        return 0
    else:
        print(f"Stato:              {colorize('GIOCO VANILLA (Nessuna mod attiva)', Colors.YELLOW)}")
        return 0

# -----------------------------------------------------------------------------
# INTERACTIVE MENUS
# -----------------------------------------------------------------------------
def interactive_select_mods(all_mods, currently_active=None, action_name="installare"):
    """Interactive CLI menu to select which mods to install or uninstall."""
    if currently_active is None:
        currently_active = set()

    car_mods = [m for m in all_mods if m != "Custom_Grid_Tool"]

    # Build brand list and category list
    brand_map = {}
    cat_map = {}
    for m in car_mods:
        b, c = classify_mod(m)
        brand_map.setdefault(b, []).append(m)
        cat_map.setdefault(c, []).append(m)

    while True:
        print(colorize("\n" + "=" * 70, Colors.BOLD))
        print(colorize(f"  Menu Selezione Auto da {action_name.capitalize()}", Colors.BOLD + Colors.CYAN))
        print(colorize("=" * 70, Colors.BOLD))
        print(f"  [1] {action_name.capitalize()} TUTTO (Tutte le 55 auto / classi del pacchetto)")
        print(f"  [2] Seleziona per Marchio (es. Ferrari, Porsche, McLaren, BMW, Audi, JDM...)")
        print(f"  [3] Seleziona per Categoria (es. GT3, GT1, Hypercars, Tuners, Hot Hatch...)")
        print(f"  [4] Selezione manuale per singola vettura (Elenco completo numerato)")
        print(f"  [0] Annulla / Esci")
        choice = input(colorize("\nScegli un'opzione [1-4, 0]: ", Colors.BOLD)).strip()

        if choice == "0":
            return None
        elif choice == "1":
            return all_mods

        elif choice == "2":
            print(colorize("\n--- Seleziona i Marchi ---", Colors.BOLD + Colors.YELLOW))
            sorted_brands = sorted(brand_map.keys())
            for idx, b in enumerate(sorted_brands, 1):
                count = len(brand_map[b])
                print(f"  [{idx:2d}] {b:20} ({count} auto)")
            print("\nInserisci i numeri dei marchi separati da virgola (es. 1, 3, 5) o 'all':")
            b_in = input(colorize("Scelta: ", Colors.BOLD)).strip()
            if not b_in: continue
            selected = set()
            if b_in.lower() == "all":
                return all_mods
            for token in b_in.split(","):
                token = token.strip()
                if token.isdigit():
                    num = int(token)
                    if 1 <= num <= len(sorted_brands):
                        selected.update(brand_map[sorted_brands[num - 1]])
            if selected:
                # Always prepend Custom_Grid_Tool for install
                return ["Custom_Grid_Tool"] + [m for m in all_mods if m in selected]
            print(colorize("Nessun marchio valido selezionato.", Colors.RED))

        elif choice == "3":
            print(colorize("\n--- Seleziona le Categorie ---", Colors.BOLD + Colors.YELLOW))
            sorted_cats = sorted(cat_map.keys())
            for idx, c in enumerate(sorted_cats, 1):
                count = len(cat_map[c])
                print(f"  [{idx:2d}] {c:20} ({count} auto)")
            print("\nInserisci i numeri delle categorie separati da virgola (es. 1, 2) o 'all':")
            c_in = input(colorize("Scelta: ", Colors.BOLD)).strip()
            if not c_in: continue
            selected = set()
            if c_in.lower() == "all":
                return all_mods
            for token in c_in.split(","):
                token = token.strip()
                if token.isdigit():
                    num = int(token)
                    if 1 <= num <= len(sorted_cats):
                        selected.update(cat_map[sorted_cats[num - 1]])
            if selected:
                return ["Custom_Grid_Tool"] + [m for m in all_mods if m in selected]
            print(colorize("Nessuna categoria valida selezionata.", Colors.RED))

        elif choice == "4":
            print(colorize("\n--- Elenco Singole Auto ---", Colors.BOLD + Colors.YELLOW))
            for idx, m in enumerate(car_mods, 1):
                b, c = classify_mod(m)
                is_act = "[ATTIVA]" if m in currently_active else "[NON ATTIVA]"
                print(f"  [{idx:2d}] {m:48} ({b} - {c}) {is_act}")
            print("\nInserisci i numeri delle auto separati da virgola (es. 1, 4, 12-15) o 'all':")
            c_in = input(colorize("Scelta: ", Colors.BOLD)).strip()
            if not c_in: continue
            selected = set()
            if c_in.lower() == "all":
                return all_mods
            for token in c_in.split(","):
                token = token.strip()
                if "-" in token:
                    parts = token.split("-")
                    if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                        start, end = int(parts[0]), int(parts[1])
                        for num in range(start, end + 1):
                            if 1 <= num <= len(car_mods):
                                selected.add(car_mods[num - 1])
                elif token.isdigit():
                    num = int(token)
                    if 1 <= num <= len(car_mods):
                        selected.add(car_mods[num - 1])
            if selected:
                return ["Custom_Grid_Tool"] + [m for m in all_mods if m in selected]
            print(colorize("Nessuna auto valida selezionata.", Colors.RED))

# -----------------------------------------------------------------------------
# COMMAND: INSTALL
# -----------------------------------------------------------------------------
def cmd_install(source_dir, target_dir, selected_mods=None, dry_run=False):
    """Installs specified or all mods with reference tracking and case-insensitive resolution."""
    all_mods = parse_mod_order(source_dir)
    backup_dir = os.path.join(target_dir, ".backup_vanilla")

    # Load existing manifest if any
    manifest = load_manifest(target_dir) or {}
    active_mods = list(manifest.get("active_mods", manifest.get("mods", [])))
    backed_up_files = manifest.get("backed_up_vanilla_files", {})
    if isinstance(backed_up_files, list):
        backed_up_files = {f.lower(): f for f in backed_up_files}
    mod_files = manifest.get("mod_files", {})

    # If selected_mods is None, default to all
    if not selected_mods:
        selected_mods = all_mods

    # Ensure Custom_Grid_Tool is always included if installing any car
    if "Custom_Grid_Tool" not in selected_mods and any(m != "Custom_Grid_Tool" for m in selected_mods):
        selected_mods = ["Custom_Grid_Tool"] + selected_mods

    # Filter to only preserve dependency order from all_mods
    mods_to_install = [m for m in all_mods if m in selected_mods]

    print(colorize("\n[ Installazione Mod Pack Project CARS ]", Colors.BOLD + Colors.CYAN))
    print(f"Origine mod:      {colorize(source_dir, Colors.BLUE)}")
    print(f"Cartella gioco:   {colorize(target_dir, Colors.BLUE)}")
    print(f"Mod selezionate:  {colorize(str(len(mods_to_install)), Colors.GREEN + Colors.BOLD)} su {len(all_mods)}")
    if dry_run:
        print(colorize("MODALITÀ SIMULAZIONE (DRY RUN): Nessun file verrà modificato.", Colors.YELLOW + Colors.BOLD))
    print("-" * 70)

    if not dry_run:
        os.makedirs(backup_dir, exist_ok=True)

    # 1. Map existing game files
    print("[1/5] Scansione dei file di gioco attuali...")
    vanilla_files = {}
    for root, _, files in os.walk(target_dir):
        if root.startswith(backup_dir): continue
        for f in files:
            full = os.path.join(root, f)
            rel = os.path.relpath(full, target_dir)
            vanilla_files[rel.lower()] = rel

    # 2. Backup vanilla files for mods that will be newly installed
    print("[2/5] Controllo e backup dei file vanilla originali sovrascritti...")
    new_backups = 0
    for mod in mods_to_install:
        if mod in active_mods:
            continue # already installed
        mod_path = os.path.join(source_dir, "MODS", mod)
        if not os.path.isdir(mod_path): continue
        for root, _, files in os.walk(mod_path):
            for f in files:
                rel_mod = os.path.relpath(os.path.join(root, f), mod_path)
                _, resolved_rel = resolve_case_insensitive_path(target_dir, rel_mod)
                low = resolved_rel.lower()
                if low in vanilla_files and low not in backed_up_files:
                    orig_rel = vanilla_files[low]
                    orig_full = os.path.join(target_dir, orig_rel)
                    b_full = os.path.join(backup_dir, orig_rel)
                    if not dry_run:
                        os.makedirs(os.path.dirname(b_full), exist_ok=True)
                        fast_copy(orig_full, b_full)
                    backed_up_files[low] = orig_rel
                    new_backups += 1
                    print(f"      Backup salvato: {orig_rel}")

    print(f"      Backup completato ({len(backed_up_files)} file originali protetti).")

    # 3. Copy files for each selected mod
    print("[3/5] Installazione dei file delle mod (risoluzione automatica maiuscole/minuscole)...")
    installed_count = 0
    for i, mod in enumerate(mods_to_install, 1):
        mod_path = os.path.join(source_dir, "MODS", mod)
        if not os.path.isdir(mod_path):
            print(colorize(f"      [AVVISO] Mod mancante nel pacchetto: {mod}", Colors.YELLOW))
            continue

        file_list = []
        for root, _, files in os.walk(mod_path):
            for f in files:
                src_file = os.path.join(root, f)
                rel_mod = os.path.relpath(src_file, mod_path)
                dest_file, resolved_rel = resolve_case_insensitive_path(target_dir, rel_mod)
                fast_copy(src_file, dest_file, dry_run=dry_run)
                file_list.append(resolved_rel)
                installed_count += 1

        mod_files[mod] = file_list
        if mod not in active_mods:
            active_mods.append(mod)

        b, c = classify_mod(mod)
        print(f"      [{i:02d}/{len(mods_to_install)}] {mod} ({len(file_list)} file) [{b} - {c}]")

    # 4. Filter and write mods.txt and tiremod.rg
    print("[4/5] Configurazione registro veicoli (mods.txt filtrato per auto attive)...")
    header, entries, entry_to_mod = parse_mods_txt_mapping(source_dir, all_mods)
    filtered_mods_txt = generate_filtered_mods_txt(header, entries, entry_to_mod, active_mods)

    if not dry_run:
        with open(os.path.join(target_dir, "mods.txt"), "w", encoding="utf-8") as f:
            f.write(filtered_mods_txt)
        # Copy tiremod.rg
        src_tire = os.path.join(source_dir, "tiremod.rg")
        if os.path.isfile(src_tire):
            fast_copy(src_tire, os.path.join(target_dir, "tiremod.rg"))
        print(f"      mods.txt aggiornato con {len(re.findall(r'([vV]ehicles[^\n]+\.crd)', filtered_mods_txt))} auto registrate.")

    # 5. Save manifest & uninstaller
    if not dry_run:
        manifest_data = {
            "installed_at": datetime.now().isoformat(),
            "active_mods": active_mods,
            "backed_up_vanilla_files": backed_up_files,
            "mod_files": mod_files,
        }
        save_manifest(target_dir, manifest_data)
        write_uninstaller_script(target_dir)

    print(colorize("\n" + "=" * 70, Colors.BOLD))
    print(colorize("INSTALLAZIONE COMPLETATA CON SUCCESSO! ✔", Colors.GREEN + Colors.BOLD))
    print(colorize("=" * 70, Colors.BOLD))
    print(f"Mod attualmente attive: {len(active_mods)}")
    print(f"File gestiti:           {installed_count}")
    print("\nPuoi avviare Project CARS direttamente da Steam!")
    return 0

# -----------------------------------------------------------------------------
# COMMAND: UNINSTALL
# -----------------------------------------------------------------------------
def cmd_uninstall(source_dir, target_dir, mods_to_remove=None, remove_all=False, dry_run=False):
    """Selectively or completely uninstalls mods, safely handling shared files."""
    manifest = load_manifest(target_dir)
    if not manifest:
        print(colorize("Nessun manifest mod (.modpack_manifest.json) trovato. Il gioco sembra già vanilla.", Colors.YELLOW))
        return 0

    active_mods = list(manifest.get("active_mods", manifest.get("mods", [])))
    mod_files = manifest.get("mod_files", {})
    backed_up_files = manifest.get("backed_up_vanilla_files", {})
    backup_dir = os.path.join(target_dir, ".backup_vanilla")

    if isinstance(backed_up_files, list):
        backed_up_files = {f.lower(): f for f in backed_up_files}

    # If remove_all or no car mods will remain, do a full clean wipe
    if remove_all or not mods_to_remove:
        mods_to_remove = list(active_mods)

    # Check if this removes everything
    remaining_mods = [m for m in active_mods if m not in mods_to_remove]
    # If only Custom_Grid_Tool remains with no cars, remove Custom_Grid_Tool as well
    if remaining_mods == ["Custom_Grid_Tool"]:
        mods_to_remove.append("Custom_Grid_Tool")
        remaining_mods = []

    print(colorize("\n[ Disinstallazione Mod Pack Project CARS ]", Colors.BOLD + Colors.CYAN))
    print(f"Mod da rimuovere:       {colorize(str(len(mods_to_remove)), Colors.YELLOW + Colors.BOLD)}")
    print(f"Mod che rimarranno:     {colorize(str(len(remaining_mods)), Colors.BLUE)}")
    if dry_run:
        print(colorize("MODALITÀ SIMULAZIONE (DRY RUN): Nessun file verrà modificato.", Colors.YELLOW + Colors.BOLD))
    print("-" * 70)

    # Identify files still needed by remaining mods
    needed_files = set()
    for m in remaining_mods:
        for f in mod_files.get(m, []):
            needed_files.add(f.lower())

    # Files to delete or restore
    files_to_remove = set()
    files_to_restore = set()

    for m in mods_to_remove:
        for f_rel in mod_files.get(m, []):
            f_low = f_rel.lower()
            if f_low not in needed_files:
                if f_low in backed_up_files:
                    files_to_restore.add(backed_up_files[f_low])
                else:
                    files_to_remove.add(f_rel)

    print(f"File unici da eliminare: {len(files_to_remove)}")
    print(f"File vanilla da ripristinare: {len(files_to_restore)}")

    if not dry_run:
        # Restore vanilla
        for orig_rel in files_to_restore:
            b_file = os.path.join(backup_dir, orig_rel)
            t_file = os.path.join(target_dir, orig_rel)
            if os.path.isfile(b_file):
                os.makedirs(os.path.dirname(t_file), exist_ok=True)
                shutil.copy2(b_file, t_file)

        # Remove mod unique files
        for f_rel in files_to_remove:
            full = os.path.join(target_dir, f_rel)
            if os.path.isfile(full):
                try: os.remove(full)
                except Exception: pass

        # Clean empty directories
        for root, dirs, files in os.walk(target_dir, topdown=False):
            if root == target_dir or root.startswith(backup_dir): continue
            if not os.listdir(root):
                try: os.rmdir(root)
                except Exception: pass

    # If completely empty
    if not remaining_mods:
        print(colorize("\nTutte le mod sono state rimosse. Ripristino completo gioco vanilla...", Colors.CYAN))
        if not dry_run:
            # Restore all remaining vanilla
            for low, orig_rel in backed_up_files.items():
                b_file = os.path.join(backup_dir, orig_rel)
                t_file = os.path.join(target_dir, orig_rel)
                if os.path.isfile(b_file):
                    shutil.copy2(b_file, t_file)

            for cfg in ["mods.txt", "tiremod.rg", "uninstall_mods.sh"]:
                p = os.path.join(target_dir, cfg)
                if os.path.isfile(p):
                    try: os.remove(p)
                    except Exception: pass

            shutil.rmtree(backup_dir, ignore_errors=True)
            manifest_path = os.path.join(target_dir, ".modpack_manifest.json")
            if os.path.exists(manifest_path):
                os.remove(manifest_path)

        print(colorize("✔ Disinstallazione completata! Il gioco è tornato 100% vanilla.", Colors.GREEN + Colors.BOLD))
        return 0

    # If some mods remain, update mods.txt and manifest
    if not dry_run:
        # Remove uninstalled mods from mod_files
        for m in mods_to_remove:
            mod_files.pop(m, None)

        all_mods = parse_mod_order(source_dir)
        header, entries, entry_to_mod = parse_mods_txt_mapping(source_dir, all_mods)
        filtered_mods_txt = generate_filtered_mods_txt(header, entries, entry_to_mod, remaining_mods)
        with open(os.path.join(target_dir, "mods.txt"), "w", encoding="utf-8") as f:
            f.write(filtered_mods_txt)

        manifest["active_mods"] = remaining_mods
        manifest["mod_files"] = mod_files
        save_manifest(target_dir, manifest)
        print(f"mods.txt aggiornato per le {len(remaining_mods)} mod rimaste attive.")

    print(colorize("\n✔ Disinstallazione selettiva completata!", Colors.GREEN + Colors.BOLD))
    print(f"Mod ancora attive nel gioco: {len(remaining_mods)}")
    return 0

# -----------------------------------------------------------------------------
# MAIN CLI
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Project CARS 1 - Mod Pack Installer & Manager per Linux (CachyOS / Arch / Proton)",
        epilog="""Esempi di utilizzo:
  # Mostra l'elenco delle auto disponibili e lo stato:
  python3 pcars_mod_installer.py list

  # Installa tutto il pacchetto (comportamento predefinito):
  python3 pcars_mod_installer.py install --all

  # Menu interattivo per scegliere le auto da installare:
  python3 pcars_mod_installer.py install --interactive

  # Installa per marchio o per categoria:
  python3 pcars_mod_installer.py install --brand ferrari,porsche
  python3 pcars_mod_installer.py install --category gt3,gt1

  # Disinstalla tutto ripristinando il gioco vanilla:
  python3 pcars_mod_installer.py uninstall --all

  # Menu interattivo per disinstallare solo alcune auto:
  python3 pcars_mod_installer.py uninstall --interactive

  # Disinstalla solo specifiche auto:
  python3 pcars_mod_installer.py uninstall --brand ferrari
""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("action", nargs="?", default="install", choices=["install", "uninstall", "status", "list"],
                        help="Azione da compiere: install (default), uninstall, status, list")
    parser.add_argument("--source", "-s", default=None,
                        help="Percorso del mod pack (default: auto-detect)")
    parser.add_argument("--target", "-t", default=None,
                        help="Percorso del gioco Project CARS (default: auto-detect)")
    parser.add_argument("--all", "-a", action="store_true",
                        help="Installa o disinstalla tutte le auto")
    parser.add_argument("--interactive", "-i", action="store_true",
                        help="Avvia il menu interattivo da terminale per scegliere le auto")
    parser.add_argument("--brand", "-b", default=None,
                        help="Filtra per marchi (separati da virgola: ferrari,porsche,audi...)")
    parser.add_argument("--category", "-c", default=None,
                        help="Filtra per categoria (separati da virgola: gt3,gt1,hypercars,tuner...)")
    parser.add_argument("--cars", default=None,
                        help="Filtra per nomi/sottostringhe auto (es: '488 GT3',laferrari,supra)")
    parser.add_argument("--dry-run", "-n", action="store_true",
                        help="Simula l'operazione senza scrivere modifiche su disco")

    args = parser.parse_args()

    target_dir = args.target or auto_detect_game_path()
    if not target_dir or not os.path.isdir(target_dir):
        print(colorize("ERRORE: Cartella di Project CARS non trovata.", Colors.RED))
        print("Specificala con: --target /percorso/a/pCars")
        sys.exit(1)

    if args.action == "status":
        sys.exit(cmd_status(target_dir))

    source_dir = args.source or auto_detect_mod_source()
    if not source_dir or not os.path.isdir(source_dir):
        print(colorize("ERRORE: Cartella del Mod Pack non trovata.", Colors.RED))
        print("Specificala con: --source /percorso/al/ModPack")
        sys.exit(1)

    if args.action == "list":
        sys.exit(cmd_list(source_dir, target_dir))

    all_mods = parse_mod_order(source_dir)

    # Helper filter by brand / category / cars
    def filter_mods(mods_pool, brands_str, cats_str, cars_str):
        matched = set()
        brands_list = [b.strip().lower() for b in brands_str.split(",")] if brands_str else []
        cats_list = [c.strip().lower() for c in cats_str.split(",")] if cats_str else []
        cars_list = [car.strip().lower() for car in cars_str.split(",")] if cars_str else []

        for m in mods_pool:
            if m == "Custom_Grid_Tool": continue
            b, c = classify_mod(m)
            m_low = m.lower()
            b_low = b.lower()
            c_low = c.lower()

            if brands_list and any(bl in b_low for bl in brands_list):
                matched.add(m)
            if cats_list and any(cl in c_low for cl in cats_list):
                matched.add(m)
            if cars_list and any(carl in m_low for carl in cars_list):
                matched.add(m)
        return list(matched)

    if args.action == "install":
        selected = None
        if args.brand or args.category or args.cars:
            matched = filter_mods(all_mods, args.brand, args.category, args.cars)
            if not matched:
                print(colorize("Nessuna auto corrisponde ai filtri specificati.", Colors.RED))
                sys.exit(1)
            selected = ["Custom_Grid_Tool"] + matched
        elif args.interactive:
            manifest = load_manifest(target_dir)
            active = set(manifest.get("active_mods", [])) if manifest else set()
            selected = interactive_select_mods(all_mods, active, action_name="installare")
            if not selected:
                print("Operazione annullata.")
                sys.exit(0)
        elif not args.all and sys.stdin.isatty():
            # Prompt user if they want all or selective
            print(colorize("\nModalità di installazione:", Colors.BOLD))
            print("  [1] Installa Tutte le auto (Consigliato)")
            print("  [2] Seleziona le auto da installare (Menu interattivo)")
            print("  [0] Annulla")
            ans = input(colorize("Scelta [1]: ", Colors.BOLD)).strip()
            if ans == "2":
                manifest = load_manifest(target_dir)
                active = set(manifest.get("active_mods", [])) if manifest else set()
                selected = interactive_select_mods(all_mods, active, action_name="installare")
                if not selected:
                    print("Operazione annullata.")
                    sys.exit(0)
            elif ans == "0":
                print("Operazione annullata.")
                sys.exit(0)
            else:
                selected = all_mods
        else:
            selected = all_mods

        sys.exit(cmd_install(source_dir, target_dir, selected_mods=selected, dry_run=args.dry_run))

    elif args.action == "uninstall":
        manifest = load_manifest(target_dir)
        if not manifest:
            print(colorize("Nessuna mod risulta attualmente installata.", Colors.YELLOW))
            sys.exit(0)

        active = list(manifest.get("active_mods", manifest.get("mods", [])))
        to_remove = None
        remove_all = args.all

        if args.brand or args.category or args.cars:
            to_remove = filter_mods(active, args.brand, args.category, args.cars)
            if not to_remove:
                print(colorize("Nessuna auto attiva corrisponde ai filtri specificati.", Colors.RED))
                sys.exit(1)
        elif args.interactive:
            chosen = interactive_select_mods(active, active, action_name="rimuovere")
            if not chosen:
                print("Operazione annullata.")
                sys.exit(0)
            to_remove = [m for m in chosen if m != "Custom_Grid_Tool"]
            if len(to_remove) == len([m for m in active if m != "Custom_Grid_Tool"]):
                remove_all = True
        elif not args.all and sys.stdin.isatty():
            print(colorize("\nModalità di disinstallazione:", Colors.BOLD))
            print("  [1] Disinstalla TUTTO (Ripristina gioco 100% vanilla)")
            print("  [2] Scegli quali auto rimuovere (Disinstallazione selettiva)")
            print("  [0] Annulla")
            ans = input(colorize("Scelta [1]: ", Colors.BOLD)).strip()
            if ans == "2":
                chosen = interactive_select_mods(active, active, action_name="rimuovere")
                if not chosen:
                    print("Operazione annullata.")
                    sys.exit(0)
                to_remove = [m for m in chosen if m != "Custom_Grid_Tool"]
            elif ans == "0":
                print("Operazione annullata.")
                sys.exit(0)
            else:
                remove_all = True
        else:
            remove_all = True

        sys.exit(cmd_uninstall(source_dir, target_dir, mods_to_remove=to_remove, remove_all=remove_all, dry_run=args.dry_run))

if __name__ == "__main__":
    main()
