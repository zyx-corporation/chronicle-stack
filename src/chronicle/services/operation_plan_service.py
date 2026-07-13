"""Operation plan preview and proposal conversion service."""

from __future__ import annotations

from pathlib import Path

from chronicle.errors import (
    ArtifactNotFoundError,
    OperationPlanAlreadyConvertedError,
    OperationPlanNotFoundError,
    OperationPlanStaleTargetError,
)
from chronicle.models.event import Actor, EventType
from chronicle.ids import generate_id
from chronicle.models.operation_plan import OperationPlan, OperationPlanStep, OperationPlanTargetRef
from chronicle.services.artifact_service import ArtifactService
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.proposal_service import ProposalService


class OperationPlanService:
    """Build preview-first operation plans and convert them into proposals."""

    def __init__(self, root: Path | None = None) -> None:
        self.chronicle = ChronicleService(root)
        self.artifacts = ArtifactService(root)
        self.proposals = ProposalService(root)

    def build_artifact_update_plan(
        self,
        *,
        artifact_id: str,
        summary: str,
        content: str,
        proposed_title: str = "",
        source_refs: list[str] | None = None,
    ) -> OperationPlan:
        artifact = self.artifacts.get(artifact_id)
        return OperationPlan(
            plan_id=generate_id("plan"),
            plan_type="artifact_update",
            operation="artifact.propose_update",
            target_refs=[
                OperationPlanTargetRef(
                    record_id=artifact_id,
                    record_type="artifact",
                    expected_version_id=artifact.current_version_id,
                )
            ],
            source_refs=source_refs or [],
            steps=[
                OperationPlanStep(
                    step_id="step_1",
                    capability="artifact.propose_update",
                    action="replace_content",
                    parameters={
                        "artifact_id": artifact_id,
                        "summary": summary,
                        "content_length": str(len(content)),
                        "proposed_title": proposed_title,
                    },
                )
            ],
            constraints={"preserve": ["append_only_proposal", "review_before_apply"]},
        )

    def convert_artifact_update_plan_to_proposal(
        self,
        *,
        plan: OperationPlan,
        summary: str,
        content: str,
        proposed_title: str = "",
    ):
        target = self._artifact_target(plan)
        artifact = self.artifacts.get(target.record_id)
        if artifact.current_version_id != target.expected_version_id:
            raise OperationPlanStaleTargetError(
                artifact_id=artifact.artifact_id,
                expected_version_id=target.expected_version_id,
                actual_version_id=artifact.current_version_id,
            )
        if self._proposal_exists_for_plan(plan.plan_id):
            raise OperationPlanAlreadyConvertedError(plan.plan_id)

        return self.proposals.propose_artifact_update(
            artifact_id=artifact.artifact_id,
            summary=summary,
            content=content,
            proposed_title=proposed_title,
            extra_payload={
                "operation_plan": plan.model_dump(mode="json"),
            },
        )

    def persist_plan(self, plan: OperationPlan, *, summary: str = "") -> str:
        event = self.chronicle.record_event(
            event_type=EventType.ASSISTANT_OUTPUT,
            actor=Actor.ASSISTANT,
            summary=summary or f"Operation plan recorded: {plan.operation}",
            payload={
                "operation_plan": plan.model_dump(mode="json"),
                "preview_only": plan.preview_only,
            },
            review_status=None,
        )
        self.chronicle.rebuild_indexes()
        return event.event_id

    def list_plans(self) -> list[dict]:
        self.chronicle.require_initialized()
        rows: list[dict] = []
        proposal_rows = self.proposals.list_proposals()
        applied_by_plan_id = self._applied_events_by_plan_id()
        for event in self.chronicle.jsonl.read_all():
            payload = getattr(event, "payload", {})
            operation_plan = payload.get("operation_plan")
            if not isinstance(operation_plan, dict):
                continue
            plan = OperationPlan.model_validate(operation_plan)
            proposal_row = self._proposal_row_for_plan(plan.plan_id, proposal_rows)
            applied_event = applied_by_plan_id.get(plan.plan_id)
            target_status = self._target_status(plan)
            action_preview = self._action_preview(
                plan=plan,
                proposal_row=proposal_row,
                applied_event=applied_event,
                target_status=target_status,
            )
            rows.append(
                {
                    "event_id": event.event_id,
                    "timestamp": event.timestamp.isoformat(),
                    "summary": event.summary,
                    "preview_only": bool(payload.get("preview_only", True)),
                    "plan": plan,
                    "proposal_event_id": proposal_row["event_id"] if proposal_row else None,
                    "latest_review_disposition": (
                        proposal_row["latest_review_disposition"] if proposal_row else None
                    ),
                    "converted": proposal_row is not None,
                    "applied": applied_event is not None,
                    "applied_event_id": applied_event["event_id"] if applied_event else None,
                    "target_status": target_status,
                    "action_preview": action_preview,
                    "action_preview_summary": {
                        "status": action_preview["status"],
                        "message": action_preview["message"],
                        "next_action_command": action_preview["next_action_command"],
                    },
                }
            )
        return rows

    def get_plan(self, plan_id: str) -> dict:
        for row in self.list_plans():
            plan = row["plan"]
            if plan.plan_id == plan_id:
                return row
        raise OperationPlanNotFoundError(plan_id)

    def _artifact_target(self, plan: OperationPlan) -> OperationPlanTargetRef:
        if plan.operation != "artifact.propose_update" or not plan.target_refs:
            raise ArtifactNotFoundError("")
        target = plan.target_refs[0]
        if target.record_type != "artifact":
            raise ArtifactNotFoundError(target.record_id)
        return target

    def _proposal_exists_for_plan(self, plan_id: str) -> bool:
        for row in self.proposals.list_proposals():
            proposal = row.get("proposal", {})
            operation_plan = proposal.get("operation_plan")
            if isinstance(operation_plan, dict) and operation_plan.get("plan_id") == plan_id:
                return True
        return False

    @staticmethod
    def _proposal_row_for_plan(plan_id: str, proposal_rows: list[dict]) -> dict | None:
        for row in proposal_rows:
            proposal = row.get("proposal", {})
            operation_plan = proposal.get("operation_plan")
            if isinstance(operation_plan, dict) and operation_plan.get("plan_id") == plan_id:
                return row
        return None

    def _applied_events_by_plan_id(self) -> dict[str, dict]:
        rows: dict[str, dict] = {}
        for event in self.chronicle.jsonl.read_all():
            proposal_apply = getattr(event, "payload", {}).get("proposal_apply")
            if not isinstance(proposal_apply, dict):
                continue
            plan_id = proposal_apply.get("operation_plan_id")
            if isinstance(plan_id, str) and plan_id:
                rows[plan_id] = {
                    "event_id": event.event_id,
                    "proposal_apply": proposal_apply,
                }
        return rows

    def _target_status(self, plan: OperationPlan) -> dict[str, str | bool]:
        target = self._artifact_target(plan)
        artifact = self.artifacts.get(target.record_id)
        stale = artifact.current_version_id != target.expected_version_id
        return {
            "target_id": artifact.artifact_id,
            "current_version_id": artifact.current_version_id,
            "expected_version_id": target.expected_version_id,
            "stale": stale,
        }

    def _action_preview(
        self,
        *,
        plan: OperationPlan,
        proposal_row: dict | None,
        applied_event: dict | None,
        target_status: dict[str, str | bool],
    ) -> dict[str, object]:
        target_id = str(target_status["target_id"])
        stale = bool(target_status["stale"])
        rebuild_command = (
            f"chronicle plan artifact-update-preview --artifact {target_id} "
            f'--summary "<summary>" --content "<content>" --record --json'
        )
        if applied_event is not None:
            return {
                "status": "applied",
                "message": "Plan lineage reached proposal apply; Chronicle primary record now reflects the approved change.",
                "next_action_command": "chronicle review queue --include-resolved --json",
                "available_commands": [
                    "chronicle review queue --include-resolved --json",
                    f"chronicle plan show --id {plan.plan_id} --json",
                ],
            }
        if proposal_row is not None:
            proposal_event_id = proposal_row["event_id"]
            if stale:
                return {
                    "status": "stale_target",
                    "message": "Plan target changed after preview; rebuild the plan before trusting the pending proposal/apply path.",
                    "next_action_command": rebuild_command,
                    "available_commands": [
                        rebuild_command,
                        f"chronicle plan show --id {plan.plan_id} --json",
                        "chronicle review queue --include-resolved --json",
                    ],
                }
            return {
                "status": "ready_for_review",
                "message": "Proposal exists and target version still matches the previewed plan; review can proceed.",
                "next_action_command": f"chronicle review approve --event {proposal_event_id} --reviewer <name>",
                "available_commands": [
                    f"chronicle review approve --event {proposal_event_id} --reviewer <name>",
                    f"chronicle artifact apply-proposal --event {proposal_event_id} --json",
                    "chronicle review queue --include-resolved --json",
                ],
            }
        if stale:
            return {
                "status": "stale_preview",
                "message": "Recorded preview no longer matches the current target version; rebuild before converting to proposal.",
                "next_action_command": rebuild_command,
                "available_commands": [
                    rebuild_command,
                    f"chronicle plan show --id {plan.plan_id} --json",
                ],
            }
        return {
            "status": "preview_only",
            "message": "Recorded preview is still current; convert it to a proposal when ready.",
            "next_action_command": (
                f"chronicle plan artifact-update-proposal --artifact {target_id} "
                f'--summary "<summary>" --content "<content>" --json'
            ),
            "available_commands": [
                f"chronicle plan show --id {plan.plan_id} --json",
                (
                    f"chronicle plan artifact-update-proposal --artifact {target_id} "
                    f'--summary "<summary>" --content "<content>" --json'
                ),
            ],
        }
