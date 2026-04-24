"""Probe: Timeline."""
from __future__ import annotations

from ._fmt import call, probe_methods, section, subsection

CANDIDATES = [
    "GetName", "SetName",
    "GetStartFrame", "GetEndFrame",
    "GetCurrentTimecode", "SetCurrentTimecode",
    "GetTrackCount", "GetItemListInTrack",
    "GetTrackName", "SetTrackName",
    "SetTrackEnable", "GetIsTrackEnabled", "GetTrackEnabled",
    "GetSetting", "SetSetting",
    "GetCurrentVideoItem",
    "AddMarker", "GetMarkers",
    "DeleteMarker", "DeleteMarkersByColor", "DeleteMarkerAtFrame",
    "GrabAllStills", "GrabStill",
    "ApplyGradeFromDRX", "Export", "GetUniqueId",
]

SETTING_KEYS = [
    "timelineFrameRate",
    "timelineResolutionWidth",
    "timelineResolutionHeight",
    "timelinePlaybackFrameRate",
    "durationTimecode",
    "startTimecode",
]


def probe(timeline) -> None:
    section("4. Timeline")

    subsection("Methods")
    probe_methods(timeline, CANDIDATES)

    subsection("Identity")
    call("GetName()", timeline.GetName)
    call("GetStartFrame()", timeline.GetStartFrame)
    call("GetEndFrame()", timeline.GetEndFrame)
    call("GetCurrentTimecode()", timeline.GetCurrentTimecode)

    subsection("Track counts")
    for track_type in ("video", "audio", "subtitle"):
        call(f"GetTrackCount({track_type!r})", timeline.GetTrackCount, track_type)

    n_audio = timeline.GetTrackCount("audio") or 0
    n_video = timeline.GetTrackCount("video") or 0

    subsection("Track names")
    if getattr(timeline, "GetTrackName", None):
        for i in range(1, n_audio + 1):
            call(f"GetTrackName('audio', {i})", timeline.GetTrackName, "audio", i)
        for i in range(1, min(n_video + 1, 4)):
            call(f"GetTrackName('video', {i})", timeline.GetTrackName, "video", i)

    subsection("Track enabled state")
    if getattr(timeline, "GetIsTrackEnabled", None):
        for i in range(1, min(n_audio + 1, 4)):
            call(f"GetIsTrackEnabled('audio', {i})", timeline.GetIsTrackEnabled, "audio", i)
        for i in range(1, min(n_video + 1, 3)):
            call(f"GetIsTrackEnabled('video', {i})", timeline.GetIsTrackEnabled, "video", i)

    subsection("GetSetting (known keys)")
    if getattr(timeline, "GetSetting", None):
        for key in SETTING_KEYS:
            call(f"GetSetting({key!r})", timeline.GetSetting, key)

    subsection("Markers")
    if getattr(timeline, "GetMarkers", None):
        call("GetMarkers()", timeline.GetMarkers)

    subsection("Current video item")
    if getattr(timeline, "GetCurrentVideoItem", None):
        call("GetCurrentVideoItem()", timeline.GetCurrentVideoItem)
