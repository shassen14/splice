from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Layout(str, Enum):
    SPLIT_V = "split-v"
    SPLIT_H = "split-h"
    PIP_CORNER = "pip-corner"
    CODE_ME = "code-me"


@dataclass
class LayoutApplier:
    """Apply a Fusion comp layout preset to every clip on the active timeline."""

    layout: Layout

    def run(self, timeline) -> None:
        # TODO: build Fusion comp nodes for each layout variant and inject into timeline clips
        raise NotImplementedError(f"LayoutApplier({self.layout.value!r})")
