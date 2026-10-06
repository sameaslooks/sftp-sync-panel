import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List

CONFIG_DIR = Path.home() / ".sftp-sync-panel"
PROFILES_FILE = CONFIG_DIR / "profiles.json"


@dataclass
class Profile:
    name: str = ""
    host: str = ""
    port: int = 22
    user: str = ""
    auth: str = "agent"        # "agent" | "key_file" | "password"
    key_file: str = ""
    local_path: str = ""
    remote_path: str = ""
    exclusions: List[str] = field(default_factory=list)
    mirror_delete: bool = False
    auto_sync: bool = False
    auto_sync_interval: int = 2
    compare_mode: str = "mtime"  # "mtime" | "md5"

    def display_name(self) -> str:
        return self.name or self.host


def load_profiles() -> List[Profile]:
    if not PROFILES_FILE.exists():
        return []
    try:
        data = json.loads(PROFILES_FILE.read_text(encoding="utf-8"))
        profiles = []
        for item in data:
            known = {f for f in Profile.__dataclass_fields__}
            filtered = {k: v for k, v in item.items() if k in known}
            profiles.append(Profile(**filtered))
        return profiles
    except Exception:
        return []


def save_profiles(profiles: List[Profile]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    PROFILES_FILE.write_text(
        json.dumps([asdict(p) for p in profiles], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
