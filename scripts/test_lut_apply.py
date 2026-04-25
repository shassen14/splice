"""
Test whether NodeGraph.SetLUT() visually commits in Resolve.

Applies test_lut.cube to the first video clip on track 1 of the active timeline.
Check the Color page after running — the clip should show a warm tint (more red, less blue).
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from splice.resolve.client import get_resolve, get_current_timeline

LUT_FULL = Path("/Users/samir/Documents/projects/media_os/splice/test_lut.cube").resolve()
LUT_SYSTEM = Path("/Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT/splice_test_warm.cube")


def try_set_lut(ng, path: str, label: str):
    r1 = ng.SetLUT(path)
    r2 = ng.SetLUT(1, path)
    rb = ng.GetLUT(1)
    print(f"  [{label}] SetLUT(path)={r1!r}  SetLUT(1,path)={r2!r}  GetLUT(1)={rb!r}")
    return r1, r2


def main():
    resolve = get_resolve()
    if resolve is None:
        print("Resolve is not running or no Studio license.")
        sys.exit(1)

    timeline = get_current_timeline()
    print(f"Timeline: {timeline.GetName()}")

    video_items = timeline.GetItemListInTrack("video", 1)
    if not video_items:
        print("No video clips on track 1.")
        sys.exit(1)

    clip = video_items[0]
    print(f"Clip: {clip.GetName()}")

    # Switch to Color page — SetLUT may require it
    print("Switching to Color page...")
    resolve.OpenPage("color")
    time.sleep(1.5)

    ng = clip.GetNodeGraph()
    if ng is None:
        print("GetNodeGraph() returned None.")
        sys.exit(1)

    print("Trying full absolute path:")
    try_set_lut(ng, str(LUT_FULL), "abs path")

    print("Trying system LUT path:")
    try_set_lut(ng, str(LUT_SYSTEM), "system path")

    # Resolve may also accept just the filename relative to its LUT root
    print("Trying LUT filename only:")
    try_set_lut(ng, "splice_test_warm.cube", "filename only")

    rb_final = ng.GetLUT(1)
    print(f"\nFinal GetLUT(1) → {rb_final!r}")
    if rb_final:
        print("LUT is registered on node 1 — check Color page for visual effect.")
    else:
        print("GetLUT(1) still empty — SetLUT is not committing.")


if __name__ == "__main__":
    main()
