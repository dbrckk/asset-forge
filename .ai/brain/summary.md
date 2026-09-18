# Repo Brain

- Index mode: full
- Files indexed: 4
- Files reparsed this run: 4
- Symbols: 47
- Internal import edges: 3
- Impacted files: 0
- Selected tests: 0

## Languages
- python: 4 files

## Highest-density symbol files
- asset_forge.py: 17 symbols
- tests/test_asset_forge.py: 17 symbols
- raster_pack.py: 7 symbols
- tests/test_raster_pack.py: 6 symbols

## Agent routing
- Read impact.json first after project/change context.
- Use selected-tests.json before broad validation.
- Search lookup.json for symbol routing; ast-grep enrichment may provide exact ranges.
- Verify source before editing.

## ast-grep enrichment
- ast-grep outline: available
- AST index mode: full
- AST files reparsed this run: 4
- outline files retained: 4
- top-level items retained: 61
- direct members retained: 17
- symbol shards: 18
- route named symbols via ast-routing.json, then fetch one ast-symbols/<initial>.json shard

