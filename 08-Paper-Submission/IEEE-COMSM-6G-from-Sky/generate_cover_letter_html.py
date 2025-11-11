#!/usr/bin/env python3
"""Generate HTML version of cover letter"""

with open('cover_letter.md', 'r', encoding='utf-8') as f:
    content = f.read()

html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Cover Letter - IEEE Communications Standards Magazine</title>
    <style>
        body {{
            font-family: "Times New Roman", Times, serif;
            max-width: 8in;
            margin: 40px auto;
            padding: 20px;
            line-height: 1.6;
            font-size: 12pt;
        }}
        h1 {{ font-size: 18pt; margin-bottom: 20px; }}
        h2 {{ font-size: 14pt; margin-top: 20px; margin-bottom: 10px; }}
        p {{ text-align: justify; margin: 10px 0; }}
        .no-print {{
            background: #ffffcc;
            padding: 15px;
            margin-bottom: 20px;
            border: 2px solid #ffcc00;
            border-radius: 5px;
        }}
        @media print {{
            .no-print {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="no-print">
        <h3>📄 PDF Generation Instructions:</h3>
        <ol>
            <li>Press <strong>Ctrl+P</strong> (Windows/Linux) or <strong>Cmd+P</strong> (Mac)</li>
            <li>Select "Save as PDF" as destination</li>
            <li>Save as <code>cover_letter.pdf</code></li>
        </ol>
    </div>

    <pre style="font-family: 'Times New Roman', Times, serif; white-space: pre-wrap; line-height: 1.6; font-size: 12pt;">
{content}
    </pre>
</body>
</html>'''

with open('cover_letter.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Cover letter HTML generated: cover_letter.html")
print("Open in browser and use Print to PDF (Ctrl+P or Cmd+P)")
