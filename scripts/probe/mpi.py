"""Probe: MediaPoolItem — shared helper used by items.py and media_pool.py."""
from __future__ import annotations

from typing import Any

CANDIDATES = [
    "GetName",
    "GetClipProperty", "SetClipProperty",
    "GetProperty", "SetProperty",
    "GetMediaId", "GetUniqueId",
    "GetFlags", "SetFlags", "ClearFlags",
    "GetClipColor", "SetClipColor",
    "GetMarkers", "AddMarker",
    "GetMetadata", "SetMetadata",
    "GetThirdPartyMetadata", "SetThirdPartyMetadata",
    "GetLinkedItems",
    "GetTranscript", "TranscribeAudio", "ClearTranscription",
]

CLIP_PROP_SPOT_KEYS = (
    "Clip Name", "File Path", "Type", "Duration", "FPS",
    "Resolution", "Video Codec", "Audio Codec",
    "Audio Ch", "Audio Bit Depth", "Sample Rate",
)


def _c(mpi, label: str, fn, *args, indent: str = "    ") -> Any:
    try:
        result = fn(*args)
    except Exception as e:
        print(f"{indent}{label:<40} FAIL  {e}")
        return None
    if result is None:
        tag = "NONE"
    elif result == {} or result == [] or result == "":
        tag = "EMPTY"
    elif result is False:
        tag = "FALSE"
    else:
        tag = "OK"
    rstr = repr(result)
    if len(rstr) > 100:
        rstr = rstr[:97] + "..."
    print(f"{indent}{label:<40} {tag:<6} {rstr}")
    return result


def probe(mpi, indent: str = "    ") -> None:
    present = [m for m in CANDIDATES if getattr(mpi, m, None) is not None]
    absent  = [m for m in CANDIDATES if getattr(mpi, m, None) is None]
    print(f"{indent}Present:  {present}")
    if absent:
        print(f"{indent}Absent:   {absent}")

    _c(mpi, "GetName()", mpi.GetName, indent=indent)
    if getattr(mpi, "GetMediaId", None):
        _c(mpi, "GetMediaId()", mpi.GetMediaId, indent=indent)
    if getattr(mpi, "GetUniqueId", None):
        _c(mpi, "GetUniqueId()", mpi.GetUniqueId, indent=indent)
    _c(mpi, "GetClipProperty()", mpi.GetClipProperty, indent=indent)

    for key in CLIP_PROP_SPOT_KEYS:
        try:
            val = mpi.GetClipProperty(key)
        except Exception:
            val = None
        if val not in (None, False, ""):
            print(f"{indent}  GetClipProperty({key!r}) → {val!r}")

    if getattr(mpi, "GetMetadata", None):
        _c(mpi, "GetMetadata()", mpi.GetMetadata, indent=indent)
    if getattr(mpi, "GetThirdPartyMetadata", None):
        _c(mpi, "GetThirdPartyMetadata()", mpi.GetThirdPartyMetadata, indent=indent)
    if getattr(mpi, "GetTranscript", None):
        _c(mpi, "GetTranscript()", mpi.GetTranscript, indent=indent)
