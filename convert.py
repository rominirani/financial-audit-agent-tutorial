import urllib.request
import re
import sys
import json

# Minimal python markdown-to-html approach, or let's try to just use BypassSandbox to pip install markdown.
# Actually, wait. Let's just create the convert.py file here and then run pip install with bypass sandbox.
import markdown

with open("architecting_autonomous_enterprise_workflows.md", "r") as f:
    md_text = f.read()

html_content = markdown.markdown(md_text, extensions=['fenced_code', 'tables'])

html_content = re.sub(
    r'<pre><code class="(language-)?mermaid">(.*?)</code></pre>',
    r'<pre class="mermaid">\2</pre>',
    html_content,
    flags=re.DOTALL
)

html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Architecting Autonomous Enterprise Workflows</title>
    
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900&family=JetBrains+Mono:ital,wght@0,100..800;1,100..800&display=swap" rel="stylesheet">
    
    <!-- Highlight.js -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css">
    
    <style>
        body {{
            background-color: white;
            color: black;
            font-family: 'Inter', sans-serif;
            line-height: 1.8;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px 20px 80px 20px;
            font-size: 16px;
        }}
        
        h1 {{
            font-size: 2.5rem;
            line-height: 1.2;
            margin-top: 2rem;
            margin-bottom: 0.5rem;
        }}
        
        h1 + p > em, h1 + em {{
            color: #666;
            font-size: 1.2rem;
            display: block;
            margin-bottom: 2rem;
        }}
        
        h2 {{
            font-size: 1.8rem;
            margin-top: 3rem;
            margin-bottom: 1rem;
            border-bottom: 1px solid #eee;
            padding-bottom: 0.5rem;
        }}
        
        h3 {{
            font-size: 1.4rem;
            margin-top: 2rem;
            margin-bottom: 1rem;
        }}
        
        p {{
            margin-bottom: 1.5rem;
        }}
        
        /* Code blocks */
        pre:not(.mermaid) {{
            background-color: #f6f8fa;
            border-radius: 8px;
            padding: 16px;
            overflow-x: auto;
            margin-bottom: 1.5rem;
        }}
        
        code, pre {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.9em;
        }}
        
        /* Inline code */
        p > code, li > code, td > code {{
            background-color: #f6f8fa;
            padding: 0.2em 0.4em;
            border-radius: 4px;
        }}
        
        /* Tables */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 2rem;
        }}
        
        th, td {{
            border: 1px solid #e1e4e8;
            padding: 12px 16px;
            text-align: left;
        }}
        
        th {{
            background-color: #f6f8fa;
            font-weight: 600;
        }}
        
        tr:nth-child(even) {{
            background-color: #fbfcfd;
        }}
        
        /* Horizontal rules */
        hr {{
            border: 0;
            border-top: 1px solid #e1e4e8;
            margin: 3rem 0;
        }}
        
        /* Blockquotes */
        blockquote {{
            margin: 0 0 1.5rem 0;
            padding: 1rem 1.5rem;
            border-left: 4px solid #d0d7de;
            background-color: #f6f8fa;
            color: #57606a;
        }}
        
        blockquote p:last-child {{
            margin-bottom: 0;
        }}
        
        /* Lists */
        ul, ol {{
            margin-bottom: 1.5rem;
            padding-left: 2rem;
        }}
        
        li {{
            margin-bottom: 0.5rem;
        }}
        
        /* Responsive */
        @media (max-width: 600px) {{
            body {{
                padding: 15px;
                font-size: 15px;
            }}
            h1 {{
                font-size: 2rem;
            }}
        }}
    </style>
</head>
<body>

{html_content}

<!-- Highlight.js script -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
<script>hljs.highlightAll();</script>

<!-- Mermaid.js script -->
<script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"></script>
<script>mermaid.initialize({{startOnLoad:true, theme:'default'}});</script>

</body>
</html>
"""

with open("index.html", "w") as f:
    f.write(html_template)
