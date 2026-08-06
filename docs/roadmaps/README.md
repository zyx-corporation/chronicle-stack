# Roadmaps

このディレクトリは、Chronicle Stack の計画・段階設計・実装順序に関する文書を置く領域です。

## Documents

- [Overall Roadmap](overall-roadmap.md): `docs/` 配下の個別ロードマップを精査して統合した全体ロードマップ。
- [Federation Implementation Roadmap](federation-implementation-roadmap.md): 分散連合拡張の実装フェーズ、CLI候補、受け入れ条件、非対象を整理したロードマップ。
- [Chronicle Daemon and API Implementation Roadmap](chronicle-daemon-api-roadmap.md): Chronicle Stack をクロニクルの保管機構として保ったまま、常駐サービス、構造化API、Kazane/agent runtime 連携、Chronicle Cloud へ進むための段階計画。
- [Local UI Implementation Roadmap](local-ui-implementation-roadmap-2026-07.md): final UI spec、Kazane handoff、i18n / light-theme 要件を実装順序へ落とした local UI 専用ロードマップ。
- [Local UI Validation Checklist](../ui-local-validation-checklist.ja.md): 現行 local UI の shell、overview、workbench、workspace、boundary を短時間で確認する実施チェック。
- [Local UI Phase 4 Closeout](../ui-phase-4-closeout.md): Review、Runtime/Retrieval、Federation workspace の summary-first renderer と自動検証証跡。
- [v0.4 Roadmap](roadmap-v0.4.md): Operational Readiness Layer の計画。
- [v0.5 Roadmap](roadmap-v0.5.md): Security-aware Composition and Integration Layer の計画。
- [Stage C Closeout](../security/stage-c-security-boundary-closeout.md): classification、operation、LLM policy、audit、lifecycle、integrity、AI interpretation warning の完了証跡。

## Classification

Roadmap 文書は、現在の実装内容そのものではなく、実装順序、段階境界、非対象、逸脱リスクを管理するための文書です。

Release readiness、release notes、release status は `docs/releases/` 配下へ分類する方針です。
