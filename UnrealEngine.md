# UE4 / UE5 Optimization Guide

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

You can find those [HERE](https://github.com/GameDevGrzesiek/OptimizationBible/blob/main/Definitions.md)

---

## Tools  

You can find them [HERE](https://github.com/GameDevGrzesiek/OptimizationBible/blob/main/UnrealEngineTools.md)

---

## Guidelines per Specialization

### General Tips **[UE4 + UE5]**

- Never optimize without profiling data. Guessing is slower and less reliable than measuring.
- The 80/20 rule applies: 20% of systems cause 80% of frame budget. Find that 20%.
- Scalability groups (`sg.ResolutionQuality`, `sg.ShadowQuality`, etc.) are your primary tools for broad platform targeting. Define scalability profiles in `BaseScalability.ini` per quality tier.
- Console variables (`CVar`) are your primary tuning interface. Expose per-scalability-group CVars in `BaseScalability.ini` rather than hardcoding values.
- Use Data Assets and Data Tables to externalize configuration. Designers can tune without recompilation.
- `FAutoConsoleVariableRef` enables any parameter to be live-tuned from the console or `.ini` without recompilation — prefer it over hardcoded constants for tunable systems.

---

### Code and Mechanics (Programmers / Gameplay Engineers) **[UE4 + UE5]**

Gameplay C++ code runs on the Game Thread by default. Every millisecond spent here is a millisecond the renderer waits.

**Common pitfalls:**

- **Raw `UObject*` without `UPROPERTY`** — invisible to GC, will become a dangling pointer when the object is collected. Always use `UPROPERTY()` or `TObjectPtr<>` (UE5). **[UE5 only]**: With incremental GC in 5.4+, raw pointer UPROPERTY members may cause premature collection.
- **`TWeakObjectPtr::IsValid()` followed by `Get()`** — this checks validity twice (double cache miss into `GUObjectArray`). Use `if (UObject* Obj = Weak.Get()) { ... }` for a single check.
- **`std::shared_ptr<UObject>`** — GC has no knowledge of shared_ptr ref counts. Use `UPROPERTY` or `TStrongObjectPtr` for UObject lifetime. `TSharedPtr` is for non-UObject types only.
- **`FName` constructed from string literals in hot paths** — `FName(TEXT("spine_01"))` acquires a thread lock on the global name table every call. Cache as `static const FName`.
- **Constructing or loading assets in constructors** — constructor runs for the CDO; all instances are copies of the CDO. Never put runtime logic in constructors.
- **Changing `UPROPERTY` or `CreateDefaultSubobject` names between Live Coding sessions** — corrupts Blueprint assets. Requires full editor restart.
- **`this` captured in lambda delegates without weak protection** — if the actor is GC'd before the lambda fires, the capture is a dangling pointer. Use `AddWeakLambda` or `MakeWeakObjectPtr`.
- **`!= nullptr` vs `IsValid()` on UObjects** — a destroyed actor passes `!= nullptr` but fails `IsValid()`. Always use `IsValid()` for destroyed-object guards.

**Recommended practices:**

- Use `TObjectPtr<T>` for all UPROPERTY members in UE5. **[UE5 only]** Zero shipping cost, editor access tracking, incremental GC compatibility.
- Pre-allocate `TArray` before bulk inserts: `Array.Reserve(ExpectedCount)`.
- Use `Array.Reset()` instead of `Array.Empty()` when you intend to refill immediately — `Reset()` preserves the heap allocation (sets Num=0, leaves Max unchanged), while `Empty()` frees and reallocates. One allocation vs zero allocations per frame.
- Use `Array.RemoveAtSwap(Index)` instead of `RemoveAt(Index)` when order does not matter. `RemoveAtSwap` is O(1); `RemoveAt` is O(n).
- Use `TMap<FName, V>` instead of `TMap<FString, V>` for identifier maps. FName comparison is an O(1) integer compare; FString is O(n).
- Use `FFastArraySerializer` for arrays replicated over the network — it sends delta updates (changed elements only) instead of the full array every time any element changes.
- Push Model replication: use `MARK_PROPERTY_DIRTY_FROM_NAME` and `bIsPushBased = true` in `GetLifetimeReplicatedProps`. Properties only replicate when dirty, saving per-frame polling on the server. [UE4.25+]
- Use `UE::Tasks` (UE5) or `AsyncTask`/`ParallelFor` to move work off the Game Thread. Never read or write UObject properties from worker threads without `FGCScopeGuard`.
- Use `TStrongObjectPtr` to safely pin UObjects against GC from non-game-thread contexts **[UE5.5+: lighter ref-counted implementation]**.
- Gate editor-only code with `#if WITH_EDITORONLY_DATA` (data fields) and `#if WITH_EDITOR` (functions).
- Prefer `FAutoConsoleVariableRef` for tunable parameters — live-tunable from the console or `.ini` without recompilation. For thread-safe reads from worker threads, use `ECVF_RenderThreadSafe`.
- `UE_LOG` format strings evaluate even in Development — wrap expensive log output in `#if !UE_BUILD_SHIPPING`.

**Threading and async systems [UE5 only]:**

```cpp
// UE::Tasks — preferred modern async API:
UE::Tasks::Launch(UE_SOURCE_LOCATION, []() {
    // background work — no UObject access here
}, UE::Tasks::ETaskPriority::BackgroundNormal);

// FGCScopeGuard — prevents GC during worker UObject access:
{
    FGCScopeGuard GCGuard;
    MyUObject->DoReadOnlyThing();
}

// TStrongObjectPtr for thread-safe UObject lifetime pinning:
TStrongObjectPtr<UMyObject> PinnedObject(MyObject);
AsyncTask(ENamedThreads::AnyBackgroundThreadNormalTask, [PinnedObject]() {
    PinnedObject->DoWork();
});

// Marshal results back to the GameThread:
AsyncTask(ENamedThreads::GameThread, [Result]() {
    // Apply results to UObjects here
});
```

| System | Best For | Notes |
|---|---|---|
| `UE::Tasks` (UE5 new API) | Dependent task graphs, modern C++ | Cleaner API; same backend as TaskGraph |
| `TaskGraph` (`FFunctionGraphTask`) | Legacy code, dependent graphs | Being replaced by `UE::Tasks` |
| `AsyncTask` / `Async()` | Fire-and-forget background work | `EAsyncExecution::Thread` = dedicated OS thread |
| `FRunnable` / `FRunnableThread` | Long-lived, persistent background threads | Higher overhead; prefer for continuous systems |
| `ParallelFor` | Data-parallel loops | Avoid TMap writes inside the body |

Use `FCriticalSection` + `FScopeLock` (not `std::mutex`). Use `FRWLock` when reads significantly outnumber writes.

**FAutoConsoleVariableRef pattern:**
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

**Push Model replication code:**
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

**Lambda delegate safety patterns:**
```cpp
// DANGEROUS: 'this' captured raw in a timer lambda:
GetWorldTimerManager().SetTimer(Handle, [this]() { DoThing(); }, 1.f, false);

// SAFE — AddWeakLambda:
SomeDelegate.AddWeakLambda(this, [this]() { DoThing(); });

// SAFE — explicit weak pointer:
auto WeakThis = MakeWeakObjectPtr(this);
GetWorldTimerManager().SetTimer(Handle, [WeakThis]() {
    if (WeakThis.IsValid()) WeakThis->DoThing();
}, 1.f, false);
```

**TWeakObjectPtr hot-path optimization:**
```cpp
// BAD: checks validity 3 times:
if (WeakPtr.IsValid()) { UObject* Obj = WeakPtr.Get(); if (IsValid(Obj)) ... }

// GOOD: single dereference with null check:
if (UObject* Obj = WeakPtr.Get()) { Obj->Foo(); Obj->Bar(); }
```

**Lesser-known tricks:**

- `TInlineAllocator<N>` keeps small arrays on the stack. Pass to functions via `TArrayView<T>` to preserve type compatibility.
- `FObjectInitializer::DoNotCreateDefaultSubobject(TEXT("CompName"))` in derived class constructors suppresses a parent's default subobject.
- GC clustering (`gc.AssetClusteringEnabled 1`) can cut GC marking time by 50%+ for clustered assets. Enable BP clustering in Project Settings > Engine > Garbage Collection.
- `tick.AllowBatchedTicks` **[UE5.5+]** — groups similar tick functions and dispatches as batches to the Task Graph, reducing per-tick overhead.
- `GameplayDebugger` module — overlay runtime debug data in-game without polluting shipping code. Gate with `#if WITH_GAMEPLAY_DEBUGGER`.
- `MarkPendingKill` API is deprecated in UE5. Use `MarkAsGarbage()` and test with `IsValid()` or `IsGarbage()`.
- `FStringView` (UE5): a non-owning view over an existing string buffer. Use it as the parameter type in functions to prevent implicit `FString` copies.
- Keep the live UObject count below ~200k as a good general practice. `gc.CreateGCClusters 1` on data assets.

**Tools for this role:**
`stat unit`, Insights (cpu,frame), `Memreport -full`, Memory Insights

**CVars cheat sheet:**

| CVar | Default | Purpose | Engine |
|---|---|---|---|
| `gc.TimeBetweenPurgingPendingKillObjects` | 60 | Seconds between GC passes | UE4 + UE5 |
| `gc.MaxObjectsNotConsideredByGC` | 0 | Objects above this index skipped in marking | UE4 + UE5 |
| `gc.AssetClusteringEnabled` | 1 | GC clustering for assets | UE4 + UE5 |
| `tick.AllowBatchedTicks` | 0 | Batch similar tick functions | UE5.5+ |
| `net.Iris.UseIrisReplication` | 0 | Enable Iris replication system | UE5.4+ |

---

### Blueprint Scripters **[UE4 + UE5]**

Every Blueprint node is a bytecode instruction interpreted by the VM. The VM overhead is real but manageable — 300 nodes executing once per event is often cheaper than 3 nodes executing every frame. Profile before rewriting Blueprints to C++.

**Common pitfalls:**

- **Tick enabled on every actor by default** — "Start with Tick Enabled" is checked by default. 200 actors with empty ticks = 200 per-frame VM dispatches. Uncheck in Class Defaults for every actor that doesn't need per-frame updates.
- **`Get All Actors Of Class` called in Tick or frequently** — iterates the entire World actor list, building a new `TArray` on every call. Catastrophically expensive. Use a manager/subsystem registration pattern instead.
- **Hard reference casts everywhere** — `Cast To BP_PlayerCharacter` placed in a UI widget loads the entire player character class (and every asset it references) into memory when the widget loads. One stray cast can add hundreds of MB of unexpected memory.
- **Pure functions wired to multiple nodes** — a pure function (green node, no exec pin) re-evaluates for every output consumer. Expensive computation wired to 3 nodes runs 3 times. Convert to impure (non-pure) and cache the result.
- **`ForEachLoop` without break for search** — always iterates the full array. Use `ForEachLoopWithBreak` and wire the Break pin.
- **Spawning actors in Construction Script** — runs every time any property changes in the editor. Orphaned actors accumulate. Use Child Actor Components or spawn in BeginPlay.
- **Missing `Replicates = true`** in Class Defaults for networked actors — no variables replicate, no RPCs execute on remote machines.
- **`Make Array` inside Event Tick** — heap allocation every frame, GC pressure. Pre-allocate as a member variable.
- **`Delay` for cancellable timed logic** — cannot be cancelled. Use `Set Timer by Event` with a stored handle.
- **`Sequence` node misused for deferred work** — all outputs fire synchronously in the same frame; it does not spread work over time.

**Recommended practices:**

- Disable tick by default in Class Defaults. Enable via `Set Actor Tick Enabled` only when needed, disable again when no longer needed. The correct C++ initialization sequence:

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

- Set `Tick Interval (secs)` for actors that need periodic but not per-frame updates (AI checks, regeneration, proximity queries). 0.1s = 10 ticks/second. Don't set below 0.05s — may fire multiple times per frame at high framerates ([CBgameDev tick guide](https://www.cbgamedev.com/blog/quick-dev-tip-74-ue4-ue5-optimising-tick-rate)).
- Replace Tick polling with Event Dispatchers. A dispatcher fires only when state changes; a Tick check fires every frame regardless. This is architecturally the Observer pattern.
- Event mechanism selection:

| Mechanism | Direction | Coupling | Use Case |
|---|---|---|---|
| Event Dispatcher | One → Many (broadcast) | Loose | Score updates, player death, level events |
| Blueprint Interface (BPI) | One → One/Many (message) | Loose | "Can this actor be interacted with?" |
| Direct Cast | One → One | Tight (hard reference) | Internal communication within the same module |

- Use Blueprint Interfaces (BPI) for loose coupling instead of hard casts. **Important nuance**: if the interface function parameter type is a specific Blueprint class, that class still loads into memory. Use base types (Actor, Pawn) as parameter types to maintain the memory escape.
- Cache costly Blueprint operations (component gets, cast results) in member variables. One cast in BeginPlay is fine. A cast in Tick is not.
- Use `Validated Get` (right-click any variable → Convert to Validated Get) instead of the Is Valid + Branch + Get triple pattern. Same result, 3 fewer nodes, one `Is Valid` and `Is Not Valid` exec output.
- `Set Timer by Event` instead of `Delay` for cancellable timed logic. Delay cannot be cancelled; if the actor is destroyed mid-delay, the resumed execution crashes on a dead object.
- Use **Soft Object References** (`TSoftObjectPtr`) for assets that should load on demand. Combine with `Async Load Asset` and wire the result into a Cast. The cast is only reached after successful load — no premature memory inflation.
- Use `Size Map` (right-click asset → Size Map) regularly to audit reference footprint. Run it on UI Blueprints and GameInstance — these are the most common culprits for unexpected memory chains ([Tom Looman optimization talk](https://tomlooman.com/unreal-engine-optimization-talk/)).
- **Blueprint Nativization is gone in UE5.** **[Deprecated in UE5]**: Removed in UE5.0. The modern alternative is C++ Blueprint Function Libraries (`UFUNCTION(BlueprintCallable)`) for hot computation. Epic's benchmarks show C++ tight loops run ~800× faster than equivalent Blueprint loops for math workloads ([Tom Looman benchmarks](https://www.youtube.com/watch?v=Z5pKkBNEyc0)).
- Use `UGameInstanceSubsystem` for global events and manager state. Persists across level transitions; avoids `Get All Actors Of Class` for manager lookups. Place global game events (currency change, pause) as Event Dispatchers on a `UGameInstanceSubsystem` — any Blueprint can bind without Tick and survives level transitions ([Global EventDispatchers](https://forums.unrealengine.com/t/global-eventdispatchers-in-gameinstance/485353)).
- Mark DataTable rows as `Primary Assets` and load via Asset Manager. Enables async loading and bundle-based streaming (load only the "UI" bundle for shop menus, full "Actor" bundle when spawning) ([Tom Looman Asset Manager guide](https://tomlooman.com/unreal-engine-asset-manager-async-loading/)).

**Actor Dormancy — an underrated multiplayer optimization [UE4 + UE5]:**

Without dormancy: ~15 ms overhead per actor, 99.3% waste rate. With `DormantAll`: 0.13 ms, zero waste ([Reddit UE5 dormancy benchmark](https://www.reddit.com/r/UnrealEngine5/comments/1lzi6xg/networking_optimization_in_unreal_engine_5_with/)). For static or rarely-changing actors (barrels, furniture, world props), dormancy eliminates the constant replication overhead.

```
DORM_Never        — always replicates (default)
DORM_DormantAll   — dormant to all connections; call FlushNetDormancy() when state changes
DORM_DormantPartial — per-connection dormancy control
```

Blueprint nodes: `Set Actor Net Dormancy`, `Flush Net Dormancy`.

**Tick Groups:** if Actor B reads a position set by Actor A, and both are in the same tick group, order is non-deterministic. Use `Add Tick Prerequisite Actor` sparingly — prerequisites trigger a TArray sort every frame in the worst case. Prefer assigning different Tick Groups over a web of prerequisites ([Epic Forums: Tick Group vs Tick Prerequisite](https://forums.unrealengine.com/t/tick-group-vs-tick-prerequisite/1728813)).

UE5.5 adds the `tick.AllowBatchedTicks` CVar — when enabled, the engine groups similar tick functions and dispatches them to the Task Graph as batches, reducing per-tick overhead for actors with many instances ([Tom Looman — UE 5.5 Performance Highlights](https://tomlooman.com/unreal-engine-5-5-performance-highlights/)).

**Casting pitfall — the most important memory concept in Blueprint development:**

When you place `Cast To BP_Enemy` anywhere in a Blueprint graph, the VM reads the entire `BP_Enemy` class — including all of its hard-referenced assets — into memory at the time the owning Blueprint loads. This happens even if the cast branch never executes at runtime. A single `Cast To BP_PlayerCharacter` in a UI widget means the entire character class (and everything it references) is loaded when the widget loads ([Intax Blueprint VM performance guide](https://intaxwashere.github.io/blueprint-performance/)).

Soft Object References: a `Soft Class Reference to BP_Enemy` variable stores only the asset path — nothing is loaded until explicitly resolved. Pitfall: if you call `Load Asset` and wire the result into `Cast To BP_Enemy`, the VM will still load `BP_Enemy` at Blueprint compile time. Escape: use a lighter base class for the soft reference and cast to the specific type only after the async load completes.

**GC and Construction Script rules:**

The Construction Script runs on every property change in the Details panel, every time an actor is moved in the editor, and at level load time. What not to do in the Construction Script:
- Spawn actors (use Child Actor Components instead)
- Expensive async operations — they block the editor thread
- Fetch references to other actors — they may not exist when the CS runs at level load
- Modify level state — the CS has no guaranteed execution order relative to other actors

**Lesser-known tricks:**

- `Instance Editable + Expose on Spawn` on a variable makes it an input pin on `Spawn Actor from Class` — eliminates post-spawn setter chains.
- `Window > Find in Blueprints` provides project-wide search. In UE5.4+, right-click a function call → Find References for exact call-site discovery.
- `Tick Prerequisites` (`Add Tick Prerequisite Actor`) enforce actor ordering within a tick group, but trigger a TArray sort every frame in the worst case. Prefer assigning different Tick Groups over a web of prerequisites.
- Blueprint diff tool: right-click Blueprint → Revision Control → Diff Against Depot. Binary `.uasset` files cannot be diffed with standard text tools ([Kokku Games Blueprint diff guide](https://kokkugames.com/tutorial-stop-guessing-what-changed-in-your-blueprintsgit-blueprint-diff-inside-unreal-engine/)).
- Editor Utility Widgets (EUW) run Blueprint logic in the editor only. Use for batch operations, naming convention validation, and procedural level setup — without any runtime cost.
- `Get Class Defaults` node accesses CDO data without constructing an instance.
- Adaptive Net Update Frequency: `net.UseAdaptiveNetUpdateFrequency 1` — when enabled, the engine dynamically lowers the update rate to `MinNetUpdateFrequency` when no properties have changed ([Matt Gibson's replication settings guide](https://mattgibson.dev/blog/unreal-replication-settings)).

**Tools for this role:**
`stat blueprints`, `stat unit`, Insights (cpu,frame), Size Map, Blueprint Profiler (Session Frontend, legacy)

---

### Level Design / Environment Art **[UE4 + UE5 unless tagged]**

Level design decisions — geometry placement, lighting configuration, streaming setup — have the broadest performance impact of any discipline because they affect nearly every other system simultaneously.

**Common pitfalls:**

- **Nanite enabled on simple meshes** **[UE5 only]** — Nanite clusters geometry for micro-polygon rendering. Meshes with fewer than ~300 triangles pay the cluster overhead without sufficient geometry to amortize it. In production tests, disabling Nanite on a handful of simple meshes yielded a ~3 ms gain with zero visual difference ([r/UnrealEngine5, 2025](https://www.reddit.com/r/UnrealEngine5/comments/1ot0ms4/nanite_warning_lower_performance_with_simples/)).
- **Nanite + Masked Material + WPO on foliage** **[UE5 only]** — forces Programmable Rasterizer (software path), 2–4× more expensive than opaque Nanite. Disabling WPO shadow evaluation per-mesh can reduce shadow depth cost from 8 ms to 3 ms in foliage-heavy scenes ([StraySpark VSM blog](https://www.strayspark.studio/blog/virtual-shadow-map-optimization-open-worlds-ue5-7)).
- **Nanite overdraw from dense overlapping geometry** **[UE5 only]** — When geometry layers overlap densely (e.g. thick foliage, tightly packed rocks), Nanite renders all overlapping triangles. Visible as white-to-yellow areas in the `r.Nanite.Visualize Overdraw` mode ([Nanite for Artists | GDC 2024](https://www.youtube.com/watch?v=eoxYceDfKEM)).
- **Nanite Fallback Mesh at default `Fallback Relative Error = 0`** **[UE5 only]** — the fallback is identical to the source mesh. In projects with many unique meshes, fallback meshes can occupy 100–400 MB of VRAM ([Epic Forums, 2025](https://forums.unrealengine.com/t/nanite-fallback-mesh-buffers-vram-residence/2563974)).
- **VSM Page Pool too small for open world** **[UE5 only]** — default 4096 pages (256 MB) overflows in large open worlds, causing shadow stippling artifacts. Increase to `r.Shadow.Virtual.MaxPhysicalPages=8192` for open world PC/console targets.
- **HLOD left at "Lowest Available LOD" for landscape** **[UE5 only]** — produces a visually degraded gray blob. Set Specific LOD = 4–5 in World Settings > HLOD Setups.
- **Auto-Save with OFPA active** **[UE5 only]** — One-File-Per-Actor generates thousands of file changes per Auto-Save in large levels. Disable Auto-Save (Editor Preferences > Loading & Saving) and save manually.
- **Too many Point Lights with Cast Shadows** — each local VSM light maintains its own shadow pages. Dozens of cast-shadow point lights = instant page pool overflow and performance collapse.
- **Cull Distance Volumes absent in dense interiors** — without explicit cull distances, small props render at any distance. CPU-side culling is nearly free; not using it is a missed optimization.
- **Monolithic building meshes** **[UE5 only]** — a single "entire building" mesh generates only exterior Lumen Cards. Interior receives no GI. Build modularly.

**Recommended practices:**

**Nanite tuning [UE5 only]:**
- Use Nanite for hero props, architecture, terrain, and rocky cliffs — not for simple flat planes, small cubes, or any mesh below ~300 triangles.
- Tune `r.Nanite.MaxPixelsPerEdge 2` on medium settings and `4` on low settings — large gains with minimal visual regression ([Intel UE5 Optimization Guide Ch.2](https://www.intel.com/content/www/us/en/developer/articles/technical/unreal-engine-optimization-chapter-2.html)).
- Configure fallback mesh settings:

```ini
; Per-mesh in Static Mesh Editor:
Fallback Triangle Percent = 1-5%   ; aggressive reduction for decorative assets
Fallback Relative Error = 1.0      ; large silhouette deviation allowed (small/background mesh)

; Project-wide (cook), UE5.5+:
[/Script/WindowsTargetPlatform.WindowsTargetSettings]
bGenerateNaniteFallbackMeshes=False   ; strip all fallbacks from the cook entirely
```

- Disable WPO shadow evaluation on foliage meshes: `Details → Shadow → Evaluate World Position Offset (Shadow) = Off`.
- Set `WPO Disable Distance` on foliage (30 m for small plants, 80 m for trees) — Nanite won't evaluate WPO for distant objects.
- For Nanite Tessellation (UE5.4+): use selectively on hero assets and key terrain features — it can double Nanite pass time if applied broadly.

```ini
r.Nanite.Tessellation=1
r.Nanite.AllowTessellation=1
r.Nanite.DicingRate=2   ; default 2px — higher = less dense, cheaper
                        ; recommended 4-8 for background, 1-2 for hero props
```

| Situation | Recommendation |
|---|---|
| Meshes < 300 triangles (simple cube, plane) | Traditional LOD / ISM |
| Meshes with Masked material and WPO (grass, leaves) | Traditional LOD or opaque Nanite geometry |
| Skeletal meshes (UE5.4 and older) | Traditional LOD (Nanite SK experimental from 5.5) |
| Translucent geometry (glass, water) | Traditional — Nanite does not support translucency |
| Foliage with opaque geometry leaves | Nanite + Preserve Area flag |

**World Partition [UE5 only]:**
- Use Runtime Grid Cell Size matching environment scale: 128 m (default) for most worlds, 64 m for dense cities, 256 m for sparse landscapes. Loading Range = 2× Cell Size.
- Data Layers: Runtime Data Layers for game state variations (peaceful vs. combat). External Data Layers for DLC. Avoid overlapping multiple Runtime Data Layers in the same spatial area — this multiplies cell count.
- Data Layers vs Level Instances — these are fundamentally different concepts:

| Use Case | Solution |
|---|---|
| DLC / seasonal content | External Data Layer (EDL) — content in a separate plugin |
| Game state (peaceful village vs. raided) | Runtime Data Layer |
| Repeating POIs (gas stations, houses) | Level Instance → Packed Level Actor |
| Modular building in multiple locations | Level Instance + Embedded (no runtime overhead) |

Runtime Data Layers are NOT compatible with Level Instances — you cannot place a Level Instance inside an External Data Layer ([xbloom.io WP Internals](https://xbloom.io/2025/10/24/unreals-world-partition-internals/)). Too many overlapping Data Layers + Runtime Grids produces a combinatorial explosion of streaming cells.

- Level Instances and Packed Level Actors: use PLA for repeating modular props (gas stations, buildings). PLAs auto-batch identical meshes into ISMs at cook time. One PLA with 20 instances of the same mesh = 1 draw call ([KitBash3D Guide](https://help.kitbash3d.com/en/articles/12038349-a-quick-guide-packed-level-actors-level-instancing-in-unreal-engine-with-kitbash3d)).
- Runtime Cell Transformers (UE5.5+): set Static Mobility on decorative props with no gameplay references. The ISM Runtime Cell Transformer automatically batches them during Streaming Generation. Zero manual effort.
- HLOD configuration: for Nanite meshes, use HLOD Layer Type = Instanced (no decimation). For non-Nanite large world objects, use Merged with appropriate LOD settings. HLOD1 is consumed by Lumen's Far Field pass.
- OFPA best practices: disable Auto-Save for large WP scenes. Rename folders containing OFPA actors only after verifying and updating all references. Use `wp.Editor.DumpStreamingGenerationLog` to debug streaming cell assignments.

**Occlusion and culling:**
- HISM vs ISM in the Nanite era: HISM for non-Nanite foliage (hierarchical LOD + CPU occlusion). ISM for Nanite meshes (Nanite handles LOD/cull on GPU — HISM hierarchy is wasted CPU).
- Precomputed Visibility for closed indoor environments (dungeons, corridors): place Precomputed Visibility Volumes covering player-accessible areas. Can reduce draw calls by 50–90% with zero runtime GPU cost ([Epic Docs: Visibility and Occlusion Culling](https://dev.epicgames.com/documentation/unreal-engine/visibility-and-occlusion-culling-in-unreal-engine)).
- Cull Distance Volumes: set cull distances by bounding sphere size. Rule of thumb: `[50cm, 2000cm]` — cull objects under 50 cm bounding sphere when farther than 20 m.

**Lesser-known tricks:**

- `wp.Editor.DumpStreamingGenerationLog` — dumps a log of which actors ended up in which streaming cells. Output in `Saved/Logs/WorldPartition/`.
- Predictive streaming source for vehicles/fast movement: add a secondary Streaming Source component offset in the direction of velocity. Fills cells before the player arrives, eliminating pop-in. The default Streaming Source is purely reactive.
- Large actors spanning more than one cell size (churches, bridges) are "promoted" to a higher grid level and may load independently of normal cells — be aware of this when designing large structures.
- World Composition → World Partition migration: `UnrealEditor.exe "project.uproject" -run=WorldPartitionConvertCommandlet "MapName"`. Foliage tiles require manual re-placement.
- HZB Occlusion `r.HZBOcclusion=0` — disable to test whether HZB is causing false occlusion culling artifacts (rare bug in some UE5 versions with fast camera rotation).
- `r.Nanite.Streaming.StreamingPoolSize` — controls Nanite geometry streaming pool. Default 512 MB. Reduce for memory-constrained platforms.
- VSM diagnostics:

```
stat VirtualShadowMapCache             ; look for "Physical page pool overflow"
r.Shadow.Virtual.Cache.DrawInvalidatingBounds 1  ; green boxes = what's invalidating the cache
r.Shadow.Virtual.Visualize 1          ; mode 2 = Page Allocation (green = cached, red = new)
```

**Tools for this role:**
Nanite Visualization modes, Lumen Surface Cache view, VSM Visualize, `stat nanite`, `stat virtualshadowmaps`, `stat initviews`, `show LOD`, `show Bounds`

**CVars cheat sheet:**

| CVar | Default | Notes | Engine |
|---|---|---|---|
| `r.Nanite.MaxPixelsPerEdge` | 1 | Higher = fewer triangles, faster | UE5 only |
| `r.Nanite.Streaming.StreamingPoolSize` | 512 (MB) | Nanite geometry pool size | UE5 only |
| `r.Shadow.Virtual.MaxPhysicalPages` | 4096 | Increase to 8192 for open worlds | UE5 only |
| `r.Shadow.Virtual.Cache.DrawInvalidatingBounds` | 0 | Green boxes = VSM cache invalidators | UE5 only |
| `r.HZBOcclusion` | 1 | Set 0 to disable HZB (debug only) | UE4 + UE5 |
| `wp.Runtime.RuntimeCellSize` | 12800 | World Partition cell size in cm | UE5 only |

---

### Materials / Shader Authors **[UE4 + UE5]**

Shaders are the silent bottleneck. High instruction count hurts fill rate; too many unique shaders hurts PSO compilation and Nanite shading bins.

**Common pitfalls:**

- **Static Switch explosion** — every Static Switch Parameter doubles compiled permutations. N switches = 2ᴺ permutations. With 8 switches in a master material, that is 256 shader variants compiled to disk, each needing a PSO. Static Switches have zero runtime cost but blow up cook time and memory if overused. Keep master materials to fewer than 6 static switches; use separate master materials for fundamentally different shading models. Every combination of settings is a separate shader from the GPU's perspective ([Epic's Knowledge Base on shader permutations](https://forums.unrealengine.com/t/knowledge-base-understanding-shader-permutations/264928)).
- **Dynamic Switch vs Static Switch distinction** — the `Switch Parameter` node (dynamic) compiles BOTH branches into the shader; both consume instruction budget even when not taken. On AMD GPUs, context rolls from mismatched PSO states with many dynamic switches cause stalls. Use Static Switches for quality tier variations; use dynamic switches only when the change happens at runtime per-instance.
- **Texture Sampler limit** — base hardware limit is 16 samplers per shader. Exceeding this causes a shader compilation fallback 2–3× slower. UE has 13 slots for use before engine reserves are consumed. Audit with the Material Stats window.
- **Dynamic Material Instance created per-frame** — `CreateDynamicMaterialInstance` allocates a new UObject on the heap. Pool MIDs: create once, store, update parameters only.
- **Custom HLSL node pitfalls** — TEXCOORD overflow (limit of 8 UV interpolators; 16 in UE5 with additional cost), texture sampling requires `Texture2DSample(Tex, TexSampler, UV)` not `tex2D()` in SM5, the HLSL compiler aggressively unrolls loops (add `[loop]` attribute for dynamic counts), and helper functions can be wrapped in a struct declaration or included via `#include "/Engine/Private/Common.ush"`.
- **Translucency overuse** — translucent objects render in a separate full-screen pass without depth testing. Layered translucency (many overlapping transparent meshes) is the fastest way to destroy fill rate.
- **PDO shadow pass limitations** — Pixel Depth Offset does not run during the shadow depth pass, causing severe self-shadowing artifacts. PDO also forces materials off Nanite's hardware raster fast path. **[UE5 only]** Lumen ghosting: when PDO is active and Lumen's temporal GI is accumulating, displaced pixels cause smearing during camera movement. Nanite Tessellation (UE5.3+) is a better alternative for displacement with correct shadows.
- **WPO + Nanite per-cluster culling** **[UE5 only]** — the `Max World Position Offset Displacement` setting in the material controls Nanite's per-cluster culling for WPO. Setting it too high disables culling; setting it to 0 disables WPO. Set it to the tightest accurate value for each material.
- **Material Complexity not measured** — a material with 200+ instructions in the pixel shader will saturate fill rate on mid-range hardware. Target <100 instructions for non-hero background surfaces.

**Recommended practices:**

- Use `Material Stats` window (the statistics panel in Material Editor) to monitor instruction count, sampler count, and interpolator usage per shader permutation.
- Use `Material Layers` (UE5 Material Layer Functions) to compose surface variations without separate master materials.
- Use `Material Quality Switch` node to route through Low/Medium/High/Epic branches, controlled by `r.MaterialQualityLevel 0/1/2/3`. Strip expensive features (normal map blending, distance-based roughness variation) on lower settings without maintaining separate master materials.
- Use **Shared Wrap sampler** (`SAMPLER_TYPE_ANISO_WRAP`) for textures using the same wrap mode. UE packs multiple textures into a single sampler slot — this allows up to 128 textures per shader (vs. the default 16 hardware limit) ([Reddit discovery thread](https://www.reddit.com/r/unrealengine/comments/3myppm/til_you_can_use_more_than_16_texture_samplers_by/)). On any `Texture Sample` node, set `Sampler Source → Shared: Wrap` (or `Shared: Clamp`). Trade-off: all textures using the shared sampler must use the same wrapping mode.
- Use `VertexInterpolator` node for expensive per-pixel calculations that can be pre-computed per-vertex. Moves cost from pixel shader to vertex shader — massive fill rate gain for dense geometry.
- **[UE5 only] Substrate**: Material Layer Functions within Substrate allow physically-based slab stacking. Requires `Project Settings > Rendering > Substrate = true`.
- **[UE5 only] Nanite + opaque materials**: Nanite's deferred shading bin system groups draws by unique shader. Minimizing unique shaders is more impactful in a Nanite scene than reducing polygon count. Merge material variants into one master with parameter variations.
- Use `Blend Mode: Masked` whenever binary opacity suffices — Masked runs a depth pre-pass then shades surviving quads once. Translucent skips depth prepass and shades every pixel every time.
- Pack multiple single-channel data maps into one RGBA texture and use component masks: R = AO, G = Roughness, B = Metallic. One texture fetch returns four values. Set sRGB = Off on packed textures.
- `Material Attributes` (enable `Use Material Attributes` on a material or function) collapses all inputs/outputs into a single `MaterialAttributes` pin. Use `BlendMaterialAttributes` to lerp between two attribute structs — ideal for layered materials (BaseLayer → WetnessLayer → SnowLayer) without spaghetti wiring.
- Use `VertexInterpolator` node for pre-computable-per-vertex data. Moves cost from pixel shader to vertex shader.
- Classic tessellation is removed in UE5.0 **[Deprecated in UE5]**. Use Nanite Displacement (UE5.2+ experimental, production from ~UE5.4) via the Nanite Displacement Mesh plugin.
- For translucency: prefer `Blend Mode: Masked` for binary opacity. Translucency lighting modes by cost:

| Mode | Cost | Quality | Use Case |
|---|---|---|---|
| `Volumetric Non-Directional` | Cheapest | Flat lighting | Smoke, fog |
| `Surface Translucency Volume` | Medium | GI approximate | Water, semi-transparent props |
| `Surface Forward Shading` | Expensive | Full PBR + specular | Glass, gems, hero props |

Refraction forces a scene color capture (read-before-write) — very expensive. For secondary materials, consider fake refraction via normal-mapped distortion.

**WPO CVars:**
```
r.Shadow.Virtual.Cache.MaxMaterialPositionInvalidationRange 10
r.Shadow.Virtual.NonNanite.IncludeInCoarsePages 0
```
The first limits the radius within which WPO movement invalidates VSM shadow cache pages — the main source of WPO performance regression on dense foliage.

**Lesser-known tricks:**

- `r.ShaderPipelineCache.Enabled 1` and PSO pre-compilation from captured PSO caches can eliminate first-draw stutter. Capture PSOs during QA and ship the cache.
- `r.CompileShadersOnDemand 0` in shipping builds forces all shaders to compile during cook, eliminating first-use stalls.
- Custom HLSL nodes can read `View.ViewToClip`, `View.WorldToView`, and other view-uniform data. Document what uniforms you reference.
- Tiling atlases vs. Texture Arrays: use `Texture2DArray` when you need to sample many variants of the same resolution/format in one shader.
- For 1D gradient LUTs (color ramp, SSS falloff): store as a 256×1 or 256×16 texture. One texture fetch replaces an expensive math chain.
- `Material Quality Switch` routes execution based on `r.MaterialQualityLevel` — use it to strip expensive features at lower quality without maintaining separate master materials.

**Tools for this role:**
Material Stats panel, Shader Complexity View Mode, Quad Overdraw View Mode, `stat shadercompiling`, RenderDoc shader debugger

**CVars cheat sheet:**

| CVar | Default | Notes | Engine |
|---|---|---|---|
| `r.MaxAnisotropy` | 4 | Texture filter quality | UE4 + UE5 |
| `r.CompileShadersOnDemand` | 1 | 0 = compile all during cook | UE4 + UE5 |
| `r.Nanite.Tessellation` | 0 | Enable Nanite displacement | UE5.2+ |
| `r.Nanite.DicingRate` | 2 | Tessellation density (pixels/triangle) | UE5.2+ |
| `r.ShaderPipelineCache.Enabled` | 1 | PSO cache usage | UE4 + UE5 |
| `r.MaterialQualityLevel` | 3 | 0=Low, 1=Medium, 2=High, 3=Epic | UE4 + UE5 |

---

### Meshes / 3D Art **[UE4 + UE5]**

**Common pitfalls:**

- **Nanite on foliage cards** **[UE5 only]** — alpha-masked foliage (leaves as cards) with WPO triggers Programmable Rasterizer on every triangle, including masked ones. Each shadow pass is also affected. Best practice: use full opaque geometry for Nanite foliage leaves, or disable Nanite and use HISM LODs.
- **Fallback mesh too high-poly** **[UE5 only]** — Nanite fallback mesh defaults to `Fallback Relative Error = 0`, meaning an exact copy of the source. For a 500k polygon source mesh, the fallback is also 500k polygons. Set `Fallback Triangle Percent = 1–5%` and `Fallback Relative Error = 1.0` for decorative assets.
- **Nanite Foliage WPO incompatibility** **[UE5 only]** — Nanite does not support per-vertex WPO wind animation without forcing the software raster path. Solutions: (1) Pivot Painter 2 — bake pivot data into UV channels, disable unused Wind Settings groups to remove instructions; (2) Hybrid LOD — LOD0 as a traditional mesh with WPO wind, LOD1+ as Nanite with instance-level sway only; (3) Per-Instance Custom Data — instance animation (rotation around base pivot) for subtle swaying ([StraySpark Nanite foliage guide](https://www.strayspark.studio/blog/nanite-foliage-ue5-complete-guide)).
- **Procedural foliage collision trap** — enabling collision on procedurally spawned foliage kills performance (the physics engine iterates all instances). The Kite Demo deliberately has no foliage collision. Use a proximity sphere around the player with separate simplified collision proxies.
- **Collision meshes too detailed** — complex collision (`Use Complex as Simple`) on dense static meshes is expensive for physics queries and for Lumen HWRT BLAS generation. Use simplified custom collision or box/sphere primitives for most props.
- **No LODs on non-Nanite meshes** — skeletal meshes, translucent meshes, and any mesh not using Nanite must have manually created LODs. A 50k polygon character without LODs tanks GPU fill rate at medium distance.
- **Unique materials per mesh in non-Nanite scene** — each unique material on a mesh requires a separate draw call. Merge materials using texture atlases.
- **Lightmap UVs overlapping or too dense** — overlapping lightmap UVs produce lighting artifacts; too-dense packing wastes texture memory.

**Recommended practices:**

- **Nanite: use for hero props, architecture, and terrain — not for simple geometry**: Triangle threshold ~300. Below that, ISM/HISM batching is usually cheaper.
- **Nanite Fallback Mesh**: Set `Fallback Triangle Percent = 1–5%` for decorative assets. For cook-time removal of all fallbacks (UE5.5+): `bGenerateNaniteFallbackMeshes=False` in target platform settings. Verify non-Nanite render paths visually.
- **WPO Disable Distance [UE5 only]**: Set per mesh in Static Mesh Editor. Small foliage: 30 m. Large trees: 80 m. Hero props requiring wind animation: 150 m or leave enabled.
- **Distance Field Resolution Scale**: Set to 0.5 for background geometry, 1.0 for hero props, 2.0 for Lumen-critical geometry.
- **Merge Actors** for static background props that will never be individually referenced by gameplay. Reduces draw calls but sacrifices per-element LOD. Use Runtime Cell Transformers (UE5 WP) as a non-destructive alternative.
- **GPU Skin Cache [UE4 + UE5]**: Enable in Project Settings > Rendering. Moves skeletal mesh skinning to GPU compute, freeing vertex shader slots and reducing CPU overhead. Required for Cloth and Mesh Deformer features. `r.SkinCache.Mode 1`.
- **Mesh Deformer [UE5 only]**: Replaces morph target deformation with a compute shader path. Compatible with Nanite Skeletal Mesh. More efficient for face shapes and body morphs at scale.
- For collision on vegetation and foliage: use simple convex hull or even no collision. Never use complex-as-simple for foliage.
- Foliage density scalability:

```ini
[FoliageQuality@0]
foliage.DensityScale=0.4
[FoliageQuality@2]
foliage.DensityScale=1.0
```

**Lesser-known tricks:**

- **Nanite Skeletal Mesh [UE5.5+ experimental]**: Significant FPS gains in crowd scenes (~22 FPS → 55+ FPS in a 500-character scene). Enable in Project Settings > Experimental ([The Future of Nanite Foliage | Unreal Fest Stockholm 2025](https://www.youtube.com/watch?v=aZr-mWAzoTg)).
- **Nanite Preserve Area flag**: for foliage with Nanite enabled, set Preserve Area to maintain silhouette accuracy at distant LODs.
- **`NaniteStats` console command** — shows per-frame Nanite cluster, instance, and streaming stats beyond what `stat nanite` shows.
- Quad Overdraw View Mode (`View → Optimization Viewmodes → Shader Complexity & Quads`) reveals how many GPU quads are wasted by sub-pixel triangles. When a triangle is smaller than one quad, the GPU still shades all 4 pixels — 75% wasted work.

**Tools for this role:**
Nanite Overdraw view mode, LOD Coloration view, `stat nanite`, `stat scenerendering`, Static Mesh Editor (Nanite fallback settings)

---

### Lights and Shadows **[UE4 + UE5]**

**Common pitfalls:**

- **Many Point Lights with Cast Shadows enabled** — each shadow-casting VSM local light maintains its own page pool allocation. Dozens of cast-shadow point lights with overlapping radii = page pool overflow, stipple artifacts, and severe performance degradation.
- **Stationary Directional Light without CSM tuning [UE4 only]** — default CSM settings are generous. `CascadeDistributionExponent`, `NumDynamicShadowCascades`, and `DynamicShadowDistanceStationaryLight` all need per-project tuning.
- **Lumen left at Epic Scalability defaults** **[UE5 only]** — Epic scalability targets high-end benchmarking hardware. Default `TracingOctahedronResolution`, `DownsampleFactor`, and `MaxTraceDistance` are too expensive for mid-range console targets without tuning.
- **Lumen emissive lighting transients** **[UE5 only]** — emissive lighting through Lumen has no historical data after a cut or level load. Visible GI flickering for 0.5–2 seconds after cuts. Mitigation: back critical emissive sources with a Point/Spot Light for stable GI. Enable the `Emissive Light Source` checkbox on an actor to prevent the Surface Cache from culling it.
- **Monolithic building meshes killing Lumen Card generation** **[UE5 only]** — a single "entire building" mesh generates only exterior Lumen Cards. Interior receives no GI. Build modularly — separate meshes for walls, floors, ceilings — for correct Lumen GI coverage inside ([Unreal Fest Gold Coast 2024](https://www.youtube.com/watch?v=szgnZx2b0Zg)).
- **VSM Page Pool overflowing in open worlds** **[UE5 only]** — the default 4096 pages is appropriate for linear games but too small for open-world projects. An overflowed page pool produces visible stippling patterns when rotating the camera ([StraySpark VSM Deep Dive](https://www.strayspark.studio/blog/virtual-shadow-map-optimization-open-worlds-ue5-7)).

**Recommended practices:**

**[UE4 only] Stationary Light workflow:**
- Use Stationary Directional + Stationary Sky for the main outdoor lighting. Bakes indirect; dynamic shadows handled by CSM.
- Stationary Point/Spot lights bake colored AO + indirect; dynamic shadow from a small shadow map (Distance Field Shadows).
- Never exceed 4 overlapping Stationary lights — UE4 falls back to dynamic for the 5th.
- Use GPU Lightmass (`r.GPULightmass 1`) for baking — 5–10× faster than CPU Lightmass. **[UE5 only]**: GPU Lightmass is the standard path in UE5.

**[UE5 only] Hardware vs Software Lumen decision matrix:**

| Consideration | Software Lumen | Hardware Lumen |
|---|---|---|
| GPU requirement | Any (DX12/Vulkan) | RT hardware required |
| Skinned mesh GI | No | Yes |
| Far Field (>1km) | No | Yes (uses HLOD1) |
| Thin objects (< 4 cm) | Excluded from Surface Cache | Better support |
| Reflections | Surface Cache (approximate) | Hit Lighting (full material eval) |
| Use case | Console, broad platform | Archviz, film, Metahuman GI |

When to use Software: console games, broad platform support. When to use Hardware: archviz, scenes with many mirror-like reflections, cinematic animations with Metahuman GI ([NVIDIA UE5.4 RT Guide](https://dlss.download.nvidia.com/uebinarypackages/Documentation/UE5+Raytracing+Guideline+v5.4.pdf)).

**[UE5 only] Lumen Surface Cache:**
- An object must be at least ~4 cm in size to enter the Surface Cache. Yellow objects in GI = culled (too distant or too small).
- Build modularly — the interior of a building as separate meshes. A single large "building" mesh will not generate correct cards for the interior.
- Increase `Num Lumen Mesh Cards` (Static Mesh Editor → Build Settings) to 8–12 for interior-critical meshes (rooms need more cards than simple exterior props).

**[UE5 only] Lumen tuning:**
```ini
; GI quality reduction (saves ~2ms on mid-range):
r.Lumen.ScreenProbeGather.TracingOctahedronResolution=2   ; default ~2; reduce to 1 for low
r.Lumen.ScreenProbeGather.DownsampleFactor=2
r.Lumen.ScreenProbeGather.IntegrateDownsampleFactor=2     ; ~3x faster in UE5.6

; Reflection quality reduction:
r.Lumen.Reflections.DownsampleFactor=2
r.Lumen.Reflections.MaxRoughnessToTrace=0.4               ; only shiny surfaces get RT reflections

; Far Field (open worlds, requires HLOD1):
r.LumenScene.FarField=1
r.LumenScene.FarField.OcclusionOnly=1                      ; UE5.6: ~50% cheaper Far Field

; Firefly suppression (UE5.6 default):
r.Lumen.ScreenProbeGather.MaxRayIntensity=10
```

Sources: [StraySpark Lumen 60fps Guide](https://www.strayspark.studio/blog/ue5-lumen-optimization-60fps), [Tom Looman UE5.6 Highlights](https://tomlooman.com/unreal-engine-5-6-performance-highlights/)

**[UE5 only] VSM tuning:**
```ini
r.Shadow.Virtual.MaxPhysicalPages=8192   ; for open world (default 4096)
r.Shadow.Virtual.UseAsync=1              ; async compute, hides ~0.4ms on PS5/XSX
r.Shadow.Virtual.Clipmap.LastLevel=20   ; reduce from 22 if horizon fog covers far distance
r.Shadow.Virtual.ResolutionLodBiasDirectionalMoving=0.5  ; cheaper new pages during fast camera movement
r.Shadow.Virtual.NonNanite.IncludeInCoarsePages=0        ; large gains for foliage-heavy scenes
r.Shadow.Virtual.Cache.MaxFramesSinceLastUsed=20         ; reduce from 60 during fast WP streaming

; Clipmap tuning for directional light:
r.Shadow.Virtual.Clipmap.FirstLevel=6    ; default — finest level
r.Shadow.Virtual.Clipmap.LastLevel=20    ; reduce from 22 if you have horizontal fog
r.Shadow.Virtual.ResolutionLodBiasDirectional=0   ; 0 = full resolution (PC)
```

- Use `IES Profile` textures for realistic light shapes without extra light sources. Cost: one texture lookup.
- `Light Functions` (material functions applied to lights) are expensive — they run a custom shader pass per light. Use sparingly for hero props.
- MegaLights (UE5.4+): designed for very large numbers of dynamic shadow-casting sources at a reasonable cost — use when you genuinely need many local lights with shadows.
- `r.DistanceFields.SupportEvenIfHardwareRayTracingSupported=0` — disable distance field generation when using Hardware Lumen only. Saves VRAM for DF atlases.

**Lesser-known tricks:**

- `r.Lumen.ScreenProbeGather.IntegrateDownsampleFactor=2` in UE5.6 reduces probe gathering cost by ~3× with minimal visual impact. One of the biggest free wins in UE5.6 ([Tom Looman UE5.6 highlights](https://tomlooman.com/unreal-engine-5-6-performance-highlights/)).
- Lumen Cards count per mesh: increase `Num Lumen Mesh Cards` (Static Mesh Editor > Build Settings) from the default for interior-critical meshes (room interiors need 8–12 cards).
- Surface Cache resolution: increase `r.LumenScene.SurfaceCache.CardMinResolution` only for hero props. Saves VRAM elsewhere.
- VSM WPO shadow cost on foliage: in a PS5 test, disabling WPO shadow for floor foliage reduced cost from 8.2 ms to 3.1 ms. One checkbox.

**Tools for this role:**
Lumen Surface Cache view, VSM Visualize, `stat virtualshadowmaps`, `stat lumen`, `stat raytracing`, GPU Visualizer (ShadowDepths, Lumen passes)

---

### VFX / Niagara **[UE4 + UE5]**

**[Deprecated in UE5]**: Cascade is available but not developed. Migrate to Niagara for all new VFX.

**Common pitfalls:**

- **Niagara fixed simulation bounds disabled** — by default, Niagara systems compute bounds dynamically each frame. For systems with predictable extents, use fixed bounds. Dynamic bounds require a CPU readback from GPU, stalling the pipeline.
- **GPU simulation without LOD** — GPU simulations spawn particles at a cost, but the rendering cost scales with screen coverage. A 100k-particle GPU sim off-screen still pays compute overhead. Use Niagara's Significance Manager integration to scale simulation budget by screen importance.
- **GPU sims disappear on camera rotation** — this is a fixed bounds trap. If the fixed bounds are off-screen, the GPU does not dispatch the compute shader and the effect disappears entirely. For travelling effects (projectile trails), expand bounds generously.
- **Using GPU sim for small particle counts** — GPU dispatch overhead means GPU sims only pay off above ~1,000 particles. For 1–100 particles, use CPU simulation. For 1–1,000 particles, the decision depends on whether gameplay integration is needed ([Niagara optimization guide](https://morevfxacademy.com/complete-guide-to-niagara-vfx-optimization-in-unreal-engine/)).
- **Spawning new Niagara Component per VFX event** — creates a UObject per effect instance. Pool Niagara components via `UNiagaraFunctionLibrary::SpawnSystemAtLocation` (automatic pooling in UE5) or implement a manual pool for high-frequency effects.
- **CPU particles on GPU-heavy scenes** — CPU particles pay Game Thread cost per particle for every update. Use GPU simulation for high-count emitters (> ~500–1000 particles).
- **Niagara Data Channel data missed** **[UE5.3+]** — NDC data is completely transient — it exists for a single tick. If you miss a frame, the data is gone ([Epic forum NDC discussion](https://forums.unrealengine.com/t/niagara-data-channel-niagara-emitters-not-taking-the-set-spawn-count/2599289)).

**Recommended practices:**

- Enable `Fixed Bounds` in Niagara System settings for effects with predictable spatial extents.
- Set `Max GPU Particles Per Emitter` to a hard cap. Without a cap, a spawner parameter bug can create millions of particles and stall the GPU.
- Use **Niagara Significance Manager** integration: register the system with a significance manager, drive `Scale By Significance` to reduce spawn rate, simulation resolution, or disable entirely for off-screen or distant effects. Built-in modes: `Distance` (closest to camera wins), `Age` (newest wins), `Custom`.
- Use **Niagara Data Channels [UE5.3+]** for effects that need to query scene data. Data Channels enable GPU-side neighbor queries without CPU readbacks. Uses: bullet impacts spawning multiple effect types from one location, rain writing wetness data read by puddle splashes, global wind direction affecting all outdoor particle systems.
- **Niagara GPU Simulation** advantages: particles can sample Distance Fields, Volume Textures, and Scene Depth for collision. Use for fire, smoke, and environmental effects.
- **LOD via Niagara Scalability**: define scalability levels in Niagara System settings. `Quality Level 0` = no simulation, `3` = full quality. Bind to project scalability groups.
- Cull particles by distance using `Cull Distance` on the Niagara Component. Start with screen-size-based culling via Significance Manager before hard kill distance.
- Every Niagara system should have a `Niagara Effect Type` asset assigned — it is the global control center for scalability: cull distances, max instances, spawn count scales, and budget limits.
- GPU particle Distance Field collision: uses the Global Distance Field — effective range ~10,000 units from camera. Beyond that range, collisions become unreliable. `Particle Radius Scale` default 0.1 is often too small; increase to 1.0–5.0 for visible effects.

**[UE4 only] Cascade-specific:**
- Cascade `LOD Check Time` controls how often LOD levels are evaluated. Default 0.025s (40 Hz). Reduce to 0.1s for background effects.
- Cascade `Max Draw Count` limits visible sprite count per emitter.

**Lesser-known tricks:**

- `Niagara Debugger` (`Window > Niagara Debugger`): shows per-system runtime stats (particle count, GPU time, scalability level). Essential for identifying expensive VFX systems.
- Distance Field Collision in Niagara GPU: enable via `Collision Module > GPU Collision Type = Distance Field`. No CPU involvement; works with Lumen's DF generation.
- Render Target sampling in Niagara for gameplay-driven VFX: a Render Target updated by Blueprint (health state, power level) can drive Niagara simulation parameters via a texture sample.
- `Niagara Data Interface: Skeletal Mesh` — sample bone/socket positions directly in GPU simulation. Use for character-attached sparks, blood drips.
- Significance Manager crash bug warning: with aggressive culling and short-lived systems dying simultaneously during significance processing, a crash can occur — see [Epic's forum post on Niagara scalability crash](https://forums.unrealengine.com/t/niagara-scalability-crash-when-processing-significance/2611550) for the fix.

**Tools for this role:**
Niagara Debugger, `stat particles`, `stat niagara`, GPU Visualizer (Niagara pass), Significance Manager debug draw

**CVars cheat sheet:**

| CVar | Default | Notes | Engine |
|---|---|---|---|
| `fx.Niagara.MaxGPUParticlesSpawnPerFrame` | variable | Hard cap GPU spawns | UE5 |
| `fx.Niagara.SystemSimulationTickBatchSize` | 8 | Batch GPU system ticks | UE5 |
| `fx.NiagaraMaxGPUCount` | 1M | Global GPU particle cap | UE5 |
| `fx.Niagara.QualityLevel` | 3 | Global quality scale (0=off) | UE5 |

---

### Audio **[UE4 + UE5]**

**Common pitfalls:**

- **Sound Cues as default in UE4 vs MetaSounds in UE5** — Sound Cues are Blueprint-like graphs executed on the Audio Thread. MetaSounds **[UE5 only]** are node-based DSP graphs with per-instance parameters. MetaSounds enable procedural audio, Quartz synchronization, and per-instance state without Blueprint overhead.
- **Sound Concurrency not configured** — without Concurrency assets, the engine has no budget for how many simultaneous sounds can play. High-frequency gameplay (footsteps, gunshots) can spawn thousands of active sounds. Configure Sound Concurrency assets and assign them to Sound Classes.
- **Streaming too many small sounds** — streaming is efficient for long ambient tracks (> 10–20 seconds). For short one-shot sounds, loading into memory is cheaper.
- **No attenuation curves** — default linear rolloff is rarely appropriate for complex environments.
- **Reverb Volumes without budget** — overlapping reverb zones overrun the Audio Thread budget.

**Recommended practices:**

- **Sound Classes** define categories (Music, SFX, Voice, Ambient). Assign concurrency, EQ, and volume controls per-class.
- **Sound Concurrency**: define `MaxCount`, `ResolutionRule` (Stop Quietest / Prevent New), and `RetriggerTime` per concurrency asset. `USoundConcurrency::MaxCount` set to 1 for UI confirm sounds with `RetriggerTime = 0.5` prevents double-trigger on rapid button press.
- **Stream Caching [UE4 + UE5]**: `au.streamcache.TrimCacheWhenOverBudget 1` and `au.streamcache.CacheSizeKB` to match your audio memory budget.
- **Quartz [UE5 only]**: provides sample-accurate musical beat synchronization. Use for rhythm games, dynamic music systems, and synchronized SFX.
- **MetaSounds [UE5 only]**: replace complex Sound Cue randomization trees with MetaSound inputs. Pass gameplay state as input values rather than routing sound branches on the Audio Thread. MetaSound input parameters can be driven by Gameplay Attributes or Subsystems, enabling fully reactive procedural audio without Blueprint tick polling.
- Use `Attenuation Shape = Capsule` for corridor environments; `Sphere` for open spaces. Custom falloff curves for reverb blend allow gradual wet/dry transitions.
- **Audio Mixer** is the default in UE4.24+ and UE5. Each source can route to one or more Submixes (SFX Bus, Music Bus, Voice Bus). Add effects at the submix level for efficient processing — one reverb instance on the Environment submix versus one per environmental sound.
- Compress audio for shipping: `OGG Vorbis` at `Quality 40–60` for most SFX. `ADPCM` for short, frequently-triggered sounds (gunshots, footsteps) — faster decode, lower quality. `PCM` only for music where quality is critical and memory is not a constraint.
- HRTF Spatialization: enable `Spatialization Algorithm = HRTF` in Sound Attenuation settings. HRTF adds CPU cost per virtualized source — budget carefully.

**Lesser-known tricks:**

- `au.Debug.SoundCues 1` — overlay active sound instances in the viewport with voice budget color coding.
- `au.DisableAudioCaching 1` — forces audio to re-stream on every play (debugging only; never ship with this).

---

### Animations **[UE4 + UE5]**

Skeletal mesh animation is one of the highest Game Thread costs in character-heavy projects. Three opt-in systems — URO, Animation Budget Allocator, and GPU Skin Cache — collectively cut CPU and GPU skinning cost dramatically when used together.

**Common pitfalls:**

- **URO not enabled per component** — Update Rate Optimizations (URO) allow animation evaluation to run at a reduced rate for distant or off-screen characters. It is opt-in per component.
- **Animation Budget Allocator plugin not enabled** — the plugin (4.26+) dynamically allocates per-frame animation CPU budget, throttling or entirely skipping distant characters. Off by default.
- **GPU Skin Cache disabled** — GPU Skin Cache moves skinning from vertex shader (runs once per draw call) to compute shader (runs once per mesh per frame). Required for Cloth simulation and Mesh Deformer (UE5). Enable in Project Settings > Rendering.
- **Animation Blueprint Fast Path not maintained** — Fast Path executes nodes directly in native code without Blueprint VM overhead. Adding a single math node can break Fast Path for the entire Anim BP. Green lightning bolt in the Anim BP node = Fast Path active.
- **Many morph targets on hero characters** — morph targets in UE4 run on CPU. In UE5, `r.MorphTarget.EnabledByDefault 1` moves them to GPU.
- **Master/Leader Pose Component misused** — `SetLeaderPoseComponent` (renamed from `MasterPoseComponent` in UE5.1) drives multiple meshes from a single animation evaluation. All slave meshes share the same pose without individual evaluation cost. Correct for modular characters.

**Recommended practices:**

- **URO configuration** per character type: background NPCs → max 15 fps evaluation at 10 m+. Hero NPCs → 30 fps at 5 m+. Player character → no URO.
- **Animation Budget Allocator**: enable plugin, set `Budget in Milliseconds` per scalability level (e.g., 2 ms on low, 4 ms on high).
- **`SetLeaderPoseComponent` [UE5] / `SetMasterPoseComponent` [UE4]**: on character spawn, set a single "driver" mesh, then attach all cosmetic meshes as followers. One animation evaluation drives all.
- **Anim BP node caching**: cache component references (Get Skeletal Mesh Component) in Update rather than re-querying per node.
- **Control Rig for procedural IK [UE5]**: replaces custom IK solver Blueprints with a compiled graph that runs on the worker thread, not the Game Thread.
- **GPU Skin Cache setup**: `r.SkinCache.Mode 1` (enables on all skeletal meshes). `r.SkinCache.Mode 2` is the recompute tangent mode (more expensive; only for cloth/Deformer use cases).
- **`Anim Next [UE5.4+ experimental]`**: a rewrite of the animation graph execution model, optimized for batch processing. Experimental; not recommended for production without thorough testing.

**Lesser-known tricks:**

- `tick.AnimationBudgetAllocator.Enabled` CVar for runtime toggle of ABA.
- Anim curves can drive material parameters, blend shape targets, and physics constraint settings — avoid Blueprint Tick polling for these by using curve-driven setups.
- `r.SkeletalMeshLODBias` — global LOD bias for all skeletal meshes. Set to 1 on low-end platforms to force all meshes one LOD step lower.

**Tools for this role:**
Animation Insights channel, `stat game` (ComponentTick), `stat gpu` (SkinCache), Anim Blueprint debugger, GPU Skin Cache visualization

**CVars cheat sheet:**

| CVar | Default | Notes | Engine |
|---|---|---|---|
| `r.SkinCache.Mode` | 0 | 0=off, 1=on, 2=with recompute tangents | UE4 + UE5 |
| `r.SkeletalMeshLODBias` | 0 | Global LOD offset for all skeletal meshes | UE4 + UE5 |
| `a.URO.Enable` | 1 | URO master toggle (per component still required) | UE4 + UE5 |
| `tick.AnimationBudgetAllocator.Enabled` | 1 (if plugin on) | ABA runtime toggle | UE4.26+ UE5 |
| `r.MorphTarget.EnabledByDefault` | 0 | 1 = GPU morph targets | UE5 |

---

### UI / UMG / Slate **[UE4 + UE5]**

**[CORRECTED] The old advice "Do not use UMG if possible" is misleading and outdated.** UMG is the standard UI framework for all Unreal projects in the 2020s. The real rules are: use Invalidation Box to prevent unnecessary widget redraws, control tick carefully, and prefer event-driven data bindings over per-frame polling.

**Common pitfalls:**

- **Per-frame Blueprint binding on widget properties** — the default `Bind` button in UMG creates a function called every frame (a "tick binding") that evaluates the expression and updates the widget even when the value hasn't changed.
- **No Invalidation Box around complex widget trees** — without an Invalidation Box, every frame the renderer walks the full widget tree looking for dirty widgets. On a HUD with 100+ widgets, this is expensive.
- **Retainer Box misuse** — Retainer Box renders a widget subtree to an off-screen Render Target at a specified update rate. Misused on static UI panels it adds Render Target overhead without benefit.
- **High-frequency `Set Text` calls** — text layout and glyph rasterization are expensive. Throttle text updates.
- **Widget creation/destruction in Tick** — spawning a `CreateWidget` inside Tick creates a UObject per frame. Pool reusable widgets.

**Recommended practices:**

- Replace tick bindings with **event-driven updates**: bind to a game delegate/dispatcher that fires only when the value changes.
- Use **Invalidation Box** around static or slowly-changing widget trees. Set `Cache Relative Transforms = true` for child widgets that translate.
- **Visibility flags for performance:**

| Visibility | Render | Hit Test | Tick |
|---|---|---|---|
| Visible | Yes | Yes | Yes |
| HitTestInvisible | Yes | No | Yes |
| SelfHitTestInvisible | Yes | No (self only) | Yes |
| Hidden | No | No | Yes |
| Collapsed | No | No | No (layout skipped) |

Use `Collapsed` for widgets that are not needed. `Hidden` still occupies layout space and ticks. `Collapsed` is the only mode that skips layout and tick entirely.

- **Common UI [UE5 only]**: Epic's Common UI plugin provides platform-agnostic input routing, activatable widget stack management, and action bar generation.
- **Texture Atlas**: pack small UI icons into a single texture atlas. Each texture slot in UMG requires a separate draw call. A 64-icon atlas uses one draw call; 64 individual textures use 64.
- Use `Set Visibility` rather than `Add to Viewport / Remove from Viewport` for panels that toggle frequently.
- For scrolling lists: `ListView` and `TileView` widgets virtualize — they create only enough widgets to fill the visible area, reusing them as the user scrolls.
- **Font caching**: avoid high-resolution dynamic fonts in real-time UI. Pre-rasterize fonts at fixed sizes.

**Lesser-known tricks:**

- `Slate.Widget.Invalidation.Enabled 1` enables the Invalidation Forest system globally. Ensure "volatile" (per-frame changing) widgets are marked volatile with `SetIsVolatile(true)` in C++ or via tick binding status in UMG.
- `Widget Reflector` tool (`Window > Widget Reflector`): visualizes the live widget tree with per-widget paint times.
- Screen-space Render Targets for world-space UI: render a UMG widget to a Render Target and apply it as a material to a plane in the world.

**Tools for this role:**
Widget Reflector, `stat Slate`, `stat SlateRendering`, `stat UMG`

---

### Networking and Multiplayer **[UE4 + UE5]**

**Common pitfalls:**

- **`DORM_Never` on all actors** — the default dormancy means every actor sends replication checks every frame. Static world props (barrels, furniture) should be `DORM_DormantAll`. A dormant actor costs 0.13 ms total vs 15 ms for an always-replicating equivalent with 99.3% waste rate ([Reddit dormancy benchmark](https://www.reddit.com/r/UnrealEngine5/comments/1lzi6xg/networking_optimization_in_unreal_engine_5_with/)).
- **Standard TArray replication for large collections** — replicates the full array on any change. Use `FFastArraySerializer` for arrays where individual element changes are frequent — it sends per-element deltas only.
- **Missing Adaptive Net Update Frequency** — `NetUpdateFrequency` defaults to 100 (pawn). Without adaptive frequency, actors update the server at max frequency even when stationary.
- **Multicast RPCs for cosmetics the server doesn't need** — `Multicast` RPC fires on server and all clients. For cosmetic-only effects (particle spawns), the server pays unnecessary cost. Use `Client` RPC or `Unreliable Multicast`.
- **No bandwidth cap** — `TotalNetBandwidth` defaults to 15000 bytes/s, low for modern games.

**Recommended practices:**

- **Actor Dormancy**: set `DORM_DormantAll` on all static world props at level load. Call `FlushNetDormancy()` on an actor before changing its state.
- **Push Model Replication**: use `MARK_PROPERTY_DIRTY_FROM_NAME` and `bIsPushBased = true` for infrequently-changed properties. Add `NetCore` to your module's dependencies or you will get a linker error.
- **Replication Graph [UE4.20+ / UE5]**: for 50+ concurrent replicating actors per client, replace the default Net Driver with the Replication Graph plugin. Spatial grid nodes provide O(1) relevancy checks.
- **Iris [UE5.4+ / default in UE5.5+]**: a rewrite of the replication data path. Enable via `net.Iris.UseIrisReplication=1`. Backward-compatible with existing UPROPERTY replication. Better CPU scalability at high player counts.
- **RepNotify vs Replicated**: use `RepNotify` (ReplicatedUsing) when clients need to react to a state change with logic (update UI, play sound). Use bare `Replicated` for values clients read directly.
- **DOREPLIFETIME_CONDITION**: `COND_OwnerOnly` for per-player private data (inventory, ability cooldowns), `COND_SkipOwner` for state the owner already knows, `COND_InitialOnly` for setup data that never changes after spawn.

```cpp
void AMyActor::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME_CONDITION(AMyActor, PrivateInventory, COND_OwnerOnly);
    DOREPLIFETIME_CONDITION(AMyActor, ServerSimulatedPosition, COND_SkipOwner);
    DOREPLIFETIME_CONDITION(AMyActor, CharacterClass, COND_InitialOnly);
    FDoRepLifetimeParams PushParams;
    PushParams.bIsPushBased = true;
    DOREPLIFETIME_WITH_PARAMS_FAST(AMyActor, Health, PushParams);
}
```

- **`FFastArraySerializer`**: use for inventory, ability lists, and any `TArray` replicated over the network where individual items change frequently. The Item struct inherits `FFastArraySerializerItem`; the List struct inherits `FFastArraySerializer`; mark dirty via `MarkItemDirty(Items[Idx])` ([ikrima.dev — Fast TArray Replication](https://ikrima.dev/ue4guide/networking/network-replication/fast-tarray-replication/)).
- Set `MinNetUpdateFrequency = 2` and `NetUpdateFrequency = 100` with Adaptive Frequency enabled.

**Lesser-known tricks:**

- `net.Iris.ReplicationWriterMaxAllowedPacketsIfNotHugeObject` (default 3): controls per-batch packet cap in Iris.
- `-NetTrace=1` command line: enables the networking trace channel for Networking Insights analysis.
- `Dormancy.FlushNetDormancyOnSpawn` CVar: flush dormancy automatically on spawn for actors with initial state to transmit.
- `GameplayDebugger` network category (`numpad '`): shows per-actor replication cost and update frequency in-game.

**Tools for this role:**
Networking Insights (`-NetTrace=1 -trace=net`), `stat net`, `stat netpackets`, `stat replication`

**CVars cheat sheet:**

| CVar | Default | Notes | Engine |
|---|---|---|---|
| `net.UseAdaptiveNetUpdateFrequency` | 0 | 1 = enable adaptive update frequency | UE4 + UE5 |
| `TotalNetBandwidth` | 15000 | Bytes/sec server bandwidth cap | UE4 + UE5 |
| `net.Iris.UseIrisReplication` | 0 | 1 = enable Iris replication | UE5.4+ |
| `net.MaxNetTickRate` | 120 | Server tick rate | UE4 + UE5 |
| `p.NetUpdateFrequency` (actor) | 100 | Max updates/sec per actor | UE4 + UE5 |

---

### QA / Build / Production **[UE4 + UE5]**

**Common pitfalls:**

- **Profiling in Editor instead of Test build** — Editor PIE adds 2–4× Game Thread overhead. All performance decisions from Editor numbers are unreliable.
- **Shipping with DDC not pre-populated** — the Derived Data Cache (DDC) stores cooked shader and physics data. Cold DDC on a fresh checkout = full shader compilation on first cook.
- **No automated performance regression testing** — manual profiling before milestones misses gradual regressions introduced over weeks.
- **Cook errors treated as warnings** — cook warnings about missing assets, oversized textures, or unset LODs ship as production issues.

**Recommended practices:**

- **Always deliver from Test build**: profiling, performance reviews, and QA sign-off should happen on Test packaged builds.
- **Gauntlet automation framework**: write `UAutomationTestBase` performance tests that run in CI, measure frame time, and fail on regression.
- **LLM memory tracking**: add `ALLOW_LOW_LEVEL_MEM_TRACKER_IN_TEST=1` to your Test target.
- **DDC pre-warm**: run on the build server and push results to a shared DDC. Epic's `Zen Store` (UE5.4+) replaces the legacy shared DDC with a content-addressable, version-tolerant cache server with REST API.
- **BuildGraph**: use Epic's BuildGraph (`Engine/Build/Graph/Build.xml`) for reproducible builds.
- **Memreport on staging**: run `Memreport -full` after a full gameplay session. Diff against the previous milestone to catch new leaks.
- **PSO cache**: PS5 and XSX require PSO pre-compilation. Plan two cook passes: one for PSO capture playthrough, one for the final shipping build with the captured PSO cache included.
- **IWYU and build speed**: keep `PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs` in all module Build.cs files. Never use `#include "Engine.h"` or `#include "UnrealEd.h"`. Set `bFasterWithoutUnity = true` for modules under heavy iteration.

**Lesser-known tricks:**

- `UE4 / UE5 Commandlets`: `-run=DerivedDataCache` for DDC warm, `-run=ResavePackages` for bulk package resave, `-run=WorldPartitionConvertCommandlet` for WP migration.
- `AssetRegistry`: build the asset registry dump via `-DumpAssetRegistry` and diff it between builds to catch accidental asset additions.
- `Automation.RunTests` console command with `-Unattended -NullRHI` allows headless automated test runs in CI without a display.
- Module organization: keep `Public/` headers minimal and stable; put implementation in `Private/`. Use `PrivateDependencyModuleNames` for everything not in your public API. Target a clean build time under 3 minutes for your most-changed module.

---

### Tech Art **[UE4 + UE5]**

Tech art sits at the intersection of all other disciplines. This section covers techniques specific to the tech art workflow.

**Common pitfalls:**

- **Runtime Virtual Texture (RVT) without fallback [UE5 only]** — RVT blends landscape material information into object materials. Without a fallback for platforms that don't support RVT, objects appear to float.
- **Custom Depth / Stencil on many actors** — Custom Depth renders a second depth pass for marked actors. Each actor with `Custom Depth Pass = Enabled` adds a draw call. Use selectively; batch related actors using a single Stencil Value.
- **Niagara + Distance Field queries on meshes without DF** — Niagara GPU simulations using Distance Field collision or queries fail silently on meshes without DF generated. The simulation looks wrong rather than crashing.
- **Virtual Heightfield Mesh without LOD bias [UE5 only]** — Virtual Heightfield Mesh (VHM) renders landscape displacement. Without appropriate LOD bias, the patch count at LOD0 can exceed the draw budget.
- **Static Switch permutation explosion in master materials** — 2ᴺ shader permutations (see Materials section). With N switches and various material instances, cook time and PSO stalls can multiply unexpectedly.
- **Translucency sorting cost hidden in profiling** — translucent objects are sorted back-to-front every frame in CPU. Cost scales with the number of translucent actors, and is often invisible in GPU profilers but shows in the Render Thread.

**Recommended practices:**

- **Runtime Virtual Texture (RVT) [UE4.23+ / UE5]**: configure RVT in the landscape material to bake per-texel color, normal, and roughness. Objects intersecting the landscape sample from RVT for context-sensitive shading. Enabling RVT on a complex landscape can reduce landscape overdraw from orange/red in Shader Complexity to full green by caching expensive material evaluation ([Brushify RVT Bootcamp](https://www.youtube.com/watch?v=0-xXIMjlmqE)).

RVT setup checklist:
1. Create a `Runtime Virtual Texture` asset.
2. Place a `Runtime Virtual Texture Volume` over the landscape.
3. Assign the RVT asset to the volume; set bounds from the landscape.
4. Add the RVT to the landscape's Virtual Textures array.
5. Modify the landscape material: add `Runtime Virtual Texture Output` node.
6. Modify prop materials: add `Runtime Virtual Texture Sample` node.

- **Sparse Virtual Textures (SVT) [UE5 only]**: for very large terrain data (64k×64k textures). SVT pages-in only the visible mip levels.
- **Render Target tricks**: drive procedural elements (lava flow, terrain deformation, decal accumulation) by rendering into Render Targets each frame or on demand. Use `Begin/EndDrawCanvasToRenderTarget` when performing multiple draws per frame — this reuses the FCanvas object instead of recreating it. GPU readback via `ReadRenderTargetPixels` is synchronous and stalls the CPU-GPU pipeline — use `EnqueueCopy` (non-blocking async readback) and consume the result a frame later.
- **Custom Depth / Stencil**: use Stencil Value ranges per-system (0–15 for outline system, 16–31 for hit flash). Setup: `Project Settings → Rendering → Custom Depth-Stencil Pass → Enabled with Stencil`, then on the actor: `Rendering → Render Custom Depth Pass: ✓` and set `Custom Depth Stencil Value` (0–255). In the post-process material: `Scene Texture → Custom Stencil` + component mask.
- **Distance Field visualization**: `show DistanceFieldAO`, `show MeshDistanceFields`. Identify meshes without DF coverage for Lumen or ambient occlusion.
- **Niagara × Distance Fields**: use `QueryMeshDistanceField` in Niagara GPU scripts for collision, attraction, and reaction.
- **View-dependent rendering tricks**: use `Camera Direction` node in materials to fade grazing-angle surfaces and drive LOD-aware material complexity.

**Texture compression reference:**

| Format | Channels | Size | Best For |
|---|---|---|---|
| DXT1 / BC1 | RGB (no alpha) | 4 bpp | Opaque diffuse |
| BC4 | R only | 4 bpp | Single-channel masks, heightmaps |
| BC5 | RG | 8 bpp | Normal maps (stores XY, derives Z) |
| BC7 | RGBA | 8 bpp | High-quality diffuse with alpha |

UE5 uses BC5 by default for Normal Map compression. Do not use BC7 for normal maps without manual shader handling. sRGB rule: normal maps, masks, roughness, metallic, AO — all linear (sRGB off). Albedo/Color — sRGB.

**Post-process effect cost reference:**

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

**TSR vs DLSS vs FSR [UE5 only]:**
TSR is Epic's built-in solution, fully integrated with Lumen, Nanite, and the velocity buffer. Best quality-to-compatibility ratio — no plugin required. Can produce ghosting/smearing on fast-moving objects with WPO or PDO. DLSS generally produces the best motion clarity ([community comparisons](https://www.reddit.com/r/nvidia/comments/wb3dh4/dlss_vs_tsr_vs_fsr_20_motion_clarity_comparison/)). FSR has the widest hardware compatibility. All three temporal AA methods require accurate velocity vectors — WPO and PDO must write correct velocity (`Output Velocity` enabled).

Auto-Exposure: three metering modes: Manual (fixed EV100 — predictable, required for cutscenes), Histogram (physically correct), Basic (legacy, confused by bright skyboxes). UE5.1+ breaking change: old `Min/Max Brightness` replaced by `Min/Max EV100` — check settings in projects migrated from UE4.

VT Pool Size tuning:
```
r.VT.PoolSizeScale 1.0       ; scale multiplier for all fixed pool sizes
r.VT.Residency.Show 1        ; on-screen HUD showing pool occupancy per format
r.VT.Residency.Notify 1      ; notification when the pool hits 100%
r.VT.DumpPoolUsage            ; dump page counts per texture asset
```

Texture streaming pool: never ship `r.Streaming.PoolSize 0` — it means "unlimited" and will crash the engine. Calibration method: temporarily set `r.Streaming.PoolSize 1`, fly through the level, note the peak warning value, use that value + a safety margin ([TechArtHub's streaming pool guide](https://techarthub.com/fixing-texture-streaming-pool-over-budget-in-unreal/)).

**Lesser-known tricks:**

- **Shared Wrap Sampler — going beyond the 16-sampler limit**: UE5's `Shared:Wrap` and `Shared:Clamp` share two engine-wide sampler states across all textures, allowing a material to reference up to 128 textures ([Reddit discovery thread](https://www.reddit.com/r/unrealengine/comments/3myppm/til_you_can_use_more_than_16_texture_samplers_by/)). When to use: when the Material editor reports "too many texture samplers" or a landscape material requires more than 16 unique textures.
- **Material Attributes pin system**: enable `Use Material Attributes` and use `BlendMaterialAttributes` to lerp between two complete material structs — `BaseLayer` → `WetnessLayer` → `SnowLayer` without spaghetti wire routing.
- `r.VT.FeedbackFactor` — controls how aggressively Virtual Textures stream. Higher = faster streaming, higher I/O load.
- `ShowFlag.ReflectionEnvironment 0` — disable reflection captures to isolate Lumen reflection cost.
- `r.ReflectionCaptureResolution` — lower from 128 to 64 for background reflection captures. Saves VRAM with minimal visual impact on non-mirror surfaces.
- `r.GBuffer.Format 1` — reduce GBuffer bit depth for memory savings (some quality loss on normals and roughness precision).
- Quad Overdraw View Mode: `View → Optimization Viewmodes → Shader Complexity & Quads` reveals how many GPU quads (2×2 pixel groups) are wasted by sub-pixel triangles.
- LUT Packed Textures: instead of sampling multiple 1-channel textures, pack them into a single RGBA texture. Standard Substance Painter packing: R = AO, G = Roughness, B = Metallic.

**Tools for this role:**
`r.VT.FeedbackFactor`, Custom Depth/Stencil, `show DistanceFieldAO`, `show MeshDistanceFields`, Material Stats, `stat shadercompiling`, RenderDoc

**CVars cheat sheet:**

| CVar | Default | Notes | Engine |
|---|---|---|---|
| `r.VT.Enable` | 1 | Virtual Texture master switch | UE4.23+ UE5 |
| `r.VT.PoolSizeScale` | 1.0 | VT pool size multiplier | UE4 + UE5 |
| `r.Streaming.PoolSize` | 800 | MB; NEVER set to 0 | UE4 + UE5 |
| `r.ReflectionCaptureResolution` | 128 | Reduce to 64 for background | UE4 + UE5 |
| `r.GBuffer.Format` | 0 | 1 = reduced precision, saves VRAM | UE4 + UE5 |
| `r.EyeAdaptation.MethodOverride` | -1 | -1=none, 0=basic, 1=histogram, 2=manual | UE4 + UE5 |

---

### Last Resort Methods **[UE4 + UE5]**

These are valid tools but should be used only after profiling identifies a specific bottleneck that targeted fixes can't fully address.

- **`r.ScreenPercentage`** — render at a sub-native resolution. 75% saves ~44% of fill rate. TSR/DLSS at 50–66% with temporal reconstruction can match native visual quality with significant savings.
- **Scalability Levels**: the built-in scalability system adjusts CVars globally per quality tier. Customize `BaseScalability.ini`:

```ini
[ShadowQuality@0]
r.Shadow.Virtual.MaxPhysicalPages=1024
r.Shadow.Virtual.ResolutionLodBiasDirectional=2.0
r.ShadowQuality=0

[PostProcessQuality@0]
r.MotionBlurQuality=0
r.AmbientOcclusionMipLevelFactor=1.0
r.DepthOfFieldQuality=0

[TextureQuality@0]
r.Streaming.MipBias=1
r.Streaming.AmortizeCPUToGPUCopy=0
```

- **`r.LODDistanceFactor`** — multiplier on all LOD distance thresholds. Values < 1 force lower LODs earlier.
- **Disable individual post-process passes**: `r.MotionBlurQuality 0`, `r.BloomQuality 0`, `r.SSR.Quality 0`, `r.AmbientOcclusion.Intensity 0`.
- **CPU physics simplification**: reduce physics substeps (`p.SubstepMaxSubsteps`), disable per-object physics below a velocity threshold.
- **`bUseBackgroundThreadForUpdate`** on AI components — moves AIPerception and behavior tree ticks to background threads.

**Scalability CVars quick reference by category:**

| Category | Key CVars | UE4 range | UE5 range |
|---|---|---|---|
| Resolution | `r.ScreenPercentage` | 50–100 | 50–100 (TSR supplements) |
| Nanite | `r.Nanite.MaxPixelsPerEdge` | N/A | 1–8 |
| Lumen | `r.Lumen.ScreenProbeGather.DownsampleFactor` | N/A | 1–4 |
| Shadows | `r.ShadowQuality` | 0–5 | 0–5 (VSM in UE5) |
| Streaming | `r.Streaming.MipBias` | 0–3 | 0–3 |
| VFX | `fx.Niagara.QualityLevel` | N/A | 0–3 |
| PostProcess | `r.PostProcessAAQuality` | 0–6 | 0–6 |

---

## Optimization Sweep Steps (Pre-Milestone Checklist)

### Map Objects

- [ ] All static meshes have correct Mobility (Static / Stationary / Moveable). Static is cheapest for lighting; avoid Moveable on props that never move.
- [ ] Unnecessary actors removed (debug helpers, placeholder volumes, unused triggers).
- [ ] Cull Distance Volumes placed in all densely-populated areas with distance/size arrays configured.
- [ ] Level Instances / Packed Level Actors used for repeated modular sets **[UE5 only]**.
- [ ] World Partition Runtime Grid Cell Size and Loading Range appropriate for world scale **[UE5 only]**.
- [ ] One-File-Per-Actor in source control: all actors committed, no missing references **[UE5 only]**.
- [ ] HLOD layers built and validated. No "Lowest Available LOD" for landscape HLOD **[UE5 only]**.
- [ ] Runtime Cell Transformers configured for decorative static meshes **[UE5.5+ only]**.

### Meshes / Models

- [ ] All non-Nanite static meshes have 3–4 LOD levels configured with `LODGroup = LargeProp / SmallProp / Vegetation`.
- [ ] Nanite meshes have Fallback Triangle Percent and Fallback Relative Error set (not at defaults for decorative props) **[UE5 only]**.
- [ ] GPU Skin Cache enabled in Project Settings for all projects with skeletal meshes.
- [ ] Skeletal meshes have URO enabled for non-player characters.
- [ ] Collision meshes are simplified (not complex-as-simple for high-poly meshes).
- [ ] Distance Field generation confirmed for all Lumen-critical and AO-relevant meshes.
- [ ] No Nanite on meshes below ~300 triangles **[UE5 only]**.
- [ ] WPO Disable Distance set on foliage assets **[UE5 only]**.
- [ ] Nanite WPO foliage: using opaque geometry leaves or Pivot Painter 2 approach **[UE5 only]**.
- [ ] No procedural foliage collision (use proximity sphere proxy instead).

### Lighting

- [ ] Shadow-casting light count audited. Only key lights cast shadows; fill lights do not.
- [ ] VSM Page Pool sized for the world: `r.Shadow.Virtual.MaxPhysicalPages` **[UE5 only]**.
- [ ] Lumen CVars tuned per scalability tier (DownsampleFactor, TracingOctahedronResolution) **[UE5 only]**.
- [ ] Lightmass builds complete and lightmap resolution appropriate **[UE4 only]**.
- [ ] Stationary Light overlap count verified — no more than 4 overlapping Stationary lights **[UE4 only]**.
- [ ] Reflection Captures placed and built. RVT configured for landscape blending **[UE4 + UE5]**.
- [ ] Hardware vs Software Lumen choice confirmed and documented **[UE5 only]**.
- [ ] Lumen building meshes modular (separate walls, floors, ceilings for interior GI) **[UE5 only]**.
- [ ] Emissive light sources backed with Point/Spot Light for stable GI during cuts **[UE5 only]**.
- [ ] `r.LumenScene.FarField.OcclusionOnly=1` enabled in UE5.6 for ~50% Far Field cost savings **[UE5.6+]**.

### Volumetrics

- [ ] Volumetric Fog Grid Size tuned: `r.VolumetricFog.GridPixelSize`, `r.VolumetricFog.GridSizeZ`.
- [ ] Volumetric Clouds shadow map ray count reduced for non-hero shots.
- [ ] Height Fog disabled or simple on platforms where volumetrics are too expensive.
- [ ] Fog bounds correct — no fog volume covering zero actual player area.

### Post Processing

- [ ] Post Process Volume(s) with `Infinite Extent` — only one should exist at the project root.
- [ ] Motion Blur, Depth of Field, Screen Space Reflections disabled or quality-reduced per scalability tier.
- [ ] Bloom kernel type: Convolution Bloom is expensive. Gaussian Bloom default is fine for most titles.
- [ ] TSR / DLSS / FSR configured and tested at target render resolution **[UE5 only]**.
- [ ] `r.PostProcessAAQuality` set appropriately per platform: 4 (TAA default), 6 (TSR high quality **[UE5 only]**).
- [ ] Auto-Exposure metering mode correct; UE5.1+ projects using `Min/Max EV100` not `Min/Max Brightness`.

### Streaming and Memory

- [ ] Texture streaming pool sized correctly: `r.Streaming.PoolSize` (MB). Default 800 MB; open world PC typically 2048–4096 MB.
- [ ] Nanite streaming pool sized: `r.Nanite.Streaming.StreamingPoolSize` (MB).
- [ ] No synchronous asset loads (`LoadSynchronous` in Tick or hot paths). Audit with Insights loadtime channel.
- [ ] Soft references used for large assets loaded on demand. Hard references audited with Size Map.
- [ ] Level Streaming vs World Partition streaming: no mixing of old Level Streaming with World Partition in the same world **[UE5 only]**.
- [ ] VT pool size adequate (`r.VT.PoolSizeScale` and per-pool settings). Monitor with `r.VT.Residency.Show 1`.

### Networking Sweep (Multiplayer Titles)

- [ ] Dormancy set on all static world actors (`DORM_DormantAll` + `FlushNetDormancy` on state change).
- [ ] Push Model enabled for frequently-polled replicated properties.
- [ ] `FFastArraySerializer` used for all replicated TArrays with per-element changes.
- [ ] `NetUpdateFrequency` and `MinNetUpdateFrequency` configured with Adaptive Frequency enabled.
- [ ] RPC reliability audit: `Unreliable` for cosmetics, `Reliable` only for critical gameplay events.
- [ ] Iris migration evaluated for projects shipping UE5.5+ **[UE5 only]**.

### Build and Cook Validation

- [ ] All maps cook clean with zero errors and minimal warnings.
- [ ] PSO cache captured from a gameplay playthrough and included in the cook **[console / PC shipping]**.
- [ ] DDC populated on build servers (no cold DDC on CI).
- [ ] Test build profiling pass completed with Insights (`cpu,frame,gpu,bookmark`).
- [ ] Automation test suite green (Blueprint compilation, map opens, custom perf tests).
- [ ] Memory budget verified on target platform hardware (not developer workstation).

---

## Top 30 Most Common Mistakes

| # | Mistake | Why It Hurts | Fix | Engine |
|---|---|---|---|---|
| 1 | Profiling in Editor PIE | 2–4× Game Thread overhead; all numbers unreliable | Always profile in Test packaged build | UE4 + UE5 |
| 2 | Tick enabled on every actor | Per-frame VM dispatch per actor even with empty graphs | Uncheck Start with Tick Enabled; enable per need | UE4 + UE5 |
| 3 | `Get All Actors Of Class` in Tick | O(n) world scan + TArray allocation every frame | Manager/subsystem registration pattern | UE4 + UE5 |
| 4 | Hard reference casts in UI Blueprints | Entire character class tree loads with every UI asset | Use interfaces; soft references; base type pins | UE4 + UE5 |
| 5 | Nanite on simple meshes (< 300 tri) | Cluster overhead > geometry savings; ~3 ms wasted for a handful of simple props | Use ISM batching for simple geometry | UE5 only |
| 6 | Nanite + Masked + WPO on foliage | Programmable Rasterizer = 2–4× Nanite cost; VSM shadow invalidation spike | Opaque geometry leaves; disable WPO shadow eval; set WPO Disable Distance | UE5 only |
| 7 | VSM Page Pool left at default 4096 in open world | Shadow stippling artifacts; overflow | `r.Shadow.Virtual.MaxPhysicalPages=8192` | UE5 only |
| 8 | Many Point Lights with Cast Shadows | Each VSM local light owns shadow pages; page pool overflow | Remove shadows from fill lights; use MegaLights for many dynamic lights | UE5 only |
| 9 | Lumen at Epic scalability without tuning | Designed for benchmarking hardware; too expensive in production | Tune DownsampleFactor, OctahedronResolution, MaxRoughnessToTrace per tier | UE5 only |
| 10 | Monolithic building mesh for Lumen | Interior gets no Lumen Cards → pink GI artifacts | Build modularly (walls, floor, ceiling separate) | UE5 only |
| 11 | Raw `UObject*` without `UPROPERTY` | GC collects object; dangling pointer | `UPROPERTY()` or `TObjectPtr<>` | UE4 + UE5 |
| 12 | Pure Blueprint function wired to multiple nodes | Re-evaluates N times for N consumers | Convert to impure; cache in variable | UE4 + UE5 |
| 13 | `FName` constructed from string in hot path | Thread lock + table search every call | `static const FName` | UE4 + UE5 |
| 14 | Array `Empty()` instead of `Reset()` in per-frame use | Frees and reallocates heap every frame | `Reset()` preserves allocation | UE4 + UE5 |
| 15 | `RemoveAt()` instead of `RemoveAtSwap()` on unordered arrays | O(n) shift vs O(1) swap | Use `RemoveAtSwap` when order doesn't matter | UE4 + UE5 |
| 16 | Missing `Replicates = true` on networked actor | No variables replicate, no RPCs fire | Check Class Defaults → Replication → Replicates | UE4 + UE5 |
| 17 | Actor dormancy left at `DORM_Never` on static world props | Per-frame replication polling on props that never change; 15 ms vs 0.13 ms per actor | `DORM_DormantAll` + `FlushNetDormancy` on change | UE4 + UE5 |
| 18 | Static Switch explosion in master material | 2ᴺ shader permutations; cook bloat; PSO stalls | Limit to < 6 switches; use Material Layering; Material Quality Switch | UE4 + UE5 |
| 19 | No URO on background NPCs | Full animation evaluation on all characters every frame | Enable URO per-component; use Animation Budget Allocator | UE4 + UE5 |
| 20 | UMG tick bindings for frequently-updated properties | Per-frame evaluation even when value unchanged | Event-driven updates via dispatchers | UE4 + UE5 |
| 21 | UMG `Hidden` instead of `Collapsed` for invisible widgets | `Hidden` still ticks and occupies layout | `Collapsed` skips layout and tick | UE4 + UE5 |
| 22 | Sound Concurrency not configured | Uncapped simultaneous voices; audio thread overrun | Create Concurrency assets; assign to Sound Classes | UE4 + UE5 |
| 23 | `std::shared_ptr<UObject>` | GC unaware; double-free / use-after-free | `UPROPERTY` / `TStrongObjectPtr` for UObjects | UE4 + UE5 |
| 24 | `this` captured raw in lambda delegates | Crash when actor is GC'd before lambda fires | `AddWeakLambda` or `MakeWeakObjectPtr` capture | UE4 + UE5 |
| 25 | Construction Script spawning actors | Orphaned actors per property change in editor | Child Actor Components or BeginPlay spawning | UE4 + UE5 |
| 26 | Fallback Mesh at `Fallback Relative Error = 0` in Nanite assets | Fallback copy = full source poly count; 100–400 MB VRAM bloat | Set Fallback Triangle Percent = 1–5%; Relative Error = 1.0 | UE5 only |
| 27 | Classic tessellation in UE5 project | Removed in UE5.0; material won't compile | Use Nanite Displacement (UE5.2+) | UE5 only |
| 28 | Blueprint Nativization expected in UE5 | Removed in UE5.0 | C++ Blueprint Function Libraries for hot paths | UE5 only |
| 29 | World Composition for new UE5 open world | Not developed; lacks WP features | World Partition for all new UE5 open world projects | UE5 only |
| 30 | HLOD "Lowest Available LOD" for landscape | Gray blob HLOD; visual regression and misleading perf data | Set Specific LOD = 4–5 in World Settings HLOD Setups | UE5 only |

---

## CVars Quick Reference

### Nanite CVars **[UE5 only]**

| CVar | Default | Tuning Notes |
|---|---|---|
| `r.Nanite.MaxPixelsPerEdge` | 1 | Higher = fewer triangles. Scalability: 1 (high), 2 (med), 4 (low) |
| `r.Nanite.Streaming.StreamingPoolSize` | 512 | MB. Increase for large open worlds; reduce for memory-constrained |
| `r.Nanite.Tessellation` | 0 | 1 = enable Nanite Displacement (requires plugin) |
| `r.Nanite.DicingRate` | 2 | Tessellation density. 1–2 for hero, 4–8 for background |
| `r.Nanite.AllowTessellation` | 0 | Enable per-mesh tessellation flag |

### Lumen CVars **[UE5 only]**

| CVar | Default | Tuning Notes |
|---|---|---|
| `r.Lumen.ScreenProbeGather.TracingOctahedronResolution` | 8 | Lower = faster, noisier. 4 is common for mid-range |
| `r.Lumen.ScreenProbeGather.DownsampleFactor` | 1 | 2 = large gains at some quality cost |
| `r.Lumen.ScreenProbeGather.IntegrateDownsampleFactor` | 1 | 2 = ~3× faster in UE5.6 |
| `r.Lumen.Reflections.DownsampleFactor` | 1 | 2 saves ~1–2 ms |
| `r.Lumen.Reflections.MaxRoughnessToTrace` | 0.6 | Lower = fewer surfaces get RT reflections |
| `r.LumenScene.FarField` | 0 | 1 = enable Far Field (>1km, needs HLOD1) |
| `r.LumenScene.FarField.OcclusionOnly` | 0 | 1 = ~50% cheaper Far Field in UE5.6 |
| `r.LumenScene.SurfaceCache.MeshCardsMinSize` | 4 | cm. Lower = more small meshes in Surface Cache |
| `r.LumenScene.SurfaceCache.CardMinResolution` | 4 | Increase only for hero props |
| `r.Lumen.ScreenProbeGather.MaxRayIntensity` | 10 | Firefly suppression (UE5.6 default) |

### Virtual Shadow Maps CVars **[UE5 only]**

| CVar | Default | Tuning Notes |
|---|---|---|
| `r.Shadow.Virtual.MaxPhysicalPages` | 4096 | 8192 for open world PC/PS5/XSX |
| `r.Shadow.Virtual.UseAsync` | 0 | 1 = async compute, hides ~0.4ms |
| `r.Shadow.Virtual.ResolutionLodBiasDirectional` | 0 | 1.0 for Steam Deck / low-end |
| `r.Shadow.Virtual.Clipmap.LastLevel` | 22 | Reduce to 20 if distant fog covers shadow range |
| `r.Shadow.Virtual.ResolutionLodBiasDirectionalMoving` | 0 | 0.5 = cheaper shadow pages during fast movement |
| `r.Shadow.Virtual.NonNanite.IncludeInCoarsePages` | 1 | 0 = large gains for foliage-heavy scenes |
| `r.Shadow.Virtual.Cache.MaxFramesSinceLastUsed` | 60 | Reduce to 20 during fast WP streaming |
| `r.Shadow.Virtual.Cache.MaxMaterialPositionInvalidationRange` | 10 | Limit WPO shadow invalidation radius |
| `r.Shadow.Virtual.Cache.DrawInvalidatingBounds` | 0 | Debug: green boxes = VSM cache invalidators |

### Streaming CVars **[UE4 + UE5]**

| CVar | Default | Tuning Notes |
|---|---|---|
| `r.Streaming.PoolSize` | 800 | MB. Open world PC: 2048–4096; NEVER 0 |
| `r.Streaming.MipBias` | 0 | 1–2 reduces texture quality to save memory |
| `r.Streaming.LimitPoolSizeToVRAM` | 0 | 1 = auto-cap pool to available VRAM |
| `r.Streaming.MaxTempMemoryAllowed` | 50 | MB temporary upload budget |

### Niagara CVars **[UE5 primarily; some UE4]**

| CVar | Default | Tuning Notes |
|---|---|---|
| `fx.Niagara.QualityLevel` | 3 | 0=off, 3=full. Bind to scalability |
| `fx.Niagara.SystemSimulationTickBatchSize` | 8 | Higher = more GPU batch efficiency |
| `fx.NiagaraMaxGPUCount` | 1000000 | Hard cap GPU particle count |
| `fx.Niagara.MaxGPUParticlesSpawnPerFrame` | variable | Hard cap GPU spawns per frame |

### Replication CVars **[UE4 + UE5]**

| CVar | Default | Tuning Notes |
|---|---|---|
| `net.UseAdaptiveNetUpdateFrequency` | 0 | 1 = enable adaptive frequency |
| `TotalNetBandwidth` | 15000 | Bytes/sec. Increase for modern games |
| `net.Iris.UseIrisReplication` | 0 | 1 = Iris (UE5.4+) |
| `net.MaxNetTickRate` | 120 | Server tick rate cap |

### Animation CVars **[UE4 + UE5]**

| CVar | Default | Tuning Notes |
|---|---|---|
| `a.URO.Enable` | 1 | Per-component opt-in still required |
| `r.SkinCache.Mode` | 0 | 0=off, 1=on, 2=with recompute tangents |
| `r.SkeletalMeshLODBias` | 0 | +1 = all meshes one LOD lower globally |
| `r.MorphTarget.EnabledByDefault` | 0 | 1 = GPU morph targets (UE5) |
| `tick.AnimationBudgetAllocator.Enabled` | 1* | Plugin must be enabled (*if plugin on) |
| `tick.AllowBatchedTicks` | 0 | 1 = batch similar tick functions (UE5.5+) |

### Materials and Post-Process CVars **[UE4 + UE5]**

| CVar | Default | Tuning Notes |
|---|---|---|
| `r.MaterialQualityLevel` | 3 | 0=Low, 1=Medium, 2=High, 3=Epic |
| `r.MaxAnisotropy` | 4 | Texture filter quality |
| `r.BloomQuality` | 5 | 0=off, 5=default, 6=convolution |
| `r.MotionBlurQuality` | 4 | 0=off, 4=max |
| `r.DepthOfFieldQuality` | 4 | 0=off, 4=max |
| `r.EyeAdaptation.MethodOverride` | -1 | -1=none, 0=basic, 1=histogram, 2=manual |
| `r.CompileShadersOnDemand` | 1 | 0 = compile all during cook |
| `r.ShaderPipelineCache.Enabled` | 1 | PSO cache usage |

### GC and Code CVars **[UE4 + UE5]**

| CVar | Default | Tuning Notes |
|---|---|---|
| `gc.TimeBetweenPurgingPendingKillObjects` | 60 | Seconds between GC passes |
| `gc.MaxObjectsNotConsideredByGC` | 0 | Objects above this index skipped in marking |
| `gc.AssetClusteringEnabled` | 1 | GC clustering for assets |

### Occlusion, Volumetrics, and Environment CVars **[UE4 + UE5]**

| CVar | Default | Tuning Notes |
|---|---|---|
| `r.HZBOcclusion` | 1 | Set 0 to debug HZB culling artifacts |
| `r.VolumetricFog.GridPixelSize` | 16 | Tile size per froxel (8 = high quality) |
| `r.VolumetricFog.GridSizeZ` | 64 | Z slices (128 = smoother light shafts) |
| `r.VT.PoolSizeScale` | 1.0 | Scale multiplier for all VT pool sizes |
| `r.VT.Residency.Show` | 0 | Pool occupancy HUD |
| `foliage.DensityScale` | 1.0 | Scale foliage instance counts per scalability |
| `r.AmbientOcclusion.Intensity` | 1.0 | Set to 0 when using Lumen GI |
| `r.ReflectionCaptureResolution` | 128 | Reduce to 64 for background captures |

---

## Bibliography and Further Reading

### Talks (Unreal Fest, GDC)

- [Optimizing the Game Thread — Unreal Fest 2024 (Jake Simpson)](https://www.youtube.com/watch?v=KxREK-DYu70)
- [Nanite for Artists — GDC 2024](https://www.youtube.com/watch?v=eoxYceDfKEM)
- [An Artist's Guide to Nanite Tessellation — Unreal Fest 2024](https://www.youtube.com/watch?v=6igUsOp8FdA)
- [The Future of Nanite Foliage — Unreal Fest Stockholm 2025](https://www.youtube.com/watch?v=aZr-mWAzoTg)
- [TSR/Nanite/Lumen/VSM Insights — Unreal Fest Gold Coast 2024](https://www.youtube.com/watch?v=szgnZx2b0Zg)
- [Scaling for Quality and Performance — Unreal Fest Bali 2025](https://www.youtube.com/watch?v=Q1whHlGJB_o)
- [Lumen with Immortalis — Arm/Epic Unreal Fest 2023](https://www.slideshare.net/slideshow/unreal-fest-2023-lumen-with-immortalis/266167635)
- [Culling & Occlusion in Unreal (2025)](https://www.youtube.com/watch?v=wOdpF4WMckE)

### Blogs and Articles

**Tom Looman:**
- [Tom Looman — UE5.6 Performance Highlights](https://tomlooman.com/unreal-engine-5-6-performance-highlights/)
- [Tom Looman — UE5.5 Performance Highlights](https://tomlooman.com/unreal-engine-5-5-performance-highlights/)
- [Tom Looman — Adding Counters and Traces](https://tomlooman.com/unreal-engine-profiling-stat-commands/)
- [Tom Looman — Asset Manager and Async Loading](https://tomlooman.com/unreal-engine-asset-manager-async-loading/)
- [Tom Looman — Optimization Talk](https://tomlooman.com/unreal-engine-optimization-talk/)

**Ben Cloward:**
- [Ben Cloward — HLSL Tutorial (YouTube)](https://www.youtube.com/watch?v=qaNPY4alhQs)

**William Faucher:**
- [William Faucher YouTube Channel](https://www.youtube.com/@WilliamFaucher) — Lumen, lighting, cinematic rendering

**Alex Forsythe:**
- [Alex Forsythe — Blueprints vs C++](http://awforsythe.com/unreal/blueprints_vs_cpp/)
- [Alex Forsythe YouTube Channel](https://www.youtube.com/@AlexForsythe)

**StraySpark:**
- [StraySpark — World Partition Deep Dive](https://www.strayspark.studio/blog/ue5-world-partition-deep-dive-streaming-hlod)
- [StraySpark — VSM Optimization for Open Worlds](https://www.strayspark.studio/blog/virtual-shadow-map-optimization-open-worlds-ue5-7)
- [StraySpark — Lumen 60fps Guide](https://www.strayspark.studio/blog/ue5-lumen-optimization-60fps)
- [StraySpark — Nanite Foliage Guide](https://www.strayspark.studio/blog/nanite-foliage-ue5-complete-guide)

**Intel:**
- [Intel — UE5 Optimization Guide Chapter 2](https://www.intel.com/content/www/us/en/developer/articles/technical/unreal-engine-optimization-chapter-2.html)
- [Intel — UE5 Profiling Fundamentals](https://www.intel.com/content/www/us/en/developer/articles/technical/unreal-engine-optimization-profiling-fundamentals.html)

**AMD GPUOpen:**
- [AMD GPUOpen — Unreal Engine Performance Guide](https://gpuopen.com/learn/unreal-engine-performance-guide/)

**NVIDIA:**
- [NVIDIA — UE5.4 Raytracing Guide (PDF)](https://dlss.download.nvidia.com/uebinarypackages/Documentation/UE5+Raytracing+Guideline+v5.4.pdf)

**Other Technical References:**
- [Intax — Blueprint VM Performance Guide](https://intaxwashere.github.io/blueprint-performance/)
- [George Prosser — Optimizing TWeakObjectPtr](https://prosser.io/optimizing-tweakobjectptr-usage/)
- [xbloom.io — World Partition Internals](https://xbloom.io/2025/10/24/unreals-world-partition-internals/)
- [Chris McCole — Culling in UE4/UE5](https://www.chrismccole.com/blog/culling-in-ue4ue5)
- [Matt Gibson — Unreal Replication Settings](https://mattgibson.dev/blog/unreal-replication-settings)
- [Kieran Newland — Replication Graph Tutorial](https://www.kierannewland.co.uk/replication-graph)
- [ikrima.dev — Fast TArray Replication](https://ikrima.dev/ue4guide/networking/network-replication/fast-tarray-replication/)
- [rick.me.uk — C++ Profiling in Unreal Engine 5](https://www.rick.me.uk/posts/2024/12/cpp-profiling-in-unreal-engine-5/)
- [kantandev.com — UE4 Includes, PCH, and IWYU](http://kantandev.com/articles/ue4-includes-precompiled-headers-and-iwyu-include-what-you-use)
- [unrealcommunity.wiki — Memory Management](https://unrealcommunity.wiki/memory-management-6rlf3v4i)
- [unrealcommunity.wiki — Hot Reload and Live Coding](https://unrealcommunity.wiki/live-compiling-in-unreal-projects-tp14jcgs)
- [unrealcommunity.wiki — Profiling with Unreal Insights](https://unrealcommunity.wiki/profiling-with-unreal-insights-ilad24y4)
- [Simplygon — HLOD Builder for World Partition](https://www.simplygon.com/posts/54162a3d-390c-47f0-bb55-6fed2f626bd8)
- [Robert Lewicki — Lambda Weak Pointer Captures](https://unreal.robertlewicki.games/p/daily-unreal-column-50-capture-weak)
- [voithos.io — Fancier Ticking in Unreal](https://voithos.io/articles/fancier-ticking-in-unreal/)
- [Tech-Artists.Org — Draw Call Optimization in UE5](https://www.tech-artists.org/t/draw-call-optimization-in-ue5/18217)
- [Kokku Games — Blueprint Diff with Git](https://kokkugames.com/tutorial-stop-guessing-what-changed-in-your-blueprintsgit-blueprint-diff-inside-unreal-engine/)
- [Rév O'Conner — Texture Compression and BCn](https://www.revoconner.com/post/texture-compression-for-unreal-engine-bcn-and-texture-packing)
- [TechArtHub — Texture Streaming Pool](https://techarthub.com/fixing-texture-streaming-pool-over-budget-in-unreal/)
- [Froyok — Render Target Performance Analysis](https://www.froyok.fr/blog/2020-06-render-target-performances/)
- [KitBash3D — Level Instances and Packed Level Actors](https://help.kitbash3d.com/en/articles/12038349-a-quick-guide-packed-level-actors-level-instancing-in-unreal-engine-with-kitbash3d)
- [Outscal — Timers vs Tick Guide](https://outscal.com/blog/unreal-engine-timers-vs-tick)
- [CBgameDev — UE4/UE5 Optimising Tick Rate](https://www.cbgamedev.com/blog/quick-dev-tip-74-ue4-ue5-optimising-tick-rate)
- [Brushify — RVT Bootcamp (YouTube)](https://www.youtube.com/watch?v=0-xXIMjlmqE)
- [Epic Developer Community — Tasks System](https://dev.epicgames.com/documentation/unreal-engine/tasks-systems-in-unreal-engine)
- [Georgy's Tech Blog — How to Use Mutex in UE](https://georgy.dev/posts/mutex/)
- [Coconut Lizard — Strings and Other Things](https://www.coconutlizard.co.uk/blog/strings-and-other-things/)
- [Daanmeysman ArtStation — Quad Overdraw and Triangles](https://daanmeysman.artstation.com/blog/7goy/keeping-your-games-optimized-part-1-triangles)
- [MoreVFX Academy — Niagara Optimization Guide](https://morevfxacademy.com/complete-guide-to-niagara-vfx-optimization-in-unreal-engine/)
- [Georgy Prosser — Optimizing TWeakObjectPtr](https://prosser.io/optimizing-tweakobjectptr-usage/)
- [Intax Blueprint Performance Guide](https://intaxwashere.github.io/blueprint-performance/)

### Official Documentation (dev.epicgames.com)

- [Unreal Insights](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-insights-in-unreal-engine)
- [Memory Insights](https://dev.epicgames.com/documentation/en-us/unreal-engine/memory-insights-in-unreal-engine)
- [Networking Insights](https://dev.epicgames.com/documentation/en-us/unreal-engine/networking-insights-in-unreal-engine)
- [Visibility and Occlusion Culling](https://dev.epicgames.com/documentation/unreal-engine/visibility-and-occlusion-culling-in-unreal-engine)
- [Tasks System in Unreal Engine](https://dev.epicgames.com/documentation/unreal-engine/tasks-systems-in-unreal-engine)
- [Developer Guide to Tracing](https://dev.epicgames.com/documentation/en-us/unreal-engine/developer-guide-to-tracing-in-unreal-engine)
- [Getting Started with Editor Utility Blueprints](https://dev.epicgames.com/community/learning/tutorials/owYv/unreal-engine-getting-started-with-editor-utility-blueprints)

### YouTube Channels

- [Ben Cloward](https://www.youtube.com/@BenCloward) — materials, HLSL, shader development
- [William Faucher](https://www.youtube.com/@WilliamFaucher) — Lumen, lighting, cinematic rendering
- [Tom Looman](https://www.youtube.com/@TomLoomanton) — C++, AI, gameplay systems in UE5
- [Alex Forsythe](https://www.youtube.com/@AlexForsythe) — Blueprint vs C++, architecture

### Repositories and Community References

- [Awesome Unreal (GitHub)](https://github.com/insthync/awesome-unreal) — curated list of UE resources
- [unrealcommunity.wiki](https://unrealcommunity.wiki) — community-maintained wiki with deep dives
- [Epic Developer Community](https://dev.epicgames.com/community/) — official tutorials and Knowledge Base
- [r/unrealengine](https://www.reddit.com/r/unrealengine/) — community Q&A and real-world experience sharing

### Epic Forums and Knowledge Base

- [Epic Forums — GC Clustering Internals](https://forums.unrealengine.com/t/knowledge-base-garbage-collector-internals/501800)
- [Epic Forums — Why Use TObjectPtr?](https://forums.unrealengine.com/t/why-should-i-replace-raw-pointers-with-tobjectptr/232781)
- [Epic Forums — Blueprint Nativization Removed](https://forums.unrealengine.com/t/why-was-blueprint-nativization-removed-no-code-preaching/232490)
- [Epic Forums — Nanite VRAM Fallback Thread](https://forums.unrealengine.com/t/nanite-fallback-mesh-buffers-vram-residence/2563974)
- [Epic Forums — When to Use Level Instance/PLA/ISM/HISM](https://forums.unrealengine.com/t/when-to-use-level-instance-packed-level-actor-or-ism-hism-in-ue5/2681508)
- [Epic Forums — Iris Bandwidth Control (UE5.5)](https://forums.unrealengine.com/t/how-is-server-to-client-bandwidth-controlled-in-iris-in-ue-5-5/2675046)
- [Epic Forums — Shader Permutations Knowledge Base](https://forums.unrealengine.com/t/knowledge-base-understanding-shader-permutations/264928)
- [Epic Forums — OFPA Best Practices](https://forums.unrealengine.com/t/tips-and-best-practices-for-one-file-per-actor/837886)
- [Epic Forums — Lumen Surface Cache Scale](https://forums.unrealengine.com/t/lumen-surface-cache-scale-woes/2669365)

---

## Extended Reference: UE4 vs UE5 Feature Mapping

### Render Feature Equivalence Table

| UE4 Feature | UE5 Equivalent | Notes |
|---|---|---|
| Cascaded Shadow Maps (CSM) | Virtual Shadow Maps (VSM) | VSM is default in UE5; CSM still available |
| Lightmass CPU/GPU | GPU Lightmass | GPU Lightmass is default in UE5 |
| TAAA / TAA | TSR | TSR default in UE5; TAA still available |
| Screen Space Reflections (SSR) | Lumen Reflections | Lumen is default; SSR fallback still available |
| Screen Space AO (SSAO) | Lumen GI / Distance Field AO | SSAO still available; often disabled with Lumen |
| Cascade Particles | Niagara | Cascade available but deprecated |
| Hot Reload | Live Coding | Live Coding is default in UE5 |
| World Composition | World Partition | WP is default for new open world projects |
| Blueprint Nativization | C++ Blueprint Function Libraries | Nativization removed in UE5.0 |
| Classic Tessellation | Nanite Tessellation (UE5.3+) | Classic removed in UE5.0 |
| Sound Cues (primary) | MetaSounds (primary) | Sound Cues still work in UE5 |
| Reflection Captures (only) | Lumen Reflections + Captures | Lumen handles dynamic; captures for static |
| Replication Net Driver (legacy) | Iris (UE5.4+) | Iris opt-in, default-eligible in UE5.5+ |

### Key UPROPERTY Changes UE4 → UE5

| UE4 Pattern | UE5 Recommended Pattern | Notes |
|---|---|---|
| `T* MyPtr;` (raw with UPROPERTY) | `TObjectPtr<T> MyPtr;` | TObjectPtr required for incremental GC in 5.4+ |
| `MarkPendingKill()` | `MarkAsGarbage()` | API renamed in UE5 |
| `IsPendingKill()` | `IsGarbage()` / `!IsValid()` | API renamed in UE5 |
| `GC.TimeBetweenPurgingPendingKillObjects` | Same, but with incremental GC option | UE5 adds incremental GC configuration |
| `CreateDefaultSubobject` (same) | Same — but requires full restart on name changes | Unchanged; Live Coding unsafe for name changes |

---

Last revised: 2025. Guide version: 3.0 (Merged Edition). This is a living document — verify CVars and version notes against current engine source for your specific UE version. CVar defaults may differ between minor versions.

---

## Extended Reference: Profiling Patterns

### Common Frame Spike Patterns and Solutions **[UE4 + UE5]**

| Spike Type | Symptom in Insights | Likely Cause | Fix |
|---|---|---|---|
| GC hitch | `FGarbageCollection::Collect` spike every N seconds | Too many UObjects, no GC clusters | Enable clustering; reduce transient UObject creation |
| Streaming hitch | `RequestAsyncLoad` stall in Game Thread | Synchronous asset load in hot path | Async loading; pre-warm content bundles |
| Shader compile stall | First-time draw of a unique material | PSO cache miss | Pre-warm PSO cache from a capture playthrough |
| Physics spike | `SyncComponentsToRBPhysics` wide bar | Overconstrained physics, too many substeps | Simplify collision; reduce substeps |
| Render Thread spike | `Nanite::DrawPass::Rasterize` wide | Nanite overdraw from dense overlapping geometry | Reduce overlap; adjust MaxPixelsPerEdge |
| Level streaming hitch | `UWorldPartition::RequestLoading` spike | Cell size too small; too many actors per cell | Increase Cell Size; use Runtime Cell Transformers |

### TRACE_BOOKMARK Workflow for Automated Regression **[UE5.3+]**

Trace bookmarks + Regions enable automated regression comparison across builds:

```cpp
// Mark gameplay events for later correlation:
TRACE_BOOKMARK(TEXT("PlayerEnteredCombatZone"));
TRACE_BOOKMARK(TEXT("BossSpawned::%s"), *BossName.ToString());

// Tag a region for automated timer export:
uint64 RegionId = TRACE_BEGIN_REGION_WITH_ID(TEXT("Wave3"));
// ... wave 3 gameplay ...
TRACE_END_REGION_WITH_ID(RegionId);
```

Automated CLI export after trace capture:
```bash
UnrealInsights.exe -AutoQuit -NoUI -OpenTraceFile="capture.utrace" \
  -ExecOnAnalysisCompleteCmd="TimingInsights.ExportTimerStatistics results.csv -region=Wave3 -threads=GPU"
```

This enables build-over-build regression tracking in CI: capture a standard trace, export GPU timers for a known scenario, compare against a baseline CSV. Frame time budgets can silently erode week-over-week without automated detection.

### Identifying the Frame Budget Breakdown **[UE4 + UE5]**

The three threads run in parallel — the effective frame time is the maximum of all three, not the sum. A project with 7 ms Game Thread, 9 ms Render Thread, and 14 ms GPU is GPU-bound at 14 ms effective frame time. You cannot fix a GPU-bound scene by optimizing C++ code.

**Profiling channel selection guide:**

| Goal | Command-line / CVar |
|---|---|
| CPU + default | `-trace=default` |
| Memory allocations | `-trace=memory_light,memtags` |
| Full memory + asset metadata | `-trace=memory,metadata,assetmetadata` |
| Named events (class/actor detail) | `-statnamedevents` (~20% overhead — targeted use only) |
| Asset load timing | `loadtime,assetloadtime` |
| Network analysis | `-NetTrace=1 -trace=net` |

Memory snapshot: `Trace.SnapshotFile` captures a point-in-time snapshot during a live session. For the best asset breakdown, define `LLM_ALLOW_ASSETS_TAGS=1` in `.target.cs`.

---

## Extended Reference: Networking Deep Dive

### Conditional Replication Patterns **[UE4 + UE5]**

```cpp
void AMyActor::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    
    // Only replicate to the owning connection (private per-player data):
    DOREPLIFETIME_CONDITION(AMyActor, PrivateInventory, COND_OwnerOnly);
    
    // Skip replication to the owner (they already know this from input):
    DOREPLIFETIME_CONDITION(AMyActor, ServerSimulatedPosition, COND_SkipOwner);
    
    // Only replicate once after spawn (immutable setup data):
    DOREPLIFETIME_CONDITION(AMyActor, CharacterClass, COND_InitialOnly);
    
    // Push model (only replicate when marked dirty):
    FDoRepLifetimeParams PushParams;
    PushParams.bIsPushBased = true;
    DOREPLIFETIME_WITH_PARAMS_FAST(AMyActor, Health, PushParams);
}
```

`COND_OwnerOnly` is the single most impactful replication condition for private per-player state (inventory, ability cooldowns, local UI state). Without it, private data replicates to all clients — a bandwidth waste and a security concern in competitive games.

### Replication Graph Spatial Grid Setup **[UE4.20+ / UE5]**

For large player counts (50+), the Replication Graph plugin replaces the default Net Driver's per-actor relevancy O(n) check with spatial grids:

```cpp
// In your ReplicationGraph subclass:
UReplicationGraphNode_GridSpatialization2D* GridNode = CreateNewNode<UReplicationGraphNode_GridSpatialization2D>();
GridNode->CellSize = 10000.0f;    // 100m spatial cells
GridNode->SpatialBias = FVector2D(-500000.0f, -500000.0f);  // world offset
AddGlobalGraphNode(GridNode);
```

Actors in spatial cells outside a client's view cone stop replicating automatically. For Fortnite-scale projects this is essential; for 8-player co-op it is overkill.

### Server-Side Move Validation **[UE4 + UE5]**

For physics-based movement with `CharacterMovementComponent`, the server always re-simulates the move from the client's inputs. Do not disable this. However, the tolerance thresholds for position reconciliation (`MaxClientSmoothingDeltaTime`, `NetworkMaxSmoothUpdateDistance`) control when the server forces a correction. Tune these per-game: a tight platformer needs strict correction; an exploration game may tolerate larger position divergence.

---

## Extended Reference: Build, Cook, and Iteration

### Derived Data Cache (DDC) Strategy **[UE4 + UE5]**

The DDC stores compiled shaders, cooked assets, and derived data keyed by source asset hash + build settings. Cold DDC on a fresh checkout forces full shader recompilation, which can take many hours.

CI/CD best practices:
- Run a nightly full cook on a build server and push results to a shared DDC (`SharedDDCPath` in `Engine.ini`).
- Developer machines pull from shared DDC, only recompiling assets they have changed.
- Epic's `Zen Store` (UE5.4+) replaces the legacy shared DDC with a content-addressable, version-tolerant cache server with REST API. Recommended for teams larger than 5 developers.

```ini
; DefaultEngine.ini (developer workstation):
[DerivedDataBackend]
Root=(Type=KeyLength, Length=120, Inner=AsyncPut)
AsyncPut=(Type=AsyncPut, Inner=Hierarchy)
Hierarchy=(Type=Hierarchical, Inner=Boot, Inner=Shared, Inner=Local)
Local=(Type=FileSystem, ReadOnly=false, Clean=false, Flush=false, PurgeTransient=true, DeleteUnused=true, UnusedFileAge=34, FoldersToClean=-1, Path=%ENGINEVERSIONAGNOSTICUSERDIR%DerivedDataCache)
Shared=(Type=FileSystem, ReadOnly=false, Clean=false, Flush=false, DeleteUnused=true, UnusedFileAge=10, FoldersToClean=10, Path=\\BuildServer\DDC, EnvPathOverride=UE-SharedDataCachePath)
Boot=(Type=Boot, Path=%GAMEINIDIR%Boot.ddc, MaxCacheSize=128)
```

### Live Coding Safe Practices **[UE4.22+ / UE5 default]**

Live Coding (`Ctrl+Alt+F11` by default) hot-patches function bodies in the running editor. Safe for:
- Logic changes inside `.cpp` function bodies
- Adding new local variables within functions
- Changing constants and literals

Unsafe (requires full editor restart):
- Adding/removing `UPROPERTY` or `UFUNCTION` declarations
- Changing struct layouts (replicated or not)
- Adding/removing virtual functions or virtual overrides
- Changing `CreateDefaultSubobject` names
- Modifying `GENERATED_BODY()` or `GENERATED_UCLASS_BODY()` macros

**[Deprecated in UE5]**: Hot Reload (the legacy `Ctrl+Alt+F11` mechanism in UE4) was replaced by Live Coding as the default in UE4.22. Enable reinstancing in `DefaultEngine.ini` to reduce Blueprint corruption risk during Live Coding of classes derived from Blueprints:
```ini
[/Script/LiveCoding]
bInstallInEngineFolder=false
```

### Module Organization for Large Projects **[UE4 + UE5]**

- Keep `Public/` headers minimal and stable; put implementation in `Private/`.
- `PublicDependencyModuleNames` transitively exposes headers to dependents. Use `PrivateDependencyModuleNames` for everything not in your public API.
- `PrivateIncludePaths` prevents internal headers from leaking transitively.
- Prefer a plugin over a module when the code ships as optional or has its own versioning lifecycle.
- Target a clean build time under 3 minutes for your most-changed module — if it exceeds this, split it further.
- Setting `bFasterWithoutUnity = true` in a specific module's `Build.cs` disables unity batching only for that module — useful for modules in constant flux without penalizing the entire build.

---

## Extended Reference: GC, Memory, and Container Patterns

### GC Clusters **[UE4 + UE5]**

GC clusters reduce the marking phase cost by grouping objects with the same lifetime. Once grouped, GC traverses the cluster root rather than each member individually. Enabling `gc.AssetClusteringEnabled 1` and Blueprint clustering in Project Settings > Engine > Garbage Collection saves 50%+ of marking time for clustered objects.

```cpp
void UMyDataAsset::PostLoad()
{
    Super::PostLoad();
    CreateCluster(); // Scans all sub-objects and groups them
}
```

### UObject Allocation Patterns **[UE4 + UE5]**

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

The Class Default Object (CDO) is created once per class at engine startup. The constructor runs only for the CDO — every subsequent instance is a copy. This means:
- Never put runtime logic in constructors (map lookups, asset loads, actor queries).
- Renaming a `CreateDefaultSubobject` component between hot reloads corrupts Blueprint assets derived from that class.

### Container Performance Patterns **[UE4 + UE5]**

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

FName pitfalls:
- The name table is NEVER GC'd — every unique string added at runtime grows it forever. With procedurally generated names in long sessions, the table can consume significant memory.
- Constructing an `FName` from a string literal in a hot path is expensive — it acquires a thread lock and searches the name table.

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

| Type | Storage | Comparison | When to Use |
|---|---|---|---|
| `FString` | Heap-allocated `TArray<TCHAR>` | O(n) | Dynamic text construction, I/O |
| `FName` | Global name table index | O(1) integer | Asset names, identifiers, map keys |
| `FText` | Immutable + localization metadata | O(?) | User-facing UI strings, localization |

---

## Extended Reference: Materials and Shaders — Advanced Patterns

### Dynamic Switch vs Static Switch — A Critical Distinction **[UE4 + UE5]**

The `Switch Parameter` node (dynamic) and `Static Switch Parameter` node behave fundamentally differently at the GPU level:

- **Static Switch**: The dead branch is eliminated by the shader compiler. Zero runtime cost for the discarded path. But generates additional shader permutations (one per unique combination of static switch values in instances). Two switches = 4 permutations; eight switches = 256 permutations.
- **Dynamic Switch**: Both branches are compiled into the shader. Both branches consume instruction budget even when not taken. On AMD GPUs, hitting a context roll from mismatched PSO states with many dynamic switches can cause stalls.

Rule: use Static Switches for quality tier variations, two-sided vs. one-sided, and opaque vs. masked mode changes. Use dynamic switches only when the change happens at runtime per-instance (e.g., an actor going wet vs. dry). From [community testing](https://www.reddit.com/r/unrealengine/comments/1hvldzb/so_i_was_always_told_that_switch_params_on/), the Shader Complexity view clearly shows dynamic switch branches burning instructions even when disabled.

A `Switch Parameter` (dynamic) does NOT eliminate branches — both sides are compiled and evaluated. In Shader Complexity view you can clearly see that a disabled dynamic switch branch still burns instructions. Rule: keep static switches below ~5 per master material. Use Material Layering or Material Functions to break up complexity instead of cramming everything into one monolithic graph.

### Custom HLSL Node Reference **[UE4 + UE5]**

The `Custom` node allows raw HLSL inline — essential for packed texture decoding, raymarching, complex math, and reducing node-graph spaghetti ([Ben Cloward's HLSL tutorial](https://www.youtube.com/watch?v=qaNPY4alhQs)).

Complete pitfall list:
- **No preview**: the Custom node renders black in Material Editor thumbnail. Test by applying to a mesh in the viewport.
- **TEXCOORD overflow**: limit of 8 UV interpolators (16 in UE5 with additional cost). Use the `Customized UVs` panel to pre-pack data into UV slots.
- **Texture sampling syntax**: use `Texture2DSample(Tex, TexSampler, UV)` where the sampler is a separate input pin (TextureObject input). Cannot use `tex2D()` directly in SM5 pixel shaders.
- **Loop unrolling**: the HLSL compiler aggressively unrolls loops. Add `[loop]` for dynamic loop counts that must not be unrolled.
- **Helper functions**: can be wrapped in a struct declaration or included via `#include "/Engine/Private/Common.ush"`.
- **View uniforms**: Custom nodes can read `View.ViewToClip`, `View.WorldToView`, and other view-uniform data. Document what uniforms you reference so future artists know the dependency.

### WPO Performance — Complete Guide **[UE5 only]**

WPO was unsupported in early Nanite (UE5.0). Available from UE5.1, with significant improvements in UE5.4 where per-cluster WPO range culling was added.

Key setting: `Max World Position Offset Displacement` in the material. Nanite uses this value to cull clusters that cannot be affected by WPO. Setting it too high disables culling; setting it to 0 disables WPO entirely for that material. This is the single most impactful WPO knob in production.

Velocity buffer: materials with WPO must write per-vertex velocity for correct TSR/motion blur. Enable `Output Velocity` in the material properties (enabled by default for WPO materials).

PDO + Lumen ghosting: when PDO is active and Lumen's temporal GI is accumulating, displaced pixels cause smearing during camera movement. Mitigation: keep PDO displacement short-range, or disable Lumen screen traces for PDO-heavy surfaces.

### Runtime Virtual Texture (RVT) — Complete Setup **[UE4.23+ / UE5]**

RVT is a render target that the landscape writes into every frame, and objects sample from for context-sensitive shading. Primary use cases: landscape blending at object bases, footprint/decal stamping, terrain-conforming roads.

Setup checklist:
1. Create a `Runtime Virtual Texture` asset.
2. Place a `Runtime Virtual Texture Volume` over the landscape.
3. Assign the RVT asset to the volume; set bounds from the landscape.
4. Add the RVT to the landscape's Virtual Textures array.
5. Modify the landscape material: add `Runtime Virtual Texture Output` node.
6. Modify prop materials: add `Runtime Virtual Texture Sample` node.

VT thrashing signs: visible resolution flickering, red pool graph (`r.VT.Residency.Show`). Causes: undersized pool, negative mip bias on VT Sample nodes, zero-gradient UV sampling (requests mip 0 for entire surface). Monitor with `r.VT.Residency.Show 1` — if the green (mip bias applied) value is non-zero, the engine is degrading texture resolution.

---

## Extended Reference: Niagara VFX — Advanced Patterns

### Niagara Scalability and Effect Types **[UE4.20+ / UE5]**

The `Niagara Effect Type` asset is the global control center for scalability: cull distances, max instances, spawn count scales, and budget limits. Every Niagara system should have an Effect Type assigned.

Per-system scalability settings to configure per quality level:

| Setting | Purpose |
|---|---|
| `Spawn Count Scale` | Reduce particle count at lower quality |
| `Cull Distance` | Hard kill beyond world-space distance |
| `Max Instances` | Cap on concurrent system instances |
| `Update Frequency` | Reduce tick rate for background effects |

The Significance Handler within the Effect Type determines which systems survive budget pressure: `Distance` (closest wins), `Age` (newest wins), `Custom`. For bullet impacts with max 100 instances, Distance ensures only the nearest impacts render.

### Niagara Data Channels (NDC) — Deep Dive **[UE5.3+]**

NDC allows different Niagara systems to communicate asynchronously — one system writes data, another reads it in the same frame. It replaces the older event system for cross-emitter spawning patterns and global VFX state.

Architecture: NDC data is completely transient — it exists for a single tick. If you miss a frame, the data is gone. Use for:
- Bullet impacts spawning multiple effect types from one location
- Rain writing wetness data read by puddle splashes
- Global wind direction affecting all outdoor particle systems without Blueprint overhead
- Crowd systems publishing density data read by ground-disturbance effects

Key limitation: NDC cannot be used to pass persistent state between frames. For persistent shared state, use a Render Target, a Texture2D written per frame, or a C++ Data Asset.

### GPU Simulation — Fixed Bounds and Distance Fields **[UE4 + UE5]**

GPU simulations require fixed bounds. Without fixed bounds, the GPU does not dispatch the compute shader when the system's bounding box is off-screen — the effect disappears silently as the camera rotates. Use `Fix Bounds` in Niagara Editor after tuning the effect. For traveling effects (projectile trails), expand bounds generously.

GPU particle Distance Field collision uses the Global Distance Field — a coarse, scene-wide approximation with an effective range of ~10,000 units from the camera. Beyond that range, collisions become unreliable. `Particle Radius Scale` default 0.1 is often too small for reliable collision detection; increase to 1.0–5.0 for visible effects.

GPU readback (UE5.3+): GPU particles can export data back to CPU/Blueprint at a measurable cost. Always profile with `stat Niagara` before relying on GPU readback in production.

---

## Extended Reference: Audio Advanced Patterns

### Sound Concurrency Deep Dive **[UE4 + UE5]**

Sound Concurrency assets define how the engine handles budget overruns for a sound category.

| Parameter | Effect |
|---|---|
| `MaxCount` | Maximum simultaneous active sounds |
| `ResolutionRule` | `StopQuietest`: kill the quietest active sound. `PreventNew`: reject new sounds when at cap |
| `RetriggerTime` | Minimum seconds between new instances (prevents rapid-fire spam) |
| `MaxDistance` | Only count sounds within this world distance toward the cap |
| `VolumeScaleMode` | Scale volume of all active sounds when at cap |

Sound Classes form a hierarchy. A concurrency rule on the "SFX" class applies to all children. Override at the leaf level for special cases (player footsteps need more budget than enemy footsteps).

### Stream Caching **[UE4.24+ / UE5]**

Streaming audio only makes sense for long files (typically > 5–10 seconds). Short sounds benefit from loading into memory — random-access memory playback is faster than stream-on-demand.

```ini
au.streamcache.TrimCacheWhenOverBudget 1
au.streamcache.CacheSizeKB 65536    ; 64 MB audio stream cache
```

For music and long ambient, streaming is essential. For SFX, evaluate each sound: streaming adds I/O latency and CPU overhead for seek. Short gunshots, footsteps, and UI sounds should be loaded into memory.

### Audio Mixer and Submix Architecture **[UE4.24+ / UE5]**

The Audio Mixer architecture (default since UE4.24) enables per-source submix routing, plugin DSP effects, and MetaSound's Quartz integration. Each source can route to one or more Submixes (SFX Bus, Music Bus, Voice Bus). Add effects (EQ, reverb, compressor) at the submix level rather than per-sound for efficient processing — one reverb instance on the Environment submix versus one per environmental sound.

With Lumen Spatialization (UE5 HRTF/Ambisonics support): enable `Spatialization Algorithm = HRTF` in Sound Attenuation settings. HRTF adds CPU cost per virtualized source. Budget carefully — HRTF is not free.


---

## Extended Reference: World Partition Internals

### Runtime Streaming Grid Architecture **[UE5 only]**

The World Partition runtime streaming grid divides the world into a spatial grid of cells. Each cell has a size (in centimeters) and a loading range. When a Streaming Source (typically the Player Controller) enters the loading range of a cell, that cell begins async streaming. When the source moves outside the range, the cell begins unloading.

Grid configuration:
```ini
RuntimeGrid.CellSize=12800     ; 128 meters (value in cm!)
RuntimeGrid.LoadingRange=25600 ; 256 meters = 2x Cell Size
```

The default 128 m (12800 cm) works for most cases:
- Dense urban environments: use 64 m cells for finer-grained streaming
- Sparse terrain/landscapes: use 256 m cells to reduce cell count and streaming overhead

For fast vehicles or flight: add a predictive streaming source based on the player's velocity vector to pre-load 1–2 cells ahead. The default Streaming Source (player controller) is purely reactive — it only triggers streaming after the player is already in the area.

Watch out for large actors that span more than one cell size (churches, bridges) — they are "promoted" to a higher grid level and may load independently of normal cells. Design hero structures to fit within cell boundaries, or be prepared for them to have different load behavior.

### HLOD in World Partition — Practical Setup **[UE5 only]**

HLOD in World Partition consists of meshes or impostors rendered for distant streaming cells. The default configuration "Lowest Available LOD" for landscape makes HLODs look like grey blobs at distance.

Key configurations:
```ini
; In World Settings → Runtime Partitions → HLOD Setups:
; INDEX [0] — HLODLayer_Instanced: set Loading Range to cover mountains
; INDEX [1] — HLOD Merged: set Specific LOD = 4-5 instead of "Lowest Available"
```

HLOD Instanced type: for Nanite meshes, set HLOD Layer Type = Instanced (no decimation). Nanite handles detail, and instancing streams faster. This prevents the "grey blob" problem for medium-distance Nanite content.

HLOD1 serves double duty: it is also consumed by Lumen's Far Field pass for GI beyond 1 km. If you skip building HLOD, Lumen Far Field will have no geometry to illuminate. Always build HLOD before evaluating Lumen quality in open worlds.

### OFPA Source Control Workflow **[UE5 only]**

One-File-Per-Actor (OFPA) stores each actor as a separate file in the `__ExternalActors__` folder. With non-Perforce VCS (Git LFS, SVN), this creates some specific workflow considerations:

- New actors added to a level still modify the main `.umap` file, not just the actor file
- Auto-Save can generate thousands of changes in `ExternalActors` simultaneously — disable Auto-Save for large WP scenes
- Conflicts in actor files are usually binary (they are serialized UAssets) — resolve by taking one version entirely
- Before renaming folders containing OFPA data: check and update all references first with the Reference Viewer

Diagnostic command:
```
wp.Editor.DumpStreamingGenerationLog
; Output in: Saved/Logs/WorldPartition/
```

This logs which actors ended up in which streaming cells, their load ranges, and their HLOD assignments. Essential for debugging unexpected streaming behavior or cell count explosions.

---

## Extended Reference: Blueprint Anti-Patterns — Complete Reference

### `Get All Actors Of Class` — Detailed Analysis **[UE4 + UE5]**

`Get All Actors Of Class` iterates the entire actor list of the current world, building a new TArray on every call. The performance cost scales with world complexity:

- A level with 500 actors: ~2,000–5,000 pointer comparisons per call
- Called in Tick at 60 fps: ~120,000–300,000 comparisons per second
- Called in Tick on a server with 20 connected clients: multiplied by connection count

Correct alternatives:
- **Manager/Subsystem registration**: actors register themselves in GameMode or GameState in BeginPlay and unregister in EndPlay. The manager holds a typed TArray. Zero lookup cost.
- **Overlap/collision events**: for "all enemies within radius," use `SphereTraceMulti` or `GetOverlappingActors` on a collision component — spatially accelerated, no world scan.
- **Gameplay Tag queries**: for heterogeneous actor types, store a `TMap<FGameplayTag, TArray<AActor*>>` in a Subsystem and query by tag.

### Pure Functions — Execution Model Explained **[UE4 + UE5]**

A "Pure" Blueprint node (green, no execution pins) is re-evaluated every time its output is consumed by a downstream node. If you wire a costly pure function's output into three nodes, the function executes three times.

This is architecturally correct in functional programming terms — pure functions have no side effects, so re-evaluation is safe. But in Blueprints, "pure" only means no exec pin, not that it is truly free to call. A pure function that iterates an array will iterate it once per downstream consumer.

Fix: call the function once as an impure (non-pure) call, cache the output in a local variable, then consume the variable. Right-click the pure node → Convert to Impure.

### Soft Reference Memory Escape Patterns **[UE4 + UE5]**

The memory leak from hard references in Blueprints can be traced systematically:

1. Open the suspect Blueprint in the editor
2. Right-click the asset in the Content Browser → `Size Map`
3. The Size Map shows a tree of all directly and transitively hard-referenced assets
4. Any class referenced via `Cast To` appears as a hard reference

The escape pattern:
- Change casts to `Cast To Actor` (or another lightweight base class) — the specific derived class is no longer a hard reference
- Use Blueprint Interfaces instead of direct casts for cross-Blueprint communication
- For assets (meshes, textures, sounds) that should only load on demand: use `TSoftObjectPtr<T>` and `Async Load Asset`

When direct casting is acceptable: within the same module (e.g., a Component casting to its owning actor), or when the reference cost has already been paid and the result is cached in a variable (cast once in BeginPlay, store the result).

### Blueprint VM Optimization Cheat Sheet **[UE4 + UE5]**

| Anti-Pattern | Cost | Fix | Engine |
|---|---|---|---|
| Tick enabled on every actor | Per-frame VM dispatch | Uncheck Start with Tick Enabled | UE4 + UE5 |
| `Get All Actors Of Class` in Tick | O(n) scan every frame | Manager/subsystem registration | UE4 + UE5 |
| Cast To BP_X in UI Blueprint | BP_X fully loaded in memory | BPI or base-class cast | UE4 + UE5 |
| Pure node wired to 3 consumers | Executes 3 times | Convert to impure + cache | UE4 + UE5 |
| `ForEachLoop` without break | Full array always traversed | ForEachLoopWithBreak + Break pin | UE4 + UE5 |
| Spawn actor in Construction Script | Orphans on every property change | Child Actor Component | UE4 + UE5 |
| `Make Array` in Tick | Heap alloc every frame | Member variable array | UE4 + UE5 |
| `Delay` for cancellable logic | Cannot be cancelled, crash risk | Set Timer by Event | UE4 + UE5 |
| `Sequence` to spread work over time | All pins fire in same frame | Set Timer by Event chain | UE4 + UE5 |
| `Set Timer by Event` without handle | Cannot cancel | Store handle, use Clear Timer | UE4 + UE5 |
| Polling `Is Valid` in Tick | Unnecessary GC lookups | Event/delegate on destroy | UE4 + UE5 |
| Direct cast in UI widget to player | Character class in memory always | Blueprint Interface | UE4 + UE5 |
| `Set Actor Tick Enabled` in Tick | Recursive overhead | Call only on state transitions | UE4 + UE5 |
| Hard ref in GameInstance variable | Asset loaded for entire session | Soft reference + lazy load | UE4 + UE5 |

---

## Extended Reference: Tech Art Tricks — Complete Reference

### Foliage Nanite — Practical Decision Matrix **[UE5 only]**

The correct approach to foliage rendering in UE5 depends on several interacting factors:

| Foliage Type | Recommended Approach | Reason |
|---|---|---|
| Dense grass, short ground cover | Non-Nanite HISM with LODs | < 300 triangles per instance; Nanite overhead not worth it |
| Small bushes, flowers | Non-Nanite HISM with LODs | Masked material would force software raster |
| Medium shrubs with alpha-card leaves | Opaque geometry leaves + Nanite | Eliminates masked material overhead |
| Trees with wind animation | Hybrid: LOD0 traditional WPO, LOD1+ Nanite | LOD0 close up uses WPO normally; Nanite for distance |
| Rocky ground clutter | Nanite + ISM | Simple opaque material, enough triangles, instance batching |
| Cliff faces, large rocks | Nanite | Hero assets, benefits most from Nanite's micro-polygon rendering |

The procedural foliage spawner creates thousands of instances. For collision: use a proximity sphere around the player instead of per-instance physics collision. The engine cannot efficiently process physics on 50,000 foliage instances.

### Custom Depth Stencil — Stencil Value Strategy **[UE4 + UE5]**

The 8-bit stencil (values 0–255) should be allocated as a shared resource across systems:

- Values 0: unused / default
- Values 1–15: outline system (character selection, interaction highlights)
- Values 16–31: hit-flash system (enemy hit indicator)
- Values 32–47: decal masking (footprints on stencil == 32 surfaces only)
- Values 48–63: see-through walls (X-ray mode for walls with stencil == 48)

This allows a single Custom Depth pass to serve multiple systems simultaneously, rather than adding a separate render pass per feature. The cost: one extra depth-only pass for all actors with Custom Depth enabled.

Performance note: the Custom Depth pass adds a separate batch of draw calls for all marked actors. For systems that activate/deactivate frequently (hit flash), toggle `Render Custom Depth Pass` on the component rather than enabling it permanently. Permanent enablement on hundreds of actors defeats the purpose of the selective pass.

### Render Targets for Procedural Workflows **[UE4 + UE5]**

Render Targets let you run material evaluation and store the result as a texture for subsequent frames. Production uses:
- Procedural terrain masks (snow accumulation, wetness spreading)
- Ripple simulations (water surface disturbed by rain or movement)
- Trail/history effects (footprints in snow, tire tracks in mud)
- Decal accumulation (permanent damage decals composited into a surface mask)

Performance rules:
- GPU readback is expensive: `ReadRenderTargetPixels` is synchronous and stalls the CPU-GPU pipeline — can cost several milliseconds ([Froyok's Render Target performance analysis](https://www.froyok.fr/blog/2020-06-render-target-performances/)). Use `EnqueueCopy` (non-blocking async readback) for gameplay data and consume the result a frame later.
- `Begin/EndDrawCanvasToRenderTarget` when performing multiple draws per frame — this reuses the FCanvas object. `DrawMaterialToRenderTarget` recreates the FCanvas each call, leading to O(N) allocations for N draws per frame.
- Render Targets that update every frame contribute to GPU memory bandwidth. Size them appropriately — a 1024×1024 RGBA8 Render Target updating at 60 fps = 256 MB/s of write bandwidth.

### Lumen Surface Cache — Advanced Tuning **[UE5 only]**

The Lumen Surface Cache is a set of cards (Lumen Cards) generated for each mesh. Understanding what determines card quality:

- Object must be at least ~4 cm in size (`r.LumenScene.SurfaceCache.MeshCardsMinSize`)
- Default 6 cards per object — enough for simple convex shapes
- Interior-critical meshes (rooms, corridors) need 8–12 cards (`Num Lumen Mesh Cards` in Static Mesh Editor → Build Settings)
- Thin objects (walls, fences) may need `Two-Sided Distance Field Generation` enabled in mesh settings

Pink artifacts in the Surface Cache visualization mean:
- The card is not yet updated (normal during load)
- The mesh is too small for the Surface Cache
- The mesh is not generating cards (check `Generate Mesh Distance Fields` is enabled)

Yellow areas = culled (too distant). Address by increasing `r.LumenScene.SurfaceCache.MeshCardsMinSize` or by checking `Emissive Light Source` on the actor to prevent culling for emissive sources.

