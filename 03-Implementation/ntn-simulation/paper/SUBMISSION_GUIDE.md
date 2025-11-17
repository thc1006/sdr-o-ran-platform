# IEEE ICC 2026 Submission Guide

## Complete Guide to Submitting Your Paper to IEEE ICC 2026

**Conference:** IEEE International Conference on Communications (ICC) 2026

**Location:** Montreal, Canada

**Dates:** June 9-13, 2026

**Website:** https://icc2026.ieee-icc.org

---

## Important Dates

| Milestone | Date | Notes |
|-----------|------|-------|
| Paper Submission Deadline | **October 2025** | TBD - check website |
| Notification of Acceptance | February 2026 | 4 months after submission |
| Camera-Ready Deadline | April 2026 | 2 months before conference |
| Early Registration Deadline | April 2026 | Reduced registration fee |
| Conference Dates | June 9-13, 2026 | Montreal, Canada |

**Note:** All deadlines are 23:59:59 AoE (Anywhere on Earth) = UTC-12

---

## Conference Overview

### IEEE ICC 2026

IEEE International Conference on Communications (ICC) is a flagship IEEE conference covering all aspects of communications.

**Scope:** Communications theory, wireless networks, network protocols, security, IoT, satellite communications, O-RAN, 6G, and more.

**Acceptance Rate:** ~35-40% (competitive)

**Attendees:** ~1,500-2,000 researchers, engineers, industry professionals

**Proceedings:** IEEE Xplore Digital Library (indexed by major databases)

### Why ICC for Our Paper

1. **Relevance:** ICC has strong tracks on:
   - Wireless Communications (our primary track)
   - Satellite & Space Communications (NTN focus)
   - Next Generation Networking (O-RAN, 6G)

2. **Visibility:** High-impact venue for communications research

3. **Timing:** June 2026 conference allows for timely dissemination

4. **Networking:** Opportunity to meet O-RAN Alliance, satellite operators

---

## Submission Requirements

### Paper Format

- **Template:** IEEE Conference Template (IEEEtran class)
- **Columns:** 2-column format
- **Font:** 10pt Times Roman or similar
- **Page Limit:** **6 pages** (including references)
  - Overlength pages allowed with fee: $200/page (max 2 extra pages)
  - **Recommendation:** Stay within 6 pages

### File Format

- **Format:** PDF only
- **Size:** Maximum 10 MB
- **Validation:** Must pass IEEE PDF eXpress check
- **Fonts:** All fonts embedded
- **Security:** No password protection

### Review Process

- **Type:** Double-blind peer review
- **Reviewers:** 3-4 expert reviewers per paper
- **Anonymization Required:**
  - Remove author names and affiliations
  - Use "Anonymous Authors" placeholder
  - Remove identifying information (project names, funding, affiliations)
  - Anonymize citations to own work: "In [1], the authors proposed..."
  - Anonymize repository URLs (use "code will be released upon acceptance")

---

## Step-by-Step Submission Process

### Phase 1: Pre-Submission (2-3 months before deadline)

#### Step 1: Complete the Paper

- [ ] Write all sections
- [ ] Create all figures (5 figures for our paper)
- [ ] Complete all tables (5 tables included)
- [ ] Add 40+ references
- [ ] Ensure 6-page limit
- [ ] Anonymize for double-blind review

#### Step 2: Internal Review

- [ ] Co-author review
- [ ] Peer review (optional but recommended)
- [ ] Revise based on feedback
- [ ] Proofread carefully

#### Step 3: Technical Validation

- [ ] Compile LaTeX successfully (make)
- [ ] Verify all figures render correctly
- [ ] Check all references resolve
- [ ] Run spell checker
- [ ] Run grammar checker (Grammarly, LanguageTool)

---

### Phase 2: PDF Preparation (1 month before deadline)

#### Step 4: Generate Initial PDF

```bash
cd paper/
make clean
make
# Output: ntn_oran_icc2026.pdf
```

Verify:
- [ ] 6 pages (or less)
- [ ] All figures visible
- [ ] All tables formatted correctly
- [ ] References complete
- [ ] Anonymized (no author names)

#### Step 5: IEEE PDF eXpress Validation

**What is PDF eXpress?**
IEEE PDF eXpress is a free service that checks and converts PDFs to IEEE Xplore-compatible format.

**Instructions:**

1. **Create Account** (if first time)
   - Go to: https://ieee-pdf-express.org
   - Click "New Users - Click Here"
   - Enter Conference ID: **[ICC 2026 ID - TBA, usually like "icc2026"]**
   - Create account with email and password

2. **Log In**
   - Use Conference ID: **[ICC 2026 ID]**
   - Enter email and password

3. **Upload PDF**
   - Click "Create New Title"
   - Enter paper title (optional, for tracking)
   - Upload `ntn_oran_icc2026.pdf`
   - Click "Upload PDF for Checking"

4. **Wait for Validation** (usually 5-30 minutes)
   - Check email for results
   - If errors, fix and re-upload
   - If success, download IEEE-compliant PDF

5. **Common Errors and Fixes**

   | Error | Fix |
   |-------|-----|
   | Fonts not embedded | Use `make` (LaTeX auto-embeds fonts) |
   | Wrong page size | Should be Letter (8.5"×11"), check LaTeX |
   | PDF version too old | Update LaTeX distribution |
   | File too large | Compress figures, use vector PDFs |
   | Security restrictions | Remove passwords, use `qpdf --decrypt` |

6. **Download Compliant PDF**
   - Save as `ntn_oran_icc2026_compliant.pdf`
   - Verify it opens correctly
   - This is the file to submit to EDAS

---

### Phase 3: EDAS Submission (deadline week)

#### Step 6: Register on EDAS

**What is EDAS?**
EDAS (Editor's Assistant) is the submission system used by IEEE ICC.

**Registration:**

1. Go to: https://edas.info
2. Click "I am a new user"
3. Fill in:
   - Email: (use institutional email if possible)
   - Password: (strong password)
   - First Name, Last Name
   - Affiliation: (your university/company)
   - Country
4. Verify email address (check inbox for verification link)

#### Step 7: Add Co-Authors to EDAS

1. Log in to EDAS
2. Go to "People" → "People I Work With"
3. For each co-author:
   - Click "Add Person"
   - Search by email (if they have EDAS account)
   - OR enter manually: Name, Email, Affiliation
   - Save

**Important:** All co-authors must have valid email addresses for notifications.

#### Step 8: Submit Paper via EDAS

**Detailed Steps:**

1. **Log in to EDAS**
   - https://edas.info
   - Use your email and password

2. **Select Conference**
   - Click "Conferences"
   - Find "ICC 2026" (or search)
   - Click "ICC 2026 - International Conference on Communications"

3. **Start New Submission**
   - Click "New Submission" (big green button)
   - Or navigate to "Papers" → "Submit New Paper"

4. **Enter Paper Title**
   - Must match PDF exactly
   - Title case (capitalize major words)
   - Example: "GPU-Accelerated NTN-O-RAN Platform with Predictive Handover and ASN.1-Optimized E2 Interface"

5. **Enter Abstract**
   - Copy-paste from LaTeX (plain text, no formatting)
   - Max 200 words
   - Must match PDF exactly

6. **Select Topics**
   - Primary topic: **Wireless Communications**
   - Secondary topics (check 2-3):
     - [ ] Satellite & Space Communications
     - [ ] Next Generation Networking & Internet
     - [ ] Machine Learning for Communications
     - [ ] 5G/6G Wireless Systems

7. **Add Keywords**
   - Non-Terrestrial Networks
   - O-RAN
   - E2 Interface
   - LEO Satellites
   - Predictive Handover
   - ASN.1 Encoding
   - 6G
   - GPU Acceleration

8. **Add Authors**
   - Click "Add Author"
   - For each author:
     - First Name, Last Name
     - Email (must be valid)
     - Affiliation
     - Country
     - **Contact Author:** Check for corresponding author
   - Order: First author, second author, ..., last author
   - **Important:** For blind review, authors are NOT shown to reviewers

9. **Upload PDF**
   - Click "Choose File"
   - Select `ntn_oran_icc2026_compliant.pdf` (IEEE-validated version)
   - Verify file size < 10 MB
   - Click "Upload"

10. **Additional Information**
    - **Track:** Select appropriate track (e.g., "SAC-06: Satellite & Space Communications Track")
    - **Conflicts of Interest:** Add any conflicts (institutions, collaborators)
    - **Comments to Chairs:** (optional) Any special requests or notes

11. **Review and Agree**
    - Review all information carefully
    - Check boxes:
      - [ ] I agree to IEEE Copyright Policy
      - [ ] I agree to IEEE Code of Ethics
      - [ ] Paper is original work
      - [ ] Paper has not been published elsewhere
      - [ ] All authors approved this submission
    - **Important:** Read policies before agreeing

12. **Submit**
    - Click "Submit" button
    - **Warning:** After submission, you CANNOT change the PDF!
    - You CAN update metadata (authors, abstract) until deadline

13. **Confirmation**
    - Confirmation page appears
    - Note **Paper ID** (e.g., ICC26-XXXX)
    - Confirmation email sent to all authors
    - Save confirmation email

---

### Phase 4: Post-Submission (after submission)

#### Step 9: Verify Submission

- [ ] Confirmation email received by all authors
- [ ] Paper ID recorded: **ICC26-_______**
- [ ] Log back into EDAS and view submission
- [ ] PDF previews correctly in EDAS
- [ ] All authors can access paper

#### Step 10: Monitor Status

**Timeline:**

- **Submission:** October 2025
- **Review Assignment:** November 2025 (1 month after)
- **Reviews Due:** December 2025 - January 2026 (2-3 months after)
- **Notification:** February 2026 (4 months after)

**How to Check Status:**

1. Log in to EDAS
2. Go to "Papers" → "My Papers"
3. Find your paper (ICC26-XXXX)
4. Status shows:
   - "Submitted" → "Under Review" → "Decision: Accept/Reject"

**Email Notifications:**

You'll receive emails for:
- Submission confirmation
- Review assignment
- Decision notification
- Camera-ready instructions (if accepted)

---

## Review Process

### What to Expect

**Timeline:**
- 3-4 expert reviewers assigned
- 6-8 weeks for review
- TPC (Technical Program Committee) discussion
- Final decision by TPC chairs

**Review Criteria:**

Reviewers will assess:

1. **Originality (30%):** Is this novel? First of its kind?
2. **Technical Quality (30%):** Sound methodology? Rigorous evaluation?
3. **Clarity (20%):** Well-written? Clear presentation?
4. **Significance (20%):** Impact on field? Relevance to ICC?

**Score Scale:**
- 6: Top 5% of papers (strong accept)
- 5: Top 15% (accept)
- 4: Top 50% (weak accept)
- 3: Bottom 50% (weak reject)
- 2: Bottom 15% (reject)
- 1: Bottom 5% (strong reject)

**Decision Outcomes:**
- **Accept:** ~35-40% of submissions
- **Reject:** ~60-65% of submissions
- **No "Revise and Resubmit"** at IEEE ICC

### Our Paper's Strengths

1. **Novelty:** First GPU-accelerated O-RAN NTN platform
2. **Completeness:** E2SM-NTN specification, 93% compression, predictive handover
3. **Rigor:** Statistical validation (p<0.001, large effect sizes)
4. **Impact:** Standardization candidate, open-source release
5. **Reproducibility:** 30K+ lines of code, Docker deployment

**Expected Outcome:** Strong accept (score 5-6) based on contributions and rigor.

---

## If Accepted (February 2026)

### Step 11: Celebrate!

- [ ] Celebrate with co-authors! 🎉
- [ ] Share news with department/lab
- [ ] Update CV/resume
- [ ] Plan for conference attendance

### Step 12: Prepare Camera-Ready Version

**Deadline:** April 2026 (2 months before conference)

**Changes Required:**

1. **De-Anonymize:**
   - Add author names and affiliations
   - Add funding acknowledgments
   - Add repository URL (make public)

2. **Address Reviewer Comments:**
   - Read reviews carefully
   - Make required changes
   - Optional changes if time allows
   - Track changes in separate document

3. **Add IEEE Copyright Notice:**
   - Download from EDAS
   - Add to bottom of first page (LaTeX: \IEEEpubid{...})

4. **Finalize Figures:**
   - Ensure all figures are high-quality
   - Check for any issues reviewers mentioned

5. **Update References:**
   - Add any new relevant papers (late 2025/early 2026)
   - Ensure all URLs are working

**Camera-Ready Submission:**

1. Generate final PDF (IEEE PDF eXpress again)
2. Upload to EDAS by deadline
3. Submit IEEE Copyright Form (eCF)
4. Pay publication fee (if any overlength pages)
5. Confirmation email received

### Step 13: Register for Conference

**Deadline:** April 2026 (early registration)

**Registration:**

1. Go to ICC 2026 registration website
2. Select registration type:
   - **Author Registration:** At least one author must register
   - **IEEE Member:** Reduced rate (~$700-800)
   - **Non-Member:** Full rate (~$900-1000)
   - **Student:** Reduced rate (~$400-500)
3. Pay registration fee
4. Receive confirmation and badge

**Important:** Paper will be withdrawn if no author registers!

### Step 14: Prepare Presentation

**Format:** Oral presentation (most ICC papers)

**Time:** 15-20 minutes + 5 minutes Q&A

**Slides:**

1. **Title Slide** (1 slide)
   - Title, authors, affiliations

2. **Motivation** (2 slides)
   - Why NTN-O-RAN integration is important
   - Challenges (Doppler, delay, handover, rain)

3. **Contributions** (1 slide)
   - 5 key contributions (bullet points)

4. **System Design** (3-4 slides)
   - Architecture diagram
   - E2SM-NTN overview
   - Predictive handover algorithm
   - ASN.1 compression

5. **Implementation** (1-2 slides)
   - Technology stack
   - Code statistics (30K lines, 85% coverage)
   - Docker deployment

6. **Experimental Results** (4-5 slides)
   - Handover performance (99.7% vs 87.3%)
   - Power efficiency (15% savings)
   - User experience (23% throughput)
   - Statistical validation (p<0.001)
   - Weather scenarios

7. **Conclusion** (1 slide)
   - Summary of achievements
   - Impact (academic + industry)
   - Future work

8. **Backup Slides** (optional, not presented unless asked)
   - Detailed equations
   - Additional experimental scenarios
   - Code examples

**Total:** 15-20 slides for 15-20 minute talk

**Tips:**

- Practice multiple times
- Time yourself (aim for 18 minutes to have buffer)
- Prepare for questions (reviewers' concerns, future work)
- Bring laptop backup (USB drive with slides)

### Step 15: Travel to Montreal

**Conference Location:** Montreal Convention Centre, Montreal, Canada

**Travel:**

- **Flights:** Book early for best rates
- **Hotel:** ICC usually has negotiated rates at nearby hotels
- **Visa:** Check if you need visa for Canada (apply early!)

**Budget (per person):**

- Registration: $700-1000
- Flights: $500-2000 (depending on origin)
- Hotel: $150-250/night × 4-5 nights = $600-1250
- Meals: $50/day × 5 days = $250
- **Total:** $2,050-4,500 per person

**Funding:**

- Check with department for travel grants
- IEEE ComSoc travel grants (for students)
- Research project funding

---

## If Rejected (February 2026)

### Don't Be Discouraged!

- Rejection is common (60-65% rejection rate)
- Does NOT mean paper is bad
- Often due to:
  - High competition (many strong papers)
  - Reviewer misunderstanding
  - Minor weaknesses fixable in revision

### Step 11: Read Reviews Carefully

- [ ] Read all reviewer comments
- [ ] Identify common concerns
- [ ] Distinguish between major and minor issues
- [ ] Take notes on what to fix

### Step 12: Revise Paper

**Common Reviewer Comments:**

1. **"Novelty unclear"** → Strengthen contribution section
2. **"Insufficient evaluation"** → Add more scenarios/metrics
3. **"Poor writing"** → Proofread, improve clarity
4. **"Missing related work"** → Add more references
5. **"Weak statistical analysis"** → Add more rigor

**Revision Strategy:**

- Address all major comments
- Address minor comments if easy
- Improve clarity throughout
- Add new experiments if needed
- Update related work with latest papers

### Step 13: Submit to Backup Venue

**Option 1: IEEE GLOBECOM 2026**

- **When:** December 2026 (6 months later)
- **Deadline:** April 2026 (2 months after ICC notification)
- **Location:** TBD
- **Similar scope:** Communications, wireless, networking
- **Acceptance rate:** ~40% (similar to ICC)

**Option 2: IEEE WCNC 2027**

- **When:** March 2027 (1 year later)
- **Deadline:** September 2026 (7 months after ICC notification)
- **Location:** TBD
- **Focus:** Wireless networking and communications

**Option 3: ACM MobiCom 2026**

- **When:** October 2026 (4 months later)
- **Deadline:** March 2026 (1 month after ICC notification)
- **Focus:** Mobile computing and networking
- **Acceptance rate:** ~15% (very competitive)
- **Note:** Different community, different style

**Option 4: Journal Submission**

- **IEEE Transactions on Wireless Communications (TWC)**
  - Top-tier journal
  - 6-12 month review
  - No page limit (expand to 12-14 pages)
  - Acceptance rate: ~20%

- **IEEE Communications Magazine**
  - Magazine-style (less technical, more vision)
  - Faster review (3-6 months)
  - Higher acceptance rate (~30%)

**Recommendation:** Try GLOBECOM 2026 first (similar venue, quick turnaround).

---

## Alternative Venues (Backup Options)

### IEEE Conferences

| Conference | Deadline | Date | Location | Focus |
|------------|----------|------|----------|-------|
| GLOBECOM 2026 | April 2026 | Dec 2026 | TBD | Communications |
| WCNC 2027 | Sept 2026 | Mar 2027 | TBD | Wireless |
| PIMRC 2026 | May 2026 | Sept 2026 | TBD | Mobile radio |
| VTC 2026-Fall | April 2026 | Sept 2026 | TBD | Vehicular tech |

### Non-IEEE Conferences

| Conference | Deadline | Date | Location | Focus |
|------------|----------|------|----------|-------|
| ACM MobiCom | March | October | Varies | Mobile computing |
| USENIX NSDI | Sept | April | Varies | Networked systems |
| ACM SIGCOMM | Jan | August | Varies | Networking |

---

## Resources

### IEEE ICC 2026

- **Website:** https://icc2026.ieee-icc.org
- **Call for Papers:** (check website)
- **Submission Portal:** https://edas.info
- **PDF eXpress:** https://ieee-pdf-express.org
- **Contact:** tpc-chairs@icc2026.org

### LaTeX and Writing

- **IEEE Templates:** https://www.ieee.org/conferences/publishing/templates.html
- **IEEEtran Class:** https://www.ctan.org/pkg/ieeetran
- **Overleaf IEEE Template:** https://www.overleaf.com/latex/templates/ieee-conference-template
- **TeX StackExchange:** https://tex.stackexchange.com

### Tools

- **Grammarly:** https://www.grammarly.com (grammar check)
- **Turnitin:** (plagiarism check, via institution)
- **iThenticate:** https://www.ithenticate.com (plagiarism check)
- **Draw.io:** https://app.diagrams.net (figures)
- **Inkscape:** https://inkscape.org (vector graphics)

### Travel

- **Montreal Tourism:** https://www.mtl.org/en
- **Conference Hotels:** (check ICC 2026 website)
- **Visa Information:** https://www.canada.ca/en/immigration-refugees-citizenship/services/visit-canada.html

---

## FAQ

### Q1: Can I submit to multiple conferences simultaneously?

**A:** No! IEEE policy prohibits concurrent submissions. You can only submit to one conference at a time. Wait for rejection before submitting elsewhere.

### Q2: Can I submit the same paper to a conference and journal?

**A:** No! Must be substantially different (>30% new content). Exception: Can submit extended journal version after conference publication.

### Q3: What if I miss the deadline?

**A:** No extensions granted. Submit to next deadline (e.g., GLOBECOM 2026).

### Q4: Can I withdraw my paper after submission?

**A:** Yes, but discouraged. Withdrawals waste reviewer time. Only withdraw if you find a major error.

### Q5: What if reviewers request major changes?

**A:** ICC has no "revise and resubmit". Decision is accept or reject. If rejected, revise for different venue.

### Q6: How many authors can be on the paper?

**A:** No limit, but typical: 3-6 authors. List in order of contribution.

### Q7: Can I change authors after submission?

**A:** You can add/remove authors in metadata until deadline. After deadline, major changes require TPC chair approval.

### Q8: What if one author cannot attend the conference?

**A:** At least one author must register and present. Can be any co-author.

### Q9: What if we have new results after submission?

**A:** Cannot change PDF after submission. If accepted, add to camera-ready version. Mention in presentation.

### Q10: Can I post on arXiv before/after submission?

**A:** Yes! IEEE allows arXiv posting. Recommended: Post after acceptance notification (to avoid scooping).

---

## Contact

### For Paper Content Questions

- **Technical:** See `../WEEK2-FINAL-REPORT.md`
- **Experiments:** See `../baseline/PAPER-RESULTS-SECTION.md`
- **Implementation:** See `../README.md`

### For Submission Questions

- **ICC 2026 TPC Chairs:** tpc-chairs@icc2026.org
- **EDAS Support:** help@edas.info
- **IEEE PDF eXpress:** support@pdf-express.org

### For LaTeX Questions

- **TeX StackExchange:** https://tex.stackexchange.com
- **Local:** See `README.md` in this directory

---

## Final Checklist

Before submission:

- [ ] Paper compiles successfully
- [ ] 6 pages (or less, or pay overlength fee)
- [ ] All figures and tables included
- [ ] All references complete
- [ ] Anonymized for blind review
- [ ] IEEE PDF eXpress validated
- [ ] EDAS account created
- [ ] Co-authors added to EDAS
- [ ] Metadata prepared (title, abstract, keywords)
- [ ] All authors approved submission
- [ ] Backup PDF saved locally
- [ ] Ready to submit!

---

**Good luck with your submission!**

**Remember:**
1. Start early (don't wait until deadline)
2. Proofread carefully
3. Ask colleagues to review
4. Validate with IEEE PDF eXpress
5. Submit 1-2 days before deadline (buffer for issues)

**We believe this paper has strong contributions and rigorous evaluation. It should be a strong accept at ICC 2026!**

---

**Document Version:** 1.0
**Last Updated:** 2025-11-17
**Status:** Ready for use
**Target:** IEEE ICC 2026 (October 2025 submission)
