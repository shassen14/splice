"""Probe NodeGraph nodes and try SetLUT via clip directly."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from splice.resolve.client import get_resolve, get_current_timeline

LUT_ABS = str(Path("/Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT/splice_test_warm.cube").resolve())
LUT_REL = "splice_test_warm.cube"


def main():
    resolve = get_resolve()
    timeline = get_current_timeline()
    clip = timeline.GetItemListInTrack("video", 1)[0]
    print(f"Clip: {clip.GetName()}")

    resolve.OpenPage("color")
    time.sleep(1.5)

    ng = clip.GetNodeGraph()

    # Node count and structure
    num_nodes = ng.GetNumNodes()
    print(f"ng.GetNumNodes() → {num_nodes!r}")
    for i in range(max(num_nodes or 0, 4)):
        tools = ng.GetToolsInNode(i)
        lut = ng.GetLUT(i)
        label = ng.GetNodeLabel(i)
        print(f"  node {i}: tools={tools!r}  GetLUT={lut!r}  GetNodeLabel={label!r}")

    # Try clip-level SetLUT / GetLUT
    print(f"\nclip.GetLUT()   → {clip.GetLUT()!r}")
    print(f"clip.GetLUT(1)  → {clip.GetLUT(1)!r}")
    print(f"clip.GetNumNodes() → {clip.GetNumNodes()!r}")

    print("\nclip.SetLUT probing:")
    for args in [
        (LUT_ABS,),
        (1, LUT_ABS),
        (LUT_REL,),
        (1, LUT_REL),
    ]:
        try:
            r = clip.SetLUT(*args)
            print(f"  clip.SetLUT{args} → {r!r}")
        except Exception as e:
            print(f"  clip.SetLUT{args} → Exception: {e}")

    print(f"\nclip.GetLUT(1) after → {clip.GetLUT(1)!r}")
    print(f"ng.GetLUT(1) after   → {ng.GetLUT(1)!r}")


if __name__ == "__main__":
    main()
