---
tags: [davinci-resolve, api, reference]
type: reference
created: 2026-04-24
updated: 2026-04-24
resolve_version: 20.0.0.49
---

# DaVinci Resolve Python Scripting API — Field Guide

> Living reference backed by `scripts/probe_resolve.py` runs.
> Every claim is tagged: **[confirmed]** = seen in probe output, **[from code]** = used in passes.py and working in practice, **[untested]** = not yet probed.
> Re-run probe after Resolve updates and reconcile.

**Resolve version probed: 20.0.0.49**

---

## Object Hierarchy

```
Resolve                        ← dvr.scriptapp("Resolve")
└── ProjectManager             ← resolve.GetProjectManager()
    └── Project                ← pm.GetCurrentProject()
        ├── Timeline[]         ← project.GetTimelineByIndex(i)  (1-based)
        │   └── TimelineItem[] ← timeline.GetItemListInTrack(type, track_idx)
        │       └── MediaPoolItem  ← item.GetMediaPoolItem()
        └── MediaPool          ← project.GetMediaPool()
            └── Folder (root "Master")
                └── Folder[]   ← folder.GetSubFolderList()
                    └── MediaPoolItem[]
```

All objects are `BlackmagicFusion.PyRemoteObject` — opaque IPC proxies.
Method discovery requires `getattr(obj, name, None) is not None`.

---

## Critical Asymmetry: GetProperty on Audio vs Video Items

**This is the single most important finding.**

| Item type | `GetProperty()` no-arg | `GetProperty(key)` |
|-----------|------------------------|---------------------|
| Video TimelineItem | Returns full transform dict ✓ | Keys work ✓ |
| Audio TimelineItem | Returns `{}` | All keys return `None` |
| Audio-only clip | Returns `{}` | All keys return `None` |

`GetProperty` is **not usable for reading audio clip state**.
`SetProperty("volume", db)` on audio items: the call does not raise, but
`GetProperty("volume")` returns `None` afterwards. Whether the value is silently
discarded or simply unreadable is unconfirmed — **visual verification required after
every audio pass**.

---

## Resolve (top-level)

| Method | Returns | Notes |
|--------|---------|-------|
| `GetProjectManager()` | ProjectManager | **[confirmed]** |
| `GetCurrentPage()` | `str` | `'edit'`, `'fairlight'`, `'deliver'`, `'fusion'`, `'color'`, `'media'`, `'cut'` **[confirmed]** |
| `GetVersionString()` | `str` | `'20.0.0.49'` **[confirmed]** — use this, not `GetProductVersion` |
| `OpenPage(page)` | `bool` | **[confirmed working]** — valid pages: `"media"`, `"cut"`, `"edit"`, `"fusion"`, `"color"`, `"fairlight"`, `"deliver"` |
| `GetMediaStorage()` | MediaStorage | **[confirmed present, not yet probed]** |
| `GetVersion()` | unknown | **[confirmed present, not yet called]** |

**`GetProductVersion` is absent in Resolve 20.** Use `GetVersionString()`.

---

## ProjectManager

| Method | Returns | Notes |
|--------|---------|-------|
| `GetCurrentProject()` | Project | **[confirmed]** — `None` if no project open |
| `GetProjectListInCurrentFolder()` | `list[str]` | **[confirmed]** — project names |
| `GetCurrentFolder()` | `str` | **[confirmed]** — returns `''` (empty string) when at root; not `None` |
| `CreateProject(name)` | Project | **[confirmed present, not called]** |
| `OpenFolder(path)` | `bool` | **[confirmed present, not called]** |
| `GotoRootFolder()` | `bool` | **[confirmed present, not called]** |
| `GotoParentFolder()` | `bool` | **[confirmed present, not called]** |

`GetFolderList`, `GetCurrentFolderName`, `GetProjectList` are **absent** in Resolve 20.

---

## Project

### Methods

| Method | Returns | Notes |
|--------|---------|-------|
| `GetName()` | `str` | **[confirmed]** |
| `SetName(name)` | `bool` | **[confirmed present]** |
| `GetCurrentTimeline()` | Timeline | **[confirmed]** — `None` if none active |
| `GetTimelineCount()` | `int` | **[confirmed]** — 21 in test project |
| `GetTimelineByIndex(i)` | Timeline | **[confirmed]** — 1-based |
| `SetCurrentTimeline(tl)` | `bool` | **[confirmed present]** |
| `GetMediaPool()` | MediaPool | **[confirmed]** |
| `GetSetting(key)` | varies | **[confirmed]** — see table below |
| `SetSetting(key, val)` | `bool` | **[confirmed present]** |
| `GetRenderPresets()` | `dict` | **[confirmed]** — `{int: name}` e.g. `{1: 'H.264 Master', 2: 'HyperDeck', ...}` |
| `GetRenderPresetList()` | unknown | **[confirmed present, not called]** — may be same as above |
| `LoadRenderPreset(name)` | `bool` | **[from code]** — e.g. `"Audio Only"` |
| `SetRenderSettings(dict)` | `bool` | **[from code]** — see render settings below |
| `AddRenderJob()` | `str` | **[from code]** — returns job ID string |
| `GetRenderJobList()` | `list` | **[confirmed]** — `[]` when no jobs queued |
| `StartRendering(*job_ids)` | `bool` | **[from code]** |
| `StopRendering()` | — | **[confirmed present]** |
| `IsRenderingInProgress()` | `bool` | **[from code]** |
| `GetRenderJobStatus(job_id)` | `dict` | **[from code]** — keys: `JobStatus`, `Error`, `CompletionPercentage` |
| `DeleteRenderJob(job_id)` | `bool` | **[from code]** |
| `DeleteAllRenderJobs()` | `bool` | **[confirmed present]** |
| `GetCurrentRenderFormatAndCodec()` | `dict` | **[confirmed present, not called]** |
| `GetRenderFormats()` | `dict` | **[confirmed]** — `{'AVI': 'avi', 'BRAW': 'braw', ...}` |
| `GetRenderCodecs(format_key)` | `dict` | **[confirmed]** — codec name → codec key |
| `GetGallery()` | Gallery | **[confirmed present, not yet probed]** |
| `GetUniqueId()` | `str` | **[confirmed present]** |
| `AddColorGroup(name)` | ColorGroup | **[confirmed present]** |
| `DeleteColorGroup(cg)` | `bool` | **[confirmed present]** |
| `GetPresetList()` | unknown | **[confirmed present, not called]** |

**Absent in Resolve 20:** `GetRenderSettings`, `GetColorGroupList`

### GetSetting keys (Project level)

`timelineFrameRate` returns a **float**, all others return strings:

| Key | Example | Type |
|-----|---------|------|
| `"timelineFrameRate"` | `24.0` | **float** |
| `"timelineResolutionWidth"` | `'1920'` | str |
| `"timelineResolutionHeight"` | `'1080'` | str |
| `"colorScienceMode"` | `'davinciYRGB'` | str |
| `"videoMonitorFormat"` | `'HD 1080p 24'` | str |
| `"audioCaptureNumChannels"` | `'2'` | str |

### GetRenderPresets return shape

```python
project.GetRenderPresets()
# → {1: 'H.264 Master', 2: 'HyperDeck', 3: 'H.265 Master',
#    4: 'ProRes 422 HQ', 5: 'YouTube - 720p', 6: 'YouTube - 1080p', ...}
```

Dict of `int → str`, not a list. Pass the preset **name** string to `LoadRenderPreset`.

### Render pipeline (confirmed working)

```python
project.LoadRenderPreset("Audio Only")
project.SetRenderSettings({
    "SelectAllFrames": 1,
    "TargetDir": "/path/to/output",
    "CustomName": "stem_name",
    "AudioSampleRate": 48000,
    "AudioBitDepth": 16,
})
job_id = project.AddRenderJob()
project.StartRendering(job_id)
while project.IsRenderingInProgress():
    time.sleep(0.25)
status = project.GetRenderJobStatus(job_id)
project.DeleteRenderJob(job_id)
# status["JobStatus"] → "Complete" | "Failed" | "Cancelled"
```

`GetRenderSettings` is **absent** — you cannot read back the current render configuration.

---

## Timeline

### Methods

| Method | Returns | Notes |
|--------|---------|-------|
| `GetName()` | `str` | **[confirmed]** |
| `SetName(name)` | `bool` | **[confirmed present]** |
| `GetStartFrame()` | `int` | **[confirmed]** — absolute frame number (e.g. `86400` = 01:00:00:00 at 24fps) |
| `GetEndFrame()` | `int` | **[confirmed]** |
| `GetCurrentTimecode()` | `str` | **[confirmed]** — e.g. `'01:00:33:10'` |
| `SetCurrentTimecode(tc)` | `bool` | **[confirmed present]** |
| `GetTrackCount(type)` | `int` | **[confirmed]** — `"video"`, `"audio"`, `"subtitle"` |
| `GetItemListInTrack(type, idx)` | `list` | **[confirmed]** — 1-based; `[]` for empty tracks |
| `GetTrackName(type, idx)` | `str` | **[confirmed]** |
| `SetTrackName(type, idx, name)` | `bool` | **[confirmed present]** |
| `SetTrackEnable(type, idx, bool)` | `bool` | **[from code, works]** |
| `GetIsTrackEnabled(type, idx)` | `bool` | **[confirmed present, not called]** — note: `GetIsTrackEnabled` not `GetTrackEnabled` |
| `GetSetting(key)` | varies | **[confirmed]** |
| `SetSetting(key, val)` | `bool` | **[confirmed present]** |
| `GetCurrentVideoItem()` | TimelineItem | **[confirmed]** — returns current playhead item |
| `GetMarkers()` | `dict` | **[confirmed]** — `{}` if none; see marker shape below |
| `AddMarker(frame, color, name, note, duration, customData)` | `bool` | **[confirmed present]** |
| `DeleteMarkerAtFrame(frame)` | `bool` | **[confirmed present]** — note: not `DeleteMarker` |
| `DeleteMarkersByColor(color)` | `bool` | **[confirmed present]** |
| `GrabStill()` | GalleryStill | **[confirmed present]** |
| `GrabAllStills(source)` | `list` | **[confirmed present]** |
| `Export(path, type)` | `bool` | **[confirmed present, not called]** |
| `GetUniqueId()` | `str` | **[confirmed present]** |

**Absent in Resolve 20:** `DeleteMarker`, `ApplyGradeFromDRX`, `GetTrackEnabled`

### GetSetting keys (Timeline level)

`timelineFrameRate` returns a **float** at both Project and Timeline level:

| Key | Example for V9x16 timeline |
|-----|----------------------------|
| `"timelineFrameRate"` | `24.0` (float) |
| `"timelineResolutionWidth"` | `'1080'` (portrait!) |
| `"timelineResolutionHeight"` | `'1920'` (portrait!) |

Timeline `GetSetting` returns the **per-timeline** resolution, which differs from the
project default when the timeline has its own settings. Always query the timeline,
not the project, when you need the active timeline's dimensions.

### GetStartFrame coordinate system

The timeline's absolute frame origin is `GetStartFrame()`. For a 01:00:00:00 start
at 24fps: `1 * 3600 * 24 = 86400`. All `TimelineItem.GetStart()` / `GetEnd()` values
are in this same absolute frame space.

To get relative position from timeline start:
```python
relative_frame = item.GetStart() - timeline.GetStartFrame()
seconds = relative_frame / timeline.GetSetting("timelineFrameRate")
```

### Track names (example from test timeline)

```
audio 1: 'Main Audio'       — synced camera audio
audio 2: 'Voiceover (Post)' — recorded VO
audio 3: 'Music 1'          — background music
audio 4: 'Music 2'
audio 5: 'SFX'
video 1: 'Main Footage'
video 2: 'B-Roll'
video 3: 'Titles / Texts'
```

Use `GetTrackName` to identify tracks by role rather than hardcoding indices.

### Marker shape

```python
timeline.GetMarkers()
# → {frame: {"color": "Blue", "name": "...", "note": "...",
#             "duration": 1, "customData": ""}}
```

Frame key is the absolute timeline frame number.

---

## TimelineItem

### Available methods (identical across audio and video items)

```
GetName, GetStart, GetEnd, GetDuration,
GetSourceStartTime, GetSourceEndTime,
GetProperty, SetProperty,
GetMediaPoolItem, GetLinkedItems,
GetFlagList, AddFlag, ClearFlags,
GetClipColor, SetClipColor,
GetMarkers, AddMarker,
GetNodeGraph, GetFusionCompCount
```

`GetVolume` / `SetVolume` are absent. Volume goes through `GetProperty` / `SetProperty`.

### Timing

| Method | Returns | Notes |
|--------|---------|-------|
| `GetStart()` | `int` | Absolute timeline frame; same coordinate as `GetStartFrame()` |
| `GetEnd()` | `int` | Absolute timeline frame |
| `GetDuration()` | `int` | `GetEnd() - GetStart()` in frames |
| `GetSourceStartTime()` | `float` | **Source clip in-point in seconds** (not frames, not TC) |
| `GetSourceEndTime()` | `float` | **Source clip out-point in seconds** |

`GetSourceStartTime()` example: `20699.971` seconds ≈ 05:44:59 — matches source TC.
The unit is confirmed as seconds by checking: `end - start = 1.875 s = 45 frames / 24fps`.

### GetProperty — video items only

```python
video_item.GetProperty()
# → {'Pan': 0.0, 'Tilt': 0.0, 'ZoomX': 1.5, 'ZoomY': 1.5, 'ZoomGang': True,
#    'RotationAngle': 0.0, 'AnchorPointX': 0.0, 'AnchorPointY': 0.0,
#    'opacity': 100.0, ...}
```

Confirmed readable keys on video items:

| Key | Type | Notes |
|-----|------|-------|
| `'Pan'` | float | Horizontal position |
| `'Tilt'` | float | Vertical position |
| `'ZoomX'` | float | e.g. `1.5` = 150% |
| `'ZoomY'` | float | |
| `'ZoomGang'` | bool | Lock X/Y zoom together |
| `'RotationAngle'` | float | |
| `'AnchorPointX'` | float | |
| `'AnchorPointY'` | float | |
| `'opacity'` | float | 0–100 |
| `'CropLeft'` etc. | float | Crop edges |
| `'FlipX'`, `'FlipY'` | bool | |

These are the reframe properties — the full set will be in the probe output dict.

### GetProperty — audio items

`GetProperty()` returns `{}`. All keyed lookups return `None`. Audio clip state
cannot be read via `GetProperty`.

### SetProperty("volume", db) — confirmed broken readback

```python
audio_item.SetProperty("volume", 0.0)
audio_item.GetProperty("volume")  # → None (always)
```

The write does not raise an exception but the value cannot be read back.
**Verify audio volume changes visually in the Resolve UI** after running a pass.
The clip volume Inspector panel should reflect the change if `SetProperty` committed.

This is the blocking unknown for `passes.py` correctness. See open questions.

### GetLinkedItems()

Returns the timeline counterpart(s) for a linked clip:

```python
# On a Video+Audio track 1 item:
item.GetLinkedItems()  # → [<TimelineItem>]  ← the paired audio item

# On a standalone audio-only item (no video link):
item.GetLinkedItems()  # → []
```

Use this to find the audio clip linked to a video clip or vice versa, without
scanning all tracks.

### GetFlagList / AddFlag / ClearFlags

```python
item.GetFlagList()  # → []  (empty unless flags set)
item.AddFlag("Red")  # valid colors: same as SetClipColor list below
item.ClearFlags("Red")  # or "All"
```

### GetClipColor / SetClipColor

```python
item.GetClipColor()  # → ''  (empty string if unset)
item.SetClipColor("Orange")
```

Valid color names: `"Orange"`, `"Apricot"`, `"Yellow"`, `"Lime"`, `"Olive"`,
`"Green"`, `"Teal"`, `"Navy"`, `"Blue"`, `"Purple"`, `"Violet"`, `"Pink"`,
`"Tan"`, `"Beige"`, `"Brown"`, `"Chocolate"`.

### GetMarkers / AddMarker (on clip)

```python
item.GetMarkers()  # → {}  if none
# Key is frame offset from clip start (not absolute timeline frame)
item.AddMarker(frame_offset, "Blue", "name", "note", 1, "")
```

### GetNodeGraph / GetFusionCompCount

```python
item.GetFusionCompCount()  # → 0  if no Fusion compositions on clip
item.GetNodeGraph()  # → node graph object (not yet probed)
```

---

## MediaPoolItem

### Available methods (Resolve 20)

```
GetName, GetClipProperty, SetClipProperty,
GetMediaId, GetUniqueId,
GetFlags, ClearFlags,
GetClipColor, SetClipColor,
GetMarkers, AddMarker,
GetMetadata, SetMetadata,
GetThirdPartyMetadata, SetThirdPartyMetadata,
TranscribeAudio, ClearTranscription
```

**Absent:** `GetProperty`, `SetProperty`, `SetFlags`, `GetLinkedItems`, `GetTranscript`

Note: `TranscribeAudio` and `ClearTranscription` exist but `GetTranscript` does not.
Transcription text may be read via `GetMetadata` or a different key — untested.

### GetMediaId vs GetUniqueId

Both present, both return UUID strings, they are **different values**:

```python
mpi.GetMediaId()   # → 'f008661a-d2b6-42e2-900e-fb282f739005'
mpi.GetUniqueId()  # → 'bfcfbff3-9674-45de-9f06-ad223bb096f4'
```

`GetMediaId` appears to be the media pool item's database ID.
`GetUniqueId` is likely a persistent content hash or clip GUID. Use `GetUniqueId`
for stable cross-session identification.

### GetClipProperty() — full metadata dict

All values are strings **except FPS which is a float**:

| Key | Video+Audio | Audio-only |
|-----|-------------|------------|
| `'Clip Name'` | `'20250417_S74_0345.MP4'` | `'Voiceover (Post)_028'` |
| `'File Name'` | same as Clip Name | `'Voiceover (Post)_028_28JH2Y.wav'` |
| `'File Path'` | absolute path | absolute path |
| `'Type'` | `'Video + Audio'` | `'Audio'` |
| `'Format'` | `'QuickTime'` | `'Wave'` |
| `'Duration'` | `'00:01:26:12'` | `'00:00:26:22'` |
| `'FPS'` | `23.976` **(float!)** | `24.0` **(float!)** |
| `'Resolution'` | `'3840x2160'` | `''` |
| `'Video Codec'` | `'H.265 Main 10 L5.0'` | `''` |
| `'Audio Codec'` | `'Linear PCM'` | `'Linear PCM'` |
| `'Audio Ch'` | `'2'` | `'1'` |
| `'Audio Bit Depth'` | `'16'` | `'24'` |
| `'Sample Rate'` | `'48000'` | `'48000'` |
| `'Start TC'` | `'05:44:38:16'` | `'01:00:00:21'` |
| `'End TC'` | `'05:46:05:04'` | `'01:00:27:19'` |
| `'Start'` | `'0'` (frame int as str) | `''` |
| `'End'` | `'2075'` | `''` |
| `'Frames'` | `'2076'` | `''` |
| `'In'` | `'05:45:55:20'` (in-point TC) | `''` |
| `'Out'` | `'05:46:01:20'` | `''` |
| `'Bit Depth'` | `'10'` | `''` |
| `'Online Status'` | `'Online'` | `'Online'` |
| `'Usage'` | `'12'` | `'1'` |
| `'Date Added'` | `'Sat Feb 21 2026 16:51:31'` | `'Wed Apr 15 2026 18:11:48'` |

**FPS is a float, not a string** — guard with `float(mpi.GetClipProperty("FPS"))`.

### GetMetadata()

Returns embedded file metadata (e.g. BWF metadata for .wav files):

```python
# For Voiceover (Post) WAV:
mpi.GetMetadata()
# → {'Camera #': 'BlackmagicDesign', 'Date Recorded': '2026-04-15',
#    'Description': 'Bwf', 'Sound Roll': ...}
```

Returns `{}` for files without embedded metadata (MP4, MP3).
`GetThirdPartyMetadata()` returns `{}` for all tested clips.

---

## MediaPool

### Methods

| Method | Returns | Notes |
|--------|---------|-------|
| `GetRootFolder()` | Folder | **[confirmed]** — root is named `'Master'` |
| `GetCurrentFolder()` | Folder | **[confirmed present]** |
| `SetCurrentFolder(folder)` | `bool` | **[confirmed present]** |
| `AddSubFolder(folder, name)` | Folder | **[confirmed present]** |
| `CreateEmptyTimeline(name)` | Timeline | **[confirmed present]** |
| `ImportMedia(paths)` | `list` | **[confirmed present]** |
| `AppendToTimeline(clips)` | `list` | **[confirmed present]** |
| `DeleteClips(clips)` | `bool` | **[confirmed present]** |
| `MoveClips(clips, folder)` | `bool` | **[confirmed present]** |
| `GetUniqueId()` | `str` | **[confirmed present]** |

**Absent:** `GetFolderList`, `GetClipList` (these are on Folder objects, not on MediaPool)

### Folder traversal

```python
mp = project.GetMediaPool()
root = mp.GetRootFolder()        # → Folder named 'Master'
root.GetName()                   # → 'Master'
root.GetClipList()               # → [] (clips are in sub-folders, not root)
root.GetSubFolderList()          # → list of Folder objects (6 in test project)

for folder in root.GetSubFolderList():
    print(folder.GetName())
    for clip in folder.GetClipList():
        print("  ", clip.GetClipProperty("Clip Name"))
```

---

## Known Limitations

### 1. Audio TimelineItem properties are write-only (at best)

`GetProperty` returns nothing for audio clips. `SetProperty("volume", db)` writes
silently — no confirmation. Must verify visually in Resolve UI.

### 2. No Fairlight automation keyframe access

The API has no path to Fairlight automation curves. Volume is a single per-clip
scalar, not a keyframed envelope. Duck pass produces step-function volume changes,
not smooth fades.

### 3. GetRenderSettings is absent

Cannot read back the current render configuration after setting it. If `LoadRenderPreset`
and `SetRenderSettings` are called in sequence, the last `SetRenderSettings` call
wins — but there's no way to confirm what Resolve will render.

### 4. Page state matters

`GetCurrentTimecode()` and video item positioning may only be accurate on the Edit page.
After `StartRendering`, Resolve is left on the Deliver page. Always call
`resolve.OpenPage("edit")` before reading timeline state post-render.

### 5. Frame coordinate system

All timeline positions (`GetStart`, `GetEnd`, `GetStartFrame`) use the **absolute**
frame number. A timeline starting at 01:00:00:00 at 24fps starts at frame 86400.
`GetSourceStartTime/EndTime` use **seconds** — a completely different unit.
Never mix them.

### 6. Render output filename

Resolve may append a suffix to `CustomName` if a file already exists.
Always glob `f"{stem}*.wav"` rather than assuming an exact filename.

### 7. GetCurrentFolder returns empty string at root

`pm.GetCurrentFolder()` → `''` when at the database root. Not `None`.

---

## Open Questions

| # | Question | Status |
|---|----------|--------|
| 1 | Does `SetProperty("volume", db)` actually change clip volume in Resolve UI? | **Unverified** — probe shows read fails; needs manual UI check after pass |
| 2 | What is the full dict returned by `video_item.GetProperty()`? | Partially seen — ZoomX/Y, Pan, Tilt, opacity confirmed; full key list needed |
| 3 | Does `GetIsTrackEnabled(type, idx)` work? What does it return? | Confirmed present, not yet called |
| 4 | What does `GetNodeGraph()` return? How to access Fusion comps? | Not yet probed |
| 5 | What are the 6 sub-folders in the MediaPool root? | Folder.GetName() calls pending |
| 6 | Does `TranscribeAudio` on MediaPoolItem trigger Resolve's AI transcription? What args? | Not probed |
| 7 | What does `GetVersion()` return vs `GetVersionString()`? | Not called |
| 8 | `GetRenderJobStatus` — is the done value `"Complete"` or `"Completed"`? | Code uses `"Complete"` — verify against a real render |
| 9 | Can `SetProperty` on video items round-trip? (Set ZoomX, read it back?) | Not yet tested |
| 10 | What are the valid `SetRenderSettings` keys beyond the 5 confirmed ones? | Full key list from Resolve docs or trial |

---

## Running the Probe

```bash
cd /Users/samir/Documents/projects/media_os/splice
uv run python scripts/probe_resolve.py 2>&1 | tee docs/probe_output_$(date +%Y%m%d).txt
```

Pipe to a dated file so each run is preserved for comparison across Resolve versions.
