# Repo Brain

- Index mode: incremental
- Files indexed: 28
- Files reparsed this run: 3
- Symbols: 229
- Internal import edges: 37
- Impacted files: 5
- Selected tests: 2

## Languages
- python: 28 files

## Highest-density symbol files
- asset_forge.py: 17 symbols
- tests/test_asset_forge.py: 17 symbols
- tests/test_godot_handoff.py: 13 symbols
- raster_pack.py: 12 symbols
- gltf_binary_metrics.py: 11 symbols
- tests/test_gltf_tools.py: 11 symbols
- tests/test_raster_pack.py: 11 symbols
- tests/test_svg_tools.py: 11 symbols
- tests/test_toolchain_3d.py: 11 symbols
- toolchain_3d.py: 11 symbols
- tests/test_gltf_quality.py: 10 symbols
- svg_tools.py: 9 symbols
- tests/test_godot_export.py: 9 symbols
- tests/test_gltf_diagnostics.py: 8 symbols
- tests/test_godot_3d_delivery.py: 8 symbols
- tests/test_gltf_binary_metrics.py: 7 symbols
- gltf_diagnostics.py: 6 symbols
- gltf_tools.py: 6 symbols
- godot_handoff.py: 6 symbols
- blender_adapter.py: 5 symbols

## Agent routing
- Read impact.json first after project/change context.
- Use selected-tests.json before broad validation.
- Search lookup.json for symbol routing; ast-grep enrichment may provide exact ranges.
- Verify source before editing.

## ast-grep enrichment
- ast-grep outline: available
- AST index mode: incremental
- AST files reparsed this run: 3
- outline files retained: 28
- top-level items retained: 281
- direct members retained: 110
- symbol shards: 23
- route named symbols via ast-routing.json, then fetch one ast-symbols/<initial>.json shard

