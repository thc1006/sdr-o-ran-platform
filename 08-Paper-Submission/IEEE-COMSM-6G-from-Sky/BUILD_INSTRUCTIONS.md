# Build Instructions - Complete Submission Package

**Last Updated:** 2025-10-27
**Status:** Ready for final build and submission
**Deadline:** December 15, 2025 (49 days remaining)

---

## 📋 Quick Build Guide (5 Steps)

### Step 1: Generate Figures (15 minutes)

```bash
cd 08-Paper-Submission/IEEE-COMSM-6G-from-Sky/figures

# Generate Figure 2 (Performance Graph)
python generate_figure2.py

# Generate Figure 1 (Architecture Diagram) - requires Graphviz
dot -Tpdf architecture_diagram.dot -o figure1_architecture.pdf
dot -Teps architecture_diagram.dot -o figure1_architecture.eps
```

**Expected Output:**
- ✅ `figures/figure1_architecture.pdf`
- ✅ `figures/figure1_architecture.eps`
- ✅ `figures/figure2_performance.pdf`
- ✅ `figures/figure2_performance.eps`

**Verification:**
```bash
ls -lh figures/*.pdf figures/*.eps
```

### Step 2: Generate PDF Manuscript (5 minutes)

**Option A: Linux/macOS**
```bash
cd 08-Paper-Submission/IEEE-COMSM-6G-from-Sky
chmod +x build_pdf.sh
./build_pdf.sh
```

**Option B: Windows**
```cmd
cd 08-Paper-Submission\IEEE-COMSM-6G-from-Sky
build_pdf.bat
```

**Expected Output:**
- ✅ `paper.pdf` (IEEE two-column format)

### Step 3: Convert Cover Letter (2 minutes)

```bash
# Using Pandoc
pandoc cover_letter.md -o cover_letter.pdf

# Or manually: Open cover_letter.md in any editor, export as PDF
```

**Expected Output:**
- ✅ `cover_letter.pdf`

### Step 4: Register ORCID ID (10 minutes)

1. Visit: https://orcid.org/register
2. Complete registration
3. Update author information in manuscript
4. Add ORCID to cover letter (line 136)

### Step 5: Final Review (30 minutes)

**Checklist:**
- [ ] Open `paper.pdf` and verify formatting
- [ ] Check that both figures appear correctly in PDF
- [ ] Verify all references are properly formatted
- [ ] Read abstract and conclusion for clarity
- [ ] Proofread for typos and grammar
- [ ] Test all DOI links in references
- [ ] Verify word count (~10,500 words)
- [ ] Check author information includes ORCID

---

## 🛠️ Detailed Instructions

### Prerequisites Installation

#### Install Python + Dependencies

**Windows:**
```cmd
# Download Python from https://www.python.org/downloads/
# During installation, check "Add Python to PATH"

# Install required packages
pip install matplotlib numpy
```

**macOS:**
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python

# Install packages
pip3 install matplotlib numpy
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install python3 python3-pip

pip3 install matplotlib numpy
```

#### Install Graphviz (for Figure 1)

**Windows:**
1. Download from https://graphviz.org/download/
2. Run installer
3. Add to PATH (installer option) or manually add `C:\Program Files\Graphviz\bin`
4. Restart terminal

**macOS:**
```bash
brew install graphviz
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install graphviz
```

#### Install LaTeX (for PDF generation)

**Windows - MiKTeX:**
1. Download from https://miktex.org/download
2. Run installer (basic installation ~300MB)
3. During first use, allow automatic package installation

**macOS - MacTeX:**
```bash
# Full installation (~4GB)
brew install --cask mactex

# Or BasicTeX (smaller, ~100MB)
brew install --cask basictex
```

**Linux (Ubuntu/Debian):**
```bash
# Full installation
sudo apt-get install texlive-full

# Or minimal installation
sudo apt-get install texlive texlive-latex-extra texlive-fonts-recommended
```

#### Install Pandoc (for format conversion)

**Windows:**
1. Download from https://pandoc.org/installing.html
2. Run installer

**macOS:**
```bash
brew install pandoc
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install pandoc
```

---

## 🎨 Figure Generation

### Automated Figure Generation (Recommended)

The submission package includes automated scripts for generating publication-quality figures:

#### Figure 2: Performance Graph

```bash
cd figures
python generate_figure2.py
```

**What it does:**
- Generates throughput vs. elevation angle plot
- Creates dual y-axis for SINR
- Outputs multiple formats (PDF, EPS, PNG)
- Uses publication-quality settings (Arial font, proper sizing)

**Output:**
- `figure2_performance.pdf` (vector, 3.5" wide, preferred)
- `figure2_performance.eps` (vector, IEEE compatible)
- `figure2_performance.png` (600 dpi backup)

#### Figure 1: Architecture Diagram

```bash
cd figures
dot -Tpdf architecture_diagram.dot -o figure1_architecture.pdf
dot -Teps architecture_diagram.dot -o figure1_architecture.eps
```

**What it does:**
- Generates four-layer architecture diagram
- Color-coded components (blue, green, orange, purple)
- Shows interfaces (E2, A1, F1, FAPI)
- Includes legend and satellite connection

**Output:**
- `figure1_architecture.pdf` (vector, 7.16" wide, preferred)
- `figure1_architecture.eps` (vector, IEEE compatible)

### Manual Figure Creation (Alternative)

If automated generation fails, see detailed instructions in:
- `figures/README.md` - Complete manual alternatives
- `FIGURES_GUIDE.md` - Design specifications

**Manual Options:**
- **draw.io:** https://app.diagrams.net/ (free, web-based)
- **Microsoft Visio:** Professional diagramming tool
- **PowerPoint:** Create slides with exact dimensions
- **Inkscape:** Free vector graphics editor

---

## 📄 PDF Generation

### Method 1: Automated Build Script (Recommended)

**Linux/macOS:**
```bash
cd 08-Paper-Submission/IEEE-COMSM-6G-from-Sky
chmod +x build_pdf.sh
./build_pdf.sh
```

**Windows:**
```cmd
cd 08-Paper-Submission\IEEE-COMSM-6G-from-Sky
build_pdf.bat
```

**What it does:**
- Checks for required tools (Pandoc, LaTeX)
- Converts `paper.md` to IEEE two-column format
- Processes citations from `references.bib`
- Generates `paper.pdf`
- Cleans up temporary files

### Method 2: Overleaf (Online, No Installation)

1. **Create Overleaf Account:**
   - Visit: https://www.overleaf.com/
   - Sign up (free account sufficient)

2. **Create New Project:**
   - Click "New Project" → "Blank Project"
   - Or use IEEE template: "New Project" → "IEEE Communications Standards Magazine"

3. **Upload Files:**
   - Upload `paper.md` content (copy-paste into main.tex)
   - Upload `references.bib`
   - Upload figures from `figures/` directory

4. **Compile:**
   - Click "Recompile"
   - Download PDF when compilation completes

**Advantages:**
- No local installation required
- Real-time preview
- Collaboration features
- Automatic LaTeX package management

### Method 3: Manual LaTeX

1. **Download IEEE Template:**
   - Visit: https://www.ieee.org/conferences/publishing/templates.html
   - Download "LaTeX Template - Conference"

2. **Create LaTeX Document:**
   ```latex
   \documentclass[journal]{IEEEtran}
   \usepackage{cite}
   \usepackage{graphicx}

   \begin{document}

   \title{Cloud-Native SDR-O-RAN Platform for Non-Terrestrial Networks}
   \author{Hsiu-Chi Tsai}

   \maketitle

   \begin{abstract}
   % Copy abstract from paper.md
   \end{abstract}

   % Copy remaining content from paper.md
   % Convert Markdown formatting to LaTeX

   \bibliographystyle{IEEEtran}
   \bibliography{references}

   \end{document}
   ```

3. **Compile:**
   ```bash
   pdflatex paper.tex
   bibtex paper
   pdflatex paper.tex
   pdflatex paper.tex
   ```

### Method 4: Microsoft Word

1. **Convert to DOCX:**
   ```bash
   pandoc paper.md --citeproc --bibliography references.bib -o paper.docx
   ```

2. **Download IEEE Word Template:**
   - Visit: https://www.ieee.org/conferences/publishing/templates.html
   - Download "Word Template - Conference"

3. **Manual Formatting:**
   - Open `paper.docx`
   - Copy content to IEEE template
   - Format according to guidelines
   - Insert figures manually
   - Export as PDF (File → Save As → PDF)

---

## ✅ Pre-Submission Checklist

### Documents Required

- [ ] **Manuscript PDF** (`paper.pdf`)
  - IEEE two-column format
  - All figures embedded and readable
  - References properly formatted
  - ~10,500 words, 12-14 pages

- [ ] **Cover Letter PDF** (`cover_letter.pdf`)
  - Addressed to Guest Editors
  - Includes ORCID ID
  - Lists suggested reviewers

- [ ] **Figure Files** (separate high-resolution versions)
  - `figure1_architecture.pdf` or `.eps`
  - `figure2_performance.pdf` or `.eps`

- [ ] **Author Information**
  - ORCID ID registered and added
  - Complete affiliation
  - Contact email verified

### Quality Checks

#### Manuscript
- [ ] Title page includes: title, author, affiliation, ORCID
- [ ] Abstract is 250 words (within 200-250 guideline)
- [ ] Keywords: 8 keywords listed
- [ ] Section numbering: Roman numerals (I, II, III...)
- [ ] Subsection numbering: Letters (A, B, C...)
- [ ] All 18 references cited in text
- [ ] References in IEEE format with DOIs
- [ ] No orphan headings (section heading at bottom of page)

#### Figures
- [ ] Figure 1: 7.16 inches wide, vector format
- [ ] Figure 2: 3.5 inches wide, vector format
- [ ] Both figures clearly readable at print size
- [ ] Figure captions match text exactly
- [ ] All figures referenced in text ("as shown in Fig. 1")
- [ ] Color scheme distinguishable in grayscale
- [ ] Text in figures minimum 8pt font

#### References
- [ ] All 18 references properly formatted
- [ ] DOI links work and go to correct articles
- [ ] References appear in order of citation
- [ ] Journal names properly abbreviated (IEEE style)
- [ ] Author names in correct format (Last, First M.)

#### Technical Content
- [ ] Abstract clearly states problem, solution, results
- [ ] Introduction explains motivation and contributions
- [ ] Standards compliance clearly documented (3GPP, O-RAN)
- [ ] Performance results with specific metrics
- [ ] Lessons learned section included
- [ ] Future work section included
- [ ] Code repository link included (GitHub)

### File Organization

```
08-Paper-Submission/IEEE-COMSM-6G-from-Sky/
├── paper.pdf ✅                          # Main manuscript (to be generated)
├── cover_letter.pdf ✅                   # Cover letter (to be generated)
├── paper.md ✅                           # Source manuscript
├── cover_letter.md ✅                    # Source cover letter
├── references.bib ✅                     # BibTeX references
├── README.md ✅                          # Package overview
├── SUBMISSION_CHECKLIST.md ✅            # Detailed checklist
├── FIGURES_GUIDE.md ✅                   # Figure specifications
├── BUILD_INSTRUCTIONS.md ✅              # This file
├── build_pdf.sh ✅                       # Build script (Linux/macOS)
├── build_pdf.bat ✅                      # Build script (Windows)
├── figures/
│   ├── generate_figure2.py ✅           # Python script for Figure 2
│   ├── architecture_diagram.dot ✅      # Graphviz for Figure 1
│   ├── README.md ✅                     # Figure generation guide
│   ├── figure1_architecture.pdf ⏳      # To be generated
│   ├── figure1_architecture.eps ⏳      # To be generated
│   ├── figure2_performance.pdf ⏳       # To be generated
│   └── figure2_performance.eps ⏳       # To be generated
└── supplementary/
    ├── author_bio.md ✅                 # Author biography
    └── dataset_info.md ✅               # Dataset information
```

---

## 📤 Submission Process

### 1. Create Manuscript Central Account

1. **Visit:** https://mc.manuscriptcentral.com/comsm-ieee
2. **Register:**
   - Full name, email, ORCID ID
   - Affiliation: Independent Researcher
   - Research interests: 6G, NTN, O-RAN, SDR
3. **Verify Email:** Check inbox and confirm

### 2. Prepare Submission Files

**Organize in a submission folder:**
```
Submission_Package/
├── paper.pdf                 # Main manuscript
├── cover_letter.pdf          # Cover letter
├── figure1_architecture.pdf  # Figure 1 (PDF)
├── figure1_architecture.eps  # Figure 1 (EPS backup)
├── figure2_performance.pdf   # Figure 2 (PDF)
└── figure2_performance.eps   # Figure 2 (EPS backup)
```

### 3. Submit Online

1. **Login** to Manuscript Central
2. **Author Center** → **Submit New Manuscript**
3. **Manuscript Type:** Select "**June 2025/6G from the Sky**"
4. **Upload Files:**
   - Main Document: `paper.pdf`
   - Cover Letter: `cover_letter.pdf`
   - Figures: Upload each figure separately
5. **Enter Metadata:**
   - Title (copy from paper.md)
   - Abstract (copy from paper.md)
   - Keywords: Software-Defined Radio, Open RAN, Non-Terrestrial Networks, 6G, AI/ML, Post-Quantum Cryptography, Cloud-Native, Network Automation
   - Author information (name, affiliation, ORCID, email)
6. **Suggested Reviewers:** (from cover_letter.md)
   - Dr. Michele Polese (m.polese@northeastern.edu)
   - Dr. Navid Nikaein (navid.nikaein@eurecom.fr)
   - Dr. Tomaso de Cola (Tomaso.deCola@dlr.de)
7. **Review Submission:**
   - Check PDF proof
   - Verify all information
8. **Submit:**
   - Click "Submit"
   - Save confirmation email with manuscript ID

### 4. Post-Submission

**Expected Timeline:**
- **Submission:** December 15, 2025 (before 23:59)
- **Editor Assignment:** 1-2 weeks (late December 2025)
- **Peer Review:** 6-8 weeks (January-February 2026)
- **Decision Notification:** February 15, 2026
- **Revision Period:** 4 weeks (if required)
- **Revised Submission:** March 15, 2026
- **Final Decision:** April 1, 2026
- **Camera-Ready:** April 15, 2026
- **Publication:** June 2026

**Tracking:**
- Login to Manuscript Central regularly
- Check email for notifications
- Respond promptly to any editorial requests

---

## 🆘 Troubleshooting

### Figure Generation Issues

**Problem: Python script fails with "No module named 'matplotlib'"**
```bash
pip install matplotlib numpy
# or
pip3 install matplotlib numpy
```

**Problem: Graphviz not found**
- Ensure Graphviz is installed (see Prerequisites)
- Check PATH environment variable
- Restart terminal after installation

**Problem: Figures too large/small**
- Edit `generate_figure2.py`: Change `figsize=(3.5, 3.5)`
- Edit `architecture_diagram.dot`: Adjust `nodesep` and `ranksep`

### PDF Generation Issues

**Problem: Pandoc not found**
```bash
# Check if installed
pandoc --version

# If not, install (see Prerequisites)
```

**Problem: LaTeX compilation errors**
- Check `pandoc_output.log` for specific error
- Common fix: Install missing LaTeX packages
  ```bash
  # MiKTeX (Windows) - will prompt to install missing packages
  # TeX Live (Linux/macOS)
  sudo tlmgr install <package-name>
  ```

**Problem: PDF fonts not embedded**
```bash
# Check fonts
pdffonts paper.pdf

# Embed fonts using Ghostscript
gs -dNOPAUSE -dBATCH -sDEVICE=pdfwrite \
   -dEmbedAllFonts=true \
   -sOutputFile=paper_embedded.pdf \
   -f paper.pdf
```

### Submission Issues

**Problem: File size too large**
- Compress PDF: https://www.ilovepdf.com/compress_pdf
- Or use Ghostscript:
  ```bash
  gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 \
     -dPDFSETTINGS=/prepress -dNOPAUSE -dQUIET -dBATCH \
     -sOutputFile=output.pdf input.pdf
  ```

**Problem: Manuscript Central upload fails**
- Try different browser (Chrome recommended)
- Clear browser cache
- Check file size < 50 MB
- Ensure PDF is not password-protected

---

## 📚 Additional Resources

### IEEE Guidelines
- **Author Guidelines:** https://www.comsoc.org/publications/magazines/ieee-communications-standards-magazine/author-guidelines
- **Graphics Guidelines:** https://ieeeauthorcenter.ieee.org/create-your-ieee-article/create-graphics-for-your-article/
- **Reference Format:** https://ieeeauthorcenter.ieee.org/wp-content/uploads/IEEE-Reference-Guide.pdf
- **Graphics Checker:** https://graphicsqc.ieee.org/

### Tools and Software
- **Overleaf:** https://www.overleaf.com/ (online LaTeX editor)
- **Pandoc:** https://pandoc.org/ (document converter)
- **Graphviz:** https://graphviz.org/ (graph visualization)
- **draw.io:** https://app.diagrams.net/ (diagram editor)

### References and Citations
- **IEEE Xplore:** https://ieeexplore.ieee.org/ (search papers)
- **Google Scholar:** https://scholar.google.com/ (find citations)
- **Connected Papers:** https://www.connectedpapers.com/ (explore related work)

### ORCID
- **Register:** https://orcid.org/register
- **Guide:** https://info.orcid.org/researchers/

---

## 📞 Support

### Technical Support
- **Manuscript Central:** support@scholarone.com, +1-888-503-1050
- **IEEE Editorial Office:** comsm@comsoc.org

### Questions?
If you encounter issues not covered in this guide:
1. Check `figures/README.md` for figure-specific issues
2. Review `SUBMISSION_CHECKLIST.md` for requirements
3. Consult `FIGURES_GUIDE.md` for design specifications
4. Contact Manuscript Central technical support

---

**Status:** ✅ All build scripts and documentation complete
**Next Action:** Generate figures, then PDF, then submit!
**Deadline:** December 15, 2025 (23:59 local time)

**Good luck with your submission!** 🚀
