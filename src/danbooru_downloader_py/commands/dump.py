# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Dongha Lim
#
# This file is part of danbooru-downloader-py
from pathlib import Path
from typing import Dict, Iterator, List, Tuple
from concurrent.futures import Future, as_completed

from danbooru_downloader_py.file_io import check_path
from danbooru_downloader_py.concurrent import DatabaseManager, HttpManager, ImageManager, PostFilter, FileWriter
from danbooru_downloader_py.project import ProjectPaths
from danbooru_downloader_py.dto import Post

from danbooru_downloader_py.utils.logger_factory import get_module_logger

logger = get_module_logger(__name__)

def run_dump(
    root: Path | str, 
    start_page: int, end_page: int,
    limit: int, 
    query: str | Path,
    exts: List[str] | str, 
    use_resizing: bool,
    target_size: Tuple[int, int], 
    username: str, api_key: str,
) -> None:
    """
    Download images from Danbooru with single query or batched query file
    """
    for current_query in iter_queries(query):
        logger.info(f"Current query: {current_query}")

        dump(
            root=root,
            start_page=start_page,
            end_page=end_page,
            limit=limit,
            query=current_query,
            exts=exts,
            use_resizing=use_resizing,
            target_size=target_size,
            username=username,
            api_key=api_key,
        )

        logger.info(f"Dumping {current_query} is complete.")

def iter_queries(query: Path | str) -> Iterator[str]:
    """
    Yield query strings.

    If `query` is a valid file path, yield each non-empty stripped line.
    Otherwise, yield `query` itself as a single query string.
    """

    if check_path(query):
        logger.info(f"Get batched query from {query}")

        with open(query, "r", encoding="utf-8") as file:
            for line in file:
                current_query = line.strip()

                # Ignore comment 
                if current_query.startswith('#'):
                    continue

                if current_query:
                    yield current_query
    else:
        yield str(query)

def dump(
    root: Path | str, 
    start_page: int, end_page: int,
    limit: int, query: str, 
    exts: List[str] | str, 
    use_resizing: bool,
    target_size: Tuple[int, int], 

    username: str, api_key: str,
) -> None:
    """
    Download images from Danbooru with single query
    """

    # Parse to list when 'exts' is instance of 'str'
    if isinstance(exts, str):
        exts = [ext.strip() for ext in exts.split(",")]

    # Create project paths
    paths = ProjectPaths(root)

    logger.debug("Load managers...")

    # Load Managers as context managers; All of them implement concurrent.BaseContextManager
    with (
        DatabaseManager(paths.get_db_path()) as db_manager, 
        HttpManager() as http_manager, 
        ImageManager(use_resizing=use_resizing, resize_size=target_size) as image_manager, 
        PostFilter(exts=exts) as post_filter, 
        FileWriter() as file_writer
    ):

        # Iterate page [start_page, end_page]
        for page in range(start_page, end_page + 1):

            logger.info(f"Download metadata with {query}... (current page: {page}, current limit: {limit})")

            # Get posts metadata from Danbooru (synchronous)
            raw_posts = http_manager.get_posts(page, username=username, api_key=api_key, query=query, limit=limit)

            if len(raw_posts) <= 0:
                logger.info("There is no posts anymore")
                return
            
            # Convert to Post object
            posts: List[Post] = [Post.from_dict(p, paths) for p in raw_posts]

            # Set flags on each post
            posts = post_filter.annotate(posts)

            # Classify by flags
            posts_for_download: List[Post] = []
            posts_for_save_meta: List[Post] = []
            for post in posts:
                if post.should_download_image: posts_for_download.append(post)
                if post.should_save_metadata: posts_for_save_meta.append(post)

            logger.info(f"Downloading {len(posts_for_download)} posts ...")

            # Generate Dictionary of path keyed by image URL
            url_path_map: Dict[str, Path] = { p.img_url: p.img_path for p in posts_for_download }

            # Get raw bytes from Image URLs asynchronously
            url_bytes: Iterator[Tuple[str, bytes]] = http_manager.get_bytes(list(url_path_map.keys()), return_future=False)

            # Resize and encode
            image_bytes = image_manager.resize_and_encode(url_bytes, return_future=False)

            # Save metadata while downloading and processing images
            saved_meta_paths = file_writer.write_json_many([(p.meta_path, p.raw) for p in posts_for_save_meta], return_future=False)

            # Iterate generator to save processed images
            saved_image_path_futures: List[Future[Path]] = []
            for url, raw_bytes in image_bytes:
                # Get path by URL
                path = url_path_map[url]
                saved_image_path_futures.append(file_writer.write_bytes(path, raw_bytes, return_future=True))

            # Logging saved images
            for f in as_completed(saved_image_path_futures):
                saved_image_path = f.result()

                logger.info(f"A image of {saved_image_path.stem} is saved to {saved_image_path}")

            # Logging saved meta (debug level)
            for p in saved_meta_paths:
                logger.debug(f"A metadata of {p.stem} is saved to {p}")


            logger.info("Update database...")

            # Update database asynchronously; No wait
            db_manager.insert_or_replace([p.raw for p in posts_for_download], as_async=True)
    
    logger.info("Dump command is complete")