from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

import typer

app = typer.Typer(
    name="splice",
    help="DaVinci Resolve editing assistant — automates mechanical post-production passes.",
    no_args_is_help=True,
)

audio_app  = typer.Typer(help="Audio passes: normalize, duck, flags.", no_args_is_help=True)
color_app  = typer.Typer(help="Color passes: lut, awb, grade.",        no_args_is_help=True)
finish_app = typer.Typer(help="Finish passes: intro, outro, lower-thirds.", no_args_is_help=True)
reframe_app = typer.Typer(help="Reframe passes: track, layout.",        no_args_is_help=True)

app.add_typer(audio_app,   name="audio")
app.add_typer(color_app,   name="color")
app.add_typer(finish_app,  name="finish")
app.add_typer(reframe_app, name="reframe")


# ---------------------------------------------------------------------------
# splice check
# ---------------------------------------------------------------------------

@app.command()
def check() -> None:
    """Verify Resolve is running and the scripting API is reachable."""
    try:
        from splice.resolve.client import get_resolve, get_current_project
    except SystemExit as exc:
        typer.echo(f"[FAIL] {exc}", err=True)
        raise typer.Exit(1)

    resolve = get_resolve()
    if resolve is None:
        typer.echo("[FAIL] Resolve API returned None — is DaVinci Resolve running?", err=True)
        raise typer.Exit(1)

    project = get_current_project()
    if project is None:
        typer.echo("[WARN] Resolve is running but no project is open.")
    else:
        typer.echo(f"[OK] Resolve is running. Current project: {project.GetName()}")


# ---------------------------------------------------------------------------
# splice script  (teleprompter)
# ---------------------------------------------------------------------------

@app.command()
def script(
    file: Path = typer.Argument(..., help="Path to script text file."),
    speed: int = typer.Option(2, "--speed", help="Scroll speed in pixels per tick."),
) -> None:
    """Open floating teleprompter window for the given script file."""
    if not file.exists():
        typer.echo(f"Script file not found: {file}", err=True)
        raise typer.Exit(1)
    from splice.teleprompter.overlay import show
    typer.echo(f"Opening teleprompter: {file}  (Space=start/stop, Esc=quit, ↑↓=speed)")
    show(file, scroll_speed=speed)


# ---------------------------------------------------------------------------
# splice audio normalize
# ---------------------------------------------------------------------------

@audio_app.command("normalize")
def audio_normalize(
    track: int = typer.Argument(..., help="1-based audio track index in Resolve."),
    lufs: float = typer.Option(-10.0, "--lufs", help="Target integrated loudness (LUFS)."),
) -> None:
    """Normalize one audio track to a target LUFS level.

    \b
    Voice tracks:  splice audio normalize 1 --lufs -10
    Music tracks:  splice audio normalize 3 --lufs -30
    """
    from splice.resolve.client import get_current_timeline
    from splice.audio.passes import NormalizePass

    timeline = get_current_timeline()
    typer.echo(f"Normalizing track {track} → {lufs} LUFS…")
    NormalizePass(track_index=track, target_lufs=lufs).run(timeline)
    typer.echo("Done.")


# ---------------------------------------------------------------------------
# splice audio duck
# ---------------------------------------------------------------------------

@audio_app.command("duck")
def audio_duck(
    voice: List[int] = typer.Option(
        ..., "--voice", help="Voice track index (repeat for multiple tracks)."
    ),
    music: int = typer.Option(..., "--music", help="Music track index to duck."),
    present_lufs: float = typer.Option(
        -30.0, "--present-lufs", help="Music level while voice is active."
    ),
    absent_lufs: float = typer.Option(
        -18.0, "--absent-lufs", help="Music level during silence."
    ),
    idle_sec: float = typer.Option(
        1.0, "--idle-sec", help="Silence duration (seconds) before music rises."
    ),
    attack_ms: float = typer.Option(200.0, "--attack-ms", help="Fade-down time in ms."),
    release_ms: float = typer.Option(500.0, "--release-ms", help="Fade-up time in ms."),
) -> None:
    """Duck the music track relative to voice track activity.

    \b
    One presenter:  splice audio duck --voice 1 --music 3
    Two presenters: splice audio duck --voice 1 --voice 2 --music 3
    """
    from splice.resolve.client import get_current_timeline
    from splice.audio.passes import DuckPass

    timeline = get_current_timeline()
    typer.echo(f"Ducking track {music} using voice tracks {list(voice)}…")
    DuckPass(
        voice_tracks=list(voice),
        music_track=music,
        voice_present_lufs=present_lufs,
        voice_absent_lufs=absent_lufs,
        idle_threshold_seconds=idle_sec,
        attack_ms=attack_ms,
        release_ms=release_ms,
    ).run(timeline)
    typer.echo("Done.")


# ---------------------------------------------------------------------------
# splice audio flags
# ---------------------------------------------------------------------------

@audio_app.command("flags")
def audio_flags(
    clip_db: float = typer.Option(-1.0, "--clip-db", help="Flag samples above this dB level."),
    silence_gap: float = typer.Option(
        2.0, "--silence-gap", help="Flag silence gaps longer than this (seconds)."
    ),
) -> None:
    """Scan timeline audio for clipping peaks and unexpected silence gaps."""
    from splice.resolve.client import get_current_timeline
    from splice.audio.passes import AnomalyPass

    timeline = get_current_timeline()
    AnomalyPass(clip_db_threshold=clip_db, silence_gap_seconds=silence_gap).run(timeline)


# ---------------------------------------------------------------------------
# splice color lut / awb / grade
# ---------------------------------------------------------------------------

@color_app.command("lut")
def color_lut(
    path: Path = typer.Argument(..., help="Path to .cube LUT file."),
) -> None:
    """Apply a LUT to all clips on the color track."""
    from splice.resolve.client import get_current_timeline
    from splice.color.passes import LUTPass

    timeline = get_current_timeline()
    typer.echo(f"Applying LUT: {path}")
    LUTPass(lut_path=path).run(timeline)
    typer.echo("Done.")


@color_app.command("awb")
def color_awb() -> None:
    """Run auto white balance on all clips."""
    from splice.resolve.client import get_current_timeline
    from splice.color.passes import AWBPass

    timeline = get_current_timeline()
    typer.echo("Running auto white balance…")
    AWBPass().run(timeline)
    typer.echo("Done.")


@color_app.command("grade")
def color_grade(
    preset: str = typer.Argument(..., help="Grade preset name from the Resolve gallery."),
) -> None:
    """Apply a named grade preset from the gallery to all clips."""
    from splice.resolve.client import get_current_timeline
    from splice.color.passes import GradePass

    timeline = get_current_timeline()
    typer.echo(f"Applying grade preset: {preset!r}")
    GradePass(preset_name=preset).run(timeline)
    typer.echo("Done.")


# ---------------------------------------------------------------------------
# splice finish intro / outro / lower-thirds
# ---------------------------------------------------------------------------

@finish_app.command("intro")
def finish_intro(
    clip: Path = typer.Argument(..., help="Path to intro clip."),
    duration: Optional[int] = typer.Option(None, "--duration", help="Duration in frames."),
) -> None:
    """Prepend an intro clip to the timeline."""
    from splice.resolve.client import get_current_timeline
    from splice.finish.passes import IntroPass

    timeline = get_current_timeline()
    typer.echo(f"Injecting intro: {clip}")
    IntroPass(clip_path=clip, duration_frames=duration).run(timeline)
    typer.echo("Done.")


@finish_app.command("outro")
def finish_outro(
    clip: Path = typer.Argument(..., help="Path to outro clip."),
) -> None:
    """Append an outro clip to the timeline."""
    from splice.resolve.client import get_current_timeline
    from splice.finish.passes import OutroPass

    timeline = get_current_timeline()
    typer.echo(f"Injecting outro: {clip}")
    OutroPass(clip_path=clip).run(timeline)
    typer.echo("Done.")


@finish_app.command("lower-thirds")
def finish_lower_thirds(
    cues_file: Path = typer.Argument(
        ..., help="JSON file: [{text, start_frame, duration_frames}, …]"
    ),
) -> None:
    """Overlay lower-third title clips from a JSON cue file."""
    from splice.resolve.client import get_current_timeline
    from splice.finish.passes import LowerThirdsPass

    timeline = get_current_timeline()
    cues = json.loads(cues_file.read_text())
    typer.echo(f"Injecting {len(cues)} lower thirds…")
    LowerThirdsPass(cues=cues).run(timeline)
    typer.echo("Done.")


# ---------------------------------------------------------------------------
# splice reframe track / layout
# ---------------------------------------------------------------------------

@reframe_app.command("track")
def reframe_track(
    video: Path = typer.Argument(..., help="Video file to track."),
    start: int = typer.Option(0, "--start", help="Start frame."),
    end: Optional[int] = typer.Option(None, "--end", help="End frame (default: last frame)."),
) -> None:
    """Track subject with OpenCV CSRT and print keyframe output."""
    from splice.reframe.tracker import CSRTTracker

    typer.echo(f"Tracking {video} frames {start}–{end or 'end'}…")
    keyframes = CSRTTracker().track(video, start_frame=start, end_frame=end)
    typer.echo(f"Emitted {len(keyframes)} keyframes.")
    for kf in keyframes[:10]:
        typer.echo(f"  frame {kf.frame}: {kf.box}")
    if len(keyframes) > 10:
        typer.echo(f"  … ({len(keyframes) - 10} more)")


@reframe_app.command("layout")
def reframe_layout(
    preset: str = typer.Argument(
        ..., help="Layout preset: split-v | split-h | pip-corner | code-me"
    ),
) -> None:
    """Apply a Fusion comp layout preset to the current timeline."""
    from splice.resolve.client import get_current_timeline
    from splice.reframe.layouts import Layout, LayoutApplier

    try:
        layout = Layout(preset)
    except ValueError:
        valid = ", ".join(v.value for v in Layout)
        typer.echo(f"Unknown preset '{preset}'. Valid: {valid}", err=True)
        raise typer.Exit(1)

    timeline = get_current_timeline()
    typer.echo(f"Applying layout '{layout.value}'…")
    LayoutApplier(layout=layout).run(timeline)
    typer.echo("Done.")
