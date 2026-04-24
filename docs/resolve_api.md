---
tags: [davinci-resolve, api, reference]
type: reference
created: 2026-04-24
updated: 2026-04-24
resolve_version: 20.3.2.9
gist_reference: https://gist.github.com/mhadifilms/2b84d469135315793220dbf2226cbe63
---

# DaVinci Resolve Python Scripting API — Field Guide

> Living reference backed by `scripts/probe` runs.
> Every claim is tagged: **[confirmed]** = seen in probe output, **[from code]** = used in passes.py and working in practice, **[untested]** = not yet probed.
> Re-run probe after Resolve updates and reconcile.

**Resolve version probed: 20.3.2.9**
`GetVersion()` → `[20, 3, 2, 9, '']`

---

## Requirements & Platform Setup

### Studio requirement

**DaVinci Resolve Studio (paid) is required.** The free version does not expose the
scripting API. The app must be running with a project open before any script can connect.
Headless mode is also supported: launch Resolve with `-nogui` for server/CI use.

### Platform paths

The `DaVinciResolveScript` module and its native library live at platform-specific locations
that must be on `PYTHONPATH` and the dynamic library search path.

**macOS:**
```
API module:  /Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules/
Library:     /Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so
```

Set in shell or `.env`:
```bash
export PYTHONPATH="/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules:$PYTHONPATH"
export DYLD_LIBRARY_PATH="/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion:$DYLD_LIBRARY_PATH"
```

**Windows:**
```
API module:  %PROGRAMDATA%\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules\
Library:     C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll
```

Set in PowerShell or System Environment Variables:
```powershell
$env:PYTHONPATH = "$env:PROGRAMDATA\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules;$env:PYTHONPATH"
```
The DLL directory is typically already on `PATH` after Resolve installs.

### Connection

```python
import DaVinciResolveScript as dvr
resolve = dvr.scriptapp("Resolve")
# resolve is None if Resolve is not running or no Studio license
```

The `probe/__main__.py` raises `SystemExit` with a diagnostic if `import DaVinciResolveScript` fails —
check `PYTHONPATH` first.

### macOS LAN-binding issue

On some macOS configurations the Resolve IPC socket binds to a LAN IP rather than
`127.0.0.1`, causing `scriptapp("Resolve")` to hang. If the connection stalls:
- Run `ifconfig | grep "inet "` to find the active LAN IP
- Or use `pinghosts('')` (Fusion scripting helper) to locate the bound address

Implement a threaded timeout wrapper around `scriptapp()` to avoid indefinite hangs:
```python
import concurrent.futures
def connect(timeout=5.0):
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        fut = ex.submit(dvr.scriptapp, "Resolve")
        return fut.result(timeout=timeout)
```

### Version delta: 20.0.x → 20.3.2

Probed on **20.3.2.9**. `GetTimelineByName()` was mentioned in the gist as new in 20.3
but was not in the probed candidates list — add it to a future probe run to confirm.

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

## Color API

### TimelineItem — color methods

| Method | Returns | Notes |
|--------|---------|-------|
| `GetNodeGraph()` | NodeGraph | **[confirmed]** — present on both video and audio items |
| `GetLUT()` | unknown | **[confirmed present, not called]** |
| `SetLUT()` | unknown | **[confirmed present, not called]** — args unknown |
| `CopyGrades()` | unknown | **[confirmed present, not called]** — args unknown |

**All absent on TimelineItem:** `AutoBalance`, `AutoColor`, `ColorBalance`, `ResetGrade`,
`GetCurrentColorVersion`, `GetColorVersionList`, `AddColorVersion`, `LoadColorVersion`,
`GrabStill`, `GrabAllStills`, `ApplyGradeFromDRX`.

Auto white balance has **no API surface** — the Color page auto-balance button is not
scriptable. `AWBPass` cannot be implemented via the Python API.

### NodeGraph object

Returned by `TimelineItem.GetNodeGraph()`.

| Method | Notes |
|--------|-------|
| `SetLUT(?)` | **[confirmed present]** — signature unknown; likely `SetLUT(path)` or `SetLUT(node_index, path)` |
| `GetLUT(?)` | **[confirmed present]** — signature unknown |
| `ApplyGradeFromDRX(?)` | **[confirmed present]** — signature unknown; this is how grade presets apply |
| `GetNodeLabel()` | **[confirmed present]** — returns label of… unclear which node |
| `SetNodeEnabled()` | **[confirmed present]** |

**All absent on NodeGraph:** `GetNodeCount`, `GetNode`, `GetNodeByIndex`, `AddNode`,
`DeleteNode`, `ExportLUT`, `Reset`, `SetNodeLabel`, `GetNodeEnabled`.

**Critical limitation:** There is no `GetNodeCount` or `GetNode(index)`. You cannot
iterate or address individual nodes in the graph. `SetLUT` and `GetLUT` operate at
the graph level — it is unclear whether they target node 1 or the whole pipeline.
This limits fine-grained per-node control (e.g. setting a LUT on a specific corrector
node vs. the input node).

### LUTPass implementation path

```python
ng = video_item.GetNodeGraph()
ng.SetLUT(lut_path)     # confirmed callable — args and behavior need verification
```

`SetLUT` and `GetLUT` on `TimelineItem` also exist (separate from the node graph call).
The relationship between these two is unconfirmed — probe with a known LUT path to see
which actually applies it and where it shows in the Resolve UI.

### Gallery

```python
gallery = project.GetGallery()           # confirmed
albums = gallery.GetGalleryStillAlbums() # confirmed — returns list of album objects
album = albums[0]
stills = album.GetStills()              # confirmed — returns list of still objects
```

Gallery methods present: `GetCurrentStillAlbum`, `SetCurrentStillAlbum`,
`GetGalleryStillAlbums`. Album methods: `GetStills`, `GetLabel`, `SetLabel`,
`ImportStills`, `ExportStills`, `DeleteStills`.

**Still objects have no methods** — `GetLabel` and `SetLabel` are absent on the still
object itself. There is no API to read a still's name or match it to a named preset.
Grade presets saved in the gallery cannot be identified by name through the API.

`ApplyGradeFromDRX` is on the **NodeGraph** object, not on Gallery stills. To apply
a grade you need a `.drx` file path, not a gallery still reference.

---

## Keyframe API

### Per-frame transform writes — confirmed not available

All keyframe write methods are **absent** on `TimelineItem` in 20.3.2:

```
AddKeyframe, DeleteKeyframeAtFrame, SetPropertyKeyframe,
SetPropertyKeyframeValue, SetPropertyKeyframes, SetKeyframeEnabled,
SetPropertyAnimated, GetDynamicZoomEase, SetDynamicZoomEase
```

Attempts to write per-frame values via `SetProperty` also fail:

```python
item.SetProperty("Pan", {frame: 0.1})       # → False (no effect)
item.SetProperty("Pan", {str(frame): 0.1})  # → False
item.SetProperty("Pan", (frame, 0.1))       # → False
```

**Conclusion: animated per-frame keyframes for inspector transforms cannot be written
through the Python API.** Subject tracking (CSRTTracker generates keyframe data) has
no confirmed write path to Resolve.

### GetProperty does accept a frame argument

```python
item.GetProperty("Pan", frame)   # → False when no animation is set on the property
```

`False` (not `None`) means the frame argument is accepted — the API recognises it but
returns `False` because no keyframe animation exists on the property. When animation
IS set (e.g. manually in the Inspector), this may return the per-frame value. **Not
yet tested with an animated clip.**

### Static transform read/write — confirmed working

All inspector transform properties round-trip correctly (set → read back = same value):

| Key | Confirmed |
|-----|-----------|
| `Pan` | read/write ✓ |
| `Tilt` | read/write ✓ |
| `ZoomX` | read/write ✓ |
| `ZoomY` | read/write ✓ |
| `RotationAngle` | read/write ✓ |

Static reframe (one fixed crop/zoom for the whole clip) is fully supported.
Smooth animated tracking is not.

---

## Known Limitations

### 1. Audio volume is write-only — confirmed broken in 20.3.2

`GetProperty` returns `{}` for audio clips; all keyed lookups return `None`.
This is unchanged from 20.0.0.49. `GetVolume`/`SetVolume` do not exist.
`SetProperty("volume", db)` does not raise, but the value cannot be read back.

**Design implication for NormalizePass:** always measure via rendered WAV,
treat the existing clip volume as unknown, and reset all clips to 0 dB before
measuring so each run is idempotent. Do NOT add a delta to the unreadable current value.

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
| 1 | Does `SetProperty("volume", db)` actually commit the value in the Resolve UI? | **Unverified visually** — readback confirmed broken; needs manual UI check after a pass run |
| 2 | What is the full dict returned by `video_item.GetProperty()`? | Pan, Tilt, ZoomX/Y, ZoomGang, RotationAngle, AnchorPointX/Y, opacity confirmed — full list needs a clip with all properties set |
| 3 | `GetIsTrackEnabled` | **[confirmed]** → `True` / `False` |
| 4 | `GetNodeGraph()` | **[confirmed]** — see Color API section |
| 5 | MediaPool folder structure | **[confirmed]** — 00_Timelines / 01_Footage / 02_Audio / 03_Graphics / 04_Project_Files / 05_Exports |
| 6 | `TranscribeAudio` args and behavior | Not probed |
| 7 | `GetVersion()` vs `GetVersionString()` | **[confirmed]** — `GetVersion()` → `[20, 3, 2, 9, '']`; `GetVersionString()` → `'20.3.2.9'` |
| 8 | `GetRenderJobStatus` — done value `"Complete"` or `"Completed"`? | Code uses `"Complete"` — verify against a real render |
| 9 | `SetProperty` round-trip on video items | **[confirmed]** — Pan, Tilt, ZoomX, ZoomY, RotationAngle all round-trip correctly |
| 10 | Valid `SetRenderSettings` keys beyond the 5 confirmed | Full key list from Resolve docs or trial |
| 11 | `NodeGraph.SetLUT(?)` — exact signature and which node it targets | Not yet called with args |
| 12 | `NodeGraph.ApplyGradeFromDRX(?)` — signature, and what does it accept (path? still object?) | Not yet called |
| 13 | `GetProperty(key, frame)` — does it return a value (not `False`) when animation IS set? | Tested only on un-animated clips; `False` = no keyframe at that frame |
| 14 | Does `GetProperty(key)` return a `{frame: value}` dict when animation is set on the property? | Would unlock read-back of existing keyframe data |
| 15 | `TimelineItem.SetLUT()` vs `NodeGraph.SetLUT()` — are these the same operation? | Both confirmed present but not yet called |
| 16 | `CopyGrades()` on TimelineItem — what does it accept? Can it copy from a still? | Not probed |

---

## Running the Probe

```bash
cd /Users/samir/Documents/projects/media_os/splice
uv run python -m scripts.probe 2>&1 | tee docs/probe_output_$(date +%Y%m%d).txt
```

Pipe to a dated file so each run is preserved for comparison across Resolve versions.
