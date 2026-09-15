# 2026-08-08 - Chronicle Yard Overview

## Chronicle Entry

- Date: 2026-08-08
- Task: Chronicle Yard の概要をドキュメント化する。
- Baseline: Yard は naming note、product map、roadmap milestones、responsibility matrix、
  handoff contract review に分散して定義されていたが、一読用の日本語概要はなかった。
- Changed: `docs/yard/overview.ja.md` を追加し、Yard の定義、中心価値、製品群の役割、
  利用者から見た流れ、境界ルール、現在状態、読む順番を整理した。`docs/yard/README.md`、
  `docs/README.md`、`docs/product-overview.md` から概要へリンクした。
- Preserved: Chronicle Yard は製品群の傘概念であり、Chronicle Stack の正式改名ではない。
  Stack は引き続き local-first なクロニクル保管機構であり、Cloud / API / CSG-RAG /
  chronicle-external-query / agent runtime の責務は明示契約で分ける。
- Why: Yard の概要を利用者向けに説明できる入口を作り、命名ノートやマイルストーン文書に
  直接入らなくても境界を把握できるようにするため。
- Next: CY-5 の operator journey を具体化するとき、この概要を実運用手順、画面導線、
  public copy の前提文書として更新する。
- Re-evaluate when: Chronicle Cloud authority model、Chronicle API contract、CSG-RAG /
  chronicle-external-query の外部リポジトリ契約が具体化したとき。

