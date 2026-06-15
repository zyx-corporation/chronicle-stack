"""Export-related doctor checks."""

from pathlib import Path

from chronicle.doctor.check_factory import ok, warn
from chronicle.exporters.html_exporter import HtmlDashboardExporter
from chronicle.models.doctor import DoctorCheck
from chronicle.services.graph_export_service import GraphExportService
from chronicle.store.paths import ChroniclePaths


def check_exports(paths: ChroniclePaths, root: Path) -> list[DoctorCheck]:
    """Check whether derived exports can be generated."""
    if not paths.is_initialized():
        return [
            warn(
                "graph_export_available",
                "graph export cannot be checked before initialization",
            ),
            warn(
                "html_export_available",
                "HTML export cannot be checked before initialization",
            ),
        ]
    return [
        check_graph_export(root),
        check_html_export(root),
    ]


def check_graph_export(root: Path) -> DoctorCheck:
    try:
        graph = GraphExportService(root).export_graph()
    except Exception as exc:
        return warn(
            "graph_export_available",
            "graph export could not be generated",
            detail=str(exc),
        )
    detail = f"{len(graph.nodes)} node(s), {len(graph.edges)} edge(s)"
    return ok("graph_export_available", "graph export can be generated", detail)


def check_html_export(root: Path) -> DoctorCheck:
    try:
        html = HtmlDashboardExporter(root).export()
    except Exception as exc:
        return warn(
            "html_export_available",
            "HTML dashboard export could not be generated",
            detail=str(exc),
        )
    detail = f"{len(html)} character(s)"
    return ok("html_export_available", "HTML dashboard export can be generated", detail)
