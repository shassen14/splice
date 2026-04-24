"""Probe: Project."""
from __future__ import annotations

from ._fmt import call, probe_methods, section, subsection

CANDIDATES = [
    "GetName", "SetName",
    "GetCurrentTimeline", "GetTimelineCount", "GetTimelineByIndex", "SetCurrentTimeline",
    "GetMediaPool",
    "GetSetting", "SetSetting",
    "GetRenderPresets", "GetRenderPresetList", "LoadRenderPreset",
    "GetRenderSettings", "SetRenderSettings",
    "AddRenderJob", "GetRenderJobList", "StartRendering", "StopRendering",
    "IsRenderingInProgress", "GetRenderJobStatus", "DeleteRenderJob", "DeleteAllRenderJobs",
    "GetCurrentRenderFormatAndCodec", "GetRenderFormats", "GetRenderCodecs",
    "GetColorGroupList", "AddColorGroup", "DeleteColorGroup",
    "GetPresetList", "GetGallery", "GetUniqueId",
]

SETTING_KEYS = [
    "timelineFrameRate",
    "timelineResolutionWidth",
    "timelineResolutionHeight",
    "colorScienceMode",
    "videoMonitorFormat",
    "audioCaptureNumChannels",
    "audioCaptureLocation",
]


def probe(project) -> None:
    section("3. Project")

    subsection("Methods")
    probe_methods(project, CANDIDATES)

    subsection("Identity / Name")
    call("GetName()", project.GetName)

    subsection("Timelines")
    count = call("GetTimelineCount()", project.GetTimelineCount)
    if count and isinstance(count, int):
        for i in range(1, min(count + 1, 4)):
            tl = call(f"GetTimelineByIndex({i})", project.GetTimelineByIndex, i)
            if tl:
                call(f"  timeline[{i}].GetName()", tl.GetName)

    subsection("Settings (known keys)")
    if getattr(project, "GetSetting", None):
        for key in SETTING_KEYS:
            call(f"GetSetting({key!r})", project.GetSetting, key)

    subsection("Render formats / codecs")
    if getattr(project, "GetRenderFormats", None):
        fmts = call("GetRenderFormats()", project.GetRenderFormats)
        if fmts and isinstance(fmts, dict):
            first_fmt = next(iter(fmts))
            call(f"GetRenderCodecs({first_fmt!r})", project.GetRenderCodecs, first_fmt)

    if getattr(project, "GetRenderPresets", None):
        call("GetRenderPresets()", project.GetRenderPresets)
    elif getattr(project, "GetRenderPresetList", None):
        call("GetRenderPresetList()", project.GetRenderPresetList)

    subsection("Current render format + codec")
    if getattr(project, "GetCurrentRenderFormatAndCodec", None):
        call("GetCurrentRenderFormatAndCodec()", project.GetCurrentRenderFormatAndCodec)

    subsection("Render settings")
    if getattr(project, "GetRenderSettings", None):
        call("GetRenderSettings()", project.GetRenderSettings)

    subsection("Render job list")
    if getattr(project, "GetRenderJobList", None):
        call("GetRenderJobList()", project.GetRenderJobList)
