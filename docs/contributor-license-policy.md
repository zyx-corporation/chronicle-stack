# Chronicle Stack Contributor License Policy

**Status:** Draft / Provisional
**Project:** Chronicle Stack
**Public License:** AGPL-3.0-or-later
**Commercial Licensing:** Possible separate commercial licensing

## 1. Purpose

Chronicle Stack is publicly licensed under AGPL-3.0-or-later and may also be offered under separate commercial license terms.

This policy explains how contributions are accepted, how contributor rights are handled, and when additional contributor agreements may be required.

This document is operational guidance for contributors and maintainers. It is not final legal advice and does not replace review by qualified counsel.

## 2. Policy Summary

Chronicle Stack uses a layered contribution policy:

1. Small fixes and ordinary documentation changes may be accepted under DCO.
2. Larger code contributions require maintainer review before acceptance.
3. Contributions intended for inclusion in commercial-license editions may require an Individual CLA, Corporate CLA, or separate written agreement.
4. Major architecture, persistence, data-model, protocol, security, or integration changes must not be accepted without clear contribution rights review.
5. No commercial relicensing rights are silently assumed from contributors.

## 3. Default Contribution Rule

Unless otherwise agreed in writing, contributions submitted to Chronicle Stack are accepted as contributions to the AGPL-3.0-or-later public version.

By submitting a contribution under the DCO process, the contributor certifies that they have the right to submit the contribution under the license indicated by the project.

DCO acceptance alone does not automatically grant ZYX Corp Ltd. or Chronicle Stack maintainers the right to include the contribution in a proprietary or commercial-license edition unless such rights are otherwise available under the applicable license or a separate agreement.

## 4. DCO Requirement

All commits should include a DCO sign-off line:

```text
Signed-off-by: Full Name <email@example.com>
```

Contributors may add this automatically using:

```bash
git commit -s
```

The sign-off indicates that the contributor certifies the contribution may be submitted to this project under the applicable open source license.

Pull requests without required sign-offs may be delayed or rejected until corrected.

## 5. Contributions Accepted Under DCO Only

The following contributions are generally eligible for DCO-only handling:

* typo fixes;
* formatting fixes;
* documentation corrections;
* small test improvements;
* small bug fixes;
* non-substantive refactoring;
* comments and examples;
* issue reproduction cases that do not include third-party proprietary code;
* minor CI or build script adjustments.

These contributions are treated as AGPL-3.0-or-later contributions unless otherwise agreed.

## 6. Contributions Requiring Pre-Acceptance Review

The following contributions require maintainer review before acceptance:

* new modules;
* major features;
* significant refactoring;
* persistence format changes;
* database schema changes;
* data model changes;
* protocol or API compatibility changes;
* cryptographic or security-related changes;
* authentication or authorization changes;
* external service integrations;
* model, AI, RAG, or agent integration changes;
* changes affecting Chronicle Records, provenance records, RDE evaluation, audit logs, or context histories;
* contributions expected to be included in commercial-license editions;
* contributions from a company, employer, university, research lab, or government organization where ownership may be unclear.

Maintainers may request additional rights clarification before reviewing or merging such contributions.

## 7. CLA Requirement

A CLA may be required when a contribution is substantial, strategic, or intended for commercial-license inclusion.

Chronicle Stack may use:

1. Individual Contributor License Agreement, ICLA;
2. Corporate Contributor License Agreement, CCLA;
3. project-specific written contribution agreement;
4. separate commercial development agreement;
5. assignment or license-back arrangement for commissioned work.

A CLA requirement should be stated before accepting the contribution.

The project must not accept major external code into a dual-license or commercial path without clear written rights.

## 8. Individual and Corporate Contributions

If a contributor contributes in a personal capacity, an Individual CLA may be sufficient.

If a contributor is contributing work created as part of employment, consulting, university research, corporate sponsorship, or organizational assignment, a Corporate CLA or equivalent employer authorization may be required.

A Corporate CLA does not necessarily remove the need for individual developer confirmation, depending on the final legal form adopted.

## 9. Commercial Licensing Implications

Chronicle Stack’s public AGPL version remains available.

Commercial licensing may be offered separately for users who need terms different from AGPL, such as:

* closed-source embedding;
* private modifications;
* SaaS or hosted service operation without AGPL source disclosure obligations;
* OEM or embedded redistribution;
* commercial support;
* contractual warranty or liability terms.

Contributions accepted only under AGPL-3.0-or-later may not be included in non-AGPL commercial-license editions unless Chronicle Stack has sufficient rights to do so.

Therefore, maintainers must classify contributions before merging when commercial inclusion is likely.

## 10. Contribution Classification

Maintainers should classify each non-trivial contribution as one of the following:

### Class A: DCO-only AGPL contribution

Small or ordinary contribution. Accepted under AGPL-3.0-or-later with DCO sign-off.

### Class B: Needs rights review

Substantial contribution or ownership ambiguity. Do not merge until contribution rights are clarified.

### Class C: CLA required

Contribution intended for dual licensing, commercial edition, strategic subsystem, data model, persistence layer, security layer, or hosted-service functionality.

### Class D: Separate agreement required

Commissioned work, corporate-sponsored work, OEM-related work, customer-specific development, or work involving confidential information.

## 11. AI-Assisted Contributions

Contributors must ensure that AI-assisted contributions do not include code, text, data, or artifacts that the contributor does not have the right to submit.

Contributors should disclose material AI assistance when it affects authorship, provenance, licensing, or reviewability.

Maintainers may request explanation of the origin of a contribution, especially for large generated code, copied snippets, model-generated implementations, or changes affecting security, persistence, or Chronicle Records.

## 12. Third-Party Code

Contributors must not submit third-party code unless:

1. the license is compatible with Chronicle Stack’s licensing;
2. attribution is preserved;
3. the source and license are clearly identified;
4. the contribution does not impose unexpected restrictions on Chronicle Stack;
5. maintainers approve inclusion.

Vendored dependencies, copied code, generated code, and snippets from examples or documentation must be clearly disclosed.

## 13. Large Contribution Process

Before starting a large contribution, contributors should open an issue or discussion describing:

* the intended change;
* affected modules;
* expected size;
* whether the contribution is personal, corporate, academic, or commissioned;
* whether the contribution should be available for commercial-license editions;
* any third-party code, data, models, APIs, or dependencies involved.

Maintainers may require a CLA, corporate authorization, design review, security review, or separate written agreement before accepting the work.

## 14. Maintainer Rules

Maintainers must not:

* silently assume commercial relicensing rights;
* merge major external code without rights clarification;
* accept ambiguous corporate contributions without checking authority;
* publish unreviewed CLA forms as final legal contracts;
* imply that AGPL prohibits commercial use;
* imply that every commercial user needs a commercial license.

Maintainers should:

* keep the AGPL public contribution path open;
* minimize friction for small contributions;
* require stronger rights review only when necessary;
* document contribution classification in the pull request when relevant;
* preserve the public project’s integrity while protecting future commercial licensing options.

## 15. RDE Review Notes

### Preserved

* Public OSS contribution remains possible.
* AGPL-3.0-or-later remains the public licensing basis.
* Small community contributions remain lightweight.
* The project does not retroactively change earlier public license terms.

### Supplemented

* Contributor rights handling is clarified for dual licensing.
* Large contributions have a pre-acceptance process.
* Commercial-license inclusion requires explicit rights.
* AI-assisted contribution provenance is addressed.

### Unresolved

* Final ICLA and CCLA legal forms require counsel review.
* The exact threshold for “large contribution” may need adjustment.
* Commercial edition governance may require a separate maintainer policy.

### Deviation Risks

* DCO-only contributions may be mistakenly assumed available for proprietary relicensing.
* CLA requirements may discourage community participation if applied too broadly.
* Corporate contributions may create ownership ambiguity.
* AI-assisted contributions may obscure provenance.
* Commercial licensing must not narrow the AGPL public grant.

## 16. Current Status

Until final legal forms are reviewed, Chronicle Stack uses this provisional policy:

* DCO is required for ordinary contributions.
* Major or strategic contributions require pre-acceptance rights review.
* Contributions intended for commercial-license inclusion require CLA or separate written agreement.
* Final CLA templates must be reviewed by qualified counsel before use as binding legal forms.
