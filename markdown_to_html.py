from __future__ import annotations

import argparse
import logging
import os
import re
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
        self.markdown = None
        self.theme = theme
        with open(
            Path(self.asset_dir, "template.html"),
            encoding=self.encoding,
        ) as f:
            self.template = f.read()
        if self.theme not in self.themes:
            raise ValueError("Theme not in list of valid options: ", self.theme)
        if not self.file.is_file():
            raise FileNotFoundError(self.file)
        with open(
            Path(self.asset_dir, f"{theme}.css"),
            encoding=self.encoding,
        ) as f:
            self.css = f.read()
        self.html = Path(self.file.parent, f"{self.file.stem}.html")

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
            "{% STYLE %}": f"<style>{self.css}</style>",
            "{% THEME %}": f"""<div
            class="github-markdown-body"
            data-color-mode="{self.theme}"
            data-dark-theme="{self.theme}"
            data-light-theme="{self.theme}">
        """,
            "{% CONTENT %}": html,
        }
        for key, value in update_tags.items():
            self.template = self.template.replace(key, value)
        with open(self.html, "w", encoding=self.encoding) as f:
            f.write(self.template)
        logger.info(f"Rendered HTML: {self.html}")

    def parse_markdown(self: MarkdownToHTML) -> None:
        """Parse the markdown file and convert metadata to table format."""
        with open(self.file, encoding=self.encoding) as f:
            markdown = f.read()
        metadata_pattern = re.compile(r"^---[\s\S]+?---")
        yaml = re.findall(metadata_pattern, markdown)
        markdown = re.sub(metadata_pattern, "", markdown)
        if len(yaml) > 0:
            yaml = yaml[0].split("\n")
            metadata = {
                key.split(":")[0].strip(): key.split(":")[-1].strip()
                for key in yaml
                if key != "---"
            }
            logger.info("Metadata detected")
            max_chars = max(map(len, metadata)) + 1
            for key in metadata:
                n = max_chars - len(key)
                padding = " " * n
                logger.info(f"  {key}{padding}: {metadata[key]}")
            headers = "|".join(metadata.keys())
            sep = "--- |" * len(metadata.keys())
            values = "|".join([metadata[key] for key in metadata])
            markdown = f"{headers}\n{sep}\n{values}\n---\n{markdown}"
        self.markdown = markdown


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
