# Repo Brain

- Index mode: full
- Files indexed: 10
- Files reparsed this run: 10
- Symbols: 80
- Internal import edges: 9
- Impacted files: 0
- Selected tests: 0

## Languages
- python: 10 files

## Highest-density symbol files
- asset_forge.py: 17 symbols
- tests/test_asset_forge.py: 17 symbols
- raster_pack.py: 11 symbols
- tests/test_godot_export.py: 9 symbols
- tests/test_raster_pack.py: 8 symbols
- godot_export.py: 5 symbols
- tests/test_animation_infer.py: 5 symbols
- tests/test_starlist_bridge.py: 5 symbols
- starlist_bridge.py: 2 symbols
- animation_infer.py: 1 symbols

## Agent routing
- Read impact.json first after project/change context.
- Use selected-tests.json before broad validation.
- Search lookup.json for symbol routing; ast-grep enrichment may provide exact ranges.
- Verify source before editing.

## ast-grep enrichment
- ast-grep outline: available
- AST index mode: full
- AST files reparsed this run: 10
- outline files retained: 10
- top-level items retained: 99
- direct members retained: 35
- symbol shards: 20
- route named symbols via ast-routing.json, then fetch one ast-symbols/<initial>.json shard

