# Repo Brain

- Index mode: incremental
- Files indexed: 54
- Files reparsed this run: 4
- Symbols: 721
- Internal import edges: 72
- Impacted files: 7
- Selected tests: 2

## Languages
- python: 51 files
- javascript: 3 files

## Highest-density symbol files
- web/runtime_atlas.mjs: 139 symbols
- tests/test_raster_pack.py: 82 symbols
- tests/test_generator_backends.py: 53 symbols
- raster_pack.py: 51 symbols
- tests/test_production_executor.py: 35 symbols
- tests/test_svg_tools.py: 22 symbols
- tests/test_asset_forge.py: 20 symbols
- asset_forge.py: 19 symbols
- tests/test_runtime_atlas.py: 19 symbols
- generator_backends.py: 18 symbols
- tests/test_godot_export.py: 14 symbols
- tests/test_godot_handoff.py: 13 symbols
- gltf_binary_metrics.py: 11 symbols
- svg_tools.py: 11 symbols
- tests/test_gltf_tools.py: 11 symbols
- tests/test_toolchain_3d.py: 11 symbols
- toolchain_3d.py: 11 symbols
- tests/test_engine_profile_validation.py: 10 symbols
- tests/test_gltf_quality.py: 10 symbols
- visual_similarity.py: 10 symbols

## Agent routing
- Read impact.json first after project/change context.
- Use selected-tests.json before broad validation.
- Search lookup.json for symbol routing; ast-grep enrichment may provide exact ranges.
- Verify source before editing.

## ast-grep enrichment
- ast-grep outline: available
- AST index mode: incremental
- AST files reparsed this run: 4
- outline files retained: 50
- top-level items retained: 953
- direct members retained: 285
- symbol shards: 26
- route named symbols via ast-routing.json, then fetch one ast-symbols/<initial>.json shard

