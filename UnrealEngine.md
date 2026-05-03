# UE5 Optimization Guide

---

## Introduction

This guide distills production knowledge from Epic's GDC and Unreal Fest talks, tech-art blogs, and community threads for indie developers building PC games in Unreal Engine 5.3–5.5. There are no beginner tutorials here — the focus is on production pitfalls, non-obvious techniques, and decisions that genuinely determine the performance of a shipped game. Mobile and VR topics are intentionally excluded.

---

## Common Foundation: Profiling and Work Hygiene

The cardinal rule: measure first, then optimize. Optimizing without data wastes time on things that are not the bottleneck.

### Core Tools

**Unreal Insights** is the primary profiling tool in UE5, consisting of `UnrealTraceServer` (backend) and `UnrealInsights` (viewer). Trace channels are selected before a session — the defaults cover typical cases, but memory analysis requires adding `memory_light,memtags`. From UE5.5 onward, `Trace.RegionBegin` / `Trace.RegionEnd` are available for tagging multi-frame regions (e.g. GC passes, level streaming) directly on the timeline ([Tom Looman — UE 5.5 Performance Highlights](https://tomlooman.com/unreal-engine-5-5-performance-highlights/)).

```
stat unit          // bottleneck: Game / Draw / GPU / RHI
stat gpu           // GPU breakdown per pass
stat scenerendering // draw calls, primitive count
stat hitches       // frames above the hitch threshold
ProfileGPU         // detailed GPU breakdown (shortcut: Ctrl+Shift+,)
```

**GPU Visualizer** is opened via `ProfileGPU`. For deep GPU debugging (per-draw-call shaders, resources, timings), use the RenderDoc plugin — with D3D12, set `r.ShowMaterialDrawEvents 0` before capturing to eliminate GPU marker overhead from skewing measurements ([AMD GPUOpen — Unreal Engine Performance Guide](https://gpuopen.com/learn/unreal-engine-performance-guide/)).

**Important:** Always profile in a "Test" configuration (packaged build), not in the editor. Editor builds carry significant overhead that heavily skews results ([Unreal Fest 2024 — Optimizing the Game Thread](https://www.youtube.com/watch?v=KxREK-DYu70)).

### Custom Code Instrumentation

Add your own statistics visible in both the `stat` overlay and Insights:

```cpp
// In the header:
DECLARE_STATS_GROUP(TEXT("MyGame"), STATGROUP_MyGame, STATCAT_Advanced);
DECLARE_CYCLE_STAT(TEXT("ProcessAI"), STAT_ProcessAI, STATGROUP_MyGame);

// In .cpp:
void UMyAIComponent::Tick(float DeltaTime)
{
    SCOPE_CYCLE_COUNTER(STAT_ProcessAI);
    // ...
}

// Scope visible in the Insights flame graph:
TRACE_CPUPROFILER_EVENT_SCOPE_STR("MySystem::HeavyUpdate");
```

`SCOPED_NAMED_EVENT` adds ~20% frame overhead — use it only in targeted sessions, never as permanent production code ([Tom Looman — Adding Counters & Traces](https://tomlooman.com/unreal-engine-profiling-stat-commands/)).

---

## Part 1: Level Design and Environment

### Nanite — When It Helps, When It Hurts

Nanite virtualizes geometry, eliminating manual LOD management. However, it is not a free resource and has specific break-even conditions.

#### Nanite Is Not Free on Simple Meshes

Nanite organizes triangles into clusters and has a fixed per-frame entry cost (overhead) that only pays off with sufficiently complex geometry. Enabling Nanite on a mesh with 8–64 triangles can cost as much as the entire Nanite pass for a richly detailed level. In production tests, disabling Nanite on a handful of simple meshes yielded a ~3 ms gain in the Nanite pass — with zero visual difference ([r/UnrealEngine5, 2025](https://www.reddit.com/r/UnrealEngine5/comments/1ot0ms4/nanite_warning_lower_performance_with_simples/)). The rule: meshes with fewer than ~300 triangles, or purely flat primitives, should use traditional LODs and ISM (Instanced Static Mesh).

#### Overlapping Geometry — Nanite's Enemy

Nanite attempts to determine which triangles are visible. When geometry layers overlap densely (e.g. thick foliage, tightly packed rocks), Nanite renders all overlapping triangles "just in case." The result is extreme overdraw, visible as white-to-yellow areas in the `r.Nanite.Visualize Overdraw` mode. Epic directly addresses this problem in [Nanite for Artists | GDC 2024](https://www.youtube.com/watch?v=eoxYceDfKEM) — alpha-card foliage is a worse case than dense rock formations, because leaves overlap across dozens of layers.

The key CVar for controlling cluster density:
```ini
r.Nanite.MaxPixelsPerEdge 2   ; higher = fewer clusters, cheaper at the cost of detail
```

Values of 2–4 on low/medium settings deliver major savings with minimal visual regression ([Intel UE5 Optimization Guide](https://www.intel.com/content/www/us/en/developer/articles/technical/unreal-engine-optimization-chapter-2.html)).

#### Nanite + Masked Materials / WPO — A Double Hit

Nanite with a Masked material or World Position Offset (WPO) requires the Programmable Rasterizer (software path) instead of the fast hardware raster — this is 2 to 4x more expensive than opaque Nanite. In UE5.4, dramatic FPS drops were reported with foliage (Nanite Masked + WPO), primarily due to a spike in Shadow Depths cost (VSM) ([Epic Forums, 2024](https://forums.unrealengine.com/t/bad-performance-with-nanite-masked-wpo-in-ue5-4-2/1906424)).

One of the most common mistakes when importing Megascans foliage — it automatically has Nanite enabled and a masked material. Solutions:
- Disable "Evaluate World Position Offset" for foliage shadows in the Static Mesh Editor (Details → Shadow → Evaluate World Position Offset = Off).
- Set `WPO Disable Distance` on the static mesh (e.g. 30 m for small plants, 80 m for trees) — Nanite won't spend time evaluating WPO for distant objects.
- For best results: model leaves as opaque full geometry instead of alpha cards.

```ini
; Per-mesh in Static Mesh Editor:
; Shadow → Evaluate World Position Offset = Off (for foliage shadows)
```

Source: [Intel UE5 Optimization Guide Ch.2](https://www.intel.com/content/www/us/en/developer/articles/technical/unreal-engine-optimization-chapter-2.html)

#### Nanite Fallback Mesh — The Forgotten Landmine

Every mesh with Nanite enabled must have a fallback mesh — a simplified version used by collisions, Lumen Hardware RT (BLAS), and platforms without Nanite support. By default, UE generates a high-poly fallback. If `Fallback Relative Error = 0`, the fallback will be identical to the original.

In projects with many unique meshes, fallback meshes can occupy 100–400 MB of VRAM ([Epic Forums, 2025](https://forums.unrealengine.com/t/nanite-fallback-mesh-buffers-vram-residence/2563974)).

```ini
; Per-mesh in Static Mesh Editor:
Fallback Triangle Percent = 1-5%   ; aggressive reduction
Fallback Relative Error = 1.0      ; large silhouette deviation allowed (small mesh)

; Project-wide (cook), UE5.5+:
[/Script/WindowsTargetPlatform.WindowsTargetSettings]
bGenerateNaniteFallbackMeshes=False   ; strip all fallbacks from the cook entirely
```

When to use: set `Fallback Relative Error` to ~1.0 for background decorative meshes. Verify visually in non-Nanite mode that the silhouette is acceptable.

#### Nanite Tessellation / Displacement

Nanite Tessellation (production-ready from UE5.4) is real-time dynamic tessellation — visually impressive, but expensive, as it runs through the software raster path. Across an entire terrain and many scene meshes it can double the Nanite pass time. Use it selectively on hero assets and key terrain features ([An Artist's Guide to Nanite Tessellation | Unreal Fest 2024](https://www.youtube.com/watch?v=6igUsOp8FdA)).

```ini
r.Nanite.Tessellation=1
r.Nanite.AllowTessellation=1
r.Nanite.DicingRate=2   ; default 2px — higher = less dense, cheaper
                        ; recommended 4-8 for background, 1-2 for hero props (GDC 2024)
```

#### Nanite Foliage — Opaque Geometry Is the Right Path

Traditional foliage with alpha cards (alpha-tested Masked) remains difficult for Nanite. The modern approach: model leaves as opaque full geometry. Nanite with the `Preserve Area` flag is required to maintain foliage silhouettes at large distances. From UE5.5, experimental Nanite Skeletal Mesh is also available — in tests with 500 animated characters it raised FPS from ~22 to ~55–60 ([The Future of Nanite Foliage | Unreal Fest Stockholm 2025](https://www.youtube.com/watch?v=aZr-mWAzoTg)).

#### When Traditional LODs Are Better Than Nanite

| Situation | Recommendation |
|---|---|
| Meshes < 300 triangles (simple cube, plane) | Traditional LOD / ISM |
| Meshes with Masked material and WPO (grass, leaves) | Traditional LOD or opaque Nanite geometry |
| Skeletal meshes (UE5.4 and older) | Traditional LOD (Nanite SK experimental from 5.5) |
| Translucent geometry (glass, water) | Traditional — Nanite does not support translucency |
| Mixed Nanite + non-Nanite scene | Maximize Nanite coverage — mixing increases overhead on both paths |

---

### World Partition — Production Pitfalls

World Partition (WP) is UE5's open-world system. It brings many benefits but hides an equal number of traps.

#### HLOD — Generation Pitfalls

HLOD (Hierarchical LOD) in World Partition consists of meshes/impostors rendered for distant streaming cells. The default configuration "Lowest Available LOD" for landscape makes HLODs look like grey blobs. Overly aggressive decimation destroys the quality of distant terrain ([r/unrealengine 2024](https://www.reddit.com/r/unrealengine/comments/1efsgdh/how_come_world_partition_landscape_is_so/)).

```ini
; In World Settings → Runtime Partitions → HLOD Setups:
; INDEX [0] — HLODLayer_Instanced: set Loading Range to cover mountains
; INDEX [1] — HLOD Merged: set Specific LOD = 4-5 instead of "Lowest Available"
```

Trick: for Nanite meshes, set HLOD Layer Type = Instanced (no decimation) — meshes stream faster through instancing, and Nanite handles the detail.

#### Data Layers vs Level Instances — Which to Use When

Two fundamentally different concepts, often confused. Data Layers are logical groups of actors inside a single WP level, loaded/unloaded independently of spatial streaming. Level Instances are nested levels that can be standalone or embedded (unpacked at cook time with no runtime overhead).

Pitfalls:
- Runtime Data Layers are NOT compatible with Level Instances — you cannot place a Level Instance inside an External Data Layer ([xbloom.io WP Internals](https://xbloom.io/2025/10/24/unreals-world-partition-internals/)).
- Too many overlapping Data Layers + Runtime Grids produces a combinatorial explosion of streaming cells.

| Use Case | Solution |
|---|---|
| DLC / seasonal content | External Data Layer (EDL) — content in a separate plugin |
| Game state (peaceful village vs. raided) | Runtime Data Layer |
| Repeating POIs (gas stations, houses) | Level Instance → Packed Level Actor |
| Modular building in multiple locations | Level Instance + Embedded (no runtime overhead) |

Source: [StraySpark WP Deep Dive](https://www.strayspark.studio/blog/ue5-world-partition-deep-dive-streaming-hlod)

#### One-File-Per-Actor (OFPA) — Source Control Pitfalls

OFPA stores each actor as a separate file in the `__ExternalActors__` folder. With non-Perforce VCS (Git LFS, SVN), conflicts are harder to resolve. New actors added to a level still modify the main `.umap` file, not just the actor file. Auto-Save can generate thousands of changes in `ExternalActors` simultaneously.

Best practices:
- Disable Auto-Save (Edit → Editor Preferences → Loading & Saving) for large WP scenes.
- Before renaming folders containing OFPA data: check and update all references first.
- Use the diagnostic tool to debug streaming:

```
wp.Editor.DumpStreamingGenerationLog
; Output in: Saved/Logs/WorldPartition/
```

Source: [Epic Forums OFPA Best Practices](https://forums.unrealengine.com/t/tips-and-best-practices-for-one-file-per-actor/837886)

#### Runtime Streaming Grid

The default 128 m (12800 cm) works for most cases, but dense urban environments need 64 m, and sparse terrain benefits from 256 m ([StraySpark Blog](https://www.strayspark.studio/blog/ue5-world-partition-deep-dive-streaming-hlod)).

```ini
RuntimeGrid.CellSize=12800     ; 128 meters (value in cm!)
RuntimeGrid.LoadingRange=25600 ; 256 meters = 2x Cell Size
```

Trick: for fast vehicles or flight, add a predictive streaming source based on the player's velocity vector to pre-load 1–2 cells ahead. The default Streaming Source (player controller) is purely reactive.

Watch out for large actors that span more than one cell size (churches, bridges) — they are "promoted" to a higher grid level and may load independently of normal cells.

---

### Lumen — Tuning GI and Reflections

Lumen is UE5's global illumination (GI) and reflections system. It works well out of the box, but the default settings are calibrated for high-end benchmark hardware.

#### Hardware vs Software Lumen

| Aspect | Software Lumen (SW RT) | Hardware Lumen (HW RT) |
|---|---|---|
| Requirements | Distance Fields (DF) on all meshes | RT-capable GPU (DXR/Vulkan RT) |
| Reflections | Surface Cache (less accurate) | Hit Lighting = full material evaluation |
| Skinned Meshes | Not lit | Lit (GI on characters) |
| Far Field (>1 km) | No | Yes (uses HLOD1) |
| Thin objects (< 4 cm) | Excluded from Surface Cache | Better support |

When to use Software: console games, broad platform support. When to use Hardware: archviz, scenes with many mirror-like reflections, cinematic animations with Metahuman GI.

Source: [NVIDIA UE5.4 RT Guide](https://dlss.download.nvidia.com/uebinarypackages/Documentation/UE5+Raytracing+Guideline+v5.4.pdf)

#### Surface Cache Invalidation — "Pink Patches"

The Lumen Surface Cache is a set of cards (Lumen Cards) generated for each mesh. When a card is out of date or missing, the area glows pink in the Surface Cache visualization. An object must be at least ~4 cm in size to make it into the Surface Cache. Yellow objects in GI = culled (too distant or too small) ([Epic Forums Surface Cache thread](https://forums.unrealengine.com/t/lumen-surface-cache-scale-woes/2669365)).

Trick: build modularly — the interior of a building as separate meshes (walls, floor, ceiling), not one blended mesh. A single large "building" mesh will not generate correct cards for the interior, causing pink GI artifacts inside ([Unreal Fest Gold Coast 2024](https://www.youtube.com/watch?v=szgnZx2b0Zg)).

```ini
; Diagnostics:
; Lumen → Surface Cache (viewport mode)
; Lumen → Card Placement (r.Lumen.Visualize.CardPlacement)

; Increase cards per object (Static Mesh Editor → Build Settings → Num Lumen Mesh Cards = 6-12)
r.LumenScene.SurfaceCache.MeshCardsMinSize=4   ; default 4 (cm)
r.LumenScene.SurfaceCache.CardMinResolution=4
; For emissive objects that must always stay in cache:
; Check "Emissive Light Source" on the actor — prevents culling
```

#### Lumen CVars Worth Knowing

```ini
; GI quality — ScreenProbeGather
r.Lumen.ScreenProbeGather.TracingOctahedronResolution=2
r.Lumen.ScreenProbeGather.DownsampleFactor=2              ; lower GI resolution = large gains
r.Lumen.ScreenProbeGather.IntegrateDownsampleFactor=2     ; UE5.6: ~3x faster, ~0.3-0.5ms

; Reflections
r.Lumen.Reflections.DownsampleFactor=2      ; saves 1-2ms
r.Lumen.Reflections.MaxRoughnessToTrace=0.4 ; only shiny materials receive RT reflections

; Far Field (open worlds, HWRT)
r.LumenScene.FarField=1
r.LumenScene.FarField.OcclusionOnly=1       ; UE5.6: ~50% cheaper Far Field

; Firefly suppression (UE5.6 default)
r.Lumen.ScreenProbeGather.MaxRayIntensity=10  ; more aggressive clamping
```

Source: [StraySpark Lumen 60fps Guide](https://www.strayspark.studio/blog/ue5-lumen-optimization-60fps), [Tom Looman UE5.6 Highlights](https://tomlooman.com/unreal-engine-5-6-performance-highlights/)

#### Lumen + Emissive — Limitations

Emissive lighting through Lumen is still marked experimental. When the camera cuts or a scene is freshly loaded, Lumen must recompute GI from scratch — a noticeable delay / flickering is visible for 0.5–2 seconds. Workaround: for critical emissive light sources, add a Point/Spot Light with Cast Shadows disabled as a backup. The emissive controls appearance; the light actor drives GI ([Unreal Fest Gold Coast 2024](https://www.youtube.com/watch?v=szgnZx2b0Zg)).

#### Baked Lighting — When It Still Makes Sense

Lumen and baked lighting cannot coexist in UE5. However, baked GPU Lightmass still makes sense in tight corridors and interiors without dynamic objects (quality above 40 FPS cost), or on older platforms. A hybrid technique without Lumen: static lights for background, Moveable only for dynamic sources (flashlight, fire).

---

### Virtual Shadow Maps

Virtual Shadow Maps (VSM) is the shadow system in UE5 — conceptually a 16k×16k shadow per light, divided into 128×128 px pages.

#### Page Pool — The Most Common Mistake

All active pages live in a single `page pool` texture. The default size of 4096 pages (256 MB) is appropriate for linear games, but far too small for open-world projects with World Partition. An overflowed page pool produces visible stippling patterns in shadows when rotating the camera, with warnings in `stat VirtualShadowMapCache` ([StraySpark VSM Deep Dive](https://www.strayspark.studio/blog/virtual-shadow-map-optimization-open-worlds-ue5-7)).

```ini
[/Script/Engine.RendererSettings]
; Open world PC/next-gen:
r.Shadow.Virtual.MaxPhysicalPages=8192   ; 512 MB

; Steam Deck / low-end PC:
r.Shadow.Virtual.MaxPhysicalPages=4096
```

Diagnostics:
```
stat VirtualShadowMapCache             ; look for "Physical page pool overflow"
r.Shadow.Virtual.Cache.DrawInvalidatingBounds 1  ; green boxes = what's invalidating the cache
r.Shadow.Virtual.Visualize 1          ; mode 2 = Page Allocation (green = cached, red = new)
```

#### Foliage + VSM — WPO Shadow Cost

The most impactful VSM optimization in foliage-heavy scenes: disable WPO evaluation for shadows on small vegetation. Players cannot tell that grass shadows aren't swaying. In a PS5 test, disabling WPO shadow for floor foliage reduced the cost from 8.2 ms to 3.1 ms. One checkbox ([StraySpark VSM Blog](https://www.strayspark.studio/blog/virtual-shadow-map-optimization-open-worlds-ue5-7)).

```ini
; Per-mesh or Foliage Type:
; Details → Rendering → Evaluate World Position Offset (Shadow) = Off

; CVar for non-Nanite foliage in coarse pages:
r.Shadow.Virtual.NonNanite.IncludeInCoarsePages=0

; Page recycling during fast WP streaming:
r.Shadow.Virtual.Cache.MaxFramesSinceLastUsed=20  ; default 60

; Cheaper new pages during camera movement:
r.Shadow.Virtual.Clipmap.ResolutionLodBiasDirectionalMoving=0.5

; Async compute (hides ~0.4ms):
r.Shadow.Virtual.UseAsync=1
```

#### VSM + Many Small Dynamic Lights

VSM generates a separate page pool for each local light. Many small Point Lights with Cast Shadows is catastrophic for performance — each one must maintain its own set of shadow pages. VSM is optimized for a directional light (sun) plus a few key lamps.

Trick: use a shadowless Point Light for ambient fill, plus one stronger light with shadows for hero props. In UE5.4+, MegaLights are available — designed for very large numbers of dynamic shadow-casting sources at a reasonable cost.

Clipmap tuning for directional light:
```ini
r.Shadow.Virtual.Clipmap.FirstLevel=6    ; default — finest level
r.Shadow.Virtual.Clipmap.LastLevel=20    ; reduce from 22 if you have horizontal fog
r.Shadow.Virtual.ResolutionLodBiasDirectional=0   ; 0 = full resolution (PC)
```

---

### Occlusion and Culling

Culling determines which objects reach the renderer at all. A well-configured culling setup reduces draw calls before the GPU ever sees them.

#### HZB Occlusion (Hierarchical Z-Buffer)

HZB is GPU-side dynamic occlusion culling — it checks whether an object's bounding box is hidden by depth data from the previous frame. Cheap for GPU-bound scenes, but introduces a "1-frame lag" in occlusion culling (ghost geometry during fast camera movement) ([YouTube: Culling & Occlusion in Unreal (2025)](https://www.youtube.com/watch?v=wOdpF4WMckE)).

```ini
r.HZBOcclusion=1       ; default 1 (enabled)
; Set to 0 to disable and test — if disabling improves stability,
; there is likely an HZB bug in that particular scene
```

#### Precomputed Visibility — Still Useful

Precomputed Visibility generates baked occlusion culling for enclosed environments (dungeons, interiors, corridors). It does not scale to open-world, but in corridors and rooms it reduces draw calls by 50–90% at near-zero CPU cost ([Epic Docs: Visibility and Occlusion Culling](https://dev.epicgames.com/documentation/unreal-engine/visibility-and-occlusion-culling-in-unreal-engine)).

Setup: enable `Enable Precomputed Visibility` in World Settings → place a `Precomputed Visibility Volume` → Rebuild Lighting or `Build → Precompute Static Visibility`.

When to use: excellent for dungeons, building interiors, and any enclosed spaces in indie games where open-world streaming is not needed.

#### Cull Distance Volumes

Cull Distance Volumes define culling distances for actors of a given size — for example, "cull objects with a bounding box < 50 cm after 20 m from camera." CPU-side culling = cheap. Excellent for dense interiors filled with small props.

Setup: drag a `Cull Distance Volume` into the scene → set the `Cull Distances` array: `[Size, Distance]` e.g. `[50, 2000]`. Use the `G` key (Game View) in the editor to see what is currently culled.

#### HISM vs ISM in the Nanite Era

In UE5 with Nanite, the instancing approach changes. HISM (Hierarchical Instanced Static Mesh) provides a hierarchical structure for CPU-side LOD and culling — useful for non-Nanite geometry. Plain ISM without a hierarchy is recommended for Nanite meshes, because Nanite moves LOD and culling to the GPU, making the HISM hierarchy redundant and wasteful of CPU time ([Epic Forums: When to Use Level Instance, PLA, ISM/HISM](https://forums.unrealengine.com/t/when-to-use-level-instance-packed-level-actor-or-ism-hism-in-ue5/2681508)).

- Nanite meshes → ISM (or Runtime Cell Transformer with automatic batching)
- Non-Nanite foliage / decorations → HISM (hierarchical LOD and occlusion)

---

### Level Workflow: Level Instances, ISM/HISM, FastGeo

#### Level Instances and Packed Level Actors

A Level Instance (LI) is a nested level used multiple times. A Packed Level Actor (PLA) is a Blueprint generated from an LI where all identical meshes are batched as ISM. A PLA with 20 instances of the same model = one draw call via ISM. Without PLA = 20 draw calls ([KitBash3D Guide](https://help.kitbash3d.com/en/articles/12038349-a-quick-guide-packed-level-actors-level-instancing-in-unreal-engine-with-kitbash3d)).

| | Level Instance | Packed Level Actor |
|---|---|---|
| Contents | Anything (light, blueprint, mesh) | Visual only (static meshes) |
| Batching | No automatic batching | Automatic ISM for repeated meshes |
| Gameplay logic | Yes | No (do not use for gameplay) |
| Editability | In-place (embedded) | Via editing the base LI |

#### Runtime Cell Transformers — Automatic ISM Batching

Runtime Cell Transformers (RCT, UE5.5) collect all immutable (unreferenced, static mobility) meshes in the same cell and group them under a single ISM component. Works automatically at cook time and in PIE with no manual art work required ([Epic Forums](https://forums.unrealengine.com/t/when-to-use-level-instance-packed-level-actor-or-ism-hism-in-ue5/2681508)).

Rule: make sure decorative static meshes are set to Static mobility and have no direct references from other actors — RCT can then batch them automatically.

#### FastGeo Plugin (UE5.6, Experimental)

FastGeo replaces static mesh actors with lighter instances, reducing the runtime UObject count. Do not use it on actors with gameplay logic — mark those objects with the `NoFastGeo` tag.

---

## Part 2: Blueprints

### Tick: The Biggest Performance Killer

Every Blueprint Actor has "Start with Tick Enabled" on by default. In a scene with 200 actors that have Event Tick wired up — even to a single Branch node — you pay for 200 per-frame virtual dispatch calls. According to [Outscal's Timers vs Tick guide](https://outscal.com/blog/unreal-engine-timers-vs-tick), this single practice delivers the most consistent performance gains of any Blueprint optimization.

Core rules:

- In Class Defaults → Actor Tick → Start with Tick Enabled: uncheck for every actor that does not need per-frame updates.
- Use `Set Actor Tick Enabled` (or `Set Component Tick Enabled`) to enable tick only when required.
- In C++: `PrimaryActorTick.bCanEverTick = false;` in the constructor as the default.
- For logic running every 100–200 ms (AI perception, health regen checks): set Tick Interval (secs) to e.g. `0.1`. Do not set it lower than `0.05` — you may execute Tick multiple times per frame and lose all the savings ([CBgameDev tick optimization guide](https://www.cbgamedev.com/blog/quick-dev-tip-74-ue4-ue5-optimising-tick-rate)).

An important initialization sequence pitfall — the correct way to control tick at runtime:

```cpp
// C++ — must be false at construction time:
PrimaryActorTick.bCanEverTick = true;
PrimaryActorTick.bStartWithTickEnabled = false; // start disabled

void AMyActor::BeginPlay()
{
    Super::BeginPlay();
    SetActorTickEnabled(true); // now safe to enable/disable
}
```

Getting the order wrong can cause `SetActorTickEnabled(false)` in BeginPlay to be overwritten by the actor initialization sequence ([Epic Forums — SetActorTickEnabled bugged](https://forums.unrealengine.com/t/setactortickenabled-bugged/357835)).

UE5.5 adds the `tick.AllowBatchedTicks` CVar — when enabled, the engine groups similar tick functions and dispatches them to the Task Graph as batches, reducing per-tick overhead for actors with many instances ([Tom Looman — UE 5.5 Performance Highlights](https://tomlooman.com/unreal-engine-5-5-performance-highlights/)).

---

### Events Instead of Polling

The classic polling anti-pattern:
```
Event Tick → Branch (Is Health <= 0?) → [true] Trigger Death
```
This runs even when health = 100%.

The correct approach: call `[HealthChanged Dispatcher]` only when health actually changes. Interested actors bind once in BeginPlay and react only when they receive a notification. This is architecturally the Observer pattern.

Full mechanism selection table:

| Mechanism | Direction | Coupling | Use Case |
|---|---|---|---|
| Event Dispatcher | One → Many (broadcast) | Loose (sender doesn't know listeners) | Score updates, player death, level events |
| Blueprint Interface (BPI) | One → One/Many (message) | Loose (caller doesn't know receiver type) | "Can this actor be interacted with?" |
| Direct Cast | One → One | Tight (hard reference, memory inflation) | Internal communication within the same module |

Key interface pitfall: if an interface function takes or returns a typed Blueprint class as a parameter, the Blueprint VM still loads that class into memory. The escape is to use more general base types ([Reddit hard/soft ref thread](https://www.reddit.com/r/unrealengine/comments/1bqbhwi/about_hard_and_soft_references/)).

Game Instance Dispatcher pattern: place global game events (currency change, pause) as Event Dispatchers on a `UGameInstanceSubsystem` (C++) or directly on the GameInstance Blueprint. Any Blueprint can bind without Tick and survives level transitions ([Global EventDispatchers in GameInstance](https://forums.unrealengine.com/t/global-eventdispatchers-in-gameinstance/485353)).

Tick Groups — if Actor B reads a position set by Actor A, and both are in the same tick group, order is non-deterministic. Use `Add Tick Prerequisite Actor` sparingly — prerequisites trigger a TArray sort every frame in the worst case ([Epic Forums: Tick Group vs Tick Prerequisite](https://forums.unrealengine.com/t/tick-group-vs-tick-prerequisite/1728813)).

---

### Casting Pitfalls

**This is the most important memory concept in Blueprint development.**

When you place `Cast To BP_Enemy` anywhere in a Blueprint graph, the VM reads the entire `BP_Enemy` class — including all of its hard-referenced assets (meshes, textures, sounds, materials) — into memory at the time the owning Blueprint loads. This happens even if the cast branch never executes at runtime.

A single `Cast To BP_PlayerCharacter` in a UI widget means the entire character class (and everything it references) is loaded when the widget loads. Chains of these references throughout a project can easily reach hundreds of megabytes of unexpected memory usage ([Intax's Blueprint VM performance guide](https://intaxwashere.github.io/blueprint-performance/)).

Audit tool: right-click any asset in the Content Browser → `Size Map`. Tom Looman recommends running this on Blueprints and levels early and often ([Tom Looman optimization talk](https://tomlooman.com/unreal-engine-optimization-talk/)).

Soft Object References and Soft Class References:
- A `Soft Class Reference to BP_Enemy` variable stores only the asset path as a string — nothing is loaded until you explicitly resolve it.
- Pitfall: if you call `Load Asset` and wire the result into `Cast To BP_Enemy`, the VM will still load `BP_Enemy` at Blueprint compile time. Escape: use a lighter base class for the soft reference (e.g. `Soft Class Reference to Actor`) and cast to the specific type only after the async load completes.

When direct casting is acceptable: within the same module (e.g. a Component casting to its owning actor), or when the reference cost has already been paid and the result is cached in a variable (cast once in BeginPlay, store the result). Never scatter `Cast To BP_PlayerCharacter` across dozens of unrelated Blueprints.

---

### Garbage Collection in Blueprints

UE5's GC collects all objects derived from `UObject` when no live `UPROPERTY` pointer references them. In Blueprint, all variables are the equivalent of `UPROPERTY` — they keep referenced objects alive.

Dangling reference pitfall: after calling `Destroy Actor`, a stored reference to that actor becomes invalid. The Blueprint variable still holds a non-null pointer to the "pending kill" object. Always check `Is Valid` before using a stored actor reference.

However, polling `Is Valid` in Tick to manage object lifetime is itself a code smell. Prefer:
- Delegates/callbacks on destruction — the owner receives an event when the referenced object is destroyed.
- Weak Object References — these do not prevent GC; they become null automatically when the object is collected.

GC Clusters: in UE5, GC groups related objects into clusters for batch collection. This means you cannot partially unload a cluster — the entire group unloads together. Relevant during level streaming and async loading subsystems.

---

### Construction Script

The Construction Script (CS) runs on every property change in the Details panel, every time an actor is moved in the editor, and at level load time. Spawning actors in the CS creates orphaned actors in the level on every re-run.

What not to do in the Construction Script:

- Spawn actors (use Child Actor Components instead).
- Expensive async operations — they block the editor thread.
- Fetch references to other actors — they may not exist when the CS runs at level load.
- Modify level state — the CS has no guaranteed execution order relative to other actors.

For logic that is only expensive in-editor: wrap it in an `Is in Editor` check (from `KismetSystemLibrary`), or in C++ use a `#if WITH_EDITOR` guard inside `OnConstruction()`.

---

### Replication

#### Replicated vs RepNotify

| Variable Mode | Behavior | Use Case |
|---|---|---|
| Replicated | Value syncs to clients; no callback | Movement speed, passive stats |
| RepNotify (ReplicatedUsing) | Value syncs + calls `OnRep_VarName()` on clients | UI-visible state (health bar), one-shot effects |

RepNotify is event-driven and avoids polling. It replays correctly for late-joining clients (they receive the current value on connection, triggering the RepNotify function). RPCs fire once — a late-joining client misses any RPC called before they connected.

#### Actor Dormancy — An Underrated Optimization

Without dormancy: ~15 ms overhead per actor, 99.3% waste rate. With `DormantAll`: 0.13 ms, zero waste ([Reddit UE5 dormancy benchmark](https://www.reddit.com/r/UnrealEngine5/comments/1lzi6xg/networking_optimization_in_unreal_engine_5_with/)). For static or rarely-changing actors (barrels, furniture, world props), dormancy eliminates the constant replication overhead.

```
DORM_Never        — always replicates (default)
DORM_DormantAll   — dormant to all connections; call FlushNetDormancy() when state changes
DORM_DormantPartial — per-connection dormancy control
```

Blueprint nodes: `Set Actor Net Dormancy`, `Flush Net Dormancy`.

#### The Most Common Networking Mistake

Forgetting to check "Replicates" in the actor's Class Defaults. Without this flag, the entire actor replication system is disabled — no variable replicates, no RPC works. Always verify: Class Defaults → Replication → Replicates = true.

Adaptive Net Update Frequency: `net.UseAdaptiveNetUpdateFrequency 1` — when enabled, the engine dynamically lowers the update rate to `MinNetUpdateFrequency` when no properties have changed ([Matt Gibson's replication settings guide](https://mattgibson.dev/blog/unreal-replication-settings)).

---

### Anti-Patterns in Blueprints

#### `Get All Actors Of Class` — The Biggest Anti-Pattern

`Get All Actors Of Class` iterates the entire actor list of the current world, building a new TArray on every call. Called in Tick or on frequent events — catastrophic for performance ([r/UnrealEngine5 thread](https://www.reddit.com/r/UnrealEngine5/comments/1kzvzt0/i_hate_get_actor_of_class/)).

Correct alternatives:
- Manager/Subsystem registration: actors register themselves in GameMode or GameState in BeginPlay and unregister in EndPlay. The manager holds a typed TArray. Zero lookup cost.
- Overlap/collision events: for "all enemies within radius," use `SphereTraceMulti` or `GetOverlappingActors` on a collision component — spatially accelerated.

#### Pure Functions — Multiple Executions

A "Pure" Blueprint node (green, no execution pins) is re-evaluated every time its output is consumed by a downstream node. If you wire a costly pure function's output into three nodes, the function executes three times ([UE Forums on pure function overhead](https://forums.unrealengine.com/t/multi-output-pure-functions-inefficient/21278)).

Fix: call the function once as an impure (non-pure) call, cache the output in a local variable, then consume the variable. Or right-click the pure node → Convert to Impure.

#### Other Pitfalls

- `ForEachLoop` without early exit: use `ForEachLoopWithBreak` with the Break pin connected.
- `Make Array` inside Event Tick: heap allocation every frame, GC pressure. Pre-allocate as a member variable.
- `Delay` for cancellable timed logic: cannot be cancelled. Use `Set Timer by Event` with a stored handle.
- `Sequence` node: all outputs fire synchronically in the same frame — this is NOT a way to spread work over time.

---

### Lesser-Known Tricks

**Validated Get — the green pin:** instead of `[Variable] → Is Valid → Branch → [True] → Get Variable`, right-click the variable getter → `Convert to Validated Get`. One node with `Is Valid` and `Is Not Valid` exec outputs. Reduces graph clutter by ~3 nodes per validity check.

**Instance Editable + Expose on Spawn:** the variable appears as an editable field on every placed level instance AND as an extra input pin on `Spawn Actor from Class`. Eliminates post-spawn setter calls and makes spawn configuration self-documenting.

**Data Tables + Primary Asset IDs:** define data in a DataTable (CSV/JSON). The same `BP_Enemy` class handles 100 enemy types by reading stats from a DataTable row in BeginPlay. Combine with Asset Bundles: load only the "UI" bundle (icon, name) at the shop menu; the full "Actor" bundle (mesh, animations) only at spawn ([Tom Looman Asset Manager guide](https://tomlooman.com/unreal-engine-asset-manager-async-loading/)).

**Editor Utility Widgets:** EUWs are full UMG UIs with Blueprint logic that run only in the editor. Practical uses: bulk-rename assets, apply materials to selected static meshes, generate DataTable rows from a spreadsheet-like interface, validate naming conventions across the project.

**Find in Blueprints (Window → Find in Blueprints):** project-wide search across all Blueprint assets. In UE5.4+: right-click a function call → "Find References" generates a pre-filtered query for that exact function. Use for auditing `Get All Actors Of Class` before shipping.

**Blueprint Diffing:** right-click a Blueprint → Revision Control → Diff Against Depot. Binary `.uasset` files cannot be diffed with standard tools. Requires a source control plugin (Perforce, Git, Plastic SCM) ([Kokku Games Blueprint diff guide](https://kokkugames.com/tutorial-stop-guessing-what-changed-in-your-blueprintsgit-blueprint-diff-inside-unreal-engine/)).

---

## Part 3: C++ and Systems Programming

### Profiling — Unreal Insights in Practice

Unreal Insights replaces the older Session Frontend. Choose trace channels before profiling:

| Goal | Command-line / CVar |
|---|---|
| CPU + default | `-trace=default` |
| Memory allocations | `-trace=memory_light,memtags` |
| Full memory + asset metadata | `-trace=memory,metadata,assetmetadata` |
| Named events (class/actor detail) | `-statnamedevents` (~20% overhead — targeted use only) |
| Asset load timing | `loadtime,assetloadtime` |

`Trace.RegionBegin` / `Trace.RegionEnd` (UE5.5+): tag custom multi-frame regions directly on the Insights timeline ([Tom Looman — UE 5.5 Performance Highlights](https://tomlooman.com/unreal-engine-5-5-performance-highlights/)).

Memory snapshot: `Trace.SnapshotFile` captures a point-in-time snapshot during a live session. For the best asset breakdown, define `LLM_ALLOW_ASSETS_TAGS=1` in `.target.cs`. `Memreport -full` is still available, but Epic treats it as a legacy tool — Memory Insights is the actively developed path ([Epic Forums — Memreport visualization](https://forums.unrealengine.com/t/visualisation-tools-for-memreport-output/2587594)).

Profiling macro comparison:

| Macro | Visible in | Overhead | When to Use |
|---|---|---|---|
| `SCOPE_CYCLE_COUNTER(STAT_X)` | Stats System + Insights | Low | General CPU timing, always-on in non-shipping |
| `TRACE_CPUPROFILER_EVENT_SCOPE_STR("X")` | Insights CPU track | Low | Fine-grained function scopes in Insights |
| `SCOPED_NAMED_EVENT(Name, Color)` | Insights + Stats | Medium | Targeted investigations |
| `TRACE_BOOKMARK(TEXT("X"))` | Insights timeline | Minimal | Frame markers, event timestamps |

---

### Threading and Async (UE::Tasks, ParallelFor, FRunnable)

| System | Best For | Notes |
|---|---|---|
| `UE::Tasks` (UE5 new API) | Dependent task graphs, modern C++ | Cleaner API; same backend scheduler as TaskGraph |
| `TaskGraph` (`FFunctionGraphTask`) | Legacy code, dependent graphs | Being replaced by `UE::Tasks` |
| `AsyncTask` / `Async()` | Fire-and-forget background work | `EAsyncExecution::Thread` = dedicated OS thread |
| `FRunnable` / `FRunnableThread` | Long-lived, persistent background threads | Higher overhead; prefer for continuous systems |
| `ParallelFor` | Data-parallel loops | Uses the Task system; avoid TMap writes inside the body |

Short `FRunnable` threads carry more overhead than queuing to the Task pool. `ParallelFor` loses its benefit if iterations contain contended writes — a TMap write inside a parallel body is almost always slower than sequential execution ([Epic Developer Docs — Tasks System](https://dev.epicgames.com/documentation/unreal-engine/tasks-systems-in-unreal-engine)).

Golden rule for thread safety with UObjects: never read or write `UObject` properties from a worker thread without explicit guards. GC can run concurrently and invalidate objects.

```cpp
// 1. FGCScopeGuard prevents GC during worker access:
{
    FGCScopeGuard GCGuard;
    MyUObject->DoReadOnlyThing();
}

// 2. TStrongObjectPtr for thread-safe pinning of UObject lifetime (UE5.5+: lighter):
TStrongObjectPtr<UMyObject> PinnedObject(MyObject);
AsyncTask(ENamedThreads::AnyBackgroundThreadNormalTask, [PinnedObject]() {
    PinnedObject->DoWork();
});

// 3. Marshal results back to the GameThread:
AsyncTask(ENamedThreads::GameThread, [Result]() {
    // Apply results to UObjects here
});
```

Use `FCriticalSection` + `FScopeLock` (not `std::mutex` — it may use MSVC/Clang debug checks that conflict with UE memory tracking). Use `FRWLock` when reads significantly outnumber writes ([Georgy's Tech Blog — How to use mutex](https://georgy.dev/posts/mutex/)).

---

### Memory and GC (TObjectPtr, TWeakObjectPtr, Clusters)

#### TObjectPtr — UE5 Replacement for Raw Pointers

`TObjectPtr<T>` is the UE5 replacement for raw `T*` in `UPROPERTY` class members. In shipping builds it compiles down to a raw pointer with zero overhead. In editor builds it adds access tracking, lazy-load support, and better diagnostics ([UE Forums — Why use TObjectPtr?](https://forums.unrealengine.com/t/why-should-i-replace-raw-pointers-with-tobjectptr/232781)).

```cpp
UPROPERTY(EditAnywhere)
TObjectPtr<UMeshComponent> MeshComponent;

// Enforce project-wide in YourGameEditor.Target.cs:
NativePointerMemberBehaviorOverride = PointerMemberBehavior.Disallow;
```

Critical in UE5.4: incremental GC requires that all `UPROPERTY` members use `TObjectPtr` — raw pointers can cause premature collection.

#### TWeakObjectPtr — Hot-Path Optimization

`TWeakObjectPtr::Get()` and `IsValid()` have nearly identical implementations — both index into `GUObjectArray` (likely a cache miss). Hot-path pitfalls:

```cpp
// BAD: checks validity 3 times (IsValid + Get + null check)
if (WeakPtr.IsValid()) { UObject* Obj = WeakPtr.Get(); if (IsValid(Obj)) ... }

// GOOD: single dereference with null check
if (UObject* Obj = WeakPtr.Get()) { Obj->Foo(); Obj->Bar(); }

// BAD in loops: constructs TWeakObjectPtr on every iteration via operator==
for (auto& W : WeakPtrArray) { if (W == SomeObject) ... }

// GOOD: pre-construct outside, use HasSameIndexAndSerialNumber
TWeakObjectPtr<UObject> SearchFor(SomeObject);
for (auto& W : WeakPtrArray) { if (W.HasSameIndexAndSerialNumber(SearchFor)) ... }
```

Source: [George Prosser — Optimizing TWeakObjectPtr Usage](https://prosser.io/optimizing-tweakobjectptr-usage/)

#### GC Clusters

GC clusters reduce the marking phase cost by grouping objects with the same lifetime. Once grouped, GC traverses the cluster root rather than each member individually. Enabling `gc.AssetClusteringEnabled 1` and Blueprint clustering in Project Settings > Engine > Garbage Collection saves 50%+ of marking time for clustered objects ([UE Forums — GC Internals](https://forums.unrealengine.com/t/knowledge-base-garbage-collector-internals/501800)).

```cpp
void UMyDataAsset::PostLoad()
{
    Super::PostLoad();
    CreateCluster(); // Scans all sub-objects and groups them
}
```

Keep the live UObject count below ~200k as a good general practice.

---

### UObject Pitfalls (NewObject, CDO, Live Coding)

#### NewObject and Choosing an Outer

```cpp
// Always provide the correct Outer — it controls lifetime and GC visibility:
UMyData* Data = NewObject<UMyData>(this);          // owned by this object
UMyData* Transient = NewObject<UMyData>(GetTransientPackage()); // no persistent owner

// NEVER use NewObject inside a constructor — use CreateDefaultSubobject:
MyComponent = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("MeshComp"));

// Runtime (after construction):
MyComponent = NewObject<UStaticMeshComponent>(this, TEXT("MeshComp"));
MyComponent->RegisterComponent();
```

#### CDO Traps and Blueprint Inheritance

The Class Default Object (CDO) is created once per class at engine startup. The constructor runs only for the CDO — every subsequent instance is a copy of the CDO. This means:

- Never put runtime logic in constructors (map lookups, asset loads, actor queries).
- Renaming a `CreateDefaultSubobject` component between hot reloads corrupts Blueprint assets derived from that class.
- Adding or removing `UPROPERTY` members requires a full editor restart — Live Coding handles this incorrectly and can cause Blueprint corruption or crash-on-open ([unrealcommunity.wiki — Hot Reload and Live Coding](https://unrealcommunity.wiki/live-compiling-in-unreal-projects-tp14jcgs)).

#### Live Coding — What Is Actually Safe

Live Coding is safe ONLY for changes inside function bodies (`.cpp` files, non-UPROPERTY logic). Operations that require a full editor restart:

- Adding or removing `UPROPERTY` or `UFUNCTION` declarations
- Changing `UPROPERTY` types or names
- Adding or removing virtual functions
- Changing struct layouts in replicated structs
- Modifying `CreateDefaultSubobject` names

---

### Containers (TArray, TInlineAllocator, FName, FStringView)

#### TArray — Performance Patterns

```cpp
// Pre-allocate before bulk inserts:
TArray<FHitResult> Hits;
Hits.Reserve(64);

// Emplace instead of Add — constructs in-place (avoids copies):
Hits.Emplace(/* constructor args */);

// Reset (keeps allocation) vs Empty (frees it):
Hits.Reset(); // faster when reused each frame
```

`TInlineAllocator` — small fixed-count arrays on the stack:
```cpp
// Elements stored inline with the TArray object (on the stack if TArray is local):
TArray<FVector, TInlineAllocator<8>> LocalPoints;
// When count exceeds 8, falls back to heap; all elements are copied
// Pass to functions via TArrayView:
void ProcessPoints(TArrayView<FVector> Points);
```

#### FName vs FString vs FText

| Type | Storage | Comparison | When to Use |
|---|---|---|---|
| `FString` | Heap-allocated `TArray<TCHAR>` | O(n) | Dynamic text construction, I/O |
| `FName` | Global name table index | O(1) integer | Asset names, identifiers, map keys |
| `FText` | Immutable + localization metadata | O(?) | User-facing UI strings, localization |

Two `FName` pitfalls:
- The name table is NEVER GC'd — every unique string added at runtime grows it forever. With procedurally generated names in long sessions, the table can consume significant memory ([Reddit — C++ FName, FString, FText](https://www.reddit.com/r/unrealengine/comments/wqox8w/c_fname_fstring_ftext_when_to_use_each_of_these/)).
- Constructing an `FName` from a string literal in a hot path is unexpectedly expensive — it acquires a thread lock and searches the name table:

```cpp
// BAD: constructs FName from string on every call:
void MyFunc() { GetBoneRotation(TEXT("spine_01")); }

// GOOD: static local initialized once:
void MyFunc() {
    static const FName SpineBone(TEXT("spine_01"));
    GetBoneRotation(SpineBone);
}
```

`FStringView` (UE5): a non-owning view over an existing string buffer. Use it as the parameter type in functions to prevent implicit `FString` copies.

---

### Networking (Push Model, Iris, FFastArraySerializer)

#### Push Model Replication

Legacy replication polls all properties every frame. The push model skips the poll — properties only replicate when you explicitly mark them dirty:

```cpp
// GetLifetimeReplicatedProps:
FDoRepLifetimeParams Params;
Params.bIsPushBased = true;
DOREPLIFETIME_WITH_PARAMS_FAST(AMyActor, Health, Params);

// Setter — MARK_PROPERTY_DIRTY on every change:
void AMyActor::SetHealth(float NewHealth)
{
    Health = NewHealth;
    MARK_PROPERTY_DIRTY_FROM_NAME(AMyActor, Health, this);
}
```

Add `NetCore` to your module's dependencies or you will get a linker error on `UEPushModelPrivate::MarkPropertyDirty`.

#### FFastArraySerializer for Large Arrays

Standard TArray replication sends the entire array on every change. `FFastArraySerializer` tracks per-element dirty keys and sends only deltas ([ikrima.dev — Fast TArray Replication](https://ikrima.dev/ue4guide/networking/network-replication/fast-tarray-replication/)).

Pattern: the Item struct inherits `FFastArraySerializerItem` → the List struct inherits `FFastArraySerializer` → mark dirty via `MarkItemDirty(Items[Idx])`.

#### Iris (UE5.4+, Default from 5.5+)

Iris is a rewrite of the replication data layer. It separates gameplay from networking by building replication state descriptors per class instead of polling raw UObject property memory. Existing UPROPERTY replication, RepNotify, and RPCs work unchanged.

```ini
; DefaultEngine.ini:
net.Iris.UseIrisReplication=1
```

---

### Compile Speed (IWYU, Unity Build)

IWYU (Include What You Use) — every `.cpp` includes only what it actually uses:

```csharp
// In the module Build.cs:
PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
```

Avoid `#include "Engine.h"` and `#include "UnrealEd.h"` — these monolithic headers pull in tens of thousands of lines and destroy PCH efficiency ([kantandev.com — UE4 Includes, PCH, and IWYU](http://kantandev.com/articles/ue4-includes-precompiled-headers-and-iwyu-include-what-you-use)).

Setting `bFasterWithoutUnity = true` in a specific module's `Build.cs` disables unity batching only for that module — useful for modules in constant flux without penalizing the entire build.

Module organization: split a large codebase into many small modules = greater build parallelism and smaller cascading recompiles. A change in a leaf module does not rebuild parents if the public interface is unchanged.

---

### Common Mistakes and Lesser-Known Tricks

**Dangerous dangling delegates and lambda captures:**
```cpp
// DANGEROUS: if 'this' is GC'd before the timer fires, crash:
GetWorldTimerManager().SetTimer(Handle, [this]() { DoThing(); }, 1.f, false);

// SAFE — AddWeakLambda:
SomeDelegate.AddWeakLambda(this, [this]() { DoThing(); });

// SAFE — explicit weak pointer:
auto WeakThis = MakeWeakObjectPtr(this);
GetWorldTimerManager().SetTimer(Handle, [WeakThis]() {
    if (WeakThis.IsValid()) WeakThis->DoThing();
}, 1.f, false);
```

**`!= nullptr` vs `IsValid()`:** these are not equivalent for `UObject*`. A destroyed (BeginDestroy) actor will pass `!= nullptr` but will not pass `IsValid()`.

**Never use `std::shared_ptr<UObject>`:** GC has no knowledge of `std::shared_ptr` ref counts — it can collect and destroy an object while the `shared_ptr` still holds ref-count = 1, leading to a double-free ([unrealcommunity.wiki — Memory Management](https://unrealcommunity.wiki/memory-management-6rlf3v4i)).

**`FAutoConsoleVariableRef` — live tuning without recompilation:**
```cpp
namespace MySystem
{
    static float CollisionRadius = 120.f;
    static FAutoConsoleVariableRef CVar_CollisionRadius(
        TEXT("my.CollisionRadius"),
        CollisionRadius,
        TEXT("Radius used by proximity check system"),
        ECVF_Scalability
    );
}
```

Any change to `my.CollisionRadius` in the console or `.ini` is immediately reflected in `CollisionRadius`. For thread-safe reads from worker threads, use `ECVF_RenderThreadSafe`.

**`WITH_EDITOR` vs `WITH_EDITORONLY_DATA`:**
- `WITH_EDITOR` — editor + EditorOnly builds; for editor-only code.
- `WITH_EDITORONLY_DATA` — all desktop platforms (even non-editor); for editor-only data fields in `UCLASS`/`USTRUCT`.

Prefer `WITH_EDITORONLY_DATA` for data fields to avoid binary bloat in shipping.

**GameplayDebugger Module:** overlay runtime debug information in-game without polluting shipping code. Activated via numpad `'`. Gate an entire category class with `#if WITH_GAMEPLAY_DEBUGGER` — it is stripped in shipping ([UE Forums — How to use Gameplay Debugger](https://forums.unrealengine.com/t/how-to-use-gameplay-debugger/13902)).

---

## Part 4: Tech Art

### Materials — Permutation Explosion and How to Stop It

Material Instances (MIC) allow changing scalar, vector, and texture parameters without recompiling shaders. In Nanite's deferred shading bin system, every unique shader (not every unique mesh) requires its own shading bin before rasterization. Minimizing unique shaders matters far more than geometry count in a Nanite scene ([Tech-Artists.Org draw call deep dive](https://www.tech-artists.org/t/draw-call-optimization-in-ue5/18217)).

#### Permutation Explosion

Every Static Switch Parameter in a master material doubles the number of compiled shader permutations. With N static switches you have up to 2^N permutations on disk — this balloons cook time, memory, and PSO loading stalls. Epic's Knowledge Base on shader permutations states it directly: every combination of settings and switches is a separate shader from the GPU's perspective ([Epic's Knowledge Base](https://forums.unrealengine.com/t/knowledge-base-understanding-shader-permutations/264928)).

Key pitfall: a `Switch Parameter` (dynamic, not static) does NOT eliminate branches — both sides are compiled and evaluated. In Shader Complexity view you can clearly see that a disabled dynamic switch branch still burns instructions.

Rule: keep static switches below ~5 per master material. Use Material Layering or Material Functions to break up complexity instead of cramming everything into one monolithic graph.

`Material Quality Switch` routes execution through Low/Medium/High/Epic branches, controlled by `r.MaterialQualityLevel 0/1/2/3`. Use it to strip expensive features (normal map blending, distance-based roughness variation) on lower settings without maintaining separate materials.

---

### Custom HLSL and Custom Node Pitfalls

The Custom node lets you write raw HLSL inline — essential for packed texture decode, raymarching, complex math, and reducing spaghetti ([Ben Cloward's HLSL tutorial](https://www.youtube.com/watch?v=qaNPY4alhQs)).

Pitfalls:
- No material preview in the thumbnail — the graph must be applied to a mesh for testing.
- TEXCOORD overflow: limit of 8 UV interpolators (16 in UE5 with additional cost). Use the `Customized UVs` panel to pre-pack data into UV slots.
- Texture sampling syntax: `Texture2DSample(Tex, TexSampler, UV)` where the sampler is a separate input pin (TextureObject input). You cannot call `tex2D()` directly in SM5 pixel shaders.
- Unreal's HLSL compiler can aggressively unroll loops; dynamic iteration counts may not compile. Use the `[loop]` attribute if needed.
- Helper functions can be wrapped in a struct declaration or included via `#include "/Engine/Private/Common.ush"`.

---

### WPO and Pixel Depth Offset

#### World Position Offset (WPO) + Nanite

WPO was unsupported in early Nanite (UE5.0). Available from UE5.1, with significant improvements in UE5.4 where per-cluster WPO range culling was added.

Key setting: `Max World Position Offset Displacement` in the material. Nanite uses this to cull clusters that cannot be affected. Setting it too high disables culling; setting it to 0 disables WPO entirely for that material. This is the single most impactful WPO knob in production ([community optimization notes](https://www.reddit.com/r/UnrealEngine5/comments/1oqon6r/how_to_optimize_this_scene_more/)).

CVars for the WPO shadow cache:
```
r.Shadow.Virtual.Cache.MaxMaterialPositionInvalidationRange 10
r.Shadow.Virtual.NonNanite.IncludeInCoarsePages 0
```
The first limits the radius within which WPO movement invalidates VSM shadow cache pages — the main source of WPO performance regression on dense foliage.

Velocity buffer: materials with WPO must write per-vertex velocity for correct TSR/motion blur. Enable `Output Velocity` in the material properties (enabled by default for WPO).

#### Pixel Depth Offset (PDO)

PDO shifts pixel depth values inward, creating the illusion of surface displacement without real geometry. Problem: PDO modifies pixel positions in the G-Buffer, but does not run during the shadow depth pass. The shadow geometry stays on the original mesh surface, causing severe self-shadowing artifacts ([community thread on PDO shadow issues](https://forums.unrealengine.com/t/pixel-depth-offset-self-shadowing-issue/154799)).

Lumen ghosting: when PDO is active and Lumen's temporal GI is accumulating, displaced pixels cause smearing during camera movement.

Requirements: PDO forces materials off the Nanite fast path onto programmable rasterization, increasing rasterization overhead. Nanite Tessellation (UE5.3+) runs during shadow passes — it is a better alternative for cases that need displacement with correct shadows.

---

### Translucency

Translucent materials must render every overlapping layer. Stacking 5 translucent spheres produces deep red in Shader Complexity; 5 masked spheres stay green. Every translucent pixel samples the scene color behind it regardless of actual opacity.

Translucency lighting modes:
- `Volumetric Non-Directional` — cheapest, flat lighting
- `Surface Translucency Volume` — reads from the light propagation volume
- `Surface Forward Shading` — full PBR lighting, most expensive; required for correct specular on glass

Key optimization: use `Blend Mode: Masked` when the material only needs binary opacity. Masked runs a depth pre-pass and shades only surviving quads once. Translucent skips the depth pre-pass and shades every pixel every time.

Refraction forces a scene color capture (read-before-write) — very expensive. For distant or secondary materials, consider fake refraction via normal-mapped distortion without the full refraction pass.

Sorting: translucent objects are sorted back-to-front every frame — CPU cost scales with the number of translucent actors.

---

### Virtual Textures (SVT, RVT)

Streaming Virtual Textures (SVT) replace traditional texture streaming for large textures. Only the tiles visible at the current mip are resident in GPU memory.

Runtime Virtual Textures (RVT) are render targets that the landscape (or other objects) writes to every frame, while other objects read from them for blending. Primary uses: landscape blending (rocks/trees adopting the terrain's color/normal/roughness), decal stamping (footprints, mud), terrain-conforming roads.

Enabling RVT on a complex landscape can reduce landscape overdraw from orange/red in Shader Complexity to full green by caching expensive material evaluation ([Brushify RVT Bootcamp](https://www.youtube.com/watch?v=0-xXIMjlmqE)).

VT Pool Size tuning:
```
r.VT.PoolSizeScale 1.0       ; scale multiplier for all fixed pool sizes
r.VT.Residency.Show 1        ; on-screen HUD showing pool occupancy per format
r.VT.Residency.Notify 1      ; notification when the pool hits 100%
r.VT.DumpPoolUsage            ; dump page counts per texture asset
```

When VT thrashes: negative mip bias, zero-gradient sampling (UVs invariant to screen-space derivatives = hardware requests mip 0 tiles for the entire surface). Monitor with `r.VT.Residency.Show 1` — if the green (mip bias applied) value is non-zero, the engine is degrading texture resolution.

---

### Niagara — GPU vs CPU, Data Channels, Significance Manager

#### GPU vs CPU Sim Thresholds

CPU sims: good for < ~1000 particles, access to BP/C++ data, full event callbacks, collisions with the physics system.
GPU sims: > ~1000 particles, offload work to the GPU compute pipeline at low CPU cost. The GPU dispatch overhead means they only pay off above ~1000 particles.

"GPU emitters are only great if you're spawning a lot of particles (more than 1000). For 1–100 particles use a CPU emitter" ([practical Niagara optimization guides](https://morevfxacademy.com/complete-guide-to-niagara-vfx-optimization-in-unreal-engine/)).

From UE5.3+: GPU readback is possible — GPU particles can export data back to CPU/Blueprint at a cost. Always profile with `stat Niagara`.

#### Niagara Data Channels (UE5.3+)

NDC allows different Niagara systems to communicate asynchronously — one system writes data, another reads it in the same frame. It replaces the older event system for cross-emitter spawning patterns and global VFX state (e.g. a wind system publishing direction data read by all particle emitters).

Key limitation: NDC data is completely transient — it exists for a single tick. If you miss a frame, the data is gone ([Epic forum NDC discussion](https://forums.unrealengine.com/t/niagara-data-channel-niagara-emitters-not-taking-the-set-spawn-count/2599289)).

#### Significance Manager

The Significance Handler in the Effect Type determines which systems survive when the budget is exceeded. Built-in modes: `Distance` (closest to camera wins), `Age` (newest wins), `Custom` (Blueprint/C++).

Crash bug warning: with aggressive culling and short-lived systems dying simultaneously during significance processing, a crash can occur — fix details in [Epic's forum post on Niagara scalability crash](https://forums.unrealengine.com/t/niagara-scalability-crash-when-processing-significance/2611550).

#### Bounds for GPU Sims

GPU sims require fixed bounds — if the fixed bounds are off-screen, the GPU does not dispatch the compute shader and the effect disappears entirely. For travelling effects (projectile trails), expand bounds generously. Diagnostic: if a GPU effect disappears when rotating the camera, the bounds are too small.

#### GPU Compute Particles + Distance Fields

GPU particle collision uses the Global Distance Field — a coarse, scene-wide approximation with an effective range of ~10,000 units from the camera. Beyond that range, collisions become unreliable ([Niagara GPU distance field collision video](https://www.youtube.com/watch?v=-jf97_EIdHI)).

Particle Radius Scale: the default 0.1 is often too small for reliable collision detection. Increase to 1.0–5.0 for visible effects.

---

### Post-Process and Upscaling (TSR/DLSS/FSR)

Post-process effect costs:

| Effect | Approximate Cost | Notes |
|---|---|---|
| Bloom (Quality 6) | ~1–2 ms | Quality 0–2 significantly cheaper; 4+ uses convolution |
| Depth of Field (Cinematic) | ~2–4 ms | Gaussian DoF significantly cheaper |
| Motion Blur (Quality 4) | ~0.5–1 ms | Adds velocity buffer read + reconstruction pass |
| Chromatic Aberration | ~0.1 ms | Minor |
| Vignette | Negligible | |

```ini
r.MotionBlurQuality 0          ; 0=off, 4=max quality
r.DepthOfFieldQuality 0        ; 0=off, 4=max
r.BloomQuality 5               ; 0=off, 5=default, 6=convolution (expensive)
```

#### TSR vs DLSS vs FSR

TSR (Temporal Super Resolution) is Epic's built-in solution, fully integrated with Lumen, Nanite, and the velocity buffer. Best quality-to-compatibility ratio — no plugin required. Downside: can produce ghosting/smearing on fast-moving objects, particularly with WPO or PDO.

DLSS (NVIDIA) generally produces the best motion clarity at equivalent quality settings ([community comparisons](https://www.reddit.com/r/nvidia/comments/wb3dh4/dlss_vs_tsr_vs_fsr_20_motion_clarity_comparison/)). Requires an NVIDIA GPU + DLSS plugin. DLSS 3.5 with Ray Reconstruction improves denoising for Lumen.

FSR (AMD/cross-platform): widest hardware compatibility. Lower quality ceiling than DLSS/TSR; can produce artifacts on fine geometry and foliage. Use for minimum-spec targets.

All three temporal AA methods require accurate velocity vectors. WPO and PDO must write correct velocity (`Output Velocity` enabled) or temporal methods will ghost on those surfaces.

#### Auto-Exposure

Three metering modes: Manual (fixed EV100 — predictable, required for cutscenes), Histogram (physically correct), Basic (legacy averaging, confused by bright skyboxes).

UE5.1+ breaking change: the old `Min/Max Brightness` parameters were replaced by `Min/Max EV100`. Check exposure settings in projects migrated from UE4.

```ini
r.EyeAdaptation.MethodOverride -1|0|1|2   ; -1=none, 0=basic, 1=histogram, 2=manual
```

---

### Textures and Streaming Pool

The streaming pool is the VRAM cache for streamed textures. The default 1000 MB is often insufficient for open-world scenes:
```ini
r.Streaming.PoolSize 4096    ; 4 GB for high-end PC targets
```

Calibration method: temporarily set `r.Streaming.PoolSize 1`, fly through the level, note the peak warning value, use that value + a safety margin as the production setting ([TechArtHub's streaming pool guide](https://techarthub.com/fixing-texture-streaming-pool-over-budget-in-unreal/)). Never ship `r.Streaming.PoolSize 0` — it means "unlimited" and will crash the engine.

Texture compression:

| Format | Channels | Size | Best For |
|---|---|---|---|
| DXT1 / BC1 | RGB (no alpha) | 4 bpp | Opaque diffuse |
| BC4 | R only | 4 bpp | Single-channel masks, heightmaps |
| BC5 | RG | 8 bpp | Normal maps (stores XY, derives Z) |
| BC7 | RGBA | 8 bpp | High-quality diffuse with alpha |

UE5 uses BC5 by default for Normal Map compression — it stores only R and G (X and Y) and derives Z in the shader. Do not use BC7 for normal maps without manual shader handling — it can introduce decompression artifacts in the RG channels ([Rév O'Conner — Texture Compression](https://www.revoconner.com/post/texture-compression-for-unreal-engine-bcn-and-texture-packing)).

sRGB golden rule: normal maps must be linear (sRGB unchecked). Masks, roughness, metallic, AO — all linear. Albedo/Color — sRGB. Quick diagnostic: if a packed texture looks too dark or too bright, check sRGB first.

---

### Foliage and Nanite Foliage

Nanite foliage virtualizes triangle rendering, eliminating traditional LOD overhead. But Nanite does not support per-vertex WPO wind animation — enabling WPO on Nanite foliage forces programmable rasterization, negating the benefit.

Solutions for wind with Nanite:
1. Pivot Painter 2: bake pivot data into UV channels. The shader can be optimized by disabling unused Wind Settings groups (each disabled group removes instructions). This is the recommended production approach ([StraySpark Nanite foliage guide](https://www.strayspark.studio/blog/nanite-foliage-ue5-complete-guide)).
2. Hybrid LOD: LOD0 as a traditional mesh with WPO wind; LOD1+ as Nanite with instance-level sway only.
3. Per-Instance Custom Data: instance animation (rotation around the base pivot) for subtle swaying.

Procedural Foliage Spawner trap: enabling collision on procedurally spawned foliage kills performance (the physics engine iterates all instances). The Kite Demo deliberately has no foliage collision. Use a proximity sphere around the player with separate simplified collision proxies.

Foliage density scalability:
```ini
[FoliageQuality@0]
foliage.DensityScale=0.4
[FoliageQuality@2]
foliage.DensityScale=1.0
```

---

### Lesser-Known Tech Art Tricks

#### Custom Depth + Custom Stencil for Cheap Masks

The Custom Depth Pass renders selected actors to a separate depth buffer with no extra shading cost (depth only). Custom Stencil adds an 8-bit integer ID per actor.

Setup:
1. `Project Settings → Rendering → Custom Depth-Stencil Pass → Enabled with Stencil`
2. On the actor: `Rendering → Render Custom Depth Pass: ✓` and set `Custom Depth Stencil Value` (0–255).
3. In the post-process material: `Scene Texture → Custom Stencil` + component mask.

Uses: object outlines, see-through walls, decal masking (blood decal only on floors — stencil value 1 on floors, decal passes only when stencil == 1).

Cost: the Custom Depth pass adds a separate batch of draw calls for all marked actors. Keep the count low; do not enable it globally on thousands of props.

#### Material Attributes — Breaking the Shader Graph into Chunks

Enable `Use Material Attributes` on a material or function to collapse all inputs/outputs into a single `MaterialAttributes` pin. Use `BlendMaterialAttributes` to lerp between two attribute structs — ideal for layering. This lets you build the material graph as composable functions: `BaseLayer` → `WetnessLayer` → `SnowLayer`, all without spaghetti wire routing.

#### Shared Wrap Sampler — Going Beyond the 16-Sampler Limit

Hardware supports 16 texture sampler registers per shader. UE5's `Shared:Wrap` and `Shared:Clamp` share two engine-wide sampler states across all textures, allowing a material to reference up to 128 textures ([Reddit discovery thread](https://www.reddit.com/r/unrealengine/comments/3myppm/til_you_can_use_more_than_16_texture_samplers_by/)).

How to use: on any `Texture Sample` node, set `Sampler Source → Shared: Wrap` (or `Shared: Clamp`). Trade-off: all textures using the shared sampler must use the same wrapping mode. Landscape materials with many layers need this regularly.

When to use: when the material editor reports "too many texture samplers" or a landscape material requires more than 16 unique textures.

#### Render Targets for Cheap Procedural Effects

Render Targets let you run material evaluation and store the result as a texture for subsequent frames. Uses: procedural terrain masks, ripple simulations, trail/history effects.

Warning: GPU readback is expensive. Reading Render Target pixel data back to CPU via `ReadRenderTargetPixels` is synchronous and stalls the CPU-GPU pipeline — it can cost several milliseconds ([Froyok's Render Target performance analysis](https://www.froyok.fr/blog/2020-06-render-target-performances/)). Use `EnqueueCopy` (non-blocking async readback) for gameplay data and consume the result a frame later.

Use `Begin/EndDrawCanvasToRenderTarget` when performing multiple draws per frame to a render target — this reuses the FCanvas object instead of recreating it (which `DrawMaterialToRenderTarget` does, leading to O(N) allocations for N draws).

#### Quad Overdraw View Mode

`View → Optimization Viewmodes → Shader Complexity & Quads` reveals how many GPU quads (2×2 pixel groups) are wasted by sub-pixel triangles. When a triangle is smaller than one quad, the GPU still shades all 4 pixels — 75% wasted work. This is the primary reason high-poly assets without Nanite are expensive even when they are not prominent ([ArtStation blog on quad overdraw](https://daanmeysman.artstation.com/blog/7goy/keeping-your-games-optimized-part-1-triangles)).

#### LUT Packed Textures

Instead of sampling multiple 1-channel textures, pack them into a single RGBA texture and use component masks. This reduces the texture sampler count (critical at the 16-sampler limit) and improves cache coherence — one texture fetch returns four values.

Standard Substance Painter packing: R = AO, G = Roughness, B = Metallic. Set sRGB off on packed textures — all channels must be linear.

---

## Part 5: Top 20 Most Common Mistakes

| Mistake | Why It Hurts | Fix |
|---|---|---|
| Nanite on meshes < 300 triangles | Fixed clustering overhead outweighs the gains; 3 ms wasted | Disable Nanite on simple meshes; use ISM |
| Nanite Masked + WPO on foliage | Programmable Rasterizer + VSM shadow invalidation = 2–4x more expensive | Disable WPO shadow; set WPO Disable Distance; consider opaque geometry |
| Fallback Relative Error = 0 | Fallback mesh identical to original; 100–400 MB VRAM wasted | Set Fallback Triangle Percent = 1-5%, Relative Error = 1.0 |
| VSM Page Pool = 4096 in open world | Overflow = stippling shadows | Increase to 8192 (PC/PS5); monitor stat VirtualShadowMapCache |
| Dozens of Point Lights with Cast Shadows | Each local VSM light = its own shadow pages = page pool overflow | Fill lights without shadows; shadows only on key lights |
| Lumen without tuning ("Epic" scalability) | Settings calibrated for high-end benchmarks, not production | Lower DownsampleFactor, MaxRoughnessToTrace, TracingOctahedronResolution |
| Monolithic building mesh with an interior | Lumen does not generate Cards for the interior → pink GI artifacts | Build modularly: separate meshes for walls, floor, ceiling |
| Tick enabled by default on everything | 200 actors × 1 Branch node = 200 VM dispatch calls/frame | Uncheck Start with Tick Enabled; use Set Actor Tick Enabled when needed |
| `Get All Actors Of Class` in Tick | O(n) scan of the entire world every frame | Manager/Subsystem registration in BeginPlay/EndPlay |
| Cast To BP_PlayerCharacter everywhere | Entire class tree loaded into memory in every referencing Blueprint | Use BPI (Blueprint Interface); cache one cast in BeginPlay |
| Pure function wired to multiple nodes | Function executes N times (once per consumer) | Convert to impure; cache result in a variable |
| Spawning actors in the Construction Script | Orphaned actors on every property change | Child Actor Components; spawn in BeginPlay |
| `Delay` instead of Timer for cancellable logic | Cannot be cancelled; crash when actor is destroyed mid-delay | Set Timer by Event with stored handle + Clear Timer |
| TWeakObjectPtr::IsValid() + Get() in hot-path | Double validity check = double cache miss into GUObjectArray | `if (UObject* Obj = WeakPtr.Get()) { ... }` — single check |
| Raw UObject* without UPROPERTY across frames | GC can collect the object → dangling pointer | TObjectPtr<T> or TWeakObjectPtr + IsValid check |
| `this` in lambda delegates | Crash when actor is GC'd before lambda fires | AddWeakLambda or MakeWeakObjectPtr in capture |
| Static Switch > 5 per master material | 2^N permutations = ballooning cook time, PSO stalls | Max 5 switches; Material Layering for complexity |
| Missing `Replicates = true` on a networked actor | Zero replication, no RPCs work | Class Defaults → Replication → Replicates = true |
| `r.Streaming.PoolSize 0` (unlimited) | Engine crash | Always set an explicit MB value |
| HLOD on "Lowest Available LOD" for landscape | Grey blob in the distance — looks bad and is misleading | Set Specific LOD = 4-5 in HLOD Setups |

---

## Part 6: Key CVars Quick Reference

### Nanite

| CVar | Default | Description |
|---|---|---|
| `r.Nanite.MaxPixelsPerEdge` | 1 | Primary Nanite scaling knob; 2–4 on low/medium |
| `r.Nanite.Tessellation` | 0 | Enable tessellation (experimental) |
| `r.Nanite.DicingRate` | 2 | Tessellation density (higher = cheaper) |
| `r.Nanite.Streaming.StreamingPoolSize` | 512 | Nanite streaming pool (MB) |

### Lumen

| CVar | Default | Description |
|---|---|---|
| `r.Lumen.ScreenProbeGather.DownsampleFactor` | 1 | Lower GI resolution; 2 = large gains |
| `r.Lumen.ScreenProbeGather.TracingOctahedronResolution` | 2 | Lower = faster, noisier |
| `r.Lumen.Reflections.DownsampleFactor` | 1 | Half-res reflections; saves 1-2 ms |
| `r.Lumen.Reflections.MaxRoughnessToTrace` | 0.6 | Only shiny materials receive RT reflections |
| `r.LumenScene.FarField` | 0 | Enable Far Field for open worlds |
| `r.LumenScene.FarField.OcclusionOnly` | 0 | UE5.6: ~50% cheaper Far Field |
| `r.LumenScene.SurfaceCache.MeshCardsMinSize` | 4 | Minimum mesh size for Surface Cache |

### Virtual Shadow Maps

| CVar | Default | Description |
|---|---|---|
| `r.Shadow.Virtual.MaxPhysicalPages` | 4096 | Page pool size (increase to 8192 for open world) |
| `r.Shadow.Virtual.NonNanite.IncludeInCoarsePages` | 1 | Set 0 for heavy foliage scenes |
| `r.Shadow.Virtual.Cache.MaxFramesSinceLastUsed` | 60 | Reduce to 20 during fast WP streaming |
| `r.Shadow.Virtual.UseAsync` | 0 | Async compute; hides ~0.4 ms |
| `r.Shadow.Virtual.Clipmap.LastLevel` | 22 | Reduce when using horizontal fog |
| `r.Shadow.Virtual.ResolutionLodBiasDirectional` | 0 | 1.0 for Steam Deck |
| `r.Shadow.Virtual.Cache.MaxMaterialPositionInvalidationRange` | 10 | Limit WPO shadow invalidation radius |

### Materials and Rendering

| CVar | Default | Description |
|---|---|---|
| `r.MaterialQualityLevel` | 3 | 0=Low, 1=Medium, 2=High, 3=Epic |
| `r.BloomQuality` | 5 | 0=off, 5=default, 6=convolution |
| `r.MotionBlurQuality` | 4 | 0=off, 4=max |
| `r.DepthOfFieldQuality` | 4 | 0=off, 4=max |
| `r.EyeAdaptation.MethodOverride` | -1 | -1=none, 2=manual |

### Textures and Streaming

| CVar | Default | Description |
|---|---|---|
| `r.Streaming.PoolSize` | 1000 | Texture streaming pool (MB) — NEVER 0 |
| `r.VT.PoolSizeScale` | 1.0 | Scale multiplier for the VT pool |
| `r.VT.Residency.Show` | 0 | Pool occupancy HUD |

### Niagara and Foliage

| CVar | Default | Description |
|---|---|---|
| `foliage.DensityScale` | 1.0 | Scale instance counts |
| `r.HairStrands.Voxelization` | 1 | Set 0 for secondary characters |
| `r.HairStrands.RasterizationScale` | 1.0 | Reduce to 0.1 |

### Volumes and Environment

| CVar | Default | Description |
|---|---|---|
| `r.VolumetricFog.GridPixelSize` | 16 | Tile size per froxel (8 = high quality) |
| `r.VolumetricFog.GridSizeZ` | 64 | Z slices (128 = smoother light shafts) |

### Occlusion

| CVar | Default | Description |
|---|---|---|
| `r.HZBOcclusion` | 1 | Hierarchical Z-Buffer occlusion |
| `gc.AssetClusteringEnabled` | 1 | GC clusters for assets |

---

## Appendix: Further Reading

### Conferences and Talks

- [Nanite for Artists | GDC 2024](https://www.youtube.com/watch?v=eoxYceDfKEM) — comprehensive Nanite talk from Epic
- [An Artist's Guide to Nanite Tessellation | Unreal Fest 2024](https://www.youtube.com/watch?v=6igUsOp8FdA) — practical tessellation guide
- [The Future of Nanite Foliage | Unreal Fest Stockholm 2025](https://www.youtube.com/watch?v=aZr-mWAzoTg) — Quixel + CD Projekt RED demo
- [Optimizing the Game Thread | Unreal Fest 2024](https://www.youtube.com/watch?v=KxREK-DYu70) — Blueprint and game thread optimization
- [TSR/Nanite/Lumen/VSM Insights | Unreal Fest Gold Coast 2024](https://www.youtube.com/watch?v=szgnZx2b0Zg) — rendering systems insights from the Japan Support Team
- [Scaling for Quality & Performance | Unreal Fest Bali 2025](https://www.youtube.com/watch?v=Q1whHlGJB_o) — BADMAD ROBOTS case study
- [Lumen with Immortalis | Arm/Unreal Fest 2023](https://www.slideshare.net/slideshow/unreal-fest-2023-lumen-with-immortalis/266167635) — Lumen optimization deep dive

### Blogs and Articles

- [Tom Looman — UE5 Performance Articles](https://tomlooman.com) — comprehensive articles on C++, profiling, UE5.5/5.6 highlights
- [StraySpark Studio Blog](https://www.strayspark.studio/blog) — World Partition, VSM, Lumen, Nanite Foliage deep dives
- [Alex Forsythe — Blueprints vs C++](http://awforsythe.com/unreal/blueprints_vs_cpp/) — essential architecture decision reading
- [Intel UE5 Optimization Guide](https://www.intel.com/content/www/us/en/developer/articles/technical/unreal-engine-optimization-chapter-2.html) — Nanite, Lumen, practical settings
- [NVIDIA UE5.4 Raytracing Guideline (PDF)](https://dlss.download.nvidia.com/uebinarypackages/Documentation/UE5+Raytracing+Guideline+v5.4.pdf) — Hardware Lumen, DLSS, RT pipeline
- [AMD GPUOpen UE Performance Guide](https://gpuopen.com/learn/unreal-engine-performance-guide/) — GPU profiling, RenderDoc
- [Intax Blueprint VM Performance Guide](https://intaxwashere.github.io/blueprint-performance/) — deep dive into the Blueprint VM
- [xbloom.io — World Partition Internals](https://xbloom.io/2025/10/24/unreals-world-partition-internals/) — WP internal architecture
- [Chris McCole — Culling in UE4/UE5](https://www.chrismccole.com/blog/culling-in-ue4ue5) — culling systems overview
- [George Prosser — Optimizing TWeakObjectPtr](https://prosser.io/optimizing-tweakobjectptr-usage/) — low-level C++ pointer optimization
- [ikrima.dev — FFastArraySerializer](https://ikrima.dev/ue4guide/networking/network-replication/fast-tarray-replication/) — network array replication
- [Rév O'Conner — Texture Compression & BCn](https://www.revoconner.com/post/texture-compression-for-unreal-engine-bcn-and-texture-packing) — texture compression deep dive
- [TechArtHub — Texture Streaming Pool](https://techarthub.com/fixing-texture-streaming-pool-over-budget-in-unreal/) — streaming pool tuning

### YouTube Channels

- [Ben Cloward](https://www.youtube.com/@BenCloward) — materials, HLSL, shader development
- [William Faucher](https://www.youtube.com/@WilliamFaucher) — Lumen, lighting, cinematic rendering
- [Tom Looman](https://www.youtube.com/@TomLoomanton) — C++, AI, gameplay systems in UE5
- [Alex Forsythe](https://www.youtube.com/@AlexForsythe) — Blueprint vs C++, architecture

### Repositories and Resources

- [Awesome Unreal Engine (GitHub)](https://github.com/insthync/awesome-unreal) — curated list of plugins, tools, and tutorials
- [unrealcommunity.wiki](https://unrealcommunity.wiki) — community-maintained wiki with deep dives
- [Epic Developer Community](https://dev.epicgames.com/community/) — official tutorials and Knowledge Base
- [r/unrealengine](https://www.reddit.com/r/unrealengine/) — community Q&A and real-world experience sharing

---

This guide compiles production knowledge from UE5.3–5.5. CVars and APIs were current at time of writing — verify against the Release Notes when upgrading the engine version.
