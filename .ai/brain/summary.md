# Repo Brain

- Index mode: incremental
- Files indexed: 38
- Files reparsed this run: 2
- Symbols: 564
- Internal import edges: 54
- Impacted files: 4
- Selected tests: 2

## Languages
- python: 36 files
- javascript: 2 files

## Highest-density symbol files
- web/runtime_atlas.mjs: 134 symbols
- tests/test_raster_pack.py: 82 symbols
- raster_pack.py: 51 symbols
- tests/test_svg_tools.py: 22 symbols
- tests/test_asset_forge.py: 20 symbols
- tests/test_runtime_atlas.py: 19 symbols
- asset_forge.py: 15 symbols
- tests/test_godot_export.py: 14 symbols
- tests/test_godot_handoff.py: 13 symbols
- gltf_binary_metrics.py: 11 symbols
- svg_tools.py: 11 symbols
- tests/test_gltf_tools.py: 11 symbols
- tests/test_toolchain_3d.py: 11 symbols
- toolchain_3d.py: 11 symbols
- tests/test_engine_profile_validation.py: 10 symbols
- tests/test_gltf_quality.py: 10 symbols
- asset_profile_validation.py: 8 symbols
- tests/test_asset_profile_validation.py: 8 symbols
- tests/test_gltf_binary_metrics.py: 8 symbols
- tests/test_gltf_diagnostics.py: 8 symbols

## Agent routing
- Read impact.json first after project/change context.
- Use selected-tests.json before broad validation.
- Search lookup.json for symbol routing; ast-grep enrichment may provide exact ranges.
- Verify source before editing.

## ast-grep enrichment
- ast-grep outline: available
- AST index mode: incremental
- AST files reparsed this run: 2
- outline files retained: 38
- top-level items retained: 783
- direct members retained: 235
- symbol shards: 26
- route named symbols via ast-routing.json, then fetch one ast-symbols/<initial>.json shard

