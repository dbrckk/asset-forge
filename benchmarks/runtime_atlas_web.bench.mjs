import assert from "node:assert/strict";
import { performance } from "node:perf_hooks";
import {
  buildInstancedSpriteBatch,
  createRuntimeAtlasPages,
  indexRuntimeAtlas,
  prepareSpriteSceneInstances,
} from "../web/runtime_atlas.mjs";

const count = Number.parseInt(process.env.ASSET_FORGE_BENCH_SPRITES ?? "50000", 10);
if (!Number.isInteger(count) || count <= 0 || count > 100000) {
  throw new Error("ASSET_FORGE_BENCH_SPRITES must be an integer between 1 and 100000");
}

const atlas = {
  format: "asset-forge-runtime-atlas",
  version: 1,
  image: "bench.png",
  imageSize: { width: 256, height: 256 },
  frameCount: 1,
  capabilities: { trimOffsets: true, clockwise90Rotation: true },
  frames: [{
    index: 0,
    name: "sprite",
    atlasRegion: { x: 0, y: 0, width: 32, height: 32 },
    uv: { u0: 0, v0: 0, u1: 0.125, v1: 0.125 },
    sourceRegion: { width: 32, height: 32 },
    sourceSize: { width: 32, height: 32 },
    trimOffset: { x: 0, y: 0 },
    rotation: { rotated: false, degreesClockwise: 0 },
  }],
};

const indexed = indexRuntimeAtlas(atlas);
const pages = createRuntimeAtlasPages([
  { id: "bench", atlas, texture: "bench.png" },
]);
const instances = Array.from({ length: count }, (_, index) => ({
  id: `sprite-${index}`,
  page: "bench",
  frame: "sprite",
  x: (index % 500) * 40,
  y: Math.floor(index / 500) * 40,
  z: index % 16,
  scaleX: 1,
  scaleY: 1,
}));

const viewport = { x: 0, y: 0, width: 1920, height: 1080 };
const startedPrepare = performance.now();
const prepared = prepareSpriteSceneInstances(pages, instances, {
  viewport,
  sort: true,
});
const prepareMs = performance.now() - startedPrepare;

assert.equal(prepared.inputCount, count);
assert.ok(prepared.outputCount > 0);
assert.ok(prepared.outputCount < count);
assert.equal(prepared.culledCount, count - prepared.outputCount);

const startedBatch = performance.now();
const batch = buildInstancedSpriteBatch(indexed, prepared.instances);
const batchMs = performance.now() - startedBatch;

assert.equal(batch.instanceCount, prepared.outputCount);
assert.equal(batch.instanceStrideFloats, 18);
assert.equal(batch.instanceStrideBytes, 72);
assert.equal(batch.instances.byteLength, batch.instanceCount * 72);
assert.equal(batch.bounds.length, batch.instanceCount);

const report = {
  sprites: count,
  visible: prepared.outputCount,
  culled: prepared.culledCount,
  prepareMs: Number(prepareMs.toFixed(3)),
  batchMs: Number(batchMs.toFixed(3)),
  instanceBytes: batch.instances.byteLength,
  bytesPerVisibleInstance: batch.instanceStrideBytes,
};
console.log(JSON.stringify(report));
