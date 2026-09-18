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
