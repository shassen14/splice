from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Pass(Protocol):
    def run(self, timeline) -> None: ...


class Pipeline:
    """Compose and run an ordered sequence of passes against a timeline."""

    def __init__(self, passes: list[Pass]) -> None:
        self._passes = passes

    def run(self, timeline) -> None:
        for p in self._passes:
            p.run(timeline)
