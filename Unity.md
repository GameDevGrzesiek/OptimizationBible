# Unity Optimization Guide

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

## Glossary  

You can find it [HERE](https://github.com/GameDevGrzesiek/OptimizationBible/blob/main/Definitions.md)

---

## Tools

You can find them [HERE](https://github.com/GameDevGrzesiek/OptimizationBible/blob/main/UnityTools.md)

---

## Table of Contents

- [How to Read This Guide](#how-to-read-this-guide)
- [Glossary](#glossary)
- [Tools](#tools)
- [Guidelines per Specialization](#guidelines-per-specialization)
  - [General Tips](#general-tips)
  - [Code & Mechanics (C# Programmers / Gameplay Engineers)](#code-mechanics-c-programmers-gameplay-engineers)
  - [Burst, Jobs, and DOTS Programmers](#burst-jobs-and-dots-programmers)
  - [Level Design / Environment](#level-design-environment)
  - [Materials / Shader Authors](#materials-shader-authors)
  - [Meshes / 3D Art](#meshes-3d-art)
  - [Lights & Shadows](#lights-shadows)
  - [VFX (Particle System and VFX Graph)](#vfx-particle-system-and-vfx-graph)
  - [Audio](#audio)
  - [Animations](#animations)
  - [Physics](#physics)
  - [UI (UGUI and UI Toolkit)](#ui-ugui-and-ui-toolkit)
  - [Networking and Multiplayer](#networking-and-multiplayer)
  - [QA / Build / Production](#qa-build-production)
  - [Tech Art](#tech-art)
  - [Last Resort Methods](#last-resort-methods)
- [Profiling Workflow Reference](#profiling-workflow-reference)
  - [Session 1: Identifying the Bottleneck Type](#session-1-identifying-the-bottleneck-type)
  - [Session 2: GC Allocation Hunting](#session-2-gc-allocation-hunting)
  - [Session 3: GPU Bottleneck Isolation](#session-3-gpu-bottleneck-isolation)
  - [Session 4: First-Frame and Load Spike](#session-4-first-frame-and-load-spike)
  - [Session 5: Memory Audit](#session-5-memory-audit)
  - [Profiling Checklist (Quick Reference)](#profiling-checklist-quick-reference)
- [Optimization Sweep Steps (Pre-Milestone Checklist)](#optimization-sweep-steps-pre-milestone-checklist)
  - [Scene Audit](#scene-audit)
  - [Meshes / Models](#meshes-models)
  - [Lighting](#lighting)
  - [VFX](#vfx)
  - [UI](#ui)
  - [Streaming and Memory](#streaming-and-memory)
  - [Physics Sweep](#physics-sweep)
  - [Networking Sweep](#networking-sweep)
  - [Build and Cook Validation](#build-and-cook-validation)
- [Top 30 Most Common Mistakes](#top-30-most-common-mistakes)
- [Knobs and Settings Cheat Sheet](#knobs-and-settings-cheat-sheet)
  - [Player Settings](#player-settings)
  - [Quality Settings](#quality-settings)
  - [URP Asset Key Knobs](#urp-asset-key-knobs)
  - [HDRP Frame Settings](#hdrp-frame-settings)
  - [Build Profile Toggles (Unity 2023.1+)](#build-profile-toggles-unity-20231)
  - [Quality Scalability Recommendations](#quality-scalability-recommendations)
  - [Physics Project Settings Reference](#physics-project-settings-reference)
  - [Audio Project Settings Reference](#audio-project-settings-reference)
  - [Editor Performance Settings Reference [All versions]](#editor-performance-settings-reference-all-versions)
- [Unity ↔ UE Concept Bridge](#unity-ue-concept-bridge)
- [Version Migration Notes](#version-migration-notes)
  - [Migrating from Built-in RP to URP [Pre-2020] → [2020-2022 LTS]](#migrating-from-built-in-rp-to-urp-pre-2020-2020-2022-lts)
  - [Migrating from Unity 2020/2021 to Unity 2022 LTS [2020-2022 LTS era internal]](#migrating-from-unity-20202021-to-unity-2022-lts-2020-2022-lts-era-internal)
  - [Migrating to Unity 6 [2020-2022 LTS] → [Unity 6+]](#migrating-to-unity-6-2020-2022-lts-unity-6)
  - [Performance Regressions to Watch After Unity Version Upgrades](#performance-regressions-to-watch-after-unity-version-upgrades)
- [Bibliography and Further Reading](#bibliography-and-further-reading)
  - [Official Documentation](#official-documentation)
  - [Unity Blog](#unity-blog)
  - [Community Guides and Blogs](#community-guides-and-blogs)
  - [YouTube Channels and Videos](#youtube-channels-and-videos)
  - [Books](#books)
  - [Repositories and Samples](#repositories-and-samples)
  - [Community](#community)

---

## Guidelines per Specialization

### General Tips

These apply regardless of discipline. Every specialist should know them.

**Common pitfalls:**
- **[All versions]** Caching `Camera.main` is still good practice even post-Unity 2019.4.9, where it was optimized from `FindGameObjectsWithTag` to an internal cache. It still crosses the native boundary; cache it in `Start()`.
- **[All versions]** `GetComponent<T>()` in `Update()` is a guaranteed frame-rate destroyer. Every call traverses the component list on that GameObject. Cache in `Awake()`.
- **[All versions]** `FindObjectOfType<T>()`, `FindGameObjectsWithTag()`, and `GameObject.Find()` in the update loop are O(n) searches of the entire scene. Never call them per-frame.
- **[All versions]** `Instantiate()` and `Destroy()` in the hot path cause GC pressure, frame spikes, and hitches on lower-end hardware. Everything spawned at runtime must be pooled.
- **[All versions]** `CompareTag("Enemy")` over `gameObject.tag == "Enemy"` — the string property version allocates on every comparison.
- **[Pre-2020]** `new WaitForSeconds(1f)` inside a coroutine loop allocates on every iteration. Cache the instance as a static readonly field.
- **[2020-2022 LTS]** Mono backend for shipping builds. Always ship IL2CPP.

**Recommended practices:**
- Identify CPU vs GPU bound before any optimization. The fix for a CPU bottleneck (reduce Update calls, use Jobs) is completely different from a GPU fix (reduce draw calls, lower shadow distance, drop render scale).
- Use `ProfilerMarker` on every major system boundary so the Hierarchy is meaningful.
- Profile on the minimum-spec hardware you ship for, not your dev machine.
- Use `QualitySettings.SetQualityLevel()` to expose Low/Medium/High/Ultra tiers to players. Ship with at least three tiers.
- Use `[RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]` for global service initialization that must survive scene transitions.
- Prefer structs over classes for frequently instantiated small objects (Vector3, Matrix4x4, custom data containers) to reduce GC pressure.
- Use `sqrMagnitude` for distance comparisons — `(a - b).sqrMagnitude < range * range` avoids a `sqrt` call.
- Enable **Enter Play Mode Settings** (Disable Domain Reload + Disable Scene Reload) immediately on any project with more than a handful of scripts — the daily iteration time saved is enormous. [Unity 2019.3+]
- Ship with `QualitySettings.vSyncCount = 1` as the default, not 0. Uncapped frame rate on a PC with a fast GPU can drive temperatures up and cause thermal throttling on the minimum-spec machine during profiling, masking real numbers.
- Use `Application.runInBackground = false` in shipped builds unless your game needs background execution. Every frame saved when the window is unfocused is CPU you get back.
- The Unity Profiler's `Others` bar in Play mode represents EditorLoop work — large `Others` in editor profiling is not game overhead and does not appear in builds. Do not optimize against it.
- For any object that needs to be found by other systems, register it with a central service locator or event system at `Awake()`. Never search for it with `FindObjectOfType<T>()` later.
- `Time.timeScale = 0` pauses the game but `FixedUpdate` still runs at zero-time steps and `Update` still ticks. If your game has a pause menu with expensive scripts, disable irrelevant MonoBehaviours explicitly on pause.
- Profile the **first frame** separately from steady-state. First-frame costs (shader compilation, texture upload, audio loading) can spike to 200 ms or more and are invisible in a steady-state capture.

**Cheat sheet — cross-discipline quick wins:**

| Action | Time cost | Discipline |
|---|---|---|
| Disable Domain Reload | 5–30 s per play press | All |
| Add asmdef files | 60–80% compile time reduction | Programmers |
| IL2CPP "Faster runtime" | Ship faster startup | QA/Build |
| `CullCompletely` on off-screen Animators | Saves per-NPC animation eval | Animation |
| Disable Raycast Target on decorative UI | Input iteration cost | UI |
| Set VFX Graph bounds to Manual | Enables off-screen culling | VFX |
| Force to Mono on all 3D audio | Halves audio memory | Audio |
| `shader_feature_local` over `multi_compile` | Strips unused variants | Materials |
| LOD Bias 0.7 instead of 1.0 | Earlier LOD transitions, lower triangle count | Level Design |
| BC5 for normal maps | Better quality at same size | Art/Tech Art |

---

### Code & Mechanics (C# Programmers / Gameplay Engineers)

Gameplay code is the most common source of CPU-bound frame-rate problems in indie projects. The following covers the patterns that matter most at production scale.

**Common pitfalls:**
- **[All versions]** `Camera.main` in `Update()` — still a native boundary crossing. Cache in `Start()`. [JetBrains Rider Camera.main docs](https://www.jetbrains.com/help/rider/Unity.PerformanceCriticalCodeCameraMain.html)
- **[All versions]** `GetComponent<T>()` in `Update()` without caching. Scene-traversal operation on every call.
- **[All versions]** `Instantiate` without pooling — causes GC spikes and frame hitches on spawn.
- **[All versions]** String concatenation in `Update()` — immutable strings, every concatenation allocates.
- **[All versions]** LINQ in hot paths — every expression allocates at minimum one enumerator object.
- **[All versions]** `foreach` over an `IEnumerable<T>` interface variable boxes the struct enumerator. Use concrete `List<T>`.
- **[Pre-2020]** `new WaitForSeconds()` inside a coroutine loop — allocates every iteration. Cache as `private static readonly`.
- **[2020-2022 LTS]** Lambda closures capturing local variables in hot paths. Compiled to heap-allocated closure objects.
- **[All versions]** `Update()` on 10,000+ MonoBehaviours — native-to-managed interop overhead at scale. [Custom tick manager 4–11× faster](https://www.reddit.com/r/Unity3D/comments/697auh/monobehaviour_update_performance_vs_handling/).

**Recommended practices:**
- Use `UnityEngine.Pool.ObjectPool<T>` (Unity 2021+) for all runtime-spawned objects:

```csharp
using UnityEngine.Pool;

private IObjectPool<Bullet> _pool;

void Awake()
{
    _pool = new ObjectPool<Bullet>(
        createFunc:      () => Instantiate(bulletPrefab),
        actionOnGet:     b  => b.gameObject.SetActive(true),
        actionOnRelease: b  => b.gameObject.SetActive(false),
        actionOnDestroy: b  => Destroy(b.gameObject),
        defaultCapacity: 20,
        maxSize: 100
    );
}
```
[Object pooling in Unity 2021+](https://www.gamedeveloper.com/design/object-pooling-in-unity-2021-)

- Implement a tick manager pattern for scenes with hundreds of MonoBehaviours with `Update()`: one singleton with a `List<IUpdatable>`, one native-to-managed crossing per frame regardless of subscriber count. [Unity 6 manual example](https://docs.unity3d.com/6000.4/Documentation/Manual/events-per-frame-optimization.html)
- Cache `LayerMask.GetMask()` results as `private static readonly int` — string hashing per call otherwise.
- Use `transform.GetPositionAndRotation(out pos, out rot)` **[Unity 2021.3+]** to halve native crossings when reading both values.
- Cache `Animator.StringToHash("ParameterName")` as static readonly ints, pass int overloads of `SetFloat`, `SetBool`.
- Reserve `FixedUpdate` strictly for physics operations (`Rigidbody`, `AddForce`). Non-physics logic in `FixedUpdate` adds unnecessary simulation steps.
- Use `Destroy(go, delay)` instead of a delay coroutine — built-in, no coroutine, no allocation.
- Use `Span<T>` and `stackalloc` for small temporary buffers **[Unity 2021+]** to avoid heap allocation entirely:

```csharp
Span<int> ids = stackalloc int[64];
FillIds(ids);
ProcessIds(ids);
```
[Unity GC spikes — Embrace.io](https://embrace.io/blog/garbage-collector-spikes-unity/)

- Enable **Incremental GC** in Player Settings (Unity 2019.1+) as a safety net, but do not treat it as an excuse for allocation-heavy code.
- Use `Physics.autoSyncTransforms = false` in physics-heavy scenes and sync manually before queries:

```csharp
Physics.autoSyncTransforms = false;
// ... move objects ...
Physics.SyncTransforms();
var hit = Physics.Raycast(origin, dir, out RaycastHit info);
```
[TheGameDev.Guru physics autoSyncTransforms](https://thegamedev.guru/unity-cpu-performance/physics-autosynctransforms/)

**Lesser-known tricks:**
- `Application.targetFrameRate` is **ignored when VSync is enabled**. Disable VSync first if you want to cap differently.
- `Time.captureFramerate = 60` forces `Time.deltaTime` to always return `1f / 60`, enabling screenshot-based cinematics at consistent timings regardless of real elapsed time.
- `HideFlags.HideInHierarchy | HideFlags.DontSave` hides manager GameObjects from designers and prevents them being included in scene serialization.
- `[ExecuteAlways]` runs in both editor and built players; `[ExecuteInEditMode]` is legacy editor-only. Prefer `OnValidate` for inspector-change responses — `[ExecuteAlways]` running `Update()` continuously in edit mode wastes editor performance.
- `List<T>.ForEach` with a capturing lambda allocates per call. A plain `for` loop with index is always allocation-free.
- `StopCoroutine` should target a stored `Coroutine` reference, not `StopAllCoroutines()` — the latter stops coroutines started by other systems on the same object.
- Using `#if DEVELOPMENT_BUILD` to strip debug logging and profiling overhead adds zero cost to release builds. Use `Scripting Define Symbols` for project-specific compile-time gates.

**Tools and profiling for this role:**
- CPU Profiler Hierarchy → sort by **GC Alloc** to find allocators. Magenta bars in Timeline = GC.Alloc.
- Enable **Allocation Call Stacks** in the Profiler toolbar to trace each GC.Alloc to its source line.
- Deep Profile a 2–5 second capture targeting the suspect system — not the whole session.
- `ProfilerMarker` on every major system boundary: AI, Pathfinding, Combat, Spawning.
- Memory Profiler package → Objects and Allocations → filter to "Managed" for heap analysis.

**Cheat sheet:**

| Pattern | Allocation? | Fix |
|---|---|---|
| `Camera.main` in Update | Native crossing | Cache in `Start()` |
| `GetComponent<T>()` in Update | Scene traversal | Cache in `Awake()` |
| `new WaitForSeconds(t)` in coroutine loop | Yes | `private static readonly WaitForSeconds` |
| `gameObject.tag == "x"` | String allocation | `CompareTag("x")` |
| `foreach (var x in iEnumerable)` | Boxing | `foreach` over concrete `List<T>` |
| LINQ in Update | Enumerator + collections | Manual `for` loop |
| Lambda capturing locals in hot path | Closure object | Static method + explicit params |
| `Instantiate/Destroy` in tick | GC + CPU spike | `ObjectPool<T>` |

---

### Burst, Jobs, and DOTS Programmers

This section is for developers choosing to adopt Unity's data-oriented stack. ECS is not required for most indie games — it earns its complexity at thousands of entities sharing similar archetypes.

**Common pitfalls:**
- **[2020-2022 LTS]** Applying ECS to small entity counts where cache benefits don't materialize. The archetype/chunk overhead breaks even at roughly 500–1000 entities of the same type.
- **[2020-2022 LTS]** Using `SystemBase` instead of `ISystem` for performance-critical systems — `SystemBase` is a managed class, not Burst-compilable on system methods.
- **[2020-2022 LTS]** `Entities.ForEach` — deprecated in Entities 1.0. Migrate to `SystemAPI.Query<T>()` (main thread) or `IJobEntity` (parallel). [Entities 1.0 SystemAPI.Query](https://docs.unity3d.com/Packages/com.unity.entities@1.0/manual/systems-systemapi-query.html)
- **[2020-2022 LTS]** Calling `Complete()` on a `JobHandle` immediately after scheduling — defeats the purpose of the Job System. Schedule early, complete as late as possible each frame.
- **[2020-2022 LTS]** `NativeList` growth during parallel execution. Pre-size with an upper bound; use `AsParallelWriter()` pattern.
- **[2020-2022 LTS]** Forgetting to `Dispose()` `NativeArray<T>` and other NativeContainers. In Editor, Unity throws exceptions. In release builds, leaks are silent.
- **[2020-2022 LTS]** Using `UnityEngine` math types (`Vector3`, `Quaternion`) in Burst jobs instead of `Unity.Mathematics` equivalents — may miss SIMD optimization opportunities.

**Recommended practices:**
- Mark all job structs `[BurstCompile]`. For maximum SIMD utilization, add `FloatMode.Fast` where determinism is not required:

```csharp
[BurstCompile(FloatPrecision.Standard, FloatMode.Fast)]
public struct VelocityJob : IJobParallelFor
{
    public NativeArray<float3> Positions;
    [ReadOnly] public NativeArray<float3> Velocities;
    public float DeltaTime;

    public void Execute(int i)
    {
        Positions[i] += Velocities[i] * DeltaTime;
    }
}
```

- Choose allocator correctly: `Allocator.Temp` (fastest, single frame, cannot pass to job fields), `Allocator.TempJob` (fast, ≤4 frames, must Dispose), `Allocator.Persistent` (unlimited, must Dispose manually — leaks are silent). [NativeContainer allocators guide](https://outscal.com/blog/how-to-choose-and-manage-collections-for-performance-in-unity)
- Chain `JobHandle` dependencies explicitly. `JobHandle.CombineDependencies` merges multiple handles. The Dependency property on `ISystem` (`state.Dependency`) automatically chains system dependencies in ECS.
- Prefer `ISystem` over `SystemBase` for all performance-critical ECS systems:

```csharp
[BurstCompile]
public partial struct MovementSystem : ISystem
{
    [BurstCompile]
    public void OnUpdate(ref SystemState state)
    {
        float dt = SystemAPI.Time.DeltaTime;
        foreach (var (transform, velocity) in
            SystemAPI.Query<RefRW<LocalTransform>, RefRO<Velocity>>())
        {
            transform.ValueRW.Position += velocity.ValueRO.Value * dt;
        }
    }
}
```
[Chunk iteration in Entities 1.0](https://coffeebraingames.wordpress.com/2023/06/25/chunk-iteration-in-entities-1-0/)

- Prefer `IJobEntity` over `IJobChunk` for per-entity work — it is higher-level and generates the same Burst-compiled code. [Unity Job System and Burst guide](https://heerozh.com/en/blog/2024-12-09_unity-job/)
- Mark input data `[ReadOnly]` in jobs — enables parallel reads without race condition checks and gives Burst additional optimization opportunities.
- Use `Unity.Mathematics` types (`float3`, `float4`, `quaternion`) for full SIMD vectorization. `UnityEngine.Vector3` can be used in Burst jobs but may miss opportunities. [Burst docs](https://docs.unity3d.com/Packages/com.unity.burst@1.8/manual/index.html)
- Wrap any debug logging needed in Burst jobs with `[BurstDiscard]`:

```csharp
[BurstDiscard]
static void DebugLog(string msg) => Debug.Log(msg);
```

- For Subscene baking, ensure bakers are stateless — never cache values on the baker instance; incremental baking calls bakers on re-run. [Entities 1.0 baker overview](https://docs.unity3d.com/Packages/com.unity.entities@1.0/manual/baking-baker-overview.html)
- Use Entities Graphics (`com.unity.entities.graphics`) for rendering ECS entities via BRG. Requires URP or HDRP with Forward+ path. [Entities Graphics docs](https://docs.unity3d.com/Packages/com.unity.entities.graphics@1.3/manual/index.html)

**Lesser-known tricks:**
- **Burst Inspector** (`Jobs → Burst Inspector`) shows generated assembly for any compiled job. Look for SIMD register usage (`ymm`, `xmm` on x86) to confirm auto-vectorization. Absence of SIMD indicates a struct alignment or managed-type dependency is blocking it.
- Burst 1.6+ supports `[BurstCompile]` on **static methods** for direct calls without job overhead — useful for math utility functions called from managed code.
- `NativeArray.Dispose(jobHandle)` ties disposal to a JobHandle completing — safer than separate Dispose calls. Prevents "collection still in use" bugs.
- `[NativeDisableParallelForRestriction]` overrides safety checks for intentionally distinct-index parallel writes. Incorrect use = silent data races in release builds.
- DOTS Physics and Havok Physics share the same data protocol — you can switch between them without rewriting content. [ECS Physics — Havok vs Unity Physics](https://learn.unity.com/tutorial/ecs-physics-havok-physics-for-unity-and-unity-physics)
- The Job System's `innerloopBatchCount` parameter in `IJobParallelFor.Schedule(count, batchCount, deps)` controls granularity. Values of 32–128 are typical; too small increases scheduling overhead, too large reduces CPU core utilization.

**Tools and profiling for this role:**
- CPU Profiler Timeline → Worker threads — are all cores utilized during job execution? Idle workers indicate scheduling bottlenecks.
- Burst Inspector for SIMD verification.
- DOTS Entities Hierarchy window (Window → Entities → Hierarchy) for entity count and archetype inspection.
- Profiler → Physics module for Unity Physics cost.

**Cheat sheet:**

| Allocator | Speed | Max lifetime |
|---|---|---|
| `Temp` | Fastest | 1 frame; cannot pass to job fields |
| `TempJob` | Fast | ≤4 frames; must Dispose() |
| `Persistent` | Slow | Unlimited; leaks silently in release |

---

### Level Design / Environment

Level designers directly control the largest contributors to both CPU and GPU frame time through scene structure and asset density.

**Common pitfalls:**
- **[All versions]** Occlusion Culling baked on open terrain or large open-world scenes — bake time is prohibitive, data is large, and the open-sky visibility defeats the purpose. Only effective in closed environments.
- **[All versions]** Missing or improperly configured LOD Groups on hero assets — a character visible at 500 m still rendering at LOD0 polygon count.
- **[All versions]** Camera far plane set too large for the scene type — a corridor game with a far plane of 1000 m wastes GPU on frustum culling and shadow calculations for geometry the player will never see.
- **[2020-2022 LTS]** Manual Light Probe Group placement leaving large unlit gaps — dynamic objects flicker between probes or go dark.
- **[Unity 6+]** Not enabling GPU Resident Drawer on scenes with hundreds of repeated mesh-material pairs.
- **[All versions]** ProBuilder meshes used directly in production without conversion to static mesh assets — no automatic LOD, poor occlusion culling cell generation on large flat faces.
- **[All versions]** Terrain with more than 4 texture splat layers per visible tile — each group of 4 layers adds a draw pass.

**Recommended practices:**
- Configure LOD Groups with screen-space percentage thresholds calibrated for your typical play distance. Recommended starting values:
  - LOD0: ≥ ~30% screen height (close range)
  - LOD1: 50% polycount reduction
  - LOD2: 80% polycount reduction
  - Culled: < ~1% screen height
  `QualitySettings.lodBias` at 0.7–0.85 often hits the best quality-performance balance on PC. [Unity LOD Group docs](https://docs.unity3d.com/Manual/class-LODGroup.html)
- Enable `Fade Mode` on LOD Groups for visual cross-fading — hides LOD pop-in without performance cost.
- Bake Occlusion Culling only for enclosed environments. Use **Occlusion Areas** to define cells and **Occlusion Portals** for openings (doors, archways). [Unity Occlusion Culling docs](https://docs.unity3d.com/6000.4/Documentation/Manual/OcclusionCulling.html)
- **[Unity 6+]** Use GPU-based occlusion culling (URP/HDRP, depth-buffer reprojection, no baking) for scenes using GPU Resident Drawer. [Unity Manual – GPU Occlusion Culling](https://docs.unity3d.com/6000.0/Documentation/Manual/urp/gpu-culling.html)
- Use Addressables-based additive scene loading for world streaming: `Addressables.LoadSceneAsync` / `Addressables.UnloadSceneAsync`. Avoid `Resources.Load` — synchronous and not memory-managed.
- Enable **Draw Instanced** on Terrain components (`terrain.drawInstanced = true`) **[Unity 2021+]** — batches terrain chunks into fewer draw calls.
- Keep Terrain splat layers ≤ 4 per visible tile. Each additional group of 4 layers adds a draw pass. For complex biomes, consider separate Terrain tiles rather than one tile with 8 layers.
- Set Camera near/far planes to the minimum required for your scene type. Shadow Distance (Quality Settings) is separate from the camera far plane and is usually the larger contributor to GPU shadow cost.
- **[Unity 6+]** Prefer Adaptive Probe Volumes (APV) over manual Light Probe Groups for complex scenes. APV placement is automatic and sampling is per-pixel rather than per-object. Enable: Quality Settings → Render Pipeline Asset → Light Probe System → Adaptive Probe Volumes. [Unity APV usage guide](https://docs.unity3d.com/6000.3/Documentation/Manual/urp/probevolumes-use.html)
- **[All versions]** Place Reflection Probes at eye level in distinct reflective zones. Use cubemap resolution 128–256 for most probes; reserve 512 for hero materials. Enable **Box Projection** for interior environments to avoid "infinitely far away" reflections.

**Lesser-known tricks:**
- APV light leakage through thin walls is common. Mitigate with Adjustment Volumes (separate indoor/outdoor zones), thicker geometry in problem areas, or manual probe override volumes. [APV vs Light Probes — Reddit](https://www.reddit.com/r/Unity3D/comments/1h9s4el/apv_vs_light_probes/)
- `StaticBatchingUtility.Combine` can be called at runtime on non-Static objects to force a combined mesh batch — useful for dynamically instantiated sets of props that won't move.
- Billboard trees have `Billboard Start` distance that controls when 3D trees switch to impostors. Push this distance as close to the camera as visually acceptable — 3D trees at 200 m contribute significant triangle and shadow cost.
- Occlusion Portal components model door openings dynamically. A closed door toggles occlusion on/off — useful for dungeon games with many connecting corridors.
- **[Unity 6+]** APV supports **Light Blending Scenarios** — bake multiple lighting states (day, night, indoor/outdoor) and blend between them at runtime without re-baking.
- ProBuilder meshes for whitebox: subdivide large flat faces before baking Occlusion Culling. Very large single faces prevent proper PVS cell generation. [Occlusion Culling with ProBuilder — Reddit](https://www.reddit.com/r/Unity3D/comments/1gs7jnv/occlusion_culling_with_probuilder/)

**Tools and profiling for this role:**
- Rendering Profiler module → visible renderers, shadow casters, triangles per frame.
- GPU Profiler → Shadows (excessive shadow distance), Geometry (missing LODs).
- Frame Debugger → inspect batching and LOD transitions.
- Rendering Debugger (URP/HDRP: Window → Analysis → Rendering Debugger) → Lighting → Shadow Cascades view for cascade boundary visualization.

**Cheat sheet:**

| Setting | Default | Recommended for PC |
|---|---|---|
| `QualitySettings.lodBias` | 1.0 | 0.7–0.85 for performance |
| `QualitySettings.shadowDistance` | 150 | 80–120 for most PC games |
| Terrain `drawInstanced` | false | Enable (Unity 2021+) |
| Reflection Probe resolution | 128 | 128–256 standard, 512 hero |
| Cascade count (URP) | 4 | 2–3 for mid-range targets |

---

### Materials / Shader Authors

Shader authors have disproportionate control over GPU performance and the SRP Batcher. The decisions made here affect every frame.

**Common pitfalls:**
- **[2020-2022 LTS]** `MaterialPropertyBlock` breaking SRP Batcher compatibility — any renderer using MPB falls back to GPU Instancing (if shader supports it) or unoptimized draw calls. [SRP Batcher deep dive — fazz.dev](https://fazz.dev/articles/building-srp-part-three)
- **[All versions]** Shader keyword variant explosion. 10 feature flags = 1,024 variants. `#pragma multi_compile` never strips unused variants automatically.
- **[Pre-2020]** Using `multi_compile` where `shader_feature` would suffice — `shader_feature` strips variants not used by any material in the build.
- **[All versions]** Global keywords instead of local keywords — global keyword space is limited (~196 available after Unity's own usage in 2020+).
- **[All versions]** Sampler limit: max 16 samplers per HLSL shader stage. Hitting this limit causes silent fallback behavior.
- **[Pre-2020]** Surface Shaders — not supported in URP or HDRP at all. Legacy Built-in RP only.
- **[2020-2022 LTS]** Custom Function Node in Shader Graph with non-deterministic output breaking SRP Batcher.

**Recommended practices:**
- For SRP Batcher compatibility, all per-material properties must be declared in a single `UnityPerMaterial` CBUFFER:

```hlsl
CBUFFER_START(UnityPerMaterial)
    float4 _BaseColor;
    float  _Smoothness;
    float  _Metallic;
CBUFFER_END
```
[SRP Batcher shader requirements](https://docs.unity3d.com/6000.3/Documentation/Manual/urp/shaders-in-universalrp-srp-batcher.html)

- Use `shader_feature_local` (not `multi_compile`) for features toggled via materials at bake time — Unity strips unused combinations:

```hlsl
#pragma shader_feature_local _EMISSION
#pragma shader_feature_local _NORMALMAP
```
[Unity shader stripping docs](https://docs.unity3d.com/2021.3/Documentation/Manual/shader-variant-stripping.html)

- Use `multi_compile_local` only for keywords enabled at runtime via `Shader.EnableKeyword`. Always local, never global.
- Restrict keyword declarations to specific shader stages to reduce variant count:

```hlsl
#pragma shader_feature_fragment_local FEATURE_A FEATURE_B
```

- Implement `IPreprocessShaders.OnProcessShader` in an Editor script for surgical variant stripping at build time. Use whitelist/blacklist workflow. [TheGameDev.Guru variant stripping](https://www.youtube.com/watch?v=WYp84rEyMWs)
- Use **Shader Variant Collection** + `ShaderVariantCollection.WarmUp()` to pre-compile critical variants before gameplay begins. Unity 6 adds a **Shader Pipeline Library** (analogous to Vulkan pipeline cache) to persist compiled shaders across sessions.
- For per-instance variation without breaking SRP Batcher: create a unique material per variant (cheap with SRP Batcher since same-shader materials batch together) OR encode variation as a per-instance buffer via BRG in Unity 6+. Reserve `MaterialPropertyBlock` for specific cases where GPU Instancing is the intended path.
- Handle the 16-sampler limit with shared sampler states:

```hlsl
TEXTURE2D(_AlbedoTex);
TEXTURE2D(_NormalTex);
SAMPLER(sampler_linear_repeat); // shared — counts as one sampler
```

- Use **Texture2DArray** to pack N textures of the same dimensions/format into one GPU resource and one sampler binding. Access via `float3(uv.x, uv.y, arrayIndex)`. [Unity BCn texture compression](https://www.reedbeta.com/blog/understanding-bcn-texture-compression-formats/)
- For GPU Instancing pragmas when using `DrawMesh*` APIs, add to the shader: `#pragma instancing_options assumeuniformscaling nolightmap nolodfade nolightprobe`.
- In Shader Graph, wrap Custom Function Nodes in Sub Graphs for reuse — Custom Function Nodes themselves cannot be reused directly. [Custom Function Node docs](https://docs.unity3d.com/Packages/com.unity.shadergraph@17.0/manual/Custom-Function-Node.html)

**Lesser-known tricks:**
- Right-click any Shader Graph asset → **See Generated Code** to inspect the HLSL output and count variant macros.
- `ShaderLab` vs Shader Graph choice: Shader Graph auto-generates SRP Batcher–compatible CBUFFERs and handles render pass tags — it is safer for material artists. Hand-written HLSL is still needed for custom render passes, fullscreen effects, and procedural geometry.
- Verify SRP Batcher batching in Frame Debugger: expand the SRP Batcher node. "Batch reason: different material" means materials differ; "different shader" means base shaders differ — the latter cannot batch even with the same material. SRP Batcher batches objects sharing the same shader.
- Normal maps should always use BC5 format on desktop targets — it independently compresses X and Y channels, superior quality vs BC1/DXT1, Z reconstructed in shader as `sqrt(1 - x² - y²)`. [BCn analysis — Nathan Reed](https://www.reedbeta.com/blog/understanding-bcn-texture-compression-formats/)

**Tools and profiling for this role:**
- Frame Debugger → SRP Batcher section: batch sizes and break reasons.
- `log shader compilation` in Player Settings to count variants at build time.
- Burst Inspector does not apply here, but NVIDIA Nsight Graphics for shader occupancy and warp utilization.
- Rendering Debugger → Material Validation for overdraw and SRP Batcher compatibility.

**Cheat sheet:**

| Feature | Use `shader_feature` | Use `multi_compile` |
|---|---|---|
| Toggled per-material at bake time | Yes | No |
| Enabled at runtime via script | No | Yes |
| Auto-stripped if no material uses it | Yes | No |

| Keyword scope | Max count | Default |
|---|---|---|
| Global (avoid) | ~196 available | Was default Pre-2021 |
| Local (`_local`) | 64 per shader | Use always |

---

### Meshes / 3D Art

Mesh import decisions have permanent memory and rendering consequences. Most are set once and forgotten — which is how mistakes persist for years.

**Common pitfalls:**
- **[All versions]** **Read/Write Enabled** left on imported meshes — keeps a CPU-side copy in system RAM, doubling mesh memory. Only needed when accessing `Mesh.vertices` or performing runtime mesh modification from C#.
- **[All versions]** Read/Write Enabled on textures — same issue: doubles VRAM+RAM. [Unity texture import docs](https://docs.unity3d.com/2021.3/Documentation/Manual/class-TextureImporterOverride.html)
- **[All versions]** 32-bit index buffers on meshes under 65,535 vertices — wastes memory and bandwidth. Default to 16-bit unless the mesh genuinely needs it. [Mesh.indexFormat docs](https://docs.unity3d.com/6000.3/Documentation/ScriptReference/Mesh-indexFormat.html)
- **[All versions]** Missing **Compress Mesh** — uncompressed vertex data (position, normals, UVs) wastes memory. Minor precision loss is rarely visible.
- **[All versions]** No LOD Group on hero assets — a distant character at LOD0 polygon count is a consistent GPU cost.
- **[2020-2022 LTS]** Static Batching enabled alongside GPU Resident Drawer — they conflict; disable Static Batching when using GRD.

**Recommended practices:**
- Disable **Read/Write Enabled** on all mesh import settings by default. Enable only for meshes accessed via C# at runtime.
- Enable **Compress Mesh** in import settings. Quantizes vertex positions and normals to 16-bit. Rarely visible in game.
- Set **Index Buffer Format** to 16-bit for meshes under 65K vertices. Use 32-bit only when genuinely needed.
- Configure LOD Groups with LOD0 (full detail), LOD1 (50% reduction), LOD2 (80% reduction), Culled (< 1% screen height). Enable **Fade Mode** for smooth transitions.
- **[Unity 6.2+]** Enable **Mesh LOD** in import settings for automatic LOD generation. Unity stores all LOD levels in the original mesh index buffer sharing the same vertex buffer, significantly reducing memory overhead vs separate LOD meshes. [Unity 6 Mesh LOD](https://www.youtube.com/watch?v=A0b2MfHCCfU)
- Use `Mesh.MarkDynamic()` for procedural/runtime-updated meshes — hints the GPU driver to use faster buffer update paths:

```csharp
mesh.MarkDynamic(); // call once after creation, before per-frame vertex writes
```

- Use `StaticBatchingUtility.Combine` to manually force-combine a set of runtime-instantiated static props that won't move.
- For GPU Skinning: enable in **Player Settings → Other Settings → GPU Skinning**. Offloads skinned mesh deformation to a Compute Shader pass. Unity 6 introduced **Batched GPU Skinning** — reduces the number of separate Compute dispatches for groups of identically-configured skinned meshes. [DOUBLE Unity Animation Performance](https://www.youtube.com/watch?v=apD2NgXulxE)
- Reduce blend weights in `Quality.blendWeights` (1, 2, or 4 bones per vertex). Four bones is the humanoid default; two is usually indistinguishable at LOD1 and beyond.
- Strip scale curves in animation clips at import if the character never scales — scale curves are more expensive than translation and rotation curves.

**Lesser-known tricks:**
- `CombineMeshes` in C# does not interact with the Unity batching system — you manage the combined mesh as a runtime asset. Best for static environmental detail meshes that will never move and share one material.
- Meshes generated with vertex colors for GPU Instancing per-instance tinting avoid creating separate materials per color variant, keeping SRP Batcher batches intact — but only if the shader uses the vertex color as the instanced parameter.
- **Optimize Game Objects** in rig import settings collapses the bone hierarchy, removing individual GameObjects per bone. Saves transform update overhead in crowds. Disable if scripts need direct access to bone transforms.
- Compute shaders always load indices as 32 bits — if using 16-bit indices in a compute buffer, unpack accordingly. This is a non-obvious mismatch that can corrupt compute shader output.

**Tools and profiling for this role:**
- Rendering Profiler module → triangles/vertices per frame.
- Memory Profiler → Objects by type → Mesh category.
- Frame Debugger → identify which meshes are generating unexpected draw calls.
- GPU module → Geometry section for vertex processing cost.

**Cheat sheet:**

| Import Setting | Default | Recommended |
|---|---|---|
| Read/Write Enabled | Off | Keep off; enable only when needed |
| Compress Mesh | On | On |
| Index Format | 16-bit | 16-bit; 32-bit only for >65K verts |
| GPU Skinning | On | On |
| Optimize Game Objects | Off | On for crowds |

---

### Lights & Shadows

Lighting is consistently the second-largest GPU cost in Unity projects after geometry, and shadow map rendering is frequently the largest single render pass.

**Common pitfalls:**
- **[All versions]** Shadow distance set too wide — `QualitySettings.shadowDistance` of 150 m in a corridor game casts shadows for geometry the player will never see.
- **[All versions]** Too many shadow-casting real-time lights — each additional shadow-casting light adds a full shadow map render pass.
- **[All versions]** Realtime Reflection Probes updating every frame — use `OnDemand` refresh unless reflections are dynamic.
- **[Pre-2020]** Enlighten Realtime GI still enabled — deprecated in 2019, removed from HDRP in 2020.1. [Enlighten deprecation docs](https://docs.unity3d.com/2020.1/Documentation/Manual/realtime-gi-using-enlighten.html)
- **[2020-2022 LTS]** Manual Light Probe Groups leaving dark seams on dynamic objects transitioning between probe groups.
- **[Unity 6+]** APV light leakage through thin walls — mitigation required for interiors.

**Recommended practices:**
- Use **Shadowmask** Mixed Lighting mode for PC desktop games — the best balance between quality and runtime performance. Near-camera: real-time shadows. Far: baked shadowmask texture. Up to 4 lights share a shadowmask (one per RGBA channel). [Unity Mixed lighting docs](https://docs.unity3d.com/2019.2/Documentation/Manual/LightMode-Mixed.html)

| Mixed Light Mode | Shadows | Cost | Best for |
|---|---|---|---|
| Baked Indirect | Real-time shadow map | Medium | High quality, stable lighting |
| Shadowmask | Near real-time, far baked | Medium-high | Best quality/perf balance |
| Subtractive | Fully baked, 1 directional | Low | Stylised games, lowest cost |

- Configure **shadow cascades** in the URP Asset → Shadows section. 2–3 cascades for mid-range PC targets; 4 for high-end. Visualize boundaries with Rendering Debugger → Lighting → Shadow Cascades. Higher cascade count improves quality at cost of additional render passes. [Shadow cascades Unity 6](https://docs.unity3d.com/6000.3/Documentation/Manual/shadow-cascades-use.html)
- Use **PCF (Percentage Closer Filtering)** for soft shadows in URP. The URP Screen Space Shadows Renderer Feature moves shadow resolve to screen space before the opaque pass — reduces aliasing at lower cascade counts.
- **[Unity 6+]** Enable **Adaptive Probe Volumes (APV)** instead of manual Light Probe Groups:
  - Probe placement: automatic (geometry density)
  - Sampling: per-pixel (eliminates seams at object boundaries)
  - Memory streaming: yes (open worlds)
  - Enable: Quality Settings → Render Pipeline Asset → Light Probe System → APV [APV concept docs](https://docs.unity3d.com/6000.2/Documentation/Manual/urp/probevolumes-concept.html)
- **[All versions]** Place Reflection Probes at eye level in distinct reflective zones. 128–256 resolution for most; 512 for hero materials. Enable Box Projection for interiors.
- Use **Rendering Layers** (URP 2021+, HDRP 2019.3+) to restrict which lights affect which renderers — reduces per-object lighting cost in scenes with many lights:

```csharp
// Assign layers in URP Asset, per-light and per-renderer Rendering Layer Mask
renderer.renderingLayerMask = LayerMask.GetMask("CharacterLayer");
```
[URP Rendering Layers docs](https://docs.unity3d.com/Packages/com.unity.render-pipelines.universal@14.0/manual/features/rendering-layers.html)

- For baking: **Unity Progressive GPU Lightmapper** for fast iteration; **Bakery** (paid) for higher quality, faster bake times, and IES light support. Community consensus in 2025: Bakery still produces better results and bakes significantly faster. [Is Bakery still better in Unity 6.2?](https://www.reddit.com/r/Unity3D/comments/1n1l632/is_bakery_still_better_than_unity_for_lightmap/)

**Lesser-known tricks:**
- SSAO in URP runs as a Renderer Feature before opaque objects are shaded. Disabling it for Low quality tier is a high-leverage GPU save.
- Disable `#pragma enable_d3d11_debug_symbols` in production builds — even as a comment it can affect shader compilation in some configurations.
- HDRP Volumetric Fog cost scales with froxel grid resolution. `Depth Extent` reduces frustum slice count; `Fog Control Mode → Balance` adjusts quality/perf on a 0–1 slider; `Directional Lights Only` halves cost for most scenes. [HDRP Fog docs](https://docs.unity3d.com/Packages/com.unity.render-pipelines.high-definition@12.0/manual/Override-Fog.html)
- APV supports **Light Blending Scenarios** — pre-bake multiple lighting states (day/night, indoor/outdoor) and blend between them at runtime without re-baking.
- In **[Pre-2020]** projects, Enlighten Realtime GI was the only dynamic indirect solution. For Unity 6+, APV is the answer for baked scenarios; HDRP Screen Space GI covers fully dynamic.

**Tools and profiling for this role:**
- GPU Profiler → Shadows, Lighting sections.
- Rendering Debugger → Shadow Cascades view, Light Overlays.
- Frame Debugger → shadow map render passes (how many passes for how many shadow-casting lights?).
- RenderDoc for shadow atlas inspection.

**Cheat sheet:**

| Setting | Performance impact | Recommendation |
|---|---|---|
| Shadow Distance | High | 80–120 m for most PC games |
| Cascade Count | Medium | 2–3 for mid-range, 4 for high-end |
| Reflection Probe Update | High (Realtime) | Use Baked or OnDemand |
| SSAO sample count | Medium | Reduce for Low quality tier |
| Mixed Lighting Mode | Medium | Shadowmask for PC |

---

### VFX (Particle System and VFX Graph)

Visual effects are one of the most asymmetric performance areas in Unity: they can look identical at 1% of the GPU cost, or destroy frame rate with the wrong configuration.

**The two systems:**

| Feature | Particle System (Shuriken) | VFX Graph |
|---|---|---|
| Execution | CPU | GPU (Compute Shader) |
| Platform requirement | All | Compute Shader support required |
| Particle ceiling | Thousands | Millions |
| Physics integration | Full Unity physics | Depth-buffer + custom |
| Render pipeline | Built-in, URP, HDRP | URP, HDRP (no Built-in) |
| Recommended for | Small-scale, physics-heavy | Large-scale, GPU-rich targets |

[Unity Manual – Choosing your particle system solution](https://docs.unity3d.com/6000.4/Documentation/Manual/ChoosingYourParticleSystem.html)

**Common pitfalls:**
- **[All versions]** VFX Graph bounds set to **Automatic** — forces `Culling Flag: Always recompute bounds and simulate`, disabling culling entirely. [Unity Manual – Visual Effect Bounds](https://docs.unity3d.com/Packages/com.unity.visualeffectgraph@17.6/manual/visual-effect-bounds.html)
- **[All versions]** Particle System Collision module enabled — world collision requires physics queries every frame per particle. By far the most expensive Particle System module.
- **[All versions]** Sub-emitters chained 3+ deep on dense burst systems — each sub-emitter is a separate CPU-evaluated system.
- **[All versions]** Light module enabled — each particle that spawns a light adds a real-time light to the scene. Limit to ≤ 4 simultaneous.
- **[All versions]** Trail module on dense systems — trail geometry rebuilds every frame; keep trail counts below a few hundred per system.
- **[All versions]** Large VFX Graph with `Automatic` bounds on many simultaneous instances — each instance simulates even when completely off-screen.

**Recommended practices:**
- Set VFX Graph bounds to **Manual** for final builds:

```
Initialize Context → AABox attribute
- Width: {max effect width}
- Height: {max effect height}
- Depth: {max effect depth}
```

Use **Recorded** bounds during development (VFX Control panel → Bounds Recording → Apply Bounds), then convert to Manual. Use `Bounds Padding` on the Initialize Context to add per-axis slack for output-stage scaling (stretched quads extend beyond simulation bounds).

- Prefer **Plane-mode collision** in Particle System over World collision. For visual-only effects, switch to VFX Graph depth-buffer collision.
- Cap the Particle System Light module to a **Max Light Count** in the module settings — prevents spikes during dense burst moments.
- Use VFX Graph's **C# Event API** and **Property Bindings** for game logic integration at near-zero allocation cost:

```csharp
var vfxComp = GetComponent<VisualEffect>();
vfxComp.SetFloat("SpeedScale", currentSpeed);

// Event with attribute payload
var attr = vfxComp.CreateVFXEventAttribute();
attr.SetVector3("HitNormal", hit.normal);
vfxComp.SendEvent("OnHit", attr);
```

- For Particle System light probe sampling per-particle: use *Blend Probes* mode in the Renderer module and ensure Light Probe Group density is adequate in the VFX area. Light probes sample at system origin by default, not per-particle.
- Output Mesh (VFX Graph): use when particle overdraw is the bottleneck — mesh output provides real depth, reducing fill-rate at the cost of vertex count scaling linearly with particle count. Profile fill-rate savings vs vertex cost.
- Output Quad default: add `Soft Particle` blend to reduce hard depth-intersection edges without extra geometry.

**Lesser-known tricks:**
- VFX Graph has a `Capacity` setting that sets the maximum particle count. Setting this too high wastes GPU memory even if particles never reach that count. Keep it the minimum required for the effect.
- VFX Graph `Culling Flags` control the simulation mode: `Recompute bounds and simulate` (always), `Only simulate when visible`, `Stop simulating when invisible`. Set to the latter for ambient effects that should not tick off-screen.
- Particle System's **Prewarm** option simulates the system forward in time on enable — avoids the "cold start" visual artifact but costs one expensive update frame at initialization. For pooled systems, `Stop()` and re-`Play()` without prewarm on reuse.
- VFX Graph **GPU events** (from Update Context to Spawn Context) can trigger child particle spawns entirely on the GPU, eliminating CPU round-trips for complex multi-stage effects.

**Tools and profiling for this role:**
- Particle Profiler section in the CPU Profiler module.
- Profiler → GPU module → Geometry section for VFX Graph vertex cost.
- Frame Debugger for overdraw analysis on transparent particle quads.
- VFX Control panel in the Editor for bounds recording and particle count visualization.

**Cheat sheet:**

| Module / Setting | Cost | Recommendation |
|---|---|---|
| Collision (World) | Very High | Avoid; use Plane mode or VFX Graph depth collision |
| Sub-emitters (3+ deep) | High | Profile; flatten chains |
| Light module | High | Cap Max Light Count |
| Trails | Medium | Cap count; strip width at distance |
| VFX Bounds: Automatic | Disables culling | Use Manual for final builds |
| VFX Capacity | GPU memory | Set to minimum required |

---

### Audio

Audio is rarely the primary frame-rate bottleneck but frequently contributes to memory bloat, unexpected CPU spikes, and subtle frame-time inconsistencies.

**Common pitfalls:**
- **[All versions]** Long music files set to **Decompress on Load** — decompresses the entire file to PCM on load, consuming massive RAM for no runtime benefit. Music must use **Streaming**.
- **[All versions]** Stereo clips on 3D spatialised sources — stereo information is discarded by spatialisation anyway. Enable **Force to Mono** on all 3D audio sources.
- **[All versions]** Voice limit not configured — Unity's default is 32 concurrent voices. Voices beyond the limit are stolen by priority. Voices playing silently still count against the limit.
- **[All versions]** AudioSource components not disabled when sources are beyond audible range — silent voices still consume voice budget.
- **[All versions]** Heavy DSP effects (convolution reverb, FFT-based effects) on many Mixer groups — DSP CPU cost scales with active effect count.

**Recommended practices:**
- Apply the correct load type per clip category: [Unity Manual – AudioClip](https://docs.unity3d.com/6000.4/Documentation/Manual/class-AudioClip.html)

| Load Type | Memory | CPU cost | Best for |
|---|---|---|---|
| Decompress on Load | High (raw PCM) | Minimal | Short one-shots, UI sounds |
| Compressed in Memory | Low | ~0.5% per Vorbis voice | Medium-length SFX, foley |
| Streaming | Minimal (~200 KB) | Separate thread | Music, long ambient loops |

- Apply correct compression format per clip:

| Format | Compression | CPU cost | Best for |
|---|---|---|---|
| PCM | 1:1 (uncompressed) | Negligible | Shortest effects, UI |
| ADPCM | ~3.5× | Very low | High-frequency noisy sounds (footsteps, impacts) |
| Vorbis/MP3 | ~5–50× | Medium | Music, dialogue, longer SFX |

[Game Developer – Unity Audio Import Optimisation](https://www.gamedeveloper.com/audio/unity-audio-import-optimisation---getting-more-bam-for-your-ram)

- Enable **Force to Mono** aggressively on all 3D audio sources. Re-check normalization after applying — stereo→mono conversion can reduce perceived loudness.
- Reduce sample rate from 44.1 kHz to 22.05 kHz for most SFX — halves raw data size with negligible audible impact.
- Set `AudioSource.priority` explicitly: 0 = highest, 256 = lowest. Dialogue: 0–64. Ambient loops: 200+.
- Disable `AudioSource` components when beyond audible range — do not rely on volume falloff alone.
- Use `AudioMixer` for group routing, DSP effects, and snapshot transitions. Monitor DSP CPU cost in the Audio Profiler module. Side-chain compression (duck music under dialogue): `Send` effect on source group + `Receive + Duck Volume` on destination.
- For 3D spatial audio: `AudioSource.spatialBlend = 1` for fully positional. Use `Logarithmic` rolloff for physics-accurate attenuation; `Linear` for predictable gameplay audio. Set `minDistance` and `maxDistance` per source — a guard post sound with `maxDistance = 20` never interferes with sources 200 m away.
- Pool `AudioSource` components — return to pool when `AudioSource.isPlaying == false`.

**Lesser-known tricks:**
- **Steam Audio** provides physics-based occlusion (raycast from listener to source), early reflections, and reverb. Integration: add `SteamAudioSource` component, check *Occlusion*. Export scene geometry with `SteamAudioGeometry`. Parametric reverb is least expensive; True Audio Next uses GPU acceleration. [Steam Audio Unity Guide](https://valvesoftware.github.io/steam-audio/doc/unity/guide.html)
- `AudioSettings.GetConfiguration()` / `AudioSettings.Reset()` lets you change DSP buffer size at runtime — lower buffer size = lower latency at cost of higher CPU. Expose in graphics options.
- ADPCM is underused. For any short, high-frequency sound (footsteps, bullet impacts, UI clicks), ADPCM gives 3.5× compression at negligible CPU cost — better than Vorbis for short clips due to lower decode overhead.
- `AudioSource.Pause()` + `AudioSource.UnPause()` is more efficient than `Stop()` + `Play()` when you expect to resume the same clip position — `Stop()` resets clip position and may trigger a new seek on streaming clips.

**Tools and profiling for this role:**
- Profiler → Audio module → DSP CPU, voice count.
- Memory Profiler → Audio category.
- AudioStats window (Window → Analysis → Audio Stats) for real-time voice visualization.

**Cheat sheet:**

| Setting | Memory | CPU | Recommendation |
|---|---|---|---|
| Music: Decompress on Load | Very High | Low | Never — use Streaming |
| SFX: Compressed in Memory | Low | Medium | Standard for medium clips |
| Short SFX: Decompress on Load | Medium | Very Low | Acceptable for <1 s clips |
| Force to Mono (3D sources) | Halves memory | None | Always enable |
| Max Voices | N/A | Scales linearly | Set priority; disable silent sources |

---

### Animations

Animation is a consistent mid-range CPU cost that compounds quickly in scenes with many characters. Configuration choices here are permanent — wrong settings at import time persist through the game's lifetime.

**System comparison:**

| System | When to use | Performance profile |
|---|---|---|
| Legacy Animation | Avoid in new projects | Fast for simple single-clip (no blend overhead) |
| Animator / Mecanim | Characters with blending | Medium-high CPU; scales with layer and bone count |
| Playable API (2017+) | Code-driven, no state machine | Low overhead; full control |
| Animation Rigging (2019+) | Runtime IK, aim, multi-position | Per-constraint cost; runs after Animator |
| DOTS Animation (experimental) | 1000+ uniform-crowd characters | Parallel Burst jobs; steep learning curve |

**Common pitfalls:**
- **[All versions]** `Animator.cullingMode = AlwaysAnimate` (default) — evaluates full state machine for off-screen characters. [Unity Manual – Animation Performance](https://docs.unity3d.com/6000.4/Documentation/Manual/MecanimPeformanceandOptimization.html)
- **[All versions]** Humanoid rig when Generic would suffice — Humanoid mode is **2–2.5× slower** on platforms without NEON SIMD due to Avatar retargeting math.
- **[All versions]** `Animator.SetFloat("ParameterName", val)` with string in Update — internal dictionary lookup per call.
- **[All versions]** Scale curves on clips for characters that never scale — more expensive than translation/rotation curves.
- **[All versions]** `Animator.Rebind()` called in the update loop — rebuilds the entire Animator state, very expensive.
- **[2020-2022 LTS]** `com.unity.animation` (DOTS Animation) used for small numbers of characters where the complexity overhead is not offset by performance gains.

**Recommended practices:**
- Set culling mode explicitly:

```csharp
// Background NPCs — stop everything when off-screen
_animator.cullingMode = AnimatorCullingMode.CullCompletely;
// with:
skinnedMeshRenderer.updateWhenOffscreen = false;

// Critical story characters — maintain state machine, skip IK
_animator.cullingMode = AnimatorCullingMode.CullUpdateTransforms;
```

- Cache Animator parameter hashes at initialization:

```csharp
private static readonly int SpeedHash     = Animator.StringToHash("Speed");
private static readonly int IsGroundedHash = Animator.StringToHash("IsGrounded");

void Update()
{
    _animator.SetFloat(SpeedHash, _velocity.magnitude);
    _animator.SetBool(IsGroundedHash, _isGrounded);
}
```
[Unity Manual – Animation Performance](https://docs.unity3d.com/6000.4/Documentation/Manual/MecanimPeformanceandOptimization.html)

- Enable **GPU Skinning** in Player Settings → Other Settings. Offloads vertex skinning to a Compute Shader pass. [DOUBLE Unity Animation Performance](https://www.youtube.com/watch?v=apD2NgXulxE)
- Use **Generic** rig instead of Humanoid unless cross-rig retargeting or Humanoid IK is required.
- Enable **Optimize Game Objects** in rig import for crowds — collapses bone hierarchy, removes per-bone GameObjects, saves transform update overhead.
- Use the **Playable API** for code-driven animation without state machine overhead:

```csharp
var graph = PlayableGraph.Create("MyGraph");
var clipPlayable = AnimationClipPlayable.Create(graph, clip);
var output = AnimationPlayableOutput.Create(graph, "Output", _animator);
output.SetSourcePlayable(clipPlayable);
graph.Play();
```

- Reduce **Blend Weights** (`Quality.blendWeights`) to 2 for LOD1 and beyond. Four bones is the humanoid default; two is usually indistinguishable at medium distance.
- Strip scale curves in import settings for characters that never scale — use an `AssetPostprocessor` to automate this.
- Set `RigLayer.weight = 0` on Animation Rigging constraints when the rig is inactive (e.g., weapon-aim rig when unarmed).

**Lesser-known tricks:**
- **[Unity 6]** Batched GPU Skinning reduces the number of separate Compute dispatches for groups of identically-configured skinned meshes — a significant improvement for crowd scenarios.
- **Avatar Mask** on Animator layers constrains which bones the layer affects — an upper-body aim layer with a full-body mask wastes evaluation time on lower-body bones. Always assign precise masks to additive layers.
- **Animation Compression** in clip import settings (Optimal, Reduced Keyframes, Custom) affects both storage size and runtime evaluation cost. Optimal is the recommended default; Custom allows per-curve compression for precision-sensitive animations (facial).
- The Playable API cost is proportional to clips actually playing, not state machine complexity — prefer it over Animator Controller for dialogue systems, procedural animation, or cinematics.
- DOTS Animation (experimental) has no built-in state machine; blend graph nodes must be authored in the data-flow graph API. Not production-ready for diverse animation needs, but valid for uniform crowd scenarios (sports audiences, pedestrians).

**Tools and profiling for this role:**
- Profiler → CPU → filter for `Animator.Update`, `AnimationUpdate`, `PreLateUpdate.DirectorUpdateAnimationBegin`.
- Check `Animators` count in Rendering Profiler module.
- Frame Debugger → SkinnedMesh section for GPU Skinning dispatch count.

**Cheat sheet:**

| Setting | Default | Recommendation |
|---|---|---|
| `cullingMode` | AlwaysAnimate | CullCompletely for background |
| Rig type | Humanoid | Generic unless retargeting needed |
| GPU Skinning | On (where supported) | On always |
| Blend Weights | 4 | 2 for LOD1+; reduce per-LOD |
| Optimize Game Objects | Off | On for crowds |
| Animation Compression | Optimal | Optimal default |

---

### Physics

Unity uses PhysX (NVIDIA's physics library) for its built-in 3D physics. Physics is one of the most reliable sources of CPU budget overruns in games that grow organically — it starts fast and gets expensive as designers add more interactive objects.

**Common pitfalls:**
- **[All versions]** Running non-physics logic in `FixedUpdate` — `FixedUpdate` may be called multiple times per frame if the game is running slowly, creating a "death spiral" where physics work compounds into a freeze. Strictly reserve `FixedUpdate` for `Rigidbody` forces and physics queries.
- **[All versions]** Using `Physics.Raycast` with `RaycastHit` allocation inside a hot loop when `Physics.RaycastNonAlloc` exists.
- **[All versions]** Enabling Mesh Colliders on high-polygon meshes for non-convex shapes — non-convex Mesh Colliders are expensive to query and cannot participate in dynamic rigidbody physics. Use compound primitive colliders instead.
- **[All versions]** `Physics.autoSyncTransforms = true` (default) syncing transforms on every write — in physics-heavy scenes with many repositioned objects this produces redundant synchronization every frame. [Unity physics auto-sync transforms](https://docs.unity3d.com/6000.3/Documentation/Manual/physics-optimization-cpu-transform-sync.html)
- **[All versions]** Default physics layer collision matrix including all pairs — unchecking irrelevant layer-layer interactions in Project Settings — Physics — Layer Collision Matrix eliminates broad-phase query cost.
- **[All versions]** Fixed timestep too small — default 0.02 s (50 Hz) is fine for most games but ambitious defaults (0.01 s = 100 Hz) double physics CPU cost for marginal benefit in non-competitive games.
- **[2020-2022 LTS]** Unity Physics (DOTS) used without Burst compilation — the entire value proposition of DOTS Physics is that the simulation runs in Burst-compiled parallel jobs; managed-only DOTS Physics is slower than PhysX.

**Recommended practices:**
- Use `Physics.RaycastNonAlloc(ray, results, distance, layerMask)` instead of `Physics.Raycast` in hot paths:

```csharp
// Pre-allocate once
private readonly RaycastHit[] _hits = new RaycastHit[10];

void Update()
{
    int count = Physics.RaycastNonAlloc(transform.position,
                                        Vector3.down, _hits, 5f, groundMask);
    if (count > 0) HandleGroundHit(_hits[0]);
}
```

Similarly, `Physics.OverlapSphereNonAlloc`, `Physics.BoxCastNonAlloc` and their 2D equivalents all have NonAlloc variants.
- Disable `Physics.autoSyncTransforms` and call `Physics.SyncTransforms()` manually before batches of queries:

```csharp
void Start() => Physics.autoSyncTransforms = false;

void UpdatePhysicsQueries()
{
    // Move objects first
    MoveAllObjects();
    // Sync once for all subsequent queries
    Physics.SyncTransforms();
    PerformAllRaycasts();
}
```
[TheGameDev.Guru — Physics autoSyncTransforms](https://thegamedev.guru/unity-cpu-performance/physics-autosynctransforms/)

- Open **Project Settings → Physics → Layer Collision Matrix** and uncheck every layer pair that will never interact. The broad-phase AABB tree queries this matrix to eliminate pairs early; fewer enabled pairs = faster broad-phase.
- Use **Compound Colliders** (multiple primitive Colliders on child GameObjects with one Rigidbody on the parent) instead of non-convex Mesh Colliders for complex shapes. Spheres, capsules, and boxes are far cheaper to query than arbitrary meshes.
- Increase `Time.fixedDeltaTime` to 0.025 s (40 Hz) or 0.033 s (30 Hz) for non-competitive games that do not require high-fidelity collision response. The visual impact is minimal for most gameplay.
- Use **sleep thresholds** — `Rigidbody.sleepThreshold` (default 0.005) determines when a Rigidbody stops being simulated. Objects that settle but have a low sleep threshold keep consuming physics budget. Increase the threshold for objects that should rest quickly (furniture, props).
- Avoid `Rigidbody.MovePosition` / `MoveRotation` inside `Update()` — these are physics operations that should be called in `FixedUpdate`. Called from `Update`, they can produce one-frame lag artifacts and incorrect physics interpolation.
- Enable **Interpolation** on player Rigidbodies: `Rigidbody.interpolation = RigidbodyInterpolation.Interpolate`. This smooths the visual position between fixed timesteps for fast-moving objects without changing the simulation rate.
- For queries that run every frame on many agents (pathfinding, line-of-sight), batch the queries using Unity's `Physics.Raycast` inside a Job via `RaycastCommand`:

```csharp
// RaycastCommand batches many raycasts as a Job
var commands = new NativeArray<RaycastCommand>(agentCount, Allocator.TempJob);
var results  = new NativeArray<RaycastHit>(agentCount, Allocator.TempJob);

for (int i = 0; i < agentCount; i++)
    commands[i] = new RaycastCommand(agents[i].position, Vector3.down, 5f);

JobHandle handle = RaycastCommand.ScheduleBatch(commands, results, 32);
handle.Complete();

for (int i = 0; i < agentCount; i++)
    if (results[i].collider != null) HandleHit(i, results[i]);

commands.Dispose();
results.Dispose();
```
`RaycastCommand` runs the queries on worker threads, parallelizing line-of-sight for large numbers of agents.

- **2D Physics** (`Physics2D`) has a separate `autoSimulation` toggle (`Physics2D.autoSimulation = false`) enabling manual stepping via `Physics2D.Simulate(Time.fixedDeltaTime)` inside a custom loop — useful for turn-based games or deterministic replay.

**Lesser-known tricks:**
- `Physics.IgnoreLayerCollision(layerA, layerB, true)` at runtime to temporarily disable physics between two layers (e.g., player layer and collectibles during an invincibility phase) — cheaper than destroying and rebuilding the collision matrix.
- `Rigidbody.detectCollisions = false` disables collision detection for a specific Rigidbody without disabling the GameObject. Use for pooled projectiles on return to pool — avoids triggering `OnTriggerExit` on the return path.
- **Physics Debugger** (Window → Analysis → Physics Debugger) visualizes the active colliders, Rigidbodies in the sleep/awake state, and contact points. Essential for diagnosing "why is this object not sleeping?" and confirming compound collider setup.
- `Rigidbody.WakeUp()` and `Rigidbody.Sleep()` allow manual sleep/wake control. Manually sleeping a Rigidbody that will not move for several frames (an inactive trap, a dropped item) removes it from the physics simulation entirely.
- `Physics.queriesHitBackfaces = false` (default) means raycasts only detect front faces. Setting it true doubles the potential hit count per query. Keep it false unless your game design specifically requires back-face hits.
- DOTS physics (`Unity Physics`) is deterministic by design — the exact same inputs produce the exact same outputs regardless of platform. Built-in PhysX is deterministic on the same hardware/driver combination but not across different systems. If you need cross-platform determinism for replays or multiplayer, DOTS Physics is the correct choice. [Unity Physics vs Havok Physics](https://learn.unity.com/tutorial/ecs-physics-havok-physics-for-unity-and-unity-physics)

**Tools and profiling for this role:**
- Profiler → Physics module: `Physics.Processing` (main simulation), `Physics.FetchResults` (result sync), `Physics.Interpolation` (position smoothing cost).
- Physics Debugger for visual collider audit.
- `stat physics` in the Editor console for real-time broad/narrow phase counts.
- Profiler → CPU Timeline: `FixedUpdate.PhysicsFixedUpdate` gives the fixed-step budget. If this exceeds the fixed timestep, physics is behind and the death spiral begins.

**Cheat sheet:**

| Setting | Default | Performance recommendation |
|---|---|---|
| `Time.fixedDeltaTime` | 0.02 (50 Hz) | 0.025–0.033 for non-competitive |
| `Physics.autoSyncTransforms` | true | false (sync manually) |
| `Rigidbody.sleepThreshold` | 0.005 | Increase for static props |
| `Rigidbody.interpolation` | None | Interpolate for player/camera targets |
| Mesh Collider (non-convex) | Allowed | Avoid; use compound primitives |
| Layer Collision Matrix | All pairs | Disable irrelevant pairs |
| `RaycastNonAlloc` | Not default | Use in all hot-path queries |

---

### UI (UGUI and UI Toolkit)

Unity's UI system is the most commonly misunderstood performance area. Canvas batching rules are non-intuitive and the default component settings are wrong for performance.

**Common pitfalls:**
- **[All versions]** Every `Image` and `RawImage` has **Raycast Target = true** by default. The Graphic Raycaster iterates every enabled Raycast Target on input. 200 images = 200 intersection tests per frame.
- **[All versions]** Single Canvas with thousands of mixed static and animating elements — any change to any element rebuilds the entire Canvas.
- **[All versions]** Layout Group on high-frequency dynamic elements — each Layout Element dirty triggers `GetComponent` calls walking up the transform hierarchy.
- **[All versions]** `SetActive(true/false)` on a Canvas with many children — triggers full rebuild on activate.
- **[All versions]** Using legacy `Text` component — sub-pixel rasterization, frequent atlas rebuilds. Use TextMeshPro exclusively.
- **[2020-2022 LTS]** World Space Canvas without necessity — full per-frame rasterization, affected by scene lighting, most expensive Render Mode.

**Recommended practices:**
- Split static and dynamic UI into separate Canvases:

```
Root Canvas
├── Static Canvas (backgrounds, labels, non-animated icons)
│       → Batches once on load, never rebuilds
└── Dynamic Canvas (health bars, timers, score, animated elements)
        → Rebuilds frequently but only contains changing elements
            └── Sub-Canvas per high-frequency element if needed
```
[Unity – UI Optimization Tips](https://unity.com/how-to/unity-ui-optimization-tips)

- Disable **Raycast Target** on every non-interactive element (decorative images, backgrounds, text labels that aren't buttons). This is a systematic change — do it for every Image component in the project.
- Use **Screen Space - Overlay** Render Mode as the default (cheapest; no camera involvement). Use Screen Space - Camera only when depth effects are required. World Space only when diegetic UI is a design requirement.
- Use **TextMeshPro** for all text. SDF rendering, resolution-independent, GPU-cheap, supports rich text. [Unity Manual – UI System Compare](https://docs.unity3d.com/6000.4/Documentation/Manual/UI-system-compare.html)
- Pack UI icons, button states, and small decorative images into **Sprite Atlases** — elements from the same atlas share a material and batch into one draw call.
- Avoid baking layouts in Layout Groups on high-frequency dynamic content. Instead, anchor positions and offsets where possible — they are purely a transform property, not a layout calculation.
- For **UI Toolkit** (production-ready Unity 2022 LTS+), animate via USS transitions on `translate`, `scale`, `rotate` — these run on the GPU via `DynamicTransform` usage hint and do not trigger layout recalculation. Never animate `width`, `height`, `top`, or `left` — those trigger expensive layout recalcs. [Unity Manual – Optimizing UI Toolkit](https://docs.unity.cn/6000.3/Documentation/Manual/best-practice-guides/ui-toolkit-for-advanced-unity-developers/optimizing-performance.html)
- UI Toolkit batches via an "uber shader" supporting up to **8 textures per batch**. Exceeding 8 unique textures in one batch breaks batching.

**Performance comparison (1000 interactive elements, Unity 2022.3 LTS):** [Angry Shark Studio – UI Toolkit vs UGUI 2025](https://www.angry-shark-studio.com/blog/unity-ui-toolkit-vs-ugui-2025-guide/)

| Metric | UGUI | UI Toolkit |
|---|---|---|
| Draw Calls | 45 | 5 |
| CPU Frame Time | 12.5 ms | 4.2 ms |
| Memory Usage | 125 MB | 48 MB |
| Instantiation (100 items) | 85 ms | 15 ms |

**Lesser-known tricks:**
- Sub-Canvases isolate their contents from parent Canvas rebuilds — but the system does not batch across separate Canvases, so excessive splitting increases draw calls. Target 2–4 Canvases per UI screen. [Unity Learn – Optimizing Unity UI](https://learn.unity.com/course/doozyui-related-tutorials/tutorial/optimizing-unity-ui)
- `Canvas.enabled = false` / `= true` is faster than `gameObject.SetActive(false/true)` for temporarily hiding a Canvas — it avoids tearing down and rebuilding the Canvas children's state.
- For high-frequency numeric updates (score, health, ammo), update the text string only when the value changes — not every frame. Store the last-rendered value and skip the text assignment if unchanged.
- Particle effects inside a Canvas with World Space Render Mode cause the Canvas to treat each particle as a UI element. Don't mix Particle Systems with World Space Canvases without profiling the overhead first.
- `CanvasGroup.alpha = 0` hides UI visually but does not disable Raycast Targets — use `CanvasGroup.blocksRaycasts = false` as well, or disable the Canvas.

**Tools and profiling for this role:**
- Profiler → CPU → `Canvas.BuildBatch`, `Canvas.SendWillRenderCanvases` — these fire every time a Canvas rebuilds.
- Profiler → GPU → UI section.
- Frame Debugger → UI category for draw call count and Canvas breakdown.

**Cheat sheet:**

| Setting/Pattern | Cost | Recommendation |
|---|---|---|
| Raycast Target default | High (many tests) | Disable on all non-interactive |
| Single large Canvas | High (full rebuild) | Split static/dynamic |
| Layout Groups on dynamic | Medium | Bake into anchors |
| World Space Render Mode | High | Only for diegetic UI |
| Legacy Text | Medium (atlas rebuilds) | Always use TextMeshPro |

---

### Networking and Multiplayer

Networking optimization is as much about architecture decisions as about code — the right framework choice for game scale matters more than micro-optimizations.

**Framework comparison:**

| Framework | Type | Scale | Strength | Limitation |
|---|---|---|---|---|
| Netcode for GameObjects (NGO) [2022+] | First-party Unity | 2–10 players | Unity integration, server-authoritative | Limited high-scale |
| Netcode for Entities [2022+] | First-party, DOTS | High | Burst jobs, deterministic | Requires full DOTS |
| Mirror | Community OSS | Small–large | Flexible transports | No cloud infra |
| Photon Fusion / PUN | Commercial SaaS | Large, global | Cloud, lag comp, rollback | Cost scales with CCU |
| Steam P2P / Steamworks | P2P relay | Small sessions | No server cost | Steam ecosystem only |

[Unity NetCode for GameObjects tutorial](https://www.youtube.com/watch?v=swIM2z6Foxk)

**Common pitfalls:**
- **[2020-2022 LTS]** Mutating `NetworkVariable` every frame — only changed values are sent, but `IsDirty` checking still has overhead. Mutate only on actual game state change.
- **[2020-2022 LTS]** `ServerRpc` calls every frame — batching is automatic per tick but the RPC submission overhead compounds.
- **[2020-2022 LTS]** Bandwidth-heavy state synchronization without visibility culling — `NetworkObject.CheckObjectVisibility` should exclude objects not relevant to a given client.
- **[All versions]** Tick rate mismatch — if client update rate < server tick rate, bandwidth is wasted with no benefit.
- **[All versions]** No lag compensation for competitive hit detection — players see positions 50–100 ms behind server state; shots never connect where aimed.

**Recommended practices:**
- Set tick rate via `NetworkManager.TickRate`:
  - 30 Hz: Turn-based, casual, co-op
  - 60 Hz: Action games, platformers
  - 128 Hz: Competitive FPS (Photon Fusion) [Unity Manual – Tick and Update Rates](https://docs.unity3d.com/Packages/com.unity.netcode.gameobjects@2.5/manual/learn/ticks-and-update-rates.html)

- Batch input into structs sent once per tick, not `ServerRpc` calls per input event.
- Implement `NetworkObject.CheckObjectVisibility` delegate to cull NetworkObjects from clients based on distance — objects not relevant to a client should not exist in their world.
- Quantize position floats to 16-bit integers for low-bandwidth transmission. NGO's `NetworkTransform` exposes interpolation and compression settings.
- For lag compensation in NGO: record `NetworkTransform` positions with timestamps in a circular buffer. On `CmdFire`, binary-search for `serverTime - clientRTT/2`, perform hit test against rewound state. [Mirror – Lag Compensation](https://mirror-networking.gitbook.io/docs/manual/general/lag-compensation)
- Use **Unity Relay** (Unity Gaming Services) for small-scale P2P games without dedicated server infrastructure. Limited throughput per relay — not suitable for >30 players or bandwidth-heavy simulations.
- For competitive or >30-player games: Unity Dedicated Server build target (headless, Unity 2021+) provides full control and arbitrary player count.
- Reference **Boss Room** (Unity's official NGO sample, 8-player co-op dungeon) for production NGO patterns: lobby flow, connection approval, in-game state machine, NetworkObject spawning. [Boss Room](https://www.youtube.com/watch?v=swIM2z6Foxk)

**Lesser-known tricks:**
- NGO's `NetworkVariable` changes within one tick are batched into a single `NetworkVariableDeltaMessage` — you do not need to manually batch variable changes, just keep them within the same tick. [NGO GitHub tick delivery](https://github.com/Unity-Technologies/com.unity.netcode.gameobjects/issues/3195)
- The distinction between server-authoritative (server owns positions, clients send inputs) and client-authoritative (clients own positions) is architectural. Server-authoritative is harder to implement but not cheatable. Use client-authoritative only for non-competitive internal tools or hotseat games.
- For Netcode for Entities: the entire entity simulation is deterministic and Burst-compiled, enabling efficient delta compression by sending only structural changes, not full position snapshots.
- Photon Fusion's rollback netcode model maintains a full copy of game state per tick for client-side prediction and server reconciliation — this requires all game-state types to be blittable. Plan your state structures before adopting Fusion.

**Tools and profiling for this role:**
- Profiler → Network module (NGO specific).
- Wireshark for raw packet inspection and bandwidth measurement.
- NGO's `NetworkStats` MonoBehaviour for in-game bandwidth display.
- Unity Multiplayer Center (Package Manager → Multiplayer Center) for architecture guidance.

**Cheat sheet:**

| Parameter | Recommended | Notes |
|---|---|---|
| Tick Rate (casual) | 30 Hz | Turn-based, co-op |
| Tick Rate (action) | 60 Hz | Platformers, action |
| Tick Rate (competitive) | 128 Hz | FPS, Photon Fusion |
| `NetworkVariable` mutation | Only on change | Not in Update() |
| Object visibility | Cull at distance | `CheckObjectVisibility` |

---

### QA / Build / Production

Build configuration and QA workflows are where the gap between development performance and shipping performance is closed.

**Common pitfalls:**
- **[All versions]** Profiling in a Development Build and drawing conclusions — Development Builds disable IL2CPP code stripping and shader stripping, slightly inflate performance cost.
- **[All versions]** Shipping with Mono backend — always ship IL2CPP.
- **[All versions]** No `asmdef` files — every code change triggers a full project recompile.
- **[2020-2022 LTS]** Missing `link.xml` when using aggressive stripping with reflection-heavy code — silent runtime failures.
- **[All versions]** `Addressables.ReleaseAsset` / `ReleaseInstance` not called — most common Addressables memory leak.
- **[2020-2022 LTS]** Single asset bundle scheme — granularity is wrong; impossible to unload individual assets without analyzing dependencies.

**Recommended practices:**
- Build configurations:

| Configuration | When to use |
|---|---|
| Development Build | All development; enables Profiler connection |
| Script Debugging | Managed debugger; significant overhead; use only when debugging |
| Autoconnect Profiler | Attaches Profiler on startup; use for automated performance runs |

Never ship a Development Build. Always profile against a non-Development build for final performance metrics.

- IL2CPP settings for shipping:
  - **Scripting Backend:** IL2CPP
  - **API Compatibility:** .NET Standard 2.1 (smaller BCL, better stripping)
  - **IL2CPP Code Generation (Unity 2021+):** "Faster runtime" for shipping builds — generates fully expanded generic code, faster execution, larger binary [Unity Manual – IL2CPP scripting backend](https://docs.unity3d.com/Manual/scripting-backends-intro.html)
  - **Managed Stripping Level:** Medium or High (test thoroughly at High); preserve reflection-dependent code in `link.xml`

```xml
<linker>
  <assembly fullname="Assembly-CSharp">
    <type fullname="MyGame.SaveData" preserve="all"/>
  </assembly>
  <assembly fullname="Newtonsoft.Json" preserve="all"/>
</linker>
```

- Add **Assembly Definition files** per subsystem (Input, AI, UI, Networking). Compile savings of 60–80% on large projects are routinely reported. Wrap third-party/Asset Store code first (rarely changes → compiles once). Runtime vs Editor assembly split prevents editor-only changes from recompiling runtime. Use [Compilation Visualizer](https://github.com/needle-tools/compilation-visualizer) to audit dependency chains. [Coffee Brain Games – asmdef](https://coffeebraingames.wordpress.com/2018/01/21/reducing-compile-time-in-unity-using-assembly-definition-files/)

- Addressables patterns:
  1. **Pack Separately** vs **Pack Together** — group assets that load/unload together into the same bundle. Fine-grained bundles enable precise unloading but increase metadata overhead.
  2. Run **Check Duplicate Bundle Dependencies** in Analyze window — shared textures pulled into multiple bundles create duplicate assets in memory.
  3. Always call `Addressables.ReleaseAsset` / `ReleaseInstance` — missing calls are the most common Addressables memory leak. [Unity Blog – Saving memory with Addressables](https://unity.com/blog/technology/tales-from-the-optimization-trenches-saving-memory-with-addressables)

- **Unity Test Runner** for automated performance regression:
  - Edit Mode tests: pure logic, math, serialization (no Play Mode needed)
  - Play Mode tests: full MonoBehaviour lifecycle
  - **Performance Testing Extension** (`com.unity.test-framework.performance`): `Measure.Method` and `Measure.Frames` for percentile data; integrates with CI to flag regressions

- **CI options:**

| Option | Notes |
|---|---|
| Unity Cloud Build | Managed CI; tight Unity integration; limited environment control |
| GitHub Actions | Free tier with self-hosted runners; supports Unity via `game-ci/unity-builder` |
| TeamCity / Jenkins | Full control; preferred for large studios; license seat management |

- Use `BuildPipeline.BuildPlayer` scripted builds and `UnityEditor.Build.Reporting.BuildReport` API for automated build-size tracking in CI. Fail the build if compressed size exceeds threshold.
- Enable **Domain Reload** and **Scene Reload** disabling immediately at project start — not after the project becomes large. The payoff is immediate and the migration cost is front-loaded.

**Lesser-known tricks:**
- **Build Profiles** (Unity 2023.1+): named build configurations with per-profile Player Settings overrides. Eliminate manual reconfiguration when switching between PC/console/QA builds.
- `Scripting Define Symbols` in Player Settings gate debug, profiling, and feature code at compile time — zero runtime cost in production builds. Use `DEVELOPMENT_BUILD` as a built-in gate.
- `Application.BuildGUID` is a unique string per build — store it in the game version overlay for QA to identify exact builds without guessing.
- The **Build Report** `Library/LastBuild.buildreport` is a Unity ScriptableObject — readable via C# in Editor scripts for CI asset-size tracking without installing the Build Report Inspector package.

**Tools and profiling for this role:**
- Build Report Inspector for post-build asset size analysis.
- Profile Analyzer for quantitative regression comparison.
- Compilation Visualizer for asmdef dependency audit.
- Unity Test Runner + Performance Testing Extension for automated performance gates.

**Cheat sheet:**

| Setting | Development | Shipping |
|---|---|---|
| Scripting Backend | Mono | IL2CPP |
| IL2CPP Code Gen | Faster builds | Faster runtime |
| API Compatibility | .NET Standard 2.1 | .NET Standard 2.1 |
| Stripping Level | Low | Medium–High |
| Domain Reload | Disabled | N/A |
| Development Build | On | Off |

---

### Tech Art

Tech artists live at the intersection of rendering and engineering, responsible for the systems that tie art into the engine pipeline without breaking performance.

**Common pitfalls:**
- **[2020-2022 LTS]** `MaterialPropertyBlock` used unintentionally killing SRP Batcher compatibility — any renderer with an MPB falls back to GPU Instancing or unoptimized draw calls.
- **[All versions]** Shader Graph multi-compile keyword spam — every Custom Function Node with conditional paths can double variant counts if not carefully scoped.
- **[Unity 6+]** Not migrating URP Renderer Features to the Render Graph API — all `ScriptableRenderPass.Execute` overrides must use `RecordRenderGraph` in Unity 6, with the old path deprecated.
- **[Unity 6+]** Enabling GPU Resident Drawer without also enabling Forward+ rendering path — GRD requires Forward+.
- **[All versions]** HDR render target enabled when Bloom is not used — R16G16B16A16_SFloat uses 8 bytes/pixel vs 4 for LDR. Disable HDR in URP Asset → Quality → HDR if Bloom is not active.
- **[2020-2022 LTS]** Camera Stacking with post-processing on each camera in the stack — post-processing should apply only on the last camera to avoid duplicate effect passes.

**Recommended practices:**
- Audit SRP Batcher compatibility via Frame Debugger: expand the SRP Batcher node. "Batch reason: different shader" means even identical materials on different base shaders cannot batch. "Different material properties" means `MaterialPropertyBlock` or mismatched CBUFFER content.
- **[Unity 6+]** Enable GPU Resident Drawer in URP scenes with many repeated mesh-material pairs:
  - Universal Renderer asset → GPU Resident Drawer → Instanced Drawing
  - Requires: Forward+ rendering path, compute shader support, SRP Batcher enabled, Static Batching disabled
  - Also enable GPU Occlusion Culling for matching depth-buffer occlusion at no bake cost [Unity GPU Resident Drawer docs](https://docs.unity3d.com/6000.0/Documentation/Manual/urp/gpu-resident-drawer.html)
- **[Unity 6+]** Migrate Renderer Features to Render Graph API:

```csharp
// Unity 6+ — Render Graph API (required)
public override void RecordRenderGraph(RenderGraph renderGraph,
    ContextContainer frameData)
{
    using (var builder = renderGraph.AddRasterRenderPass<PassData>(
        "MyPass", out var passData))
    {
        // declare resource usage, not execution
        builder.SetRenderFunc((PassData data, RasterGraphContext context) =>
            ExecutePass(data, context));
    }
}
```
[Write a render pass using Render Graph](https://docs.unity3d.com/6000.0/Documentation/Manual/urp/render-graph-write-render-pass.html)

- **[Unity 6+]** Enable **STP (Spatial-Temporal Post-Processing)** for GPU-bound scenes:
  - URP Asset → Quality → Upscaling Filter → Spatial-Temporal Post-Processing
  - 0.7–0.8 Render Scale with STP can match 1.0 native quality at significantly lower GPU cost [Unity STP docs](https://docs.unity3d.com/6000.2/Documentation/Manual/urp/stp/stp-upscaler.html)
- URP Renderer Feature injection points (use the most downstream that works):
  - `BeforeRenderingOpaques` — for effects that modify depth before geometry pass
  - `AfterRenderingOpaques` — for screen-space effects using opaque depth
  - `AfterRenderingTransparents` — for effects needing full scene
  - `BeforeRenderingPostProcessing` — for effects that post-processing must read
- HDRP Custom Pass injection points: `BeforePreRefraction`, `BeforeTransparent`, `BeforePostProcess`, `AfterPostProcess`. Supports fullscreen, object, and quad injection types.
- Choose Render Texture format by precision need:
  - `R8_UNorm` — 1 byte/px, masks, stencil-like effects
  - `R8G8_UNorm` — 2 bytes/px, packed normal XY or two masks
  - `R8G8B8A8_UNorm` — 4 bytes/px, standard LDR color
  - `R16G16B16A16_SFloat` — 8 bytes/px, HDR, physically-based values
- For HDRP Decal Projectors: each active projector adds a draw call and samples the decal atlas. Set `Max Decal on Screen` in HDRP Asset; bake static decals into albedo lightmaps where possible. Clustered decal rendering available from HDRP 2022+. [HDRP Local Volumetric Fog](https://docs.unity3d.com/Packages/com.unity.render-pipelines.high-definition@15.0/manual/Local-Volumetric-Fog.html)
- **DLSS/FSR/XeSS status:**
  - DLSS: HDRP native (Unity 2021.2+); URP via NVIDIA DLSS package. Requires RTX hardware, DX12/Vulkan.
  - FSR: AMD, hardware-agnostic; integrated via `com.unity.render-pipelines.core` TAA in URP/HDRP from Unity 2022+.
  - XeSS: Intel, DX12 only; [open-source plugin](https://github.com/GameTechDev/XeSSUnityPlugin). [Unity STP docs](https://docs.unity3d.com/6000.1/Documentation/Manual/urp/stp/stp-upscaler.html)

**Lesser-known tricks:**
- **Custom Render Textures** support self-updating procedural textures with configurable update modes (on demand, per frame, real-time) — useful for animated noise, fluid simulations, texture projections without requiring a camera.
- Disable HDR when Bloom is inactive. LDR render targets use half the memory and bandwidth. [Rendering tricks research](https://docs.unity3d.com/6000.0/Documentation/Manual/urp/gpu-resident-drawer.html)
- Render Scale + STP: `0.7 scale + STP` is often visually indistinguishable from `1.0 native` at a meaningful GPU cost reduction. Run a blind comparison before publishing any marketing claims.
- Camera Stacking in URP: overlay cameras always render in Forward path even if the Base Camera uses Deferred. Culling optimizations within a single camera do not apply across stack boundaries.
- `Shader.WarmupAllShaders()` compiles every variant — thorough but slow. Prefer `ShaderVariantCollection.WarmUp()` with a curated collection for controlled warm-up scope. Unity 6's Shader Pipeline Library persists compiled variants across sessions, eliminating first-frame stutter on repeat sessions.

**Tools and profiling for this role:**
- Frame Debugger — primary tool for SRP Batcher analysis, Render Graph pass names (Unity 6), render order.
- RenderDoc — visual debugging, texture/buffer inspection, draw call state.
- NVIDIA Nsight Graphics — warp utilization, shader occupancy for GPU-bound shaders.
- Rendering Debugger (URP/HDRP) — overdraw, Material Validation, Light Overlaps.

**Cheat sheet:**

| Feature | Min version | Enable via |
|---|---|---|
| SRP Batcher | URP 2019.3+ | On by default in URP |
| GPU Resident Drawer | Unity 6, URP | Universal Renderer asset → Instanced Drawing |
| Render Graph | Unity 6 mandatory | All new Renderer Features |
| STP | Unity 6 | URP Asset → Upscaling Filter → STP |
| APV | Unity 6 | Light Probe System → APV |
| Forward+ | URP 2021.2+ | Universal Renderer → Rendering Path |

---

### Last Resort Methods

When profiling reveals systemic issues too large to fix before a deadline, these are valid temporary measures with known quality costs. They are not substitutes for proper optimization — they buy time.

**Quality Settings drop:**
- `QualitySettings.SetQualityLevel(1)` at runtime to switch to a lower tier mid-session for hardware that misses frame budget.
- Expose as a user-facing setting in the options menu. At minimum: Low, Medium, High. Low should target 1080p/30 FPS on 5-year-old integrated graphics; High should target 1440p/60 FPS on mid-range discrete.

**Render Scale:**
- URP Asset → Quality → Render Scale. Reduce to 0.7–0.75 as a GPU-bound relief valve. Pair with STP (Unity 6+) for quality recovery.
- Expose Render Scale as an advanced graphics option — some players prefer 0.85 at 4K over 1.0 at 1080p.

**Scalability per-platform quality tier configuration:**
```ini
[Low Quality Tier]
Shadow Distance: 60
Cascade Count: 1
Shadow Quality: Soft PCF 2x2
MSAA: Off
Anti-Aliasing: FXAA
Render Scale: 0.75
HDR: Off
SSAO: Off
Bloom: Off
Depth of Field: Off

[Medium Tier]
Shadow Distance: 100
Cascade Count: 2
MSAA: 2x
Anti-Aliasing: TAA
Render Scale: 0.85
HDR: On
SSAO: Low (4 samples)
Bloom: On

[High Tier]
Shadow Distance: 150
Cascade Count: 3–4
MSAA: Off (use TAA/STP)
Render Scale: 1.0
HDR: On
SSAO: Medium (8 samples)
Bloom: On, DoF: On

[Ultra Tier]
Shadow Distance: 200+
STP/DLSS/FSR: On
Cascade Count: 4
All effects: On
Render Scale: 1.0 (or >1.0 with DLSS Quality)
```

**Texture quality downgrade:**
- `QualitySettings.globalTextureMipmapLimit = 1` — forces all textures to render at half resolution globally. A blunt instrument; use per-texture mip streaming first.

**Physics fixed timestep:**
- Increase `Time.fixedDeltaTime` from 0.02 (50 Hz) to 0.033 (30 Hz) for CPU-bound physics. Lower fidelity collision response but significant CPU save in physics-heavy scenes.

---

## Profiling Workflow Reference

This section is a condensed workflow guide for the most common profiling sessions. It complements the Tools section with ordered process steps rather than feature descriptions.

### Session 1: Identifying the Bottleneck Type

The fastest diagnostic session is a 5-minute triage. Run it first, before opening any specialization section.

1. **Build a Development Build** with Autoconnect Profiler enabled. Never profile in Editor Play mode for shipping decisions.
2. **Connect the Profiler** and navigate to the worst-case in-game area (highest density, most active enemies, peak VFX).
3. **Capture 60–100 frames**. Open Profile Analyzer and note the **median frame time** and **99th percentile**.
4. **Open a median frame in CPU Timeline**. Identify the widest bar on the main thread:
   - `BehaviourUpdate` dominant → C# gameplay code bottleneck. Go to Code & Mechanics section.
   - `Camera.Render` / `PostLateUpdate.FinishFrameRendering` dominant → rendering. Check GPU module.
   - `Physics.Processing` dominant → physics. Go to Physics section.
   - `Gfx.WaitForPresentOnGfxThread` large → GPU-bound. Look at GPU module breakdown.
5. **Check the Rendering module** for draw call count and SetPass count:
   - SetPass calls ≈ draw calls: SRP Batcher not working. Open Frame Debugger.
   - SetPass calls << draw calls: SRP Batcher working but many objects. Consider GPU Resident Drawer (Unity 6+).
   - Both low but GPU-bound: fill-rate problem (overdraw, post-processing, shadow maps). [Unity profiling best practices](https://unity.com/how-to/best-practices-for-profiling-game-performance)

### Session 2: GC Allocation Hunting

GC spikes appear as periodic frame-time bumps that don't correspond to visible scene events. Run this session when frame time is irregular.

1. In the CPU Profiler Hierarchy, enable the **GC Alloc** column. Sort by GC Alloc descending.
2. Enable **Allocation Call Stacks** in the Profiler toolbar (gear icon). This traces each `GC.Alloc` back to its source line in a subsequent capture.
3. Re-capture with call stacks enabled. Find the top allocators in `BehaviourUpdate`.
4. Common hotspots: `Debug.Log` (always allocates a string), LINQ expressions, `Camera.main`, `new WaitForSeconds()`, `GetComponent<T>()` results not cached, coroutines allocating state machines.
5. After fixing each allocator, re-run Profile Analyzer Compare mode with the before/after `.pdata` files to confirm the GC Alloc column dropped.

**Incremental GC note:** With Incremental GC on, spikes are spread across frames. Sort the Hierarchy by **Total** (not Self) and look for `GC.Collect` entries to find residual full-collection events. If `GC.Collect` still appears regularly, total allocation rate is too high for incremental collection to keep up. [Unity incremental GC docs](https://docs.unity3d.com/Manual/performance-incremental-garbage-collection.html)

### Session 3: GPU Bottleneck Isolation

1. In the GPU Profiler module, identify which category is largest: Geometry, Shadows, Lighting, Post-Processing.
2. For **Shadows**: reduce `QualitySettings.shadowDistance` by 20% increments. Open Frame Debugger to count shadow map render passes (one per shadow-casting light per cascade).
3. For **Geometry**: check triangle count in Rendering module. Enable LOD Groups or reduce LOD Bias.
4. For **Post-Processing**: disable effects one by one via Volume overrides in the editor. The one that causes the largest GPU time drop is the primary target.
5. For **Overdraw**: open RenderDoc, inspect the Depth/Color targets for transparent geometry. Or use Rendering Debugger → Lighting → Overdraw view.
6. When GPU-bound on PC: consider dropping Render Scale to 0.85 with STP (Unity 6+) or TAA upscaling. A 0.85 render scale reduces pixel count by ~28%, which typically matches a ~25% GPU time reduction for fill-rate-bound passes.

### Session 4: First-Frame and Load Spike

First-frame spikes (200+ ms on startup or level load) are distinct from steady-state performance. Diagnose them separately:

1. Set `Application.targetFrameRate = -1` and disable VSync for the load sequence so the full spike is visible in the Profiler without VSync padding.
2. Look for `ShaderLab.CreateGpuProgram` — shader compilation stutters on first use. Fix with `ShaderVariantCollection.WarmUp()` during a loading screen.
3. Look for `Loading.LoadObjectFromFile` and `Loading.AwakeFromLoad` — synchronous asset loads. Convert to async with `Resources.LoadAsync` or Addressables.
4. Look for `GarbageCollector.CollectIncremental` spikes immediately after load — indicates large number of allocations during scene setup that triggered a collection. Reduce setup allocations.
5. `Domain.Reload` in Editor profiling is not present in builds; do not optimize against it for shipping. Disable it in Editor for iteration speed, not for build performance.

### Session 5: Memory Audit

Memory problems (gradual leaks, VRAM over-budget) require snapshot-based analysis, not frame-rate profiling.

1. Install the Memory Profiler package (`com.unity.memoryprofiler`).
2. Take a snapshot at game start (just after the main menu loads).
3. Play for 15–20 minutes. Take a second snapshot.
4. Use **Diff** view to see objects present in snapshot 2 but not snapshot 1. These are potential leaks.
5. Common leak sources:
   - Addressables assets loaded but `ReleaseAsset` never called — the asset stays resident.
   - Event handlers (`UnityEvent`, C# events) holding references to destroyed objects — the object cannot be collected.
   - Static dictionaries accumulating entries without eviction.
   - `RenderTexture` created every frame without explicit `Release()`.
6. Check the **Objects and Allocations** view for Textures. Find any texture with unexpectedly high memory — common causes: Read/Write Enabled (doubles memory), wrong max size (2048 when 512 would do), wrong format (RGBA32 instead of BC3). [Memory Profiler docs](https://docs.unity3d.com/Packages/com.unity.memoryprofiler@1.1/manual/index.html)

### Profiling Checklist (Quick Reference)

| Step | Tool | What you're looking for |
|---|---|---|
| Identify bottleneck type | CPU Profiler Timeline | Widest bar on main thread |
| GC allocation hunt | CPU Hierarchy + Call Stacks | GC Alloc column dominators |
| Draw call analysis | Rendering module + Frame Debugger | SetPass vs batch counts |
| GPU pass breakdown | GPU module + RenderDoc | Geometry/Shadows/PP cost |
| Shader stutter | Frame Debugger + Profiler | `ShaderLab.CreateGpuProgram` |
| Memory leak | Memory Profiler snapshots | Diff view; growing object types |
| Regression validation | Profile Analyzer Compare | Median frame time before/after |
| Build size audit | Build Report Inspector | Largest assets in build |

---

## Optimization Sweep Steps (Pre-Milestone Checklist)

Run this sweep before every major milestone: Alpha, Beta, Gold Master.

### Scene Audit

- [ ] Capture 100+ frame Profile Analyzer baseline from Development Build player on minimum-spec hardware
- [ ] Identify CPU-bound vs GPU-bound state (check `Gfx.WaitForPresentOnGfxThread` vs `BehaviourUpdate`)
- [ ] All major systems have ProfilerMarkers and are visible in Hierarchy
- [ ] 99th-percentile frame time within budget (33 ms for 30 FPS, 16.67 ms for 60 FPS)
- [ ] No unexpected frame spikes > 2× median in representative gameplay
- [ ] Profile Analyzer baseline `.pdata` saved for regression comparison
- [ ] Draw call count and SetPass count in Rendering module are in expected range
- [ ] GC Alloc in steady-state gameplay is 0 bytes per frame (or minimized)

### Meshes / Models

- [ ] Read/Write Enabled disabled on all imported meshes (unless runtime access required)
- [ ] Compress Mesh enabled on all imported meshes
- [ ] All meshes ≤ 65K vertices use 16-bit index format
- [ ] LOD Groups configured on all hero assets with ≥ 3 LOD levels
- [ ] LOD Bias set to target value (0.7–0.85 for most PC games)
- [ ] GPU Skinning enabled in Player Settings (Player Settings → Other Settings → GPU Skinning)
- [ ] Scale curves stripped from clips for characters that never scale
- [ ] `Optimize Game Objects` enabled on all crowd-character rigs
- [ ] Static Batching disabled if GPU Resident Drawer is enabled (they conflict)
- [ ] Meshes used in procedural/runtime updates have `Mesh.MarkDynamic()` called

### Lighting

- [ ] Shadow Distance set to minimum viable range for game type (80–120 m for most PC games)
- [ ] Cascade count appropriate for target hardware tier (2–3 for mid-range)
- [ ] Realtime Reflection Probes set to `OnDemand` refresh (not `EveryFrame`)
- [ ] Lightmaps baked at final quality settings (not Draft/Low quality)
- [ ] APV enabled (Unity 6+) or manual probe placement validated and gap-free
- [ ] SSAO sample count appropriate per quality tier (4 samples on Low, 8 Medium, 16+ High)
- [ ] Mixed Lighting mode is Shadowmask (not Baked Indirect if you have moving objects)
- [ ] No lights left on `Realtime` mode that should be `Baked` or `Mixed`
- [ ] Rendering Layers configured to exclude irrelevant light-mesh pairs

### VFX

- [ ] All VFX Graph assets have Manual or Recorded bounds (not Automatic)
- [ ] All VFX Graph assets have `Culling Flags` set appropriately (stop simulating when invisible)
- [ ] VFX Graph `Capacity` values are at minimum required, not set to "just in case" maximums
- [ ] Particle System Collision modules: World mode replaced with Plane mode or VFX Graph depth collision
- [ ] Light module: `Max Light Count` set on all Particle Systems using it
- [ ] Particle System Trail module: trail count capped; width-at-distance strip enabled
- [ ] Sub-emitter chains: no chain deeper than 3 sub-emitters on dense burst systems

### UI

- [ ] All non-interactive Image/RawImage components have Raycast Target disabled
- [ ] Static and dynamic elements on separate Canvases
- [ ] No Layout Groups on elements that update more than once per second
- [ ] All text uses TextMeshPro (zero legacy `Text` components)
- [ ] Sprite Atlases created for icon sets and button states
- [ ] World Space Canvases justified (not used for screen UI)
- [ ] `CanvasGroup.blocksRaycasts = false` set alongside `alpha = 0` for hidden panels
- [ ] UI Toolkit: USS transitions use `translate`/`scale`/`rotate` only; no `width`/`height` animation

### Streaming and Memory

- [ ] All audio files > 10 s use Streaming load type; all audio files < 1 s use Decompress on Load
- [ ] All textures checked for Read/Write Enabled trap
- [ ] All textures using correct BC compression format (BC5 for normals, BC1/BC3 for albedo, BC4 for single-channel masks)
- [ ] Texture max sizes appropriate to their use (distant props: 512 max; hero materials: 1024–2048 max)
- [ ] Mipmap Streaming enabled in Quality Settings for open-world or large scenes
- [ ] Addressables Analyze: Check Duplicate Bundle Dependencies ran and resolved
- [ ] All `Addressables.ReleaseAsset` / `ReleaseInstance` calls verified against all load paths
- [ ] Memory Profiler baseline snapshot taken; compared against 20-minute play session for leaks
- [ ] No `RenderTexture` created per-frame without explicit `Release()` on the same frame

### Physics Sweep

- [ ] Layer Collision Matrix audited — irrelevant layer pairs disabled
- [ ] `Physics.autoSyncTransforms` set to false in physics-heavy scenes
- [ ] `Time.fixedDeltaTime` set to minimum required for gameplay fidelity (0.02–0.033 s)
- [ ] All `Physics.Raycast` hot-path calls replaced with `RaycastNonAlloc`
- [ ] Non-convex Mesh Colliders replaced with compound primitive colliders
- [ ] `Rigidbody.sleepThreshold` increased on static props and furniture
- [ ] `Rigidbody.interpolation` set to `Interpolate` on player character and camera targets
- [ ] Physics Profiler module checked: `Physics.Processing` within budget

### Networking Sweep

- [ ] Tick rate matched to game type and client update rate
- [ ] `NetworkVariable` mutations are change-driven, not per-frame
- [ ] Object visibility culling configured (`CheckObjectVisibility`)
- [ ] Bandwidth measured and within target for minimum spec connection
- [ ] No `ServerRpc` calls per frame (batched into per-tick structs)
- [ ] Position quantization enabled on `NetworkTransform` for bandwidth reduction

### Build and Cook Validation

- [ ] IL2CPP backend, .NET Standard 2.1, "Faster runtime" code gen selected
- [ ] Managed stripping at Medium or High; `link.xml` protecting all reflection-dependent code
- [ ] Build Report Inspector opened; largest assets identified and justified against budget
- [ ] Any asset > 50 MB in the build has a written rationale (streaming audio, large lightmap, etc.)
- [ ] Shader variant count logged (`log shader compilation` in Player Settings); variants > 2,000 investigated
- [ ] `ShaderVariantCollection.WarmUp()` called during loading screen for all commonly used materials
- [ ] Development Build disabled for Gold Master candidate build
- [ ] Final profile captured on minimum-spec hardware (not dev machine)
- [ ] `Application.BuildGUID` visible in game's credits/version overlay for QA identification
- [ ] All `asmdef` files in place; compile time verified against baseline
- [ ] Test Runner Performance Testing Extension baseline tests passing with no regression flags
- [ ] Build size compared against previous milestone; any increase > 10% investigated

---

## Top 30 Most Common Mistakes

| # | Mistake | Why it hurts | Fix | Era |
|---|---|---|---|---|
| 1 | `Camera.main` in `Update()` | Native boundary crossing per frame | Cache in `Start()` | All |
| 2 | `GetComponent<T>()` in `Update()` without caching | Scene traversal per frame | Cache in `Awake()` | All |
| 3 | `Instantiate` without pooling | GC pressure + CPU spike on spawn | `UnityEngine.Pool.ObjectPool<T>` | All |
| 4 | String concatenation in `Update()` | Allocates new string object per frame | `StringBuilder` or update-on-change only | All |
| 5 | LINQ in hot paths | Enumerator + intermediate collection allocations | Manual `for` loops | All |
| 6 | `Vector3 ==` for distance check (wrong semantics too) | Epsilon exact equality, not range check; `sqrt` cost | `(a - b).sqrMagnitude < threshold * threshold` | All |
| 7 | `new WaitForSeconds()` inside coroutine loop | Allocates heap object per iteration | `private static readonly WaitForSeconds Wait1s = new(1f)` | Pre-2020 |
| 8 | `Find` / `FindObjectOfType` / `FindGameObjectsWithTag` in tick | O(n) scene search per frame | Cache reference in `Awake()` or use event-based injection | All |
| 9 | `Animator.SetFloat("Name", val)` with strings in `Update()` | Internal string dictionary lookup per frame | `Animator.StringToHash` at init; pass int overloads | All |
| 10 | Layout Group on a UI element that updates every frame | `GetComponent` walk up transform hierarchy on dirty | Bake positions into anchors; avoid Layout Groups on dynamic elements | All |
| 11 | All Image components have Raycast Target = true by default | Graphic Raycaster iterates every enabled target on input | Disable Raycast Target on all non-interactive elements | All |
| 12 | `SetActive(true/false)` on a Canvas with many children | Full Canvas rebuild on activate/deactivate | Use `Canvas.enabled` or restructure | All |
| 13 | Read/Write Enabled on imported textures/meshes | Doubles memory (GPU copy + CPU copy) | Disable unless runtime pixel/vertex access required | All |
| 14 | Audio Clip "Decompress on Load" for long music files | Full decompressed PCM in RAM on load | Use Streaming load type for all music | All |
| 15 | `Animator.cullingMode` default `AlwaysAnimate` for off-screen NPCs | Full state machine evaluation regardless of visibility | Set `CullCompletely` for background characters | All |
| 16 | Mixed static and animating UI on one Canvas | Any change forces full Canvas rebuild | Split into static Canvas + dynamic Canvas | All |
| 17 | `MaterialPropertyBlock` breaking SRP Batcher | MPB opts renderer out of SRP Batcher, falls back to instancing or unoptimized draw calls | Use unique materials per variant; reserve MPB for explicit instancing paths | 2020-2022 LTS |
| 18 | Shader keyword variant explosion | 1,024 variants from 10 features; build time + memory | `shader_feature_local` for bake-time features; `IPreprocessShaders` for build-time stripping | All |
| 19 | Global keywords instead of local (`_local`) keywords | Global keyword space limited (~196 available); overflow causes silent fallback | Always use `shader_feature_local` / `multi_compile_local` | 2020-2022 LTS |
| 20 | Single Addressable bundle without dependency analysis | Shared assets duplicated across bundles → memory bloat | Run Analyze → Check Duplicate Bundle Dependencies | 2020-2022 LTS |
| 21 | Domain Reload enabled | 5–30 s iteration tax per Play press on large projects | Project Settings → Editor → Disable Domain Reload | 2019.3+ |
| 22 | Mono backend for shipping builds | JIT overhead, slower startup, weaker code stripping | Switch to IL2CPP for all shipping targets | All |
| 23 | LINQ `GroupBy`/`OrderBy` on dictionaries every frame | Multiple allocations + O(n log n) + enumerator boxing | Cache results; compute on change events, not per-frame | All |
| 24 | Coroutines never stopped on object destruction | Coroutine continues running on a destroyed object; NullReferenceException or worse | Stop coroutines in `OnDestroy` or use `destroyCancellationToken` (Unity 2022.2+) | All |
| 25 | `Animator.Rebind()` called in the update loop | Full Animator state rebuild; extremely expensive | Call only on rig change; never per-frame | All |
| 26 | `GameObject.SetActive` flicker-frame thrash | SetActive(false/true) in the same frame or alternate frames causes repeated full initialization | Restructure; use a state machine, not SetActive per-update | All |
| 27 | Shader Graph multi-compile keyword spam | Custom Function Nodes with conditional paths double variants if not scoped | Scope to `shader_feature_local`; wrap Custom Function Nodes in Sub Graphs with explicit keyword gating | 2020-2022 LTS |
| 28 | SRP Batcher disabled by Custom Function Node with non-deterministic output | SRP Batcher requires deterministic shader output to use cached constant buffers | Keep Custom Function Nodes deterministic; avoid state reads with non-constant results | 2020-2022 LTS |
| 29 | GPU Instancing not enabled on materials used with `DrawMesh*` APIs | `DrawMeshInstanced` / `DrawMeshInstancedIndirect` require `#pragma instancing_options` AND the material checkbox | Enable GPU Instancing on material + add instancing pragma | All |
| 30 | VFX Graph bounds set to Automatic | Disables culling entirely; every instance simulates every frame | Set Manual or Recorded bounds before shipping | All |

---

## Knobs and Settings Cheat Sheet

### Player Settings

| Setting | Options | Recommendation |
|---|---|---|
| Scripting Backend | Mono, IL2CPP | IL2CPP for shipping; Mono for development |
| IL2CPP Code Generation | Faster builds / Faster runtime | "Faster runtime" for shipping |
| API Compatibility Level | .NET Standard 2.1 / .NET Framework | .NET Standard 2.1 (smaller BCL, better stripping) |
| Managed Stripping Level | Disabled / Low / Medium / High | Medium (test) or High (with link.xml) |
| Graphics Jobs (Experimental) | Off / On | Off by default; test per-project |
| Multithreaded Rendering | On (default) | Keep On; disable only to see full render queue in Profiler |
| GPU Skinning | On / Off | On always where supported |

### Quality Settings

| Setting | Low | Medium | High | Ultra |
|---|---|---|---|---|
| VSync | Off | Off | On (optional) | On |
| Anti-Aliasing | Off/FXAA | 2× MSAA or TAA | TAA or STP | STP or DLSS/FSR |
| Shadow Quality | Soft 2×2 PCF | Soft 4×4 PCF | Soft PCF | PCF or PCSS |
| Shadow Distance | 60 m | 100 m | 150 m | 200 m+ |
| Cascade Count | 1 | 2 | 3 | 4 |
| Texture Quality | Half | 3/4 | Full | Full |
| LOD Bias | 0.5 | 0.7 | 1.0 | 1.5 |
| Pixel Light Count | 1 | 2 | 4 | Unlimited |

### URP Asset Key Knobs

| Setting | Recommendation |
|---|---|
| HDR | On (if Bloom used); Off otherwise |
| Render Scale | 1.0 baseline; 0.7–0.8 with STP (Unity 6+) |
| Anti-Aliasing (MSAA) | Off (use TAA/STP on High+); 2× on Medium |
| Main Light Shadow Resolution | 2048 for High; 1024 for Medium |
| Cascade Count | See Quality Settings table |
| Soft Shadows | On for High+; Off for Low |
| Additional Light Shadow Atlas | 2048 for High; disable on Low |
| GPU Resident Drawer | Instanced Drawing (Unity 6+, Forward+) |
| STP Upscaling | On at render scale < 1.0 (Unity 6+) |
| Forward+ | Enable when using GPU Resident Drawer |

### HDRP Frame Settings

| Setting | Performance toggle |
|---|---|
| Ray Tracing | Off for low/medium tiers |
| Volumetric Fog | Depth Extent, Balance slider, Directional Only |
| Decal Count | `Max Decal on Screen` cap |
| SSGI / SSAO | Disable for low tier |
| Motion Blur | Disable for low/medium |
| Screen Space Reflections | Toggle; fall back to Reflection Probes |
| Bloom | On for high+; Off for low |
| Depth of Field | Off for low; Physical DOF only on Ultra |

### Build Profile Toggles (Unity 2023.1+)

| Profile | Scripting Backend | Stripping | Dev Build | Autoconnect |
|---|---|---|---|---|
| Dev-Debug | Mono | Disabled | On | On |
| QA-Release | IL2CPP | Medium | On | Off |
| Gold-Master | IL2CPP | High | Off | Off |
| CI-Automated | IL2CPP | Medium | On | Off |

### Quality Scalability Recommendations

```ini
[Low — Target: 720p/30 FPS, 5-year-old integrated graphics]
QualitySettings.shadows = ShadowQuality.HardOnly
QualitySettings.shadowDistance = 60
QualitySettings.shadowCascades = 1
QualitySettings.globalTextureMipmapLimit = 1
QualitySettings.antiAliasing = 0
QualitySettings.lodBias = 0.5
URP Render Scale = 0.7 (no STP)
HDR = Off

[Medium — Target: 1080p/60 FPS, GTX 1060 class]
QualitySettings.shadows = ShadowQuality.All (PCF 2x2)
QualitySettings.shadowDistance = 100
QualitySettings.shadowCascades = 2
QualitySettings.antiAliasing = 2
QualitySettings.lodBias = 0.7
URP Render Scale = 0.85
HDR = On

[High — Target: 1440p/60 FPS, RTX 2080 class]
QualitySettings.shadowDistance = 150
QualitySettings.shadowCascades = 3
QualitySettings.antiAliasing = 0 (TAA/STP)
QualitySettings.lodBias = 1.0
URP Render Scale = 1.0 (or 0.85 with STP)
HDR = On
SSAO = Medium

[Ultra — Target: 4K/60 FPS or 1440p/120 FPS]
QualitySettings.shadowDistance = 200
QualitySettings.shadowCascades = 4
URP Render Scale = 1.0 + DLSS/FSR/STP Quality mode
HDR = On
All effects On
```

### Physics Project Settings Reference

| Setting | Location | Low tier | High tier |
|---|---|---|---|
| `fixedDeltaTime` | Project Settings → Time | 0.033 s (30 Hz) | 0.02 s (50 Hz) |
| `maximumAllowedTimestep` | Project Settings → Time | 0.033 s | 0.1 s (default) |
| `sleepThreshold` (global) | Project Settings → Physics | 0.1 | 0.005 (default) |
| `defaultContactOffset` | Project Settings → Physics | 0.02 | 0.01 (default) |
| `autoSyncTransforms` | Project Settings → Physics | false | false |
| Solver Type | Project Settings → Physics | Projected Gauss-Seidel | Temporal Gauss-Seidel (Unity 2022+) |
| Broadphase Type | Project Settings → Physics | SAP (Sweep and Prune) | MBP (Multi-Box Pruning, large open worlds) |

**Solver Type note:** Temporal Gauss-Seidel (TGS, Unity 2022+) provides more stable stacking and joint constraints at the same iteration count as Projected Gauss-Seidel (PGS). TGS is more expensive per-iteration but often requires fewer iterations for equivalent quality, resulting in a net neutral or slight win for complex stacking scenarios.

**Broadphase Type note:** Multi-Box Pruning (MBP) is preferred for large open worlds where objects span a wide spatial distribution. Sweep and Prune (SAP) is faster for scenes where objects cluster in a small area.

### Audio Project Settings Reference

| Setting | Location | Recommendation |
|---|---|---|
| DSP Buffer Size | Project Settings → Audio | Best Latency for input-sensitive games; Default for most titles |
| Max Virtual Voices | Project Settings → Audio | 512 (default); reduce to 256 if audio CPU cost is high |
| Real Voices | Project Settings → Audio | 32 (default); increase only if voice-stealing is audible |
| Spatializer Plugin | Project Settings → Audio | Built-in (default); Steam Audio for physics-based occlusion |
| Sample Rate | Project Settings → Audio | 44100 Hz default; 22050 Hz acceptable for most game SFX |

### Editor Performance Settings Reference **[All versions]**

These settings have zero shipping build impact but dramatically affect daily iteration speed:

| Setting | Location | Recommendation |
|---|---|---|
| Disable Domain Reload | Project Settings → Editor → Enter Play Mode | Enable immediately on all projects |
| Disable Scene Reload | Project Settings → Editor → Enter Play Mode | Enable; requires stateless startup code |
| Import Worker Count | Preferences → General | Leave at default (auto); increase on machines with >16 cores |
| Script Changes While Playing | Preferences → External Tools | Recompile and Continue Playing (not Stop Playing and Recompile) |
| Preferred Version Control | Project Settings → Version Control | Visible Meta Files (never Hidden Meta Files) |

---

## Unity ↔ UE Concept Bridge

This guide's companion document is the UE4/UE5 Optimization Guide. If you use both engines or are migrating, these equivalences prevent re-learning the same concepts under different names.

| Unity Concept | UE Equivalent | Notes |
|---|---|---|
| SRP Batcher | PSO (Pipeline State Object) caching | Both reduce per-draw-call GPU state setup overhead. SRP Batcher is more automatic; PSO requires explicit pipeline compilation. |
| GPU Resident Drawer (Unity 6+) | Nanite clustering / HLOD | Both reduce draw call count via GPU-driven instance batching. UE5 Nanite is more ambitious (full virtualized geometry); Unity GRD is an instancing layer. |
| Render Graph (URP Unity 6+) | RDG (Render Dependency Graph, UE4+) | Both use declarative pass registration with automatic resource lifetime and pass culling. Unity's is newer and simpler; UE's RDG is battle-tested across all console generations. |
| Shader Graph | Material Editor (UE) | Both are visual, node-based shader authoring tools. Unity Shader Graph generates HLSL; UE Material Editor generates HLSL/GLSL per platform. |
| `shader_feature_local` / `multi_compile_local` | Material Static Switch Parameters | Both select shader paths at compile time without runtime branching overhead. |
| Addressables | UE Asset Manager + Primary Asset Labels | Both provide reference-counted async asset loading over a bundle/pak layer. Addressables is simpler to configure; UE Asset Manager is more deeply integrated with streaming. |
| Entity Component System (ECS) | Mass AI / Data-Oriented Entities | Both are cache-friendly entity-component architectures for high entity counts. Unity's is more general-purpose; UE's Mass system is specifically targeted at AI crowd simulations. |
| Burst Compiler | ISPC / Multithreaded execution in UE | Both generate SIMD-optimized code for data-parallel workloads. Burst is more accessible (C# + `[BurstCompile]`); ISPC requires a separate language. |
| Light Probes + APV | Distance Field Ambient Occlusion + Lumen (indirect) | Unity APV ≈ UE5 Lumen's indirect lighting cache conceptually. Both provide per-pixel GI for dynamic objects. Lumen requires no baking but is GPU-heavier; APV is baked but near-zero runtime cost. |
| Progressive Lightmapper | CPU Lightmass (UE4) / GPU Lightmass (UE4.26+) | Both are path-tracing bakers. UE GPU Lightmass is broadly comparable to Unity's Progressive GPU Lightmapper in workflow. |
| STP (Spatial-Temporal Post-Processing) | TSR (Temporal Super Resolution) | Both are software temporal upsamplers built into the engine, requiring no vendor SDK. TSR (UE5) is more mature with wider platform support; STP (Unity 6+) is newer but compute-only. |
| DLSS / FSR / XeSS plugins | DLSS / FSR / XeSS plugins | Identical vendor technology; both engines require separate plugin/SDK installation. UE has more polished DLSS integration via the NVIDIA DLSS for Unreal plugin. |
| LOD Group + LOD Bias | LOD system + `r.StaticMeshLODDistanceScale` | Conceptually identical. Unity uses screen-space coverage percentages; UE uses distance-based LOD transitions scaled by a console variable. |
| Occlusion Culling (baked) | Precomputed Visibility (UE4) | Both precompute per-cell visibility at edit time for closed environments. UE5 with Nanite largely eliminates the need for PVS; Unity has added GPU occlusion culling (Unity 6+) as an alternative. |
| VFX Graph (GPU particles) | Niagara GPU simulation | Both are compute-shader particle simulators with a visual graph authoring interface. Niagara has broader platform support and more advanced simulation modules; VFX Graph requires compute shader capable hardware. |
| Netcode for GameObjects | Native replication (AGameMode/APlayerController) | Both are server-authoritative networked replication systems. UE's native replication is more mature and deeply integrated with the engine's actor lifecycle. |
| `NetworkVariable<T>` | Replicated UPROPERTY | Both synchronize state from server to clients. UE's replicated properties have more granular RepNotify controls; NGO's `NetworkVariable` is simpler but less flexible. |
| Unity Physics (DOTS) | Chaos Physics (UE5) | Both are data-oriented physics systems written to run in parallel jobs. Chaos is more stable in production as of 2024; Unity Physics is simpler but less feature-complete. |

---

## Version Migration Notes

For teams moving between major Unity versions, these are the performance-impacting breaking changes that most commonly cause regressions.

### Migrating from Built-in RP to URP **[Pre-2020] → [2020-2022 LTS]**

This is the highest-impact migration in Unity's history for most indie teams.

- **Surface Shaders do not exist in URP.** Rewrite all Surface Shaders as Unlit or Lit ShaderLab programs using URP's ShaderLibrary includes, or recreate in Shader Graph. This is the largest migration cost.
- **Post-Processing Stack v2 is replaced by URP's Volume system.** Remove `com.unity.postprocessing`; recreate effects as Volume Overrides in the Universal Renderer.
- **All custom `CommandBuffer` injections must be rewritten** as `ScriptableRendererFeature` + `ScriptableRenderPass` (pre-Unity 6) or Render Graph (Unity 6+).
- **SRP Batcher is automatically active in URP.** Ensure all shaders have `CBUFFER_START(UnityPerMaterial)` blocks or batching will silently fall back.
- **Dynamic Batching**: Recommended to disable in URP. SRP Batcher handles the same use cases more efficiently. [Unity draw call optimization](https://docs.unity3d.com/cn/2021.3/Manual/optimizing-draw-calls.html)
- **GPU Instancing vs SRP Batcher**: You cannot use both simultaneously on the same renderer. Decide per use case: SRP Batcher for heterogeneous static scenes; GPU Instancing for thousands of identical dynamic objects.
- Reference: [Migrating from Built-in RP to URP](https://docs.unity.cn/6000.6/Documentation/Manual/urp/upgrading-from-birp.html)

### Migrating from Unity 2020/2021 to Unity 2022 LTS **[2020-2022 LTS era internal]**

- **DOTS Entities 1.0** was released for Unity 2022.2. The entire ECS API changed: `Entities.ForEach` deprecated, `ISystem` introduced, baking system replaced conversion workflow. ECS projects from Unity 2020/2021 require significant migration. [DOTS migration guide](https://docs.unity3d.com/Packages/com.unity.entities@1.0/manual/)
- **UI Toolkit** became production-ready for runtime UIs in Unity 2022 LTS. The IMGUI backend no longer receives feature investment for runtime UI. Toolkit-based UIs in 2020/2021 may need API updates.
- **GraphicsFormat API** changed for some render texture formats between 2021 and 2022. RenderTexture creation using deprecated format enums will produce console warnings.
- **Hybrid Renderer V2 renamed to Entities Graphics** (`com.unity.entities.graphics`). The package name changed; update `manifest.json`.

### Migrating to Unity 6 **[2020-2022 LTS] → [Unity 6+]**

- **Render Graph is mandatory in URP.** All `ScriptableRenderPass.Execute()` overrides must be migrated to `RecordRenderGraph()`. Unity 6.0 ships a compatibility mode (`Compatibility Mode` toggle in the Universal Renderer asset) that keeps old code working, but it is removed in a later release. Migrate immediately. [Render Graph introduction](https://docs.unity3d.com/6000.3/Documentation/Manual/urp/render-graph-introduction.html)
- **GPU Resident Drawer** is opt-in in URP, on-by-default in HDRP. If Static Batching was your primary batching strategy, disable it and switch to GRD for GPU-side instancing.
- **Adaptive Probe Volumes (APV)** become the recommended default for new projects. Existing projects using Light Probe Groups still work but miss APV features (per-pixel sampling, sky occlusion, scenario blending).
- **Built-in RP is deprecated in Unity 6.5.** Not removed yet, but no new features. If your project uses Built-in RP, begin URP migration planning. [BIRP deprecation notice](https://www.maxkillstudios.com/learn/birp-deprecated-migrate-urp-or-wait)
- **Mesh LOD** automatic generation added in Unity 6.2 — re-import meshes to take advantage of shared-vertex-buffer LODs.
- **`Awaitable`** (introduced Unity 2023.1, part of the Unity 6 lifecycle) replaces coroutine-heavy async patterns. Gradually migrate long-running coroutines to `Awaitable` where value return or cancellation is needed.
- **`destroyCancellationToken`** available on all `MonoBehaviour` from Unity 2022.2 — use it to automatically cancel async operations when the object is destroyed.

### Performance Regressions to Watch After Unity Version Upgrades

Every major version upgrade should be followed by a Profile Analyzer comparison against the pre-upgrade baseline. Common regression patterns:

| Symptom | Likely cause | Investigation step |
|---|---|---|
| Higher draw call count after upgrade | SRP Batcher compatibility broken by new Unity shader changes | Frame Debugger → SRP Batcher batch breakdown |
| GC spikes introduced after upgrade | Unity internal API change allocating where it didn't before | CPU Hierarchy → sort by GC Alloc; look for new Unity engine entries |
| Shader compilation stutter at first use | New shader variants generated by updated URP/HDRP | Re-run `ShaderVariantCollection.WarmUp()` with updated collection |
| Physics FixedUpdate over budget | Changed default physics settings between versions | Compare Project Settings → Physics between version snapshots |
| Memory increase | Texture format defaults changed, or new Unity assets auto-imported | Memory Profiler snapshot diff; check Textures category |

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

---

This guide covers Unity 2018/2019 (Pre-2020 era), Unity 2020–2022 LTS, and Unity 6 (October 2024 release, 6000.x). All API references verified against official Unity documentation at time of writing. Era tags indicate the first version where a feature became stable and production-recommended, not necessarily where it was first introduced in preview.
