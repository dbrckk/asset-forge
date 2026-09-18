# Repo Brain

- Index mode: incremental
- Files indexed: 34
- Files reparsed this run: 3
- Symbols: 388
- Internal import edges: 48
- Impacted files: 6
- Selected tests: 3

## Languages
- python: 34 files

## Highest-density symbol files
- tests/test_raster_pack.py: 75 symbols
- raster_pack.py: 47 symbols
- tests/test_svg_tools.py: 22 symbols
- tests/test_asset_forge.py: 20 symbols
- asset_forge.py: 15 symbols
- tests/test_godot_export.py: 13 symbols
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
- tests/test_godot_3d_delivery.py: 8 symbols
- tests/test_raster_backend.py: 8 symbols

## Agent routing
- Read impact.json first after project/change context.
- Use selected-tests.json before broad validation.
- Search lookup.json for symbol routing; ast-grep enrichment may provide exact ranges.
- Verify source before editing.

## ast-grep enrichment
- ast-grep outline: available
- AST index mode: incremental
- AST files reparsed this run: 3
- outline files retained: 34
- top-level items retained: 386
- direct members retained: 209
- symbol shards: 24
- route named symbols via ast-routing.json, then fetch one ast-symbols/<initial>.json shard

