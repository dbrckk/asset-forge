export function indexRuntimeAtlas(atlas) {
  if (!atlas || atlas.format !== "asset-forge-runtime-atlas" || atlas.version !== 1) {
    throw new Error("unsupported Asset Forge runtime atlas");
  }
  if (!Array.isArray(atlas.frames) || atlas.frames.length !== atlas.frameCount) {
    throw new Error("runtime atlas frameCount mismatch");
  }

  const byIndex = new Map();
  const byName = new Map();
  const animations = new Map();

  for (const frame of atlas.frames) {
    if (byIndex.has(frame.index)) {
      throw new Error(`duplicate runtime atlas frame index ${frame.index}`);
    }
    byIndex.set(frame.index, frame);
    if (frame.name != null) {
      if (byName.has(frame.name)) {
        throw new Error(`duplicate runtime atlas frame name ${frame.name}`);
      }
      byName.set(frame.name, frame);
    }
  }

  for (const animation of atlas.animations ?? []) {
    if (animations.has(animation.name)) {
      throw new Error(`duplicate runtime atlas animation name ${animation.name}`);
    }
    animations.set(animation.name, animation);
  }

  return {
    atlas,
    byIndex,
    byName,
    animations,
    frame(indexOrName) {
      const frame =
        typeof indexOrName === "number"
          ? byIndex.get(indexOrName)
          : byName.get(indexOrName);
      if (!frame) {
        throw new Error(`runtime atlas frame not found: ${indexOrName}`);
      }
      return frame;
    },
    animation(name) {
      const animation = animations.get(name);
      if (!animation) {
        throw new Error(`runtime atlas animation not found: ${name}`);
      }
      return animation;
    },
  };
}

export function frameQuad(frame) {
  const { uv, sourceRegion, trimOffset, rotation } = frame;
  return {
    sourceSize: { ...frame.sourceSize },
    trimOffset: { ...trimOffset },
    sourceRegion: { ...sourceRegion },
    rotated: rotation.rotated,
    degreesClockwise: rotation.degreesClockwise,
    uv: {
      topLeft: { u: uv.u0, v: uv.v0 },
      topRight: { u: uv.u1, v: uv.v0 },
      bottomRight: { u: uv.u1, v: uv.v1 },
      bottomLeft: { u: uv.u0, v: uv.v1 },
    },
  };
}

export function drawFrameCanvas2D(
  ctx,
  image,
  frame,
  destinationX = 0,
  destinationY = 0,
  options = {},
) {
  const scale = options.scale ?? 1;
  if (!(scale > 0)) {
    throw new Error("scale must be > 0");
  }

  const region = frame.atlasRegion;
  const source = frame.sourceRegion;
  const offset = frame.trimOffset;
  const rotation = frame.rotation;

  const dx = destinationX + offset.x * scale;
  const dy = destinationY + offset.y * scale;

  ctx.save();
  try {
    if (rotation.rotated) {
      if (rotation.degreesClockwise !== 90) {
        throw new Error("Canvas2D consumer only supports 90-degree clockwise packed rotation");
      }

      // Atlas pixels are stored 90° clockwise. Rotate the destination context
      // 90° counter-clockwise so the sprite is restored to source orientation.
      ctx.translate(dx, dy + source.height * scale);
      ctx.rotate(-Math.PI / 2);
      ctx.drawImage(
        image,
        region.x,
        region.y,
        region.width,
        region.height,
        0,
        0,
        region.width * scale,
        region.height * scale,
      );
    } else {
      ctx.drawImage(
        image,
        region.x,
        region.y,
        region.width,
        region.height,
        dx,
        dy,
        source.width * scale,
        source.height * scale,
      );
    }
  } finally {
    ctx.restore();
  }

  return {
    x: destinationX,
    y: destinationY,
    width: frame.sourceSize.width * scale,
    height: frame.sourceSize.height * scale,
  };
}


export function sourceOrientedUVs(frame) {
  const { u0, v0, u1, v1 } = frame.uv;
  if (!frame.rotation.rotated) {
    return [
      { u: u0, v: v0 },
      { u: u1, v: v0 },
      { u: u1, v: v1 },
      { u: u0, v: v1 },
    ];
  }
  if (frame.rotation.degreesClockwise !== 90) {
    throw new Error("runtime atlas consumer only supports 90-degree clockwise packed rotation");
  }

  // Return UVs in source-orientation vertex order:
  // top-left, top-right, bottom-right, bottom-left.
  return [
    { u: u0, v: v1 },
    { u: u0, v: v0 },
    { u: u1, v: v0 },
    { u: u1, v: v1 },
  ];
}


export function animationFrameAtTime(indexedAtlas, animationOrName, timeSeconds) {
  if (!Number.isFinite(timeSeconds)) {
    throw new Error("timeSeconds must be finite");
  }

  const animation =
    typeof animationOrName === "string"
      ? indexedAtlas.animation(animationOrName)
      : animationOrName;

  if (!animation || !(animation.fps > 0) || !Array.isArray(animation.frames) || animation.frames.length === 0) {
    throw new Error("invalid runtime atlas animation");
  }

  const frameUnits = animation.frames.map((entry) => {
    if (!(entry.duration > 0)) {
      throw new Error("animation frame duration must be > 0");
    }
    return entry.duration;
  });
  const totalUnits = frameUnits.reduce((sum, value) => sum + value, 0);
  const durationSeconds = totalUnits / animation.fps;

  let t = Math.max(0, timeSeconds);
  if (animation.loop) {
    t = durationSeconds > 0 ? t % durationSeconds : 0;
  } else if (t >= durationSeconds) {
    const last = animation.frames[animation.frames.length - 1];
    return {
      animation,
      frame: indexedAtlas.frame(last.index),
      frameIndex: animation.frames.length - 1,
      localTimeSeconds: durationSeconds,
      durationSeconds,
      finished: true,
    };
  }

  const unitPosition = t * animation.fps;
  let accumulated = 0;
  for (let i = 0; i < animation.frames.length; i += 1) {
    accumulated += frameUnits[i];
    if (unitPosition < accumulated || i === animation.frames.length - 1) {
      const entry = animation.frames[i];
      return {
        animation,
        frame: indexedAtlas.frame(entry.index),
        frameIndex: i,
        localTimeSeconds: t,
        durationSeconds,
        finished: false,
      };
    }
  }

  throw new Error("unable to resolve animation frame");
}


export function animationDurationSeconds(animation) {
  if (!animation || !(animation.fps > 0) || !Array.isArray(animation.frames) || animation.frames.length === 0) {
    throw new Error("invalid runtime atlas animation");
  }
  let units = 0;
  for (const entry of animation.frames) {
    if (!(entry.duration > 0)) {
      throw new Error("animation frame duration must be > 0");
    }
    units += entry.duration;
  }
  return units / animation.fps;
}

export function animationEventsBetween(animation, startTimeSeconds, endTimeSeconds) {
  if (!Number.isFinite(startTimeSeconds) || !Number.isFinite(endTimeSeconds)) {
    throw new Error("animation event interval must be finite");
  }
  if (startTimeSeconds < 0 || endTimeSeconds < startTimeSeconds) {
    throw new Error("invalid animation event interval");
  }
  if (endTimeSeconds === startTimeSeconds) {
    return [];
  }

  const events = animation.events ?? [];
  if (!Array.isArray(events) || events.length === 0) {
    return [];
  }

  const durationSeconds = animationDurationSeconds(animation);
  const occurrences = [];
  const includeOccurrence = (event, absoluteTimeSeconds, loopCount, eventIndex) => {
    const crossed =
      (absoluteTimeSeconds > startTimeSeconds ||
        (startTimeSeconds === 0 && absoluteTimeSeconds === 0)) &&
      absoluteTimeSeconds <= endTimeSeconds;
    if (!crossed) {
      return;
    }
    occurrences.push({
      event,
      name: event.name,
      payload: event.payload ?? null,
      timeSeconds: event.timeSeconds,
      absoluteTimeSeconds,
      loopCount,
      eventIndex,
    });
    if (occurrences.length > 10000) {
      throw new Error("too many animation events crossed in one update");
    }
  };

  if (animation.loop) {
    const firstLoop = Math.floor(startTimeSeconds / durationSeconds);
    const lastLoop = Math.floor(endTimeSeconds / durationSeconds);
    for (let loopCount = firstLoop; loopCount <= lastLoop; loopCount += 1) {
      for (let eventIndex = 0; eventIndex < events.length; eventIndex += 1) {
        const event = events[eventIndex];
        includeOccurrence(
          event,
          loopCount * durationSeconds + event.timeSeconds,
          loopCount,
          eventIndex,
        );
      }
    }
  } else {
    const cappedEnd = Math.min(endTimeSeconds, durationSeconds);
    for (let eventIndex = 0; eventIndex < events.length; eventIndex += 1) {
      const event = events[eventIndex];
      const absoluteTimeSeconds = event.timeSeconds;
      if (absoluteTimeSeconds <= cappedEnd) {
        includeOccurrence(event, absoluteTimeSeconds, 0, eventIndex);
      }
    }
  }

  occurrences.sort(
    (a, b) =>
      a.absoluteTimeSeconds - b.absoluteTimeSeconds ||
      a.eventIndex - b.eventIndex,
  );
  return occurrences;
}


export function createAnimationPlayer(indexedAtlas, animationName, options = {}) {
  const animation = indexedAtlas.animation(animationName);
  let timeSeconds = options.startTime ?? 0;
  let playing = options.autoplay ?? false;
  let playbackRate = options.playbackRate ?? 1;
  let lastFrameIndex = null;
  let finishEmitted = false;

  if (!Number.isFinite(timeSeconds) || timeSeconds < 0) {
    throw new Error("startTime must be a finite value >= 0");
  }
  if (!Number.isFinite(playbackRate) || playbackRate <= 0) {
    throw new Error("playbackRate must be > 0");
  }

  const onFrame = typeof options.onFrame === "function" ? options.onFrame : null;
  const onFinish = typeof options.onFinish === "function" ? options.onFinish : null;
  const onLoop = typeof options.onLoop === "function" ? options.onLoop : null;
  const onEvent = typeof options.onEvent === "function" ? options.onEvent : null;

  function emit(sample) {
    if (sample.frameIndex !== lastFrameIndex) {
      lastFrameIndex = sample.frameIndex;
      onFrame?.(sample);
    }
    if (sample.finished) {
      playing = false;
      if (!finishEmitted) {
        finishEmitted = true;
        onFinish?.(sample);
      }
    } else {
      finishEmitted = false;
    }
    return sample;
  }

  function sample() {
    return emit(animationFrameAtTime(indexedAtlas, animation, timeSeconds));
  }

  return {
    get animation() {
      return animation;
    },
    get timeSeconds() {
      return timeSeconds;
    },
    get playing() {
      return playing;
    },
    get playbackRate() {
      return playbackRate;
    },
    play() {
      playing = true;
      return sample();
    },
    pause() {
      playing = false;
      return sample();
    },
    seek(nextTimeSeconds) {
      if (!Number.isFinite(nextTimeSeconds) || nextTimeSeconds < 0) {
        throw new Error("seek time must be a finite value >= 0");
      }
      timeSeconds = nextTimeSeconds;
      finishEmitted = false;
      return sample();
    },
    setPlaybackRate(rate) {
      if (!Number.isFinite(rate) || rate <= 0) {
        throw new Error("playbackRate must be > 0");
      }
      playbackRate = rate;
      return playbackRate;
    },
    sample,
    update(deltaSeconds) {
      if (!Number.isFinite(deltaSeconds) || deltaSeconds < 0) {
        throw new Error("deltaSeconds must be a finite value >= 0");
      }
      if (playing) {
        const before = animationFrameAtTime(indexedAtlas, animation, timeSeconds);
        const previousTime = timeSeconds;
        timeSeconds += deltaSeconds * playbackRate;
        const after = animationFrameAtTime(indexedAtlas, animation, timeSeconds);

        if (animation.loop && before.durationSeconds > 0 && onLoop) {
          const previousLoops = Math.floor(previousTime / before.durationSeconds);
          const nextLoops = Math.floor(timeSeconds / after.durationSeconds);
          for (let loopIndex = previousLoops; loopIndex < nextLoops; loopIndex += 1) {
            onLoop({
              animation,
              loopCount: loopIndex + 1,
              durationSeconds: after.durationSeconds,
            });
          }
        }

        if (onEvent) {
          for (const occurrence of animationEventsBetween(
            animation,
            previousTime,
            timeSeconds,
          )) {
            onEvent({
              ...occurrence,
              animation,
            });
          }
        }
      }
      return sample();
    },
  };
}


export function drawAnimationPlayerCanvas2D(
  ctx,
  image,
  player,
  destinationX = 0,
  destinationY = 0,
  options = {},
) {
  const sample = player.sample();
  const bounds = drawFrameCanvas2D(
    ctx,
    image,
    sample.frame,
    destinationX,
    destinationY,
    options,
  );
  return { ...sample, bounds };
}


export function buildSpriteBatch(indexedAtlas, instances, options = {}) {
  if (!Array.isArray(instances)) {
    throw new Error("sprite batch instances must be an array");
  }
  const maxInstances = options.maxInstances ?? 100000;
  if (!Number.isInteger(maxInstances) || maxInstances <= 0) {
    throw new Error("maxInstances must be a positive integer");
  }
  if (instances.length > maxInstances) {
    throw new Error(
      `sprite batch instance count ${instances.length} exceeds maxInstances ${maxInstances}`,
    );
  }

  const vertexCount = instances.length * 4;
  const indexCount = instances.length * 6;
  const vertices = new Float32Array(vertexCount * 4);
  const IndexArray = vertexCount <= 65535 ? Uint16Array : Uint32Array;
  const indices = new IndexArray(indexCount);
  const bounds = new Array(instances.length);

  for (let instanceIndex = 0; instanceIndex < instances.length; instanceIndex += 1) {
    const instance = instances[instanceIndex];
    if (!instance || typeof instance !== "object") {
      throw new Error(`sprite batch instance ${instanceIndex} must be an object`);
    }

    const frame = indexedAtlas.frame(instance.frame);
    const x = instance.x ?? 0;
    const y = instance.y ?? 0;
    const scaleX = instance.scaleX ?? instance.scale ?? 1;
    const scaleY = instance.scaleY ?? instance.scale ?? 1;
    const spriteRotation = instance.rotation ?? 0;
    const pivotX = instance.pivotX ?? 0;
    const pivotY = instance.pivotY ?? 0;

    for (const [name, value] of Object.entries({
      x, y, scaleX, scaleY, spriteRotation, pivotX, pivotY,
    })) {
      if (!Number.isFinite(value)) {
        throw new Error(`sprite batch instance ${instanceIndex} ${name} must be finite`);
      }
    }
    if (scaleX <= 0 || scaleY <= 0) {
      throw new Error(`sprite batch instance ${instanceIndex} scale must be > 0`);
    }

    const left = x + frame.trimOffset.x * scaleX;
    const top = y + frame.trimOffset.y * scaleY;
    const right = left + frame.sourceRegion.width * scaleX;
    const bottom = top + frame.sourceRegion.height * scaleY;
    const uvs = sourceOrientedUVs(frame);
    const pivotWorldX = x + pivotX * scaleX;
    const pivotWorldY = y + pivotY * scaleY;
    const cosRotation = Math.cos(spriteRotation);
    const sinRotation = Math.sin(spriteRotation);
    const positions = [
      [left, top],
      [right, top],
      [right, bottom],
      [left, bottom],
    ].map(([px, py]) => {
      if (spriteRotation === 0) return [px, py];
      const dx = px - pivotWorldX;
      const dy = py - pivotWorldY;
      return [
        pivotWorldX + dx * cosRotation - dy * sinRotation,
        pivotWorldY + dx * sinRotation + dy * cosRotation,
      ];
    });

    const vertexBase = instanceIndex * 4;
    for (let corner = 0; corner < 4; corner += 1) {
      const write = (vertexBase + corner) * 4;
      vertices[write] = positions[corner][0];
      vertices[write + 1] = positions[corner][1];
      vertices[write + 2] = uvs[corner].u;
      vertices[write + 3] = uvs[corner].v;
    }

    const indexBase = instanceIndex * 6;
    indices[indexBase] = vertexBase;
    indices[indexBase + 1] = vertexBase + 1;
    indices[indexBase + 2] = vertexBase + 2;
    indices[indexBase + 3] = vertexBase;
    indices[indexBase + 4] = vertexBase + 2;
    indices[indexBase + 5] = vertexBase + 3;

    bounds[instanceIndex] = {
      x,
      y,
      width: frame.sourceSize.width * scaleX,
      height: frame.sourceSize.height * scaleY,
      visibleX: Math.min(...positions.map(([px]) => px)),
      visibleY: Math.min(...positions.map(([, py]) => py)),
      visibleWidth:
        Math.max(...positions.map(([px]) => px)) -
        Math.min(...positions.map(([px]) => px)),
      visibleHeight:
        Math.max(...positions.map(([, py]) => py)) -
        Math.min(...positions.map(([, py]) => py)),
      rotation: spriteRotation,
      pivotWorldX,
      pivotWorldY,
      frameIndex: frame.index,
      frameName: frame.name ?? null,
    };
  }

  return {
    instanceCount: instances.length,
    vertexCount,
    indexCount,
    vertexStrideFloats: 4,
    vertexLayout: ["x", "y", "u", "v"],
    vertices,
    indices,
    indexType: indices instanceof Uint16Array ? "uint16" : "uint32",
    bounds,
  };
}

export function drawSpriteBatchCanvas2D(ctx, image, indexedAtlas, instances) {
  if (!Array.isArray(instances)) {
    throw new Error("sprite batch instances must be an array");
  }

  const bounds = [];
  for (let instanceIndex = 0; instanceIndex < instances.length; instanceIndex += 1) {
    const instance = instances[instanceIndex];
    if (!instance || typeof instance !== "object") {
      throw new Error(`sprite batch instance ${instanceIndex} must be an object`);
    }
    const frame = indexedAtlas.frame(instance.frame);
    const x = instance.x ?? 0;
    const y = instance.y ?? 0;
    const scaleX = instance.scaleX ?? instance.scale ?? 1;
    const scaleY = instance.scaleY ?? instance.scale ?? 1;
    if (scaleX !== scaleY) {
      throw new Error(
        "Canvas2D sprite batch currently requires uniform scale per instance",
      );
    }
    bounds.push(
      drawFrameCanvas2D(ctx, image, frame, x, y, { scale: scaleX }),
    );
  }
  return bounds;
}


export function buildInstancedSpriteBatch(indexedAtlas, instances, options = {}) {
  if (!Array.isArray(instances)) {
    throw new Error("instanced sprite batch instances must be an array");
  }
  const maxInstances = options.maxInstances ?? 100000;
  if (!Number.isInteger(maxInstances) || maxInstances <= 0) {
    throw new Error("maxInstances must be a positive integer");
  }
  if (instances.length > maxInstances) {
    throw new Error(
      `instanced sprite batch count ${instances.length} exceeds maxInstances ${maxInstances}`,
    );
  }

  // Per instance:
  // visibleX, visibleY, visibleWidth, visibleHeight,
  // u0, v0, u1, v1,
  // atlasRotationFlag, sourceWidth, sourceHeight, spriteRotationRadians,
  // pivotWorldX, pivotWorldY,
  // tintR, tintG, tintB, alpha
  const strideFloats = 18;
  const data = new Float32Array(instances.length * strideFloats);
  const bounds = new Array(instances.length);

  for (let instanceIndex = 0; instanceIndex < instances.length; instanceIndex += 1) {
    const instance = instances[instanceIndex];
    if (!instance || typeof instance !== "object") {
      throw new Error(`instanced sprite batch instance ${instanceIndex} must be an object`);
    }

    const frame = indexedAtlas.frame(instance.frame);
    const x = instance.x ?? 0;
    const y = instance.y ?? 0;
    const scaleX = instance.scaleX ?? instance.scale ?? 1;
    const scaleY = instance.scaleY ?? instance.scale ?? 1;
    const spriteRotation = instance.rotation ?? 0;
    const pivotX = instance.pivotX ?? 0;
    const pivotY = instance.pivotY ?? 0;
    const alpha = instance.alpha ?? 1;
    const tintR = instance.tintR ?? 1;
    const tintG = instance.tintG ?? 1;
    const tintB = instance.tintB ?? 1;

    for (const [name, value] of Object.entries({
      x,
      y,
      scaleX,
      scaleY,
      spriteRotation,
      pivotX,
      pivotY,
      alpha,
      tintR,
      tintG,
      tintB,
    })) {
      if (!Number.isFinite(value)) {
        throw new Error(
          `instanced sprite batch instance ${instanceIndex} ${name} must be finite`,
        );
      }
    }
    if (scaleX <= 0 || scaleY <= 0) {
      throw new Error(
        `instanced sprite batch instance ${instanceIndex} scale must be > 0`,
      );
    }
    for (const [name, value] of Object.entries({ alpha, tintR, tintG, tintB })) {
      if (value < 0 || value > 1) {
        throw new Error(
          `instanced sprite batch instance ${instanceIndex} ${name} must be between 0 and 1`,
        );
      }
    }

    const visibleX = x + frame.trimOffset.x * scaleX;
    const visibleY = y + frame.trimOffset.y * scaleY;
    const visibleWidth = frame.sourceRegion.width * scaleX;
    const visibleHeight = frame.sourceRegion.height * scaleY;
    const write = instanceIndex * strideFloats;
    const { u0, v0, u1, v1 } = frame.uv;

    data[write] = visibleX;
    data[write + 1] = visibleY;
    data[write + 2] = visibleWidth;
    data[write + 3] = visibleHeight;
    data[write + 4] = u0;
    data[write + 5] = v0;
    data[write + 6] = u1;
    data[write + 7] = v1;
    data[write + 8] = frame.rotation.rotated ? 1 : 0;
    data[write + 9] = frame.sourceSize.width * scaleX;
    data[write + 10] = frame.sourceSize.height * scaleY;
    data[write + 11] = spriteRotation;
    data[write + 12] = x + pivotX * scaleX;
    data[write + 13] = y + pivotY * scaleY;
    data[write + 14] = tintR;
    data[write + 15] = tintG;
    data[write + 16] = tintB;
    data[write + 17] = alpha;

    bounds[instanceIndex] = {
      x,
      y,
      width: frame.sourceSize.width * scaleX,
      height: frame.sourceSize.height * scaleY,
      visibleX,
      visibleY,
      visibleWidth,
      visibleHeight,
      frameIndex: frame.index,
      frameName: frame.name ?? null,
      rotated: frame.rotation.rotated,
      rotation: spriteRotation,
      pivotWorldX: x + pivotX * scaleX,
      pivotWorldY: y + pivotY * scaleY,
    };
  }

  return {
    instanceCount: instances.length,
    instanceStrideFloats: strideFloats,
    instanceStrideBytes: strideFloats * Float32Array.BYTES_PER_ELEMENT,
    instanceLayout: [
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
      "tintR",
      "tintG",
      "tintB",
      "alpha",
    ],
    instances: data,
    bounds,
    unitQuad: {
      vertices: new Float32Array([
        0, 0,
        1, 0,
        1, 1,
        0, 1,
      ]),
      indices: new Uint16Array([0, 1, 2, 0, 2, 3]),
    },
  };
}

export function instancedSpriteUV(
  u0,
  v0,
  u1,
  v1,
  rotationFlag,
  unitX,
  unitY,
) {
  if (![u0, v0, u1, v1, rotationFlag, unitX, unitY].every(Number.isFinite)) {
    throw new Error("instanced sprite UV arguments must be finite");
  }
  if (rotationFlag !== 0 && rotationFlag !== 1) {
    throw new Error("rotationFlag must be 0 or 1");
  }

  if (rotationFlag === 0) {
    return {
      u: u0 + (u1 - u0) * unitX,
      v: v0 + (v1 - v0) * unitY,
    };
  }

  // Packed texture is 90° clockwise. Convert source-oriented unit coords
  // to stored atlas UV coordinates.
  return {
    u: u0 + (u1 - u0) * unitY,
    v: v1 - (v1 - v0) * unitX,
  };
}


export function instancedSpriteWebGL2Shaders() {
  return {
    attributes: {
      aUnitPosition: { location: 0, components: 2, divisor: 0 },
      aVisibleRect: { location: 1, components: 4, divisor: 1 },
      aUvRect: { location: 2, components: 4, divisor: 1 },
      aRotationAndSource: { location: 3, components: 4, divisor: 1 },
      aPivotAndReserved: { location: 4, components: 2, divisor: 1 },
      aTint: { location: 5, components: 4, divisor: 1 },
    },
    uniforms: {
      uViewportSize: "vec2",
      uTexture: "sampler2D",
    },
    vertex: `#version 300 es
precision highp float;

layout(location = 0) in vec2 aUnitPosition;
layout(location = 1) in vec4 aVisibleRect;
layout(location = 2) in vec4 aUvRect;
layout(location = 3) in vec4 aRotationAndSource;
layout(location = 4) in vec4 aPivotAndReserved;
layout(location = 5) in vec4 aTint;

uniform vec2 uViewportSize;

out vec2 vUv;
out vec4 vTint;

void main() {
  vec2 pixelPosition =
    aVisibleRect.xy + aUnitPosition * aVisibleRect.zw;

  float spriteRotation = aRotationAndSource.w;
  if (spriteRotation != 0.0) {
    vec2 pivot = aPivotAndReserved.xy;
    vec2 delta = pixelPosition - pivot;
    float c = cos(spriteRotation);
    float s = sin(spriteRotation);
    pixelPosition = pivot + vec2(
      delta.x * c - delta.y * s,
      delta.x * s + delta.y * c
    );
  }

  vec2 clip = vec2(
    pixelPosition.x / uViewportSize.x * 2.0 - 1.0,
    1.0 - pixelPosition.y / uViewportSize.y * 2.0
  );

  float rotationFlag = aRotationAndSource.x;
  if (rotationFlag < 0.5) {
    vUv = mix(aUvRect.xy, aUvRect.zw, aUnitPosition);
  } else {
    vUv = vec2(
      mix(aUvRect.x, aUvRect.z, aUnitPosition.y),
      mix(aUvRect.w, aUvRect.y, aUnitPosition.x)
    );
  }

  vTint = aTint;
  gl_Position = vec4(clip, 0.0, 1.0);
}
`,
    fragment: `#version 300 es
precision mediump float;

uniform sampler2D uTexture;
in vec2 vUv;
in vec4 vTint;
out vec4 outColor;

void main() {
  outColor = texture(uTexture, vUv) * vTint;
}
`,
  };
}

export function instancedSpriteAttributeViews(batch) {
  if (!batch || !(batch.instances instanceof Float32Array)) {
    throw new Error("invalid instanced sprite batch");
  }
  if (batch.instanceStrideFloats !== 18) {
    throw new Error("unsupported instanced sprite stride");
  }

  return {
    buffer: batch.instances,
    strideBytes: batch.instanceStrideBytes,
    attributes: [
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
        offsetBytes: 4 * Float32Array.BYTES_PER_ELEMENT,
        divisor: 1,
      },
      {
        name: "aRotationAndSource",
        location: 3,
        size: 4,
        offsetBytes: 8 * Float32Array.BYTES_PER_ELEMENT,
        divisor: 1,
      },
      {
        name: "aPivotAndReserved",
        location: 4,
        size: 2,
        offsetBytes: 12 * Float32Array.BYTES_PER_ELEMENT,
        divisor: 1,
      },
      {
        name: "aTint",
        location: 5,
        size: 4,
        offsetBytes: 14 * Float32Array.BYTES_PER_ELEMENT,
        divisor: 1,
      },
    ],
  };
}


export function createRuntimeAtlasPages(pages) {
  if (!Array.isArray(pages) || pages.length === 0) {
    throw new Error("runtime atlas pages must be a non-empty array");
  }

  const byId = new Map();
  const ordered = [];

  for (let index = 0; index < pages.length; index += 1) {
    const page = pages[index];
    if (!page || typeof page !== "object") {
      throw new Error(`runtime atlas page ${index} must be an object`);
    }
    const id = page.id;
    if (typeof id !== "string" || id.length === 0) {
      throw new Error(`runtime atlas page ${index} id must be a non-empty string`);
    }
    if (byId.has(id)) {
      throw new Error(`duplicate runtime atlas page id ${id}`);
    }

    const indexedAtlas =
      page.atlas?.frame && page.atlas?.atlas
        ? page.atlas
        : indexRuntimeAtlas(page.atlas);
    const texture = page.texture ?? indexedAtlas.atlas.image;

    const normalized = {
      id,
      texture,
      atlas: indexedAtlas,
      order: index,
    };
    byId.set(id, normalized);
    ordered.push(normalized);
  }

  return {
    pages: ordered,
    byId,
    page(id) {
      const page = byId.get(id);
      if (!page) {
        throw new Error(`runtime atlas page not found: ${id}`);
      }
      return page;
    },
  };
}

export function buildTexturePageBatches(
  atlasPages,
  instances,
  options = {},
) {
  if (!atlasPages || typeof atlasPages.page !== "function") {
    throw new Error("invalid runtime atlas page catalogue");
  }
  if (!Array.isArray(instances)) {
    throw new Error("texture-page batch instances must be an array");
  }

  const mode = options.mode ?? "instanced";
  if (mode !== "instanced" && mode !== "classic") {
    throw new Error("texture-page batch mode must be instanced or classic");
  }

  const preserveOrder = options.preserveOrder ?? false;
  if (typeof preserveOrder !== "boolean") {
    throw new Error("preserveOrder must be boolean");
  }

  const sequence = [];
  let previousPageId = null;
  let inputTextureSwitches = 0;

  const prepared = instances.map((instance, instanceIndex) => {
    if (!instance || typeof instance !== "object") {
      throw new Error(`texture-page instance ${instanceIndex} must be an object`);
    }
    const pageId = instance.page;
    if (typeof pageId !== "string" || pageId.length === 0) {
      throw new Error(`texture-page instance ${instanceIndex} page must be a non-empty string`);
    }

    const page = atlasPages.page(pageId);
    if (previousPageId !== null && previousPageId !== pageId) {
      inputTextureSwitches += 1;
    }
    previousPageId = pageId;
    sequence.push(pageId);

    const { page: _page, ...spriteInstance } = instance;
    return {
      page,
      spriteInstance,
      inputIndex: instanceIndex,
    };
  });

  const groups = [];
  if (preserveOrder) {
    let current = null;
    for (const item of prepared) {
      if (!current || current.page.id !== item.page.id) {
        current = {
          page: item.page,
          instances: [],
          inputIndices: [],
          firstInputIndex: item.inputIndex,
        };
        groups.push(current);
      }
      current.instances.push(item.spriteInstance);
      current.inputIndices.push(item.inputIndex);
    }
  } else {
    const byPage = new Map();
    for (const item of prepared) {
      if (!byPage.has(item.page.id)) {
        byPage.set(item.page.id, {
          page: item.page,
          instances: [],
          inputIndices: [],
          firstInputIndex: item.inputIndex,
        });
      }
      const group = byPage.get(item.page.id);
      group.instances.push(item.spriteInstance);
      group.inputIndices.push(item.inputIndex);
    }
    groups.push(
      ...Array.from(byPage.values()).sort(
        (a, b) => a.page.order - b.page.order || a.page.id.localeCompare(b.page.id),
      ),
    );
  }

  const batches = groups.map((group) => {
    const batch =
      mode === "instanced"
        ? buildInstancedSpriteBatch(group.page.atlas, group.instances, options)
        : buildSpriteBatch(group.page.atlas, group.instances, options);

    return {
      pageId: group.page.id,
      texture: group.page.texture,
      atlas: group.page.atlas,
      instanceCount: group.instances.length,
      firstInputIndex: group.firstInputIndex,
      inputIndices: group.inputIndices,
      batch,
    };
  });

  const outputTextureSwitches = Math.max(0, batches.length - 1);

  return {
    mode,
    preserveOrder,
    pageCount: new Set(batches.map((batch) => batch.pageId)).size,
    batchCount: batches.length,
    instanceCount: instances.length,
    inputTextureSwitches,
    outputTextureSwitches,
    textureSwitchesSaved: Math.max(
      0,
      inputTextureSwitches - outputTextureSwitches,
    ),
    inputPageSequence: sequence,
    batches,
  };
}


function _compileWebGL2Shader(gl, type, source) {
  const shader = gl.createShader(type);
  if (!shader) {
    throw new Error("WebGL2 shader allocation failed");
  }
  gl.shaderSource(shader, source);
  gl.compileShader(shader);
  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
    const log = gl.getShaderInfoLog(shader) || "unknown shader compile error";
    gl.deleteShader(shader);
    throw new Error(`WebGL2 shader compile failed: ${log}`);
  }
  return shader;
}

function _linkWebGL2Program(gl, vertexSource, fragmentSource) {
  const vertex = _compileWebGL2Shader(gl, gl.VERTEX_SHADER, vertexSource);
  const fragment = _compileWebGL2Shader(gl, gl.FRAGMENT_SHADER, fragmentSource);
  const program = gl.createProgram();
  if (!program) {
    gl.deleteShader(vertex);
    gl.deleteShader(fragment);
    throw new Error("WebGL2 program allocation failed");
  }

  gl.attachShader(program, vertex);
  gl.attachShader(program, fragment);
  gl.linkProgram(program);
  gl.deleteShader(vertex);
  gl.deleteShader(fragment);

  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
    const log = gl.getProgramInfoLog(program) || "unknown program link error";
    gl.deleteProgram(program);
    throw new Error(`WebGL2 program link failed: ${log}`);
  }
  return program;
}

export function createInstancedSpriteRendererWebGL2(gl, options = {}) {
  if (!gl || typeof gl.drawElementsInstanced !== "function") {
    throw new Error("WebGL2 context with drawElementsInstanced is required");
  }

  const shaderContract = options.shaders ?? instancedSpriteWebGL2Shaders();
  const alphaBlending = options.alphaBlending ?? true;
  if (typeof alphaBlending !== "boolean") {
    throw new Error("alphaBlending must be boolean");
  }
  const resolveTexture =
    typeof options.resolveTexture === "function"
      ? options.resolveTexture
      : (texture) => texture;
  const program = _linkWebGL2Program(
    gl,
    shaderContract.vertex,
    shaderContract.fragment,
  );

  const vao = gl.createVertexArray();
  const unitVertexBuffer = gl.createBuffer();
  const unitIndexBuffer = gl.createBuffer();
  const instanceBuffer = gl.createBuffer();
  if (!vao || !unitVertexBuffer || !unitIndexBuffer || !instanceBuffer) {
    if (vao) gl.deleteVertexArray(vao);
    if (unitVertexBuffer) gl.deleteBuffer(unitVertexBuffer);
    if (unitIndexBuffer) gl.deleteBuffer(unitIndexBuffer);
    if (instanceBuffer) gl.deleteBuffer(instanceBuffer);
    gl.deleteProgram(program);
    throw new Error("WebGL2 sprite renderer buffer allocation failed");
  }

  const unitVertices = new Float32Array([
    0, 0,
    1, 0,
    1, 1,
    0, 1,
  ]);
  const unitIndices = new Uint16Array([0, 1, 2, 0, 2, 3]);

  gl.bindVertexArray(vao);

  gl.bindBuffer(gl.ARRAY_BUFFER, unitVertexBuffer);
  gl.bufferData(gl.ARRAY_BUFFER, unitVertices, gl.STATIC_DRAW);
  gl.enableVertexAttribArray(0);
  gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 2 * 4, 0);
  gl.vertexAttribDivisor(0, 0);

  gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, unitIndexBuffer);
  gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, unitIndices, gl.STATIC_DRAW);

  gl.bindBuffer(gl.ARRAY_BUFFER, instanceBuffer);
  const layout = instancedSpriteAttributeViews(
    buildInstancedSpriteBatch(
      {
        frame() {
          throw new Error("internal layout probe should not resolve frames");
        },
      },
      [],
    ),
  );
  for (const attribute of layout.attributes) {
    gl.enableVertexAttribArray(attribute.location);
    gl.vertexAttribPointer(
      attribute.location,
      attribute.size,
      gl.FLOAT,
      false,
      layout.strideBytes,
      attribute.offsetBytes,
    );
    gl.vertexAttribDivisor(attribute.location, attribute.divisor);
  }

  gl.bindVertexArray(null);
  gl.bindBuffer(gl.ARRAY_BUFFER, null);

  const viewportLocation = gl.getUniformLocation(program, "uViewportSize");
  const textureLocation = gl.getUniformLocation(program, "uTexture");
  if (viewportLocation == null || textureLocation == null) {
    gl.deleteVertexArray(vao);
    gl.deleteBuffer(unitVertexBuffer);
    gl.deleteBuffer(unitIndexBuffer);
    gl.deleteBuffer(instanceBuffer);
    gl.deleteProgram(program);
    throw new Error("WebGL2 sprite renderer required uniforms not found");
  }

  let disposed = false;
  let uploadedCapacityBytes = 0;

  function assertActive() {
    if (disposed) {
      throw new Error("WebGL2 sprite renderer is disposed");
    }
  }

  function renderBatch(batch, texture, viewportWidth, viewportHeight) {
    assertActive();
    if (!batch || !(batch.instances instanceof Float32Array)) {
      throw new Error("instanced sprite batch required");
    }
    if (!(viewportWidth > 0) || !(viewportHeight > 0)) {
      throw new Error("viewport dimensions must be > 0");
    }
    if (!texture) {
      throw new Error("WebGL texture is required");
    }
    if (batch.instanceCount === 0) {
      return { drawCalls: 0, instances: 0, uploadedBytes: 0 };
    }

    if (alphaBlending) {
      gl.enable(gl.BLEND);
      gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
    }
    gl.useProgram(program);
    gl.bindVertexArray(vao);
    gl.bindBuffer(gl.ARRAY_BUFFER, instanceBuffer);

    if (batch.instances.byteLength > uploadedCapacityBytes) {
      gl.bufferData(gl.ARRAY_BUFFER, batch.instances, gl.DYNAMIC_DRAW);
      uploadedCapacityBytes = batch.instances.byteLength;
    } else {
      gl.bufferSubData(gl.ARRAY_BUFFER, 0, batch.instances);
    }

    gl.uniform2f(viewportLocation, viewportWidth, viewportHeight);
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, texture);
    gl.uniform1i(textureLocation, 0);

    gl.drawElementsInstanced(
      gl.TRIANGLES,
      6,
      gl.UNSIGNED_SHORT,
      0,
      batch.instanceCount,
    );

    gl.bindVertexArray(null);

    return {
      drawCalls: 1,
      instances: batch.instanceCount,
      uploadedBytes: batch.instances.byteLength,
    };
  }

  function renderPageBatches(pageBatches, viewportWidth, viewportHeight) {
    assertActive();
    if (!pageBatches || !Array.isArray(pageBatches.batches)) {
      throw new Error("texture-page batches required");
    }
    let drawCalls = 0;
    let instances = 0;
    let uploadedBytes = 0;

    for (const entry of pageBatches.batches) {
      if (!entry.batch || !(entry.batch.instances instanceof Float32Array)) {
        throw new Error("instanced texture-page batches required");
      }
      const texture = resolveTexture(entry.texture, entry);
      if (!texture) {
        throw new Error(`WebGL texture could not be resolved for page ${entry.pageId}`);
      }
      const result = renderBatch(
        entry.batch,
        texture,
        viewportWidth,
        viewportHeight,
      );
      drawCalls += result.drawCalls;
      instances += result.instances;
      uploadedBytes += result.uploadedBytes;
    }

    return {
      drawCalls,
      instances,
      uploadedBytes,
      textureSwitches: Math.max(0, drawCalls - 1),
    };
  }

  function dispose() {
    if (disposed) return;
    disposed = true;
    gl.deleteVertexArray(vao);
    gl.deleteBuffer(unitVertexBuffer);
    gl.deleteBuffer(unitIndexBuffer);
    gl.deleteBuffer(instanceBuffer);
    gl.deleteProgram(program);
  }

  return {
    program,
    vao,
    unitVertexBuffer,
    unitIndexBuffer,
    instanceBuffer,
    renderBatch,
    renderPageBatches,
    dispose,
    get disposed() {
      return disposed;
    },
    get uploadedCapacityBytes() {
      return uploadedCapacityBytes;
    },
    get alphaBlending() {
      return alphaBlending;
    },
  };
}


export function createWebGL2TextureCache(gl, options = {}) {
  if (!gl || typeof gl.createTexture !== "function") {
    throw new Error("WebGL2 texture-capable context required");
  }

  const entries = new Map();
  const pending = new Map();
  let disposed = false;

  const defaults = {
    minFilter: options.minFilter ?? gl.LINEAR,
    magFilter: options.magFilter ?? gl.LINEAR,
    wrapS: options.wrapS ?? gl.CLAMP_TO_EDGE,
    wrapT: options.wrapT ?? gl.CLAMP_TO_EDGE,
    generateMipmap: options.generateMipmap ?? false,
    premultiplyAlpha: options.premultiplyAlpha ?? false,
  };

  function assertActive() {
    if (disposed) {
      throw new Error("WebGL2 texture cache is disposed");
    }
  }

  function createTextureFromSource(source, textureOptions = {}) {
    assertActive();
    if (!source) {
      throw new Error("texture source is required");
    }

    const texture = gl.createTexture();
    if (!texture) {
      throw new Error("WebGL2 texture allocation failed");
    }

    const minFilter = textureOptions.minFilter ?? defaults.minFilter;
    const magFilter = textureOptions.magFilter ?? defaults.magFilter;
    const wrapS = textureOptions.wrapS ?? defaults.wrapS;
    const wrapT = textureOptions.wrapT ?? defaults.wrapT;
    const generateMipmap =
      textureOptions.generateMipmap ?? defaults.generateMipmap;
    const premultiplyAlpha =
      textureOptions.premultiplyAlpha ?? defaults.premultiplyAlpha;

    try {
      gl.bindTexture(gl.TEXTURE_2D, texture);
      gl.pixelStorei(
        gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL,
        premultiplyAlpha ? 1 : 0,
      );
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, minFilter);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, magFilter);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, wrapS);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, wrapT);
      gl.texImage2D(
        gl.TEXTURE_2D,
        0,
        gl.RGBA,
        gl.RGBA,
        gl.UNSIGNED_BYTE,
        source,
      );
      if (generateMipmap) {
        gl.generateMipmap(gl.TEXTURE_2D);
      }
    } catch (error) {
      gl.deleteTexture(texture);
      throw error;
    } finally {
      gl.bindTexture(gl.TEXTURE_2D, null);
    }

    return texture;
  }

  function acquire(key, source, textureOptions = {}) {
    assertActive();
    if (
      (typeof key !== "string" && typeof key !== "number") ||
      key === ""
    ) {
      throw new Error("texture cache key must be a non-empty string or number");
    }

    const existing = entries.get(key);
    if (existing) {
      existing.references += 1;
      return existing.texture;
    }

    const texture = createTextureFromSource(source, textureOptions);
    entries.set(key, {
      key,
      texture,
      references: 1,
      source,
      options: { ...textureOptions },
    });
    return texture;
  }

  async function load(key, sourceOrFactory, textureOptions = {}) {
    assertActive();
    if (entries.has(key)) {
      entries.get(key).references += 1;
      return entries.get(key).texture;
    }
    if (pending.has(key)) {
      const texture = await pending.get(key);
      const entry = entries.get(key);
      if (!entry) {
        throw new Error(`texture cache load completed without entry for ${key}`);
      }
      entry.references += 1;
      return texture;
    }

    const promise = (async () => {
      const source =
        typeof sourceOrFactory === "function"
          ? await sourceOrFactory(key)
          : await sourceOrFactory;
      assertActive();
      const texture = createTextureFromSource(source, textureOptions);
      entries.set(key, {
        key,
        texture,
        references: 1,
        source,
        options: { ...textureOptions },
      });
      return texture;
    })();

    pending.set(key, promise);
    try {
      return await promise;
    } finally {
      pending.delete(key);
    }
  }

  function get(key) {
    assertActive();
    return entries.get(key)?.texture ?? null;
  }

  function has(key) {
    assertActive();
    return entries.has(key);
  }

  function references(key) {
    assertActive();
    return entries.get(key)?.references ?? 0;
  }

  function release(key) {
    assertActive();
    const entry = entries.get(key);
    if (!entry) {
      return false;
    }
    entry.references -= 1;
    if (entry.references <= 0) {
      gl.deleteTexture(entry.texture);
      entries.delete(key);
      return true;
    }
    return false;
  }

  function deleteTexture(key) {
    assertActive();
    const entry = entries.get(key);
    if (!entry) {
      return false;
    }
    gl.deleteTexture(entry.texture);
    entries.delete(key);
    return true;
  }

  function clear() {
    assertActive();
    for (const entry of entries.values()) {
      gl.deleteTexture(entry.texture);
    }
    entries.clear();
  }

  function dispose() {
    if (disposed) return;
    for (const entry of entries.values()) {
      gl.deleteTexture(entry.texture);
    }
    entries.clear();
    pending.clear();
    disposed = true;
  }

  return {
    acquire,
    load,
    get,
    has,
    references,
    release,
    delete: deleteTexture,
    clear,
    dispose,
    get size() {
      return entries.size;
    },
    get pendingCount() {
      return pending.size;
    },
    get disposed() {
      return disposed;
    },
    defaults: { ...defaults },
  };
}


export async function loadImageBitmapSource(url, options = {}) {
  if (typeof url !== "string" || url.length === 0) {
    throw new Error("image URL must be a non-empty string");
  }

  const fetchImpl = options.fetchImpl ?? globalThis.fetch;
  const createImageBitmapImpl =
    options.createImageBitmapImpl ?? globalThis.createImageBitmap;

  if (typeof fetchImpl !== "function") {
    throw new Error("fetch implementation is required");
  }
  if (typeof createImageBitmapImpl !== "function") {
    throw new Error("createImageBitmap implementation is required");
  }

  const response = await fetchImpl(url, options.fetchOptions);
  if (!response || !response.ok) {
    const status = response?.status ?? "unknown";
    throw new Error(`image fetch failed for ${url}: HTTP ${status}`);
  }

  const blob = await response.blob();
  return createImageBitmapImpl(blob, options.imageBitmapOptions);
}

export async function preloadRuntimeAtlasPageTextures(
  atlasPages,
  textureCache,
  options = {},
) {
  if (!atlasPages || !Array.isArray(atlasPages.pages)) {
    throw new Error("runtime atlas page catalogue required");
  }
  if (!textureCache || typeof textureCache.load !== "function") {
    throw new Error("WebGL2 texture cache with load() required");
  }

  const resolveUrl =
    typeof options.resolveUrl === "function"
      ? options.resolveUrl
      : (textureKey) => textureKey;

  const loaded = [];
  try {
    for (const page of atlasPages.pages) {
      const textureKey = page.texture;
      const url = resolveUrl(textureKey, page);
      if (typeof url !== "string" || url.length === 0) {
        throw new Error(`texture URL could not be resolved for page ${page.id}`);
      }

      const texture = await textureCache.load(
        textureKey,
        () =>
          loadImageBitmapSource(url, {
            fetchImpl: options.fetchImpl,
            fetchOptions: options.fetchOptions,
            createImageBitmapImpl: options.createImageBitmapImpl,
            imageBitmapOptions: options.imageBitmapOptions,
          }),
        options.textureOptions,
      );

      loaded.push({
        pageId: page.id,
        textureKey,
        texture,
      });
    }
  } catch (error) {
    for (let index = loaded.length - 1; index >= 0; index -= 1) {
      textureCache.release(loaded[index].textureKey);
    }
    throw error;
  }

  return {
    count: loaded.length,
    pages: loaded,
  };
}

export function releaseRuntimeAtlasPageTextures(textureCache, preloadResult) {
  if (!textureCache || typeof textureCache.release !== "function") {
    throw new Error("WebGL2 texture cache with release() required");
  }
  if (!preloadResult || !Array.isArray(preloadResult.pages)) {
    throw new Error("runtime atlas preload result required");
  }

  let deleted = 0;
  for (const page of preloadResult.pages) {
    if (textureCache.release(page.textureKey)) {
      deleted += 1;
    }
  }
  return {
    released: preloadResult.pages.length,
    deleted,
  };
}

export async function createWebGL2RuntimeAtlasScene(
  gl,
  pageDefinitions,
  options = {},
) {
  if (!Array.isArray(pageDefinitions) || pageDefinitions.length === 0) {
    throw new Error("pageDefinitions must be a non-empty array");
  }

  const pages = createRuntimeAtlasPages(pageDefinitions);
  const textureCache =
    options.textureCache ??
    createWebGL2TextureCache(gl, options.textureCacheOptions);
  const ownsTextureCache = !options.textureCache;

  let preloadResult;
  let renderer;
  try {
    preloadResult = await preloadRuntimeAtlasPageTextures(
      pages,
      textureCache,
      options.loaderOptions,
    );

    renderer = createInstancedSpriteRendererWebGL2(gl, {
      ...options.rendererOptions,
      resolveTexture(textureKey) {
        const texture = textureCache.get(textureKey);
        if (!texture) {
          throw new Error(`texture not loaded: ${textureKey}`);
        }
        return texture;
      },
    });
  } catch (error) {
    if (preloadResult) {
      releaseRuntimeAtlasPageTextures(textureCache, preloadResult);
    }
    if (ownsTextureCache) {
      textureCache.dispose();
    }
    throw error;
  }

  let disposed = false;

  return {
    pages,
    textureCache,
    renderer,
    buildBatches(instances, batchOptions = {}) {
      if (disposed) {
        throw new Error("runtime atlas scene is disposed");
      }
      const {
        viewport,
        culling,
        sort = false,
        sortKey,
        sortDirection,
        ...textureBatchOptions
      } = batchOptions;
      const prepared = prepareSpriteSceneInstances(pages, instances, {
        viewport,
        culling,
        sort,
        sortKey,
        sortDirection,
      });
      const batches = buildTexturePageBatches(pages, prepared.instances, {
        mode: "instanced",
        ...textureBatchOptions,
      });
      return {
        ...batches,
        scenePreparation: prepared,
      };
    },
    render(instancesOrBatches, viewportWidth, viewportHeight, batchOptions = {}) {
      if (disposed) {
        throw new Error("runtime atlas scene is disposed");
      }
      const batches = Array.isArray(instancesOrBatches)
        ? this.buildBatches(instancesOrBatches, batchOptions)
        : instancesOrBatches;
      return renderer.renderPageBatches(
        batches,
        viewportWidth,
        viewportHeight,
      );
    },
    dispose() {
      if (disposed) return;
      disposed = true;
      renderer.dispose();
      releaseRuntimeAtlasPageTextures(textureCache, preloadResult);
      if (ownsTextureCache) {
        textureCache.dispose();
      }
    },
    get disposed() {
      return disposed;
    },
  };
}


export function spriteInstanceBounds(atlasPages, instance) {
  if (!atlasPages || typeof atlasPages.page !== "function") {
    throw new Error("runtime atlas page catalogue required");
  }
  if (!instance || typeof instance !== "object") {
    throw new Error("sprite instance must be an object");
  }
  const page = atlasPages.page(instance.page);
  const frame = page.atlas.frame(instance.frame);
  const x = instance.x ?? 0;
  const y = instance.y ?? 0;
  const scaleX = instance.scaleX ?? instance.scale ?? 1;
  const scaleY = instance.scaleY ?? instance.scale ?? 1;
  const rotation = instance.rotation ?? 0;
  const pivotX = instance.pivotX ?? 0;
  const pivotY = instance.pivotY ?? 0;

  for (const [name, value] of Object.entries({
    x, y, scaleX, scaleY, rotation, pivotX, pivotY,
  })) {
    if (!Number.isFinite(value)) {
      throw new Error(`sprite instance ${name} must be finite`);
    }
  }
  if (scaleX <= 0 || scaleY <= 0) {
    throw new Error("sprite instance scale must be > 0");
  }

  const logicalWidth = frame.sourceSize.width * scaleX;
  const logicalHeight = frame.sourceSize.height * scaleY;
  const visibleX = x + frame.trimOffset.x * scaleX;
  const visibleY = y + frame.trimOffset.y * scaleY;
  const visibleWidth = frame.sourceRegion.width * scaleX;
  const visibleHeight = frame.sourceRegion.height * scaleY;
  const pivotWorldX = x + pivotX * scaleX;
  const pivotWorldY = y + pivotY * scaleY;

  function rotatedAabb(rx, ry, rw, rh) {
    if (rotation === 0) {
      return { x: rx, y: ry, width: rw, height: rh };
    }
    const cos = Math.cos(rotation);
    const sin = Math.sin(rotation);
    const corners = [
      [rx, ry],
      [rx + rw, ry],
      [rx + rw, ry + rh],
      [rx, ry + rh],
    ].map(([cx, cy]) => {
      const dx = cx - pivotWorldX;
      const dy = cy - pivotWorldY;
      return [
        pivotWorldX + dx * cos - dy * sin,
        pivotWorldY + dx * sin + dy * cos,
      ];
    });
    const xs = corners.map(([cx]) => cx);
    const ys = corners.map(([, cy]) => cy);
    const minX = Math.min(...xs);
    const maxX = Math.max(...xs);
    const minY = Math.min(...ys);
    const maxY = Math.max(...ys);
    return {
      x: minX,
      y: minY,
      width: maxX - minX,
      height: maxY - minY,
    };
  }

  const logical = rotatedAabb(x, y, logicalWidth, logicalHeight);
  const visible = rotatedAabb(
    visibleX,
    visibleY,
    visibleWidth,
    visibleHeight,
  );

  return {
    x: logical.x,
    y: logical.y,
    width: logical.width,
    height: logical.height,
    visibleX: visible.x,
    visibleY: visible.y,
    visibleWidth: visible.width,
    visibleHeight: visible.height,
    rotation,
    pivotWorldX,
    pivotWorldY,
  };
}

export function cullSpriteInstances(
  atlasPages,
  instances,
  viewport,
  options = {},
) {
  if (!Array.isArray(instances)) {
    throw new Error("sprite instances must be an array");
  }
  if (!viewport || typeof viewport !== "object") {
    throw new Error("viewport must be an object");
  }

  const x = viewport.x ?? 0;
  const y = viewport.y ?? 0;
  const width = viewport.width;
  const height = viewport.height;
  const padding = options.padding ?? 0;
  const useVisibleBounds = options.useVisibleBounds ?? true;

  for (const [name, value] of Object.entries({ x, y, width, height, padding })) {
    if (!Number.isFinite(value)) {
      throw new Error(`viewport ${name} must be finite`);
    }
  }
  if (width < 0 || height < 0) {
    throw new Error("viewport width/height must be >= 0");
  }
  if (padding < 0) {
    throw new Error("viewport padding must be >= 0");
  }
  if (typeof useVisibleBounds !== "boolean") {
    throw new Error("useVisibleBounds must be boolean");
  }

  const left = x - padding;
  const top = y - padding;
  const right = x + width + padding;
  const bottom = y + height + padding;

  const visible = [];
  const culledIndices = [];

  for (let index = 0; index < instances.length; index += 1) {
    const instance = instances[index];
    const bounds = spriteInstanceBounds(atlasPages, instance);
    const bx = useVisibleBounds ? bounds.visibleX : bounds.x;
    const by = useVisibleBounds ? bounds.visibleY : bounds.y;
    const bw = useVisibleBounds ? bounds.visibleWidth : bounds.width;
    const bh = useVisibleBounds ? bounds.visibleHeight : bounds.height;
    const intersects =
      bx + bw > left &&
      by + bh > top &&
      bx < right &&
      by < bottom;

    if (intersects) {
      visible.push(instance);
    } else {
      culledIndices.push(index);
    }
  }

  return {
    instances: visible,
    inputCount: instances.length,
    visibleCount: visible.length,
    culledCount: culledIndices.length,
    culledIndices,
    viewport: { x, y, width, height, padding, useVisibleBounds },
  };
}

export function stableSortSpriteInstances(instances, options = {}) {
  if (!Array.isArray(instances)) {
    throw new Error("sprite instances must be an array");
  }

  const key = options.key ?? "z";
  const direction = options.direction ?? "ascending";
  if (typeof key !== "string" || key.length === 0) {
    throw new Error("sort key must be a non-empty string");
  }
  if (direction !== "ascending" && direction !== "descending") {
    throw new Error("sort direction must be ascending or descending");
  }

  const multiplier = direction === "ascending" ? 1 : -1;
  const decorated = instances.map((instance, index) => {
    const value = instance?.[key] ?? 0;
    if (!Number.isFinite(value)) {
      throw new Error(`sprite sort value ${key} must be finite`);
    }
    return { instance, index, value };
  });

  decorated.sort((a, b) => {
    const delta = (a.value - b.value) * multiplier;
    return delta || a.index - b.index;
  });

  return decorated.map((entry) => entry.instance);
}

export function prepareSpriteSceneInstances(
  atlasPages,
  instances,
  options = {},
) {
  if (!Array.isArray(instances)) {
    throw new Error("sprite instances must be an array");
  }

  let prepared = instances;
  let culling = null;

  if (options.viewport) {
    culling = cullSpriteInstances(
      atlasPages,
      prepared,
      options.viewport,
      options.culling,
    );
    prepared = culling.instances;
  }

  if (options.sort !== false) {
    prepared = stableSortSpriteInstances(prepared, {
      key: options.sortKey ?? "z",
      direction: options.sortDirection ?? "ascending",
    });
  }

  return {
    instances: prepared,
    inputCount: instances.length,
    outputCount: prepared.length,
    culledCount: culling?.culledCount ?? 0,
    culling,
  };
}


export function resizeWebGL2Canvas(canvas, gl, options = {}) {
  if (!canvas || !gl || typeof gl.viewport !== "function") {
    throw new Error("canvas and WebGL2 context with viewport() are required");
  }

  const cssWidth = options.cssWidth ?? canvas.clientWidth ?? canvas.width;
  const cssHeight = options.cssHeight ?? canvas.clientHeight ?? canvas.height;
  const pixelRatio = options.pixelRatio ?? globalThis.devicePixelRatio ?? 1;
  const maxPixelRatio = options.maxPixelRatio ?? 3;

  for (const [name, value] of Object.entries({
    cssWidth,
    cssHeight,
    pixelRatio,
    maxPixelRatio,
  })) {
    if (!Number.isFinite(value) || value < 0) {
      throw new Error(`${name} must be a finite value >= 0`);
    }
  }
  if (maxPixelRatio <= 0) {
    throw new Error("maxPixelRatio must be > 0");
  }

  const effectivePixelRatio = Math.min(pixelRatio, maxPixelRatio);
  const width = Math.max(1, Math.round(cssWidth * effectivePixelRatio));
  const height = Math.max(1, Math.round(cssHeight * effectivePixelRatio));
  const resized = canvas.width !== width || canvas.height !== height;

  if (resized) {
    canvas.width = width;
    canvas.height = height;
  }
  gl.viewport(0, 0, width, height);

  return {
    resized,
    cssWidth,
    cssHeight,
    pixelRatio: effectivePixelRatio,
    width,
    height,
  };
}

export async function createWebGL2CanvasRuntime(
  canvas,
  pageDefinitions,
  options = {},
) {
  if (!canvas || typeof canvas.getContext !== "function") {
    throw new Error("canvas with getContext() is required");
  }

  const contextAttributes = options.contextAttributes;
  const getContext =
    typeof options.getContext === "function"
      ? options.getContext
      : () => canvas.getContext("webgl2", contextAttributes);
  const onContextLost =
    typeof options.onContextLost === "function" ? options.onContextLost : null;
  const onContextRestored =
    typeof options.onContextRestored === "function"
      ? options.onContextRestored
      : null;

  let gl = getContext();
  if (!gl) {
    throw new Error("WebGL2 context could not be created");
  }

  let scene = await createWebGL2RuntimeAtlasScene(
    gl,
    pageDefinitions,
    options.sceneOptions,
  );
  const entityStore =
    options.entityStore ?? createSpriteEntityStore(options.entityStoreOptions);
  const animationSystem =
    options.animationSystem ??
    createSpriteAnimationSystem(
      scene.pages,
      entityStore,
      options.animationOptions,
    );
  let visibilityMask = options.visibilityMask ?? 0xffffffff;
  if (
    !Number.isInteger(visibilityMask) ||
    visibilityMask < 0 ||
    visibilityMask > 0xffffffff
  ) {
    throw new Error("visibilityMask must be an unsigned 32-bit integer");
  }
  visibilityMask >>>= 0;
  let camera = {
    x: options.camera?.x ?? 0,
    y: options.camera?.y ?? 0,
    zoom: options.camera?.zoom ?? 1,
  };
  applyCameraToSpriteInstances([], camera);
  const cameraController =
    options.cameraController ??
    createCamera2DController(camera, options.cameraControllerOptions);
  let worldBounds = options.worldBounds
    ? { ...options.worldBounds }
    : null;
  if (worldBounds) {
    clampCameraToWorldBounds(
      camera,
      worldBounds,
      canvas.width ?? 0,
      canvas.height ?? 0,
    );
  }
  let contextLost = false;
  let disposed = false;
  let restorePromise = null;

  function assertActive() {
    if (disposed) {
      throw new Error("WebGL2 canvas runtime is disposed");
    }
  }

  function resize(resizeOptions = {}) {
    assertActive();
    return resizeWebGL2Canvas(canvas, gl, {
      ...options.resizeOptions,
      ...resizeOptions,
    });
  }

  function clampRuntimeCamera(nextCamera) {
    if (!worldBounds) {
      return { ...nextCamera };
    }
    const size = resize();
    return clampCameraToWorldBounds(
      nextCamera,
      worldBounds,
      size.width,
      size.height,
    );
  }

  function pickRuntimeEntity(x, y, pickOptions = {}) {
    const {
      all = false,
      useVisibleBounds = false,
      ...batchOptions
    } = pickOptions;
    const prepared = buildSpriteEntityInstances(entityStore, {
      visibilityMask,
      camera,
      ...batchOptions,
    });
    return pickSpriteInstances(
      scene.pages,
      prepared.instances,
      x,
      y,
      { all, useVisibleBounds },
    );
  }

  const pointerOptions = options.pointerOptions ?? {};
  const autoDragEntities = pointerOptions.autoDragEntities ?? false;
  if (typeof autoDragEntities !== "boolean") {
    throw new Error("autoDragEntities must be boolean");
  }
  const dragAxis = pointerOptions.dragAxis ?? "both";
  if (!["both", "x", "y"].includes(dragAxis)) {
    throw new Error("dragAxis must be both, x, or y");
  }
  const dragGridSize = pointerOptions.dragGridSize ?? 0;
  if (!Number.isFinite(dragGridSize) || dragGridSize < 0) {
    throw new Error("dragGridSize must be a finite value >= 0");
  }
  const dragBounds =
    pointerOptions.dragBounds === undefined
      ? null
      : pointerOptions.dragBounds;
  const dragSelection = pointerOptions.dragSelection ?? false;
  if (typeof dragSelection !== "boolean") {
    throw new Error("dragSelection must be boolean");
  }
  const userOnDrag =
    typeof pointerOptions.onDrag === "function"
      ? pointerOptions.onDrag
      : null;
  const {
    autoDragEntities: _autoDragEntities,
    dragAxis: _dragAxis,
    dragGridSize: _dragGridSize,
    dragBounds: _dragBounds,
    dragSelection: _dragSelection,
    onDrag: _onDrag,
    ...pointerControllerOptions
  } = pointerOptions;

  const selection =
    options.selectionModel ??
    createSpriteSelectionModel(options.selectionOptions);
  const historyOptions = options.historyOptions ?? {};
  const history =
    options.entityHistory ??
    createSpriteEntityHistory(entityStore, {
      ...historyOptions,
      captureContext:
        historyOptions.captureContext ??
        (() => selection.snapshot().ids),
      restoreContext:
        historyOptions.restoreContext ??
        ((ids) => selection.set(
          Array.isArray(ids)
            ? ids.filter((id) => entityStore.has(id))
            : [],
        )),
    });
  const autoHistory = options.autoHistory !== false;

  function recordRuntimeEdit(label, callback) {
    if (!autoHistory || history.active === true) {
      return callback();
    }
    return history.record(label, callback);
  }

  const clipboard =
    options.clipboardController ??
    createSpriteClipboardController(
      entityStore,
      selection,
      options.clipboardOptions,
    );

  const pointerInteractions = createSpritePointerInteractionController({
    ...pointerControllerOptions,
    pick: pickRuntimeEntity,
    toWorld: (x, y) => screenToWorldPoint(x, y, camera),
    onDrag(event) {
      if (
        autoDragEntities &&
        event.capturedEntityId != null
      ) {
        const zoom = camera.zoom;
        const moveOptions = {
          axis: dragAxis,
          gridSize: dragGridSize,
          bounds: dragBounds ?? worldBounds,
        };
        if (
          dragSelection &&
          selection.has(event.capturedEntityId) &&
          selection.size > 1
        ) {
          event.draggedSelection = moveSelectedSpriteEntitiesByWorldDelta(
            entityStore,
            selection,
            event.dx / zoom,
            event.dy / zoom,
            moveOptions,
          );
        } else {
          event.draggedEntity = moveSpriteEntityByWorldDelta(
            entityStore,
            event.capturedEntityId,
            event.dx / zoom,
            event.dy / zoom,
            moveOptions,
          );
        }
      }
      userOnDrag?.(event);
    },
  });

  async function rebuildAfterContextRestore() {
    assertActive();
    const restoredGl = getContext();
    if (!restoredGl) {
      throw new Error("WebGL2 context could not be restored");
    }

    const oldScene = scene;
    gl = restoredGl;
    scene = await createWebGL2RuntimeAtlasScene(
      gl,
      pageDefinitions,
      options.sceneOptions,
    );
    oldScene.dispose();
    contextLost = false;
    resize();
    onContextRestored?.({ gl, scene });
    return scene;
  }

  function handleContextLost(event) {
    if (disposed) return;
    event?.preventDefault?.();
    contextLost = true;
    onContextLost?.({ event, gl, scene });
  }

  function handleContextRestored() {
    if (disposed) return;
    restorePromise = rebuildAfterContextRestore().finally(() => {
      restorePromise = null;
    });
    restorePromise.catch(() => {});
  }

  canvas.addEventListener?.("webglcontextlost", handleContextLost);
  canvas.addEventListener?.("webglcontextrestored", handleContextRestored);

  if (options.resizeOnCreate !== false) {
    resize();
  }

  return {
    entities: entityStore,
    animations: animationSystem,
    history,
    clipboard,
    get visibilityMask() {
      return visibilityMask;
    },
    setVisibilityMask(nextMask) {
      assertActive();
      if (
        !Number.isInteger(nextMask) ||
        nextMask < 0 ||
        nextMask > 0xffffffff
      ) {
        throw new Error("visibilityMask must be an unsigned 32-bit integer");
      }
      visibilityMask = nextMask >>> 0;
      return visibilityMask;
    },
    get camera() {
      return { ...camera };
    },
    get worldBounds() {
      return worldBounds ? { ...worldBounds } : null;
    },
    cameraController,
    setWorldBounds(nextBounds) {
      assertActive();
      if (nextBounds == null) {
        worldBounds = null;
        return null;
      }
      const candidate = { ...nextBounds };
      camera = clampCameraToWorldBounds(
        camera,
        candidate,
        canvas.width ?? 0,
        canvas.height ?? 0,
      );
      worldBounds = candidate;
      cameraController.setCamera(camera);
      return { ...worldBounds };
    },
    setCamera(nextCamera = {}) {
      assertActive();
      const candidate = {
        x: nextCamera.x ?? camera.x,
        y: nextCamera.y ?? camera.y,
        zoom: nextCamera.zoom ?? camera.zoom,
      };
      applyCameraToSpriteInstances([], candidate);
      camera = clampRuntimeCamera(candidate);
      cameraController.setCamera(camera);
      return { ...camera };
    },
    updateCameraFollow(targetX, targetY, deltaSeconds) {
      assertActive();
      const nextCamera = cameraController.update(
        targetX,
        targetY,
        deltaSeconds,
      );
      camera = clampRuntimeCamera(nextCamera);
      cameraController.setCamera(camera);
      return { ...camera };
    },
    updateCameraFollowEntity(entityId, deltaSeconds, followOptions = {}) {
      assertActive();
      const resolved = resolveSpriteEntityHierarchy(entityStore, {
        includeDisabled: true,
      });
      const entity = resolved.byId.get(entityId);
      if (!entity) {
        throw new Error(`sprite entity not found: ${entityId}`);
      }
      const offsetX = followOptions.offsetX ?? 0;
      const offsetY = followOptions.offsetY ?? 0;
      for (const [name, value] of Object.entries({ offsetX, offsetY })) {
        if (!Number.isFinite(value)) {
          throw new Error(`${name} must be finite`);
        }
      }
      return this.updateCameraFollow(
        entity.x + offsetX,
        entity.y + offsetY,
        deltaSeconds,
      );
    },
    shakeCamera(amplitude, durationSeconds, frequency) {
      assertActive();
      cameraController.setCamera(camera);
      const nextCamera = cameraController.shake(
        amplitude,
        durationSeconds,
        frequency,
      );
      camera = clampRuntimeCamera(nextCamera);
      return { ...camera };
    },
    clearCameraShake() {
      assertActive();
      camera = clampRuntimeCamera(cameraController.clearShake());
      cameraController.setCamera(camera);
      return { ...camera };
    },
    get gl() {
      return gl;
    },
    get scene() {
      return scene;
    },
    get contextLost() {
      return contextLost;
    },
    get restoring() {
      return restorePromise !== null;
    },
    resize,
    async waitForRestore() {
      assertActive();
      if (restorePromise) {
        await restorePromise;
      }
      return scene;
    },
    buildBatches(instances, batchOptions = {}) {
      assertActive();
      if (contextLost) {
        throw new Error("WebGL2 context is lost");
      }
      return scene.buildBatches(instances, batchOptions);
    },
    buildEntityBatches(batchOptions = {}) {
      assertActive();
      if (contextLost) {
        throw new Error("WebGL2 context is lost");
      }
      const prepared = buildSpriteEntityInstances(entityStore, {
        visibilityMask,
        camera,
        ...batchOptions,
      });
      return scene.buildBatches(
        prepared.instances,
        prepared.sceneBatchOptions,
      );
    },
    updateAnimations(deltaSeconds) {
      assertActive();
      return animationSystem.update(deltaSeconds);
    },
    render(instancesOrBatches, batchOptions = {}) {
      assertActive();
      if (contextLost) {
        throw new Error("WebGL2 context is lost");
      }
      const size = resize();
      return scene.render(
        instancesOrBatches,
        size.width,
        size.height,
        batchOptions,
      );
    },
    renderEntities(batchOptions = {}) {
      assertActive();
      if (contextLost) {
        throw new Error("WebGL2 context is lost");
      }
      const size = resize();
      const prepared = buildSpriteEntityInstances(entityStore, {
        visibilityMask,
        camera,
        ...batchOptions,
      });
      return scene.render(
        prepared.instances,
        size.width,
        size.height,
        prepared.sceneBatchOptions,
      );
    },
    screenToWorld(x, y) {
      assertActive();
      return screenToWorldPoint(x, y, camera);
    },
    worldToScreen(x, y, parallax = {}) {
      assertActive();
      return worldToScreenPoint(x, y, camera, parallax);
    },
    pickEntity(x, y, pickOptions = {}) {
      assertActive();
      return pickRuntimeEntity(x, y, pickOptions);
    },
    pointerInteractions,
    selection,
    selectEntity(entityId, selectOptions = {}) {
      assertActive();
      if (!entityStore.has(entityId)) {
        throw new Error(`sprite entity not found: ${entityId}`);
      }
      return selection.select(entityId, selectOptions);
    },
    clearSelection() {
      assertActive();
      return selection.clear();
    },
    duplicateSelection(duplicateOptions = {}) {
      assertActive();
      return recordRuntimeEdit(
        "duplicate selection",
        () => clipboard.duplicate(duplicateOptions),
      );
    },
    cutSelection(cutOptions = {}) {
      assertActive();
      return recordRuntimeEdit(
        "cut selection",
        () => clipboard.cut(cutOptions),
      );
    },
    pasteClipboard(pasteOptions = {}) {
      assertActive();
      return recordRuntimeEdit(
        "paste clipboard",
        () => clipboard.paste(pasteOptions),
      );
    },
    copySelection(copyOptions = {}) {
      assertActive();
      return copySpriteEntities(
        entityStore,
        selection.snapshot().ids,
        copyOptions,
      );
    },
    pasteEntities(clipboard, pasteOptions = {}) {
      assertActive();
      return recordRuntimeEdit("paste entities", () => {
        const result = pasteSpriteEntities(
          entityStore,
          clipboard,
          pasteOptions,
        );
        selection.set(result.ids);
        return result;
      });
    },
    reparentEntity(entityId, parentId = null, reparentOptions = {}) {
      assertActive();
      return recordRuntimeEdit(
        "reparent entity",
        () => reparentSpriteEntity(
          entityStore,
          entityId,
          parentId,
          reparentOptions,
        ),
      );
    },
    removeEntity(entityId, removeOptions = {}) {
      assertActive();
      return recordRuntimeEdit("remove entity", () => {
        const result = removeSpriteEntityHierarchy(
          entityStore,
          entityId,
          removeOptions,
        );
        for (const id of result.removedIds) selection.remove(id);
        return result;
      });
    },
    removeSelection(removeOptions = {}) {
      assertActive();
      return recordRuntimeEdit("remove selection", () => {
        const ids = selection.snapshot().ids;
        const removed = new Set();
        for (const id of ids) {
          if (!entityStore.has(id)) continue;
          const result = removeSpriteEntityHierarchy(
            entityStore,
            id,
            removeOptions,
          );
          for (const removedId of result.removedIds) removed.add(removedId);
        }
        for (const id of removed) selection.remove(id);
        return { removedIds: [...removed], count: removed.size };
      });
    },
    undo() {
      assertActive();
      const result = history.undo();
      if (result) {
        const liveIds = new Set(
          entityStore.snapshot({ includeDisabled: true }).map((entity) => entity.id),
        );
        selection.set(selection.snapshot().ids.filter((id) => liveIds.has(id)));
      }
      return result;
    },
    redo() {
      assertActive();
      const result = history.redo();
      if (result) {
        const liveIds = new Set(
          entityStore.snapshot({ includeDisabled: true }).map((entity) => entity.id),
        );
        selection.set(selection.snapshot().ids.filter((id) => liveIds.has(id)));
      }
      return result;
    },
    selectEntitiesInRect(rect, selectOptions = {}) {
      assertActive();
      const {
        additive = false,
        mode = "intersect",
        ...batchOptions
      } = selectOptions;
      if (typeof additive !== "boolean") {
        throw new Error("selection additive must be boolean");
      }
      const prepared = buildSpriteEntityInstances(entityStore, {
        visibilityMask,
        camera,
        ...batchOptions,
      });
      const hits = selectSpriteInstancesInRect(
        scene.pages,
        prepared.instances,
        rect,
        { mode },
      );
      const ids = hits
        .map((hit) => hit.instance.id)
        .filter((id) => id != null);
      if (additive) {
        for (const id of ids) {
          selection.select(id, { additive: true });
        }
        return selection.snapshot();
      }
      return selection.set(ids);
    },
    moveEntityByWorldDelta(entityId, deltaX, deltaY, moveOptions = {}) {
      assertActive();
      return recordRuntimeEdit(
        "move entity",
        () => moveSpriteEntityByWorldDelta(
          entityStore,
          entityId,
          deltaX,
          deltaY,
          moveOptions,
        ),
      );
    },
    transformSelection(transformOptions = {}) {
      assertActive();
      return recordRuntimeEdit(
        "transform selection",
        () => transformSelectedSpriteEntities(
          entityStore,
          selection,
          transformOptions,
        ),
      );
    },
    selectionHandles(handleOptions = {}) {
      assertActive();
      return selectionTransformHandleGeometry(
        entityStore,
        selection,
        handleOptions,
      );
    },
    dragSelectionHandle(
      handle,
      startPoint,
      currentPoint,
      handleOptions = {},
    ) {
      assertActive();
      return recordRuntimeEdit(
        "drag selection handle",
        () => applySelectionTransformHandleDrag(
          entityStore,
          selection,
          handle,
          startPoint,
          currentPoint,
          handleOptions,
        ),
      );
    },
    moveSelectionByWorldDelta(deltaX, deltaY, moveOptions = {}) {
      assertActive();
      return recordRuntimeEdit(
        "move selection",
        () => moveSelectedSpriteEntitiesByWorldDelta(
          entityStore,
          selection,
          deltaX,
          deltaY,
          moveOptions,
        ),
      );
    },
    pointerMove(pointerId, x, y, pickOptions = {}) {
      assertActive();
      return pointerInteractions.move(pointerId, x, y, pickOptions);
    },
    pointerDown(pointerId, x, y, pickOptions = {}) {
      assertActive();
      return pointerInteractions.down(pointerId, x, y, pickOptions);
    },
    pointerUp(pointerId, x, y, pickOptions = {}) {
      assertActive();
      return pointerInteractions.up(pointerId, x, y, pickOptions);
    },
    pointerCancel(pointerId) {
      assertActive();
      return pointerInteractions.cancel(pointerId);
    },
    async restore() {
      assertActive();
      if (!restorePromise) {
        restorePromise = rebuildAfterContextRestore().finally(() => {
          restorePromise = null;
        });
      }
      return restorePromise;
    },
    dispose() {
      if (disposed) return;
      disposed = true;
      canvas.removeEventListener?.("webglcontextlost", handleContextLost);
      canvas.removeEventListener?.("webglcontextrestored", handleContextRestored);
      pointerInteractions.clear();
      scene.dispose();
    },
    get disposed() {
      return disposed;
    },
  };
}


export function createSpriteEntityStore(options = {}) {
  const entities = new Map();
  let nextNumericId = options.startId ?? 1;
  let version = 0;

  if (!Number.isInteger(nextNumericId) || nextNumericId < 1) {
    throw new Error("startId must be a positive integer");
  }

  function normalizeId(id) {
    if (
      (typeof id !== "string" && typeof id !== "number") ||
      id === ""
    ) {
      throw new Error("sprite entity id must be a non-empty string or number");
    }
    return id;
  }

  function validateEntity(entity, label = "sprite entity") {
    if (!entity || typeof entity !== "object") {
      throw new Error(`${label} must be an object`);
    }
    if (typeof entity.page !== "string" || entity.page.length === 0) {
      throw new Error(`${label}.page must be a non-empty string`);
    }
    if (
      typeof entity.frame !== "string" &&
      typeof entity.frame !== "number"
    ) {
      throw new Error(`${label}.frame must be a string or number`);
    }

    if (
      entity.parent != null &&
      typeof entity.parent !== "string" &&
      typeof entity.parent !== "number"
    ) {
      throw new Error(`${label}.parent must be a string, number, or null`);
    }
    if (entity.parent === "") {
      throw new Error(`${label}.parent must not be an empty string`);
    }

    for (const field of [
      "x",
      "y",
      "z",
      "scale",
      "scaleX",
      "scaleY",
      "rotation",
      "pivotX",
      "pivotY",
      "alpha",
      "tintR",
      "tintG",
      "tintB",
      "parallaxX",
      "parallaxY",
    ]) {
      if (entity[field] != null && !Number.isFinite(entity[field])) {
        throw new Error(`${label}.${field} must be finite`);
      }
    }
    const sx = entity.scaleX ?? entity.scale ?? 1;
    const sy = entity.scaleY ?? entity.scale ?? 1;
    if (!(sx > 0) || !(sy > 0)) {
      throw new Error(`${label} scale must be > 0`);
    }
    for (const field of ["alpha", "tintR", "tintG", "tintB"]) {
      const value = entity[field];
      if (value != null && (value < 0 || value > 1)) {
        throw new Error(`${label}.${field} must be between 0 and 1`);
      }
    }
    if (
      entity.layerMask != null &&
      (!Number.isInteger(entity.layerMask) ||
        entity.layerMask < 0 ||
        entity.layerMask > 0xffffffff)
    ) {
      throw new Error(`${label}.layerMask must be an unsigned 32-bit integer`);
    }
    for (const field of ["parallaxX", "parallaxY"]) {
      const value = entity[field];
      if (value != null && value < 0) {
        throw new Error(`${label}.${field} must be >= 0`);
      }
    }
  }

  function cloneEntity(entity) {
    return { ...entity };
  }

  function add(entity) {
    validateEntity(entity);
    const requestedId = entity.id;
    const id =
      requestedId == null ? nextNumericId++ : normalizeId(requestedId);
    if (entities.has(id)) {
      throw new Error(`sprite entity already exists: ${id}`);
    }

    const stored = cloneEntity({ ...entity, id });
    entities.set(id, stored);
    version += 1;
    return cloneEntity(stored);
  }

  function get(id) {
    const stored = entities.get(normalizeId(id));
    return stored ? cloneEntity(stored) : null;
  }

  function has(id) {
    return entities.has(normalizeId(id));
  }

  function update(id, patch) {
    id = normalizeId(id);
    const current = entities.get(id);
    if (!current) {
      throw new Error(`sprite entity not found: ${id}`);
    }
    if (!patch || typeof patch !== "object") {
      throw new Error("sprite entity patch must be an object");
    }
    if ("id" in patch && patch.id !== id) {
      throw new Error("sprite entity id cannot be changed");
    }

    const next = { ...current, ...patch, id };
    validateEntity(next);
    entities.set(id, next);
    version += 1;
    return cloneEntity(next);
  }

  function remove(id) {
    id = normalizeId(id);
    const existing = entities.get(id);
    if (!existing) {
      return null;
    }
    entities.delete(id);
    version += 1;
    return cloneEntity(existing);
  }

  function clear() {
    if (entities.size === 0) {
      return 0;
    }
    const count = entities.size;
    entities.clear();
    version += 1;
    return count;
  }

  function snapshot(options = {}) {
    const includeDisabled = options.includeDisabled ?? false;
    if (typeof includeDisabled !== "boolean") {
      throw new Error("includeDisabled must be boolean");
    }

    const result = [];
    for (const entity of entities.values()) {
      if (!includeDisabled && entity.enabled === false) {
        continue;
      }
      result.push(cloneEntity(entity));
    }
    return result;
  }

  function instances(options = {}) {
    return snapshot(options).map((entity) => {
      const { enabled, ...instance } = entity;
      return instance;
    });
  }

  function transact(callback) {
    if (typeof callback !== "function") {
      throw new Error("sprite entity transaction callback required");
    }

    const before = new Map(
      Array.from(entities.entries(), ([id, entity]) => [id, cloneEntity(entity)]),
    );
    const beforeNextId = nextNumericId;
    const beforeVersion = version;

    try {
      return callback({
        add,
        get,
        has,
        update,
        remove,
      });
    } catch (error) {
      entities.clear();
      for (const [id, entity] of before) {
        entities.set(id, entity);
      }
      nextNumericId = beforeNextId;
      version = beforeVersion;
      throw error;
    }
  }

  return {
    add,
    get,
    has,
    update,
    remove,
    clear,
    snapshot,
    instances,
    transact,
    get size() {
      return entities.size;
    },
    get version() {
      return version;
    },
  };
}


export function duplicateSpriteEntities(
  entityStore,
  entityIds,
  options = {},
) {
  if (!Array.isArray(entityIds)) {
    throw new Error("duplicate entity ids must be an array");
  }
  const offsetX = options.offsetX ?? 16;
  const offsetY = options.offsetY ?? 16;
  if (!Number.isFinite(offsetX) || !Number.isFinite(offsetY)) {
    throw new Error("duplicate offsets must be finite");
  }
  const includeDescendants = options.includeDescendants ?? false;
  if (typeof includeDescendants !== "boolean") {
    throw new Error("includeDescendants must be boolean");
  }

  const snapshot = entityStore.snapshot({ includeDisabled: true });
  const byId = new Map(snapshot.map((entity) => [entity.id, entity]));
  const selected = new Set(entityIds);
  for (const id of selected) {
    if (!byId.has(id)) throw new Error(`sprite entity not found: ${id}`);
  }

  if (includeDescendants) {
    let changed = true;
    while (changed) {
      changed = false;
      for (const entity of snapshot) {
        if (
          entity.parent != null &&
          selected.has(entity.parent) &&
          !selected.has(entity.id)
        ) {
          selected.add(entity.id);
          changed = true;
        }
      }
    }
  }

  const ordered = snapshot.filter((entity) => selected.has(entity.id));
  const idMap = new Map();
  const created = [];

  entityStore.transact(({ add }) => {
    for (const source of ordered) {
      const copy = { ...source };
      delete copy.id;
      const parentWasCopied =
        source.parent != null && selected.has(source.parent);
      if (!parentWasCopied) {
        copy.x = (copy.x ?? 0) + offsetX;
        copy.y = (copy.y ?? 0) + offsetY;
      }
      const createdEntity = add(copy);
      idMap.set(source.id, createdEntity.id);
      created.push(createdEntity);
    }
    for (let index = 0; index < ordered.length; index += 1) {
      const source = ordered[index];
      if (source.parent != null && idMap.has(source.parent)) {
        created[index] = entityStore.update(created[index].id, {
          parent: idMap.get(source.parent),
        });
      }
    }
  });

  return {
    entities: created,
    ids: created.map((entity) => entity.id),
    idMap,
    count: created.length,
  };
}

export function copySpriteEntities(
  entityStore,
  entityIds,
  options = {},
) {
  if (!Array.isArray(entityIds)) {
    throw new Error("copy entity ids must be an array");
  }
  const includeDescendants = options.includeDescendants ?? false;
  if (typeof includeDescendants !== "boolean") {
    throw new Error("includeDescendants must be boolean");
  }
  const snapshot = entityStore.snapshot({ includeDisabled: true });
  const byId = new Map(snapshot.map((entity) => [entity.id, entity]));
  const selected = new Set(entityIds);
  for (const id of selected) {
    if (!byId.has(id)) throw new Error(`sprite entity not found: ${id}`);
  }
  if (includeDescendants) {
    let changed = true;
    while (changed) {
      changed = false;
      for (const entity of snapshot) {
        if (entity.parent != null && selected.has(entity.parent) && !selected.has(entity.id)) {
          selected.add(entity.id);
          changed = true;
        }
      }
    }
  }
  const entities = snapshot
    .filter((entity) => selected.has(entity.id))
    .map((entity) => ({ ...entity }));
  return {
    format: "asset-forge-sprite-clipboard",
    version: 1,
    entities,
  };
}

export function pasteSpriteEntities(
  entityStore,
  clipboard,
  options = {},
) {
  if (
    !clipboard ||
    clipboard.format !== "asset-forge-sprite-clipboard" ||
    clipboard.version !== 1 ||
    !Array.isArray(clipboard.entities)
  ) {
    throw new Error("invalid sprite entity clipboard");
  }
  const offsetX = options.offsetX ?? 16;
  const offsetY = options.offsetY ?? 16;
  if (!Number.isFinite(offsetX) || !Number.isFinite(offsetY)) {
    throw new Error("paste offsets must be finite");
  }
  const sourceIds = new Set(clipboard.entities.map((entity) => entity.id));
  const idMap = new Map();
  const created = [];
  entityStore.transact(({ add }) => {
    for (const source of clipboard.entities) {
      const copy = { ...source };
      delete copy.id;
      const parentIsInternal =
        source.parent != null && sourceIds.has(source.parent);
      if (!parentIsInternal) {
        copy.parent =
          source.parent != null && entityStore.has(source.parent)
            ? source.parent
            : null;
        copy.x = (copy.x ?? 0) + offsetX;
        copy.y = (copy.y ?? 0) + offsetY;
      } else {
        copy.parent = null;
      }
      const entity = add(copy);
      idMap.set(source.id, entity.id);
      created.push(entity);
    }
    for (let index = 0; index < clipboard.entities.length; index += 1) {
      const source = clipboard.entities[index];
      if (source.parent != null && idMap.has(source.parent)) {
        created[index] = entityStore.update(created[index].id, {
          parent: idMap.get(source.parent),
        });
      }
    }
  });
  return {
    entities: created,
    ids: created.map((entity) => entity.id),
    idMap,
    count: created.length,
  };
}


export function reparentSpriteEntity(
  entityStore,
  entityId,
  parentId = null,
  options = {},
) {
  const keepWorldTransform = options.keepWorldTransform ?? true;
  if (typeof keepWorldTransform !== "boolean") {
    throw new Error("keepWorldTransform must be boolean");
  }
  const entity = entityStore.get(entityId);
  if (!entity) throw new Error(`sprite entity not found: ${entityId}`);
  if (parentId === entityId) {
    throw new Error("sprite entity cannot parent itself");
  }
  if (parentId != null && !entityStore.has(parentId)) {
    throw new Error(`sprite entity parent not found: ${parentId}`);
  }

  const before = resolveSpriteEntityHierarchy(entityStore, {
    includeDisabled: true,
  });
  const world = before.byId.get(entityId);
  if (parentId != null) {
    let cursor = before.byId.get(parentId);
    while (cursor) {
      if (cursor.id === entityId) {
        throw new Error("sprite entity reparent would create a cycle");
      }
      cursor = cursor.parent == null ? null : before.byId.get(cursor.parent);
    }
  }

  if (!keepWorldTransform) {
    return entityStore.update(entityId, { parent: parentId });
  }

  let x = world.x;
  let y = world.y;
  let z = world.z;
  let rotation = world.rotation;
  let scaleX = world.scaleX;
  let scaleY = world.scaleY;

  if (parentId != null) {
    const parent = before.byId.get(parentId);
    const dx = world.x - parent.x;
    const dy = world.y - parent.y;
    const cos = Math.cos(-parent.rotation);
    const sin = Math.sin(-parent.rotation);
    x = (dx * cos - dy * sin) / parent.scaleX;
    y = (dx * sin + dy * cos) / parent.scaleY;
    z = world.z - parent.z;
    rotation = world.rotation - parent.rotation;
    scaleX = world.scaleX / parent.scaleX;
    scaleY = world.scaleY / parent.scaleY;
  }

  return entityStore.update(entityId, {
    parent: parentId,
    x,
    y,
    z,
    rotation,
    scaleX,
    scaleY,
  });
}

export function removeSpriteEntityHierarchy(
  entityStore,
  entityId,
  options = {},
) {
  const childPolicy = options.childPolicy ?? "detach";
  if (!["detach", "cascade", "reject"].includes(childPolicy)) {
    throw new Error("childPolicy must be detach, cascade, or reject");
  }
  if (!entityStore.has(entityId)) return { removedIds: [], count: 0 };

  const snapshot = entityStore.snapshot({ includeDisabled: true });
  const children = new Map();
  for (const entity of snapshot) {
    if (entity.parent != null) {
      const list = children.get(entity.parent) ?? [];
      list.push(entity.id);
      children.set(entity.parent, list);
    }
  }
  const directChildren = children.get(entityId) ?? [];
  if (childPolicy === "reject" && directChildren.length > 0) {
    throw new Error(`sprite entity has children: ${entityId}`);
  }

  const removedIds = [];
  entityStore.transact(({ remove }) => {
    if (childPolicy === "cascade") {
      const visit = (id) => {
        for (const childId of children.get(id) ?? []) visit(childId);
        if (remove(id)) removedIds.push(id);
      };
      visit(entityId);
      return;
    }
    if (childPolicy === "detach") {
      for (const childId of directChildren) {
        reparentSpriteEntity(entityStore, childId, null, {
          keepWorldTransform: true,
        });
      }
    }
    if (remove(entityId)) removedIds.push(entityId);
  });
  return { removedIds, count: removedIds.length };
}


export function createSpriteEntityHistory(
  entityStore,
  options = {},
) {
  if (
    !entityStore ||
    typeof entityStore.snapshot !== "function" ||
    typeof entityStore.transact !== "function"
  ) {
    throw new Error("sprite entity store with snapshot/transact required");
  }
  const maxEntries = options.maxEntries ?? 100;
  if (!Number.isInteger(maxEntries) || maxEntries <= 0) {
    throw new Error("history maxEntries must be a positive integer");
  }

  const captureContext = options.captureContext ?? null;
  const restoreContext = options.restoreContext ?? null;
  if (
    captureContext !== null &&
    typeof captureContext !== "function"
  ) {
    throw new Error("history captureContext must be a function");
  }
  if (
    restoreContext !== null &&
    typeof restoreContext !== "function"
  ) {
    throw new Error("history restoreContext must be a function");
  }
  if ((captureContext === null) !== (restoreContext === null)) {
    throw new Error(
      "history captureContext and restoreContext must be provided together",
    );
  }

  const undoStack = [];
  const redoStack = [];
  let pending = null;

  const capture = () => entityStore.snapshot({ includeDisabled: true });
  const captureExtra = () =>
    captureContext === null ? undefined : captureContext();

  function sameValue(a, b) {
    return JSON.stringify(a) === JSON.stringify(b);
  }

  function restore(snapshot, context) {
    const wanted = new Map(snapshot.map((entity) => [entity.id, entity]));
    entityStore.transact(({ add, update, remove }) => {
      for (const current of entityStore.snapshot({ includeDisabled: true })) {
        if (!wanted.has(current.id)) remove(current.id);
      }
      for (const entity of snapshot) {
        if (entityStore.has(entity.id)) update(entity.id, entity);
        else add(entity);
      }
    });
    if (restoreContext !== null) {
      restoreContext(context);
    }
    return capture();
  }

  function push(entry) {
    if (
      sameValue(entry.before, entry.after) &&
      sameValue(entry.beforeContext, entry.afterContext)
    ) {
      return false;
    }
    undoStack.push(entry);
    while (undoStack.length > maxEntries) undoStack.shift();
    redoStack.length = 0;
    return true;
  }

  return {
    begin(label = "edit") {
      if (pending) throw new Error("sprite entity history edit already active");
      pending = {
        label,
        before: capture(),
        beforeContext: captureExtra(),
      };
      return pending.before;
    },
    commit() {
      if (!pending) throw new Error("sprite entity history edit not active");
      const entry = {
        ...pending,
        after: capture(),
        afterContext: captureExtra(),
      };
      pending = null;
      return push(entry);
    },
    cancel() {
      if (!pending) return false;
      const entry = pending;
      pending = null;
      restore(entry.before, entry.beforeContext);
      return true;
    },
    record(label, callback) {
      if (typeof callback !== "function") {
        throw new Error("sprite entity history callback required");
      }
      this.begin(label);
      try {
        const result = callback();
        if (result && typeof result.then === "function") {
          this.cancel();
          throw new Error("sprite entity history callbacks must be synchronous");
        }
        this.commit();
        return result;
      } catch (error) {
        if (pending) this.cancel();
        throw error;
      }
    },
    undo() {
      if (pending) throw new Error("cannot undo during active history edit");
      const entry = undoStack.at(-1);
      if (!entry) return null;
      restore(entry.before, entry.beforeContext);
      undoStack.pop();
      redoStack.push(entry);
      return {
        label: entry.label,
        snapshot: capture(),
        context: captureExtra(),
      };
    },
    redo() {
      if (pending) throw new Error("cannot redo during active history edit");
      const entry = redoStack.at(-1);
      if (!entry) return null;
      restore(entry.after, entry.afterContext);
      redoStack.pop();
      undoStack.push(entry);
      return {
        label: entry.label,
        snapshot: capture(),
        context: captureExtra(),
      };
    },
    clear() {
      const count = undoStack.length + redoStack.length;
      undoStack.length = 0;
      redoStack.length = 0;
      pending = null;
      return count;
    },
    get canUndo() { return undoStack.length > 0; },
    get canRedo() { return redoStack.length > 0; },
    get undoCount() { return undoStack.length; },
    get redoCount() { return redoStack.length; },
    get active() { return pending !== null; },
  };
}


export function createSpriteAnimationSystem(
  atlasPages,
  entityStore,
  options = {},
) {
  if (!atlasPages || typeof atlasPages.page !== "function") {
    throw new Error("runtime atlas page catalogue required");
  }
  if (
    !entityStore ||
    typeof entityStore.get !== "function" ||
    typeof entityStore.update !== "function"
  ) {
    throw new Error("sprite entity store required");
  }

  const bindings = new Map();
  const onEvent =
    typeof options.onEvent === "function" ? options.onEvent : null;
  const onFinish =
    typeof options.onFinish === "function" ? options.onFinish : null;
  const onLoop =
    typeof options.onLoop === "function" ? options.onLoop : null;
  const onFrame =
    typeof options.onFrame === "function" ? options.onFrame : null;

  function ensureEntity(entityId) {
    const entity = entityStore.get(entityId);
    if (!entity) {
      throw new Error(`sprite entity not found: ${entityId}`);
    }
    return entity;
  }

  function bind(entityId, animationName, bindOptions = {}) {
    const entity = ensureEntity(entityId);
    if (typeof animationName !== "string" || animationName.length === 0) {
      throw new Error("animationName must be a non-empty string");
    }

    const pageId = bindOptions.page ?? entity.page;
    const page = atlasPages.page(pageId);
    page.atlas.animation(animationName);

    if (bindings.has(entityId)) {
      bindings.delete(entityId);
    }

    let binding;
    const player = createAnimationPlayer(page.atlas, animationName, {
      autoplay: bindOptions.autoplay ?? true,
      startTime: bindOptions.startTime ?? 0,
      playbackRate: bindOptions.playbackRate ?? 1,
      onFrame(sample) {
        const current = entityStore.get(entityId);
        if (!current) return;
        const nextFrame = sample.frame.index;
        const patch = {};
        if (current.frame !== nextFrame) patch.frame = nextFrame;
        if (current.page !== pageId) patch.page = pageId;
        if (Object.keys(patch).length > 0) {
          entityStore.update(entityId, patch);
        }
        onFrame?.({
          entityId,
          pageId,
          animationName,
          sample,
          binding,
        });
        bindOptions.onFrame?.(sample);
      },
      onEvent(event) {
        const payload = {
          entityId,
          pageId,
          animationName,
          ...event,
        };
        onEvent?.(payload);
        bindOptions.onEvent?.(payload);
      },
      onLoop(event) {
        const payload = {
          entityId,
          pageId,
          animationName,
          ...event,
        };
        onLoop?.(payload);
        bindOptions.onLoop?.(payload);
      },
      onFinish(sample) {
        const payload = {
          entityId,
          pageId,
          animationName,
          sample,
        };
        onFinish?.(payload);
        bindOptions.onFinish?.(payload);
      },
    });

    binding = {
      entityId,
      pageId,
      animationName,
      player,
      get playing() {
        return player.playing;
      },
      get timeSeconds() {
        return player.timeSeconds;
      },
      play() {
        return player.play();
      },
      pause() {
        return player.pause();
      },
      seek(timeSeconds) {
        return player.seek(timeSeconds);
      },
      setPlaybackRate(rate) {
        return player.setPlaybackRate(rate);
      },
      sample() {
        return player.sample();
      },
    };

    bindings.set(entityId, binding);
    player.sample();
    return binding;
  }

  function get(entityId) {
    return bindings.get(entityId) ?? null;
  }

  function unbind(entityId) {
    const binding = bindings.get(entityId);
    if (!binding) return null;
    bindings.delete(entityId);
    return binding;
  }

  function update(deltaSeconds) {
    if (!Number.isFinite(deltaSeconds) || deltaSeconds < 0) {
      throw new Error("deltaSeconds must be a finite value >= 0");
    }

    const samples = [];
    const removedEntityIds = [];
    for (const [entityId, binding] of bindings) {
      if (!entityStore.has(entityId)) {
        bindings.delete(entityId);
        removedEntityIds.push(entityId);
        continue;
      }
      samples.push({
        entityId,
        sample: binding.player.update(deltaSeconds),
      });
    }

    return {
      bindingCount: bindings.size,
      updatedCount: samples.length,
      removedEntityIds,
      samples,
    };
  }

  function clear() {
    const count = bindings.size;
    bindings.clear();
    return count;
  }

  return {
    bind,
    get,
    unbind,
    update,
    clear,
    get size() {
      return bindings.size;
    },
  };
}


function _stableSceneCacheKey(value, seen = new Set()) {
  if (value === null) return "null";
  const type = typeof value;
  if (type === "string") return JSON.stringify(value);
  if (type === "number" || type === "boolean") {
    if (type === "number" && !Number.isFinite(value)) {
      throw new Error("scene cache options must contain only finite numbers");
    }
    return JSON.stringify(value);
  }
  if (type === "undefined") return "undefined";
  if (type !== "object") {
    throw new Error("scene cache options must be JSON-like data");
  }
  if (seen.has(value)) {
    throw new Error("scene cache options must not be circular");
  }
  seen.add(value);
  try {
    if (Array.isArray(value)) {
      return `[${value.map((entry) => _stableSceneCacheKey(entry, seen)).join(",")}]`;
    }
    const keys = Object.keys(value).sort();
    return `{${keys
      .map(
        (key) =>
          `${JSON.stringify(key)}:${_stableSceneCacheKey(value[key], seen)}`,
      )
      .join(",")}}`;
  } finally {
    seen.delete(value);
  }
}

export function createSpriteEntityBatchCache(
  runtimeScene,
  entityStore,
  options = {},
) {
  if (!runtimeScene || typeof runtimeScene.buildBatches !== "function") {
    throw new Error("runtime atlas scene with buildBatches() required");
  }
  if (
    !entityStore ||
    typeof entityStore.instances !== "function" ||
    !Number.isInteger(entityStore.version)
  ) {
    throw new Error("sprite entity store with version required");
  }

  const maxEntries = options.maxEntries ?? 8;
  if (!Number.isInteger(maxEntries) || maxEntries <= 0) {
    throw new Error("maxEntries must be a positive integer");
  }

  const entries = new Map();
  let cachedVersion = entityStore.version;
  let hits = 0;
  let misses = 0;
  let invalidations = 0;

  function invalidate() {
    const removed = entries.size;
    entries.clear();
    cachedVersion = entityStore.version;
    if (removed > 0) {
      invalidations += 1;
    }
    return removed;
  }

  function ensureVersion() {
    if (cachedVersion !== entityStore.version) {
      invalidate();
    }
  }

  function build(batchOptions = {}) {
    ensureVersion();
    const key = _stableSceneCacheKey(batchOptions);
    const existing = entries.get(key);
    if (existing) {
      entries.delete(key);
      entries.set(key, existing);
      hits += 1;
      return {
        batches: existing,
        cacheHit: true,
        entityVersion: cachedVersion,
        cacheKey: key,
      };
    }

    misses += 1;
    const prepared = buildSpriteEntityInstances(
      entityStore,
      batchOptions,
    );
    const batches = runtimeScene.buildBatches(
      prepared.instances,
      prepared.sceneBatchOptions,
    );
    entries.set(key, batches);

    while (entries.size > maxEntries) {
      const oldestKey = entries.keys().next().value;
      entries.delete(oldestKey);
    }

    return {
      batches,
      cacheHit: false,
      entityVersion: cachedVersion,
      cacheKey: key,
    };
  }

  function clear() {
    return invalidate();
  }

  return {
    build,
    invalidate: clear,
    get size() {
      ensureVersion();
      return entries.size;
    },
    get stats() {
      ensureVersion();
      return {
        hits,
        misses,
        invalidations,
        entries: entries.size,
        entityVersion: cachedVersion,
        maxEntries,
      };
    },
  };
}


export function resolveSpriteEntityHierarchy(entityStore, options = {}) {
  if (
    !entityStore ||
    typeof entityStore.snapshot !== "function"
  ) {
    throw new Error("sprite entity store required");
  }

  const includeDisabled = options.includeDisabled ?? false;
  const inheritDisabled = options.inheritDisabled ?? true;
  const allowMissingParents = options.allowMissingParents ?? false;
  for (const [name, value] of Object.entries({
    includeDisabled,
    inheritDisabled,
    allowMissingParents,
  })) {
    if (typeof value !== "boolean") {
      throw new Error(`${name} must be boolean`);
    }
  }

  const snapshot = entityStore.snapshot({ includeDisabled: true });
  const byId = new Map(snapshot.map((entity) => [entity.id, entity]));
  const resolved = new Map();
  const visiting = new Set();

  function resolve(entity) {
    if (resolved.has(entity.id)) {
      return resolved.get(entity.id);
    }
    if (visiting.has(entity.id)) {
      throw new Error(`sprite entity hierarchy cycle detected at ${entity.id}`);
    }
    visiting.add(entity.id);

    const localScaleX = entity.scaleX ?? entity.scale ?? 1;
    const localScaleY = entity.scaleY ?? entity.scale ?? 1;
    const localX = entity.x ?? 0;
    const localY = entity.y ?? 0;
    const localZ = entity.z ?? 0;
    const localRotation = entity.rotation ?? 0;
    const localAlpha = entity.alpha ?? 1;
    const localTintR = entity.tintR ?? 1;
    const localTintG = entity.tintG ?? 1;
    const localTintB = entity.tintB ?? 1;

    let worldX = localX;
    let worldY = localY;
    let worldZ = localZ;
    let worldScaleX = localScaleX;
    let worldScaleY = localScaleY;
    let worldRotation = localRotation;
    let worldAlpha = localAlpha;
    let worldTintR = localTintR;
    let worldTintG = localTintG;
    let worldTintB = localTintB;
    let inheritedDisabled = false;

    if (entity.parent != null) {
      const parent = byId.get(entity.parent);
      if (!parent) {
        if (!allowMissingParents) {
          visiting.delete(entity.id);
          throw new Error(
            `sprite entity parent not found: ${entity.parent} for ${entity.id}`,
          );
        }
      } else {
        const parentWorld = resolve(parent);
        worldScaleX = parentWorld.scaleX * localScaleX;
        worldScaleY = parentWorld.scaleY * localScaleY;
        worldRotation = parentWorld.rotation + localRotation;
        worldAlpha = parentWorld.alpha * localAlpha;
        worldTintR = parentWorld.tintR * localTintR;
        worldTintG = parentWorld.tintG * localTintG;
        worldTintB = parentWorld.tintB * localTintB;
        const parentRotation = parentWorld.rotation;
        const scaledLocalX = localX * parentWorld.scaleX;
        const scaledLocalY = localY * parentWorld.scaleY;
        const cosParent = Math.cos(parentRotation);
        const sinParent = Math.sin(parentRotation);
        worldX =
          parentWorld.x +
          scaledLocalX * cosParent -
          scaledLocalY * sinParent;
        worldY =
          parentWorld.y +
          scaledLocalX * sinParent +
          scaledLocalY * cosParent;
        worldZ = parentWorld.z + localZ;
        inheritedDisabled =
          inheritDisabled &&
          (parentWorld.disabled === true || parent.enabled === false);
      }
    }

    const world = {
      ...entity,
      x: worldX,
      y: worldY,
      z: worldZ,
      scaleX: worldScaleX,
      scaleY: worldScaleY,
      rotation: worldRotation,
      alpha: worldAlpha,
      tintR: worldTintR,
      tintG: worldTintG,
      tintB: worldTintB,
      disabled: entity.enabled === false || inheritedDisabled,
    };
    delete world.scale;
    delete world.enabled;

    visiting.delete(entity.id);
    resolved.set(entity.id, world);
    return world;
  }

  const instances = [];
  for (const entity of snapshot) {
    const world = resolve(entity);
    if (!includeDisabled && world.disabled) {
      continue;
    }
    const instance = { ...world };
    delete instance.disabled;
    instances.push(instance);
  }

  return {
    instances,
    count: instances.length,
    totalCount: snapshot.length,
    disabledCount: snapshot.length - instances.length,
    byId: resolved,
  };
}

export function applyCameraToSpriteInstances(
  instances,
  camera = {},
) {
  if (!Array.isArray(instances)) {
    throw new Error("sprite instances must be an array");
  }
  if (!camera || typeof camera !== "object") {
    throw new Error("camera must be an object");
  }

  const x = camera.x ?? 0;
  const y = camera.y ?? 0;
  const zoom = camera.zoom ?? 1;
  for (const [name, value] of Object.entries({ x, y, zoom })) {
    if (!Number.isFinite(value)) {
      throw new Error(`camera ${name} must be finite`);
    }
  }
  if (!(zoom > 0)) {
    throw new Error("camera zoom must be > 0");
  }

  const transformed = instances.map((instance, index) => {
    if (!instance || typeof instance !== "object") {
      throw new Error(`sprite instance ${index} must be an object`);
    }
    const parallaxX = instance.parallaxX ?? 1;
    const parallaxY = instance.parallaxY ?? 1;
    if (!Number.isFinite(parallaxX) || parallaxX < 0) {
      throw new Error(`sprite instance ${index} parallaxX must be finite and >= 0`);
    }
    if (!Number.isFinite(parallaxY) || parallaxY < 0) {
      throw new Error(`sprite instance ${index} parallaxY must be finite and >= 0`);
    }

    const scaleX = (instance.scaleX ?? instance.scale ?? 1) * zoom;
    const scaleY = (instance.scaleY ?? instance.scale ?? 1) * zoom;
    return {
      ...instance,
      x: ((instance.x ?? 0) - x * parallaxX) * zoom,
      y: ((instance.y ?? 0) - y * parallaxY) * zoom,
      scaleX,
      scaleY,
      parallaxX,
      parallaxY,
    };
  });

  return {
    instances: transformed,
    count: transformed.length,
    camera: { x, y, zoom },
  };
}

export function filterSpriteInstancesByLayer(
  instances,
  visibilityMask = 0xffffffff,
) {
  if (!Array.isArray(instances)) {
    throw new Error("sprite instances must be an array");
  }
  if (
    !Number.isInteger(visibilityMask) ||
    visibilityMask < 0 ||
    visibilityMask > 0xffffffff
  ) {
    throw new Error("visibilityMask must be an unsigned 32-bit integer");
  }

  const mask = visibilityMask >>> 0;
  const visible = [];
  const filteredIndices = [];

  for (let index = 0; index < instances.length; index += 1) {
    const instance = instances[index];
    if (!instance || typeof instance !== "object") {
      throw new Error(`sprite instance ${index} must be an object`);
    }
    const layerMask = instance.layerMask ?? 1;
    if (
      !Number.isInteger(layerMask) ||
      layerMask < 0 ||
      layerMask > 0xffffffff
    ) {
      throw new Error(
        `sprite instance ${index} layerMask must be an unsigned 32-bit integer`,
      );
    }

    if (((layerMask >>> 0) & mask) !== 0) {
      visible.push(instance);
    } else {
      filteredIndices.push(index);
    }
  }

  return {
    instances: visible,
    inputCount: instances.length,
    visibleCount: visible.length,
    filteredCount: filteredIndices.length,
    filteredIndices,
    visibilityMask: mask,
  };
}

function _splitEntityHierarchyOptions(batchOptions = {}) {
  const {
    hierarchy = true,
    hierarchyOptions,
    visibilityMask = 0xffffffff,
    camera = null,
    ...sceneBatchOptions
  } = batchOptions;
  if (typeof hierarchy !== "boolean") {
    throw new Error("hierarchy must be boolean");
  }
  if (
    !Number.isInteger(visibilityMask) ||
    visibilityMask < 0 ||
    visibilityMask > 0xffffffff
  ) {
    throw new Error("visibilityMask must be an unsigned 32-bit integer");
  }
  return {
    hierarchy,
    hierarchyOptions,
    visibilityMask: visibilityMask >>> 0,
    camera,
    sceneBatchOptions,
  };
}

export function buildSpriteEntityInstances(entityStore, batchOptions = {}) {
  const {
    hierarchy,
    hierarchyOptions,
    visibilityMask,
    camera,
    sceneBatchOptions,
  } = _splitEntityHierarchyOptions(batchOptions);
  const sourceInstances = hierarchy
    ? resolveSpriteEntityHierarchy(entityStore, hierarchyOptions).instances
    : entityStore.instances();
  const layerFiltering = filterSpriteInstancesByLayer(
    sourceInstances,
    visibilityMask,
  );
  const cameraTransform = camera == null
    ? {
        instances: layerFiltering.instances,
        count: layerFiltering.instances.length,
        camera: null,
      }
    : applyCameraToSpriteInstances(layerFiltering.instances, camera);
  return {
    instances: cameraTransform.instances,
    layerFiltering,
    cameraTransform,
    sceneBatchOptions,
  };
}


export function clampCameraToWorldBounds(
  camera,
  worldBounds,
  viewportWidth,
  viewportHeight,
) {
  if (!camera || typeof camera !== "object") {
    throw new Error("camera must be an object");
  }
  if (!worldBounds || typeof worldBounds !== "object") {
    throw new Error("worldBounds must be an object");
  }

  const x = camera.x ?? 0;
  const y = camera.y ?? 0;
  const zoom = camera.zoom ?? 1;
  const boundsX = worldBounds.x ?? 0;
  const boundsY = worldBounds.y ?? 0;
  const boundsWidth = worldBounds.width;
  const boundsHeight = worldBounds.height;

  for (const [name, value] of Object.entries({
    x,
    y,
    zoom,
    boundsX,
    boundsY,
    boundsWidth,
    boundsHeight,
    viewportWidth,
    viewportHeight,
  })) {
    if (!Number.isFinite(value)) {
      throw new Error(`${name} must be finite`);
    }
  }
  if (!(zoom > 0)) {
    throw new Error("camera zoom must be > 0");
  }
  if (boundsWidth < 0 || boundsHeight < 0) {
    throw new Error("world bounds width/height must be >= 0");
  }
  if (viewportWidth < 0 || viewportHeight < 0) {
    throw new Error("viewport width/height must be >= 0");
  }

  const visibleWorldWidth = viewportWidth / zoom;
  const visibleWorldHeight = viewportHeight / zoom;

  function clampAxis(value, min, size, visibleSize) {
    const max = min + size - visibleSize;
    if (max < min) {
      return min + (size - visibleSize) / 2;
    }
    return Math.min(max, Math.max(min, value));
  }

  return {
    x: clampAxis(x, boundsX, boundsWidth, visibleWorldWidth),
    y: clampAxis(y, boundsY, boundsHeight, visibleWorldHeight),
    zoom,
  };
}

export function createCamera2DController(initialCamera = {}, options = {}) {
  let camera = {
    x: initialCamera.x ?? 0,
    y: initialCamera.y ?? 0,
    zoom: initialCamera.zoom ?? 1,
  };
  applyCameraToSpriteInstances([], camera);

  const deadZoneWidth = options.deadZoneWidth ?? 0;
  const deadZoneHeight = options.deadZoneHeight ?? 0;
  const smoothing = options.smoothing ?? 0;
  for (const [name, value] of Object.entries({
    deadZoneWidth,
    deadZoneHeight,
    smoothing,
  })) {
    if (!Number.isFinite(value) || value < 0) {
      throw new Error(`${name} must be a finite value >= 0`);
    }
  }

  let shakeTime = 0;
  let shakeDuration = 0;
  let shakeAmplitude = 0;
  let shakeFrequency = 24;
  let shakePhase = 0;

  function baseCamera() {
    return { ...camera };
  }

  function shakenCamera() {
    if (!(shakeTime < shakeDuration) || shakeAmplitude <= 0) {
      return baseCamera();
    }
    const remaining = 1 - shakeTime / shakeDuration;
    const amplitude = shakeAmplitude * remaining;
    const phase = shakePhase + shakeTime * shakeFrequency * Math.PI * 2;
    return {
      x: camera.x + Math.sin(phase) * amplitude,
      y: camera.y + Math.cos(phase * 1.61803398875) * amplitude,
      zoom: camera.zoom,
    };
  }

  function update(targetX, targetY, deltaSeconds) {
    for (const [name, value] of Object.entries({
      targetX,
      targetY,
      deltaSeconds,
    })) {
      if (!Number.isFinite(value)) {
        throw new Error(`${name} must be finite`);
      }
    }
    if (deltaSeconds < 0) {
      throw new Error("deltaSeconds must be >= 0");
    }

    const halfW = deadZoneWidth / 2;
    const halfH = deadZoneHeight / 2;
    let desiredX = camera.x;
    let desiredY = camera.y;

    if (targetX < camera.x - halfW) desiredX = targetX + halfW;
    else if (targetX > camera.x + halfW) desiredX = targetX - halfW;

    if (targetY < camera.y - halfH) desiredY = targetY + halfH;
    else if (targetY > camera.y + halfH) desiredY = targetY - halfH;

    if (smoothing > 0 && deltaSeconds > 0) {
      const alpha = 1 - Math.exp(-smoothing * deltaSeconds);
      camera.x += (desiredX - camera.x) * alpha;
      camera.y += (desiredY - camera.y) * alpha;
    } else {
      camera.x = desiredX;
      camera.y = desiredY;
    }

    shakeTime = Math.min(shakeDuration, shakeTime + deltaSeconds);
    return shakenCamera();
  }

  function setCamera(nextCamera = {}) {
    const candidate = {
      x: nextCamera.x ?? camera.x,
      y: nextCamera.y ?? camera.y,
      zoom: nextCamera.zoom ?? camera.zoom,
    };
    applyCameraToSpriteInstances([], candidate);
    camera = candidate;
    return baseCamera();
  }

  function shake(amplitude, durationSeconds, frequency = 24) {
    for (const [name, value] of Object.entries({
      amplitude,
      durationSeconds,
      frequency,
    })) {
      if (!Number.isFinite(value) || value < 0) {
        throw new Error(`${name} must be a finite value >= 0`);
      }
    }
    if (frequency === 0 && amplitude > 0 && durationSeconds > 0) {
      throw new Error("frequency must be > 0 when shake is active");
    }
    shakeAmplitude = amplitude;
    shakeDuration = durationSeconds;
    shakeFrequency = frequency || 24;
    shakeTime = 0;
    shakePhase += Math.PI / 7;
    return shakenCamera();
  }

  function clearShake() {
    shakeTime = shakeDuration;
    shakeAmplitude = 0;
    return baseCamera();
  }

  return {
    update,
    setCamera,
    shake,
    clearShake,
    get camera() {
      return shakenCamera();
    },
    get baseCamera() {
      return baseCamera();
    },
    get shaking() {
      return shakeTime < shakeDuration && shakeAmplitude > 0;
    },
  };
}


export function worldToScreenPoint(x, y, camera = {}, parallax = {}) {
  const cameraX = camera.x ?? 0;
  const cameraY = camera.y ?? 0;
  const zoom = camera.zoom ?? 1;
  const parallaxX = parallax.x ?? parallax.parallaxX ?? 1;
  const parallaxY = parallax.y ?? parallax.parallaxY ?? 1;
  for (const [name, value] of Object.entries({
    x, y, cameraX, cameraY, zoom, parallaxX, parallaxY,
  })) {
    if (!Number.isFinite(value)) {
      throw new Error(`${name} must be finite`);
    }
  }
  if (!(zoom > 0)) throw new Error("camera zoom must be > 0");
  if (parallaxX < 0 || parallaxY < 0) {
    throw new Error("parallax must be >= 0");
  }
  return {
    x: (x - cameraX * parallaxX) * zoom,
    y: (y - cameraY * parallaxY) * zoom,
  };
}

export function screenToWorldPoint(x, y, camera = {}) {
  const cameraX = camera.x ?? 0;
  const cameraY = camera.y ?? 0;
  const zoom = camera.zoom ?? 1;
  for (const [name, value] of Object.entries({
    x, y, cameraX, cameraY, zoom,
  })) {
    if (!Number.isFinite(value)) {
      throw new Error(`${name} must be finite`);
    }
  }
  if (!(zoom > 0)) throw new Error("camera zoom must be > 0");
  return {
    x: x / zoom + cameraX,
    y: y / zoom + cameraY,
  };
}

export function pointHitsSpriteInstance(
  atlasPages,
  instance,
  pointX,
  pointY,
  options = {},
) {
  if (!atlasPages || typeof atlasPages.page !== "function") {
    throw new Error("runtime atlas page catalogue required");
  }
  if (!instance || typeof instance !== "object") {
    throw new Error("sprite instance must be an object");
  }
  if (!Number.isFinite(pointX) || !Number.isFinite(pointY)) {
    throw new Error("hit-test point must be finite");
  }

  const useVisibleBounds = options.useVisibleBounds ?? false;
  if (typeof useVisibleBounds !== "boolean") {
    throw new Error("useVisibleBounds must be boolean");
  }

  const page = atlasPages.page(instance.page);
  const frame = page.atlas.frame(instance.frame);
  const x = instance.x ?? 0;
  const y = instance.y ?? 0;
  const scaleX = instance.scaleX ?? instance.scale ?? 1;
  const scaleY = instance.scaleY ?? instance.scale ?? 1;
  const rotation = instance.rotation ?? 0;
  const pivotX = instance.pivotX ?? 0;
  const pivotY = instance.pivotY ?? 0;

  for (const [name, value] of Object.entries({
    x, y, scaleX, scaleY, rotation, pivotX, pivotY,
  })) {
    if (!Number.isFinite(value)) {
      throw new Error(`sprite instance ${name} must be finite`);
    }
  }
  if (!(scaleX > 0) || !(scaleY > 0)) {
    throw new Error("sprite instance scale must be > 0");
  }

  const pivotWorldX = x + pivotX * scaleX;
  const pivotWorldY = y + pivotY * scaleY;
  const dx = pointX - pivotWorldX;
  const dy = pointY - pivotWorldY;
  const cos = Math.cos(-rotation);
  const sin = Math.sin(-rotation);
  const localPointX = pivotWorldX + dx * cos - dy * sin;
  const localPointY = pivotWorldY + dx * sin + dy * cos;

  const left = useVisibleBounds
    ? x + frame.trimOffset.x * scaleX
    : x;
  const top = useVisibleBounds
    ? y + frame.trimOffset.y * scaleY
    : y;
  const width = (useVisibleBounds
    ? frame.sourceRegion.width
    : frame.sourceSize.width) * scaleX;
  const height = (useVisibleBounds
    ? frame.sourceRegion.height
    : frame.sourceSize.height) * scaleY;

  const hit =
    localPointX >= left &&
    localPointX <= left + width &&
    localPointY >= top &&
    localPointY <= top + height;

  return {
    hit,
    localPointX,
    localPointY,
    bounds: { x: left, y: top, width, height },
  };
}

export function pickSpriteInstances(
  atlasPages,
  instances,
  pointX,
  pointY,
  options = {},
) {
  if (!Array.isArray(instances)) {
    throw new Error("sprite instances must be an array");
  }
  const all = options.all ?? false;
  if (typeof all !== "boolean") {
    throw new Error("all must be boolean");
  }

  const hits = [];
  for (let index = 0; index < instances.length; index += 1) {
    const instance = instances[index];
    const result = pointHitsSpriteInstance(
      atlasPages,
      instance,
      pointX,
      pointY,
      options,
    );
    if (!result.hit) continue;
    const z = instance.z ?? 0;
    if (!Number.isFinite(z)) {
      throw new Error(`sprite instance ${index} z must be finite`);
    }
    hits.push({
      instance,
      inputIndex: index,
      z,
      hit: result,
    });
  }

  hits.sort((a, b) => b.z - a.z || b.inputIndex - a.inputIndex);
  return all ? hits : (hits[0] ?? null);
}


export function moveSpriteEntityByWorldDelta(
  entityStore,
  entityId,
  deltaX,
  deltaY,
  options = {},
) {
  if (
    !entityStore ||
    typeof entityStore.get !== "function" ||
    typeof entityStore.update !== "function"
  ) {
    throw new Error("sprite entity store required");
  }
  if (!Number.isFinite(deltaX) || !Number.isFinite(deltaY)) {
    throw new Error("entity drag delta must be finite");
  }

  const axis = options.axis ?? "both";
  if (!["both", "x", "y"].includes(axis)) {
    throw new Error("drag axis must be both, x, or y");
  }
  if (axis === "x") deltaY = 0;
  if (axis === "y") deltaX = 0;

  const gridSize = options.gridSize ?? 0;
  if (!Number.isFinite(gridSize) || gridSize < 0) {
    throw new Error("gridSize must be a finite value >= 0");
  }

  const bounds = options.bounds ?? null;
  if (bounds != null) {
    if (!bounds || typeof bounds !== "object") {
      throw new Error("drag bounds must be an object");
    }
    const bx = bounds.x ?? 0;
    const by = bounds.y ?? 0;
    const bw = bounds.width;
    const bh = bounds.height;
    for (const [name, value] of Object.entries({ bx, by, bw, bh })) {
      if (!Number.isFinite(value)) {
        throw new Error(`drag bounds ${name} must be finite`);
      }
    }
    if (bw < 0 || bh < 0) {
      throw new Error("drag bounds width/height must be >= 0");
    }
  }

  const entity = entityStore.get(entityId);
  if (!entity) {
    throw new Error(`sprite entity not found: ${entityId}`);
  }

  const resolvedBefore = resolveSpriteEntityHierarchy(entityStore, {
    includeDisabled: true,
  });
  const currentWorld = resolvedBefore.byId.get(entityId);
  if (!currentWorld) {
    throw new Error(`sprite entity not found: ${entityId}`);
  }

  let targetWorldX = currentWorld.x + deltaX;
  let targetWorldY = currentWorld.y + deltaY;

  if (gridSize > 0) {
    targetWorldX = Math.round(targetWorldX / gridSize) * gridSize;
    targetWorldY = Math.round(targetWorldY / gridSize) * gridSize;
  }

  if (bounds != null) {
    const minX = bounds.x ?? 0;
    const minY = bounds.y ?? 0;
    const maxX = minX + bounds.width;
    const maxY = minY + bounds.height;
    targetWorldX = Math.min(maxX, Math.max(minX, targetWorldX));
    targetWorldY = Math.min(maxY, Math.max(minY, targetWorldY));
  }

  const worldDeltaX = targetWorldX - currentWorld.x;
  const worldDeltaY = targetWorldY - currentWorld.y;

  let localDeltaX = worldDeltaX;
  let localDeltaY = worldDeltaY;

  if (entity.parent != null) {
    const parent = resolvedBefore.byId.get(entity.parent);
    if (!parent) {
      throw new Error(
        `sprite entity parent not found: ${entity.parent} for ${entityId}`,
      );
    }

    const cos = Math.cos(-parent.rotation);
    const sin = Math.sin(-parent.rotation);
    const rotatedX = worldDeltaX * cos - worldDeltaY * sin;
    const rotatedY = worldDeltaX * sin + worldDeltaY * cos;
    localDeltaX = rotatedX / parent.scaleX;
    localDeltaY = rotatedY / parent.scaleY;
  }

  return entityStore.update(entityId, {
    x: (entity.x ?? 0) + localDeltaX,
    y: (entity.y ?? 0) + localDeltaY,
  });
}

export function createSpritePointerInteractionController(options = {}) {
  if (typeof options.pick !== "function") {
    throw new Error("pointer interaction pick() callback required");
  }
  const toWorld =
    typeof options.toWorld === "function"
      ? options.toWorld
      : (x, y) => ({ x, y });
  const dragThreshold = options.dragThreshold ?? 4;
  if (!Number.isFinite(dragThreshold) || dragThreshold < 0) {
    throw new Error("dragThreshold must be a finite value >= 0");
  }

  const callbacks = {
    onEnter: typeof options.onEnter === "function" ? options.onEnter : null,
    onLeave: typeof options.onLeave === "function" ? options.onLeave : null,
    onMove: typeof options.onMove === "function" ? options.onMove : null,
    onDown: typeof options.onDown === "function" ? options.onDown : null,
    onUp: typeof options.onUp === "function" ? options.onUp : null,
    onClick: typeof options.onClick === "function" ? options.onClick : null,
    onDragStart:
      typeof options.onDragStart === "function" ? options.onDragStart : null,
    onDrag: typeof options.onDrag === "function" ? options.onDrag : null,
    onDragEnd:
      typeof options.onDragEnd === "function" ? options.onDragEnd : null,
    onCancel: typeof options.onCancel === "function" ? options.onCancel : null,
  };

  const pointers = new Map();
  let hoverEntityId = null;

  function validatePointer(pointerId, x, y) {
    if (
      (typeof pointerId !== "string" && typeof pointerId !== "number") ||
      pointerId === ""
    ) {
      throw new Error("pointerId must be a non-empty string or number");
    }
    if (!Number.isFinite(x) || !Number.isFinite(y)) {
      throw new Error("pointer coordinates must be finite");
    }
  }

  function pickedEntity(hit) {
    return hit?.instance ?? null;
  }

  function makeEvent(type, state, hit, x, y, extra = {}) {
    const world = toWorld(x, y);
    return {
      type,
      pointerId: state.pointerId,
      x,
      y,
      worldX: world.x,
      worldY: world.y,
      entity: pickedEntity(hit),
      hit,
      dragging: state.dragging,
      capturedEntityId: state.capturedEntityId,
      ...extra,
    };
  }

  function updateHover(state, hit, x, y) {
    if (state.pointerId !== 0 && state.pointerId !== "mouse") {
      return;
    }
    const nextId = pickedEntity(hit)?.id ?? null;
    if (nextId === hoverEntityId) return;

    const previousId = hoverEntityId;
    hoverEntityId = nextId;
    if (previousId != null) {
      callbacks.onLeave?.(
        makeEvent("leave", state, null, x, y, {
          entityId: previousId,
        }),
      );
    }
    if (nextId != null) {
      callbacks.onEnter?.(
        makeEvent("enter", state, hit, x, y, {
          entityId: nextId,
        }),
      );
    }
  }

  function move(pointerId, x, y, pickOptions = {}) {
    validatePointer(pointerId, x, y);
    let state = pointers.get(pointerId);
    if (!state) {
      state = {
        pointerId,
        down: false,
        startX: x,
        startY: y,
        lastX: x,
        lastY: y,
        dragging: false,
        capturedEntityId: null,
        downEntityId: null,
      };
      pointers.set(pointerId, state);
    }

    const hit = options.pick(x, y, pickOptions);
    updateHover(state, hit, x, y);

    const dx = x - state.lastX;
    const dy = y - state.lastY;
    const totalDx = x - state.startX;
    const totalDy = y - state.startY;

    if (
      state.down &&
      !state.dragging &&
      Math.hypot(totalDx, totalDy) >= dragThreshold
    ) {
      state.dragging = true;
      const dragStart = makeEvent("dragstart", state, hit, x, y, {
        dx,
        dy,
        totalDx,
        totalDy,
      });
      callbacks.onDragStart?.(dragStart);
    }

    if (state.down && state.dragging) {
      callbacks.onDrag?.(
        makeEvent("drag", state, hit, x, y, {
          dx,
          dy,
          totalDx,
          totalDy,
        }),
      );
    }

    state.lastX = x;
    state.lastY = y;
    const event = makeEvent("move", state, hit, x, y, {
      dx,
      dy,
      totalDx,
      totalDy,
    });
    callbacks.onMove?.(event);
    return event;
  }

  function down(pointerId, x, y, pickOptions = {}) {
    validatePointer(pointerId, x, y);
    const hit = options.pick(x, y, pickOptions);
    const entity = pickedEntity(hit);
    const state = {
      pointerId,
      down: true,
      startX: x,
      startY: y,
      lastX: x,
      lastY: y,
      dragging: false,
      capturedEntityId: entity?.id ?? null,
      downEntityId: entity?.id ?? null,
    };
    pointers.set(pointerId, state);
    updateHover(state, hit, x, y);
    const event = makeEvent("down", state, hit, x, y);
    callbacks.onDown?.(event);
    return event;
  }

  function up(pointerId, x, y, pickOptions = {}) {
    validatePointer(pointerId, x, y);
    const state = pointers.get(pointerId) ?? {
      pointerId,
      down: false,
      startX: x,
      startY: y,
      lastX: x,
      lastY: y,
      dragging: false,
      capturedEntityId: null,
      downEntityId: null,
    };
    const hit = options.pick(x, y, pickOptions);
    const upEntityId = pickedEntity(hit)?.id ?? null;
    const wasDragging = state.dragging;
    state.down = false;

    const event = makeEvent("up", state, hit, x, y, {
      totalDx: x - state.startX,
      totalDy: y - state.startY,
    });
    callbacks.onUp?.(event);

    if (wasDragging) {
      callbacks.onDragEnd?.(
        makeEvent("dragend", state, hit, x, y, {
          totalDx: x - state.startX,
          totalDy: y - state.startY,
        }),
      );
    } else if (
      state.downEntityId != null &&
      state.downEntityId === upEntityId
    ) {
      callbacks.onClick?.(
        makeEvent("click", state, hit, x, y),
      );
    }

    state.capturedEntityId = null;
    pointers.delete(pointerId);
    return event;
  }

  function cancel(pointerId) {
    const state = pointers.get(pointerId);
    if (!state) return null;
    const event = {
      type: "cancel",
      pointerId,
      entity: null,
      hit: null,
      dragging: state.dragging,
      capturedEntityId: state.capturedEntityId,
    };
    if (state.dragging) {
      callbacks.onDragEnd?.({ ...event, type: "dragend", cancelled: true });
    }
    callbacks.onCancel?.(event);
    pointers.delete(pointerId);
    return event;
  }

  function clear() {
    for (const pointerId of Array.from(pointers.keys())) {
      cancel(pointerId);
    }
    hoverEntityId = null;
  }

  return {
    move,
    down,
    up,
    cancel,
    clear,
    get hoverEntityId() {
      return hoverEntityId;
    },
    get activePointerCount() {
      return pointers.size;
    },
    pointerState(pointerId) {
      const state = pointers.get(pointerId);
      return state ? { ...state } : null;
    },
  };
}


export function createSpriteClipboardController(
  entityStore,
  selectionModel,
  options = {},
) {
  if (!selectionModel || typeof selectionModel.snapshot !== "function") {
    throw new Error("sprite selection model required");
  }
  let clipboard = null;
  const defaultOffsetX = options.offsetX ?? 16;
  const defaultOffsetY = options.offsetY ?? 16;
  if (!Number.isFinite(defaultOffsetX) || !Number.isFinite(defaultOffsetY)) {
    throw new Error("clipboard offsets must be finite");
  }

  return {
    copy(copyOptions = {}) {
      clipboard = copySpriteEntities(
        entityStore,
        selectionModel.snapshot().ids,
        copyOptions,
      );
      return clipboard;
    },
    cut(cutOptions = {}) {
      const {
        childPolicy = "cascade",
        ...copyOptions
      } = cutOptions;
      clipboard = copySpriteEntities(
        entityStore,
        selectionModel.snapshot().ids,
        copyOptions,
      );
      const selected = [...selectionModel.snapshot().ids];
      const removed = new Set();
      for (const id of selected) {
        if (!entityStore.has(id)) continue;
        const result = removeSpriteEntityHierarchy(
          entityStore,
          id,
          { childPolicy },
        );
        for (const removedId of result.removedIds) removed.add(removedId);
      }
      selectionModel.clear();
      return {
        clipboard,
        removedIds: [...removed],
        count: removed.size,
      };
    },
    paste(pasteOptions = {}) {
      if (!clipboard) return null;
      const result = pasteSpriteEntities(
        entityStore,
        clipboard,
        {
          offsetX: defaultOffsetX,
          offsetY: defaultOffsetY,
          ...pasteOptions,
        },
      );
      selectionModel.set(result.ids);
      return result;
    },
    duplicate(duplicateOptions = {}) {
      const result = duplicateSpriteEntities(
        entityStore,
        selectionModel.snapshot().ids,
        {
          offsetX: defaultOffsetX,
          offsetY: defaultOffsetY,
          ...duplicateOptions,
        },
      );
      selectionModel.set(result.ids);
      return result;
    },
    set(value) {
      if (
        value != null &&
        (
          value.format !== "asset-forge-sprite-clipboard" ||
          value.version !== 1 ||
          !Array.isArray(value.entities)
        )
      ) {
        throw new Error("invalid sprite entity clipboard");
      }
      clipboard = value == null
        ? null
        : {
            ...value,
            entities: value.entities.map((entity) => ({ ...entity })),
          };
      return this.get();
    },
    get() {
      return clipboard == null
        ? null
        : {
            ...clipboard,
            entities: clipboard.entities.map((entity) => ({ ...entity })),
          };
    },
    clear() {
      const hadClipboard = clipboard != null;
      clipboard = null;
      return hadClipboard;
    },
    get hasData() {
      return clipboard != null;
    },
  };
}


export function selectionTransformHandleGeometry(
  entityStore,
  selectionModel,
  options = {},
) {
  const snapshot = selectionModel.snapshot();
  if (!snapshot.ids.length) return null;
  const resolved = resolveSpriteEntityHierarchy(entityStore, {
    includeDisabled: true,
  });
  const worlds = snapshot.ids.map((id) => {
    const entity = resolved.byId.get(id);
    if (!entity) throw new Error(`sprite entity not found: ${id}`);
    return entity;
  });
  const minX = Math.min(...worlds.map((entity) => entity.x));
  const minY = Math.min(...worlds.map((entity) => entity.y));
  const maxX = Math.max(...worlds.map((entity) => entity.x));
  const maxY = Math.max(...worlds.map((entity) => entity.y));
  const pivotX = options.pivotX ?? (minX + maxX) / 2;
  const pivotY = options.pivotY ?? (minY + maxY) / 2;
  const handleDistance = options.handleDistance ?? 32;
  if (![pivotX, pivotY, handleDistance].every(Number.isFinite)) {
    throw new Error("selection handle geometry values must be finite");
  }
  if (handleDistance < 0) {
    throw new Error("selection handleDistance must be >= 0");
  }
  return {
    bounds: {
      x: minX,
      y: minY,
      width: maxX - minX,
      height: maxY - minY,
    },
    pivot: { x: pivotX, y: pivotY },
    handles: {
      nw: { x: minX, y: minY },
      ne: { x: maxX, y: minY },
      se: { x: maxX, y: maxY },
      sw: { x: minX, y: maxY },
      rotate: { x: pivotX, y: minY - handleDistance },
      pivot: { x: pivotX, y: pivotY },
    },
  };
}

export function applySelectionTransformHandleDrag(
  entityStore,
  selectionModel,
  handle,
  startPoint,
  currentPoint,
  options = {},
) {
  if (!startPoint || !currentPoint) {
    throw new Error("selection transform handle points required");
  }
  for (const value of [
    startPoint.x,
    startPoint.y,
    currentPoint.x,
    currentPoint.y,
  ]) {
    if (!Number.isFinite(value)) {
      throw new Error("selection transform handle points must be finite");
    }
  }
  const geometry = selectionTransformHandleGeometry(
    entityStore,
    selectionModel,
    options,
  );
  if (!geometry) return { ids: [], count: 0, entities: [] };
  const pivot = geometry.pivot;

  if (handle === "rotate") {
    const a0 = Math.atan2(startPoint.y - pivot.y, startPoint.x - pivot.x);
    const a1 = Math.atan2(currentPoint.y - pivot.y, currentPoint.x - pivot.x);
    return transformSelectedSpriteEntities(entityStore, selectionModel, {
      pivotX: pivot.x,
      pivotY: pivot.y,
      rotation: a1 - a0,
    });
  }

  if (!["nw", "ne", "se", "sw"].includes(handle)) {
    throw new Error("selection transform handle must be nw, ne, se, sw, or rotate");
  }
  const startDx = startPoint.x - pivot.x;
  const startDy = startPoint.y - pivot.y;
  const currentDx = currentPoint.x - pivot.x;
  const currentDy = currentPoint.y - pivot.y;
  const uniform = options.uniform ?? false;
  if (typeof uniform !== "boolean") {
    throw new Error("selection transform uniform must be boolean");
  }
  let scaleX = Math.abs(startDx) < 1e-9 ? 1 : Math.abs(currentDx / startDx);
  let scaleY = Math.abs(startDy) < 1e-9 ? 1 : Math.abs(currentDy / startDy);
  if (uniform) {
    const scale = Math.max(scaleX, scaleY);
    scaleX = scale;
    scaleY = scale;
  }
  scaleX = Math.max(scaleX, 1e-6);
  scaleY = Math.max(scaleY, 1e-6);
  return transformSelectedSpriteEntities(entityStore, selectionModel, {
    pivotX: pivot.x,
    pivotY: pivot.y,
    scaleX,
    scaleY,
  });
}


export function transformSelectedSpriteEntities(
  entityStore,
  selectionModel,
  transform = {},
) {
  if (!selectionModel || typeof selectionModel.snapshot !== "function") {
    throw new Error("sprite selection model required");
  }
  const snapshot = selectionModel.snapshot();
  const ids = snapshot.ids ?? [];
  if (ids.length === 0) {
    return { ids: [], count: 0, entities: [] };
  }
  const rotationDelta = transform.rotation ?? 0;
  const scaleX = transform.scaleX ?? transform.scale ?? 1;
  const scaleY = transform.scaleY ?? transform.scale ?? 1;
  for (const [name, value] of Object.entries({ rotationDelta, scaleX, scaleY })) {
    if (!Number.isFinite(value)) {
      throw new Error(`selection transform ${name} must be finite`);
    }
  }
  if (!(scaleX > 0) || !(scaleY > 0)) {
    throw new Error("selection transform scale must be > 0");
  }

  const resolved = resolveSpriteEntityHierarchy(entityStore, {
    includeDisabled: true,
  });
  const selectedSet = new Set(ids);
  const roots = ids.filter((id) => {
    let current = resolved.byId.get(id);
    if (!current) throw new Error(`sprite entity not found: ${id}`);
    while (current.parent != null) {
      if (selectedSet.has(current.parent)) return false;
      current = resolved.byId.get(current.parent);
      if (!current) break;
    }
    return true;
  });

  let pivotX = transform.pivotX;
  let pivotY = transform.pivotY;
  if (pivotX == null || pivotY == null) {
    const worlds = roots.map((id) => resolved.byId.get(id));
    pivotX = worlds.reduce((sum, entity) => sum + entity.x, 0) / worlds.length;
    pivotY = worlds.reduce((sum, entity) => sum + entity.y, 0) / worlds.length;
  }
  if (!Number.isFinite(pivotX) || !Number.isFinite(pivotY)) {
    throw new Error("selection transform pivot must be finite");
  }

  const cos = Math.cos(rotationDelta);
  const sin = Math.sin(rotationDelta);
  const entities = [];

  entityStore.transact(() => {
    for (const id of roots) {
      const world = resolved.byId.get(id);
      const dx = (world.x - pivotX) * scaleX;
      const dy = (world.y - pivotY) * scaleY;
      const targetX = pivotX + dx * cos - dy * sin;
      const targetY = pivotY + dx * sin + dy * cos;

      moveSpriteEntityByWorldDelta(
        entityStore,
        id,
        targetX - world.x,
        targetY - world.y,
      );

      const current = entityStore.get(id);
      const parentWorld =
        current.parent == null ? null : resolved.byId.get(current.parent);
      const parentRotation = parentWorld?.rotation ?? 0;
      const parentScaleX = parentWorld?.scaleX ?? 1;
      const parentScaleY = parentWorld?.scaleY ?? 1;
      const targetWorldRotation = world.rotation + rotationDelta;
      const targetWorldScaleX = world.scaleX * scaleX;
      const targetWorldScaleY = world.scaleY * scaleY;
      entities.push(entityStore.update(id, {
        rotation: targetWorldRotation - parentRotation,
        scaleX: targetWorldScaleX / parentScaleX,
        scaleY: targetWorldScaleY / parentScaleY,
      }));
    }
  });

  return {
    ids: [...ids],
    transformedRootIds: roots,
    entities,
    count: ids.length,
    pivotX,
    pivotY,
  };
}


export function moveSelectedSpriteEntitiesByWorldDelta(
  entityStore,
  selectionModel,
  deltaX,
  deltaY,
  options = {},
) {
  if (!selectionModel || typeof selectionModel.snapshot !== "function") {
    throw new Error("sprite selection model required");
  }
  if (!Number.isFinite(deltaX) || !Number.isFinite(deltaY)) {
    throw new Error("selection drag delta must be finite");
  }
  const snapshot = selectionModel.snapshot();
  const ids = snapshot.ids ?? [];
  if (!Array.isArray(ids)) {
    throw new Error("selection snapshot ids must be an array");
  }
  if (ids.length === 0) {
    return { ids: [], entities: [], count: 0 };
  }

  const before = resolveSpriteEntityHierarchy(entityStore, {
    includeDisabled: true,
  });
  const selectedSet = new Set(ids);
  const roots = ids.filter((id) => {
    let current = before.byId.get(id);
    if (!current) {
      throw new Error(`sprite entity not found: ${id}`);
    }
    while (current.parent != null) {
      if (selectedSet.has(current.parent)) return false;
      current = before.byId.get(current.parent);
      if (!current) break;
    }
    return true;
  });

  const primary = snapshot.primaryId != null
    ? before.byId.get(snapshot.primaryId)
    : null;
  if (!primary) {
    throw new Error("selection primary entity not found");
  }

  let targetX = primary.x + deltaX;
  let targetY = primary.y + deltaY;
  const gridSize = options.gridSize ?? 0;
  if (!Number.isFinite(gridSize) || gridSize < 0) {
    throw new Error("gridSize must be a finite value >= 0");
  }
  if (gridSize > 0) {
    targetX = Math.round(targetX / gridSize) * gridSize;
    targetY = Math.round(targetY / gridSize) * gridSize;
  }

  const effectiveDeltaX = targetX - primary.x;
  const effectiveDeltaY = targetY - primary.y;
  const entities = [];

  entityStore.transact(() => {
    for (const id of roots) {
      entities.push(
        moveSpriteEntityByWorldDelta(
          entityStore,
          id,
          effectiveDeltaX,
          effectiveDeltaY,
          {
            ...options,
            gridSize: 0,
          },
        ),
      );
    }
  });

  return {
    ids: [...ids],
    movedRootIds: roots,
    entities,
    count: ids.length,
    deltaX: effectiveDeltaX,
    deltaY: effectiveDeltaY,
  };
}

export function createSpriteSelectionModel(options = {}) {
  const selected = new Set();
  let primaryId = null;
  const onChange =
    typeof options.onChange === "function" ? options.onChange : null;

  function emit(reason) {
    const snapshot = api.snapshot();
    onChange?.({ reason, ...snapshot });
    return snapshot;
  }

  function select(entityId, selectOptions = {}) {
    const additive = selectOptions.additive ?? false;
    const toggle = selectOptions.toggle ?? false;
    if (typeof additive !== "boolean" || typeof toggle !== "boolean") {
      throw new Error("selection additive/toggle options must be boolean");
    }
    if (!additive && !toggle) {
      selected.clear();
    }
    if (toggle && selected.has(entityId)) {
      selected.delete(entityId);
      if (primaryId === entityId) {
        primaryId = selected.size ? Array.from(selected).at(-1) : null;
      }
    } else {
      selected.add(entityId);
      primaryId = entityId;
    }
    return emit("select");
  }

  function set(ids) {
    if (!Array.isArray(ids)) {
      throw new Error("selection ids must be an array");
    }
    selected.clear();
    for (const id of ids) selected.add(id);
    primaryId = ids.length ? ids[ids.length - 1] : null;
    return emit("set");
  }

  function clear() {
    selected.clear();
    primaryId = null;
    return emit("clear");
  }

  function remove(entityId) {
    const changed = selected.delete(entityId);
    if (!changed) return api.snapshot();
    if (primaryId === entityId) {
      primaryId = selected.size ? Array.from(selected).at(-1) : null;
    }
    return emit("remove");
  }

  const api = {
    select,
    set,
    clear,
    remove,
    has(entityId) {
      return selected.has(entityId);
    },
    snapshot() {
      return {
        ids: Array.from(selected),
        primaryId,
        count: selected.size,
      };
    },
    get primaryId() {
      return primaryId;
    },
    get size() {
      return selected.size;
    },
  };

  return api;
}

export function selectSpriteInstancesInRect(
  atlasPages,
  instances,
  rect,
  options = {},
) {
  if (!atlasPages || typeof atlasPages.page !== "function") {
    throw new Error("runtime atlas page catalogue required");
  }
  if (!Array.isArray(instances)) {
    throw new Error("sprite instances must be an array");
  }
  if (!rect || typeof rect !== "object") {
    throw new Error("selection rect must be an object");
  }

  const x1 = rect.x1 ?? rect.x ?? 0;
  const y1 = rect.y1 ?? rect.y ?? 0;
  const x2 = rect.x2 ?? ((rect.x ?? 0) + (rect.width ?? 0));
  const y2 = rect.y2 ?? ((rect.y ?? 0) + (rect.height ?? 0));
  for (const [name, value] of Object.entries({ x1, y1, x2, y2 })) {
    if (!Number.isFinite(value)) {
      throw new Error(`selection rect ${name} must be finite`);
    }
  }
  const minX = Math.min(x1, x2);
  const minY = Math.min(y1, y2);
  const maxX = Math.max(x1, x2);
  const maxY = Math.max(y1, y2);
  const mode = options.mode ?? "intersect";
  if (!["intersect", "contain"].includes(mode)) {
    throw new Error("selection rect mode must be intersect or contain");
  }

  const hits = [];
  for (let index = 0; index < instances.length; index += 1) {
    const instance = instances[index];
    const bounds = spriteInstanceBounds(atlasPages, instance);
    const bx1 = bounds.x;
    const by1 = bounds.y;
    const bx2 = bounds.x + bounds.width;
    const by2 = bounds.y + bounds.height;
    const match = mode === "contain"
      ? bx1 >= minX && by1 >= minY && bx2 <= maxX && by2 <= maxY
      : bx2 >= minX && by2 >= minY && bx1 <= maxX && by1 <= maxY;
    if (match) {
      hits.push({ instance, inputIndex: index, bounds });
    }
  }

  hits.sort(
    (a, b) =>
      (b.instance.z ?? 0) - (a.instance.z ?? 0) ||
      b.inputIndex - a.inputIndex,
  );
  return hits;
}
