# Makefile for IEEE ICC 2026 Paper
# GPU-Accelerated NTN-O-RAN Platform

# Configuration
PAPER = ntn_oran_icc2026
LATEX = pdflatex
BIBTEX = bibtex
RM = rm -f

# Targets
.PHONY: all clean distclean quick view help

# Default target: full build with bibliography
all: $(PAPER).pdf

# Full build with bibliography
$(PAPER).pdf: $(PAPER).tex references.bib
	@echo "=== Building IEEE paper with bibliography ==="
	$(LATEX) $(PAPER).tex
	$(BIBTEX) $(PAPER)
	$(LATEX) $(PAPER).tex
	$(LATEX) $(PAPER).tex
	@echo "=== Build complete: $(PAPER).pdf ==="
	@echo ""
	@echo "Paper statistics:"
	@texcount -inc -incbib -sum $(PAPER).tex

# Quick build (no bibliography update)
quick: $(PAPER).tex
	@echo "=== Quick build (no bibliography) ==="
	$(LATEX) $(PAPER).tex
	@echo "=== Quick build complete ==="

# View the PDF
view: $(PAPER).pdf
	@if command -v evince > /dev/null 2>&1; then \
		evince $(PAPER).pdf & \
	elif command -v okular > /dev/null 2>&1; then \
		okular $(PAPER).pdf & \
	elif command -v xdg-open > /dev/null 2>&1; then \
		xdg-open $(PAPER).pdf & \
	else \
		echo "No PDF viewer found. Please open $(PAPER).pdf manually."; \
	fi

# Word count (approximate)
wordcount: $(PAPER).tex
	@echo "=== Word count (approximate) ==="
	@texcount -inc -incbib -sum $(PAPER).tex

# Check for common LaTeX errors
check: $(PAPER).tex
	@echo "=== Checking for common LaTeX errors ==="
	@grep -n "TODO\|FIXME\|XXX" $(PAPER).tex || echo "No TODOs found"
	@grep -n "???" $(PAPER).tex || echo "No undefined references"
	@echo "=== Check complete ==="

# Clean auxiliary files
clean:
	@echo "=== Cleaning auxiliary files ==="
	$(RM) $(PAPER).aux $(PAPER).bbl $(PAPER).blg $(PAPER).log
	$(RM) $(PAPER).out $(PAPER).toc $(PAPER).lof $(PAPER).lot
	$(RM) $(PAPER).fls $(PAPER).fdb_latexmk $(PAPER).synctex.gz
	@echo "=== Clean complete ==="

# Clean everything including PDF
distclean: clean
	@echo "=== Removing PDF output ==="
	$(RM) $(PAPER).pdf
	@echo "=== Distclean complete ==="

# Validate paper for IEEE PDF eXpress
validate: $(PAPER).pdf
	@echo "=== IEEE PDF eXpress Pre-Validation ==="
	@echo "Checking file size..."
	@ls -lh $(PAPER).pdf
	@echo ""
	@echo "Checking PDF version..."
	@pdfinfo $(PAPER).pdf | grep "PDF version" || echo "pdfinfo not installed"
	@echo ""
	@echo "Next steps:"
	@echo "1. Upload $(PAPER).pdf to IEEE PDF eXpress"
	@echo "2. Use conference ID: [Your ICC 2026 Conference ID]"
	@echo "3. Fix any errors reported by PDF eXpress"
	@echo "4. Download corrected PDF for submission"
	@echo ""

# Help message
help:
	@echo "=== IEEE ICC 2026 Paper Build System ==="
	@echo ""
	@echo "Available targets:"
	@echo "  make          - Full build with bibliography (default)"
	@echo "  make all      - Same as 'make'"
	@echo "  make quick    - Quick build without bibliography update"
	@echo "  make view     - Open PDF in viewer"
	@echo "  make wordcount- Count words in paper"
	@echo "  make check    - Check for TODOs and undefined references"
	@echo "  make clean    - Remove auxiliary files (.aux, .log, etc.)"
	@echo "  make distclean- Remove all generated files including PDF"
	@echo "  make validate - Pre-validate for IEEE PDF eXpress"
	@echo "  make help     - Show this help message"
	@echo ""
	@echo "Requirements:"
	@echo "  - pdflatex (TeXLive 2020 or later recommended)"
	@echo "  - bibtex"
	@echo "  - texcount (optional, for word count)"
	@echo "  - pdfinfo (optional, for PDF validation)"
	@echo ""
	@echo "IEEE ICC 2026 Submission:"
	@echo "  - Page limit: 6 pages (including references)"
	@echo "  - Format: IEEE double-column conference format"
	@echo "  - Deadline: October 2025 (check official site)"
	@echo ""
