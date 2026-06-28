# Chronicle Stack v0.2 Release Readiness

## Scope

v0.2 第一波 Context Sovereignty Layer のリリース判定。

## Completed Issues

| Issue | Title |
|-------|-------|
| #10 | Context Scope Model |
| #12 | Visibility Hints |
| #13 | Source Provenance |
| #11 | Boundary Rules |
| #14 | Context Injection Plans |

## Feature Summary

| Feature | Status |
|---------|--------|
| ContextScope (formal scope model) | ✅ |
| VisibilityHint (public/private/sensitive) | ✅ |
| SourceProvenance (structured metadata) | ✅ |
| BoundaryRule (include/exclude/warn) | ✅ |
| BoundaryRule index rebuild | ✅ |
| Context Injection Plan generation | ✅ |
| CLI: add-context --scope | ✅ |
| CLI: add-context --visibility | ✅ |
| CLI: add-context --source-* | ✅ |
| CLI: record --source-* | ✅ |
| CLI: artifact create --visibility | ✅ |
| CLI: artifact create --source-* | ✅ |
| CLI: boundary add/list/check | ✅ |
| CLI: injection plan | ✅ |

## Non-goals

- GraphRAG
- Dashboard
- LLM prompt injection
- Vector search / embeddings
- External LLM API integration
- Cloud sync
- Permission enforcement
- Cryptographic provenance

## Compatibility

- v0.1 JSONL はそのまま読み込める
- `scope_hint` → `scope` 自動補完
- `visibility_hint` なし → `UNKNOWN` に fallback
- `source` なし → `None` として読み込み
- Boundary Rule や Injection Plan は Context を変更しない

## License

Chronicle Stack v0.2.0 and later are licensed under AGPL-3.0-or-later.

Earlier releases that were published under different license terms remain available under the license terms published with those releases. This transition does not retroactively change previously released versions.

Commercial licensing may be available separately from ZYX Corp株式会社 for use cases requiring different terms, including closed-source embedding, proprietary SaaS deployment, or other commercial arrangements.

## CLI Coverage

| コマンド | v0.2 |
|---------|------|
| `chronicle add-context --scope` | ✅ |
| `chronicle add-context --visibility` | ✅ |
| `chronicle add-context --source-*` | ✅ |
| `chronicle record --source-*` | ✅ |
| `chronicle artifact create --visibility` | ✅ |
| `chronicle artifact create --source-*` | ✅ |
| `chronicle boundary add` | ✅ |
| `chronicle boundary list` | ✅ |
| `chronicle boundary check` | ✅ |
| `chronicle injection plan` | ✅ |

## Test Coverage

```
87 passed
```

| File | Tests |
|------|-------|
| test_context_scope.py | 6 |
| test_visibility_hint.py | 8 |
| test_source_provenance.py | 11 |
| test_boundary_rules.py | 11 |
| test_injection_plan.py | 9 |
| Others (v0.1) | 42 |

## Smoke Test

[v0.2 スモークテスト手順](../smoke/smoke-test-v0.2.md) 参照。

## Documentation Coverage

| Document | Status |
|----------|--------|
| README.md | ✅ updated |
| ../../architecture.md | ✅ updated |
| ../../data-model.md | ✅ updated |
| ../../cli-reference.md | ✅ updated |
| ../../storage-format.md | ✅ updated |
| ../smoke/smoke-test-v0.2.md | ✅ created |
| ../../licensing.md | ✅ created |
| CHANGELOG.md | ✅ updated |

## Known Limitations

- GraphRAG 未実装
- Dashboard 未実装
- InjectionPlan はデフォルトでは永続化しない
- LLM への自動注入は行わない
- Boundary Rule はアクセス制御ではない
- RDE は正しさを証明しない
- Source Provenance は出所の記録であり、真実性の証明ではない
- 同一 Version への複数 RDE は JSONL 上の最後の RDE が優先
- 商用ライセンス条件はこのリポジトリでは定義しない

## Release Decision

**v0.2.0 release candidate として可。**

条件:
1. CI pass ✅
2. ruff pass ✅
3. pytest 87 passed ✅
4. Smoke test pass ✅
5. License transition documented ✅
