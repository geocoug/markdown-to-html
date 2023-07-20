from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path

import requests

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class MarkdownToHTML:
    """Convert Markdown to HTML with GitHub styling."""

    encoding = "utf-8"
    asset_dir = Path(os.path.dirname(__file__), "assets")
    themes = [
        Path(file).stem for file in os.listdir(asset_dir) if file != "template.html"
    ]

    def __init__(self: MarkdownToHTML, file: str, theme: str) -> None:
        """Convert Markdown to HTML with GitHub styling.

        Args:
        ----
            file (str): Markdown file to convert.
            theme (str): Theme for the output HTML (dark, light).
        """
        self.file = Path(file)
        if not self.file.is_file():
            raise FileNotFoundError(self.file)
        if theme not in self.themes:
            raise ValueError("Theme not in list of valid options: ", self.theme)
        self.markdown = None
        self.theme = theme
        self.template = Path(self.asset_dir, "template.html")
        self.css = Path(self.asset_dir, f"{theme}.css")
        self.html = Path(self.file.parent, f"{self.file.stem}.html")

    def read_file(self: MarkdownToHTML, file: Path) -> str:
        """Read a file and return it's contents.

        Args:
        ----
            file (Path): File path as a urllib.Path object.

        Returns:
        -------
            str: File contents
        """
        with open(file, encoding=self.encoding) as f:
            return f.read()

    def render(self: MarkdownToHTML) -> None:
        """Render the Markdown as HTML."""
        self.parse_markdown()
        html = send_request(
            method="POST",
            url="https://api.github.com/markdown",
            json={
                "mode": "markdown",
                "text": self.markdown,
            },
            headers={
                "Content-Type": "application/json",
            },
        ).text
        update_tags = {
            "{% STYLE %}": f"<style>{self.read_file(self.css)}</style>",
            "{% THEME %}": f"""<div
            class="github-markdown-body"
            data-color-mode="{self.theme}"
            data-dark-theme="{self.theme}"
            data-light-theme="{self.theme}">
        """,
            "{% CONTENT %}": html,
        }
        template = self.read_file(self.template)
        for key, value in update_tags.items():
            template = template.replace(key, value)
        with open(self.html, "w", encoding=self.encoding) as f:
            f.write(template)
        logger.info(f"Rendered HTML: {self.html}")

    def parse_markdown(self: MarkdownToHTML) -> None:
        """Read the markdown file."""
        with open(self.file, encoding=self.encoding) as f:
            self.markdown = f.read()


def send_request(method: str, url: str, **kwargs) -> requests.Response:  # noqa
    """Send an HTTP request.

    Args:
    ----
        method (str): Request method to use (GET, POST, DELETE).
        url (str): URL to send request.

    Returns:
    -------
        requests.Response: Request response.
    """
    try:
        response = requests.request(method=method, url=url, **kwargs)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as err:
        logger.exception(err)
        raise err


def clparser() -> argparse.ArgumentParser:
    """Create a parser to handle input arguments and displaying a help message."""
    desc_msg = (
        "Small utility for converting markdown documents to HTML with GitHub styling."
    )
    parser = argparse.ArgumentParser(
        description=desc_msg,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "markdown_file",
        type=str,
        help="Markdown file to render as HTML.",
    )
    parser.add_argument(
        "-t",
        "--theme",
        type=str,
        default="dark",
        help=f"Theme for rendering HTML. Valid themes: {MarkdownToHTML.themes}",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Control the amount of information to display.",
    )
    return parser


if __name__ == "__main__":
    args = clparser().parse_args()
    if args.verbose:
        logger.addHandler(logging.StreamHandler())
    MarkdownToHTML(file=args.markdown_file, theme=args.theme).render()
