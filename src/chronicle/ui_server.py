"""Explicit foreground local web UI for Chronicle Stack.

This module intentionally uses Python stdlib only. It serves read-only views over
local Chronicle files and must not be confused with a daemon, hosted service,
model runtime, GraphRAG engine, vector DB, or graph DB.
"""

from __future__ import annotations

import html
import ipaddress
import json
import re
import webbrowser
from dataclasses import asdict, dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote, urlparse

from chronicle.errors import ChronicleError, UIHostNotLoopbackError
from chronicle.exporters.html_exporter import HtmlDashboardExporter
from chronicle.models.runtime import RuntimeExecutionResult, RuntimeInvocationPlan, RuntimeRetrievalPlan
from chronicle.models.review import ReviewerIdentity, ReviewerIdentityKind
from chronicle.services.audit_service import AuditService
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.graph_index_service import GraphIndexService
from chronicle.services.graph_export_service import GraphExportService
from chronicle.services.integration_package_service import IntegrationPackageService
from chronicle.services.lifecycle_service import LifecycleService
from chronicle.services.package_review_service import PackageReviewService
from chronicle.services.review_service import (
    ReviewAuditInsertionError,
    ReviewDecisionPersistenceError,
    ReviewService,
    review_action_commands,
)
from chronicle.services.runtime_config_service import RuntimeConfigService
from chronicle.services.runtime_service import RuntimeService
from chronicle.services.summary_job_service import SummaryJobService
from chronicle.services.vector_index_service import VectorIndexService

DEFAULT_UI_HOST = "127.0.0.1"
DEFAULT_UI_PORT = 8765
REVIEWER_LABEL_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{1,63}$")
SESSION_LABEL_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{1,63}$")
REVIEW_WARNING_TEXT: dict[str, str] = {
    "ui_auth_not_enabled": "UI auth mode is not enabled, so reviewer identity is not enforced by the local UI boundary.",
    "ui_authorization_not_enabled": "UI authorization mode is not enabled, so reviewer permissions remain advisory only.",
    "no_reviewer_identity_recorded": "No reviewer identity metadata is available for this pending target yet.",
    "reviewer_identity_declared_only": "Reviewer identity is self-declared and has not been strengthened by a local auth boundary.",
    "reviewer_session_label_missing": "Session-gated review expects a local session label, but none was recorded.",
}
REVIEW_WARNING_LABELS: dict[str, str] = {
    "ui_auth_not_enabled": "Auth not enabled",
    "ui_authorization_not_enabled": "Authorization advisory",
    "no_reviewer_identity_recorded": "Reviewer missing",
    "reviewer_identity_declared_only": "Declared identity only",
    "reviewer_session_label_missing": "Session label required",
}
REVIEW_WARNING_PRIORITY: dict[str, int] = {
    "ui_auth_not_enabled": 0,
    "ui_authorization_not_enabled": 1,
    "reviewer_session_label_missing": 2,
    "reviewer_identity_declared_only": 3,
    "no_reviewer_identity_recorded": 4,
}
AUTH_BOUNDARY_BLOCKER_TEXT: dict[str, str] = {
    "auth_not_enabled": "Define explicit local auth boundary.",
    "authorization_not_enabled": "Define authorization semantics for reviewer actions.",
    "reviewer_identity_missing": "Record reviewer identity metadata before relying on GUI review signals.",
    "reviewer_identity_declared_only": "Strengthen reviewer identity beyond self-declared metadata.",
    "reviewer_session_label_missing": "Require session labels when session-gated review is expected.",
    "shared_machine_session_unhardened": "Clarify shared-machine expectations for session-gated review.",
}
AUTH_BOUNDARY_WARNING_TO_BLOCKER: dict[str, str] = {
    "ui_auth_not_enabled": "auth_not_enabled",
    "ui_authorization_not_enabled": "authorization_not_enabled",
    "no_reviewer_identity_recorded": "reviewer_identity_missing",
    "reviewer_identity_declared_only": "reviewer_identity_declared_only",
    "reviewer_session_label_missing": "reviewer_session_label_missing",
}
MUTATION_BLOCKER_TEXT: dict[str, str] = {
    "write_routes_disabled": "Keep write routes disabled until all explicit local mutation prerequisites are satisfied.",
    "auth_not_enabled": "Define explicit local auth boundary.",
    "authorization_not_enabled": "Define authorization semantics for reviewer actions.",
    "mutation_capability_flag_disabled": "Require the explicit mutation capability flag before any GUI write path can activate.",
    "ui_mutation_enable_flag_disabled": "Require the explicit UI mutation enable flag for each local write-capable session.",
    "reviewer_identity_missing": "Record reviewer identity metadata before using the local GUI write path.",
    "reviewer_identity_declared_only": "Strengthen reviewer identity beyond self-declared metadata before relying on GUI mutation.",
    "reviewer_session_label_missing": "Require a local session label before session-gated GUI mutation is treated as eligible.",
}
OVERVIEW_SLICE_LABELS: dict[str, str] = {
    "reviewer_identity_declared_only": "Declared identity only",
    "reviewer_session_label_missing": "Session label required",
}
UI_I18N_CATALOG: dict[str, dict[str, Any]] = {
    "ja": {
        "label.language": "表示言語",
        "locale.ja": "日本語",
        "locale.en": "English",
        "locale.zh-CN": "简体中文",
        "shell.title": "Chronicle Stack ローカルUI",
        "shell.root": "ルート",
        "shell.warning_title": "読み取り専用の前景ローカルUIです。",
        "shell.warning_body": "このUIはローカルの Chronicle ファイルを読み取りますが、レコードは書き込みません。",
        "shell.boundary_body": "daemon なし、自動起動なし、外部 model API なし、GraphRAG runtime なし、vector DB なし、graph DB なし。UI の可視化は correctness proof ではありません。",
        "shell.loading_overview": "概要を読み込み中...",
        "shell.select_json": "テーブル行の JSON を選択して単一レコードを確認します。",
        "placeholder.runtime_filter": "runtime record を絞り込む...",
        "placeholder.review_filter": "review queue を絞り込む...",
        "placeholder.summary_filter": "summary job を絞り込む...",
        "placeholder.review_note": "任意のレビュー note",
        "placeholder.reviewer": "alice",
        "placeholder.session": "desk-session-1",
        "nav./api/overview": "概要",
        "nav./api/events": "イベント",
        "nav./api/contexts": "コンテキスト",
        "nav./api/artifacts": "成果物",
        "nav./api/decisions": "判断",
        "nav./api/rde": "RDE",
        "nav./api/boundary": "境界",
        "nav./api/audit": "監査",
        "nav./api/lifecycle": "ライフサイクル",
        "nav./api/runtime-records": "ランタイム記録",
        "nav./api/review-queue": "レビューキュー",
        "nav./api/summary-jobs": "要約ジョブ",
        "nav./api/ui-boundary": "UI境界",
        "nav./api/runtime-config": "ランタイム設定",
        "nav./api/package-review": "パッケージレビュー",
        "nav./api/graph-summary": "グラフ要約",
        "nav./api/ai-index-status": "AIインデックス状態",
        "nav./api/ai-index-vector": "AIインデックスベクター",
        "nav./api/ai-index-graph-nodes": "AIインデックスグラフノード",
        "nav./api/ai-index-graph-edges": "AIインデックスグラフエッジ",
        "button.copy_cli": "CLIをコピー",
        "button.copy_recovery_cli": "復旧CLIをコピー",
        "button.preview_blocked_route": "拒否ルートをプレビュー",
        "button.apply": "適用",
        "button.actions": "操作",
        "button.reset_filter": "フィルターをリセット",
        "button.clear_slice": "スライスを解除",
        "button.open_package_review": "パッケージレビューを開く",
        "button.open_runtime_records": "ランタイム記録を開く",
        "button.open_review_queue": "レビューキューを開く",
        "button.open_summary_jobs": "要約ジョブを開く",
        "button.open_runtime_config": "ランタイム設定を開く",
        "button.open_review": "レビューを開く",
        "button.more_details": "補助詳細",
        "button.back_current_list": "現在の一覧へ戻る",
        "button.back_previous_detail": "前の詳細へ戻る",
        "status.loading_blocked_preview": "拒否ルートプレビューを読み込み中…",
        "status.applying_review_action": "レビュー操作を適用中…",
        "status.blocked_route_preview": "拒否ルートプレビュー",
        "status.review_action_result": "レビュー操作結果",
        "status.not_found": "見つかりません。",
        "status.no_message": "メッセージが返りませんでした。",
        "status.copied_recovery_cli": "recovery CLI をコピーしました: ",
        "status.copy_failed_command": "コピー失敗。コマンド: ",
        "status.active_view": "アクティブ view",
        "status.sort": "並び順",
        "status.more": "詳細",
        "status.detail": "詳細",
        "status.view": "view",
        "status.trail": "trail",
        "label.record_json": "レコードJSON",
        "label.response_json": "応答JSON",
        "label.table_detail": "詳細",
        "label.table_event": "イベント",
        "label.table_kind": "種別",
        "label.table_auth": "認証",
        "label.table_preview": "プレビュー",
        "label.table_review_route": "レビュー経路",
        "label.table_target": "対象",
        "label.table_status": "状態",
        "label.table_warnings": "警告",
        "label.table_latest_reviewer": "最新レビュアー",
        "label.table_summary_job": "要約ジョブ",
        "label.table_identity": "本人性",
        "label.table_runtime": "ランタイム",
        "notice.action_preview": "操作プレビュー",
        "notice.navigation": "ナビゲーション",
        "notice.runtime_preview": "ランタイムプレビュー",
        "notice.retrieval_handoff": "検索引き継ぎ",
        "notice.package_handoff_preview": "パッケージ引き継ぎプレビュー",
        "notice.invocation_plan": "呼び出し計画",
        "notice.provider_response": "プロバイダ応答",
        "notice.review_package_readiness": "レビュー用パッケージ準備状況",
        "notice.related_links": "関連リンク",
        "notice.auth_readiness": "認証準備状況",
        "notice.review_capability": "レビュー可否",
        "notice.mutation_enablement": "Mutation 有効化状況",
        "notice.cli_parity": "CLI整合",
        "notice.identity_assurance": "本人性保証",
        "notice.review_timeline": "レビュー履歴",
        "notice.mutation_enabled_detail": "この詳細ビューでは local mutation が有効です。各操作では明示的な reviewer context が必要で、audit-backed な review history が書き込まれます。",
        "notice.mutation_enabled_runtime_records": "この runtime-record 一覧ビューでは local mutation が有効です。各操作では明示的な reviewer context が必要で、audit-backed な review history が書き込まれます。",
        "notice.mutation_enabled_review_queue": "この一覧ビューでは local mutation が有効です。各操作では明示的な reviewer context が必要で、audit-backed な review history が書き込まれます。",
        "notice.mutation_enabled_summary_jobs": "summary-backed review target では local mutation が有効です。各操作では明示的な reviewer context が必要で、audit-backed な review history が書き込まれます。",
        "notice.blocked_route_preview_runtime_records": "Runtime-record の blocked-route preview は read-only のままで、CLI fallback contract を返します。",
        "notice.blocked_route_preview_review_queue": "Review queue の blocked-route preview は read-only のままで、CLI fallback contract を返します。",
        "notice.blocked_route_preview_summary_jobs": "Summary jobs の blocked-route preview は read-only のままで、CLI fallback contract を返します。",
        "notice.blocked_route_preview_detail": "Blocked route preview は read-only のままで、CLI fallback contract を返します。",
        "badge.auth_aligned": "認証整合",
        "badge.auth_advisory": "認証注意",
        "badge.auth_na": "認証なし",
        "badge.identity_aligned": "本人性整合",
        "badge.identity_advisory": "本人性注意",
        "badge.identity_na": "本人性なし",
        "badge.ready": "準備完了",
        "badge.resolved": "解決済み",
        "badge.advisory": "助言のみ",
        "badge.package_ready": "パッケージ準備完了",
        "badge.package_advisory": "パッケージ要確認",
        "badge.package_unknown": "パッケージ不明",
        "badge.mutation_ready": "Mutation 準備完了",
        "badge.mutation_preview": "Mutation プレビュー",
        "badge.mutation_na": "Mutation なし",
        "section.counts": "件数",
        "section.runtime_boundary": "ランタイム境界",
        "section.runtime_config": "ランタイム設定",
        "section.ui_boundary": "UI境界",
        "section.auth_boundary": "認証境界",
        "section.identity_boundary": "本人性境界",
        "section.mutation_readiness": "Mutation 準備状況",
        "section.ai_index_snapshot": "AIインデックススナップショット",
        "section.runtime_records": "ランタイム記録",
        "section.summary_jobs": "要約ジョブ",
        "section.triage": "トリアージ",
        "section.recovery_contract": "回復契約",
        "section.review_action": "レビュー操作",
        "section.action_result": "現在の結果",
        "section.metrics": "集計詳細",
        "sort.runtime.latest": "新しい順",
        "sort.runtime.mutation": "Mutation 準備状況",
        "sort.runtime.auth": "認証準備状況",
        "sort.runtime.kind": "種別",
        "sort.review.attention": "要対応優先",
        "sort.review.parity": "CLI drift 優先",
        "sort.review.latest": "新しい順",
        "sort.review.reviewer": "レビュアー",
        "sort.summary.latest": "新しい順",
        "sort.summary.mutation": "Mutation 準備状況",
        "sort.summary.review": "要対応優先",
        "sort.summary.title": "タイトル",
        "filter.runtime.preview_only": "ランタイム Mutation プレビュー",
        "filter.runtime.advisory_only": "ランタイム認証注意",
        "filter.runtime.boundary_aligned": "ランタイム本人性整合",
        "filter.runtime.retrieval_plan": "ランタイム検索計画",
        "filter.runtime.response_id": "ランタイム応答あり",
        "filter.summary.preview_only": "要約 Mutation プレビュー",
        "filter.summary.advisory_only": "要約注意",
        "filter.summary.package_context_available": "要約パッケージ準備完了",
        "filter.summary.boundary_aligned": "要約本人性整合",
        "filter.summary.response_id": "要約応答あり",
        "filter.review.review_requested": "レビュー依頼あり",
        "filter.review.ready": "レビュー可能",
        "filter.review.advisory_only": "レビュー注意",
        "filter.review.advisory": "レビュー注意",
        "filter.review.drift_detected": "CLI差分あり",
        "filter.review.aligned": "CLI整合",
        "filter.review.boundary_aligned": "本人性整合",
        "filter.review.ui_auth_not_enabled": "認証境界警告",
        "filter.review.reviewer_identity_declared_only": "申告のみの本人性",
        "filter.review.package_context_available": "パッケージ準備完了",
        "filter.review.no_context_records": "パッケージ要確認",
        "detail.resource.runtime-records": "Runtime",
        "detail.resource.review-queue": "Review",
        "detail.resource.summary-jobs": "Summary",
        "detail.resource.runtime-config": "ランタイム設定",
        "detail.resource.events": "Event",
        "detail.resource.contexts": "Context",
        "detail.resource.artifacts": "Artifact",
        "detail.resource.decisions": "Decision",
        "detail.resource.audit": "Audit",
        "detail.resource.lifecycle": "Lifecycle",
        "detail.resource.boundary": "Boundary",
        "detail.resource.rde": "RDE",
        "overview.authorization_warnings": "認可警告",
        "overview.missing_identity": "本人性不足",
        "overview.provider_response": "プロバイダ応答",
        "overview.session_label_required": "セッションラベル必須",
        "overview.warning_priority": "警告優先度",
        "exact": {
            "Overview": "概要",
            "Events": "イベント",
            "Contexts": "コンテキスト",
            "Artifacts": "成果物",
            "Decisions": "判断",
            "Boundary": "境界",
            "Audit": "監査",
            "Lifecycle": "ライフサイクル",
            "Runtime Records": "ランタイム記録",
            "Review Queue": "レビューキュー",
            "Summary Jobs": "要約ジョブ",
            "UI Boundary": "UI境界",
            "Runtime Config": "ランタイム設定",
            "Package Review": "パッケージレビュー",
            "Graph Summary": "グラフ要約",
            "AI Index Status": "AIインデックス状態",
            "AI Index Vector": "AIインデックスベクター",
            "AI Index Graph Nodes": "AIインデックスグラフノード",
            "AI Index Graph Edges": "AIインデックスグラフエッジ",
            "Counts": "件数",
            "Runtime Boundary": "ランタイム境界",
            "Auth Boundary": "認証境界",
            "Identity Boundary": "本人性境界",
            "Mutation Readiness": "Mutation 準備状況",
            "Triage": "トリアージ",
            "Ready": "準備完了",
            "Resolved": "解決済み",
            "Advisory": "助言のみ",
            "Package Ready": "パッケージ準備完了",
            "Package Advisory": "パッケージ要確認",
            "Package Unknown": "パッケージ不明",
            "Auth aligned": "認証整合",
            "Auth advisory": "認証注意",
            "Auth n/a": "認証なし",
            "Identity aligned": "本人性整合",
            "Identity advisory": "本人性注意",
            "Identity n/a": "本人性なし",
            "Mutation ready": "Mutation 準備完了",
            "Mutation preview": "Mutation プレビュー",
            "Mutation n/a": "Mutation なし",
            "CLI aligned": "CLI整合",
            "CLI drift": "CLI差分あり",
            "Review Requested": "レビュー依頼あり",
            "Review Ready": "レビュー可能",
            "Review Advisory": "レビュー注意",
            "Auth Boundary Warnings": "認証境界警告",
            "Declared Identity Only": "申告のみの本人性",
            "Runtime Mutation Preview": "ランタイム Mutation プレビュー",
            "Runtime Auth Advisory": "ランタイム認証注意",
            "Runtime Identity Aligned": "ランタイム本人性整合",
            "Runtime Retrieval Plans": "ランタイム検索計画",
            "Runtime Provider Response": "ランタイム応答あり",
            "Summary Mutation Preview": "要約 Mutation プレビュー",
            "Summary Advisory": "要約注意",
            "Summary Package Ready": "要約パッケージ準備完了",
            "Summary Identity Aligned": "要約本人性整合",
            "Summary Provider Response": "要約応答あり",
            "Latest first": "新しい順",
            "Mutation readiness": "Mutation 準備状況",
            "Auth readiness": "認証準備状況",
            "Kind": "種別",
            "Needs attention first": "要対応優先",
            "CLI drift first": "CLI差分優先",
            "Reviewer": "レビュアー",
            "Session": "セッション",
            "Note": "ノート",
            "Title": "タイトル",
            "JSON": "JSON",
            "Reset Filter": "フィルターをリセット",
            "Clear Slice": "スライスを解除",
            "Local Review Mutation": "ローカル Review Mutation",
            "Summary Review Mutation": "Summary Review Mutation",
            "Detail": "詳細",
            "Blocked Route Preview": "拒否ルートプレビュー",
            "Review Action Result": "レビュー操作結果",
            "Action Preview": "操作プレビュー",
            "Navigation": "ナビゲーション",
            "Runtime Preview": "ランタイムプレビュー",
            "Retrieval Handoff": "検索引き継ぎ",
            "Package Handoff Preview": "パッケージ引き継ぎプレビュー",
            "Invocation Plan": "呼び出し計画",
            "Provider Response": "プロバイダ応答",
            "Review Package Readiness": "レビュー用パッケージ準備状況",
            "Related Links": "関連リンク",
            "Auth Readiness": "認証準備状況",
            "Review Capability": "レビュー可否",
            "Mutation Enablement": "Mutation 有効化状況",
            "CLI Parity": "CLI整合",
            "Identity Assurance": "本人性保証",
            "Review Timeline": "レビュー履歴",
            "Back to current list": "現在の一覧へ戻る",
            "Back to previous detail": "前の詳細へ戻る",
            "Open review": "レビューを開く",
            "No matching runtime records for current filter.": "現在のフィルターに一致する runtime record はありません。",
            "No matching review rows for current filter.": "現在のフィルターに一致する review row はありません。",
            "No matching summary jobs for current filter.": "現在のフィルターに一致する summary job はありません。",
            "Status": "状態",
            "Expected actions": "想定アクション",
            "Missing preview commands": "不足している preview command",
            "Missing queue commands": "不足している queue command",
            "Vector entries": "ベクター件数",
            "Graph nodes": "グラフノード数",
            "Graph edges": "グラフエッジ数",
            "Needs-review records": "要レビュー件数",
            "Warning priority": "警告優先度",
            "Source refs total": "Source refs 合計",
            "Warning counts": "Warning 件数",
            "Status counts": "状態件数",
            "Review capability counts": "Review capability 件数",
            "Package readiness counts": "Package readiness 件数",
            "Identity assurance counts": "Identity assurance 件数",
            "Reviewer kind counts": "Reviewer kind 件数",
            "Runtime provider counts": "Runtime provider 件数",
            "Mutation readiness counts": "Mutation readiness 件数",
            "Mutation operational counts": "Mutation operational 件数",
            "Auth readiness counts": "Auth readiness 件数",
            "Provider finish reasons": "Provider finish reason 件数",
            "Provider statuses": "Provider status 件数",
            "Runtime kinds": "Runtime kind 件数",
            "Auth review capability counts": "Auth review capability 件数",
            "Declared identity only": "申告のみの本人性",
            "Session label required": "セッションラベル必須",
            "Authorization warnings": "認可警告",
            "Missing identity": "本人性不足",
            "Provider response": "プロバイダ応答",
            "Action": "操作",
            "Event": "イベント",
            "Error code": "エラーコード",
            "Identity assurance": "本人性保証",
            "Identity assurance message": "本人性保証メッセージ",
            "CLI equivalent": "CLI相当",
            "Failure summary": "失敗要約",
            "Warnings": "警告",
            "Recovery path": "回復パス",
            "Rollback status": "ロールバック状態",
            "Transaction status": "トランザクション状態",
            "Durable mutation on failure": "失敗時の durable mutation",
            "Possible errors": "想定エラー",
            "Recovery commands": "回復コマンド",
            "Follow-up commands": "後続コマンド",
            "Review capability": "レビュー可否",
            "Blockers": "阻害要因",
            "Next steps": "次のステップ",
            "Enablement ready": "有効化準備完了",
            "Enablement checks": "有効化チェック",
            "Operational readiness": "運用準備状況",
            "Operational summary": "運用要約",
            "Remaining prerequisites": "残り前提条件",
            "Blocker sources": "阻害要因ソース",
            "Checks": "チェック",
            "Remaining checks": "残りチェック",
            "Reviewer fields": "レビュアー項目",
            "Reviewer kinds": "レビュアー種別",
            "Reviewer label pattern": "レビュアーラベルパターン",
            "Reviewer label examples": "レビュアーラベル例",
            "Session label pattern": "セッションラベルパターン",
            "Write route": "書き込みルート",
            "Write actions": "書き込み操作",
            "Write success status": "書き込み成功ステータス",
            "Write blocked status": "書き込み拒否ステータス",
            "Identity proof status": "本人確認ステータス",
            "Identity proof fields": "本人確認項目",
            "Eligible contexts": "対象コンテキスト",
            "Suggested commands": "推奨コマンド",
            "Package review status": "パッケージレビュー状態",
            "Package warnings": "パッケージ警告",
            "Manifest refs": "マニフェスト参照",
            "Provider": "プロバイダ",
            "Model": "モデル",
            "Operation": "操作種別",
            "Invocation ready": "呼び出し準備完了",
            "Would use network": "ネットワーク使用予定",
            "Network allowed by contract": "契約上のネットワーク許可",
            "Blocking reasons": "阻害理由",
            "Request preview": "リクエストプレビュー",
            "Downstream commands": "下流コマンド",
            "Query": "クエリ",
            "Referenced IDs": "参照ID",
            "Notes": "ノート",
            "CLI": "CLI",
            "Response ID": "応答ID",
            "Finish reason": "終了理由",
            "Provider status": "プロバイダ状態",
            "Usage input tokens": "入力トークン数",
            "Usage output tokens": "出力トークン数",
            "Usage total tokens": "総トークン数",
            "Metadata fields": "メタデータ項目数",
            "Top-level response keys": "トップレベル応答キー数",
            "Response keys": "応答キー",
            "Approve": "承認",
            "Reject": "却下",
            "Request Changes": "修正依頼",
            "POST enabled": "POST有効",
            "Preview blocked route": "拒否ルートをプレビュー",
            "Read-only": "読み取り専用",
            "External model API": "外部 model API",
            "GraphRAG runtime": "GraphRAG runtime",
            "Vector DB": "Vector DB",
            "Graph DB": "Graph DB",
            "Bind scope": "bind scope",
            "Mutation enabled": "mutation 有効",
            "Mutation capability flag": "mutation capability flag",
            "Auth mode": "認証モード",
            "Authorization mode": "認可モード",
            "Session gating": "セッション制御",
            "Write request fields": "書き込みリクエスト項目",
            "Source": "ソース",
            "Provider kind": "プロバイダ種別",
            "Provider name": "プロバイダ名",
            "Allow network": "ネットワーク許可",
            "Allow external context": "外部コンテキスト許可",
            "Auth blockers": "認証阻害要因",
            "Auth next steps": "認証の次ステップ",
            "Runtime records": "ランタイム記録",
            "Summary jobs": "要約ジョブ",
            "Shared machine safe": "共有端末安全",
            "Missing identity rows": "本人性不足行数",
            "Declared-only rows": "申告のみ行数",
            "Session-label-missing rows": "セッションラベル不足行数",
            "Identity blockers": "本人性阻害要因",
            "Identity next steps": "本人性の次ステップ",
            "Ready rows": "準備完了行数",
            "Advisory rows": "注意行数",
            "Blocker details": "阻害要因詳細",
            "Effective reviewer fields": "有効レビュアー項目",
            "Accepted reviewer kinds": "許可レビュアー種別",
            "Audit ID": "監査ID",
            "Decision event": "判断イベント",
            "Source counts": "ソース件数",
            "Skipped records": "スキップ記録",
            "UI auth boundary is not enabled; reviewer identity remains advisory only.": "UI の認証境界が未有効のため、レビュアー本人性は助言扱いのままです。",
            "UI auth boundary is loopback-local, but reviewer authorization remains advisory only.": "UI 認証境界は loopback-local ですが、レビュアー認可は助言扱いのままです。",
            "UI auth/authz metadata is configured for preview, but GUI mutation remains disabled.": "UI の認証/認可メタデータはプレビュー用に設定されていますが、GUI mutation は無効のままです。",
            "Recorded reviewer identity metadata is aligned with the current preview auth boundary.": "記録済みのレビュアー本人性メタデータは現在のプレビュー認証境界と整合しています。",
            "Some reviewer identity metadata is present, but boundary alignment remains incomplete.": "レビュアー本人性メタデータは一部ありますが、境界整合はまだ不完全です。",
            "Reviewer identity assurance is not yet available in the current derived queue view.": "現在の派生 queue view では、レビュアー本人性保証をまだ利用できません。",
            "Current review metadata is aligned with the preview auth boundary, while GUI mutation remains disabled.": "現在のレビュー用メタデータはプレビュー認証境界と整合していますが、GUI mutation は無効のままです。",
            "Current review metadata remains advisory only until auth, authorization, and reviewer identity boundaries are explicit.": "認証・認可・レビュアー本人性の境界が明示されるまで、現在のレビュー用メタデータは助言扱いのままです。",
            "Some reviewer identity metadata is present, but auth-boundary alignment remains incomplete.": "レビュアー本人性メタデータは一部ありますが、認証境界との整合はまだ不完全です。",
            "Auth-boundary readiness is not yet available in the current derived detail view.": "現在の派生 detail view では、認証境界の準備状況をまだ利用できません。",
            "Reviewer identity is self-declared only; UI auth is not enforcing reviewer identity.": "レビュアー本人性は自己申告のみで、UI 認証はレビュアー本人性を強制していません。",
            "Reviewer identity carries local session metadata, but UI auth/authz is not enabled.": "レビュアー本人性にはローカル session メタデータがありますが、UI の認証/認可は未有効です。",
            "Reviewer identity metadata is aligned with the current UI auth boundary.": "レビュアー本人性メタデータは現在の UI 認証境界と整合しています。",
            "No context-linked records available for package/export preview.": "package/export preview に利用できる context 連携レコードはありません。",
            "GUI mutation remains disabled for this session; use the CLI review path instead.": "この session では GUI mutation は無効のままです。代わりに CLI review path を使ってください。",
            "Reviewer label is missing, so the UI cannot attribute the review action.": "reviewer label がないため、UI はレビュー操作の実行者を特定できません。",
            "Reviewer label must start with a lowercase letter or digit and use only lowercase letters, digits, dot, underscore, or hyphen.": "reviewer label は小文字の英字または数字で始まり、小文字英字・数字・ドット・アンダースコア・ハイフンのみを使う必要があります。",
            "Session label is required for the current session-gated local mutation boundary.": "現在の session-gated local mutation boundary では session label が必須です。",
            "Session label must start with a lowercase letter or digit and use only lowercase letters, digits, dot, underscore, or hyphen.": "session label は小文字の英字または数字で始まり、小文字英字・数字・ドット・アンダースコア・ハイフンのみを使う必要があります。",
            "Requested route and submitted UI intent differ, so the action was rejected before mutation.": "要求された route と送信された UI intent が一致しないため、mutation 前に操作は拒否されました。",
            "Reviewer kind is not one of the supported local reviewer identity kinds.": "reviewer kind が、サポート対象の local reviewer identity kind に含まれていません。",
            "Reviewer identity or session boundary is not aligned, so the action stays blocked.": "レビュアー本人性または session 境界が整合していないため、操作は blocked のままです。",
            "The target review event is no longer available from the current Chronicle state.": "対象 review event は現在の Chronicle state ではもう利用できません。",
            "The review target is no longer pending; inspect the resolved queue before retrying.": "review target はもう pending ではありません。再試行前に解決済み queue を確認してください。",
            "The request body could not be parsed as JSON, so no mutation path was attempted.": "request body を JSON として解釈できなかったため、mutation path は試行されませんでした。",
            "Audit insertion failed before the review decision could be reported as applied.": "レビュー判断を適用済みと報告する前に audit insertion が失敗しました。",
            "Audit insertion succeeded, but the Chronicle primary-record append failed, so treat the route as fail-closed.": "audit insertion は成功しましたが Chronicle primary-record append が失敗したため、この route は fail-closed として扱ってください。",
        },
        "prefix": {
            "Open review target ": "レビュー対象を開く ",
            "Open event ": "イベントを開く ",
            "Open context ": "コンテキストを開く ",
            "Root: ": "ルート: ",
            "Chronicle ID: ": "Chronicle ID: ",
            "Status: ": "状態: ",
            "Route: ": "ルート: ",
            "Action: ": "操作: ",
            "Event: ": "イベント: ",
            "Error code: ": "エラーコード: ",
            "Identity assurance: ": "本人性保証: ",
            "Identity assurance message: ": "本人性保証メッセージ: ",
            "CLI equivalent: ": "CLI相当: ",
            "Failure summary: ": "失敗要約: ",
            "Warnings: ": "警告: ",
            "Recovery path: ": "回復パス: ",
            "Rollback status: ": "ロールバック状態: ",
            "Transaction status: ": "トランザクション状態: ",
            "Durable mutation on failure: ": "failure 時 durable mutation: ",
            "Possible errors: ": "想定エラー: ",
            "Recovery commands: ": "回復コマンド: ",
            "Follow-up commands: ": "後続コマンド: ",
            "Read-only: ": "読み取り専用: ",
            "External model API: ": "external model API: ",
            "GraphRAG runtime: ": "GraphRAG runtime: ",
            "Vector DB: ": "vector DB: ",
            "Graph DB: ": "graph DB: ",
            "Bind scope: ": "bind scope: ",
            "Mutation enabled: ": "mutation 有効: ",
            "Mutation capability flag: ": "mutation capability flag: ",
            "Auth mode: ": "認証モード: ",
            "Authorization mode: ": "認可モード: ",
            "Session gating: ": "セッション制御: ",
            "Mutation readiness: ": "mutation 準備状況: ",
            "Write route: ": "書き込みルート: ",
            "Write actions: ": "書き込み操作: ",
            "Write request fields: ": "書き込みリクエスト項目: ",
            "Write success status: ": "書き込み成功ステータス: ",
            "Write blocked status: ": "書き込み拒否ステータス: ",
            "Identity proof status: ": "本人確認ステータス: ",
            "Identity proof fields: ": "本人確認項目: ",
            "Source: ": "ソース: ",
            "Provider kind: ": "プロバイダ種別: ",
            "Provider name: ": "プロバイダ名: ",
            "Model: ": "model: ",
            "Allow network: ": "ネットワーク許可: ",
            "Allow external context: ": "外部コンテキスト許可: ",
            "Auth blockers: ": "認証阻害要因: ",
            "Auth next steps: ": "認証の次ステップ: ",
            "slice:": "slice:",
            "Active view: ": "アクティブ view: ",
            "view=": "view=",
            "trail=": "trail=",
            "Response ": "応答 ",
            "More ": "詳細 ",
        },
    },
    "en": {
        "label.language": "Language",
        "locale.ja": "日本語",
        "locale.en": "English",
        "locale.zh-CN": "简体中文",
        "shell.title": "Chronicle Stack Local UI",
        "shell.root": "Root",
        "shell.warning_title": "Read-only foreground local UI.",
        "shell.warning_body": "This UI reads local Chronicle files and does not write records.",
        "shell.boundary_body": "No daemon, no autostart, no external model API, no GraphRAG runtime, no vector DB, no graph DB. UI visibility is not correctness proof.",
        "shell.loading_overview": "Loading overview...",
        "shell.select_json": "Select JSON from a table row to inspect one record.",
        "placeholder.runtime_filter": "Filter runtime records...",
        "placeholder.review_filter": "Filter review queue...",
        "placeholder.summary_filter": "Filter summary jobs...",
        "placeholder.review_note": "optional review note",
        "placeholder.reviewer": "alice",
        "placeholder.session": "desk-session-1",
        "button.copy_cli": "Copy CLI",
        "button.copy_recovery_cli": "Copy Recovery CLI",
        "button.preview_blocked_route": "Preview Blocked Route",
        "button.apply": "Apply",
        "button.actions": "Actions",
        "button.reset_filter": "Reset Filter",
        "button.clear_slice": "Clear Slice",
        "button.open_package_review": "Open Package Review",
        "button.open_runtime_records": "Open Runtime Records",
        "button.open_review_queue": "Open Review Queue",
        "button.open_summary_jobs": "Open Summary Jobs",
        "button.open_runtime_config": "Open Runtime Config",
        "button.open_review": "Open review",
        "button.more_details": "More details",
        "button.back_current_list": "Back to current list",
        "button.back_previous_detail": "Back to previous detail",
        "status.loading_blocked_preview": "Loading blocked-route preview...",
        "status.applying_review_action": "Applying review action...",
        "status.blocked_route_preview": "Blocked Route Preview",
        "status.review_action_result": "Review Action Result",
        "status.not_found": "Not found.",
        "status.no_message": "No message returned.",
        "status.copied_recovery_cli": "Copied recovery CLI: ",
        "status.copy_failed_command": "Copy failed; command: ",
        "status.active_view": "Active view",
        "status.sort": "Sort",
        "status.more": "More",
        "status.detail": "Detail",
        "status.view": "view",
        "status.trail": "trail",
        "label.record_json": "Record JSON",
        "label.response_json": "Response JSON",
        "label.table_detail": "Detail",
        "label.table_event": "Event",
        "label.table_kind": "Kind",
        "label.table_auth": "Auth",
        "label.table_preview": "Preview",
        "label.table_review_route": "Review Route",
        "label.table_target": "Target",
        "label.table_status": "Status",
        "label.table_warnings": "Warnings",
        "label.table_latest_reviewer": "Latest Reviewer",
        "label.table_summary_job": "Summary Job",
        "label.table_identity": "Identity",
        "label.table_runtime": "Runtime",
        "notice.action_preview": "Action Preview",
        "notice.navigation": "Navigation",
        "notice.runtime_preview": "Runtime Preview",
        "notice.retrieval_handoff": "Retrieval Handoff",
        "notice.package_handoff_preview": "Package Handoff Preview",
        "notice.invocation_plan": "Invocation Plan",
        "notice.provider_response": "Provider Response",
        "notice.review_package_readiness": "Review Package Readiness",
        "notice.related_links": "Related Links",
        "notice.auth_readiness": "Auth Readiness",
        "notice.review_capability": "Review Capability",
        "notice.mutation_enablement": "Mutation Enablement",
        "notice.cli_parity": "CLI Parity",
        "notice.identity_assurance": "Identity Assurance",
        "notice.review_timeline": "Review Timeline",
        "notice.mutation_enabled_detail": "Local mutation is enabled for this detail view. Every action still requires explicit reviewer context and writes audit-backed review history.",
        "notice.mutation_enabled_runtime_records": "Local mutation is enabled for this runtime-record list view. Each action still requires explicit reviewer context and writes audit-backed review history.",
        "notice.mutation_enabled_review_queue": "Local mutation is enabled for this list view. Each action still requires explicit reviewer context and writes audit-backed review history.",
        "notice.mutation_enabled_summary_jobs": "Local mutation is enabled for summary-backed review targets. Actions still require explicit reviewer context and write audit-backed review history.",
        "notice.blocked_route_preview_runtime_records": "Runtime-record blocked-route preview stays read-only and returns the CLI fallback contract.",
        "notice.blocked_route_preview_review_queue": "Review queue blocked-route preview stays read-only and returns the CLI fallback contract.",
        "notice.blocked_route_preview_summary_jobs": "Summary jobs blocked-route preview stays read-only and returns the CLI fallback contract.",
        "notice.blocked_route_preview_detail": "Blocked route preview stays read-only and returns the CLI fallback contract.",
        "badge.auth_aligned": "Auth aligned",
        "badge.auth_advisory": "Auth advisory",
        "badge.auth_na": "Auth n/a",
        "badge.identity_aligned": "Identity aligned",
        "badge.identity_advisory": "Identity advisory",
        "badge.identity_na": "Identity n/a",
        "badge.ready": "Ready",
        "badge.resolved": "Resolved",
        "badge.advisory": "Advisory",
        "badge.package_ready": "Package Ready",
        "badge.package_advisory": "Package Advisory",
        "badge.package_unknown": "Package Unknown",
        "badge.mutation_ready": "Mutation ready",
        "badge.mutation_preview": "Mutation preview",
        "badge.mutation_na": "Mutation n/a",
        "section.counts": "Counts",
        "section.runtime_boundary": "Runtime Boundary",
        "section.runtime_config": "Runtime Config",
        "section.ui_boundary": "UI Boundary",
        "section.auth_boundary": "Auth Boundary",
        "section.identity_boundary": "Identity Boundary",
        "section.mutation_readiness": "Mutation Readiness",
        "section.ai_index_snapshot": "AI Index Snapshot",
        "section.runtime_records": "Runtime Records",
        "section.summary_jobs": "Summary Jobs",
        "section.triage": "Triage",
        "section.recovery_contract": "Recovery Contract",
        "section.review_action": "Review Action",
        "section.action_result": "Current Result",
        "section.metrics": "Metrics",
        "sort.runtime.latest": "Latest first",
        "sort.runtime.mutation": "Mutation readiness",
        "sort.runtime.auth": "Auth readiness",
        "sort.runtime.kind": "Kind",
        "sort.review.attention": "Needs attention first",
        "sort.review.parity": "CLI drift first",
        "sort.review.latest": "Latest first",
        "sort.review.reviewer": "Reviewer",
        "sort.summary.latest": "Latest first",
        "sort.summary.mutation": "Mutation readiness",
        "sort.summary.review": "Needs attention first",
        "sort.summary.title": "Title",
        "filter.runtime.preview_only": "Runtime mutation preview",
        "filter.runtime.advisory_only": "Runtime auth advisory",
        "filter.runtime.boundary_aligned": "Runtime identity aligned",
        "filter.runtime.retrieval_plan": "Runtime retrieval plans",
        "filter.runtime.response_id": "Runtime provider response",
        "filter.summary.preview_only": "Summary mutation preview",
        "filter.summary.advisory_only": "Summary advisory",
        "filter.summary.package_context_available": "Summary package ready",
        "filter.summary.boundary_aligned": "Summary identity aligned",
        "filter.summary.response_id": "Summary provider response",
        "filter.review.review_requested": "Review requested",
        "filter.review.ready": "Review ready",
        "filter.review.advisory_only": "Review advisory",
        "filter.review.advisory": "Review advisory",
        "filter.review.drift_detected": "CLI drift",
        "filter.review.aligned": "CLI aligned",
        "filter.review.boundary_aligned": "Identity aligned",
        "filter.review.ui_auth_not_enabled": "Auth boundary warnings",
        "filter.review.reviewer_identity_declared_only": "Declared identity only",
        "filter.review.package_context_available": "Package ready",
        "filter.review.no_context_records": "Package advisory",
        "detail.resource.runtime-records": "Runtime",
        "detail.resource.review-queue": "Review",
        "detail.resource.summary-jobs": "Summary",
        "detail.resource.runtime-config": "Runtime Config",
        "detail.resource.events": "Event",
        "detail.resource.contexts": "Context",
        "detail.resource.artifacts": "Artifact",
        "detail.resource.decisions": "Decision",
        "detail.resource.audit": "Audit",
        "detail.resource.lifecycle": "Lifecycle",
        "detail.resource.boundary": "Boundary",
        "detail.resource.rde": "RDE",
        "overview.authorization_warnings": "Authorization warnings",
        "overview.missing_identity": "Missing identity",
        "overview.provider_response": "Provider response",
        "overview.session_label_required": "Session label required",
        "overview.warning_priority": "Warning priority",
    },
    "zh-CN": {
        "label.language": "显示语言",
        "locale.ja": "日本語",
        "locale.en": "English",
        "locale.zh-CN": "简体中文",
        "shell.title": "Chronicle Stack 本地界面",
        "shell.root": "根目录",
        "shell.warning_title": "这是只读的前台本地界面。",
        "shell.warning_body": "该界面读取本地 Chronicle 文件，但不会写入记录。",
        "shell.boundary_body": "无 daemon、无自动启动、无外部 model API、无 GraphRAG runtime、无 vector DB、无 graph DB。界面可见性不等于 correctness proof。",
        "shell.loading_overview": "正在加载概览...",
        "shell.select_json": "从表格行选择 JSON 以查看单条记录。",
        "placeholder.runtime_filter": "筛选运行时记录...",
        "placeholder.review_filter": "筛选审查队列...",
        "placeholder.summary_filter": "筛选摘要任务...",
        "placeholder.review_note": "可选审查备注",
        "placeholder.reviewer": "alice",
        "placeholder.session": "desk-session-1",
        "button.copy_cli": "复制 CLI",
        "button.copy_recovery_cli": "复制恢复 CLI",
        "button.preview_blocked_route": "预览阻止路由",
        "button.apply": "应用",
        "button.actions": "操作",
        "button.reset_filter": "重置筛选",
        "button.clear_slice": "清除切片",
        "button.open_package_review": "打开包审查",
        "button.open_runtime_records": "打开运行时记录",
        "button.open_review_queue": "打开审查队列",
        "button.open_summary_jobs": "打开摘要任务",
        "button.open_runtime_config": "打开运行时配置",
        "button.open_review": "打开审查",
        "button.more_details": "更多细节",
        "button.back_current_list": "返回当前列表",
        "button.back_previous_detail": "返回上一条详情",
        "status.loading_blocked_preview": "正在加载阻止路由预览…",
        "status.applying_review_action": "正在应用审查操作…",
        "status.blocked_route_preview": "阻止路由预览",
        "status.review_action_result": "审查操作结果",
        "status.not_found": "未找到。",
        "status.no_message": "未返回消息。",
        "status.copied_recovery_cli": "已复制恢复 CLI: ",
        "status.copy_failed_command": "复制失败；命令: ",
        "status.active_view": "当前视图",
        "status.sort": "排序",
        "status.more": "更多",
        "status.detail": "详情",
        "status.view": "view",
        "status.trail": "trail",
        "label.record_json": "记录 JSON",
        "label.response_json": "响应 JSON",
        "label.table_detail": "详情",
        "label.table_event": "事件",
        "label.table_kind": "类型",
        "label.table_auth": "认证",
        "label.table_preview": "预览",
        "label.table_review_route": "审查路径",
        "label.table_target": "目标",
        "label.table_status": "状态",
        "label.table_warnings": "警告",
        "label.table_latest_reviewer": "最新审阅者",
        "label.table_summary_job": "摘要任务",
        "label.table_identity": "身份",
        "label.table_runtime": "运行时",
        "notice.action_preview": "操作预览",
        "notice.navigation": "导航",
        "notice.runtime_preview": "运行时预览",
        "notice.retrieval_handoff": "检索交接",
        "notice.package_handoff_preview": "包交接预览",
        "notice.invocation_plan": "调用计划",
        "notice.provider_response": "提供方响应",
        "notice.review_package_readiness": "审查包就绪度",
        "notice.related_links": "相关链接",
        "notice.auth_readiness": "认证就绪度",
        "notice.review_capability": "审查能力",
        "notice.mutation_enablement": "Mutation 启用状态",
        "notice.cli_parity": "CLI 一致性",
        "notice.identity_assurance": "身份保证",
        "notice.review_timeline": "审查时间线",
        "notice.mutation_enabled_detail": "此详情视图已启用本地 mutation。每个操作仍需要显式的 reviewer context，并会写入带审计支撑的审查历史。",
        "notice.mutation_enabled_runtime_records": "此运行时记录列表视图已启用本地 mutation。每个操作仍需要显式的 reviewer context，并会写入带审计支撑的审查历史。",
        "notice.mutation_enabled_review_queue": "此列表视图已启用本地 mutation。每个操作仍需要显式的 reviewer context，并会写入带审计支撑的审查历史。",
        "notice.mutation_enabled_summary_jobs": "此基于摘要的审查目标已启用本地 mutation。操作仍需要显式的 reviewer context，并会写入带审计支撑的审查历史。",
        "notice.blocked_route_preview_runtime_records": "运行时记录的 blocked-route preview 保持只读，并返回 CLI fallback contract。",
        "notice.blocked_route_preview_review_queue": "审查队列的 blocked-route preview 保持只读，并返回 CLI fallback contract。",
        "notice.blocked_route_preview_summary_jobs": "摘要任务的 blocked-route preview 保持只读，并返回 CLI fallback contract。",
        "notice.blocked_route_preview_detail": "blocked-route preview 保持只读，并返回 CLI fallback contract。",
        "badge.auth_aligned": "认证一致",
        "badge.auth_advisory": "认证提示",
        "badge.auth_na": "无认证",
        "badge.identity_aligned": "身份一致",
        "badge.identity_advisory": "身份提示",
        "badge.identity_na": "无身份信息",
        "badge.ready": "就绪",
        "badge.resolved": "已解决",
        "badge.advisory": "仅提示",
        "badge.package_ready": "包已就绪",
        "badge.package_advisory": "包需关注",
        "badge.package_unknown": "包状态未知",
        "badge.mutation_ready": "Mutation 已就绪",
        "badge.mutation_preview": "Mutation 预览",
        "badge.mutation_na": "无 Mutation",
        "section.counts": "计数",
        "section.runtime_boundary": "运行时边界",
        "section.runtime_config": "运行时配置",
        "section.ui_boundary": "UI 边界",
        "section.auth_boundary": "认证边界",
        "section.identity_boundary": "身份边界",
        "section.mutation_readiness": "Mutation 就绪度",
        "section.ai_index_snapshot": "AI 索引快照",
        "section.runtime_records": "运行时记录",
        "section.summary_jobs": "摘要任务",
        "section.triage": "分诊",
        "section.recovery_contract": "恢复契约",
        "section.review_action": "审查操作",
        "section.action_result": "当前结果",
        "section.metrics": "统计详情",
        "sort.runtime.latest": "最新优先",
        "sort.runtime.mutation": "Mutation 就绪度",
        "sort.runtime.auth": "认证就绪度",
        "sort.runtime.kind": "类型",
        "sort.review.attention": "优先显示需关注项",
        "sort.review.parity": "优先显示 CLI 差异",
        "sort.review.latest": "最新优先",
        "sort.review.reviewer": "审阅者",
        "sort.summary.latest": "最新优先",
        "sort.summary.mutation": "Mutation 就绪度",
        "sort.summary.review": "优先显示需关注项",
        "sort.summary.title": "标题",
        "filter.runtime.preview_only": "运行时 Mutation 预览",
        "filter.runtime.advisory_only": "运行时认证提示",
        "filter.runtime.boundary_aligned": "运行时身份一致",
        "filter.runtime.retrieval_plan": "运行时检索计划",
        "filter.runtime.response_id": "运行时提供方响应",
        "filter.summary.preview_only": "摘要 Mutation 预览",
        "filter.summary.advisory_only": "摘要提示",
        "filter.summary.package_context_available": "摘要包已就绪",
        "filter.summary.boundary_aligned": "摘要身份一致",
        "filter.summary.response_id": "摘要提供方响应",
        "filter.review.review_requested": "已请求审查",
        "filter.review.ready": "可立即审查",
        "filter.review.advisory_only": "审查提示",
        "filter.review.advisory": "审查提示",
        "filter.review.drift_detected": "CLI 差异",
        "filter.review.aligned": "CLI 一致",
        "filter.review.boundary_aligned": "身份一致",
        "filter.review.ui_auth_not_enabled": "认证边界警告",
        "filter.review.reviewer_identity_declared_only": "仅声明身份",
        "filter.review.package_context_available": "包已就绪",
        "filter.review.no_context_records": "包需关注",
        "detail.resource.runtime-records": "运行时",
        "detail.resource.review-queue": "审查",
        "detail.resource.summary-jobs": "摘要",
        "detail.resource.runtime-config": "运行时配置",
        "detail.resource.events": "事件",
        "detail.resource.contexts": "上下文",
        "detail.resource.artifacts": "成果物",
        "detail.resource.decisions": "决策",
        "detail.resource.audit": "Audit",
        "detail.resource.lifecycle": "Lifecycle",
        "detail.resource.boundary": "Boundary",
        "detail.resource.rde": "RDE",
        "overview.authorization_warnings": "授权警告",
        "overview.missing_identity": "缺少身份",
        "overview.provider_response": "提供方响应",
        "overview.session_label_required": "需要会话标签",
        "overview.warning_priority": "警告优先级",
        "exact": {
            "Overview": "概览",
            "Events": "事件",
            "Contexts": "上下文",
            "Artifacts": "成果物",
            "Decisions": "决策",
            "Boundary": "边界",
            "Audit": "审计",
            "Lifecycle": "生命周期",
            "Counts": "计数",
            "Ready": "就绪",
            "Resolved": "已解决",
            "Advisory": "仅提示",
            "Latest first": "最新优先",
            "Needs attention first": "优先显示需关注项",
            "Reviewer": "审阅者",
            "Session": "会话",
            "Note": "备注",
            "Title": "标题",
            "JSON": "JSON",
            "Reset Filter": "重置筛选",
            "Clear Slice": "清除切片",
            "Detail": "详情",
            "Blocked Route Preview": "阻止路由预览",
            "Review Action Result": "审阅操作结果",
            "Navigation": "导航",
            "Runtime Preview": "运行时预览",
            "Retrieval Handoff": "检索交接",
            "Package Handoff Preview": "包交接预览",
            "Invocation Plan": "调用计划",
            "Provider Response": "提供方响应",
            "Review Package Readiness": "审查包就绪度",
            "Related Links": "相关链接",
            "Auth Readiness": "认证就绪度",
            "Review Capability": "审查能力",
            "Mutation Enablement": "Mutation 启用状态",
            "Back to current list": "返回当前列表",
            "Back to previous detail": "返回上一条详情",
            "Open review": "打开审查",
            "Action": "操作",
            "Event": "事件",
            "Error code": "错误代码",
            "Identity assurance": "身份保证",
            "Identity assurance message": "身份保证消息",
            "CLI equivalent": "CLI 等价命令",
            "Failure summary": "失败摘要",
            "Warnings": "警告",
            "Recovery path": "恢复路径",
            "Rollback status": "回滚状态",
            "Transaction status": "事务状态",
            "Durable mutation on failure": "失败时 durable mutation",
            "Possible errors": "可能错误",
            "Recovery commands": "恢复命令",
            "Follow-up commands": "后续命令",
            "Review capability": "审查能力",
            "Blockers": "阻塞项",
            "Next steps": "下一步",
            "Enablement ready": "启用就绪",
            "Enablement checks": "启用检查",
            "Operational readiness": "运行就绪度",
            "Operational summary": "运行摘要",
            "Remaining prerequisites": "剩余前提条件",
            "Blocker sources": "阻塞来源",
            "Checks": "检查项",
            "Remaining checks": "剩余检查项",
            "Reviewer fields": "审阅者字段",
            "Reviewer kinds": "审阅者类型",
            "Reviewer label pattern": "审阅者标签模式",
            "Reviewer label examples": "审阅者标签示例",
            "Session label pattern": "会话标签模式",
            "Write route": "写入路由",
            "Write actions": "写入操作",
            "Write success status": "写入成功状态",
            "Write blocked status": "写入阻止状态",
            "Identity proof status": "身份验证状态",
            "Identity proof fields": "身份验证字段",
            "Eligible contexts": "可用上下文",
            "Suggested commands": "建议命令",
            "Package review status": "包审查状态",
            "Package warnings": "包警告",
            "Manifest refs": "清单引用",
            "Provider": "提供方",
            "Model": "模型",
            "Operation": "操作",
            "Invocation ready": "调用就绪",
            "Would use network": "将使用网络",
            "Network allowed by contract": "契约允许网络",
            "Blocking reasons": "阻塞原因",
            "Request preview": "请求预览",
            "Downstream commands": "下游命令",
            "Query": "查询",
            "Referenced IDs": "引用 ID",
            "Notes": "备注",
            "CLI": "CLI",
            "Response ID": "响应 ID",
            "Finish reason": "结束原因",
            "Provider status": "提供方状态",
            "Usage input tokens": "输入 token 数",
            "Usage output tokens": "输出 token 数",
            "Usage total tokens": "总 token 数",
            "Metadata fields": "元数据字段数",
            "Top-level response keys": "顶层响应键数",
            "Response keys": "响应键",
            "Approve": "批准",
            "Reject": "拒绝",
            "Request Changes": "请求修改",
            "POST enabled": "POST 已启用",
            "Preview blocked route": "预览阻止路由",
            "Read-only": "只读",
            "External model API": "外部 model API",
            "GraphRAG runtime": "GraphRAG runtime",
            "Vector DB": "Vector DB",
            "Graph DB": "Graph DB",
            "Bind scope": "绑定范围",
            "Mutation enabled": "mutation 已启用",
            "Mutation capability flag": "mutation capability flag",
            "Auth mode": "认证模式",
            "Authorization mode": "授权模式",
            "Session gating": "会话门控",
            "Mutation readiness": "mutation 就绪度",
            "Write request fields": "写入请求字段",
            "Source": "来源",
            "Provider kind": "提供方类型",
            "Provider name": "提供方名称",
            "Allow network": "允许网络",
            "Allow external context": "允许外部上下文",
            "Auth blockers": "认证阻塞项",
            "Auth next steps": "认证下一步",
            "Runtime records": "运行时记录",
            "Summary jobs": "摘要任务",
            "Shared machine safe": "共享设备安全",
            "Missing identity rows": "缺少身份行数",
            "Declared-only rows": "仅声明身份行数",
            "Session-label-missing rows": "缺少会话标签行数",
            "Identity blockers": "身份阻塞项",
            "Identity next steps": "身份下一步",
            "Ready rows": "就绪行数",
            "Advisory rows": "提示行数",
            "Blocker details": "阻塞详情",
            "Effective reviewer fields": "有效审阅者字段",
            "Accepted reviewer kinds": "允许的审阅者类型",
            "Audit ID": "审计 ID",
            "Decision event": "决策事件",
            "Source counts": "来源计数",
            "Skipped records": "跳过记录",
            "UI auth boundary is not enabled; reviewer identity remains advisory only.": "UI 认证边界未启用，因此审阅者身份仍仅作为提示信息处理。",
            "UI auth boundary is loopback-local, but reviewer authorization remains advisory only.": "UI 认证边界为 loopback-local，但审阅者授权仍仅作为提示信息处理。",
            "UI auth/authz metadata is configured for preview, but GUI mutation remains disabled.": "UI 认证/授权元数据已为预览配置，但 GUI mutation 仍保持禁用。",
            "Recorded reviewer identity metadata is aligned with the current preview auth boundary.": "已记录的审阅者身份元数据与当前预览认证边界一致。",
            "Some reviewer identity metadata is present, but boundary alignment remains incomplete.": "已有部分审阅者身份元数据，但边界一致性仍不完整。",
            "Reviewer identity assurance is not yet available in the current derived queue view.": "当前派生 queue view 尚未提供审阅者身份保证。",
            "Current review metadata is aligned with the preview auth boundary, while GUI mutation remains disabled.": "当前审阅元数据与预览认证边界一致，但 GUI mutation 仍保持禁用。",
            "Current review metadata remains advisory only until auth, authorization, and reviewer identity boundaries are explicit.": "在认证、授权与审阅者身份边界明确之前，当前审阅元数据仍仅作为提示信息处理。",
            "Some reviewer identity metadata is present, but auth-boundary alignment remains incomplete.": "已有部分审阅者身份元数据，但与认证边界的一致性仍不完整。",
            "Auth-boundary readiness is not yet available in the current derived detail view.": "当前派生 detail view 尚未提供认证边界就绪度。",
            "Reviewer identity is self-declared only; UI auth is not enforcing reviewer identity.": "审阅者身份仅为自我声明；UI 认证未强制校验审阅者身份。",
            "Reviewer identity carries local session metadata, but UI auth/authz is not enabled.": "审阅者身份带有本地 session 元数据，但 UI 认证/授权尚未启用。",
            "Reviewer identity metadata is aligned with the current UI auth boundary.": "审阅者身份元数据与当前 UI 认证边界一致。",
            "No context-linked records available for package/export preview.": "没有可用于 package/export preview 的 context 关联记录。",
            "GUI mutation remains disabled for this session; use the CLI review path instead.": "当前 session 的 GUI mutation 仍保持禁用；请改用 CLI review path。",
            "Reviewer label is missing, so the UI cannot attribute the review action.": "缺少 reviewer label，因此 UI 无法归属该审阅操作。",
            "Reviewer label must start with a lowercase letter or digit and use only lowercase letters, digits, dot, underscore, or hyphen.": "reviewer label 必须以小写字母或数字开头，且只能包含小写字母、数字、点、下划线或连字符。",
            "Session label is required for the current session-gated local mutation boundary.": "当前 session-gated local mutation boundary 需要 session label。",
            "Session label must start with a lowercase letter or digit and use only lowercase letters, digits, dot, underscore, or hyphen.": "session label 必须以小写字母或数字开头，且只能包含小写字母、数字、点、下划线或连字符。",
            "Requested route and submitted UI intent differ, so the action was rejected before mutation.": "请求的 route 与提交的 UI intent 不一致，因此操作在 mutation 前被拒绝。",
            "Reviewer kind is not one of the supported local reviewer identity kinds.": "reviewer kind 不属于受支持的 local reviewer identity kind。",
            "Reviewer identity or session boundary is not aligned, so the action stays blocked.": "审阅者身份或 session 边界未对齐，因此操作保持 blocked。",
            "The target review event is no longer available from the current Chronicle state.": "目标 review event 在当前 Chronicle state 中已不可用。",
            "The review target is no longer pending; inspect the resolved queue before retrying.": "review target 已不再处于 pending 状态；请在重试前检查 resolved queue。",
            "The request body could not be parsed as JSON, so no mutation path was attempted.": "request body 无法解析为 JSON，因此未尝试 mutation path。",
            "Audit insertion failed before the review decision could be reported as applied.": "在将 review decision 报告为已应用之前，audit insertion 已失败。",
            "Audit insertion succeeded, but the Chronicle primary-record append failed, so treat the route as fail-closed.": "audit insertion 已成功，但 Chronicle primary-record append 失败，因此应将该 route 视为 fail-closed。",
        },
        "prefix": {
            "Open review target ": "打开审查目标 ",
            "Open event ": "打开事件 ",
            "Open context ": "打开上下文 ",
            "Root: ": "根目录: ",
            "Status: ": "状态: ",
            "Action: ": "操作: ",
            "Event: ": "事件: ",
            "Error code: ": "错误代码: ",
            "Warnings: ": "警告: ",
            "Response ": "响应 ",
        },
    },
}


class UIAuthMode:
    NOT_ENABLED = "not_enabled"
    LOOPBACK_LOCAL = "loopback_local"


class UIAuthorizationMode:
    NOT_ENABLED = "not_enabled"
    REVIEWER_DECLARED = "reviewer_declared"


@dataclass(frozen=True)
class UIBoundaryMetadata:
    """Read-only UI boundary configuration."""

    bind_scope: str
    loopback_only: bool = True
    read_only: bool = True
    mutation_enabled: bool = False
    mutation_capability_flag: bool = False
    auth_mode: str = UIAuthMode.NOT_ENABLED
    authorization_mode: str = UIAuthorizationMode.NOT_ENABLED
    session_gating: bool = False
    shared_machine_safe: bool = False
    review_queue_preview_only: bool = True
    future_write_requires_auth: bool = True
    primary_record_authoritative: bool = True
    mutation_readiness_status: str = "preview_only"
    mutation_readiness_message: str = "GUI mutation remains disabled; read-only preview only."
    mutation_blockers: tuple[str, ...] = (
        "write_routes_disabled",
        "auth_not_enabled",
        "authorization_not_enabled",
        "audit_insertion_cli_only",
    )
    mutation_blocker_details: list[dict[str, str]] | None = None
    reviewer_context_requirements: dict[str, Any] | None = None
    auth_boundary_summary: dict[str, Any] | None = None
    write_route_contract: dict[str, Any] | None = None


def _auth_boundary_summary(metadata: UIBoundaryMetadata) -> dict[str, Any]:
    blockers: list[str] = []
    next_steps: list[str] = []

    if metadata.auth_mode == UIAuthMode.NOT_ENABLED:
        _append_auth_boundary_blocker(blockers, next_steps, "auth_not_enabled")
    if metadata.authorization_mode == UIAuthorizationMode.NOT_ENABLED:
        _append_auth_boundary_blocker(blockers, next_steps, "authorization_not_enabled")
    if metadata.session_gating and not metadata.shared_machine_safe:
        _append_auth_boundary_blocker(blockers, next_steps, "shared_machine_session_unhardened")

    if metadata.auth_mode == UIAuthMode.NOT_ENABLED:
        status = "auth_not_enabled"
        message = "UI auth boundary is not enabled; reviewer identity remains advisory only."
    elif metadata.authorization_mode == UIAuthorizationMode.NOT_ENABLED:
        status = "authorization_not_enabled"
        message = "UI auth boundary is loopback-local, but reviewer authorization remains advisory only."
    else:
        status = "reviewer_declared_preview"
        message = "UI auth/authz metadata is configured for preview, but GUI mutation remains disabled."

    return {
        "status": status,
        "message": message,
        "blockers": blockers,
        "blocker_details": _serialize_auth_boundary_blocker_details(blockers),
        "next_steps": next_steps,
        "shared_machine_safe": metadata.shared_machine_safe,
        "session_gating": metadata.session_gating,
    }


def _append_auth_boundary_blocker(
    blockers: list[str],
    next_steps: list[str],
    blocker_code: str,
) -> None:
    blockers.append(blocker_code)
    next_steps.append(AUTH_BOUNDARY_BLOCKER_TEXT.get(blocker_code, blocker_code.replace("_", " ")))


def _serialize_auth_boundary_blocker_details(blockers: list[str]) -> list[dict[str, str]]:
    return [
        {
            "code": blocker,
            "message": AUTH_BOUNDARY_BLOCKER_TEXT.get(blocker, blocker.replace("_", " ")),
        }
        for blocker in blockers
    ]


def _serialize_review_warning_details(warnings: list[str]) -> list[dict[str, str]]:
    return [
        {
            "code": warning,
            "message": REVIEW_WARNING_TEXT.get(warning, warning.replace("_", " ")),
        }
        for warning in warnings
    ]


def _append_mutation_blocker(
    blockers: list[str],
    next_steps: list[str],
    blocker_code: str,
) -> None:
    if blocker_code not in blockers:
        blockers.append(blocker_code)
    message = MUTATION_BLOCKER_TEXT.get(blocker_code, blocker_code.replace("_", " "))
    if message not in next_steps:
        next_steps.append(message)


def _serialize_mutation_blocker_details(blockers: list[str]) -> list[dict[str, str]]:
    return [
        {
            "code": blocker,
            "message": MUTATION_BLOCKER_TEXT.get(blocker, blocker.replace("_", " ")),
        }
        for blocker in blockers
    ]


def _mutation_blocker_summaries(
    *,
    boundary_blockers: list[str],
    pending_boundary_warning_counts: dict[str, int],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for blocker_code in boundary_blockers:
        key = ("boundary", blocker_code)
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "code": blocker_code,
                "message": MUTATION_BLOCKER_TEXT.get(blocker_code, blocker_code.replace("_", " ")),
                "source": "boundary",
                "affected_count": 1,
            }
        )
    for blocker_code, count in sorted(pending_boundary_warning_counts.items()):
        key = ("review_queue", blocker_code)
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "code": blocker_code,
                "message": MUTATION_BLOCKER_TEXT.get(blocker_code, blocker_code.replace("_", " ")),
                "source": "review_queue",
                "affected_count": count,
            }
        )
    return rows


def _mutation_enablement_checks(
    *,
    boundary: dict[str, Any],
    pending_boundary_warning_counts: dict[str, int],
) -> list[dict[str, Any]]:
    blocker_set = {str(item) for item in boundary.get("mutation_blockers", [])}
    checks = [
        {
            "code": "mutation_capability_flag",
            "label": "Capability flag enabled",
            "satisfied": "mutation_capability_flag_disabled" not in blocker_set,
            "detail": MUTATION_BLOCKER_TEXT["mutation_capability_flag_disabled"],
        },
        {
            "code": "ui_mutation_enable_flag",
            "label": "Session enable flag enabled",
            "satisfied": "ui_mutation_enable_flag_disabled" not in blocker_set,
            "detail": MUTATION_BLOCKER_TEXT["ui_mutation_enable_flag_disabled"],
        },
        {
            "code": "auth_boundary",
            "label": "Auth boundary configured",
            "satisfied": "auth_not_enabled" not in blocker_set,
            "detail": MUTATION_BLOCKER_TEXT["auth_not_enabled"],
        },
        {
            "code": "authorization_boundary",
            "label": "Authorization boundary configured",
            "satisfied": "authorization_not_enabled" not in blocker_set,
            "detail": MUTATION_BLOCKER_TEXT["authorization_not_enabled"],
        },
        {
            "code": "reviewer_identity",
            "label": "Reviewer identity recorded",
            "satisfied": pending_boundary_warning_counts.get("reviewer_identity_missing", 0) == 0,
            "detail": MUTATION_BLOCKER_TEXT["reviewer_identity_missing"],
        },
        {
            "code": "session_labels",
            "label": "Session labels recorded",
            "satisfied": pending_boundary_warning_counts.get("reviewer_session_label_missing", 0) == 0,
            "detail": MUTATION_BLOCKER_TEXT["reviewer_session_label_missing"],
        },
    ]
    return checks


def _mutation_operational_readiness(
    *,
    enablement_checks: list[dict[str, Any]],
) -> dict[str, Any]:
    unsatisfied = [
        {
            "code": str(check.get("code", "")),
            "label": str(check.get("label", check.get("code", ""))),
            "detail": str(check.get("detail", "")),
        }
        for check in enablement_checks
        if check.get("satisfied") is not True
    ]
    satisfied_count = len(enablement_checks) - len(unsatisfied)
    required_count = len(enablement_checks)
    return {
        "status": "ready" if not unsatisfied else "blocked",
        "satisfied_count": satisfied_count,
        "required_count": required_count,
        "remaining_count": len(unsatisfied),
        "unsatisfied_checks": unsatisfied,
        "message": (
            "All explicit local mutation prerequisites are currently satisfied."
            if not unsatisfied
            else f"{len(unsatisfied)} explicit local mutation prerequisite(s) remain unsatisfied."
        ),
    }


def _reviewer_context_requirements(metadata: UIBoundaryMetadata) -> dict[str, Any]:
    effective_required_fields = ["reviewer_label", "reviewer_kind", "ui_intent"]
    if metadata.session_gating:
        effective_required_fields.append("session_label")
    return {
        "required_fields": ["reviewer_label", "reviewer_kind", "ui_intent"],
        "effective_required_fields": effective_required_fields,
        "reviewer_label_pattern": REVIEWER_LABEL_PATTERN.pattern,
        "reviewer_label_examples": ["alice", "desk-operator.01"],
        "session_label_required": bool(metadata.session_gating),
        "session_label_pattern": SESSION_LABEL_PATTERN.pattern,
        "session_label_examples": ["desk-session-1", "review.local-01"],
        "accepted_reviewer_kinds": [ReviewerIdentityKind.LOCAL_OPERATOR.value],
        "advisory_only_reviewer_kinds": [ReviewerIdentityKind.USER_DECLARED.value],
        "authority_note": "Request reviewer metadata is required local context, but it is not sufficient proof of authority on its own.",
        "reviewer_label_note": "Reviewer label must identify the local operator consistently enough for audit and review history drilldown.",
        "session_note": (
            "Session label is required because the current local mutation boundary is session-gated."
            if metadata.session_gating
            else "Session label is optional while session-gated review is disabled."
        ),
    }


def _reviewer_identity_proof_contract(metadata: UIBoundaryMetadata) -> dict[str, Any]:
    reviewer_context = _reviewer_context_requirements(metadata)
    return {
        "proof_status": (
            "session_gated_local_operator"
            if metadata.session_gating
            else "local_operator_advisory"
        ),
        "accepted_auth_modes": [UIAuthMode.LOOPBACK_LOCAL],
        "required_identity_fields": reviewer_context.get("effective_required_fields", []),
        "session_label_required": bool(metadata.session_gating),
        "session_label_pattern": reviewer_context.get("session_label_pattern", ""),
        "accepted_reviewer_kinds": reviewer_context.get("accepted_reviewer_kinds", []),
        "advisory_only_reviewer_kinds": reviewer_context.get("advisory_only_reviewer_kinds", []),
        "proof_note": (
            "Local reviewer identity proof currently means loopback-local operator context plus reviewer/session metadata."
        ),
        "insufficient_without": [
            "explicit authorization boundary",
            "fail-closed audit insertion",
        ],
    }


def _ui_write_route_contract(metadata: UIBoundaryMetadata) -> dict[str, Any]:
    reviewer_context = _reviewer_context_requirements(metadata)
    identity_proof = _reviewer_identity_proof_contract(metadata)
    mutation_enabled = bool(metadata.mutation_enabled)
    actions = ["approve", "reject", "request-changes"]
    return {
        "route_template": "/api/review-actions/<event_id>/<action>",
        "actions": actions,
        "expected_request_fields": reviewer_context.get("effective_required_fields", []),
        "optional_request_fields": ["note"],
        "accepted_reviewer_kinds": reviewer_context.get("accepted_reviewer_kinds", []),
        "advisory_only_reviewer_kinds": reviewer_context.get("advisory_only_reviewer_kinds", []),
        "session_gated": bool(metadata.session_gating),
        "mutation_enabled": mutation_enabled,
        "success_status_code": HTTPStatus.OK.value,
        "blocked_status_code": HTTPStatus.FORBIDDEN.value,
        "validation_status_code": HTTPStatus.BAD_REQUEST.value,
        "resolved_status_code": HTTPStatus.CONFLICT.value,
        "missing_target_status_code": HTTPStatus.NOT_FOUND.value,
        "server_error_status_code": HTTPStatus.INTERNAL_SERVER_ERROR.value,
        "transaction_rule": (
            "No durable GUI review result is reported as applied unless both review decision persistence and audit insertion succeed."
        ),
        "identity_proof_contract": identity_proof,
        "success_contract": {
            "transaction_status": "decision_and_audit_persisted",
            "rollback_status": "not_required",
            "durable_mutation_reported": True,
        },
        "failure_contract": {
            "rollback_status": "fail_closed",
            "durable_mutation_reported_on_failure": False,
            "possible_error_codes": [
                "mutation_disabled",
                "reviewer_label_required",
                "invalid_reviewer_label",
                "session_label_required",
                "invalid_session_label",
                "ui_intent_mismatch",
                "invalid_reviewer_kind",
                "authorization_failed",
                "review_target_not_found",
                "review_not_pending",
                "invalid_json",
                "audit_insertion_failed",
                "decision_persistence_failed",
            ],
        },
    }


@dataclass(frozen=True)
class UIStartupMetadata:
    """Startup metadata printed by `chronicle ui --json`."""

    host: str
    port: int
    url: str
    root: str
    bind_scope: str
    read_only: bool = True
    runtime: str = "foreground-local-ui"
    external_runtime: bool = False
    mutation_enabled: bool = False
    mutation_capability_flag: bool = False
    auth_mode: str = UIAuthMode.NOT_ENABLED
    authorization_mode: str = UIAuthorizationMode.NOT_ENABLED
    ui_boundary: UIBoundaryMetadata | None = None

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)


def build_startup_metadata(
    *,
    host: str,
    port: int,
    root: Path,
    mutation_capability_flag: bool = False,
    enable_ui_mutation: bool = False,
    auth_mode: str = UIAuthMode.NOT_ENABLED,
    authorization_mode: str = UIAuthorizationMode.NOT_ENABLED,
) -> UIStartupMetadata:
    """Build local UI startup metadata without starting the server."""
    ui_boundary = build_ui_boundary_metadata(
        host=host,
        mutation_capability_flag=mutation_capability_flag,
        enable_ui_mutation=enable_ui_mutation,
        auth_mode=auth_mode,
        authorization_mode=authorization_mode,
    )
    return UIStartupMetadata(
        host=host,
        port=port,
        url=f"http://{host}:{port}",
        root=str(root.resolve()),
        bind_scope=ui_boundary.bind_scope,
        mutation_enabled=ui_boundary.mutation_enabled,
        mutation_capability_flag=ui_boundary.mutation_capability_flag,
        auth_mode=ui_boundary.auth_mode,
        authorization_mode=ui_boundary.authorization_mode,
        ui_boundary=ui_boundary,
    )


def build_ui_boundary_metadata(
    *,
    host: str = DEFAULT_UI_HOST,
    mutation_capability_flag: bool = False,
    enable_ui_mutation: bool = False,
    auth_mode: str = UIAuthMode.NOT_ENABLED,
    authorization_mode: str = UIAuthorizationMode.NOT_ENABLED,
) -> UIBoundaryMetadata:
    """Build explicit UI boundary metadata."""
    mutation_enabled = (
        enable_ui_mutation
        and mutation_capability_flag
        and auth_mode == UIAuthMode.LOOPBACK_LOCAL
        and authorization_mode == UIAuthorizationMode.REVIEWER_DECLARED
    )
    blockers = []
    if not mutation_enabled:
        blockers.append("write_routes_disabled")
    if auth_mode == UIAuthMode.NOT_ENABLED:
        blockers.append("auth_not_enabled")
    if authorization_mode == UIAuthorizationMode.NOT_ENABLED:
        blockers.append("authorization_not_enabled")
    if not mutation_capability_flag:
        blockers.append("mutation_capability_flag_disabled")
    if not enable_ui_mutation:
        blockers.append("ui_mutation_enable_flag_disabled")
    metadata = UIBoundaryMetadata(
        bind_scope=_bind_scope(host),
        read_only=not mutation_enabled,
        mutation_enabled=mutation_enabled,
        mutation_capability_flag=mutation_capability_flag,
        auth_mode=auth_mode,
        authorization_mode=authorization_mode,
        session_gating=auth_mode == UIAuthMode.LOOPBACK_LOCAL,
        shared_machine_safe=mutation_enabled,
        mutation_blockers=tuple(blockers),
        mutation_readiness_status="enabled" if mutation_enabled else "preview_only",
        mutation_readiness_message=(
            "GUI mutation is explicitly enabled for loopback-local reviewer-declared actions."
            if mutation_enabled
            else (
                "GUI mutation remains disabled; capability flag is noted as preview intent only."
                if mutation_capability_flag
                else "GUI mutation remains disabled; read-only preview only."
            )
        ),
    )
    return UIBoundaryMetadata(
        **{
            **asdict(metadata),
            "mutation_blocker_details": _serialize_mutation_blocker_details(list(metadata.mutation_blockers)),
            "reviewer_context_requirements": _reviewer_context_requirements(metadata),
            "auth_boundary_summary": _auth_boundary_summary(metadata),
            "write_route_contract": _ui_write_route_contract(metadata),
        }
    )


def _dump_model(model: object) -> dict[str, Any]:
    return model.model_dump(mode="json")  # type: ignore[attr-defined]


def _find_by_attr(items: list[object], attr: str, value: str) -> dict[str, Any] | None:
    for item in items:
        if getattr(item, attr, None) == value:
            return _dump_model(item)
    return None


def _unique_list(plan: RuntimeRetrievalPlan) -> list[str]:
    seen: set[str] = set()
    values: list[str] = []
    for hit in [*plan.vector_hits, *plan.graph_hits, *plan.chronicle_hits]:
        if hit.identifier and hit.identifier not in seen:
            values.append(hit.identifier)
            seen.add(hit.identifier)
    return values


def _related_link(path: str, label: str) -> dict[str, str]:
    return {"path": path, "label": label}


def _open_detail_label(resource: str, record_id: str) -> str:
    labels = {
        "contexts": "Open context",
        "events": "Open event",
    }
    prefix = labels.get(resource, f"Open {resource.rstrip('s')}")
    return f"{prefix} {record_id}".strip()


def _open_matching_detail_label(resource: str) -> str:
    labels = {
        "review-queue": "Open matching review detail",
        "runtime-records": "Open matching runtime record",
    }
    return labels.get(resource, f"Open matching {resource.rstrip('s')} detail")


class ChronicleUIDataService:
    """Read-only data provider for the local UI."""

    def __init__(
        self,
        root: Path | None = None,
        *,
        host: str = DEFAULT_UI_HOST,
        mutation_capability_flag: bool = False,
        enable_ui_mutation: bool = False,
        auth_mode: str = UIAuthMode.NOT_ENABLED,
        authorization_mode: str = UIAuthorizationMode.NOT_ENABLED,
    ) -> None:
        self.root = root or Path.cwd()
        self.host = host
        self.mutation_capability_flag = mutation_capability_flag
        self.enable_ui_mutation = enable_ui_mutation
        self.auth_mode = auth_mode
        self.authorization_mode = authorization_mode
        self.chronicle = ChronicleService(self.root)
        self.audit = AuditService(self.root)
        self.lifecycle = LifecycleService(self.root)
        self.packages = IntegrationPackageService(self.root)
        self.package_review = PackageReviewService(self.root)
        self.review = ReviewService(self.root)
        self.runtime = RuntimeService(self.root)
        self.runtime_config = RuntimeConfigService(self.root)
        self.summary_jobs = SummaryJobService(self.root)
        self.vector_index = VectorIndexService(self.root)
        self.graph_index = GraphIndexService(self.root)

    def overview(self) -> dict[str, Any]:
        metadata = self.chronicle.require_initialized()
        events = self.chronicle.jsonl.read_all()
        artifacts, _ = self.chronicle.index.load_artifacts()
        contexts = self.chronicle.index.load_contexts()
        decisions = self.chronicle.index.load_decisions()
        rde_records = self.chronicle.index.load_rde_records()
        boundary_rules = self.chronicle.index.load_boundary_rules()
        audit_events = self.audit.list_events()
        lifecycle_events = self.lifecycle.list_events()
        runtime_records = self.runtime_records()["runtime_records"]
        review_queue = self.review_queue()["review_queue"]
        summary_jobs = self.summary_jobs_list()["summary_jobs"]
        ai_index_status = self.ai_index_status()["ai_index_status"]
        runtime_config = self.runtime_config_state()["runtime_config"]
        triage = self.overview_triage(runtime_records, review_queue)
        identity_boundary_summary = self.identity_boundary_summary(review_queue)
        summary_jobs_summary = self.summary_jobs_overview(summary_jobs)
        auth_boundary_overview = self.auth_boundary_overview(review_queue)
        runtime_records_summary = self.runtime_records_overview(runtime_records)
        return {
            "chronicle": {
                "id": metadata.chronicle_id,
                "title": metadata.title,
                "schema_version": metadata.schema_version,
                "root": str(self.root.resolve()),
            },
            "counts": {
                "events": len(events),
                "contexts": len(contexts),
                "artifacts": len(artifacts),
                "decisions": len(decisions),
                "rde_records": len(rde_records),
                "boundary_rules": len(boundary_rules),
                "audit_events": len(audit_events),
                "lifecycle_markers": len(lifecycle_events),
                "runtime_records": len(runtime_records),
                "review_queue": len(review_queue),
                "summary_jobs": len(summary_jobs),
                "vector_index_entries": ai_index_status["vector"]["entry_count"],
                "graph_index_nodes": ai_index_status["graph"]["node_count"],
                "graph_index_edges": ai_index_status["graph"]["edge_count"],
            },
            "package_review": self.package_review_snapshot(),
            "graph_summary": self.graph_summary(),
            "ai_index": ai_index_status,
            "runtime_config": runtime_config,
            "triage": triage,
            "runtime_boundary": self.runtime_boundary(),
            "ui_boundary": self.ui_boundary()["ui_boundary"],
            "auth_boundary_summary": self.ui_boundary()["ui_boundary"]["auth_boundary_summary"],
            "auth_boundary_overview": auth_boundary_overview,
            "identity_boundary_summary": identity_boundary_summary,
            "runtime_records_summary": runtime_records_summary,
            "summary_jobs_summary": summary_jobs_summary,
            "mutation_readiness": self.mutation_readiness_summary(review_queue),
        }

    def runtime_records_overview(self, runtime_records: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        rows = runtime_records if runtime_records is not None else self.runtime_records()["runtime_records"]
        kind_counts: dict[str, int] = {}
        auth_counts: dict[str, int] = {}
        mutation_counts: dict[str, int] = {}
        mutation_operational_counts: dict[str, int] = {}
        finish_reason_counts: dict[str, int] = {}
        provider_status_counts: dict[str, int] = {}
        response_present_count = 0
        for row in rows:
            kind = str(row.get("runtime_record_kind", "unknown"))
            auth_status = str(row.get("auth_readiness_status", "unknown"))
            mutation_summary = row.get("mutation_enablement_summary", {})
            mutation_status = str(mutation_summary.get("status", "unknown"))
            mutation_operational_status = str(
                mutation_summary.get("operational_status", "unknown")
            )
            response_summary = row.get("response_metadata_summary", {})
            kind_counts[kind] = kind_counts.get(kind, 0) + 1
            auth_counts[auth_status] = auth_counts.get(auth_status, 0) + 1
            mutation_counts[mutation_status] = mutation_counts.get(mutation_status, 0) + 1
            mutation_operational_counts[mutation_operational_status] = (
                mutation_operational_counts.get(mutation_operational_status, 0) + 1
            )
            if isinstance(response_summary, dict) and response_summary.get("present") is True:
                response_present_count += 1
                finish_reason = str(response_summary.get("finish_reason") or "unknown")
                provider_status = str(response_summary.get("provider_status") or "unknown")
                finish_reason_counts[finish_reason] = finish_reason_counts.get(finish_reason, 0) + 1
                provider_status_counts[provider_status] = provider_status_counts.get(provider_status, 0) + 1
        return {
            "kind_counts": kind_counts,
            "auth_readiness_counts": auth_counts,
            "mutation_readiness_counts": mutation_counts,
            "mutation_operational_counts": mutation_operational_counts,
            "provider_response_present_count": response_present_count,
            "provider_response_absent_count": len(rows) - response_present_count,
            "provider_response_finish_reason_counts": finish_reason_counts,
            "provider_response_status_counts": provider_status_counts,
        }

    def auth_boundary_overview(self, review_queue: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        queue = review_queue if review_queue is not None else self.review_queue()["review_queue"]
        auth_warning_count = 0
        authorization_warning_count = 0
        missing_identity_count = 0
        declared_identity_count = 0
        session_label_missing_count = 0
        review_capability_counts: dict[str, int] = {}
        assurance_counts: dict[str, int] = {}
        provider_finish_reason_counts: dict[str, int] = {}
        provider_status_counts: dict[str, int] = {}
        provider_response_present_count = 0

        for row in queue:
            capability = row.get("review_capability", {})
            capability_status = str(capability.get("status", "unknown"))
            review_capability_counts[capability_status] = review_capability_counts.get(capability_status, 0) + 1
            warnings = capability.get("warnings", [])
            if "ui_auth_not_enabled" in warnings:
                auth_warning_count += 1
            if "ui_authorization_not_enabled" in warnings:
                authorization_warning_count += 1
            if "no_reviewer_identity_recorded" in warnings:
                missing_identity_count += 1
            if "reviewer_identity_declared_only" in warnings:
                declared_identity_count += 1
            if "reviewer_session_label_missing" in warnings:
                session_label_missing_count += 1
            assurance = row.get("latest_identity_assurance")
            if isinstance(assurance, dict) and assurance.get("status"):
                assurance_status = str(assurance.get("status", "unknown"))
                assurance_counts[assurance_status] = assurance_counts.get(assurance_status, 0) + 1
            response_summary = row.get("response_metadata_summary", {})
            if isinstance(response_summary, dict) and response_summary.get("present") is True:
                provider_response_present_count += 1
                finish_reason = str(response_summary.get("finish_reason") or "unknown")
                provider_status = str(response_summary.get("provider_status") or "unknown")
                provider_finish_reason_counts[finish_reason] = (
                    provider_finish_reason_counts.get(finish_reason, 0) + 1
                )
                provider_status_counts[provider_status] = (
                    provider_status_counts.get(provider_status, 0) + 1
                )

        return {
            "auth_warning_count": auth_warning_count,
            "authorization_warning_count": authorization_warning_count,
            "missing_identity_count": missing_identity_count,
            "declared_identity_count": declared_identity_count,
            "session_label_missing_count": session_label_missing_count,
            "review_capability_counts": review_capability_counts,
            "identity_assurance_counts": assurance_counts,
            "provider_response_present_count": provider_response_present_count,
            "provider_response_absent_count": len(queue) - provider_response_present_count,
            "provider_response_finish_reason_counts": provider_finish_reason_counts,
            "provider_response_status_counts": provider_status_counts,
        }

    def summary_jobs_overview(self, summary_jobs: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        rows = summary_jobs if summary_jobs is not None else self.summary_jobs_list()["summary_jobs"]
        status_counts: dict[str, int] = {}
        review_counts: dict[str, int] = {}
        auth_counts: dict[str, int] = {}
        package_counts: dict[str, int] = {}
        mutation_counts: dict[str, int] = {}
        mutation_operational_counts: dict[str, int] = {}
        provider_counts: dict[str, int] = {}
        assurance_counts: dict[str, int] = {}
        reviewer_kind_counts: dict[str, int] = {}
        finish_reason_counts: dict[str, int] = {}
        provider_status_counts: dict[str, int] = {}
        response_present_count = 0
        source_count_total = 0
        for row in rows:
            status = str(row.get("status", "unknown"))
            review_status = str(row.get("review_capability_status", "unknown"))
            auth_status = str(row.get("auth_readiness_status", "unknown"))
            package_status = str(row.get("package_readiness_status", "unknown"))
            mutation_summary = row.get("mutation_enablement_summary", {})
            mutation_status = str(mutation_summary.get("status", "unknown"))
            mutation_operational_status = str(
                mutation_summary.get("operational_status", "unknown")
            )
            provider_kind = str(row.get("runtime_provider_kind", "unknown"))
            assurance_status = str(row.get("identity_assurance_status", "unknown"))
            reviewer_kind = str((row.get("latest_reviewer_identity") or {}).get("kind", "unknown"))
            status_counts[status] = status_counts.get(status, 0) + 1
            review_counts[review_status] = review_counts.get(review_status, 0) + 1
            auth_counts[auth_status] = auth_counts.get(auth_status, 0) + 1
            package_counts[package_status] = package_counts.get(package_status, 0) + 1
            mutation_counts[mutation_status] = mutation_counts.get(mutation_status, 0) + 1
            mutation_operational_counts[mutation_operational_status] = (
                mutation_operational_counts.get(mutation_operational_status, 0) + 1
            )
            provider_counts[provider_kind] = provider_counts.get(provider_kind, 0) + 1
            assurance_counts[assurance_status] = assurance_counts.get(assurance_status, 0) + 1
            reviewer_kind_counts[reviewer_kind] = reviewer_kind_counts.get(reviewer_kind, 0) + 1
            response_summary = row.get("response_metadata_summary", {})
            if isinstance(response_summary, dict) and response_summary.get("present") is True:
                response_present_count += 1
                finish_reason = str(response_summary.get("finish_reason") or "unknown")
                provider_status = str(response_summary.get("provider_status") or "unknown")
                finish_reason_counts[finish_reason] = finish_reason_counts.get(finish_reason, 0) + 1
                provider_status_counts[provider_status] = provider_status_counts.get(provider_status, 0) + 1
            source_count_total += int(row.get("summary_source_count", 0) or 0)
        return {
            "status_counts": status_counts,
            "review_capability_counts": review_counts,
            "auth_readiness_counts": auth_counts,
            "package_readiness_counts": package_counts,
            "mutation_readiness_counts": mutation_counts,
            "mutation_operational_counts": mutation_operational_counts,
            "runtime_provider_counts": provider_counts,
            "provider_response_present_count": response_present_count,
            "provider_response_absent_count": len(rows) - response_present_count,
            "provider_response_finish_reason_counts": finish_reason_counts,
            "provider_response_status_counts": provider_status_counts,
            "identity_assurance_counts": assurance_counts,
            "reviewer_kind_counts": reviewer_kind_counts,
            "summary_source_total": source_count_total,
        }

    def identity_boundary_summary(self, review_queue: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        queue = review_queue if review_queue is not None else self.review_queue()["review_queue"]
        assurance_counts: dict[str, int] = {}
        missing_identity_count = 0
        declared_identity_count = 0
        session_label_missing_count = 0

        for row in queue:
            assurance = row.get("latest_identity_assurance")
            if isinstance(assurance, dict) and assurance.get("status"):
                status = str(assurance["status"])
                assurance_counts[status] = assurance_counts.get(status, 0) + 1
            else:
                missing_identity_count += 1

            warnings = row.get("review_capability", {}).get("warnings", [])
            if "reviewer_identity_declared_only" in warnings:
                declared_identity_count += 1
            if "reviewer_session_label_missing" in warnings:
                session_label_missing_count += 1

        blockers: list[str] = []
        next_steps: list[str] = []
        if missing_identity_count > 0:
            blockers.append("reviewer_identity_missing")
            next_steps.append("Record reviewer identity metadata before relying on GUI review signals.")
        if declared_identity_count > 0:
            blockers.append("reviewer_identity_declared_only")
            next_steps.append("Strengthen reviewer identity beyond self-declared metadata.")
        if session_label_missing_count > 0:
            blockers.append("reviewer_session_label_missing")
            next_steps.append("Require session labels when session-gated review is expected.")

        if assurance_counts.get("boundary_aligned", 0) > 0 and not blockers:
            status = "boundary_aligned"
            message = "Recorded reviewer identity metadata is aligned with the current preview auth boundary."
        elif assurance_counts:
            status = "partially_aligned"
            message = "Some reviewer identity metadata is present, but boundary alignment remains incomplete."
        else:
            status = "identity_unavailable"
            message = "Reviewer identity assurance is not yet available in the current derived queue view."

        return {
            "status": status,
            "message": message,
            "assurance_counts": assurance_counts,
            "missing_identity_count": missing_identity_count,
            "declared_identity_count": declared_identity_count,
            "session_label_missing_count": session_label_missing_count,
            "blockers": blockers,
            "next_steps": next_steps,
        }

    def overview_triage(
        self,
        runtime_records: list[dict[str, Any]],
        review_queue: list[dict[str, Any]],
    ) -> dict[str, Any]:
        runtime_by_kind: dict[str, int] = {}
        for row in runtime_records:
            kind = str(row.get("runtime_record_kind", "unknown"))
            runtime_by_kind[kind] = runtime_by_kind.get(kind, 0) + 1

        review_capability_counts: dict[str, int] = {}
        readiness_counts: dict[str, int] = {}
        cli_parity_counts: dict[str, int] = {}
        warning_counts: dict[str, int] = {}
        identity_assurance_counts: dict[str, int] = {}
        reviewer_kind_counts: dict[str, int] = {}
        provider_response_present_reviews = 0
        ready_now = 0
        advisory_only = 0
        package_ready = 0
        parity_aligned = 0
        parity_drift = 0
        identity_boundary_aligned = 0
        identity_declared_only = 0

        for row in review_queue:
            capability_status = str(row.get("review_capability", {}).get("status", "unknown"))
            review_capability_counts[capability_status] = review_capability_counts.get(capability_status, 0) + 1
            if capability_status == "ready":
                ready_now += 1
            elif capability_status == "advisory_only":
                advisory_only += 1

            readiness_status = str(row.get("package_readiness_summary", {}).get("status", "unknown"))
            readiness_counts[readiness_status] = readiness_counts.get(readiness_status, 0) + 1
            if readiness_status == "package_context_available":
                package_ready += 1

            parity_status = str(row.get("cli_parity_summary", {}).get("status", "unknown"))
            cli_parity_counts[parity_status] = cli_parity_counts.get(parity_status, 0) + 1
            if parity_status == "aligned":
                parity_aligned += 1
            elif parity_status == "drift_detected":
                parity_drift += 1

            for warning_code in row.get("review_capability", {}).get("warnings", []):
                code = str(warning_code)
                warning_counts[code] = warning_counts.get(code, 0) + 1
                if code == "reviewer_identity_declared_only":
                    identity_declared_only += 1

            assurance = row.get("latest_identity_assurance") or {}
            assurance_status = str(assurance.get("status", "unknown"))
            identity_assurance_counts[assurance_status] = identity_assurance_counts.get(assurance_status, 0) + 1
            if assurance_status == "boundary_aligned":
                identity_boundary_aligned += 1

            latest_identity = row.get("latest_reviewer_identity") or {}
            reviewer_kind = str(latest_identity.get("kind", "unknown"))
            reviewer_kind_counts[reviewer_kind] = reviewer_kind_counts.get(reviewer_kind, 0) + 1
            response_summary = row.get("response_metadata_summary", {})
            if isinstance(response_summary, dict) and response_summary.get("present") is True:
                provider_response_present_reviews += 1

        return {
            "runtime_record_kinds": runtime_by_kind,
            "review_capability_counts": review_capability_counts,
            "package_readiness_counts": readiness_counts,
            "cli_parity_counts": cli_parity_counts,
            "warning_counts": warning_counts,
            "identity_assurance_counts": identity_assurance_counts,
            "reviewer_kind_counts": reviewer_kind_counts,
            "warning_summaries": self._warning_summaries(warning_counts),
            "ready_now_reviews": ready_now,
            "advisory_only_reviews": advisory_only,
            "package_ready_reviews": package_ready,
            "cli_parity_aligned_reviews": parity_aligned,
            "cli_parity_drift_reviews": parity_drift,
            "identity_boundary_aligned_reviews": identity_boundary_aligned,
            "identity_declared_only_reviews": identity_declared_only,
            "provider_response_present_reviews": provider_response_present_reviews,
            "needs_attention_reviews": len(review_queue),
        }

    def _warning_summaries(self, warning_counts: dict[str, int]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for code, count in warning_counts.items():
            rows.append(
                {
                    "code": code,
                    "count": count,
                    "priority": REVIEW_WARNING_PRIORITY.get(code, 99),
                    "label": code.replace("_", " "),
                    "message": self._warning_message(code),
                }
            )
        return sorted(rows, key=lambda item: (item["priority"], -item["count"], item["code"]))

    def events(self, *, limit: int = 100) -> dict[str, Any]:
        self.chronicle.require_initialized()
        events = self.chronicle.jsonl.read_all()
        return {"events": [_dump_model(event) for event in reversed(events[-limit:])]}

    def contexts(self) -> dict[str, Any]:
        self.chronicle.require_initialized()
        contexts = sorted(self.chronicle.index.load_contexts().values(), key=lambda ctx: ctx.created_at)
        return {"contexts": [_dump_model(context) for context in contexts]}

    def artifacts(self) -> dict[str, Any]:
        self.chronicle.require_initialized()
        artifacts, versions = self.chronicle.index.load_artifacts()
        rows = []
        for artifact in sorted(artifacts.values(), key=lambda item: item.created_at):
            data = _dump_model(artifact)
            data["version_count"] = len(versions.get(artifact.artifact_id, []))
            rows.append(data)
        return {"artifacts": rows}

    def decisions(self) -> dict[str, Any]:
        self.chronicle.require_initialized()
        decisions = sorted(self.chronicle.index.load_decisions().values(), key=lambda item: item.decided_at)
        return {"decisions": [_dump_model(decision) for decision in decisions]}

    def rde_records(self) -> dict[str, Any]:
        self.chronicle.require_initialized()
        records = sorted(self.chronicle.index.load_rde_records().values(), key=lambda item: item.created_at)
        return {"rde_records": [_dump_model(record) for record in records]}

    def boundary_rules(self) -> dict[str, Any]:
        self.chronicle.require_initialized()
        rules = sorted(self.chronicle.index.load_boundary_rules().values(), key=lambda item: item.created_at)
        return {"boundary_rules": [_dump_model(rule) for rule in rules]}

    def audit_events(self, *, limit: int = 100) -> dict[str, Any]:
        events = self.audit.list_events()
        return {"audit_events": [_dump_model(event) for event in reversed(events[-limit:])]}

    def lifecycle_markers(self, *, limit: int = 100) -> dict[str, Any]:
        events = self.lifecycle.list_events()
        return {"lifecycle_markers": [_dump_model(event) for event in reversed(events[-limit:])]}

    def runtime_records(self, *, limit: int = 100) -> dict[str, Any]:
        self.chronicle.require_initialized()
        events = [
            event
            for event in self.chronicle.jsonl.read_all()
            if event.event_type.value == "assistant_output"
            and (
                "runtime_summary" in event.payload
                or "runtime_execution" in event.payload
                or "runtime_retrieval_plan" in event.payload
                or "runtime_invocation_plan" in event.payload
            )
        ]
        rows: list[dict[str, Any]] = []
        for event in reversed(events[-limit:]):
            data = _dump_model(event)
            preview = self.runtime.record_preview(event)
            data["runtime_record_kind"] = preview.record_kind
            data["runtime_record_preview"] = preview.model_dump(mode="json")
            review_row = self._review_queue_row(event.event_id)
            if review_row is not None:
                mutation_enablement = self.mutation_readiness_summary()
                data["review_target_event_id"] = event.event_id
                data["review_capability_status"] = str(
                    review_row.get("review_capability", {}).get("status", "")
                )
                data["auth_readiness_status"] = str(
                    review_row.get("auth_boundary_notice", {}).get("status", "")
                )
                data["action_preview_summary"] = review_row.get("action_preview_summary", {})
                data["identity_assurance_status"] = str(
                    review_row.get("latest_identity_assurance", {}).get("status", "unknown")
                )
                data["mutation_enablement_summary"] = self._mutation_enablement_list_summary(
                    mutation_enablement
                )
                data["ui_mutation_enabled"] = bool(mutation_enablement.get("enablement_ready")) and bool(
                    review_row.get("ui_mutation_enabled", False)
                )
                data["review_preview_only"] = not bool(data["ui_mutation_enabled"])
            data["response_metadata_summary"] = self._runtime_response_metadata_summary(payload=data["payload"])
            rows.append(data)
        return {"runtime_records": rows}

    def review_queue(self, *, limit: int = 100) -> dict[str, Any]:
        self.chronicle.require_initialized()
        boundary = self.ui_boundary()["ui_boundary"]
        rows: list[dict[str, Any]] = []
        for entry in self.review.queue()[:limit]:
            data = entry.model_dump(mode="json")
            data["suggested_cli_family"] = self._suggested_cli_family_from_kind(entry.review_kind)
            data["response_metadata_summary"] = self._review_target_response_metadata_summary(
                entry.target_event_id
            )
            data["review_capability"] = self._review_capability(
                pending=bool(data.get("pending")),
                boundary=boundary,
                identity=(
                    ReviewerIdentity.model_validate(data["latest_reviewer_identity"])
                    if data.get("latest_reviewer_identity") is not None
                    else None
                ),
            )
            if data.get("latest_reviewer_identity") is not None:
                data["latest_identity_assurance"] = self._identity_assurance(
                    ReviewerIdentity.model_validate(data["latest_reviewer_identity"]),
                    boundary,
                )
            data["auth_boundary_notice"] = self._auth_boundary_notice(
                boundary,
                data.get("review_capability"),
                data.get("latest_identity_assurance"),
            )
            readiness = self.review_package_readiness(entry.target_event_id)
            data["package_readiness_summary"] = self._package_readiness_summary(readiness)
            data["action_preview_summary"] = self._review_action_preview(
                entry.target_event_id,
                data.get("review_capability", {}),
                mutation_enabled=bool(boundary.get("mutation_enabled", False)),
                write_route_contract=boundary.get("write_route_contract", {}),
            )
            data["cli_parity_summary"] = self._review_cli_parity_summary(
                entry.target_event_id,
                data.get("available_actions", []),
                data["action_preview_summary"],
            )
            data["ui_mutation_enabled"] = bool(boundary.get("mutation_enabled", False))
            data["review_preview_only"] = not bool(boundary.get("mutation_enabled", False))
            rows.append(data)
        mutation_enablement = self._mutation_enablement_list_summary(
            self.mutation_readiness_summary(rows)
        )
        for row in rows:
            row["mutation_enablement_summary"] = mutation_enablement
        return {"review_queue": rows}

    def summary_jobs_list(self, *, limit: int = 100) -> dict[str, Any]:
        rows: list[dict[str, Any]] = []
        for job in reversed(self.summary_jobs.list_jobs()[:limit]):
            data = job.model_dump(mode="json")
            data["summary_source_count"] = len(job.source_refs)
            data["runtime_provider_kind"] = job.provenance.runtime.provider_kind.value
            data["response_metadata_summary"] = self._response_metadata_summary(
                response_metadata=job.provenance.response_metadata,
                response_keys=job.provenance.response_keys,
            )
            data["suggested_cli_family"] = "chronicle summary show --id"
            data["identity_assurance_status"] = "unknown"
            review_target_event_id = str(data.get("event_id", ""))
            if review_target_event_id.startswith("evt_"):
                review_row = self._review_queue_row(review_target_event_id)
                if review_row is not None:
                    boundary = self.ui_boundary()["ui_boundary"]
                    data["review_target_event_id"] = review_target_event_id
                    data["review_capability_status"] = str(
                        review_row.get("review_capability", {}).get("status", "")
                    )
                    data["auth_readiness_status"] = str(
                        review_row.get("auth_boundary_notice", {}).get("status", "")
                    )
                    data["package_readiness_status"] = str(
                        review_row.get("package_readiness_summary", {}).get("status", "")
                    )
                    data["cli_parity_status"] = str(
                        review_row.get("cli_parity_summary", {}).get("status", "")
                    )
                    data["action_preview_summary"] = review_row.get("action_preview_summary", {})
                    data["mutation_enablement_summary"] = self._mutation_enablement_list_summary(
                        self.mutation_readiness_summary()
                    )
                    data["ui_mutation_enabled"] = bool(boundary.get("mutation_enabled", False))
                    data["review_preview_only"] = not bool(boundary.get("mutation_enabled", False))
                    if review_row.get("latest_reviewer_identity") is not None:
                        data["latest_reviewer_identity"] = review_row.get("latest_reviewer_identity")
                    if review_row.get("latest_identity_assurance") is not None:
                        data["latest_identity_assurance"] = review_row.get("latest_identity_assurance")
                        data["identity_assurance_status"] = str(
                            review_row.get("latest_identity_assurance", {}).get("status", "")
                        )
            rows.append(data)
        return {"summary_jobs": rows}

    def mutation_readiness_summary(self, review_queue: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        boundary = self.ui_boundary()["ui_boundary"]
        queue = review_queue if review_queue is not None else self.review_queue()["review_queue"]
        ready_rows = sum(1 for row in queue if row.get("review_capability", {}).get("can_review_now") is True)
        advisory_rows = sum(1 for row in queue if row.get("review_capability", {}).get("can_review_now") is not True)
        blockers: list[str] = []
        next_steps: list[str] = []
        boundary_blockers = [str(blocker) for blocker in boundary.get("mutation_blockers", [])]
        for blocker in boundary_blockers:
            _append_mutation_blocker(blockers, next_steps, str(blocker))
        pending_boundary_warning_counts: dict[str, int] = {}
        for row in queue:
            for warning in row.get("review_capability", {}).get("warnings", []):
                blocker_code = AUTH_BOUNDARY_WARNING_TO_BLOCKER.get(str(warning))
                if blocker_code is None:
                    continue
                pending_boundary_warning_counts[blocker_code] = (
                    pending_boundary_warning_counts.get(blocker_code, 0) + 1
                )
        for blocker_code in pending_boundary_warning_counts:
            _append_mutation_blocker(blockers, next_steps, blocker_code)
        enablement_checks = _mutation_enablement_checks(
            boundary=boundary,
            pending_boundary_warning_counts=pending_boundary_warning_counts,
        )
        blocker_summaries = _mutation_blocker_summaries(
            boundary_blockers=boundary_blockers,
            pending_boundary_warning_counts=pending_boundary_warning_counts,
        )
        operational_readiness = _mutation_operational_readiness(
            enablement_checks=enablement_checks,
        )
        satisfied_checks = sum(1 for check in enablement_checks if check.get("satisfied") is True)
        if ready_rows > 0:
            next_steps.append(
                "Preserve review-ready signals as preview-only until browser-triggered write ADR and audit semantics are explicit."
            )
        return {
            "status": boundary.get("mutation_readiness_status", "preview_only"),
            "message": boundary.get("mutation_readiness_message", "GUI mutation remains disabled."),
            "ready_row_count": ready_rows,
            "advisory_row_count": advisory_rows,
            "blockers": blockers,
            "blocker_details": _serialize_mutation_blocker_details(blockers),
            "blocker_summaries": blocker_summaries,
            "pending_boundary_warning_counts": pending_boundary_warning_counts,
            "enablement_checks": enablement_checks,
            "enablement_ready": satisfied_checks == len(enablement_checks),
            "enablement_satisfied_count": satisfied_checks,
            "enablement_required_count": len(enablement_checks),
            "operational_readiness": operational_readiness,
            "reviewer_context_requirements": boundary.get("reviewer_context_requirements", {}),
            "write_route_contract": boundary.get("write_route_contract", {}),
            "next_steps": next_steps,
        }

    @staticmethod
    def _mutation_enablement_list_summary(mutation_readiness: dict[str, Any]) -> dict[str, Any]:
        operational_readiness = mutation_readiness.get("operational_readiness", {})
        write_route_contract = mutation_readiness.get("write_route_contract", {})
        identity_proof_contract = write_route_contract.get("identity_proof_contract", {})
        return {
            "status": str(mutation_readiness.get("status", "")),
            "enablement_ready": bool(mutation_readiness.get("enablement_ready", False)),
            "operational_status": str(operational_readiness.get("status", "")),
            "remaining_count": int(operational_readiness.get("remaining_count", 0) or 0),
            "blocked_status_code": write_route_contract.get("blocked_status_code"),
            "success_status_code": write_route_contract.get("success_status_code"),
            "identity_proof_status": str(identity_proof_contract.get("proof_status", "")),
            "identity_proof_fields": [
                str(item)
                for item in identity_proof_contract.get("required_identity_fields", [])
            ],
        }

    def ai_index_status(self) -> dict[str, Any]:
        vector_status = self.vector_index.status()
        graph_snapshot = self.graph_index.snapshot()
        return {
            "ai_index_status": {
                "vector": vector_status.model_dump(mode="json"),
                "graph": {
                    "path": str(self.graph_index.paths.graph_index_file),
                    "node_count": len(graph_snapshot.nodes),
                    "edge_count": len(graph_snapshot.edges),
                    "external_call_made": False,
                },
                "derived_surface": True,
                "primary_record_authoritative": True,
                "external_services": False,
                "graphrag_runtime": False,
                "correctness_proof": False,
            }
        }

    def ai_index_vector_entries(self) -> dict[str, Any]:
        snapshot = self.vector_index.snapshot()
        return {"vector_entries": [_dump_model(entry) for entry in snapshot.entries]}

    def ai_index_graph_nodes(self) -> dict[str, Any]:
        snapshot = self.graph_index.snapshot()
        return {"graph_nodes": [_dump_model(node) for node in snapshot.nodes]}

    def ai_index_graph_edges(self) -> dict[str, Any]:
        snapshot = self.graph_index.snapshot()
        return {"graph_edges": [_dump_model(edge) for edge in snapshot.edges]}

    def runtime_config_state(self) -> dict[str, Any]:
        state = self.runtime_config.show()
        return {"runtime_config": state.model_dump(mode="json")}

    def package_review_snapshot(self) -> dict[str, Any]:
        try:
            report = self.package_review.review_context_package(purpose="chronicle ui overview")
            return report.model_dump(mode="json")
        except Exception as exc:  # pragma: no cover - defensive UI degradation
            return {"status": "unavailable", "error": str(exc)}

    def graph_summary(self) -> dict[str, Any]:
        try:
            graph = GraphExportService(self.root).export_graph()
            return {"nodes": len(graph.nodes), "edges": len(graph.edges)}
        except Exception as exc:  # pragma: no cover - defensive UI degradation
            return {"nodes": 0, "edges": 0, "error": str(exc)}

    def runtime_package_handoff(self, plan: RuntimeRetrievalPlan) -> dict[str, Any]:
        context_ids = [record_id for record_id in _unique_list(plan) if record_id.startswith("ctx_")]
        skipped_ids = [record_id for record_id in _unique_list(plan) if not record_id.startswith("ctx_")]
        payload: dict[str, Any] = {
            "status": "package_context_available" if context_ids else "no_context_records",
            "eligible_context_ids": context_ids,
            "skipped_record_ids": skipped_ids,
            "purpose": f"runtime retrieval handoff: {plan.query}",
            "target_environment": "local",
            "package_review_required": True,
        }
        if not context_ids:
            payload["message"] = "No context records were selected by the retrieval dry-run, so package preview is advisory only."
            return payload
        package = self.packages.build_context_package(
            purpose=payload["purpose"],
            context_ids=context_ids,
        )
        review = self.package_review.review_package(package)
        payload["package_manifest_preview"] = package.manifest.model_dump(mode="json")
        payload["package_review"] = review.model_dump(mode="json")
        payload["message"] = "Read-only package preview derived from retrieval-plan context hits."
        return payload

    def runtime_related_links(self, event_id: str, payload: dict[str, Any]) -> list[dict[str, str]]:
        links = [
            _related_link(
                f"/api/review-queue/{event_id}",
                _open_matching_detail_label("review-queue"),
            )
        ]
        if "runtime_invocation_plan" in payload:
            request_preview = payload["runtime_invocation_plan"].get("request_preview", {})
            summary_job_id = request_preview.get("summary_job_id")
            if isinstance(summary_job_id, str) and summary_job_id.startswith("sum_"):
                links.append(
                    _related_link(
                        f"/api/summary-jobs/{summary_job_id}",
                        f"Open summary job {summary_job_id}",
                    )
                )
        if "runtime_execution" in payload:
            execution = RuntimeExecutionResult.model_validate(payload["runtime_execution"])
            if execution.draft_summary_job_id:
                links.append(
                    _related_link(
                        f"/api/summary-jobs/{execution.draft_summary_job_id}",
                        f"Open summary job {execution.draft_summary_job_id}",
                    )
                )
            if execution.artifact_id:
                links.append(
                    _related_link(
                        f"/api/artifacts/{execution.artifact_id}",
                        f"Open artifact {execution.artifact_id}",
                    )
                )
        if "runtime_retrieval_plan" in payload:
            plan = RuntimeRetrievalPlan.model_validate(payload["runtime_retrieval_plan"])
            for record_id in _unique_list(plan):
                if record_id.startswith("ctx_"):
                    links.append(
                        _related_link(
                            f"/api/contexts/{record_id}",
                            _open_detail_label("contexts", record_id),
                        )
                    )
                elif record_id.startswith("evt_"):
                    links.append(
                        _related_link(
                            f"/api/events/{record_id}",
                            _open_detail_label("events", record_id),
                        )
                    )
        return links

    def review_package_readiness(self, target_event_id: str) -> dict[str, Any]:
        self.chronicle.require_initialized()
        event = next(
            (item for item in self.chronicle.jsonl.read_all() if item.event_id == target_event_id),
            None,
        )
        if event is None:
            return {
                "status": "missing_target",
                "message": "Target event is not available for package readiness derivation.",
                "suggested_commands": [],
            }

        payload = getattr(event, "payload", {})
        if "runtime_retrieval_plan" in payload:
            plan = RuntimeRetrievalPlan.model_validate(payload["runtime_retrieval_plan"])
            handoff = self.runtime_package_handoff(plan)
            handoff["suggested_commands"] = [
                'chronicle package review --purpose "runtime retrieval handoff"',
                'chronicle package context --purpose "runtime retrieval handoff" --persist',
            ]
            return handoff

        context_ids = [context_id for context_id in getattr(event, "context_ids", []) if context_id.startswith("ctx_")]
        source_ref = getattr(getattr(event, "source", None), "source_ref", "") or ""
        if source_ref.startswith("ctx_") and source_ref not in context_ids:
            context_ids.append(source_ref)

        if not context_ids:
            return {
                "status": "no_context_records",
                "eligible_context_ids": [],
                "skipped_record_ids": [],
                "message": "No context-linked records are available for package/export preview from this review target.",
                "suggested_commands": ["chronicle show --json", "chronicle review queue --json"],
                "package_review_required": True,
            }

        package = self.packages.build_context_package(
            purpose=f"review target handoff: {target_event_id}",
            context_ids=context_ids,
        )
        review = self.package_review.review_package(package)
        return {
            "status": "package_context_available",
            "eligible_context_ids": context_ids,
            "skipped_record_ids": [],
            "message": "Read-only package readiness derived from context-linked review target records.",
            "suggested_commands": [
                'chronicle package review --purpose "review target handoff"',
                'chronicle package context --purpose "review target handoff" --persist',
            ],
            "package_review_required": True,
            "package_manifest_preview": package.manifest.model_dump(mode="json"),
            "package_review": review.model_dump(mode="json"),
        }

    def review_related_links(self, target_event_id: str) -> list[dict[str, str]]:
        links = [
            _related_link(
                f"/api/runtime-records/{target_event_id}",
                _open_matching_detail_label("runtime-records"),
            )
        ]
        readiness = self.review_package_readiness(target_event_id)
        for context_id in readiness.get("eligible_context_ids", []):
            if isinstance(context_id, str) and context_id.startswith("ctx_"):
                links.append(
                    _related_link(
                        f"/api/contexts/{context_id}",
                        _open_detail_label("contexts", context_id),
                    )
                )
        return links

    def summary_job_related_links(self, summary_job_id: str, job: dict[str, Any]) -> list[dict[str, str]]:
        links: list[dict[str, str]] = []
        event_id = str(job.get("event_id", ""))
        if event_id.startswith("evt_"):
            links.append(
                _related_link(
                    f"/api/review-queue/{event_id}",
                    f"Open review target {event_id}",
                )
            )
        for ref in job.get("source_refs", []):
            record_type = str(ref.get("record_type", "event"))
            record_id = str(ref.get("record_id", ""))
            if record_type == "event" and record_id.startswith("evt_"):
                links.append(_related_link(f"/api/events/{record_id}", f"Open event {record_id}"))
            elif record_id.startswith("ctx_"):
                links.append(_related_link(f"/api/contexts/{record_id}", f"Open context {record_id}"))
        artifact_id = str(job.get("artifact_id", ""))
        if artifact_id.startswith("art_"):
            links.append(_related_link(f"/api/artifacts/{artifact_id}", f"Open artifact {artifact_id}"))
        return links

    def runtime_boundary(self) -> dict[str, Any]:
        return {
            "read_only": True,
            "foreground_process": True,
            "daemon": False,
            "server_default_host": DEFAULT_UI_HOST,
            "external_model_api": False,
            "graphrag_runtime": False,
            "vector_db": False,
            "graph_db": False,
            "correctness_proof": False,
        }

    @staticmethod
    def _response_metadata_summary(
        *,
        response_metadata: dict[str, Any] | None,
        response_keys: list[str] | None,
    ) -> dict[str, Any]:
        metadata = response_metadata or {}
        keys = [str(item) for item in (response_keys or [])]
        return {
            "present": bool(metadata or keys),
            "response_id": metadata.get("response_id"),
            "finish_reason": metadata.get("finish_reason"),
            "provider_status": metadata.get("provider_status"),
            "usage_input_tokens": metadata.get("usage_input_tokens"),
            "usage_output_tokens": metadata.get("usage_output_tokens"),
            "usage_total_tokens": metadata.get("usage_total_tokens"),
            "metadata_count": len(metadata),
            "response_key_count": len(keys),
            "response_keys": keys,
        }

    def _runtime_response_metadata_summary(self, *, payload: dict[str, Any]) -> dict[str, Any]:
        if "runtime_execution" in payload:
            execution = RuntimeExecutionResult.model_validate(payload["runtime_execution"])
            return self._response_metadata_summary(
                response_metadata=execution.response_metadata,
                response_keys=execution.response_keys,
            )
        if "runtime_summary" in payload:
            summary = payload["runtime_summary"]
            return self._response_metadata_summary(
                response_metadata=summary.get("response_metadata", {}),
                response_keys=summary.get("response_keys", []),
            )
        return self._response_metadata_summary(response_metadata={}, response_keys=[])

    def _review_target_response_metadata_summary(self, target_event_id: str) -> dict[str, Any]:
        event = next(
            (item for item in self.chronicle.jsonl.read_all() if item.event_id == target_event_id),
            None,
        )
        if event is None:
            return self._response_metadata_summary(response_metadata={}, response_keys=[])
        payload = getattr(event, "payload", {})
        if not isinstance(payload, dict):
            return self._response_metadata_summary(response_metadata={}, response_keys=[])
        return self._runtime_response_metadata_summary(payload=payload)

    def ui_boundary(self) -> dict[str, Any]:
        metadata = build_ui_boundary_metadata(
            host=self.host,
            mutation_capability_flag=self.mutation_capability_flag,
            enable_ui_mutation=self.enable_ui_mutation,
            auth_mode=self.auth_mode,
            authorization_mode=self.authorization_mode,
        )
        return {"ui_boundary": asdict(metadata)}

    @staticmethod
    def _auth_boundary_notice(
        boundary: dict[str, Any],
        capability: dict[str, Any] | None,
        assurance: dict[str, Any] | None,
    ) -> dict[str, Any]:
        capability = capability or {}
        assurance = assurance or {}
        warnings = [str(item) for item in capability.get("warnings", [])]
        blockers: list[str] = []
        next_steps: list[str] = []

        for warning in warnings:
            blocker_code = AUTH_BOUNDARY_WARNING_TO_BLOCKER.get(warning)
            if blocker_code is None:
                continue
            _append_auth_boundary_blocker(blockers, next_steps, blocker_code)

        assurance_status = str(assurance.get("status", "unknown"))
        capability_status = str(capability.get("status", "unknown"))
        if capability_status == "ready" and assurance_status == "boundary_aligned" and not blockers:
            status = "boundary_aligned"
            message = "Current review metadata is aligned with the preview auth boundary, while GUI mutation remains disabled."
        elif blockers:
            status = "advisory_only"
            message = "Current review metadata remains advisory only until auth, authorization, and reviewer identity boundaries are explicit."
        elif assurance_status != "unknown":
            status = assurance_status
            message = "Some reviewer identity metadata is present, but auth-boundary alignment remains incomplete."
        else:
            status = capability_status
            message = "Auth-boundary readiness is not yet available in the current derived detail view."

        return {
            "status": status,
            "message": message,
            "blockers": blockers,
            "blocker_details": _serialize_auth_boundary_blocker_details(blockers),
            "next_steps": next_steps,
            "capability_status": capability_status,
            "identity_assurance_status": assurance_status,
        }

    def _review_queue_row(self, target_event_id: str) -> dict[str, Any] | None:
        for row in self.review_queue()["review_queue"]:
            if row.get("target_event_id") == target_event_id:
                return row
        return None

    def _review_queue_row_including_resolved(self, target_event_id: str) -> dict[str, Any] | None:
        boundary = self.ui_boundary()["ui_boundary"]
        for entry in self.review.queue(include_resolved=True):
            if entry.target_event_id != target_event_id:
                continue
            data = entry.model_dump(mode="json")
            data["review_capability"] = self._review_capability(
                pending=bool(data.get("pending")),
                boundary=boundary,
                identity=(
                    ReviewerIdentity.model_validate(data["latest_reviewer_identity"])
                    if data.get("latest_reviewer_identity") is not None
                    else None
                ),
            )
            return data
        return None

    @staticmethod
    def _review_kind(payload: dict[str, Any]) -> str:
        if "runtime_summary" in payload:
            return "runtime_summary"
        if "runtime_retrieval_plan" in payload:
            return "runtime_retrieval_plan"
        if "runtime_invocation_plan" in payload:
            return "runtime_invocation_plan"
        return "assistant_output"

    @staticmethod
    def _suggested_cli_family(payload: dict[str, Any]) -> str:
        if "runtime_summary" in payload:
            return "chronicle runtime summarize --record"
        if "runtime_retrieval_plan" in payload:
            return "chronicle runtime retrieve-plan --record"
        if "runtime_invocation_plan" in payload:
            return "chronicle runtime invoke-plan --record"
        return "chronicle show --json"

    @staticmethod
    def _suggested_cli_family_from_kind(review_kind: str) -> str:
        if review_kind == "runtime_summary":
            return "chronicle runtime summarize --record"
        if review_kind == "runtime_retrieval_plan":
            return "chronicle runtime retrieve-plan --record"
        if review_kind == "runtime_invocation_plan":
            return "chronicle runtime invoke-plan --record"
        return "chronicle show --json"

    @staticmethod
    def _identity_assurance(identity: ReviewerIdentity, boundary: dict[str, Any]) -> dict[str, Any]:
        boundary_auth_mode = boundary.get("auth_mode", "not_enabled")
        session_gating = bool(boundary.get("session_gating", False))
        if identity.auth_mode.value == "none":
            status = "declared_only"
            message = "Reviewer identity is self-declared only; UI auth is not enforcing reviewer identity."
        elif boundary_auth_mode == "not_enabled":
            status = "local_session_unverified"
            message = "Reviewer identity carries local session metadata, but UI auth/authz is not enabled."
        else:
            status = "boundary_aligned"
            message = "Reviewer identity metadata is aligned with the current UI auth boundary."
        return {
            "status": status,
            "reviewer_auth_mode": identity.auth_mode.value,
            "boundary_auth_mode": boundary_auth_mode,
            "session_gating": session_gating,
            "message": message,
        }

    def _review_capability(
        self,
        *,
        pending: bool,
        boundary: dict[str, Any],
        identity: ReviewerIdentity | None,
    ) -> dict[str, Any]:
        if not pending:
            return {
                "status": "resolved",
                "can_review_now": False,
                "warnings": [],
                "message": "Review target is already resolved in the current derived queue view.",
            }

        warnings: list[str] = []
        auth_mode = boundary.get("auth_mode", UIAuthMode.NOT_ENABLED)
        authorization_mode = boundary.get("authorization_mode", UIAuthorizationMode.NOT_ENABLED)
        session_gating = bool(boundary.get("session_gating", False))

        if auth_mode == UIAuthMode.NOT_ENABLED:
            warnings.append("ui_auth_not_enabled")
        if authorization_mode == UIAuthorizationMode.NOT_ENABLED:
            warnings.append("ui_authorization_not_enabled")
        if identity is None:
            warnings.append("no_reviewer_identity_recorded")
        elif identity.kind.value == "user_declared":
            warnings.append("reviewer_identity_declared_only")
        elif session_gating and identity.session_label is None:
            warnings.append("reviewer_session_label_missing")

        can_review_now = len(warnings) == 0
        message = (
            "Boundary and reviewer identity conditions are aligned for future mutation-capable review."
            if can_review_now
            else "Review remains CLI-led and read-only in UI; see warnings for unmet boundary conditions."
        )
        return {
            "status": "ready" if can_review_now else "advisory_only",
            "can_review_now": can_review_now,
            "warnings": warnings,
            "warning_details": _serialize_review_warning_details(warnings),
            "message": message,
        }

    def _history_row(self, item: Any, boundary: dict[str, Any]) -> dict[str, Any]:
        data = item.model_dump(mode="json")
        data["identity_assurance"] = self._identity_assurance(item.reviewer_identity, boundary)
        return data

    @staticmethod
    def _package_readiness_summary(readiness: dict[str, Any]) -> dict[str, Any]:
        package_review = readiness.get("package_review", {})
        status = str(readiness.get("status", "unknown"))
        review_status = str(package_review.get("status", "not_available"))
        eligible_context_ids = readiness.get("eligible_context_ids", [])
        warnings = package_review.get("package_warnings", [])

        if status == "package_context_available":
            label = f"package:{review_status}"
            message = (
                f"Package preview available for {len(eligible_context_ids)} context record(s); "
                f"review status is {review_status}."
            )
        elif status == "no_context_records":
            label = "package:advisory"
            message = "No context-linked records available for package/export preview."
        else:
            label = f"package:{status}"
            message = str(readiness.get("message", "Package readiness unavailable."))

        return {
            "status": status,
            "review_status": review_status,
            "eligible_context_count": len(eligible_context_ids) if isinstance(eligible_context_ids, list) else 0,
            "warning_count": len(warnings) if isinstance(warnings, list) else 0,
            "label": label,
            "message": message,
        }

    @staticmethod
    def _review_recovery_commands(
        *,
        event_id: str | None = None,
        action: str | None = None,
        error_code: str | None = None,
        audit_id: str | None = None,
    ) -> list[str]:
        cli_equivalent = (
            f"chronicle review {action} --event {event_id}"
            if event_id and action
            else ""
        )
        commands: list[str] = []
        if error_code == "review_not_pending":
            commands.extend([
                "chronicle review queue --include-resolved --json",
                cli_equivalent,
            ])
        elif error_code == "review_target_not_found":
            commands.extend([
                "chronicle review queue --include-resolved --json",
                cli_equivalent,
            ])
        elif error_code == "authorization_failed":
            commands.extend([
                "chronicle review queue --json",
                cli_equivalent,
            ])
        elif error_code == "audit_insertion_failed":
            commands.extend([
                cli_equivalent,
                "chronicle audit list --json",
            ])
        elif error_code == "decision_persistence_failed":
            commands.extend([
                "chronicle review queue --include-resolved --json",
                f"chronicle audit show --id {audit_id} --json" if audit_id else "",
                "chronicle audit list --json",
                cli_equivalent,
            ])
        else:
            commands.append(cli_equivalent)
        return [command for index, command in enumerate(commands) if command and command not in commands[:index]]

    @staticmethod
    def _warning_message(code: str) -> str:
        return REVIEW_WARNING_TEXT.get(code, code.replace("_", " "))

    @staticmethod
    def _warning_label(code: str) -> str:
        return REVIEW_WARNING_LABELS.get(code, code.replace("_", " "))

    @staticmethod
    def _review_action_failure_contract(
        *,
        mutation_enabled: bool,
        cli_equivalent: str | None = None,
        event_id: str | None = None,
        action: str | None = None,
        error_code: str | None = None,
        audit_id: str | None = None,
    ) -> dict[str, Any]:
        possible_error_codes = [
            "mutation_disabled",
            "reviewer_label_required",
            "invalid_reviewer_label",
            "session_label_required",
            "invalid_session_label",
            "ui_intent_mismatch",
            "invalid_reviewer_kind",
            "authorization_failed",
            "review_target_not_found",
            "review_not_pending",
            "invalid_json",
        ]
        recovery_commands = ChronicleUIDataService._review_recovery_commands(
            event_id=event_id,
            action=action,
            error_code=error_code,
            audit_id=audit_id,
        )
        return {
            "transaction_rule": (
                "No durable GUI review result is reported as applied unless both review decision persistence and audit insertion succeed."
            ),
            "rollback_status": "fail_closed",
            "durable_mutation_reported_on_failure": False,
            "partial_failure_visible": True,
            "possible_error_codes": possible_error_codes,
            "recovery_path": (
                recovery_commands[0]
                if recovery_commands
                else cli_equivalent or "Use the equivalent chronicle review CLI command for recovery or inspection."
            ),
            "recovery_commands": recovery_commands,
        }

    @staticmethod
    def _review_action_failure_message(error_code: str) -> str:
        messages = {
            "mutation_disabled": "GUI mutation remains disabled for this session; use the CLI review path instead.",
            "reviewer_label_required": "Reviewer label is missing, so the UI cannot attribute the review action.",
            "invalid_reviewer_label": "Reviewer label must start with a lowercase letter or digit and use only lowercase letters, digits, dot, underscore, or hyphen.",
            "session_label_required": "Session label is required for the current session-gated local mutation boundary.",
            "invalid_session_label": "Session label must start with a lowercase letter or digit and use only lowercase letters, digits, dot, underscore, or hyphen.",
            "ui_intent_mismatch": "Requested route and submitted UI intent differ, so the action was rejected before mutation.",
            "invalid_reviewer_kind": "Reviewer kind is not one of the supported local reviewer identity kinds.",
            "authorization_failed": "Reviewer identity or session boundary is not aligned, so the action stays blocked.",
            "review_target_not_found": "The target review event is no longer available from the current Chronicle state.",
            "review_not_pending": "The review target is no longer pending; inspect the resolved queue before retrying.",
            "invalid_json": "The request body could not be parsed as JSON, so no mutation path was attempted.",
            "audit_insertion_failed": "Audit insertion failed before the review decision could be reported as applied.",
            "decision_persistence_failed": "Audit insertion succeeded, but the Chronicle primary-record append failed, so treat the route as fail-closed.",
        }
        return messages.get(error_code, error_code.replace("_", " "))

    @staticmethod
    def _review_action_failure_summary(
        *,
        error_code: str,
        warning_codes: list[str] | None = None,
        identity_assurance_status: str | None = None,
    ) -> str:
        if error_code == "authorization_failed":
            warning_text = " | ".join(
                ChronicleUIDataService._warning_message(code)
                for code in (warning_codes or [])
                if code
            )
            if warning_text and identity_assurance_status:
                return f"authorization_failed; identity={identity_assurance_status}; warnings={warning_text}"
            if identity_assurance_status:
                return f"authorization_failed; identity={identity_assurance_status}"
            if warning_text:
                return f"authorization_failed; warnings={warning_text}"
        if error_code == "review_not_pending":
            return "review_not_pending; inspect resolved queue state before retry"
        if error_code == "audit_insertion_failed":
            return "audit_insertion_failed; inspect local audit surface before retry"
        if error_code == "decision_persistence_failed":
            return "decision_persistence_failed; inspect audit trail and primary record state"
        return error_code

    @staticmethod
    def _review_action_success_contract(
        *,
        cli_equivalent: str | None = None,
        event_id: str | None = None,
        audit_id: str | None = None,
    ) -> dict[str, Any]:
        follow_up_commands = [
            command
            for command in [
                "chronicle review queue --include-resolved --json" if event_id else "",
                f"chronicle audit show --id {audit_id} --json" if audit_id else "",
                cli_equivalent or "",
            ]
            if command
        ]
        return {
            "transaction_status": "decision_and_audit_persisted",
            "rollback_status": "not_required",
            "durable_mutation_reported": True,
            "audit_insertion_required": True,
            "recovery_path": follow_up_commands[0] if follow_up_commands else cli_equivalent or "Use the equivalent chronicle review CLI command for follow-up inspection.",
            "follow_up_commands": follow_up_commands,
        }

    @staticmethod
    def _review_action_preview(
        target_event_id: str,
        capability: dict[str, Any],
        *,
        mutation_enabled: bool = False,
        write_route_contract: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        can_review_now = bool(capability.get("can_review_now", False))
        actions = []
        for item in review_action_commands(target_event_id):
            route_action = str(item.get("action", "")).replace("_", "-")
            actions.append(
                {
                    **item,
                    "post_path": (
                        f"/api/review-actions/{quote(target_event_id, safe='')}/{quote(route_action, safe='')}"
                    ),
                    "post_expected_status": (
                        HTTPStatus.OK.value if mutation_enabled else HTTPStatus.FORBIDDEN.value
                    ),
                    "post_expected_error_code": (None if mutation_enabled else "mutation_disabled"),
                }
            )
        return {
            "status": "enabled" if mutation_enabled else "preview_only",
            "ui_mutation_enabled": mutation_enabled,
            "can_review_now": can_review_now,
            "message": (
                (
                    "UI mutation is enabled for this local session; review actions still require explicit reviewer context."
                    if can_review_now
                    else "UI mutation is enabled, but boundary warnings still block review until reviewer context aligns."
                )
                if mutation_enabled
                else (
                    "UI mutation is not enabled; use the equivalent CLI command."
                    if can_review_now
                    else "UI mutation is not enabled; boundary warnings still require CLI-led review."
                )
            ),
            "failure_contract": ChronicleUIDataService._review_action_failure_contract(
                mutation_enabled=mutation_enabled,
                cli_equivalent=f"chronicle review approve --event {target_event_id}",
                event_id=target_event_id,
                action="approve",
                error_code="mutation_disabled",
            ),
            "success_contract": ChronicleUIDataService._review_action_success_contract(
                cli_equivalent=f"chronicle review approve --event {target_event_id}",
                event_id=target_event_id,
                audit_id=None,
            ),
            "write_route_contract": write_route_contract or {},
            "actions": actions,
        }

    @staticmethod
    def _review_cli_parity_summary(
        target_event_id: str,
        available_actions: list[str],
        action_preview: dict[str, Any],
    ) -> dict[str, Any]:
        preview_actions = action_preview.get("actions", [])
        preview_commands = [
            str(item.get("command", ""))
            for item in preview_actions
            if isinstance(item, dict) and item.get("command")
        ]
        canonical_actions = review_action_commands(target_event_id)
        expected_commands = [item["command"] for item in canonical_actions]
        expected_action_ids = [item["action"] for item in canonical_actions]
        queue_commands = [command for command in available_actions if isinstance(command, str)]
        missing_preview_commands = [
            command for command in expected_commands if command not in preview_commands
        ]
        missing_queue_commands = [
            command for command in expected_commands if command not in queue_commands
        ]
        extra_preview_commands = [
            command for command in preview_commands if command not in expected_commands
        ]
        extra_queue_commands = [command for command in queue_commands if command not in expected_commands]
        aligned = (
            not missing_preview_commands
            and not missing_queue_commands
            and not extra_preview_commands
            and not extra_queue_commands
        )
        return {
            "status": "aligned" if aligned else "drift_detected",
            "preview_only": True,
            "expected_actions": expected_action_ids,
            "expected_commands": expected_commands,
            "preview_command_count": len(preview_commands),
            "queue_command_count": len(queue_commands),
            "missing_preview_commands": missing_preview_commands,
            "missing_queue_commands": missing_queue_commands,
            "extra_preview_commands": extra_preview_commands,
            "extra_queue_commands": extra_queue_commands,
            "message": (
                "UI preview commands match the current append-only review CLI contract."
                if aligned
                else "UI preview commands drifted from the append-only review CLI contract."
            ),
        }

    def detail_payload(self, path: str) -> dict[str, Any] | None:
        parts = [unquote(part) for part in path.strip("/").split("/")]
        if len(parts) == 4 and parts[0] == "api" and parts[1] == "ai-index":
            resource, record_id = parts[2], parts[3]
            if resource == "vector":
                entry = self.vector_index.get_entry(record_id)
                return {"record": _dump_model(entry)} if entry is not None else None
            if resource == "graph-nodes":
                node = self.graph_index.get_node(record_id)
                if node is None:
                    return None
                payload = _dump_model(node)
                neighbors = self.graph_index.neighbors(node_id=record_id)
                payload["neighbors"] = neighbors.model_dump(mode="json")
                return {"record": payload}
            return None

        if len(parts) == 3 and parts[0] == "api" and parts[1] == "runtime-records":
            self.chronicle.require_initialized()
            event = next(
                (item for item in self.chronicle.jsonl.read_all() if item.event_id == parts[2]),
                None,
            )
            if event is None:
                return None
            record = _dump_model(event)
            payload = record["payload"]
            if (
                "runtime_summary" not in payload
                and "runtime_execution" not in payload
                and "runtime_retrieval_plan" not in payload
                and "runtime_invocation_plan" not in payload
            ):
                return None
            preview = self.runtime.record_preview(event)
            record["runtime_record_kind"] = preview.record_kind
            record["runtime_record_preview"] = preview.model_dump(mode="json")
            record["suggested_cli_family"] = preview.suggested_cli_family
            record["related_links"] = self.runtime_related_links(parts[2], payload)
            record["response_metadata_summary"] = self._runtime_response_metadata_summary(payload=payload)
            review_row = self._review_queue_row(parts[2])
            if review_row is not None:
                record["auth_boundary_notice"] = review_row.get("auth_boundary_notice")
                record["mutation_enablement"] = self.mutation_readiness_summary()
                record["auth_readiness_status"] = str(
                    review_row.get("auth_boundary_notice", {}).get("status", "")
                )
            if "runtime_retrieval_plan" in payload:
                plan = RuntimeRetrievalPlan.model_validate(payload["runtime_retrieval_plan"])
                record["retrieval_handoff"] = self.runtime.retrieval_handoff(plan).model_dump(mode="json")
                record["package_handoff_preview"] = self.runtime_package_handoff(plan)
            if "runtime_invocation_plan" in payload:
                plan = RuntimeInvocationPlan.model_validate(payload["runtime_invocation_plan"])
                record["invocation_plan"] = plan.model_dump(mode="json")
            return {"record": record}

        if len(parts) == 3 and parts[0] == "api" and parts[1] == "review-queue":
            boundary = self.ui_boundary()["ui_boundary"]
            for row in self.review_queue()["review_queue"]:
                if row.get("target_event_id") == parts[2]:
                    row["history"] = [
                        self._history_row(item, boundary)
                        for item in self.review.history(event_id=parts[2])
                    ]
                    row["package_readiness"] = self.review_package_readiness(parts[2])
                    row["related_links"] = self.review_related_links(parts[2])
                    row["action_preview"] = self._review_action_preview(
                        parts[2],
                        row.get("review_capability", {}),
                        mutation_enabled=bool(boundary.get("mutation_enabled", False)),
                        write_route_contract=boundary.get("write_route_contract", {}),
                    )
                    row["cli_parity"] = self._review_cli_parity_summary(
                        parts[2],
                        row.get("available_actions", []),
                        row["action_preview"],
                    )
                    row["auth_boundary_notice"] = self._auth_boundary_notice(
                        boundary,
                        row.get("review_capability"),
                        row.get("latest_identity_assurance"),
                    )
                    row["mutation_enablement"] = self.mutation_readiness_summary()
                    row["ui_mutation_enabled"] = bool(boundary.get("mutation_enabled", False))
                    row["review_preview_only"] = not bool(boundary.get("mutation_enabled", False))
                    return {"record": row}
            return None

        if len(parts) == 3 and parts[0] == "api" and parts[1] == "summary-jobs":
            job = self.summary_jobs.get(parts[2]).model_dump(mode="json")
            job["summary_source_count"] = len(job.get("source_refs", []))
            job["runtime_provider_kind"] = str(job.get("provenance", {}).get("runtime", {}).get("provider_kind", ""))
            job["response_metadata_summary"] = self._response_metadata_summary(
                response_metadata=job.get("provenance", {}).get("response_metadata", {}),
                response_keys=job.get("provenance", {}).get("response_keys", []),
            )
            job["suggested_cli_family"] = "chronicle summary show --id"
            job["identity_assurance_status"] = "unknown"
            event_id = str(job.get("event_id", ""))
            if event_id.startswith("evt_"):
                review_row = self._review_queue_row(event_id)
                if review_row is not None:
                    boundary = self.ui_boundary()["ui_boundary"]
                    job["review_target_event_id"] = event_id
                    job["review_kind"] = review_row.get("review_kind")
                    job["review_capability"] = review_row.get("review_capability")
                    if review_row.get("latest_identity_assurance") is not None:
                        job["latest_identity_assurance"] = review_row.get("latest_identity_assurance")
                        job["identity_assurance_status"] = str(
                            review_row.get("latest_identity_assurance", {}).get("status", "")
                        )
                    if review_row.get("latest_reviewer_identity") is not None:
                        job["latest_reviewer_identity"] = review_row.get("latest_reviewer_identity")
                    job["package_readiness_summary"] = review_row.get("package_readiness_summary")
                    job["package_readiness"] = self.review_package_readiness(event_id)
                    job["action_preview"] = self._review_action_preview(
                        event_id,
                        job["review_capability"],
                        mutation_enabled=bool(boundary.get("mutation_enabled", False)),
                        write_route_contract=boundary.get("write_route_contract", {}),
                    )
                    job["cli_parity"] = self._review_cli_parity_summary(
                        event_id,
                        review_row.get("available_actions", []),
                        job["action_preview"],
                    )
                    job["auth_boundary_notice"] = self._auth_boundary_notice(
                        boundary,
                        job.get("review_capability"),
                        job.get("latest_identity_assurance"),
                    )
                    job["mutation_enablement"] = self.mutation_readiness_summary()
                    job["history"] = [
                        self._history_row(item, boundary)
                        for item in self.review.history(event_id=event_id)
                    ]
                    job["ui_mutation_enabled"] = bool(boundary.get("mutation_enabled", False))
                    job["review_preview_only"] = not bool(boundary.get("mutation_enabled", False))
            job["related_links"] = self.summary_job_related_links(parts[2], job)
            return {"record": job}

        if len(parts) != 3 or parts[0] != "api":
            return None
        resource, record_id = parts[1], parts[2]
        self.chronicle.require_initialized()
        if resource == "events":
            record = _find_by_attr(self.chronicle.jsonl.read_all(), "event_id", record_id)
        elif resource == "contexts":
            contexts = self.chronicle.index.load_contexts()
            record = _dump_model(contexts[record_id]) if record_id in contexts else None
        elif resource == "artifacts":
            artifacts, versions = self.chronicle.index.load_artifacts()
            record = _dump_model(artifacts[record_id]) if record_id in artifacts else None
            if record is not None:
                record["versions"] = [_dump_model(version) for version in versions.get(record_id, [])]
        elif resource == "decisions":
            decisions = self.chronicle.index.load_decisions()
            record = _dump_model(decisions[record_id]) if record_id in decisions else None
        elif resource == "rde":
            records = self.chronicle.index.load_rde_records()
            record = _dump_model(records[record_id]) if record_id in records else None
        elif resource == "boundary":
            rules = self.chronicle.index.load_boundary_rules()
            record = _dump_model(rules[record_id]) if record_id in rules else None
        elif resource == "audit":
            record = _find_by_attr(self.audit.list_events(), "audit_id", record_id)
        elif resource == "lifecycle":
            record = _find_by_attr(self.lifecycle.list_events(), "lifecycle_id", record_id)
        else:
            return None
        return {"record": record} if record is not None else None

    def api_payload(self, path: str) -> dict[str, Any] | None:
        routes = {
            "/api/overview": self.overview,
            "/api/events": self.events,
            "/api/contexts": self.contexts,
            "/api/artifacts": self.artifacts,
            "/api/decisions": self.decisions,
            "/api/rde": self.rde_records,
            "/api/boundary": self.boundary_rules,
            "/api/audit": self.audit_events,
            "/api/lifecycle": self.lifecycle_markers,
            "/api/runtime-records": self.runtime_records,
            "/api/review-queue": self.review_queue,
            "/api/summary-jobs": self.summary_jobs_list,
            "/api/ui-boundary": self.ui_boundary,
            "/api/runtime-config": self.runtime_config_state,
            "/api/package-review": lambda: {"package_review": self.package_review_snapshot()},
            "/api/graph-summary": lambda: {"graph_summary": self.graph_summary()},
            "/api/ai-index-status": self.ai_index_status,
            "/api/ai-index-vector": self.ai_index_vector_entries,
            "/api/ai-index-graph-nodes": self.ai_index_graph_nodes,
            "/api/ai-index-graph-edges": self.ai_index_graph_edges,
        }
        handler = routes.get(path)
        if handler:
            return handler()
        return self.detail_payload(path)

    def review_action_blocked_response(self, path: str) -> tuple[HTTPStatus, dict[str, Any]] | None:
        parts = [unquote(part) for part in path.strip("/").split("/")]
        if len(parts) != 4 or parts[0] != "api" or parts[1] != "review-actions":
            return None
        event_id, action = parts[2], parts[3]
        if action not in {"approve", "reject", "request-changes"}:
            return None
        return (
            HTTPStatus.FORBIDDEN,
            {
                "ok": False,
                "status": "blocked",
                "event_id": event_id,
                "action": action,
                "error_code": "mutation_disabled",
                "message": self._review_action_failure_message("mutation_disabled"),
                "mutation_enabled": False,
                "cli_equivalent": f"chronicle review {action} --event {event_id}",
                "failure_contract": self._review_action_failure_contract(
                    mutation_enabled=False,
                    cli_equivalent=f"chronicle review {action} --event {event_id}",
                    event_id=event_id,
                    action=action,
                    error_code="mutation_disabled",
                ),
            },
        )

    def review_action_response(
        self,
        path: str,
        payload: dict[str, Any],
    ) -> tuple[HTTPStatus, dict[str, Any]] | None:
        parts = [unquote(part) for part in path.strip("/").split("/")]
        if len(parts) != 4 or parts[0] != "api" or parts[1] != "review-actions":
            return None
        event_id, action = parts[2], parts[3]
        action_map = {
            "approve": self.review.approve,
            "reject": self.review.reject,
            "request-changes": self.review.request_changes,
        }
        review_action = action_map.get(action)
        if review_action is None:
            return None

        boundary = self.ui_boundary()["ui_boundary"]
        reviewer_context_requirements = boundary.get("reviewer_context_requirements", {})
        if not boundary.get("mutation_enabled", False):
            return self.review_action_blocked_response(path)

        reviewer_label = str(payload.get("reviewer_label", "")).strip()
        reviewer_kind_value = str(payload.get("reviewer_kind", ReviewerIdentityKind.USER_DECLARED.value))
        session_label = payload.get("session_label")
        session_label_value = str(session_label).strip() if isinstance(session_label, str) else None
        note = payload.get("note")
        note_value = str(note).strip() if isinstance(note, str) and str(note).strip() else None
        ui_intent = str(payload.get("ui_intent", "")).strip()

        if not reviewer_label:
            return (
                HTTPStatus.BAD_REQUEST,
                {
                    "ok": False,
                    "status": "blocked",
                    "event_id": event_id,
                    "action": action,
                    "error_code": "reviewer_label_required",
                    "message": self._review_action_failure_message("reviewer_label_required"),
                    "mutation_enabled": True,
                    "reviewer_context_requirements": reviewer_context_requirements,
                    "failure_contract": self._review_action_failure_contract(
                        mutation_enabled=True,
                        cli_equivalent=f"chronicle review {action} --event {event_id}",
                        event_id=event_id,
                        action=action,
                        error_code="reviewer_label_required",
                    ),
                },
            )
        if not REVIEWER_LABEL_PATTERN.fullmatch(reviewer_label):
            return (
                HTTPStatus.BAD_REQUEST,
                {
                    "ok": False,
                    "status": "blocked",
                    "event_id": event_id,
                    "action": action,
                    "error_code": "invalid_reviewer_label",
                    "message": self._review_action_failure_message("invalid_reviewer_label"),
                    "mutation_enabled": True,
                    "reviewer_context_requirements": reviewer_context_requirements,
                    "failure_contract": self._review_action_failure_contract(
                        mutation_enabled=True,
                        cli_equivalent=f"chronicle review {action} --event {event_id}",
                        event_id=event_id,
                        action=action,
                        error_code="invalid_reviewer_label",
                    ),
                },
            )
        if boundary.get("session_gating", False) and not session_label_value:
            return (
                HTTPStatus.BAD_REQUEST,
                {
                    "ok": False,
                    "status": "blocked",
                    "event_id": event_id,
                    "action": action,
                    "error_code": "session_label_required",
                    "message": self._review_action_failure_message("session_label_required"),
                    "mutation_enabled": True,
                    "reviewer_context_requirements": reviewer_context_requirements,
                    "failure_contract": self._review_action_failure_contract(
                        mutation_enabled=True,
                        cli_equivalent=f"chronicle review {action} --event {event_id}",
                        event_id=event_id,
                        action=action,
                        error_code="session_label_required",
                    ),
                },
            )
        if session_label_value and not SESSION_LABEL_PATTERN.fullmatch(session_label_value):
            return (
                HTTPStatus.BAD_REQUEST,
                {
                    "ok": False,
                    "status": "blocked",
                    "event_id": event_id,
                    "action": action,
                    "error_code": "invalid_session_label",
                    "message": self._review_action_failure_message("invalid_session_label"),
                    "mutation_enabled": True,
                    "reviewer_context_requirements": reviewer_context_requirements,
                    "failure_contract": self._review_action_failure_contract(
                        mutation_enabled=True,
                        cli_equivalent=f"chronicle review {action} --event {event_id}",
                        event_id=event_id,
                        action=action,
                        error_code="invalid_session_label",
                    ),
                },
            )
        if ui_intent != action:
            return (
                HTTPStatus.BAD_REQUEST,
                {
                    "ok": False,
                    "status": "blocked",
                    "event_id": event_id,
                    "action": action,
                    "error_code": "ui_intent_mismatch",
                    "message": self._review_action_failure_message("ui_intent_mismatch"),
                    "mutation_enabled": True,
                    "reviewer_context_requirements": reviewer_context_requirements,
                    "failure_contract": self._review_action_failure_contract(
                        mutation_enabled=True,
                        cli_equivalent=f"chronicle review {action} --event {event_id}",
                        event_id=event_id,
                        action=action,
                        error_code="ui_intent_mismatch",
                    ),
                },
            )
        try:
            reviewer_kind = ReviewerIdentityKind(reviewer_kind_value)
        except ValueError:
            return (
                HTTPStatus.BAD_REQUEST,
                {
                    "ok": False,
                    "status": "blocked",
                    "event_id": event_id,
                    "action": action,
                    "error_code": "invalid_reviewer_kind",
                    "message": self._review_action_failure_message("invalid_reviewer_kind"),
                    "mutation_enabled": True,
                    "reviewer_context_requirements": reviewer_context_requirements,
                    "failure_contract": self._review_action_failure_contract(
                        mutation_enabled=True,
                        cli_equivalent=f"chronicle review {action} --event {event_id}",
                        event_id=event_id,
                        action=action,
                        error_code="invalid_reviewer_kind",
                    ),
                },
            )

        reviewer_identity = ReviewerIdentity(
            label=reviewer_label,
            kind=reviewer_kind,
            auth_mode="loopback_local",
            session_label=session_label_value,
        )
        capability = self._review_capability(
            pending=True,
            boundary=boundary,
            identity=reviewer_identity,
        )
        assurance = self._identity_assurance(reviewer_identity, boundary)
        if capability.get("can_review_now") is not True or assurance.get("status") != "boundary_aligned":
            return (
                HTTPStatus.FORBIDDEN,
                {
                    "ok": False,
                    "status": "blocked",
                    "event_id": event_id,
                    "action": action,
                    "error_code": "authorization_failed",
                    "message": self._review_action_failure_message("authorization_failed"),
                    "mutation_enabled": True,
                    "warning_codes": capability.get("warnings", []),
                    "warning_details": capability.get("warning_details", []),
                    "identity_assurance_status": assurance.get("status"),
                    "identity_assurance_message": assurance.get("message"),
                    "reviewer_context_requirements": reviewer_context_requirements,
                    "failure_summary": self._review_action_failure_summary(
                        error_code="authorization_failed",
                        warning_codes=capability.get("warnings", []),
                        identity_assurance_status=str(assurance.get("status", "")),
                    ),
                    "cli_equivalent": f"chronicle review {action} --event {event_id}",
                    "failure_contract": self._review_action_failure_contract(
                        mutation_enabled=True,
                        cli_equivalent=f"chronicle review {action} --event {event_id}",
                        event_id=event_id,
                        action=action,
                        error_code="authorization_failed",
                    ),
                },
            )

        review_row = self._review_queue_row_including_resolved(event_id)
        if review_row is None:
            return (
                HTTPStatus.NOT_FOUND,
                {
                    "ok": False,
                    "status": "blocked",
                    "event_id": event_id,
                    "action": action,
                    "error_code": "review_target_not_found",
                    "message": self._review_action_failure_message("review_target_not_found"),
                    "mutation_enabled": True,
                    "failure_contract": self._review_action_failure_contract(
                        mutation_enabled=True,
                        cli_equivalent=f"chronicle review {action} --event {event_id}",
                        event_id=event_id,
                        action=action,
                        error_code="review_target_not_found",
                    ),
                },
            )
        if review_row.get("pending") is not True:
            return (
                HTTPStatus.CONFLICT,
                {
                    "ok": False,
                    "status": "blocked",
                    "event_id": event_id,
                    "action": action,
                    "error_code": "review_not_pending",
                    "message": self._review_action_failure_message("review_not_pending"),
                    "mutation_enabled": True,
                    "failure_summary": self._review_action_failure_summary(
                        error_code="review_not_pending",
                    ),
                    "cli_equivalent": f"chronicle review {action} --event {event_id}",
                    "failure_contract": self._review_action_failure_contract(
                        mutation_enabled=True,
                        cli_equivalent=f"chronicle review {action} --event {event_id}",
                        event_id=event_id,
                        action=action,
                        error_code="review_not_pending",
                    ),
                },
            )

        try:
            result = review_action(
                event_id=event_id,
                reviewer=reviewer_label,
                reviewer_kind=reviewer_kind,
                session_label=session_label_value,
                note=note_value,
            )
        except ReviewAuditInsertionError as exc:
            return (
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {
                    "ok": False,
                    "status": "blocked",
                    "event_id": event_id,
                    "action": action,
                    "error_code": "audit_insertion_failed",
                    "message": self._review_action_failure_message("audit_insertion_failed"),
                    "mutation_enabled": True,
                    "detail": exc.hint,
                    "failure_summary": self._review_action_failure_summary(
                        error_code="audit_insertion_failed",
                    ),
                    "cli_equivalent": f"chronicle review {action} --event {event_id}",
                    "failure_contract": self._review_action_failure_contract(
                        mutation_enabled=True,
                        cli_equivalent=f"chronicle review {action} --event {event_id}",
                        event_id=event_id,
                        action=action,
                        error_code="audit_insertion_failed",
                    ),
                },
            )
        except ReviewDecisionPersistenceError as exc:
            return (
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {
                    "ok": False,
                    "status": "blocked",
                    "event_id": event_id,
                    "action": action,
                    "error_code": "decision_persistence_failed",
                    "message": self._review_action_failure_message("decision_persistence_failed"),
                    "mutation_enabled": True,
                    "detail": exc.hint,
                    "audit_id": exc.audit_id,
                    "failure_summary": self._review_action_failure_summary(
                        error_code="decision_persistence_failed",
                    ),
                    "cli_equivalent": f"chronicle review {action} --event {event_id}",
                    "failure_contract": self._review_action_failure_contract(
                        mutation_enabled=True,
                        cli_equivalent=f"chronicle review {action} --event {event_id}",
                        event_id=event_id,
                        action=action,
                        error_code="decision_persistence_failed",
                        audit_id=exc.audit_id,
                    ),
                },
            )
        return (
            HTTPStatus.OK,
            {
                "ok": True,
                "status": "applied",
                "event_id": event_id,
                "action": action,
                "audit_id": result.audit_id,
                "decision_event_id": result.review_event_id,
                "cli_equivalent": f"chronicle review {action} --event {event_id}",
                "mutation_enabled": True,
                "reviewer_identity": result.reviewer_identity.model_dump(mode="json"),
                "success_contract": self._review_action_success_contract(
                    cli_equivalent=f"chronicle review {action} --event {event_id}",
                    event_id=event_id,
                    audit_id=result.audit_id,
                ),
            },
        )

    def html_shell(self) -> str:
        metadata = self.chronicle.require_initialized()
        title = html.escape(metadata.title)
        root = html.escape(str(self.root.resolve()))
        review_warning_labels_json = json.dumps(REVIEW_WARNING_LABELS, ensure_ascii=False)
        ui_i18n_catalog_json = json.dumps(UI_I18N_CATALOG, ensure_ascii=False)
        return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Chronicle Stack ローカルUI — {title}</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; max-width: 1280px; margin: 0 auto; padding: 20px; color: #1f2937; background: #ffffff; }}
button {{ margin: 3px; padding: 6px 9px; cursor: pointer; }}
select, input {{ margin: 3px; padding: 6px 8px; }}
nav {{ display: flex; flex-wrap: wrap; gap: 4px; margin: 14px 0 16px; padding-bottom: 4px; }}
.shell-grid {{ display: grid; grid-template-columns: minmax(0, 1.25fr) minmax(320px, 0.95fr); gap: 16px; align-items: start; }}
.panel {{ border: 1px solid #e5e7eb; border-radius: 10px; padding: 14px; margin: 12px 0; background: #ffffff; overflow: auto; box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04); }}
.panel > :first-child {{ margin-top: 0; }}
#view, #detail {{ min-width: 0; }}
#detail {{ position: sticky; top: 16px; max-height: calc(100vh - 32px); }}
.warning {{ background: #fefce8; border-left: 4px solid #eab308; padding: 10px 12px; }}
.notice {{ background: #eff6ff; border-left: 4px solid #3b82f6; padding: 10px 12px; margin: 10px 0; }}
.notice-section {{ margin-top: 12px; padding-top: 10px; border-top: 1px solid #bfdbfe; }}
.notice-section:first-of-type {{ margin-top: 0; padding-top: 0; border-top: none; }}
.notice-section h4 {{ margin: 0 0 8px; font-size: 0.95rem; color: #1d4ed8; }}
.fold-section {{ margin: 12px 0 0; }}
.fold-section summary {{ cursor: pointer; font-weight: 600; color: #1f2937; }}
.fold-section[open] summary {{ margin-bottom: 8px; }}
.badge {{ display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 0.85em; margin-right: 6px; }}
.badge-warning {{ background: #fef3c7; color: #92400e; }}
.badge-ready {{ background: #dcfce7; color: #166534; }}
.badge-neutral {{ background: #e5e7eb; color: #374151; }}
.fact-line {{ display: grid; grid-template-columns: minmax(132px, 220px) minmax(0, 1fr); gap: 8px 12px; align-items: start; margin: 8px 0; }}
.fact-label {{ font-weight: 600; color: #374151; }}
.fact-value {{ min-width: 0; overflow-wrap: anywhere; }}
.fact-code {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.9em; }}
.cell-title {{ font-weight: 600; color: #111827; }}
.cell-meta {{ color: #4b5563; font-size: 0.92em; }}
.cell-stack > * + * {{ margin-top: 4px; }}
.cell-details {{ margin-top: 6px; }}
.cell-details summary {{ cursor: pointer; color: #1f2937; font-size: 0.9em; }}
.cell-details[open] summary {{ margin-bottom: 6px; }}
.cell-details-body > * + * {{ margin-top: 4px; }}
.cell-actions {{ display: flex; flex-wrap: wrap; gap: 4px; }}
.cell-code {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.85em; }}
.json-block {{ margin: 12px 0 0; border-top: 1px solid #e5e7eb; padding-top: 12px; }}
.json-block summary {{ cursor: pointer; font-weight: 600; color: #111827; }}
.json-block[open] summary {{ margin-bottom: 10px; }}
pre {{ white-space: pre-wrap; word-break: break-word; background: #f9fafb; padding: 12px; border-radius: 8px; overflow-x: auto; }}
table {{ width: 100%; border-collapse: collapse; display: block; overflow-x: auto; }}
thead, tbody {{ width: 100%; }}
th, td {{ padding: 6px; border-bottom: 1px solid #e5e7eb; vertical-align: top; }}
th {{ position: sticky; top: 0; background: #ffffff; }}
.id {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.85em; }}
@media (max-width: 980px) {{
  .shell-grid {{ grid-template-columns: 1fr; }}
  #detail {{ position: static; max-height: none; }}
}}
</style>
</head>
<body>
<div class="notice">
  <label for="locale-select" id="locale-label">表示言語</label>
  <select id="locale-select">
    <option value="ja">日本語</option>
    <option value="en">English</option>
    <option value="zh-CN">简体中文</option>
  </select>
</div>
<h1 id="shell-title">Chronicle Stack ローカルUI</h1>
<p><strong>{title}</strong></p>
<p><span id="shell-root-label">ルート</span>: <span class="id">{root}</span></p>
<div class="warning" id="shell-warning">
  <p><strong id="shell-warning-title">読み取り専用の前景ローカルUIです。</strong> <span id="shell-warning-body">このUIはローカルの Chronicle ファイルを読み取りますが、レコードは書き込みません。</span></p>
  <p id="shell-boundary-body">daemon なし、自動起動なし、外部 model API なし、GraphRAG runtime なし、vector DB なし、graph DB なし。UI の可視化は correctness proof ではありません。</p>
</div>
<nav>
  <button data-endpoint="/api/overview">概要</button>
  <button data-endpoint="/api/events">イベント</button>
  <button data-endpoint="/api/contexts">コンテキスト</button>
  <button data-endpoint="/api/artifacts">成果物</button>
  <button data-endpoint="/api/decisions">判断</button>
  <button data-endpoint="/api/rde">RDE</button>
  <button data-endpoint="/api/boundary">境界</button>
  <button data-endpoint="/api/audit">監査</button>
  <button data-endpoint="/api/lifecycle">ライフサイクル</button>
  <button data-endpoint="/api/runtime-records">Runtime Records</button>
  <button data-endpoint="/api/review-queue">Review Queue</button>
  <button data-endpoint="/api/summary-jobs">Summary Jobs</button>
  <button data-endpoint="/api/ui-boundary">UI Boundary</button>
  <button data-endpoint="/api/runtime-config">Runtime Config</button>
  <button data-endpoint="/api/package-review">Package Review</button>
  <button data-endpoint="/api/graph-summary">Graph Summary</button>
  <button data-endpoint="/api/ai-index-status">AI Index Status</button>
  <button data-endpoint="/api/ai-index-vector">AI Index Vector</button>
  <button data-endpoint="/api/ai-index-graph-nodes">AI Index Graph Nodes</button>
  <button data-endpoint="/api/ai-index-graph-edges">AI Index Graph Edges</button>
</nav>
<div class="shell-grid">
  <section id="view" class="panel"><p id="shell-loading-overview">概要を読み込み中...</p></section>
  <section id="detail" class="panel"><p id="shell-select-json">テーブル行の JSON を選択して単一レコードを確認します。</p></section>
</div>
<script>
const idFields = ['event_id', 'context_id', 'artifact_id', 'decision_id', 'rde_record_id', 'rule_id', 'audit_id', 'lifecycle_id', 'record_id', 'node_id', 'summary_job_id'];
const reviewWarningLabels = {review_warning_labels_json};
const uiI18nCatalog = {ui_i18n_catalog_json};
const supportedLocales = ['ja', 'en', 'zh-CN'];
const defaultLocale = 'ja';
function normalizeLocale(locale) {{
  const value = String(locale || '').trim();
  if (supportedLocales.includes(value)) return value;
  if (value.startsWith('ja')) return 'ja';
  if (value.startsWith('zh')) return 'zh-CN';
  return 'en';
}}
function currentLocale() {{ return window.__chronicleLocale || defaultLocale; }}
function t(key, fallback = '') {{
  const locale = currentLocale();
  const localeCatalog = uiI18nCatalog[locale] || {{}};
  const englishCatalog = uiI18nCatalog.en || {{}};
  return localeCatalog[key] || englishCatalog[key] || fallback || key;
}}
function exactTranslations() {{ return (uiI18nCatalog[currentLocale()] || {{}}).exact || {{}}; }}
function prefixTranslations() {{ return (uiI18nCatalog[currentLocale()] || {{}}).prefix || {{}}; }}
function localizeTextValue(value) {{
  const text = String(value || '');
  const exact = exactTranslations();
  const trimmed = text.trim();
  if (trimmed && exact[trimmed]) {{
    return text.replace(trimmed, exact[trimmed]);
  }}
  const prefixes = prefixTranslations();
  for (const [source, translated] of Object.entries(prefixes)) {{
    if (text.includes(source)) {{
      return text.replace(source, translated);
    }}
  }}
  return text;
}}
function label(key, fallback = '') {{
  return t(key, fallback || key);
}}
function localizeRenderedRegion(element) {{
  if (!element) return;
  const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT, {{
    acceptNode(node) {{
      const parent = node.parentElement;
      if (!parent) return NodeFilter.FILTER_REJECT;
      if (parent.closest('pre, code, .id')) return NodeFilter.FILTER_REJECT;
      return NodeFilter.FILTER_ACCEPT;
    }}
  }});
  const nodes = [];
  while (walker.nextNode()) nodes.push(walker.currentNode);
  nodes.forEach(node => {{
    node.nodeValue = localizeTextValue(node.nodeValue || '');
  }});
}}
function applyDynamicAttributeTranslations(root) {{
  if (!root) return;
  root.querySelectorAll('[data-filter-input]').forEach(input => {{
    const target = String(input.getAttribute('data-filter-input') || '');
    if (target === 'runtimeRecords') input.setAttribute('placeholder', t('placeholder.runtime_filter'));
    if (target === 'reviewQueue') input.setAttribute('placeholder', t('placeholder.review_filter'));
    if (target === 'summaryJobs') input.setAttribute('placeholder', t('placeholder.summary_filter'));
  }});
  root.querySelectorAll('input[id$=\"-reviewer-note\"]').forEach(input => input.setAttribute('placeholder', t('placeholder.review_note')));
  root.querySelectorAll('input[id$=\"-reviewer-label\"]').forEach(input => input.setAttribute('placeholder', t('placeholder.reviewer')));
  root.querySelectorAll('input[id$=\"-reviewer-session-label\"]').forEach(input => input.setAttribute('placeholder', t('placeholder.session')));
}}
function applyShellTranslations() {{
  document.title = t('shell.title') + ' — ' + {json.dumps(metadata.title, ensure_ascii=False)};
  document.documentElement.lang = currentLocale();
  const localeLabel = document.getElementById('locale-label');
  if (localeLabel) localeLabel.textContent = t('label.language');
  const shellTitle = document.getElementById('shell-title');
  if (shellTitle) shellTitle.textContent = t('shell.title');
  const shellRootLabel = document.getElementById('shell-root-label');
  if (shellRootLabel) shellRootLabel.textContent = t('shell.root');
  const warningTitle = document.getElementById('shell-warning-title');
  if (warningTitle) warningTitle.textContent = t('shell.warning_title');
  const warningBody = document.getElementById('shell-warning-body');
  if (warningBody) warningBody.textContent = t('shell.warning_body');
  const boundaryBody = document.getElementById('shell-boundary-body');
  if (boundaryBody) boundaryBody.textContent = t('shell.boundary_body');
  const loadingOverview = document.getElementById('shell-loading-overview');
  if (loadingOverview) loadingOverview.textContent = t('shell.loading_overview');
  const selectJson = document.getElementById('shell-select-json');
  if (selectJson) selectJson.textContent = t('shell.select_json');
  document.querySelectorAll('button[data-endpoint]').forEach(button => {{
    button.textContent = t('nav.' + button.dataset.endpoint, button.textContent || '');
  }});
  const localeSelect = document.getElementById('locale-select');
  if (localeSelect) {{
    Array.from(localeSelect.options).forEach(option => {{
      option.textContent = t('locale.' + option.value, option.textContent || option.value);
    }});
    localeSelect.value = currentLocale();
  }}
}}
function applyLocaleToPage() {{
  applyShellTranslations();
  const view = document.getElementById('view');
  const detail = document.getElementById('detail');
  localizeRenderedRegion(view);
  localizeRenderedRegion(detail);
  applyDynamicAttributeTranslations(view);
  applyDynamicAttributeTranslations(detail);
}}
function initialLocale() {{
  const params = new URLSearchParams(window.location.search);
  const queryLocale = params.get('locale');
  if (queryLocale) return normalizeLocale(queryLocale);
  const storedLocale = window.localStorage.getItem('chronicle-ui-locale');
  if (storedLocale) return normalizeLocale(storedLocale);
  return normalizeLocale(navigator.language || defaultLocale);
}}
function setLocale(locale, rerender = true) {{
  window.__chronicleLocale = normalizeLocale(locale);
  window.localStorage.setItem('chronicle-ui-locale', window.__chronicleLocale);
  applyLocaleToPage();
  if (!rerender) return;
  if (window.__chronicleCurrentEndpoint) loadEndpoint(window.__chronicleCurrentEndpoint);
  if (window.__chronicleLastDetail) loadDetail(window.__chronicleLastDetail);
}}
function esc(value) {{ return String(value).replace(/[&<>\"']/g, ch => ({{'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}}[ch])); }}
function firstArray(payload) {{ for (const key of Object.keys(payload)) if (Array.isArray(payload[key])) return payload[key]; return null; }}
function badge(text, cls) {{ return '<span class="badge ' + cls + '">' + esc(text) + '</span>'; }}
function jumpBadge(text, cls, endpoint, filterTarget, filterValue) {{
  const targetAttr = filterTarget ? ' data-filter-target="' + esc(filterTarget) + '"' : '';
  const valueAttr = filterValue ? ' data-filter-value="' + esc(filterValue) + '"' : '';
  return '<button data-jump="' + esc(endpoint) + '"' + targetAttr + valueAttr + '>'
    + badge(text, cls) + '</button>';
}}
function copyCommandButton(command, targetId, label = '') {{
  if (!command) return '';
  return '<button data-copy-command="' + esc(command) + '" data-copy-target="' + esc(targetId || 'action-preview-response') + '">' + esc(label || t('button.copy_cli')) + '</button>';
}}
function sourceCountBadges(sourceCounts) {{
  return Object.entries(sourceCounts || {{}}).map(([key, value]) =>
    badge(key + ':' + value, 'badge-neutral')
  ).join('');
}}
function detailMessages(items, fallbackItems = []) {{
  const details = Array.isArray(items) ? items : [];
  const fallback = Array.isArray(fallbackItems) ? fallbackItems : [];
  return details.map(item => item.message).join(' | ') || fallback.join(' | ') || '';
}}
function reviewActionCoreDetailLines(payload, action = '', recordId = '') {{
  return ''
    + detailLine('Action', payload.action || action || '')
    + detailLine('Event', payload.event_id || recordId || '')
    + detailLine('Error code', payload.error_code || '')
    + detailLine('Identity assurance', payload.identity_assurance_status || '')
    + detailLine('Identity assurance message', payload.identity_assurance_message || '')
    + detailLine('CLI equivalent', payload.cli_equivalent || '')
    + detailLine('Failure summary', payload.failure_summary || '')
    + detailLine('Warnings', detailMessages(payload.warning_details, payload.warning_codes));
}}
function contractDetailLines(successContract, failureContract, targetId) {{
  const resolvedContract = (successContract || failureContract) || {{}};
  const lines = []
    + detailLine('Recovery path', resolvedContract.recovery_path || '')
    + detailLine('Rollback status', resolvedContract.rollback_status || '')
    + detailLine('Transaction status', (successContract || {{}}).transaction_status || '')
    + detailLine('Durable mutation on failure', (failureContract || {{}}).durable_mutation_reported_on_failure)
    + detailListLine('Possible errors', (failureContract || {{}}).possible_error_codes, ' | ')
    + detailListLine('Recovery commands', (failureContract || {{}}).recovery_commands, ' | ')
    + detailListLine('Follow-up commands', (successContract || {{}}).follow_up_commands, ' | ');
  return lines + (resolvedContract.recovery_path ? '<p>' + copyCommandButton(resolvedContract.recovery_path, targetId, t('button.copy_recovery_cli')) + '</p>' : '');
}}
function renderReviewActionResultPanel(title, responseStatus, path, payload, targetId, options = {{}}) {{
  const action = options.action || '';
  const recordId = options.recordId || '';
  const message = options.useStatusFallback
    ? (payload.message || payload.status || t('status.no_message'))
    : (payload.message || t('status.no_message'));
  const extraLines = options.extraLines || '';
  return ''
    + '<p><strong>' + esc(title) + '</strong></p>'
    + '<p>' + esc(localizeTextValue('Status: ')) + esc(responseStatus) + '</p>'
    + '<p>' + esc(localizeTextValue('Route: ')) + '<span class="id">' + esc(path) + '</span></p>'
    + '<p>' + esc(message) + '</p>'
    + reviewActionCoreDetailLines(payload, action, recordId)
    + extraLines
    + contractDetailLines(payload.success_contract, payload.failure_contract, targetId);
}}
function renderReviewMutationForm(title, prefix) {{
  return '<div class="notice"><strong>' + esc(title) + '</strong><p>'
    + '<label>' + esc(localizeTextValue('Reviewer')) + ' <input id="' + esc(prefix) + '-reviewer-label" value="local-ui" placeholder="' + esc(t('placeholder.reviewer')) + '"></label> '
    + '<label>' + esc(localizeTextValue('Kind')) + ' <select id="' + esc(prefix) + '-reviewer-kind"><option value="local_operator">local_operator</option><option value="user_declared">user_declared</option></select></label> '
    + '<label>' + esc(localizeTextValue('Session')) + ' <input id="' + esc(prefix) + '-reviewer-session-label" value="local-ui-session" placeholder="' + esc(t('placeholder.session')) + '"></label> '
    + '<label>' + esc(localizeTextValue('Note')) + ' <input id="' + esc(prefix) + '-reviewer-note" placeholder="' + esc(t('placeholder.review_note')) + '"></label></p></div>';
}}
function renderPreviewSummary(preview) {{
  return preview.status
    ? '<strong>' + esc(preview.status) + '</strong><br>' + esc(preview.message || '')
    : esc(preview.message || '');
}}
function renderPreviewContractSummary(preview, previewTarget = 'action-preview-response') {{
  const failureContract = (preview && preview.failure_contract) || {{}};
  const successContract = (preview && preview.success_contract) || {{}};
  const writeRouteContract = (preview && preview.write_route_contract) || {{}};
  const identityProofContract = writeRouteContract.identity_proof_contract || {{}};
  const recoveryPath = failureContract.recovery_path || '';
  const possibleErrors = Array.isArray(failureContract.possible_error_codes)
    ? failureContract.possible_error_codes
    : [];
  const followUpCommands = Array.isArray(successContract.follow_up_commands)
    ? successContract.follow_up_commands
    : [];
  const requestFields = Array.isArray(writeRouteContract.expected_request_fields)
    ? writeRouteContract.expected_request_fields
    : [];
  if (!recoveryPath && possibleErrors.length === 0 && followUpCommands.length === 0 && requestFields.length === 0) return '';
  return [
    failureContract.rollback_status
      ? '<br><span class="id">rollback=' + esc(failureContract.rollback_status) + '</span>'
      : '',
    successContract.transaction_status
      ? '<br><span class="id">transaction=' + esc(successContract.transaction_status) + '</span>'
      : '',
    typeof failureContract.durable_mutation_reported_on_failure === 'boolean'
      ? '<br><span class="id">durable-on-failure=' + esc(failureContract.durable_mutation_reported_on_failure) + '</span>'
      : '',
    writeRouteContract.route_template
      ? '<br><span class="id">write-route=' + esc(writeRouteContract.route_template) + '</span>'
      : '',
    requestFields.length > 0
      ? '<br><span class="id">request-fields=' + esc(requestFields.join(' | ')) + '</span>'
      : '',
    writeRouteContract.success_status_code
      ? '<br><span class="id">success-status=' + esc(writeRouteContract.success_status_code) + '</span>'
      : '',
    writeRouteContract.blocked_status_code
      ? '<br><span class="id">blocked-status=' + esc(writeRouteContract.blocked_status_code) + '</span>'
      : '',
    identityProofContract.proof_status
      ? '<br><span class="id">proof-status=' + esc(identityProofContract.proof_status) + '</span>'
      : '',
    Array.isArray(identityProofContract.required_identity_fields) && identityProofContract.required_identity_fields.length > 0
      ? '<br><span class="id">proof-fields=' + esc(identityProofContract.required_identity_fields.join(' | ')) + '</span>'
      : '',
    recoveryPath
      ? '<br><span class="id">recovery=' + esc(recoveryPath) + '</span> '
        + copyCommandButton(recoveryPath, previewTarget, t('button.copy_recovery_cli'))
      : '',
    possibleErrors.length > 0
      ? '<br><span class="id">errors=' + esc(possibleErrors.join(' | ')) + '</span>'
      : '',
    followUpCommands.length > 0
      ? '<br><span class="id">follow-up=' + esc(followUpCommands.join(' | ')) + '</span>'
      : '',
  ].join('');
}}
function renderPreviewButtons(previewActions, options = {{}}) {{
  const actions = Array.isArray(previewActions) ? previewActions : [];
  const mutationEnabled = Boolean(options.mutationEnabled);
  const recordId = options.recordId || '';
  const fieldPrefix = options.fieldPrefix || '';
  const successDetail = options.successDetail || '';
  const previewTarget = options.previewTarget || 'action-preview-response';
  return actions.map(item =>
    mutationEnabled
      ? '<button data-submit-review-action="' + esc(item.post_path || '') + '" data-review-action="' + esc(item.action || '') + '" data-review-record="' + esc(recordId) + '" data-review-fields="' + esc(fieldPrefix) + '" data-success-detail="' + esc(successDetail) + '" data-preview-target="' + esc(previewTarget) + '">' + esc(item.label || item.action || t('button.apply')) + '</button>'
      : '<button data-preview-post="' + esc(item.post_path || '') + '" data-preview-target="' + esc(previewTarget) + '">' + esc(t('button.preview_blocked_route')) + '</button>'
  ).join(' ');
}}
function authReadinessBadge(status) {{
  return status === 'boundary_aligned'
    ? jumpBadge(label('badge.auth_aligned', 'Auth aligned'), 'badge-ready', '/api/review-queue', 'reviewQueue', 'boundary_aligned')
    : jumpBadge(label('badge.auth_advisory', 'Auth advisory'), 'badge-warning', '/api/review-queue', 'reviewQueue', status || 'advisory_only');
}}
function identityAssuranceBadge(status) {{
  return status === 'boundary_aligned'
    ? jumpBadge(label('badge.identity_aligned', 'Identity aligned'), 'badge-ready', '/api/review-queue', 'reviewQueue', 'boundary_aligned')
    : status
      ? jumpBadge(label('badge.identity_advisory', 'Identity advisory'), 'badge-warning', '/api/review-queue', 'reviewQueue', status)
      : badge(label('badge.identity_na', 'Identity n/a'), 'badge-neutral');
}}
function summaryReviewStatusBadge(status) {{
  return status === 'ready'
    ? jumpBadge(label('badge.ready', 'Ready'), 'badge-ready', '/api/review-queue', 'reviewQueue', 'ready')
    : status === 'resolved'
      ? jumpBadge(label('badge.resolved', 'Resolved'), 'badge-neutral', '/api/review-queue', 'reviewQueue', 'resolved')
      : jumpBadge(label('badge.advisory', 'Advisory'), 'badge-warning', '/api/review-queue', 'reviewQueue', 'advisory');
}}
function packageStatusBadge(status) {{
  return status === 'package_context_available'
    ? jumpBadge(label('badge.package_ready', 'Package Ready'), 'badge-ready', '/api/review-queue', 'reviewQueue', 'package:package_context_available')
    : status === 'no_context_records'
      ? jumpBadge(label('badge.package_advisory', 'Package Advisory'), 'badge-warning', '/api/review-queue', 'reviewQueue', 'package:no_context_records')
      : badge(status || label('badge.package_unknown', 'Package Unknown'), 'badge-neutral');
}}
function previewButtonsConfig(row, config) {{
  return {{
    mutationEnabled: row.ui_mutation_enabled,
    recordId: config.recordId || '',
    fieldPrefix: config.fieldPrefix || '',
    successDetail: config.successDetail || '',
    previewTarget: config.previewTarget || 'action-preview-response',
  }};
}}
function mutationEnablementBadge(summary) {{
  if (!summary || !summary.status) return badge(label('badge.mutation_na', 'Mutation n/a'), 'badge-neutral');
  if (summary.enablement_ready) return badge(label('badge.mutation_ready', 'Mutation ready'), 'badge-ready');
  return badge(label('badge.mutation_preview', 'Mutation preview'), 'badge-warning');
}}
function renderMutationEnablementSummary(summary) {{
  if (!summary || !summary.status) return '';
  const proofFields = Array.isArray(summary.identity_proof_fields) ? summary.identity_proof_fields : [];
  return [
    '<span class="id">mutation=' + esc(summary.status || '') + '</span>',
    summary.operational_status
      ? '<span class="id">operational=' + esc(summary.operational_status) + '</span>'
      : '',
    typeof summary.remaining_count === 'number'
      ? '<span class="id">remaining=' + esc(summary.remaining_count) + '</span>'
      : '',
    summary.blocked_status_code
      ? '<span class="id">blocked-status=' + esc(summary.blocked_status_code) + '</span>'
      : '',
    summary.identity_proof_status
      ? '<span class="id">proof-status=' + esc(summary.identity_proof_status) + '</span>'
      : '',
    proofFields.length > 0
      ? '<span class="id">proof-fields=' + esc(proofFields.join(' | ')) + '</span>'
      : '',
  ].filter(Boolean).join('<br>');
}}
function detailJsonButton(endpoint, row) {{
  const path = detailPath(endpoint, row);
  return path ? '<button data-detail="' + esc(path) + '">JSON</button>' : '';
}}
function stackedCell(parts, separator = '<br>') {{
  return parts.filter(part => part).join(separator);
}}
function cellTitle(text) {{
  return text ? '<div class="cell-title">' + esc(text) + '</div>' : '';
}}
function cellMeta(text) {{
  return text ? '<div class="cell-meta">' + esc(text) + '</div>' : '';
}}
function cellCode(text) {{
  return text ? '<div class="cell-code">' + esc(text) + '</div>' : '';
}}
function cellStack(parts) {{
  return '<div class="cell-stack">' + parts.filter(part => part).join('') + '</div>';
}}
function cellDetails(summary, parts, open = false) {{
  const body = parts.filter(part => part).join('');
  if (!body) return '';
  return '<details class="cell-details"' + (open ? ' open' : '') + '><summary>'
    + esc(summary)
    + '</summary><div class="cell-details-body">' + body + '</div></details>';
}}
function responseSummaryLine(responseMetadata) {{
  if (!responseMetadata || !responseMetadata.present) return '';
  return cellMeta(
    'Response ' + String(responseMetadata.response_id || '(no response_id)')
    + (responseMetadata.finish_reason ? ' / ' + String(responseMetadata.finish_reason) : '')
  );
}}
function previewCell(preview, previewActions, options) {{
  const previewSummary = renderPreviewSummary(preview || {{}});
  const previewContractSummary = renderPreviewContractSummary(
    preview || {{}},
    (options && options.previewTarget) || 'action-preview-response',
  );
  const previewButtons = renderPreviewButtons(previewActions, options);
  return cellStack([
    previewSummary,
    cellDetails(label('button.more_details', 'More details'), [previewContractSummary]),
    cellDetails(label('button.actions', 'Actions'), [
      previewButtons ? '<div class="cell-actions">' + previewButtons + '</div>' : '',
    ]),
  ]);
}}
function reviewerCell(identity, fallbackLabel = '') {{
  const reviewerBadge = reviewerIdentityBadge(identity);
  const label = (identity && identity.label) || fallbackLabel || '';
  return reviewerBadge + (reviewerBadge ? '<br>' : '') + esc(label);
}}
function summaryIdentityCell(identityBadge, reviewerIdentity) {{
  const reviewerBadge = reviewerIdentityBadge(reviewerIdentity);
  const reviewerLabel = (reviewerIdentity && reviewerIdentity.label) || '';
  return identityBadge
    + (reviewerBadge ? '<br>' + reviewerBadge : '')
    + (reviewerLabel ? '<br>' + esc(reviewerLabel) : '');
}}
function resetFilterButton(query, target) {{
  return query ? '<p><button data-reset-filter="' + esc(target) + '">' + esc(label('button.reset_filter', 'Reset Filter')) + '</button></p>' : '';
}}
function emptyFilterState(query, rows, message) {{
  return query && rows.length === 0 ? '<p>' + esc(message) + '</p>' : '';
}}
function actionPreviewStatus(targetId, mutationEnabled, enabledMessage, disabledMessage) {{
  return '<div id="' + esc(targetId) + '"><p>'
    + (mutationEnabled ? enabledMessage : disabledMessage)
    + '</p></div>';
}}
function tableHtml(headers, body) {{
  return '<table><thead><tr>' + headers.map(header => '<th>' + esc(header) + '</th>').join('')
    + '</tr></thead><tbody>' + body + '</tbody></table>';
}}
function listToolbar(endpoint, target, placeholder, sortOptions, filterChipHtml, query) {{
  return activeViewSummary(endpoint, 'list')
    + textInput(target, placeholder)
    + sortSelect(target, currentSortValue(endpoint), sortOptions)
    + filterChipHtml
    + resetFilterButton(query, target);
}}
function renderRuntimeRecordRow(row, endpoint) {{
  const button = detailJsonButton(endpoint, row);
  const preview = row.runtime_record_preview || {{}};
  const actionPreview = row.action_preview_summary || {{}};
  const previewActions = Array.isArray(actionPreview.actions) ? actionPreview.actions : [];
  const mutationEnablement = row.mutation_enablement_summary || {{}};
  const responseMetadata = row.response_metadata_summary || {{}};
  const sourceBadges = sourceCountBadges(preview.source_counts || {{}});
  const authBadge = row.auth_readiness_status === 'boundary_aligned'
    ? jumpBadge(label('badge.auth_aligned', 'Auth aligned'), 'badge-ready', '/api/review-queue', 'reviewQueue', 'boundary_aligned')
    : row.auth_readiness_status
      ? jumpBadge(label('badge.auth_advisory', 'Auth advisory'), 'badge-warning', '/api/review-queue', 'reviewQueue', row.auth_readiness_status)
      : badge(label('badge.auth_na', 'Auth n/a'), 'badge-neutral');
  const mutationBadge = mutationEnablementBadge(mutationEnablement);
  const kindBadge = jumpBadge(
    row.runtime_record_kind || 'unknown',
    'badge-neutral',
    '/api/runtime-records',
    'runtimeRecords',
    row.runtime_record_kind || 'unknown',
  );
  return '<tr>'
    + '<td>' + button + '</td>'
    + '<td><span class="id">' + esc(row.event_id || '') + '</span></td>'
    + '<td>' + kindBadge + '</td>'
    + '<td>' + cellStack([
      authBadge,
      mutationBadge,
      cellDetails(label('button.more_details', 'More details'), [
        cellMeta(renderMutationEnablementSummary(mutationEnablement)),
      ]),
    ]) + '</td>'
    + '<td>' + cellStack([
      cellTitle(preview.title || ''),
      cellMeta(preview.preview_text || ''),
      sourceBadges,
      cellDetails(label('button.more_details', 'More details'), [
        cellCode(JSON.stringify(preview.source_counts || {{}})),
        responseSummaryLine(responseMetadata),
      ]),
    ]) + '</td>'
    + '<td>' + previewCell(actionPreview, previewActions, previewButtonsConfig(row, {{
      recordId: row.review_target_event_id || row.event_id || '',
      fieldPrefix: 'runtime-records',
      successDetail: '/api/runtime-records/' + esc(row.event_id || ''),
      previewTarget: 'runtime-records-action-preview-response',
    }})) + '</td>'
    + '</tr>';
}}
function renderReviewQueueRow(row, endpoint) {{
  const button = detailJsonButton(endpoint, row);
  const capability = row.review_capability || {{}};
  const readiness = row.package_readiness_summary || {{}};
  const parity = row.cli_parity_summary || {{}};
  const preview = row.action_preview_summary || {{}};
  const previewActions = Array.isArray(preview.actions) ? preview.actions : [];
  const authReadiness = row.auth_boundary_notice || {{}};
  const mutationEnablement = row.mutation_enablement_summary || {{}};
  const responseMetadata = row.response_metadata_summary || {{}};
  const warnList = Array.isArray(capability.warnings) ? capability.warnings : [];
  const warnDetails = Array.isArray(capability.warning_details) ? capability.warning_details : [];
  const warnBadges = reviewWarningBadges(warnList);
  const reviewKindBadge = row.review_kind
    ? jumpBadge(row.review_kind, 'badge-neutral', '/api/review-queue', 'reviewQueue', row.review_kind)
    : '';
  const statusBadge = reviewCapabilityBadge(capability);
  const readinessBadge = packageReadinessBadge(readiness);
  const parityBadge = reviewParityBadge(parity);
  const authBadge = authReadinessBadge(authReadiness.status || '');
  return '<tr>'
    + '<td>' + button + '</td>'
    + '<td>' + cellStack([
      '<div><span class="id">' + esc(row.target_event_id || '') + '</span></div>',
      reviewKindBadge,
      cellMeta(row.target_summary || ''),
      cellDetails(label('button.more_details', 'More details'), [
        responseSummaryLine(responseMetadata),
      ]),
    ]) + '</td>'
    + '<td>' + cellStack([
      statusBadge,
      cellDetails(label('button.more_details', 'More details'), [
        readinessBadge,
        parityBadge,
        authBadge,
      ]),
    ]) + '</td>'
    + '<td>' + cellStack([
      mutationEnablementBadge(mutationEnablement),
      previewCell(preview, previewActions, previewButtonsConfig(row, {{
        recordId: row.target_event_id || '',
        fieldPrefix: 'review-queue',
        successDetail: '/api/review-queue/' + esc(row.target_event_id || ''),
        previewTarget: 'review-queue-action-preview-response',
      }})),
      cellDetails(label('button.more_details', 'More details'), [
        cellMeta(renderMutationEnablementSummary(mutationEnablement)),
      ]),
    ]) + '</td>'
    + '<td>' + cellStack([
      warnBadges,
      cellDetails(label('button.more_details', 'More details'), [
        cellMeta(warnDetails.map(item => item.message).join(' | ') || warnList.join(', ') || '(none)'),
      ]),
    ]) + '</td>'
    + '<td>' + reviewerCell(row.latest_reviewer_identity, row.latest_reviewer || '') + '</td>'
    + '</tr>';
}}
function renderSummaryJobRow(row, endpoint) {{
  const button = detailJsonButton(endpoint, row);
  const reviewStatus = row.review_capability_status || '';
  const authReadinessStatus = row.auth_readiness_status || '';
  const packageStatus = row.package_readiness_status || '';
  const identityAssuranceStatus = row.identity_assurance_status || '';
  const preview = row.action_preview_summary || {{}};
  const previewActions = Array.isArray(preview.actions) ? preview.actions : [];
  const mutationEnablement = row.mutation_enablement_summary || {{}};
  const reviewBadge = summaryReviewStatusBadge(reviewStatus);
  const authBadge = authReadinessBadge(authReadinessStatus);
  const identityBadge = identityAssuranceBadge(identityAssuranceStatus);
  const packageBadge = packageStatusBadge(packageStatus);
  const responseMetadata = row.response_metadata_summary || {{}};
  const targetButton = row.review_target_event_id
    ? '<button data-detail-nav="/api/review-queue/' + esc(row.review_target_event_id) + '">' + esc(label('button.open_review', 'Open review')) + '</button>'
    : '';
  return '<tr>'
    + '<td>' + button + '</td>'
    + '<td>' + cellStack(['<div><span class="id">' + esc(row.summary_job_id || '') + '</span></div>', cellTitle(row.title || ''), targetButton]) + '</td>'
    + '<td>' + cellStack([
      cellMeta(row.status || ''),
      reviewBadge,
      cellDetails(label('button.more_details', 'More details'), [
        authBadge,
        packageBadge,
        mutationEnablementBadge(mutationEnablement),
        cellMeta(renderMutationEnablementSummary(mutationEnablement)),
      ]),
    ]) + '</td>'
    + '<td>' + summaryIdentityCell(identityBadge, row.latest_reviewer_identity) + '</td>'
    + '<td>' + previewCell(preview, previewActions, previewButtonsConfig(row, {{
      recordId: row.review_target_event_id || '',
      fieldPrefix: 'summary-jobs',
      successDetail: '/api/summary-jobs/' + esc(row.summary_job_id || ''),
      previewTarget: 'summary-jobs-action-preview-response',
    }})) + '</td>'
    + '<td>' + cellStack([
      cellMeta(row.runtime_provider_kind || ''),
      cellMeta('sources: ' + String(row.summary_source_count ?? 0)),
      cellDetails(label('button.more_details', 'More details'), [
        responseSummaryLine(responseMetadata),
      ]),
    ]) + '</td>'
    + '</tr>';
}}
function renderRuntimeRecordsTable(endpoint, rows) {{
  const query = (window.__chronicleFilters && window.__chronicleFilters.runtimeRecords || '').toLowerCase();
  const filtered = filterRows(rows, row => {{
    if (!query) return true;
    const preview = row.runtime_record_preview || {{}};
    const actionPreview = row.action_preview_summary || {{}};
    const mutationEnablement = row.mutation_enablement_summary || {{}};
    const responseMetadata = row.response_metadata_summary || {{}};
    return includesQuery([
      row.event_id || '',
      row.runtime_record_kind || '',
      row.auth_readiness_status || '',
      row.review_capability_status || '',
      row.identity_assurance_status || '',
      preview.title || '',
      preview.preview_text || '',
      actionPreview.status || '',
      mutationEnablement.status || '',
      mutationEnablement.operational_status || '',
      mutationEnablement.identity_proof_status || '',
      String(mutationEnablement.remaining_count ?? ''),
      String(mutationEnablement.blocked_status_code ?? ''),
      responseMetadata.response_id || '',
      responseMetadata.finish_reason || '',
      responseMetadata.provider_status || '',
      String(responseMetadata.usage_input_tokens ?? ''),
      String(responseMetadata.usage_output_tokens ?? ''),
      String(responseMetadata.usage_total_tokens ?? ''),
      ...(Array.isArray(responseMetadata.response_keys) ? responseMetadata.response_keys : []),
    ], query);
  }});
  const sorted = sortRuntimeRows(filtered);
  const mutationEnabled = sorted.some(row => row.ui_mutation_enabled);
  return listToolbar(endpoint, 'runtimeRecords', t('placeholder.runtime_filter'), [
      {{ value: 'latest', label: t('sort.runtime.latest') }},
      {{ value: 'mutation', label: t('sort.runtime.mutation') }},
      {{ value: 'auth', label: t('sort.runtime.auth') }},
      {{ value: 'kind', label: t('sort.runtime.kind') }},
    ], runtimeRecordsFilterChips(), query)
    + sliceButtonRow(runtimeRecordsSliceButtons())
    + emptyFilterState(query, sorted, localizeTextValue('No matching runtime records for current filter.'))
    + (
      mutationEnabled
        ? renderReviewMutationForm(localizeTextValue('Local Review Mutation'), 'runtime-records')
        : ''
    )
    + actionPreviewStatus(
      'runtime-records-action-preview-response',
      mutationEnabled,
      t('notice.mutation_enabled_runtime_records'),
      t('notice.blocked_route_preview_runtime_records')
    )
    + tableHtml([
      label('label.table_detail', 'Detail'),
      label('label.table_event', 'Event'),
      label('label.table_kind', 'Kind'),
      label('label.table_auth', 'Auth'),
      label('label.table_preview', 'Preview'),
      label('label.table_review_route', 'Review Route'),
    ], sorted.map(row => renderRuntimeRecordRow(row, endpoint)).join(''));
}}
function renderReviewQueueTable(endpoint, rows) {{
  const query = (window.__chronicleFilters && window.__chronicleFilters.reviewQueue || '').toLowerCase();
  const filtered = filterRows(rows, row => {{
    if (!query) return true;
    const capability = row.review_capability || {{}};
    const readiness = row.package_readiness_summary || {{}};
    const parity = row.cli_parity_summary || {{}};
    const authReadiness = row.auth_boundary_notice || {{}};
    const mutationEnablement = row.mutation_enablement_summary || {{}};
    const responseMetadata = row.response_metadata_summary || {{}};
    return includesQuery([
      row.target_event_id || '',
      row.target_summary || '',
      row.review_kind || '',
      capability.status || '',
      readiness.label || '',
      parity.status || '',
      authReadiness.status || '',
      mutationEnablement.status || '',
      mutationEnablement.operational_status || '',
      mutationEnablement.identity_proof_status || '',
      (row.latest_identity_assurance && row.latest_identity_assurance.status) || '',
      (row.latest_reviewer_identity && row.latest_reviewer_identity.kind) || '',
      (row.latest_reviewer_identity && row.latest_reviewer_identity.label) || row.latest_reviewer || '',
      responseMetadata.response_id || '',
      responseMetadata.finish_reason || '',
      responseMetadata.provider_status || '',
      String(responseMetadata.usage_input_tokens ?? ''),
      String(responseMetadata.usage_output_tokens ?? ''),
      String(responseMetadata.usage_total_tokens ?? ''),
      ...(Array.isArray(responseMetadata.response_keys) ? responseMetadata.response_keys : []),
    ], query);
  }});
  const sorted = sortReviewRows(filtered);
  const mutationEnabled = sorted.some(row => row.ui_mutation_enabled);
  return listToolbar(endpoint, 'reviewQueue', t('placeholder.review_filter'), [
      {{ value: 'attention', label: t('sort.review.attention') }},
      {{ value: 'parity', label: t('sort.review.parity') }},
      {{ value: 'latest', label: t('sort.review.latest') }},
      {{ value: 'reviewer', label: t('sort.review.reviewer') }},
    ], reviewQueueFilterChips(), query)
    + sliceButtonRow(reviewQueueSliceButtons())
    + emptyFilterState(query, sorted, localizeTextValue('No matching review rows for current filter.'))
    + (
      mutationEnabled
        ? renderReviewMutationForm(localizeTextValue('Local Review Mutation'), 'review-queue')
        : ''
    )
    + actionPreviewStatus(
      'review-queue-action-preview-response',
      mutationEnabled,
      t('notice.mutation_enabled_review_queue'),
      t('notice.blocked_route_preview_review_queue')
    )
    + tableHtml([
      label('label.table_detail', 'Detail'),
      label('label.table_target', 'Target'),
      label('label.table_status', 'Status'),
      label('label.table_preview', 'Preview'),
      label('label.table_warnings', 'Warnings'),
      label('label.table_latest_reviewer', 'Latest Reviewer'),
    ], sorted.map(row => renderReviewQueueRow(row, endpoint)).join(''));
}}
function renderSummaryJobsTable(endpoint, rows) {{
  const query = (window.__chronicleFilters && window.__chronicleFilters.summaryJobs || '').toLowerCase();
  const filtered = filterRows(rows, row => {{
    if (!query) return true;
    const responseMetadata = row.response_metadata_summary || {{}};
    const mutationEnablement = row.mutation_enablement_summary || {{}};
    return includesQuery([
      row.summary_job_id || '',
      row.title || '',
      row.status || '',
      row.review_capability_status || '',
      row.auth_readiness_status || '',
      row.package_readiness_status || '',
      row.identity_assurance_status || '',
      mutationEnablement.status || '',
      mutationEnablement.operational_status || '',
      mutationEnablement.identity_proof_status || '',
      String(mutationEnablement.remaining_count ?? ''),
      (row.latest_reviewer_identity && row.latest_reviewer_identity.kind) || '',
      (row.latest_reviewer_identity && row.latest_reviewer_identity.label) || '',
      row.cli_parity_status || '',
      row.runtime_provider_kind || '',
      responseMetadata.response_id || '',
      responseMetadata.finish_reason || '',
      responseMetadata.provider_status || '',
      String(responseMetadata.usage_input_tokens ?? ''),
      String(responseMetadata.usage_output_tokens ?? ''),
      String(responseMetadata.usage_total_tokens ?? ''),
      ...(Array.isArray(responseMetadata.response_keys) ? responseMetadata.response_keys : []),
    ], query);
  }});
  const sorted = sortSummaryJobRows(filtered);
  const mutationEnabled = sorted.some(row => row.ui_mutation_enabled);
  return listToolbar(endpoint, 'summaryJobs', t('placeholder.summary_filter'), [
      {{ value: 'latest', label: t('sort.summary.latest') }},
      {{ value: 'mutation', label: t('sort.summary.mutation') }},
      {{ value: 'review', label: t('sort.summary.review') }},
      {{ value: 'title', label: t('sort.summary.title') }},
    ], summaryJobsFilterChips(), query)
    + sliceButtonRow(summaryJobsSliceButtons())
    + emptyFilterState(query, sorted, localizeTextValue('No matching summary jobs for current filter.'))
    + (
      mutationEnabled
        ? renderReviewMutationForm(localizeTextValue('Summary Review Mutation'), 'summary-jobs')
        : ''
    )
    + actionPreviewStatus(
      'summary-jobs-action-preview-response',
      mutationEnabled,
      t('notice.mutation_enabled_summary_jobs'),
      t('notice.blocked_route_preview_summary_jobs')
    )
    + tableHtml([
      label('label.table_detail', 'Detail'),
      label('label.table_summary_job', 'Summary Job'),
      label('label.table_status', 'Status'),
      label('label.table_identity', 'Identity'),
      label('label.table_preview', 'Preview'),
      label('label.table_runtime', 'Runtime'),
    ], sorted.map(row => renderSummaryJobRow(row, endpoint)).join(''));
}}
function renderGenericTable(endpoint, rows) {{
  const keys = Object.keys(rows[0]).slice(0, 8);
  return '<table><thead><tr><th>' + esc(label('label.table_detail', 'Detail')) + '</th>' + keys.map(k => '<th>' + esc(k) + '</th>').join('') + '</tr></thead><tbody>'
    + rows.map(row => {{
      const path = detailPath(endpoint, row);
      const button = path ? '<button data-detail="' + esc(path) + '">JSON</button>' : '';
      return '<tr><td>' + button + '</td>'
        + keys.map(k => '<td>' + esc(typeof row[k] === 'object' ? JSON.stringify(row[k]) : row[k] ?? '') + '</td>').join('')
        + '</tr>';
    }}).join('') + '</tbody></table>';
}}
const endpointRenderers = {{
  '/api/runtime-records': renderRuntimeRecordsTable,
  '/api/review-queue': renderReviewQueueTable,
  '/api/summary-jobs': renderSummaryJobsTable,
}};
function reviewerIdentityBadge(identity) {{
  if (!identity) return '';
  const kind = identity.kind || 'reviewer';
  const label = identity.label || 'unknown';
  return badge(kind + ':' + label, 'badge-neutral');
}}
function reviewWarningBadges(warnings) {{
  return (warnings || []).map(code => {{
    const text = reviewWarningLabels[String(code || '')] || String(code || '').replaceAll('_', ' ');
    return jumpBadge(text, 'badge-warning', '/api/review-queue', 'reviewQueue', String(code || ''));
  }}).join('');
}}
function reviewCapabilityBadge(capability) {{
  const status = String((capability && capability.status) || '');
  if (status === 'ready') return badge('Ready', 'badge-ready');
  if (status === 'resolved') return badge('Resolved', 'badge-neutral');
  return badge('Advisory', 'badge-warning');
}}
function packageReadinessBadge(readiness) {{
  const status = String((readiness && readiness.status) || '');
  const label = String((readiness && readiness.label) || '');
  if (status === 'package_context_available') {{
    return badge(label || 'Package Ready', 'badge-ready');
  }}
  if (status === 'no_context_records') {{
    return badge(label || 'Package Advisory', 'badge-warning');
  }}
  return badge(label || 'Package Unknown', 'badge-neutral');
}}
function reviewParityBadge(parity) {{
  const status = String((parity && parity.status) || '');
  if (status === 'aligned') {{
    return jumpBadge('CLI aligned', 'badge-ready', '/api/review-queue', 'reviewQueue', 'aligned');
  }}
  return jumpBadge('CLI drift', 'badge-warning', '/api/review-queue', 'reviewQueue', 'drift_detected');
}}
function textInput(id, placeholder) {{
  return '<input id="' + esc(id) + '" data-filter-input="' + esc(id) + '" placeholder="' + esc(placeholder)
    + '" style="margin: 6px 6px 10px 0; padding: 6px 8px; width: 260px;">';
}}
function filterRows(rows, predicate) {{
  return rows.filter(predicate);
}}
function includesQuery(values, query) {{
  return JSON.stringify(values).toLowerCase().includes(query);
}}
function includesQuery(values, query) {{
  return JSON.stringify(values).toLowerCase().includes(query);
}}
function sortRows(rows, comparator) {{
  return [...rows].sort(comparator);
}}
const endpointFilterTargets = {{
  '/api/runtime-records': 'runtimeRecords',
  '/api/review-queue': 'reviewQueue',
  '/api/summary-jobs': 'summaryJobs',
}};
const endpointSortDefaults = {{
  '/api/runtime-records': 'latest',
  '/api/review-queue': 'attention',
  '/api/summary-jobs': 'latest',
}};
function currentSortValue(endpoint) {{
  if (!window.__chronicleSorts) return '';
  const target = endpointFilterTargets[endpoint];
  if (!target) return '';
  return window.__chronicleSorts[target] || endpointSortDefaults[endpoint] || '';
}}
function currentFilterValue(endpoint) {{
  if (!window.__chronicleFilters) return '';
  const target = endpointFilterTargets[endpoint];
  return target ? window.__chronicleFilters[target] || '' : '';
}}
function setFilterValue(target, value) {{
  if (!window.__chronicleFilters || !target) return;
  window.__chronicleFilters[target] = value || '';
}}
function setSortValue(target, value) {{
  if (!window.__chronicleSorts || !target) return;
  const endpoint = Object.keys(endpointFilterTargets).find(key => endpointFilterTargets[key] === target) || '';
  window.__chronicleSorts[target] = value || endpointSortDefaults[endpoint] || '';
}}
function clearFilterValue(target) {{
  if (!window.__chronicleFilters || !target) return;
  window.__chronicleFilters[target] = '';
}}
function resetAllFilterValues() {{
  if (!window.__chronicleFilters) return;
  Object.values(endpointFilterTargets).forEach(target => {{
    window.__chronicleFilters[target] = '';
  }});
}}
function endpointStateLabel(kind, endpoint) {{
  const value = kind === 'filter' ? currentFilterValue(endpoint) : currentSortValue(endpoint);
  return value ? stateLabel(kind, value) : '';
}}
function endpointFilterTarget(endpoint) {{
  return endpointFilterTargets[endpoint] || '';
}}
function stateLabel(kind, value, suffix) {{
  const normalizedValue = String(value || '');
  if (!normalizedValue) return '';
  const normalizedSuffix = String(suffix || '');
  return normalizedSuffix
    ? kind + '=' + normalizedValue + ' (' + normalizedSuffix + ')'
    : kind + '=' + normalizedValue;
}}
function activeReviewWarningFilter() {{
  const value = String((window.__chronicleFilters && window.__chronicleFilters.reviewQueue) || '');
  if (!value) return '';
  if (value.includes('warning')) return value;
  if (value.startsWith('ui_')) return value;
  if (value.startsWith('reviewer_')) return value;
  if (value.startsWith('no_')) return value;
  return '';
}}
function sortSelect(id, value, options) {{
  return '<label style="margin-right: 10px;">Sort: <select data-sort-input="' + esc(id)
    + '" style="margin: 6px 6px 10px 6px; padding: 6px 8px;">'
    + options.map(option =>
      '<option value="' + esc(option.value) + '"' + (option.value === value ? ' selected' : '') + '>'
      + esc(option.label) + '</option>'
    ).join('')
    + '</select></label>';
}}
function compareTextDesc(left, right) {{
  return String(right || '').localeCompare(String(left || ''));
}}
function compareReviewerLabel(left, right) {{
  const leftReviewer = (left.latest_reviewer_identity && left.latest_reviewer_identity.label) || left.latest_reviewer || '';
  const rightReviewer = (right.latest_reviewer_identity && right.latest_reviewer_identity.label) || right.latest_reviewer || '';
  return String(leftReviewer).localeCompare(String(rightReviewer));
}}
function compareReviewTargetDesc(left, right) {{
  return compareTextDesc(left.target_event_id, right.target_event_id);
}}
function reviewAttentionRank(row) {{
  const capability = row.review_capability || {{}};
  const readiness = row.package_readiness_summary || {{}};
  const parity = row.cli_parity_summary || {{}};
  if (parity.status === 'drift_detected') return 0;
  if (row.review_kind === 'review_requested') return 0;
  if (capability.status === 'advisory_only') return 1;
  if (capability.status === 'ready') return 2;
  if (readiness.status === 'package_context_available') return 3;
  if (capability.status === 'resolved') return 4;
  return 5;
}}
function reviewParityRank(row) {{
  const parity = row.cli_parity_summary || {{}};
  if (parity.status === 'drift_detected') return 0;
  if (parity.status === 'aligned') return 1;
  return 2;
}}
function reviewWarningFilterRank(row) {{
  const warningFilter = activeReviewWarningFilter();
  if (!warningFilter) return 0;
  const warnings = ((row.review_capability || {{}}).warnings || []).map(value => String(value || ''));
  return warnings.includes(warningFilter) ? 0 : 1;
}}
function mutationSummaryRank(summary) {{
  const status = String((summary && summary.status) || '');
  const operationalStatus = String((summary && summary.operational_status) || '');
  const remainingCount = Number((summary && summary.remaining_count) || 0);
  if (status === 'enabled') return 0;
  if (operationalStatus === 'blocked') return 1;
  if (status === 'preview_only') return 2;
  if (operationalStatus === 'ready') return 3;
  return 4 + Math.max(0, remainingCount);
}}
function authStatusRank(status) {{
  const value = String(status || '');
  if (value === 'boundary_aligned') return 0;
  if (value === 'advisory_only') return 1;
  if (value) return 2;
  return 3;
}}
function sortRuntimeRows(rows) {{
  const sortValue = currentSortValue('/api/runtime-records');
  if (sortValue === 'mutation') {{
    return sortRows(rows, (left, right) => {{
      const mutationCompare = mutationSummaryRank(left.mutation_enablement_summary) - mutationSummaryRank(right.mutation_enablement_summary);
      if (mutationCompare !== 0) return mutationCompare;
      const authCompare = authStatusRank(left.auth_readiness_status) - authStatusRank(right.auth_readiness_status);
      if (authCompare !== 0) return authCompare;
      return compareTextDesc(left.event_id, right.event_id);
    }});
  }}
  if (sortValue === 'auth') {{
    return sortRows(rows, (left, right) => {{
      const authCompare = authStatusRank(left.auth_readiness_status) - authStatusRank(right.auth_readiness_status);
      if (authCompare !== 0) return authCompare;
      const mutationCompare = mutationSummaryRank(left.mutation_enablement_summary) - mutationSummaryRank(right.mutation_enablement_summary);
      if (mutationCompare !== 0) return mutationCompare;
      return compareTextDesc(left.event_id, right.event_id);
    }});
  }}
  if (sortValue === 'kind') {{
    return sortRows(rows, (left, right) => {{
      const kindCompare = String(left.runtime_record_kind || '').localeCompare(String(right.runtime_record_kind || ''));
      if (kindCompare !== 0) return kindCompare;
      return compareTextDesc(left.event_id, right.event_id);
    }});
  }}
  return sortRows(rows, (left, right) => compareTextDesc(left.event_id, right.event_id));
}}
function sortReviewRows(rows) {{
  const sortValue = currentSortValue('/api/review-queue');
  if (sortValue === 'latest') {{
    return sortRows(rows, compareReviewTargetDesc);
  }}
  if (sortValue === 'reviewer') {{
    return sortRows(rows, (left, right) => {{
      const reviewerCompare = compareReviewerLabel(left, right);
      if (reviewerCompare !== 0) return reviewerCompare;
      return compareReviewTargetDesc(left, right);
    }});
  }}
  if (sortValue === 'parity') {{
    return sortRows(rows, (left, right) => {{
      const warningCompare = reviewWarningFilterRank(left) - reviewWarningFilterRank(right);
      if (warningCompare !== 0) return warningCompare;
      const parityCompare = reviewParityRank(left) - reviewParityRank(right);
      if (parityCompare !== 0) return parityCompare;
      const attentionCompare = reviewAttentionRank(left) - reviewAttentionRank(right);
      if (attentionCompare !== 0) return attentionCompare;
      return compareReviewTargetDesc(left, right);
    }});
  }}
  return sortRows(rows, (left, right) => {{
    const warningCompare = reviewWarningFilterRank(left) - reviewWarningFilterRank(right);
    if (warningCompare !== 0) return warningCompare;
    const rankCompare = reviewAttentionRank(left) - reviewAttentionRank(right);
    if (rankCompare !== 0) return rankCompare;
    return compareReviewTargetDesc(left, right);
  }});
}}
function summaryJobAttentionRank(row) {{
  const reviewStatus = String(row.review_capability_status || '');
  const packageStatus = String(row.package_readiness_status || '');
  const parityStatus = String(row.cli_parity_status || '');
  if (parityStatus === 'drift_detected') return 0;
  if (reviewStatus === 'advisory_only') return 1;
  if (reviewStatus === 'ready') return 2;
  if (packageStatus === 'package_context_available') return 3;
  if (reviewStatus === 'resolved') return 4;
  return 5;
}}
function compareSummaryJobDesc(left, right) {{
  return compareTextDesc(left.summary_job_id, right.summary_job_id);
}}
function sortSummaryJobRows(rows) {{
  const sortValue = currentSortValue('/api/summary-jobs');
  if (sortValue === 'mutation') {{
    return sortRows(rows, (left, right) => {{
      const mutationCompare = mutationSummaryRank(left.mutation_enablement_summary) - mutationSummaryRank(right.mutation_enablement_summary);
      if (mutationCompare !== 0) return mutationCompare;
      const reviewCompare = summaryJobAttentionRank(left) - summaryJobAttentionRank(right);
      if (reviewCompare !== 0) return reviewCompare;
      return compareSummaryJobDesc(left, right);
    }});
  }}
  if (sortValue === 'title') {{
    return sortRows(rows, (left, right) => {{
      const titleCompare = String(left.title || '').localeCompare(String(right.title || ''));
      if (titleCompare !== 0) return titleCompare;
      return compareSummaryJobDesc(left, right);
    }});
  }}
  if (sortValue === 'review') {{
    return sortRows(rows, (left, right) => {{
      const rankCompare = summaryJobAttentionRank(left) - summaryJobAttentionRank(right);
      if (rankCompare !== 0) return rankCompare;
      const reviewCompare = String(left.review_capability_status || '').localeCompare(String(right.review_capability_status || ''));
      if (reviewCompare !== 0) return reviewCompare;
      return compareSummaryJobDesc(left, right);
    }});
  }}
  return sortRows(rows, compareSummaryJobDesc);
}}
function currentFilterLabel() {{
  if (!window.__chronicleCurrentEndpoint || !window.__chronicleFilters) return '';
  const endpoint = window.__chronicleCurrentEndpoint;
  const target = endpointFilterTarget(endpoint);
  const value = target ? window.__chronicleFilters[target] || '' : '';
  return value ? stateLabel('filter', value, filterValueLabel(target, value)) : '';
}}
function sortValueLabel(endpoint, sortValue) {{
  const normalizedEndpoint = String(endpoint || '');
  const normalizedSort = String(sortValue || '');
  if (!normalizedSort) return '';
  if (normalizedEndpoint === '/api/runtime-records') {{
    if (normalizedSort === 'latest') return label('sort.runtime.latest', 'Latest first');
    if (normalizedSort === 'mutation') return label('sort.runtime.mutation', 'Mutation readiness');
    if (normalizedSort === 'auth') return label('sort.runtime.auth', 'Auth readiness');
    if (normalizedSort === 'kind') return label('sort.runtime.kind', 'Kind');
  }}
  if (normalizedEndpoint === '/api/review-queue') {{
    if (normalizedSort === 'attention') return label('sort.review.attention', 'Needs attention first');
    if (normalizedSort === 'parity') return label('sort.review.parity', 'CLI drift first');
    if (normalizedSort === 'latest') return label('sort.review.latest', 'Latest first');
    if (normalizedSort === 'reviewer') return label('sort.review.reviewer', 'Reviewer');
  }}
  if (normalizedEndpoint === '/api/summary-jobs') {{
    if (normalizedSort === 'latest') return label('sort.summary.latest', 'Latest first');
    if (normalizedSort === 'mutation') return label('sort.summary.mutation', 'Mutation readiness');
    if (normalizedSort === 'review') return label('sort.summary.review', 'Needs attention first');
    if (normalizedSort === 'title') return label('sort.summary.title', 'Title');
  }}
  return normalizedSort.replaceAll('_', ' ');
}}
function sortStateLabel(endpoint, sortValue) {{
  if (!sortValue) return '';
  if (endpoint === '/api/review-queue') {{
    const warningFilter = activeReviewWarningFilter();
    if (warningFilter) {{
      return stateLabel(
        'sort',
        sortValue,
        sortValueLabel(endpoint, sortValue) + ' / warning-first:' + warningFilter,
      );
    }}
  }}
  return stateLabel('sort', sortValue, sortValueLabel(endpoint, sortValue));
}}
function currentSortLabel(endpoint) {{
  const currentEndpoint = endpoint || window.__chronicleCurrentEndpoint || '';
  const sortValue = currentSortValue(currentEndpoint);
  return sortStateLabel(currentEndpoint, sortValue);
}}
function hasActiveFilters() {{
  if (!window.__chronicleFilters) return false;
  return Object.values(endpointFilterTargets).some(target => Boolean(window.__chronicleFilters[target]));
}}
function resetFilters(target) {{
  if (!window.__chronicleFilters) return;
  if (!target || target === 'all') {{
    resetAllFilterValues();
    return;
  }}
  clearFilterValue(target);
}}
function currentTrailLabel() {{
  if (!Array.isArray(window.__chronicleDetailTrail) || window.__chronicleDetailTrail.length === 0) return '';
  return window.__chronicleDetailTrail.slice(-3).join(' <- ');
}}
function currentTrailButtons() {{
  if (!Array.isArray(window.__chronicleDetailTrail) || window.__chronicleDetailTrail.length === 0) return '';
  return window.__chronicleDetailTrail.slice(-3).map(path =>
    '<button data-detail-trail="' + esc(path) + '">' + esc(humanizeDetailPath(path)) + '</button>'
  ).join('');
}}
function filterValueLabel(target, value) {{
  const normalizedTarget = String(target || '');
  const normalizedValue = String(value || '');
  if (!normalizedValue) return '';
  if (normalizedTarget === 'runtimeRecords') {{
    if (normalizedValue === 'preview_only') return label('filter.runtime.preview_only', 'Runtime mutation preview');
    if (normalizedValue === 'advisory_only') return label('filter.runtime.advisory_only', 'Runtime auth advisory');
    if (normalizedValue === 'boundary_aligned') return label('filter.runtime.boundary_aligned', 'Runtime identity aligned');
    if (normalizedValue === 'retrieval_plan') return label('filter.runtime.retrieval_plan', 'Runtime retrieval plans');
    if (normalizedValue === 'response_id') return label('filter.runtime.response_id', 'Runtime provider response');
  }}
  if (normalizedTarget === 'summaryJobs') {{
    if (normalizedValue === 'preview_only') return label('filter.summary.preview_only', 'Summary mutation preview');
    if (normalizedValue === 'advisory_only') return label('filter.summary.advisory_only', 'Summary advisory');
    if (normalizedValue === 'package_context_available') return label('filter.summary.package_context_available', 'Summary package ready');
    if (normalizedValue === 'boundary_aligned') return label('filter.summary.boundary_aligned', 'Summary identity aligned');
    if (normalizedValue === 'response_id') return label('filter.summary.response_id', 'Summary provider response');
  }}
  if (normalizedTarget === 'reviewQueue') {{
    if (normalizedValue === 'review_requested') return label('filter.review.review_requested', 'Review requested');
    if (normalizedValue === 'ready') return label('filter.review.ready', 'Review ready');
    if (normalizedValue === 'advisory_only' || normalizedValue === 'advisory') return label('filter.review.advisory', 'Review advisory');
    if (normalizedValue === 'drift_detected') return label('filter.review.drift_detected', 'CLI drift');
    if (normalizedValue === 'aligned') return label('filter.review.aligned', 'CLI aligned');
    if (normalizedValue === 'boundary_aligned') return label('filter.review.boundary_aligned', 'Identity aligned');
    if (normalizedValue === 'ui_auth_not_enabled') return label('filter.review.ui_auth_not_enabled', 'Auth boundary warnings');
    if (normalizedValue === 'reviewer_identity_declared_only') return label('filter.review.reviewer_identity_declared_only', 'Declared identity only');
    if (normalizedValue === 'package:package_context_available') return label('filter.review.package_context_available', 'Package ready');
    if (normalizedValue === 'package:no_context_records') return label('filter.review.no_context_records', 'Package advisory');
  }}
  return normalizedValue.replaceAll('_', ' ');
}}
function sliceChip(filterValue, cls, resetTarget) {{
  const value = String(filterValue || '');
  if (!value) return '';
  const filterLabel = filterValueLabel(resetTarget, value);
  return '<p>'
    + badge('slice:' + filterLabel, cls)
    + ' <span class="id">' + esc(value) + '</span>'
    + ' <button data-reset-filter="' + esc(resetTarget) + '">' + esc(label('button.clear_slice', 'Clear Slice')) + '</button>'
    + '</p>';
}}
function sliceBadge(text, count, cls) {{
  return badge(text + ': ' + count, cls);
}}
function filterChips(target, cls) {{
  const filterValue = String((window.__chronicleFilters && window.__chronicleFilters[target]) || '');
  return sliceChip(filterValue, cls, target);
}}
function sliceButtonRow(buttons) {{
  return buttons.length > 0 ? '<p>' + buttons.join('') + '</p>' : '';
}}
function reviewQueueFilterChips() {{
  return filterChips('reviewQueue', 'badge-warning');
}}
function reviewQueueSliceButtons() {{
  return [
    listJumpButton(localizeTextValue('Review Requested'), '/api/review-queue', 'reviewQueue', 'review_requested'),
    listJumpButton(localizeTextValue('Review Ready'), '/api/review-queue', 'reviewQueue', 'ready'),
    listJumpButton(localizeTextValue('Review Advisory'), '/api/review-queue', 'reviewQueue', 'advisory'),
    listJumpButton(localizeTextValue('CLI Drift'), '/api/review-queue', 'reviewQueue', 'drift_detected'),
    listJumpButton(localizeTextValue('Package Ready'), '/api/review-queue', 'reviewQueue', 'package:package_context_available'),
    listJumpButton(localizeTextValue('Auth Boundary Warnings'), '/api/review-queue', 'reviewQueue', 'ui_auth_not_enabled'),
    listJumpButton(localizeTextValue('Declared Identity Only'), '/api/review-queue', 'reviewQueue', 'reviewer_identity_declared_only'),
  ];
}}
function runtimeRecordsFilterChips() {{
  return filterChips('runtimeRecords', 'badge-neutral');
}}
function summaryJobsFilterChips() {{
  return filterChips('summaryJobs', 'badge-neutral');
}}
function runtimeRecordsSliceButtons() {{
  return [
    listJumpButton(localizeTextValue('Runtime Mutation Preview'), '/api/runtime-records', 'runtimeRecords', 'preview_only'),
    listJumpButton(localizeTextValue('Runtime Auth Advisory'), '/api/runtime-records', 'runtimeRecords', 'advisory_only'),
    listJumpButton(localizeTextValue('Runtime Identity Aligned'), '/api/runtime-records', 'runtimeRecords', 'boundary_aligned'),
    listJumpButton(localizeTextValue('Runtime Retrieval Plans'), '/api/runtime-records', 'runtimeRecords', 'retrieval_plan'),
    listJumpButton(localizeTextValue('Runtime Provider Response'), '/api/runtime-records', 'runtimeRecords', 'response_id'),
  ];
}}
function summaryJobsSliceButtons() {{
  return [
    listJumpButton(localizeTextValue('Summary Mutation Preview'), '/api/summary-jobs', 'summaryJobs', 'preview_only'),
    listJumpButton(localizeTextValue('Summary Advisory'), '/api/summary-jobs', 'summaryJobs', 'advisory_only'),
    listJumpButton(localizeTextValue('Summary Package Ready'), '/api/summary-jobs', 'summaryJobs', 'package_context_available'),
    listJumpButton(localizeTextValue('Summary Identity Aligned'), '/api/summary-jobs', 'summaryJobs', 'boundary_aligned'),
    listJumpButton(localizeTextValue('Summary Provider Response'), '/api/summary-jobs', 'summaryJobs', 'response_id'),
  ];
}}
function activeViewSummary(endpoint, mode) {{
  const parts = [];
  const currentEndpoint = endpoint || window.__chronicleCurrentEndpoint || '/api/overview';
  parts.push(label('status.view', 'view') + '=' + currentEndpoint);
  const filterLabel = currentFilterLabel();
  if (filterLabel) parts.push(filterLabel);
  const sortLabel = currentSortLabel(currentEndpoint);
  if (sortLabel) parts.push(sortLabel);
  if (mode === 'detail') {{
    const trailLabel = currentTrailLabel();
    if (trailLabel) parts.push(label('status.trail', 'trail') + '=' + trailLabel);
  }}
  return '<p class="id">' + esc(label('status.active_view', 'Active view')) + ': ' + esc(parts.join(' | ')) + '</p>';
}}
function humanizeDetailPath(path) {{
  const parts = String(path || '').split('/').filter(Boolean);
  if (parts.length < 3 || parts[0] !== 'api') return String(path || '');
  const resource = parts[1];
  const recordId = parts[2];
  return label('detail.resource.' + resource, resource) + ': ' + recordId;
}}
function overviewJumpButton(label, endpoint, filterTarget, filterValue, variant) {{
  const targetAttr = filterTarget ? ' data-filter-target="' + esc(filterTarget) + '"' : '';
  const valueAttr = filterValue ? ' data-filter-value="' + esc(filterValue) + '"' : '';
  const className = variant ? ' class="' + esc(variant) + '"' : '';
  return '<button' + className + ' data-jump="' + esc(endpoint) + '"' + targetAttr + valueAttr + '>'
    + label + '</button>';
}}
function listJumpButton(label, endpoint, filterTarget, filterValue, variant) {{
  return overviewJumpButton(esc(label), endpoint, filterTarget, filterValue, variant);
}}
function moreSliceButton(filterValue, endpoint, filterTarget) {{
  const value = String(filterValue || '');
  if (!value) return '';
  return listJumpButton('More ' + value, endpoint, filterTarget, value);
}}
function sectionTitle(text) {{
  return '<h3>' + esc(text) + '</h3>';
}}
function detailLine(label, value) {{
  return '<div class="fact-line"><div class="fact-label">' + esc(localizeTextValue(label))
    + '</div><div class="fact-value">' + esc(value || '') + '</div></div>';
}}
function detailListLine(label, values, separator) {{
  const items = Array.isArray(values) ? values : [];
  const joiner = separator || ', ';
  return detailLine(label, items.join(joiner) || '(none)');
}}
function summaryJsonLine(label, value) {{
  return '<div class="fact-line"><div class="fact-label">' + esc(localizeTextValue(label))
    + '</div><div class="fact-value fact-code">' + esc(JSON.stringify(value || {{}})) + '</div></div>';
}}
function messageParagraph(message) {{
  return '<p>' + esc(message || '') + '</p>';
}}
function buttonRow(buttons) {{
  return buttons.length > 0 ? '<p>' + buttons.join('') + '</p>' : '';
}}
function moreStatusButtons(status, endpoint, filterTarget, prefix = '') {{
  if (!status) return [];
  return [listJumpButton(label('status.more', 'More') + ' ' + status, endpoint, filterTarget, prefix + status)];
}}
function statusMessageBody(status, message, buttons = []) {{
  return detailLine('Status', status || '') + buttonRow(buttons) + messageParagraph(message);
}}
function routeHeading(endpoint) {{
  return '<h2>' + esc(endpoint === '/api/overview' ? label('nav./api/overview', 'Overview') : endpoint) + '</h2>';
}}
function prettyJsonPre(value) {{
  return '<pre>' + esc(JSON.stringify(value, null, 2)) + '</pre>';
}}
function collapsibleJsonBlock(summaryLabel, value, open = false) {{
  return '<details class="json-block"' + (open ? ' open' : '') + '><summary>'
    + esc(summaryLabel)
    + '</summary>'
    + prettyJsonPre(value)
    + '</details>';
}}
function noticeSection(title, body) {{
  return '<section class="notice-section"><h4>' + esc(title) + '</h4>' + body + '</section>';
}}
function collapsibleSection(title, body, open = false) {{
  return '<details class="fold-section"' + (open ? ' open' : '') + '><summary>'
    + esc(title)
    + '</summary>'
    + body
    + '</details>';
}}
function renderNotice(title, body) {{
  return '<div class="notice">' + sectionTitle(title) + body + '</div>';
}}
function packageReviewButtons(record) {{
  return (record.package_handoff_preview || record.package_readiness)
    ? [listJumpButton(label('button.open_package_review', 'Open Package Review'), '/api/package-review')]
    : [];
}}
function runtimeRelatedButtons(record) {{
  const buttons = [listJumpButton(label('button.open_runtime_records', 'Open Runtime Records'), '/api/runtime-records')];
  const runtimeKind = record.runtime_record_kind || (record.runtime_record_preview && record.runtime_record_preview.record_kind) || '';
  if (runtimeKind) buttons.push(moreSliceButton(runtimeKind, '/api/runtime-records', 'runtimeRecords'));
  return buttons;
}}
function reviewRelatedButtons(record) {{
  const buttons = [listJumpButton(label('button.open_review_queue', 'Open Review Queue'), '/api/review-queue')];
  const capability = record.review_capability || {{}};
  const readiness = record.package_readiness || {{}};
  const warnings = Array.isArray(capability.warnings) ? capability.warnings : [];
  if (record.review_kind) buttons.push(moreSliceButton(record.review_kind, '/api/review-queue', 'reviewQueue'));
  if (capability.status) buttons.push(moreSliceButton(capability.status, '/api/review-queue', 'reviewQueue'));
  warnings.slice(0, 2).forEach(code => buttons.push(moreSliceButton(code, '/api/review-queue', 'reviewQueue')));
  if (readiness.status) buttons.push(listJumpButton(label('status.more', 'More') + ' ' + readiness.status, '/api/review-queue', 'reviewQueue', 'package:' + readiness.status));
  return buttons;
}}
function summaryRelatedButtons(record) {{
  const buttons = [listJumpButton(label('button.open_summary_jobs', 'Open Summary Jobs'), '/api/summary-jobs')];
  if (record.review_target_event_id) buttons.push(listJumpButton(label('button.open_review_queue', 'Open Review Queue'), '/api/review-queue'));
  const capability = record.review_capability || {{}};
  const readiness = record.package_readiness || {{}};
  const parity = record.cli_parity || {{}};
  if (capability.status) buttons.push(moreSliceButton(capability.status, '/api/review-queue', 'reviewQueue'));
  if (readiness.status) buttons.push(listJumpButton(label('status.more', 'More') + ' ' + readiness.status, '/api/review-queue', 'reviewQueue', 'package:' + readiness.status));
  if (parity.status) buttons.push(moreSliceButton(parity.status, '/api/review-queue', 'reviewQueue'));
  return buttons;
}}
function relatedListButtons(detailEndpoint, record) {{
  const buttons = [];
  if (detailEndpoint.startsWith('/api/runtime-records/')) buttons.push(...runtimeRelatedButtons(record));
  if (detailEndpoint.startsWith('/api/review-queue/')) buttons.push(...reviewRelatedButtons(record));
  if (detailEndpoint.startsWith('/api/summary-jobs/')) buttons.push(...summaryRelatedButtons(record));
  buttons.push(...packageReviewButtons(record));
  return buttons.join('');
}}
function renderNavigationNotice(endpoint, record, options = {{}}) {{
  const filterLabel = options.filterLabel || '';
  const previousDetail = options.previousDetail || '';
  const trailLabel = options.trailLabel || '';
  const trailButtons = options.trailButtons || '';
  const listButtons = options.listButtons || relatedListButtons(endpoint, record);
  return renderNotice(
    label('notice.navigation', 'Navigation'),
    activeViewSummary(endpoint, 'detail')
      + '<p><button data-back-view="true">' + esc(label('button.back_current_list', 'Back to current list')) + '</button> '
      + (previousDetail ? '<button data-back-detail="true">' + esc(label('button.back_previous_detail', 'Back to previous detail')) + '</button> ' : '')
      + (hasActiveFilters() ? '<button data-reset-filters="all">' + esc(label('button.reset_filter', 'Reset Filter')) + '</button> ' : '')
      + '<span class="id">' + esc(window.__chronicleCurrentEndpoint || '/api/overview') + '</span> → '
      + '<span class="id">' + esc(endpoint) + '</span>'
      + (filterLabel ? ' <span class="id">(' + esc(filterLabel) + ')</span>' : '')
      + (previousDetail ? ' <span class="id">prev=' + esc(previousDetail) + '</span>' : '')
      + '</p>'
      + (trailLabel ? '<p><span class="id">trail=' + esc(trailLabel) + '</span></p>' : '')
      + (trailButtons ? '<p>' + trailButtons + '</p>' : '')
      + (listButtons ? '<p>' + listButtons + '</p>' : '')
  );
}}
function renderRuntimePreviewNotice(record) {{
  if (!record.runtime_record_preview) return '';
  const preview = record.runtime_record_preview;
  return renderNotice(
    label('notice.runtime_preview', 'Runtime Preview'),
    '<p><strong>' + esc(preview.title || '') + '</strong></p>'
      + '<p>' + esc(preview.preview_text || '') + '</p>'
      + detailLine('Kind', preview.record_kind || record.runtime_record_kind || '')
      + summaryJsonLine('Source counts', preview.source_counts)
      + detailListLine('Referenced IDs', preview.referenced_record_ids)
      + detailLine('CLI', preview.suggested_cli_family || '')
  );
}}
function renderRetrievalHandoffNotice(record) {{
  if (!record.retrieval_handoff) return '';
  const handoff = record.retrieval_handoff;
  return renderNotice(
    label('notice.retrieval_handoff', 'Retrieval Handoff'),
    detailLine('Query', handoff.query || '')
      + '<p>Hit counts: vector=' + esc(handoff.vector_hit_count || 0)
      + ', graph=' + esc(handoff.graph_hit_count || 0)
      + ', chronicle=' + esc(handoff.chronicle_hit_count || 0) + '</p>'
      + detailListLine('Referenced IDs', handoff.referenced_record_ids)
      + detailListLine('Downstream commands', handoff.downstream_commands, ' | ')
      + detailListLine('Notes', handoff.notes, ' | ')
  );
}}
function renderPackageHandoffPreviewNotice(record) {{
  if (!record.package_handoff_preview) return '';
  const preview = record.package_handoff_preview;
  const packageReview = preview.package_review || {{}};
  const manifest = preview.package_manifest_preview || {{}};
  return renderNotice(
    label('notice.package_handoff_preview', 'Package Handoff Preview'),
    statusMessageBody(preview.status, preview.message)
      + detailListLine('Eligible contexts', preview.eligible_context_ids)
      + detailListLine('Skipped records', preview.skipped_record_ids)
      + detailLine('Package review status', packageReview.status || '(not available)')
      + detailListLine('Package warnings', packageReview.package_warnings)
      + detailListLine('Manifest refs', manifest.referenced_records)
  );
}}
function renderInvocationPlanNotice(record) {{
  if (!record.invocation_plan) return '';
  const plan = record.invocation_plan;
  const requestPreview = plan.request_preview || {{}};
  return renderNotice(
    label('notice.invocation_plan', 'Invocation Plan'),
    detailLine('Provider', (plan.provider_kind || '') + ' / ' + (plan.provider_name || ''))
      + detailLine('Model', plan.model_name || '')
      + detailLine('Operation', plan.operation || '')
      + detailLine('Invocation ready', plan.invocation_ready)
      + detailLine('Would use network', plan.would_use_network)
      + detailLine('Network allowed by contract', plan.network_allowed_by_contract)
      + detailListLine('Blocking reasons', plan.blocking_reasons, ' | ')
      + summaryJsonLine('Request preview', requestPreview)
      + detailListLine('Downstream commands', plan.downstream_commands, ' | ')
      + detailListLine('Notes', plan.notes, ' | ')
  );
}}
function renderResponseMetadataNotice(record) {{
  if (!record.response_metadata_summary || !record.response_metadata_summary.present) return '';
  const summary = record.response_metadata_summary;
  return renderNotice(
    label('notice.provider_response', 'Provider Response'),
    detailLine('Response ID', summary.response_id || '')
      + detailLine('Finish reason', summary.finish_reason || '')
      + detailLine('Provider status', summary.provider_status || '')
      + detailLine('Usage input tokens', summary.usage_input_tokens ?? '')
      + detailLine('Usage output tokens', summary.usage_output_tokens ?? '')
      + detailLine('Usage total tokens', summary.usage_total_tokens ?? '')
      + detailLine('Metadata fields', summary.metadata_count ?? 0)
      + detailLine('Top-level response keys', summary.response_key_count ?? 0)
      + detailListLine('Response keys', summary.response_keys, ' | ')
  );
}}
function renderPackageReadinessNotice(record) {{
  if (!record.package_readiness) return '';
  const readiness = record.package_readiness;
  const packageReview = readiness.package_review || {{}};
  const manifest = readiness.package_manifest_preview || {{}};
  const readinessButtons = moreStatusButtons(readiness.status, '/api/review-queue', 'reviewQueue', 'package:');
  return renderNotice(
    label('notice.review_package_readiness', 'Review Package Readiness'),
    statusMessageBody(readiness.status, readiness.message, readinessButtons)
      + detailListLine('Eligible contexts', readiness.eligible_context_ids)
      + detailListLine('Suggested commands', readiness.suggested_commands, ' | ')
      + detailLine('Package review status', packageReview.status || '(not available)')
      + detailListLine('Package warnings', packageReview.package_warnings)
      + detailListLine('Manifest refs', manifest.referenced_records)
  );
}}
function renderRelatedLinksNotice(record) {{
  if (!Array.isArray(record.related_links) || record.related_links.length === 0) return '';
  return renderNotice(
    label('notice.related_links', 'Related Links'),
    '<p>' + record.related_links.map(item =>
      '<button data-detail-nav="' + esc(item.path || '') + '">'
      + esc(localizeTextValue(item.label || humanizeDetailPath(item.path || '')))
      + '</button>'
    ).join('') + '</p>'
  );
}}
function renderAuthReadinessNotice(record) {{
  if (!record.auth_boundary_notice) return '';
  const notice = record.auth_boundary_notice;
  const blockerDetails = Array.isArray(notice.blocker_details) ? notice.blocker_details : [];
  const noticeButtons = moreStatusButtons(notice.status, '/api/review-queue', 'reviewQueue');
  return renderNotice(
    label('notice.auth_readiness', 'Auth Readiness'),
    statusMessageBody(notice.status, notice.message, noticeButtons)
      + detailLine('Review capability', notice.capability_status || '')
      + detailLine('Identity assurance', notice.identity_assurance_status || '')
      + detailLine('Blockers', detailMessages(blockerDetails, notice.blockers))
      + detailListLine('Next steps', notice.next_steps, ' | ')
  );
}}
function renderReviewCapabilityNotice(record) {{
  if (!record.review_capability) return '';
  const capability = record.review_capability;
  const warnList = Array.isArray(capability.warnings) ? capability.warnings : [];
  const warnDetails = Array.isArray(capability.warning_details) ? capability.warning_details : [];
  const warnBadges = reviewWarningBadges(warnList);
  return renderNotice(
    label('notice.review_capability', 'Review Capability'),
    messageParagraph(capability.message)
      + detailLine('Status', capability.status || '')
      + (warnBadges ? '<p>' + warnBadges + '</p>' : '')
      + detailLine('Warnings', detailMessages(warnDetails, warnList) || '(none)')
  );
}}
function renderMutationEnablementNotice(record) {{
  if (!record.mutation_enablement) return '';
  const readiness = record.mutation_enablement;
  const blockerDetails = Array.isArray(readiness.blocker_details) ? readiness.blocker_details : [];
  const blockerSummaries = Array.isArray(readiness.blocker_summaries) ? readiness.blocker_summaries : [];
  const enablementChecks = Array.isArray(readiness.enablement_checks) ? readiness.enablement_checks : [];
  const operationalReadiness = readiness.operational_readiness || {{}};
  const reviewerContext = readiness.reviewer_context_requirements || {{}};
  const writeRouteContract = readiness.write_route_contract || {{}};
  const identityProofContract = writeRouteContract.identity_proof_contract || {{}};
  const readinessButtons = moreStatusButtons(readiness.status, '/api/review-queue', 'reviewQueue');
  return renderNotice(
    label('notice.mutation_enablement', 'Mutation Enablement'),
    statusMessageBody(readiness.status, readiness.message, readinessButtons)
      + detailLine('Enablement ready', readiness.enablement_ready)
      + detailLine('Enablement checks', String(readiness.enablement_satisfied_count ?? 0) + '/' + String(readiness.enablement_required_count ?? 0))
      + detailLine('Operational readiness', operationalReadiness.status || '')
      + detailLine('Operational summary', operationalReadiness.message || '')
      + detailLine('Remaining prerequisites', operationalReadiness.remaining_count ?? 0)
      + detailLine('Blockers', detailMessages(blockerDetails, readiness.blockers))
      + detailListLine('Blocker sources', blockerSummaries.map(item => ((item.source || 'unknown') + ':' + (item.code || 'blocker') + '=' + String(item.affected_count ?? 0))), ' | ')
      + detailListLine('Checks', enablementChecks.map(check => ((check.satisfied ? 'ok: ' : 'blocked: ') + (check.label || check.code || 'check'))), ' | ')
      + detailListLine('Remaining checks', (operationalReadiness.unsatisfied_checks || []).map(item => ((item.label || item.code || 'check') + ': ' + (item.detail || ''))), ' | ')
      + detailListLine('Reviewer fields', reviewerContext.effective_required_fields, ' | ')
      + detailListLine('Reviewer kinds', reviewerContext.accepted_reviewer_kinds, ' | ')
      + detailLine('Reviewer label pattern', reviewerContext.reviewer_label_pattern || '')
      + detailListLine('Reviewer label examples', reviewerContext.reviewer_label_examples, ' | ')
      + detailLine('Session label pattern', reviewerContext.session_label_pattern || '')
      + detailLine('Write route', writeRouteContract.route_template || '')
      + detailListLine('Write actions', writeRouteContract.actions, ' | ')
      + detailLine('Write success status', writeRouteContract.success_status_code ?? '')
      + detailLine('Write blocked status', writeRouteContract.blocked_status_code ?? '')
      + detailLine('Identity proof status', identityProofContract.proof_status || '')
      + detailListLine('Identity proof fields', identityProofContract.required_identity_fields, ' | ')
      + detailListLine('Next steps', readiness.next_steps, ' | ')
  );
}}
function renderDetailActionPreviewControls(preview, actions, mutationTargetEventId) {{
  const activeActionButtons = actions.map(item =>
    '<button data-submit-review-action="' + esc(item.post_path || '') + '" data-review-action="' + esc(item.action || '') + '" data-review-record="' + esc(mutationTargetEventId) + '">'
    + esc(item.label || item.action || 'Apply')
    + '</button>'
  ).join(' ');
  return preview.ui_mutation_enabled
    ? '<p><label>' + esc(localizeTextValue('Reviewer')) + ' <input id="reviewer-label" value="local-ui" placeholder="' + esc(t('placeholder.reviewer')) + '"></label> '
      + '<label>' + esc(localizeTextValue('Kind')) + ' <select id="reviewer-kind"><option value="local_operator">local_operator</option><option value="user_declared">user_declared</option></select></label> '
      + '<label>' + esc(localizeTextValue('Session')) + ' <input id="reviewer-session-label" value="local-ui-session" placeholder="' + esc(t('placeholder.session')) + '"></label></p>'
      + '<p><label>' + esc(localizeTextValue('Note')) + ' <input id="reviewer-note" placeholder="' + esc(t('placeholder.review_note')) + '"></label></p>'
      + '<p>' + activeActionButtons + '</p>'
    : '<p><button disabled>' + esc(localizeTextValue('Approve')) + '</button> <button disabled>' + esc(localizeTextValue('Reject')) + '</button> <button disabled>' + esc(localizeTextValue('Request Changes')) + '</button></p>';
}}
function renderDetailActionPreviewList(preview, actions) {{
  return '<ul>' + actions.map(item =>
    '<li><strong>' + esc(item.label || '') + ':</strong> <span class="id">' + esc(item.command || '') + '</span>'
    + (item.command ? ' ' + copyCommandButton(item.command, 'action-preview-response') : '')
    + (item.post_path
      ? (
          preview.ui_mutation_enabled
            ? '<br><span class="id">' + esc(item.post_path || '') + '</span> <span class="id">' + esc(localizeTextValue('POST enabled')) + '</span>'
            : '<br><span class="id">' + esc(item.post_path || '') + '</span> <button data-preview-post="' + esc(item.post_path || '') + '">' + esc(localizeTextValue('Preview blocked route')) + '</button>'
        )
      : '')
    + '</li>'
  ).join('') + '</ul>';
}}
function renderDetailActionPreviewNotice(record) {{
  if (!record.action_preview) return '';
  const preview = record.action_preview;
  const actions = Array.isArray(preview.actions) ? preview.actions : [];
  const failureContract = preview.failure_contract || {{}};
  const capability = record.review_capability || {{}};
  const parity = record.cli_parity || {{}};
  const mutationTargetEventId = record.target_event_id || record.review_target_event_id || record.event_id || '';
  const previewButtons = [
    ...moreStatusButtons(capability.status, '/api/review-queue', 'reviewQueue'),
    ...moreStatusButtons(parity.status, '/api/review-queue', 'reviewQueue'),
  ];
  const recoveryContractSection = noticeSection(
    label('section.recovery_contract', 'Recovery Contract'),
    detailLine('Rollback status', failureContract.rollback_status || '')
      + detailLine('Durable mutation on failure', failureContract.durable_mutation_reported_on_failure)
      + detailLine('Recovery path', failureContract.recovery_path || '')
      + detailListLine('Possible errors', failureContract.possible_error_codes, ' | ')
      + detailListLine('Recovery commands', failureContract.recovery_commands, ' | ')
      + (failureContract.recovery_path ? '<p>' + copyCommandButton(failureContract.recovery_path, 'action-preview-response', t('button.copy_recovery_cli')) + '</p>' : '')
      + ((failureContract.recovery_commands || []).length > 0 ? '<p>' + (failureContract.recovery_commands || []).map(command => copyCommandButton(command, 'action-preview-response', t('button.copy_cli'))).join(' ') + '</p>' : '')
  );
  const reviewActionSection = noticeSection(
    label('section.review_action', 'Review Action'),
    renderDetailActionPreviewControls(preview, actions, mutationTargetEventId)
      + renderDetailActionPreviewList(preview, actions)
  );
  const actionResultSection = noticeSection(
    label('section.action_result', 'Current Result'),
    '<div id="action-preview-response"><p>'
      + (
        preview.ui_mutation_enabled
          ? t('notice.mutation_enabled_detail')
          : t('notice.blocked_route_preview_detail')
      )
      + '</p></div>'
  );
  return renderNotice(
    label('notice.action_preview', 'Action Preview'),
    noticeSection(
      label('status.detail', 'Detail'),
      messageParagraph(preview.message)
        + detailLine('Status', preview.status || '')
        + buttonRow(previewButtons)
    )
      + recoveryContractSection
      + reviewActionSection
      + actionResultSection
  );
}}
function renderCliParityNotice(record) {{
  if (!record.cli_parity) return '';
  const parity = record.cli_parity;
  const parityButtons = moreStatusButtons(parity.status, '/api/review-queue', 'reviewQueue');
  return renderNotice(
    label('notice.cli_parity', 'CLI Parity'),
    messageParagraph(parity.message)
      + detailLine('Status', parity.status || '')
      + buttonRow(parityButtons)
      + detailListLine('Expected actions', parity.expected_actions)
      + detailListLine('Missing preview commands', parity.missing_preview_commands, ' | ')
      + detailListLine('Missing queue commands', parity.missing_queue_commands, ' | ')
  );
}}
function renderIdentityAssuranceNotice(record) {{
  if (!record.latest_identity_assurance) return '';
  const assurance = record.latest_identity_assurance;
  const assuranceButtons = moreStatusButtons(assurance.status, '/api/review-queue', 'reviewQueue');
  return renderNotice(
    label('notice.identity_assurance', 'Identity Assurance'),
    statusMessageBody(assurance.status, assurance.message, assuranceButtons)
  );
}}
function renderReviewTimelineNotice(record) {{
  if (!Array.isArray(record.history) || record.history.length === 0) return '';
  return renderNotice(
    label('notice.review_timeline', 'Review Timeline'),
    '<ul>' + record.history.map(item => {{
      const timelineButtons = [
        ...moreStatusButtons(item.disposition, '/api/review-queue', 'reviewQueue'),
        ...moreStatusButtons(item.identity_assurance && item.identity_assurance.status, '/api/review-queue', 'reviewQueue'),
      ];
      return '<li>'
        + esc(item.reviewed_at || '') + ' — '
        + esc(item.disposition || '') + ' by '
        + esc((item.reviewer_identity && item.reviewer_identity.label) || item.reviewer || '')
        + ' (' + esc((item.identity_assurance && item.identity_assurance.status) || '') + ')'
        + (timelineButtons.length > 0 ? '<br>' + timelineButtons.join('') : '')
        + '</li>';
      }}).join('') + '</ul>'
  );
}}
async function responseJsonOrEmpty(response) {{
  try {{
    return await response.json();
  }} catch (_error) {{
    return {{}};
  }}
}}
async function postJson(path, body = undefined) {{
  const options = {{ method: 'POST' }};
  if (body !== undefined) {{
    options.headers = {{ 'Content-Type': 'application/json' }};
    options.body = JSON.stringify(body);
  }}
  const response = await fetch(path, options);
  const payload = await responseJsonOrEmpty(response);
  return {{ response, payload }};
}}
function appendCommandFeedback(target, command, copied) {{
  if (!target) return;
  target.innerHTML += '<p>' + esc(copied ? t('status.copied_recovery_cli') : t('status.copy_failed_command')) + '<span class="id">' + esc(command) + '</span></p>';
}}
async function tryCopyText(command) {{
  if (navigator.clipboard && navigator.clipboard.writeText) {{
    try {{
      await navigator.clipboard.writeText(command);
      return true;
    }} catch (_error) {{
      return false;
    }}
  }}
  const textArea = document.createElement('textarea');
  textArea.value = command;
  textArea.setAttribute('readonly', 'readonly');
  textArea.style.position = 'absolute';
  textArea.style.left = '-9999px';
  document.body.appendChild(textArea);
  textArea.select();
  const copied = document.execCommand('copy');
  document.body.removeChild(textArea);
  return copied;
}}
function reviewActionRequestBody(action, fieldPrefix = 'reviewer') {{
  return {{
    reviewer_label: reviewFieldValue(fieldPrefix, 'reviewer-label', ''),
    reviewer_kind: reviewFieldValue(fieldPrefix, 'reviewer-kind', 'local_operator') || 'local_operator',
    session_label: reviewFieldValue(fieldPrefix, 'reviewer-session-label', ''),
    note: reviewFieldValue(fieldPrefix, 'reviewer-note', ''),
    ui_intent: action || '',
  }};
}}
function reloadCurrentEndpoint() {{
  if (window.__chronicleCurrentEndpoint) loadEndpoint(window.__chronicleCurrentEndpoint);
}}
function applyJumpFilter(filterTarget, filterValue) {{
  setFilterValue(filterTarget, filterValue);
}}
function updateFilterState(filterId, value) {{
  setFilterValue(filterId, value);
}}
function updateSortState(sortId, value) {{
  setSortValue(sortId, value);
}}
function handleDetailTrailNavigation(target) {{
  if (!target) return;
  const index = window.__chronicleDetailTrail.lastIndexOf(target);
  if (index >= 0) window.__chronicleDetailTrail = window.__chronicleDetailTrail.slice(0, index);
  window.__chronicleLastDetail = '';
  loadDetail(target);
}}
function handleBackDetail() {{
  if (window.__chronicleDetailTrail.length <= 0) return;
  const previousDetail = window.__chronicleDetailTrail.pop();
  if (!previousDetail) return;
  window.__chronicleLastDetail = '';
  loadDetail(previousDetail);
}}
function handleViewClick(event) {{
  if (event.target.dataset.copyCommand) {{
    copyCommand(
      event.target.dataset.copyCommand,
      event.target.dataset.copyTarget || 'review-queue-action-preview-response',
    );
  }}
  if (event.target.dataset.detail) loadDetail(event.target.dataset.detail);
  if (event.target.dataset.jump) {{
    applyJumpFilter(event.target.dataset.filterTarget, event.target.dataset.filterValue || '');
    loadEndpoint(event.target.dataset.jump);
  }}
  if (event.target.dataset.resetFilter) {{
    resetFilters(event.target.dataset.resetFilter);
    reloadCurrentEndpoint();
  }}
  if (event.target.dataset.resetFilters) {{
    resetFilters(event.target.dataset.resetFilters);
    reloadCurrentEndpoint();
  }}
}}
function handleDetailClick(event) {{
  if (event.target.dataset.copyCommand) copyCommand(event.target.dataset.copyCommand, event.target.dataset.copyTarget || 'action-preview-response');
  if (event.target.dataset.previewPost) previewBlockedRoute(event.target.dataset.previewPost);
  if (event.target.dataset.submitReviewAction) {{
    submitReviewAction(
      event.target.dataset.submitReviewAction,
      event.target.dataset.reviewAction || '',
      event.target.dataset.reviewRecord || '',
      event.target.dataset.previewTarget || 'action-preview-response',
      event.target.dataset.reviewFields || 'reviewer',
      event.target.dataset.successDetail || '',
    );
  }}
  if (event.target.dataset.detailNav) loadDetail(event.target.dataset.detailNav);
  if (event.target.dataset.detailTrail) handleDetailTrailNavigation(event.target.dataset.detailTrail);
  if (event.target.dataset.backDetail) handleBackDetail();
  if (event.target.dataset.resetFilters) {{
    resetFilters(event.target.dataset.resetFilters);
    reloadCurrentEndpoint();
  }}
  if (event.target.dataset.backView) reloadCurrentEndpoint();
}}
function handleViewPreviewPost(event) {{
  if (!event.target.dataset.previewPost) return;
  previewBlockedRoute(
    event.target.dataset.previewPost,
    event.target.dataset.previewTarget || 'review-queue-action-preview-response',
  );
}}
function handleViewInput(event) {{
  const filterId = event.target.dataset.filterInput;
  if (!filterId) return;
  updateFilterState(filterId, event.target.value || '');
  reloadCurrentEndpoint();
}}
function handleViewChange(event) {{
  const sortId = event.target.dataset.sortInput;
  if (!sortId || !window.__chronicleSorts) return;
  updateSortState(sortId, event.target.value || '');
  reloadCurrentEndpoint();
}}
function renderPanel(body) {{
  return '<div class="panel">' + body + '</div>';
}}
function renderOverviewHeaderPanel(chronicle) {{
  return renderPanel(
    '<p><strong>' + esc(chronicle.title || '') + '</strong></p>'
    + '<p>' + esc(localizeTextValue('Chronicle ID')) + ': <span class="id">' + esc(chronicle.id || '') + '</span></p>'
    + '<p>' + esc(localizeTextValue('Root')) + ': <span class="id">' + esc(chronicle.root || '') + '</span></p>'
  );
}}
function renderOverviewCountsPanel(counts) {{
  const countRows = Object.entries(counts || {{}}).map(([key, value]) =>
    '<tr><th>' + esc(key) + '</th><td>' + esc(value ?? '') + '</td></tr>'
  ).join('');
  return renderPanel(
    sectionTitle(label('section.counts', 'Counts'))
    + '<table><tbody>' + countRows + '</tbody></table>'
  );
}}
function renderOverviewRuntimeBoundaryPanel(runtime) {{
  return renderPanel(
    sectionTitle(label('section.runtime_boundary', 'Runtime Boundary'))
    + detailLine('Read-only', runtime.read_only)
    + detailLine('External model API', runtime.external_model_api)
    + detailLine('GraphRAG runtime', runtime.graphrag_runtime)
    + detailLine('Vector DB', runtime.vector_db)
    + detailLine('Graph DB', runtime.graph_db)
  );
}}
function renderOverviewRuntimeConfigPanel(runtimeConfig, runtimeConfigContract) {{
  return renderPanel(
    sectionTitle(label('section.runtime_config', 'Runtime Config'))
    + detailLine('Source', runtimeConfig.source || '')
    + detailLine('Provider kind', runtimeConfigContract.provider_kind || '')
    + detailLine('Provider name', runtimeConfigContract.provider_name || '')
    + detailLine('Model', runtimeConfigContract.model_name || '')
    + detailLine('Allow network', runtimeConfigContract.allow_network)
    + detailLine('Allow external context', runtimeConfigContract.allow_external_context)
    + detailListLine('Warnings', runtimeConfig.warnings, ' | ')
    + '<p>' + listJumpButton(label('button.open_runtime_config', 'Open Runtime Config'), '/api/runtime-config') + '</p>'
  );
}}
function renderOverviewUiBoundaryPanel(uiBoundary) {{
  const writeRouteContract = uiBoundary.write_route_contract || {{}};
  const identityProofContract = writeRouteContract.identity_proof_contract || {{}};
  return renderPanel(
    sectionTitle(label('section.ui_boundary', 'UI Boundary'))
    + detailLine('Bind scope', uiBoundary.bind_scope || '')
    + detailLine('Mutation enabled', uiBoundary.mutation_enabled)
    + detailLine('Mutation capability flag', uiBoundary.mutation_capability_flag)
    + detailLine('Auth mode', uiBoundary.auth_mode || '')
    + detailLine('Authorization mode', uiBoundary.authorization_mode || '')
    + detailLine('Session gating', uiBoundary.session_gating)
    + detailLine('Mutation readiness', uiBoundary.mutation_readiness_status || '')
    + detailLine('Write route', writeRouteContract.route_template || '')
    + detailListLine('Write actions', writeRouteContract.actions, ' | ')
    + detailListLine('Write request fields', writeRouteContract.expected_request_fields, ' | ')
    + detailLine('Write success status', writeRouteContract.success_status_code ?? '')
    + detailLine('Write blocked status', writeRouteContract.blocked_status_code ?? '')
    + detailLine('Identity proof status', identityProofContract.proof_status || '')
    + detailListLine('Identity proof fields', identityProofContract.required_identity_fields, ' | ')
  );
}}
function renderOverviewAuthBoundaryPanel(authBoundary, authBoundaryOverview) {{
  const metricsSection = collapsibleSection(
    label('section.metrics', 'Metrics'),
    summaryJsonLine('Auth review capability counts', authBoundaryOverview.review_capability_counts)
      + summaryJsonLine('Provider finish reasons', authBoundaryOverview.provider_response_finish_reason_counts)
      + summaryJsonLine('Provider statuses', authBoundaryOverview.provider_response_status_counts),
    false
  );
  return renderPanel(
    sectionTitle(label('section.auth_boundary', 'Auth Boundary'))
    + '<p>'
    + overviewJumpButton(sliceBadge('Auth Boundary Warnings', esc(authBoundaryOverview.auth_warning_count ?? 0), 'badge-warning'), '/api/review-queue', 'reviewQueue', 'ui_auth_not_enabled')
    + overviewJumpButton(sliceBadge(label('overview.authorization_warnings', 'Authorization warnings'), esc(authBoundaryOverview.authorization_warning_count ?? 0), 'badge-warning'), '/api/review-queue', 'reviewQueue', 'ui_authorization_not_enabled')
    + overviewJumpButton(sliceBadge(label('overview.missing_identity', 'Missing identity'), esc(authBoundaryOverview.missing_identity_count ?? 0), 'badge-warning'), '/api/review-queue', 'reviewQueue', 'no_reviewer_identity_recorded')
    + overviewJumpButton(sliceBadge(label('overview.provider_response', 'Provider response'), esc(authBoundaryOverview.provider_response_present_count ?? 0), 'badge-ready'), '/api/review-queue', 'reviewQueue', 'response_id')
    + '</p>'
    + detailLine('Status', authBoundary.status || '')
    + '<p>' + esc(authBoundary.message || '') + '</p>'
    + detailLine('Session gating', authBoundary.session_gating)
    + detailLine('Shared machine safe', authBoundary.shared_machine_safe)
    + metricsSection
    + detailListLine('Auth blockers', authBoundary.blockers, ' | ')
    + detailListLine('Auth next steps', authBoundary.next_steps, ' | ')
  );
}}
function renderOverviewIdentityBoundaryPanel(identityBoundary) {{
  const metricsSection = collapsibleSection(
    label('section.metrics', 'Metrics'),
    summaryJsonLine('Identity assurance counts', identityBoundary.assurance_counts),
    false
  );
  return renderPanel(
    sectionTitle(label('section.identity_boundary', 'Identity Boundary'))
    + '<p>'
    + overviewJumpButton(sliceBadge(localizeTextValue('Declared identity only'), esc(identityBoundary.declared_identity_count ?? 0), 'badge-warning'), '/api/review-queue', 'reviewQueue', 'reviewer_identity_declared_only')
    + overviewJumpButton(sliceBadge(label('overview.session_label_required', 'Session label required'), esc(identityBoundary.session_label_missing_count ?? 0), 'badge-warning'), '/api/review-queue', 'reviewQueue', 'reviewer_session_label_missing')
    + overviewJumpButton(sliceBadge(localizeTextValue('Identity aligned'), esc((identityBoundary.assurance_counts && identityBoundary.assurance_counts.boundary_aligned) ?? 0), 'badge-ready'), '/api/review-queue', 'reviewQueue', 'boundary_aligned')
    + '</p>'
    + detailLine('Status', identityBoundary.status || '')
    + '<p>' + esc(identityBoundary.message || '') + '</p>'
    + metricsSection
    + detailLine('Missing identity rows', identityBoundary.missing_identity_count ?? 0)
    + detailLine('Declared-only rows', identityBoundary.declared_identity_count ?? 0)
    + detailLine('Session-label-missing rows', identityBoundary.session_label_missing_count ?? 0)
    + detailListLine('Identity blockers', identityBoundary.blockers, ' | ')
    + detailListLine('Identity next steps', identityBoundary.next_steps, ' | ')
  );
}}
function renderOverviewMutationReadinessPanel(mutationReadiness) {{
  const blockerDetails = Array.isArray(mutationReadiness.blocker_details) ? mutationReadiness.blocker_details : [];
  const blockerSummaries = Array.isArray(mutationReadiness.blocker_summaries) ? mutationReadiness.blocker_summaries : [];
  const reviewerContextRequirements = mutationReadiness.reviewer_context_requirements || {{}};
  const writeRouteContract = mutationReadiness.write_route_contract || {{}};
  const identityProofContract = writeRouteContract.identity_proof_contract || {{}};
  const enablementChecks = Array.isArray(mutationReadiness.enablement_checks) ? mutationReadiness.enablement_checks : [];
  const operationalReadiness = mutationReadiness.operational_readiness || {{}};
  return renderPanel(
    sectionTitle(label('section.mutation_readiness', 'Mutation Readiness'))
    + detailLine('Status', mutationReadiness.status || '')
    + '<p>' + esc(mutationReadiness.message || '') + '</p>'
    + detailLine('Ready rows', mutationReadiness.ready_row_count ?? 0)
    + detailLine('Advisory rows', mutationReadiness.advisory_row_count ?? 0)
    + detailLine('Enablement ready', mutationReadiness.enablement_ready)
    + detailLine('Enablement checks', String(mutationReadiness.enablement_satisfied_count ?? 0) + '/' + String(mutationReadiness.enablement_required_count ?? 0))
    + detailLine('Operational readiness', operationalReadiness.status || '')
    + detailLine('Operational summary', operationalReadiness.message || '')
    + detailLine('Remaining prerequisites', operationalReadiness.remaining_count ?? 0)
    + detailListLine('Blockers', mutationReadiness.blockers, ' | ')
    + detailLine('Blocker details', detailMessages(blockerDetails, mutationReadiness.blockers))
    + detailListLine('Blocker sources', blockerSummaries.map(item => ((item.source || 'unknown') + ':' + (item.code || 'blocker') + '=' + String(item.affected_count ?? 0))), ' | ')
    + detailListLine('Enablement checks', enablementChecks.map(check => ((check.satisfied ? 'ok: ' : 'blocked: ') + (check.label || check.code || 'check'))), ' | ')
    + detailListLine('Remaining checks', (operationalReadiness.unsatisfied_checks || []).map(item => ((item.label || item.code || 'check') + ': ' + (item.detail || ''))), ' | ')
    + detailListLine('Effective reviewer fields', reviewerContextRequirements.effective_required_fields, ' | ')
    + detailListLine('Reviewer fields', reviewerContextRequirements.required_fields, ' | ')
    + detailListLine('Accepted reviewer kinds', reviewerContextRequirements.accepted_reviewer_kinds, ' | ')
    + detailLine('Reviewer label pattern', reviewerContextRequirements.reviewer_label_pattern || '')
    + detailListLine('Reviewer label examples', reviewerContextRequirements.reviewer_label_examples, ' | ')
    + detailLine('Session label required', reviewerContextRequirements.session_label_required)
    + detailLine('Session label pattern', reviewerContextRequirements.session_label_pattern || '')
    + detailLine('Write route', writeRouteContract.route_template || '')
    + detailListLine('Write actions', writeRouteContract.actions, ' | ')
    + detailListLine('Write request fields', writeRouteContract.expected_request_fields, ' | ')
    + detailLine('Write success status', writeRouteContract.success_status_code ?? '')
    + detailLine('Write blocked status', writeRouteContract.blocked_status_code ?? '')
    + detailLine('Identity proof status', identityProofContract.proof_status || '')
    + detailListLine('Identity proof fields', identityProofContract.required_identity_fields, ' | ')
    + detailListLine('Next steps', mutationReadiness.next_steps, ' | ')
  );
}}
function renderOverviewAiIndexPanel(aiIndex, counts) {{
  const vectorEntryCount = aiIndex.vector && aiIndex.vector.entry_count ? aiIndex.vector.entry_count : 0;
  const graphNodeCount = aiIndex.graph && aiIndex.graph.node_count ? aiIndex.graph.node_count : 0;
  const graphEdgeCount = aiIndex.graph && aiIndex.graph.edge_count ? aiIndex.graph.edge_count : 0;
  return renderPanel(
    sectionTitle(label('section.ai_index_snapshot', 'AI Index Snapshot'))
    + detailLine('Vector entries', vectorEntryCount)
    + detailLine('Graph nodes', graphNodeCount)
    + detailLine('Graph edges', graphEdgeCount)
    + detailLine('Runtime records', counts.runtime_records ?? 0)
    + detailLine('Summary jobs', counts.summary_jobs ?? 0)
    + detailLine('Needs-review records', counts.review_queue ?? 0)
  );
}}
function renderOverviewRuntimeRecordsPanel(counts, runtimeRecords) {{
  const metricsSection = collapsibleSection(
    label('section.metrics', 'Metrics'),
    summaryJsonLine('Runtime kinds', runtimeRecords.kind_counts)
      + summaryJsonLine('Auth readiness counts', runtimeRecords.auth_readiness_counts)
      + summaryJsonLine('Mutation readiness counts', runtimeRecords.mutation_readiness_counts)
      + summaryJsonLine('Mutation operational counts', runtimeRecords.mutation_operational_counts)
      + summaryJsonLine('Provider finish reasons', runtimeRecords.provider_response_finish_reason_counts)
      + summaryJsonLine('Provider statuses', runtimeRecords.provider_response_status_counts),
    false
  );
  return renderPanel(
    sectionTitle(label('section.runtime_records', 'Runtime Records'))
    + '<p>'
    + overviewJumpButton(sliceBadge(localizeTextValue('Runtime records'), esc(counts.runtime_records ?? 0), 'badge-neutral'), '/api/runtime-records')
    + overviewJumpButton(sliceBadge(label('overview.provider_response', 'Provider response'), esc(runtimeRecords.provider_response_present_count ?? 0), 'badge-ready'), '/api/runtime-records', 'runtimeRecords', 'response_id')
    + overviewJumpButton(sliceBadge(localizeTextValue('Runtime auth advisory'), esc((runtimeRecords.auth_readiness_counts && runtimeRecords.auth_readiness_counts.advisory_only) ?? 0), 'badge-warning'), '/api/runtime-records', 'runtimeRecords', 'advisory_only')
    + overviewJumpButton(sliceBadge(localizeTextValue('Runtime mutation preview'), esc((runtimeRecords.mutation_readiness_counts && runtimeRecords.mutation_readiness_counts.preview_only) ?? 0), 'badge-warning'), '/api/runtime-records', 'runtimeRecords', 'preview_only')
    + '</p>'
    + metricsSection
    + sliceButtonRow(runtimeRecordsSliceButtons())
    + '<p>' + listJumpButton(label('button.open_runtime_records', 'Open Runtime Records'), '/api/runtime-records') + '</p>'
  );
}}
function renderOverviewSummaryJobsPanel(counts, summaryJobs) {{
  const metricsSection = collapsibleSection(
    label('section.metrics', 'Metrics'),
    summaryJsonLine('Status counts', summaryJobs.status_counts)
      + summaryJsonLine('Review capability counts', summaryJobs.review_capability_counts)
      + summaryJsonLine('Auth readiness counts', summaryJobs.auth_readiness_counts)
      + summaryJsonLine('Package readiness counts', summaryJobs.package_readiness_counts)
      + summaryJsonLine('Mutation readiness counts', summaryJobs.mutation_readiness_counts)
      + summaryJsonLine('Mutation operational counts', summaryJobs.mutation_operational_counts)
      + summaryJsonLine('Provider finish reasons', summaryJobs.provider_response_finish_reason_counts)
      + summaryJsonLine('Provider statuses', summaryJobs.provider_response_status_counts)
      + summaryJsonLine('Identity assurance counts', summaryJobs.identity_assurance_counts)
      + summaryJsonLine('Reviewer kind counts', summaryJobs.reviewer_kind_counts)
      + summaryJsonLine('Runtime provider counts', summaryJobs.runtime_provider_counts),
    false
  );
  return renderPanel(
    sectionTitle(label('section.summary_jobs', 'Summary Jobs'))
    + '<p>'
    + overviewJumpButton(sliceBadge(localizeTextValue('Summary jobs'), esc(counts.summary_jobs ?? 0), 'badge-neutral'), '/api/summary-jobs')
    + overviewJumpButton(sliceBadge(label('overview.provider_response', 'Provider response'), esc(summaryJobs.provider_response_present_count ?? 0), 'badge-ready'), '/api/summary-jobs', 'summaryJobs', 'response_id')
    + overviewJumpButton(sliceBadge(localizeTextValue('Summary advisory'), esc((summaryJobs.review_capability_counts && summaryJobs.review_capability_counts.advisory_only) ?? 0), 'badge-warning'), '/api/summary-jobs', 'summaryJobs', 'advisory_only')
    + overviewJumpButton(sliceBadge(localizeTextValue('Summary auth advisory'), esc((summaryJobs.auth_readiness_counts && summaryJobs.auth_readiness_counts.advisory_only) ?? 0), 'badge-warning'), '/api/summary-jobs', 'summaryJobs', 'advisory_only')
    + overviewJumpButton(sliceBadge(localizeTextValue('Summary package ready'), esc((summaryJobs.package_readiness_counts && summaryJobs.package_readiness_counts.package_context_available) ?? 0), 'badge-ready'), '/api/summary-jobs', 'summaryJobs', 'package_context_available')
    + overviewJumpButton(sliceBadge(localizeTextValue('Summary identity aligned'), esc((summaryJobs.identity_assurance_counts && summaryJobs.identity_assurance_counts.boundary_aligned) ?? 0), 'badge-ready'), '/api/summary-jobs', 'summaryJobs', 'boundary_aligned')
    + overviewJumpButton(sliceBadge(localizeTextValue('Summary mutation preview'), esc((summaryJobs.mutation_readiness_counts && summaryJobs.mutation_readiness_counts.preview_only) ?? 0), 'badge-warning'), '/api/summary-jobs', 'summaryJobs', 'preview_only')
    + '</p>'
    + metricsSection
    + detailLine('Source refs total', summaryJobs.summary_source_total ?? 0)
    + sliceButtonRow(summaryJobsSliceButtons())
    + '<p>' + listJumpButton(label('button.open_summary_jobs', 'Open Summary Jobs'), '/api/summary-jobs') + '</p>'
  );
}}
function renderOverviewTriagePanel(triage, warningButtons, warningSummaries) {{
  const metricsSection = collapsibleSection(
    label('section.metrics', 'Metrics'),
    summaryJsonLine('Runtime kinds', triage.runtime_record_kinds)
      + summaryJsonLine('Review capability counts', triage.review_capability_counts)
      + summaryJsonLine('Package readiness counts', triage.package_readiness_counts)
      + summaryJsonLine('CLI parity counts', triage.cli_parity_counts)
      + summaryJsonLine('Identity assurance counts', triage.identity_assurance_counts)
      + summaryJsonLine('Reviewer kind counts', triage.reviewer_kind_counts)
      + summaryJsonLine('Warning counts', triage.warning_counts),
    false
  );
  return renderPanel(
    sectionTitle(label('section.triage', 'Triage'))
    + '<p>'
    + overviewJumpButton(sliceBadge(localizeTextValue('Review Requested'), esc(triage.needs_attention_reviews ?? 0), 'badge-warning'), '/api/review-queue', 'reviewQueue', 'review_requested')
    + '</p>'
    + '<p>'
    + overviewJumpButton(sliceBadge(localizeTextValue('Review Ready'), esc(triage.ready_now_reviews ?? 0), 'badge-ready'), '/api/review-queue', 'reviewQueue', 'ready')
    + overviewJumpButton(sliceBadge(localizeTextValue('Review Advisory'), esc(triage.advisory_only_reviews ?? 0), 'badge-warning'), '/api/review-queue', 'reviewQueue', 'advisory')
    + '</p>'
    + '<p>'
    + overviewJumpButton(sliceBadge(localizeTextValue('Package Ready'), esc(triage.package_ready_reviews ?? 0), 'badge-ready'), '/api/review-queue', 'reviewQueue', 'package:package_context_available')
    + '</p>'
    + '<p>'
    + overviewJumpButton(sliceBadge(localizeTextValue('CLI Aligned'), esc(triage.cli_parity_aligned_reviews ?? 0), 'badge-ready'), '/api/review-queue', 'reviewQueue', 'aligned')
    + overviewJumpButton(sliceBadge(localizeTextValue('CLI Drift'), esc(triage.cli_parity_drift_reviews ?? 0), 'badge-warning'), '/api/review-queue', 'reviewQueue', 'drift_detected')
    + '</p>'
    + '<p>'
    + overviewJumpButton(sliceBadge(localizeTextValue('Identity Aligned'), esc(triage.identity_boundary_aligned_reviews ?? 0), 'badge-ready'), '/api/review-queue', 'reviewQueue', 'boundary_aligned')
    + overviewJumpButton(sliceBadge(localizeTextValue('Declared Identity Only'), esc(triage.identity_declared_only_reviews ?? 0), 'badge-warning'), '/api/review-queue', 'reviewQueue', 'reviewer_identity_declared_only')
    + '</p>'
    + '<p>'
    + overviewJumpButton(sliceBadge(localizeTextValue('Provider Response'), esc(triage.provider_response_present_reviews ?? 0), 'badge-ready'), '/api/review-queue', 'reviewQueue', 'response_id')
    + '</p>'
    + '<p>' + (warningButtons || '') + '</p>'
    + metricsSection
    + '<p>' + esc(label('overview.warning_priority', 'Warning priority')) + ': '
    + (warningSummaries.length > 0
      ? warningSummaries.map(item =>
          sliceBadge((item.label || item.code || 'warning'), item.count ?? 0, 'badge-warning')
        ).join('')
      : '(none)')
    + '</p>'
    + '<p>' + listJumpButton(label('button.open_review_queue', 'Open Review Queue'), '/api/review-queue')
    + listJumpButton(label('button.open_runtime_records', 'Open Runtime Records'), '/api/runtime-records')
    + listJumpButton(label('button.open_summary_jobs', 'Open Summary Jobs'), '/api/summary-jobs')
    + listJumpButton(label('button.open_runtime_config', 'Open Runtime Config'), '/api/runtime-config')
    + listJumpButton(label('button.open_package_review', 'Open Package Review'), '/api/package-review')
    + '<button data-reset-filters="all">' + esc(label('button.reset_filter', 'Reset Filter')) + '</button></p>'
    + sliceButtonRow(reviewQueueSliceButtons())
    + '<p>' + listJumpButton(localizeTextValue('Review Advisory'), '/api/review-queue', 'reviewQueue', 'advisory')
    + listJumpButton(localizeTextValue('Package Ready'), '/api/review-queue', 'reviewQueue', 'package:package_context_available')
    + listJumpButton(localizeTextValue('CLI Aligned'), '/api/review-queue', 'reviewQueue', 'aligned')
    + listJumpButton(localizeTextValue('Identity Aligned'), '/api/review-queue', 'reviewQueue', 'boundary_aligned')
    + listJumpButton(localizeTextValue('Auth Boundary Warnings'), '/api/review-queue', 'reviewQueue', 'ui_auth_not_enabled')
    + listJumpButton(localizeTextValue('Declared Identity Only'), '/api/review-queue', 'reviewQueue', 'reviewer_identity_declared_only')
    + listJumpButton(localizeTextValue('Runtime Retrieval Plans'), '/api/runtime-records', 'runtimeRecords', 'retrieval_plan')
    + '</p>'
  );
}}
function overviewWarningButtons(warningSummaries) {{
  return warningSummaries.map(item =>
    overviewJumpButton(
      sliceBadge((item.label || item.code || 'warning'), item.count ?? 0, 'badge-warning'),
      '/api/review-queue',
      'reviewQueue',
      item.code || ''
    )
  ).join('');
}}
const overviewPanelRenderers = [
  data => renderOverviewHeaderPanel(data.chronicle),
  data => renderOverviewCountsPanel(data.counts),
  data => renderOverviewRuntimeBoundaryPanel(data.runtime),
  data => renderOverviewRuntimeConfigPanel(data.runtimeConfig, data.runtimeConfigContract),
  data => renderOverviewUiBoundaryPanel(data.uiBoundary),
  data => renderOverviewAuthBoundaryPanel(data.authBoundary, data.authBoundaryOverview),
  data => renderOverviewIdentityBoundaryPanel(data.identityBoundary),
  data => renderOverviewMutationReadinessPanel(data.mutationReadiness),
  data => renderOverviewAiIndexPanel(data.aiIndex, data.counts),
  data => renderOverviewRuntimeRecordsPanel(data.counts, data.runtimeRecords),
  data => renderOverviewSummaryJobsPanel(data.counts, data.summaryJobs),
  data => renderOverviewTriagePanel(data.triage, data.warningButtons, data.warningSummaries),
];
function renderOverviewPanels(data) {{
  return overviewPanelRenderers.map(renderer => renderer(data)).join('');
}}
function renderOverview(payload) {{
  const chronicle = payload.chronicle || {{}};
  const counts = payload.counts || {{}};
  const runtime = payload.runtime_boundary || {{}};
  const uiBoundary = payload.ui_boundary || {{}};
  const authBoundary = payload.auth_boundary_summary || uiBoundary.auth_boundary_summary || {{}};
  const authBoundaryOverview = payload.auth_boundary_overview || {{}};
  const identityBoundary = payload.identity_boundary_summary || {{}};
  const aiIndex = payload.ai_index || {{}};
  const triage = payload.triage || {{}};
  const mutationReadiness = payload.mutation_readiness || {{}};
  const runtimeConfig = payload.runtime_config || {{}};
  const runtimeConfigContract = runtimeConfig.config || {{}};
  const runtimeRecords = payload.runtime_records_summary || {{}};
  const summaryJobs = payload.summary_jobs_summary || {{}};
  const warningSummaries = Array.isArray(triage.warning_summaries) ? triage.warning_summaries : [];
  const warningButtons = overviewWarningButtons(warningSummaries);
  const overviewData = {{
    aiIndex,
    authBoundary,
    authBoundaryOverview,
    chronicle,
    counts,
    identityBoundary,
    mutationReadiness,
    runtime,
    runtimeConfig,
    runtimeConfigContract,
    runtimeRecords,
    summaryJobs,
    triage,
    uiBoundary,
    warningButtons,
    warningSummaries,
  }};
  return ''
    + '<h2>/api/overview</h2>'
    + renderPanel(activeViewSummary('/api/overview', 'overview'))
    + renderOverviewPanels(overviewData);
}}
const detailPathResolvers = {{
  '/api/ai-index-graph-edges': () => null,
  '/api/ai-index-vector': row => row.record_id ? '/api/ai-index/vector/' + encodeURIComponent(row.record_id) : null,
  '/api/ai-index-graph-nodes': row => row.node_id ? '/api/ai-index/graph-nodes/' + encodeURIComponent(row.node_id) : null,
  '/api/runtime-records': row => row.event_id ? '/api/runtime-records/' + encodeURIComponent(row.event_id) : null,
  '/api/review-queue': row => row.event_id ? '/api/review-queue/' + encodeURIComponent(row.event_id) : null,
}};
function detailPath(endpoint, row) {{
  const resolver = detailPathResolvers[endpoint];
  if (resolver) return resolver(row);
  for (const key of idFields) if (row[key]) return endpoint + '/' + encodeURIComponent(row[key]);
  return null;
}}
function renderTable(endpoint, rows) {{
  if (!rows || rows.length === 0) return messageParagraph('No records.');
  const renderer = endpointRenderers[endpoint];
  return renderer ? renderer(endpoint, rows) : renderGenericTable(endpoint, rows);
}}
function endpointBody(endpoint, payload) {{
  if (endpoint === '/api/overview') return renderOverview(payload);
  const rows = firstArray(payload);
  return rows
    ? routeHeading(endpoint) + renderTable(endpoint, rows)
    : routeHeading(endpoint) + collapsibleJsonBlock(label('label.response_json', 'Response JSON'), payload, true);
}}
function detailNavigationOptions(endpoint, record) {{
  const previousDetail = window.__chronicleDetailTrail.length > 0
    ? window.__chronicleDetailTrail[window.__chronicleDetailTrail.length - 1]
    : '';
  return {{
    filterLabel: currentFilterLabel(),
    listButtons: relatedListButtons(endpoint, record),
    previousDetail: previousDetail,
    trailLabel: currentTrailLabel(),
    trailButtons: currentTrailButtons(),
  }};
}}
const detailNoticeRenderers = [
  renderRuntimePreviewNotice,
  renderResponseMetadataNotice,
  renderRetrievalHandoffNotice,
  renderPackageHandoffPreviewNotice,
  renderInvocationPlanNotice,
  renderPackageReadinessNotice,
  renderRelatedLinksNotice,
  renderAuthReadinessNotice,
  renderReviewCapabilityNotice,
  renderMutationEnablementNotice,
  renderDetailActionPreviewNotice,
  renderCliParityNotice,
  renderIdentityAssuranceNotice,
  renderReviewTimelineNotice,
];
function renderDetailNotices(record) {{
  return detailNoticeRenderers.map(renderer => renderer(record)).join('');
}}
function detailNoticeBody(endpoint, record) {{
  const options = detailNavigationOptions(endpoint, record);
  return renderNavigationNotice(endpoint, record, options) + renderDetailNotices(record);
}}
function detailBody(endpoint, payload) {{
  const record = payload.record || {{}};
  return routeHeading(endpoint)
    + detailNoticeBody(endpoint, record)
    + collapsibleJsonBlock(label('label.record_json', 'Record JSON'), payload, false);
}}
async function loadEndpoint(endpoint) {{
  window.__chronicleCurrentEndpoint = endpoint;
  const response = await fetch(endpoint);
  const payload = await response.json();
  document.getElementById('view').innerHTML = endpointBody(endpoint, payload);
  applyLocaleToPage();
}}
async function loadDetail(endpoint) {{
  if (window.__chronicleLastDetail && window.__chronicleLastDetail !== endpoint) {{
    window.__chronicleDetailTrail.push(window.__chronicleLastDetail);
  }}
  window.__chronicleLastDetail = endpoint;
  const response = await fetch(endpoint);
  if (!response.ok) {{
    document.getElementById('detail').innerHTML = '<h2>' + esc(localizeTextValue('Detail')) + '</h2><p>' + esc(t('status.not_found')) + '</p>';
    applyLocaleToPage();
    return;
  }}
  const payload = await response.json();
  document.getElementById('detail').innerHTML = detailBody(endpoint, payload);
  applyLocaleToPage();
}}
async function previewBlockedRoute(path, targetId = 'action-preview-response') {{
  const target = document.getElementById(targetId);
  if (!target) return;
  target.innerHTML = '<p>' + esc(t('status.loading_blocked_preview')) + '</p>';
  const {{ response, payload }} = await postJson(path);
  target.innerHTML = renderReviewActionResultPanel(
    t('status.blocked_route_preview'),
    response.status,
    path,
    payload,
    targetId,
    {{
      extraLines: detailLine('Mutation enabled', payload.mutation_enabled),
    }},
  );
  applyLocaleToPage();
}}
function reviewFieldValue(prefix, suffix, fallback = '') {{
  const element = prefix === 'reviewer'
    ? document.getElementById(suffix)
    : document.getElementById(prefix + '-' + suffix);
  return element && typeof element.value === 'string' ? element.value : fallback;
}}
async function copyCommand(command, targetId = 'action-preview-response') {{
  const target = document.getElementById(targetId);
  if (!command) return;
  const copied = await tryCopyText(command);
  appendCommandFeedback(target, command, copied);
}}
async function submitReviewAction(path, action, recordId, targetId = 'action-preview-response', fieldPrefix = 'reviewer', successDetail = '') {{
  const target = document.getElementById(targetId);
  if (!target) return;
  target.innerHTML = '<p>' + esc(t('status.applying_review_action')) + '</p>';
  const {{ response, payload }} = await postJson(path, reviewActionRequestBody(action, fieldPrefix));
  target.innerHTML = renderReviewActionResultPanel(
    t('status.review_action_result'),
    response.status,
    path,
    payload,
    targetId,
    {{
      action: action,
      recordId: recordId,
      useStatusFallback: true,
      extraLines: ''
        + detailLine('Audit ID', payload.audit_id || '')
        + detailLine('Decision event', payload.decision_event_id || ''),
    }},
  );
  applyLocaleToPage();
  if (response.ok) {{
    if (window.__chronicleCurrentEndpoint) loadEndpoint(window.__chronicleCurrentEndpoint);
    if (successDetail) {{
      loadDetail(successDetail);
    }} else if (recordId) {{
      loadDetail('/api/review-queue/' + encodeURIComponent(recordId));
    }}
  }}
}}
document.querySelectorAll('button[data-endpoint]').forEach(button => button.addEventListener('click', () => loadEndpoint(button.dataset.endpoint)));
document.getElementById('view').addEventListener('click', handleViewClick);
document.getElementById('detail').addEventListener('click', handleDetailClick);
document.getElementById('view').addEventListener('click', handleViewPreviewPost);
window.__chronicleFilters = {{ runtimeRecords: '', reviewQueue: '', summaryJobs: '' }};
window.__chronicleSorts = {{ runtimeRecords: 'latest', reviewQueue: 'attention', summaryJobs: 'latest' }};
window.__chronicleDetailTrail = [];
window.__chronicleLocale = initialLocale();
document.getElementById('view').addEventListener('input', handleViewInput);
document.getElementById('view').addEventListener('change', handleViewChange);
document.getElementById('locale-select').addEventListener('change', event => setLocale(event.target.value));
applyLocaleToPage();
loadEndpoint('/api/overview');
</script>
</body>
</html>"""

    def static_review_console(self) -> str:
        return HtmlDashboardExporter(self.root).export()


def create_handler(
    root: Path | None = None,
    *,
    host: str = DEFAULT_UI_HOST,
    mutation_capability_flag: bool = False,
    enable_ui_mutation: bool = False,
    auth_mode: str = UIAuthMode.NOT_ENABLED,
    authorization_mode: str = UIAuthorizationMode.NOT_ENABLED,
) -> type[BaseHTTPRequestHandler]:
    service = ChronicleUIDataService(
        root,
        host=host,
        mutation_capability_flag=mutation_capability_flag,
        enable_ui_mutation=enable_ui_mutation,
        auth_mode=auth_mode,
        authorization_mode=authorization_mode,
    )

    class ChronicleUIRequestHandler(BaseHTTPRequestHandler):
        server_version = "ChronicleUILocal/0.3"

        def do_GET(self) -> None:  # noqa: N802 - stdlib API
            parsed = urlparse(self.path)
            if parsed.path in ("/", "/index.html"):
                self._send_html(service.html_shell())
                return
            if parsed.path == "/review-console":
                self._send_html(service.static_review_console())
                return
            payload = service.api_payload(parsed.path)
            if payload is not None:
                self._send_json(payload)
                return
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")

        def do_POST(self) -> None:  # noqa: N802 - stdlib API
            parsed = urlparse(self.path)
            content_length = int(self.headers.get("Content-Length", "0") or 0)
            raw_body = self.rfile.read(content_length) if content_length > 0 else b"{}"
            try:
                body = json.loads(raw_body.decode("utf-8"))
            except json.JSONDecodeError:
                self._send_json(
                    {
                        "ok": False,
                        "status": "blocked",
                        "error_code": "invalid_json",
                        "message": service._review_action_failure_message("invalid_json"),
                        "mutation_enabled": service.ui_boundary()["ui_boundary"]["mutation_enabled"],
                        "failure_contract": service._review_action_failure_contract(
                            mutation_enabled=service.ui_boundary()["ui_boundary"]["mutation_enabled"],
                            error_code="invalid_json",
                        ),
                    },
                    status=HTTPStatus.BAD_REQUEST,
                )
                return
            if not isinstance(body, dict):
                self._send_json(
                    {
                        "ok": False,
                        "status": "blocked",
                        "error_code": "invalid_request_body",
                        "message": "Request body must be a JSON object.",
                        "mutation_enabled": service.ui_boundary()["ui_boundary"]["mutation_enabled"],
                    },
                    status=HTTPStatus.BAD_REQUEST,
                )
                return
            result = service.review_action_response(parsed.path, body)
            if result is not None:
                status, payload = result
                self._send_json(payload, status=status)
                return
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")

        def log_message(self, format: str, *args: object) -> None:
            return

        def _send_html(self, body: str) -> None:
            payload = body.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def _send_json(self, body: dict[str, Any], *, status: HTTPStatus = HTTPStatus.OK) -> None:
            payload = json.dumps(body, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    return ChronicleUIRequestHandler


def make_server(
    *,
    host: str = DEFAULT_UI_HOST,
    port: int = DEFAULT_UI_PORT,
    root: Path | None = None,
    mutation_capability_flag: bool = False,
    enable_ui_mutation: bool = False,
    auth_mode: str = UIAuthMode.NOT_ENABLED,
    authorization_mode: str = UIAuthorizationMode.NOT_ENABLED,
) -> ThreadingHTTPServer:
    return ThreadingHTTPServer(
        (host, port),
        create_handler(
            root,
            host=host,
            mutation_capability_flag=mutation_capability_flag,
            enable_ui_mutation=enable_ui_mutation,
            auth_mode=auth_mode,
            authorization_mode=authorization_mode,
        ),
    )


def serve_ui(
    *,
    host: str = DEFAULT_UI_HOST,
    port: int = DEFAULT_UI_PORT,
    root: Path | None = None,
    open_browser: bool = False,
    mutation_capability_flag: bool = False,
    enable_ui_mutation: bool = False,
    auth_mode: str = UIAuthMode.NOT_ENABLED,
    authorization_mode: str = UIAuthorizationMode.NOT_ENABLED,
) -> UIStartupMetadata:
    root_path = root or Path.cwd()
    service = ChronicleService(root_path)
    service.require_initialized()
    metadata = build_startup_metadata(
        host=host,
        port=port,
        root=root_path,
        mutation_capability_flag=mutation_capability_flag,
        enable_ui_mutation=enable_ui_mutation,
        auth_mode=auth_mode,
        authorization_mode=authorization_mode,
    )
    server = make_server(
        host=host,
        port=port,
        root=root_path,
        mutation_capability_flag=mutation_capability_flag,
        enable_ui_mutation=enable_ui_mutation,
        auth_mode=auth_mode,
        authorization_mode=authorization_mode,
    )
    if open_browser:
        webbrowser.open(metadata.url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:  # pragma: no cover - interactive shutdown path
        pass
    finally:
        server.server_close()
    return metadata


def validate_ui_root(root: Path | None = None) -> None:
    try:
        ChronicleService(root).require_initialized()
    except ChronicleError:
        raise


def validate_ui_host(host: str) -> None:
    if _is_loopback_host(host):
        return
    raise UIHostNotLoopbackError(host)


def _bind_scope(host: str) -> str:
    return "loopback-only" if _is_loopback_host(host) else "non-loopback"


def _is_loopback_host(host: str) -> bool:
    normalized = host.strip().lower()
    if normalized == "localhost":
        return True
    try:
        return ipaddress.ip_address(normalized).is_loopback
    except ValueError:
        return False
