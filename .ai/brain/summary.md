# Repo Brain

- Index mode: full
- Files indexed: 6
- Files reparsed this run: 6
- Symbols: 62
- Internal import edges: 5
- Impacted files: 0
- Selected tests: 0

## Languages
- python: 6 files

## Highest-density symbol files
- asset_forge.py: 17 symbols
- tests/test_asset_forge.py: 17 symbols
- raster_pack.py: 11 symbols
- tests/test_raster_pack.py: 8 symbols
- tests/test_godot_export.py: 6 symbols
- godot_export.py: 3 symbols

## Agent routing
- Read impact.json first after project/change context.
- Use selected-tests.json before broad validation.
- Search lookup.json for symbol routing; ast-grep enrichment may provide exact ranges.
- Verify source before editing.

## ast-grep enrichment
- ast-grep outline: available
- AST index mode: full
- AST files reparsed this run: 6
- outline files retained: 6
- top-level items retained: 76
- direct members retained: 24
- symbol shards: 19
- route named symbols via ast-routing.json, then fetch one ast-symbols/<initial>.json shard

