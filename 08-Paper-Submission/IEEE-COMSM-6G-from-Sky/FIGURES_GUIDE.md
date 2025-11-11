# Figures Creation Guide

This document provides detailed specifications for creating the figures required for the manuscript.

---

## Figure 1: Overall System Architecture

### Description
Comprehensive multi-layer architecture diagram showing the complete SDR-O-RAN platform for NTN operations.

### Specifications
- **Format:** Vector (EPS or PDF preferred) or high-resolution PNG (>300 dpi)
- **Size:** Two-column width (7.16 inches / 18.2 cm / 43 picas wide)
- **Aspect Ratio:** 16:9 or 4:3 recommended
- **Color:** Full color acceptable (will be printed in color)
- **Font:** Arial or Helvetica, minimum 8pt for readability when printed
- **File Name:** `figure1_architecture.eps` or `figure1_architecture.pdf`

### Content Requirements

The diagram should illustrate four primary layers:

**Layer 1: Physical Infrastructure** (Bottom)
- USRP X310 SDR with GPSDO (hardware illustration)
- Multi-band antenna system (C/Ku/Ka bands)
- 3x compute servers with specifications
- 10 GbE networking
- Connect these with lines showing data flow

**Layer 2: SDR Platform**
- VITA 49.2 VRT Receiver (show packet structure icon)
- gRPC Bidirectional Streaming Server (show bidirectional arrows)
- FastAPI REST Gateway (show HTTP/REST icon)
- Show IQ data flow from Layer 1 to Layer 3

**Layer 3: O-RAN Components**
- OpenAirInterface 5G-NTN gNB (show DU/CU split)
- Near-RT RIC Platform (show E2 interface)
- Intelligent xApps (show 2-3 example xApps: Traffic Steering, QoS Optimization)
- Show E2 and A1 interfaces with labeled arrows

**Layer 4: Cloud-Native Orchestration** (Top)
- Kubernetes Cluster (show pods/containers icon)
- Nephio Network Automation (show orchestration symbol)
- Monitoring Stack (Prometheus + Grafana icons)
- Show management/control plane

### Visual Style
- Use consistent color scheme:
  - Blue tones for physical/hardware
  - Green tones for SDR platform
  - Orange/yellow tones for O-RAN
  - Purple tones for cloud/orchestration
- Use standard network diagram symbols (IEEE/UML)
- Include a legend explaining interface types (E2, A1, F1, FAPI)
- Show satellite in sky (optional, for context)

### Tools Recommendation
- **draw.io** (https://app.diagrams.net/) - Free, web-based, exports to EPS/PDF
- **Microsoft Visio** - Professional diagramming tool
- **Lucidchart** - Online diagramming with good export options
- **PowerPoint/Keynote** - Can create and export as PDF
- **Inkscape** - Free vector graphics editor, exports to EPS/PDF

### Caption
```
Fig. 1. Overall architecture of the cloud-native SDR-O-RAN platform for NTN operations, showing four primary layers: (1) Physical Infrastructure with USRP X310 SDR and multi-band antenna system, (2) SDR Platform implementing VITA 49.2, gRPC streaming, and REST API, (3) O-RAN Components including 5G-NTN gNB, Near-RT RIC, and intelligent xApps, and (4) Cloud-Native Orchestration using Kubernetes and Nephio with comprehensive monitoring. Key interfaces (E2, A1, F1, FAPI) enable standards-compliant integration.
```

---

## Figure 2: Throughput Performance vs. Satellite Elevation Angle

### Description
Line graph showing downlink and uplink throughput performance as a function of satellite elevation angle, with SINR as secondary axis.

### Specifications
- **Format:** Vector (PDF or EPS preferred)
- **Size:** Single-column width (3.5 inches / 8.9 cm / 21 picas wide)
- **Aspect Ratio:** 4:3 or 1:1
- **Resolution:** Vector preferred, or >600 dpi if raster
- **File Name:** `figure2_performance.pdf` or `figure2_performance.eps`

### Content Requirements

**X-axis:**
- Label: "Satellite Elevation Angle (degrees)"
- Range: 10° to 90°
- Tick marks: Every 20° (10, 30, 50, 70, 90)

**Y-axis (Primary):**
- Label: "Throughput (Mbps)"
- Range: 0 to 100 Mbps
- Tick marks: Every 20 Mbps (0, 20, 40, 60, 80, 100)

**Y-axis (Secondary, right side):**
- Label: "SINR (dB)"
- Range: 0 to 16 dB
- Tick marks: Every 4 dB (0, 4, 8, 12, 16)

**Data Series:**
1. **Downlink Throughput** (blue solid line with circle markers)
   - Data points: (10°, 52.3), (30°, 78.5), (60°, 89.2), (90°, 94.7)

2. **Uplink Throughput** (red dashed line with square markers)
   - Data points: (10°, 18.7), (30°, 31.2), (60°, 38.6), (90°, 41.3)

3. **SINR** (green dotted line with triangle markers, secondary axis)
   - Data points: (10°, 3.2), (30°, 8.5), (60°, 12.8), (90°, 15.2)

### Visual Style
- Grid: Light gray grid lines for readability
- Line width: 1.5-2pt
- Marker size: Medium (visible but not overwhelming)
- Legend: Place in upper left corner, showing all three data series
- Font: Arial or Helvetica, 9pt for axis labels, 8pt for tick labels

### Tools Recommendation
- **Python matplotlib:** Professional plotting, perfect vector output
- **MATLAB:** High-quality technical plots
- **R ggplot2:** Publication-quality graphics
- **Excel/Google Sheets:** Can work, but export as PDF for best quality
- **Origin/SigmaPlot:** Professional scientific plotting software

### Python matplotlib Example Code

```python
import matplotlib.pyplot as plt
import numpy as np

# Data
elevation = [10, 30, 60, 90]
dl_throughput = [52.3, 78.5, 89.2, 94.7]
ul_throughput = [18.7, 31.2, 38.6, 41.3]
sinr = [3.2, 8.5, 12.8, 15.2]

# Create figure and axes
fig, ax1 = plt.subplots(figsize=(3.5, 3.5))  # Single-column width

# Primary axis: Throughput
ax1.set_xlabel('Satellite Elevation Angle (degrees)', fontsize=9)
ax1.set_ylabel('Throughput (Mbps)', fontsize=9)
ax1.plot(elevation, dl_throughput, 'b-o', linewidth=1.5,
         markersize=6, label='Downlink Throughput')
ax1.plot(elevation, ul_throughput, 'r--s', linewidth=1.5,
         markersize=6, label='Uplink Throughput')
ax1.set_xlim([0, 100])
ax1.set_ylim([0, 100])
ax1.grid(True, alpha=0.3)
ax1.tick_params(axis='both', labelsize=8)

# Secondary axis: SINR
ax2 = ax1.twinx()
ax2.set_ylabel('SINR (dB)', fontsize=9)
ax2.plot(elevation, sinr, 'g:^', linewidth=1.5,
         markersize=6, label='SINR')
ax2.set_ylim([0, 16])
ax2.tick_params(axis='y', labelsize=8)

# Combined legend
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2,
           loc='upper left', fontsize=7)

# Tight layout and save
plt.tight_layout()
plt.savefig('figure2_performance.pdf', dpi=300, bbox_inches='tight')
plt.savefig('figure2_performance.eps', format='eps', bbox_inches='tight')
```

### Caption
```
Fig. 2. Throughput and SINR performance as a function of satellite elevation angle. Downlink (DL) throughput reaches 94.7 Mbps at zenith (90°) with SINR of 15.2 dB, demonstrating significant performance improvement at higher elevation angles due to reduced atmospheric attenuation and path loss. Uplink (UL) throughput is limited by UE power constraints (23 dBm max EIRP), achieving 41.3 Mbps at zenith. LEO satellite performance measured at 600 km altitude using ITU-R P.681 channel model.
```

---

## Tables (Already Included in Manuscript)

The manuscript includes three tables that do not require separate creation as they are formatted in the text:

### Table I: PQC vs. Classical Cryptography Performance Comparison
- Location: Section IV.B (Post-Quantum Cryptographic Security)
- Content: Performance comparison of cryptographic operations

### Table II: Complete Technology Stack
- Location: Section V.A (Software Stack and Technology Selection)
- Content: Comprehensive list of technologies used

### Table III: E2E Latency Results for Different Orbits
- Location: Section VI.B (Latency and Throughput Analysis)
- Content: Latency measurements for LEO/MEO/GEO

---

## Figure Submission Checklist

### Before Submission:
- [ ] Figure 1 created and exported as EPS/PDF
- [ ] Figure 2 created and exported as PDF/EPS
- [ ] Both figures meet size specifications (Fig 1: 7.16", Fig 2: 3.5")
- [ ] Vector format confirmed (scalable without pixelation)
- [ ] Fonts embedded in PDF/EPS (check with PDF viewer)
- [ ] File sizes reasonable (<5 MB each)
- [ ] Figures reviewed for clarity and readability
- [ ] Captions match manuscript text exactly
- [ ] Figure numbers and references in manuscript are correct

### Quality Check:
- [ ] Print figures at actual size to verify readability
- [ ] Check that all text is legible at publication size
- [ ] Verify color scheme is distinguishable (consider colorblind-friendly palette)
- [ ] Ensure consistent styling between both figures
- [ ] Confirm legend and labels are clear and unambiguous

---

## IEEE-Specific Requirements

### Graphics Format Guidelines

**Accepted Formats:**
- EPS (Encapsulated PostScript) - Vector, preferred for diagrams
- PDF (Portable Document Format) - Vector, widely accepted
- TIFF (Tagged Image File Format) - Raster, if vector not possible
- PNG (Portable Network Graphics) - Raster, last resort

**Resolution Requirements:**
- **Vector graphics:** Preferred (infinitely scalable)
- **Color/Grayscale images:** Minimum 300 dpi at publication size
- **Line art (black and white):** Minimum 600 dpi

### File Naming Convention

IEEE recommends the following naming convention:
- `lastname_figX.ext` where X is the figure number
- Example: `tsai_fig1.pdf`, `tsai_fig2.eps`

### Figure Captions

- Submit captions in a separate document or in manuscript
- Number figures sequentially (Fig. 1, Fig. 2, Fig. 3...)
- Reference figures in text: "as shown in Fig. 1"
- Captions should be self-contained (explain what is shown)
- Avoid overly long captions (3-4 sentences maximum)

---

## Additional Resources

- **IEEE Author Tools:** https://ieeeauthorcenter.ieee.org/create-your-ieee-article/create-graphics-for-your-article/
- **IEEE Graphics Checker:** https://graphicsqc.ieee.org/
- **ColorBrewer (colorblind-safe palettes):** https://colorbrewer2.org/
- **Matplotlib IEEE Style:** https://github.com/garrettj403/SciencePlots
- **Draw.io Templates:** https://app.diagrams.net/ (search "network architecture")

---

**Status:** Ready for figure creation
**Estimated Time:** 2-4 hours for both figures (depending on tool proficiency)
**Priority:** High (required for submission)

---

**Last Updated:** 2025-10-27
