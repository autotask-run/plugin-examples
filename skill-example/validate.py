"""Dependency-free validator for the example Skill bundle."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

MAX_FILE_BYTES = 128 * 1024
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


def _read_bounded(path: Path) -> str:
    data = path.read_bytes()
    if len(data) > MAX_FILE_BYTES:
        raise ValueError(f"{path.name} exceeds the {MAX_FILE_BYTES}-byte example limit")
    return data.decode("utf-8")


def _parse_scalar(raw: str) -> Any:
    value = raw.strip()
    if not value:
        return ""
    if value in ("[]", "{}"):  # useful for a minimal frontmatter fixture
        return [] if value == "[]" else {}
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    return value


def parse_frontmatter(text: str) -> dict[str, Any]:
    lines = text.splitlines()
    if len(lines) < 3 or lines[0].strip() != "---":
        raise ValueError("SKILL.md must start with YAML frontmatter")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError("SKILL.md frontmatter is not closed") from exc
    result: dict[str, Any] = {}
    active_list: str | None = None
    for line in lines[1:end]:
        if not line.strip():
            continue
        if line.startswith("  - "):
            if active_list is None or not isinstance(result.get(active_list), list):
                raise ValueError("frontmatter list item has no list key")
            result[active_list].append(_parse_scalar(line[4:]))
            continue
        if line.startswith(" "):
            raise ValueError("frontmatter supports only scalar keys and two-space lists")
        if ":" not in line:
            raise ValueError(f"invalid frontmatter line: {line}")
        key, raw = line.split(":", 1)
        key = key.strip()
        if not key or key in result:
            raise ValueError(f"duplicate or empty frontmatter key: {key}")
        if raw.strip():
            result[key] = _parse_scalar(raw)
            active_list = None
        else:
            result[key] = []
            active_list = key
    return result


def validate_bundle(skill_path: Path, manifest_path: Path) -> list[str]:
    errors: list[str] = []
    try:
        frontmatter = parse_frontmatter(_read_bounded(skill_path))
    except (OSError, UnicodeError, ValueError) as exc:
        return [str(exc)]
    required = {"name", "description", "version", "author", "tags", "tools"}
    missing = sorted(required - frontmatter.keys())
    errors.extend(f"frontmatter missing {key}" for key in missing)
    if frontmatter.get("name") != "example/repository-review":
        errors.append("frontmatter name must be example/repository-review")
    if not isinstance(frontmatter.get("description"), str) or len(frontmatter.get("description", "")) < 20:
        errors.append("frontmatter description must be a useful string")
    if not SEMVER.fullmatch(str(frontmatter.get("version", ""))):
        errors.append("frontmatter version must be major.minor.patch")
    for key in ("tags", "tools"):
        if not isinstance(frontmatter.get(key), list) or not frontmatter[key] or not all(isinstance(item, str) for item in frontmatter[key]):
            errors.append(f"frontmatter {key} must be a non-empty string list")

    try:
        manifest = json.loads(_read_bounded(manifest_path))
    except (OSError, UnicodeError, ValueError) as exc:
        return errors + [str(exc)]
    try:
        capability = manifest["capabilities"]["skills"]
        if len(capability) != 1:
            errors.append("manifest must contain exactly one skill capability")
        else:
            skill = capability[0]
            checks = {
                "skill_id": "example/repository-review",
                "version": "1.0.0",
                "entrypoint": "agent_profile",
                "bundle_ref": "./",
                "support_level": "projected_read_only",
            }
            for key, expected in checks.items():
                if skill.get(key) != expected:
                    errors.append(f"manifest skills[0].{key} must be {expected!r}")
            if skill.get("required_tools") != frontmatter.get("tools"):
                errors.append("manifest required_tools must match SKILL.md tools")
        if manifest["classification"]["plugin_kind"] != "skill_pack":
            errors.append("manifest classification.plugin_kind must be skill_pack")
        if manifest["classification"]["source_kind"] != "personal":
            errors.append("reference manifest source_kind must be personal")
    except (KeyError, TypeError, IndexError) as exc:
        errors.append(f"manifest shape is incomplete: {exc}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill", type=Path, default=Path(__file__).with_name("SKILL.md"))
    parser.add_argument("--manifest", type=Path, default=Path(__file__).with_name("manifest.template.json"))
    args = parser.parse_args()
    errors = validate_bundle(args.skill, args.manifest)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Skill bundle contract OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
