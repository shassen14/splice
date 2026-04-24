"""Probe: Fusion comp API on TimelineItem.

Tests whether per-frame keyframe values can be written via the Fusion layer —
the only remaining candidate path for animated transform keyframes.
"""
from __future__ import annotations

from ._fmt import call, probe_methods, section, subsection

TI_FUSION_CANDIDATES = [
    "GetFusionCompByIndex",
    "GetFusionCompList",
    "AddFusionComp",
    "DeleteFusionCompByIndex",
    "ImportFusionComp",
    "ExportFusionComp",
    "GetFusionCompCount",
]

COMP_CANDIDATES = [
    "FindTool", "GetToolList", "AddTool",
    "GetCurrentTime", "SetCurrentTime",
    "GetAttrs", "SetAttrs",
    "Lock", "Unlock", "StartUndo", "EndUndo",
]

TOOL_CANDIDATES = [
    "GetAttrs", "SetAttrs",
    "GetInputList", "GetOutputList",
    "ConnectInput",
]

INPUT_CANDIDATES = [
    "SetValueAtTime", "GetValueAtTime",
    "GetValue", "SetValue",
    "GetAttrs",
]


def _probe_input(inp, label: str, test_frame: int) -> None:
    """Probe a single Fusion Input object for keyframe read/write."""
    subsection(f"Input: {label}")
    probe_methods(inp, INPUT_CANDIDATES)

    # Current value
    get_val = getattr(inp, "GetValue", None)
    if get_val:
        call("  GetValue()", get_val)

    # SetValueAtTime — the key test
    svat = getattr(inp, "SetValueAtTime", None)
    gvat = getattr(inp, "GetValueAtTime", None)
    if svat:
        print(f"\n  [keyframe write test at frame {test_frame}]")
        try:
            # Fusion uses {1: x, 2: y} for Point inputs, scalar for others
            result = svat(test_frame, 0.6)
            print(f"  SetValueAtTime({test_frame}, 0.6) → {result!r}")
        except Exception as e:
            print(f"  SetValueAtTime({test_frame}, 0.6) → {type(e).__name__}: {e}")
            try:
                result = svat(test_frame, {1: 0.6, 2: 0.4})
                print(f"  SetValueAtTime({test_frame}, {{1:0.6, 2:0.4}}) → {result!r}  [Point input form]")
            except Exception as e2:
                print(f"  SetValueAtTime point form → {type(e2).__name__}: {e2}")

        if gvat:
            try:
                readback = gvat(test_frame)
                print(f"  GetValueAtTime({test_frame}) → {readback!r}")
                if readback is not None and readback is not False:
                    print("  *** FUSION KEYFRAME READ/WRITE WORKS ***")
                else:
                    print("  *** KEYFRAME WRITE UNCONFIRMED — readback empty ***")
            except Exception as e:
                print(f"  GetValueAtTime({test_frame}) → {type(e).__name__}: {e}")
    else:
        print("  SetValueAtTime absent on this input.")


def _probe_transform_tool(comp, test_frame: int) -> None:
    """Add a Transform tool, probe its inputs, then clean up."""
    subsection("AddTool('Transform') — keyframe write test")

    add_tool = getattr(comp, "AddTool", None)
    if not add_tool:
        print("  AddTool absent — cannot test.")
        return

    try:
        t = add_tool("Transform")
    except Exception as e:
        print(f"  AddTool('Transform') → {type(e).__name__}: {e}")
        return

    if not t:
        print("  AddTool('Transform') returned None.")
        return

    print(f"  AddTool('Transform') → {t!r}")

    # Try GetInputList first (confirmed present from previous probe)
    get_inputs = getattr(t, "GetInputList", None)
    if get_inputs:
        inputs = call("  t.GetInputList()", get_inputs)
        if inputs and isinstance(inputs, dict):
            print(f"  Input names: {[str(v) for v in inputs.values()][:8]}")
            # Pick the first non-trivial input to test SetValueAtTime
            test_input = None
            test_label = None
            for k, inp in inputs.items():
                name = str(inp)
                if "Center" in name or "Size" in name or "Angle" in name or "Aspect" in name:
                    test_input = inp
                    test_label = name
                    break
            if test_input is None and inputs:
                test_input = next(iter(inputs.values()))
                test_label = str(test_input)
            if test_input:
                _probe_input(test_input, test_label, test_frame)

    # Also try magic bracket access — PyRemoteObjects sometimes support this
    # even when getattr("Inputs") returns None
    subsection("Direct bracket access: t['Center']")
    try:
        center = t["Center"]
        print(f"  t['Center'] → {center!r}")
        if center:
            _probe_input(center, "Center (bracket access)", test_frame)
    except Exception as e:
        print(f"  t['Center'] → {type(e).__name__}: {e}")

    # Remove the tool — Fusion comps don't have a RemoveTool per se,
    # but we can delete the whole comp via the TimelineItem after.


def _probe_comp(comp, test_frame: int) -> None:
    subsection("Fusion Composition")
    probe_methods(comp, COMP_CANDIDATES)

    tools = call("  GetToolList()", comp.GetToolList) if getattr(comp, "GetToolList", None) else None
    if tools and isinstance(tools, dict):
        print(f"  Default tools in empty comp: {len(tools)}")
        for k, t in tools.items():
            attrs = t.GetAttrs() if getattr(t, "GetAttrs", None) else {}
            name = attrs.get("TOOLS_Name", f"tool_{k}")
            print(f"    [{k}] {name}")

    _probe_transform_tool(comp, test_frame)


def probe(video_item) -> None:
    section("11. Fusion API")

    subsection("TimelineItem Fusion methods")
    probe_methods(video_item, TI_FUSION_CANDIDATES)

    count_fn = getattr(video_item, "GetFusionCompCount", None)
    count = count_fn() if count_fn else 0
    print(f"  Existing Fusion comps: {count}")

    add_comp = getattr(video_item, "AddFusionComp", None)
    get_by_idx = getattr(video_item, "GetFusionCompByIndex", None)

    comp = None
    added = False

    if count and count > 0 and get_by_idx:
        comp = get_by_idx(1)
        print("  Using existing comp.")
    elif add_comp:
        subsection("Adding fresh Fusion comp for probe (will be cleaned up)")
        comp = add_comp()
        added = True
        print(f"  AddFusionComp() → {comp!r}")

    if not comp:
        print("  Could not get a Fusion comp — cannot probe further.")
        return

    # Use the timeline item's start frame as the test frame
    start = video_item.GetStart() if getattr(video_item, "GetStart", None) else 0
    test_frame = start + 5

    _probe_comp(comp, test_frame)

    # Clean up: delete the comp we added
    if added:
        del_fn = getattr(video_item, "DeleteFusionCompByIndex", None)
        if del_fn:
            result = del_fn(1)
            print(f"\n  Cleanup: DeleteFusionCompByIndex(1) → {result!r}")
        else:
            print("\n  Note: DeleteFusionCompByIndex absent — comp left on clip. Remove manually.")
