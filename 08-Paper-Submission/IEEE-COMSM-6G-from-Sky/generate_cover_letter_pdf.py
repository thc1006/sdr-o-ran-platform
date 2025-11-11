#!/usr/bin/env python3
"""Generate cover letter PDF using reportlab"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.lib import colors
import os

def create_cover_letter_pdf():
    # Create PDF
    pdf_file = "cover_letter.pdf"
    doc = SimpleDocTemplate(pdf_file, pagesize=letter,
                            rightMargin=1*inch, leftMargin=1*inch,
                            topMargin=1*inch, bottomMargin=1*inch)

    elements = []
    styles = getSampleStyleSheet()

    # Custom styles
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.black,
        spaceAfter=10,
        alignment=TA_LEFT,
        fontName='Times-Roman'
    )

    # Read cover letter content
    with open('cover_letter.md', 'r', encoding='utf-8') as f:
        content = f.read()

    # Add date and recipient
    elements.append(Paragraph("October 27, 2025", normal_style))
    elements.append(Spacer(1, 0.3*inch))

    elements.append(Paragraph("IEEE Communications Standards Magazine", normal_style))
    elements.append(Paragraph("Editorial Office", normal_style))
    elements.append(Paragraph("Special Issue: 6G from the Sky", normal_style))
    elements.append(Spacer(1, 0.3*inch))

    elements.append(Paragraph("<b>Subject: Manuscript Submission - Cloud-Native SDR-O-RAN Platform for Non-Terrestrial Networks</b>", normal_style))
    elements.append(Spacer(1, 0.2*inch))

    elements.append(Paragraph("Dear Editor-in-Chief and Editorial Team,", normal_style))
    elements.append(Spacer(1, 0.15*inch))

    # Main body paragraphs
    paragraphs = [
        "I am pleased to submit our manuscript titled \"Cloud-Native SDR-O-RAN Platform for Non-Terrestrial Networks: A Standards-Compliant Open-Source Implementation\" for consideration in the special issue \"6G from the Sky: Enhancing the Connectivity via Non-Terrestrial Networks\" of IEEE Communications Standards Magazine.",

        "This work presents the first open-source, production-ready implementation integrating Software-Defined Radio (SDR) and Open Radio Access Network (O-RAN) technologies specifically designed for Non-Terrestrial Network (NTN) operations. Our platform achieves full compliance with 3GPP Release 18/19 NTN specifications and O-RAN Alliance v12.00 standards while reducing infrastructure costs by 60-75% compared to commercial solutions.",

        "<b>Key Contributions:</b>",

        "1. <b>Standards-Compliant NTN Implementation:</b> Complete realization of 3GPP Release 18/19 NTN features including transparent/regenerative payloads, timing advance mechanisms (up to 25.77ms for GEO), Doppler pre-compensation, and ITU-R P.681 satellite channel modeling.",

        "2. <b>Integrated SDR-O-RAN Architecture:</b> Novel integration of USRP X310 SDR with VITA 49.2 streaming, OpenAirInterface 5G-NTN gNB, and O-RAN Near-RT RIC with intelligent xApps through standards-compliant E2, A1, and F1 interfaces.",

        "3. <b>AI/ML-Driven Optimization:</b> Deep Reinforcement Learning (PPO and SAC algorithms) achieving <15ms inference latency with SHAP-based explainability for autonomous resource management.",

        "4. <b>Post-Quantum Security:</b> First implementation of NIST-standardized PQC (ML-KEM-1024 and ML-DSA-87) in O-RAN NTN context with hybrid classical+PQC cryptography.",

        "5. <b>Cloud-Native Orchestration:</b> Production-grade Kubernetes deployment with Nephio R2 automation and Terraform Infrastructure-as-Code.",

        "6. <b>Open-Source Release:</b> Complete 8,814-line codebase under Apache 2.0 license with comprehensive documentation.",

        "<b>Relevance to Special Issue:</b>",

        "Our work directly addresses the special issue's focus on NTN integration with terrestrial networks for global 6G connectivity. By providing a cost-effective, standards-compliant, open-source platform, we enable broader research community participation in NTN standardization and deployment. The platform demonstrates practical LEO satellite connectivity with 47-73ms latency, 80-95 Mbps throughput, and 99.9% availability, bridging the gap between academic research and production deployment.",

        "<b>Suggested Reviewers:</b>",

        "We respectfully suggest the following experts as potential reviewers:",

        "1. <b>Dr. Marco Giordani</b> (University of Padova) - Expert in NTN and 6G systems<br/>Email: giordani@dei.unipd.it",

        "2. <b>Dr. Navid Nikaein</b> (EURECOM / OpenAirInterface) - OpenAirInterface architect<br/>Email: navid.nikaein@eurecom.fr",

        "3. <b>Dr. Sundeep Rangan</b> (NYU Wireless) - Expert in mmWave and NTN<br/>Email: srangan@nyu.edu",

        "4. <b>Dr. Ashutosh Dutta</b> (Johns Hopkins University APL) - O-RAN and network automation<br/>Email: ashutosh.dutta@jhuapl.edu",

        "5. <b>Dr. Chih-Lin I</b> (China Mobile Research Institute) - 6G and O-RAN standardization<br/>Email: icl@chinamobile.com",

        "<b>Author Information:</b>",

        "<b>Hsiu-Chi Tsai</b> (Corresponding Author)<br/>Independent Researcher<br/>Email: hctsai@linux.com, thc1006@ieee.org<br/>ORCID: [To be provided upon acceptance]",

        "I confirm that this manuscript is original work, has not been published elsewhere, and is not under consideration by any other journal. All authors have approved the manuscript and agree with its submission to IEEE Communications Standards Magazine.",

        "Thank you for considering our manuscript. We look forward to your response and are happy to provide any additional information required.",

        "Sincerely,",

        "Hsiu-Chi Tsai<br/>Corresponding Author<br/>Email: hctsai@linux.com"
    ]

    for para in paragraphs:
        elements.append(Paragraph(para, normal_style))
        elements.append(Spacer(1, 0.1*inch))

    # Build PDF
    doc.build(elements)

    print("=" * 70)
    print("Cover Letter PDF Generated Successfully!")
    print("=" * 70)
    print()
    print(f"Output file: {pdf_file}")
    print(f"File size: {os.path.getsize(pdf_file) / 1024:.1f} KB")
    print()
    print("=" * 70)

if __name__ == "__main__":
    create_cover_letter_pdf()
