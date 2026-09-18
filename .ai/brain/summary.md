# Repo Brain

- Index mode: incremental
- Files indexed: 32
- Files reparsed this run: 2
- Symbols: 297
- Internal import edges: 44
- Impacted files: 3
- Selected tests: 1

## Languages
- python: 32 files

## Highest-density symbol files
- tests/test_raster_pack.py: 31 symbols
- tests/test_svg_tools.py: 22 symbols
- raster_pack.py: 19 symbols
- tests/test_asset_forge.py: 17 symbols
- asset_forge.py: 15 symbols
- tests/test_godot_handoff.py: 13 symbols
- gltf_binary_metrics.py: 11 symbols
- svg_tools.py: 11 symbols
- tests/test_gltf_tools.py: 11 symbols
- tests/test_toolchain_3d.py: 11 symbols
- toolchain_3d.py: 11 symbols
- tests/test_engine_profile_validation.py: 10 symbols
- tests/test_gltf_quality.py: 10 symbols
- tests/test_godot_export.py: 9 symbols
- asset_profile_validation.py: 8 symbols
- tests/test_asset_profile_validation.py: 8 symbols
- tests/test_gltf_diagnostics.py: 8 symbols
- tests/test_godot_3d_delivery.py: 8 symbols
- tests/test_gltf_binary_metrics.py: 7 symbols
- gltf_diagnostics.py: 6 symbols

## Agent routing
- Read impact.json first after project/change context.
- Use selected-tests.json before broad validation.
- Search lookup.json for symbol routing; ast-grep enrichment may provide exact ranges.
- Verify source before editing.

## ast-grep enrichment
- ast-grep outline: available
- AST index mode: incremental
- AST files reparsed this run: 2
- outline files retained: 32
- top-level items retained: 336
- direct members retained: 157
- symbol shards: 24
- route named symbols via ast-routing.json, then fetch one ast-symbols/<initial>.json shard

