# Repo Brain

- Index mode: full
- Files indexed: 2
- Files reparsed this run: 2
- Symbols: 34
- Internal import edges: 1
- Impacted files: 0
- Selected tests: 0

## Languages
- python: 2 files

## Highest-density symbol files
- asset_forge.py: 17 symbols
- tests/test_asset_forge.py: 17 symbols

## Agent routing
- Read impact.json first after project/change context.
- Use selected-tests.json before broad validation.
- Search lookup.json for symbol routing; ast-grep enrichment may provide exact ranges.
- Verify source before editing.

## ast-grep enrichment
- ast-grep outline: available
- AST index mode: full
- AST files reparsed this run: 2
- outline files retained: 2
- top-level items retained: 38
- direct members retained: 14
- symbol shards: 15
- route named symbols via ast-routing.json, then fetch one ast-symbols/<initial>.json shard

