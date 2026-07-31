#!/usr/bin/env python3
"""Generate tutorial.html from tutorial_financial_audit_agent.md"""
import html
import os

DIR = os.path.dirname(os.path.abspath(__file__))
MD_FILE = os.path.join(DIR, "tutorial_financial_audit_agent.md")
HTML_FILE = os.path.join(DIR, "tutorial.html")

# Read markdown
with open(MD_FILE, "r") as f:
    md_content = f.read()

# Minimally escape the markdown — only prevent premature </script> closure.
# <script type="text/template"> content is inert; browsers don't parse it as HTML.
# html.escape() was breaking mermaid arrows (-->) and quotes.
escaped_md = md_content.replace("</script>", "<\\/script>")

html_output = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Financial Audit Agent Tutorial</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css">
    <style>
        body {
            background-color: #fff;
            color: #000;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px 40px;
            font-family: 'Inter', sans-serif;
            line-height: 1.7;
        }
        pre {
            background-color: #f6f8fa;
            border: 1px solid #e1e4e8;
            border-radius: 6px;
            padding: 16px;
            overflow-x: auto;
        }
        pre code {
            font-family: 'JetBrains Mono', monospace;
            font-size: 14px;
            background: none;
            padding: 0;
            border: none;
        }
        code {
            background-color: #f0f0f0;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 0.9em;
            font-family: 'JetBrains Mono', monospace;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 16px 0;
        }
        th {
            background-color: #f6f8fa;
            font-weight: 600;
            text-align: left;
        }
        th, td {
            padding: 12px 16px;
            border-bottom: 1px solid #e1e4e8;
        }
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        blockquote {
            border-left: 4px solid #4285f4;
            background: #f0f7ff;
            padding: 16px 20px;
            margin: 24px 0;
        }
        blockquote.callout-tip {
            border-left-color: #34a853;
            background: #f0fff4;
        }
        blockquote.callout-warning {
            border-left-color: #ea4335;
            background: #fff8f0;
        }
        blockquote.callout-key {
            border-left-color: #fbbc05;
            background: #fffbf0;
        }
        h1 { font-size: 2.2em; border-bottom: 2px solid #e1e4e8; padding-bottom: 12px; }
        h2 { font-size: 1.6em; border-bottom: 1px solid #e1e4e8; padding-bottom: 8px; margin-top: 48px; }
        h3 { font-size: 1.3em; margin-top: 32px; }
        hr { border: none; border-top: 2px solid #e1e4e8; margin: 48px 0; }
        a { color: #1a73e8; text-decoration: none; }
        a:hover { text-decoration: underline; }
        img { max-width: 100%; border-radius: 8px; }
        .mermaid { background: #fff; text-align: center; }
    </style>
</head>
<body>

<div id="render-target"></div>

<script id="markdown-source" type="text/template">
""" + escaped_md + """
</script>

<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>

<script>
document.addEventListener('DOMContentLoaded', function() {
    var rawMarkdown = document.getElementById('markdown-source').textContent;

    var renderer = new marked.Renderer();
    renderer.blockquote = function(body) {
        var text = (typeof body === 'object') ? (body.text || '') : String(body);
        var cls = 'callout-info';
        if (text.indexOf('\\u{1f4a1}') !== -1 || text.indexOf('Tip') !== -1) cls = 'callout-tip';
        if (text.indexOf('\\u26a0') !== -1 || text.indexOf('Warning') !== -1) cls = 'callout-warning';
        if (text.indexOf('\\u{1f511}') !== -1 || text.indexOf('Key Insight') !== -1) cls = 'callout-key';
        if (text.indexOf('\\u2705') !== -1 || text.indexOf('Validation') !== -1 || text.indexOf('real output') !== -1) cls = 'callout-tip';
        return '<blockquote class="' + cls + '">' + text + '</blockquote>';
    };

    marked.setOptions({ renderer: renderer, gfm: true, breaks: false });

    document.getElementById('render-target').innerHTML = marked.parse(rawMarkdown);

    document.querySelectorAll('pre code').forEach(function(block) {
        if (!block.classList.contains('language-mermaid')) {
            hljs.highlightElement(block);
        }
    });

    document.querySelectorAll('pre code.language-mermaid').forEach(function(block) {
        var pre = block.parentElement;
        var div = document.createElement('pre');
        div.className = 'mermaid';
        div.textContent = block.textContent;
        pre.parentNode.replaceChild(div, pre);
    });

    mermaid.initialize({ startOnLoad: false, theme: 'default' });
    mermaid.run({ querySelector: '.mermaid' });
});
</script>

</body>
</html>
"""

with open(HTML_FILE, "w") as f:
    f.write(html_output)

print(f"Generated {HTML_FILE}")
print(f"  Markdown: {len(md_content):,} chars")
print(f"  Escaped:  {len(escaped_md):,} chars")
print(f"  HTML:     {len(html_output):,} chars")
