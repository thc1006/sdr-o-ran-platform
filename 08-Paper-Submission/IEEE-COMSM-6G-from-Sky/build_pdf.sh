#!/bin/bash
# Build script for generating IEEE format PDF from Markdown manuscript
# Supports multiple conversion methods

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "======================================"
echo "IEEE Paper PDF Generation Script"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
check_command() {
    if command -v "$1" &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 found"
        return 0
    else
        echo -e "${RED}✗${NC} $1 not found"
        return 1
    fi
}

# Check for required tools
echo "Checking prerequisites..."
PANDOC_AVAILABLE=false
LATEX_AVAILABLE=false

if check_command pandoc; then
    PANDOC_AVAILABLE=true
fi

if check_command pdflatex || check_command xelatex; then
    LATEX_AVAILABLE=true
fi

echo ""

# Method selection
if [ "$PANDOC_AVAILABLE" = true ] && [ "$LATEX_AVAILABLE" = true ]; then
    echo "Available conversion methods:"
    echo "  1. Pandoc + LaTeX (Recommended)"
    echo "  2. Pandoc to DOCX (for manual formatting)"
    echo "  3. LaTeX template (manual setup required)"
    echo ""

    # For automated builds, use method 1
    METHOD=1
    echo "Using Method 1: Pandoc + LaTeX"
    echo ""

elif [ "$PANDOC_AVAILABLE" = true ]; then
    echo "LaTeX not found. Using Pandoc to DOCX conversion."
    METHOD=2
else
    echo -e "${RED}Error: Pandoc not found.${NC}"
    echo ""
    echo "Please install Pandoc:"
    echo "  - Windows: https://pandoc.org/installing.html"
    echo "  - macOS: brew install pandoc"
    echo "  - Linux: sudo apt-get install pandoc"
    echo ""
    echo "For best results, also install LaTeX:"
    echo "  - Windows: MiKTeX (https://miktex.org/)"
    echo "  - macOS: MacTeX (https://www.tug.org/mactex/)"
    echo "  - Linux: sudo apt-get install texlive-full"
    exit 1
fi

# Method 1: Pandoc + LaTeX
if [ "$METHOD" -eq 1 ]; then
    echo "Converting paper.md to PDF using Pandoc + LaTeX..."

    # Create temporary LaTeX template
    cat > ieee_template.tex << 'EOF'
\documentclass[journal]{IEEEtran}
\usepackage{cite}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{algorithmic}
\usepackage{graphicx}
\usepackage{textcomp}
\usepackage{xcolor}
\usepackage{hyperref}
\usepackage{url}
\usepackage{booktabs}

\hypersetup{
    colorlinks=true,
    linkcolor=blue,
    filecolor=magenta,
    urlcolor=blue,
    citecolor=blue,
}

\begin{document}

$body$

\end{document}
EOF

    echo "Generating PDF..."
    pandoc paper.md \
        --from markdown \
        --to latex \
        --template ieee_template.tex \
        --citeproc \
        --bibliography references.bib \
        --output paper.pdf \
        --pdf-engine=pdflatex \
        --variable geometry:margin=1in \
        2>&1 | tee pandoc_output.log

    if [ -f "paper.pdf" ]; then
        echo -e "${GREEN}✓ PDF generated successfully: paper.pdf${NC}"

        # Check PDF properties
        if command -v pdfinfo &> /dev/null; then
            echo ""
            echo "PDF Information:"
            pdfinfo paper.pdf | grep -E "(Pages|PDF version|Page size)"
        fi

        # Clean up temporary files
        rm -f ieee_template.tex
        rm -f *.aux *.log *.out *.toc 2>/dev/null || true

        echo ""
        echo -e "${GREEN}Build complete!${NC}"
        echo "Output: paper.pdf"
    else
        echo -e "${RED}✗ PDF generation failed${NC}"
        echo "Check pandoc_output.log for errors"
        exit 1
    fi
fi

# Method 2: Pandoc to DOCX
if [ "$METHOD" -eq 2 ]; then
    echo "Converting paper.md to DOCX..."

    pandoc paper.md \
        --from markdown \
        --to docx \
        --citeproc \
        --bibliography references.bib \
        --output paper.docx \
        --reference-doc=ieee_template.docx 2>/dev/null || \
    pandoc paper.md \
        --from markdown \
        --to docx \
        --citeproc \
        --bibliography references.bib \
        --output paper.docx

    if [ -f "paper.docx" ]; then
        echo -e "${GREEN}✓ DOCX generated: paper.docx${NC}"
        echo ""
        echo "Next steps:"
        echo "1. Download IEEE Word template: https://www.ieee.org/conferences/publishing/templates.html"
        echo "2. Open paper.docx in Microsoft Word"
        echo "3. Copy content to IEEE template"
        echo "4. Format according to IEEE guidelines"
        echo "5. Export as PDF"
    else
        echo -e "${RED}✗ DOCX generation failed${NC}"
        exit 1
    fi
fi

echo ""
echo "======================================"
echo "Additional Resources:"
echo "======================================"
echo ""
echo "IEEE Templates:"
echo "  https://www.ieee.org/conferences/publishing/templates.html"
echo ""
echo "Overleaf (Online LaTeX):"
echo "  https://www.overleaf.com/"
echo "  1. Create account"
echo "  2. New Project → IEEE Communications Standards Magazine"
echo "  3. Upload paper.md content"
echo "  4. Compile online"
echo ""
echo "Manual PDF Generation:"
echo "  See README.md for detailed instructions"
echo ""
