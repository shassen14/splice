"""Probe: TimelineItem — audio tracks (section 5) and video tracks (section 6)."""
from __future__ import annotations

from . import mpi as mpi_probe
from ._fmt import call, probe_methods, section, subsection

_AUDIO_PROP_KEYS = [
    "volume", "Volume", "pan", "Pan",
    "Enabled", "enabled", "Clip Volume", "AudioLevel",
    "gain", "Gain", "level", "Level",
    "pitchAdjust", "speed", "compositeMode", "opacity",
    # Additional candidates for 20.3+
    "clipVolume", "audioLevel", "clipLevel", "dBFS",
    "VolumeDB", "volumeDB", "FaderValue", "faderValue",
]

# Extra method candidates added in 20.3 or not yet probed
_AUDIO_METHOD_CANDIDATES = [
    "GetProperty", "SetProperty",
    "GetVolume", "SetVolume",
    "GetStart", "GetEnd", "GetDuration",
    "GetName", "GetMediaPoolItem", "GetLinkedItems",
    "GetFlagList", "AddFlag", "ClearFlags",
    "GetClipColor", "SetClipColor",
    "GetMarkers", "AddMarker",
    "GetFusionCompCount",
    "GetNodeGraph",
]

_VIDEO_PROP_KEYS = [
    "Pan", "Tilt", "ZoomX", "ZoomY", "ZoomGang", "RotationAngle",
    "AnchorPointX", "AnchorPointY", "Pitch", "Yaw",
    "FlipX", "FlipY",
    "CropLeft", "CropRight", "CropTop", "CropBottom",
    "Enabled", "enabled", "volume", "Volume",
    "opacity", "compositeMode", "speed", "pitchAdjust", "retimeProcess",
]


def _probe_timing(item) -> None:
    call("  GetStart()", item.GetStart)
    call("  GetEnd()", item.GetEnd)
    call("  GetDuration()", item.GetDuration)
    call("  GetSourceStartTime()", item.GetSourceStartTime)
    call("  GetSourceEndTime()", item.GetSourceEndTime)


def _probe_misc(item) -> None:
    call("  GetClipColor()", item.GetClipColor)
    call("  GetFlagList()", item.GetFlagList)
    call("  GetMarkers()", item.GetMarkers)
    call("  GetLinkedItems()", item.GetLinkedItems)
    call("  GetFusionCompCount()", item.GetFusionCompCount)


def _probe_keyed_props(item, keys: list[str]) -> None:
    found_any = False
    for key in keys:
        try:
            val = item.GetProperty(key)
        except Exception:
            val = None
        if val not in (None, False, ""):
            call(f"  GetProperty({key!r})", item.GetProperty, key)
            found_any = True
    if not found_any:
        print("  GetProperty(key) → all tested keys returned None/False/empty")


def _probe_mpi(item) -> None:
    mpi = item.GetMediaPoolItem() if getattr(item, "GetMediaPoolItem", None) else None
    if mpi is None:
        print("  GetMediaPoolItem() → None")
        return
    print("  GetMediaPoolItem() → OK")
    mpi_probe.probe(mpi)


def _probe_audio_volume_roundtrip(item) -> None:
    print()
    print("  [volume round-trip] Testing SetProperty/GetProperty on audio item:")

    # Step 1: read current value
    current = item.GetProperty("volume")
    print(f"    GetProperty('volume') before write: {current!r}")

    # Step 2: set to a known value
    try:
        item.SetProperty("volume", -6.0)
    except Exception as e:
        print(f"    SetProperty('volume', -6.0) → FAIL: {e}")
        return

    # Step 3: read back
    readback = item.GetProperty("volume")
    print(f"    GetProperty('volume') after SetProperty(-6.0): {readback!r}")

    if readback is not None:
        print("    *** VOLUME READBACK WORKS IN THIS VERSION ***")
    else:
        print("    *** VOLUME READBACK STILL BROKEN — write may still apply visually ***")

    # Step 4: try 'Volume' (capital V)
    item.SetProperty("Volume", -6.0)
    readback_cap = item.GetProperty("Volume")
    print(f"    GetProperty('Volume') [capital V] after SetProperty: {readback_cap!r}")

    # Step 5: restore original
    restore_val = float(current) if current is not None else 0.0
    item.SetProperty("volume", restore_val)
    print(f"    Restored to {restore_val}")


def probe_audio(timeline) -> None:
    section("5. TimelineItem — audio tracks")
    n_audio = timeline.GetTrackCount("audio") or 0

    for track_idx in range(1, n_audio + 1):
        items = timeline.GetItemListInTrack("audio", track_idx)
        if not items:
            print(f"\n  [audio track {track_idx}] — no clips")
            continue

        item = items[0]
        clip_name = item.GetName() if getattr(item, "GetName", None) else "?"
        subsection(f"audio track {track_idx}  —  {clip_name!r}  ({len(items)} clips total)")

        print()
        subsection(f"  Methods (track {track_idx})")
        probe_methods(item, _AUDIO_METHOD_CANDIDATES)

        print()
        _probe_timing(item)

        print()
        call("  GetProperty()", item.GetProperty)
        _probe_keyed_props(item, _AUDIO_PROP_KEYS)

        _probe_audio_volume_roundtrip(item)

        print()
        _probe_misc(item)
        print()
        _probe_mpi(item)


def probe_video(timeline) -> None:
    section("6. TimelineItem — video tracks")
    n_video = timeline.GetTrackCount("video") or 0

    for track_idx in range(1, min(n_video + 1, 4)):
        items = timeline.GetItemListInTrack("video", track_idx)
        if not items:
            print(f"\n  [video track {track_idx}] — no clips")
            continue

        item = items[0]
        clip_name = item.GetName() if getattr(item, "GetName", None) else "?"
        subsection(f"video track {track_idx}  —  {clip_name!r}  ({len(items)} clips total)")

        print()
        _probe_timing(item)

        print()
        call("  GetProperty()", item.GetProperty)
        _probe_keyed_props(item, _VIDEO_PROP_KEYS)

        print()
        print("  [round-trip] SetProperty('ZoomX', 1.5) → GetProperty('ZoomX'):")
        try:
            original = item.GetProperty("ZoomX")
            item.SetProperty("ZoomX", 1.5)
            readback = item.GetProperty("ZoomX")
            print(f"    original={original!r}  after SetProperty(1.5): GetProperty → {readback!r}")
            if original is not None:
                item.SetProperty("ZoomX", original)
        except Exception as e:
            print(f"    FAIL: {e}")

        print()
        _probe_misc(item)
        print()
        _probe_mpi(item)
        break  # one clip per track is enough for method discovery
