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
    if (sample.finished && !finishEmitted) {
      finishEmitted = true;
      playing = false;
      onFinish?.(sample);
    } else if (!sample.finished) {
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

    for (const [name, value] of Object.entries({ x, y, scaleX, scaleY })) {
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
    const positions = [
      [left, top],
      [right, top],
      [right, bottom],
      [left, bottom],
    ];

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
      visibleX: left,
      visibleY: top,
      visibleWidth: frame.sourceRegion.width * scaleX,
      visibleHeight: frame.sourceRegion.height * scaleY,
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
  // rotationFlag, sourceWidth, sourceHeight, reserved
  const strideFloats = 12;
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

    for (const [name, value] of Object.entries({ x, y, scaleX, scaleY })) {
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
    data[write + 11] = 0;

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
      "rotationFlag",
      "sourceWidth",
      "sourceHeight",
      "reserved",
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

uniform vec2 uViewportSize;

out vec2 vUv;

void main() {
  vec2 pixelPosition =
    aVisibleRect.xy + aUnitPosition * aVisibleRect.zw;

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

  gl_Position = vec4(clip, 0.0, 1.0);
}
`,
    fragment: `#version 300 es
precision mediump float;

uniform sampler2D uTexture;
in vec2 vUv;
out vec4 outColor;

void main() {
  outColor = texture(uTexture, vUv);
}
`,
  };
}

export function instancedSpriteAttributeViews(batch) {
  if (!batch || !(batch.instances instanceof Float32Array)) {
    throw new Error("invalid instanced sprite batch");
  }
  if (batch.instanceStrideFloats !== 12) {
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
},
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

  const groups = new Map();
  const sequence = [];
  let previousPageId = null;
  let inputTextureSwitches = 0;

  for (let instanceIndex = 0; instanceIndex < instances.length; instanceIndex += 1) {
    const instance = instances[instanceIndex];
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

    if (!groups.has(pageId)) {
      groups.set(pageId, {
        page,
        instances: [],
        firstInputIndex: instanceIndex,
      });
    }
    groups.get(pageId).instances.push({
      ...instance,
      frame: instance.frame,
      _inputIndex: instanceIndex,
    });
    sequence.push(pageId);
  }

  let grouped = Array.from(groups.values());
  if (!preserveOrder) {
    grouped.sort((a, b) => a.page.order - b.page.order || a.page.id.localeCompare(b.page.id));
  } else {
    grouped.sort((a, b) => a.firstInputIndex - b.firstInputIndex);
  }

  const batches = grouped.map((group) => {
    const normalizedInstances = group.instances.map(({ _inputIndex, page, ...instance }) => instance);
    const batch =
      mode === "instanced"
        ? buildInstancedSpriteBatch(group.page.atlas, normalizedInstances, options)
        : buildSpriteBatch(group.page.atlas, normalizedInstances, options);

    return {
      pageId: group.page.id,
      texture: group.page.texture,
      atlas: group.page.atlas,
      instanceCount: normalizedInstances.length,
      firstInputIndex: group.firstInputIndex,
      inputIndices: group.instances.map((instance) => instance._inputIndex),
      batch,
    };
  });

  return {
    mode,
    preserveOrder,
    pageCount: batches.length,
    instanceCount: instances.length,
    inputTextureSwitches,
    groupedTextureSwitches: Math.max(0, batches.length - 1),
    textureSwitchesSaved: Math.max(
      0,
      inputTextureSwitches - Math.max(0, batches.length - 1),
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
      const result = renderBatch(
        entry.batch,
        entry.texture,
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
  };
}
