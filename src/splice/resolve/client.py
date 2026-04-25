try:
    import DaVinciResolveScript as dvr
except ImportError:
    raise SystemExit(
        "Resolve scripting API not found. "
        "Is DaVinci Resolve installed and running?\n"
        "Check that RESOLVE_SCRIPT_API and RESOLVE_SCRIPT_LIB env vars are set, "
        "or that Resolve has added its scripting path to PYTHONPATH."
    )


def get_resolve():
    return dvr.scriptapp("Resolve")


def open_page(page: str) -> None:
    """Switch Resolve to the named page ("edit", "fairlight", "deliver", etc.)."""
    get_resolve().OpenPage(page)


def get_project_manager():
    return get_resolve().GetProjectManager()


def get_current_project():
    return get_project_manager().GetCurrentProject()


def get_current_timeline():
    project = get_current_project()
    if project is None:
        raise SystemExit("No project is open in Resolve.")
    timeline = project.GetCurrentTimeline()
    if timeline is None:
        raise SystemExit("No timeline is active in the current project.")
    return timeline
