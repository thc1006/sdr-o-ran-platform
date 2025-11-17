# IEEE ICC 2026 Paper Submission Checklist

## Pre-Submission Checklist for GPU-Accelerated NTN-O-RAN Platform

**Target Conference:** IEEE ICC 2026 (June 2026, Montreal, Canada)

**Deadline:** October 2025

**Paper ID:** [To be assigned after submission]

---

## 1. Content Completeness

### Abstract
- [ ] Abstract written (200 words max)
- [ ] All 5 key contributions mentioned
- [ ] Main results included (99.7% handover, 93% compression, etc.)
- [ ] Statistical significance mentioned (p<0.001)
- [ ] No undefined abbreviations on first use

### Introduction
- [ ] Motivation clearly stated (6G, NTN, O-RAN)
- [ ] Problem statement well-defined
- [ ] 4 key challenges described (Doppler, delay, handover, rain)
- [ ] Solution overview provided
- [ ] 5 novel contributions highlighted
- [ ] Paper organization paragraph included

### Related Work
- [ ] 3GPP NTN standards covered (Rel-17, 18, 19)
- [ ] O-RAN architecture explained
- [ ] E2 interface and service models described
- [ ] Existing simulation tools compared (ns-3, OMNeT++, MATLAB)
- [ ] OpenNTN and Sionna discussed
- [ ] Gap analysis showing our novelty
- [ ] Clear positioning vs. state-of-the-art

### System Design
- [ ] Overall architecture diagram (Fig. 1) referenced
- [ ] 6 core components described
- [ ] OpenNTN channel models explained with equations
- [ ] SGP4 orbit propagation detailed
- [ ] E2SM-NTN specification complete (33 KPMs, 6 triggers, 6 actions)
- [ ] ASN.1 PER encoding described (93% reduction)
- [ ] Predictive vs. reactive handover comparison
- [ ] Weather-aware power control with ITU-R P.618
- [ ] All equations numbered and referenced

### Implementation
- [ ] Technology stack table complete
- [ ] Standards compliance documented
- [ ] Development approach explained (11 agents)
- [ ] Code statistics provided (30,412 lines, 86 files)
- [ ] Test coverage mentioned (85%)
- [ ] Docker containerization described (5 services)
- [ ] Performance optimizations detailed

### Experimental Results
- [ ] Simulation setup clearly described
  - [ ] 100 UEs, 60-minute duration
  - [ ] 8,805 Starlink satellites
  - [ ] 3 weather scenarios
  - [ ] All parameters listed
- [ ] Handover performance table included (Table II)
- [ ] Power control results presented
- [ ] User experience metrics table (Table III)
- [ ] Weather scenario results table (Table IV)
- [ ] Statistical analysis complete
  - [ ] p-values for all metrics
  - [ ] Effect sizes (Cohen's d, Cramér's V)
  - [ ] 95% confidence intervals
  - [ ] Statistical significance table (Table V)
- [ ] All claims supported by data or references

### Conclusion
- [ ] Summary of contributions
- [ ] Key achievements listed (5.5ms latency, 600 msg/sec, etc.)
- [ ] Impact assessment (academic + industry)
- [ ] Future work (short, medium, long-term)
- [ ] Open-source release mentioned

### References
- [ ] 40+ references included
- [ ] All in-text citations have bibliography entries
- [ ] No [?] or missing references
- [ ] References formatted in IEEE style
- [ ] Recent papers (2022-2024) from ICC/INFOCOM/GLOBECOM
- [ ] 3GPP standards cited (TR38.811, TR38.821, TR38.863)
- [ ] O-RAN specs cited (E2AP, E2SM)
- [ ] ITU-R recommendations cited (P.618, P.837, P.838)
- [ ] OpenNTN and Sionna papers cited

---

## 2. Formatting Compliance

### IEEE Format
- [ ] IEEEtran class used (\documentclass[conference]{IEEEtran})
- [ ] Double-column format
- [ ] 10pt font size (default)
- [ ] Letter size paper (8.5" × 11")
- [ ] Margins correct (IEEE default)
- [ ] Page numbering disabled (IEEE will add)

### Page Limit
- [ ] Total pages ≤ 6 (including references)
- [ ] Current page count: ____ pages
- [ ] If > 6 pages, reduce content or use overlength page charges

### Title and Authors
- [ ] Title concise and descriptive
- [ ] Title case (capitalize major words)
- [ ] Authors listed (or "Anonymous Authors" for blind review)
- [ ] Affiliations provided (or omitted for blind review)
- [ ] Email addresses (or omitted for blind review)

### Abstract and Keywords
- [ ] Abstract ≤ 200 words
- [ ] 5-8 keywords listed
- [ ] Keywords relevant to paper content

### Section Headings
- [ ] All sections numbered (I, II, III, ...)
- [ ] Subsections numbered (A, B, C, ...)
- [ ] Sub-subsections numbered (1, 2, 3, ...)
- [ ] Consistent capitalization
- [ ] No orphan headings (heading at bottom of column)

### Equations
- [ ] All equations numbered
- [ ] Equations centered
- [ ] Variables defined on first use
- [ ] Math notation consistent throughout
- [ ] No display math without equation numbers (unless single-line)

### Figures
- [ ] All figures referenced in text
- [ ] Figure captions below figures
- [ ] Figures numbered (Fig. 1, Fig. 2, ...)
- [ ] Figure quality: vector PDFs (not rasterized)
- [ ] Font size in figures readable (≥ 8pt)
- [ ] Color/grayscale both acceptable
- [ ] Figures fit within column width (or span two columns)

### Tables
- [ ] All tables referenced in text
- [ ] Table captions above tables
- [ ] Tables numbered (Table I, Table II, ...)
- [ ] Table formatting: \toprule, \midrule, \bottomrule (booktabs)
- [ ] Tables fit within column width
- [ ] Font size readable (≥ 8pt, use \scriptsize if needed)

### Citations
- [ ] Citation style: IEEE [1], [2], [3]
- [ ] Citations in numerical order
- [ ] Multiple citations sorted: [1], [3], [5] not [5], [1], [3]
- [ ] Ranges: [1]--[5] not [1, 2, 3, 4, 5]
- [ ] Citations before punctuation: "...as shown in [1]." not "...as shown in. [1]"

### Abbreviations
- [ ] All abbreviations defined on first use
- [ ] Consistent abbreviation usage
- [ ] Common abbreviations: NTN, LEO, O-RAN, E2, SGP4, KPM, etc.
- [ ] No abbreviations in abstract unless widely known

---

## 3. Figure Quality

### Architecture Diagram (Fig. 1)
- [ ] Created as vector PDF
- [ ] Resolution: 300 dpi minimum if rasterized
- [ ] All text readable
- [ ] Legend/labels clear
- [ ] Colors distinguishable (or use patterns for B&W)
- [ ] File size reasonable (<5 MB)

### Handover Comparison (Fig. 2)
- [ ] Bar chart or grouped bar chart
- [ ] Error bars showing 95% CI or standard deviation
- [ ] Axes labeled with units
- [ ] Legend clear
- [ ] Reactive vs. Predictive clearly distinguished

### Throughput Comparison (Fig. 3)
- [ ] Line plot showing time series
- [ ] Two lines: Reactive, Predictive
- [ ] Handover events marked (optional)
- [ ] Axes labeled with units
- [ ] Legend clear

### Power Efficiency (Fig. 4)
- [ ] Box plots or bar chart
- [ ] Shows distribution (median, quartiles)
- [ ] Reactive vs. Predictive comparison
- [ ] Axes labeled with units

### Rain Fade Mitigation (Fig. 5)
- [ ] Stacked or grouped bar chart
- [ ] Three weather scenarios: Clear, Rain, Storm
- [ ] Success rates shown
- [ ] Legend clear

### General Figure Checks
- [ ] All figures in figures/ directory
- [ ] File names match LaTeX: architecture_diagram.pdf, etc.
- [ ] PDF format (preferred) or high-res PNG/EPS
- [ ] No unnecessary white space
- [ ] Aspect ratios appropriate
- [ ] Consistent style across all figures

---

## 4. Table Quality

### Table I: E2SM-NTN KPMs
- [ ] 33 KPMs categorized
- [ ] Units specified
- [ ] Formatting consistent
- [ ] Readable at IEEE column width

### Table II: Handover Performance
- [ ] Metrics, Reactive, Predictive, Improvement, p-value columns
- [ ] All values with proper precision
- [ ] Statistical significance indicated

### Table III: User Experience Metrics
- [ ] Throughput, Latency, Packet Loss, Uptime
- [ ] Mean ± std dev format
- [ ] Improvement percentages
- [ ] p-values

### Table IV: Weather Scenarios
- [ ] Clear, Rain, Storm scenarios
- [ ] Multiple metrics per scenario
- [ ] Reactive vs. Predictive comparison

### Table V: Statistical Summary
- [ ] All metrics listed
- [ ] p-values, significance level, effect sizes
- [ ] Legend explaining significance levels

### General Table Checks
- [ ] All tables use booktabs style (\toprule, \midrule, \bottomrule)
- [ ] No vertical lines (IEEE style)
- [ ] Centered columns for numbers
- [ ] Left-aligned for text
- [ ] Bold for headers
- [ ] Proper alignment

---

## 5. Language and Style

### Grammar and Spelling
- [ ] No spelling errors (run spell check)
- [ ] No grammatical errors (run grammar check)
- [ ] Consistent tense (past for results, present for facts)
- [ ] Active voice preferred over passive
- [ ] No colloquialisms or informal language

### Technical Writing
- [ ] Clear and concise sentences
- [ ] No ambiguous pronouns (it, this, that)
- [ ] Avoid excessive jargon
- [ ] Define technical terms on first use
- [ ] Logical flow between paragraphs
- [ ] No orphan paragraphs (single-line at top/bottom of page)

### Consistency
- [ ] Terminology consistent (e.g., "handover" not "hand-over" or "hand over")
- [ ] Units consistent (ms not milliseconds, dB not decibels)
- [ ] Notation consistent (elevation angle: θ throughout)
- [ ] Capitalization consistent (E2 Interface, not E2 interface)

### Clarity
- [ ] All claims supported by evidence or citations
- [ ] No vague statements ("very good", "much better")
- [ ] Quantify improvements ("+14.2%" not "significant")
- [ ] Use specific values, not ranges ("5.5ms" not "5-6ms")

---

## 6. References and Citations

### Reference Quality
- [ ] All references accessible (DOI, URL, or standard number)
- [ ] All references in English or with English translation
- [ ] All references properly formatted (IEEE style)
- [ ] Conference papers: authors, title, booktitle, year, pages
- [ ] Journal articles: authors, title, journal, year, volume, number, pages
- [ ] Technical reports: organization, number, year
- [ ] Books: authors, title, publisher, year, ISBN (optional)

### Citation Coverage
- [ ] All sections have citations (no "naked" claims)
- [ ] Recent citations (50%+ from last 5 years)
- [ ] Diverse sources (not all from one venue)
- [ ] Self-citations minimal (<20%)
- [ ] Competing approaches cited fairly

### BibTeX Quality
- [ ] All BibTeX entries complete
- [ ] No duplicate entries
- [ ] No unused entries (if any, remove)
- [ ] Special characters escaped (e.g., \& for &)
- [ ] Titles in title case or sentence case (consistent)

---

## 7. Reproducibility

### Code Availability
- [ ] Code mentioned as open-source
- [ ] Repository URL provided (or "to be released")
- [ ] Code version/commit hash (optional)
- [ ] License mentioned (MIT)

### Data Availability
- [ ] TLE data source cited (CelesTrak)
- [ ] Simulation parameters clearly listed
- [ ] Random seed fixed for reproducibility
- [ ] Configuration files available

### Experimental Details
- [ ] All parameters specified
- [ ] Software versions listed (TensorFlow, Sionna, etc.)
- [ ] Hardware requirements mentioned (GPU)
- [ ] Sufficient detail to replicate experiments

---

## 8. Ethical Compliance

### Authorship
- [ ] All authors contributed significantly
- [ ] Author order agreed upon
- [ ] No ghost authors or honorary authorship
- [ ] Corresponding author designated

### Plagiarism
- [ ] No text copied without quotation/citation
- [ ] Paraphrased content cited
- [ ] Self-plagiarism avoided (if extending prior work, cite it)
- [ ] Plagiarism check run (Turnitin, iThenticate)
- [ ] Similarity score acceptable (<20%)

### Data Integrity
- [ ] No fabricated data
- [ ] No manipulated figures
- [ ] Statistical analysis correct
- [ ] No selective reporting (report all relevant results)

### Conflicts of Interest
- [ ] Funding sources acknowledged
- [ ] No undisclosed conflicts of interest
- [ ] Open-source tools cited properly

---

## 9. IEEE PDF eXpress Validation

### Pre-Validation
- [ ] PDF generated successfully
- [ ] PDF opens without errors
- [ ] All fonts embedded
- [ ] File size <10 MB (IEEE limit)
- [ ] PDF version 1.4 or later

### PDF eXpress Steps
1. [ ] Create IEEE PDF eXpress account
2. [ ] Use conference ID: [ICC 2026 ID - TBA]
3. [ ] Upload PDF for validation
4. [ ] Fix any errors reported
5. [ ] Download IEEE-compliant PDF
6. [ ] Verify compliant PDF renders correctly

### Common PDF Issues
- [ ] Missing fonts (embed all fonts)
- [ ] RGB vs. CMYK colors (both acceptable)
- [ ] Incorrect page size (should be Letter)
- [ ] Security restrictions (should be none)
- [ ] Bookmarks/hyperlinks (acceptable)

---

## 10. Submission Portal

### EDAS Registration
- [ ] Create EDAS account (if not existing)
- [ ] Verify email address
- [ ] Complete profile
- [ ] Add co-authors to EDAS

### Paper Upload
- [ ] Log in to EDAS
- [ ] Select "ICC 2026"
- [ ] Click "Submit New Paper"
- [ ] Upload PDF (IEEE-compliant version)
- [ ] Enter title (exactly as in PDF)
- [ ] Enter abstract (exactly as in PDF)
- [ ] Select topics/keywords
- [ ] Add all authors with emails
- [ ] Agree to IEEE policies
- [ ] Submit before deadline

### After Submission
- [ ] Confirmation email received
- [ ] Paper ID noted: _______________
- [ ] PDF verified in system
- [ ] Authors can access submission

---

## 11. Final Checks Before Submission

### Content
- [ ] Read paper aloud for flow
- [ ] Check all numbers match between text and tables
- [ ] Verify all claims have evidence
- [ ] Ensure contributions are clear
- [ ] Check conclusion summarizes properly

### Formatting
- [ ] Compile LaTeX without errors
- [ ] Compile LaTeX without warnings (or all warnings explained)
- [ ] Page limit: 6 pages ✓
- [ ] Figures render correctly in PDF
- [ ] Tables formatted properly

### Quality
- [ ] Spell check run (make check)
- [ ] Grammar check run (Grammarly or similar)
- [ ] Peer review by colleague (optional but recommended)
- [ ] PDF eXpress validation passed

### Metadata
- [ ] Title correct
- [ ] Authors correct (or anonymous for blind review)
- [ ] Keywords appropriate
- [ ] Affiliations correct (or omitted)

---

## 12. Timeline

### 3 Months Before Deadline (July 2025)
- [ ] Complete first draft
- [ ] Create all figures
- [ ] Gather all references
- [ ] Run preliminary experiments

### 2 Months Before Deadline (August 2025)
- [ ] Internal review by co-authors
- [ ] Revise based on feedback
- [ ] Finalize figures and tables
- [ ] Polish writing

### 1 Month Before Deadline (September 2025)
- [ ] Final experiments and data analysis
- [ ] Complete all sections
- [ ] Proofread thoroughly
- [ ] Run plagiarism check

### 2 Weeks Before Deadline (Mid-October 2025)
- [ ] PDF eXpress validation
- [ ] Final formatting check
- [ ] Backup submission (in case of issues)

### 1 Week Before Deadline (Late October 2025)
- [ ] Register on EDAS
- [ ] Prepare submission metadata
- [ ] Final author approval
- [ ] Ready to submit

### Day of Deadline (October 2025)
- [ ] Submit paper via EDAS
- [ ] Receive confirmation
- [ ] Save confirmation email
- [ ] Backup PDF stored safely

---

## 13. Post-Submission

### Immediate (Same Day)
- [ ] Confirmation email saved
- [ ] Paper ID recorded
- [ ] Co-authors notified of submission
- [ ] Submission PDF archived

### Review Period (October 2025 - February 2026)
- [ ] Monitor EDAS for updates
- [ ] Prepare rebuttal (if reviews request clarifications)
- [ ] Plan camera-ready revisions (if accepted)

### If Accepted (February 2026)
- [ ] Celebrate! 🎉
- [ ] Address reviewer comments
- [ ] Prepare camera-ready version
- [ ] Submit camera-ready by April 2026
- [ ] Register for conference
- [ ] Prepare presentation
- [ ] Book travel to Montreal

### If Rejected (February 2026)
- [ ] Read reviews carefully
- [ ] Revise paper based on feedback
- [ ] Submit to backup venue (IEEE GLOBECOM 2026, etc.)
- [ ] Do not be discouraged - rejection is common

---

## 14. Emergency Contacts

### Technical Issues
- **IEEE PDF eXpress:** support@pdf-express.org
- **EDAS Support:** help@edas.info
- **LaTeX Issues:** TeX StackExchange (https://tex.stackexchange.com)

### Conference Organizers
- **ICC 2026 Website:** https://icc2026.ieee-icc.org
- **Technical Program Chairs:** (check website)
- **Publication Chairs:** (check website)

---

## Summary Statistics

### Current Status
- **Sections Complete:** 6/6 (100%)
- **Figures Complete:** 0/5 (0%) - Placeholder PDFs needed
- **Tables Complete:** 5/5 (100%)
- **References Complete:** 40/40 (100%)
- **Page Count:** 6 pages (target: ≤6)
- **Word Count:** ~4,800 words
- **Compilation:** ✓ Success (no errors)

### Critical Path Items
1. **HIGH PRIORITY:** Create 5 figure PDFs
2. **HIGH PRIORITY:** Run IEEE PDF eXpress validation
3. **MEDIUM PRIORITY:** Spell/grammar check
4. **MEDIUM PRIORITY:** Plagiarism check
5. **LOW PRIORITY:** Peer review (optional)

### Estimated Time to Submission-Ready
- Figure creation: 4-8 hours
- Final proofreading: 2-4 hours
- PDF eXpress: 1-2 hours
- Total: **7-14 hours of work**

---

## Sign-Off

**Lead Author:** _________________ Date: _______

**Co-Authors:**
- _________________ Date: _______
- _________________ Date: _______
- _________________ Date: _______

**Final Approval:** All authors have reviewed and approved this submission.

---

**Checklist Version:** 1.0
**Last Updated:** 2025-11-17
**Status:** Ready for final review and figure creation
**Target Submission:** October 2025
**Conference:** IEEE ICC 2026, Montreal, Canada
