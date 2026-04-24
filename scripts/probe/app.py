"""Probe: Resolve top-level app object."""
from __future__ import annotations

from ._fmt import call, probe_methods, section, subsection

CANDIDATES = [
    "GetProductVersion",
    "GetCurrentPage",
    "OpenPage",
    "GetMediaStorage",
    "GetProjectManager",
    "GetVersion",
    "GetVersionString",
    "Quit",
]


def probe(resolve) -> None:
    section("1. Resolve (top-level)")

    subsection("Identity")
    call("type(resolve)", type, resolve)

    subsection("Methods")
    probe_methods(resolve, CANDIDATES)

    subsection("Calls")
    call("GetProductVersion()", resolve.GetProductVersion)
    call("GetCurrentPage()", resolve.GetCurrentPage)
    if getattr(resolve, "GetVersionString", None):
        call("GetVersionString()", resolve.GetVersionString)
    if getattr(resolve, "GetVersion", None):
        call("GetVersion()", resolve.GetVersion)
