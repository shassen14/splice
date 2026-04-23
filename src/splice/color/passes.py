from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class LUTPass:
    """Apply a .cube LUT to every clip on the color track."""

    lut_path: Path

    def run(self, timeline) -> None:
        # TODO: use Resolve color API to attach LUT node to each clip in the color page
        raise NotImplementedError(f"LUTPass({self.lut_path})")


@dataclass
class AWBPass:
    """Run Resolve's auto white balance on every clip."""

    def run(self, timeline) -> None:
        # TODO: iterate clips, call color page auto-balance API per clip
        raise NotImplementedError("AWBPass")


@dataclass
class GradePass:
    """Apply a named still/grade preset from the Resolve gallery to every clip."""

    preset_name: str

    def run(self, timeline) -> None:
        # TODO: access gallery stills, match by preset_name, apply grade to each clip
        raise NotImplementedError(f"GradePass({self.preset_name!r})")
