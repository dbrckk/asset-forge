import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import {
  drawFrameCanvas2D,
  frameQuad,
  indexRuntimeAtlas,
  sourceOrientedUVs,
  animationFrameAtTime,
  createAnimationPlayer,
  drawAnimationPlayerCanvas2D,
  animationEventsBetween,
  animationDurationSeconds,
  buildSpriteBatch,
  drawSpriteBatchCanvas2D,
  buildInstancedSpriteBatch,
  instancedSpriteUV,
  instancedSpriteWebGL2Shaders,
  instancedSpriteAttributeViews,
  createRuntimeAtlasPages,
  buildTexturePageBatches,
  createInstancedSpriteRendererWebGL2,
  createWebGL2TextureCache,
  loadImageBitmapSource,
  preloadRuntimeAtlasPageTextures,
  releaseRuntimeAtlasPageTextures,
  createWebGL2RuntimeAtlasScene,
  spriteInstanceBounds,
  cullSpriteInstances,
  stableSortSpriteInstances,
  prepareSpriteSceneInstances,
  resizeWebGL2Canvas,
  createWebGL2CanvasRuntime,
  createSpriteEntityStore,
  createSpriteEntityHistory,
  reparentSpriteEntity,
  duplicateSpriteEntities,
  copySpriteEntities,
  pasteSpriteEntities,
  removeSpriteEntityHierarchy,
  createSpriteAnimationSystem,
  resolveSpriteEntityHierarchy,
  buildSpriteEntityInstances,
  createSpriteEntityBatchCache,
  filterSpriteInstancesByLayer,
  applyCameraToSpriteInstances,
  createCamera2DController,
  clampCameraToWorldBounds,
  worldToScreenPoint,
  screenToWorldPoint,
  pointHitsSpriteInstance,
  pickSpriteInstances,
  createSpritePointerInteractionController,
  moveSpriteEntityByWorldDelta,
  createSpriteSelectionModel,
  moveSelectedSpriteEntitiesByWorldDelta,
  transformSelectedSpriteEntities,
  selectSpriteInstancesInRect,
} from "../web/runtime_atlas.mjs";

const atlas = JSON.parse(
  await readFile(new URL("../examples/runtime-atlas.json", import.meta.url), "utf8"),
);
const indexed = indexRuntimeAtlas(atlas);
const frame = indexed.frame(0);

assert.equal(indexed.frame("hero_0.png"), frame);
assert.equal(frameQuad(frame).rotated, true);
assert.deepEqual(frameQuad(frame).sourceRegion, { width: 8, height: 6 });
assert.deepEqual(sourceOrientedUVs(frame), [
  { u: 10 / 64, v: 28 / 64 },
  { u: 10 / 64, v: 20 / 64 },
  { u: 16 / 64, v: 20 / 64 },
  { u: 16 / 64, v: 28 / 64 },
]);

const calls = [];
const ctx = {
  save() {
    calls.push(["save"]);
  },
  restore() {
    calls.push(["restore"]);
  },
  translate(x, y) {
    calls.push(["translate", x, y]);
  },
  rotate(angle) {
    calls.push(["rotate", angle]);
  },
  drawImage(...args) {
    calls.push(["drawImage", ...args]);
  },
};

const image = { id: "atlas-image" };
const bounds = drawFrameCanvas2D(ctx, image, frame, 100, 200, { scale: 2 });

assert.deepEqual(bounds, { x: 100, y: 200, width: 24, height: 20 });
assert.deepEqual(calls[0], ["save"]);
assert.deepEqual(calls[1], ["translate", 104, 214]);
assert.equal(calls[2][0], "rotate");
assert.equal(calls[2][1], -Math.PI / 2);
assert.deepEqual(calls[3], [
  "drawImage",
  image,
  10,
  20,
  6,
  8,
  0,
  0,
  12,
  16,
]);
assert.deepEqual(calls[4], ["restore"]);

const plainAtlas = {
  format: "asset-forge-runtime-atlas",
  version: 1,
  image: "atlas.png",
  imageSize: { width: 16, height: 16 },
  frameCount: 1,
  capabilities: { trimOffsets: true, clockwise90Rotation: true },
  frames: [
    {
      index: 0,
      name: "plain",
      atlasRegion: { x: 1, y: 2, width: 4, height: 5 },
      uv: { u0: 1 / 16, v0: 2 / 16, u1: 5 / 16, v1: 7 / 16 },
      sourceRegion: { width: 4, height: 5 },
      sourceSize: { width: 6, height: 7 },
      trimOffset: { x: 1, y: 1 },
      rotation: { rotated: false, degreesClockwise: 0 },
    },
  ],
};
const plainCalls = [];
const plainCtx = {
  save() { plainCalls.push(["save"]); },
  restore() { plainCalls.push(["restore"]); },
  translate(...args) { plainCalls.push(["translate", ...args]); },
  rotate(...args) { plainCalls.push(["rotate", ...args]); },
  drawImage(...args) { plainCalls.push(["drawImage", ...args]); },
};
const plainFrame = indexRuntimeAtlas(plainAtlas).frame("plain");
assert.deepEqual(sourceOrientedUVs(plainFrame), [
  { u: 1 / 16, v: 2 / 16 },
  { u: 5 / 16, v: 2 / 16 },
  { u: 5 / 16, v: 7 / 16 },
  { u: 1 / 16, v: 7 / 16 },
]);
drawFrameCanvas2D(plainCtx, image, plainFrame, 10, 20);
assert.deepEqual(plainCalls, [
  ["save"],
  ["drawImage", image, 1, 2, 4, 5, 11, 21, 4, 5],
  ["restore"],
]);


const animatedAtlas = {
  ...plainAtlas,
  frameCount: 2,
  frames: [
    plainAtlas.frames[0],
    {
      ...plainAtlas.frames[0],
      index: 1,
      name: "plain_2",
      atlasRegion: { x: 5, y: 2, width: 4, height: 5 },
      uv: { u0: 5 / 16, v0: 2 / 16, u1: 9 / 16, v1: 7 / 16 },
    },
  ],
  animations: [
    {
      name: "run",
      fps: 10,
      loop: true,
      frames: [
        { index: 0, duration: 1 },
        { index: 1, duration: 2 },
      ],
    },
    {
      name: "once",
      fps: 2,
      loop: false,
      frames: [
        { index: 0, duration: 1 },
        { index: 1, duration: 1 },
      ],
    },
  ],
};

const animated = indexRuntimeAtlas(animatedAtlas);
assert.equal(animated.animation("run").fps, 10);
assert.equal(animationFrameAtTime(animated, "run", 0.05).frame.index, 0);
assert.equal(animationFrameAtTime(animated, "run", 0.15).frame.index, 1);
assert.equal(animationFrameAtTime(animated, "run", 0.35).frame.index, 0);

const onceFinished = animationFrameAtTime(animated, "once", 5);
assert.equal(onceFinished.frame.index, 1);
assert.equal(onceFinished.finished, true);
assert.equal(onceFinished.durationSeconds, 1);


const events = [];
const player = createAnimationPlayer(animated, "once", {
  autoplay: true,
  playbackRate: 2,
  onFrame(sample) {
    events.push(["frame", sample.frame.index]);
  },
  onFinish(sample) {
    events.push(["finish", sample.frame.index]);
  },
});

assert.equal(player.playing, true);
assert.equal(player.playbackRate, 2);
assert.equal(player.update(0).frame.index, 0);
assert.equal(player.update(0.30).frame.index, 1);
assert.equal(player.update(0.30).finished, true);
assert.equal(player.playing, false);
assert.deepEqual(events, [
  ["frame", 0],
  ["frame", 1],
  ["finish", 1],
]);

player.seek(0);
assert.equal(player.sample().frame.index, 0);
player.setPlaybackRate(0.5);
assert.equal(player.playbackRate, 0.5);
player.play();
player.pause();
const pausedTime = player.timeSeconds;
player.update(1);
assert.equal(player.timeSeconds, pausedTime);

assert.throws(
  () => createAnimationPlayer(animated, "run", { playbackRate: 0 }),
  /playbackRate must be > 0/,
);
assert.throws(() => player.seek(-1), /seek time/);
assert.throws(() => player.update(-1), /deltaSeconds/);


const loopEvents = [];
const loopPlayer = createAnimationPlayer(animated, "run", {
  autoplay: true,
  onLoop(event) {
    loopEvents.push(event.loopCount);
  },
});
loopPlayer.update(0.65);
assert.deepEqual(loopEvents, [1, 2]);

const animationDrawCalls = [];
const animationCtx = {
  save() { animationDrawCalls.push(["save"]); },
  restore() { animationDrawCalls.push(["restore"]); },
  translate(...args) { animationDrawCalls.push(["translate", ...args]); },
  rotate(...args) { animationDrawCalls.push(["rotate", ...args]); },
  drawImage(...args) { animationDrawCalls.push(["drawImage", ...args]); },
};
const drawPlayer = createAnimationPlayer(animated, "run");
drawPlayer.seek(0.15);
const drawn = drawAnimationPlayerCanvas2D(
  animationCtx,
  image,
  drawPlayer,
  3,
  4,
  { scale: 2 },
);
assert.equal(drawn.frame.index, 1);
assert.deepEqual(drawn.bounds, { x: 3, y: 4, width: 12, height: 14 });
assert.equal(animationDrawCalls[0][0], "save");
assert.equal(animationDrawCalls.at(-1)[0], "restore");


const eventAtlas = {
  ...animatedAtlas,
  animations: [
    {
      name: "event-loop",
      fps: 10,
      loop: true,
      frames: [
        { index: 0, duration: 1 },
        { index: 1, duration: 1 },
      ],
      events: [
        { name: "start", timeSeconds: 0, payload: { phase: "begin" } },
        { name: "footstep", timeSeconds: 0.05 },
        { name: "impact", timeSeconds: 0.15, payload: { damage: 7 } },
      ],
    },
    {
      name: "event-once",
      fps: 10,
      loop: false,
      frames: [
        { index: 0, duration: 1 },
        { index: 1, duration: 1 },
      ],
      events: [
        { name: "fire", timeSeconds: 0.1 },
      ],
    },
  ],
};

const eventIndexed = indexRuntimeAtlas(eventAtlas);
assert.equal(animationDurationSeconds(eventIndexed.animation("event-loop")), 0.2);
assert.deepEqual(
  animationEventsBetween(eventIndexed.animation("event-loop"), 0, 0.46).map(
    (entry) => [entry.name, Number(entry.absoluteTimeSeconds.toFixed(2)), entry.loopCount],
  ),
  [
    ["start", 0, 0],
    ["footstep", 0.05, 0],
    ["impact", 0.15, 0],
    ["start", 0.2, 1],
    ["footstep", 0.25, 1],
    ["impact", 0.35, 1],
    ["start", 0.4, 2],
    ["footstep", 0.45, 2],
  ],
);

const markerEvents = [];
const markerPlayer = createAnimationPlayer(eventIndexed, "event-loop", {
  autoplay: true,
  onEvent(event) {
    markerEvents.push([
      event.name,
      Number(event.absoluteTimeSeconds.toFixed(2)),
      event.loopCount,
      event.payload,
    ]);
  },
});
markerPlayer.update(0.46);
assert.deepEqual(markerEvents, [
  ["start", 0, 0, { phase: "begin" }],
  ["footstep", 0.05, 0, null],
  ["impact", 0.15, 0, { damage: 7 }],
  ["start", 0.2, 1, { phase: "begin" }],
  ["footstep", 0.25, 1, null],
  ["impact", 0.35, 1, { damage: 7 }],
  ["start", 0.4, 2, { phase: "begin" }],
  ["footstep", 0.45, 2, null],
]);

const onceMarkerEvents = [];
const onceMarkerPlayer = createAnimationPlayer(eventIndexed, "event-once", {
  autoplay: true,
  onEvent(event) {
    onceMarkerEvents.push(event.name);
  },
});
onceMarkerPlayer.update(5);
onceMarkerPlayer.update(1);
assert.deepEqual(onceMarkerEvents, ["fire"]);

assert.throws(
  () => animationEventsBetween(eventIndexed.animation("event-loop"), 1, 0),
  /invalid animation event interval/,
);


const rotatedBatch = buildSpriteBatch(indexed, [
  { frame: "hero_0.png", x: 100, y: 200, scale: 2 },
]);
assert.equal(rotatedBatch.instanceCount, 1);
assert.equal(rotatedBatch.vertexCount, 4);
assert.equal(rotatedBatch.indexCount, 6);
assert.equal(rotatedBatch.indexType, "uint16");
assert.deepEqual(Array.from(rotatedBatch.indices), [0, 1, 2, 0, 2, 3]);
assert.deepEqual(
  Array.from(rotatedBatch.vertices),
  [
    104, 202, 10 / 64, 28 / 64,
    120, 202, 10 / 64, 20 / 64,
    120, 214, 16 / 64, 20 / 64,
    104, 214, 16 / 64, 28 / 64,
  ],
);
assert.deepEqual(rotatedBatch.bounds[0], {
  x: 100,
  y: 200,
  width: 24,
  height: 20,
  visibleX: 104,
  visibleY: 202,
  visibleWidth: 16,
  visibleHeight: 12,
  frameIndex: 0,
  frameName: "hero_0.png",
});

const plainBatch = buildSpriteBatch(indexRuntimeAtlas(plainAtlas), [
  { frame: "plain", x: 10, y: 20, scaleX: 2, scaleY: 3 },
]);
assert.deepEqual(
  Array.from(plainBatch.vertices),
  [
    12, 23, 1 / 16, 2 / 16,
    20, 23, 5 / 16, 2 / 16,
    20, 38, 5 / 16, 7 / 16,
    12, 38, 1 / 16, 7 / 16,
  ],
);

const canvasBatchCalls = [];
const canvasBatchCtx = {
  save() { canvasBatchCalls.push(["save"]); },
  restore() { canvasBatchCalls.push(["restore"]); },
  translate(...args) { canvasBatchCalls.push(["translate", ...args]); },
  rotate(...args) { canvasBatchCalls.push(["rotate", ...args]); },
  drawImage(...args) { canvasBatchCalls.push(["drawImage", ...args]); },
};
const canvasBatchBounds = drawSpriteBatchCanvas2D(
  canvasBatchCtx,
  image,
  animated,
  [
    { frame: 0, x: 1, y: 2, scale: 1 },
    { frame: 1, x: 20, y: 30, scale: 2 },
  ],
);
assert.deepEqual(canvasBatchBounds, [
  { x: 1, y: 2, width: 6, height: 7 },
  { x: 20, y: 30, width: 12, height: 14 },
]);
assert.equal(
  canvasBatchCalls.filter((entry) => entry[0] === "drawImage").length,
  2,
);

assert.throws(
  () => buildSpriteBatch(indexed, [{}]),
  /frame not found/,
);
assert.throws(
  () => buildSpriteBatch(indexed, [{ frame: 0, scale: 0 }]),
  /scale must be > 0/,
);
assert.throws(
  () => buildSpriteBatch(indexed, [{ frame: 0 }], { maxInstances: 0 }),
  /maxInstances must be a positive integer/,
);
assert.throws(
  () => buildSpriteBatch(indexed, [{ frame: 0 }, { frame: 0 }], { maxInstances: 1 }),
  /exceeds maxInstances/,
);
assert.throws(
  () => drawSpriteBatchCanvas2D(canvasBatchCtx, image, indexRuntimeAtlas(plainAtlas), [
    { frame: "plain", scaleX: 1, scaleY: 2 },
  ]),
  /uniform scale/,
);


const instanced = buildInstancedSpriteBatch(indexed, [
  { frame: "hero_0.png", x: 100, y: 200, scale: 2 },
]);
assert.equal(instanced.instanceCount, 1);
assert.equal(instanced.instanceStrideFloats, 20);
assert.equal(instanced.instanceStrideBytes, 80);
assert.deepEqual(instanced.instanceLayout, [
  "visibleX",
  "visibleY",
  "visibleWidth",
  "visibleHeight",
  "u0",
  "v0",
  "u1",
  "v1",
  "atlasRotationFlag",
  "sourceWidth",
  "sourceHeight",
  "spriteRotationRadians",
  "pivotWorldX",
  "pivotWorldY",
  "reserved0",
  "reserved1",
  "tintR",
  "tintG",
  "tintB",
  "alpha",
]);
assert.deepEqual(
  Array.from(instanced.instances),
  [
    104,
    202,
    16,
    12,
    10 / 64,
    20 / 64,
    16 / 64,
    28 / 64,
    1,
    24,
    20,
    0,
    100,
    200,
    0,
    0,
    1,
    1,
    1,
    1,
  ],
);
assert.deepEqual(Array.from(instanced.unitQuad.vertices), [
  0, 0,
  1, 0,
  1, 1,
  0, 1,
]);
assert.deepEqual(Array.from(instanced.unitQuad.indices), [0, 1, 2, 0, 2, 3]);

assert.deepEqual(
  instancedSpriteUV(10 / 64, 20 / 64, 16 / 64, 28 / 64, 1, 0, 0),
  { u: 10 / 64, v: 28 / 64 },
);
assert.deepEqual(
  instancedSpriteUV(10 / 64, 20 / 64, 16 / 64, 28 / 64, 1, 1, 0),
  { u: 10 / 64, v: 20 / 64 },
);
assert.deepEqual(
  instancedSpriteUV(10 / 64, 20 / 64, 16 / 64, 28 / 64, 1, 1, 1),
  { u: 16 / 64, v: 20 / 64 },
);
assert.deepEqual(
  instancedSpriteUV(10 / 64, 20 / 64, 16 / 64, 28 / 64, 1, 0, 1),
  { u: 16 / 64, v: 28 / 64 },
);

const plainInstanced = buildInstancedSpriteBatch(indexRuntimeAtlas(plainAtlas), [
  { frame: "plain", x: 10, y: 20, scaleX: 2, scaleY: 3 },
]);
assert.equal(plainInstanced.instances[8], 0);
assert.deepEqual(
  instancedSpriteUV(1 / 16, 2 / 16, 5 / 16, 7 / 16, 0, 1, 1),
  { u: 5 / 16, v: 7 / 16 },
);

const manyInstances = Array.from({ length: 1000 }, (_, index) => ({
  frame: "plain",
  x: index,
  y: index,
}));
const classicMany = buildSpriteBatch(indexRuntimeAtlas(plainAtlas), manyInstances);
const instancedMany = buildInstancedSpriteBatch(indexRuntimeAtlas(plainAtlas), manyInstances);
assert.equal(classicMany.vertices.byteLength, 1000 * 4 * 4 * 4);
assert.equal(instancedMany.instances.byteLength, 1000 * 20 * 4);
assert.ok(
  instancedMany.instances.byteLength <
    classicMany.vertices.byteLength + classicMany.indices.byteLength,
);

assert.throws(
  () => buildInstancedSpriteBatch(indexed, [{ frame: 0, scale: 0 }]),
  /scale must be > 0/,
);
assert.throws(
  () => buildInstancedSpriteBatch(indexed, [{ frame: 0 }, { frame: 0 }], { maxInstances: 1 }),
  /exceeds maxInstances/,
);
assert.throws(
  () => instancedSpriteUV(0, 0, 1, 1, 2, 0, 0),
  /rotationFlag must be 0 or 1/,
);


const shaderContract = instancedSpriteWebGL2Shaders();
assert.equal(shaderContract.attributes.aUnitPosition.location, 0);
assert.equal(shaderContract.attributes.aVisibleRect.divisor, 1);
assert.equal(shaderContract.uniforms.uViewportSize, "vec2");
assert.match(shaderContract.vertex, /#version 300 es/);
assert.match(shaderContract.vertex, /rotationFlag/);
assert.match(shaderContract.fragment, /texture\(uTexture, vUv\)/);

const attributeViews = instancedSpriteAttributeViews(instanced);
assert.equal(attributeViews.buffer, instanced.instances);
assert.equal(attributeViews.strideBytes, 80);
assert.deepEqual(attributeViews.attributes, [
  {
    name: "aVisibleRect",
    location: 1,
    size: 4,
    offsetBytes: 0,
    divisor: 1,
  },
  {
    name: "aUvRect",
    location: 2,
    size: 4,
    offsetBytes: 16,
    divisor: 1,
  },
  {
    name: "aRotationAndSource",
    location: 3,
    size: 4,
    offsetBytes: 32,
    divisor: 1,
  },
  {
    name: "aPivotAndReserved",
    location: 4,
    size: 4,
    offsetBytes: 48,
    divisor: 1,
  },
  {
    name: "aTint",
    location: 5,
    size: 4,
    offsetBytes: 64,
    divisor: 1,
  },
]);
assert.throws(
  () => instancedSpriteAttributeViews({ instances: new Float32Array(), instanceStrideFloats: 8 }),
  /unsupported instanced sprite stride/,
);


const atlasB = {
  ...plainAtlas,
  image: "atlas-b.png",
  frames: [
    {
      ...plainAtlas.frames[0],
      index: 0,
      name: "enemy",
      atlasRegion: { x: 2, y: 3, width: 4, height: 5 },
      uv: { u0: 2 / 16, v0: 3 / 16, u1: 6 / 16, v1: 8 / 16 },
    },
  ],
};

const pages = createRuntimeAtlasPages([
  { id: "heroes", atlas: indexRuntimeAtlas(plainAtlas), texture: { id: "tex-a" } },
  { id: "enemies", atlas: atlasB, texture: { id: "tex-b" } },
]);
assert.equal(pages.page("heroes").atlas.frame("plain").index, 0);
assert.equal(pages.page("enemies").atlas.frame("enemy").name, "enemy");
assert.equal(pages.page("heroes").texture.id, "tex-a");

const paged = buildTexturePageBatches(
  pages,
  [
    { page: "heroes", frame: "plain", x: 0, y: 0 },
    { page: "enemies", frame: "enemy", x: 10, y: 0 },
    { page: "heroes", frame: "plain", x: 20, y: 0 },
    { page: "enemies", frame: "enemy", x: 30, y: 0 },
  ],
  { mode: "instanced" },
);
assert.equal(paged.pageCount, 2);
assert.equal(paged.instanceCount, 4);
assert.equal(paged.inputTextureSwitches, 3);
assert.equal(paged.outputTextureSwitches, 1);
assert.equal(paged.textureSwitchesSaved, 2);
assert.equal(paged.batchCount, 2);
assert.deepEqual(paged.inputPageSequence, [
  "heroes",
  "enemies",
  "heroes",
  "enemies",
]);
assert.deepEqual(
  paged.batches.map((batch) => [batch.pageId, batch.instanceCount, batch.inputIndices]),
  [
    ["heroes", 2, [0, 2]],
    ["enemies", 2, [1, 3]],
  ],
);
assert.equal(paged.batches[0].batch.instanceCount, 2);
assert.equal(paged.batches[1].batch.instanceCount, 2);

const pagedClassic = buildTexturePageBatches(
  pages,
  [
    { page: "enemies", frame: "enemy", x: 0, y: 0 },
    { page: "heroes", frame: "plain", x: 10, y: 0 },
    { page: "enemies", frame: "enemy", x: 20, y: 0 },
  ],
  { mode: "classic", preserveOrder: true },
);
assert.equal(pagedClassic.mode, "classic");
assert.equal(pagedClassic.preserveOrder, true);
assert.deepEqual(
  pagedClassic.batches.map((batch) => [batch.pageId, batch.inputIndices]),
  [
    ["enemies", [0]],
    ["heroes", [1]],
    ["enemies", [2]],
  ],
);
assert.equal(pagedClassic.pageCount, 2);
assert.equal(pagedClassic.batchCount, 3);
assert.equal(pagedClassic.inputTextureSwitches, 2);
assert.equal(pagedClassic.outputTextureSwitches, 2);
assert.equal(pagedClassic.textureSwitchesSaved, 0);
assert.equal(pagedClassic.batches[0].batch.vertexCount, 4);

assert.throws(
  () => createRuntimeAtlasPages([
    { id: "dup", atlas: plainAtlas },
    { id: "dup", atlas: atlasB },
  ]),
  /duplicate runtime atlas page id/,
);
assert.throws(
  () => buildTexturePageBatches(pages, [{ page: "missing", frame: "plain" }]),
  /runtime atlas page not found/,
);
assert.throws(
  () => buildTexturePageBatches(pages, [], { mode: "unknown" }),
  /mode must be instanced or classic/,
);


function createMockWebGL2() {
  const calls = [];
  let nextId = 1;
  const object = (type) => ({ type, id: nextId++ });
  const gl = {
    calls,
    VERTEX_SHADER: 0x8B31,
    FRAGMENT_SHADER: 0x8B30,
    COMPILE_STATUS: 0x8B81,
    LINK_STATUS: 0x8B82,
    ARRAY_BUFFER: 0x8892,
    ELEMENT_ARRAY_BUFFER: 0x8893,
    STATIC_DRAW: 0x88E4,
    DYNAMIC_DRAW: 0x88E8,
    FLOAT: 0x1406,
    TEXTURE0: 0x84C0,
    TEXTURE_2D: 0x0DE1,
    TEXTURE_MIN_FILTER: 0x2801,
    TEXTURE_MAG_FILTER: 0x2800,
    TEXTURE_WRAP_S: 0x2802,
    TEXTURE_WRAP_T: 0x2803,
    LINEAR: 0x2601,
    NEAREST: 0x2600,
    CLAMP_TO_EDGE: 0x812F,
    REPEAT: 0x2901,
    RGBA: 0x1908,
    UNSIGNED_BYTE: 0x1401,
    UNPACK_PREMULTIPLY_ALPHA_WEBGL: 0x9241,
    TRIANGLES: 0x0004,
    UNSIGNED_SHORT: 0x1403,
    BLEND: 0x0BE2,
    SRC_ALPHA: 0x0302,
    ONE_MINUS_SRC_ALPHA: 0x0303,
    createShader(type) {
      const value = object("shader");
      calls.push(["createShader", type, value.id]);
      return value;
    },
    shaderSource(shader, source) {
      calls.push(["shaderSource", shader.id, source.includes("#version 300 es")]);
    },
    compileShader(shader) {
      calls.push(["compileShader", shader.id]);
    },
    getShaderParameter(shader, parameter) {
      calls.push(["getShaderParameter", shader.id, parameter]);
      return true;
    },
    getShaderInfoLog() { return ""; },
    deleteShader(shader) { calls.push(["deleteShader", shader.id]); },
    createProgram() {
      const value = object("program");
      calls.push(["createProgram", value.id]);
      return value;
    },
    attachShader(program, shader) {
      calls.push(["attachShader", program.id, shader.id]);
    },
    linkProgram(program) { calls.push(["linkProgram", program.id]); },
    getProgramParameter(program, parameter) {
      calls.push(["getProgramParameter", program.id, parameter]);
      return true;
    },
    getProgramInfoLog() { return ""; },
    deleteProgram(program) { calls.push(["deleteProgram", program.id]); },
    createVertexArray() {
      const value = object("vao");
      calls.push(["createVertexArray", value.id]);
      return value;
    },
    deleteVertexArray(vao) { calls.push(["deleteVertexArray", vao.id]); },
    createBuffer() {
      const value = object("buffer");
      calls.push(["createBuffer", value.id]);
      return value;
    },
    createTexture() {
      const value = object("texture");
      calls.push(["createTexture", value.id]);
      return value;
    },
    deleteTexture(texture) {
      calls.push(["deleteTexture", texture.id]);
    },
    deleteBuffer(buffer) { calls.push(["deleteBuffer", buffer.id]); },
    bindVertexArray(vao) { calls.push(["bindVertexArray", vao?.id ?? null]); },
    bindBuffer(target, buffer) { calls.push(["bindBuffer", target, buffer?.id ?? null]); },
    bufferData(target, data, usage) {
      calls.push(["bufferData", target, data.byteLength, usage]);
    },
    bufferSubData(target, offset, data) {
      calls.push(["bufferSubData", target, offset, data.byteLength]);
    },
    enableVertexAttribArray(location) {
      calls.push(["enableVertexAttribArray", location]);
    },
    vertexAttribPointer(location, size, type, normalized, stride, offset) {
      calls.push([
        "vertexAttribPointer",
        location,
        size,
        type,
        normalized,
        stride,
        offset,
      ]);
    },
    vertexAttribDivisor(location, divisor) {
      calls.push(["vertexAttribDivisor", location, divisor]);
    },
    getUniformLocation(program, name) {
      const value = { program: program.id, name };
      calls.push(["getUniformLocation", program.id, name]);
      return value;
    },
    enable(capability) { calls.push(["enable", capability]); },
    blendFunc(source, destination) {
      calls.push(["blendFunc", source, destination]);
    },
    useProgram(program) { calls.push(["useProgram", program.id]); },
    uniform2f(location, x, y) {
      calls.push(["uniform2f", location.name, x, y]);
    },
    activeTexture(texture) { calls.push(["activeTexture", texture]); },
    bindTexture(target, texture) {
      calls.push(["bindTexture", target, texture?.id ?? texture ?? null]);
    },
    pixelStorei(parameter, value) {
      calls.push(["pixelStorei", parameter, value]);
    },
    texParameteri(target, parameter, value) {
      calls.push(["texParameteri", target, parameter, value]);
    },
    texImage2D(...args) {
      const source = args.at(-1);
      calls.push([
        "texImage2D",
        args[0],
        args[1],
        args[2],
        args[3],
        args[4],
        source?.id ?? source,
      ]);
    },
    generateMipmap(target) {
      calls.push(["generateMipmap", target]);
    },
    uniform1i(location, value) {
      calls.push(["uniform1i", location.name, value]);
    },
    drawElementsInstanced(mode, count, type, offset, instances) {
      calls.push(["drawElementsInstanced", mode, count, type, offset, instances]);
    },
  };
  return gl;
}

const rendererGl = createMockWebGL2();
const renderer = createInstancedSpriteRendererWebGL2(rendererGl);
const rendererBatch = buildInstancedSpriteBatch(indexRuntimeAtlas(plainAtlas), [
  { frame: "plain", x: 1, y: 2 },
  { frame: "plain", x: 3, y: 4 },
]);
const rendererTexture = { id: "texture-a" };
const firstRender = renderer.renderBatch(rendererBatch, rendererTexture, 800, 600);
assert.deepEqual(firstRender, {
  drawCalls: 1,
  instances: 2,
  uploadedBytes: rendererBatch.instances.byteLength,
});

assert.equal(renderer.alphaBlending, true);
assert.ok(
  rendererGl.calls.some(
    (call) => call[0] === "enable" && call[1] === rendererGl.BLEND,
  ),
);
assert.ok(
  rendererGl.calls.some(
    (call) =>
      call[0] === "blendFunc" &&
      call[1] === rendererGl.SRC_ALPHA &&
      call[2] === rendererGl.ONE_MINUS_SRC_ALPHA,
  ),
);
assert.equal(renderer.uploadedCapacityBytes, rendererBatch.instances.byteLength);
assert.ok(
  rendererGl.calls.some(
    (call) =>
      call[0] === "drawElementsInstanced" &&
      call[2] === 6 &&
      call[5] === 2,
  ),
);
assert.ok(
  rendererGl.calls.some(
    (call) => call[0] === "bindTexture" && call[2] === "texture-a",
  ),
);

const dataUploadsBefore = rendererGl.calls.filter(
  (call) => call[0] === "bufferData" && call[3] === rendererGl.DYNAMIC_DRAW,
).length;
renderer.renderBatch(rendererBatch, rendererTexture, 800, 600);
const subDataUploads = rendererGl.calls.filter(
  (call) => call[0] === "bufferSubData",
);
assert.equal(dataUploadsBefore, 1);
assert.ok(subDataUploads.length >= 1);

const rendererPages = createRuntimeAtlasPages([
  { id: "a", atlas: plainAtlas, texture: { id: "page-a" } },
  { id: "b", atlas: atlasB, texture: { id: "page-b" } },
]);
const rendererPageBatches = buildTexturePageBatches(
  rendererPages,
  [
    { page: "a", frame: "plain", x: 0, y: 0 },
    { page: "b", frame: "enemy", x: 10, y: 0 },
  ],
  { mode: "instanced" },
);
const pageRender = renderer.renderPageBatches(rendererPageBatches, 1024, 768);
assert.deepEqual(pageRender, {
  drawCalls: 2,
  instances: 2,
  uploadedBytes:
    rendererPageBatches.batches[0].batch.instances.byteLength +
    rendererPageBatches.batches[1].batch.instances.byteLength,
  textureSwitches: 1,
});

renderer.dispose();
assert.equal(renderer.disposed, true);
assert.throws(
  () => renderer.renderBatch(rendererBatch, rendererTexture, 800, 600),
  /renderer is disposed/,
);
renderer.dispose();

assert.throws(
  () => createInstancedSpriteRendererWebGL2({}),
  /drawElementsInstanced is required/,
);


const resolvingGl = createMockWebGL2();
const resolvedTextures = [];
const resolvingRenderer = createInstancedSpriteRendererWebGL2(resolvingGl, {
  resolveTexture(textureKey, entry) {
    resolvedTextures.push([textureKey, entry.pageId]);
    return { id: `gpu-${entry.pageId}` };
  },
});
const keyPages = createRuntimeAtlasPages([
  { id: "a", atlas: plainAtlas, texture: "hero-texture-key" },
  { id: "b", atlas: atlasB, texture: "enemy-texture-key" },
]);
const keyPageBatches = buildTexturePageBatches(
  keyPages,
  [
    { page: "a", frame: "plain" },
    { page: "b", frame: "enemy" },
  ],
  { mode: "instanced" },
);
resolvingRenderer.renderPageBatches(keyPageBatches, 320, 240);
assert.deepEqual(resolvedTextures, [
  ["hero-texture-key", "a"],
  ["enemy-texture-key", "b"],
]);
assert.ok(
  resolvingGl.calls.some(
    (call) => call[0] === "bindTexture" && call[2] === "gpu-a",
  ),
);
assert.ok(
  resolvingGl.calls.some(
    (call) => call[0] === "bindTexture" && call[2] === "gpu-b",
  ),
);
resolvingRenderer.dispose();


const textureGl = createMockWebGL2();
const textureCache = createWebGL2TextureCache(textureGl, {
  minFilter: textureGl.NEAREST,
  magFilter: textureGl.LINEAR,
  wrapS: textureGl.CLAMP_TO_EDGE,
  wrapT: textureGl.REPEAT,
  premultiplyAlpha: true,
});
const imageSource = { id: "image-source" };
const textureOne = textureCache.acquire("hero", imageSource);
const textureAgain = textureCache.acquire("hero", imageSource);
assert.equal(textureOne, textureAgain);
assert.equal(textureCache.size, 1);
assert.equal(textureCache.references("hero"), 2);
assert.equal(textureCache.has("hero"), true);
assert.equal(textureCache.get("hero"), textureOne);
assert.ok(
  textureGl.calls.some(
    (call) =>
      call[0] === "texParameteri" &&
      call[2] === textureGl.TEXTURE_MIN_FILTER &&
      call[3] === textureGl.NEAREST,
  ),
);
assert.ok(
  textureGl.calls.some(
    (call) =>
      call[0] === "pixelStorei" &&
      call[1] === textureGl.UNPACK_PREMULTIPLY_ALPHA_WEBGL &&
      call[2] === 1,
  ),
);
assert.ok(
  textureGl.calls.some(
    (call) => call[0] === "texImage2D" && call.at(-1) === "image-source",
  ),
);

assert.equal(textureCache.release("hero"), false);
assert.equal(textureCache.references("hero"), 1);
assert.equal(textureCache.release("hero"), true);
assert.equal(textureCache.has("hero"), false);
assert.equal(
  textureGl.calls.filter((call) => call[0] === "deleteTexture").length,
  1,
);

const mipSource = { id: "mip-source" };
textureCache.acquire("mip", mipSource, {
  generateMipmap: true,
  minFilter: textureGl.LINEAR,
});
assert.ok(
  textureGl.calls.some((call) => call[0] === "generateMipmap"),
);
assert.equal(textureCache.delete("mip"), true);

textureCache.acquire("a", { id: "a-source" });
textureCache.acquire("b", { id: "b-source" });
assert.equal(textureCache.size, 2);
textureCache.clear();
assert.equal(textureCache.size, 0);

textureCache.acquire("c", { id: "c-source" });
textureCache.dispose();
assert.equal(textureCache.disposed, true);
assert.equal(textureCache.size, 0);
assert.throws(
  () => textureCache.acquire("d", { id: "d-source" }),
  /texture cache is disposed/,
);
textureCache.dispose();

assert.throws(
  () => createWebGL2TextureCache({}),
  /texture-capable context required/,
);


const asyncTextureGl = createMockWebGL2();
const asyncTextureCache = createWebGL2TextureCache(asyncTextureGl);
let factoryCalls = 0;
let resolveSource;
const sourcePromise = new Promise((resolve) => {
  resolveSource = resolve;
});
const firstLoad = asyncTextureCache.load("shared", async () => {
  factoryCalls += 1;
  return sourcePromise;
});
const secondLoad = asyncTextureCache.load("shared", async () => {
  factoryCalls += 1;
  return { id: "should-not-be-used" };
});
assert.equal(asyncTextureCache.pendingCount, 1);
assert.equal(factoryCalls, 1);
resolveSource({ id: "shared-source" });
const [loadedOne, loadedTwo] = await Promise.all([firstLoad, secondLoad]);
assert.equal(loadedOne, loadedTwo);
assert.equal(asyncTextureCache.pendingCount, 0);
assert.equal(asyncTextureCache.references("shared"), 2);
assert.equal(
  asyncTextureGl.calls.filter((call) => call[0] === "createTexture").length,
  1,
);
assert.equal(asyncTextureCache.release("shared"), false);
assert.equal(asyncTextureCache.release("shared"), true);

const cachedTexture = await asyncTextureCache.load(
  "cached",
  Promise.resolve({ id: "cached-source" }),
);
const createCountBeforeCachedReload = asyncTextureGl.calls.filter(
  (call) => call[0] === "createTexture",
).length;
const cachedAgain = await asyncTextureCache.load(
  "cached",
  Promise.resolve({ id: "unused-source" }),
);
assert.equal(cachedTexture, cachedAgain);
assert.equal(asyncTextureCache.references("cached"), 2);
assert.equal(
  asyncTextureGl.calls.filter((call) => call[0] === "createTexture").length,
  createCountBeforeCachedReload,
);
asyncTextureCache.dispose();

const disposedDuringLoadGl = createMockWebGL2();
const disposedDuringLoadCache = createWebGL2TextureCache(disposedDuringLoadGl);
let finishDisposedLoad;
const waitingLoad = disposedDuringLoadCache.load(
  "late",
  () =>
    new Promise((resolve) => {
      finishDisposedLoad = resolve;
    }),
);
disposedDuringLoadCache.dispose();
finishDisposedLoad({ id: "late-source" });
await assert.rejects(waitingLoad, /texture cache is disposed/);
assert.equal(disposedDuringLoadCache.pendingCount, 0);


const bitmapCalls = [];
const fetchedUrls = [];
const fakeFetch = async (url) => {
  fetchedUrls.push(url);
  return {
    ok: true,
    status: 200,
    async blob() {
      return { id: `blob:${url}` };
    },
  };
};
const fakeCreateImageBitmap = async (blob, options) => {
  bitmapCalls.push([blob.id, options ?? null]);
  return { id: `bitmap:${blob.id}` };
};

const loadedBitmap = await loadImageBitmapSource("hero.png", {
  fetchImpl: fakeFetch,
  createImageBitmapImpl: fakeCreateImageBitmap,
  imageBitmapOptions: { premultiplyAlpha: "premultiply" },
});
assert.deepEqual(loadedBitmap, { id: "bitmap:blob:hero.png" });
assert.deepEqual(fetchedUrls, ["hero.png"]);
assert.deepEqual(bitmapCalls, [
  ["blob:hero.png", { premultiplyAlpha: "premultiply" }],
]);

await assert.rejects(
  loadImageBitmapSource("missing.png", {
    fetchImpl: async () => ({ ok: false, status: 404 }),
    createImageBitmapImpl: fakeCreateImageBitmap,
  }),
  /HTTP 404/,
);

const preloadGl = createMockWebGL2();
const preloadCache = createWebGL2TextureCache(preloadGl);
const sharedPages = createRuntimeAtlasPages([
  { id: "hero-a", atlas: plainAtlas, texture: "shared.png" },
  { id: "hero-b", atlas: plainAtlas, texture: "shared.png" },
]);
let sharedFetches = 0;
const preloadResult = await preloadRuntimeAtlasPageTextures(
  sharedPages,
  preloadCache,
  {
    fetchImpl: async (url) => {
      sharedFetches += 1;
      return {
        ok: true,
        status: 200,
        async blob() {
          return { id: `blob:${url}` };
        },
      };
    },
    createImageBitmapImpl: async (blob) => ({ id: `bitmap:${blob.id}` }),
  },
);
assert.equal(preloadResult.count, 2);
assert.equal(sharedFetches, 1);
assert.equal(preloadCache.size, 1);
assert.equal(preloadCache.references("shared.png"), 2);
assert.equal(preloadResult.pages[0].texture, preloadResult.pages[1].texture);

const releaseResult = releaseRuntimeAtlasPageTextures(
  preloadCache,
  preloadResult,
);
assert.deepEqual(releaseResult, { released: 2, deleted: 1 });
assert.equal(preloadCache.size, 0);

const rollbackGl = createMockWebGL2();
const rollbackCache = createWebGL2TextureCache(rollbackGl);
const rollbackPages = createRuntimeAtlasPages([
  { id: "ok", atlas: plainAtlas, texture: "ok.png" },
  { id: "bad", atlas: atlasB, texture: "bad.png" },
]);
await assert.rejects(
  preloadRuntimeAtlasPageTextures(rollbackPages, rollbackCache, {
    fetchImpl: async (url) => ({
      ok: url !== "bad.png",
      status: url === "bad.png" ? 500 : 200,
      async blob() {
        return { id: `blob:${url}` };
      },
    }),
    createImageBitmapImpl: async (blob) => ({ id: `bitmap:${blob.id}` }),
  }),
  /HTTP 500/,
);
assert.equal(rollbackCache.size, 0);

const sceneGl = createMockWebGL2();
const scene = await createWebGL2RuntimeAtlasScene(
  sceneGl,
  [
    { id: "heroes", atlas: plainAtlas, texture: "heroes.png" },
    { id: "enemies", atlas: atlasB, texture: "enemies.png" },
  ],
  {
    loaderOptions: {
      fetchImpl: async (url) => ({
        ok: true,
        status: 200,
        async blob() {
          return { id: `blob:${url}` };
        },
      }),
      createImageBitmapImpl: async (blob) => ({
        id: `bitmap:${blob.id}`,
      }),
    },
  },
);
assert.equal(scene.textureCache.size, 2);
const sceneBatches = scene.buildBatches([
  { page: "heroes", frame: "plain", x: 1, y: 2 },
  { page: "enemies", frame: "enemy", x: 3, y: 4 },
]);
assert.equal(sceneBatches.batchCount, 2);

const sceneRender = scene.render(
  [
    { page: "heroes", frame: "plain", x: 1, y: 2 },
    { page: "enemies", frame: "enemy", x: 3, y: 4 },
  ],
  640,
  360,
);
assert.equal(sceneRender.drawCalls, 2);
assert.equal(sceneRender.instances, 2);

scene.dispose();
assert.equal(scene.disposed, true);
assert.equal(scene.textureCache.disposed, true);
assert.throws(
  () => scene.buildBatches([{ page: "heroes", frame: "plain" }]),
  /scene is disposed/,
);
scene.dispose();

const externalSceneGl = createMockWebGL2();
const externalCache = createWebGL2TextureCache(externalSceneGl);
const externalScene = await createWebGL2RuntimeAtlasScene(
  externalSceneGl,
  [{ id: "heroes", atlas: plainAtlas, texture: "heroes.png" }],
  {
    textureCache: externalCache,
    loaderOptions: {
      fetchImpl: async (url) => ({
        ok: true,
        status: 200,
        async blob() {
          return { id: `blob:${url}` };
        },
      }),
      createImageBitmapImpl: async (blob) => ({
        id: `bitmap:${blob.id}`,
      }),
    },
  },
);
externalScene.dispose();
assert.equal(externalCache.disposed, false);
assert.equal(externalCache.size, 0);
externalCache.dispose();


const scenePagesForCulling = createRuntimeAtlasPages([
  { id: "heroes", atlas: plainAtlas, texture: "heroes.png" },
]);

assert.deepEqual(
  spriteInstanceBounds(scenePagesForCulling, {
    page: "heroes",
    frame: "plain",
    x: 10,
    y: 20,
    scaleX: 2,
    scaleY: 3,
  }),
  {
    x: 10,
    y: 20,
    width: 12,
    height: 21,
    visibleX: 12,
    visibleY: 23,
    visibleWidth: 8,
    visibleHeight: 15,
  },
);

const cullingInput = [
  { page: "heroes", frame: "plain", x: 0, y: 0, z: 5, id: "inside-a" },
  { page: "heroes", frame: "plain", x: 20, y: 20, z: 1, id: "inside-b" },
  { page: "heroes", frame: "plain", x: 200, y: 200, z: 3, id: "outside" },
  { page: "heroes", frame: "plain", x: -3, y: -3, z: 1, id: "edge" },
];
const culled = cullSpriteInstances(
  scenePagesForCulling,
  cullingInput,
  { x: 0, y: 0, width: 64, height: 64 },
);
assert.equal(culled.inputCount, 4);
assert.equal(culled.visibleCount, 3);
assert.equal(culled.culledCount, 1);
assert.deepEqual(culled.culledIndices, [2]);
assert.deepEqual(
  culled.instances.map((instance) => instance.id),
  ["inside-a", "inside-b", "edge"],
);

const paddedCull = cullSpriteInstances(
  scenePagesForCulling,
  [{ page: "heroes", frame: "plain", x: 66, y: 0, id: "near" }],
  { x: 0, y: 0, width: 64, height: 64 },
  { padding: 8 },
);
assert.equal(paddedCull.visibleCount, 1);

const stableSorted = stableSortSpriteInstances(
  [
    { id: "a", z: 2 },
    { id: "b", z: 1 },
    { id: "c", z: 1 },
    { id: "d", z: 3 },
  ],
);
assert.deepEqual(
  stableSorted.map((instance) => instance.id),
  ["b", "c", "a", "d"],
);

const stableSortedDesc = stableSortSpriteInstances(
  [
    { id: "a", z: 2 },
    { id: "b", z: 1 },
    { id: "c", z: 1 },
    { id: "d", z: 3 },
  ],
  { direction: "descending" },
);
assert.deepEqual(
  stableSortedDesc.map((instance) => instance.id),
  ["d", "a", "b", "c"],
);

const preparedScene = prepareSpriteSceneInstances(
  scenePagesForCulling,
  cullingInput,
  {
    viewport: { x: 0, y: 0, width: 64, height: 64 },
    sortKey: "z",
  },
);
assert.equal(preparedScene.inputCount, 4);
assert.equal(preparedScene.outputCount, 3);
assert.equal(preparedScene.culledCount, 1);
assert.deepEqual(
  preparedScene.instances.map((instance) => instance.id),
  ["inside-b", "edge", "inside-a"],
);

assert.throws(
  () => stableSortSpriteInstances([{ z: Number.NaN }]),
  /sort value z must be finite/,
);
assert.throws(
  () =>
    cullSpriteInstances(
      scenePagesForCulling,
      cullingInput,
      { width: -1, height: 10 },
    ),
  /viewport width\/height must be >= 0/,
);


const culledSceneGl = createMockWebGL2();
const culledScene = await createWebGL2RuntimeAtlasScene(
  culledSceneGl,
  [{ id: "heroes", atlas: plainAtlas, texture: "heroes.png" }],
  {
    loaderOptions: {
      fetchImpl: async (url) => ({
        ok: true,
        status: 200,
        async blob() {
          return { id: `blob:${url}` };
        },
      }),
      createImageBitmapImpl: async (blob) => ({
        id: `bitmap:${blob.id}`,
      }),
    },
  },
);

const culledSceneBatches = culledScene.buildBatches(
  [
    { page: "heroes", frame: "plain", x: 100, y: 100, z: 9, id: "offscreen" },
    { page: "heroes", frame: "plain", x: 10, y: 10, z: 2, id: "front" },
    { page: "heroes", frame: "plain", x: 5, y: 5, z: 1, id: "back" },
  ],
  {
    viewport: { x: 0, y: 0, width: 32, height: 32 },
    sort: true,
    sortKey: "z",
    preserveOrder: true,
  },
);
assert.equal(culledSceneBatches.instanceCount, 2);
assert.equal(culledSceneBatches.scenePreparation.culledCount, 1);
assert.deepEqual(
  culledSceneBatches.scenePreparation.instances.map((instance) => instance.id),
  ["back", "front"],
);
assert.deepEqual(culledSceneBatches.batches[0].inputIndices, [0, 1]);

const culledSceneRender = culledScene.render(
  [
    { page: "heroes", frame: "plain", x: 100, y: 100, z: 9 },
    { page: "heroes", frame: "plain", x: 10, y: 10, z: 2 },
    { page: "heroes", frame: "plain", x: 5, y: 5, z: 1 },
  ],
  32,
  32,
  {
    viewport: { x: 0, y: 0, width: 32, height: 32 },
    sort: true,
    preserveOrder: true,
  },
);
assert.equal(culledSceneRender.instances, 2);
culledScene.dispose();


function createMockCanvas() {
  const listeners = new Map();
  return {
    width: 0,
    height: 0,
    clientWidth: 320,
    clientHeight: 180,
    addEventListener(type, handler) {
      if (!listeners.has(type)) listeners.set(type, new Set());
      listeners.get(type).add(handler);
    },
    removeEventListener(type, handler) {
      listeners.get(type)?.delete(handler);
    },
    dispatch(type, event = {}) {
      for (const handler of listeners.get(type) ?? []) {
        handler(event);
      }
    },
    getContext() {
      return null;
    },
  };
}

const resizeGl = createMockWebGL2();
resizeGl.viewport = (...args) => resizeGl.calls.push(["viewport", ...args]);
const resizeCanvas = createMockCanvas();
const resizeResult = resizeWebGL2Canvas(resizeCanvas, resizeGl, {
  pixelRatio: 2,
  maxPixelRatio: 1.5,
});
assert.deepEqual(resizeResult, {
  resized: true,
  cssWidth: 320,
  cssHeight: 180,
  pixelRatio: 1.5,
  width: 480,
  height: 270,
});
assert.equal(resizeCanvas.width, 480);
assert.equal(resizeCanvas.height, 270);
assert.deepEqual(resizeGl.calls.at(-1), ["viewport", 0, 0, 480, 270]);

const contextGlA = createMockWebGL2();
contextGlA.viewport = (...args) => contextGlA.calls.push(["viewport", ...args]);
const contextGlB = createMockWebGL2();
contextGlB.viewport = (...args) => contextGlB.calls.push(["viewport", ...args]);
const runtimeCanvas = createMockCanvas();
let contextIndex = 0;
let lostCallbacks = 0;
let restoredCallbacks = 0;

const canvasRuntime = await createWebGL2CanvasRuntime(
  runtimeCanvas,
  [{ id: "heroes", atlas: plainAtlas, texture: "heroes.png" }],
  {
    getContext() {
      return contextIndex === 0 ? contextGlA : contextGlB;
    },
    resizeOptions: { pixelRatio: 1 },
    sceneOptions: {
      loaderOptions: {
        fetchImpl: async (url) => ({
          ok: true,
          status: 200,
          async blob() {
            return { id: `blob:${url}` };
          },
        }),
        createImageBitmapImpl: async (blob) => ({
          id: `bitmap:${blob.id}`,
        }),
      },
    },
    onContextLost() {
      lostCallbacks += 1;
    },
    onContextRestored() {
      restoredCallbacks += 1;
    },
  },
);

assert.equal(canvasRuntime.contextLost, false);
assert.equal(canvasRuntime.scene.textureCache.size, 1);
const initialRender = canvasRuntime.render([
  { page: "heroes", frame: "plain", x: 1, y: 2 },
]);
assert.equal(initialRender.drawCalls, 1);

let prevented = false;
runtimeCanvas.dispatch("webglcontextlost", {
  preventDefault() {
    prevented = true;
  },
});
assert.equal(prevented, true);
assert.equal(canvasRuntime.contextLost, true);
assert.equal(lostCallbacks, 1);
assert.throws(
  () =>
    canvasRuntime.render([
      { page: "heroes", frame: "plain", x: 1, y: 2 },
    ]),
  /context is lost/,
);

contextIndex = 1;
runtimeCanvas.dispatch("webglcontextrestored");
await canvasRuntime.waitForRestore();
assert.equal(canvasRuntime.contextLost, false);
assert.equal(restoredCallbacks, 1);
assert.equal(canvasRuntime.gl, contextGlB);
assert.equal(canvasRuntime.scene.textureCache.size, 1);
const restoredRender = canvasRuntime.render([
  { page: "heroes", frame: "plain", x: 1, y: 2 },
]);
assert.equal(restoredRender.drawCalls, 1);

canvasRuntime.dispose();
assert.equal(canvasRuntime.disposed, true);
assert.throws(() => canvasRuntime.resize(), /runtime is disposed/);
canvasRuntime.dispose();


const entityStore = createSpriteEntityStore();
const heroEntity = entityStore.add({
  page: "heroes",
  frame: "plain",
  x: 10,
  y: 20,
  z: 2,
});
assert.equal(heroEntity.id, 1);
assert.equal(entityStore.size, 1);
assert.equal(entityStore.version, 1);
assert.deepEqual(entityStore.get(1), heroEntity);

const enemyEntity = entityStore.add({
  id: "enemy-1",
  page: "heroes",
  frame: "plain",
  x: 30,
  y: 40,
  enabled: false,
});
assert.equal(enemyEntity.id, "enemy-1");
assert.equal(entityStore.size, 2);
assert.equal(entityStore.version, 2);
assert.deepEqual(
  entityStore.snapshot().map((entity) => entity.id),
  [1],
);
assert.deepEqual(
  entityStore.snapshot({ includeDisabled: true }).map((entity) => entity.id),
  [1, "enemy-1"],
);

const updatedHero = entityStore.update(1, { x: 15, z: 5 });
assert.equal(updatedHero.x, 15);
assert.equal(updatedHero.z, 5);
assert.equal(entityStore.version, 3);

const renderInstances = entityStore.instances();
assert.deepEqual(renderInstances, [
  {
    id: 1,
    page: "heroes",
    frame: "plain",
    x: 15,
    y: 20,
    z: 5,
  },
]);

const versionBeforeTransaction = entityStore.version;
assert.throws(
  () =>
    entityStore.transact((tx) => {
      tx.update(1, { x: 99 });
      tx.add({
        id: "temporary",
        page: "heroes",
        frame: "plain",
      });
      throw new Error("rollback");
    }),
  /rollback/,
);
assert.equal(entityStore.version, versionBeforeTransaction);
assert.equal(entityStore.get(1).x, 15);
assert.equal(entityStore.has("temporary"), false);

entityStore.transact((tx) => {
  tx.update(1, { x: 25 });
  tx.remove("enemy-1");
});
assert.equal(entityStore.get(1).x, 25);
assert.equal(entityStore.has("enemy-1"), false);
assert.equal(entityStore.size, 1);

assert.throws(
  () => entityStore.update(1, { id: 2 }),
  /id cannot be changed/,
);
assert.throws(
  () =>
    entityStore.add({
      page: "heroes",
      frame: "plain",
      scale: 0,
    }),
  /scale must be > 0/,
);
assert.equal(entityStore.remove("missing"), null);
assert.equal(entityStore.clear(), 1);
assert.equal(entityStore.size, 0);


const entityRuntimeGlA = createMockWebGL2();
entityRuntimeGlA.viewport = (...args) => entityRuntimeGlA.calls.push(["viewport", ...args]);
const entityRuntimeGlB = createMockWebGL2();
entityRuntimeGlB.viewport = (...args) => entityRuntimeGlB.calls.push(["viewport", ...args]);
const entityRuntimeCanvas = createMockCanvas();
let entityRuntimeContextIndex = 0;

const entityRuntime = await createWebGL2CanvasRuntime(
  entityRuntimeCanvas,
  [{ id: "heroes", atlas: plainAtlas, texture: "heroes.png" }],
  {
    getContext() {
      return entityRuntimeContextIndex === 0
        ? entityRuntimeGlA
        : entityRuntimeGlB;
    },
    resizeOptions: { pixelRatio: 1 },
    sceneOptions: {
      loaderOptions: {
        fetchImpl: async (url) => ({
          ok: true,
          status: 200,
          async blob() {
            return { id: `blob:${url}` };
          },
        }),
        createImageBitmapImpl: async (blob) => ({
          id: `bitmap:${blob.id}`,
        }),
      },
    },
  },
);

entityRuntime.entities.add({
  id: "hero",
  page: "heroes",
  frame: "plain",
  x: 10,
  y: 10,
  z: 1,
});
entityRuntime.entities.add({
  id: "offscreen",
  page: "heroes",
  frame: "plain",
  x: 1000,
  y: 1000,
  z: 2,
});

const entityBatches = entityRuntime.buildEntityBatches({
  viewport: { x: 0, y: 0, width: 64, height: 64 },
  sort: true,
  preserveOrder: true,
});
assert.equal(entityBatches.instanceCount, 1);
assert.equal(entityBatches.scenePreparation.culledCount, 1);

const entityRender = entityRuntime.renderEntities({
  viewport: { x: 0, y: 0, width: 64, height: 64 },
  sort: true,
  preserveOrder: true,
});
assert.equal(entityRender.instances, 1);

entityRuntimeCanvas.dispatch("webglcontextlost", {
  preventDefault() {},
});
entityRuntimeContextIndex = 1;
entityRuntimeCanvas.dispatch("webglcontextrestored");
await entityRuntime.waitForRestore();

assert.equal(entityRuntime.entities.size, 2);
assert.equal(entityRuntime.entities.get("hero").x, 10);
const entityRenderAfterRestore = entityRuntime.renderEntities({
  viewport: { x: 0, y: 0, width: 64, height: 64 },
  preserveOrder: true,
});
assert.equal(entityRenderAfterRestore.instances, 1);

entityRuntime.entities.update("hero", { x: 20 });
assert.equal(entityRuntime.entities.get("hero").x, 20);
entityRuntime.dispose();

const suppliedStore = createSpriteEntityStore();
suppliedStore.add({
  id: "supplied",
  page: "heroes",
  frame: "plain",
});
const suppliedRuntimeGl = createMockWebGL2();
suppliedRuntimeGl.viewport = (...args) => suppliedRuntimeGl.calls.push(["viewport", ...args]);
const suppliedCanvas = createMockCanvas();
const suppliedRuntime = await createWebGL2CanvasRuntime(
  suppliedCanvas,
  [{ id: "heroes", atlas: plainAtlas, texture: "heroes.png" }],
  {
    entityStore: suppliedStore,
    getContext() {
      return suppliedRuntimeGl;
    },
    resizeOptions: { pixelRatio: 1 },
    sceneOptions: {
      loaderOptions: {
        fetchImpl: async (url) => ({
          ok: true,
          status: 200,
          async blob() {
            return { id: `blob:${url}` };
          },
        }),
        createImageBitmapImpl: async (blob) => ({
          id: `bitmap:${blob.id}`,
        }),
      },
    },
  },
);
assert.equal(suppliedRuntime.entities, suppliedStore);
assert.equal(suppliedRuntime.renderEntities().instances, 1);
suppliedRuntime.dispose();
assert.equal(suppliedStore.size, 1);


const completedReplayPlayer = createAnimationPlayer(animated, "once", {
  autoplay: true,
});
completedReplayPlayer.update(2);
assert.equal(completedReplayPlayer.playing, false);
completedReplayPlayer.play();
assert.equal(completedReplayPlayer.playing, false);

const entityAnimationAtlas = {
  ...animatedAtlas,
  animations: [
    {
      ...animatedAtlas.animations[0],
      events: [
        { name: "step", timeSeconds: 0.05, payload: { foot: "left" } },
        { name: "impact", timeSeconds: 0.15 },
      ],
    },
    animatedAtlas.animations[1],
  ],
};
const entityAnimationPages = createRuntimeAtlasPages([
  {
    id: "heroes",
    atlas: entityAnimationAtlas,
    texture: "heroes.png",
  },
]);
const animatedEntities = createSpriteEntityStore();
animatedEntities.add({
  id: "animated-hero",
  page: "heroes",
  frame: 0,
  x: 10,
  y: 20,
});

const entityAnimationEvents = [];
const entityAnimationFrames = [];
const entityAnimationSystem = createSpriteAnimationSystem(
  entityAnimationPages,
  animatedEntities,
  {
    onEvent(event) {
      entityAnimationEvents.push([
        event.entityId,
        event.name,
        event.payload,
      ]);
    },
    onFrame(event) {
      entityAnimationFrames.push([
        event.entityId,
        event.sample.frame.index,
      ]);
    },
  },
);

const heroBinding = entityAnimationSystem.bind(
  "animated-hero",
  "run",
  { autoplay: true },
);
assert.equal(entityAnimationSystem.size, 1);
assert.equal(heroBinding.playing, true);
assert.equal(animatedEntities.get("animated-hero").frame, 0);

const animationUpdateA = entityAnimationSystem.update(0.16);
assert.equal(animationUpdateA.updatedCount, 1);
assert.equal(animatedEntities.get("animated-hero").frame, 1);
assert.deepEqual(entityAnimationEvents, [
  ["animated-hero", "step", { foot: "left" }],
  ["animated-hero", "impact", null],
]);
assert.ok(
  entityAnimationFrames.some(
    ([entityId, frameIndex]) =>
      entityId === "animated-hero" && frameIndex === 1,
  ),
);

heroBinding.pause();
const pausedEntityTime = heroBinding.timeSeconds;
entityAnimationSystem.update(1);
assert.equal(heroBinding.timeSeconds, pausedEntityTime);

heroBinding.seek(0);
assert.equal(animatedEntities.get("animated-hero").frame, 0);
heroBinding.setPlaybackRate(2);
assert.equal(heroBinding.player.playbackRate, 2);
heroBinding.play();
entityAnimationSystem.update(0.08);
assert.equal(animatedEntities.get("animated-hero").frame, 1);

assert.equal(
  entityAnimationSystem.get("animated-hero"),
  heroBinding,
);
assert.equal(
  entityAnimationSystem.unbind("animated-hero"),
  heroBinding,
);
assert.equal(entityAnimationSystem.size, 0);

entityAnimationSystem.bind("animated-hero", "once", {
  autoplay: true,
});
entityAnimationSystem.update(2);
assert.equal(
  entityAnimationSystem.get("animated-hero").playing,
  false,
);

animatedEntities.remove("animated-hero");
const removedAnimationUpdate = entityAnimationSystem.update(0.1);
assert.deepEqual(removedAnimationUpdate.removedEntityIds, ["animated-hero"]);
assert.equal(entityAnimationSystem.size, 0);

assert.throws(
  () => entityAnimationSystem.bind("missing", "run"),
  /sprite entity not found/,
);



const animatedRuntimeGlA = createMockWebGL2();
animatedRuntimeGlA.viewport = (...args) =>
  animatedRuntimeGlA.calls.push(["viewport", ...args]);
const animatedRuntimeGlB = createMockWebGL2();
animatedRuntimeGlB.viewport = (...args) =>
  animatedRuntimeGlB.calls.push(["viewport", ...args]);
const animatedRuntimeCanvas = createMockCanvas();
let animatedRuntimeContextIndex = 0;
const animatedRuntimeEvents = [];

const animatedRuntime = await createWebGL2CanvasRuntime(
  animatedRuntimeCanvas,
  [{ id: "heroes", atlas: entityAnimationAtlas, texture: "heroes.png" }],
  {
    getContext() {
      return animatedRuntimeContextIndex === 0
        ? animatedRuntimeGlA
        : animatedRuntimeGlB;
    },
    resizeOptions: { pixelRatio: 1 },
    animationOptions: {
      onEvent(event) {
        animatedRuntimeEvents.push([event.entityId, event.name]);
      },
    },
    sceneOptions: {
      loaderOptions: {
        fetchImpl: async (url) => ({
          ok: true,
          status: 200,
          async blob() {
            return { id: `blob:${url}` };
          },
        }),
        createImageBitmapImpl: async (blob) => ({
          id: `bitmap:${blob.id}`,
        }),
      },
    },
  },
);

animatedRuntime.entities.add({
  id: "runtime-hero",
  page: "heroes",
  frame: 0,
  x: 5,
  y: 5,
});
const runtimeHeroAnimation = animatedRuntime.animations.bind(
  "runtime-hero",
  "run",
);
animatedRuntime.updateAnimations(0.16);
assert.equal(animatedRuntime.entities.get("runtime-hero").frame, 1);
assert.deepEqual(animatedRuntimeEvents, [
  ["runtime-hero", "step"],
  ["runtime-hero", "impact"],
]);
assert.equal(animatedRuntime.renderEntities().instances, 1);

animatedRuntimeCanvas.dispatch("webglcontextlost", {
  preventDefault() {},
});
const animationTimeBeforeLostUpdate = runtimeHeroAnimation.timeSeconds;
animatedRuntime.updateAnimations(0.05);
assert.ok(runtimeHeroAnimation.timeSeconds > animationTimeBeforeLostUpdate);

animatedRuntimeContextIndex = 1;
animatedRuntimeCanvas.dispatch("webglcontextrestored");
await animatedRuntime.waitForRestore();
assert.equal(animatedRuntime.animations.size, 1);
assert.equal(
  animatedRuntime.animations.get("runtime-hero"),
  runtimeHeroAnimation,
);
assert.equal(animatedRuntime.entities.get("runtime-hero").page, "heroes");
animatedRuntime.updateAnimations(0.10);
assert.equal(animatedRuntime.renderEntities().instances, 1);
animatedRuntime.dispose();



const hierarchyStore = createSpriteEntityStore();
hierarchyStore.add({
  id: "root",
  page: "heroes",
  frame: "plain",
  x: 100,
  y: 50,
  z: 10,
  scaleX: 2,
  scaleY: 3,
});
hierarchyStore.add({
  id: "child",
  parent: "root",
  page: "heroes",
  frame: "plain",
  x: 5,
  y: 4,
  z: 2,
  scaleX: 0.5,
  scaleY: 2,
});
hierarchyStore.add({
  id: "grandchild",
  parent: "child",
  page: "heroes",
  frame: "plain",
  x: 8,
  y: 2,
  z: -1,
});

const hierarchyResolved = resolveSpriteEntityHierarchy(hierarchyStore);
assert.equal(hierarchyResolved.count, 3);
assert.deepEqual(
  hierarchyResolved.instances.map((instance) => [
    instance.id,
    instance.x,
    instance.y,
    instance.z,
    instance.scaleX,
    instance.scaleY,
  ]),
  [
    ["root", 100, 50, 10, 2, 3],
    ["child", 110, 62, 12, 1, 6],
    ["grandchild", 118, 74, 11, 1, 6],
  ],
);

const builtHierarchyInstances = buildSpriteEntityInstances(hierarchyStore, {
  hierarchy: true,
  sort: true,
  preserveOrder: true,
});
assert.equal(builtHierarchyInstances.instances[1].x, 110);
assert.deepEqual(builtHierarchyInstances.sceneBatchOptions, {
  sort: true,
  preserveOrder: true,
});

hierarchyStore.update("root", { enabled: false });
const hiddenHierarchy = resolveSpriteEntityHierarchy(hierarchyStore);
assert.equal(hiddenHierarchy.count, 0);
const visibleDisabledHierarchy = resolveSpriteEntityHierarchy(hierarchyStore, {
  includeDisabled: true,
});
assert.equal(visibleDisabledHierarchy.count, 3);

hierarchyStore.update("root", { enabled: true });
hierarchyStore.add({
  id: "missing-parent-child",
  parent: "missing",
  page: "heroes",
  frame: "plain",
});
assert.throws(
  () => resolveSpriteEntityHierarchy(hierarchyStore),
  /parent not found/,
);
assert.equal(
  resolveSpriteEntityHierarchy(hierarchyStore, {
    allowMissingParents: true,
  }).count,
  4,
);
hierarchyStore.remove("missing-parent-child");

hierarchyStore.add({
  id: "cycle-a",
  parent: "cycle-b",
  page: "heroes",
  frame: "plain",
});
hierarchyStore.add({
  id: "cycle-b",
  parent: "cycle-a",
  page: "heroes",
  frame: "plain",
});
assert.throws(
  () => resolveSpriteEntityHierarchy(hierarchyStore),
  /hierarchy cycle detected/,
);
hierarchyStore.remove("cycle-a");
hierarchyStore.remove("cycle-b");

const hierarchySceneGl = createMockWebGL2();
const hierarchyScene = await createWebGL2RuntimeAtlasScene(
  hierarchySceneGl,
  [{ id: "heroes", atlas: plainAtlas, texture: "heroes.png" }],
  {
    loaderOptions: {
      fetchImpl: async (url) => ({
        ok: true,
        status: 200,
        async blob() {
          return { id: `blob:${url}` };
        },
      }),
      createImageBitmapImpl: async (blob) => ({
        id: `bitmap:${blob.id}`,
      }),
    },
  },
);
const hierarchyCache = createSpriteEntityBatchCache(
  hierarchyScene,
  hierarchyStore,
);
const hierarchyCacheFirst = hierarchyCache.build({
  hierarchy: true,
  preserveOrder: true,
});
assert.equal(hierarchyCacheFirst.cacheHit, false);
const hierarchyCacheSecond = hierarchyCache.build({
  hierarchy: true,
  preserveOrder: true,
});
assert.equal(hierarchyCacheSecond.cacheHit, true);
hierarchyStore.update("root", { x: 200 });
const hierarchyCacheAfterParentMove = hierarchyCache.build({
  hierarchy: true,
  preserveOrder: true,
});
assert.equal(hierarchyCacheAfterParentMove.cacheHit, false);
assert.ok(hierarchyCache.stats.invalidations >= 1);
hierarchyScene.dispose();

const hierarchyRuntimeGl = createMockWebGL2();
hierarchyRuntimeGl.viewport = (...args) =>
  hierarchyRuntimeGl.calls.push(["viewport", ...args]);
const hierarchyRuntimeCanvas = createMockCanvas();
const hierarchyRuntime = await createWebGL2CanvasRuntime(
  hierarchyRuntimeCanvas,
  [{ id: "heroes", atlas: plainAtlas, texture: "heroes.png" }],
  {
    getContext() {
      return hierarchyRuntimeGl;
    },
    resizeOptions: { pixelRatio: 1 },
    sceneOptions: {
      loaderOptions: {
        fetchImpl: async (url) => ({
          ok: true,
          status: 200,
          async blob() {
            return { id: `blob:${url}` };
          },
        }),
        createImageBitmapImpl: async (blob) => ({
          id: `bitmap:${blob.id}`,
        }),
      },
    },
  },
);
hierarchyRuntime.entities.add({
  id: "runtime-parent",
  page: "heroes",
  frame: "plain",
  x: 10,
  y: 20,
  scale: 2,
});
hierarchyRuntime.entities.add({
  id: "runtime-child",
  parent: "runtime-parent",
  page: "heroes",
  frame: "plain",
  x: 5,
  y: 3,
});
const runtimeHierarchyBatches = hierarchyRuntime.buildEntityBatches({
  hierarchy: true,
  preserveOrder: true,
});
assert.equal(runtimeHierarchyBatches.instanceCount, 2);
assert.equal(runtimeHierarchyBatches.batches[0].batch.bounds[1].x, 20);
assert.equal(runtimeHierarchyBatches.batches[0].batch.bounds[1].y, 26);
const runtimeHierarchyRender = hierarchyRuntime.renderEntities({
  hierarchy: true,
  preserveOrder: true,
});
assert.equal(runtimeHierarchyRender.instances, 2);
hierarchyRuntime.dispose();



const quarterTurn = Math.PI / 2;
const rotatedInstanced = buildInstancedSpriteBatch(
  indexRuntimeAtlas(plainAtlas),
  [
    {
      frame: "plain",
      x: 10,
      y: 20,
      rotation: quarterTurn,
      pivotX: 3,
      pivotY: 3.5,
    },
  ],
);
assert.equal(rotatedInstanced.instances[11], quarterTurn);
assert.equal(rotatedInstanced.instances[12], 13);
assert.equal(rotatedInstanced.instances[13], 23.5);
assert.equal(rotatedInstanced.bounds[0].rotation, quarterTurn);
assert.equal(rotatedInstanced.bounds[0].pivotWorldX, 13);
assert.equal(rotatedInstanced.bounds[0].pivotWorldY, 23.5);

const rotatedClassic = buildSpriteBatch(
  indexRuntimeAtlas(plainAtlas),
  [
    {
      frame: "plain",
      x: 10,
      y: 20,
      rotation: quarterTurn,
      pivotX: 3,
      pivotY: 3.5,
    },
  ],
);
const rotatedClassicPositions = [];
for (let i = 0; i < 4; i += 1) {
  rotatedClassicPositions.push([
    rotatedClassic.vertices[i * 4],
    rotatedClassic.vertices[i * 4 + 1],
  ]);
}
assert.ok(
  Math.abs(rotatedClassicPositions[0][0] - 15.5) < 1e-6 &&
    Math.abs(rotatedClassicPositions[0][1] - 21.5) < 1e-6,
);

const rotatedBounds = spriteInstanceBounds(
  createRuntimeAtlasPages([
    { id: "plain-page", atlas: plainAtlas, texture: "plain.png" },
  ]),
  {
    page: "plain-page",
    frame: "plain",
    x: 10,
    y: 20,
    rotation: quarterTurn,
    pivotX: 3,
    pivotY: 3.5,
  },
);
assert.ok(Math.abs(rotatedBounds.width - 7) < 1e-6);
assert.ok(Math.abs(rotatedBounds.height - 6) < 1e-6);
assert.ok(Math.abs(rotatedBounds.visibleWidth - 5) < 1e-6);
assert.ok(Math.abs(rotatedBounds.visibleHeight - 4) < 1e-6);

const rotationHierarchyStore = createSpriteEntityStore();
rotationHierarchyStore.add({
  id: "rot-parent",
  page: "heroes",
  frame: "plain",
  x: 100,
  y: 100,
  rotation: quarterTurn,
  scale: 2,
});
rotationHierarchyStore.add({
  id: "rot-child",
  parent: "rot-parent",
  page: "heroes",
  frame: "plain",
  x: 10,
  y: 0,
  rotation: quarterTurn,
});
const resolvedRotationHierarchy =
  resolveSpriteEntityHierarchy(rotationHierarchyStore);
const rotatedChild = resolvedRotationHierarchy.instances.find(
  (instance) => instance.id === "rot-child",
);
assert.ok(Math.abs(rotatedChild.x - 100) < 1e-6);
assert.ok(Math.abs(rotatedChild.y - 120) < 1e-6);
assert.ok(Math.abs(rotatedChild.rotation - Math.PI) < 1e-6);
assert.equal(rotatedChild.scaleX, 2);
assert.equal(rotatedChild.scaleY, 2);

const shaderWithSpriteRotation = instancedSpriteWebGL2Shaders();
assert.equal(
  shaderWithSpriteRotation.attributes.aPivotAndReserved.location,
  4,
);
assert.match(shaderWithSpriteRotation.vertex, /cos\(spriteRotation\)/);
assert.match(shaderWithSpriteRotation.vertex, /aPivotAndReserved/);



const tintedInstanced = buildInstancedSpriteBatch(
  indexRuntimeAtlas(plainAtlas),
  [
    {
      frame: "plain",
      tintR: 0.5,
      tintG: 0.25,
      tintB: 0.75,
      alpha: 0.4,
    },
  ],
);
assert.equal(tintedInstanced.instanceStrideFloats, 20);
assert.equal(tintedInstanced.instanceStrideBytes, 80);
assert.deepEqual(Array.from(tintedInstanced.instances.slice(16, 20)), [
  0.5,
  0.25,
  0.75,
  0.4,
]);

assert.throws(
  () =>
    buildInstancedSpriteBatch(indexRuntimeAtlas(plainAtlas), [
      { frame: "plain", alpha: 1.1 },
    ]),
  /alpha must be between 0 and 1/,
);
assert.throws(
  () =>
    buildInstancedSpriteBatch(indexRuntimeAtlas(plainAtlas), [
      { frame: "plain", tintR: -0.1 },
    ]),
  /tintR must be between 0 and 1/,
);

const tintHierarchyStore = createSpriteEntityStore();
tintHierarchyStore.add({
  id: "tint-parent",
  page: "heroes",
  frame: "plain",
  alpha: 0.5,
  tintR: 0.8,
  tintG: 0.5,
  tintB: 1,
});
tintHierarchyStore.add({
  id: "tint-child",
  parent: "tint-parent",
  page: "heroes",
  frame: "plain",
  alpha: 0.5,
  tintR: 0.5,
  tintG: 1,
  tintB: 0.25,
});
const tintResolved = resolveSpriteEntityHierarchy(tintHierarchyStore);
const tintChild = tintResolved.instances.find(
  (instance) => instance.id === "tint-child",
);
assert.ok(Math.abs(tintChild.alpha - 0.25) < 1e-6);
assert.ok(Math.abs(tintChild.tintR - 0.4) < 1e-6);
assert.ok(Math.abs(tintChild.tintG - 0.5) < 1e-6);
assert.ok(Math.abs(tintChild.tintB - 0.25) < 1e-6);

assert.throws(
  () =>
    tintHierarchyStore.add({
      id: "bad-alpha",
      page: "heroes",
      frame: "plain",
      alpha: -0.01,
    }),
  /alpha must be between 0 and 1/,
);

const tintShader = instancedSpriteWebGL2Shaders();
assert.equal(tintShader.attributes.aTint.location, 5);
assert.match(tintShader.vertex, /out vec4 vTint/);
assert.match(tintShader.fragment, /texture\(uTexture, vUv\) \* vTint/);



const noBlendGl = createMockWebGL2();
const noBlendRenderer = createInstancedSpriteRendererWebGL2(noBlendGl, {
  alphaBlending: false,
});
noBlendRenderer.renderBatch(
  buildInstancedSpriteBatch(indexRuntimeAtlas(plainAtlas), [
    { frame: "plain", alpha: 0.5 },
  ]),
  { id: "no-blend-texture" },
  100,
  100,
);
assert.equal(noBlendRenderer.alphaBlending, false);
assert.equal(
  noBlendGl.calls.some((call) => call[0] === "enable" && call[1] === noBlendGl.BLEND),
  false,
);
noBlendRenderer.dispose();

assert.throws(
  () => createInstancedSpriteRendererWebGL2(createMockWebGL2(), {
    alphaBlending: "yes",
  }),
  /alphaBlending must be boolean/,
);



const layerInstances = [
  { id: "world", layerMask: 0b0001 },
  { id: "effects", layerMask: 0b0010 },
  { id: "ui", layerMask: 0b0100 },
  { id: "world-ui", layerMask: 0b0101 },
  { id: "hidden", layerMask: 0 },
  { id: "default-layer" },
];

const worldLayerFilter = filterSpriteInstancesByLayer(
  layerInstances,
  0b0001,
);
assert.deepEqual(
  worldLayerFilter.instances.map((instance) => instance.id),
  ["world", "world-ui", "default-layer"],
);
assert.equal(worldLayerFilter.filteredCount, 3);
assert.deepEqual(worldLayerFilter.filteredIndices, [1, 2, 4]);

const uiLayerFilter = filterSpriteInstancesByLayer(
  layerInstances,
  0b0100,
);
assert.deepEqual(
  uiLayerFilter.instances.map((instance) => instance.id),
  ["ui", "world-ui"],
);

const allLayerFilter = filterSpriteInstancesByLayer(layerInstances);
assert.equal(allLayerFilter.visibleCount, 5);
assert.equal(allLayerFilter.filteredCount, 1);

assert.throws(
  () => filterSpriteInstancesByLayer(layerInstances, -1),
  /visibilityMask must be an unsigned 32-bit integer/,
);
assert.throws(
  () => filterSpriteInstancesByLayer(
    [{ id: "bad", layerMask: 0x100000000 }],
  ),
  /layerMask must be an unsigned 32-bit integer/,
);

const layerStore = createSpriteEntityStore();
layerStore.add({
  id: "world",
  page: "heroes",
  frame: "plain",
  layerMask: 0b0001,
});
layerStore.add({
  id: "fx",
  page: "heroes",
  frame: "plain",
  layerMask: 0b0010,
});
layerStore.add({
  id: "ui",
  page: "heroes",
  frame: "plain",
  layerMask: 0b0100,
});
layerStore.add({
  id: "child-ui",
  parent: "world",
  page: "heroes",
  frame: "plain",
  layerMask: 0b0100,
});

const worldEntityInstances = buildSpriteEntityInstances(layerStore, {
  visibilityMask: 0b0001,
});
assert.deepEqual(
  worldEntityInstances.instances.map((instance) => instance.id),
  ["world"],
);
assert.equal(worldEntityInstances.layerFiltering.filteredCount, 3);

const uiEntityInstances = buildSpriteEntityInstances(layerStore, {
  visibilityMask: 0b0100,
});
assert.deepEqual(
  uiEntityInstances.instances.map((instance) => instance.id),
  ["ui", "child-ui"],
);

assert.throws(
  () =>
    layerStore.add({
      id: "bad-layer",
      page: "heroes",
      frame: "plain",
      layerMask: -1,
    }),
  /layerMask must be an unsigned 32-bit integer/,
);

const layerSceneGl = createMockWebGL2();
const layerScene = await createWebGL2RuntimeAtlasScene(
  layerSceneGl,
  [{ id: "heroes", atlas: plainAtlas, texture: "heroes.png" }],
  {
    loaderOptions: {
      fetchImpl: async (url) => ({
        ok: true,
        status: 200,
        async blob() {
          return { id: `blob:${url}` };
        },
      }),
      createImageBitmapImpl: async (blob) => ({
        id: `bitmap:${blob.id}`,
      }),
    },
  },
);
const layerCache = createSpriteEntityBatchCache(layerScene, layerStore);
const layerCacheWorld = layerCache.build({
  visibilityMask: 0b0001,
  preserveOrder: true,
});
const layerCacheWorldAgain = layerCache.build({
  visibilityMask: 0b0001,
  preserveOrder: true,
});
const layerCacheUi = layerCache.build({
  visibilityMask: 0b0100,
  preserveOrder: true,
});
assert.equal(layerCacheWorld.cacheHit, false);
assert.equal(layerCacheWorldAgain.cacheHit, true);
assert.equal(layerCacheUi.cacheHit, false);
assert.notEqual(layerCacheWorld.cacheKey, layerCacheUi.cacheKey);
assert.equal(layerCacheWorld.batches.instanceCount, 1);
assert.equal(layerCacheUi.batches.instanceCount, 2);
layerScene.dispose();

const layerRuntimeGl = createMockWebGL2();
layerRuntimeGl.viewport = (...args) =>
  layerRuntimeGl.calls.push(["viewport", ...args]);
const layerRuntimeCanvas = createMockCanvas();
const layerRuntime = await createWebGL2CanvasRuntime(
  layerRuntimeCanvas,
  [{ id: "heroes", atlas: plainAtlas, texture: "heroes.png" }],
  {
    visibilityMask: 0b0001,
    getContext() {
      return layerRuntimeGl;
    },
    resizeOptions: { pixelRatio: 1 },
    sceneOptions: {
      loaderOptions: {
        fetchImpl: async (url) => ({
          ok: true,
          status: 200,
          async blob() {
            return { id: `blob:${url}` };
          },
        }),
        createImageBitmapImpl: async (blob) => ({
          id: `bitmap:${blob.id}`,
        }),
      },
    },
  },
);
layerRuntime.entities.add({
  id: "runtime-world",
  page: "heroes",
  frame: "plain",
  layerMask: 0b0001,
});
layerRuntime.entities.add({
  id: "runtime-ui",
  page: "heroes",
  frame: "plain",
  layerMask: 0b0100,
});

assert.equal(layerRuntime.visibilityMask, 0b0001);
assert.equal(layerRuntime.renderEntities().instances, 1);
layerRuntime.setVisibilityMask(0b0100);
assert.equal(layerRuntime.visibilityMask, 0b0100);
assert.equal(layerRuntime.renderEntities().instances, 1);
assert.equal(
  layerRuntime.renderEntities({ visibilityMask: 0b0101 }).instances,
  2,
);
assert.throws(
  () => layerRuntime.setVisibilityMask(0x100000000),
  /visibilityMask must be an unsigned 32-bit integer/,
);
layerRuntime.dispose();



const cameraInput = [
  {
    id: "world",
    x: 120,
    y: 80,
    scaleX: 2,
    scaleY: 3,
  },
  {
    id: "background",
    x: 120,
    y: 80,
    parallaxX: 0.5,
    parallaxY: 0.25,
  },
];
const cameraApplied = applyCameraToSpriteInstances(
  cameraInput,
  { x: 100, y: 40, zoom: 2 },
);
assert.deepEqual(
  cameraApplied.instances.map((instance) => [
    instance.id,
    instance.x,
    instance.y,
    instance.scaleX,
    instance.scaleY,
    instance.parallaxX,
    instance.parallaxY,
  ]),
  [
    ["world", 40, 80, 4, 6, 1, 1],
    ["background", 140, 140, 2, 2, 0.5, 0.25],
  ],
);
assert.deepEqual(cameraApplied.camera, {
  x: 100,
  y: 40,
  zoom: 2,
});

assert.throws(
  () => applyCameraToSpriteInstances([], { zoom: 0 }),
  /camera zoom must be > 0/,
);
assert.throws(
  () =>
    applyCameraToSpriteInstances(
      [{ x: 0, y: 0, parallaxX: -1 }],
      {},
    ),
  /parallaxX must be finite and >= 0/,
);

const cameraStore = createSpriteEntityStore();
cameraStore.add({
  id: "camera-world",
  page: "heroes",
  frame: "plain",
  x: 120,
  y: 80,
  layerMask: 1,
});
cameraStore.add({
  id: "camera-bg",
  page: "heroes",
  frame: "plain",
  x: 120,
  y: 80,
  layerMask: 1,
  parallaxX: 0.5,
  parallaxY: 0.5,
});

const cameraPrepared = buildSpriteEntityInstances(cameraStore, {
  camera: { x: 100, y: 40, zoom: 2 },
});
assert.deepEqual(
  cameraPrepared.instances.map((instance) => [
    instance.id,
    instance.x,
    instance.y,
  ]),
  [
    ["camera-world", 40, 80],
    ["camera-bg", 140, 120],
  ],
);
assert.deepEqual(cameraPrepared.cameraTransform.camera, {
  x: 100,
  y: 40,
  zoom: 2,
});

assert.throws(
  () =>
    cameraStore.add({
      id: "bad-parallax",
      page: "heroes",
      frame: "plain",
      parallaxX: -0.1,
    }),
  /parallaxX must be >= 0/,
);

const cameraSceneGl = createMockWebGL2();
const cameraScene = await createWebGL2RuntimeAtlasScene(
  cameraSceneGl,
  [{ id: "heroes", atlas: plainAtlas, texture: "heroes.png" }],
  {
    loaderOptions: {
      fetchImpl: async (url) => ({
        ok: true,
        status: 200,
        async blob() {
          return { id: `blob:${url}` };
        },
      }),
      createImageBitmapImpl: async (blob) => ({
        id: `bitmap:${blob.id}`,
      }),
    },
  },
);
const cameraCache = createSpriteEntityBatchCache(cameraScene, cameraStore);
const cameraCacheA = cameraCache.build({
  camera: { x: 0, y: 0, zoom: 1 },
  preserveOrder: true,
});
const cameraCacheAAgain = cameraCache.build({
  camera: { x: 0, y: 0, zoom: 1 },
  preserveOrder: true,
});
const cameraCacheB = cameraCache.build({
  camera: { x: 50, y: 0, zoom: 1 },
  preserveOrder: true,
});
assert.equal(cameraCacheA.cacheHit, false);
assert.equal(cameraCacheAAgain.cacheHit, true);
assert.equal(cameraCacheB.cacheHit, false);
assert.notEqual(cameraCacheA.cacheKey, cameraCacheB.cacheKey);
cameraScene.dispose();

const cameraRuntimeGl = createMockWebGL2();
cameraRuntimeGl.viewport = (...args) =>
  cameraRuntimeGl.calls.push(["viewport", ...args]);
const cameraRuntimeCanvas = createMockCanvas();
const cameraRuntime = await createWebGL2CanvasRuntime(
  cameraRuntimeCanvas,
  [{ id: "heroes", atlas: plainAtlas, texture: "heroes.png" }],
  {
    camera: { x: 100, y: 40, zoom: 2 },
    getContext() {
      return cameraRuntimeGl;
    },
    resizeOptions: { pixelRatio: 1 },
    sceneOptions: {
      loaderOptions: {
        fetchImpl: async (url) => ({
          ok: true,
          status: 200,
          async blob() {
            return { id: `blob:${url}` };
          },
        }),
        createImageBitmapImpl: async (blob) => ({
          id: `bitmap:${blob.id}`,
        }),
      },
    },
  },
);
cameraRuntime.entities.add({
  id: "runtime-camera-world",
  page: "heroes",
  frame: "plain",
  x: 120,
  y: 80,
});

assert.deepEqual(cameraRuntime.camera, {
  x: 100,
  y: 40,
  zoom: 2,
});
const cameraRuntimeBatches = cameraRuntime.buildEntityBatches({
  preserveOrder: true,
});
assert.equal(cameraRuntimeBatches.batches[0].batch.bounds[0].x, 40);
assert.equal(cameraRuntimeBatches.batches[0].batch.bounds[0].y, 80);

cameraRuntime.setCamera({ x: 110, zoom: 1 });
assert.deepEqual(cameraRuntime.camera, {
  x: 110,
  y: 40,
  zoom: 1,
});
const movedCameraBatches = cameraRuntime.buildEntityBatches({
  preserveOrder: true,
});
assert.equal(movedCameraBatches.batches[0].batch.bounds[0].x, 10);
assert.equal(movedCameraBatches.batches[0].batch.bounds[0].y, 40);

const cameraOverrideBatches = cameraRuntime.buildEntityBatches({
  camera: { x: 0, y: 0, zoom: 1 },
  preserveOrder: true,
});
assert.equal(cameraOverrideBatches.batches[0].batch.bounds[0].x, 120);
assert.equal(cameraOverrideBatches.batches[0].batch.bounds[0].y, 80);

assert.throws(
  () => cameraRuntime.setCamera({ zoom: -1 }),
  /camera zoom must be > 0/,
);
cameraRuntime.dispose();



const followController = createCamera2DController(
  { x: 0, y: 0, zoom: 2 },
  {
    deadZoneWidth: 20,
    deadZoneHeight: 10,
    smoothing: 0,
  },
);
assert.deepEqual(
  followController.update(5, 2, 0.016),
  { x: 0, y: 0, zoom: 2 },
);
assert.deepEqual(
  followController.update(30, 20, 0.016),
  { x: 20, y: 15, zoom: 2 },
);

const smoothController = createCamera2DController(
  { x: 0, y: 0, zoom: 1 },
  { smoothing: 4 },
);
const smoothedCamera = smoothController.update(100, 0, 0.25);
assert.ok(smoothedCamera.x > 0 && smoothedCamera.x < 100);
assert.equal(smoothedCamera.y, 0);
assert.equal(smoothedCamera.zoom, 1);

const shakeControllerA = createCamera2DController(
  { x: 10, y: 20, zoom: 1 },
);
const shakeStartA = shakeControllerA.shake(8, 1, 10);
assert.equal(shakeControllerA.shaking, true);
const shakeStepA = shakeControllerA.update(10, 20, 0.25);
assert.notDeepEqual(shakeStepA, { x: 10, y: 20, zoom: 1 });
shakeControllerA.update(10, 20, 0.75);
assert.equal(shakeControllerA.shaking, false);
assert.deepEqual(shakeControllerA.camera, {
  x: 10,
  y: 20,
  zoom: 1,
});

const shakeControllerB = createCamera2DController(
  { x: 10, y: 20, zoom: 1 },
);
const shakeStartB = shakeControllerB.shake(8, 1, 10);
assert.deepEqual(shakeStartA, shakeStartB);
assert.deepEqual(
  shakeControllerB.update(10, 20, 0.25),
  shakeStepA,
);
assert.deepEqual(shakeControllerB.clearShake(), {
  x: 10,
  y: 20,
  zoom: 1,
});
assert.equal(shakeControllerB.shaking, false);

assert.throws(
  () => createCamera2DController({}, { deadZoneWidth: -1 }),
  /deadZoneWidth must be a finite value >= 0/,
);
assert.throws(
  () => shakeControllerB.update(0, 0, -0.1),
  /deltaSeconds must be >= 0/,
);
assert.throws(
  () => shakeControllerB.shake(5, 1, 0),
  /frequency must be > 0 when shake is active/,
);

const followRuntimeGl = createMockWebGL2();
followRuntimeGl.viewport = (...args) =>
  followRuntimeGl.calls.push(["viewport", ...args]);
const followRuntimeCanvas = createMockCanvas();
const followRuntime = await createWebGL2CanvasRuntime(
  followRuntimeCanvas,
  [{ id: "heroes", atlas: plainAtlas, texture: "heroes.png" }],
  {
    camera: { x: 0, y: 0, zoom: 1 },
    cameraControllerOptions: {
      deadZoneWidth: 20,
      deadZoneHeight: 20,
      smoothing: 0,
    },
    getContext() {
      return followRuntimeGl;
    },
    resizeOptions: { pixelRatio: 1 },
    sceneOptions: {
      loaderOptions: {
        fetchImpl: async (url) => ({
          ok: true,
          status: 200,
          async blob() {
            return { id: `blob:${url}` };
          },
        }),
        createImageBitmapImpl: async (blob) => ({
          id: `bitmap:${blob.id}`,
        }),
      },
    },
  },
);
followRuntime.entities.add({
  id: "follow-target",
  page: "heroes",
  frame: "plain",
  x: 100,
  y: 50,
});
assert.deepEqual(
  followRuntime.updateCameraFollow(100, 50, 0.016),
  { x: 90, y: 40, zoom: 1 },
);
const followedBatches = followRuntime.buildEntityBatches({
  preserveOrder: true,
});
assert.equal(followedBatches.batches[0].batch.bounds[0].x, 10);
assert.equal(followedBatches.batches[0].batch.bounds[0].y, 10);

const runtimeShake = followRuntime.shakeCamera(4, 0.5, 12);
assert.notDeepEqual(runtimeShake, {
  x: 90,
  y: 40,
  zoom: 1,
});
assert.equal(followRuntime.cameraController.shaking, true);
followRuntime.clearCameraShake();
assert.equal(followRuntime.cameraController.shaking, false);
assert.deepEqual(followRuntime.camera, {
  x: 90,
  y: 40,
  zoom: 1,
});
followRuntime.dispose();



assert.deepEqual(
  clampCameraToWorldBounds(
    { x: -50, y: -20, zoom: 1 },
    { x: 0, y: 0, width: 1000, height: 500 },
    320,
    180,
  ),
  { x: 0, y: 0, zoom: 1 },
);

assert.deepEqual(
  clampCameraToWorldBounds(
    { x: 900, y: 450, zoom: 1 },
    { x: 0, y: 0, width: 1000, height: 500 },
    320,
    180,
  ),
  { x: 680, y: 320, zoom: 1 },
);

assert.deepEqual(
  clampCameraToWorldBounds(
    { x: 900, y: 450, zoom: 2 },
    { x: 0, y: 0, width: 1000, height: 500 },
    320,
    180,
  ),
  { x: 840, y: 410, zoom: 2 },
);

assert.deepEqual(
  clampCameraToWorldBounds(
    { x: 0, y: 0, zoom: 1 },
    { x: 100, y: 200, width: 100, height: 80 },
    320,
    180,
  ),
  { x: -10, y: 150, zoom: 1 },
);

assert.throws(
  () =>
    clampCameraToWorldBounds(
      { x: 0, y: 0, zoom: 1 },
      { x: 0, y: 0, width: -1, height: 100 },
      320,
      180,
    ),
  /world bounds width\/height must be >= 0/,
);

const boundedRuntimeGl = createMockWebGL2();
boundedRuntimeGl.viewport = (...args) =>
  boundedRuntimeGl.calls.push(["viewport", ...args]);
const boundedRuntimeCanvas = createMockCanvas();
boundedRuntimeCanvas.clientWidth = 320;
boundedRuntimeCanvas.clientHeight = 180;

const boundedRuntime = await createWebGL2CanvasRuntime(
  boundedRuntimeCanvas,
  [{ id: "heroes", atlas: plainAtlas, texture: "heroes.png" }],
  {
    camera: { x: 900, y: 450, zoom: 1 },
    worldBounds: { x: 0, y: 0, width: 1000, height: 500 },
    cameraControllerOptions: {
      deadZoneWidth: 0,
      deadZoneHeight: 0,
      smoothing: 0,
    },
    getContext() {
      return boundedRuntimeGl;
    },
    resizeOptions: { pixelRatio: 1 },
    sceneOptions: {
      loaderOptions: {
        fetchImpl: async (url) => ({
          ok: true,
          status: 200,
          async blob() {
            return { id: `blob:${url}` };
          },
        }),
        createImageBitmapImpl: async (blob) => ({
          id: `bitmap:${blob.id}`,
        }),
      },
    },
  },
);

boundedRuntime.setCamera({ x: 900, y: 450 });
assert.deepEqual(boundedRuntime.camera, {
  x: 680,
  y: 320,
  zoom: 1,
});

boundedRuntime.entities.add({
  id: "follow-parent",
  page: "heroes",
  frame: "plain",
  x: 100,
  y: 50,
});
boundedRuntime.entities.add({
  id: "follow-child",
  parent: "follow-parent",
  page: "heroes",
  frame: "plain",
  x: 30,
  y: 20,
});

const entityFollowCamera = boundedRuntime.updateCameraFollowEntity(
  "follow-child",
  0.016,
  { offsetX: 10, offsetY: 5 },
);
assert.deepEqual(entityFollowCamera, {
  x: 140,
  y: 75,
  zoom: 1,
});

boundedRuntime.setCamera({ x: 680, y: 320 });
const boundedShake = boundedRuntime.shakeCamera(50, 1, 12);
assert.ok(boundedShake.x <= 680);
assert.ok(boundedShake.y <= 320);
assert.ok(boundedShake.x >= 0);
assert.ok(boundedShake.y >= 0);

boundedRuntime.setWorldBounds({
  x: 100,
  y: 100,
  width: 500,
  height: 300,
});
assert.deepEqual(boundedRuntime.worldBounds, {
  x: 100,
  y: 100,
  width: 500,
  height: 300,
});
assert.ok(boundedRuntime.camera.x >= 100);
assert.ok(boundedRuntime.camera.y >= 100);

assert.equal(boundedRuntime.setWorldBounds(null), null);
assert.equal(boundedRuntime.worldBounds, null);
boundedRuntime.setCamera({ x: -500, y: -500 });
assert.deepEqual(boundedRuntime.camera, {
  x: -500,
  y: -500,
  zoom: 1,
});

assert.throws(
  () =>
    boundedRuntime.updateCameraFollowEntity(
      "missing-follow-target",
      0.016,
    ),
  /sprite entity not found/,
);

boundedRuntime.dispose();



assert.deepEqual(
  worldToScreenPoint(
    120,
    80,
    { x: 100, y: 40, zoom: 2 },
  ),
  { x: 40, y: 80 },
);
assert.deepEqual(
  screenToWorldPoint(
    40,
    80,
    { x: 100, y: 40, zoom: 2 },
  ),
  { x: 120, y: 80 },
);
assert.deepEqual(
  worldToScreenPoint(
    120,
    80,
    { x: 100, y: 40, zoom: 2 },
    { parallaxX: 0.5, parallaxY: 0.25 },
  ),
  { x: 140, y: 140 },
);

const pickingPages = createRuntimeAtlasPages([
  { id: "heroes", atlas: plainAtlas, texture: "heroes.png" },
]);
const plainHit = pointHitsSpriteInstance(
  pickingPages,
  {
    page: "heroes",
    frame: "plain",
    x: 10,
    y: 20,
  },
  12,
  22,
);
assert.equal(plainHit.hit, true);
assert.equal(
  pointHitsSpriteInstance(
    pickingPages,
    {
      page: "heroes",
      frame: "plain",
      x: 10,
      y: 20,
    },
    100,
    100,
  ).hit,
  false,
);

const visibleOnlyMiss = pointHitsSpriteInstance(
  pickingPages,
  {
    page: "heroes",
    frame: "plain",
    x: 10,
    y: 20,
  },
  10.5,
  20.5,
  { useVisibleBounds: true },
);
assert.equal(visibleOnlyMiss.hit, false);

const rotatedPickInstance = {
  page: "heroes",
  frame: "plain",
  x: 10,
  y: 20,
  rotation: Math.PI / 2,
  pivotX: 3,
  pivotY: 3.5,
};
assert.equal(
  pointHitsSpriteInstance(
    pickingPages,
    rotatedPickInstance,
    13,
    23.5,
  ).hit,
  true,
);

const overlappingPick = pickSpriteInstances(
  pickingPages,
  [
    {
      id: "back",
      page: "heroes",
      frame: "plain",
      x: 10,
      y: 20,
      z: 1,
    },
    {
      id: "front",
      page: "heroes",
      frame: "plain",
      x: 10,
      y: 20,
      z: 5,
    },
    {
      id: "front-later",
      page: "heroes",
      frame: "plain",
      x: 10,
      y: 20,
      z: 5,
    },
  ],
  12,
  22,
);
assert.equal(overlappingPick.instance.id, "front-later");

const allOverlappingPicks = pickSpriteInstances(
  pickingPages,
  [
    {
      id: "back",
      page: "heroes",
      frame: "plain",
      x: 10,
      y: 20,
      z: 1,
    },
    {
      id: "front",
      page: "heroes",
      frame: "plain",
      x: 10,
      y: 20,
      z: 5,
    },
  ],
  12,
  22,
  { all: true },
);
assert.deepEqual(
  allOverlappingPicks.map((entry) => entry.instance.id),
  ["front", "back"],
);

const pickingRuntimeGl = createMockWebGL2();
pickingRuntimeGl.viewport = (...args) =>
  pickingRuntimeGl.calls.push(["viewport", ...args]);
const pickingRuntimeCanvas = createMockCanvas();
const pickingRuntime = await createWebGL2CanvasRuntime(
  pickingRuntimeCanvas,
  [{ id: "heroes", atlas: plainAtlas, texture: "heroes.png" }],
  {
    camera: { x: 100, y: 40, zoom: 2 },
    getContext() {
      return pickingRuntimeGl;
    },
    resizeOptions: { pixelRatio: 1 },
    sceneOptions: {
      loaderOptions: {
        fetchImpl: async (url) => ({
          ok: true,
          status: 200,
          async blob() {
            return { id: `blob:${url}` };
          },
        }),
        createImageBitmapImpl: async (blob) => ({
          id: `bitmap:${blob.id}`,
        }),
      },
    },
  },
);
pickingRuntime.entities.add({
  id: "pick-back",
  page: "heroes",
  frame: "plain",
  x: 120,
  y: 80,
  z: 1,
});
pickingRuntime.entities.add({
  id: "pick-front",
  page: "heroes",
  frame: "plain",
  x: 120,
  y: 80,
  z: 10,
});

assert.deepEqual(
  pickingRuntime.worldToScreen(120, 80),
  { x: 40, y: 80 },
);
assert.deepEqual(
  pickingRuntime.screenToWorld(40, 80),
  { x: 120, y: 80 },
);
assert.equal(
  pickingRuntime.pickEntity(42, 82).instance.id,
  "pick-front",
);
assert.deepEqual(
  pickingRuntime
    .pickEntity(42, 82, { all: true })
    .map((entry) => entry.instance.id),
  ["pick-front", "pick-back"],
);
assert.equal(
  pickingRuntime.pickEntity(500, 500),
  null,
);
pickingRuntime.dispose();



const pointerEvents = [];
const pointerController = createSpritePointerInteractionController({
  dragThreshold: 5,
  pick(x, y) {
    if (x >= 0 && x <= 20 && y >= 0 && y <= 20) {
      return {
        instance: { id: "button", z: 1 },
      };
    }
    return null;
  },
  toWorld(x, y) {
    return { x: x + 100, y: y + 200 };
  },
  onEnter(event) {
    pointerEvents.push(["enter", event.entity?.id ?? event.entityId]);
  },
  onLeave(event) {
    pointerEvents.push(["leave", event.entityId]);
  },
  onDown(event) {
    pointerEvents.push(["down", event.entity?.id ?? null]);
  },
  onClick(event) {
    pointerEvents.push(["click", event.entity?.id ?? null]);
  },
  onDragStart(event) {
    pointerEvents.push(["dragstart", event.capturedEntityId]);
  },
  onDrag(event) {
    pointerEvents.push(["drag", event.totalDx, event.totalDy]);
  },
  onDragEnd(event) {
    pointerEvents.push(["dragend", event.cancelled ?? false]);
  },
  onUp(event) {
    pointerEvents.push(["up", event.entity?.id ?? null]);
  },
});

const mouseMoveEvent = pointerController.move("mouse", 10, 10);
assert.equal(mouseMoveEvent.entity.id, "button");
assert.equal(mouseMoveEvent.worldX, 110);
assert.equal(mouseMoveEvent.worldY, 210);
assert.equal(pointerController.hoverEntityId, "button");

pointerController.down("mouse", 10, 10);
pointerController.up("mouse", 12, 12);
assert.ok(pointerEvents.some((entry) => entry[0] === "click"));

pointerController.down("mouse", 10, 10);
pointerController.move("mouse", 20, 20);
assert.equal(pointerController.pointerState("mouse").dragging, true);
pointerController.up("mouse", 25, 25);
assert.equal(pointerController.pointerState("mouse"), null);
assert.ok(pointerEvents.some((entry) => entry[0] === "dragstart"));
assert.ok(pointerEvents.some((entry) => entry[0] === "drag"));
assert.ok(pointerEvents.some((entry) => entry[0] === "dragend"));

pointerController.move("mouse", 50, 50);
assert.equal(pointerController.hoverEntityId, null);
assert.ok(pointerEvents.some((entry) => entry[0] === "leave"));

pointerController.down(1, 10, 10);
pointerController.down(2, 10, 10);
assert.equal(pointerController.activePointerCount, 2);
const cancelledPointer = pointerController.cancel(1);
assert.equal(cancelledPointer.type, "cancel");
assert.equal(pointerController.activePointerCount, 1);
pointerController.clear();
assert.equal(pointerController.activePointerCount, 0);

assert.throws(
  () =>
    createSpritePointerInteractionController({
      pick() {
        return null;
      },
      dragThreshold: -1,
    }),
  /dragThreshold must be a finite value >= 0/,
);

const pointerRuntimeGl = createMockWebGL2();
pointerRuntimeGl.viewport = (...args) =>
  pointerRuntimeGl.calls.push(["viewport", ...args]);
const pointerRuntimeCanvas = createMockCanvas();
const runtimePointerEvents = [];

const pointerRuntime = await createWebGL2CanvasRuntime(
  pointerRuntimeCanvas,
  [{ id: "heroes", atlas: plainAtlas, texture: "heroes.png" }],
  {
    camera: { x: 100, y: 40, zoom: 2 },
    pointerOptions: {
      dragThreshold: 4,
      onDown(event) {
        runtimePointerEvents.push(["down", event.entity?.id ?? null]);
      },
      onClick(event) {
        runtimePointerEvents.push(["click", event.entity?.id ?? null]);
      },
      onDragStart(event) {
        runtimePointerEvents.push(["dragstart", event.capturedEntityId]);
      },
      onDrag(event) {
        runtimePointerEvents.push([
          "drag",
          event.worldX,
          event.worldY,
        ]);
      },
    },
    getContext() {
      return pointerRuntimeGl;
    },
    resizeOptions: { pixelRatio: 1 },
    sceneOptions: {
      loaderOptions: {
        fetchImpl: async (url) => ({
          ok: true,
          status: 200,
          async blob() {
            return { id: `blob:${url}` };
          },
        }),
        createImageBitmapImpl: async (blob) => ({
          id: `bitmap:${blob.id}`,
        }),
      },
    },
  },
);

pointerRuntime.entities.add({
  id: "runtime-button",
  page: "heroes",
  frame: "plain",
  x: 120,
  y: 80,
  z: 10,
});

const runtimePointerDown = pointerRuntime.pointerDown("mouse", 42, 82);
assert.equal(runtimePointerDown.entity.id, "runtime-button");
assert.equal(runtimePointerDown.worldX, 121);
assert.equal(runtimePointerDown.worldY, 81);

pointerRuntime.pointerUp("mouse", 43, 83);
assert.deepEqual(runtimePointerEvents.slice(0, 2), [
  ["down", "runtime-button"],
  ["click", "runtime-button"],
]);

pointerRuntime.pointerDown("touch-1", 42, 82);
pointerRuntime.pointerMove("touch-1", 52, 92);
assert.equal(
  pointerRuntime.pointerInteractions.pointerState("touch-1").dragging,
  true,
);
assert.ok(
  runtimePointerEvents.some((entry) => entry[0] === "dragstart"),
);
assert.ok(
  runtimePointerEvents.some(
    (entry) =>
      entry[0] === "drag" &&
      Math.abs(entry[1] - 126) < 1e-6 &&
      Math.abs(entry[2] - 86) < 1e-6,
  ),
);
pointerRuntime.pointerUp("touch-1", 52, 92);
assert.equal(pointerRuntime.pointerInteractions.activePointerCount, 0);

pointerRuntime.pointerDown("touch-2", 42, 82);
pointerRuntime.dispose();
assert.equal(pointerRuntime.pointerInteractions.activePointerCount, 0);



const dragStore = createSpriteEntityStore();
dragStore.add({
  id: "drag-root",
  page: "heroes",
  frame: "plain",
  x: 10,
  y: 20,
});
const dragVersionBefore = dragStore.version;
moveSpriteEntityByWorldDelta(
  dragStore,
  "drag-root",
  5,
  -3,
);
assert.deepEqual(
  {
    x: dragStore.get("drag-root").x,
    y: dragStore.get("drag-root").y,
  },
  { x: 15, y: 17 },
);
assert.ok(dragStore.version > dragVersionBefore);

moveSpriteEntityByWorldDelta(
  dragStore,
  "drag-root",
  10,
  10,
  { axis: "x" },
);
assert.deepEqual(
  {
    x: dragStore.get("drag-root").x,
    y: dragStore.get("drag-root").y,
  },
  { x: 25, y: 17 },
);

dragStore.add({
  id: "drag-parent",
  page: "heroes",
  frame: "plain",
  x: 100,
  y: 100,
  rotation: Math.PI / 2,
  scaleX: 2,
  scaleY: 4,
});
dragStore.add({
  id: "drag-child",
  parent: "drag-parent",
  page: "heroes",
  frame: "plain",
  x: 10,
  y: 5,
});

const childWorldBefore =
  resolveSpriteEntityHierarchy(dragStore).byId.get("drag-child");
moveSpriteEntityByWorldDelta(
  dragStore,
  "drag-child",
  8,
  4,
);
const childWorldAfter =
  resolveSpriteEntityHierarchy(dragStore).byId.get("drag-child");
assert.ok(
  Math.abs(childWorldAfter.x - (childWorldBefore.x + 8)) < 1e-6,
);
assert.ok(
  Math.abs(childWorldAfter.y - (childWorldBefore.y + 4)) < 1e-6,
);

assert.throws(
  () =>
    moveSpriteEntityByWorldDelta(
      dragStore,
      "drag-root",
      1,
      1,
      { axis: "diagonal" },
    ),
  /drag axis must be both, x, or y/,
);

const autoDragGl = createMockWebGL2();
autoDragGl.viewport = (...args) =>
  autoDragGl.calls.push(["viewport", ...args]);
const autoDragCanvas = createMockCanvas();
const autoDragEvents = [];

const autoDragRuntime = await createWebGL2CanvasRuntime(
  autoDragCanvas,
  [{ id: "heroes", atlas: plainAtlas, texture: "heroes.png" }],
  {
    camera: { x: 100, y: 40, zoom: 2 },
    pointerOptions: {
      dragThreshold: 2,
      autoDragEntities: true,
      dragAxis: "both",
      onDrag(event) {
        autoDragEvents.push({
          id: event.capturedEntityId,
          x: event.draggedEntity?.x,
          y: event.draggedEntity?.y,
        });
      },
    },
    getContext() {
      return autoDragGl;
    },
    resizeOptions: { pixelRatio: 1 },
    sceneOptions: {
      loaderOptions: {
        fetchImpl: async (url) => ({
          ok: true,
          status: 200,
          async blob() {
            return { id: `blob:${url}` };
          },
        }),
        createImageBitmapImpl: async (blob) => ({
          id: `bitmap:${blob.id}`,
        }),
      },
    },
  },
);

autoDragRuntime.entities.add({
  id: "draggable",
  page: "heroes",
  frame: "plain",
  x: 120,
  y: 80,
  z: 10,
});

const draggableVersionBefore = autoDragRuntime.entities.version;
autoDragRuntime.pointerDown("touch-drag", 42, 82);
autoDragRuntime.pointerMove("touch-drag", 52, 92);

const draggedEntity = autoDragRuntime.entities.get("draggable");
assert.equal(draggedEntity.x, 125);
assert.equal(draggedEntity.y, 85);
assert.ok(autoDragRuntime.entities.version > draggableVersionBefore);
assert.deepEqual(autoDragEvents[0], {
  id: "draggable",
  x: 125,
  y: 85,
});

autoDragRuntime.pointerUp("touch-drag", 52, 92);

autoDragRuntime.moveEntityByWorldDelta(
  "draggable",
  7,
  9,
  { axis: "y" },
);
assert.deepEqual(
  {
    x: autoDragRuntime.entities.get("draggable").x,
    y: autoDragRuntime.entities.get("draggable").y,
  },
  { x: 125, y: 94 },
);

autoDragRuntime.dispose();

assert.throws(
  async () =>
    createWebGL2CanvasRuntime(
      createMockCanvas(),
      [{ id: "heroes", atlas: plainAtlas, texture: "heroes.png" }],
      {
        pointerOptions: {
          autoDragEntities: "yes",
        },
        getContext() {
          return createMockWebGL2();
        },
        resizeOptions: { pixelRatio: 1 },
        sceneOptions: {
          loaderOptions: {
            fetchImpl: async () => ({
              ok: true,
              status: 200,
              async blob() {
                return {};
              },
            }),
            createImageBitmapImpl: async () => ({}),
          },
        },
      },
    ),
  /autoDragEntities must be boolean/,
);



const snapStore = createSpriteEntityStore();
snapStore.add({
  id: "snap-root",
  page: "heroes",
  frame: "plain",
  x: 13,
  y: 17,
});
moveSpriteEntityByWorldDelta(
  snapStore,
  "snap-root",
  6,
  7,
  { gridSize: 10 },
);
assert.deepEqual(
  {
    x: snapStore.get("snap-root").x,
    y: snapStore.get("snap-root").y,
  },
  { x: 20, y: 20 },
);

moveSpriteEntityByWorldDelta(
  snapStore,
  "snap-root",
  1000,
  -1000,
  {
    bounds: {
      x: 0,
      y: 0,
      width: 100,
      height: 80,
    },
  },
);
assert.deepEqual(
  {
    x: snapStore.get("snap-root").x,
    y: snapStore.get("snap-root").y,
  },
  { x: 100, y: 0 },
);

snapStore.add({
  id: "snap-parent",
  page: "heroes",
  frame: "plain",
  x: 100,
  y: 100,
  rotation: Math.PI / 2,
  scaleX: 2,
  scaleY: 2,
});
snapStore.add({
  id: "snap-child",
  parent: "snap-parent",
  page: "heroes",
  frame: "plain",
  x: 5,
  y: 0,
});
moveSpriteEntityByWorldDelta(
  snapStore,
  "snap-child",
  13,
  7,
  { gridSize: 10 },
);
const snappedChildWorld =
  resolveSpriteEntityHierarchy(snapStore).byId.get("snap-child");
assert.ok(Math.abs(snappedChildWorld.x - 110) < 1e-6);
assert.ok(Math.abs(snappedChildWorld.y - 110) < 1e-6);

assert.throws(
  () =>
    moveSpriteEntityByWorldDelta(
      snapStore,
      "snap-root",
      1,
      1,
      { gridSize: -1 },
    ),
  /gridSize must be a finite value >= 0/,
);
assert.throws(
  () =>
    moveSpriteEntityByWorldDelta(
      snapStore,
      "snap-root",
      1,
      1,
      {
        bounds: {
          x: 0,
          y: 0,
          width: -1,
          height: 10,
        },
      },
    ),
  /drag bounds width\/height must be >= 0/,
);

const constrainedDragGl = createMockWebGL2();
constrainedDragGl.viewport = (...args) =>
  constrainedDragGl.calls.push(["viewport", ...args]);
const constrainedDragCanvas = createMockCanvas();

const constrainedDragRuntime = await createWebGL2CanvasRuntime(
  constrainedDragCanvas,
  [{ id: "heroes", atlas: plainAtlas, texture: "heroes.png" }],
  {
    camera: { x: 0, y: 0, zoom: 2 },
    worldBounds: { x: 0, y: 0, width: 100, height: 100 },
    pointerOptions: {
      dragThreshold: 1,
      autoDragEntities: true,
      dragGridSize: 10,
    },
    getContext() {
      return constrainedDragGl;
    },
    resizeOptions: { pixelRatio: 1 },
    sceneOptions: {
      loaderOptions: {
        fetchImpl: async (url) => ({
          ok: true,
          status: 200,
          async blob() {
            return { id: `blob:${url}` };
          },
        }),
        createImageBitmapImpl: async (blob) => ({
          id: `bitmap:${blob.id}`,
        }),
      },
    },
  },
);

constrainedDragRuntime.entities.add({
  id: "snap-drag",
  page: "heroes",
  frame: "plain",
  x: 20,
  y: 20,
  z: 10,
});

constrainedDragRuntime.pointerDown("snap-touch", 42, 42);
constrainedDragRuntime.pointerMove("snap-touch", 59, 59);
assert.deepEqual(
  {
    x: constrainedDragRuntime.entities.get("snap-drag").x,
    y: constrainedDragRuntime.entities.get("snap-drag").y,
  },
  { x: 30, y: 30 },
);

constrainedDragRuntime.pointerMove("snap-touch", 999, 999);
assert.deepEqual(
  {
    x: constrainedDragRuntime.entities.get("snap-drag").x,
    y: constrainedDragRuntime.entities.get("snap-drag").y,
  },
  { x: 100, y: 100 },
);
constrainedDragRuntime.pointerUp("snap-touch", 999, 999);
constrainedDragRuntime.dispose();



const selectionChanges = [];
const selectionModel = createSpriteSelectionModel({
  onChange(event) {
    selectionChanges.push(event);
  },
});
selectionModel.select("a");
assert.deepEqual(selectionModel.snapshot(), {
  ids: ["a"],
  primaryId: "a",
  count: 1,
});
selectionModel.select("b", { additive: true });
assert.deepEqual(selectionModel.snapshot(), {
  ids: ["a", "b"],
  primaryId: "b",
  count: 2,
});
selectionModel.select("b", { toggle: true });
assert.deepEqual(selectionModel.snapshot(), {
  ids: ["a"],
  primaryId: "a",
  count: 1,
});
selectionModel.set(["a", "c"]);
assert.equal(selectionModel.primaryId, "c");
selectionModel.remove("c");
assert.equal(selectionModel.primaryId, "a");
selectionModel.clear();
assert.equal(selectionModel.size, 0);
assert.ok(selectionChanges.length >= 5);

const selectionPages = createRuntimeAtlasPages([
  { id: "heroes", atlas: plainAtlas, texture: "heroes.png" },
]);
const marqueeInstances = [
  {
    id: "one",
    page: "heroes",
    frame: "plain",
    x: 10,
    y: 10,
    z: 1,
  },
  {
    id: "two",
    page: "heroes",
    frame: "plain",
    x: 30,
    y: 30,
    z: 5,
  },
  {
    id: "three",
    page: "heroes",
    frame: "plain",
    x: 100,
    y: 100,
    z: 2,
  },
];
const marqueeIntersect = selectSpriteInstancesInRect(
  selectionPages,
  marqueeInstances,
  { x1: 40, y1: 40, x2: 0, y2: 0 },
  { mode: "intersect" },
);
assert.deepEqual(
  marqueeIntersect.map((hit) => hit.instance.id),
  ["two", "one"],
);
const marqueeContain = selectSpriteInstancesInRect(
  selectionPages,
  marqueeInstances,
  { x: 0, y: 0, width: 20, height: 20 },
  { mode: "contain" },
);
assert.deepEqual(
  marqueeContain.map((hit) => hit.instance.id),
  ["one"],
);

const selectionRuntimeGl = createMockWebGL2();
selectionRuntimeGl.viewport = (...args) =>
  selectionRuntimeGl.calls.push(["viewport", ...args]);
const selectionRuntimeCanvas = createMockCanvas();
const selectionRuntime = await createWebGL2CanvasRuntime(
  selectionRuntimeCanvas,
  [{ id: "heroes", atlas: plainAtlas, texture: "heroes.png" }],
  {
    camera: { x: 100, y: 40, zoom: 2 },
    getContext() {
      return selectionRuntimeGl;
    },
    resizeOptions: { pixelRatio: 1 },
    sceneOptions: {
      loaderOptions: {
        fetchImpl: async (url) => ({
          ok: true,
          status: 200,
          async blob() {
            return { id: `blob:${url}` };
          },
        }),
        createImageBitmapImpl: async (blob) => ({
          id: `bitmap:${blob.id}`,
        }),
      },
    },
  },
);
selectionRuntime.entities.add({
  id: "sel-a",
  page: "heroes",
  frame: "plain",
  x: 120,
  y: 80,
  z: 1,
});
selectionRuntime.entities.add({
  id: "sel-b",
  page: "heroes",
  frame: "plain",
  x: 140,
  y: 80,
  z: 2,
});

selectionRuntime.selectEntity("sel-a");
selectionRuntime.selectEntity("sel-b", { additive: true });
assert.deepEqual(selectionRuntime.selection.snapshot(), {
  ids: ["sel-a", "sel-b"],
  primaryId: "sel-b",
  count: 2,
});
selectionRuntime.clearSelection();
assert.equal(selectionRuntime.selection.size, 0);

const rectSelection = selectionRuntime.selectEntitiesInRect({
  x: 35,
  y: 75,
  width: 50,
  height: 20,
});
assert.deepEqual(rectSelection.ids, ["sel-b", "sel-a"]);
assert.equal(rectSelection.primaryId, "sel-a");

selectionRuntime.clearSelection();
selectionRuntime.selectEntity("sel-a");
const additiveRectSelection =
  selectionRuntime.selectEntitiesInRect(
    {
      x: 75,
      y: 75,
      width: 30,
      height: 20,
    },
    { additive: true },
  );
assert.deepEqual(additiveRectSelection.ids, ["sel-a", "sel-b"]);
selectionRuntime.dispose();



const multiMoveStore = createSpriteEntityStore();
multiMoveStore.add({ id: "group-parent", page: "heroes", frame: "plain", x: 10, y: 10 });
multiMoveStore.add({ id: "group-child", parent: "group-parent", page: "heroes", frame: "plain", x: 5, y: 0 });
multiMoveStore.add({ id: "group-peer", page: "heroes", frame: "plain", x: 40, y: 20 });
const multiSelection = createSpriteSelectionModel();
multiSelection.set(["group-parent", "group-child", "group-peer"]);
const multiBefore = resolveSpriteEntityHierarchy(multiMoveStore);
const multiMoved = moveSelectedSpriteEntitiesByWorldDelta(
  multiMoveStore,
  multiSelection,
  7,
  9,
);
assert.deepEqual(multiMoved.movedRootIds, ["group-parent", "group-peer"]);
const multiAfter = resolveSpriteEntityHierarchy(multiMoveStore);
for (const id of ["group-parent", "group-child", "group-peer"]) {
  assert.ok(Math.abs(multiAfter.byId.get(id).x - (multiBefore.byId.get(id).x + 7)) < 1e-6);
  assert.ok(Math.abs(multiAfter.byId.get(id).y - (multiBefore.byId.get(id).y + 9)) < 1e-6);
}

multiSelection.set(["group-peer", "group-parent"]);
const snappedGroup = moveSelectedSpriteEntitiesByWorldDelta(
  multiMoveStore,
  multiSelection,
  4,
  4,
  { gridSize: 10 },
);
assert.equal(snappedGroup.deltaX, 3);
assert.equal(snappedGroup.deltaY, 1);

const groupDragGl = createMockWebGL2();
groupDragGl.viewport = (...args) => groupDragGl.calls.push(["viewport", ...args]);
const groupDragCanvas = createMockCanvas();
const groupDragRuntime = await createWebGL2CanvasRuntime(
  groupDragCanvas,
  [{ id: "heroes", atlas: plainAtlas, texture: "heroes.png" }],
  {
    pointerOptions: {
      autoDragEntities: true,
      dragSelection: true,
      dragThreshold: 1,
    },
    getContext() { return groupDragGl; },
    resizeOptions: { pixelRatio: 1 },
    sceneOptions: {
      loaderOptions: {
        fetchImpl: async (url) => ({
          ok: true,
          status: 200,
          async blob() { return { id: `blob:${url}` }; },
        }),
        createImageBitmapImpl: async (blob) => ({ id: `bitmap:${blob.id}` }),
      },
    },
  },
);
groupDragRuntime.entities.add({ id: "drag-a", page: "heroes", frame: "plain", x: 10, y: 10, z: 2 });
groupDragRuntime.entities.add({ id: "drag-b", page: "heroes", frame: "plain", x: 30, y: 10, z: 1 });
groupDragRuntime.selection.set(["drag-a", "drag-b"]);
groupDragRuntime.pointerDown("mouse", 12, 12);
const groupMoveEvent = groupDragRuntime.pointerMove("mouse", 17, 16);
assert.equal(groupMoveEvent.capturedEntityId, "drag-a");
assert.equal(groupDragRuntime.entities.get("drag-a").x, 15);
assert.equal(groupDragRuntime.entities.get("drag-a").y, 14);
assert.equal(groupDragRuntime.entities.get("drag-b").x, 35);
assert.equal(groupDragRuntime.entities.get("drag-b").y, 14);
groupDragRuntime.pointerUp("mouse", 17, 16);
groupDragRuntime.moveSelectionByWorldDelta(5, 0);
assert.equal(groupDragRuntime.entities.get("drag-a").x, 20);
assert.equal(groupDragRuntime.entities.get("drag-b").x, 40);
groupDragRuntime.dispose();



const historyStore = createSpriteEntityStore();
historyStore.add({ id: "history-a", page: "heroes", frame: "plain", x: 10, y: 20 });
const history = createSpriteEntityHistory(historyStore, { maxEntries: 3 });
history.record("move a", () => historyStore.update("history-a", { x: 30 }));
assert.equal(historyStore.get("history-a").x, 30);
assert.equal(history.canUndo, true);
assert.equal(history.undo().label, "move a");
assert.equal(historyStore.get("history-a").x, 10);
assert.equal(history.canRedo, true);
assert.equal(history.redo().label, "move a");
assert.equal(historyStore.get("history-a").x, 30);

history.begin("compound");
historyStore.update("history-a", { y: 99 });
historyStore.add({ id: "history-b", page: "heroes", frame: "plain", x: 5, y: 6 });
assert.equal(history.commit(), true);
history.undo();
assert.equal(historyStore.get("history-a").y, 20);
assert.equal(historyStore.get("history-b"), null);
history.redo();
assert.equal(historyStore.get("history-a").y, 99);
assert.ok(historyStore.get("history-b"));

history.begin("cancelled");
historyStore.remove("history-a");
assert.equal(history.cancel(), true);
assert.ok(historyStore.get("history-a"));

assert.throws(
  () => history.record("async", () => Promise.resolve()),
  /history callbacks must be synchronous/,
);

const historyRuntimeGl = createMockWebGL2();
historyRuntimeGl.viewport = (...args) => historyRuntimeGl.calls.push(["viewport", ...args]);
const historyRuntime = await createWebGL2CanvasRuntime(
  createMockCanvas(),
  [{ id: "heroes", atlas: plainAtlas, texture: "heroes.png" }],
  {
    getContext() { return historyRuntimeGl; },
    resizeOptions: { pixelRatio: 1 },
    sceneOptions: {
      loaderOptions: {
        fetchImpl: async (url) => ({
          ok: true,
          status: 200,
          async blob() { return { id: `blob:${url}` }; },
        }),
        createImageBitmapImpl: async (blob) => ({ id: `bitmap:${blob.id}` }),
      },
    },
  },
);
historyRuntime.entities.add({ id: "runtime-history", page: "heroes", frame: "plain", x: 1, y: 2 });
historyRuntime.history.record("runtime move", () => {
  historyRuntime.moveEntityByWorldDelta("runtime-history", 10, 0);
});
assert.equal(historyRuntime.entities.get("runtime-history").x, 11);
historyRuntime.undo();
assert.equal(historyRuntime.entities.get("runtime-history").x, 1);
historyRuntime.redo();
assert.equal(historyRuntime.entities.get("runtime-history").x, 11);
historyRuntime.dispose();



const hierarchyEditStore = createSpriteEntityStore();
hierarchyEditStore.add({ id: "edit-root-a", page: "heroes", frame: "plain", x: 100, y: 50, rotation: 0.5, scaleX: 2, scaleY: 3 });
hierarchyEditStore.add({ id: "edit-root-b", page: "heroes", frame: "plain", x: -20, y: 40, rotation: -0.25, scaleX: 1.5, scaleY: 0.75 });
hierarchyEditStore.add({ id: "edit-child", parent: "edit-root-a", page: "heroes", frame: "plain", x: 10, y: 5, rotation: 0.2, scaleX: 0.5, scaleY: 2 });
const editWorldBefore = resolveSpriteEntityHierarchy(hierarchyEditStore).byId.get("edit-child");
reparentSpriteEntity(hierarchyEditStore, "edit-child", "edit-root-b");
const editWorldAfter = resolveSpriteEntityHierarchy(hierarchyEditStore).byId.get("edit-child");
for (const key of ["x", "y", "z", "rotation", "scaleX", "scaleY"]) {
  assert.ok(Math.abs(editWorldAfter[key] - editWorldBefore[key]) < 1e-6);
}
assert.throws(
  () => reparentSpriteEntity(hierarchyEditStore, "edit-root-b", "edit-child"),
  /create a cycle/,
);

hierarchyEditStore.add({ id: "detach-parent", page: "heroes", frame: "plain", x: 30, y: 30 });
hierarchyEditStore.add({ id: "detach-child", parent: "detach-parent", page: "heroes", frame: "plain", x: 7, y: 8 });
const detachBefore = resolveSpriteEntityHierarchy(hierarchyEditStore).byId.get("detach-child");
removeSpriteEntityHierarchy(hierarchyEditStore, "detach-parent", { childPolicy: "detach" });
const detachAfter = resolveSpriteEntityHierarchy(hierarchyEditStore).byId.get("detach-child");
assert.equal(detachAfter.parent, null);
assert.ok(Math.abs(detachAfter.x - detachBefore.x) < 1e-6);
assert.ok(Math.abs(detachAfter.y - detachBefore.y) < 1e-6);

hierarchyEditStore.add({ id: "cascade-parent", page: "heroes", frame: "plain" });
hierarchyEditStore.add({ id: "cascade-child", parent: "cascade-parent", page: "heroes", frame: "plain" });
hierarchyEditStore.add({ id: "cascade-grandchild", parent: "cascade-child", page: "heroes", frame: "plain" });
const cascadeResult = removeSpriteEntityHierarchy(hierarchyEditStore, "cascade-parent", { childPolicy: "cascade" });
assert.equal(cascadeResult.count, 3);
assert.equal(hierarchyEditStore.has("cascade-grandchild"), false);

hierarchyEditStore.add({ id: "reject-parent", page: "heroes", frame: "plain" });
hierarchyEditStore.add({ id: "reject-child", parent: "reject-parent", page: "heroes", frame: "plain" });
assert.throws(
  () => removeSpriteEntityHierarchy(hierarchyEditStore, "reject-parent", { childPolicy: "reject" }),
  /has children/,
);



const clipboardStore = createSpriteEntityStore();
clipboardStore.add({ id: "copy-parent", page: "heroes", frame: "plain", x: 10, y: 20 });
clipboardStore.add({ id: "copy-child", parent: "copy-parent", page: "heroes", frame: "plain", x: 5, y: 6 });
clipboardStore.add({ id: "copy-other", page: "heroes", frame: "plain", x: 100, y: 200 });

const duplicatedTree = duplicateSpriteEntities(
  clipboardStore,
  ["copy-parent"],
  { includeDescendants: true, offsetX: 20, offsetY: 30 },
);
assert.equal(duplicatedTree.count, 2);
const duplicateParentId = duplicatedTree.idMap.get("copy-parent");
const duplicateChildId = duplicatedTree.idMap.get("copy-child");
assert.equal(clipboardStore.get(duplicateParentId).x, 30);
assert.equal(clipboardStore.get(duplicateParentId).y, 50);
assert.equal(clipboardStore.get(duplicateChildId).parent, duplicateParentId);
assert.equal(clipboardStore.get(duplicateChildId).x, 5);
assert.equal(clipboardStore.get(duplicateChildId).y, 6);

const clipboard = copySpriteEntities(
  clipboardStore,
  ["copy-parent"],
  { includeDescendants: true },
);
assert.equal(clipboard.format, "asset-forge-sprite-clipboard");
assert.equal(clipboard.entities.length, 2);

const pasteStore = createSpriteEntityStore();
const pasted = pasteSpriteEntities(
  pasteStore,
  clipboard,
  { offsetX: 40, offsetY: 50 },
);
assert.equal(pasted.count, 2);
const pastedParent = pasteStore.get(pasted.idMap.get("copy-parent"));
const pastedChild = pasteStore.get(pasted.idMap.get("copy-child"));
assert.equal(pastedParent.x, 50);
assert.equal(pastedParent.y, 70);
assert.equal(pastedChild.parent, pastedParent.id);
assert.equal(pastedChild.x, 5);
assert.equal(pastedChild.y, 6);



const groupTransformStore = createSpriteEntityStore();
groupTransformStore.add({ id: "transform-a", page: "heroes", frame: "plain", x: 0, y: 0 });
groupTransformStore.add({ id: "transform-b", page: "heroes", frame: "plain", x: 10, y: 0 });
const groupTransformSelection = createSpriteSelectionModel();
groupTransformSelection.set(["transform-a", "transform-b"]);
const rotatedGroup = transformSelectedSpriteEntities(
  groupTransformStore,
  groupTransformSelection,
  { rotation: Math.PI / 2, pivotX: 5, pivotY: 0 },
);
assert.equal(rotatedGroup.count, 2);
assert.ok(Math.abs(groupTransformStore.get("transform-a").x - 5) < 1e-6);
assert.ok(Math.abs(groupTransformStore.get("transform-a").y + 5) < 1e-6);
assert.ok(Math.abs(groupTransformStore.get("transform-b").x - 5) < 1e-6);
assert.ok(Math.abs(groupTransformStore.get("transform-b").y - 5) < 1e-6);
assert.ok(Math.abs(groupTransformStore.get("transform-a").rotation - Math.PI / 2) < 1e-6);

transformSelectedSpriteEntities(
  groupTransformStore,
  groupTransformSelection,
  { scaleX: 2, scaleY: 3, pivotX: 5, pivotY: 0 },
);
assert.ok(Math.abs(groupTransformStore.get("transform-a").y + 15) < 1e-6);
assert.ok(Math.abs(groupTransformStore.get("transform-b").y - 15) < 1e-6);
assert.ok(Math.abs(groupTransformStore.get("transform-a").scaleX - 2) < 1e-6);
assert.ok(Math.abs(groupTransformStore.get("transform-a").scaleY - 3) < 1e-6);

console.log("runtime_atlas.mjs smoke test passed");
