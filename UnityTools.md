# Unity Optimization Tools Guide

---

## How to Read This Guide

This guide targets Unity 2018 through Unity 6 (6000.x), with emphasis on shipping to **PC/Steam**. Mobile and VR are explicitly out of scope. Every tip that differs meaningfully across engine generations is tagged:

- **[Pre-2020]** — Unity 2018/2019, Built-in RP era. Much of the workaround folklore on the internet comes from this period. Some of it is now obsolete.
- **[2020-2022 LTS]** — Unity 2020, 2021, and 2022 LTS. URP and HDRP stable, DOTS Entities 1.0, Addressables as the standard asset management layer, ObjectPool built in.
- **[Unity 6+]** — Unity 6 (October 2024) and later. GPU Resident Drawer, Render Graph mandatory in URP, STP upscaler, Adaptive Probe Volumes by default, Awaitable mature.
- **[All versions]** — Applies broadly across all three eras without meaningful change.

**Profile first.** Every section assumes you have the Unity Profiler open and a concrete marker pointing at the bottleneck. Optimizing without profiling data produces regressions as often as gains. [Unity profiling best practices](https://unity.com/how-to/best-practices-for-profiling-game-performance) state this plainly: measure before and after every change.

Unity's SRP Batcher is conceptually similar to UE's PSO caching in that both aim to reduce per-draw-call GPU state setup overhead — but they operate differently. The UE guide is your parallel reference for Unreal patterns; this guide mirrors its structure exactly for Unity equivalents.

---

## Table of Contents

- [How to Read This Guide](#how-to-read-this-guide)
- [Tools](#tools)
  - [Built-in Profiler [All versions]](#built-in-profiler-all-versions)
  - [Frame Debugger [All versions]](#frame-debugger-all-versions)
  - [Memory Profiler Package [2020-2022 LTS] (com.unity.memoryprofiler, from Unity 2018.3)](#memory-profiler-package-2020-2022-lts-comunitymemoryprofiler-from-unity-20183)
  - [Profile Analyzer Package [2020-2022 LTS] (com.unity.performance.profile-analyzer, from 2019)](#profile-analyzer-package-2020-2022-lts-comunityperformanceprofile-analyzer-from-2019)
  - [Deep Profile Mode [All versions]](#deep-profile-mode-all-versions)
  - [Custom Profiler Markers [All versions]](#custom-profiler-markers-all-versions)
  - [Standalone Profiler [Unity 6+] (available 2022.2+)](#standalone-profiler-unity-6-available-20222)
  - [Connecting to a Player Build (Remote Profiling) [All versions]](#connecting-to-a-player-build-remote-profiling-all-versions)
  - [RenderDoc / PIX / NSight [All versions]](#renderdoc-pix-nsight-all-versions)
  - [Build Report Inspector / Build Profiles [2020-2022 LTS] (introduced Unity 2022.2)](#build-report-inspector-build-profiles-2020-2022-lts-introduced-unity-20222)
  - [Profile in a Player Build, Not the Editor [All versions]](#profile-in-a-player-build-not-the-editor-all-versions)
  - [Editor Iteration Settings — Domain and Scene Reload [Unity 2019.3+]](#editor-iteration-settings-domain-and-scene-reload-unity-20193)
- [Prerequisites for Checkups](#prerequisites-for-checkups)
- [Basic Checkup List](#basic-checkup-list)
- [Advanced Checkup List](#advanced-checkup-list)
- [Bibliography and Further Reading](#bibliography-and-further-reading)
  - [Official Documentation](#official-documentation)
  - [Unity Blog](#unity-blog)
  - [Community Guides and Blogs](#community-guides-and-blogs)
  - [YouTube Channels and Videos](#youtube-channels-and-videos)
  - [Books](#books)
  - [Repositories and Samples](#repositories-and-samples)
  - [Community](#community)

---

## Tools

### Built-in Profiler **[All versions]**

The Unity Profiler (`Window → Analysis → Profiler`, `Ctrl+7`) is the primary diagnostic tool. [Unity Profiler docs](https://docs.unity3d.com/Manual/Profiler.html)

**Key modules for PC desktop:**
- **CPU Usage** — timeline and hierarchy of all thread work: main thread, render thread, job workers. Most important module. Use Timeline view first to understand frame shape; Hierarchy view to rank worst offenders by Total ms.
- **GPU Usage** — GPU timeline split into Geometry, Lighting, Shadows, Post-Processing, UI. Disabled when Graphics Jobs are on — use vendor tools in that case.
- **Rendering** — draw call count, batches, SetPass calls, shadow casters, triangles. Evaluate batching efficiency here.
- **Memory** — total allocated, GC heap, asset categories (textures, meshes, audio). Not a substitute for the Memory Profiler package.
- **Audio** — CPU time for mixing and DSP effects.
- **Physics** — time in physics simulation. Diagnose over-budget `FixedUpdate`.

**Timeline vs Hierarchy:** Timeline shows all threads simultaneously — essential for diagnosing sync stalls (`WaitForJob`, `Gfx.WaitForPresentOnGfxThread`). Hierarchy is a sorted table for ranking costly functions. Use Timeline first, Hierarchy to drill in.

The three "wait" markers you must distinguish:

| Marker | Meaning | Verdict |
|---|---|---|
| `WaitForTargetFPS` / `Gfx.SleepWorker` | Main thread idle, waiting for VSync or frame cap | Healthy — budget headroom |
| `Gfx.WaitForPresentOnGfxThread` | CPU waiting for GPU to finish previous frame | GPU-bound |
| `WaitForJobGroupID` | Main thread stalled on a CPU Job | Worker/DOTS bottleneck |

Call `Profiler.SetAreaEnabled` in code to disable noisy modules (Rendering, Audio, Physics) and narrow capture data.

### Frame Debugger **[All versions]**

`Window → Analysis → Frame Debugger` freezes on a single frame and displays every rendering event in sequence. Step through draw calls to see which mesh/material/shader was used, where the SRP Batcher created or broke batches, and render target state. [Unity Frame Debugger docs](https://docs.unity3d.com/Manual/frame-debugger-window.html)

**Key uses:**
- Diagnose why two objects are not batching (mismatched material, non-static flag, MaterialPropertyBlock, keyword mismatch)
- Understand URP render pass order (shadow map → depth prepass → opaque → transparent → post-processing)
- Inspect shader properties and texture bindings per draw call
- In Unity 6, shows Render Graph pass names for cleaner URP pass context

Attach to a standalone Development Build via the Target Selector dropdown for production-accurate data.

### Memory Profiler Package **[2020-2022 LTS]** (com.unity.memoryprofiler, from Unity 2018.3)

Install via Package Manager. Snapshot-based memory analysis of the entire managed heap, native allocations, Unity object references, and texture/mesh residency. [Memory Profiler docs](https://docs.unity3d.com/Packages/com.unity.memoryprofiler@1.1/manual/index.html)

**Key views:**
- **Summary** — total managed heap, native memory, GfxDriver (VRAM) at a glance
- **Objects and Allocations** — every Unity object by type and memory cost; invaluable for "why is this texture 80 MB?"
- **Residency View (Unity 6)** — shows actual physical RAM committed by the OS, more accurate than allocated size

Always snapshot in the player build, not the Editor. Compare snapshot at game start vs. after 20 minutes to identify gradual leaks.

### Profile Analyzer Package **[2020-2022 LTS]** (com.unity.performance.profile-analyzer, from 2019)

Aggregates data from a set of Profiler frames and computes statistics (median, mean, 99th percentile) per marker. **Compare mode** is the key feature: load two `.pdata` files side-by-side to validate whether an optimization changed median frame time for specific markers. [Profile Analyzer docs](https://docs.unity3d.com/Packages/com.unity.performance.profile-analyzer@1.2/manual/index.html)

Use it to confirm a LOD tweak actually reduced `Camera.Render` across 300 frames, not just one lucky frame.

### Deep Profile Mode **[All versions]**

Instruments every C# method call, not just `ProfilerMarker` scopes. Provides complete call stacks at the cost of 10×–100× frame time inflation. Use only for short (2–5 second) targeted captures after identifying the suspect system. Manual `ProfilerMarker`s are far less disruptive for narrow investigations.

### Custom Profiler Markers **[All versions]**

```csharp
// Modern zero-overhead approach — recommended
private static readonly ProfilerMarker s_SpawnMarker =
    new ProfilerMarker("MyGame.SpawnEnemies");

void Update()
{
    using (s_SpawnMarker.Auto())
    {
        SpawnIfNeeded();
    }
}

// Legacy — still works but sends full string per frame
Profiler.BeginSample("MyGame.SpawnEnemies");
// code
Profiler.EndSample();
```

`ProfilerMarker` transmits only an integer marker ID; `Profiler.BeginSample` sends the full string each frame. Both compile away in non-development builds via `[Conditional("ENABLE_PROFILER")]`. [Unity ProfilerMarker API](https://docs.unity3d.com/6000.3/Documentation/ScriptReference/Unity.Profiling.ProfilerMarker.html)

**Profiling Core API** `[2020-2022 LTS]` — `com.unity.profiling.core` provides `ProfilerCounter<T>` for custom numeric metrics (enemy count, active particle systems) visible in the Profiler window. [ProfilerCounter docs](https://docs.unity3d.com/Packages/com.unity.profiling.core@1.0/manual/profilercounter-guide.html)

### Standalone Profiler **[Unity 6+]** (available 2022.2+)

Launches the Profiler as a separate OS process, isolated from the Unity Editor. Most useful when profiling the Editor itself as the target or using Deep Profile on the Editor without the Profiler window contaminating the data. [Unity Standalone Profiler docs](https://docs.unity3d.com/6000.4/Documentation/Manual/profiler-standalone-process.html)

### Connecting to a Player Build (Remote Profiling) **[All versions]**

1. Enable **Development Build** and **Autoconnect Profiler** in Build Settings.
2. Build & Run — the player launches and auto-connects to the Profiler window.
3. For different machines: select the device from the **Attach to Player** dropdown or type IP directly.
4. Firewall: open UDP/TCP ports **54998–55511**.
5. For startup analysis: enable **Deep Profiling Support** in Build Settings. [Unity profiling applications docs](https://docs.unity3d.com/2022.3/Documentation/Manual/profiler-profiling-applications.html)

### RenderDoc / PIX / NSight **[All versions]**

**RenderDoc** (free): Built-in Unity integration via right-click on Game View → Load RenderDoc. Captures full frame state: draw calls, textures, buffers, render targets. Indispensable for visual rendering artifacts and SRP pass order verification. Add `#pragma enable_d3d11_debug_symbols` for shader debugging. [Unity RenderDoc docs](https://docs.unity3d.com/2017.1/Documentation/Manual/RenderDocIntegration.html)

**PIX** (Windows): DX11/DX12 pipeline state analysis, resource binding, shader occupancy. [PIX on Windows](https://devblogs.microsoft.com/pix/)

**NVIDIA Nsight Graphics**: Full GPU pipeline debugger with ray-tracing support for DX12/Vulkan. Use Nsight Systems first for CPU-GPU timeline; Nsight Graphics for per-draw-call metrics. [NVIDIA Nsight Systems](https://developer.nvidia.com/nsight-systems)

Note: Unity's GPU Profiler module is disabled when Graphics Jobs are enabled — use vendor tools for GPU timings in that configuration.

### Build Report Inspector / Build Profiles **[2020-2022 LTS]** (introduced Unity 2022.2)

Install `com.unity.build-report-inspector`. Open via **Assets → Open Last Build Report**. Shows:
- Build step timings (which step is slowest: shader compilation, texture compression?)
- Asset breakdown by size in final build — find the 200 MB texture that slipped in
- Scene object summary and managed stripping information

**Build Profiles** (Unity 2023.1+): Named build configurations that persist platform, scenes, and Player Settings overrides. Replaces manual per-platform Build Settings workflow. [QA/Build section for details](#qabuild-section-for-details)

### Profile in a Player Build, Not the Editor **[All versions]**

Profiling in Editor Play mode inflates all timings: the Editor's own rendering, asset database operations, and `EditorLoop` all run in-process. `GC.Alloc` counts are elevated by Editor infrastructure. Driver heuristics may behave differently. Relative timings under Deep Profile become meaningless.

**Rule:** Identify candidate problems in editor Play mode, then validate every timing decision against a Development Build player on target hardware. This rule applies especially to GC allocation counts, shader compile stutter, and GPU timing. [Unity profiling applications docs](https://docs.unity3d.com/2022.3/Documentation/Manual/profiler-profiling-applications.html)

### Editor Iteration Settings — Domain and Scene Reload **[Unity 2019.3+]**

In **Project Settings → Editor → Enter Play Mode Settings**:
- **Disable Domain Reload**: Skip AppDomain reinitialization on Play. Saves 5–30 seconds per play press on large projects. Requires static field initialization via `[RuntimeInitializeOnLoadMethod]` or explicit `Awake()`/`Start()`.
- **Disable Scene Reload**: Skip scene reconstruction. Even faster iteration. Requires code that doesn't depend on scene-reload state.

Combined, these two toggles are the highest-impact editor iteration improvement available to teams. Zero shipping impact.

---

## Prerequisites for Checkups

Before running any optimization sweep, confirm these baseline conditions are met:

1. **Target frame budget is defined.** For 60 FPS on PC: 16.67 ms/frame. For 30 FPS: 33.33 ms. Know your target before touching any setting.
2. **Profiler is connected to a Development Build player**, not the editor.
3. **A representative test scene or sequence is identified.** Profile the worst-case scenario your players will encounter: the most crowded area, the most particle-dense combat moment, the heaviest UI screen.
4. **Baseline profile is saved.** Capture 100+ frames with Profile Analyzer and save the `.pdata` file. Every subsequent optimization should be compared against this baseline.
5. **Hardware target is defined.** For Steam PC, know your minimum spec: integrated graphics? Budget discrete? This determines which render path, shadow quality, and effect toggles are viable.
6. **Scripting backend and build configuration are set correctly.** Always validate on an IL2CPP build for final shipping numbers; Mono builds run measurably slower.
7. **VSync is in a known state.** Always record whether VSync was on during profiling. `WaitForTargetFPS` showing as main thread work when VSync is on is not a bug — it is budget headroom.

---

## Basic Checkup List

These are the first things to check on any Unity project before investigating further:

- **Profiler: Is the game CPU-bound or GPU-bound?** Check `Gfx.WaitForPresentOnGfxThread` (GPU-bound) vs. `BehaviourUpdate`/`Physics.Processing` dominating (CPU-bound). Different problems, different solutions.
- **Frame Debugger: Are draw calls in the expected range?** For a mid-complexity PC game, 500–1500 draw calls/frame is typical. If you see 5,000+, batching is broken somewhere.
- **SRP Batcher compatibility.** Open Frame Debugger and expand the SRP Batcher section. Are batches large (50+ draw calls each) or tiny (1–2 each)? Small batches indicate MaterialPropertyBlock usage, per-object materials, or non-compatible shaders.
- **GC.Alloc per frame.** Sort CPU Profiler Hierarchy by GC Alloc. Is there significant allocation in steady-state gameplay? Target: 0 bytes allocated per frame.
- **Memory snapshot.** Total resident memory in the range expected for your VRAM budget? Textures dominating? Meshes with Read/Write Enabled?
- **Rendering module stats.** Shadow caster count, triangle count, visible renderers. Unexpectedly high triangle counts suggest missing LODs.
- **Quality Settings active tier.** Is the expected tier (High, Medium, etc.) active for the profiled build?
- **IL2CPP backend active?** Check Player Settings → Other Settings → Scripting Backend. Ship with IL2CPP.
- **Domain Reload disabled?** If not, every play press costs 5–30 seconds. Fix this first for iteration speed.

---

## Advanced Checkup List

After passing basic checks, investigate:

- **ProfilerMarker granularity.** Have you placed ProfilerMarkers on every major system (AI, Physics, Spawning, VFX, UI)? Without them, the Hierarchy will show generic markers like `BehaviourUpdate` with no sub-detail.
- **GPU module (if available).** Identify the heaviest GPU pass: Geometry, Shadows, or Post-Processing? This determines the next action.
- **Shader variant count.** Check via `log shader compilation` in Player settings. Are you compiling more than a few hundred variants? Variant explosion is a common silent cost.
- **Texture memory.** Memory Profiler → Objects and Allocations → sort by memory. Are there textures without Crunch compression, with unnecessarily high max size, or with Read/Write Enabled?
- **Audio clip load types.** Are long music files set to Decompress on Load? They should be Streaming.
- **Animator culling mode.** Are off-screen Animators running `AlwaysAnimate`? They should use `CullCompletely` for background NPCs.
- **Canvas rebuild rate.** Are Canvases rebuilding every frame? Frame Debugger → UI.Render shows Canvas draw calls. Dynamic elements mixed into a static Canvas = constant rebuilds.
- **Job System integration.** For any computation touching > 1,000 data elements, is it on the Job System? Check `WorkerThread` activity in Profiler Timeline.
- **Physics auto-sync transforms.** If `Physics.autoSyncTransforms` is still true (the default), consider disabling it for physics-heavy scenes. [TheGameDev.Guru physics sync](https://thegamedev.guru/unity-cpu-performance/physics-autosynctransforms/)
- **LOD bias tuning.** `QualitySettings.lodBias` default is 1.0. Competitive titles often find 0.7–0.85 hits the right quality-performance balance.
- **Addressables duplicate dependencies.** Run **Check Duplicate Bundle Dependencies** in the Addressables Analyze window. Shared textures pulled into multiple bundles inflate memory.
- **Graphics Jobs status.** Is **Graphics Jobs (Experimental)** enabled in Player Settings? If so, the GPU module in the Profiler is disabled. Disable Graphics Jobs temporarily for GPU profiling, then re-enable for final builds if your pipeline supports it.
- **IL2CPP code generation mode.** Is it set to "Faster runtime"? This setting (Unity 2021+) in Player Settings → IL2CPP Code Generation is the single-line build change that most reliably improves shipped game startup and GC performance.
- **RenderTexture releases.** Are any `RenderTexture.GetTemporary()` calls not paired with `RenderTexture.ReleaseTemporary()`? Unreleased temporary RTs accumulate in the GPU memory pool silently.
- **First-frame spike.** Add a `ProfilerMarker` around your scene setup code and check whether the first frame is taking 200+ ms. Shader compilation on first use (`ShaderLab.CreateGpuProgram`) and large synchronous asset loads are the usual culprits.
- **Worker thread utilization.** In CPU Timeline, are all available worker threads busy during Job System execution, or are jobs finishing on 1–2 threads with others idle? Idle workers indicate job batch count is too large (reduce `innerloopBatchCount` on `IJobParallelFor`) or dependency chains are too sequential.

---

## Bibliography and Further Reading

### Official Documentation

- [Unity Profiler (Manual)](https://docs.unity3d.com/Manual/Profiler.html)
- [Unity profiling best practices](https://unity.com/how-to/best-practices-for-profiling-game-performance)
- [Unity profiling applications](https://docs.unity3d.com/2022.3/Documentation/Manual/profiler-profiling-applications.html)
- [SRP Batcher (Manual)](https://docs.unity3d.com/Manual/SRPBatcher.html)
- [GPU instancing (Manual)](https://docs.unity3d.com/6000.6/Documentation/Manual/GPUInstancing.html)
- [GPU Resident Drawer (URP)](https://docs.unity3d.com/6000.0/Documentation/Manual/urp/gpu-resident-drawer.html)
- [Render Graph introduction (URP)](https://docs.unity3d.com/6000.3/Documentation/Manual/urp/render-graph-introduction.html)
- [Write a render pass using Render Graph](https://docs.unity3d.com/6000.0/Documentation/Manual/urp/render-graph-write-render-pass.html)
- [Rendering paths comparison (URP)](https://docs.unity3d.com/6000.1/Documentation/Manual/urp/rendering-paths-comparison.html)
- [Adaptive Probe Volumes concept (Unity 6)](https://docs.unity3d.com/6000.2/Documentation/Manual/urp/probevolumes-concept.html)
- [APV usage guide (Unity 6)](https://docs.unity3d.com/6000.3/Documentation/Manual/urp/probevolumes-use.html)
- [STP upscaler (Unity 6)](https://docs.unity3d.com/6000.1/Documentation/Manual/urp/stp/stp-upscaler.html)
- [Shadow cascades (Unity 6)](https://docs.unity3d.com/6000.3/Documentation/Manual/shadow-cascades-use.html)
- [Mixed lighting (Unity 2019)](https://docs.unity3d.com/2019.2/Documentation/Manual/LightMode-Mixed.html)
- [Occlusion Culling (Unity 6)](https://docs.unity3d.com/6000.4/Documentation/Manual/OcclusionCulling.html)
- [GPU Occlusion Culling URP](https://docs.unity3d.com/6000.0/Documentation/Manual/urp/gpu-culling.html)
- [LOD Group (Manual)](https://docs.unity3d.com/Manual/class-LODGroup.html)
- [BatchRendererGroup API](https://docs.unity3d.com/Manual/batch-renderer-group.html)
- [Entities Graphics (Manual)](https://docs.unity3d.com/Packages/com.unity.entities.graphics@1.3/manual/index.html)
- [Burst Compiler (Manual)](https://docs.unity3d.com/Packages/com.unity.burst@1.8/manual/index.html)
- [Job System (Manual)](https://docs.unity3d.com/Manual/JobSystem.html)
- [Garbage collection best practices](https://docs.unity3d.com/2022.3/Documentation/Manual/performance-garbage-collection-best-practices.html)
- [Incremental GC (Manual)](https://docs.unity3d.com/Manual/performance-incremental-garbage-collection.html)
- [IL2CPP scripting backend](https://docs.unity3d.com/Manual/scripting-backends-intro.html)
- [Shader variants (Manual)](https://docs.unity3d.com/Manual/shader-variants.html)
- [Shader variant stripping](https://docs.unity3d.com/2021.3/Documentation/Manual/shader-variant-stripping.html)
- [Custom Function Node (Shader Graph)](https://docs.unity3d.com/Packages/com.unity.shadergraph@17.0/manual/Custom-Function-Node.html)
- [Draw call batching (Manual)](https://docs.unity3d.com/cn/2021.3/Manual/optimizing-draw-calls.html)
- [Texture compression formats (Manual)](https://docs.unity3d.com/2021.3/Documentation/Manual/class-TextureImporterOverride.html)
- [Mipmap Streaming (Manual)](https://docs.unity3d.com/2021.3/Documentation/Manual/TextureStreaming.html)
- [Mesh.indexFormat (Scripting API)](https://docs.unity3d.com/6000.3/Documentation/ScriptReference/Mesh-indexFormat.html)
- [Addressables (Manual)](https://docs.unity3d.com/Packages/com.unity.addressables@2.3/manual/index.html)
- [Per-frame event optimization (Unity 6)](https://docs.unity3d.com/6000.4/Documentation/Manual/events-per-frame-optimization.html)
- [Physics autoSyncTransforms](https://docs.unity3d.com/6000.3/Documentation/Manual/physics-optimization-cpu-transform-sync.html)
- [AudioClip import settings](https://docs.unity3d.com/6000.4/Documentation/Manual/class-AudioClip.html)
- [Animation performance (Manual)](https://docs.unity3d.com/6000.4/Documentation/Manual/MecanimPeformanceandOptimization.html)
- [UI Optimization Tips (Unity)](https://unity.com/how-to/unity-ui-optimization-tips)
- [UI system comparison (Unity 6)](https://docs.unity3d.com/6000.4/Documentation/Manual/UI-system-compare.html)
- [Netcode for GameObjects — Tick and Update Rates](https://docs.unity3d.com/Packages/com.unity.netcode.gameobjects@2.5/manual/learn/ticks-and-update-rates.html)
- [Entities 1.0 — Baker Overview](https://docs.unity3d.com/Packages/com.unity.entities@1.0/manual/baking-baker-overview.html)
- [Entities 1.0 — SystemAPI.Query](https://docs.unity3d.com/Packages/com.unity.entities@1.0/manual/systems-systemapi-query.html)
- [Profile Analyzer](https://docs.unity3d.com/Packages/com.unity.performance.profile-analyzer@1.2/manual/index.html)
- [Memory Profiler](https://docs.unity3d.com/Packages/com.unity.memoryprofiler@1.1/manual/index.html)
- [ProfilerMarker API](https://docs.unity3d.com/6000.3/Documentation/ScriptReference/Unity.Profiling.ProfilerMarker.html)
- [Standalone Profiler](https://docs.unity3d.com/6000.4/Documentation/Manual/profiler-standalone-process.html)
- [Choose a render pipeline](https://docs.unity3d.com/Manual/choose-a-render-pipeline.html)
- [BIRP deprecated in Unity 6.5](https://www.maxkillstudios.com/learn/birp-deprecated-migrate-urp-or-wait)
- [Choosing your particle system solution](https://docs.unity3d.com/6000.4/Documentation/Manual/ChoosingYourParticleSystem.html)
- [VFX Graph Visual Effect Bounds](https://docs.unity3d.com/Packages/com.unity.visualeffectgraph@17.6/manual/visual-effect-bounds.html)
- [URP Rendering Layers](https://docs.unity3d.com/Packages/com.unity.render-pipelines.universal@14.0/manual/features/rendering-layers.html)
- [Camera Stacking (URP)](https://docs.unity3d.com/Packages/com.unity.render-pipelines.universal@7.2/manual/camera-stacking.html)
- [HDRP Volumetric Fog](https://docs.unity3d.com/Packages/com.unity.render-pipelines.high-definition@12.0/manual/Override-Fog.html)
- [Optimizing UI Toolkit](https://docs.unity.cn/6000.3/Documentation/Manual/best-practice-guides/ui-toolkit-for-advanced-unity-developers/optimizing-performance.html)

### Unity Blog

- [Saving memory with Addressables](https://unity.com/blog/technology/tales-from-the-optimization-trenches-saving-memory-with-addressables)
- [Unite 2022 – Performance in Unity](https://www.youtube.com/c/UnityTechnologies)
- [Unity SRP Batcher — official deep dive](https://blog.unity.com/engine-platform/srp-batcher-speed-up-your-rendering)

### Community Guides and Blogs

- [TheGameDev.Guru — Draw Call Batching: The Ultimate Guide](https://thegamedev.guru/unity-performance/draw-call-optimization/)
- [TheGameDev.Guru — Physics autoSyncTransforms](https://thegamedev.guru/unity-cpu-performance/physics-autosynctransforms/)
- [TheGameDev.Guru — Render Modes and Graphics Jobs](https://thegamedev.guru/unity-cpu-performance/rendermodes-graphics-jobs/)
- [Tarodev — Unity Optimization Tips](https://www.youtube.com/c/Tarodev) — YouTube channel with practical optimization walkthroughs
- [Code Monkey — Unity Tutorial Channel](https://www.youtube.com/c/CodeMonkeyUnity) — DOTS, ECS, UI, practical Unity systems
- [Catlike Coding — Unity Tutorials](https://catlikecoding.com/unity/tutorials/) — Deep-dive rendering, lighting, and shader tutorials
- [Acerola — Unity Rendering](https://www.youtube.com/c/Acerola_t) — Shader math and custom rendering
- [Game Dev Guide — Unity](https://www.youtube.com/c/GameDevGuide) — UI, animation, editor tooling
- [NotSlot — Unity Optimization](https://www.youtube.com/@NotSlot) — Performance-focused Unity content
- [fazz.dev — SRP Batcher deep dive](https://fazz.dev/articles/building-srp-part-three)
- [Azur Games — SRP Batcher optimization](https://azurgames.com/blog/optimizing-the-midcore-increasing-fps-using-srp-batcher/)
- [Angry Shark Studio — UI Toolkit vs UGUI 2025](https://www.angry-shark-studio.com/blog/unity-ai-toolkit-vs-ugui-2025-guide/)
- [Coffee Brain Games — Reducing Compile Time with asmdef](https://coffeebraingames.wordpress.com/2018/01/21/reducing-compile-time-in-unity-using-assembly-definition-files/)
- [Generalist Programmer — Burst Compiler Guide](https://generalistprogrammer.com/tutorials/unity-burst-compiler-complete-performance-optimization-guide)
- [Embrace.io — GC spikes in Unity](https://embrace.io/blog/garbage-collector-spikes-unity/)
- [JetBrains Rider — Camera.main inspection](https://www.jetbrains.com/help/rider/Unity.PerformanceCriticalCodeCameraMain.html)
- [Nathan Reed — Understanding BCn texture compression](https://www.reedbeta.com/blog/understanding-bcn-texture-compression-formats/)
- [Game Developer — Unity Audio Import Optimisation](https://www.gamedeveloper.com/audio/unity-audio-import-optimisation---getting-more-bam-for-your-ram)
- [Steam Audio Unity Guide](https://valvesoftware.github.io/steam-audio/doc/unity/guide.html)
- [Mirror — Lag Compensation](https://mirror-networking.gitbook.io/docs/manual/general/lag-compensation)
- [HackerNoon — Unity 2023.1 Awaitable Class](https://hackernoon.com/unity-20231-introduces-awaitable-class)
- [NativeContainer allocators guide — Outscal](https://outscal.com/blog/how-to-choose-and-manage-collections-for-performance-in-unity)
- [Techarthub — Texture Compression in Unity](https://techarthub.com/an-introduction-to-texture-compression-in-unity/)
- [Chunk iteration in Entities 1.0 — Coffee Brain Games](https://coffeebraingames.wordpress.com/2023/06/25/chunk-iteration-in-entities-1-0/)

### YouTube Channels and Videos

- [Tarodev](https://www.youtube.com/c/Tarodev) — Practical C#, DOTS, performance
- [Code Monkey](https://www.youtube.com/c/CodeMonkeyUnity) — DOTS, ECS, UI, Unity systems
- [Catlike Coding](https://catlikecoding.com/unity/tutorials/) — Rendering, shaders, mathematics
- [Sebastian Lague](https://www.youtube.com/c/SebastianLague) — Procedural generation, creative coding
- [Acerola](https://www.youtube.com/c/Acerola_t) — Custom rendering, shader mathematics
- [Game Dev Guide](https://www.youtube.com/c/GameDevGuide) — Editor tooling, animation, UI
- [NotSlot](https://www.youtube.com/@NotSlot) — Performance, ECS, systems architecture
- [Brackeys (legacy)](https://www.youtube.com/c/Brackeys) — Legacy tutorials; many patterns no longer optimal in Unity 6 but useful for concept background
- [DOUBLE Unity Animation Performance — GPU Skinning](https://www.youtube.com/watch?v=apD2NgXulxE)
- [How to use Adaptive Probe Volumes Unity 6](https://www.youtube.com/watch?v=4plpXdjWgOI)
- [Unity 6 Mesh LOD Tutorial](https://www.youtube.com/watch?v=A0b2MfHCCfU)
- [DOTS Animation — Code Monkey](https://www.youtube.com/watch?v=P01egjRl2cs)
- [Netcode for GameObjects Tutorial](https://www.youtube.com/watch?v=swIM2z6Foxk)

### Books

- **"Unity Game Optimization, 3rd Edition"** — Chris Dickinson. The most comprehensive single-volume reference for Unity performance. Covers CPU, GPU, memory, physics, and audio in depth. Published by Packt; available in print and digital.
- **"Game Programming Patterns"** — Robert Nystrom (free at [gameprogrammingpatterns.com](http://gameprogrammingpatterns.com)). Not Unity-specific but covers object pooling, event queues, component patterns, and data locality — directly applicable.
- **"Data-Oriented Design"** — Richard Fabian (free at [dataorienteddesign.com](https://www.dataorienteddesign.com/dodbook/)). The theoretical foundation for DOTS/ECS; useful for understanding why ECS outperforms OOP at scale.

### Repositories and Samples

- [Unity DOTS Samples — GitHub](https://github.com/Unity-Technologies/EntityComponentSystemSamples) — Official ECS, Jobs, and Burst samples
- [Unity Boss Room — GitHub](https://github.com/Unity-Technologies/com.unity.multiplayer.samples.coop) — Production NGO multiplayer reference
- [Unity HLOD System — GitHub](https://github.com/Unity-Technologies/HLODSystem) — Hierarchical LOD for large scenes
- [Compilation Visualizer — GitHub (Needle Tools)](https://github.com/needle-tools/compilation-visualizer) — asmdef dependency audit
- [Awesome Unity — GitHub](https://github.com/RyanNielson/awesome-unity) — Curated Unity resources list
- [XeSS Unity Plugin — GitHub (Intel)](https://github.com/GameTechDev/XeSSUnityPlugin) — Open-source XeSS integration
- [UniTask — GitHub (Cysharp)](https://github.com/Cysharp/UniTask) — Zero-allocation async/await for Unity

### Community

- [r/Unity3D](https://www.reddit.com/r/Unity3D/) — Broad community; performance discussions, gotcha reports, version-specific discoveries
- [Unity Forums](https://discussions.unity.com/) — Official support forums; engine team responses on ambiguous behavior
- [Unity Discord (official)](https://discord.gg/unity) — Real-time community help
- [Brackeys Discord (community)](https://discord.gg/brackeys) — Large community, accessible for beginners
- [Unity Road Map](https://unity.com/roadmap) — Track upcoming features before they ship to avoid investing in soon-to-be-superseded patterns
