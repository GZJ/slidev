from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import textwrap
from importlib import resources
from pathlib import Path

import webview
from webview.errors import WebViewException

DEFAULT_TEMPLATE = textwrap.dedent(
    """
    <!doctype html>
    <html lang="en">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
            <title>slidev</title>
            <link rel="stylesheet" href="dist/reset.css">
            <link rel="stylesheet" href="dist/reveal.css">
            <link rel="stylesheet" href="dist/theme/black.css">
            <link rel="stylesheet" href="dist/plugin/highlight/monokai.css">
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
            <script src="dist/plugin/notes.js"></script>
            <script src="dist/plugin/markdown.js"></script>
            <script src="dist/plugin/highlight.js"></script>
            <script>
                Reveal.initialize({
                    hash: true,
                    plugins: [ RevealMarkdown, RevealHighlight, RevealNotes ]
                });
            </script>
        </body>
    </html>
    """
).strip()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create a presentation from markdown using pywebview",
        add_help=False,
    )
    parser.add_argument("file", help="Markdown file to load")
    parser.add_argument("-t", "--tmpl", default=None, help="Optional custom HTML template")
    parser.add_argument("-w", "--width", type=int, default=800, help="Window width")
    parser.add_argument("-h", "--height", type=int, default=600, help="Window height")
    parser.add_argument("-x", type=int, default=0, help="Window x position")
    parser.add_argument("-y", type=int, default=0, help="Window y position")
    parser.add_argument("--help", action="help", help="Show this help message and exit")
    return parser


def _get_packaged_reveal_root() -> resources.abc.Traversable:
    reveal_root = resources.files("slidev").joinpath("assets", "reveal")
    if not reveal_root.is_dir():
        raise RuntimeError(
            "Packaged reveal.js assets were not found. Run `npm --prefix frontend run build` first."
        )
    return reveal_root


def _read_manifest(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_reveal_assets_extracted(cache_root: Path) -> Path:
    destination = cache_root / "slidev" / "reveal"
    packaged_root = _get_packaged_reveal_root()

    with resources.as_file(packaged_root) as source_root:
        source_manifest = _read_manifest(source_root / "manifest.json")
        destination_manifest = _read_manifest(destination / "manifest.json")

        if not destination.exists() or destination_manifest != source_manifest:
            if destination.exists():
                shutil.rmtree(destination)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(source_root, destination)

    return destination


def _escape_markdown_for_template(markdown_content: str) -> str:
    return markdown_content.replace("</textarea>", "&lt;/textarea>")


def generate_html_from_markdown(
    markdown_file: Path, output_index_path: Path, template: str | None = None
) -> None:
    markdown_content = markdown_file.read_text(encoding="utf-8")
    html_template = template or DEFAULT_TEMPLATE
    html_content = html_template.replace(
        "{markdown_content}", _escape_markdown_for_template(markdown_content)
    )
    output_index_path.write_text(html_content, encoding="utf-8")


def _start_webview() -> None:
    try:
        webview.start()
    except WebViewException as error:
        message = str(error)
        if "either QT or GTK" in message:
            raise SystemExit(
                "slidev could not start a GUI backend.\n"
                "On Linux this project expects the Qt backend from the uv environment.\n"
                "Run `uv sync` and try again. If it still fails, ensure you are running inside a graphical desktop session."
            ) from error
        raise


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    markdown_path = Path(args.file).expanduser().resolve()
    if not markdown_path.is_file():
        parser.error(f"Markdown file does not exist: {markdown_path}")

    template_path = Path(args.tmpl).expanduser().resolve() if args.tmpl else None
    if template_path and not template_path.is_file():
        parser.error(f"Template file does not exist: {template_path}")

    custom_template = (
        template_path.read_text(encoding="utf-8") if template_path else None
    )
    reveal_root = ensure_reveal_assets_extracted(Path(tempfile.gettempdir()))
    index_path = reveal_root / "index.html"
    generate_html_from_markdown(markdown_path, index_path, custom_template)

    webview.create_window(
        title="slidev",
        url=index_path.as_uri(),
        width=args.width,
        height=args.height,
        x=args.x,
        y=args.y,
    )
    _start_webview()


__all__ = ["main"]
