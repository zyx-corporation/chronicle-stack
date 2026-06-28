from chronicle.models.reaction import ChronicleReactionType
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.reaction_service import ReactionService


def test_reaction_service_records_meaningful_relation(tmp_path):
    ChronicleService(tmp_path).init("Reaction Test")
    reaction = ReactionService(tmp_path).record(
        reaction_type=ChronicleReactionType.REFERENCE,
        created_by="user",
        target_object_id="obj_target",
        summary="Reference this object from another context",
        detail="Meaningful reaction instead of a generic like.",
        source_object_id="obj_source",
    )

    assert reaction.reaction_id.startswith("react_")
    rows = ReactionService(tmp_path).list_reactions()
    assert rows[0].target_object_id == "obj_target"
    assert rows[0].source_object_id == "obj_source"
