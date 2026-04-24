"""Probe: Color API — node graphs, LUTs, CDL, gallery, auto-balance.

Requires an open project with at least one video timeline item.
Must be called with a video TimelineItem and the current Project object.
"""
from __future__ import annotations

from ._fmt import call, probe_methods, section, subsection

# ── TimelineItem color-related methods ──────────────────────────────────────

TI_COLOR_CANDIDATES = [
    "GetNodeGraph",
    "GetCurrentColorVersion",
    "GetColorVersionList",
    "AddColorVersion",
    "DeleteColorVersion",
    "LoadColorVersion",
    "RenameColorVersion",
    "CopyGrades",
    "GrabStill",
    "GrabAllStills",
    "ApplyGradeFromDRX",
    "AutoBalance",
    "AutoColor",
    "ColorBalance",
    "ResetGrade",
    "GetLUT",
    "SetLUT",
]

# ── Node graph object ────────────────────────────────────────────────────────

NODEGRAPH_CANDIDATES = [
    "GetNodeCount",
    "GetNodeCountByType",
    "GetNode",
    "GetNodeByIndex",
    "AddNode",
    "DeleteNode",
    "InsertNode",
    "SetLUT",
    "GetLUT",
    "ExportLUT",
    "ApplyGradeFromDRX",
    "GetList",
    "Reset",
    "GetNodeLabel",
    "SetNodeLabel",
    "GetNodeEnabled",
    "SetNodeEnabled",
]

# ── Individual color node ────────────────────────────────────────────────────

NODE_CANDIDATES = [
    "GetNodeLabel",
    "SetNodeLabel",
    "GetNodeEnabled",
    "SetNodeEnabled",
    "GetLUT",
    "SetLUT",
    "GetCDL",
    "SetCDL",
    "GetType",
    "GetIndex",
]

# ── Gallery ──────────────────────────────────────────────────────────────────

GALLERY_CANDIDATES = [
    "GetAlbumList",
    "GetCurrentStillAlbum",
    "SetCurrentStillAlbum",
    "CreateEmptyGalleryStillAlbum",
    "DeleteGalleryStillAlbum",
    "GetGalleryStillAlbums",
    "ImportIntoGalleryStillAlbum",
]

ALBUM_CANDIDATES = [
    "GetStills",
    "GetLabel",
    "SetLabel",
    "ImportStills",
    "ExportStills",
    "DeleteStills",
]

STILL_CANDIDATES = [
    "GetLabel",
    "SetLabel",
]


def probe_nodegraph(ng) -> None:
    subsection("NodeGraph methods")
    probe_methods(ng, NODEGRAPH_CANDIDATES)

    node_count = call("GetNodeCount()", ng.GetNodeCount) if getattr(ng, "GetNodeCount", None) else None

    if node_count and isinstance(node_count, int):
        subsection(f"First node (index 1) — {node_count} node(s) total")
        get_fn = getattr(ng, "GetNode", None) or getattr(ng, "GetNodeByIndex", None)
        if get_fn:
            node = call("GetNode(1)", get_fn, 1)
            if node:
                probe_methods(node, NODE_CANDIDATES)
                call("  GetNodeLabel()", node.GetNodeLabel) if getattr(node, "GetNodeLabel", None) else None
                call("  GetLUT()", node.GetLUT) if getattr(node, "GetLUT", None) else None
                call("  GetCDL()", node.GetCDL) if getattr(node, "GetCDL", None) else None
                call("  GetType()", node.GetType) if getattr(node, "GetType", None) else None

    # GetLUT — read current LUT path (no args)
    if getattr(ng, "GetLUT", None):
        subsection("GetLUT() — read current LUT assignment")
        call("GetLUT()", ng.GetLUT)
        call("GetLUT(1)", ng.GetLUT, 1)  # try with node index

    # SetLUT — test with a nonsense path to discover signature (will fail but shows arg count)
    if getattr(ng, "SetLUT", None):
        subsection("SetLUT — signature discovery (safe: bad path expected to return False)")
        for args in [("/nonexistent.cube",), (1, "/nonexistent.cube"), (0, "/nonexistent.cube")]:
            try:
                result = ng.SetLUT(*args)
                print(f"  SetLUT{args} → {result!r}")
            except TypeError as e:
                print(f"  SetLUT{args} → TypeError: {e}  [wrong arg count]")
            except Exception as e:
                print(f"  SetLUT{args} → {type(e).__name__}: {e}")

    # ApplyGradeFromDRX — discover signature the same way
    if getattr(ng, "ApplyGradeFromDRX", None):
        subsection("ApplyGradeFromDRX — signature discovery")
        for args in [("/nonexistent.drx",), ("/nonexistent.drx", 0), ("/nonexistent.drx", 1)]:
            try:
                result = ng.ApplyGradeFromDRX(*args)
                print(f"  ApplyGradeFromDRX{args} → {result!r}")
            except TypeError as e:
                print(f"  ApplyGradeFromDRX{args} → TypeError: {e}  [wrong arg count]")
            except Exception as e:
                print(f"  ApplyGradeFromDRX{args} → {type(e).__name__}: {e}")

    if getattr(ng, "ExportLUT", None):
        subsection("ExportLUT present (not called — would write a file)")
        print("  ExportLUT exists. Typical call: ng.ExportLUT(path, 'cube', 33)")


def probe_gallery(project) -> None:
    section("8. Gallery")
    gallery_fn = getattr(project, "GetGallery", None)
    if not gallery_fn:
        print("  GetGallery absent on Project — skipping.")
        return

    gallery = call("project.GetGallery()", gallery_fn)
    if not gallery:
        print("  No gallery returned.")
        return

    probe_methods(gallery, GALLERY_CANDIDATES)

    # Album list
    get_albums = (
        getattr(gallery, "GetAlbumList", None)
        or getattr(gallery, "GetGalleryStillAlbums", None)
    )
    if get_albums:
        albums = call("GetAlbumList()", get_albums)
        if albums and isinstance(albums, list) and len(albums) > 0:
            album = albums[0]
            subsection(f"First album — {len(albums)} album(s)")
            probe_methods(album, ALBUM_CANDIDATES)
            stills_fn = getattr(album, "GetStills", None)
            if stills_fn:
                stills = call("album.GetStills()", stills_fn)
                if stills and isinstance(stills, list) and len(stills) > 0:
                    still = stills[0]
                    subsection(f"First still — {len(stills)} still(s)")
                    probe_methods(still, STILL_CANDIDATES)
                    call("  still.GetLabel()", still.GetLabel) if getattr(still, "GetLabel", None) else None


def probe(video_item, project) -> None:
    section("7. Color API")

    subsection("TimelineItem color methods")
    probe_methods(video_item, TI_COLOR_CANDIDATES)

    # Auto-balance candidates — the ones we most want to confirm/deny
    subsection("Auto-balance method check (most wanted)")
    for name in ("AutoBalance", "AutoColor", "ColorBalance", "ResetGrade"):
        present = getattr(video_item, name, None) is not None
        print(f"  {name:<30} {'PRESENT' if present else 'absent'}")

    # Color versions
    subsection("Color versions")
    if getattr(video_item, "GetCurrentColorVersion", None):
        call("GetCurrentColorVersion()", video_item.GetCurrentColorVersion)
    if getattr(video_item, "GetColorVersionList", None):
        call("GetColorVersionList()", video_item.GetColorVersionList)

    # Node graph
    subsection("GetNodeGraph()")
    get_ng = getattr(video_item, "GetNodeGraph", None)
    if not get_ng:
        print("  GetNodeGraph absent on TimelineItem.")
    else:
        ng = call("GetNodeGraph()", get_ng)
        if ng:
            probe_nodegraph(ng)
        else:
            print("  GetNodeGraph() returned None/empty.")

    probe_gallery(project)
