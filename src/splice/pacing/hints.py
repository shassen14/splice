from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class SilenceWindow:
    start_sec: float
    end_sec: float

    @property
    def duration_sec(self) -> float:
        return self.end_sec - self.start_sec


@dataclass
class CutHint:
    frame: int
    reason: str
    confidence: float   # 0.0–1.0


class SilenceDetector:
    """Detect silence windows in an audio file by RMS thresholding."""

    def __init__(
        self,
        silence_db: float = -40.0,
        min_gap_seconds: float = 0.5,
    ) -> None:
        self.silence_db = silence_db
        self.min_gap_seconds = min_gap_seconds

    def detect(self, audio_path: Path) -> list[SilenceWindow]:
        # TODO: load with soundfile, compute RMS per frame, threshold at silence_db,
        #       merge windows shorter than min_gap_seconds
        raise NotImplementedError("SilenceDetector.detect")


class CutAdvisor:
    """Suggest cut points based on silence windows and scene changes."""

    def __init__(
        self,
        silence_detector: Optional[SilenceDetector] = None,
        scene_change_threshold: float = 30.0,
    ) -> None:
        self.silence_detector = silence_detector or SilenceDetector()
        self.scene_change_threshold = scene_change_threshold

    def suggest(self, timeline, audio_path: Optional[Path] = None) -> list[CutHint]:
        # TODO:
        #   1. silence_detector.detect(audio_path) → natural pause points
        #   2. OpenCV frame-diff → scene change frames above scene_change_threshold
        #   3. merge, deduplicate, rank by confidence
        raise NotImplementedError("CutAdvisor.suggest")
