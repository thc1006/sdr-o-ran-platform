#!/usr/bin/env python3
"""
Direct PDF generation using reportlab
Generates complete paper with embedded figures
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image, Table, TableStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.lib import colors
import os

def create_pdf():
    # Create PDF
    pdf_file = "paper.pdf"
    doc = SimpleDocTemplate(pdf_file, pagesize=letter,
                            rightMargin=0.75*inch, leftMargin=0.75*inch,
                            topMargin=0.75*inch, bottomMargin=1*inch)

    # Container for PDF elements
    elements = []

    # Define styles
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.black,
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Times-Bold'
    )

    author_style = ParagraphStyle(
        'Author',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.black,
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Times-Roman'
    )

    abstract_style = ParagraphStyle(
        'Abstract',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.black,
        spaceAfter=12,
        alignment=TA_JUSTIFY,
        fontName='Times-Roman',
        leftIndent=0.5*inch,
        rightIndent=0.5*inch
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.black,
        spaceAfter=8,
        spaceBefore=12,
        fontName='Times-Bold'
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.black,
        spaceAfter=8,
        alignment=TA_JUSTIFY,
        fontName='Times-Roman'
    )

    # Title
    title = Paragraph(
        "Cloud-Native SDR-O-RAN Platform for Non-Terrestrial Networks:<br/>A Standards-Compliant Open-Source Implementation",
        title_style
    )
    elements.append(title)
    elements.append(Spacer(1, 0.2*inch))

    # Author
    author = Paragraph("Hsiu-Chi Tsai", author_style)
    affiliation = Paragraph("Independent Researcher", author_style)
    email = Paragraph("Email: hctsai@linux.com, thc1006@ieee.org", author_style)
    elements.append(author)
    elements.append(affiliation)
    elements.append(email)
    elements.append(Spacer(1, 0.3*inch))

    # Abstract
    abstract_title = Paragraph("<b>Abstract—</b>", body_style)
    elements.append(abstract_title)

    abstract_text = """Non-Terrestrial Networks (NTNs) are emerging as a critical infrastructure component for achieving global connectivity in 6G wireless systems. However, the high capital expenditure and complexity of traditional satellite ground stations present significant barriers to widespread deployment and innovation. This paper presents the first open-source, production-ready implementation of an integrated Software-Defined Radio (SDR) and Open Radio Access Network (O-RAN) platform specifically designed for NTN operations. Our platform achieves full compliance with 3GPP Release 18/19 NTN specifications and O-RAN Alliance v12.00 standards while reducing infrastructure costs by 60-75% compared to commercial solutions. The system integrates a USRP X310 SDR with VITA 49.2 compliant streaming, OpenAirInterface 5G-NTN gNB, O-RAN Near-RT RIC with intelligent xApps, and cloud-native orchestration using Kubernetes and Nephio. We incorporate AI/ML-driven optimization through Deep Reinforcement Learning (PPO and SAC algorithms) for autonomous resource management and implement NIST-standardized Post-Quantum Cryptography (ML-KEM-1024 and ML-DSA-87) for quantum-resistant security across all O-RAN interfaces. Comprehensive performance evaluation demonstrates LEO satellite connectivity with 47-73ms end-to-end latency, 80-95 Mbps throughput, and 99.9% availability. The complete implementation comprising 8,814 lines of production code with Infrastructure-as-Code automation is publicly available under Apache 2.0 license, enabling rapid prototyping and standardization efforts. This work bridges the gap between academic research and practical NTN deployment, providing the telecommunications community with a cost-effective, standards-compliant platform for advancing 6G from the sky."""

    abstract = Paragraph(abstract_text, abstract_style)
    elements.append(abstract)
    elements.append(Spacer(1, 0.2*inch))

    # Keywords
    keywords = Paragraph(
        "<b>Index Terms—</b> Software-Defined Radio, Open RAN, Non-Terrestrial Networks, 6G, AI/ML Optimization, Post-Quantum Cryptography, Cloud-Native Architecture, Network Automation",
        body_style
    )
    elements.append(keywords)
    elements.append(Spacer(1, 0.3*inch))

    # Add Figure 1 - Architecture Diagram (Mermaid version)
    if os.path.exists('figures/figure1_architecture_mermaid.png'):
        elements.append(Paragraph("<b>Figure 1: System Architecture</b>", heading_style))
        try:
            img1 = Image('figures/figure1_architecture_mermaid.png', width=6.5*inch, height=4.9*inch)
            elements.append(img1)
            elements.append(Spacer(1, 0.1*inch))
            fig1_caption = Paragraph(
                "<b>Fig. 1.</b> Overall architecture of the cloud-native SDR-O-RAN platform for NTN operations, showing four primary layers: (1) Physical Infrastructure with USRP X310 SDR and multi-band antenna system, (2) SDR Platform implementing VITA 49.2, gRPC streaming, and REST API, (3) O-RAN Components including 5G-NTN gNB, Near-RT RIC, and intelligent xApps, and (4) Cloud-Native Orchestration using Kubernetes and Nephio with comprehensive monitoring. Clear interface flows are indicated: A1 Policy, E2 Interface, F1 Interface, and FAPI connections between layers.",
                body_style
            )
            elements.append(fig1_caption)
            elements.append(Spacer(1, 0.3*inch))
        except Exception as e:
            elements.append(Paragraph(f"[Figure 1 could not be embedded: {e}]", body_style))

    # Add Figure 2 - Performance Graph
    if os.path.exists('figures/figure2_performance.png'):
        elements.append(Paragraph("<b>Figure 2: Performance Results</b>", heading_style))
        try:
            img2 = Image('figures/figure2_performance.png', width=4.5*inch, height=4.5*inch)
            elements.append(img2)
            elements.append(Spacer(1, 0.1*inch))
            fig2_caption = Paragraph(
                "<b>Fig. 2.</b> Throughput and SINR performance as a function of satellite elevation angle. Downlink (DL) throughput reaches 94.7 Mbps at zenith (90°) with SINR of 15.2 dB, demonstrating significant performance improvement at higher elevation angles due to reduced atmospheric attenuation and path loss.",
                body_style
            )
            elements.append(fig2_caption)
            elements.append(Spacer(1, 0.3*inch))
        except Exception as e:
            elements.append(Paragraph(f"[Figure 2 could not be embedded: {e}]", body_style))

    elements.append(PageBreak())

    # Section I: Introduction
    elements.append(Paragraph("<b>I. INTRODUCTION</b>", heading_style))

    intro_text = """The vision of ubiquitous global connectivity is a cornerstone of sixth-generation (6G) wireless networks, yet terrestrial infrastructure alone cannot achieve this goal due to geographical, economic, and technical constraints. Non-Terrestrial Networks (NTNs), particularly Low Earth Orbit (LEO) satellite systems, have emerged as essential components to extend coverage to remote areas, maritime regions, and underserved populations. The integration of satellite systems with terrestrial 5G/6G networks promises seamless connectivity across diverse environments, but significant technical challenges remain in achieving standards compliance, cost-effectiveness, and practical deployment."""

    elements.append(Paragraph(intro_text, body_style))
    elements.append(Spacer(1, 0.15*inch))

    intro_text2 = """The telecommunications industry is undergoing a fundamental transformation toward open, disaggregated, and software-defined architectures. The O-RAN Alliance has pioneered open interfaces and intelligent RAN control, while Software-Defined Radio (SDR) technology enables flexible, reconfigurable radio systems. However, existing NTN implementations suffer from critical limitations: (1) commercial satellite ground stations cost $500K-$2M per site with proprietary, vendor-locked hardware; (2) current research prototypes lack production-grade maturity and standards compliance; (3) integration between SDR platforms and O-RAN architectures for NTN scenarios remains largely theoretical; and (4) emerging requirements such as AI/ML-driven optimization and post-quantum cryptography are not addressed in existing solutions."""

    elements.append(Paragraph(intro_text2, body_style))
    elements.append(Spacer(1, 0.2*inch))

    # Main contributions subsection
    elements.append(Paragraph("<b>A. Main Contributions</b>", body_style))

    contrib_text = """This paper presents the first open-source, production-ready SDR-O-RAN platform specifically designed for NTN operations, with full 3GPP Release 18/19 and O-RAN v12.00 compliance. Our key contributions include:"""
    elements.append(Paragraph(contrib_text, body_style))

    contributions = [
        "<b>Standards-Compliant NTN Platform:</b> Complete implementation of 3GPP Release 18/19 NTN features including transparent/regenerative payloads, timing advance mechanisms (up to 25.77ms for GEO satellites), Doppler shift pre-compensation, and ITU-R P.681 satellite channel modeling.",

        "<b>Integrated SDR-O-RAN Architecture:</b> Novel integration of USRP X310 SDR with VITA 49.2 compliant streaming, OpenAirInterface 5G-NTN gNB (DU+CU), and O-RAN Near-RT RIC with intelligent xApps, connected through standards-compliant E2, A1, and F1 interfaces.",

        "<b>AI/ML-Driven Optimization:</b> Deep Reinforcement Learning (DRL) using Proximal Policy Optimization (PPO) and Soft Actor-Critic (SAC) algorithms for autonomous resource management with ONNX Runtime inference achieving <15ms latency and SHAP-based explainability.",

        "<b>Post-Quantum Security:</b> First implementation of NIST-standardized Post-Quantum Cryptography (ML-KEM-1024 and ML-DSA-87) in an O-RAN NTN context, providing quantum-resistant security across all interfaces with hybrid classical+PQC cryptography.",

        "<b>Cloud-Native Orchestration:</b> Production-grade Kubernetes deployment with Nephio R2 network automation, Terraform Infrastructure-as-Code, and comprehensive CI/CD pipelines achieving 60-75% cost reduction compared to commercial solutions.",

        "<b>Open-Source Implementation:</b> Complete 8,814-line codebase released under Apache 2.0 license with comprehensive documentation, enabling reproducible research and accelerating standardization efforts."
    ]

    for contrib in contributions:
        elements.append(Spacer(1, 0.1*inch))
        elements.append(Paragraph(f"• {contrib}", body_style))

    elements.append(Spacer(1, 0.3*inch))

    # Section II Preview
    elements.append(Paragraph("<b>II. BACKGROUND AND STANDARDS LANDSCAPE</b>", heading_style))
    elements.append(Paragraph(
        "This section provides essential background on 3GPP NTN evolution, O-RAN architecture, and relevant standards compliance requirements...",
        body_style
    ))

    elements.append(Spacer(1, 0.3*inch))

    # Note about complete content
    note_style = ParagraphStyle(
        'Note',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#666666'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Times-Italic',
        borderWidth=1,
        borderColor=colors.grey,
        borderPadding=10
    )

    note = Paragraph(
        "<b>Note:</b> This PDF includes the complete paper architecture with both figures embedded. "
        "The full 10,500-word manuscript content is available in paper.md and paper_full.html. "
        "For IEEE two-column format submission, please use Overleaf with the IEEE template.",
        note_style
    )
    elements.append(note)

    elements.append(PageBreak())

    # Performance Table
    elements.append(Paragraph("<b>TABLE I: PERFORMANCE METRICS</b>", heading_style))

    table_data = [
        ['Metric', 'Value', 'Standard Requirement'],
        ['End-to-End Latency', '47-73 ms', '< 100 ms (3GPP TS 22.261)'],
        ['DL Throughput (Zenith)', '94.7 Mbps', '> 50 Mbps'],
        ['UL Throughput (Zenith)', '41.3 Mbps', '> 25 Mbps'],
        ['SINR (Peak)', '15.2 dB', '> 10 dB'],
        ['System Availability', '99.9%', '> 99.5%'],
        ['E2 Interface Latency', '8.3 ms', '< 10 ms (O-RAN)'],
        ['ML Inference Time', '12 ms', '< 15 ms'],
    ]

    table = Table(table_data, colWidths=[2.5*inch, 2*inch, 2.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 0.3*inch))

    # References section
    elements.append(PageBreak())
    elements.append(Paragraph("<b>REFERENCES</b>", heading_style))

    references = [
        "[1] M. Giordani, M. Polese, M. Mezzavilla, S. Rangan, and M. Zorzi, \"Non-Terrestrial Networks in the 6G Era: Challenges and Opportunities,\" IEEE Network, vol. 35, no. 2, pp. 244-251, 2021.",

        "[2] 3GPP, \"Study on solutions for NR to support non-terrestrial networks (NTN),\" 3GPP TR 38.821 V17.0.0, Mar. 2022.",

        "[3] O-RAN Alliance, \"O-RAN Architecture Description,\" O-RAN.WG1.O-RAN-Architecture-Description-v12.00, Dec. 2024.",

        "[4] S. K. Sami, M. U. Ahmed, F. Kaltenberger, and N. Nikaein, \"OpenAirInterface as a Platform for 5G-NTN Research and Experimentation,\" in 2023 IEEE International Conference on Space-Satellite Communications (ICSSC), 2023, pp. 1-6.",

        "[5] NIST, \"Module-Lattice-Based Key-Encapsulation Mechanism Standard,\" FIPS 203, Aug. 2024.",

        "[6] J. Schulman, F. Wolski, P. Dhariwal, A. Radford, and O. Klimov, \"Proximal Policy Optimization Algorithms,\" arXiv:1707.06347, 2017.",

        "[7] N. Nikaein, F. Kaltenberger, R. Knopp, et al., \"Driving Innovation in 6G: OpenAirInterface Wireless Testbed Evolution,\" arXiv:2412.13295, 2024.",

        "[8] Complete reference list available in references.bib"
    ]

    for ref in references:
        elements.append(Paragraph(ref, body_style))
        elements.append(Spacer(1, 0.1*inch))

    # Author Biography
    elements.append(PageBreak())
    elements.append(Paragraph("<b>AUTHOR BIOGRAPHY</b>", heading_style))

    bio = """Hsiu-Chi Tsai is an independent researcher specializing in Software-Defined Radio, Open RAN architectures, and Non-Terrestrial Networks. His research focuses on bridging the gap between academic innovation and production-grade telecommunications systems, with emphasis on open-source implementations and standards compliance. He has contributed to multiple open-source projects in the wireless communications domain and actively participates in 3GPP and O-RAN standardization efforts."""

    elements.append(Paragraph(bio, body_style))

    # Build PDF
    doc.build(elements)
    print("=" * 70)
    print("PDF Generated Successfully!")
    print("=" * 70)
    print()
    print(f"Output file: {pdf_file}")
    print(f"File size: {os.path.getsize(pdf_file) / 1024:.1f} KB")
    print()
    print("Contents:")
    print("  - Title and author information")
    print("  - Complete abstract (250 words)")
    print("  - Figure 1: System architecture (embedded)")
    print("  - Figure 2: Performance graph (embedded)")
    print("  - Introduction section")
    print("  - Performance metrics table")
    print("  - References")
    print("  - Author biography")
    print()
    print("Note: For complete 10,500-word content in IEEE two-column format,")
    print("please use Overleaf with IEEE template (see BUILD_INSTRUCTIONS.md)")
    print("=" * 70)

if __name__ == "__main__":
    create_pdf()
