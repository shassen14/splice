from __future__ import annotations

from dataclasses import dataclass, field

# Sensible defaults — override per-track as needed
VOICE_LUFS: float = -10.0
MUSIC_LUFS: float = -30.0
MUSIC_IDLE_LUFS: float = -18.0


@dataclass
class NormalizePass:
    """Measure integrated loudness on one Resolve audio track and adjust gain to target_lufs.

    Use separate instances for voice and music tracks:
        NormalizePass(track_index=1, target_lufs=VOICE_LUFS)
        NormalizePass(track_index=3, target_lufs=MUSIC_LUFS)
    """

    track_index: int          # 1-based Resolve audio track index
    target_lufs: float = VOICE_LUFS

    def run(self, timeline) -> None:
        # TODO:
        #   1. render this track to a temp WAV via Resolve's export API
        #   2. measure with pyloudnorm.Meter().integrated_loudness()
        #   3. gain_delta = target_lufs - measured_lufs
        #   4. apply gain_delta via timeline.SetTrackVolume or per-clip audio attributes
        raise NotImplementedError(
            f"NormalizePass(track={self.track_index}, target={self.target_lufs} LUFS)"
        )


@dataclass
class DuckPass:
    """Automate music track volume relative to voice activity.

    When any voice track has signal the music drops to voice_present_lufs.
    After silence longer than idle_threshold_seconds the music rises to voice_absent_lufs.
    Transitions are smoothed with attack/release envelopes.

    Example — two presenters, one music bed:
        DuckPass(voice_tracks=[1, 2], music_track=3)
    """

    voice_tracks: list[int]                      # 1-based track indices
    music_track: int                             # 1-based track index
    voice_present_lufs: float = MUSIC_LUFS       # music level while voice is active
    voice_absent_lufs: float = MUSIC_IDLE_LUFS   # music level during silence
    idle_threshold_seconds: float = 1.0          # silence gap before music rises
    attack_ms: float = 200.0                     # fade-down speed when voice appears
    release_ms: float = 500.0                    # fade-up speed when silence detected

    def run(self, timeline) -> None:
        # TODO:
        #   1. for each voice_track render to temp WAV, detect silence windows via RMS
        #   2. union voice-present windows across all voice_tracks
        #   3. invert to get silence windows; apply idle_threshold_seconds filter
        #   4. at each voice-start transition: write keyframes on music_track ramping
        #      down over attack_ms to voice_present_lufs
        #   5. at each silence-start transition (post-idle): write keyframes ramping
        #      up over release_ms to voice_absent_lufs
        raise NotImplementedError(
            f"DuckPass(voice={self.voice_tracks}, music={self.music_track})"
        )


@dataclass
class AnomalyPass:
    """Flag clipping peaks and unexpected silence gaps on the timeline."""

    clip_db_threshold: float = -1.0    # flag any sample above this
    silence_gap_seconds: float = 2.0   # flag silence gaps longer than this

    def run(self, timeline) -> None:
        # TODO: scan per-track waveform data; print {track, timecode, reason} for each hit
        raise NotImplementedError("AnomalyPass")
