# Repo Brain

- Index mode: full
- Files indexed: 16
- Files reparsed this run: 16
- Symbols: 126
- Internal import edges: 15
- Impacted files: 0
- Selected tests: 0

## Languages
- python: 16 files

## Highest-density symbol files
- asset_forge.py: 17 symbols
- tests/test_asset_forge.py: 17 symbols
- raster_pack.py: 12 symbols
- tests/test_raster_pack.py: 11 symbols
- tests/test_svg_tools.py: 11 symbols
- svg_tools.py: 9 symbols
- tests/test_godot_export.py: 9 symbols
- tests/test_gltf_tools.py: 8 symbols
- blender_adapter.py: 5 symbols
- godot_export.py: 5 symbols
- tests/test_animation_infer.py: 5 symbols
- tests/test_blender_adapter.py: 5 symbols
- tests/test_starlist_bridge.py: 5 symbols
- gltf_tools.py: 4 symbols
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
- AST files reparsed this run: 16
- outline files retained: 16
- top-level items retained: 158
- direct members retained: 58
- symbol shards: 22
- route named symbols via ast-routing.json, then fetch one ast-symbols/<initial>.json shard

