"""Probe: ProjectManager."""
from __future__ import annotations

from ._fmt import call, probe_methods, section, subsection

CANDIDATES = [
    "GetCurrentProject",
    "GetProjectListInCurrentFolder",
    "GetProjectList",
    "GetCurrentFolder",
    "GetFolderList",
    "CreateProject",
    "OpenFolder",
    "GotoRootFolder",
    "GotoParentFolder",
    "GetCurrentFolderName",
]


def probe(pm) -> None:
    section("2. ProjectManager")

    subsection("Methods")
    probe_methods(pm, CANDIDATES)

    subsection("Calls")
    if getattr(pm, "GetCurrentFolder", None):
        call("GetCurrentFolder()", pm.GetCurrentFolder)
    if getattr(pm, "GetCurrentFolderName", None):
        call("GetCurrentFolderName()", pm.GetCurrentFolderName)

    fn = getattr(pm, "GetProjectListInCurrentFolder", None) or getattr(pm, "GetProjectList", None)
    if fn:
        call("GetProjectListInCurrentFolder()", fn)
