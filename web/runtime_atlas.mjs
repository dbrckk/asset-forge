export function indexRuntimeAtlas(atlas) {
  if (!atlas || atlas.format !== "asset-forge-runtime-atlas" || atlas.version !== 1) {
    throw new Error("unsupported Asset Forge runtime atlas");
  }
  if (!Array.isArray(atlas.frames) || atlas.frames.length !== atlas.frameCount) {
    throw new Error("runtime atlas frameCount mismatch");
  }

  const byIndex = new Map();
  const byName = new Map();

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

  return {
    atlas,
    byIndex,
    byName,
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
