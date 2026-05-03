# UE4 / UE5 Glossary

---

## How to Read This Guide

This guide covers Unreal Engine 4 (4.22–4.27) and Unreal Engine 5 (5.0–5.6+). Every tip that differs meaningfully between engine generations is tagged:

- **[UE4 + UE5]** — applies to both engines without significant changes
- **[UE4 only]** — UE4-specific feature or workflow removed or replaced in UE5
- **[UE5 only]** — UE5-exclusive feature not present or experimental in UE4
- **[Deprecated in UE5]** — was standard in UE4, removed or superseded in UE5

**Profile first.** Every section assumes you have profiling data pointing at the bottleneck. Optimizing without data produces regressions as often as gains.

---

## Glossary

### Frames per Second (FPS) **[UE4 + UE5]**
Frames rendered per second. Higher is better. The inverse is frame time in milliseconds (ms): 60 FPS = 16.67 ms/frame, 30 FPS = 33.33 ms/frame. Always reason in ms, not FPS — a 10 FPS drop from 60 to 50 FPS costs 3.3 ms, but a 10 FPS drop from 30 to 20 FPS costs 16.7 ms.

### CPU **[UE4 + UE5]**
The game's central processor. In UE, the CPU runs the Game Thread (ticks, AI, physics, Blueprints), the Render Thread (render command building, Lumen and Nanite CPU-side), and the RHI Thread (API submission). Bottleneck is identified with `stat unit`: if the `Game` line is highest, the Game Thread is the limiting factor.

### GPU **[UE4 + UE5]**
Executes shaders, rasterization, compute passes (Lumen, Nanite, VSM, Niagara GPU). Bottleneck identified when the `GPU` line in `stat unit` exceeds the frame budget. Use `ProfileGPU` (Ctrl+Shift+,) or `stat gpu` for per-pass breakdown.

### Draw Call **[UE4 + UE5]**
A command to the GPU to render a batch of geometry with a given material and state. In UE4, draw calls are a primary CPU bottleneck. In UE5 with Nanite, the traditional draw call model is replaced for Nanite geometry — the bottleneck shifts to shading bins. Draw calls still matter for non-Nanite geometry, skeletal meshes, translucency, and UI.

### Antialiasing **[UE4 + UE5]**
Technique to reduce jagged edges. UE options: MSAA (forward shading only), FXAA (cheap, low quality), TAA (UE4 default, temporal ghosting), TSR **[UE5 only]** (Temporal Super Resolution — Epic's production AA + upsampler). DLSS (NVIDIA), FSR (AMD), and XeSS (Intel) are third-party plugins layered on top.

### TSR (Temporal Super Resolution) **[UE5 only]**
Epic's built-in temporal upsampler and AA solution, replacing TAA as the default in UE5. Renders at a lower internal resolution then reconstructs. Key CVars: `r.TSR.History.ScreenPercentage`, `r.TSR.Velocity.WeightClampingPixelSpeedLimit`. More stable than TAA for high-frequency detail, significantly cheaper than DLSS at equivalent upscale ratios.

### Ambient Occlusion **[UE4 + UE5]**
A screen-space post-process (SSAO) approximating how much ambient light a point receives. In UE5 with Lumen enabled, SSAO is usually disabled in favor of Lumen's GI. `r.AmbientOcclusion.Intensity 0` to disable.

### Anti-Tearing Techniques (V-Sync, G-Sync, FreeSync) **[UE4 + UE5]**
V-Sync caps the renderer to the monitor refresh rate, eliminating tearing but introducing input latency and frame pacing issues when performance dips below target. G-Sync and FreeSync (adaptive sync) allow variable refresh rates. `r.VSync` to toggle.

### Checkerboarding **[UE4 + UE5]**
Rendering alternating pixels on alternating frames and reconstructing a full image using temporal data. A cost-cutting technique for consoles. Not to be confused with TSR or DLSS upscaling, which operate on full output resolution reconstruction.

### Shadow Mapping **[UE4 + UE5]**
Classic depth-map shadow technique. In UE4 (and UE5 without Lumen), cascaded shadow maps (CSM) are used for directional lights. Shadow map resolution, cascade count, and cascade transition distances are primary tuning parameters. In UE5 with Lumen, VSM (Virtual Shadow Maps) replaces conventional shadow maps for dynamic lights.

### Virtual Shadow Maps (VSM) **[UE5 only]**
UE5's default shadow rendering system. Conceptually a 16k×16k virtual shadow atlas per light, subdivided into 128×128 pages. Only pages covering actually visible shadow-receiving surfaces are allocated in a physical page pool. Dramatically reduces the "resolution vs. coverage" trade-off of traditional shadow maps. Key CVar: `r.Shadow.Virtual.MaxPhysicalPages` (default 4096, increase to 8192 for open worlds).

### Ray Tracing **[UE4 + UE5]**
Hardware-accelerated ray tracing (DXR / Vulkan RT). In UE4.26+, ray tracing is optional for shadows, reflections, GI, and AO. In UE5, Lumen uses ray tracing internally (Hardware Lumen) or falls back to distance fields (Software Lumen). Requires GPU with RT cores (NVIDIA RTX, AMD RX 6000+, Intel Arc).

### Lumen **[UE5 only]**
UE5's fully dynamic global illumination and reflections system. Operates in two modes: Software Lumen (distance fields + surface cache, no RT hardware required) and Hardware Lumen (DXR ray tracing, higher quality, more platforms). See Section 3 (Lights & Shadows) for detailed tuning. CVars: `r.Lumen.ScreenProbeGather.TracingOctahedronResolution`, `r.Lumen.Reflections.DownsampleFactor`.

### Nanite **[UE5 only]**
UE5's virtualized micro-polygon geometry renderer. Automatically streams and renders only visible micropolygons from an unlimited-polygon source mesh. Replaces manual LOD creation for high-poly static meshes. Does not support translucency, two-sided foliage cards with complex WPO, or skeletal meshes (experimental in UE5.5+). Primary CVar: `r.Nanite.MaxPixelsPerEdge`.

### Tessellation **[UE4 + UE5 — version notes critical]**
Classic GPU hardware tessellation (PN Triangles, flat tessellation) was a first-class material feature in UE4. **[Deprecated in UE5]**: Classic pipeline tessellation was removed in UE5.0. It is replaced by Nanite Tessellation / Nanite Displacement (experimental UE5.2, production from ~UE5.4), which operates via the Nanite software rasterizer rather than the fixed-function GPU tessellator. Enabling Nanite Tessellation requires `r.Nanite.Tessellation=1` and the Nanite Displacement Mesh plugin.

### Depth of Field (DOF) **[UE4 + UE5]**
Post-process effect simulating camera lens blur for out-of-focus objects. Methods: Gaussian (cheapest, mobile), Circle DOF (UE4), Cinematic DOF (bokeh simulation, expensive). Disable `r.DepthOfField.TemporalAA` for a slight temporal stability gain.

### Anisotropy **[UE4 + UE5]**
Anisotropic texture filtering. Improves texture sharpness at oblique angles at a minor cost. `r.MaxAnisotropy 4` or `8` is a common shipping target. `16` is overkill for most surfaces.

### Volumetric Effects **[UE4 + UE5]**
Includes Volumetric Fog, Volumetric Clouds, and height fog. Expensive. Key CVars: `r.VolumetricFog.GridPixelSize`, `r.VolumetricFog.GridSizeZ`, `r.VolumetricCloud.ShadowMap.RaymarchMaxStepCount`. Disable on low-end targets with `r.VolumetricFog 0`.

### DLSS, FSR, XeSS **[UE4 + UE5]**
Third-party upscaling plugins. DLSS (NVIDIA, deep learning), FSR 3 (AMD, open, includes Frame Generation), XeSS (Intel). All function as replacements for TSR/TAA in the AA post-process slot. Install via vendor plugin packages; they do not ship with the engine. DLSS Frame Generation requires DLSS 3+ and RTX 40+ series.

### Rendering Pipeline **[UE4 + UE5]**
UE5 defaults to Deferred Rendering. Forward Rendering is available for VR or mobile. The path significantly affects which lighting features are available. Nanite and Lumen require Deferred. VSM requires Deferred.

### Shader **[UE4 + UE5]**
A GPU program. In UE, materials compile to many shader permutations via the shader compilation system. Too many unique shaders increases PSO (Pipeline State Object) compilation stalls on first render. Use `stat shadercompiling` to track outstanding compilations.

### Material **[UE4 + UE5]**
A node graph that compiles to a shader. A material defines the shader topology. Material Instances (MIC / MID) share the parent's compiled shader but vary scalar/vector/texture parameters.

### Material Instance **[UE4 + UE5]**
A child of a master material. Shares the master's compiled shader, only overrides parameters. Dynamic Material Instances (MID) are created at runtime. Pool MIDs rather than creating them per-frame. Static Material Instances (MIC, the cooked asset) have zero overhead over the master.

### Material Pass **[UE4 + UE5]**
The render pass a material occupies: Opaque, Masked, or Translucent. Opaque is cheapest. Masked adds a discard step. Translucent renders in a separate pass and cannot receive accurate shadows from VSM or Lumen without special handling.

### LOD (Level of Detail) **[UE4 + UE5]**
A lower-polygon mesh substituted at distance to reduce GPU load. Still the primary strategy for non-Nanite geometry. In UE5 with Nanite enabled on a mesh, manual LODs are no longer used for rendering — Nanite manages its own internal LOD. Fallback LODs in Nanite meshes serve collision and non-Nanite render paths.

### World Partition **[UE5 only]**
UE5's streaming world system, replacing World Composition for new projects. Divides the world into a spatial grid of cells, streaming them in/out based on proximity to streaming sources (typically the player controller). Supports One-File-Per-Actor (OFPA) for source control. Key concepts: Runtime Grids, Data Layers, Level Instances, Packed Level Actors. **[Deprecated in UE5]**: World Composition is still available but not recommended for new UE5 projects.

### Data Layers **[UE5 only]**
World Partition concept grouping actors into logical layers that can be loaded/unloaded independently. Runtime Data Layers control game state (e.g., "occupied vs. destroyed village"). External Data Layers (EDL) separate DLC or seasonal content into plugins.

### HLOD (Hierarchical LOD) **[UE4 + UE5 — different impl]**
UE4 HLOD: generated merged meshes for distant clusters, configured per-HLOD Layer. UE5 World Partition HLOD: automatically built for streaming cells; supports Instanced (no decimation, keeps Nanite) and Merged (decimated mesh) types. HLOD1 also serves as Lumen's Far Field geometry (>1 km).

### Mesh Distance Fields **[UE4 + UE5]**
Volumetric distance field representation of each mesh, used by Software Lumen, dynamic shadow casting (DF shadows), and ambient occlusion. Enable per mesh in Static Mesh Editor > Build Settings > Generate Mesh Distance Field. Global setting: `Project Settings > Rendering > Generate Mesh Distance Fields`.

### Niagara **[UE4.20+ + UE5]**
UE's modern GPU and CPU particle system, replacing Cascade. Supports GPU simulations, Data Channels, Significance Manager integration, and neighbor queries. **[Deprecated in UE5]**: Cascade is still usable but not developed. Niagara is the standard.

### MetaSounds **[UE5 only]**
UE5's node-based audio DSP graph system. Replaces Sound Cues as the primary audio authoring tool in UE5. Supports per-instance parameters, procedural synthesis, and Quartz integration. **[UE4 only]**: Sound Cues remain the primary system in UE4.

### Iris **[UE5.4+ experimental, UE5.5+ shipping option]**
A rewrite of UE's replication data path. Separates gameplay from networking via replication state descriptors. Backward-compatible with existing UPROPERTY replication. Enabled via `net.Iris.UseIrisReplication=1`. Offers better scalability at high player counts versus the legacy Net Driver.

### Push Model Replication **[UE4.25+ + UE5]**
An opt-in optimization that skips property replication polling for actors that haven't changed. Instead of the engine scanning all replicated properties every frame, properties only replicate when explicitly marked dirty via `MARK_PROPERTY_DIRTY_FROM_NAME`. Significant server CPU savings for actors with infrequently-changing state.

### TSoftObjectPtr / TSoftClassPtr **[UE4 + UE5]**
Pointer types that store only an asset path (string). The asset is NOT loaded until explicitly resolved via `LoadSynchronous()` or `RequestAsyncLoad()`. Use to avoid loading assets at Blueprint startup. **[CORRECTED]**: An older version of this guide stated "TSoftObjectPtr uses dynamic_cast which is very expensive." This is wrong. UE never uses `dynamic_cast` in its `Cast<>` system — it walks the UClass tree via static lookup. The real performance concern with soft pointers is the synchronous resolve (`LoadSynchronous()`), which stalls the calling thread until the asset is loaded from disk. Cache the result; never call `LoadSynchronous()` in Tick.

### TObjectPtr **[UE5 only]**
UE5 replacement for raw `T*` in `UPROPERTY` class members. Compiles to a raw pointer in shipping builds (zero cost). In editor builds adds access tracking, lazy-load support, and better null diagnostics. Required for correct behavior with UE5.4+ incremental GC.

### TWeakObjectPtr **[UE4 + UE5]**
Non-owning pointer that becomes null automatically when the referenced UObject is garbage-collected. `Get()` incurs a `GUObjectArray` lookup (potential cache miss). Pattern: `if (UObject* Obj = WeakPtr.Get()) { ... }` — single dereference, null check, use.

### Subsystems **[UE4.22+ + UE5]**
Engine-managed singleton-like objects tied to the lifetime of their outer (Game Instance, World, Player Controller, etc.). The preferred replacement for custom manager actors and singletons. `UGameInstanceSubsystem`, `UWorldSubsystem`, `ULocalPlayerSubsystem`, `UEngineSubsystem`.

### Live Coding **[UE4.22+ default in UE5]**
Hot-patch compilation that recompiles and relinks function bodies in a running editor session. Safe only for changes inside function bodies (`.cpp` logic changes). Unsafe for UPROPERTY / UFUNCTION declaration changes, struct layout changes, or constructor changes — those require a full editor restart. **[Deprecated in UE5]**: Hot Reload (the older `Ctrl+Alt+F11` mechanism) is replaced by Live Coding as the default.

### Inclusive Time vs Exclusive Time **[UE4 + UE5]**
Inclusive time: wall time of a function including all called children. Exclusive time: time spent only in that function body, not children. Sort Insights Timers by Exclusive Time to find the single most expensive function scope.

### CPU Bound vs GPU Bound **[UE4 + UE5]**
CPU bound: the GPU is waiting for the CPU to finish (Game Thread or Render Thread is the bottleneck). GPU bound: the CPU is waiting for the GPU. Diagnosed with `stat unit`. You cannot fix GPU-bound scenes by optimizing CPU code.

### Substrate **[UE5.3+ experimental / UE5.5+ opt-in]**
UE5's new material shading model system replacing the fixed-function material domain system. Supports layered shading models, physically-based slab stacking, and heterogeneous material structures. Enabled via Project Settings > Rendering > Substrate. Not backward compatible — requires material conversion.
