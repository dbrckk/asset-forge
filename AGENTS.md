# Shared repository intelligence

## Shared development policy — 88 validated rules (2026-10-09)

The project adopts the [88-rule standard](https://github.com/dbrckk/repo-standards/blob/db2f86657ada74a0561e07189f9942d6b66ebb4a/standards/88-rules.md), the [operational agent skill](https://github.com/dbrckk/repo-standards/blob/db2f86657ada74a0561e07189f9942d6b66ebb4a/skills/repo-excellence-88/SKILL.md), and the [educational wiki](https://github.com/dbrckk/repo-standards/blob/db2f86657ada74a0561e07189f9942d6b66ebb4a/docs/WIKI-88.md). Read the relevant parts before substantial work and apply conditional rules only where appropriate.

**Owner preference: do not create new unit tests.** Existing tests may be run for diagnostics; prioritize real functional and integration verification, lint, build, and reproducible checks. Never claim an unexecuted check passed.

Preserve repository-specific constraints and authorized scope. The pinned policy commit above governs the 88 rules; `.repo-standards.yml` continues to configure existing repository intelligence and reusable workflows independently. Do not change workflow refs merely to adopt these rules.


This repository uses `dbrckk/repo-standards` and `dbrckk/repo-brain`. Before substantial work, follow `.repo-standards.yml` and the bounded-context reading order from the central standards. Preserve the repository-specific instructions below.

# asset-forge agent instructions

This repository inherits global conventions from `dbrckk/repo-standards`.

## Context order

1. Read `.ai/project-state.md`.
2. Read task-relevant pipeline definitions.
3. Read `config/tooling.json` when selecting production tools.
4. Read the manifest/schema relevant to the requested asset.
5. Fetch only implementation files required for the task.

## Production rules

- Treat this repository as production infrastructure, not an asset dump.
- Do not store large reusable binary libraries in Git unless explicitly justified.
- Prefer deterministic transformations and reproducible commands.
- Preserve source/master assets separately from optimized delivery assets.
- Every external asset must have source and license metadata.
- Important identity-bearing assets default to custom creation rather than approximate stock substitution.
- Secondary assets may be sourced externally when style, quality, license, and technical constraints match.
- Never silently change the consuming project's art direction.

## Tool selection

Selection order:

1. approved tool in `config/tooling.json`;
2. candidate from `dbrckk/star-list`;
3. broader GitHub/web discovery;
4. custom implementation only when existing tools are insufficient.

A discovered tool must be reviewed before being marked approved.

## Definition of done

A workflow is complete only when provenance is known, licensing is compatible, technical validation passes, export is reproducible, and the consuming project can import the result.
