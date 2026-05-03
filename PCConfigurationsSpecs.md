# Steam Hardware Survey — PC Tier Configurations & Game Dev Targets

**Source:** [Steam Hardware & Software Survey April 2026](https://store.steampowered.com/hwsurvey/Steam-Hardware-Software-Survey-Welcome-to-Steam)

---

## Table of Contents

- [Steam Hardware Survey Ś PC Tier Configurations & Game Dev Targets](#steam-hardware-survey-pc-tier-configurations-game-dev-targets)
  - [1. Survey Data Summary](#1-survey-data-summary)
    - [1.1 GPU Distribution (Top Models, April 2026)](#11-gpu-distribution-top-models-april-2026)
    - [1.2 System RAM](#12-system-ram)
    - [1.3 CPU](#13-cpu)
    - [1.4 Primary Display Resolution](#14-primary-display-resolution)
    - [1.5 Operating System](#15-operating-system)
    - [1.6 Storage](#16-storage)
  - [2. Three-Tier PC Configuration Model](#2-three-tier-pc-configuration-model)
    - [Tier Definitions at a Glance](#tier-definitions-at-a-glance)
    - [2.1 Low Tier Ś Bottom ~25% of Steam Users](#21-low-tier-bottom-25-of-steam-users)
    - [2.2 Mid Tier Ś Median ~40ľ50% of Steam Users](#22-mid-tier-median-4050-of-steam-users)
    - [2.3 High Tier Ś Top ~10ľ15% of Steam Users](#23-high-tier-top-1015-of-steam-users)
  - [3. Tier Î Game Type Performance Matrix](#3-tier-game-type-performance-matrix)
    - [3.1 Indie Game (Stylized, Low-Poly or 2D/3D Hybrid)](#31-indie-game-stylized-low-poly-or-2d3d-hybrid)
    - [3.2 AA Game (Moderate Scope, Lumen Software RT Optional)](#32-aa-game-moderate-scope-lumen-software-rt-optional)
    - [3.3 Demanding AAA Game (Full Nanite + Hardware Lumen + VSM + VFX)](#33-demanding-aaa-game-full-nanite-hardware-lumen-vsm-vfx)
  - [4. Minimum / Recommended / High Spec System Requirements](#4-minimum-recommended-high-spec-system-requirements)
    - [4.1 Indie / Small Scope Game](#41-indie-small-scope-game)
    - [4.2 AA Game (Software Lumen + Partial Nanite)](#42-aa-game-software-lumen-partial-nanite)
    - [4.3 Demanding AAA (Full Nanite + HW Lumen + VSM)](#43-demanding-aaa-full-nanite-hw-lumen-vsm)
  - [5. UE5-Specific Notes for Developers](#5-ue5-specific-notes-for-developers)
    - [5.1 Nanite Requirements](#51-nanite-requirements)
    - [5.2 Hardware Lumen Requirements](#52-hardware-lumen-requirements)
    - [5.3 Virtual Shadow Maps (VSM) and VRAM](#53-virtual-shadow-maps-vsm-and-vram)
    - [5.4 DirectX 12 and Shader Model Summary](#54-directx-12-and-shader-model-summary)
    - [5.5 TSR (Temporal Super Resolution) Recommendations](#55-tsr-temporal-super-resolution-recommendations)
  - [6. Summary Table: What to Write in Steam Store Requirements](#6-summary-table-what-to-write-in-steam-store-requirements)
    - [Indie / Small Scope](#indie-small-scope)
    - [AA (Lumen Software + Partial Nanite)](#aa-lumen-software-partial-nanite)
    - [Demanding AAA (HW Lumen + Nanite + VSM)](#demanding-aaa-hw-lumen-nanite-vsm)
  - [7. Key Takeaways](#7-key-takeaways)

---

## 1. Survey Data Summary

### 1.1 GPU Distribution (Top Models, April 2026)

The following table lists the top discrete GPU models by share. The survey does not aggregate by GPU family tier — each SKU is listed individually. Percentages are of all surveyed Steam users (Windows, macOS, Linux combined).

| Rank | GPU | Share | Notes |
|------|-----|-------|-------|
| 1 | NVIDIA GeForce RTX 3060 | 3.99% | Consistently #1 for most of 2025–2026 |
| 2 | NVIDIA GeForce RTX 4060 | 3.86% | Desktop Ada mid-range |
| 3 | NVIDIA GeForce RTX 4060 Laptop GPU | 3.78% | Mobile variant |
| 4 | NVIDIA GeForce RTX 3050 | 3.04% | Budget Ampere |
| 5 | NVIDIA GeForce RTX 5070 | 2.86% | Blackwell flagship mid |
| 6 | NVIDIA GeForce RTX 5060 | 2.57% | New Blackwell entry-mid |
| 7 | NVIDIA GeForce GTX 1650 | 2.58% | Legacy budget |
| 8 | NVIDIA GeForce RTX 3070 | 2.10% | Ampere upper-mid |
| 9 | AMD Radeon (TM) Graphics (iGPU catch-all) | 2.27% | Includes RDNA 2/3 iGPU |
| 10 | NVIDIA GeForce RTX 4060 Ti | 2.45% | Ada upper-mid |
| 11 | NVIDIA GeForce RTX 5060 Ti | 1.81% | Blackwell upper-entry |
| 12 | NVIDIA GeForce RTX 3060 Laptop GPU | 1.87% | Mobile Ampere |
| 13 | NVIDIA GeForce RTX 4070 | 1.79% | Ada high-mid |
| 14 | Intel Iris Xe Graphics | 1.69% | Integrated |
| 15 | NVIDIA GeForce RTX 2060 | 1.76% | Turing budget |
| 16 | NVIDIA GeForce GTX 1060 | 1.61% | Legacy DX11-era |
| 17 | NVIDIA GeForce RTX 5060 Laptop GPU | 1.61% | New mobile entry |
| 18 | NVIDIA GeForce RTX 4050 Laptop GPU | 1.56% | Ada mobile entry |
| 19 | NVIDIA GeForce RTX 5070 Ti | 1.62% | Blackwell upper |
| 20 | NVIDIA GeForce GTX 1660 SUPER | 1.46% | Turing budget |
| -- | NVIDIA GeForce RTX 4070 SUPER | 1.51% | Ada high |
| -- | AMD Radeon RX 7800 XT | 1.22% | RDNA 3 high-mid |
| -- | NVIDIA GeForce RTX 3080 | 1.45% | Ampere high |
| -- | NVIDIA GeForce RTX 4090 | 0.74% | Flagship |
| -- | NVIDIA GeForce RTX 5080 | 1.37% | Blackwell high |
| -- | AMD Radeon RX 9070 | 0.17% | RDNA 4, newly visible |

**VRAM distribution:**

| VRAM | Share | Change |
|------|-------|--------|
| 4 GB or less | ~16.6% | Declining |
| 6 GB | 6.35% | -0.44% |
| 8 GB | 26.76% | -0.76% |
| 12 GB | 13.45% | -0.25% |
| 16 GB | 23.51% | +1.98% |
| 20 GB | 1.25% | +0.06% |
| 24 GB | 5.03% | +0.19% |
| Other/legacy | ~7.1% | Declining |

8 GB remains the single most common VRAM tier at 26.76%, followed closely by 16 GB at 23.51%. The 16 GB bucket is rising fast, driven by RTX 50-series cards shipping with 16 GB as standard at the mid-range. 12 GB (RTX 3060/4070 class) accounts for another 13.45%. The combined 12 GB + 16 GB share now exceeds 8 GB and will overtake it within 2026 at current trend rates, according to [The FPS Review's April 2026 analysis](https://www.thefpsreview.com/2026/05/02/trends-from-the-april-2026-steam-hardware-survey/).

### 1.2 System RAM

| Amount | Share |
|--------|-------|
| 8 GB | 7.66% |
| 12 GB | 2.46% |
| 16 GB | 40.86% (most common) |
| 24 GB | 1.97% |
| 32 GB | 37.55% |
| 48 GB | 1.20% |
| 64 GB | 4.10% |

16 GB is the single most common configuration at 40.86%, having surpassed 32 GB in March 2026. 32 GB is at 37.55% and trending up. The two together cover ~78% of the Steam user base.

### 1.3 CPU

**Manufacturer split (Windows):**

| Vendor | Share |
|--------|-------|
| Intel | ~57% |
| AMD | ~43% |

AMD has gained approximately 7 percentage points over the prior 18 months, per [TweakTown's September 2025 coverage](https://www.tweaktown.com/news/108073/steam-data-shows-pc-gamers-are-choosing-amd-cpus-over-intel/index.html). Intel holds a slim majority but the gap continues to narrow.

**CPU core counts (Windows, most common):**

| Logical Cores | Share |
|---------------|-------|
| 6 cores | 28.62% (most common) |
| 8 cores | 26.95% |
| 10 cores | 7.60% |
| 4 cores | 13.02% |
| 12 cores | 5.10% |
| 14 cores | 4.93% |
| 16 cores | 5.51% |

6-core and 8-core CPUs together represent over 55% of Steam users. 4-core is at 13% and declining. The 10-core and 14-core entries reflect Intel's hybrid (P+E core) architecture (e.g., Core i5-13400F = 6P+4E = 10 logical, Core i7-13700 = 8P+8E = 16 logical reported as logical cores).

**Intel CPU base clock distribution (Windows):**
Most common band is 2.3–2.69 GHz (20.73%), which maps to Intel's hybrid cores where P-core base clocks often sit at 2.5 GHz with boost to 4.6+ GHz (e.g., i5-13400F). The 3.3–3.69 GHz band (12.27%) covers older all-core desktop chips. AMD's most common band is 3.7 GHz and above (roughly 28%), consistent with Ryzen 5/7 desktop processors (e.g., Ryzen 5 5600X base 3.7 GHz, Ryzen 5 7600 base 3.8 GHz).

**Note:** The Steam survey does not identify specific CPU models — only vendor, base clock band, and core count. The CPU examples below are derived from cross-referencing core counts and clock bands with current market SKUs.

### 1.4 Primary Display Resolution

| Resolution | Share |
|------------|-------|
| 1920x1080 (1080p) | 52.21% |
| 2560x1440 (1440p) | 21.41% |
| 2560x1600 | 4.87% |
| 3840x2160 (4K) | 5.09% |
| 3440x1440 (ultrawide) | 3.14% |
| 1366x768 | 2.31% |
| 1920x1200 | 2.36% |

1080p remains the dominant resolution at 52.21%. 1440p is the second most common at 21.41% and growing (+0.71% month-over-month). 4K sits at 5.09% (+0.30% MoM). The 2560x1600 bucket at 4.87% is predominantly MacBook and laptop panels — not a PC gaming monitor target.

### 1.5 Operating System

| OS | Share |
|----|-------|
| Windows 11 64-bit | 67.74% |
| windows 11 64-bit | 25.63% |
| All Windows | 93.47% |
| macOS | 2.01% |
| Linux | ~4.5% |

Windows 11 is now the clear majority OS. DirectX 12 GPUs account for 91.89% of the Steam user base per [the April 2026 video card detail page](https://store.steampowered.com/hwsurvey/videocard/).

### 1.6 Storage

The Steam survey does not track storage type (SSD vs HDD) or capacity by speed class directly — only total storage size buckets are surveyed. Storage notes below are based on market trends and developer assumptions, not survey data.

---

## 2. Three-Tier PC Configuration Model

The tiers below are derived from cumulative survey share. "Low tier" approximates the bottom ~25% of the performance distribution, "mid tier" approximates the median ~40–50%, and "high tier" the top ~10–15%.

### Tier Definitions at a Glance

| | Low Tier | Mid Tier | High Tier |
|---|---|---|---|
| Approx. Steam population | Bottom ~25% | Middle ~45% | Top ~15% |
| GPU (NVIDIA example) | RTX 3050 / GTX 1650 | RTX 3060 / RTX 4060 | RTX 4070 Super / 4080 / 5070 |
| GPU (AMD example) | RX 6600 | RX 6700 XT / RX 7600 XT | RX 7800 XT / RX 7900 XTX |
| VRAM | 4–8 GB | 8–12 GB | 12–16 GB+ |
| RAM | 8–16 GB | 16 GB | 32 GB |
| CPU (Intel) | Core i5-10400F / i5-12400F | Core i5-13400F | Core i7-13700K / i7-14700F |
| CPU (AMD) | Ryzen 5 3600 / 5500 | Ryzen 5 5600X / 7600 | Ryzen 7 7700X / 7800X3D |
| CPU cores | 6-core (some 4-core) | 6–8 core | 8–16 core |
| Primary resolution | 1080p | 1080p–1440p | 1440p–4K |
| Target refresh | 60 FPS | 60–120 FPS | 60–144 FPS |
| OS | windows 11/11 | Windows 11 | Windows 11 |
| Storage | HDD likely present; SSD common | SSD standard (SATA or NVMe) | NVMe SSD assumed |
| DX12 support | Yes (SM6 on RTX; SM5 fallback on GTX) | Yes (SM6) | Yes (SM6 + HW RT) |

---

### 2.1 Low Tier — Bottom ~25% of Steam Users

This tier captures users with GPUs in the GTX 1650 / RTX 3050 range, or integrated graphics. GPU share contributors: GTX 1650 (2.58%), RTX 3050 (3.04%), GTX 1060 (1.61%), GTX 1660 SUPER (1.46%), integrated iGPUs (~5% combined). Combined with older Pascal/Turing budget cards, this segment represents roughly the bottom quarter of discrete GPU performance.

**Representative Configuration:**

| Component | Spec | Notes |
|-----------|------|-------|
| CPU (Intel) | Core i5-10400F or Core i5-12400F | 6C/12T, 2.9–4.4 GHz boost; very common 10th/12th gen pairing |
| CPU (AMD) | Ryzen 5 3600 or Ryzen 5 5500 | 6C/12T, 3.6–4.4 GHz boost |
| GPU (NVIDIA) | RTX 3050 (8 GB) or GTX 1650 (4 GB) | 3050 = 8 GB VRAM, SM6, DX12; 1650 = 4 GB, SM6, DX12 |
| GPU (AMD) | RX 6600 (8 GB) | RDNA 2, 8 GB, DX12 SM6, HW RT capable |
| VRAM | 4–8 GB | 4 GB on GTX 1650; 8 GB on RTX 3050 and RX 6600 |
| System RAM | 8–16 GB | ~8% of Steam users at 8 GB; 16 GB target |
| Storage | SATA SSD (250–500 GB) or HDD | Survey does not report storage type; HDD still present at this tier |
| Resolution | 1920x1080 | 1080p exclusively |
| Refresh target | 60 FPS | High refresh rate uncommon at this tier |
| OS | windows 11 or 11 | windows 11 still significant at lower tiers |
| DirectX | DX12 (SM6 on RTX/RX; SM5 fallback on GTX 1650) | GTX 1650 is DX12 but lacks HW RT |

**Tier Notes:**
- GTX 1650 has no hardware ray tracing. Nanite requires DX12 with SM6 and 64-bit integer atomics (Feature Level 12_1); the GTX 1650 supports DX12 Feature Level 12_0 but not 12_1. This means Nanite and VSM in default UE5 configurations will not run on GTX 1650. Games using UE5's DX11/SM5 fallback path can still run on this GPU, but with heavy restrictions.
- RTX 3050 (8 GB) and RX 6600 support Nanite + VSM (DX12 SM6) but are slow in compute-heavy passes.
- Hardware Lumen requires hardware ray tracing: RTX 20xx or later, RX 6000 or later. GTX 1650 cannot run Hardware Lumen. Software Lumen (screen-space + SDF) is supported on DX12 SM5 hardware.

---

### 2.2 Mid Tier — Median ~40–50% of Steam Users

The RTX 3060 at 3.99% is the single most popular discrete GPU on Steam, a position it has held consistently throughout 2025–2026. The RTX 4060 desktop at 3.86% is a close second. Combined with 4060 Ti, 3060 Ti, 3070, RTX 5060, and AMD's RX 7600 XT / RX 6700 XT, this band represents the performance median. Most mid-tier users have 16 GB RAM and run at 1080p or 1440p.

**Representative Configuration:**

| Component | Spec | Notes |
|-----------|------|-------|
| CPU (Intel) | Core i5-13400F | 6P+4E = 10 logical cores, 2.5 GHz base / 4.6 GHz boost; dominant in prebuilts |
| CPU (AMD) | Ryzen 5 5600X or Ryzen 5 7600 | 6C/12T; 5600X at 3.7 GHz base, 7600 at 3.8 GHz base |
| GPU (NVIDIA) | RTX 3060 (12 GB) or RTX 4060 (8 GB) | Both DX12 SM6 + HW RT. 3060 has more VRAM; 4060 has better perf/W |
| GPU (AMD) | RX 7600 XT (16 GB) or RX 6700 XT (12 GB) | RDNA 2/3; HW RT capable; strong rasterization |
| VRAM | 8–12 GB | RTX 3060 = 12 GB; RTX 4060 = 8 GB; RX 7600 XT = 16 GB |
| System RAM | 16 GB | 40.86% of Steam users — single largest RAM configuration |
| Storage | NVMe SSD (500 GB–1 TB) | Expected at this price point; no survey confirmation |
| Resolution | 1920x1080 or 2560x1440 | Most at 1080p; growing 1440p adoption |
| Refresh target | 60–120 FPS at 1080p | Depends on game type |
| OS | Windows 11 | Dominant at this tier |
| DirectX | DX12 SM6 + Hardware RT | All RTX 2x+ and RX 6000+ support HW RT |

**Tier Notes:**
- RTX 3060 12 GB is notable for its VRAM headroom — more than the RTX 4060 8 GB despite being an older card. For VRAM-heavy workloads (VSM, high-res textures), the RTX 3060 may outperform the RTX 4060 in practice.
- RX 7600 XT 16 GB is an outlier for VRAM capacity at this price tier. It represents a growing VRAM trend confirmed by the 16 GB VRAM bucket rising to 23.51% in April 2026.
- Hardware Lumen and Nanite are fully supported at this tier on all listed GPUs.
- DLSS 3 (Frame Generation) available on RTX 4060; FSR 3 Frame Generation on RX 7600 XT.

---

### 2.3 High Tier — Top ~10–15% of Steam Users

This tier aggregates users with RTX 4070 (1.79%), RTX 4070 Super (1.51%), RTX 4070 Ti / Ti Super (~1.75% combined), RTX 4080/4080S (~1.32%), RTX 4090 (0.74%), RTX 5070 (2.86%), RTX 5070 Ti (1.62%), RTX 5080 (1.37%), AMD RX 7800 XT (1.22%), and RX 7900 XTX (0.48%). Combined this represents roughly 15–16% of the surveyed Steam population. Most of these users are at 1440p or 4K, with 32 GB RAM.

**Representative Configuration:**

| Component | Spec | Notes |
|-----------|------|-------|
| CPU (Intel) | Core i7-13700K or Core i7-14700F | 8P+8E/16P = 16–24 logical cores; strong IPC for game workloads |
| CPU (AMD) | Ryzen 7 7700X or Ryzen 7 7800X3D | 8C/16T; 7800X3D = best gaming CPU in class due to 3D V-Cache |
| GPU (NVIDIA) | RTX 4070 Super (12 GB) or RTX 5070 (12 GB) | Ada/Blackwell; DLSS 3; full HW RT support; Blackwell improves shader throughput |
| GPU (NVIDIA high-end) | RTX 4080 (16 GB) / RTX 5080 (16 GB) | 4K capable; 16 GB VRAM |
| GPU (AMD) | RX 7800 XT (16 GB) or RX 7900 XTX (24 GB) | RDNA 3; FSR 3; strong rasterization; HW RT decent |
| VRAM | 12–16 GB (24 GB at very high end) | 16 GB is the new standard at this tier |
| System RAM | 32 GB | 37.55% of Steam users; expected at this tier |
| Storage | NVMe Gen4 SSD (1–2 TB) | Expected; no survey confirmation |
| Resolution | 2560x1440 or 3840x2160 | 1440p at 21.41%; 4K at 5.09% of all Steam users |
| Refresh target | 60–144 FPS | 144 Hz common at 1440p; 60 FPS with quality settings at 4K |
| OS | Windows 11 | Universal at this tier |
| DirectX | DX12 SM6 + Hardware RT | All listed GPUs fully support |

**Tier Notes:**
- RTX 5070 (12 GB) uses Blackwell architecture with improved shader performance and DLSS 4 with Multi Frame Generation (up to 4x frames). Despite "only" 12 GB VRAM vs. the RTX 4070 Super's 12 GB, raw performance is meaningfully higher.
- RTX 4090 (24 GB) at 0.74% share represents the top 1% performance tier. Included in calculations but not modeled separately.
- Ryzen 7 7800X3D is the dominant gaming CPU choice among performance users due to its L3 cache advantage in CPU-bound scenarios, per general market evidence.

---

## 3. Tier × Game Type Performance Matrix

Three game categories are modeled:

- **Indie** — stylized visuals, traditional rendering (no Nanite/Lumen required), tight CPU draw call budgets, target 60+ FPS native
- **AA** — moderate scope, optional Lumen Software RT, partial Nanite, target 60 FPS native or with TSR upscaling
- **Demanding AAA** — full Nanite + Hardware Lumen + Virtual Shadow Maps (VSM) + advanced VFX, DLSS/FSR upscaling expected, target 30–60 FPS

### 3.1 Indie Game (Stylized, Low-Poly or 2D/3D Hybrid)

*Examples: Hollow Knight Silksong, Celeste, A Short Hike, Stardew Valley genre, or low-budget UE5 games using deferred + baked lighting only.*

| Tier | Settings | Resolution | FPS Target | Experience | Notes |
|------|----------|------------|-----------|------------|-------|
| Low | Medium–High | 1080p native | 60–120 FPS | Excellent | CPU/GPU load is low; even iGPU can run most titles. No Nanite/Lumen needed. GTX 1650 fully capable. |
| Mid | Ultra | 1080p–1440p native | 120+ FPS | Excellent | Effectively unconstrained. The bottleneck is game quality, not hardware. |
| High | Ultra + high refresh | 1440p–4K native | 144+ FPS | Excellent | Overkill hardware for the game type. CPU frame pacing is the only concern. |

**Scalability for Indie:**
- No DLSS/FSR needed; all tiers can run native
- If UE5: disable Nanite, use static lighting (baked), disable Lumen — all on by default in UE5 but must be opted out
- Target GTX 1060 / RX 580 as your floor (these GPUs still appear at ~2.1% combined share)

---

### 3.2 AA Game (Moderate Scope, Lumen Software RT Optional)

*Examples: Lies of P, Hi-Fi Rush, The Outer Worlds 2, medium-budget UE5 games with Lumen Software RT + partial Nanite on hero assets.*

| Tier | Settings | Resolution | FPS Target | Experience | Notes |
|------|----------|------------|-----------|------------|-------|
| Low | Low–Medium, Lumen off | 1080p native | 30–60 FPS | Acceptable | GTX 1650 requires Lumen disabled + Nanite disabled (no SM6.6 support). RTX 3050 / RX 6600 can run Software Lumen at Medium. Expect 40–55 FPS at 1080p on quality-balanced presets. |
| Mid | Medium–High, Software Lumen on | 1080p (native) or 1440p (TSR 67%) | 60 FPS | Good | RTX 3060 at 1080p High = ~65–75 FPS with Software Lumen. RTX 4060 gains ~15% on top via better shader throughput. TSR at 66% quality enables 1440p output. |
| High | High–Ultra, Lumen (HW or SW) | 1440p native or 4K TSR | 60–100 FPS | Excellent | RTX 4070 Super at 1440p ultra = ~90–110 FPS with Hardware Lumen. RX 7800 XT strong here. DLSS Quality or FSR Quality for 4K. |

**Scalability recommendations:**
- Ship with three presets: Low (no Lumen, baked GI fallback), Medium (Software Lumen, VSM medium), High (full path)
- TSR is strongly recommended over TAAU — TSR at "Balanced" (~67% of native) is near-indistinguishable from native at 1440p
- DLSS Quality mode should be enabled as default for RTX 20xx and above users

---

### 3.3 Demanding AAA Game (Full Nanite + Hardware Lumen + VSM + VFX)

*Examples: Black Myth: Wukong, Alan Wake 2, Senua's Saga: Hellblade II, Avowed, or your AAA UE5 production with no rendering shortcuts.*

| Tier | Settings | Resolution | FPS Target | Experience | Notes |
|------|----------|------------|-----------|------------|-------|
| Low | Low–Medium, HW Lumen off, VSM medium, upscaling | 1080p + FSR/DLSS Performance | 30–45 FPS | Marginal | RTX 3050 / RX 6600 can technically run Nanite (DX12 SM6), but VSM is compute-heavy and VRAM pressure at 8 GB is real. Expect frequent hitching on 4 GB GPUs. GTX 1650 is effectively excluded from this game type without a DX11 fallback. Need FSR Performance (2x upscale) to reach playable FPS. 30 FPS floor may require further cuts. |
| Mid | Medium, HW Lumen on (RTX), SW Lumen on (AMD), DLSS/FSR Quality | 1080p native or 1440p + DLSS Balanced | 45–60 FPS | Good | RTX 3060 12 GB: strong VRAM headroom; DLSS at Quality renders ~720p internally → 1080p output. Hardware Lumen + Nanite at Medium. Target 60 FPS achieved at 1080p with DLSS Quality on most scenes. RTX 4060 8 GB: faster shader execution but 8 GB VRAM can become a constraint with 4K textures; keep texture pool low. |
| High | High–Ultra, HW Lumen, VSM high, DLSS/FSR Quality | 1440p (native or DLSS Quality from 960p) or 4K + DLSS Balanced | 60–90 FPS | Excellent | RTX 4070 Super at 1440p with DLSS Quality = 75–90 FPS typical. RTX 5070 adds ~25–30% perf gain + Multi Frame Generation. RX 7800 XT 16 GB: excellent VRAM headroom, FSR 3 Frame Gen. RTX 4090 at 4K Ultra DLSS Quality = 80–120 FPS on demanding titles. |

**Scalability recommendations:**
- Must ship FSR 3 (free, no NVIDIA license needed) as baseline upscaling for all GPUs
- DLSS 3 (or DLSS 4 on RTX 50 series) for NVIDIA users — reduces GPU compute burden significantly
- Low preset must disable Hardware Lumen (fall back to Software Lumen or baked GI), reduce VSM cascade resolution, cut Nanite fallback mesh detail
- For VSM: set `r.Shadow.Virtual.MaxPhysicalPages` lower on Low/Medium presets; it is the single biggest VRAM drain in VSM
- Frame Generation (DLSS 3 / FSR 3) should be offered as opt-in — it reduces latency perception at lower FPS but is not a substitute for base framerate optimization

---

## 4. Minimum / Recommended / High Spec System Requirements

These targets represent what you should publish on your Steam store page system requirements section.

### 4.1 Indie / Small Scope Game

| | Min Spec | Recommended Spec |
|-|----------|-----------------|
| OS | windows 11 64-bit | Windows 11 64-bit |
| CPU | Intel Core i5-8400 / AMD Ryzen 5 2600 (6-core, 2.8+ GHz) | Intel Core i5-12400F / AMD Ryzen 5 5600 |
| RAM | 8 GB | 16 GB |
| GPU | NVIDIA GeForce GTX 1060 6 GB / AMD RX 580 8 GB | NVIDIA GeForce RTX 3060 / AMD RX 6600 8 GB |
| VRAM | 4 GB | 8 GB |
| Storage | 10–20 GB HDD or SSD | SSD recommended |
| DirectX | DirectX 11 | DirectX 12 |
| Target FPS | 60 FPS @ 1080p Low | 60 FPS @ 1080p High / 1440p Medium |

**Notes:** If your game uses no Nanite/Lumen/VSM, GTX 1060 and RX 580 are safe minimum targets. These GPUs account for roughly 2% of Steam users combined but define the long tail. Do not use UE5 defaults (Nanite on, Lumen on, VSM on) in your packaged build without explicit quality tier gating.

---

### 4.2 AA Game (Software Lumen + Partial Nanite)

| | Min Spec | Recommended Spec | High Spec |
|-|----------|-----------------|-----------|
| OS | windows 11 64-bit | Windows 11 64-bit | Windows 11 64-bit |
| CPU | Intel Core i5-10600K / AMD Ryzen 5 3600 (6-core, 3.3+ GHz) | Intel Core i5-13400F / AMD Ryzen 5 5600X | Intel Core i7-13700K / AMD Ryzen 7 7700X |
| RAM | 12 GB | 16 GB | 32 GB |
| GPU | NVIDIA GeForce RTX 2060 / AMD RX 6600 | NVIDIA GeForce RTX 3060 12 GB / AMD RX 6700 XT | NVIDIA GeForce RTX 4070 Super / AMD RX 7800 XT |
| VRAM | 8 GB | 8–12 GB | 12–16 GB |
| Storage | 30–50 GB SSD | SSD (NVMe preferred) | NVMe SSD |
| DirectX | DirectX 12 (SM6) | DirectX 12 (SM6) | DirectX 12 (SM6) |
| Upscaling | FSR 2 recommended | DLSS Quality / FSR 3 | DLSS Quality / native |
| Target FPS | 30 FPS @ 1080p Low | 60 FPS @ 1080p High or 1440p TSR | 60–90 FPS @ 1440p Ultra |

**Notes:** Minimum spec requires DX12 SM6 (Feature Level 12_1) if Nanite and VSM are enabled. GTX 1650 and Intel Iris Xe are excluded from this minimum because they lack 64-bit integer atomics. If you want to support GTX 1650, you must disable Nanite and VSM on the Low preset and provide a DX11 SM5 fallback or DX12 SM5 path.

---

### 4.3 Demanding AAA (Full Nanite + HW Lumen + VSM)

| | Min Spec | Recommended Spec | High Spec |
|-|----------|-----------------|-----------|
| OS | windows 11 64-bit | Windows 11 64-bit | Windows 11 64-bit |
| CPU | Intel Core i5-10600K / AMD Ryzen 5 5600X (6-core, 3.5+ GHz) | Intel Core i5-13400F / AMD Ryzen 5 7600 | Intel Core i7-14700K / AMD Ryzen 7 7800X3D |
| RAM | 16 GB | 16 GB | 32 GB |
| GPU | NVIDIA GeForce RTX 2060 Super / AMD RX 6700 | NVIDIA GeForce RTX 3060 Ti / AMD RX 6700 XT | NVIDIA GeForce RTX 4070 Super / AMD RX 7900 XT |
| VRAM | 8 GB | 12 GB | 16 GB |
| Storage | 50–100 GB NVMe SSD | NVMe SSD | NVMe Gen4 SSD |
| DirectX | DirectX 12 (SM6 / Feature Level 12_1) | DirectX 12 (SM6) | DirectX 12 (SM6) |
| Upscaling | Required: FSR 3 Performance or DLSS Performance | DLSS Quality / FSR 3 Quality | DLSS Quality or native 1440p |
| Target FPS | 30 FPS @ 1080p Low (upscaled) | 60 FPS @ 1080p High (DLSS/FSR Quality) | 60 FPS @ 1440p Ultra / 4K DLSS Balanced |

**Notes:** Min spec explicitly excludes GTX 10xx and GTX 16xx series (no HW RT, insufficient compute for VSM). RTX 20xx is the practical floor for Hardware Lumen. If you wish to support RTX 2060 at minimum, you must limit shadow cascade count, VSM page pool size, and Lumen probe density.

---

## 5. UE5-Specific Notes for Developers

### 5.1 Nanite Requirements

Nanite requires DirectX 12 with Shader Model 6 (SM6) and Feature Level 12_1 (64-bit integer atomics). This excludes:

- All GTX 10xx / 16xx series (no HW RT, limited DX12 FL)
- Intel Iris Xe Graphics (confirmed missing SM6.6 / FL12_1 per [Steam community UE5 thread](https://steamcommunity.com/app/3041230/discussions/0/757304900494414150/))
- Intel HD / UHD Graphics (pre-Arc)
- Older AMD GCN cards (RX 400/500 series support DX12 but not FL12_1)

GPUs with Nanite support in the April 2026 survey: RTX 20xx+ (HW RT), RTX 30xx+, RTX 40xx+, RTX 50xx+, RX 6000+, RX 7000+, RX 9000+, Intel Arc. These collectively represent approximately 65–70% of the surveyed Steam userbase on discrete GPUs.

**Nanite fallback path:** UE5 ships a software Nanite fallback that renders using traditional triangle meshes with LODs. This is slow (not a real-time optimized path) and unsuitable for shipping without substantial art pipeline work. If you want GTX 1650-class support, plan your LOD pipeline explicitly and disable Nanite in that hardware tier via scalability settings.

### 5.2 Hardware Lumen Requirements

Hardware Lumen uses hardware ray tracing (BVH traversal on RT cores). It requires:

- NVIDIA RTX 20xx or newer (Turing+)
- AMD RX 6000 or newer (RDNA 2+)
- Intel Arc (Xe-HPG)

**Software Lumen** (screen-space + signed distance field tracing) runs on any DX11/DX12 GPU with SM5 or SM6. It is available as fallback for GTX 10xx / GTX 16xx and non-RT AMD cards. Software Lumen quality is substantially lower (no offscreen bounce light, shorter trace distances, more temporal noise) but provides a usable GI approximation at medium settings.

**Performance cost:** Hardware Lumen on an RTX 3060 at 1080p Medium adds approximately 8–15 ms GPU time over a baked lighting scene. Software Lumen at Medium adds approximately 4–8 ms. Both costs rise significantly at higher resolutions and with more dynamic light sources.

### 5.3 Virtual Shadow Maps (VSM) and VRAM

VSM is the default shadow technology in UE5 for DX12 targets. It provides high-quality, stable shadows for Nanite geometry. It is compute-intensive and VRAM-intensive:

- VSM requires a physical page pool stored in VRAM. Default pool size is approximately 4–6 GB on high settings.
- On 8 GB VRAM cards (RTX 4060, RTX 3060 desktop is 12 GB but mobile 3060 is 6/8 GB), VSM can consume 30–50% of total VRAM budget.
- On 4–6 GB VRAM cards (GTX 1650, GTX 1060), VSM is not feasible at any quality level.

**Developer action required:** Use the scalability system to reduce `r.Shadow.Virtual.MaxPhysicalPages` per hardware tier. Low-end preset should use Traditional Shadow Maps (TSM) instead of VSM, or heavily limit VSM page count. VSM can be disabled entirely with `r.Shadow.Virtual.Enable 0`.

### 5.4 DirectX 12 and Shader Model Summary

| Feature | Min GPU DX Requirement | Share of Steam users with this capability |
|---------|----------------------|------------------------------------------|
| DX12 (any) | GTX 10xx / RX 400+ / Intel HD 620+ | ~91.9% (DX12 GPU share, April 2026) |
| DX12 SM6 (basic) | RTX 20xx / RX 5000+ / GTX 16xx (partial) | ~75–80% estimated |
| DX12 SM6.6 / FL12_1 (Nanite + VSM) | RTX 20xx / RX 6000+ / Intel Arc | ~65–70% estimated |
| Hardware Ray Tracing | RTX 20xx / RX 6000+ / Intel Arc | ~65–70% estimated |
| DLSS (any version) | RTX 20xx+ only | ~45–50% estimated |
| FSR 3 (GPU-agnostic) | Any DX11+ GPU | ~91% |

The survey reports DirectX 12 GPUs at 91.89%, DirectX 11 at 0.43%, DirectX 10 at 0.22%, and legacy DX8 and below at 7.46%. The 7.46% "DX8 and below" bucket contains legacy/virtual GPUs, not real gaming hardware.

### 5.5 TSR (Temporal Super Resolution) Recommendations

UE5's built-in TSR is the recommended upscaler for cross-platform compatibility (no vendor license required, works on all GPUs). Key usage notes:

- TSR at "Quality" mode (67% of native): minimal visual difference from native at 1440p. Recommended as default for mid-tier users.
- TSR at "Balanced" (59% native): good for high-tier users at 4K where native is too expensive on non-flagship hardware.
- TSR at "Performance" (50% native): noticeable softness; acceptable only as a low-tier fallback for demanding AAA games.
- DLSS 4 Super Resolution (RTX 20xx+ with updated driver) outperforms TSR at equivalent sample rates on NVIDIA hardware. Offer both.
- FSR 4 (available on RX 9000 series only as of May 2026) uses ML upscaling. Too early to specify as a baseline — use FSR 3 as the AMD/universal path.

---

## 6. Summary Table: What to Write in Steam Store Requirements

### Indie / Small Scope

| Requirement Level | CPU | GPU | RAM | VRAM | OS |
|-------------------|-----|-----|-----|------|----|
| Minimum | i5-8400 / Ryzen 5 2600 | GTX 1060 6 GB / RX 580 | 8 GB | 4 GB | windows 11 |
| Recommended | i5-12400F / Ryzen 5 5600 | RTX 3060 / RX 6600 | 16 GB | 8 GB | Windows 11 |

### AA (Lumen Software + Partial Nanite)

| Requirement Level | CPU | GPU | RAM | VRAM | OS |
|-------------------|-----|-----|-----|------|----|
| Minimum | i5-10600 / Ryzen 5 3600 | RTX 2060 / RX 6600 | 12 GB | 8 GB | windows 11 (DX12) |
| Recommended | i5-13400F / Ryzen 5 5600X | RTX 3060 12 GB / RX 6700 XT | 16 GB | 12 GB | Windows 11 |
| High (optional) | i7-13700K / Ryzen 7 7700X | RTX 4070 Super / RX 7800 XT | 32 GB | 16 GB | Windows 11 |

### Demanding AAA (HW Lumen + Nanite + VSM)

| Requirement Level | CPU | GPU | RAM | VRAM | OS |
|-------------------|-----|-----|-----|------|----|
| Minimum | i5-10600K / Ryzen 5 5600X | RTX 2060 Super / RX 6700 | 16 GB | 8 GB | windows 11 (DX12 SM6) |
| Recommended | i5-13400F / Ryzen 5 7600 | RTX 3060 Ti / RX 6700 XT | 16 GB | 12 GB | Windows 11 |
| High | i7-14700K / Ryzen 7 7800X3D | RTX 4070 Super / RX 7900 XT | 32 GB | 16 GB | Windows 11 |

---

## 7. Key Takeaways

1. **The median Steam user in April 2026 has an RTX 3060 or RTX 4060, 16 GB RAM, a 1080p display, a 6–8 core CPU, and Windows 11.** This is your "Recommended" spec baseline for most genres.

2. **8 GB VRAM is the current median VRAM tier** (26.76%), but 16 GB is rising fast (+1.98% in one month alone). Targeting 8 GB as minimum VRAM is appropriate; do not assume 12+ GB is available for your baseline recommended spec.

3. **GTX 10xx / 16xx users still represent ~5–7% of Steam** via GTX 1060 (1.61%), GTX 1650 (2.58%), GTX 1660 SUPER (1.46%), and others. These GPUs cannot run Nanite or Hardware Lumen in default UE5 configurations. If you want to support them, plan an explicit DX11/SM5 fallback or Low preset that disables these features.

4. **AMD discrete GPUs are underrepresented on Steam relative to AMD's market share.** A significant portion appears in the generic "AMD Radeon(TM) Graphics" and "AMD Radeon Graphics" catch-all buckets (~4% combined). Per [The FPS Review's April 2026 analysis](https://www.thefpsreview.com/2026/05/02/trends-from-the-april-2026-steam-hardware-survey/), AMD's discrete presence is historically weak on Steam. Test AMD paths carefully despite lower survey representation.

5. **RTX 50 series (Blackwell) is accumulating share.** RTX 5070 (2.86%), RTX 5060 (2.57%), RTX 5060 Ti (1.81%), RTX 5070 Ti (1.62%), RTX 5080 (1.37%). Combined ~10% and growing. DLSS 4 Multi Frame Generation is available to these users. Plan for it as an optional enhancement, not a baseline.

6. **1440p is the next battleground.** 21.41% of Steam users are already at 1440p, up 0.71% month-over-month. TSR at Quality mode (67% native) or DLSS Quality render at ~960p → 1440p output is the sweet spot for mid-tier cards at this resolution.

7. **Windows 11 is dominant at 67.74%** and DX12 at 91.89%. You can safely default to DX12 in your build with a DX11 fallback for the ~8% without DX12 capable hardware.

---

*Sources: [Steam Hardware & Software Survey April 2026](https://store.steampowered.com/hwsurvey/Steam-Hardware-Software-Survey-Welcome-to-Steam) | [The FPS Review April 2026 Analysis](https://www.thefpsreview.com/2026/05/02/trends-from-the-april-2026-steam-hardware-survey/) | [The FPS Review March 2026 Analysis](https://www.thefpsreview.com/2026/04/03/trends-from-the-march-2026-steam-hardware-survey/) | [Wccftech March 2026 Survey Coverage](https://wccftech.com/steam-hardware-survey-march-2026/) | [Windows Forum January 2026 Survey](https://windowsforum.com/threads/january-2026-steam-survey-more-vram-more-ram-1440p-on-the-rise.400066/) | [TweakTown AMD CPU Gain Sept 2025](https://www.tweaktown.com/news/108073/steam-data-shows-pc-gamers-are-choosing-amd-cpus-over-intel/index.html) | [Epic Dev Community — UE5 Nanite/VSM hardware requirements](https://steamcommunity.com/app/3041230/discussions/0/757304900494414150/) | [Reddit r/unrealengine UE5 hardware thread](https://www.reddit.com/r/unrealengine/comments/16iaovc/minimum_system_requirements_for_running_games_on/)*
