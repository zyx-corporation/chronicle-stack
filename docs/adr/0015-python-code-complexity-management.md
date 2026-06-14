# ADR-0015: Pythonコード巨大化を防ぐための分割・複雑度管理基準

## Status

Proposed

## Date

2026-06-15

## Context

Pythonは記述開始が容易であり、初期開発速度に優れる一方、コードベースが成長すると、単一ファイル・単一関数・単一クラスに複数の責務が混在しやすい。

特に以下のような状態になると、変更影響の把握、テスト、レビュー、リファクタリングが困難になる。

- `main.py`, `app.py`, `service.py`, `manager.py`, `utils.py` が肥大化する
- CLI処理、設定読み込み、DB接続、外部API呼び出し、業務ロジック、ログ、例外処理が同一モジュールに混在する
- `dict` ベースの曖昧なデータ構造が複数箇所に広がる
- 副作用を持つ処理と純粋な業務判断が分離されていない
- テストのために大量の mock や fixture が必要になる
- 変更理由が異なる処理が同じファイル・関数・クラスに閉じ込められている

この状態は単なる可読性低下ではなく、変更によって生じる意味変化、すなわち ΔM の観測不能化を招く。

したがって、本プロジェクトでは Python コードの巨大化を防ぐため、責務分離、依存方向、複雑度、テスト容易性に関する基準を定める。

## Decision

Pythonコードの分割・整理は、単純な行数ではなく、以下の基準に基づいて判断する。

### 1. 変更理由による分割を最優先する

同じ理由で変更されるものは近くに置き、異なる理由で変更されるものは分離する。

以下は原則として別責務とみなす。

- 設定読み込み
- CLI / Web API などの入力インターフェース
- 業務ロジック
- ユースケース制御
- DB / ファイル / 外部API などの I/O
- ログ設定
- 例外定義
- データ構造定義
- テスト用補助処理

### 2. I/O と業務ロジックを分離する

業務ロジック内に以下を直接混在させない。

- `requests`
- `sqlite3`, SQLAlchemy などのDB接続
- `boto3` などのクラウドSDK
- `os.environ`
- `pathlib` / ファイルI/O
- `print`
- 現在時刻取得
- 乱数生成

副作用を持つ処理は外側の adapter / infrastructure 層に置き、中心部には純粋関数または副作用の少ない domain logic を置く。

### 3. import 方向を固定する

基本的な依存方向は以下とする。

```text
interfaces / cli / api
  ↓
usecases
  ↓
domain
```

外部接続は adapter として外側に置く。

```text
adapters / infrastructure
  → domain の型・インターフェースに合わせる

domain
  → adapters / infrastructure を知らない
```

domain 層が DB、HTTP、ファイルシステム、クラウドSDKに依存し始めた場合は設計劣化とみなす。

### 4. テスト容易性を分割基準にする

以下の状態になった場合、その関数・クラス・モジュールは責務過多の可能性が高い。

- 単体テストのためにネットワーク接続が必要
- 単体テストのためにDBが必要
- 現在時刻や環境変数に強く依存する
- mock が多すぎる
- fixture が巨大化する
- 1つの変更に対して広範囲のテストが壊れる

目標は以下のテスト構造とする。

```text
unit test:
  純粋関数・domain logic を入力値と出力値で確認する

usecase test:
  repository / gateway を fake に差し替えて確認する

integration test:
  実DB・実APIに近い構成で確認する
```

### 5. 型とデータ構造を明示する

同じ dict 構造を3箇所以上で参照する場合、以下のいずれかを検討する。

- dataclass
- TypedDict
- Pydantic model
- domain model class

外部入力の検証が必要な場合は Pydantic を優先する。

内部の不変データ構造には `dataclass(frozen=True)` を優先する。

### 6. クラス化は状態と依存を持つ場合に限定する

以下の場合はクラス化を検討する。

- 状態を持つ
- 複数メソッドで同じ依存を共有する
- repository / gateway / service などを差し替えたい
- ライフサイクル管理が必要
- 抽象インターフェースを実装したい

単なる関数の集合にはクラスを使わない。

避けるべき例:

```python
class TextUtils:
    def normalize(self, text: str) -> str:
        return text.strip()
```

この場合は通常の関数でよい。

### 7. 複雑度の警戒値を定める

以下を警戒値とする。

- 1ファイル: 300〜500行を超えたら分割検討
- 1関数: 30〜50行を超えたら分割検討
- 1クラス: 200行を超えたら分割検討
- 関数引数: 5個を超えたら dataclass / command object を検討
- ネスト: 3段を超えたら早期 return / 関数分割を検討
- Cyclomatic Complexity: 10超で注意、20超で原則リファクタ対象

これらは絶対的禁止値ではなく、設計確認を促す警報値とする。

### 8. 神ファイルを禁止する

以下の名前のモジュールが肥大化した場合、責務が曖昧になっている可能性が高いため、具体的な名前へ分割する。

- `utils.py`
- `common.py`
- `helper.py`
- `service.py`
- `manager.py`
- `main.py`
- `app.py`

例:

```text
utils.py
  ↓
text_normalizer.py
date_range.py
retry_policy.py
json_codec.py
```

### 9. 推奨プロジェクト構成

一定以上の規模になることが予想される場合、以下のような `src/` レイアウトを採用する。

```text
project/
  pyproject.toml
  README.md
  src/
    myapp/
      __init__.py
      config.py
      domain/
        __init__.py
        models.py
        rules.py
        errors.py
      usecases/
        __init__.py
        register_user.py
      adapters/
        __init__.py
        repository_sqlite.py
        external_api.py
      interfaces/
        __init__.py
        cli.py
        web.py
      logging_config.py
  tests/
    unit/
    usecase/
    integration/
```

小規模スクリプトではこの構成を強制しない。ただし、以下の条件を満たした場合はレイヤー分割を開始する。

- CLI以外の入口が増えた
- Web API 化する可能性が出た
- 保存先を変更する可能性が出た
- 外部APIが2種類以上になった
- テストが書きにくくなった
- `utils.py` が増え始めた
- 同じ処理をコピーし始めた

### 10. CIで複雑度を監視する

以下のツールの利用を推奨する。

```text
ruff      # lint / format
mypy      # 型検査
pyright   # 型検査の代替または補完
pytest    # テスト
radon     # cyclomatic complexity
vulture   # 未使用コード検出
deptry    # 依存関係チェック
```

CIでは最低限、以下を確認する。

- lint が通ること
- format が揃っていること
- unit test が通ること
- 型検査が通ること
- 複雑度が警戒値を超えていないこと

## Consequences

### Positive

この基準により、以下が期待できる。

- 変更影響範囲を限定しやすくなる
- テストが書きやすくなる
- domain logic が副作用から守られる
- レビュー時に責務混在を発見しやすくなる
- `utils.py` や `service.py` の肥大化を防ぎやすくなる
- 将来的な CLI / Web API / batch / worker 化に対応しやすくなる
- 変更による意味変化 ΔM をテストで観測しやすくなる

### Negative

一方で、以下のコストが発生する。

- 初期実装時のファイル数が増える
- 小規模コードでは分割が過剰に見える場合がある
- レイヤー設計を理解していない開発者には学習コストがある
- 過度に抽象化すると、逆に追跡しにくくなる
- 型定義や interface 定義が増えることで、短期的な開発速度が落ちる場合がある

## Alternatives Considered

### Alternative 1: 単一スクリプト中心で運用する

小規模・短命なスクリプトでは有効である。

しかし、長期保守、テスト、自動化、複数入口、外部連携が発生すると急速に破綻しやすい。

本プロジェクトでは、短命な実験コードを除き、採用しない。

### Alternative 2: 最初から厳密な Clean Architecture を採用する

依存方向と責務分離は明確になる。

しかし、Pythonプロジェクトでは過剰設計になりやすく、初期開発速度を損なう可能性がある。

本プロジェクトでは、Clean Architecture の考え方を参考にしつつ、軽量なレイヤー分割に留める。

### Alternative 3: 行数だけで分割判断する

単純で運用しやすい。

しかし、行数が少なくても複雑な関数は存在し、逆に行数が多くても単純なデータ定義ファイルは問題にならない。

したがって、行数は警戒値として扱い、最終判断は変更理由・依存方向・テスト容易性・複雑度で行う。

## RDE Review

### 保存された要素

- Pythonの開発速度を損なわない
- 初期段階での過剰設計を避ける
- テスト容易性を重視する
- 副作用を外側へ寄せる
- 変更理由によって分割する
- 意味変化 ΔM を追跡可能にする

### 変換された要素

元の「巨大化防止」という実装上の問題を、ADRでは以下の設計判断へ変換した。

```text
コード量の問題
↓
責務境界の問題
↓
依存方向の問題
↓
テスト可能性の問題
↓
意味変化 ΔM の観測可能性の問題
```

### 補完された要素

ADRとして運用可能にするため、以下を補完した。

- Status
- Context
- Decision
- Consequences
- Alternatives Considered
- CIでの監視基準
- 推奨ディレクトリ構成
- 警戒メトリクス
- RDE Review

### 未解決の要素

以下はプロジェクトごとに調整が必要である。

- 実際の複雑度閾値
- mypy と pyright のどちらを正式採用するか
- Pydantic v2 を標準採用するか
- repository / gateway interface を Protocol で書くか abstract base class で書くか
- 小規模スクリプトにどこまで適用するか

### 逸脱リスク

このADRの主な逸脱リスクは以下である。

- 分割そのものが目的化する
- ファイル数だけが増え、意味境界が明確にならない
- Clean Architecture 風の過剰抽象化に陥る
- 小さなスクリプトにも同じ基準を強制する
- 型定義が形式的になり、実際の不変条件を表現しない
- テスト容易性ではなく、単なる見た目の整理に留まる

## 次回更新方針

実プロジェクトで以下を観測し、ADRを更新する。

- 複雑度警戒値が現実的か
- 分割基準がレビューで使いやすいか
- CIで検出できる項目と、人間レビューが必要な項目の境界
- domain, usecases, adapters, interfaces の粒度が適切か
- RDE / TDD / CI の連携方法
- 実際に巨大化したファイルのリファクタ事例

## Final Rule

Pythonコードの巨大化は、行数ではなく意味境界の崩壊として扱う。

したがって、本プロジェクトでは以下を基本原則とする。

```text
変更理由が違うものは分ける。
副作用は外側へ寄せる。
domain は外部依存を知らない。
テストしにくいコードは責務過多とみなす。
意味変化 ΔM をテストで観測可能にする。
```
