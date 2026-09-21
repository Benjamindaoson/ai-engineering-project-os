# Architecture

AI Engineering Project OS is a long-horizon Agent harness for auditing and upgrading real AI repositories.

```mermaid
flowchart TD
    I["Repository import"] --> A["Audit"]
    A --> G["Gap model"]
    G --> P["Upgrade plan"]
    P --> X["Sandbox execution"]
    X --> V["Deterministic verification"]
    V -->|pass| E["Evidence and version"]
    V -->|fail| R["Recover or replan"]
    R --> X
    E --> A2["Re-audit"]
```

## Runtime responsibilities

- Repository audit produces evidence-backed maturity findings.
- Planning turns gaps into bounded, testable tasks.
- Execution changes code only inside the controlled project workspace.
- Verification checks actual files, commands, tests, and build results.
- Evidence and version records preserve why a task is considered complete.
- Re-audit measures the resulting repository rather than trusting the previous plan.

## Trust boundary

A model proposal is not completion evidence. Tests, builds, artifacts, and persisted execution records determine task status.
