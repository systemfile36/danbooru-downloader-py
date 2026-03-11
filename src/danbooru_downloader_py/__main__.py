# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Dongha Lim
#
# This file is part of danbooru-downloader-py
from typing import List, Tuple
import click
import danbooru_downloader_py

#https://click.palletsprojects.com/en/stable/options/

__version__ = "1.0.0"

@click.version_option(prog_name="DanbooruDownloaderPy", version=__version__)
@click.group()
def main():
    """
    A CLI tool for downloading and managing images from Danbooru.

    It helps you automatically collect anime image datasets with complicate query.
    """

@main.command("dump")
@click.argument(
    "root", type=click.Path(exists=False, resolve_path=True, file_okay=False, dir_okay=True)
)
@click.option("-sp", "--start-page", type=int, default=1, help="The start page. Default is 1")
@click.option("-ep", "--end-page", type=int, help="The end page", required=True)
@click.option("--limit", default=200, help="The limit for each page post count. Default is 200")
@click.option("--query", type=str, default="order:id_asc", help="Tags or metatags for post to search or the path of line-seperated text file of them. It will be used like '/posts.json?tags={QUERY}'. See https://danbooru.donmai.us/wiki_pages/help:cheatsheet")
@click.option("--exts", type=str, default="png,jpg,jpeg", help="A set of extensions to download as comma-seperated list. (e.g, 'png,jpg') Default is 'png,jpg,jpeg'" )
@click.option("--use-resizing", is_flag=True, help="If set, active resizing.")
@click.option("--target-size", type=(int, int), help="Target size as 'WIDTH HEIGHT' for resizing. Default is '1024 1024'")
@click.option("--username", required=True, help="Danbooru username for authentication")
@click.option("--api-key", required=True, help="Danbooru API key for authentication.")
def dump(
    root: str, 
    start_page: int, end_page: int,
    limit: int, query: str,
    exts: str, 
    use_resizing: bool, 
    target_size: Tuple[int, int], 
    username: str, api_key: str,
) -> None:

    danbooru_downloader_py.dump(
        root, start_page, end_page, 
        limit, query, exts, 
        use_resizing, target_size, 
        username, api_key
    )

if __name__ == "__main__":
    main()