from __future__ import annotations

import fnmatch
import hashlib
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class OpType(Enum):
    ADD = "add"
    UPDATE = "update"
    DELETE = "delete"


@dataclass
class FileInfo:
    path: str    # relative to root, forward slashes
    size: int
    mtime: float
    md5: Optional[str] = field(default=None, compare=False)


@dataclass
class SyncOp:
    op: OpType
    path: str
    local: Optional[FileInfo] = None
    remote: Optional[FileInfo] = None

    def description(self) -> str:
        if self.op == OpType.ADD:
            return f"Upload (new)  {self.path}"
        if self.op == OpType.UPDATE:
            return f"Upload (diff) {self.path}"
        return f"Delete remote {self.path}"


FileTree = Dict[str, FileInfo]


# ---------------------------------------------------------------------------
# Exclusion helpers

def _is_excluded(rel_path: str, exclusions: List[str]) -> bool:
    """rel_path uses forward slashes."""
    parts = rel_path.split("/")
    for pattern in exclusions:
        p = pattern.rstrip("/")
        if fnmatch.fnmatch(rel_path, p) or fnmatch.fnmatch(rel_path, pattern):
            return True
        for part in parts:
            if fnmatch.fnmatch(part, p):
                return True
    return False


# ---------------------------------------------------------------------------
# Local scan

def _md5_local(path: str) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def scan_local(root: str, exclusions: List[str], compute_md5: bool = False) -> FileTree:
    result: FileTree = {}
    root = os.path.normpath(root)

    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root).replace("\\", "/")
        if rel_dir != "." and _is_excluded(rel_dir + "/", exclusions):
            dirnames.clear()
            continue

        dirnames[:] = [
            d for d in dirnames
            if not _is_excluded(
                (f"{rel_dir}/{d}" if rel_dir != "." else d) + "/",
                exclusions,
            )
        ]

        for fname in filenames:
            rel_file = (f"{rel_dir}/{fname}" if rel_dir != "." else fname)
            if _is_excluded(rel_file, exclusions):
                continue
            full = os.path.join(dirpath, fname)
            try:
                st = os.stat(full)
                md5 = _md5_local(full) if compute_md5 else None
                result[rel_file] = FileInfo(rel_file, st.st_size, st.st_mtime, md5=md5)
            except OSError:
                pass

    return result


# ---------------------------------------------------------------------------
# Remote scan  (single SSH round-trip via `find`)

def scan_remote(conn, remote_root: str, exclusions: List[str], compute_md5: bool = False) -> FileTree:
    # Enumerate all remote files in one round-trip; exclusions are applied
    # in Python below via _is_excluded().  The old find -prune approach
    # incorrectly dropped *files* (not just dirs) whose names matched any
    # exclusion glob, making uploaded files appear perpetually "new".
    cmd = f'find {remote_root} -type f -printf "%T@|%s|%P\\n" 2>/dev/null'
    stdout, _ = conn.exec(cmd)

    result: FileTree = {}
    for line in stdout.splitlines():
        parts = line.strip().split("|", 2)
        if len(parts) != 3:
            continue
        mtime_s, size_s, rel = parts
        try:
            mtime = float(mtime_s)
            size = int(size_s)
        except ValueError:
            continue
        if _is_excluded(rel, exclusions):
            continue
        result[rel] = FileInfo(rel, size, mtime)

    if compute_md5 and result:
        prefix = remote_root.rstrip("/") + "/"
        md5_cmd = f'find {remote_root} -type f -print0 | xargs -0 md5sum 2>/dev/null'
        md5_out, _ = conn.exec(md5_cmd)
        for line in md5_out.splitlines():
            parts = line.split(None, 1)
            if len(parts) != 2:
                continue
            hash_val, abs_path = parts[0], parts[1].strip()
            rel = abs_path[len(prefix):] if abs_path.startswith(prefix) else None
            if rel and rel in result:
                result[rel].md5 = hash_val

    return result


# ---------------------------------------------------------------------------
# Diff

def compute_diff(
    local: FileTree,
    remote: FileTree,
    mirror_delete: bool = False,
    compare_mode: str = "mtime",
) -> List[SyncOp]:
    ops: List[SyncOp] = []

    for path, lf in local.items():
        if path not in remote:
            ops.append(SyncOp(OpType.ADD, path, local=lf))
        elif _changed(lf, remote[path], compare_mode):
            ops.append(SyncOp(OpType.UPDATE, path, local=lf, remote=remote[path]))

    if mirror_delete:
        for path in remote:
            if path not in local:
                ops.append(SyncOp(OpType.DELETE, path, remote=remote[path]))

    return ops


def _changed(lf: FileInfo, rf: FileInfo, mode: str) -> bool:
    if lf.size != rf.size:
        return True
    if mode == "md5" and lf.md5 is not None and rf.md5 is not None:
        return lf.md5 != rf.md5
    return abs(lf.mtime - rf.mtime) > 1.0
