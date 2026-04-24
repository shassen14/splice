"""Probe: MediaPool and its folder tree."""
from __future__ import annotations

from ._fmt import call, probe_methods, section, subsection

CANDIDATES = [
    "GetRootFolder",
    "GetCurrentFolder",
    "SetCurrentFolder",
    "AddSubFolder",
    "CreateEmptyTimeline",
    "ImportMedia",
    "AppendToTimeline",
    "DeleteClips",
    "MoveClips",
    "GetFolderList",
    "GetClipList",
    "GetUniqueId",
]


def _probe_folder(folder, depth: int = 0) -> None:
    indent = "  " * (depth + 2)
    name = folder.GetName() if getattr(folder, "GetName", None) else "?"
    clips = folder.GetClipList() if getattr(folder, "GetClipList", None) else []
    n = len(clips) if isinstance(clips, list) else "?"
    print(f"{indent}{name!r}  ({n} clips)")

    subs = folder.GetSubFolderList() if getattr(folder, "GetSubFolderList", None) else []
    if isinstance(subs, list):
        for sub in subs:
            _probe_folder(sub, depth + 1)


def probe(project) -> None:
    section("7. MediaPool")

    if not getattr(project, "GetMediaPool", None):
        print("  GetMediaPool() not available on Project")
        return

    mp = project.GetMediaPool()
    if mp is None:
        print("  GetMediaPool() → None")
        return

    print(f"  type: {type(mp)}")
    probe_methods(mp, CANDIDATES)

    root = call("GetRootFolder()", mp.GetRootFolder) if getattr(mp, "GetRootFolder", None) else None
    if not root:
        return

    subsection("Folder tree")
    _probe_folder(root)
