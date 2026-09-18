# Repo Brain

- Index mode: full
- Files indexed: 8
- Files reparsed this run: 8
- Symbols: 69
- Internal import edges: 7
- Impacted files: 0
- Selected tests: 0

## Languages
- python: 8 files

## Highest-density symbol files
- asset_forge.py: 17 symbols
- tests/test_asset_forge.py: 17 symbols
- raster_pack.py: 11 symbols
- tests/test_raster_pack.py: 8 symbols
- tests/test_godot_export.py: 6 symbols
- tests/test_starlist_bridge.py: 5 symbols
- godot_export.py: 3 symbols
- starlist_bridge.py: 2 symbols

## Agent routing
- Read impact.json first after project/change context.
- Use selected-tests.json before broad validation.
- Search lookup.json for symbol routing; ast-grep enrichment may provide exact ranges.
- Verify source before editing.

## ast-grep enrichment
- ast-grep outline: available
- AST index mode: full
- AST files reparsed this run: 8
- outline files retained: 8
- top-level items retained: 90
- direct members retained: 28
- symbol shards: 20
- route named symbols via ast-routing.json, then fetch one ast-symbols/<initial>.json shard

