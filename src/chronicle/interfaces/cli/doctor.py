"""Doctor command for the primary Chronicle CLI."""

import json
from typing import Annotated

import typer

from chronicle.models.doctor import DoctorSeverity
from chronicle.services.doctor_service import DoctorService


def register_doctor_command(app: typer.Typer) -> None:
    """Register doctor command."""

    @app.command("doctor")
    def doctor_cmd(
        json_output: Annotated[bool, typer.Option("--json")] = False,
    ) -> None:
        """Run read-only health checks for the current Chronicle."""
        report = DoctorService().run()
        if json_output:
            typer.echo(json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2))
        else:
            typer.echo("Chronicle Doctor")
            typer.echo("")
            typer.echo(f"Status: {report.status.value}")
            if report.chronicle_id:
                typer.echo(f"Chronicle ID: {report.chronicle_id}")
            typer.echo("")
            for check in report.checks:
                typer.echo(f"[{check.severity.value}] {check.check_id}: {check.summary}")
                if check.detail:
                    typer.echo(f"  Detail: {check.detail}")
                if check.recommendation:
                    typer.echo(f"  Recommendation: {check.recommendation}")

        if report.status == DoctorSeverity.ERROR:
            raise typer.Exit(code=1)
