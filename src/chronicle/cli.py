"""Chronicle CLI — primary interface for Chronicle Core."""

from importlib.metadata import PackageNotFoundError, version as _package_version
from typing import Annotated

import typer

from chronicle.cli_package import package_app
from chronicle.interfaces.cli.artifact import artifact_app
from chronicle.interfaces.cli.boundary import boundary_app
from chronicle.interfaces.cli.core import register_core_commands
from chronicle.interfaces.cli.decision import decision_app
from chronicle.interfaces.cli.doctor import register_doctor_command
from chronicle.interfaces.cli.export import register_export_command
from chronicle.interfaces.cli.index import index_app
from chronicle.interfaces.cli.injection import injection_app
from chronicle.interfaces.cli.rde import rde_app


def _version_callback(value: bool) -> None:
    if value:
        try:
            package_version = _package_version("chronicle-stack")
        except PackageNotFoundError:
            package_version = "0.0.0+unknown"
        typer.echo(f"chronicle {package_version}")
        raise typer.Exit()


app = typer.Typer(
    name="chronicle",
    help=(
        "Chronicle Stack — local-first record of context, artifacts,"
        " decisions, diffs, provenance, and boundary rules."
    ),
    no_args_is_help=True,
)


@app.callback()
def _root_callback(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=_version_callback,
            is_eager=True,
            help="Show version and exit.",
        ),
    ] = False,
) -> None:
    pass


register_core_commands(app)
register_doctor_command(app)
register_export_command(app)

app.add_typer(artifact_app, name="artifact")
app.add_typer(decision_app, name="decision")
app.add_typer(rde_app, name="rde")
app.add_typer(index_app, name="index")
app.add_typer(boundary_app, name="boundary")
app.add_typer(injection_app, name="injection")
app.add_typer(package_app, name="package")


if __name__ == "__main__":
    app()
