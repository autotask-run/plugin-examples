# Skill bundle example

This directory is a small, dependency-free Skill bundle. It demonstrates the two
files an author must keep in sync: `SKILL.md` carries the instructions and
`autotask-skill.json` declares the artifact contract and tools.

```sh
python3 -m unittest discover -s skill-example -v
python3 skill-example/validate.py
```

`manifest.template.json` documents the public `skill_pack` catalog shape. The
bundle embeds `SKILL.md`, `autotask-skill.json`, and bounded UTF-8 reference
files in the immutable plugin version, so Platform review sees the exact
content that a Worker will receive. It contains no command, URL, credential,
archive, or executable file.

Generate your author namespace and validate the submission shape:

```sh
python3 skill-example/prepare.py --author-id <your-user-id>
python3 skill-example/validate.py --manifest autotask-skill-pack.json
autotask plugin submit --manifest ./autotask-skill-pack.json --dry-run
autotask plugin submit --manifest ./autotask-skill-pack.json --json
```

The platform reviewer must publish the submission before another workspace can
install it. `source_kind=native` describes the embedded bundle; it does not
grant the author executable code or an external runtime.

To prove a real Skill installation, install the reviewed plugin, bind its Skill
capability to an Agent Profile, run a review task, and inspect the materialized
version plus the `repository_review` artifact. Passing this local validator only
proves bundle shape; it does not prove runtime materialization or artifact
creation.
