@echo off
REM Build script for generating IEEE format PDF from Markdown manuscript (Windows)
REM Supports multiple conversion methods

setlocal enabledelayedexpansion

cd /d "%~dp0"

echo ======================================
echo IEEE Paper PDF Generation Script
echo ======================================
echo.

REM Check prerequisites
echo Checking prerequisites...

where pandoc >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [32m[✓][0m pandoc found
    set PANDOC_AVAILABLE=true
) else (
    echo [31m[✗][0m pandoc not found
    set PANDOC_AVAILABLE=false
)

where pdflatex >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [32m[✓][0m pdflatex found
    set LATEX_AVAILABLE=true
) else (
    where xelatex >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        echo [32m[✓][0m xelatex found
        set LATEX_AVAILABLE=true
    ) else (
        echo [31m[✗][0m LaTeX not found
        set LATEX_AVAILABLE=false
    )
)

echo.

REM Method selection
if "%PANDOC_AVAILABLE%"=="true" (
    if "%LATEX_AVAILABLE%"=="true" (
        echo Available conversion methods:
        echo   1. Pandoc + LaTeX ^(Recommended^)
        echo   2. Pandoc to DOCX ^(for manual formatting^)
        echo.

        REM For automated builds, use method 1
        set METHOD=1
        echo Using Method 1: Pandoc + LaTeX
        echo.
    ) else (
        echo LaTeX not found. Using Pandoc to DOCX conversion.
        set METHOD=2
    )
) else (
    echo [31mError: Pandoc not found.[0m
    echo.
    echo Please install Pandoc:
    echo   Download from: https://pandoc.org/installing.html
    echo.
    echo For best results, also install LaTeX:
    echo   Download MiKTeX from: https://miktex.org/
    echo.
    pause
    exit /b 1
)

REM Method 1: Pandoc + LaTeX
if "%METHOD%"=="1" (
    echo Converting paper.md to PDF using Pandoc + LaTeX...

    REM Create temporary LaTeX template
    (
        echo \documentclass[journal]{IEEEtran}
        echo \usepackage{cite}
        echo \usepackage{amsmath,amssymb,amsfonts}
        echo \usepackage{algorithmic}
        echo \usepackage{graphicx}
        echo \usepackage{textcomp}
        echo \usepackage{xcolor}
        echo \usepackage{hyperref}
        echo \usepackage{url}
        echo \usepackage{booktabs}
        echo.
        echo \hypersetup{
        echo     colorlinks=true,
        echo     linkcolor=blue,
        echo     filecolor=magenta,
        echo     urlcolor=blue,
        echo     citecolor=blue,
        echo }
        echo.
        echo \begin{document}
        echo.
        echo $body$
        echo.
        echo \end{document}
    ) > ieee_template.tex

    echo Generating PDF...
    pandoc paper.md ^
        --from markdown ^
        --to latex ^
        --template ieee_template.tex ^
        --citeproc ^
        --bibliography references.bib ^
        --output paper.pdf ^
        --pdf-engine=pdflatex ^
        --variable geometry:margin=1in ^
        2>&1 | tee pandoc_output.log

    if exist "paper.pdf" (
        echo [32m[✓] PDF generated successfully: paper.pdf[0m

        REM Clean up temporary files
        del /f /q ieee_template.tex 2>nul
        del /f /q *.aux *.log *.out *.toc 2>nul

        echo.
        echo [32mBuild complete![0m
        echo Output: paper.pdf
    ) else (
        echo [31m[✗] PDF generation failed[0m
        echo Check pandoc_output.log for errors
        pause
        exit /b 1
    )
)

REM Method 2: Pandoc to DOCX
if "%METHOD%"=="2" (
    echo Converting paper.md to DOCX...

    pandoc paper.md ^
        --from markdown ^
        --to docx ^
        --citeproc ^
        --bibliography references.bib ^
        --output paper.docx

    if exist "paper.docx" (
        echo [32m[✓] DOCX generated: paper.docx[0m
        echo.
        echo Next steps:
        echo 1. Download IEEE Word template: https://www.ieee.org/conferences/publishing/templates.html
        echo 2. Open paper.docx in Microsoft Word
        echo 3. Copy content to IEEE template
        echo 4. Format according to IEEE guidelines
        echo 5. Export as PDF
    ) else (
        echo [31m[✗] DOCX generation failed[0m
        pause
        exit /b 1
    )
)

echo.
echo ======================================
echo Additional Resources:
echo ======================================
echo.
echo IEEE Templates:
echo   https://www.ieee.org/conferences/publishing/templates.html
echo.
echo Overleaf ^(Online LaTeX^):
echo   https://www.overleaf.com/
echo   1. Create account
echo   2. New Project -^> IEEE Communications Standards Magazine
echo   3. Upload paper.md content
echo   4. Compile online
echo.
echo Manual PDF Generation:
echo   See README.md for detailed instructions
echo.

pause
