---
tags: [content, davinci-resolve, python, video-editing]
type: project
area: build
status: idea
created: 2026-04-19
---

# splice

> A DaVinci Resolve editing assistant that automates the mechanical parts of the editing session — reframing, audio leveling, color, titles, and script display — so the editing session is focused on creative decisions only.

---

## Purpose

`splice` is a standalone editing assistant. It connects to a running DaVinci Resolve instance and operates on whatever project is open. No dependency on `content_os` at runtime — the Resolve project already exists with footage imported and timeline markers in place before splice is involved.

---

## Workflow (End to End)

```
content_os bootstraps Resolve project
    — footage imported, timeline created, stream markers imported
    ↓
You edit: rough cut, pacing, creative decisions
    ↓
splice: Reframe Pass
    — subject tracking with keyframes (climbing)
    — split/PiP layout templates applied (programming)
    ↓
splice: Audio Pass
    — normalize voice track to target LUFS
    — duck background music under voice
    — flag clips with clipping or silence anomalies
    ↓
splice: Color Pass
    — apply base LUT to all clips from a source
    — auto white balance on flagged clips
    — apply saved grade presets per camera/content type
    ↓
splice: Finishing Pass
    — inject intro/title from template
    — inject outro from template
    — render lower thirds / title cards from config
    — display script overlay (teleprompter mode, if script exists)
    ↓
You approve and hit render
```

---

## Core Features

### Reframe Pass

#### Subject Tracking

Generates keyframes to keep a subject in frame across a clip. Default behavior uses a heuristic (largest detected person in frame). Override by drawing a bounding box in a small preview UI splice shows for that clip.

- Heuristic mode: no input required, runs automatically
- Manual mode: splice shows a single-frame preview; you draw a bounding box; tracking runs from that anchor
- Outputs keyframes written back to the Resolve timeline via the scripting API
- Primary use case: climbing footage where the subject moves across the frame

#### Layout Templates

Applies a named Fusion composition template that splits the frame into multiple panes. Instantiated on a clip or clip range — no manual Fusion setup per clip.

Named presets:

| Preset        | Layout                                      |
| ------------- | ------------------------------------------- |
| `split-v`     | Vertical split, two equal panes             |
| `split-h`     | Horizontal split, two equal panes           |
| `pip-corner`  | Primary full frame + small PiP in corner    |
| `code-me`     | Code feed left, face cam right (16:9 split) |

Primary use case: programming content with a face cam + screen capture.

### Audio Normalization

- Target: `-14 LUFS` (YouTube standard) or configurable
- Voice track: normalize loudness, gentle dynamic range compression
- Background music: auto-duck when voice is active (detect voice via RMS threshold)
- Flag clips with clipping or silence anomalies for manual review

### ML Audio (upgrades to normalization pass)

- Voice activity detection via `silero-vad` or `webrtcvad` — more accurate than RMS for music ducking
- Speaker separation to isolate voice from background before normalization
- Loudness anomaly detection to flag takes with clipping or mic issues automatically

### Color Tools

- LUT library: per-camera, per-location presets
- One-command "apply grade to all clips of this type"
- Auto-correct obvious white balance issues (not creative grading — just cleanup)
- Export/import Resolve color presets as named profiles

### Creating LUTs

- Export a manually dialed grade from Resolve as a `.cube` file
- Script-generate technical LUTs (e.g. log-to-rec709) using the `colour-science` Python library
- Build a "house LUT" by sampling input/output color pairs from a reference grade and interpolating a 3D cube

### Pacing Hints

- Silence/gap detection to flag dead air between cuts
- RMS energy drops to suggest natural cut points
- Clip duration outlier flagging (shots that run long relative to your average)

### Title & Branding Templates

- Intro sequence: title card with consistent font/color/animation, configurable duration
- Outro: subscribe card, end screen layout
- Lower thirds: name/topic bars rendered from a text config file
- All templates stored as Resolve Fusion compositions or Power Bin items
- Injected directly into the timeline — no manual placement per project

### Teleprompter / Script Display

- If a `.txt` or `.md` script exists for the project, display it as a floating overlay on the Resolve UI
- Scroll control via keyboard shortcut or `helm` button
- Does not touch the timeline — purely a reference display

---

## Architecture

DaVinci Resolve exposes a Python scripting API (`DaVinciResolveScript`). `splice` is a Python process that connects to the running Resolve instance via this API.

```
splice (Python)
    ↕ DaVinciResolveScript (local IPC)
DaVinci Resolve (running on Editing PC)
```

For subject tracking, splice uses an external CV library (MediaPipe or OpenCV) to compute the tracking path from the source clip file, then writes the resulting keyframes back to Resolve via the scripting API. The small bounding box preview UI (for manual mode) is a lightweight Tkinter window or floating browser window — it only appears when the user invokes manual tracking on a clip.

A lightweight CLI + optional small web UI for triggering passes. `helm` can call the CLI commands via shell or HTTP.

### CLI Shape

```
splice audio                    — run audio normalization pass
splice color [preset]           — apply color pass
splice finish                   — inject intro/outro/titles
splice reframe track [range]    — subject tracking with keyframe generation
splice reframe layout [preset]  — apply split/PiP layout template to clip(s)
splice script                   — launch teleprompter overlay
splice check                    — report issues (clipping, silence, missing assets)
```

---

## Tech Stack

| Layer               | Choice                                              |
| ------------------- | --------------------------------------------------- |
| Resolve integration | DaVinci Resolve Python API (`DaVinciResolveScript`) |
| Subject tracking    | MediaPipe or OpenCV (external CV, writes keyframes back to Resolve) |
| Audio analysis      | `pyloudnorm`, `librosa`, or FFmpeg loudnorm filter  |
| Bounding box UI     | Tkinter or floating browser window                  |
| Script overlay UI   | Tkinter or a floating browser window (simple)       |
| Config              | TOML                                                |
| CLI                 | `click` or `typer`                                  |

---

## Relationship to Other Projects

| Project          | Relationship                                                              |
| ---------------- | ------------------------------------------------------------------------- |
| `helm`           | Deck buttons trigger passes (audio, color, reframe, etc.) while editing   |
| `boneless_couch` | Stream markers are already imported into the timeline before splice runs  |

---

## Scope

- Works on the open Resolve project — no dependency on `content_os` at runtime
- Does not do project creation, footage import, or clip organization — that is `content_os`'s job
- Reframing automates keyframe generation and layout templates; it does not do narrative editing
- Does not do creative editing (pacing, b-roll selection, narrative) — that stays manual
- Does not replace a colorist for high-quality work — this is consistency/cleanup automation
- Audio ducking defaults to amplitude-based (RMS); ML VAD is an upgrade path

---

## Next

- [ ] Confirm DaVinci Resolve Python API version compatibility (Mac)
- [ ] Prototype: connect to running Resolve instance, read open timeline
- [ ] Test audio normalization pipeline with pyloudnorm
- [ ] Prototype: MediaPipe person detection on a sample clip, write keyframes via Resolve API
- [ ] Design title/branding template system in Resolve Power Bin
- [ ] Design Fusion composition presets for layout templates (split-v, split-h, pip-corner, code-me)
- [ ] Stub CLI with click/typer
