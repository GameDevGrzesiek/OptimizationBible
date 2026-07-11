# Useful Plugins for Unreal Engine

A curated list of plugins and tools that help with (or are relevant to) optimization work in Unreal Engine projects.

**This is a living document** — it will grow over time. If you know a plugin worth adding, [let me know](https://github.com/GameDevGrzesiek/OptimizationBible#readme) and I'll credit your contribution.

---

## Table of Contents

- [Profiling & Debugging](#profiling--debugging)
- [Gameplay & Architecture](#gameplay--architecture)
- [Multiplayer](#multiplayer)
- [UI](#ui)
- [Animation](#animation)

---

## Profiling & Debugging

| Plugin | What it does | Notes |
|---|---|---|
| [RenderDoc plugin (built-in)](https://renderdoc.org/) | One-click GPU frame captures from the editor toolbar | Enable via Plugins → RenderDoc; see [UE Tools doc](UnrealEngineTools.md) |
| PIX plugin (built-in) | Attach PIX for D3D12 GPU captures | When enabled, launch with `-AttachPIX`; capture via editor button or `pix.GpuCaptureFrame` — even without launching PIX itself *(contributed by [Radosław Paszkowski](https://www.linkedin.com/in/rpaszkowski/))* |
| [Gameplay Insights / Animation Insights (built-in)](https://dev.epicgames.com/documentation/en-us/unreal-engine/animation-insights-in-unreal-engine) | Extends Unreal Insights with animation/gameplay tracks | Ships with the engine, disabled by default |

## Gameplay & Architecture

| Plugin | What it does | Notes |
|---|---|---|
| [UE-DynamicOctree](https://github.com/BenVlodgi/UE-DynamicOctree) | Easy-to-use octree for spatial queries | The right alternative to `Get All Actors Of Class` / `Get All Actors With Interface` for spatial lookups. Written for UE5, but contains no Content, so it's relatively easy to port to UE4 *(contributed by [Urszula Kustra](https://www.linkedin.com/in/urszula-kustra/))* |
| [FastActorIterator](https://github.com/moadib/FastActorIterator) | Per-class actor lists with `GetAllActorsOfClass`-compatible signatures | Fast iteration over actors in worlds with large actor counts |
| [GameplayMessageRouter (Lyra)](https://dev.epicgames.com/documentation/en-us/unreal-engine/lyra-sample-game-in-unreal-engine) | Global event bus: one generic delegate accepting any struct + generic AsyncAction node | Create any global event without recompiling code; integrate it from the Lyra sample *(contributed by [Urszula Kustra](https://www.linkedin.com/in/urszula-kustra/))* |
| [Gameplay Ability System (GAS)](https://dev.epicgames.com/documentation/en-us/unreal-engine/gameplay-ability-system-for-unreal-engine) | Framework for abilities, attributes, and gameplay effects | Also a multiplayer optimization aid — see below *(contributed by [Urszula Kustra](https://www.linkedin.com/in/urszula-kustra/))* |

## Multiplayer

| Plugin | What it does | Notes |
|---|---|---|
| [Replication Graph](https://dev.epicgames.com/documentation/en-us/unreal-engine/replication-graph-in-unreal-engine) | Spatial-grid based replication relevancy | For 50+ concurrent replicating actors per client; O(1) relevancy checks |
| [Gameplay Ability System (GAS)](https://dev.epicgames.com/documentation/en-us/unreal-engine/gameplay-ability-system-for-unreal-engine) | GameplayCues for replicated cosmetics | Reduces the need to enable replication on many actor instances just to fire a cosmetic Multicast — grab the `AbilitySystemComponent` from e.g. the Instigator and trigger a GameplayCue on it *(contributed by [Urszula Kustra](https://www.linkedin.com/in/urszula-kustra/))* |

## UI

| Plugin | What it does | Notes |
|---|---|---|
| [Common UI](https://dev.epicgames.com/documentation/en-us/unreal-engine/common-ui-plugin-for-advanced-user-interfaces-in-unreal-engine) **[UE5]** | Platform-agnostic input routing, activatable widget stacks | Encourages the widget-stack/switcher architecture that keeps inactive UI from ticking |

## Animation

| Plugin | What it does | Notes |
|---|---|---|
| [Animation Budget Allocator](https://dev.epicgames.com/documentation/en-us/unreal-engine/animation-budget-allocator-in-unreal-engine) | Dynamically throttles skeletal animation quality to fit a fixed budget | Essential for crowd-heavy scenes |
