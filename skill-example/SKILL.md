---
name: example/repository-review
description: Review a repository and produce an evidence-backed findings artifact.
version: 1.0.0
author: Example author
tags:
  - example
  - review
  - artifact-producer
tools:
  - file_read
  - file_search
  - create_task_artifact
---

# Repository Review Skill

Use this skill when a task asks for a focused repository review and the current
Agent Profile has this skill enabled.

## Procedure

1. Read only the files needed to answer the request.
2. Record each finding with a concrete file path, command result, or other evidence.
3. Separate verified facts from assumptions and open questions.
4. Do not edit implementation files while producing the review artifact.
5. Create one `repository_review` artifact with `summary` and at least one `findings` entry.

A finding should include `title`, `severity`, `evidence`, `impact`, and
`recommended_action`. If no defect is found, record the checks that support that
conclusion instead of inventing a finding.
