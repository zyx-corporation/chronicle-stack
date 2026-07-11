# Third-Party Notices

This file records third-party software, documentation, protocols, and reference implementations that are directly included, depended upon, or materially studied in the design of Chronicle Stack.

The presence of a project in the **Reference studies** section does not mean that its source code is bundled into Chronicle Stack.

## Directly included or vendored code

No third-party source code has been added by the Chronicle Stack Stage 2 design documentation change.

When source code or substantial portions of a third-party work are added, this section must include:

- project and source URL;
- exact version or commit;
- included paths or package names;
- copyright notice;
- license notice or full license text when required;
- Chronicle Stack target paths;
- modification summary;
- public AGPL and separate commercial-edition rights review status.

## Reference studies

### MulmoClaude

- Project: MulmoClaude
- Repository: `https://github.com/receptron/mulmoclaude`
- Reviewed commit: `6fcf15f3d976ebb499d6946b791a95290dafbf1a`
- License observed at repository root: MIT License
- Copyright notice observed: Copyright (c) 2026 Satoshi Nakajima and the members of Receptron
- Use in Chronicle Stack: architecture reference study only
- Direct source reuse: no
- Adoption mode: conceptual reimplementation
- Detailed record: `docs/provenance/upstream-study-mulmoclaude.md`
- Adoption ledger: `docs/provenance/upstream-adoption-ledger.yaml`

The Stage 2 documents study separation patterns for runtime backends, capability boundaries, scoped integration access, structured execution plans, review-oriented GUI surfaces, and messaging transport adapters. Chronicle Stack defines its own models and contracts from Chronicle-specific requirements, including primary-record authority, boundary review, provenance, audit, RDE, and proposal-first mutation.

If future work directly copies or modifies MulmoClaude source, documentation, schema, tests, or assets, the applicable MIT copyright and permission notice must be preserved in copies or substantial portions, and this file must be updated in the same pull request.

## Maintainer checklist

Before merging a change that uses third-party material:

- [ ] The exact source, version or commit, and path are recorded.
- [ ] The applicable license was checked for the actual distributed artifact.
- [ ] Required copyright and permission notices are preserved.
- [ ] Direct source reuse is distinguished from conceptual reimplementation.
- [ ] AI-assisted output was checked for material copying or distinctive similarity.
- [ ] AGPL public-edition compatibility was reviewed.
- [ ] Rights for any separate commercial edition were reviewed independently.
- [ ] `docs/provenance/upstream-adoption-ledger.yaml` was updated.

This notice register is operational documentation and is not legal advice.
