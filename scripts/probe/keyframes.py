"""Probe: Keyframe API on TimelineItem.

Tests whether Resolve 20.3+ exposes per-frame keyframe writes for
inspector transform properties (Pan, Tilt, ZoomX, etc.).

Called with a video TimelineItem that has at least one clip.
"""
from __future__ import annotations

from ._fmt import call, probe_methods, section, subsection

# All known/speculated keyframe method names across Resolve versions
KEYFRAME_CANDIDATES = [
    # Direct keyframe write/read
    "AddKeyframe",
    "DeleteKeyframeAtFrame",
    "DeleteKeyframesInRange",
    "GetKeyframes",
    "GetKeyframeList",
    "SetPropertyKeyframe",
    "SetPropertyKeyframeValue",
    "GetPropertyKeyframeValue",
    "SetPropertyKeyframes",
    "GetPropertyKeyframes",
    # Enable/disable animation on a property
    "SetKeyframeEnabled",
    "GetKeyframeEnabled",
    "SetPropertyAnimated",
    "GetPropertyAnimated",
    # Dynamic zoom (a separate system in Resolve)
    "GetDynamicZoomEase",
    "SetDynamicZoomEase",
    "GetStereoConvergenceValues",
    "GetStereoLeftFloatingWindowParams",
    "SetStereoLeftFloatingWindowParams",
    # Retime / speed
    "GetRetimeValues",
    "SetRetimeValues",
]

# Transform property keys we care most about for tracking
TRACK_PROPS = ["Pan", "Tilt", "ZoomX", "ZoomY", "RotationAngle"]


def _test_prop_roundtrip(item, key: str, test_val: float) -> None:
    original = item.GetProperty(key)
    item.SetProperty(key, test_val)
    readback = item.GetProperty(key)
    restored = original if original is not None else test_val
    item.SetProperty(key, restored)
    match = (
        "MATCH" if (readback is not None and abs(float(readback) - test_val) < 0.001)
        else f"MISMATCH (got {readback!r})"
    )
    print(f"    {key:<20} set={test_val}  read={readback!r}  → {match}")


def _test_getproperty_at_frame(item, key: str, frame: int) -> None:
    """Test whether GetProperty accepts a frame argument (per-frame value)."""
    try:
        val = item.GetProperty(key, frame)
        print(f"    GetProperty({key!r}, frame={frame}) → {val!r}  [FRAME ARG ACCEPTED]")
    except TypeError as e:
        print(f"    GetProperty({key!r}, frame={frame}) → TypeError: {e}  [no frame arg]")
    except Exception as e:
        print(f"    GetProperty({key!r}, frame={frame}) → {type(e).__name__}: {e}")


def probe(video_item) -> None:
    section("9. Keyframe API")

    subsection("Keyframe method candidates on TimelineItem")
    probe_methods(video_item, KEYFRAME_CANDIDATES)

    subsection("GetProperty round-trip — transform properties")
    print("  (original values are restored after each test)")
    for key in TRACK_PROPS:
        try:
            _test_prop_roundtrip(video_item, key, 0.25)
        except Exception as e:
            print(f"    {key:<20} FAIL: {e}")

    subsection("GetProperty with frame argument (per-frame read)")
    start = video_item.GetStart() if getattr(video_item, "GetStart", None) else 0
    test_frame = start + 5
    for key in ["Pan", "ZoomX"]:
        _test_getproperty_at_frame(video_item, key, test_frame)

    subsection("SetProperty with frame dict (per-frame write attempt)")
    # Some Resolve versions accept {frame: value} dict as the value argument.
    # Test this without clobbering the clip — set and immediately revert.
    original_pan = video_item.GetProperty("Pan")
    for attempt_val in [
        {test_frame: 0.1},                  # frame→value dict
        {str(test_frame): 0.1},              # string key variant
        (test_frame, 0.1),                   # tuple variant
    ]:
        try:
            result = video_item.SetProperty("Pan", attempt_val)
            readback = video_item.GetProperty("Pan")
            print(f"    SetProperty('Pan', {attempt_val!r}) → {result!r}  readback={readback!r}")
        except Exception as e:
            print(f"    SetProperty('Pan', {attempt_val!r}) → {type(e).__name__}: {e}")
        finally:
            # Always restore
            video_item.SetProperty("Pan", original_pan if original_pan is not None else 0.0)

    subsection("AddKeyframe (if present)")
    add_kf = getattr(video_item, "AddKeyframe", None)
    if not add_kf:
        print("  AddKeyframe absent — per-frame keyframe writes not available via this method.")
    else:
        # Try calling it — Resolve keyframe types: 0=All, 1=Color, 2=Sizing
        result = call("AddKeyframe(frame, 2)", add_kf, test_frame, 2)
        print(f"  AddKeyframe present. Result: {result!r}")
