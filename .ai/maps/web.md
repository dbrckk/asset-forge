This file is a merged representation of a subset of the codebase, containing specifically included files and files not matching ignore patterns, combined into a single document by Repomix.
The content has been processed where content has been compressed (code blocks are separated by ⋮---- delimiter).

# File Summary

## Purpose
This file contains a packed representation of a subset of the repository's contents that is considered the most important context.
It is designed to be easily consumable by AI systems for analysis, code review,
or other automated processes.

## File Format
The content is organized as follows:
1. This summary section
2. Repository information
3. Directory structure
4. Repository files (if enabled)
5. Multiple file entries, each consisting of:
  a. A header with the file path (## File: path/to/file)
  b. The full contents of the file in a code block

## Usage Guidelines
- This file should be treated as read-only. Any changes should be made to the
  original repository files, not this packed version.
- When processing this file, use the file path to distinguish
  between different files in the repository.
- Be aware that this file may contain sensitive information. Handle it with
  the same level of security as you would the original repository.

## Notes
- Some files may have been excluded based on .gitignore rules and Repomix's configuration
- Binary files are not included in this packed representation. Please refer to the Repository Structure section for a complete list of file paths, including binary files
- Only files matching these patterns are included: **/*.{py,js,mjs,cjs,ts,tsx,jsx,java,kt,kts,gd,groovy,gradle,toml,json,yaml,yml,sql,sh}
- Files matching these patterns are excluded: .ai/**, **/node_modules/**, **/.gradle/**, **/build/**, **/dist/**, **/.venv/**, **/__pycache__/**, **/.pytest_cache/**, **/.git/**, **/coverage/**, **/*.lock, **/*.min.js, **/*.map, assets/**, art/**, art_sources/**, marketing/**, colab/**, kaggle/**, discovery-cache.json, health-snapshot.json, history.json
- Files matching patterns in .gitignore are excluded
- Files matching default ignore patterns are excluded
- Content has been compressed - code blocks are separated by ⋮---- delimiter
- Files are sorted by Git change count (files with more changes are at the bottom)

# Directory Structure
```
runtime_atlas.mjs
```

# Files

## File: runtime_atlas.mjs
```javascript
export function indexRuntimeAtlas(atlas)
⋮----
frame(indexOrName)
animation(name)
⋮----
export function frameQuad(frame)
⋮----
export function drawFrameCanvas2D(
  ctx,
  image,
  frame,
  destinationX = 0,
  destinationY = 0,
  options = {},
)
⋮----
// Atlas pixels are stored 90° clockwise. Rotate the destination context
// 90° counter-clockwise so the sprite is restored to source orientation.
⋮----
export function sourceOrientedUVs(frame)
⋮----
// Return UVs in source-orientation vertex order:
// top-left, top-right, bottom-right, bottom-left.
⋮----
export function animationFrameAtTime(indexedAtlas, animationOrName, timeSeconds)
⋮----
export function animationDurationSeconds(animation)
⋮----
export function animationEventsBetween(animation, startTimeSeconds, endTimeSeconds)
⋮----
const includeOccurrence = (event, absoluteTimeSeconds, loopCount, eventIndex) =>
⋮----
export function createAnimationPlayer(indexedAtlas, animationName, options =
⋮----
function emit(sample)
⋮----
function sample()
⋮----
get animation()
get timeSeconds()
get playing()
get playbackRate()
play()
pause()
seek(nextTimeSeconds)
setPlaybackRate(rate)
⋮----
update(deltaSeconds)
⋮----
export function drawAnimationPlayerCanvas2D(
  ctx,
  image,
  player,
  destinationX = 0,
  destinationY = 0,
  options = {},
)
⋮----
export function buildSpriteBatch(indexedAtlas, instances, options =
⋮----
export function drawSpriteBatchCanvas2D(ctx, image, indexedAtlas, instances)
⋮----
export function buildInstancedSpriteBatch(indexedAtlas, instances, options =
⋮----
// Per instance:
// visibleX, visibleY, visibleWidth, visibleHeight,
// u0, v0, u1, v1,
// atlasRotationFlag, sourceWidth, sourceHeight, spriteRotationRadians,
// pivotWorldX, pivotWorldY,
// tintR, tintG, tintB, alpha
⋮----
export function instancedSpriteUV(
  u0,
  v0,
  u1,
  v1,
  rotationFlag,
  unitX,
  unitY,
)
⋮----
// Packed texture is 90° clockwise. Convert source-oriented unit coords
// to stored atlas UV coordinates.
⋮----
export function instancedSpriteWebGL2Shaders()
⋮----
export function instancedSpriteAttributeViews(batch)
⋮----
export function createRuntimeAtlasPages(pages)
⋮----
page(id)
⋮----
export function buildTexturePageBatches(
  atlasPages,
  instances,
  options = {},
)
⋮----
function _compileWebGL2Shader(gl, type, source)
⋮----
function _linkWebGL2Program(gl, vertexSource, fragmentSource)
⋮----
export function createInstancedSpriteRendererWebGL2(gl, options =
⋮----
frame()
⋮----
function assertActive()
⋮----
function renderBatch(batch, texture, viewportWidth, viewportHeight)
⋮----
function renderPageBatches(pageBatches, viewportWidth, viewportHeight)
⋮----
function dispose()
⋮----
get disposed()
get uploadedCapacityBytes()
get alphaBlending()
⋮----
export function createWebGL2TextureCache(gl, options =
⋮----
function createTextureFromSource(source, textureOptions =
⋮----
function acquire(key, source, textureOptions =
⋮----
async function load(key, sourceOrFactory, textureOptions =
⋮----
function get(key)
⋮----
function has(key)
⋮----
function references(key)
⋮----
function release(key)
⋮----
function deleteTexture(key)
⋮----
function clear()
⋮----
get size()
get pendingCount()
⋮----
export async function loadImageBitmapSource(url, options =
⋮----
export async function preloadRuntimeAtlasPageTextures(
  atlasPages,
  textureCache,
  options = {},
)
⋮----
export function releaseRuntimeAtlasPageTextures(textureCache, preloadResult)
⋮----
export async function createWebGL2RuntimeAtlasScene(
  gl,
  pageDefinitions,
  options = {},
)
⋮----
resolveTexture(textureKey)
⋮----
buildBatches(instances, batchOptions =
render(instancesOrBatches, viewportWidth, viewportHeight, batchOptions =
dispose()
⋮----
export function spriteInstanceBounds(atlasPages, instance)
⋮----
function rotatedAabb(rx, ry, rw, rh)
⋮----
export function cullSpriteInstances(
  atlasPages,
  instances,
  viewport,
  options = {},
)
⋮----
// Most scene sprites are not rotated. Avoid constructing full logical +
// visible bounds objects for this hot culling path.
⋮----
export function stableSortSpriteInstances(instances, options =
⋮----
export function prepareSpriteSceneInstances(
  atlasPages,
  instances,
  options = {},
)
⋮----
export function resizeWebGL2Canvas(canvas, gl, options =
⋮----
export async function createWebGL2CanvasRuntime(
  canvas,
  pageDefinitions,
  options = {},
)
⋮----
function resize(resizeOptions =
⋮----
function clampRuntimeCamera(nextCamera)
⋮----
function pickRuntimeEntity(x, y, pickOptions =
⋮----
function recordRuntimeEdit(label, callback)
⋮----
toWorld: (x, y)
onDrag(event)
⋮----
async function rebuildAfterContextRestore()
⋮----
function handleContextLost(event)
⋮----
function handleContextRestored()
⋮----
get visibilityMask()
setVisibilityMask(nextMask)
get camera()
get worldBounds()
⋮----
setWorldBounds(nextBounds)
setCamera(nextCamera =
updateCameraFollow(targetX, targetY, deltaSeconds)
updateCameraFollowEntity(entityId, deltaSeconds, followOptions =
shakeCamera(amplitude, durationSeconds, frequency)
clearCameraShake()
get gl()
get scene()
get contextLost()
get restoring()
⋮----
async waitForRestore()
⋮----
buildEntityBatches(batchOptions =
updateAnimations(deltaSeconds)
render(instancesOrBatches, batchOptions =
renderEntities(batchOptions =
screenToWorld(x, y)
worldToScreen(x, y, parallax =
pickEntity(x, y, pickOptions =
⋮----
selectEntity(entityId, selectOptions =
clearSelection()
duplicateSelection(duplicateOptions =
cutSelection(cutOptions =
pasteClipboard(pasteOptions =
copySelection(copyOptions =
pasteEntities(clipboard, pasteOptions =
reparentEntity(entityId, parentId = null, reparentOptions =
removeEntity(entityId, removeOptions =
removeSelection(removeOptions =
undo()
redo()
selectEntitiesInRect(rect, selectOptions =
moveEntityByWorldDelta(entityId, deltaX, deltaY, moveOptions =
transformSelection(transformOptions =
selectionHandles(handleOptions =
dragSelectionHandle(
      handle,
      startPoint,
      currentPoint,
      handleOptions = {},
)
moveSelectionByWorldDelta(deltaX, deltaY, moveOptions =
pointerMove(pointerId, x, y, pickOptions =
pointerDown(pointerId, x, y, pickOptions =
pointerUp(pointerId, x, y, pickOptions =
pointerCancel(pointerId)
async restore()
⋮----
export function createSpriteEntityStore(options =
⋮----
function normalizeId(id)
⋮----
function validateEntity(entity, label = "sprite entity")
⋮----
function cloneEntity(entity)
⋮----
function add(entity)
⋮----
function get(id)
⋮----
function has(id)
⋮----
function update(id, patch)
⋮----
function remove(id)
⋮----
function snapshot(options =
⋮----
function instances(options =
⋮----
function transact(callback)
⋮----
get version()
⋮----
export function duplicateSpriteEntities(
  entityStore,
  entityIds,
  options = {},
)
⋮----
export function copySpriteEntities(
  entityStore,
  entityIds,
  options = {},
)
⋮----
export function pasteSpriteEntities(
  entityStore,
  clipboard,
  options = {},
)
⋮----
export function reparentSpriteEntity(
  entityStore,
  entityId,
  parentId = null,
  options = {},
)
⋮----
export function removeSpriteEntityHierarchy(
  entityStore,
  entityId,
  options = {},
)
⋮----
const visit = (id) =>
⋮----
export function createSpriteEntityHistory(
  entityStore,
  options = {},
)
⋮----
const capture = () => entityStore.snapshot(
const captureExtra = ()
⋮----
function sameValue(a, b)
⋮----
function restore(snapshot, context)
⋮----
function push(entry)
⋮----
begin(label = "edit")
commit()
cancel()
record(label, callback)
⋮----
clear()
get canUndo()
get canRedo()
get undoCount()
get redoCount()
get active()
⋮----
export function createSpriteAnimationSystem(
  atlasPages,
  entityStore,
  options = {},
)
⋮----
function ensureEntity(entityId)
⋮----
function bind(entityId, animationName, bindOptions =
⋮----
onFrame(sample)
onEvent(event)
onLoop(event)
onFinish(sample)
⋮----
seek(timeSeconds)
⋮----
sample()
⋮----
function get(entityId)
⋮----
function unbind(entityId)
⋮----
function update(deltaSeconds)
⋮----
function _stableSceneCacheKey(value, seen = new Set())
⋮----
export function createSpriteEntityBatchCache(
  runtimeScene,
  entityStore,
  options = {},
)
⋮----
function invalidate()
⋮----
function ensureVersion()
⋮----
function build(batchOptions =
⋮----
get stats()
⋮----
export function resolveSpriteEntityHierarchy(entityStore, options =
⋮----
function resolve(entity)
⋮----
export function applyCameraToSpriteInstances(
  instances,
  camera = {},
)
⋮----
export function filterSpriteInstancesByLayer(
  instances,
  visibilityMask = 0xffffffff,
)
⋮----
function _splitEntityHierarchyOptions(batchOptions =
⋮----
export function buildSpriteEntityInstances(entityStore, batchOptions =
⋮----
export function clampCameraToWorldBounds(
  camera,
  worldBounds,
  viewportWidth,
  viewportHeight,
)
⋮----
function clampAxis(value, min, size, visibleSize)
⋮----
export function createCamera2DController(initialCamera =
⋮----
function baseCamera()
⋮----
function shakenCamera()
⋮----
function update(targetX, targetY, deltaSeconds)
⋮----
function setCamera(nextCamera =
⋮----
function shake(amplitude, durationSeconds, frequency = 24)
⋮----
function clearShake()
⋮----
get baseCamera()
get shaking()
⋮----
export function worldToScreenPoint(x, y, camera =
⋮----
export function screenToWorldPoint(x, y, camera =
⋮----
export function pointHitsSpriteInstance(
  atlasPages,
  instance,
  pointX,
  pointY,
  options = {},
)
⋮----
export function pickSpriteInstances(
  atlasPages,
  instances,
  pointX,
  pointY,
  options = {},
)
⋮----
export function moveSpriteEntityByWorldDelta(
  entityStore,
  entityId,
  deltaX,
  deltaY,
  options = {},
)
⋮----
export function createSpritePointerInteractionController(options =
⋮----
function validatePointer(pointerId, x, y)
⋮----
function pickedEntity(hit)
⋮----
function makeEvent(type, state, hit, x, y, extra =
⋮----
function updateHover(state, hit, x, y)
⋮----
function move(pointerId, x, y, pickOptions =
⋮----
function down(pointerId, x, y, pickOptions =
⋮----
function up(pointerId, x, y, pickOptions =
⋮----
function cancel(pointerId)
⋮----
get hoverEntityId()
get activePointerCount()
pointerState(pointerId)
⋮----
export function createSpriteClipboardController(
  entityStore,
  selectionModel,
  options = {},
)
⋮----
copy(copyOptions =
cut(cutOptions =
paste(pasteOptions =
duplicate(duplicateOptions =
set(value)
get()
⋮----
get hasData()
⋮----
export function selectionTransformHandleGeometry(
  entityStore,
  selectionModel,
  options = {},
)
⋮----
export function applySelectionTransformHandleDrag(
  entityStore,
  selectionModel,
  handle,
  startPoint,
  currentPoint,
  options = {},
)
⋮----
export function transformSelectedSpriteEntities(
  entityStore,
  selectionModel,
  transform = {},
)
⋮----
export function moveSelectedSpriteEntitiesByWorldDelta(
  entityStore,
  selectionModel,
  deltaX,
  deltaY,
  options = {},
)
⋮----
export function createSpriteSelectionModel(options =
⋮----
function emit(reason)
⋮----
function select(entityId, selectOptions =
⋮----
function set(ids)
⋮----
function remove(entityId)
⋮----
has(entityId)
snapshot()
get primaryId()
⋮----
export function selectSpriteInstancesInRect(
  atlasPages,
  instances,
  rect,
  options = {},
)
```
