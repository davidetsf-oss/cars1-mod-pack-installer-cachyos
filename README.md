# Project CARS 1 - Mod Pack Installer per Linux (CachyOS / Arch / Proton)

[![OS - CachyOS / Arch Linux](https://img.shields.io/badge/OS-CachyOS%20%7C%20Arch%20Linux-blue?logo=archlinux)](https://cachyos.org)
[![Proton - Compatible](https://img.shields.io/badge/Compatibility-Steam%20Proton-brightgreen?logo=steam)](https://github.com/ValveSoftware/Proton)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-yellow?logo=python)](https://www.python.org/)
[![License - MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Uno strumento automatizzato per installare e gestire in modo sicuro e pulito l'**Ultimate Mod Pack** (e le mod auto della community) per **Project CARS 1** su sistemi **Linux (CachyOS, Arch, SteamOS / Steam Deck)** in esecuzione tramite **Steam Proton**.

---

## 🎯 Il Problema Risolto (Linux & Case-Sensitivity)

Su Windows (NTFS), il file system ignora la differenza tra maiuscole e minuscole (*case-insensitive*). Strumenti tradizionali come **JSGME** (JoneSoft Generic Mod Enabler) creano o sovrascrivono cartelle indistintamente.

Su Linux (Btrfs / ext4), i file sono **case-sensitive**. Copiare una mod con percorsi come `vehicles/...`, `audio/...` o `gui/...` all'interno della cartella di gioco crea directory separate rispetto alle originali (`Vehicles/`, `Audio/`, `GUI/`). Con Proton, il gioco non trova i file dei modelli, le texture o i file audio, causando crash o auto invisibili.

Questo installer:
1. **Risolve ricorsivamente tutti i percorsi in modo case-insensitive**: garantisce che ogni file finisca nella directory originale corretta senza mai sdoppiare cartelle.
2. **Supporta Copy-on-Write (Btrfs / XFS reflink)**: installa istantaneamente oltre 20.000 file senza consumare spazio disco extra iniziale.
3. **Crea un backup automatico preventivo**: salva tutti i file vanilla originali sovrascritti (solo 18 file di boot e interfaccia) in `.backup_vanilla/`.
4. **Disinstallatore completo (1-Click)**: ripristina il gioco allo stato 100% originale vanilla con un singolo comando.
5. **Rilevamento automatico di Steam**: trova automaticamente la cartella `pCars` in librerie Steam native o Flatpak.

---

## 🚀 Requisiti

- **Sistema Operativo**: CachyOS, Arch Linux o qualsiasi distribuzione Linux con Steam.
- **Python**: 3.8 o superiore (preinstallato su CachyOS).
- **Project CARS 1**: Versione Steam (GOTY v11.2 / 64-bit raccomandata).
- **Proton**: `proton-cachyos`, `Proton Experimental` o `Proton GE / Hotfix`.

---

## 📦 Installazione Rapida

### 1. Clona questo repository
```bash
git clone https://github.com/<tuo-utente>/project-cars-mod-installer-cachyos.git
cd project-cars-mod-installer-cachyos
```

### 2. Posiziona o specifica il Mod Pack
Se hai scaricato l'archivio estratto `Project Cars 1 Ultimate Mod Pack`, l'installer lo cercherà automaticamente in:
- Nella cartella corrente
- In `~/Scaricati/Project Cars 1 Ultimate Mod Pack`
- In `~/Downloads/Project Cars 1 Ultimate Mod Pack`

Oppure puoi specificarne il percorso manualmente.

### 3. Esegui l'installazione
```bash
./install.sh
```
*Oppure specificando manualmente i percorsi:*
```bash
python3 pcars_mod_installer.py install --source "/percorso/al/ModPack" --target "/percorso/a/pCars"
```

---

## 🛠️ Comandi Disponibili

| Comando | Descrizione |
|---|---|
| `./install.sh` | Installa tutte le mod in sequenza con backup automatico dei file vanilla |
| `./status.sh` | Mostra lo stato attuale delle mod, numero di file e data di installazione |
| `./uninstall.sh` | Ripristina i file vanilla e rimuove tutti i file mod dal gioco |
| `python3 pcars_mod_installer.py install --dry-run` | Simula l'installazione senza modificare alcun file sul disco |

---

## 🏎️ Contenuto del Pacchetto (Oltre 70 Auto)

Il pacchetto include 56 categorie di mod configurate nell'ordine ottimale (`JSGME.ini`), tra cui:
- **Ferrari**: 250 GTO, 458 Italia, 488 GT3, 599 GTB, 812 Superfast, F40 '87, F430 Scuderia, F430C GT3, LaFerrari.
- **Porsche**: 911R '16, 918 Spyder, 997 GT3 Cup, GT3RS '16.
- **McLaren**: 650S GT3, 688HS, P1 GTR.
- **Lamborghini**: Gallardo LP560-4, Huracan GT3, Murcielago R-SV GT1.
- **Audi**: A4 DTM, R8 LMS 2015, R8 Spyder V10, S3, RS4.
- **FIA GT1 Pack**: Maserati MC12, Ford GT GT1, Corvette C6.R, Aston Martin DBR9, Nissan GT-R GT1, Lamborghini Murcielago.
- **JDM & Tuners**: Toyota Supra (Stage 1 e 4), Nissan Skyline R34 Tuner, Silvia S15 Tuner, Mazda RX-7 Spirit R, Honda S2000 AP1.
- **Hot Hatch Class & GT3 Class Expansion**.

---

## 🎮 Come Utilizzare le Auto nel Gioco

1. Avvia **Project CARS** normalmente da Steam.
2. Vai su **Quick Race** (Gara Veloce) o **Prova Libera**.
3. Seleziona la tua auto: troverai tutti i nuovi modelli disponibili con suoni personalizzati, visuali cockpit e HUD Motec funzionanti.
4. Per correre con avversari IA personalizzati in gare multiclasse, puoi selezionare la categoria corrispondente o le classi espanse.

> [!WARNING]
> La modalità Carriera ufficiale potrebbe non riconoscere correttamente le classi personalizzate create dai modder. Si raccomanda di utilizzare le auto moddate principalmente in **Quick Race**, **Gare Singole** e **Time Trial**.

---

## 📂 Struttura del Progetto

```
├── pcars_mod_installer.py  # Motore principale Python (rilevamento Steam, CoW reflink, case mapping)
├── install.sh              # Wrapper bash per installazione rapida
├── uninstall.sh            # Wrapper bash per disinstallazione rapida
├── status.sh               # Wrapper bash per verifica stato
├── LICENSE                 # Licenza MIT
└── README.md               # Questa documentazione
```

---

## ⚖️ Licenza e Crediti

- **Installer Tool**: Rilasciato sotto licenza MIT.
- **Mod Asset**: I modelli 3D, le fisiche e i suoni appartengono ai rispettivi autori della community di Project CARS (Slightly Mad Studios, ThunderFlash, JDougNY, Random12multi, KAOS Modding Team, ecc.).
