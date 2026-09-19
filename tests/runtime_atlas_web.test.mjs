import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import {
  drawFrameCanvas2D,
  frameQuad,
  indexRuntimeAtlas,
  sourceOrientedUVs,
  animationFrameAtTime,
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
