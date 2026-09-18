# Repo Brain

- Index mode: full
- Files indexed: 2
- Files reparsed this run: 2
- Symbols: 23
- Internal import edges: 1
- Impacted files: 1
- Selected tests: 1

## Languages
- python: 2 files

## Highest-density symbol files
- asset_forge.py: 12 symbols
- tests/test_asset_forge.py: 11 symbols

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
- top-level items retained: 31
- direct members retained: 9
- symbol shards: 15
- route named symbols via ast-routing.json, then fetch one ast-symbols/<initial>.json shard

