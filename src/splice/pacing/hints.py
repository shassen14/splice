from __future__ import annotations

import math
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np


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
        with wave.open(str(audio_path), "rb") as wf:
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            rate = wf.getframerate()
            raw = wf.readframes(wf.getnframes())

        if sampwidth == 2:
            pcm = np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32_768.0
        elif sampwidth == 4:
            pcm = np.frombuffer(raw, dtype=np.int32).astype(np.float64) / 2_147_483_648.0
        else:
            raise ValueError(f"Unsupported WAV sample width: {sampwidth} bytes")

        mono = pcm.reshape(-1, n_channels).mean(axis=1)

        # 50ms frames — vectorised RMS
        frame = max(1, int(rate * 0.05))
        n_frames = math.ceil(len(mono) / frame)
        padded = np.zeros(n_frames * frame)
        padded[: len(mono)] = mono
        blocks = padded.reshape(n_frames, frame)
        rms = np.sqrt(np.mean(blocks ** 2, axis=1))
        rms_db = 20.0 * np.log10(np.maximum(rms, 1e-10))
        is_silent = rms_db < self.silence_db

        frame_sec = frame / rate
        windows: list[SilenceWindow] = []
        start = -1
        for i, silent in enumerate(is_silent):
            if silent and start < 0:
                start = i
            elif not silent and start >= 0:
                dur = (i - start) * frame_sec
                if dur >= self.min_gap_seconds:
                    windows.append(SilenceWindow(start * frame_sec, i * frame_sec))
                start = -1
        if start >= 0:
            dur = (len(is_silent) - start) * frame_sec
            if dur >= self.min_gap_seconds:
                windows.append(SilenceWindow(start * frame_sec, len(is_silent) * frame_sec))

        return windows


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
