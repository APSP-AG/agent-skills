#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

SKILL_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
ALLOWED_STATUS = {"alpha", "stable", "deprecated"}
REQUIRED_REGISTRY_FIELDS = {
    "id",
    "path",
    "owner",
    "status",
    "tags",
    "updated_at",
    "summary",
}


def load_yaml(path: Path) -> object:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"Failed to parse YAML: {exc}") from exc


def parse_skill_frontmatter(skill_md_path: Path) -> dict:
    content = skill_md_path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    if not match:
        raise ValueError("SKILL.md frontmatter is missing or malformed")
    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML frontmatter: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("Frontmatter must be a YAML object")
    return data


def validate_registry(root: Path) -> list[str]:
    errors: list[str] = []
    registry_path = root / "registry" / "skills.yaml"
    if not registry_path.exists():
        return [f"Missing registry file: {registry_path}"]

    try:
        registry_data = load_yaml(registry_path)
    except ValueError as exc:
        return [f"{registry_path}: {exc}"]

    if not isinstance(registry_data, dict):
        return [f"{registry_path}: top-level YAML must be an object"]

    version = registry_data.get("version")
    if version != 1:
        errors.append(f"{registry_path}: version must be 1")

    skills = registry_data.get("skills")
    if not isinstance(skills, list) or not skills:
        return [f"{registry_path}: skills must be a non-empty list"]

    seen_ids: set[str] = set()
    registered_paths: set[Path] = set()

    for index, entry in enumerate(skills, start=1):
        location = f"{registry_path} [skills[{index}]]"
        if not isinstance(entry, dict):
            errors.append(f"{location}: entry must be an object")
            continue

        missing = REQUIRED_REGISTRY_FIELDS - set(entry.keys())
        if missing:
            errors.append(f"{location}: missing fields: {', '.join(sorted(missing))}")
            continue

        skill_id = entry["id"]
        if not isinstance(skill_id, str) or not SKILL_ID_PATTERN.match(skill_id):
            errors.append(f"{location}: invalid id '{skill_id}'")
            continue
        if skill_id in seen_ids:
            errors.append(f"{location}: duplicate id '{skill_id}'")
            continue
        seen_ids.add(skill_id)

        declared_path = entry["path"]
        if not isinstance(declared_path, str):
            errors.append(f"{location}: path must be a string")
            continue
        expected_path = f"skills/{skill_id}"
        if declared_path != expected_path:
            errors.append(
                f"{location}: path must equal '{expected_path}' (got '{declared_path}')"
            )
            continue

        owner = entry["owner"]
        if not isinstance(owner, str) or not owner.strip():
            errors.append(f"{location}: owner must be a non-empty string")

        status = entry["status"]
        if status not in ALLOWED_STATUS:
            errors.append(
                f"{location}: status must be one of {sorted(ALLOWED_STATUS)} (got '{status}')"
            )

        tags = entry["tags"]
        if (
            not isinstance(tags, list)
            or not tags
            or any(not isinstance(tag, str) or not tag.strip() for tag in tags)
        ):
            errors.append(f"{location}: tags must be a non-empty list of strings")

        updated_at = entry["updated_at"]
        if not isinstance(updated_at, str) or not re.match(r"^\d{4}-\d{2}-\d{2}$", updated_at):
            errors.append(f"{location}: updated_at must be YYYY-MM-DD")

        summary = entry["summary"]
        if not isinstance(summary, str) or len(summary.strip()) < 10:
            errors.append(f"{location}: summary must be a descriptive string")

        skill_dir = root / declared_path
        registered_paths.add(skill_dir.resolve())
        if not skill_dir.is_dir():
            errors.append(f"{location}: directory not found: {declared_path}")
            continue

        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            errors.append(f"{location}: missing SKILL.md at {declared_path}/SKILL.md")
            continue

        try:
            frontmatter = parse_skill_frontmatter(skill_md)
        except ValueError as exc:
            errors.append(f"{skill_md}: {exc}")
            continue

        keys = set(frontmatter.keys())
        if keys != {"name", "description"}:
            errors.append(
                f"{skill_md}: frontmatter keys must be exactly 'name' and 'description'"
            )

        name = frontmatter.get("name")
        if name != skill_id:
            errors.append(f"{skill_md}: frontmatter name '{name}' must equal id '{skill_id}'")

        description = frontmatter.get("description")
        if not isinstance(description, str) or not description.strip():
            errors.append(f"{skill_md}: description must be non-empty")

        openai_yaml = skill_dir / "agents" / "openai.yaml"
        if not openai_yaml.exists():
            errors.append(f"{location}: missing agents/openai.yaml")
            continue
        try:
            openai_data = load_yaml(openai_yaml)
        except ValueError as exc:
            errors.append(f"{openai_yaml}: {exc}")
            continue
        if not isinstance(openai_data, dict) or not isinstance(openai_data.get("interface"), dict):
            errors.append(f"{openai_yaml}: top-level 'interface' object is required")
            continue
        interface = openai_data["interface"]
        display_name = interface.get("display_name")
        short_description = interface.get("short_description")
        if not isinstance(display_name, str) or not display_name.strip():
            errors.append(f"{openai_yaml}: interface.display_name must be non-empty")
        if not isinstance(short_description, str):
            errors.append(f"{openai_yaml}: interface.short_description must be a string")
        else:
            short_len = len(short_description)
            if short_len < 25 or short_len > 64:
                errors.append(
                    f"{openai_yaml}: interface.short_description length must be 25-64 (got {short_len})"
                )

    skills_root = root / "skills"
    if skills_root.exists():
        for path in skills_root.iterdir():
            if not path.is_dir() or path.name.startswith("."):
                continue
            if path.resolve() not in registered_paths:
                errors.append(
                    f"{path}: skill directory exists but is not listed in registry/skills.yaml"
                )

    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = validate_registry(root)
    if errors:
        print("Skill validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("All skills validated successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
