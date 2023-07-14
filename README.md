# markdown-to-html

[![Python Checks](https://github.com/geocoug/markdown-to-html/actions/workflows/python-checks.yml/badge.svg)](https://github.com/geocoug/markdown-to-html/actions/workflows/python-checks.yml)
[![Docker Build](https://github.com/geocoug/markdown-to-html/actions/workflows/docker-build.yml/badge.svg)](https://github.com/geocoug/markdown-to-html/actions/workflows/docker-build.yml)

Small utility for converting markdown documents to HTML with GitHub styling.

## Usage

```txt
usage: markdown_to_html.py [-h] [-t THEME] [-v] markdown_file

Small utility for converting markdown documents to HTML with GitHub styling.

positional arguments:
  markdown_file         Markdown file to render as HTML.

options:
  -h, --help            show this help message and exit
  -t THEME, --theme THEME
                        Theme for rendering HTML. Valid themes: ['dark', 'light'] (default: dark)
  -v, --verbose         Control the amount of information to display. (default: False)
```

## Docker

`docker run --rm -v $(pwd):/usr/local/app ghcr.io/geocoug/markdown-to-html -v README.md`
