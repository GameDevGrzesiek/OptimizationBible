# Console Hardware Specs and PC Equivalents

## Introduction

The "PC equivalent" ratings in this document are approximations. Consoles benefit from low-level, metal-to-the-metal APIs (GNM/GNMX on PlayStation, DirectX 12 Ultimate on Xbox), a fixed and fully known hardware target, unified memory pools that eliminate VRAM/system RAM boundaries, and years of developer optimization on a single silicon revision. A PC matching a console's raw TFLOP count will typically need 20--40 percent more headroom to deliver the same frame-rate targets at the same visual quality, because PC drivers, Windows overhead, variable hardware configurations, and higher-level graphics APIs all introduce overhead that console developers simply do not face. ML upscalers (DLSS, PSSR) and hardware ray-tracing units add further console-specific advantages that cannot be replicated purely through raw raster performance comparisons. All equivalencies below are therefore guidance for matching gaming workload output, not raw spec-sheet parity.

---

## Table of Contents

- [Console Hardware Specs and PC Equivalents](#console-hardware-specs-and-pc-equivalents)
  - [Introduction](#introduction)
  - [1. Nintendo Switch (Original, 2017) -- NVIDIA Tegra X1](#1-nintendo-switch-original-2017-nvidia-tegra-x1)
    - [A. Official Hardware Specs](#a-official-hardware-specs)
    - [B. PC Equivalent -- Variant 1 (Intel CPU + NVIDIA GPU)](#b-pc-equivalent-variant-1-intel-cpu-nvidia-gpu)
    - [C. PC Equivalent -- Variant 2 (Full AMD)](#c-pc-equivalent-variant-2-full-amd)
  - [2. Nintendo Switch 2 (2025) -- NVIDIA T239 (Custom Ampere)](#2-nintendo-switch-2-2025-nvidia-t239-custom-ampere)
    - [A. Official Hardware Specs](#a-official-hardware-specs-1)
    - [B. PC Equivalent -- Variant 1 (Intel CPU + NVIDIA GPU)](#b-pc-equivalent-variant-1-intel-cpu-nvidia-gpu-1)
    - [C. PC Equivalent -- Variant 2 (Full AMD)](#c-pc-equivalent-variant-2-full-amd-1)
  - [3. Xbox Series S](#3-xbox-series-s)
    - [A. Official Hardware Specs](#a-official-hardware-specs-2)
    - [B. PC Equivalent -- Variant 1 (Intel CPU + NVIDIA GPU)](#b-pc-equivalent-variant-1-intel-cpu-nvidia-gpu-2)
    - [C. PC Equivalent -- Variant 2 (Full AMD)](#c-pc-equivalent-variant-2-full-amd-2)
  - [4. Xbox Series X](#4-xbox-series-x)
    - [A. Official Hardware Specs](#a-official-hardware-specs-3)
    - [B. PC Equivalent -- Variant 1 (Intel CPU + NVIDIA GPU)](#b-pc-equivalent-variant-1-intel-cpu-nvidia-gpu-3)
    - [C. PC Equivalent -- Variant 2 (Full AMD)](#c-pc-equivalent-variant-2-full-amd-3)
  - [5. PlayStation 5](#5-playstation-5)
    - [A. Official Hardware Specs](#a-official-hardware-specs-4)
    - [B. PC Equivalent -- Variant 1 (Intel CPU + NVIDIA GPU)](#b-pc-equivalent-variant-1-intel-cpu-nvidia-gpu-4)
    - [C. PC Equivalent -- Variant 2 (Full AMD)](#c-pc-equivalent-variant-2-full-amd-4)
  - [6. PlayStation 5 Pro (Released November 2024)](#6-playstation-5-pro-released-november-2024)
    - [A. Official Hardware Specs](#a-official-hardware-specs-5)
    - [B. PC Equivalent -- Variant 1 (Intel CPU + NVIDIA GPU)](#b-pc-equivalent-variant-1-intel-cpu-nvidia-gpu-5)
    - [C. PC Equivalent -- Variant 2 (Full AMD)](#c-pc-equivalent-variant-2-full-amd-5)
  - [Summary Table](#summary-table)
  - [Caveats and Console-Specific Advantages](#caveats-and-console-specific-advantages)
    - [Unified Memory Architecture](#unified-memory-architecture)
    - [Fixed-Function Hardware: Console-Specific Blocks](#fixed-function-hardware-console-specific-blocks)
    - [Ray Tracing Hardware Generations](#ray-tracing-hardware-generations)
    - [Driver and OS Overhead](#driver-and-os-overhead)
    - [API Efficiency](#api-efficiency)

---

## 1. Nintendo Switch (Original, 2017) -- NVIDIA Tegra X1

### A. Official Hardware Specs

| Component | Specification |
|---|---|
| SoC | NVIDIA Tegra T210 (Tegra X1) |
| CPU Architecture | ARM big.LITTLE: 4x Cortex-A57 + 4x Cortex-A53 |
| CPU Clock (docked) | 1020 MHz (A57 cluster active) |
| CPU Clock (handheld) | 1020 MHz; 1 core reserved for OS (3 available to developers) |
| GPU Architecture | NVIDIA Maxwell (GM20B variant) |
| GPU Compute Units | 2 SMs / 256 CUDA cores |
| GPU Clock (docked) | 768 MHz |
| GPU Clock (handheld) | ~307--460 MHz |
| GPU TFLOPS (docked, FP32) | ~0.39 TFLOPS |
| GPU TFLOPS (handheld) | ~0.15--0.19 TFLOPS |
| RAM Total | 4 GB LPDDR4 |
| RAM Bandwidth (docked) | 25.6 GB/s (64-bit bus at 1600 MHz) |
| RAM Bandwidth (handheld) | ~21.3 GB/s (downclocked) |
| RAM for Games | ~3.2 GB (0.8 GB reserved for OS) |
| Storage | 32 GB eMMC internal; microSD expansion |
| Storage Bandwidth | eMMC (no NVMe); much slower than SSD |
| RT Cores | None |
| ML Upscaler | None (Maxwell predates Tensor cores) |
| Process Node | 20 nm (TSMC), revised to 16 nm FinFET (Mariko revision, 2019) |
| Power Budget | ~7--11 W SoC load docked; ~8--9 W handheld under load |

Sources: [Nintendo Switch Tegra X1 architecture -- SwitchBrew](https://switchbrew.org/wiki/Tegra_X1), [AnandTech Switch Power Analysis](https://www.neogaf.com/threads/anandtech-switch-power-consumption-analysis.1350361/), [Chips and Cheese Maxwell GPU analysis](https://chipsandcheese.com/p/nintendo-switchs-igpu-maxwell-nerfed-edition), [TweakTown teardown confirmation](https://www.tweaktown.com/news/56725/nintendo-switch-stock-nvidia-tegra-x1-cpu-maxwell-gpu/index.html)

Notable context: The Tegra X1 in the Switch runs the Maxwell GPU below its rated 1 GHz ceiling. The docked 768 MHz GPU clock is already a significant underclock from the chip's specification. Maxwell's architecture predates dedicated RT or Tensor hardware; any ML-based upscaling or ray tracing is absent entirely.

---

### B. PC Equivalent -- Variant 1 (Intel CPU + NVIDIA GPU)

| Component | Recommendation |
|---|---|
| CPU | Intel Core i3-6100 (dual-core, 3.7 GHz, Skylake) |
| GPU | NVIDIA GeForce GT 1030 (2 GB GDDR5) |
| RAM | 4 GB DDR4-2133 |

Justification: The Tegra X1's Maxwell GPU at 768 MHz delivers approximately 0.39 TFLOPS FP32. The GT 1030 (384 CUDA cores at ~1.23 GHz boost) delivers ~0.63 TFLOPS -- modestly above the docked Switch -- but given console-optimized code efficiency, a GT 1030 is the closest practical desktop GPU. The 4 GB RAM ceiling mirrors the Switch's total pool. An i3-6100 provides comparable CPU throughput to the A57 cluster for game workloads.

---

### C. PC Equivalent -- Variant 2 (Full AMD)

| Component | Recommendation |
|---|---|
| CPU | AMD Ryzen 3 1200 (quad-core, 3.1 GHz base, Zen) |
| GPU | AMD Radeon RX 460 2 GB (or RX 550 as alternative) |
| RAM | 4 GB DDR4-2133 |

Justification: The RX 460 (896 stream processors, ~2.2 TFLOPS at a low power envelope) is overpowered in raw TFLOPS but constrained in practice at 2 GB VRAM and older driver optimization. Given the Switch's extreme efficiency advantages, the RX 460/550 class represents a fair analog for PC gaming output at Switch-equivalent settings. The Ryzen 3 1200 closely matches A57 quad-core single-thread performance.

---

## 2. Nintendo Switch 2 (2025) -- NVIDIA T239 (Custom Ampere)

### A. Official Hardware Specs

| Component | Specification |
|---|---|
| SoC | NVIDIA T239 (custom, Samsung 8 nm) |
| CPU Architecture | 8x ARM Cortex-A78C, ARMv8 64-bit, cryptography extensions |
| CPU Clock (docked) | 998 MHz |
| CPU Clock (handheld) | 1101 MHz |
| CPU Clock (maximum rated) | 1.7 GHz (potentially used for asset decompression) |
| CPU Cores for Games | 6 (2 reserved for OS) |
| GPU Architecture | NVIDIA Ampere (as in RTX 30 series) |
| GPU CUDA Cores | 1536 |
| GPU Clock (handheld) | 561 MHz |
| GPU Clock (docked) | 1007 MHz |
| GPU Clock (maximum stated) | 1.4 GHz |
| GPU TFLOPS (docked, FP32) | 3.072 TFLOPS |
| GPU TFLOPS (handheld) | ~1.71 TFLOPS |
| RT Performance | ~10 Grays/s handheld, ~20 Grays/s docked |
| RAM Total | 12 GB LPDDR5X (2x 6 GB modules), 128-bit bus |
| RAM Bandwidth (docked) | 102 GB/s |
| RAM Bandwidth (handheld) | 68 GB/s |
| RAM for Games | 9 GB (3 GB reserved for OS / GameChat) |
| Storage | 256 GB UFS internal; microSD Express up to 2 TB |
| Notable Features | DLSS (1x/2x/3x + DLAA), dedicated RT cores (Ampere 2nd-gen), hardware file decompression engine (LZ4), G-Sync VRR on internal display |
| Power Budget | ~10--12 W handheld; ~18--19 W docked (system total) |

Sources: [Digital Foundry / Eurogamer confirmed specs -- May 2025](https://www.eurogamer.net/digitalfoundry-2025-nintendo-switch-2-final-tech-specs-and-system-reservations-confirmed), [Nintendo Life spec table](https://www.nintendolife.com/news/2025/05/nintendo-switch-2-final-tech-specs-have-been-confirmed), [Digital Foundry YouTube deep dive](https://www.youtube.com/watch?v=huxDoYXS8Ng), [Notebookcheck coverage](https://www.notebookcheck.net/Digital-Foundry-confirms-Nintendo-Switch-2-specs-with-CPU-GPU-and-surprising-memory-allocation-details.1015981.0.html), [Famiboards power draw thread](https://famiboards.com/threads/switch-2-power-draw.14150/)

Notable context: The T239 is purpose-built silicon, not an off-the-shelf product. The CPU curiously runs faster in handheld mode (1101 MHz) than docked mode (998 MHz), which Digital Foundry speculates compensates for reduced memory bandwidth in portable play. The GPU gets the same Ampere second-gen RT cores and Tensor cores found in desktop RTX 30 series, enabling real DLSS inference and hardware-accelerated BVH traversal for ray tracing. DLSS is confirmed in the Nintendo SDK. Samsung 8 nm is an older node than rivals (Steam Deck uses TSMC 7 nm), but the chip's compact die (~200--220 mm²) manages thermals effectively within its power budget.

---

### B. PC Equivalent -- Variant 1 (Intel CPU + NVIDIA GPU)

| Component | Recommendation |
|---|---|
| CPU | Intel Core i5-11400 (6-core, 2.6--4.4 GHz, Rocket Lake) |
| GPU | NVIDIA GeForce RTX 2060 (6 GB GDDR6) / RTX 2050 mobile (for the docked-mode analogy) |
| RAM | 12 GB DDR4-3200 |

Justification: At 3.072 TFLOPS docked and with DLSS + dedicated RT cores, the T239 most closely resembles a significantly power-constrained desktop RTX 2060 or a full-power mobile RTX 2050/2060. The RTX 2060 (1920 CUDA cores Turing) provides comparable raster throughput and shares the same DLSS 1st/2nd-gen Tensor core capability. Docked at 1007 MHz the T239 delivers 3.07 TFLOPS vs. the RTX 2060's ~6.5 TFLOPS at desktop clocks -- however, the Switch runs at a fraction of the power (18 W system vs. ~160 W desktop card TGP), and heavily optimized console code closes the practical gap significantly. An i5-11400 provides strong single-thread performance matching the A78C cores in gaming workloads.

---

### C. PC Equivalent -- Variant 2 (Full AMD)

| Component | Recommendation |
|---|---|
| CPU | AMD Ryzen 5 5600 (6-core, 3.5--4.4 GHz, Zen 3) |
| GPU | AMD Radeon RX 6600 (8 GB GDDR6) |
| RAM | 12 GB DDR4-3200 |

Justification: The RX 6600 (1792 stream processors, RDNA 2, ~8 TFLOPS) gives more raw headroom than the T239 to compensate for PC overhead, and represents the lower end of what a PC user would need to match Switch 2 docked performance in optimized titles. It lacks hardware ML upscaling equivalent to DLSS (FSR is shader-based, not Tensor-driven), so at equivalent output quality, the RX 6600 needs its extra raster headroom to compensate. Ryzen 5 5600 matches A78C single-thread throughput in a 6-core configuration.

---

## 3. Xbox Series S

### A. Official Hardware Specs

| Component | Specification |
|---|---|
| SoC | Custom AMD, 7 nm |
| Die Size | 197.05 mm² |
| CPU Architecture | 8x AMD Zen 2 cores, custom |
| CPU Clock | 3.6 GHz (3.4 GHz with SMT enabled) |
| GPU Architecture | AMD RDNA 2, custom |
| GPU Compute Units | 20 CUs |
| GPU Clock | 1.565 GHz |
| GPU TFLOPS (FP32) | 4 TFLOPS |
| RAM Total | 10 GB GDDR6, 128-bit bus |
| RAM Bandwidth | 8 GB @ 224 GB/s; 2 GB @ 56 GB/s |
| RAM for Games | ~7.5 GB (OS reserves ~2.5 GB) |
| Storage | 512 GB Custom PCIe 4.0 NVMe SSD |
| Storage I/O | 2.4 GB/s raw; 4.8 GB/s compressed (custom hardware decompression) |
| RT Support | Hardware DirectX Raytracing (RDNA 2 RT units) |
| ML Upscaler | None dedicated (FSR shader-based available) |
| Target Resolution | 1440p @ 60 FPS; up to 120 FPS |
| Power Budget | ~65--77 W under gaming load |

Sources: [Microsoft Xbox Series S official specs page](https://www.xbox.com/en-US/consoles/xbox-series-s), [Microsoft Store Series S listing](https://www.microsoft.com/en-us/d/xbox-series-s/942j774tp9jn), [Tom's Hardware spec comparison](https://www.tomshardware.com/news/xbox-series-s-specs-reveal)

Notable context: Despite only 4 TFLOPS, the Series S delivers solid 1440p gaming because its Zen 2 CPU is identical in architecture to the Series X (slightly lower clocked), it shares the same custom PCIe 4.0 NVMe SSD bandwidth as Series X, and Xbox Velocity Architecture (XVA) includes Sampler Feedback Streaming (SFS) and DirectStorage which reduce effective GPU VRAM pressure. The 10 GB GDDR6 total is tight for modern 4K assets, which is why 1440p is the resolution target. The Series S APU TDP is approximately 100 W at the chip level based on comparable RDNA 2 silicon; system power draw is 65--77 W in gaming.

---

### B. PC Equivalent -- Variant 1 (Intel CPU + NVIDIA GPU)

| Component | Recommendation |
|---|---|
| CPU | Intel Core i5-10400 (6-core, 2.9--4.3 GHz, Comet Lake) |
| GPU | NVIDIA GeForce GTX 1660 Super (6 GB GDDR6) |
| RAM | 10 GB (8+2 GB) DDR4-3200 |

Justification: The GTX 1660 Super (1408 CUDA cores Turing, ~5 TFLOPS at full desktop clocks) provides the raw raster headroom a PC needs to match Series S in 1440p gaming, compensating for the lack of console-level driver optimization. It does not have RT cores (unlike RDNA 2), so for RT workloads an RTX 3060 (12 GB) is a better match. The i5-10400 maps well to Zen 2 8c performance in game workloads at its price tier.

---

### C. PC Equivalent -- Variant 2 (Full AMD)

| Component | Recommendation |
|---|---|
| CPU | AMD Ryzen 5 3600 (6-core, 3.6--4.2 GHz, Zen 2) |
| GPU | AMD Radeon RX 6600 XT (8 GB GDDR6) |
| RAM | 10 GB DDR4-3200 |

Justification: The RX 6600 XT (2048 stream processors, RDNA 2, ~10.6 TFLOPS) surpasses the Series S GPU on paper due to PC overhead requirements. In practice, benchmarks against Xbox Series S show the RX 6600 XT winning by a significant margin, which is intentional: the PC needs that overhead to match console-equivalent output. The Ryzen 5 3600 is a direct Zen 2 architectural equivalent to the Series S CPU, differing mainly in that the console runs 8 cores at a slightly higher clock with custom memory access patterns.

---

## 4. Xbox Series X

### A. Official Hardware Specs

| Component | Specification |
|---|---|
| SoC | Custom AMD, 7 nm Enhanced (TSMC) |
| Die Size | 360.45 mm² |
| CPU Architecture | 8x AMD Zen 2 cores, custom |
| CPU Clock | 3.8 GHz (3.6 GHz with SMT enabled) |
| GPU Architecture | AMD RDNA 2, custom |
| GPU Compute Units | 52 CUs |
| GPU Clock | 1.825 GHz |
| GPU TFLOPS (FP32) | 12 TFLOPS |
| RAM Total | 16 GB GDDR6, 320-bit bus |
| RAM Bandwidth | 10 GB @ 560 GB/s; 6 GB @ 336 GB/s |
| RAM for Games | ~13.5 GB (OS reserves ~2.5 GB) |
| Storage | 1 TB Custom PCIe 4.0 NVMe SSD |
| Storage I/O | 2.4 GB/s raw; 4.8 GB/s compressed (hardware decompression + SFS) |
| RT Support | Hardware DirectX Raytracing (RDNA 2 BVH traversal units) |
| ML Upscaler | None dedicated (FSR shader-based; no Tensor-core equivalent) |
| Target Resolution | 4K @ 60 FPS; up to 120 FPS |
| Power Budget | ~150--200 W under gaming load |

Sources: [Xbox Series X official specs -- Xbox.com](https://www.xbox.com/en-US/consoles/xbox-series-x), [WCCFTech full spec reveal](https://wccftech.com/xbox-series-x-specs/), [The Verge 12 TFLOPS confirmation](https://www.theverge.com/2020/2/24/21150578/microsoft-xbox-series-x-specs-performance-12-teraflops-gpu-details-features)

Notable context: The Series X GPU's 52 CUs at 1.825 GHz is a notably high clock for RDNA 2, which Microsoft achieved by binning the 7 nm die for high-frequency performance. Sampler Feedback Streaming (SFS) is a Microsoft-proprietary technique that reduces effective GPU memory load by only streaming the mip levels currently visible, making the 16 GB pool behave more efficiently than a 16 GB PC VRAM pool. The CPU is the same Zen 2 architecture as the Ryzen 3000 series but runs at a slightly higher fixed clock.

---

### B. PC Equivalent -- Variant 1 (Intel CPU + NVIDIA GPU)

| Component | Recommendation |
|---|---|
| CPU | Intel Core i7-10700K (8-core, 3.8--5.1 GHz, Comet Lake) |
| GPU | NVIDIA GeForce RTX 3070 (8 GB GDDR6) |
| RAM | 16 GB DDR4-3600 |

Justification: The Series X GPU at 12 TFLOPS (RDNA 2) sits between the RTX 3060 Ti (~16.2 TFLOPS) and RTX 3070 (~20 TFLOPS) in raw FP32. However, the Series X's RDNA 2 architecture and fixed-function hardware, combined with 560 GB/s peak memory bandwidth and SFS, means real-world performance punches above its raw TFLOPS. A PC RTX 3070 provides comfortable headroom to match Series X gaming output across 4K/60 titles, factoring in the usual 20--30% PC overhead. An i7-10700K closely mirrors the 8-core Zen 2 CPU in games that are thread-sensitive. Digital Foundry's analysis has aligned Series X with approximately RX 6800 or RTX 3070-class desktop performance in optimized titles.

---

### C. PC Equivalent -- Variant 2 (Full AMD)

| Component | Recommendation |
|---|---|
| CPU | AMD Ryzen 7 3700X (8-core/16-thread, 3.6--4.4 GHz, Zen 2) |
| GPU | AMD Radeon RX 6800 (16 GB GDDR6) |
| RAM | 16 GB DDR4-3600 |

Justification: The Ryzen 7 3700X is the most direct architectural equivalent to the Series X CPU -- same Zen 2 cores, same 8-core count, comparable base clock. The RX 6800 (60 CUs, RDNA 2, ~16.2 TFLOPS) is the natural AMD desktop counterpart to the 52 CU Series X GPU, with its 16 GB GDDR6 mirroring the console's total memory (though Series X's 320-bit bus and 560 GB/s bandwidth exceeds the RX 6800's 16 GB @ 512 GB/s). Real-world game benchmarks place the RX 6800 somewhat ahead of Series X, which accounts appropriately for PC overhead.

---

## 5. PlayStation 5

### A. Official Hardware Specs

| Component | Specification |
|---|---|
| SoC | Custom AMD, 7 nm (TSMC) |
| CPU Architecture | x86-64 AMD Ryzen "Zen 2" |
| CPU Cores / Threads | 8 cores / 16 threads |
| CPU Clock | Variable frequency, up to 3.5 GHz |
| GPU Architecture | AMD RDNA 2 (custom, "Oberon") |
| GPU Compute Units | 36 CUs |
| GPU Clock | Variable frequency, up to 2.23 GHz |
| GPU TFLOPS (FP32) | 10.28 TFLOPS (commonly cited as 10.3 TFLOPS) |
| RAM Total | 16 GB GDDR6, 256-bit bus |
| RAM Bandwidth | 448 GB/s |
| RAM for Games | ~12.5 GB (OS reserves ~3.5 GB) |
| Storage | Custom 825 GB PCIe 4.0 NVMe SSD (12-channel, custom controller) |
| Storage I/O | 5.5 GB/s raw; 8--9 GB/s typical compressed |
| RT Support | Hardware ray tracing (RDNA 2 RT units, though repurposed TMUs) |
| ML Upscaler | None at launch (Tempest audio engine is the custom accelerator; no GPU-based ML upscaler until PS5 Pro) |
| Dedicated I/O | Custom Kraken decompression engine (hardware), I/O coprocessors, Flash controller |
| Audio | "Tempest" 3D Audio engine (dedicated hardware) |
| Target | 4K @ 60 FPS with ray tracing in select titles |
| Power Budget | ~200--220 W under gaming load |

Sources: [PlayStation Blog official spec reveal -- March 2020](https://blog.playstation.com/2020/03/18/unveiling-new-details-of-playstation-5-hardware-technical-specs/), [IGN PS5 full specs](https://www.ign.com/articles/ps5-full-specs-revealed), [Digital Foundry PS5 GPU = RX 6700 analysis -- NeoGAF](https://www.neogaf.com/threads/digital-foundry-the-ps5-gpu-in-pc-form-radeon-rx-6700-in-depth-console-equivalent-pc-performance.1667623/)

Notable context: Sony's "variable frequency" design lets the system dynamically redistribute power budget between the CPU and GPU -- if the CPU is lightly loaded, the GPU can sustain closer to its 2.23 GHz peak, and vice versa. The 825 GB SSD was purpose-engineered with a 12-channel flash interface and custom hardware decompression equivalent to the throughput of nine Zen 2 CPU cores working in parallel. This enables near-instant asset streaming and is a significant architectural advantage over a standard PC NVMe setup, even one using PCIe 4.0 storage. Digital Foundry found the PS5 GPU broadly equivalent to the Radeon RX 6700 in real-world multi-game testing.

---

### B. PC Equivalent -- Variant 1 (Intel CPU + NVIDIA GPU)

| Component | Recommendation |
|---|---|
| CPU | Intel Core i7-10700 (8-core, 2.9--4.8 GHz, Comet Lake) |
| GPU | NVIDIA GeForce RTX 2070 Super (8 GB GDDR6) |
| RAM | 16 GB DDR4-3200 |

Justification: The PS5 GPU at 10.28 TFLOPS RDNA 2 maps roughly to the RTX 2070 Super (TFLOPS are not 1:1 across architectures, but in real game benchmarks Digital Foundry placed PS5 close to an RTX 2070 Super or RTX 3060 range). Because RDNA 2 has better raster/compute efficiency than Turing per TFLOP, an Nvidia card needs slightly more raw TFLOPS to match. The RTX 2070 Super also has dedicated RT cores and DLSS capability, making it a functionally richer PC analog. The i7-10700 provides 8 Zen 2-equivalent cores.

---

### C. PC Equivalent -- Variant 2 (Full AMD)

| Component | Recommendation |
|---|---|
| CPU | AMD Ryzen 7 3700X (8-core/16-thread, 3.6--4.4 GHz, Zen 2) |
| GPU | AMD Radeon RX 6700 XT (12 GB GDDR6) |
| RAM | 16 GB DDR4-3600 |

Justification: Digital Foundry tested the PS5 GPU directly against the RX 6700 and found it "often a close match," with the RX 6700 typically pulling 5--15% ahead in multi-game averages. The RX 6700 XT (2560 stream processors, ~13.2 TFLOPS RDNA 2) provides the slight headroom a PC needs. Its 12 GB GDDR6 ensures no VRAM bottleneck (the RX 6700 6 GB was found to be VRAM-constrained in some tests). Ryzen 7 3700X is again the most direct CPU architectural equivalent.

---

## 6. PlayStation 5 Pro (Released November 2024)

### A. Official Hardware Specs

| Component | Specification |
|---|---|
| SoC | Custom AMD, advanced node (TSMC-based) |
| CPU Architecture | x86-64 AMD Ryzen "Zen 2" |
| CPU Cores / Threads | 8 cores / 16 threads |
| CPU Clock | Variable frequency, up to 3.85 GHz (higher than base PS5's 3.5 GHz) |
| GPU Architecture | Custom AMD RDNA 2.x baseline with RDNA 3 and RDNA 4 extensions ("future RDNA" per Mark Cerny) |
| GPU Compute Units | 60 CUs |
| GPU Clock (typical) | ~2.17 GHz typical; up to 2.35 GHz boost |
| GPU TFLOPS (FP32) | 16.7 TFLOPS |
| RT Performance | 2--3x faster than PS5; BVH8 traversal (vs BVH4 on PS5); hardware stack management |
| RAM Total | 16 GB GDDR6 + 2 GB DDR5 |
| RAM Bandwidth | 576 GB/s (GDDR6, 256-bit bus -- 28% faster than PS5) |
| RAM for Games | ~13.7 GB (including 1+ GB DDR5 available to developers) |
| Storage | Custom 2 TB PCIe 4.0 NVMe SSD |
| Storage I/O | 5.5 GB/s raw (same as base PS5) |
| ML Upscaler | PSSR (PlayStation Spectral Super Resolution) -- GPU-based CNN using repurposed WGP vector registers; ~300 INT8 TOPS; ~2 ms per 4K frame |
| Connectivity | Wi-Fi 7, Bluetooth 5.1, HDMI 2.1 |
| Power Budget | ~214--235 W under gaming load (similar to base PS5 per Digital Foundry testing) |

Sources: [Hardware Busters PS5 Pro spec comparison](https://hwbusters.com/gaming/sony-playstation-5-pro-performance-part-analysis-power-consumption-noise/), [TechRadar PS5 Pro specs](https://www.techradar.com/gaming/ps5-pro-specs), [Digital Foundry / Eurogamer PS5 Pro deep dive -- December 2024](https://www.eurogamer.net/digitalfoundry-2024-ps5-pro-deep-dive), [Tom's Hardware PS5 Pro power consumption](https://www.tomshardware.com/video-games/playstation/the-ps5-pro-is-surprisingly-efficient-30-percent-performance-uplift-while-operating-at-nearly-the-same-power-draw-as-the-base-ps5)

Notable context: The PS5 Pro GPU architecture is technically still "RDNA 2" at the shader level (ensuring backward compatibility with all PS5 game shaders, which cannot be recompiled on the fly), but it incorporates significant RT and ML extensions from RDNA 3 and RDNA 4 lineages. Mark Cerny explicitly confirmed this unusual hybrid design was necessary because PS5 shader code is not portable to later RDNA generations. The PSSR upscaler uses repurposed WGP vector registers rather than dedicated NPU hardware, giving it 200 TB/s internal bandwidth but limiting it to approximately 300 INT8 TOPS -- below RDNA 4 desktop capabilities but sufficient for a sub-2ms 4K upscale. A future FSR 4 model adaptation for PS5 Pro titles in 2026 is being developed under the Sony-AMD "Amethyst" collaboration per Digital Foundry reporting. Real-world power draw was surprisingly similar to the base PS5 (~214 W in Elden Ring, ~232 W in Spider-Man 2), suggesting Sony made significant efficiency gains in the GPU design.

---

### B. PC Equivalent -- Variant 1 (Intel CPU + NVIDIA GPU)

| Component | Recommendation |
|---|---|
| CPU | Intel Core i7-10700K (8-core, 3.8--5.1 GHz) |
| GPU | NVIDIA GeForce RTX 3070 (8 GB GDDR6) |
| RAM | 16 GB DDR4-3600 |

Justification: This is the most nuanced equivalency in the document. Raw raster performance of the PS5 Pro's 60 RDNA 2.x CUs (~16.7 TFLOPS) places it between an RX 6800 and RX 6800 XT on paper. Digital Foundry's Richard Leadbetter stated the RTX 4070 would be "the closest equivalent GPU" because the RTX 4070 adds DLSS 3 (matching PSSR upscaling quality), significantly better RT performance, and similar raster throughput when accounting for the Pro's RDNA 2-heritage efficiency at its clock speeds. However, independent testing by Jacob Terkelsen found the RTX 3070 and RX 6800 to be the most accurate matches in rasterization gaming workloads when PS5 Pro settings are properly replicated. The RTX 3070 is the Nvidia equivalent that best balances raster throughput parity with RT and DLSS capability (PSSR analog), without the 4070's significant cost premium and 40% raster gap. For users also prioritizing DLSS 3 Frame Generation, an RTX 4070 is the natural step up.

---

### C. PC Equivalent -- Variant 2 (Full AMD)

| Component | Recommendation |
|---|---|
| CPU | AMD Ryzen 7 3700X (8-core/16-thread, Zen 2, 3.6--4.4 GHz) |
| GPU | AMD Radeon RX 6800 (16 GB GDDR6) |
| RAM | 16 GB DDR4-3600 |

Justification: The RX 6800 (60 CUs, RDNA 2, ~16.2 TFLOPS) is the nearest AMD desktop match to the PS5 Pro GPU in raw CU count and architecture. Testing confirms it trades blows with the Pro in rasterization, with the Pro holding occasional advantages from PSSR and its custom RT hardware. The RX 6800's 16 GB GDDR6 provides headroom the Pro's ~13.7 GB pool lacks. The caveat is that no AMD RDNA 2 or RDNA 3 desktop GPU offers a neural ML upscaler comparable to PSSR or DLSS -- FSR 2/3 are shader-based and generally inferior in image quality at similar performance costs. For full feature parity including ML upscaling, an RX 7800 XT (RDNA 3, 2048 SPs, ~25 TFLOPS raster) overcompensates on raster but still lacks dedicated Tensor-equivalent hardware. The RX 6800 is the correct raw-raster analog; accept the PSSR gap as a known limitation.

---

## Summary Table

| Console | TFLOPS (FP32) | RAM | Intel+NVIDIA PC Equiv (CPU / GPU) | AMD PC Equiv (CPU / GPU) |
|---|---|---|---|---|
| Nintendo Switch (2017) | ~0.39 T (docked) | 4 GB LPDDR4 | i3-6100 / GT 1030 | Ryzen 3 1200 / RX 460 |
| Nintendo Switch 2 (2025) | 3.07 T (docked) / 1.71 T (handheld) | 12 GB LPDDR5X | i5-11400 / RTX 2060 | Ryzen 5 5600 / RX 6600 |
| Xbox Series S | 4.0 T | 10 GB GDDR6 | i5-10400 / GTX 1660 Super | Ryzen 5 3600 / RX 6600 XT |
| Xbox Series X | 12.0 T | 16 GB GDDR6 | i7-10700K / RTX 3070 | Ryzen 7 3700X / RX 6800 |
| PlayStation 5 | 10.28 T | 16 GB GDDR6 | i7-10700 / RTX 2070 Super | Ryzen 7 3700X / RX 6700 XT |
| PlayStation 5 Pro | 16.7 T | 16 GB GDDR6 + 2 GB DDR5 | i7-10700K / RTX 3070 (or RTX 4070 for DLSS/RT parity) | Ryzen 7 3700X / RX 6800 |

---

## Caveats and Console-Specific Advantages

### Unified Memory Architecture
All consoles use a single pool of high-bandwidth memory shared between the CPU and GPU. On a PC, VRAM and system RAM are separate, requiring costly PCIe bandwidth transfers when the GPU needs data from system RAM. Console games are written to exploit direct GPU access to all memory, enabling texture streaming patterns that are architecturally impractical on current desktop PC designs.

### Fixed-Function Hardware: Console-Specific Blocks

**PlayStation 5 -- Custom I/O and Kraken Decompression:**
The PS5's SSD controller is built into the SoC alongside dedicated Kraken hardware decompression units and flash management coprocessors. Raw throughput is 5.5 GB/s (uncompressed) / 8--9 GB/s (Kraken compressed), equivalent to the throughput of nine Zen 2 CPU cores. No PC NVMe drive, even PCIe 5.0, replicates this because the PS5's pipeline routes data directly to GPU memory bypassing DRAM entirely. ([PlayStation Blog](https://blog.playstation.com/2020/03/18/unveiling-new-details-of-playstation-5-hardware-technical-specs/))

**Xbox Series X/S -- Sampler Feedback Streaming (SFS) and Velocity Architecture:**
Microsoft's Xbox Velocity Architecture combines the PCIe 4.0 NVMe SSD with Sampler Feedback Streaming, a hardware feature that allows the GPU to request only the mip-map tiles it is actually sampling, rather than loading entire texture sets. This dramatically reduces GPU memory pressure and effective VRAM requirements. SFS is partially exposed on PC via DirectStorage and Tier 2 Mesh Shader pipelines, but console implementations are more tightly integrated. ([Xbox Wire -- original announcement](https://news.xbox.com/en-us/2020/03/16/xbox-series-x-full-specs/))

**PlayStation 5 Pro -- PSSR (PlayStation Spectral Super Resolution):**
PSSR is an ML-based temporal upscaler implemented in hardware-repurposed WGP vector registers (~200 TB/s internal bandwidth). Unlike FSR which runs as a shader on the GPU's general-purpose units, PSSR's implementation was architecturally integrated to minimize per-frame latency (target ~2 ms for 4K output). It is the PS5 Pro's equivalent of DLSS 2/3 and is exclusive to the PS5 Pro. ([Digital Foundry / Eurogamer PS5 Pro deep dive](https://www.eurogamer.net/digitalfoundry-2024-ps5-pro-deep-dive))

**Nintendo Switch 2 -- DLSS and Hardware File Decompression:**
The T239's Ampere Tensor cores enable genuine DLSS inference (not a shader approximation), providing significant image quality advantages over a 561 MHz handheld GPU's native render output. DLSS 1x/2x/3x and DLAA are all SDK-supported. Additionally, a dedicated file decompression engine accelerates LZ4 unpacking for game packages, reducing load times without burdening either the CPU or GPU. ([Digital Foundry / Eurogamer Switch 2 specs](https://www.eurogamer.net/digitalfoundry-2025-nintendo-switch-2-final-tech-specs-and-system-reservations-confirmed))

### Ray Tracing Hardware Generations

| Console | RT Hardware |
|---|---|
| Switch 2 | Ampere 2nd-gen RT cores (dedicated BVH traversal, same as RTX 30 series) |
| Xbox Series S/X | RDNA 2 RT units (TMU-repurposed BVH4, similar to RX 6000 series) |
| PS5 | RDNA 2 RT (BVH4, TMU-based intersection) |
| PS5 Pro | Enhanced RDNA 2.x with RDNA 3/4 extensions: BVH8, hardware stack management, 2--3x faster than PS5; comparable to RDNA 4 RT capability per Digital Foundry analysis |

### Driver and OS Overhead
Windows, WDDM GPU drivers, background processes, and DirectX/Vulkan translation layers add measurable CPU and GPU overhead compared to a console's bare-metal GNM (PS5) or DirectX 12 Ultimate (Xbox) implementation. This is the primary reason PC "equivalents" are recommended at a higher spec tier than raw TFLOP parity would suggest -- benchmarks consistently show a 15--35% performance gap between console-equivalent settings on PC and native console execution, depending on the game and optimization quality.

### API Efficiency
PS5 uses Sony's proprietary GNM/GNMX graphics API -- closer in design to Vulkan than DirectX, with near-zero overhead draw calls and explicit GPU scheduling. Xbox uses DirectX 12 Ultimate with proprietary extensions. Both are significantly lower overhead than any broadly-targeted PC API, including Vulkan, which must generalize across thousands of hardware configurations.

---

Sources consulted: [PlayStation Blog PS5 spec reveal](https://blog.playstation.com/2020/03/18/unveiling-new-details-of-playstation-5-hardware-technical-specs/), [Xbox.com Series X specs](https://www.xbox.com/en-US/consoles/xbox-series-x), [Xbox.com Series S specs](https://www.xbox.com/en-US/consoles/xbox-series-s), [Digital Foundry / Eurogamer Switch 2 confirmed specs](https://www.eurogamer.net/digitalfoundry-2025-nintendo-switch-2-final-tech-specs-and-system-reservations-confirmed), [Digital Foundry / Eurogamer PS5 Pro deep dive](https://www.eurogamer.net/digitalfoundry-2024-ps5-pro-deep-dive), [Digital Foundry YouTube Switch 2 specs](https://www.youtube.com/watch?v=huxDoYXS8Ng), [Hardware Busters PS5 Pro analysis](https://hwbusters.com/gaming/sony-playstation-5-pro-performance-part-analysis-power-consumption-noise/), [Tom's Hardware PS5 Pro power consumption](https://www.tomshardware.com/video-games/playstation/the-ps5-pro-is-surprisingly-efficient-30-percent-performance-uplift-while-operating-at-nearly-the-same-power-draw-as-the-base-ps5), [SwitchBrew Tegra X1 wiki](https://switchbrew.org/wiki/Tegra_X1), [Chips and Cheese Maxwell GPU analysis](https://chipsandcheese.com/p/nintendo-switchs-igpu-maxwell-nerfed-edition)*
