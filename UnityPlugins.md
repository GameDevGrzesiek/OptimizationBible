# Useful Plugins for Unity

A curated list of plugins, packages, and tools that help with (or are relevant to) optimization work in Unity projects.

**This is a living document** — it will grow over time. If you know a plugin worth adding, [let me know](https://github.com/GameDevGrzesiek/OptimizationBible#readme) and I'll credit your contribution.

---

## Table of Contents

- [All Types](#all-types)
- [2D Games](#2d-games)
- [3D Games](#3d-games)

---

## All Types

| Plugin / Package | What it does | Notes |
|---|---|---|
| [Memory Profiler](https://docs.unity3d.com/Packages/com.unity.memoryprofiler@latest) | Full memory snapshots with diffing | First-party package; essential for leak hunting |
| [Profile Analyzer](https://docs.unity3d.com/Packages/com.unity.performance.profile-analyzer@latest) | Statistical comparison of profiler captures | First-party; quantitative before/after regression checks |
| [Performance Testing Extension](https://docs.unity3d.com/Packages/com.unity.test-framework.performance@latest) | `Measure.Method` / `Measure.Frames` for automated perf tests | Integrates with CI to flag regressions |
| [Compilation Visualizer](https://github.com/needle-tools/compilation-visualizer) | Visualizes asmdef compilation order and dependencies | Audit compile-time bottlenecks |
| [Build Report Inspector](https://docs.unity3d.com/Packages/com.unity.build-report-inspector@latest) | Inspects build size per asset | Find what bloats your build |
| [Addressables](https://docs.unity3d.com/Packages/com.unity.addressables@latest) | Reference-counted async asset loading | The standard asset management layer; see the [Unity Tools doc](UnityTools.md) for the Profiler module tip |
| [Graphy](https://github.com/Tayx94/graphy) | Runtime FPS / memory / audio monitor overlay | Free, MIT; great for QA builds |
| [Superluminal](https://superluminal.eu/) | External sampling CPU profiler | Not a plugin per se, but attaches to Unity/IL2CPP builds |

## 2D Games

| Plugin / Package | What it does | Notes |
|---|---|---|
| [Sprite Atlas (built-in)](https://docs.unity3d.com/Manual/class-SpriteAtlas.html) | Batches sprites into shared textures | Remember: compress the atlas, not the source sprites (see [Unity guide — UI section](Unity.md)) |
| [2D PSD Importer](https://docs.unity3d.com/Packages/com.unity.2d.psdimporter@latest) | Imports layered PSB files directly | Keeps source files out of runtime atlas memory when configured correctly |

*(section to be expanded)*

## 3D Games

| Plugin / Package | What it does | Notes |
|---|---|---|
| [UnityMeshSimplifier](https://github.com/Whinarn/UnityMeshSimplifier) | Automatic mesh decimation / LOD generation | Free, MIT |
| [Amplify Impostors](https://assetstore.unity.com/packages/tools/utilities/amplify-impostors-119877) | Bakes meshes into billboard impostors | Massive draw call and triangle savings for distant objects |
| [GPU Instancer Pro](https://assetstore.unity.com/packages/tools/utilities/gpu-instancer-pro-283742) | Indirect GPU instancing for vegetation/props/crowds | For pre-Unity 6 projects without GPU Resident Drawer |

*(section to be expanded)*
