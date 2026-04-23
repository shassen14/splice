from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import cv2
import numpy as np


@dataclass
class BoundingBox:
    x: int
    y: int
    w: int
    h: int


@dataclass
class Keyframe:
    frame: int
    box: BoundingBox


class CSRTTracker:
    """Track a subject through a video using OpenCV's CSRT algorithm.

    If no initial_box is provided the tracker heuristically selects the
    largest detected person in the first frame. Pass initial_box to override.
    """

    def __init__(self, initial_box: Optional[BoundingBox] = None) -> None:
        self._initial_box = initial_box

    def _detect_largest_person(self, frame: np.ndarray) -> Optional[BoundingBox]:
        hog = cv2.HOGDescriptor()
        hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        boxes, _ = hog.detectMultiScale(frame, winStride=(8, 8))
        if len(boxes) == 0:
            return None
        x, y, w, h = max(boxes, key=lambda b: b[2] * b[3])
        return BoundingBox(int(x), int(y), int(w), int(h))

    def track(
        self,
        video_path: Path,
        start_frame: int = 0,
        end_frame: Optional[int] = None,
    ) -> list[Keyframe]:
        cap = cv2.VideoCapture(str(video_path))
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if end_frame is None:
            end_frame = total - 1

        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        ok, first = cap.read()
        if not ok:
            raise ValueError(f"Cannot read frame {start_frame} from {video_path}")

        initial_box = self._initial_box or self._detect_largest_person(first)
        if initial_box is None:
            raise ValueError(
                "No subject detected in first frame. "
                "Pass initial_box= to CSRTTracker to specify the target manually."
            )

        tracker = cv2.TrackerCSRT_create()
        tracker.init(first, (initial_box.x, initial_box.y, initial_box.w, initial_box.h))

        keyframes: list[Keyframe] = [Keyframe(start_frame, initial_box)]
        for frame_idx in range(start_frame + 1, end_frame + 1):
            ok, frame = cap.read()
            if not ok:
                break
            success, (x, y, w, h) = tracker.update(frame)
            if success:
                keyframes.append(
                    Keyframe(frame_idx, BoundingBox(int(x), int(y), int(w), int(h)))
                )

        cap.release()
        return keyframes
