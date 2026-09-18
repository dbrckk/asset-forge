# Repo Brain

- Index mode: full
- Files indexed: 12
- Files reparsed this run: 12
- Symbols: 104
- Internal import edges: 11
- Impacted files: 0
- Selected tests: 0

## Languages
- python: 12 files

## Highest-density symbol files
- asset_forge.py: 17 symbols
- tests/test_asset_forge.py: 17 symbols
- raster_pack.py: 12 symbols
- tests/test_raster_pack.py: 11 symbols
- tests/test_svg_tools.py: 11 symbols
- svg_tools.py: 9 symbols
- tests/test_godot_export.py: 9 symbols
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
- AST files reparsed this run: 12
- outline files retained: 12
- top-level items retained: 125
- direct members retained: 48
- symbol shards: 22
- route named symbols via ast-routing.json, then fetch one ast-symbols/<initial>.json shard

