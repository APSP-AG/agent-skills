# APSP Agent Skills

Reusable skills for coding agents.

## Repository layout

```text
skills/<skill-slug>/...
registry/skills.yaml
scripts/validate_skills.py
```

- Keep each skill self-contained under `skills/<skill-slug>`.
- Keep install URLs stable by never renaming published skill paths.
- Track metadata and discovery fields in `registry/skills.yaml`.

## Install a skill

Use a direct GitHub tree URL to a skill folder:

```bash
npx skills add https://github.com/APSP-AG/agent-skills/tree/main/skills/wsl-embedded-debugging
```

## Validate locally

```bash
python3 -m pip install pyyaml
python3 scripts/validate_skills.py
```

## Available skills

- `skills/wsl-embedded-debugging` — run Windows embedded flash/debug commands from WSL and capture bounded logs.
- `skills/saleae-logic2-embedded-debug` — author and run Saleae Logic 2 automation workflows and extensions for embedded debugging.
