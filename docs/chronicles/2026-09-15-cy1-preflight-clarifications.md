# CY-1後続着手前の確認

Date: 2026-09-15
Baseline: `717a23bea3d5166262f2cdf9edfa6e4e19e79bfc`

## team_syncの到達可能性

`src/chronicle/api/cloud_authority.py`のfactoryから
`src/chronicle/interfaces/cli/daemon.py`の`daemon cloud federation-boundary`へ至る
経路は存在する。CLIを実行し、JSONで`team_sync.consent_required=False`が表示されること、
空の作業ディレクトリにファイルが作られないことを確認した。

src・tests・scriptsの参照、公開export、動的importの記述、daemonルートを調べた範囲では、
同期・認可の操作判定へ渡す経路はない。公開モデルなので外部利用者まで不活性とは証明しない。
「完全に到達不能」ではなく「設計表示には到達するが、現行の操作許可には使われない」と訂正する。
この値による現行default-deny迂回は見つからず、先行遮断の修正対象はない。

FederationPackageService.boundary_checkの同名`consent_required`は
`bool(package.records)`から独立に生成される事前確認出力で、Cloudの設定を参照していない。
同じキー名であることをデータフローの接続と扱わない。

## 方針と次の工程

- Cloudの正本性とpermissionを分離し、将来の同期への設計値の流用を禁止する旨を文書化。
- AgentCapabilityKindへの改称と関連フィールドの移行方針をADR-0109に追記。改称実装は未着手。
- actor／originとメンバーの非同一性をADR-0109に明記。主体の対応方法は未決。
- Codexが本タスクでtoken回収の安全条件設計初版を作成。PID単独判定を避け、所有・競合・
  再生成・失敗時の条件を整理した。OS別方式の実証と自動回収実装は未実施、開始日は未確定。
- 順序はCloud整合整理、Event Origin整合整理、その後containment/grantのスキーマ定義のみ。
  本作業は確認と方針の記録まで。共通認可、スキーマ追加、データ移行は実施しない。

## Failure Note: PR #391の分離粒度

5コミットの分類を満たすだけでは、task 0内部のCloud・agent・simulator変更を
セキュリティ上必要な依存とそれ以外に分離できなかった。コミット名・タスク番号を根拠に
必要性を扱ったことが検出漏れにつながった。
AGENTS.mdへ、各コミットの実diffで分類を検証し、混在は内容で分割し、必要依存と除外内容を
記録したうえで、移植後の最終差分も確認する手順を追加した。

## 検証

- CLIの設計表示確認: 成功。これは同期・認可全体の安全性を実証するテストではない。
- 全pytest: 582 passed（30.82秒）。Ruff: All checks passed。
- 差分の空白検査: 成功。変更は文書・手順のみで、src・tests・CI定義に変更なし。
- ローカルact・ホストCIは今回未実行。設計案の競合・電源断条件も未検証。

## 追加フィードバックの反映

- Cloudの別リポジトリ／別サービス実装計画の有無は未調査と明記。実装先と契約消費者を
  特定し、Cloud実装着手時に境界をまたいで到達可能性を再確認する条件を追加した。
- Agent改称はコード・公開契約まで含む。Cloud固有フィールドは別判断とし、
  Sayane等の外部コード／文書の旧名参照を調べて互換性方針を決める確認事項を追加した。
- 次の統合ではローカルCI成功後にpushし、そのpushの対象コミットに対するホストCI成功を
  確認してからマージする。ホストCIはpush後に実行されるため、両CIのpush前成功とはしない。
- diff分類確認は今後の作業依頼にも適用する一般則とする。このリポジトリではAGENTS.mdが
  適用元となる。別の作業環境へ依頼する際にも手順を引き継ぎ、未確認の他環境へ既に
  自動適用済みとは扱わない。

追加反映後の検証: pytest 582 passed（30.50秒）、Ruff成功、差分の空白検査成功。
文書3件のみ変更。ローカルCI・ホストCI、push・マージは本追記では実施していない。
