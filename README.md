# sftp-sync-panel

A fast, multi-server SFTP sync tool with a native GUI — built as a lightweight alternative to WinSCP.

## Features

- **Multiple server profiles** — manage and sync to several servers simultaneously, each in its own tab
- **SSH agent support** — authenticates via the Windows OpenSSH agent (no passwords stored)
- **One-directional sync** (local → remote) with optional mirror-delete
- **Auto-sync** — watchdog monitors local changes and syncs automatically with a configurable debounce
- **Per-profile exclusions** — glob patterns (e.g. `node_modules/`, `.env*`, `*.log`)
- **Fast remote tree scan** — single `find` round-trip instead of per-file `stat` calls
- **Non-blocking delete notifications** — when a file is deleted locally, a prompt appears in the UI without blocking other operations
- **Server-side trash** — remote files are moved to `.synctool-trash/YYYY-MM-DD/` instead of hard-deleted

## Requirements

- Python 3.11+
- Windows 10/11 with OpenSSH agent service enabled (for agent auth)
- Or a key file / password as fallback auth

## Setup

```bat
launch.bat
```

The launch script creates a `venv`, installs dependencies, and starts the app. Run it again any time to start the app — it skips venv creation if it already exists.

To enable the Windows OpenSSH agent:

```powershell
Set-Service -Name ssh-agent -StartupType Automatic
Start-Service ssh-agent
```

## Configuration

Profiles are stored in `%USERPROFILE%\.sftp-sync-panel\profiles.json`. Add, edit and delete profiles from within the app. Add `.sftp-sync-panel/` to your global `.gitignore` if needed.

## Project structure

```
sftp-sync-panel/
├── launch.bat
├── requirements.txt
└── src/
    ├── main.py
    ├── config.py              # Profile dataclass + JSON persistence
    ├── engine/
    │   ├── connection.py      # SSHClient + SFTPClient + agent key handling
    │   ├── pool.py            # Multi-connection pool
    │   ├── differ.py          # Local/remote tree scan + diff (SyncPlan)
    │   ├── executor.py        # Upload/delete queue with server-side trash
    │   └── watcher.py         # watchdog wrapper with debounce
    └── gui/
        ├── mainwindow.py      # QMainWindow — sidebar + tab widget
        ├── serverpanel.py     # Left sidebar — server list + SSH agent status
        ├── synctab.py         # Per-connection tab (toolbar, file panels, log)
        ├── filepanel.py       # QTreeView file browser (local or remote)
        ├── logpanel.py        # Log + progress bar
        ├── notificationstrip.py  # Non-blocking delete prompts
        ├── workers.py         # QThread workers for connect/scan/sync
        ├── style.py           # QSS stylesheet
        └── dialogs/
            ├── profile.py     # Add/edit server profile
            ├── syncplan.py    # Sync plan review + mirror-delete confirm
            ├── exclusions.py  # Exclusion rules editor
            └── agent.py       # SSH agent key inspector
```

## Sync behaviour

| Scenario | Behaviour |
|---|---|
| File added/changed locally | Uploaded on next sync |
| File deleted locally (manual sync) | Listed in plan, mirror-delete checkbox off by default |
| File deleted locally (auto-sync) | Non-blocking notification chip appears — user chooses delete / keep |
| Remote-only file | Ignored (local → remote only) |
| Excluded path | Skipped entirely, shown with `skip` badge in file panel |

## Auth methods

| Method | How |
|---|---|
| `agent` | `paramiko.Agent()` → Windows OpenSSH named pipe |
| `key_file` | Path to private key (PEM/OpenSSH format) |
| `password` | Prompted at connect time, never stored |
