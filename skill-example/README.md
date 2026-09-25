# Skill bundle example

This directory is a small, dependency-free Skill bundle. It demonstrates the two
files an author must keep in sync: `SKILL.md` carries the instructions and
`autotask-skill.json` declares the artifact contract and tools.

```sh
python3 -m unittest discover -s skill-example -v
python3 skill-example/validate.py
```

`manifest.template.json` documents the catalog shape for a Skill capability. It
is intentionally marked `projected_read_only` and `source_kind=personal`: this
sample is for a private/workspace installation and materialization exercise.
The public `plugin submit` endpoint currently accepts remote HTTPS MCP tools and
personal memory providers, not Skill bundles. Do not submit this manifest as if
it were a public listing.

To prove a real Skill installation, import the bundle into a private catalog,
enable it on an Agent Profile, run a review task, and inspect the materialized
version plus the `repository_review` artifact. Passing this local validator only
proves bundle shape; it does not prove runtime materialization or artifact
creation.
