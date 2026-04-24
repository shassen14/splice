"""
DaVinci Resolve scripting API probe.

Run with Resolve open, a project loaded, and at least one timeline active:

    cd /Users/samir/Documents/projects/media_os/splice
    uv run python -m scripts.probe

Pipe to a file to preserve the run:
    uv run python -m scripts.probe 2>&1 | tee docs/probe_output_$(date +%Y%m%d).txt
"""
from __future__ import annotations

import sys

try:
    import DaVinciResolveScript as dvr
except ImportError:
    raise SystemExit(
        "DaVinciResolveScript not found.\n"
        "Is Resolve running and PYTHONPATH set to its scripting directory?"
    )

from . import app, color, fairlight, fusion, items, keyframes, media_pool, pm, project, timeline
from ._fmt import W


def _first_video_item(tl):
    """Return the first video TimelineItem found, or None."""
    n = tl.GetTrackCount("video") if getattr(tl, "GetTrackCount", None) else 0
    for i in range(1, n + 1):
        clips = tl.GetItemListInTrack("video", i)
        if clips:
            return clips[0]
    return None


def main() -> None:
    resolve = dvr.scriptapp("Resolve")

    app.probe(resolve)

    mgr = resolve.GetProjectManager()
    pm.probe(mgr)

    proj = mgr.GetCurrentProject()
    if proj is None:
        sys.exit("No project open in Resolve.")
    project.probe(proj)

    tl = proj.GetCurrentTimeline()
    if tl is None:
        sys.exit("No active timeline in the current project.")
    timeline.probe(tl)

    items.probe_audio(tl)
    items.probe_video(tl)

    media_pool.probe(proj)

    # Fairlight audio probe
    fairlight.probe(tl)

    # Color, keyframe, and Fusion probes require a video item
    video_item = _first_video_item(tl)
    if video_item is None:
        print("\n  [color/keyframe/fusion probes skipped — no video clips on timeline]")
    else:
        color.probe(video_item, proj)
        keyframes.probe(video_item)
        fusion.probe(video_item)

    print(f"\n{'=' * W}")
    print("  Probe complete.")
    print(f"{'=' * W}\n")


if __name__ == "__main__":
    main()
