# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Dongha Lim
#
# This file is part of danbooru-downloader-py
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, List

from danbooru_downloader_py.dto import Post
from danbooru_downloader_py.concurrent.image_manager import IMAGE_EXT

from danbooru_downloader_py.concurrent.base_context_manager import BaseContextManager

class PostFilter(BaseContextManager):
    """
    Reusable parallel Post filter

    Mutates post flags 

    Using ThreadPoolExecutor for disk I/O (e.g, checking image or meta already exists)
    """

    def __init__(self, 
                 exts: List[str] = ['jpg', 'jpeg', 'png'],
                 num_workers: int = 6, 
                 extra_rule: Callable[[Post], None] | None = None):
        self.executor = ThreadPoolExecutor(max_workers=num_workers)

        self.exts = exts

        self.extra_rule = extra_rule

    def close(self) -> None:
        """
        Close and finalize executor
        """
        self.executor.shutdown(wait=True, cancel_futures=False)

    def __del__(self):
        try: 
            self.close()
        except Exception:
            pass
        
    # Create __enter__ manually for type hint
    def __enter__(self) -> PostFilter:
        return self
    
    def _worker(self, post: Post) -> Post:
        """
        Worker function excuted in thread pool.
        Mutates post flags and returns it
        """

        # Get path from md5
        img_path = post.img_path
        meta_path = post.meta_path

        if img_path is None or meta_path is None:
            post.is_valid = False
            return post

        if post.is_deleted or post.is_pending or post.ext not in self.exts:
            post.is_valid = False
            return post

        # Set flag as valid
        post.is_valid = True

        # Check both of extension, the original and `IMAGE_EXT` 
        # Because suffix of the path may be changed to `IMAGE_EXT` from original suffix when resized
        img_exists = img_path.with_suffix(IMAGE_EXT).exists() or img_path.exists()
        meta_exists = meta_path.exists()

        post.should_download_image = not img_exists
        post.should_save_metadata = not meta_exists
        
        if self.extra_rule is not None:
            self.extra_rule(post)

        return post
    
    def annotate(self, posts: List[Post]) -> List[Post]:
        """
        Set flags on each post in parallel and return posts 

        Preserve original order
        """

        if not posts:
            return []
        
        # Using 'map' to preserve original order
        return list(self.executor.map(self._worker, posts))