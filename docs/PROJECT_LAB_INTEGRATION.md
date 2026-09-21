# Project Lab read-only assessment contract

AI Engineering Project OS exposes a dedicated integration path for AI Talents Learning OS.

## Why a separate assessment path exists

The normal Project OS lifecycle can modify a repository:

```text
Audit → Plan → Execute → Verify
```

That behavior is useful for autonomous engineering, but it is not safe as learner evidence. If the evaluator edits a student's repository before verification, the final project quality no longer proves what the learner submitted.

Project Lab therefore uses a read-only contract:

```text
Student Repository
      ↓
Import
      ↓
Audit
      ↓
Read-only Test / Verify
      ↓
Engineering Evidence
```

The assessment service constructs a synthetic verification task with **zero code changes**. Verification may inspect files and execute test discovery, but it never invokes the autonomous upgrade runtime.

## Endpoint

```text
POST /api/project-lab/projects/{project_id}/assess
```

Example request:

```json
{
  "skill_ids": ["rag.hybrid-retrieval"],
  "criteria": [
    {
      "criterion": "Project tests are discoverable",
      "evidence_type": "test",
      "verification_method": "pytest_collection"
    }
  ]
}
```

Response includes:

- assessment ID
- project ID
- source snapshot / commit metadata
- read-only flag
- verification details
- pass / partial / failure summary

## Trust boundary

Project OS returns **engineering evidence** only.

It does not decide whether the learner personally mastered the skill.

That attribution step belongs to AI Talents Learning OS:

```text
Engineering Evidence
      ↓
Learning Evidence Adapter
      ↓
Attribution / independence checks
      ↓
Learner Model
```
