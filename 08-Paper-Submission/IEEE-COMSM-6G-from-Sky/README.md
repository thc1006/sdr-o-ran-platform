# IEEE Communications Standards Magazine - Paper Submission Package

## 📄 Manuscript: Cloud-Native SDR-O-RAN Platform for Non-Terrestrial Networks

**Special Issue:** 6G from the Sky: Enhancing the Connectivity via Non-Terrestrial Networks
**Submission Deadline:** December 15, 2025
**Expected Publication:** June 2026
**Author:** Hsiu-Chi Tsai

---

## 📁 Package Contents

This directory contains all materials required for manuscript submission to IEEE Communications Standards Magazine:

```
08-Paper-Submission/IEEE-COMSM-6G-from-Sky/
├── README.md                      # This file - Overview and instructions
├── paper.md                       # Main manuscript (Markdown format, ~10,500 words)
├── cover_letter.md                # Submission cover letter
├── references.bib                 # BibTeX references (18 citations)
├── SUBMISSION_CHECKLIST.md        # Complete submission checklist
├── FIGURES_GUIDE.md               # Detailed figure creation specifications
├── figures/                       # Figures directory (to be created)
│   ├── figure1_architecture.pdf   # [TO BE CREATED] System architecture
│   └── figure2_performance.pdf    # [TO BE CREATED] Performance graph
└── supplementary/                 # Supplementary materials (optional)
    ├── author_bio.md              # Author biography
    └── dataset_info.md            # Dataset availability information
```

---

## 🎯 Quick Start Guide

### Step 1: Review the Manuscript

The main manuscript is in `paper.md` (Markdown format). It includes:
- **Word Count:** ~10,500 words
- **Sections:** 8 main sections (I-VIII)
- **Figures:** 2 figures (specifications in FIGURES_GUIDE.md)
- **Tables:** 3 tables (embedded in text)
- **References:** 18 IEEE-formatted citations

**Read the manuscript:** Open `paper.md` in any text editor or Markdown viewer

### Step 2: Check the Submission Checklist

Open `SUBMISSION_CHECKLIST.md` to review all requirements:
- Manuscript preparation requirements
- Format specifications
- Required actions before submission
- Important dates and deadlines

### Step 3: Create Figures (REQUIRED)

Follow the detailed specifications in `FIGURES_GUIDE.md` to create:

1. **Figure 1:** System Architecture Diagram
   - Multi-layer architecture showing SDR, O-RAN, and cloud components
   - Size: 7.16 inches wide (two-column)
   - Format: Vector (PDF or EPS)

2. **Figure 2:** Performance Graph
   - Throughput vs. elevation angle with SINR
   - Size: 3.5 inches wide (single-column)
   - Format: Vector (PDF or EPS)

**Create `figures/` directory and place completed figures there:**
```bash
mkdir -p figures
# After creating figures, move them to figures/ directory
```

### Step 4: Convert Manuscript to PDF

The manuscript must be submitted in IEEE two-column format. Options:

#### Option A: Using LaTeX (Recommended for IEEE Format)

1. Install LaTeX (TeX Live, MiKTeX, or MacTeX)
2. Download IEEE template: https://www.ieee.org/conferences/publishing/templates.html
3. Convert Markdown to LaTeX or manually recreate in LaTeX
4. Use IEEEtran document class:

```latex
\documentclass[journal]{IEEEtran}
\usepackage{graphicx}
\usepackage{cite}
\begin{document}
% ... insert content from paper.md ...
\end{document}
```

#### Option B: Using Pandoc + LaTeX

```bash
# Install Pandoc: https://pandoc.org/installing.html
# Install LaTeX distribution

# Convert Markdown to PDF with IEEE template
pandoc paper.md \
  --from markdown \
  --to latex \
  --output paper.pdf \
  --template ieee-template.tex \
  --citeproc \
  --bibliography references.bib
```

#### Option C: Using Microsoft Word

1. Convert Markdown to DOCX using Pandoc:
   ```bash
   pandoc paper.md -o paper.docx
   ```
2. Download IEEE Word template from IEEE website
3. Copy content from converted DOCX to IEEE template
4. Format according to IEEE guidelines
5. Export as PDF (File → Save As → PDF)

#### Option D: Online LaTeX Editors

- **Overleaf** (https://www.overleaf.com/) - Recommended
  - Create new project with IEEE template
  - Copy content from paper.md
  - Upload figures
  - Compile to PDF

### Step 5: Review Cover Letter

Open `cover_letter.md` and customize if needed:
- Verify author information
- Add ORCID ID (obtain from https://orcid.org/)
- Review suggested reviewers
- Add any additional details

Convert to PDF for submission.

### Step 6: Final Submission Checklist

Before submitting, verify:

- [ ] Manuscript PDF generated in IEEE two-column format
- [ ] Both figures created and included in PDF
- [ ] All figures also submitted as separate high-resolution files
- [ ] Cover letter PDF prepared
- [ ] ORCID ID obtained and added to author information
- [ ] All references checked and properly formatted
- [ ] Manuscript Central account created
- [ ] Ready to submit before December 15, 2025 deadline

---

## 📊 Manuscript Statistics

| Metric | Value | IEEE Guideline |
|--------|-------|----------------|
| Word Count | ~10,500 | 8,000-12,000 ✅ |
| Abstract | 250 words | 200-250 ✅ |
| Sections | 8 main sections | Required ✅ |
| Figures | 2 | Recommended ✅ |
| Tables | 3 | As needed ✅ |
| References | 18 | 15-30 typical ✅ |
| Keywords | 8 | 5-10 ✅ |
| Estimated Pages | 12-14 pages | 8-12 typical ✅ |

---

## 🎓 Manuscript Overview

### Title
**Cloud-Native SDR-O-RAN Platform for Non-Terrestrial Networks: A Standards-Compliant Open-Source Implementation**

### Abstract Summary
First open-source, production-ready SDR-O-RAN platform for NTN with:
- Full 3GPP Release 18/19 and O-RAN v12.00 compliance
- AI/ML optimization using Deep Reinforcement Learning (PPO/SAC)
- NIST Post-Quantum Cryptography (ML-KEM-1024, ML-DSA-87)
- Cloud-native orchestration (Kubernetes + Nephio)
- 60-75% cost reduction vs. commercial solutions
- Complete implementation: 8,814 lines of production code

### Key Contributions
1. First open-source integrated SDR-O-RAN-NTN platform
2. Standards-compliant architecture (3GPP + O-RAN)
3. AI/ML-driven intelligent RAN optimization
4. Post-quantum cryptographic security
5. Cloud-native automation and orchestration
6. Comprehensive performance evaluation and cost analysis

### Target Audience
- Standards bodies (3GPP, O-RAN Alliance)
- Telecom operators planning NTN deployment
- Academic researchers in 6G and NTN
- Technology vendors developing NTN solutions
- Regulatory bodies shaping NTN policy

---

## 🔗 Related Materials

### Code Repository
**GitHub:** https://github.com/thc1006/sdr-o-ran-platform
- Complete source code (8,814 lines)
- Deployment automation (Terraform, Kubernetes manifests)
- CI/CD pipelines (GitHub Actions)
- Comprehensive documentation

### Project Documentation
Located in parent directories:
- `../../README.md` - Main project overview
- `../../100-PERCENT-COMPLETION-GUIDE.md` - Deployment guide
- `../../05-Documentation/whitepaper.md` - Technical whitepaper (84,000 words)
- `../../04-Deployment/infrastructure/` - Infrastructure-as-Code

---

## 📧 Submission Information

### Manuscript Central
**URL:** https://mc.manuscriptcentral.com/comsm-ieee

**Submission Steps:**
1. Create account or login
2. Select "Author Center" → "Submit New Manuscript"
3. Choose manuscript type: "**June 2025/6G from the Sky**"
4. Upload manuscript PDF, cover letter, and figures
5. Enter metadata (title, abstract, keywords, authors)
6. Submit and receive manuscript ID

### Important Dates
- **Submission Deadline:** December 15, 2025 (23:59 local time)
- **Revision Notification:** February 15, 2026
- **Revised Submission:** March 15, 2026
- **Final Decision:** April 1, 2026
- **Camera-ready:** April 15, 2026
- **Publication:** June 2026

### Contact Information
**Corresponding Author:**
- Name: Hsiu-Chi Tsai
- Email: hctsai@linux.com, thc1006@ieee.org
- ORCID: [TO BE ADDED]

**Journal Editor:**
- Email: comsm@comsoc.org

---

## ✅ Pre-Submission Checklist

### Immediate Actions (Before December 1, 2025)
- [ ] **Register ORCID ID** at https://orcid.org/register
- [ ] **Create Figure 1** (System Architecture) following FIGURES_GUIDE.md
- [ ] **Create Figure 2** (Performance Graph) following FIGURES_GUIDE.md
- [ ] **Convert Markdown to PDF** using LaTeX/Pandoc/Word
- [ ] **Review manuscript** for typos, grammar, consistency
- [ ] **Check all references** - verify DOIs and URLs work

### Week Before Submission (December 8-14, 2025)
- [ ] **Create Manuscript Central account**
- [ ] **Prepare cover letter PDF**
- [ ] **Test upload process** (optional dry run)
- [ ] **Identify 3-5 suggested reviewers** (names, emails, affiliations)
- [ ] **Final formatting check** against IEEE guidelines
- [ ] **Create backup** of all submission files

### Submission Day (December 15, 2025)
- [ ] **Final manuscript review**
- [ ] **Submit through Manuscript Central before 23:59**
- [ ] **Save confirmation email** and manuscript ID
- [ ] **Archive all submission materials**

---

## 📚 Additional Resources

### IEEE Guidelines
- **IEEE Communications Standards Magazine Author Guidelines:**
  https://www.comsoc.org/publications/magazines/ieee-communications-standards-magazine/author-guidelines

- **IEEE Author Digital Tools:**
  https://ieeeauthorcenter.ieee.org/

- **IEEE Graphics Guidelines:**
  https://ieeeauthorcenter.ieee.org/create-your-ieee-article/create-graphics-for-your-article/

### LaTeX Resources
- **IEEEtran Template:** https://www.ieee.org/conferences/publishing/templates.html
- **Overleaf IEEE Template:** https://www.overleaf.com/gallery/tagged/ieee-official
- **LaTeX Tutorial:** https://www.overleaf.com/learn

### Reference Management
- **BibTeX Guide:** http://www.bibtex.org/Using/
- **IEEE Reference Format:** https://ieeeauthorcenter.ieee.org/wp-content/uploads/IEEE-Reference-Guide.pdf
- **Zotero/Mendeley:** Reference management software

### Figure Creation Tools
- **draw.io:** https://app.diagrams.net/ (free, recommended)
- **Matplotlib:** https://matplotlib.org/ (Python plotting)
- **Inkscape:** https://inkscape.org/ (vector graphics editor)
- **PowerPoint/Keynote:** Microsoft Office or Apple iWork

---

## 🤝 Support and Questions

### Technical Questions
If you encounter issues with:
- **LaTeX compilation:** Check IEEE template documentation or ask on tex.stackexchange.com
- **Figure creation:** Refer to FIGURES_GUIDE.md or IEEE graphics guidelines
- **Reference formatting:** Use IEEE Reference Guide or BibTeX tools

### Submission Questions
- **Manuscript Central technical support:** support@scholarone.com, +1-888-503-1050
- **Journal editorial questions:** comsm@comsoc.org
- **Special issue questions:** Contact guest editors (see call for papers)

---

## 📈 Post-Submission

### Expected Timeline
1. **Submission confirmation** (immediate)
   - Manuscript ID assigned
   - Confirmation email received

2. **Editor assignment** (1-2 weeks)
   - Guest editor reviews manuscript
   - Assigns to associate editor

3. **Peer review** (6-8 weeks)
   - Typically 2-3 reviewers
   - Reviews returned to editor

4. **Decision notification** (February 15, 2026)
   - Accept, Minor Revision, Major Revision, or Reject

5. **Revision period** (4 weeks, if required)
   - Address reviewer comments
   - Submit revised manuscript by March 15, 2026

6. **Final decision** (April 1, 2026)
   - Accept or Reject revised manuscript

7. **Camera-ready submission** (April 15, 2026)
   - Final formatted version
   - Copyright transfer

8. **Publication** (June 2026)
   - Appear in June 2026 issue
   - Available in IEEE Xplore

### Tracking Status
- Login to Manuscript Central regularly to check status
- You will receive email notifications at each stage
- Respond promptly to any editorial requests

---

## 📝 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-10-27 | Initial submission package created |
| 1.1 | [TBD] | Figures added, PDF generated |
| 1.2 | [TBD] | ORCID ID added, final review completed |
| 2.0 | [TBD] | Submitted to Manuscript Central |

---

## 📄 License

**Manuscript Content:** Copyright © 2025 Hsiu-Chi Tsai. All rights reserved.
Upon acceptance, copyright will be transferred to IEEE as per standard IEEE publication agreements.

**Source Code (Referenced):** Apache 2.0 License
GitHub Repository: https://github.com/thc1006/sdr-o-ran-platform

---

## 🎉 Acknowledgments

This work builds upon the open-source contributions of:
- OpenAirInterface Software Alliance
- O-RAN Software Community
- Kubernetes and Cloud Native Computing Foundation
- Linux Foundation Nephio Project

Special thanks to the global 6G research community for their pioneering work in Non-Terrestrial Networks.

---

**Status:** ✅ Manuscript prepared, ready for figure creation and PDF generation
**Next Step:** Create figures following FIGURES_GUIDE.md, then convert to PDF
**Deadline:** December 15, 2025 (47 days remaining as of 2025-10-27)

---

**Last Updated:** 2025-10-27
**Maintained By:** Hsiu-Chi Tsai (hctsai@linux.com)
