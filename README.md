# splice

A DaVinci Resolve editing assistant that automates the mechanical parts of a post-production session: audio normalization and ducking, color passes, reframing, titles, and teleprompter display.

splice connects to a **running Resolve instance** via its Python scripting API and operates on whatever project is open. It has no dependency on `content_os` at runtime — content_os bootstraps the Resolve project; splice works on the result.

---

## Prerequisites

| Requirement | Notes |
|---|---|
| DaVinci Resolve 18+ | Must be **installed and running** before any splice command |
| Python 3.11+ | Required by splice itself |
| uv | Package/tool manager — [install](https://docs.astral.sh/uv/getting-started/installation/) |

splice does **not** use ffmpeg, MediaPipe, or any dependency that requires a separate installer. All CV work goes through OpenCV (ships as a wheel). All audio measurement goes through pyloudnorm (pure Python). All actual edits go through Resolve's scripting API.

---

## Installation

**As a global tool** (recommended — available from any directory without activating a venv):

```bash
cd media_os/splice
uv tool install .
splice --help
```

**Dev mode** (edits to source take effect immediately):

```bash
cd media_os/splice
uv venv
uv pip install -e .
.venv/bin/splice --help
```

---

## Resolve API setup

Resolve's Python API is not a pip package. It is importable only when Resolve has added its scripting directories to your environment. Resolve sets these automatically on install on most systems, but if `splice check` reports "API not found", add these to your shell profile manually:

**macOS (`~/.zshrc` or `~/.zshenv`)**

```bash
export RESOLVE_SCRIPT_API="/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting"
export RESOLVE_SCRIPT_LIB="/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so"
export PYTHONPATH="$PYTHONPATH:$RESOLVE_SCRIPT_API/Modules/"
```

**Windows (System Environment Variables)**

```
RESOLVE_SCRIPT_API = C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting
RESOLVE_SCRIPT_LIB = C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll
PYTHONPATH         = %PYTHONPATH%;%RESOLVE_SCRIPT_API%\Modules\
```

After setting these, restart your terminal. Run `splice check` to confirm.

---

## Verifying the setup

```
splice check
```

Expected output when everything is working:

```
[OK] Resolve is running. Current project: My Video Title
```

Possible failure modes:

| Output | Cause | Fix |
|---|---|---|
| `Resolve scripting API not found` | env vars not set or Resolve not installed | See Resolve API setup above |
| `Resolve API returned None` | Resolve is not running | Open DaVinci Resolve, then retry |
| `No project is open` | Resolve running but no project loaded | Open a project in Resolve |

---

## CLI reference

```
splice check                          Verify Resolve bridge
splice script SCRIPT_FILE             Teleprompter overlay
splice audio normalize TRACK          Normalize one track to a LUFS target
splice audio duck                     Automate music volume relative to voice
splice audio flags                    Scan for clipping and silence anomalies
splice color lut LUT_FILE             Apply a .cube LUT to all clips
splice color awb                      Auto white balance all clips
splice color grade PRESET             Apply a gallery grade preset
splice finish intro CLIP              Prepend intro clip
splice finish outro CLIP              Append outro clip
splice finish lower-thirds CUES.json  Overlay lower thirds from a JSON cue file
splice reframe track VIDEO            Track subject with OpenCV CSRT
splice reframe layout PRESET          Apply a Fusion layout preset
```

### Audio examples

Normalize voice and music tracks to different levels, then duck the music bed:

```bash
splice audio normalize 1 --lufs -10    # voice (track 1)
splice audio normalize 2 --lufs -10    # second presenter (track 2)
splice audio normalize 3 --lufs -30    # music bed (track 3) — quiet under voice
splice audio duck --voice 1 --voice 2 --music 3
```

`duck` detects silence on the voice tracks. While voice is active, music stays at `--present-lufs` (default -30). When silence persists longer than `--idle-sec` (default 1.0 s), music rises to `--absent-lufs` (default -18). Transitions are smoothed with configurable attack/release envelopes.

```bash
# tighter ducking, slower release
splice audio duck --voice 1 --music 3 --idle-sec 0.5 --release-ms 800
```

### Reframe examples

```bash
# auto-detect and track the largest person in the frame
splice reframe track /path/to/clip.mp4

# track a specific range
splice reframe track /path/to/clip.mp4 --start 120 --end 600

# apply a layout preset to the current timeline
splice reframe layout code-me      # code feed left, face cam right
splice reframe layout pip-corner   # face cam as small PiP
```

Layout presets: `split-v`, `split-h`, `pip-corner`, `code-me`

### Teleprompter

Opens a floating, always-on-top Tkinter window. No timeline changes — display only.

```bash
splice script episode_42_script.txt
```

Controls: `Space` start/stop scroll · `↑↓` adjust speed · `Esc` quit

---

## Architecture

### Pass protocol and Pipeline

Every editing operation is a `Pass` — a class with a `run(self, timeline)` method and its configuration stored as constructor arguments. Passes compose into a `Pipeline`.

```
core.py
  Pass       (Protocol)   — the interface every pass satisfies
  Pipeline                — runs an ordered list of passes against a timeline
```

This means you can build a pipeline in Python code and run it as a single unit:

```python
from splice.core import Pipeline
from splice.audio.passes import NormalizePass, DuckPass

Pipeline([
    NormalizePass(track_index=1, target_lufs=-10.0),
    NormalizePass(track_index=3, target_lufs=-30.0),
    DuckPass(voice_tracks=[1], music_track=3),
]).run(timeline)
```

The CLI is a factory that constructs pass instances from command-line arguments and calls `run()`. Adding a new pass means adding a class and one CLI command — the core never changes.

### Module layout

```
src/splice/
├── core.py               Pass protocol, Pipeline
├── cli.py                Typer root — all subcommands
├── resolve/
│   └── client.py         Resolve API bridge (get_resolve, get_current_timeline, etc.)
├── audio/
│   └── passes.py         NormalizePass, DuckPass, AnomalyPass
├── color/
│   └── passes.py         LUTPass, AWBPass, GradePass
├── finish/
│   └── passes.py         IntroPass, OutroPass, LowerThirdsPass
├── reframe/
│   ├── tracker.py        CSRTTracker (OpenCV CSRT, BoundingBox, Keyframe)
│   └── layouts.py        LayoutApplier, Layout enum
├── pacing/
│   └── hints.py          SilenceDetector, CutAdvisor, CutHint
└── teleprompter/
    └── overlay.py        TeleprompterWindow (Tkinter)
```

### Resolve API bridge

`resolve/client.py` provides four helpers:

```python
get_resolve()            → dvr.scriptapp("Resolve")
get_project_manager()   → resolve.GetProjectManager()
get_current_project()   → project manager's current project
get_current_timeline()  → current project's active timeline (raises SystemExit if none)
```

All pass `run()` methods receive a `timeline` object from `get_current_timeline()`. The Resolve API is then used directly on that object inside each pass.

---

## Implementation status

| Feature | Status | Notes |
|---|---|---|
| `splice check` | **Working** | Full Resolve bridge |
| `splice script` (teleprompter) | **Working** | Tkinter overlay, scroll controls |
| `splice reframe track` | **Broken** | CSRT tracker runs and generates keyframe data, but all keyframe write methods (`AddKeyframe`, `SetPropertyKeyframe`, etc.) are absent in Resolve 20. Tracking output has no write path. |
| Pass protocol + Pipeline | **Working** | `core.py` |
| CLI shape (all commands) | **Working** | All commands registered, help text correct |
| `NormalizePass` | **Broken** | `SetProperty("volume")` does not commit on audio items in Resolve 20 — visually verified. Pass runs without error but clips are unchanged. |
| `DuckPass` | **Broken** | Same root cause as NormalizePass — audio volume writes are silently discarded. |
| `AnomalyPass` | **Working** | Vectorised peak scan for clipping + RMS-frame silence gap detection, all tracks |
| `LUTPass` | **Working** | Copies LUT to Resolve's LUT directory, calls `RefreshLUTList()`, then `NodeGraph.SetLUT(1, path)` per clip. See `docs/resolve_api.md` for constraints. |
| `AWBPass` | **Not possible** | Auto white balance has no Python API surface in Resolve 20. |
| `GradePass` | Stub | Needs: Resolve gallery still API |
| `IntroPass` / `OutroPass` | Stub | Needs: Resolve media pool insert API |
| `LowerThirdsPass` | Stub | Needs: Fusion title comp or Power Bin item API |
| `LayoutApplier` | Stub | Needs: Fusion comp node construction per layout |
| `SilenceDetector` | **Working** | 50ms RMS frames via numpy + standard `wave` module; no soundfile dependency |
| `CutAdvisor` | Stub | Needs: SilenceDetector + OpenCV frame-diff |

"Stub" means the CLI command is reachable and the pass object is constructable, but calling `.run()` raises `NotImplementedError`. The scaffolding and configuration contract is in place — implementation fills in the `run()` body.

---

## What to implement next

The highest-value, lowest-complexity path:

1. **`IntroPass` / `OutroPass`** — `MediaPool.AppendToTimeline()` is confirmed present. The main design decision is how to look up the source clip (by name, by path, or by UUID).

2. **`LayoutApplier`** — `TimelineItem.ImportFusionComp(path)` is confirmed. Build layout presets as `.comp` files in Resolve's Fusion page, export once, apply via the API with no keyframe writes required.

3. **`LayoutApplier`** — build one Fusion comp per preset in Resolve, export as `.setting` files, inject via the scripting API. Manual setup once; automated from there.

4. **`CutAdvisor`** — `SilenceDetector` is now implemented; add the OpenCV frame-diff scene change pass and merge with silence windows to produce ranked cut hints.

5. **Smooth ducking** — `DuckPass` applies per-clip volumes rather than smooth automation curves because the Resolve Python scripting API does not expose Fairlight automation keyframes. True attack/release ducking would require driving Resolve's Fairlight API or a third-party DAW automation format.

---

## Relationship to other tools in media_os

| Tool | Relationship |
|---|---|
| `content_os` | Sets up the Resolve project (footage import, timeline creation, stream markers). splice assumes this is already done. |
| `helm` | Stream deck integration. Helm buttons can call splice CLI commands directly: `splice audio normalize 1`, `splice reframe track`, etc. |
| `boneless_couch` | Provides stream markers that content_os imports into the timeline. Relevant for pacing hints (cut points often align with markers). |
