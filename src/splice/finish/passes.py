from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class IntroPass:
    """Prepend an intro clip at the start of the timeline."""

    clip_path: Path
    duration_frames: Optional[int] = None   # None → use clip's native duration

    def run(self, timeline) -> None:
        # TODO: insert media pool item at frame 0, shift existing clips right
        raise NotImplementedError(f"IntroPass({self.clip_path})")


@dataclass
class OutroPass:
    """Append an outro clip at the end of the timeline."""

    clip_path: Path

    def run(self, timeline) -> None:
        # TODO: find last clip end frame, append media pool item
        raise NotImplementedError(f"OutroPass({self.clip_path})")


@dataclass
class LowerThirdsPass:
    """Overlay lower-third title clips at specified timecodes.

    Each cue: {"text": str, "start_frame": int, "duration_frames": int}
    """

    cues: list[dict] = field(default_factory=list)

    def run(self, timeline) -> None:
        # TODO: create Fusion title comps or use media pool titles, place on subtitle track
        raise NotImplementedError(f"LowerThirdsPass({len(self.cues)} cues)")
