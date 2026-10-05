# Repo Brain

- Index mode: incremental
- Files indexed: 78
- Files reparsed this run: 0
- Symbols: 1013
- Internal import edges: 101
- Impacted files: 0
- Selected tests: 0

## Languages
- python: 75 files
- javascript: 3 files

## Highest-density symbol files
- web/runtime_atlas.mjs: 139 symbols
- tests/test_generator_backends.py: 106 symbols
- tests/test_raster_pack.py: 83 symbols
- raster_pack.py: 53 symbols
- tests/test_production_executor.py: 53 symbols
- generator_backends.py: 22 symbols
- tests/test_svg_tools.py: 22 symbols
- tests/test_asset_forge.py: 20 symbols
- asset_forge.py: 19 symbols
- tests/test_runtime_atlas.py: 19 symbols
- asset_library.py: 17 symbols
- visual_similarity.py: 15 symbols
- tests/test_cloudflare_backend.py: 14 symbols
- tests/test_godot_export.py: 14 symbols
- tests/test_remote_batch.py: 14 symbols
- tests/test_godot_handoff.py: 13 symbols
- tests/test_asset_library.py: 12 symbols
- tests/test_gltf_quality.py: 12 symbols
- tests/test_vector_backend.py: 12 symbols
- gltf_binary_metrics.py: 11 symbols

## Agent routing
- Read impact.json first after project/change context.
- Use selected-tests.json before broad validation.
- Search lookup.json for symbol routing; ast-grep enrichment may provide exact ranges.
- Verify source before editing.

## ast-grep enrichment
- ast-grep outline: available
- AST index mode: incremental
- AST files reparsed this run: 0
- outline files retained: 74
- top-level items retained: 1232
- direct members retained: 392
- symbol shards: 26
- route named symbols via ast-routing.json, then fetch one ast-symbols/<initial>.json shard

