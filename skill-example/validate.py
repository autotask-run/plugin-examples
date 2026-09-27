"""Dependency-free validator for the example Skill bundle."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

MAX_FILE_BYTES = 32 * 1024
MAX_BUNDLE_BYTES = 128 * 1024
MAX_FILES = 8
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
        classification = manifest["classification"]
        if classification.get("plugin_kind") != "skill_pack":
            errors.append("manifest classification.plugin_kind must be skill_pack")
        if classification.get("source_kind") != "native":
            errors.append("reference manifest source_kind must be native")
        if classification.get("runtime_kinds") != ["skill"]:
            errors.append("manifest classification.runtime_kinds must be ['skill']")
        runtimes = manifest["runtimes"]
        if runtimes != [{"runtime_id": "bundle", "kind": "skill", "protocol": "autotask.skill-bundle.v1"}]:
            errors.append("manifest runtimes must declare the bundle skill runtime")
        capabilities = manifest["capabilities"]
        skill_capabilities = capabilities["skills"]
        if len(skill_capabilities) != 1:
            errors.append("manifest must contain exactly one skill capability")
        else:
            skill = skill_capabilities[0]
            checks = {
                "name": "example/repository-review",
                "runtime_id": "bundle",
                "runtime_kind": "skill",
                "support_level": "closed_loop_supported",
            }
            for key, expected in checks.items():
                if skill.get(key) != expected:
                    errors.append(f"manifest skills[0].{key} must be {expected!r}")
            if skill.get("permissions") != ["workspace_scoped"]:
                errors.append("manifest skills[0].permissions must be ['workspace_scoped']")
            bundle = skill.get("metadata", {}).get("skill_bundle", {})
            if bundle.get("schema_version") != "autotask.skill-bundle.v1":
                errors.append("skill_bundle.schema_version must be autotask.skill-bundle.v1")
            if bundle.get("readme_content") != skill_path.read_text(encoding="utf-8"):
                errors.append("skill_bundle.readme_content must match SKILL.md")
            declared_manifest_path = skill_path.parent / "autotask-skill.json"
            if not declared_manifest_path.exists():
                declared_manifest_path = manifest_path.parent / "autotask-skill.json"
            declared_skill_manifest = json.loads(declared_manifest_path.read_text(encoding="utf-8"))
            if bundle.get("manifest") != declared_skill_manifest:
                errors.append("skill_bundle.manifest must match autotask-skill.json")
            files = bundle.get("files")
            if not isinstance(files, list) or len(files) > MAX_FILES:
                errors.append("skill_bundle.files must contain at most 8 files")
            seen = set()
            bundle_bytes = len(bundle.get("readme_content", "").encode("utf-8")) + len(json.dumps(declared_skill_manifest, ensure_ascii=False).encode("utf-8"))
            for index, file in enumerate(files or []):
                if set(file) != {"path", "content"}:
                    errors.append(f"skill_bundle.files[{index}] must contain only path and content")
                    continue
                path = file.get("path", "")
                parts = path.split("/") if isinstance(path, str) else []
                if not path or path.startswith("/") or "\\" in path or "://" in path or any(part in ("", ".", "..") for part in parts):
                    errors.append(f"skill_bundle.files[{index}].path is not a safe relative path")
                if path in ("SKILL.md", "autotask-skill.json") or path in seen:
                    errors.append(f"skill_bundle.files[{index}].path is reserved or duplicated")
                seen.add(path)
                content = file.get("content")
                if not isinstance(content, str) or len(content.encode("utf-8")) > MAX_FILE_BYTES:
                    errors.append(f"skill_bundle.files[{index}].content exceeds the example file limit")
                bundle_bytes += len(str(path).encode("utf-8")) + len(content.encode("utf-8")) if isinstance(content, str) else 0
            if bundle_bytes > MAX_BUNDLE_BYTES:
                errors.append("skill_bundle content exceeds the 128 KiB example limit")
            for key in ("bundle_ref", "entrypoint", "command", "url", "source_url", "repository", "dependencies", "install", "install_command"):
                if key in bundle.get("manifest", {}):
                    errors.append(f"skill_bundle.manifest cannot contain {key}")
            if skill.get("required_tools") is not None:
                errors.append("manifest skills[0].required_tools is not part of the embedded contract")
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
