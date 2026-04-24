"""Probe: Fairlight audio API.

Tests whether TimelineItem exposes FairlightAudioClip objects with
proper volume read/write — separate from the broken GetProperty("volume") path.
"""
from __future__ import annotations

from ._fmt import call, probe_methods, section, subsection

# Fairlight-specific methods on TimelineItem (Resolve 18+)
TI_FAIRLIGHT_CANDIDATES = [
    "GetFairlightAudioClips",
    "GetAudioMapping",
    "SetAudioMapping",
    "GetFairlightAudioLoudness",
]

# FairlightAudioClip object
FAC_CANDIDATES = [
    "GetVolume", "SetVolume",
    "GetPan", "SetPan",
    "GetStart", "GetEnd", "GetDuration",
    "GetEnabled", "SetEnabled",
    "GetNodeGraph",
    "GetName",
]


def _probe_fac(fac, label: str) -> None:
    subsection(f"FairlightAudioClip — {label}")
    probe_methods(fac, FAC_CANDIDATES)

    call("  GetVolume()", fac.GetVolume) if getattr(fac, "GetVolume", None) else None
    call("  GetEnabled()", fac.GetEnabled) if getattr(fac, "GetEnabled", None) else None

    # Volume round-trip
    get_vol = getattr(fac, "GetVolume", None)
    set_vol = getattr(fac, "SetVolume", None)
    if get_vol and set_vol:
        print()
        print("  [volume round-trip]")
        before = call("  GetVolume() before", get_vol)
        call("  SetVolume(-6.0)", set_vol, -6.0)
        after = call("  GetVolume() after SetVolume(-6.0)", get_vol)
        if after is not None and after != before:
            print("  *** FAIRLIGHT VOLUME READ/WRITE WORKS ***")
        elif after == -6.0 or (isinstance(after, (int, float)) and abs(float(after) - (-6.0)) < 0.01):
            print("  *** FAIRLIGHT VOLUME READ/WRITE WORKS ***")
        else:
            print("  *** FAIRLIGHT VOLUME WRITE UNCONFIRMED — readback unchanged or None ***")
        # Restore
        if before is not None:
            set_vol(before)
            print(f"  Restored to {before}")


def probe(timeline) -> None:
    section("10. Fairlight Audio API")

    n_audio = timeline.GetTrackCount("audio") or 0
    if n_audio == 0:
        print("  No audio tracks — skipping.")
        return

    for track_idx in range(1, min(n_audio + 1, 4)):
        clips = timeline.GetItemListInTrack("audio", track_idx)
        if not clips:
            continue
        item = clips[0]
        clip_name = item.GetName() if getattr(item, "GetName", None) else "?"

        subsection(f"audio track {track_idx} — {clip_name!r}")
        probe_methods(item, TI_FAIRLIGHT_CANDIDATES)

        get_fac = getattr(item, "GetFairlightAudioClips", None)
        if not get_fac:
            print("  GetFairlightAudioClips absent on this item.")
            continue

        fac_list = call("  GetFairlightAudioClips()", get_fac)
        if not fac_list:
            print("  GetFairlightAudioClips() returned empty/None.")
            continue

        print(f"  → {len(fac_list)} FairlightAudioClip object(s)")
        _probe_fac(fac_list[0], f"track {track_idx}, clip 0")
        break  # one track is enough to confirm the API shape
