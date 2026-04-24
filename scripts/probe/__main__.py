"""
DaVinci Resolve scripting API probe.

Run with Resolve open, a project loaded, and at least one timeline active:

    cd /Users/samir/Documents/projects/media_os/splice
    uv run python scripts/probe

Pipe to a file to preserve the run:
    uv run python scripts/probe 2>&1 | tee docs/probe_output_$(date +%Y%m%d).txt
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

from . import app, items, media_pool, pm, project, timeline
from ._fmt import W


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

    print(f"\n{'=' * W}")
    print("  Probe complete.")
    print(f"{'=' * W}\n")


if __name__ == "__main__":
    main()
