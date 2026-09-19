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
  createSpriteAnimationSystem,
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
assert.equal(instanced.instanceStrideFloats, 12);
assert.equal(instanced.instanceStrideBytes, 48);
assert.deepEqual(instanced.instanceLayout, [
  "visibleX",
  "visibleY",
  "visibleWidth",
  "visibleHeight",
  "u0",
  "v0",
  "u1",
  "v1",
  "rotationFlag",
  "sourceWidth",
  "sourceHeight",
  "reserved",
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
assert.equal(instancedMany.instances.byteLength, 1000 * 12 * 4);
assert.ok(instancedMany.instances.byteLength < classicMany.vertices.byteLength);

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
assert.equal(attributeViews.strideBytes, 48);
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

console.log("runtime_atlas.mjs smoke test passed");
