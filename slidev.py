import os
import sys
import shutil
import webview
import argparse
import tempfile

def get_reveal_js_resource_path():
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, 'reveal.js')
    else:
        return os.path.join(os.path.dirname(__file__), 'reveal.js')

def ensure_reveal_js_extracted(cache_dir):
    reveal_cache_dir = os.path.join(cache_dir, 'reveal.js')
    print(reveal_cache_dir)
    
    if not os.path.exists(reveal_cache_dir):
        os.makedirs(reveal_cache_dir, exist_ok=True)
        
        source_reveal_dir = get_reveal_js_resource_path()
        
        shutil.copytree(source_reveal_dir, reveal_cache_dir, dirs_exist_ok=True)
        print(f"Extracted Reveal.js to {reveal_cache_dir}")
    
    return reveal_cache_dir

DEFAULT_TMPL = '''
<!doctype html>
<html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>Markdown Presentation</title>
        <link rel="stylesheet" href="dist/reset.css">
        <link rel="stylesheet" href="dist/reveal.css">
        <link rel="stylesheet" href="dist/theme/black.css">
        <link rel="stylesheet" href="plugin/highlight/monokai.css">
    </head>
    <body>
        <div class="reveal">
            <div class="slides">
                <section data-markdown data-separator="^---" data-separator-vertical="^--">
                    <textarea data-template>
                        {markdown_content}
                    </textarea>
                </section>
            </div>
        </div>
        <script src="dist/reveal.js"></script>
        <script src="plugin/notes/notes.js"></script>
        <script src="plugin/markdown/markdown.js"></script>
        <script src="plugin/highlight/highlight.js"></script>
        <script>
            Reveal.initialize({
                hash: true,
                plugins: [ RevealMarkdown, RevealHighlight, RevealNotes ]
            });
        </script>
    </body>
</html>
'''

def generate_html_from_markdown(markdown_file, output_index_path, template=None):
    """
    Generate HTML presentation from markdown file
    
    :param markdown_file: Path to the markdown file
    :param output_index_path: Path to save the generated index.html
    :param template: Optional custom HTML template
    """
    with open(markdown_file, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    html_template = template or DEFAULT_TMPL
    html_content = html_template.replace('{markdown_content}', markdown_content)
    
    with open(output_index_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

def main():
    parser = argparse.ArgumentParser(description='Create a presentation from markdown using webview')
    parser.add_argument('file', help='Markdown file to load')
    parser.add_argument('-t', '--tmpl', default=None, 
                        help='Optional custom HTML template')
    parser.add_argument('-w', '--width', type=int, default=800, 
                        help='Window width')
    parser.add_argument('-H', '--height', type=int, default=600, 
                        help='Window height')
    parser.add_argument('-x', type=int, default=0, 
                        help='Window x position')
    parser.add_argument('-y', type=int, default=0, 
                        help='Window y position')
    
    args = parser.parse_args()
    
    cache_dir = os.path.join(tempfile.gettempdir(), 'slidev')
    reveal_cache_dir = ensure_reveal_js_extracted(cache_dir)
    markdown_path = os.path.abspath(args.file)
    template_path = os.path.abspath(args.tmpl) if args.tmpl else None
    
    custom_template = None
    if template_path and os.path.exists(template_path):
        with open(template_path, 'r', encoding='utf-8') as f:
            custom_template = f.read()
    
    index_path = os.path.join(reveal_cache_dir, 'index.html')
    generate_html_from_markdown(markdown_path, index_path, custom_template)
    
    window = webview.create_window(
        title='Markdown Presentation',
        url=f'file://{index_path}',
        width=args.width,
        height=args.height,
        x=args.x,
        y=args.y
    )
    
    webview.start()

if __name__ == '__main__':
    main()
