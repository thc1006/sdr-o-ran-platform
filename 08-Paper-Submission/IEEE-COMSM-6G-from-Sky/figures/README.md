# Figures Generation Guide

This directory contains scripts and source files for generating publication-quality figures for the manuscript.

## Quick Start

### Prerequisites

1. **Python 3.8+** with matplotlib and numpy:
   ```bash
   pip install matplotlib numpy
   ```

2. **Graphviz** (for architecture diagram):
   - Windows: Download from https://graphviz.org/download/
   - macOS: `brew install graphviz`
   - Linux: `sudo apt-get install graphviz` or `sudo yum install graphviz`

### Generate Figures

#### Figure 2: Performance Graph (Automated)

```bash
cd figures
python generate_figure2.py
```

**Output:**
- `figure2_performance.pdf` (vector, preferred)
- `figure2_performance.eps` (vector, IEEE compatible)
- `figure2_performance.png` (600 dpi raster backup)

#### Figure 1: Architecture Diagram (Graphviz)

```bash
cd figures

# Generate PDF (recommended)
dot -Tpdf architecture_diagram.dot -o figure1_architecture.pdf

# Generate EPS (IEEE compatible)
dot -Teps architecture_diagram.dot -o figure1_architecture.eps

# Generate high-res PNG (backup)
dot -Tpng architecture_diagram.dot -o figure1_architecture.png -Gdpi=300
```

**Alternative: Edit Graphviz Online**
1. Copy contents of `architecture_diagram.dot`
2. Visit https://dreampuf.github.io/GraphvizOnline/
3. Paste and visualize
4. Download as SVG/PDF/PNG

## Files Description

### Source Files

- **`generate_figure2.py`** - Python script to generate performance graph
  - Automated generation
  - Publication-quality settings
  - Multiple output formats

- **`architecture_diagram.dot`** - Graphviz DOT file for architecture diagram
  - Four-layer architecture
  - Color-coded components
  - Standard network symbols
  - Interface labels

### Output Files (Generated)

- **`figure1_architecture.pdf`** - Architecture diagram (PDF vector)
- **`figure1_architecture.eps`** - Architecture diagram (EPS vector)
- **`figure2_performance.pdf`** - Performance graph (PDF vector)
- **`figure2_performance.eps`** - Performance graph (EPS vector)

## Manual Alternatives

### Figure 1: Architecture Diagram

If you prefer manual creation, use these tools:

#### Option A: draw.io (Recommended for non-programmers)
1. Visit https://app.diagrams.net/
2. Create new diagram (7.16 inches × 5 inches)
3. Follow specifications in `../FIGURES_GUIDE.md`
4. Export as PDF or EPS

#### Option B: Microsoft Visio
1. Open Visio with network diagram template
2. Create architecture using specifications
3. Export as PDF (File → Export → PDF)

#### Option C: PowerPoint/Keynote
1. Create slide with exact dimensions (7.16" × 5")
2. Build architecture diagram
3. Export as PDF with high quality

### Figure 2: Performance Graph

If Python is not available:

#### Option A: MATLAB
```matlab
elevation = [10, 30, 60, 90];
dl_throughput = [52.3, 78.5, 89.2, 94.7];
ul_throughput = [18.7, 31.2, 38.6, 41.3];
sinr = [3.2, 8.5, 12.8, 15.2];

figure('Units', 'inches', 'Position', [0 0 3.5 3.5]);
yyaxis left
plot(elevation, dl_throughput, 'b-o', 'LineWidth', 1.5, 'MarkerSize', 6);
hold on;
plot(elevation, ul_throughput, 'r--s', 'LineWidth', 1.5, 'MarkerSize', 6);
ylabel('Throughput (Mbps)');
xlabel('Satellite Elevation Angle (degrees)');
ylim([0 100]);
grid on;

yyaxis right
plot(elevation, sinr, 'g:^', 'LineWidth', 1.5, 'MarkerSize', 6);
ylabel('SINR (dB)');
ylim([0 16]);

legend('Downlink Throughput', 'Uplink Throughput', 'SINR', 'Location', 'northwest');
set(gca, 'FontSize', 8);

print('figure2_performance', '-dpdf', '-r300');
```

#### Option B: Excel/Google Sheets
1. Input data from `generate_figure2.py`
2. Create combination chart (line + secondary axis)
3. Format according to specifications
4. Export as high-quality PDF

## Quality Checklist

Before submission, verify:

### Figure 1: Architecture
- [ ] Vector format (PDF or EPS)
- [ ] Size: 7.16 inches wide (two-column)
- [ ] Four layers clearly visible
- [ ] Interface labels (E2, A1, F1, FAPI) readable
- [ ] Color scheme consistent
- [ ] Legend included
- [ ] All text readable at print size (minimum 8pt)

### Figure 2: Performance
- [ ] Vector format (PDF or EPS)
- [ ] Size: 3.5 inches wide (single-column)
- [ ] Axes labeled clearly
- [ ] Data points visible with markers
- [ ] Legend positioned appropriately
- [ ] Grid lines subtle but visible
- [ ] Dual y-axes clearly labeled

### General
- [ ] File size < 5 MB per figure
- [ ] Fonts embedded in PDF
- [ ] No pixelation when zoomed
- [ ] Colors distinguishable in grayscale
- [ ] Print test at actual size successful

## Troubleshooting

### Python Script Issues

**Error: `ModuleNotFoundError: No module named 'matplotlib'`**
```bash
pip install matplotlib numpy
```

**Error: Font warning**
- Script will fall back to default fonts
- Output will still be publication-quality

### Graphviz Issues

**Error: `dot: command not found`**
- Install Graphviz (see Prerequisites)
- Add to PATH: Windows users may need to restart terminal

**Layout too large/small:**
- Edit `architecture_diagram.dot`
- Adjust `nodesep` and `ranksep` values
- Regenerate

### General Issues

**PDF fonts not embedded:**
```bash
# Check PDF fonts
pdffonts figure1_architecture.pdf

# If fonts not embedded, try:
gs -dNOPAUSE -dBATCH -sDEVICE=pdfwrite \
   -dEmbedAllFonts=true \
   -sOutputFile=figure1_embedded.pdf \
   -f figure1_architecture.pdf
```

**Figure too large:**
- Compress PDF: https://www.ilovepdf.com/compress_pdf
- Or optimize with Ghostscript:
  ```bash
  gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 \
     -dPDFSETTINGS=/prepress -dNOPAUSE -dQUIET -dBATCH \
     -sOutputFile=output.pdf input.pdf
  ```

## IEEE Submission Format

### Required Formats
- **Primary:** EPS (Encapsulated PostScript)
- **Alternative:** PDF (Portable Document Format)
- **Backup:** TIFF or PNG at >300 dpi

### File Naming
- `tsai_fig1.pdf` or `tsai_fig1.eps`
- `tsai_fig2.pdf` or `tsai_fig2.eps`

### Captions
Captions are in the main manuscript (`../paper.md`):
- Figure 1: Section III (System Architecture)
- Figure 2: Section VI (Performance Evaluation)

## Support

For issues or questions:
1. Check `../FIGURES_GUIDE.md` for detailed specifications
2. Review IEEE graphics guidelines: https://ieeeauthorcenter.ieee.org/create-your-ieee-article/create-graphics-for-your-article/
3. Test with IEEE Graphics Checker: https://graphicsqc.ieee.org/

## References

- **Graphviz Documentation:** https://graphviz.org/documentation/
- **Matplotlib Documentation:** https://matplotlib.org/stable/
- **IEEE Graphics Guidelines:** https://ieeeauthorcenter.ieee.org/
- **draw.io:** https://app.diagrams.net/

---

**Last Updated:** 2025-10-27
**Status:** Ready for figure generation
