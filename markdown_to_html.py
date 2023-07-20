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

    def __init__(self: MarkdownToHTML, markdown_file: str, theme: str = "dark") -> None:
        """Convert Markdown to HTML with GitHub styling.

        Args:
        ----
            markdown_file (str): Markdown file to convert.
            theme (str): Theme for the output HTML (dark, light).
        """
        self.markdown_file = Path(markdown_file)
        if not self.markdown_file.is_file():
            raise FileNotFoundError(self.markdown_file)
        if theme not in self.themes:
            raise ValueError("Theme not in list of valid options: ", self.theme)
        self.markdown = self.read(self.markdown_file)
        self.theme = theme
        self.template_file = Path(self.asset_dir, "template.html")
        self.template = self.read(self.template_file)
        self.css_file = Path(self.asset_dir, f"{theme}.css")
        self.css = self.read(self.css_file)
        self.html_file = Path(
            self.markdown_file.parent,
            f"{self.markdown_file.stem}.html",
        )
        self.html = None

    def __repr__(self: MarkdownToHTML) -> str:
        """MarkdownToHTML instance representation."""
        return f"{self.__class__.__name__}(markdown_file={self.markdown_file}, theme={self.theme})"  # noqa

    def read(self: MarkdownToHTML, file: Path) -> str:
        """Read a file and return it's contents.

        Args:
        ----
            file (Path): File path as a urllib.Path object.

        Returns:
        -------
            str: File contents
        """
        if not isinstance(file, Path):
            raise TypeError(f"{file} not of type urllib.Path.")
        try:
            with open(file, encoding=self.encoding) as f:
                return f.read()
        except (FileExistsError, FileNotFoundError, OSError) as err:
            logger.exception(err)
            raise err

    def markdown_to_html(self: MarkdownToHTML) -> MarkdownToHTML:
        """Convert Markdown to HTML using the GitHub API."""
        self.html = send_request(
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
        return self

    def render(self: MarkdownToHTML) -> MarkdownToHTML:
        """Render the Markdown as HTML."""
        if not self.html:
            self.markdown_to_html()
        update_tags = {
            "{% STYLE %}": f"<style>{self.css}</style>",
            "{% THEME %}": f"""<div
            class="github-markdown-body"
            data-color-mode="{self.theme}"
            data-dark-theme="{self.theme}"
            data-light-theme="{self.theme}">
        """,
            "{% CONTENT %}": self.html,
        }
        for key, value in update_tags.items():
            self.template = self.template.replace(key, value)
        with open(self.html_file, "w", encoding=self.encoding) as f:
            f.write(self.template)
        logger.info(f"Complete: {self.markdown_file} -> {self.html_file}")
        return self


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
    MarkdownToHTML(markdown_file=args.markdown_file, theme=args.theme).render()
