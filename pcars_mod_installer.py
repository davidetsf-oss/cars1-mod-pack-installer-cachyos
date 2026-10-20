#!/usr/bin/env python3
"""
Project CARS 1 - Mod Pack Installer & Manager for Linux (CachyOS / Arch / Proton)
================================================================================
Author: Davide & Antigravity (AI Assistant)
License: MIT

Features:
- Automatic Steam / Project CARS installation detection (Native & Flatpak, multiple libraries)
- Safe case-insensitive path resolver avoiding duplicate directories (Vehicles vs vehicles, Audio vs audio, etc.)
- Automatic Copy-on-Write (Btrfs/XFS reflink) for lightning-fast installation and zero initial disk waste
- Full safety backup of vanilla files before overwriting
- Comprehensive JSON manifest logging
- Clean, one-command uninstallation restoring 100% vanilla game state
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
    # Common default paths fallback
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
    # Fallback to alphanumeric sort
    mods_dir = os.path.join(source_dir, "MODS")
    subdirs = [d for d in os.listdir(mods_dir) if not d.startswith("!") and os.path.isdir(os.path.join(mods_dir, d))]
    # Ensure Custom_Grid_Tool is always first if present
    if "Custom_Grid_Tool" in subdirs:
        subdirs.remove("Custom_Grid_Tool")
        return ["Custom_Grid_Tool"] + sorted(subdirs)
    return sorted(subdirs)

def resolve_case_insensitive_path(base_dir, rel_path):
    """
    Given a base directory and a relative path (e.g. 'vehicles/audi/car.crd'),
    resolves each segment against existing files/directories on disk case-insensitively.
    This guarantees that we reuse existing folders ('Vehicles', 'Audio', 'GUI')
    instead of creating Linux case duplicates ('vehicles', 'audio', 'gui').
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

def cmd_status(target_dir):
    """Checks the current mod status of Project CARS."""
    print(colorize("\n[ Controllo Stato Mod ]", Colors.BOLD + Colors.CYAN))
    if not target_dir or not os.path.isdir(target_dir):
        print(colorize(f"Cartella di gioco non valida: {target_dir}", Colors.RED))
        return 1

    manifest_path = os.path.join(target_dir, ".modpack_manifest.json")
    backup_dir = os.path.join(target_dir, ".backup_vanilla")

    if os.path.isfile(manifest_path):
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            installed_at = data.get("installed_at", "Sconosciuto")
            total_mods = data.get("total_mods", len(data.get("mods", [])))
            backed_up = len(data.get("backed_up_vanilla_files", []))
            installed_files = len(data.get("installed_files", []))

            print(f"Stato:             {colorize('MOD PACK INSTALLATO', Colors.GREEN + Colors.BOLD)}")
            print(f"Data installazione: {installed_at}")
            print(f"Mod attive:        {total_mods}")
            print(f"File installati:   {installed_files}")
            print(f"File di backup:    {backed_up} (in {backup_dir})")
            print(f"Disinstallatore:   {os.path.join(target_dir, 'uninstall_mods.sh')}")
            return 0
        except Exception as e:
            print(colorize(f"Errore lettura manifest: {e}", Colors.RED))
            return 1
    else:
        print(f"Stato:             {colorize('GIOCO VANILLA (Nessun mod pack attivo)', Colors.YELLOW)}")
        return 0

def cmd_uninstall(target_dir):
    """Restores the vanilla game from backup and removes installed mod files."""
    print(colorize("\n[ Disinstallazione Mod Pack ]", Colors.BOLD + Colors.CYAN))
    manifest_path = os.path.join(target_dir, ".modpack_manifest.json")
    backup_dir = os.path.join(target_dir, ".backup_vanilla")

    if not os.path.isfile(manifest_path):
        print(colorize("Nessun manifest mod (.modpack_manifest.json) trovato. Il gioco sembra già vanilla.", Colors.YELLOW))
        return 0

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except Exception as e:
        print(colorize(f"Impossibile leggere il manifest: {e}", Colors.RED))
        return 1

    # 1. Restore vanilla backups
    vanilla_files = manifest.get("backed_up_vanilla_files", [])
    print(f"Ripristino di {len(vanilla_files)} file originali...")
    for orig_rel in vanilla_files:
        b_file = os.path.join(backup_dir, orig_rel)
        t_file = os.path.join(target_dir, orig_rel)
        if os.path.isfile(b_file):
            os.makedirs(os.path.dirname(t_file), exist_ok=True)
            shutil.copy2(b_file, t_file)

    # 2. Delete added files
    vanilla_set = set(f.lower() for f in vanilla_files)
    installed_files = manifest.get("installed_files", [])
    print(f"Rimozione di {len(installed_files)} file delle mod...")
    removed_count = 0
    for f_rel in installed_files:
        if f_rel.lower() not in vanilla_set:
            full = os.path.join(target_dir, f_rel)
            if os.path.isfile(full):
                try:
                    os.remove(full)
                    removed_count += 1
                except Exception:
                    pass

    # Clean empty directories
    for root, dirs, files in os.walk(target_dir, topdown=False):
        if root == target_dir or root.startswith(backup_dir):
            continue
        if not os.listdir(root):
            try:
                os.rmdir(root)
            except Exception:
                pass

    # Cleanup backup directory and manifest
    shutil.rmtree(backup_dir, ignore_errors=True)
    if os.path.exists(manifest_path):
        os.remove(manifest_path)
    sh_script = os.path.join(target_dir, "uninstall_mods.sh")
    if os.path.exists(sh_script):
        os.remove(sh_script)

    print(colorize("\n✔ Disinstallazione completata con successo!", Colors.GREEN + Colors.BOLD))
    print("Project CARS è stato ripristinato allo stato 100% vanilla originale.")
    return 0

def cmd_install(source_dir, target_dir, dry_run=False):
    """Installs the Ultimate Mod Pack with full case-sensitivity and backup handling."""
    print(colorize("\n[ Installazione Mod Pack Project CARS ]", Colors.BOLD + Colors.CYAN))
    print(f"Origine mod:      {colorize(source_dir, Colors.BLUE)}")
    print(f"Cartella gioco:   {colorize(target_dir, Colors.BLUE)}")
    if dry_run:
        print(colorize("MODALITÀ SIMULAZIONE (DRY RUN): Nessun file verrà modificato.", Colors.YELLOW + Colors.BOLD))
    print("-" * 70)

    backup_dir = os.path.join(target_dir, ".backup_vanilla")
    manifest_path = os.path.join(target_dir, ".modpack_manifest.json")

    # Check if already installed
    if os.path.isfile(manifest_path) and not dry_run:
        print(colorize("AVVISO: È già presente un'installazione mod registrata.", Colors.YELLOW))
        print("Si consiglia di eseguire prima una disinstallazione pulita se si vuole reinstallare.")
        ans = input("Vuoi sovrascrivere l'installazione esistente? [s/N]: ").strip().lower()
        if ans not in ("s", "si", "y", "yes"):
            print("Operazione annullata.")
            return 0

    if not dry_run:
        os.makedirs(backup_dir, exist_ok=True)

    # 1. Map existing vanilla files
    print("[1/5] Scansione dei file di gioco attuali...")
    vanilla_files = {}
    for root, _, files in os.walk(target_dir):
        if root.startswith(backup_dir):
            continue
        for f in files:
            full = os.path.join(root, f)
            rel = os.path.relpath(full, target_dir)
            vanilla_files[rel.lower()] = rel
    print(f"      Trovati {len(vanilla_files)} file esistenti.")

    # 2. Get mods in order
    mods = parse_mod_order(source_dir)
    print(f"[2/5] Rilevate {len(mods)} mod da installare nell'ordine corretto.")

    # 3. Create backups of vanilla files that will be overwritten
    print("[3/5] Creazione del backup di sicurezza dei file sovrascritti...")
    backed_up_files = {}
    for mod in mods:
        mod_path = os.path.join(source_dir, "MODS", mod)
        if not os.path.isdir(mod_path):
            continue
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
                    print(f"      Backup: {orig_rel}")

    print(f"      Backup pronto per {len(backed_up_files)} file originali.")

    # 4. Copy mod files in order
    print("[4/5] Copia dei file delle mod (risoluzione automatica maiuscole/minuscole)...")
    installed_files = set()

    for i, mod in enumerate(mods, 1):
        mod_path = os.path.join(source_dir, "MODS", mod)
        if not os.path.isdir(mod_path):
            print(colorize(f"      [AVVISO] Mod mancante nel pacchetto: {mod}", Colors.YELLOW))
            continue

        file_count = 0
        for root, _, files in os.walk(mod_path):
            for f in files:
                src_file = os.path.join(root, f)
                rel_mod = os.path.relpath(src_file, mod_path)
                dest_file, resolved_rel = resolve_case_insensitive_path(target_dir, rel_mod)

                fast_copy(src_file, dest_file, dry_run=dry_run)
                installed_files.add(resolved_rel)
                file_count += 1
        print(f"      [{i:02d}/{len(mods)}] {mod} ({file_count} file)")

    # 5. Copy root config files
    print("[5/5] Installazione file di configurazione principali (mods.txt, tiremod.rg)...")
    for cfg_file in ["mods.txt", "tiremod.rg"]:
        src_cfg = os.path.join(source_dir, cfg_file)
        if os.path.isfile(src_cfg):
            dest_cfg = os.path.join(target_dir, cfg_file)
            fast_copy(src_cfg, dest_cfg, dry_run=dry_run)
            installed_files.add(cfg_file)
            print(f"      Copiato {cfg_file}")

    if dry_run:
        print(colorize("\n✔ Simulazione completata senza errori!", Colors.GREEN + Colors.BOLD))
        print(f"File previsti per l'installazione: {len(installed_files)}")
        print(f"File originali da salvare in backup: {len(backed_up_files)}")
        return 0

    # Write manifest
    manifest = {
        "installed_at": datetime.now().isoformat(),
        "total_mods": len(mods),
        "mods": mods,
        "backed_up_vanilla_files": list(backed_up_files.values()),
        "installed_files": sorted(list(installed_files)),
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # Write uninstaller wrapper script
    uninstaller_path = os.path.join(target_dir, "uninstall_mods.sh")
    with open(uninstaller_path, "w", encoding="utf-8") as f:
        f.write("""#!/usr/bin/env bash
set -e
GAME_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST="$GAME_DIR/.modpack_manifest.json"
BACKUP_DIR="$GAME_DIR/.backup_vanilla"

if [ ! -f "$MANIFEST" ]; then
    echo "Errore: Nessun manifest delle mod trovato in $MANIFEST"
    exit 1
fi

python3 -c "
import os, json, shutil

game_dir = '$GAME_DIR'
manifest_path = '$MANIFEST'
backup_dir = '$BACKUP_DIR'

with open(manifest_path, 'r') as f:
    manifest = json.load(f)

for orig_rel in manifest.get('backed_up_vanilla_files', []):
    b_file = os.path.join(backup_dir, orig_rel)
    t_file = os.path.join(game_dir, orig_rel)
    if os.path.exists(b_file):
        os.makedirs(os.path.dirname(t_file), exist_ok=True)
        shutil.copy2(b_file, t_file)
        print('Ripristinato:', orig_rel)

vanilla_set = set(f.lower() for f in manifest.get('backed_up_vanilla_files', []))
removed = 0
for f_rel in manifest.get('installed_files', []):
    if f_rel.lower() not in vanilla_set:
        full_path = os.path.join(game_dir, f_rel)
        if os.path.exists(full_path):
            try:
                os.remove(full_path)
                removed += 1
            except Exception:
                pass
print(f'Rimossi {removed} file mod.')

for root, dirs, files in os.walk(game_dir, topdown=False):
    if root == game_dir: continue
    if not os.listdir(root):
        try: os.rmdir(root)
        except Exception: pass

shutil.rmtree(backup_dir, ignore_errors=True)
if os.path.exists(manifest_path): os.remove(manifest_path)
print('Disinstallazione completata con successo!')
"
rm -f "$GAME_DIR/uninstall_mods.sh"
""")
    os.chmod(uninstaller_path, 0o755)

    print(colorize("\n" + "=" * 70, Colors.BOLD))
    print(colorize("INSTALLAZIONE COMPLETATA CON SUCCESSO! ✔", Colors.GREEN + Colors.BOLD))
    print(colorize("=" * 70, Colors.BOLD))
    print(f"Mod installate:        {len(mods)}")
    print(f"File installati:       {len(installed_files)}")
    print(f"File salvati in backup:{len(backed_up_files)}")
    print(f"Manifest creato in:    {manifest_path}")
    print(f"Script disinstallatore:{uninstaller_path}")
    print("\nPuoi avviare Project CARS direttamente da Steam!")
    return 0

def main():
    parser = argparse.ArgumentParser(
        description="Project CARS 1 - Mod Pack Installer & Manager per Linux (CachyOS / Arch / Proton)"
    )
    parser.add_argument("action", nargs="?", default="install", choices=["install", "uninstall", "status"],
                        help="Azione da compiere: install (default), uninstall, status")
    parser.add_argument("--source", "-s", default=None,
                        help="Percorso della cartella contenente il mod pack (default: auto-detect)")
    parser.add_argument("--target", "-t", default=None,
                        help="Percorso della cartella di installazione di Project CARS (default: auto-detect)")
    parser.add_argument("--dry-run", "-n", action="store_true",
                        help="Simula l'operazione senza modificare alcun file sul disco")

    args = parser.parse_args()

    target_dir = args.target or auto_detect_game_path()
    if not target_dir or not os.path.isdir(target_dir):
        print(colorize(f"ERRORE: Cartella di installazione di Project CARS non trovata.", Colors.RED))
        print("Specificala con il parametro: --target /percorso/a/steamapps/common/pCars")
        sys.exit(1)

    if args.action == "status":
        sys.exit(cmd_status(target_dir))
    elif args.action == "uninstall":
        sys.exit(cmd_uninstall(target_dir))
    elif args.action == "install":
        source_dir = args.source or auto_detect_mod_source()
        if not source_dir or not os.path.isdir(source_dir):
            print(colorize(f"ERRORE: Cartella del Mod Pack non trovata.", Colors.RED))
            print("Specificala con il parametro: --source /percorso/a/'Project Cars 1 Ultimate Mod Pack'")
            sys.exit(1)
        sys.exit(cmd_install(source_dir, target_dir, dry_run=args.dry_run))

if __name__ == "__main__":
    main()
