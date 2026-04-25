from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

_RESOLVE_LUT_DIR = Path(
    "/Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT"
)
_NODE_INDEX = 1


@dataclass
class LUTPass:
    """Apply a .cube LUT to every video clip on track 1."""

    lut_path: Path

    def run(self, timeline) -> None:
        from splice.resolve.client import get_resolve

        lut_path = Path(self.lut_path).resolve()
        if not lut_path.exists():
            raise FileNotFoundError(lut_path)

        # Resolve only sees LUT files inside its LUT directory.
        # Copy the file there if it isn't already, then refresh.
        dest = _RESOLVE_LUT_DIR / lut_path.name
        if not dest.exists():
            shutil.copy2(lut_path, dest)

        project = get_resolve().GetProjectManager().GetCurrentProject()
        project.RefreshLUTList()

        video_track_count = timeline.GetTrackCount("video")
        applied = 0
        failed = 0
        for track in range(1, video_track_count + 1):
            for item in timeline.GetItemListInTrack("video", track):
                ng = item.GetNodeGraph()
                if ng is None:
                    continue
                ok = ng.SetLUT(_NODE_INDEX, str(dest))
                if ok:
                    applied += 1
                else:
                    failed += 1

        print(f"LUTPass: applied={applied} failed={failed} lut={dest.name}")


@dataclass
class AWBPass:
    """Run Resolve's auto white balance on every clip."""

    def run(self, timeline) -> None:
        raise NotImplementedError(
            "AWBPass: auto white balance has no Python API surface in Resolve 20"
        )


@dataclass
class GradePass:
    """Apply a named still/grade preset from the Resolve gallery to every clip."""

    preset_name: str

    def run(self, timeline) -> None:
        # TODO: access gallery stills, match by preset_name, apply grade to each clip
        raise NotImplementedError(f"GradePass({self.preset_name!r})")
