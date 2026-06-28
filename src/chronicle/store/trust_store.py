"""Persistence for local trust profiles and relations."""

import json
from pathlib import Path

from chronicle.models.trust import NodeProfile, TrustRelation
from chronicle.store.paths import ChroniclePaths


class TrustStore:
    def __init__(self, paths: ChroniclePaths) -> None:
        self.paths = paths

    def save_node_profile(self, profile: NodeProfile) -> Path:
        self.paths.trust_nodes_dir.mkdir(parents=True, exist_ok=True)
        path = self.paths.trust_nodes_dir / f"{profile.node_id}.json"
        path.write_text(json.dumps(profile.model_dump(mode="json"), ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def load_node_profile(self, node_id: str) -> NodeProfile:
        path = self.paths.trust_nodes_dir / f"{node_id}.json"
        raw = json.loads(path.read_text(encoding="utf-8"))
        return NodeProfile.model_validate(raw)

    def list_node_profiles(self) -> list[NodeProfile]:
        if not self.paths.trust_nodes_dir.exists():
            return []
        rows = []
        for path in sorted(self.paths.trust_nodes_dir.glob("*.json")):
            raw = json.loads(path.read_text(encoding="utf-8"))
            rows.append(NodeProfile.model_validate(raw))
        return rows

    def save_relation(self, relation: TrustRelation) -> Path:
        self.paths.trust_relations_dir.mkdir(parents=True, exist_ok=True)
        path = self.paths.trust_relations_dir / f"{relation.relation_id}.json"
        path.write_text(json.dumps(relation.model_dump(mode="json"), ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def load_relation(self, relation_id: str) -> TrustRelation:
        path = self.paths.trust_relations_dir / f"{relation_id}.json"
        raw = json.loads(path.read_text(encoding="utf-8"))
        return TrustRelation.model_validate(raw)

    def list_relations(self) -> list[TrustRelation]:
        if not self.paths.trust_relations_dir.exists():
            return []
        rows = []
        for path in sorted(self.paths.trust_relations_dir.glob("*.json")):
            raw = json.loads(path.read_text(encoding="utf-8"))
            rows.append(TrustRelation.model_validate(raw))
        return rows
