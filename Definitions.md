# Glossary — Universal + Unreal Engine + Unity

A unified reference combining engine-agnostic rendering and performance vocabulary with engine-specific terms for Unreal Engine 4/5 and Unity 2018 through Unity 6.

---

## Table of Contents

- [How to Read This Guide](#how-to-read-this-guide)
  - [Unreal Engine version tags](#unreal-engine-version-tags)
  - [Unity version tags](#unity-version-tags)
- [Common Glossary (Engine-Agnostic)](#common-glossary-engine-agnostic)
  - Performance fundamentals
    - [FPS and Frame Time](#fps-and-frame-time)
    - [CPU](#cpu)
    - [GPU](#gpu)
    - [Draw Call](#draw-call)
    - [Shader](#shader)
    - [CPU Bound vs GPU Bound](#cpu-bound-vs-gpu-bound)
    - [Inclusive Time vs Exclusive Time](#inclusive-time-vs-exclusive-time)
  - Rendering paths and pipelines
    - [Rendering Pipeline (Forward / Deferred)](#rendering-pipeline-forward--deferred)
    - [Rasterization](#rasterization)
    - [Ray Tracing](#ray-tracing)
  - Materials and shading
    - [Material](#material)
    - [Material Instance](#material-instance)
    - [Material Pass / Material Domain](#material-pass--material-domain)
  - Geometry and culling
    - [LOD (Level of Detail)](#lod-level-of-detail)
    - [Occlusion Culling](#occlusion-culling)
  - Lighting
    - [Light Probes](#light-probes)
    - [Reflection Probes](#reflection-probes)
    - [Lightmaps](#lightmaps)
    - [Mixed Lighting](#mixed-lighting)
    - [Shadow Mapping](#shadow-mapping)
  - Image quality and post-processing
    - [Antialiasing](#antialiasing)
    - [DLSS / FSR / XeSS](#dlss--fsr--xess)
    - [Ambient Occlusion](#ambient-occlusion)
    - [Depth of Field](#depth-of-field)
    - [Anisotropy](#anisotropy)
    - [Volumetric Effects](#volumetric-effects)
    - [Checkerboarding](#checkerboarding)
    - [Anti-Tearing Techniques (V-Sync, G-Sync, FreeSync)](#anti-tearing-techniques-v-sync-g-sync-freesync)
- [Unreal Engine 4 / UE5 Glossary](#unreal-engine-4--ue5-glossary)
  - Rendering & lighting (UE)
    - [TSR (Temporal Super Resolution)](#tsr-temporal-super-resolution)
    - [Lumen](#lumen)
    - [Nanite](#nanite)
    - [Virtual Shadow Maps (VSM)](#virtual-shadow-maps-vsm)
    - [Tessellation in UE](#tessellation-in-ue)
    - [Mesh Distance Fields (UE)](#mesh-distance-fields-ue)
    - [HLOD (Hierarchical LOD)](#hlod-hierarchical-lod)
    - [Substrate](#substrate)
  - World and streaming (UE)
    - [World Partition](#world-partition)
    - [Data Layers](#data-layers)
  - Effects and audio (UE)
    - [Niagara](#niagara)
    - [MetaSounds](#metasounds)
  - Networking & gameplay (UE)
    - [Iris](#iris)
    - [Push Model Replication](#push-model-replication)
    - [Subsystems](#subsystems)
  - C++ pointers and lifecycle (UE)
    - [TSoftObjectPtr / TSoftClassPtr](#tsoftobjectptr--tsoftclassptr)
    - [TObjectPtr](#tobjectptr)
    - [TWeakObjectPtr](#tweakobjectptr)
  - Tooling (UE)
    - [Live Coding](#live-coding)
- [Unity Glossary](#unity-glossary)
  - Render pipelines & batching (Unity)
    - [Built-in RP](#built-in-rp)
    - [URP (Universal Render Pipeline)](#urp-universal-render-pipeline)
    - [HDRP (High Definition Render Pipeline)](#hdrp-high-definition-render-pipeline)
    - [Forward / Forward+ / Deferred (Unity)](#forward--forward--deferred-unity)
    - [SRP Batcher](#srp-batcher)
    - [GPU Instancing (Unity)](#gpu-instancing-unity)
    - [Static Batching (Unity)](#static-batching-unity)
    - [Dynamic Batching (Unity)](#dynamic-batching-unity)
    - [GPU Resident Drawer](#gpu-resident-drawer)
    - [BatchRendererGroup (BRG)](#batchrenderergroup-brg)
    - [Render Graph (Unity)](#render-graph-unity)
  - Lighting (Unity)
    - [APV (Adaptive Probe Volumes)](#apv-adaptive-probe-volumes)
  - Geometry and culling (Unity)
    - [LOD Group](#lod-group)
  - Image quality (Unity)
    - [STP (Spatial-Temporal Post-Processing)](#stp-spatial-temporal-post-processing)
  - Shaders (Unity)
    - [Shader Variant](#shader-variant)
    - [Shader Graph](#shader-graph)
  - Multithreading & data-oriented (Unity)
    - [Burst](#burst)
    - [Job System](#job-system)
    - [IJob / IJobParallelFor](#ijob--ijobparallelfor)
    - [DOTS / ECS](#dots--ecs)
    - [Entities Graphics](#entities-graphics)
  - Scripting & async (Unity)
    - [IL2CPP vs Mono](#il2cpp-vs-mono)
    - [Awaitable](#awaitable)
    - [UniTask](#unitask)
    - [Incremental GC](#incremental-gc)
  - Asset management (Unity)
    - [Addressables](#addressables)
    - [Asset Bundles](#asset-bundles)
  - Editor (Unity)
    - [Domain Reload](#domain-reload)

---

## How to Read This Guide

Two engines, three Unreal generations, three Unity generations — terms are shared where the concept is identical, and split into engine-specific sections where the implementation diverges. Where a single concept carries different baggage in each engine (for example, "Draw Call" or "LOD"), it lives in the Common Glossary with engine-specific notes called out.

### Unreal Engine version tags

This guide covers Unreal Engine 4 (4.22–4.27) and Unreal Engine 5 (5.0–5.6+). Every UE tip that differs meaningfully between engine generations is tagged:

- **[UE4 + UE5]** — applies to both engines without significant changes
- **[UE4 only]** — UE4-specific feature or workflow removed or replaced in UE5
- **[UE5 only]** — UE5-exclusive feature not present or experimental in UE4
- **[Deprecated in UE5]** — was standard in UE4, removed or superseded in UE5

### Unity version tags

This guide targets Unity 2018 through Unity 6 (6000.x), with emphasis on shipping to PC/Steam. Mobile and VR are out of scope. Every Unity tip that differs meaningfully across engine generations is tagged:

- **[Pre-2020]** — Unity 2018/2019, Built-in RP era. Much of the workaround folklore on the internet comes from this period. Some of it is now obsolete.
- **[2020-2022 LTS]** — Unity 2020, 2021, and 2022 LTS. URP and HDRP stable, DOTS Entities 1.0, Addressables as the standard asset management layer, ObjectPool built in.
- **[Unity 6+]** — Unity 6 (October 2024) and later. GPU Resident Drawer, Render Graph mandatory in URP, STP upscaler, Adaptive Probe Volumes by default, Awaitable mature.
- **[All versions]** — Applies broadly across all three eras without meaningful change.

Common Glossary entries are tagged **[Universal]** when the concept is engine-agnostic. Where engine handling diverges, the entry includes inline notes for both engines.

---

## Common Glossary (Engine-Agnostic)

### FPS and Frame Time
**[Universal]**
Frames rendered per second. The inverse is frame time in milliseconds (ms): 60 FPS = 16.67 ms/frame, 30 FPS = 33.33 ms/frame. Always reason in ms, not FPS — a 10 FPS drop from 60 to 50 costs 3.3 ms; from 30 to 20 costs 16.7 ms. Track frame time distributions and percentiles (P95, P99), not FPS averages. [Unity best practices](https://unity.com/how-to/best-practices-for-profiling-game-performance)

### CPU
**[Universal]**
The game's central processor. Both engines split CPU work across multiple threads.
- **Unreal:** Game Thread (ticks, AI, physics, Blueprints), Render Thread (render command building, Lumen and Nanite CPU-side), and the RHI Thread (API submission). Bottleneck is identified with `stat unit`: if the `Game` line is highest, the Game Thread is the limiting factor.
- **Unity:** Main Thread (MonoBehaviour Update, physics, animation), Render Thread (graphics command submission), and Job Worker threads (Burst-compiled jobs). Diagnosed in the Unity Profiler CPU Usage module.

### GPU
**[Universal]**
Executes shaders, rasterization, compute passes, and (where supported) ray tracing.
- **Unreal:** Lumen, Nanite, VSM, Niagara GPU all run as compute. Bottleneck identified when the `GPU` line in `stat unit` exceeds the frame budget. Use `ProfileGPU` (Ctrl+Shift+,) or `stat gpu` for per-pass breakdown.
- **Unity:** GPU bound when `Gfx.WaitForPresentOnGfxThread` dominates. Use the GPU Usage profiler module (or RenderDoc / PIX / NSight) for per-pass breakdown.

### Draw Call
**[Universal]**
A command issued by the CPU to the GPU to render a batch of geometry with a given material and shader state. Each call has CPU overhead for state binding regardless of geometry complexity.
- **Unreal:** Draw calls are a primary CPU bottleneck in UE4. In UE5 with Nanite, the traditional draw call model is replaced for Nanite geometry — the bottleneck shifts to shading bins. Draw calls still matter for non-Nanite geometry, skeletal meshes, translucency, and UI.
- **Unity:** PC budgets of 1,000–3,000 per frame are common depending on CPU speed and render path. SRP Batcher, GPU Instancing, Static Batching, Dynamic Batching, and (Unity 6+) GPU Resident Drawer all reduce CPU overhead. [Unity GPU instancing docs](https://docs.unity3d.com/6000.6/Documentation/Manual/GPUInstancing.html)

### Shader
**[Universal]**
A GPU program executed for vertices, pixels, or compute work.
- **Unreal:** Materials compile to many shader permutations via the shader compilation system. Too many unique shaders increase PSO (Pipeline State Object) compilation stalls on first render. Use `stat shadercompiling` to track outstanding compilations.
- **Unity:** Authored as HLSL (`.shader`/`.hlsl`) or via Shader Graph. Compiled into shader variants per platform/keyword combination (see [Shader Variant](#shader-variant)).

### CPU Bound vs GPU Bound
**[Universal]**
- **CPU bound:** the GPU is waiting for the CPU to finish (Game/Main Thread or Render Thread is the bottleneck).
- **GPU bound:** the CPU is waiting for the GPU.

You cannot fix a GPU-bound scene by optimizing CPU code, and vice versa. Diagnose in Unreal with `stat unit` (compare Game/Draw vs GPU lines) or in Unity with the Profiler CPU/GPU modules and `Gfx.WaitForPresent` markers.

### Inclusive Time vs Exclusive Time
**[Universal]**
- **Inclusive time:** wall time of a function including all called children.
- **Exclusive time:** time spent only in that function body, not children.

Sort profiler timers by Exclusive Time (Unreal Insights, Unity Profiler hierarchy view) to find the single most expensive function scope. Sort by Inclusive Time to find which top-level call paths dominate the frame.

### Rendering Pipeline (Forward / Deferred)
**[Universal]**
- **Forward:** each object is rendered per light affecting it. Cheap memory bandwidth; cost scales with object × light count. Supports MSAA. Used for VR, mobile, and simple scenes.
- **Deferred:** all geometry first writes a G-buffer (positions, normals, material properties), then lighting is computed in screen space. Supports many simultaneous lights cheaply. No MSAA. Higher VRAM and bandwidth cost.
- **Forward+ / Tiled / Clustered:** hybrid that culls lights into screen tiles or volumetric clusters. Allows many lights without full deferred cost.

Engine specifics:
- **Unreal:** UE5 defaults to Deferred. Forward Rendering is available for VR or mobile. Nanite, Lumen, and VSM require Deferred.
- **Unity:** see [Forward / Forward+ / Deferred (Unity)](#forward--forward--deferred-unity) for URP rendering paths, and [HDRP](#hdrp-high-definition-render-pipeline) for the high-fidelity deferred-by-default option.

### Rasterization
**[Universal]**
The process of converting triangles into pixel coverage. The hardware rasterizer is fixed-function; for sub-pixel geometry, a software rasterizer (Nanite in UE5) outperforms it.

### Ray Tracing
**[Universal]**
Hardware-accelerated ray tracing (DXR / Vulkan RT). Requires GPU with RT cores (NVIDIA RTX, AMD RX 6000+, Intel Arc).
- **Unreal:** In UE4.26+, ray tracing is optional for shadows, reflections, GI, and AO. In UE5, Lumen uses ray tracing internally (Hardware Lumen) or falls back to distance fields (Software Lumen).
- **Unity:** HDRP supports DXR-based reflections, shadows, AO, GI, and recursive ray tracing. URP exposes ray tracing via experimental APIs in Unity 6+; not production-ready for indie targets.

### Material
**[Universal]**
A node graph (or shader file) that defines the surface shading of geometry.
- **Unreal:** Material assets compile to a shader. Material defines shader topology.
- **Unity:** A `Material` asset references a shader plus parameter values. Shader Graph generates shaders for URP/HDRP. Hand-authored shaders are HLSL.

### Material Instance
**[Universal]**
A child of a master material that shares the parent's compiled shader and only overrides parameters.
- **Unreal:** Material Instance Constant (MIC, cooked, zero overhead) and Material Instance Dynamic (MID, runtime-created). Pool MIDs rather than creating them per-frame.
- **Unity:** Materials inherit from a shader; runtime variants are created via `material.SetX` (which clones the shared material and breaks SRP batching) or via `MaterialPropertyBlock` (which preserves batching for some patterns but breaks SRP Batcher specifically).

### Material Pass / Material Domain
**[Universal]**
The render pass a material occupies: Opaque, Masked / Alpha-tested, or Translucent.
- Opaque is cheapest.
- Masked adds a discard step.
- Translucent renders in a separate pass, sorts back-to-front, and cannot easily receive accurate shadows from VSM (UE5) or per-pixel GI without special handling.

### LOD (Level of Detail)
**[Universal]**
A lower-polygon mesh substituted at distance to reduce GPU load.
- **Unreal:** Still primary for non-Nanite geometry. With Nanite enabled on a mesh, manual LODs are no longer used for rendering — Nanite manages its own internal LOD. Fallback LODs in Nanite meshes serve collision and non-Nanite render paths.
- **Unity:** Authored via the [LOD Group](#lod-group) component; `QualitySettings.lodBias` globally scales transition distances. Required for any large open-world scene without Nanite-equivalent tooling. [Unity LOD Group docs](https://docs.unity3d.com/Manual/class-LODGroup.html)

### Occlusion Culling
**[Universal]**
A visibility system preventing draw calls for fully occluded objects.
- **Unreal:** Hardware Occlusion Queries (default) and Round Robin Occlusion. Precomputed Visibility Volumes are deprecated for streaming worlds.
- **Unity:** Baked PVS via Window → Rendering → Occlusion Culling. GPU-based alternative in Unity 6+ URP/HDRP requires no baking. Most beneficial in closed environments. [Unity Occlusion Culling docs](https://docs.unity3d.com/6000.4/Documentation/Manual/OcclusionCulling.html)

### Light Probes
**[Universal]**
Spherical Harmonics captures at discrete world positions used to light dynamic objects at runtime. Sampled per-object, not per-pixel.
- **Unreal:** Indirect Lighting Cache and (in UE5) volumetric lightmaps; the Lumen path largely supersedes manual probe placement in lit dynamic scenes.
- **Unity:** Placed manually via `Light Probe Group` components, or automatically via [APV](#apv-adaptive-probe-volumes) in Unity 6+ (per-pixel sampling).

### Reflection Probes
**[Universal]**
360° cubemap captures of the environment used for specular reflections. Three modes: Baked (at bake time), Realtime (per frame or on demand), Custom (arbitrary cubemap). Realtime probes are expensive — use *On Demand* refresh mode where possible.

### Lightmaps
**[Universal]**
Baked texture atlases storing diffuse indirect lighting for static geometry. High-quality GI at near-zero runtime cost.
- **Unreal:** Lightmass (CPU/GPU) generates lightmaps for stationary/static lights.
- **Unity:** Generated by the Progressive Lightmapper (CPU/GPU variants) or the third-party Bakery plugin.

### Mixed Lighting
**[Universal]**
Lights that combine real-time direct lighting with baked indirect.
- **Unreal:** Light mobility is `Static`, `Stationary`, or `Movable`. Stationary is the closest equivalent to mixed mode (baked indirect, real-time direct, baked shadows for low-priority casters).
- **Unity:** Modes: Baked Indirect (real-time shadows + baked GI), Shadowmask (near real-time, far baked), Subtractive (one directional light, fully baked).

### Shadow Mapping
**[Universal]**
Classic depth-map shadow technique.
- **Unreal:** UE4 (and UE5 without Lumen) uses Cascaded Shadow Maps (CSM) for directional lights. Shadow map resolution, cascade count, and cascade transition distances are primary tuning parameters. UE5 with Lumen uses [VSM](#virtual-shadow-maps-vsm) for dynamic lights.
- **Unity:** Cascaded shadow maps for directional lights (configured per render pipeline asset). Shadow distance, cascade count (1/2/4), and shadow resolution are primary tuning parameters.

### Antialiasing
**[Universal]**
Technique to reduce jagged edges along high-contrast geometry boundaries.
- **MSAA** — multisample, forward-only, expensive.
- **FXAA / SMAA** — cheap post-process; soft, can blur detail.
- **TAA** — temporal accumulation; can ghost.
- **TSR / DLSS / FSR / XeSS / STP** — temporal upscalers that double as AA solutions; see [DLSS / FSR / XeSS](#dlss--fsr--xess) and the engine-specific entries.

### DLSS / FSR / XeSS
**[Universal]**
Vendor (or vendor-aligned) temporal upscalers. All three function as replacements for TAA/TSR/STP in the AA + upscale post-process slot.
- **DLSS** — NVIDIA, deep-learning, RTX-only. DLSS 3+ adds Frame Generation on RTX 40-series.
- **FSR** — AMD, hardware-agnostic. FSR 3+ includes Frame Generation. Most compatible cross-vendor option.
- **XeSS** — Intel; quality-for-cost between FSR and DLSS on Arc and recent NVIDIA cards.
- **Unreal:** ship as plugins in Marketplace / Fab; install per-vendor. DLSS Frame Generation requires DLSS 3+ and RTX 40+ series.
- **Unity:** DLSS native in HDRP, plugin in URP. FSR built into URP since 2022. XeSS via the [open-source plugin](https://github.com/GameTechDev/XeSSUnityPlugin). For most indie PC games, [STP](#stp-spatial-temporal-post-processing) (Unity 6+) is the simpler default.

### Ambient Occlusion
**[Universal]**
A screen-space (SSAO) or ray-traced approximation of how much ambient light a point receives.
- **Unreal:** In UE5 with Lumen, SSAO is usually disabled in favor of Lumen's GI. `r.AmbientOcclusion.Intensity 0` disables.
- **Unity:** SSAO available as a URP/HDRP renderer feature; ray-traced AO in HDRP DXR.

### Depth of Field
**[Universal]**
Post-process effect simulating camera lens blur for out-of-focus objects. Methods range from cheap Gaussian (mobile) to physically-based bokeh (cinematic).
- **Unreal:** Circle DOF (UE4) or Cinematic DOF (bokeh simulation, expensive). Disable `r.DepthOfField.TemporalAA` for a slight temporal stability gain.
- **Unity:** Volume-overridable DOF in URP and HDRP; HDRP includes a path-traced reference DOF.

### Anisotropy
**[Universal]**
Anisotropic texture filtering. Improves texture sharpness at oblique angles at a minor cost.
- **Unreal:** `r.MaxAnisotropy 4` or `8` is a common shipping target. `16` is overkill for most surfaces.
- **Unity:** `QualitySettings.anisotropicFiltering` and per-texture override.

### Volumetric Effects
**[Universal]**
Includes volumetric fog, volumetric clouds, and height fog. All are expensive at high quality.
- **Unreal:** Key CVars — `r.VolumetricFog.GridPixelSize`, `r.VolumetricFog.GridSizeZ`, `r.VolumetricCloud.ShadowMap.RaymarchMaxStepCount`. Disable on low-end with `r.VolumetricFog 0`.
- **Unity:** HDRP volumetric fog and clouds are expensive but shippable. URP has limited volumetric fog support; consider third-party assets for high quality.

### Checkerboarding
**[Universal]**
Rendering alternating pixels on alternating frames and reconstructing a full image using temporal data. A cost-cutting technique most associated with PS4-era consoles. Distinct from temporal upscalers, which operate on full output reconstruction.

### Anti-Tearing Techniques (V-Sync, G-Sync, FreeSync)
**[Universal]**
- **V-Sync** caps the renderer to the monitor refresh rate, eliminating tearing but introducing input latency and frame pacing issues when performance dips below target.
- **G-Sync (NVIDIA) and FreeSync (AMD/VESA Adaptive-Sync)** allow variable refresh rates: the monitor refresh follows the GPU output rate within a supported range.
- **Unreal:** `r.VSync` to toggle. Frame pacing is platform-dependent.
- **Unity:** `QualitySettings.vSyncCount` (0 = off, 1 = every refresh, 2 = every other) and `Application.targetFrameRate`. Both must be set carefully — V-Sync 0 with `targetFrameRate -1` is "uncapped".

---

## Unreal Engine 4 / UE5 Glossary

This section covers terms specific to Unreal Engine 4 and Unreal Engine 5. Engine-agnostic concepts (CPU, GPU, Draw Call, LOD, Material, etc.) live in the [Common Glossary](#common-glossary-engine-agnostic) above with UE-specific notes inline.

### TSR (Temporal Super Resolution)
**[UE5 only]**
Epic's built-in temporal upsampler and AA solution, replacing TAA as the default in UE5. Renders at a lower internal resolution then reconstructs. Key CVars: `r.TSR.History.ScreenPercentage`, `r.TSR.Velocity.WeightClampingPixelSpeedLimit`. More stable than TAA for high-frequency detail, significantly cheaper than DLSS at equivalent upscale ratios.

### Lumen
**[UE5 only]**
UE5's fully dynamic global illumination and reflections system. Operates in two modes: Software Lumen (distance fields + surface cache, no RT hardware required) and Hardware Lumen (DXR ray tracing, higher quality, more platforms). See the Lights & Shadows specialization section of the optimization guide for detailed tuning. CVars: `r.Lumen.ScreenProbeGather.TracingOctahedronResolution`, `r.Lumen.Reflections.DownsampleFactor`.

### Nanite
**[UE5 only]**
UE5's virtualized micro-polygon geometry renderer. Automatically streams and renders only visible micropolygons from an unlimited-polygon source mesh. Replaces manual LOD creation for high-poly static meshes. Does not support translucency, two-sided foliage cards with complex WPO, or skeletal meshes (experimental in UE5.5+). Primary CVar: `r.Nanite.MaxPixelsPerEdge`.

### Virtual Shadow Maps (VSM)
**[UE5 only]**
UE5's default shadow rendering system. Conceptually a 16k×16k virtual shadow atlas per light, subdivided into 128×128 pages. Only pages covering actually visible shadow-receiving surfaces are allocated in a physical page pool. Dramatically reduces the "resolution vs coverage" trade-off of traditional shadow maps. Key CVar: `r.Shadow.Virtual.MaxPhysicalPages` (default 4096; increase to 8192 for open worlds).

### Tessellation in UE
**[UE4 + UE5 — version notes critical]**
Classic GPU hardware tessellation (PN Triangles, flat tessellation) was a first-class material feature in UE4. **[Deprecated in UE5]**: Classic pipeline tessellation was removed in UE5.0. It is replaced by Nanite Tessellation / Nanite Displacement (experimental UE5.2, production from ~UE5.4), which operates via the Nanite software rasterizer rather than the fixed-function GPU tessellator. Enabling Nanite Tessellation requires `r.Nanite.Tessellation=1` and the Nanite Displacement Mesh plugin.

### Mesh Distance Fields (UE)
**[UE4 + UE5]**
Volumetric distance field representation of each mesh, used by Software Lumen, dynamic shadow casting (DF shadows), and ambient occlusion. Enable per mesh in Static Mesh Editor → Build Settings → Generate Mesh Distance Field. Global setting: Project Settings → Rendering → Generate Mesh Distance Fields.

### HLOD (Hierarchical LOD)
**[UE4 + UE5 — different impl]**
- **UE4 HLOD:** generated merged meshes for distant clusters, configured per-HLOD Layer.
- **UE5 World Partition HLOD:** automatically built for streaming cells; supports Instanced (no decimation, keeps Nanite) and Merged (decimated mesh) types. HLOD1 also serves as Lumen's Far Field geometry (>1 km).

### Substrate
**[UE5.3+ experimental / UE5.5+ opt-in]**
UE5's new material shading model system replacing the fixed-function material domain system. Supports layered shading models, physically-based slab stacking, and heterogeneous material structures. Enabled via Project Settings → Rendering → Substrate. Not backward compatible — requires material conversion.

### World Partition
**[UE5 only]**
UE5's streaming world system, replacing World Composition for new projects. Divides the world into a spatial grid of cells, streaming them in/out based on proximity to streaming sources (typically the player controller). Supports One-File-Per-Actor (OFPA) for source control. Key concepts: Runtime Grids, Data Layers, Level Instances, Packed Level Actors. **[Deprecated in UE5]**: World Composition is still available but not recommended for new UE5 projects.

### Data Layers
**[UE5 only]**
World Partition concept grouping actors into logical layers that can be loaded/unloaded independently. Runtime Data Layers control game state (e.g., "occupied vs destroyed village"). External Data Layers (EDL) separate DLC or seasonal content into plugins.

### Niagara
**[UE4.20+ + UE5]**
UE's modern GPU and CPU particle system, replacing Cascade. Supports GPU simulations, Data Channels, Significance Manager integration, and neighbor queries. **[Deprecated in UE5]**: Cascade is still usable but not developed. Niagara is the standard.

### MetaSounds
**[UE5 only]**
UE5's node-based audio DSP graph system. Replaces Sound Cues as the primary audio authoring tool in UE5. Supports per-instance parameters, procedural synthesis, and Quartz integration. **[UE4 only]**: Sound Cues remain the primary system in UE4.

### Iris
**[UE5.4+ experimental, UE5.5+ shipping option]**
A rewrite of UE's replication data path. Separates gameplay from networking via replication state descriptors. Backward-compatible with existing UPROPERTY replication. Enabled via `net.Iris.UseIrisReplication=1`. Offers better scalability at high player counts versus the legacy Net Driver.

### Push Model Replication
**[UE4.25+ + UE5]**
An opt-in optimization that skips property replication polling for actors that haven't changed. Instead of the engine scanning all replicated properties every frame, properties only replicate when explicitly marked dirty via `MARK_PROPERTY_DIRTY_FROM_NAME`. Significant server CPU savings for actors with infrequently-changing state.

### Subsystems
**[UE4.22+ + UE5]**
Engine-managed singleton-like objects tied to the lifetime of their outer (Game Instance, World, Player Controller, etc.). The preferred replacement for custom manager actors and singletons. `UGameInstanceSubsystem`, `UWorldSubsystem`, `ULocalPlayerSubsystem`, `UEngineSubsystem`.

### TSoftObjectPtr / TSoftClassPtr
**[UE4 + UE5]**
Pointer types that store only an asset path (string). The asset is NOT loaded until explicitly resolved via `LoadSynchronous()` or `RequestAsyncLoad()`. Use to avoid loading assets at Blueprint startup. **[CORRECTED]**: An older version of this guide stated "TSoftObjectPtr uses dynamic_cast which is very expensive." This is wrong. UE never uses `dynamic_cast` in its `Cast<>` system — it walks the UClass tree via static lookup. The real performance concern with soft pointers is the synchronous resolve (`LoadSynchronous()`), which stalls the calling thread until the asset is loaded from disk. Cache the result; never call `LoadSynchronous()` in Tick.

### TObjectPtr
**[UE5 only]**
UE5 replacement for raw `T*` in `UPROPERTY` class members. Compiles to a raw pointer in shipping builds (zero cost). In editor builds adds access tracking, lazy-load support, and better null diagnostics. Required for correct behavior with UE5.4+ incremental GC.

### TWeakObjectPtr
**[UE4 + UE5]**
Non-owning pointer that becomes null automatically when the referenced UObject is garbage-collected. `Get()` incurs a `GUObjectArray` lookup (potential cache miss). Pattern: `if (UObject* Obj = WeakPtr.Get()) { ... }` — single dereference, null check, use.

### Live Coding
**[UE4.22+ default in UE5]**
Hot-patch compilation that recompiles and relinks function bodies in a running editor session. Safe only for changes inside function bodies (`.cpp` logic changes). Unsafe for UPROPERTY / UFUNCTION declaration changes, struct layout changes, or constructor changes — those require a full editor restart. **[Deprecated in UE5]**: Hot Reload (the older `Ctrl+Alt+F11` mechanism) is replaced by Live Coding as the default.

---

## Unity Glossary

This section covers terms specific to Unity. Engine-agnostic concepts live in the [Common Glossary](#common-glossary-engine-agnostic) above with Unity-specific notes inline.

### Built-in RP
**[Pre-2020 default; deprecated Unity 6.5]**
Unity's legacy fixed-function render pipeline. No SRP Batcher, no Render Graph. Enormous asset store ecosystem but no future feature investment. [Confirmed deprecated in Unity 6.5](https://www.maxkillstudios.com/learn/birp-deprecated-migrate-urp-or-wait).

### URP (Universal Render Pipeline)
**[2020-2022 LTS recommended default]**
Scriptable, forward-by-default, optimized for a wide hardware range. Recommended default for new PC Steam titles. Full SRP Batcher, GPU Resident Drawer, Render Graph, Forward+ all available.

### HDRP (High Definition Render Pipeline)
**[All versions on high-end PC]**
High-fidelity physically accurate pipeline for AAA-quality PC/console. Physically based lights, volumetrics, full ray tracing support. Higher baseline GPU cost — not for broad hardware support.

### Forward / Forward+ / Deferred (Unity)
**[All versions]**
- **Forward:** each object rendered per light affecting it; max 9 additional real-time lights in URP.
- **Forward+:** (URP 2021.2+) tile-based light culling, unlimited real-time lights, required for GPU Resident Drawer.
- **Deferred:** G-buffer pass then screen-space lighting, unlimited opaque lights, no MSAA.

[URP rendering paths comparison](https://docs.unity3d.com/6000.1/Documentation/Manual/urp/rendering-paths-comparison.html)

### SRP Batcher
**[2020-2022 LTS]** (available from Unity 2019.3)
A low-level render loop that keeps per-material constant buffer data persistent in GPU memory between frames, eliminating CPU re-upload work. It reduces GPU state changes rather than raw draw call count. Compatible with URP and HDRP only; not Built-in RP. For a shader to be SRP Batcher compatible, all per-material properties must live in a single CBUFFER named `UnityPerMaterial`. [Unity SRP Batcher docs](https://docs.unity3d.com/Manual/SRPBatcher.html)

### GPU Instancing (Unity)
**[All versions]**
A hardware-level optimization that sends one draw command to render multiple copies of the same mesh with potentially different per-instance transforms and properties. Activated per-material. GPU Instancing and the SRP Batcher are mutually exclusive for a given renderer — GPU Instancing opts the material out of SRP batching. [Unity GPU instancing docs](https://docs.unity3d.com/6000.6/Documentation/Manual/GPUInstancing.html)

### Static Batching (Unity)
**[All versions]**
Combines meshes marked Batching Static that share a material into a single large merged mesh at build time, reducing draw calls. Trades draw call count for memory (duplicate mesh data per instance). Disable when using GPU Resident Drawer — the two systems conflict. [TheGameDev.Guru batching guide](https://thegamedev.guru/unity-performance/draw-call-optimization/)

### Dynamic Batching (Unity)
**[All versions]**
Merges small meshes (under 300 vertices) at runtime for objects sharing a material. Has CPU cost each frame and is largely superseded by SRP Batcher and GPU Resident Drawer. Leave enabled for small particle meshes but do not rely on it as primary strategy in URP/HDRP projects. [Unity draw call batching](https://docs.unity3d.com/cn/2021.3/Manual/optimizing-draw-calls.html)

### GPU Resident Drawer
**[Unity 6+]**
Introduced in Unity 6.0 for URP, uses the `BatchRendererGroup` API to draw GameObjects with GPU instancing automatically. Reduces SetPass calls and draw calls with minimal setup. Requires Forward+ rendering path, compute shader support, SRP Batcher enabled, and Static Batching disabled. Set GPU Resident Drawer to *Instanced Drawing* in the Universal Renderer asset. [Unity GPU Resident Drawer docs](https://docs.unity3d.com/6000.0/Documentation/Manual/urp/gpu-resident-drawer.html)

### BatchRendererGroup (BRG)
**[2020-2022 LTS]** (production-ready Unity 6)
Low-level C# API for high-performance custom rendering in SRP projects. Bypasses GameObjects entirely. The Entities Graphics package is the canonical consumer for DOTS-based rendering. [Unity BRG docs](https://docs.unity3d.com/Manual/batch-renderer-group.html)

### Render Graph (Unity)
**[Unity 6+]**
The mandatory render pass management system in URP from Unity 6 onwards. Replaces the legacy `ScriptableRenderPass.Execute` pattern with a declarative graph that automatically manages pass ordering, resource lifetimes, and pass culling. All URP Renderer Features must use `RecordRenderGraph` in Unity 6. [Unity Render Graph introduction](https://docs.unity3d.com/6000.3/Documentation/Manual/urp/render-graph-introduction.html)

### APV (Adaptive Probe Volumes)
**[Unity 6+]**
Replaces manual Light Probe Group placement with automatic geometry-density-driven probe distribution. Per-pixel sampling instead of per-object. Supports Light Blending Scenarios and sky occlusion. [Unity APV usage guide](https://docs.unity3d.com/6000.3/Documentation/Manual/urp/probevolumes-use.html)

### LOD Group
**[All versions]**
The `LODGroup` component manages Level of Detail transitions based on screen-space coverage. `QualitySettings.lodBias` globally scales transition distances. [Unity LOD Group docs](https://docs.unity3d.com/Manual/class-LODGroup.html)

### STP (Spatial-Temporal Post-Processing)
**[Unity 6+]**
Unity's software-based temporal upscaler. Renders at lower resolution, reconstructs full image using temporal and spatial data. No vendor SDK required — compute shaders only. Enable via URP Asset → Quality → Upscaling Filter → STP. [Unity STP docs](https://docs.unity3d.com/6000.1/Documentation/Manual/urp/stp/stp-upscaler.html)

### Shader Variant
**[All versions]**
A fully compiled shader program for one specific keyword combination. 10 feature flags = 1,024 variants. Manage via `shader_feature` (strips unused), `multi_compile` (never strips automatically), and `IPreprocessShaders`. [Unity shader variants docs](https://docs.unity3d.com/Manual/shader-variants.html)

### Shader Graph
**[2020-2022 LTS]** (available from 2018)
Node-based visual shader authoring tool for URP and HDRP. Automatically generates SRP Batcher-compatible `UnityPerMaterial` CBUFFERs. Not supported in Built-in RP with active feature development.

### Burst
**[2020-2022 LTS]** (stable ~Unity 2019.1)
LLVM-based compiler that translates C# Job System code into SIMD-vectorized native CPU code. 10–100× faster than equivalent managed code for compute-heavy work. Only applies to job structs marked `[BurstCompile]` and static methods in Burst 1.6+. [Burst docs](https://docs.unity3d.com/Packages/com.unity.burst@1.8/manual/index.html)

### Job System
**[2020-2022 LTS]** (stable from Unity 2018.1)
Safe, structured multi-threading via job structs with `NativeContainer` data. Integrates with Burst for maximum performance. [Unity Job System docs](https://docs.unity3d.com/Manual/JobSystem.html)

### IJob / IJobParallelFor
**[2020-2022 LTS]**
- `IJob`: single-threaded job on one worker thread.
- `IJobParallelFor`: splits indexed work across multiple worker threads.

Both scheduled via `.Schedule()`, completed via `jobHandle.Complete()`. [Unity Job System docs](https://docs.unity3d.com/Manual/JobSystem.html)

### DOTS / ECS
**[2020-2022 LTS]** (Entities 1.0 production-ready Unity 2022.2)
Data-Oriented Technology Stack: Entity Component System (Entities package) + Job System + Burst. Stores component data in dense contiguous arrays (archetypes/chunks), maximizing cache efficiency. Not worth the complexity overhead for most indie game object counts. [Unity 2022 LTS for programmers](https://unity.com/releases/lts/programmers)

### Entities Graphics
**[2020-2022 LTS]** (formerly Hybrid Renderer V2)
Graphics bridge for DOTS ECS using `BatchRendererGroup`. Requires URP or HDRP with Forward+ path. [Entities Graphics docs](https://docs.unity3d.com/Packages/com.unity.entities.graphics@1.3/manual/index.html)

### IL2CPP vs Mono
**[All versions]**
Mono uses JIT compilation at runtime (fast builds, moderate runtime performance). IL2CPP converts C# IL to C++ ahead-of-time (slow builds, generally faster runtime, better stripping). Ship with IL2CPP; develop with Mono. [Unity scripting backend docs](https://docs.unity3d.com/Manual/scripting-backends-intro.html)

### Awaitable
**[Unity 6+]** (introduced Unity 2023.1)
Unity's built-in pooled async primitive. Allocation-friendly. Never await the same instance twice. Use `Awaitable.BackgroundThreadAsync()` / `MainThreadAsync()` for thread switching. Use `destroyCancellationToken` for object-lifetime cancellation. [Unity Awaitable docs](https://hackernoon.com/unity-20231-introduces-awaitable-class)

### UniTask
**[All versions]** (third-party)
Struct-based `UniTask<T>` with near-zero allocations via a custom AsyncMethodBuilder. Best allocation profile for async patterns pre-Unity 6. [UniTask GitHub](https://github.com/Cysharp/UniTask)

### Incremental GC
**[All versions]** (available Unity 2019.1+)
Spreads GC marking work across multiple frames rather than one stop-the-world collection. Reduces frame spikes but adds write-barrier overhead. Does not eliminate allocation pressure — the goal remains 0 bytes allocated per frame in gameplay. [Unity incremental GC docs](https://docs.unity3d.com/Manual/performance-incremental-garbage-collection.html)

### Addressables
**[2020-2022 LTS]** (introduced 2018.3)
High-level asset management layer on top of Asset Bundles. Reference-counted loading, async load/release APIs, dependency tracking, and bundle analysis tooling. The modern standard for content streaming. [Unity Addressables docs](https://docs.unity3d.com/Packages/com.unity.addressables@2.3/manual/index.html)

### Asset Bundles
**[Pre-2020]**
Low-level binary packaging system for runtime asset loading. Still functional in all versions but requires manual dependency/lifecycle management. Prefer Addressables for new projects.

### Domain Reload
**[All versions]**
Editor-side AppDomain reinitialization on every Play press. Takes 5–30 seconds in large projects. Disable via Project Settings → Editor → Enter Play Mode Settings for major iteration speed gains. [Unity 2019.3+]
