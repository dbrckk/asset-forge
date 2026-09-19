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

console.log("runtime_atlas.mjs smoke test passed");


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
      calls.push(["bindTexture", target, texture?.id ?? texture]);
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
