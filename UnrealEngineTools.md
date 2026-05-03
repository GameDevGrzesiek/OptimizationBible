# UE4 / UE5 Tools Guide

---

## How to Read This Guide

This guide covers Unreal Engine 4 (4.22–4.27) and Unreal Engine 5 (5.0–5.6+). Every tip that differs meaningfully between engine generations is tagged:

- **[UE4 + UE5]** — applies to both engines without significant changes
- **[UE4 only]** — UE4-specific feature or workflow removed or replaced in UE5
- **[UE5 only]** — UE5-exclusive feature not present or experimental in UE4
- **[Deprecated in UE5]** — was standard in UE4, removed or superseded in UE5

**Profile first.** Every section assumes you have profiling data pointing at the bottleneck. Optimizing without data produces regressions as often as gains.

---

## Tools

### Console / `stat` Commands **[UE4 + UE5]**

Always run `stat unit` first. It tells you which thread is over budget.

| Command | What It Shows |
|---|---|
| `stat none` | Clears all active stat overlays |
| `stat fps` | Frame time and FPS counter |
| `stat unit` | Game / Draw / GPU / RHIT thread times — primary bottleneck identifier |
| `stat unitgraph` | Rolling time-series graph of all thread times |
| `stat game` | Game Thread tick group breakdown |
| `stat scenerendering` | Draw call count, primitive count, mesh draw commands |
| `stat gpu` | GPU pass breakdown (requires `r.GPUStatsEnabled 1`) |
| `stat particles` | Particle system CPU budget |
| `stat hitches` | Flags frames above hitch threshold (default 200 ms) |
| `stat namedevents` | Enables runtime named event instrumentation |
| `stat memory` | High-level memory category totals |
| `stat streaming` | Texture and mesh streaming status |
| `stat streaming.details` | Detailed streaming pool breakdown |
| `stat shadercomplexity` | (View Mode) — see View Modes section |
| `stat nanite` **[UE5 only]** | Nanite cluster/triangle/instance stats |
| `stat lumen` **[UE5 only]** | Lumen probe and cache stats |
| `stat virtualshadowmaps` **[UE5 only]** | VSM page pool usage and cache stats |
| `stat raytracing` | Ray tracing pass counts (when RT enabled) |
| `stat initviews` | Visibility culling stats: frustum, occlusion, precomputed |
| `ProfileGPU` | Opens GPU Visualizer (or Ctrl+Shift+,) |
| `Memreport -full` | Dumps `.memreport` to `Saved/Profiling/MemReports/` |
| `obj list` | Lists all loaded UObjects by class with memory |

**`ShowFlag` commands** — prefix with `show` to toggle individual rendering features:
```
show StaticMeshes
show SkeletalMeshes
show Particles
show Decals
show Translucency
show LOD
show Bounds
show Collision
show LightComplexity
show ShaderComplexity
```

---

### View Modes **[UE4 + UE5]**

Access via the Viewport dropdown (Lit → select mode) or the `viewmode` console command.

| View Mode | Purpose |
|---|---|
| Lit | Default final frame |
| Unlit | Removes lighting cost — shows pure material shading |
| Wireframe | Polygon density visualization |
| Shader Complexity | Shader instruction cost per pixel (green = cheap, red = expensive) |
| Quad Overdraw | Overdraw of shaded quads — high values = fill rate bottleneck |
| Light Complexity | Number of lights affecting each pixel |
| LOD Coloration | Visualize active LOD per mesh |
| Nanite Visualization → Overdraw **[UE5 only]** | Nanite overdraw (white/yellow = expensive layers) |
| Nanite Visualization → Triangles **[UE5 only]** | Triangle density per screen area |
| Nanite Visualization → Clusters **[UE5 only]** | Cluster allocation visualization |
| Lumen → Surface Cache **[UE5 only]** | Pink = no coverage; yellow = culled |
| Lumen → Card Placement **[UE5 only]** | Lumen card orientation debug |
| Virtual Shadow Map → Page Allocation **[UE5 only]** | Green = cached pages, red = new page allocations |
| Substrate Visualization **[UE5.3+ only]** | Substrate material layer breakdown |

---

### Unreal Engine Profiler (Session Frontend) **[UE4 + UE5 — Legacy]**

The Session Frontend (`Window > Developer Tools > Session Frontend`) includes a CPU profiler with flame graph, stat capture, and remote session support. In UE5 this tool is superseded by Unreal Insights and receives minimal development. The Session Frontend profiler requires a networked editor session; it cannot profile standalone packaged builds. Use it only if Insights is unavailable or for quick in-editor investigations. For any serious performance work, use Unreal Insights.

---

### GPU Visualizer **[UE4 + UE5]**

Open with `ProfileGPU` console command or `Ctrl+Shift+,`. Displays GPU time per render pass in a hierarchical tree. Key passes to examine:

- `ShadowDepths` — shadow map rendering (most often the culprit in complex scenes)
- `BasePass` — G-buffer fill
- `Translucency` — translucent geometry rendering
- `PostProcessing` — post-process stack
- `Nanite` **[UE5 only]** — Nanite rasterize, classify, shadow depth passes
- `Lumen` **[UE5 only]** — screen probe gather, reflections, surface cache updates

The milliseconds toggle (switch between GPU cycles and ms) is essential for platform comparison. UE5.6 unified the GPU Profiler — `stat gpu`, `ProfileGPU`, and Insights GPU track now share the same instrumentation stream.

For capture-level debugging, enable the **RenderDoc** plugin (restart required), then use the RenderDoc toolbar button to capture a frame. RenderDoc exposes per-draw-call shaders, resource states, and timing unavailable from the in-engine visualizer. With D3D12, set `r.ShowMaterialDrawEvents 0` before capturing to eliminate GPU marker overhead from skewing timing ([AMD GPUOpen — Unreal Engine Performance Guide](https://gpuopen.com/learn/unreal-engine-performance-guide/)).

**Alternatives [UE4 + UE5]:**
- PIX (Microsoft) — D3D12 captures, GPU timeline, shader debugging
- NSight (NVIDIA) — deep shader and warp-level profiling
- Radeon GPU Profiler (AMD) — pipeline stall visualization

---

### Unreal Insights **[UE4.21+, primary tool in UE5]**
Unreal Insights is not just a viewer for frame times. It is a post-mortem analysis system built on a streaming binary protocol called Trace, which records structured events into `.utrace` files that can be analyzed offline or in real time. Unlike the classic `stat` system — which paints numbers onto the viewport and is limited to Development builds — Insights is available in every configuration including Test, and can be enabled in Shipping with a single define. For an indie team shipping on Steam, that distinction matters enormously: your published build and your profiling build can be nearly identical.

The architecture separates concerns cleanly. A lightweight runtime component (TraceLog) emits binary events over a TCP connection or directly to disk with minimal overhead. A separate process, `UnrealTraceServer`, records and stores those events. The Insights frontend application reads stored sessions and renders the analysis UI. This means your game instance, your profiling data store, and your analysis tool can all run on different machines — critical for headless server profiling in CI/CD pipelines.

The core workflow is: identify which thread or category is over budget using `stat unit` in-game, then open Insights to understand *why*. Insights gives you a full flame graph, allocation stacks, replication packet contents, and animation graph state — none of which are visible from `stat unit` alone. The payoff of learning the tool well is that many "mysterious" frame spikes are diagnosed in minutes rather than hours.

A critical philosophical point that experienced developers emphasize: [Unreal Fest 2024 speaker Jake Simpson](https://www.youtube.com/watch?v=KxREK-DYu70) and the [Epic Technical Developer Relations team](https://www.youtube.com/watch?v=C-AjCqjKRSs) both stress that you should always profile in a Test build, never in the Editor. The Editor imposes a 3× to 4× overhead on the Game Thread compared to a standalone packaged binary. Any optimization decision made from Editor numbers is unreliable.

---

#### Setting Up: Server, Client, Trace Files

##### UnrealTraceServer, Ports, and Network Captures

The Unreal Trace Server (`UnrealTraceServer.exe`, located in `Engine/Binaries/Win64`) is a headless process with two components: the Trace Recorder, which listens on TCP port **1981** for incoming trace streams from game instances; and the Trace Store, which watches a folder on disk and exposes stored sessions to the Insights frontend via TCP port **1989**. The Insights frontend itself connects to port **1985** on the game instance when performing a live "late connect." These three ports serve entirely different roles, and confusing them is a common source of connection failures ([Epic DevCom — Connecting Unreal Insights to a remote trace server](https://forums.unrealengine.com/t/connecting-unreal-insights-to-a-remote-trace-server/2662205)).

To start the server manually:

```ini
Engine\Binaries\Win64\UnrealTraceServer.exe
```

The server stores its configuration and log files at `%LOCALAPPDATA%\UnrealEngine\Common\UnrealTrace` on Windows, and `~/UnrealEngine/UnrealTrace` on macOS/Linux. You can redirect where trace files land by opening Insights, clicking the "Manage store settings" dropdown, and using "Set Trace Store directory." The old directory is automatically added as a watch folder, so existing sessions remain accessible ([Epic Unreal Insights docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-insights-in-unreal-engine)).

For multi-machine setups — a common pattern when profiling a dedicated server — run `UnrealTraceServer.exe` on your analysis PC, then pass the recorder port explicitly to the game instance:

```ini
YourServer-Win64-Test.exe -tracehost=192.168.1.100
```

The server instance sends trace data to port 1981 on the analysis PC. The Insights frontend running on the analysis PC sees the session appear in the browser automatically. On Windows, when the game instance runs on the same machine, `-tracehost` is often omitted because auto-discovery handles it — but always specify it explicitly for Linux and Mac game clients.

##### File Location, Retention, and On-Disk Size

Trace files are written to the Trace Store directory by default. A typical CPU+GPU capture of a 60-second play session can range from 50 MB (minimal channels) to over 1 GB (full CPU + memory + named events). The companion `.ucache` file in the same directory stores resolved symbol data and is regenerated on demand. You can safely delete `.ucache` files; they are rebuilt the next time you open the trace. Do not delete `.utrace` files unless you are certain you no longer need them — there is no undo.

To cap trace size during automated CI captures, use a duration-bounded capture:

```ini
-trace=cpu,frame,gpu,bookmark -tracefile=C:\Traces\build_1234.utrace
```

Then issue `Trace.Stop` from a console command triggered at a known frame count, or use `-benchmarkseconds=N` with `-ExitAfterCsvProfiling` for automation scripts ([Intel UE5 Optimization Guide Chapter 2](https://www.intel.com/content/www/us/en/developer/articles/technical/unreal-engine-optimization-chapter-2.html)).

##### Late-Attach with `Trace.SendTo` and `-tracehost=`

If you forgot to start a trace before launching a game instance, you can attach without restarting. From the in-game console, run:

```
Trace.SendTo 127.0.0.1 cpu,frame,gpu,bookmark
```

This tells the already-running instance to begin emitting the specified channels to the local trace server. The trace will start from the current moment — you cannot retroactively recover pre-attach data. For a game already running on a remote machine, replace `127.0.0.1` with the IP of the machine running `UnrealTraceServer.exe`. The alternative to late-attach is to always launch with `-trace=` on the command line, which begins tracing from process startup ([Unreal Engine Community Wiki — Profiling with Unreal Insights](https://unrealcommunity.wiki/profiling-with-unreal-insights-ilad24y4)).

---

#### Trace Channels — The Channel Cheat Sheet

##### Default Channels

When you pass `-trace` on the command line without channel arguments, or click "Start Trace" from the editor status bar without customization, the engine uses the "default" channel set. In UE5 this covers the essentials needed for CPU timing: `cpu`, `frame`, `log`, `bookmark`, and `counters`. It does not include `gpu`, `memory`, `net`, or `animation` by default — those require explicit opt-in. The difference between minimal and full traces is an order of magnitude in both overhead and file size.

| Channel | What it captures | Relative overhead |
|---------|-----------------|-------------------|
| `cpu` | CPU timing events (scoped timers) | Low |
| `frame` | Frame begin/end markers | Minimal |
| `bookmark` | Named bookmarks from `TRACE_BOOKMARK` | Minimal |
| `counters` | Integer/float counter time series | Low |
| `log` | UE log output | Low |
| `gpu` | GPU hardware timestamps (DX12/Vulkan) | Low–Medium |
| `loadtime` | Asset loading durations | Low |
| `rendercommands` | Render command buffer | Medium |
| `rhicommands` | RHI command buffer events | Medium |
| `object` | UObject create/destroy events | Medium |
| `net` | Network replication packets | Medium (with `-NetTrace=1`) |
| `animation` | Animation graph state and poses | Medium–High |
| `memory` | Full allocation trace (all allocs/frees) | **Very High** |
| `assetmetadata` | Asset name metadata for memory | Medium |
| `task` | Task Graph scheduling and dependencies | Medium |

([Unreal Engine Community Wiki](https://unrealcommunity.wiki/profiling-with-unreal-insights-ilad24y4); [Intel UE5 Profiling Fundamentals](https://www.intel.com/content/www/us/en/developer/articles/technical/unreal-engine-optimization-profiling-fundamentals.html))

##### Memory Channels: Costs and Tradeoffs

Memory profiling has three levels of depth, each with increasing overhead:

- **`memtag`** (enabled via `-trace=default,memtag` or the `memory` channel group): Captures per-LLM-tag totals at frame granularity. Suitable for tracking broad memory categories over time. Minimal runtime cost but compiled out of Test/Shipping unless you add `ALLOW_LOW_LEVEL_MEM_TRACKER_IN_TEST=1` to your `.Target.cs`.

- **`memory`** (full allocation trace): Captures every `malloc`, `realloc`, and `free` with a call stack. This is essential for leak hunting but adds significant CPU overhead and generates traces that can exceed 10 GB for long sessions. The `MarkerSamplePeriod` setting in `MemoryAllocationTrace.cpp` defaults to emitting a timestamp every 4096 allocation/free events; set it to 0 for per-event granularity (much larger files) ([Epic Memory Insights docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/memory-insights-in-unreal-engine)).

- **`assetmetadata`**: Works alongside `memory` to attach asset package names to allocations. Required for the "Asset (Package)" grouping preset in Memory Insights. Combined command line: `-trace=default,memory,metadata,assetmetadata`.

The memory trace channel **must be active from process start** — you cannot retroactively capture allocation history by late-attaching the memory channel. Plan ahead and always pass it on the command line if you intend to do memory analysis.

##### GPU Channel Limitations

The `gpu` channel captures GPU hardware timestamps and requires D3D12 or Vulkan with timestamp query support. A common gotcha: on some NVIDIA and AMD driver versions, the GPU track appears empty or shows only a flat line. If the GPU track is missing, check that you are not running in D3D11 mode (`-dx11` disables GPU timestamps), that your driver supports timestamp queries, and that you are running a Test or Development build (not Editor-only PIE). As of UE 5.6, GPU profiling in Insights was substantially improved with the GPU Profiler 2.0, which unifies `stat gpu`, `ProfileGPU`, and Insights GPU data into a single stream ([Tom Looman — UE 5.6 Performance Highlights](https://tomlooman.com/unreal-engine-5-6-performance-highlights/)).

##### Custom Channel Creation in C++

You can gate your custom trace events behind a named channel. Declare a channel in a header:

```cpp
// MyModule.h
UE_TRACE_CHANNEL_EXTERN(MyGameChannel, ENGINE_API);
```

Define it in the corresponding `.cpp`:

```cpp
// MyModule.cpp
UE_TRACE_CHANNEL_DEFINE(MyGameChannel);
```

Or for module-private use, just declare and define together in one `.cpp`:

```cpp
UE_TRACE_CHANNEL(MyGameChannel);
```

Channels are disabled by default. Enable at runtime:

```
Trace.Enable MyGameChannel
```

Or on the command line:

```ini
-trace=cpu,frame,MyGameChannel
```

Events can be gated on multiple channels simultaneously using bitwise OR: `UE_TRACE_LOG(MyLogger, MyEvent, MyGameChannel|cpu)` emits only if both channels are active ([Epic Developer Guide to Tracing](https://dev.epicgames.com/documentation/en-us/unreal-engine/developer-guide-to-tracing-in-unreal-engine)).

##### The `Trace.Enable` / `Trace.Status` / `Trace.Stop` Workflow

The three most useful Trace console commands during a live session:

```
Trace.Status            — prints which channels are active and where data is going
Trace.Enable gpu,memory — enables additional channels on an already-running trace
Trace.Stop              — finalizes and closes the trace file
```

Use `Trace.Status` first whenever Insights shows an empty or unexpected trace — it reveals whether the instance is connected to a store and which channels are emitting. `Trace.Stop` is safe to call at any time; it does not crash the game instance and leaves the file in a valid, analyzable state.

##### `-trace=...` Command Line vs In-Editor Toggle

The command line argument is evaluated at startup before any gameplay systems initialize, making it the correct place to specify channels that must be active from frame zero (especially `memory` and `loadtime`). The in-editor toggle via the status bar toolbar widget in UE5 starts the trace after the editor is already running — fine for CPU timing investigations, but will miss any allocations that occurred during module loading. For packaged builds, always use the command line or the `-ExecCmds="Trace.Start cpu,frame,gpu"` pattern if you want to defer the trace start.

##### Bookmark Channel and `TRACE_BOOKMARK` Macro

Bookmarks are zero-overhead markers that appear as vertical lines in the Timing Insights timeline. They are invaluable for correlating gameplay events ("player crossed checkpoint", "GC pass started", "level stream completed") with timing data:

```cpp
TRACE_BOOKMARK(TEXT("LevelStream::StartLoad::%s"), *LevelName.ToString());
```

The `bookmark` channel carries these events and has near-zero overhead. A community-recommended pattern from [Reddit r/unrealengine](https://www.reddit.com/r/unrealengine/comments/1cacdpe/best_resource_for_learning_how_to_use_and/) is to add bookmarks at every major game state transition so that when you see a spike in a trace, you can immediately identify which phase of gameplay it belongs to.

---

#### Capturing Data

##### Editor vs Standalone vs Packaged Test Build Differences

This is not a stylistic preference — it is the most impactful decision in your profiling workflow. The Editor runs additional subsystems (content browser, level viewport, undo history, property details panels) that consume Game Thread cycles independently of your game code. Measurements taken in Editor PIE can be 2× to 4× slower than in a packaged standalone build. [Jake Simpson at Unreal Fest 2024](https://www.youtube.com/watch?v=KxREK-DYu70) documented a concrete case: a project showed 15 ms Game Thread time in Editor PIE and only 4 ms in a standalone build.

The correct build hierarchy for profiling, from least accurate to most accurate:

1. Editor PIE — only for rapid iteration and catching obvious regressions
2. Standalone launch (Play > Standalone Game in UE5) — removes some editor overhead, but still runs with Development optimizations
3. Development packaged build — full packaged build, Development config, all optimizations enabled
4. **Test packaged build** — identical to Shipping in terms of optimizations, but with Insights, stat named events, and logging enabled; this is the gold standard

##### The "Always Profile in Test Build" Rule

Test builds strip out STATS groups, debug draw calls, and PIE bookkeeping but retain the trace infrastructure. To enable additional profiling features in your `.Target.cs`:

```cpp
bool bIsTest = Target.Configuration == UnrealTargetConfiguration.Test;
if (bIsTest)
{
    bAllowProfileGPUInTest = true;          // enables ProfileGPU and GPU markers
    bUseLoggingInShipping = true;           // enables log-to-file
    GlobalDefinitions.Add("ENABLE_STATNAMEDEVENTS=1");
    GlobalDefinitions.Add("ENABLE_STATNAMEDEVENTS_UOBJECT=1");
    // Optional: full LLM in Test
    // GlobalDefinitions.Add("ALLOW_LOW_LEVEL_MEM_TRACKER_IN_TEST=1");
}
```

([Intel UE5 Profiling Fundamentals](https://www.intel.com/content/www/us/en/developer/articles/technical/unreal-engine-optimization-profiling-fundamentals.html))

##### Targeted Captures with `Trace.Start` / `Trace.Stop`

For steady-state profiling of a specific gameplay moment, use the console to start and stop the trace around the relevant window rather than recording from startup. Connect to the game via the Insights Connection tab (port 1985), confirm `Trace.Status` shows a live connection, then:

```
Trace.Start cpu,frame,gpu,bookmark
// ... play the scenario you want to profile ...
Trace.Stop
```

This produces a small, focused trace that is much faster to analyze than a 10-minute session dump. For automated testing, drive this via `-ExecCmds`:

```ini
YourGame-Win64-Test.exe -ExecCmds="Trace.Start cpu,frame,gpu" -tracefile=C:\Perf\focused.utrace
```

##### Capturing the First 60 Seconds vs Steady-State

The first 60 seconds of a session include asset streaming, shader compilation flushes, and initial GC passes that will not represent steady-state behavior. For performance optimization work, target steady-state: load the level, wait for streaming to settle, then start the trace. For load-time and hitching investigations, start the trace from process startup using `-trace=loadtime,cpu,frame,bookmark` to capture the full initialization sequence.

##### Network Captures (Multiple Clients)

Launch each game instance (server and clients) with the net trace parameters, pointing at a shared trace server:

```ini
YourServer-Win64-Test.exe -trace=net -NetTrace=1 -tracehost=192.168.1.100
YourClient-Win64-Test.exe -trace=net -NetTrace=1 -tracehost=192.168.1.100
```

Each instance creates a separate `.utrace` file in the store. In the Networking Insights tab, the "Game Instance" dropdown lets you switch between server and client views, and the "Connection" dropdown selects specific connections ([Epic Networking Insights docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/networking-insights-in-unreal-engine)).

##### Late-Attach to Running Instances

From the Insights frontend: Connection tab → enter the game instance IP and port 1985 → Connect. The session appears in the session browser with a "LIVE" badge. Channel selection at this point only captures data from the moment of connection onward. This workflow is useful for profiling production builds that are already running, or for server farms where you do not control the launch parameters ([Epic DevCom forum](https://forums.unrealengine.com/t/connecting-unreal-insights-to-a-remote-trace-server/2662205)).

##### Trace.RegionBegin / Trace.RegionEnd (UE5.3+) — Tagging Multi-Frame Regions

Regions mark a named span that can cross frame boundaries and appear as a dedicated track in Timing Insights. This is useful for tagging specific scenarios (a combat encounter, a level stream) for later comparison:

```
Trace.RegionBegin BossArena
// ... play through the boss encounter ...
Trace.RegionEnd BossArena
```

In C++:

```cpp
uint64 RegionId = TRACE_BEGIN_REGION_WITH_ID(TEXT("BossArena"));
// ... work ...
TRACE_END_REGION_WITH_ID(RegionId);
```

In Blueprints: "Trace Mark Region Start" / "Trace Mark Region End" nodes. Regions are especially powerful for automated comparison: the Insights CLI can export timer statistics scoped to a named region:

```ini
UnrealInsights.exe -AutoQuit -NoUI -OpenTraceFile="capture.utrace" ^
  -ExecOnAnalysisCompleteCmd="TimingInsights.ExportTimerStatistics results.csv -region=BossArena -threads=GPU"
```

([Intel UE5 Optimization Guide Chapter 2](https://www.intel.com/content/www/us/en/developer/articles/technical/unreal-engine-optimization-chapter-2.html))

---

#### CPU Insights (Timing Insights)

##### Reading Flame Graphs

The Timing panel is the core of CPU Insights. It shows horizontal bars for each thread, stacked vertically, where each bar represents a named scope and its width represents duration. You read it left-to-right (time), top-to-bottom (nesting depth). A wide parent bar with one narrow child means the work is spread across many anonymous calls that are not individually instrumented — a signal to add more `TRACE_CPUPROFILER_EVENT_SCOPE` markers. A wide parent bar with one child that is nearly as wide means a single bottleneck function.

The Frame panel at the top shows every frame as a colored bar: green for on-budget, yellow for 33% over budget, red for 100% over budget. Click a spike to zoom the Timing panel to that frame. This is the correct entry point for every profiling session: find the worst frames first, not the most recent frames.

##### Aggregation Panel, Sorting, and Filters

The Timers tab below the flame graph aggregates all scope instances across the selected time range. The columns are: Name, Count (instances), Inclusive Time (total wall time including children), and Exclusive Time (time spent only in this scope, not children). Sort by Exclusive Time to find the single most expensive function. Sort by Count to find code that runs unexpectedly many times per frame. The Callers/Callees panel shows the call hierarchy for the selected timer, which helps trace back from a symptom (an expensive function) to a root cause (the caller that invokes it too frequently).

##### Threads View: GameThread, RenderThread, RHIThread, TaskGraph Workers

A typical UE5 game produces dozens of threads in the trace. The actionable ones are:

- **GameThread** — executes actor ticks, Blueprints, physics, input, networking receive. This is where most gameplay code runs.
- **RenderThread** — builds render commands, submits draw calls, drives Lumen and Nanite CPU-side work. In UE5, this is often the thread that bottlenecks with complex scenes.
- **RHIThread** — translates Unreal's render commands into D3D12/Vulkan API calls. On modern hardware this is pipelined; stalls here indicate command buffer management issues.
- **TaskGraph workers** — labeled `TaskGraphThreadBP`, used for async tasks like animation updates, physics cloth, and Niagara.

The filter icon in the Timing panel lets you show/hide individual thread tracks. For Game Thread analysis, hide everything else — the visual noise from dozens of TaskGraph threads makes the Game Thread nearly invisible by default ([Unreal Fest 2024 — Optimizing the Game Thread](https://www.youtube.com/watch?v=KxREK-DYu70)).

##### Identifying GT-Bound vs RT-Bound vs RHIT-Bound vs GPU-Bound

Use `stat unit` in-game first. The readout shows:

| `stat unit` line | Over budget means |
|-----------------|------------------|
| `Frame` | Longest of all threads |
| `Game` | Game Thread bottleneck |
| `Draw` | Render Thread bottleneck |
| `GPU` | GPU bottleneck |
| `RHIT` | RHI Thread bottleneck |

In Insights, confirm by looking at which thread's bar extends furthest to the right before the next frame marker. The thread that causes the frame to miss budget is the one you optimize.

##### The "Wait for GPU" Trap

The most common misdiagnosis in UE5 profiling: the Render Thread has a long idle period labeled `WaitForGPU` or similar, and developers conclude that the Render Thread is underutilized. In reality, this means the GPU is the bottleneck and the Render Thread is stalled waiting for the GPU to finish the previous frame before it can submit new work. The Render Thread is not slow — it is fast enough to outrun the GPU. The correct fix is to reduce GPU workload (shadows, resolution, draw calls), not to optimize Render Thread code. The [Mastering Performance Analysis with Unreal Insights talk at Unreal Fest Bali 2025](https://www.youtube.com/watch?v=HQLYkwoDoT4) explicitly covers this pattern.

##### Filtering by Event Name, Regex

In the Timers tab search box, type a partial name to filter the list. The search supports substring matching. For flame graph filtering, right-click any event → "Filter by name" to dim all events that do not match. This is useful when looking for all instances of a specific Blueprint function across the entire session.

##### Comparing Two Captures Side by Side

Insights does not natively support side-by-side comparison within the same window, but you can open two separate Insights windows (launch `UnrealInsights.exe` twice) and load different `.utrace` files into each. Alternatively, use the CLI export with `TimingInsights.ExportTimerStatistics` for both files and compare the CSV output in a spreadsheet — this is the most reliable method for A/B comparisons after a code change ([Intel UE5 Optimization Guide Chapter 2](https://www.intel.com/content/www/us/en/developer/articles/technical/unreal-engine-optimization-chapter-2.html)).

---

#### Adding Your Own Scopes (Instrumentation)

##### SCOPE_CYCLE_COUNTER (Stats System)

The classic instrumentation macro, part of the Stats System. Requires a prior declaration and shows up in both the in-game `stat` overlay and in Insights (when the `cpu` channel is active):

```cpp
// At file scope
DECLARE_CYCLE_STAT(TEXT("GetModuleByClass"), STAT_GetModuleByClass, STATGROUP_MyGame);

// In the function
void AMyShip::GetModuleByClass(...)
{
    SCOPE_CYCLE_COUNTER(STAT_GetModuleByClass);
    // ... work ...
}
```

Stats are stripped in Test and Shipping builds by default. They are good for developer-visible metrics that the whole team can see with `stat MyGame` in the viewport. However, the Stats System has more overhead than the Trace-native macros below ([Tom Looman — Adding Counters & Traces](https://tomlooman.com/unreal-engine-profiling-stat-commands/)).

##### TRACE_CPUPROFILER_EVENT_SCOPE / _SCOPE_STR

The preferred modern approach for custom Insights scopes. Lower overhead than the Stats System and does not require a separate declaration:

```cpp
#include "ProfilingDebugging/CpuProfilerTrace.h"

void UMyComponent::DoWork()
{
    TRACE_CPUPROFILER_EVENT_SCOPE(UMyComponent::DoWork);

    {
        TRACE_CPUPROFILER_EVENT_SCOPE_STR("Fancy inner scope");
        // Only this block is timed
    }
}
```

The `_STR` variant accepts a static string literal with runtime dynamic naming via the dynamic string variant — use static strings whenever possible, as dynamic strings carry extra memory and CPU cost. These events appear in the `cpu` Timing track and require the `cpu` channel to be enabled ([Epic Developer Guide to Tracing](https://dev.epicgames.com/documentation/en-us/unreal-engine/developer-guide-to-tracing-in-unreal-engine)).

##### SCOPED_NAMED_EVENT — Overhead Warning

`SCOPED_NAMED_EVENT` is the correct macro when you need an event that is visible in both Insights AND in external GPU frame debuggers (RenderDoc, PIX, Nsight) as a CPU-side annotation. However, it carries significantly more overhead than `TRACE_CPUPROFILER_EVENT_SCOPE` — [Tom Looman documents](https://tomlooman.com/unreal-engine-profiling-stat-commands/) reports from developers of up to 20% added frame time when enabled broadly. Never leave `SCOPED_NAMED_EVENT` in hot paths in production. It is activated either by:

```ini
-statnamedevents           # command line
stat namedevents            # in-game console
```

```cpp
SCOPED_NAMED_EVENT(MyActionName, FColor::Green);
SCOPED_NAMED_EVENT_FSTRING(GetClass()->GetName(), FColor::White);  // runtime name, extra overhead
```

The `_FSTRING` variant evaluates the string at runtime every call — reserve it for very-low-frequency events only.

##### LLM Tags for Memory: LLM_SCOPE / DECLARE_LLM_MEMORY_STAT

LLM scopes tag allocations so Memory Insights can attribute memory to categories:

```cpp
// MySystem.h
LLM_DECLARE_TAG(MySystem);

// MySystem.cpp
LLM_DEFINE_TAG(MySystem);

void UMySystem::Initialize()
{
    LLM_SCOPE_BYTAG(MySystem);
    BigBuffer.Reset(new uint8[1024 * 1024]);  // tagged as MySystem
}
```

LLM adds 21 bytes per live allocation (pointer, size, tag, hash key) and can add 100 MB+ of overhead for large games. It is compiled out entirely in Test and Shipping unless you explicitly enable it with `ALLOW_LOW_LEVEL_MEM_TRACKER_IN_TEST=1` in your Target.cs. The investment is worthwhile when hunting down memory regressions between builds ([Epic LLM docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/using-the-low-level-memory-tracker-in-unreal-engine)).

##### Custom Counters: TRACE_INT_VALUE / TRACE_FLOAT_VALUE

Track game-state values over time as a line graph in the Counters tab:

```cpp
// At file scope
TRACE_DECLARE_INT_COUNTER(ActiveEnemyCount, TEXT("Game/ActiveEnemies"));
TRACE_DECLARE_FLOAT_COUNTER(PlayerHealthPct, TEXT("Game/PlayerHealth"));

// In update code
TRACE_COUNTER_SET(ActiveEnemyCount, EnemyManager->GetCount());
TRACE_COUNTER_ADD(PlayerHealthPct, DeltaHealth);
TRACE_COUNTER_SUBTRACT(ActiveEnemyCount, DestroyedCount);
```

Counters require the `counters` channel to be active. They are excellent for correlating performance with game state: if frame time spikes when `ActiveEnemyCount` exceeds 40, you have a scaling problem to investigate ([Tom Looman — Adding Counters & Traces](https://tomlooman.com/unreal-engine-profiling-stat-commands/)).

##### Custom Trace Channels in C++ (`UE_TRACE_CHANNEL`)

Full custom channel with custom events (beyond just CPU timing) uses the raw Trace API:

```cpp
UE_TRACE_CHANNEL(MyGameChannel);

UE_TRACE_EVENT_BEGIN(MyLogger, SpawnEvent)
    UE_TRACE_EVENT_FIELD(uint32, ActorId)
    UE_TRACE_EVENT_FIELD(Trace::WideString, ActorClass)
UE_TRACE_EVENT_END()

void LogActorSpawned(uint32 Id, const FString& ClassName)
{
    UE_TRACE_LOG(MyLogger, SpawnEvent, MyGameChannel)
        << SpawnEvent.ActorId(Id)
        << SpawnEvent.ActorClass(*ClassName);
}
```

Custom events require a custom analyzer plugin in Insights to be visualized — the engine does not automatically render arbitrary event types. For most gameplay code, `TRACE_CPUPROFILER_EVENT_SCOPE` and `TRACE_BOOKMARK` cover 95% of use cases without needing a custom analyzer ([Epic Developer Guide to Tracing](https://dev.epicgames.com/documentation/en-us/unreal-engine/developer-guide-to-tracing-in-unreal-engine)).

---

#### Memory Insights (LLM)

##### Enabling Memory Tracing

Memory tracing must be enabled from process start. The minimal command line for leak investigation:

```ini
YourGame-Win64-Development.exe -trace=default,memory -tracefile=memory_session.utrace
```

For asset-level attribution (which package or asset owns the memory):

```ini
YourGame-Win64-Development.exe -trace=default,memory,metadata,assetmetadata -tracefile=asset_memory.utrace
```

The `-LLM` flag enables the Low Level Memory Tracker (which populates the LLM prefix graphs in Insights), and `-LLMCSV` additionally writes out a CSV file continuously. These are separate from the memory trace channel but complement it: the LLM graphs show per-tag totals at frame granularity, while the full memory trace shows individual allocations with callstacks ([Epic Memory Insights docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/memory-insights-in-unreal-engine)).

##### LLM Tags Overview

Key built-in LLM tags visible in the Memory Insights graphs:

| Tag | What it covers |
|-----|---------------|
| `UObject` | All UObject-derived allocations |
| `StaticMesh` | Static mesh render data |
| `RHI` | GPU-side render resources (textures, buffers) |
| `Audio` | Audio system buffers |
| `RenderTargets` | Render target allocations |
| `SceneRender` | Per-frame render scene data |
| `EngineMisc` | Engine allocations not in other categories |
| `TaskGraphTasksMisc` | Task graph overhead |

Custom tags defined with `LLM_DEFINE_TAG` appear alongside built-in tags after enabling `-LLM`. Use the LLM Tags panel in Memory Insights to show/hide categories, group them, or assign custom colors.

##### Snapshots: Trace.SnapshotFile vs Memreport

To capture a memory state at a specific moment without running a full allocation trace session, use `Memreport` from the in-game console:

```
Memreport -full
```

This writes a text report to `Saved/Profiling/MemReports/` listing UObject counts, asset memory, and pool usage. It is fast and works in all build configurations but gives only a static snapshot with no callstack attribution. For callstack-accurate leak hunting, use the Memory Insights allocation trace with two region markers (before and after the suspected leak window) and use the "Memory Leaks" query rule in the Investigation panel ([Epic Memory Insights docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/memory-insights-in-unreal-engine)).

##### Finding Leaks: Comparing Snapshots

The Memory Insights Investigation panel has a "Memory Leaks" query rule with three time points (A, B, C). It identifies allocations that were made between A and B but not freed before C. A practical workflow for detecting a level-transition leak:

1. Start a memory trace from the main menu.
2. Mark region A at the point of level-load-start.
3. Mark region B when the level is fully loaded.
4. Trigger the level transition (which should unload the level).
5. Mark region C after the transition is complete.
6. In the Investigation panel, run the "Memory Leaks" query for A–B–C.

Any allocations in the result set are candidates for leak investigation. Right-click an allocation to jump to its callstack ([Epic Memory Insights docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/memory-insights-in-unreal-engine)).

##### The "Asset Memory by Category" View

With `assetmetadata` tracing active, switch to the "Asset (Package)" preset grouping in Memory Insights. This breaks down allocations by package path and asset name, making it trivial to see which texture, mesh, or Blueprint is consuming the most memory. The Path Breakdown hierarchy further decomposes by LLM tag within each asset. This view has replaced the old `obj list` console command for most memory attribution tasks in UE5.

---

#### Networking Insights

##### Capturing Replication

Each game instance (server + clients) needs `-trace=net -NetTrace=1` to populate the Networking Insights tab. Set `-NetTrace=1` for baseline packet-level data; `-NetTrace=2` adds per-property tracking (higher overhead). When running in the editor:

```ini
-NetTrace=1 -trace=net -tracehost=localhost
```

In the Networking Insights tab, the Connection Selection Panel has three dropdowns: Game Instance (server or client), Connection (specific connection), and Connection Mode (incoming vs outgoing). Start with the server's outgoing data to understand what is being sent, then switch to a client's incoming data to see what it receives.

##### Packet View, Bunches, RPCs

The Packet Overview Panel displays a bar graph where each bar is a network packet. Bar height corresponds to bit count. Tall bars indicate unexpectedly large packets. Click a bar to expand it in the Packet Content Panel, which reveals the packet hierarchy:

- **Level 0**: Bunches (named after the channel they belong to: `Actor ChannelId:28`, etc.)
- **Level 1**: Replicated Actors within each bunch
- **Level 2**: Replicated properties and RPCs for that Actor
- **Level 3–4**: Serialized property values and array contents

Dropped packets appear in red. Split bunches — events larger than the bunch size — appear with their first part at the originating frame and their final part when reassembled. Example finding: an RPC named `NetMulticast_InvokeGameplayCueExecuted_FromSpec` consuming 1301 bits per call is visible immediately at Level 2 ([Epic Networking Insights docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/networking-insights-in-unreal-engine)).

##### Identifying Expensive Replicated Properties

Sort the Net Stats panel by "Total Inclusive Size (bits)" to rank all replicated events by bandwidth consumption. Filter by actor name to focus on a specific class. High-frequency properties with large sizes are prime candidates for either Push Model conversion (to reduce frequency) or quantization (to reduce size per update).

##### Push Model Verification

The Push Model optimization (`DOREPLIFETIME_WITH_PARAMS_FAST` with `ELifetimeCondition` and the `MARK_PROPERTY_DIRTY_FROM_NAME` API) requires `net.IsPushModelEnabled=1` in `DefaultEngine.ini` to be active. A subtle production bug: if a property is declared as Push Model but never explicitly marked dirty, it will replicate on initial replication only, then appear to replicate normally until the actor goes dormant and wakes up. In Networking Insights, this shows as a property that sends data on actor spawn but then goes silent — which may or may not be correct behavior for your game. Verify Push Model is working by checking that the property's bit contribution disappears between `MARK_PROPERTY_DIRTY_FROM_NAME` calls ([UE Issues tracker UE-226689](https://issues.unrealengine.com/issue/UE-226689)).

##### Iris vs Generic Replication Captures

Iris (enabled via `net.Iris.UseIrisReplication=1` in `DefaultEngine.ini`) replaces the default replication system's `NetBroadcastTickTime` with Iris-specific scopes like `FReplicationWriter_Write`. The Networking Insights view works identically for both systems. When analyzing Iris traces, watch for `FReplicationWriter_PrepareWrite` and `FReplicationWriter_FinishWrite` consuming more than expected — these wrap a per-frame temporary allocation that a [real-world analysis](https://bormor.dev/posts/iris-one-hundred-players/) showed to be 524 KB allocated and freed 101 times per frame at 100-player scale.

---

#### Animation Insights

##### Enabling Animation Insights

Animation Insights requires two plugins: `Animation Insights` and `Trace Data Filtering`. Enable both in Edit > Plugins, restart the editor, then navigate to Tools > Profile > Animation Insights. The recommended trace channel combination is:

```ini
-trace=cpu,frame,object,animation
```

The `object` channel is required for actor tracking; `animation` carries the pose, graph, curve, and montage events. Toggle channel filters in the Trace Data Filtering panel to limit data to specific Actors or Components using Class Filters and User Filters (Blueprint-based filters for custom logic).

##### Skeletal Animation Cost Analysis

Animation Insights adds tracks per-Actor below the CPU thread view. Each actor with a Skeletal Mesh Component gets a set of tracks: **Notifies**, **Curves**, **Pose**, **Graph**, **Montage**, and **Blend Weights**. The **Graph** track shows when the Animation Blueprint evaluated, with vertical bars indicating update ticks. Wide bars indicate expensive evaluation. Right-click a Graph track bar → "Debug this Graph" to open the Animation Blueprint debugger at that exact point in time, showing pose link weights, state machine positions, and blendspace sample coordinates ([Epic Animation Insights docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/animation-insights-in-unreal-engine)).

##### Anim Graph Performance

Animation Insights replaces the older `showdebug animation` text overlay with a visual timeline that can be scrubbed and reviewed post-capture. Key information visible in the Graph track includes which sub-graphs updated, the order of evaluation, and the time spent in each. Compare the Animation Blueprint eval time in Insights with the overall `USkeletalMeshComponent::TickAnimation` scope in the Game Thread view to understand what fraction of Game Thread budget animation consumes.

For projects with many characters, use Source Filtering to trace only specific Actors by class or name rather than all actors — this dramatically reduces trace size and overhead. Save filter presets for common investigation scenarios (player only, enemy archetype only) via the Filter Preset dropdown.

---

#### GPU Profiling

##### Insights GPU Track Limitations

The `gpu` channel in Insights captures GPU hardware timestamp queries and presents them as a timeline track. This is useful for identifying which passes are most expensive at a glance, but it has limitations before UE 5.6:

- Pass names can be generic ("DrawMesh", "RenderScene") without the fine-grained sub-pass detail available in dedicated GPU profilers.
- The GPU timeline does not show async compute queue utilization (before UE 5.6 GPU Profiler 2.0).
- Empty GPU tracks occur when D3D11 is active, when timestamp queries are disabled, or on certain driver/OS combinations.

As of UE 5.6, the GPU Profiler 2.0 unifies `stat gpu`, `ProfileGPU`, and Insights GPU data into a single stream from the RHI breadcrumb system, adding multi-queue awareness and compute pipeline visibility ([Tom Looman — UE 5.6 Performance Highlights](https://tomlooman.com/unreal-engine-5-6-performance-highlights/)).

##### When to Use GPU Visualizer (`ProfileGPU`) Instead

For identifying which specific render pass is expensive, `ProfileGPU` (keyboard shortcut Ctrl+, in editor, or type `ProfileGPU` in console) gives a hierarchical breakdown with exact millisecond costs per pass, including sub-passes inside Nanite, Lumen, VSM, and RDG. It is compiled into Development and Test builds (with `bAllowProfileGPUInTest = true` in Target.cs). Use it when the GPU track in Insights shows high cost on the GPU but you cannot identify which pass is responsible.

Enable detailed events before capturing:

```
r.EmitMeshDrawEvents 1
r.ShowMaterialDrawEvents 1
EnableIdealGPUCaptureOptions 1   // sets both of the above plus RDG debug names
```

([Intel UE5 Profiling Fundamentals](https://www.intel.com/content/www/us/en/developer/articles/technical/unreal-engine-optimization-profiling-fundamentals.html))

##### When to Use RenderDoc / PIX / Nsight

External GPU frame debuggers provide pixel-level analysis that Insights cannot: shader disassembly, texture contents, depth buffer visualization, draw call reordering. The decision matrix:

| Tool | Best for |
|------|---------|
| Unreal Insights | CPU+GPU correlation, session-length profiling, memory, networking |
| ProfileGPU (`stat gpu`) | Quick per-pass GPU cost breakdown without external tools |
| RenderDoc | Pixel-perfect debugging, overdraw visualization, shader stepping |
| PIX | GPU timeline with CPU correlation on Windows, deep D3D12 analysis |
| Nsight | NVIDIA-specific: warp occupancy, memory bandwidth, shader ALU analysis |

A common production pattern documented by developers at [r/unrealengine](https://www.reddit.com/r/unrealengine/comments/1mcc65m/small_studios_how_do_you_approach_game_performance/) is: confirm GPU bound in Insights → use ProfileGPU to identify expensive pass → use RenderDoc to inspect the specific draw calls in that pass.

##### Combining Traces (CPU Insights + GPU Visualizer Dump)

There is no single native workflow that fuses an Insights trace with a RenderDoc capture, but you can manually correlate them by using `TRACE_BOOKMARK` to mark the exact frame you then capture in RenderDoc. In your C++ BeginFrame or a console command:

```cpp
TRACE_BOOKMARK(TEXT("RenderDoc::CaptureFrame::%d"), GFrameNumber);
```

Then trigger a single-frame RenderDoc capture at the same frame number. The bookmark appears in Insights as a visible line, letting you confirm which frame in the session corresponds to the captured RenderDoc frame.

---

#### Workflow Tricks (The Lesser-Known Stuff)

##### Bookmarks for Level Streaming Events / GC Pass

Add bookmarks to engine events you care about by subclassing or using a delegate:

```cpp
// In your streaming manager or via a hook
FCoreUObjectDelegates::PreLoadMap.AddLambda([](const FString& MapName) {
    TRACE_BOOKMARK(TEXT("Map::PreLoad::%s"), *MapName);
});
```

For GC passes, `FCoreDelegates::GetPostGarbageCollect()` fires after each collection — add a bookmark there to correlate GC hitches with Insights timing data.

##### Auto-Trace on Startup with `-trace=...` and `-statnamedevents`

The most common launch arguments for a Steam game in Test config, suitable for sharing with QA:

```ini
YourGame-Win64-Test.exe -trace=cpu,frame,gpu,bookmark,counters,log -tracehost=127.0.0.1 -statnamedevents
```

Add this to the game's Steam launch options override: right-click the game in Steam → Properties → General → Launch Options. The [Epic Technical Developer Relations team demonstrated this at Unreal Fest Stockholm](https://www.youtube.com/watch?v=C-AjCqjKRSs) as the recommended way to profile a game you do not have source access to recompile.

##### Headless Server Traces in CI/CD

For a dedicated server running in CI, redirect the trace to a central `UnrealTraceServer` on your build machine:

```ini
YourServer-Win64-Test.exe -trace=cpu,frame,net,bookmark -tracehost=10.0.0.5 -NetTrace=1 &
```

The trace server stores the session with a timestamp-based filename. After the CI run, download the `.utrace` file as a build artifact. This enables regression tracking — if a build's `Game Thread` timer increases by more than a threshold, flag the CI run as a performance regression.

##### Symbol Resolution for Shipping Builds

Callstacks in Memory Insights require debug symbols to resolve function names. For a packaged Shipping build:

1. Build with `bUsePDBFiles=true` (or keep PDB files from the build machine).
2. Store the PDB files alongside the binary on your symbols server or a local path.
3. In Memory Insights, open the Modules panel and load symbols from the PDB directory.

Symbol resolution search order: user-specified paths → executable path → `UE_INSIGHTS_SYMBOLPATH` environment variable → `_NT_SYMBOL_PATH` (Windows symbol path) → user config. Setting `UE_INSIGHTS_SYMBOLPATH` in your environment is the most portable solution for team-wide symbol access ([Epic Memory Insights docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/memory-insights-in-unreal-engine)).

##### The `-statnamedevents` Command Line Flag — Shipping-Friendly Named Events

Adding `ENABLE_STATNAMEDEVENTS=1` to your Test target's `GlobalDefinitions` and launching with `-statnamedevents` exposes `SCOPED_NAMED_EVENT` calls in the Insights trace without the full STATS system. The tradeoff documented by [the Unreal Fest Stockholm profiling session](https://www.youtube.com/watch?v=C-AjCqjKRSs) is approximately 20% frame time overhead — use it for investigation, not for baseline performance measurement.

##### Trace Size Management

For long sessions, control file size by:

1. Enable only the channels you need: `-trace=cpu,frame,bookmark` is 10× smaller than `-trace=cpu,frame,gpu,memory,net`
2. Use `Trace.Stop` as soon as you have captured the scenario of interest
3. For CI, use `-benchmarkseconds=60` to automatically stop after 60 seconds
4. Disable `rhicommands` and `rendercommands` unless you are specifically investigating RHI threading — these channels are high volume

##### Filtering Noise: Hiding TaskGraph Workers and RHIThread

In the Timing panel, right-click the thread list → uncheck `TaskGraphThread*` to collapse all task workers. Right-click `RHIThread` → Hide Track. This leaves Game Thread, Render Thread, and GPU as the primary view — sufficient for 90% of optimization work. Save this layout via Window → Save Layout.

##### Insights "Live" Mode for Real-Time Monitoring

When you launch a game with `-tracehost=127.0.0.1` and Insights is open, the session appears in the browser with a green "LIVE" status. Double-click it to open a live-updating Timing view. The data streams in real time and the frame panel scrolls automatically. This is useful for monitoring a headless server or watching for intermittent hitches without needing to stop the process and re-analyze a file.

##### The Hidden CSV Export for Spreadsheet Analysis

From the Insights CLI, export timer statistics for any region or the entire session:

```ini
UnrealInsights.exe -AutoQuit -NoUI -OpenTraceFile="session.utrace" ^
  -ExecOnAnalysisCompleteCmd="TimingInsights.ExportTimerStatistics output.csv -threads=GameThread"
```

The resulting CSV has columns: Name, Count, InclusiveTime_ms, ExclusiveTime_ms. Import into Excel or Python for trend analysis across builds. This is the foundation of automated performance regression detection ([Intel UE5 Optimization Guide Chapter 2](https://www.intel.com/content/www/us/en/developer/articles/technical/unreal-engine-optimization-chapter-2.html)).

---

#### Common Pitfalls

##### Profiling in Editor Instead of Test Build

Already covered, but worth repeating as the single most common mistake. [Forum posts on r/unrealengine](https://www.reddit.com/r/unrealengine/comments/175y7ue/if_game_has_the_highest_ms_under_stat_unit_how_do/) document 3–4× frame time differences between Editor and Test. Optimization work done on Editor numbers is directionally useful at best, and actively misleading at worst.

##### Forgetting to Enable Channels Before Trace Start

The memory and loadtime channels must be active from process start. Any attempt to enable them via `Trace.Enable` after the game is running will capture data only from that moment forward — all prior allocations and all asset loads that already occurred are invisible. Always use the command line for these channels.

##### GPU Track Empty — DX12 Driver / Vendor Mismatch Issues

If the GPU track shows nothing or a flat line: confirm you are running D3D12 (not D3D11 or D3D11 fallback), check that `r.GPUCrashDebugging` is not forcing safe mode, verify your graphics driver is current, and confirm the engine is not running with `-nullrhi`. On some integrated GPU configurations the timestamp query may not be supported — try on a discrete GPU. Before UE 5.6, the GPU channel required specific driver support; after 5.6 the GPU Profiler 2.0 is more robust across vendors.

##### Symbol Resolution Failing in Shipping

Common causes: the PDB file does not match the binary (binaries rebuilt without updating PDB path), the `_NT_SYMBOL_PATH` points to a Microsoft symbol server that does not have your private symbols, or the PDB was stripped during packaging. Solution: always archive your PDB files alongside each Steam build. Add a post-build step in your CI pipeline to copy PDBs to a versioned symbols directory.

##### Insights Crash on Huge Traces — Chunking Captures

Traces exceeding approximately 4–8 GB can cause Insights to crash or become unresponsive during analysis, depending on available RAM. Solution: scope captures to specific scenarios using `Trace.Start`/`Trace.Stop`, keep the memory channel disabled unless specifically investigating leaks, and use regions to export only the relevant time window to CSV for analysis rather than loading the full file.

##### Confusing GPU Duration with Frame Time

The GPU track in Insights shows the duration of GPU work, not the time from frame start to frame end on the GPU. If async compute is enabled, multiple GPU queues may overlap — the visual track shows only the graphics queue. A frame where the GPU executes for 12 ms starting 3 ms after frame start does not necessarily mean a 12 ms GPU contribution to frame time. Always cross-reference with `stat unit`'s GPU readout, which measures GPU frame duration from the perspective of the Render Thread's present-to-present time.

---

#### Quick Reference: CVars and Command Lines

##### Essential Launch Arguments

```ini
# Minimal CPU profiling (low overhead)
-trace=cpu,frame,bookmark,counters

# Full CPU + GPU profiling
-trace=cpu,frame,gpu,bookmark,counters,log

# Named events (higher overhead, ~20% frame time cost)
-trace=cpu,frame,gpu,bookmark -statnamedevents

# Full memory leak investigation (must be from process start)
-trace=default,memory,metadata,assetmetadata -LLM

# Networking profiling (server + clients)
-trace=cpu,frame,net,bookmark -NetTrace=1

# Animation investigation
-trace=cpu,frame,object,animation

# Send to remote trace server
-tracehost=192.168.1.100

# Save directly to file (no server required)
-tracefile=C:\Traces\session.utrace

# CI/CD automated capture
-benchmarkseconds=60 -trace=cpu,frame,gpu,bookmark -tracefile=build_perf.utrace
```

##### Key Console Commands

```
Trace.Status               — show active channels and connection state
Trace.Enable <channels>    — add channels to a running trace
Trace.Stop                 — finalize and close the trace file
Trace.SendTo <ip> <channels> — start sending to a trace server from a running instance
Trace.RegionBegin <name>   — start a named multi-frame region
Trace.RegionEnd <name>     — end a named multi-frame region
ProfileGPU                 — capture one frame of GPU pass timing
stat unit                  — show GT/RT/GPU/RHIT frame times
stat namedevents           — enable named events at runtime
```

##### Instrumentation Macro Cheat Sheet

| Macro | Channel needed | Overhead | Use case |
|-------|----------------|----------|----------|
| `TRACE_CPUPROFILER_EVENT_SCOPE(Name)` | `cpu` | Low | Primary custom CPU scope |
| `TRACE_CPUPROFILER_EVENT_SCOPE_STR("text")` | `cpu` | Low | Static string scope |
| `SCOPE_CYCLE_COUNTER(STAT_X)` | `cpu` | Low–Medium | Dual Stats System + Insights |
| `SCOPED_NAMED_EVENT(Name, Color)` | `cpu` + `-statnamedevents` | High | Cross-tool annotations |
| `TRACE_BOOKMARK(TEXT("..."), ...)` | `bookmark` | Minimal | Event markers |
| `TRACE_DECLARE_INT_COUNTER(...)` | `counters` | Low | Game state over time |
| `LLM_SCOPE_BYTAG(Tag)` | `memtag`/`memory` + `-LLM` | Medium | Memory attribution |
| `TRACE_BEGIN_REGION_WITH_ID(TEXT("..."))` | `cpu` | Minimal | Multi-frame spans |

##### Build Configuration Profiling Capability

| Feature | Shipping | Test | Development |
|---------|----------|------|-------------|
| Unreal Insights trace | `UE_TRACE_ENABLED=1` | Yes | Yes |
| PIX / GPU markers | No | `bAllowProfileGPUInTest` | Yes |
| `stat` commands | No | Limited (`FORCE_USE_STATS=1`) | Full |
| `-statnamedevents` | No | `ENABLE_STATNAMEDEVENTS=1` | Yes |
| LLM Tracker | No | `ALLOW_LOW_LEVEL_MEM_TRACKER_IN_TEST=1` | Yes |
| Log to file | `bUseLoggingInShipping` | `bUseLoggingInShipping` | Yes |

([Intel UE5 Profiling Fundamentals](https://www.intel.com/content/www/us/en/developer/articles/technical/unreal-engine-optimization-profiling-fundamentals.html))

---

*Sources: [Epic — Unreal Insights docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-insights-in-unreal-engine) | [Epic — Memory Insights](https://dev.epicgames.com/documentation/en-us/unreal-engine/memory-insights-in-unreal-engine) | [Epic — Networking Insights](https://dev.epicgames.com/documentation/en-us/unreal-engine/networking-insights-in-unreal-engine) | [Epic — Animation Insights](https://dev.epicgames.com/documentation/en-us/unreal-engine/animation-insights-in-unreal-engine) | [Epic — Developer Guide to Tracing](https://dev.epicgames.com/documentation/en-us/unreal-engine/developer-guide-to-tracing-in-unreal-engine) | [Epic — LLM Tracker](https://dev.epicgames.com/documentation/en-us/unreal-engine/using-the-low-level-memory-tracker-in-unreal-engine) | [Tom Looman — Adding Counters & Traces](https://tomlooman.com/unreal-engine-profiling-stat-commands/) | [Tom Looman — UE 5.6 Performance Highlights](https://tomlooman.com/unreal-engine-5-6-performance-highlights/) | [Intel — UE5 Profiling Fundamentals](https://www.intel.com/content/www/us/en/developer/articles/technical/unreal-engine-optimization-profiling-fundamentals.html) | [Intel — UE5 Optimization Guide Chapter 2](https://www.intel.com/content/www/us/en/developer/articles/technical/unreal-engine-optimization-chapter-2.html) | [Unreal Community Wiki — Profiling with Insights](https://unrealcommunity.wiki/profiling-with-unreal-insights-ilad24y4) | [Unreal Fest 2024 — Optimizing the Game Thread](https://www.youtube.com/watch?v=KxREK-DYu70) | [Unreal Fest Bali 2025 — Mastering Performance Analysis with Unreal Insights](https://www.youtube.com/watch?v=HQLYkwoDoT4) | [Unreal Fest Stockholm 2025 — Performance Lessons from a Real Project](https://www.youtube.com/watch?v=C-AjCqjKRSs) | [BorMor — Iris 100 Players Analysis](https://bormor.dev/posts/iris-one-hundred-players/) | [Epic DevCom — Trace Server Ports](https://forums.unrealengine.com/t/connecting-unreal-insights-to-a-remote-trace-server/2662205)*


---

### CSVtoSVG Tool **[UE4 + UE5]**

Epic's `CSVtoSVG` tool converts CSV profiling output (from `-csvprofile` or Gauntlet automation) into SVG charts. Useful for regression tracking across builds in CI pipelines. Located in `Engine/Programs/CSVTools/`.

---

### RenderDoc / PIX / NSight **[UE4 + UE5]**

Enable RenderDoc via Plugins > RenderDoc. Restart editor. A toolbar button appears for frame capture. Inside RenderDoc:
- Inspect per-draw-call shader source, resource bindings, and output
- Examine render target contents after each pass
- Profile with GPU timing overlay

When capturing with D3D12, set `r.ShowMaterialDrawEvents 0` before capture to eliminate GPU marker overhead from skewing timing. Use PIX (Microsoft) or NSight (NVIDIA) when you need warp-level or shader register analysis.

---

### Build Configurations **[UE4 + UE5]**

| Config | Optimization | Logging | Profiling | Use For |
|---|---|---|---|---|
| Debug | None | Full | Full | Engine/plugin debugging |
| DebugGame | Full (engine) | Full | Full | Gameplay debugging |
| Development | Full | Full | Full | Daily iteration |
| Test | Full (Shipping) | Configurable | Insights + stat | **Performance profiling** |
| Shipping | Full | Minimal | None | Release builds |

**Always profile in Test.** It matches Shipping optimizations but retains Insights trace support. In `.Target.cs`:
```cpp
if (Target.Configuration == UnrealTargetConfiguration.Test)
{
    bAllowProfileGPUInTest = true;
    GlobalDefinitions.Add("ENABLE_STATNAMEDEVENTS=1");
    GlobalDefinitions.Add("ALLOW_LOW_LEVEL_MEM_TRACKER_IN_TEST=1");
}
```

---

### LLM (Low-Level Memory Tracker) **[UE4.20+ expanded in UE5]**

LLM tracks memory at the allocation level, categorized by LLM tags. Enable with `-LLM` on launch. View in Insights (memtag channel) or via `stat LLM` overlay. Define custom tags in C++:
```cpp
LLM_DEFINE_TAG(MySystem, NAME_None, NAME_None, GET_STATFNAME(STAT_MySystemLLM), GET_STATFNAME(STAT_MySystemLLM_Summary));

// In code:
LLM_SCOPE_BYTAG(MySystem);
```
LLM has overhead in non-shipping builds. The `memtag` channel in Insights (minimal overhead) is suitable for live monitoring; full `memory` channel is for leak investigation.

---

## Prerequisites for Checkups

Before profiling:

1. **Profile in a Test build** packaged for the target platform, not in Editor PIE.
2. **Close other applications** consuming CPU or GPU resources (Chrome, Discord, OBS, secondary monitors with heavy compositors).
3. **Establish a stable 60-second baseline** in a representative gameplay scenario — not the main menu, not a cutscene, but actual gameplay.
4. **Disable VSync** during CPU/GPU bottleneck investigation (`r.VSync 0`) to see uncapped frame times.
5. **Profile on target hardware.** Profiling on a developer workstation and shipping on console gives misleading data. Use platform-specific profiling tools for console targets.
6. **One change at a time.** Make one optimization, measure, compare. Multiple simultaneous changes make it impossible to attribute gains or regressions.

---

## Basic Checkup List **[UE4 + UE5]**

1. Run `stat unit` in a representative play session. Identify the bottleneck thread (Game, Draw, GPU, RHIT).
2. If GPU-bound: run `ProfileGPU`. Find the most expensive passes. Use View Modes (Shader Complexity, Nanite Overdraw, VSM Visualization) to localize.
3. If Game Thread-bound: open Insights with `cpu,frame,bookmark` channels. Sort Timers by Exclusive Time. Look for tick-heavy actors, frequent GC passes (`FGarbageCollection`), or expensive physics.
4. If Render Thread-bound: excessive draw calls (non-Nanite geometry), overdraw from translucency, or high Material/Shader complexity on the Render Thread task list.

---

## Advanced Checkup List **[UE4 + UE5]**

1. **Baseline capture.** Test build, `stat unit` stable, Insights trace running (`cpu,frame,gpu,bookmark`).
2. **Identify the stack.** Use `stat unit` → Insights flame graph → ProfileGPU in that order. Never jump directly to GPU tooling if the Game Thread is the bottleneck.
3. **Tick budget audit.** In Insights Timers tab, filter by Game Thread, sort Exclusive Time. Look for `ActorTick`, `ComponentTick`, and custom tick functions above 0.5 ms.
4. **GC pressure check.** In Insights, look for `FGarbageCollection::Collect` spikes. If GC > 5 ms regularly, audit UObject count (`obj list`), enable clustering, reduce per-frame UObject allocations.
5. **Memory audit.** `Memreport -full` or Memory Insights with `memory,assetmetadata`. Look for texture pool overrun (`r.Streaming.PoolSize`), unexpected asset loads (check Soft vs Hard references with Size Map).
6. **Streaming hitch audit.** `stat streaming`. Hitches from streaming = too-large cells, too many actors per cell, or synchronous loads. Use `Trace.RegionBegin/End` around level transitions.
7. **GPU pass breakdown.** ProfileGPU. Identify top 3 passes by cost. Shadow rendering (VSM, shadow depth) and Lumen Screen Probe Gather are most commonly over-budget.
8. **Nanite audit [UE5 only].** `stat nanite` + Nanite → Overdraw view mode. Identify overdraw clusters > 4×. Check for Nanite enabled on simple meshes (< 300 triangles).
9. **Network audit (multiplayer).** `stat net`. Check for excessive bandwidth, actor relevancy overhead, or RPC spam. Enable Networking Insights for packet-level analysis.
10. **Validate in Shipping build.** Run a final smoke test in Shipping config. Some optimizations that appear in Development (stat display overhead) are not present in Shipping.

**Frame budget targets:**

| Target FPS | Frame budget | Game Thread | Render Thread | GPU |
|---|---|---|---|---|
| 60 FPS | 16.7 ms | < 8 ms | < 7 ms | < 16 ms |
| 30 FPS | 33.3 ms | < 15 ms | < 14 ms | < 33 ms |
| 120 FPS | 8.3 ms | < 4 ms | < 4 ms | < 8 ms |

These are guidelines — threads run in parallel, so the effective frame time is the maximum of the three, not the sum.
