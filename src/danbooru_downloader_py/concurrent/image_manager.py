# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Dongha Lim
#
# This file is part of danbooru-downloader-py
from __future__ import annotations
from io import BytesIO
from typing import Iterator, List, Tuple
from concurrent.futures import Future, ProcessPoolExecutor, as_completed

from danbooru_downloader_py.concurrent.base_context_manager import BaseContextManager
from PIL import Image

from danbooru_downloader_py.utils.logger_factory import get_module_logger

logger = get_module_logger(__name__)

IMAGE_EXT = '.png'

BACKGROUND = (0, 0, 0, 0)

RETRY_COUNT = 1
RETRY_DELAY = 1

def _encode_png_resized_padded(
        url: str,
        raw_bytes: bytes, 
        resize_wh: Tuple[int, int]
) -> Tuple[str, bytes]:
    """
    Decode -> convert -> resize(pad) -> PNG compress -> return PNG bytes

    Top-level function for ProcessPool pickle-safety

    Args:
        url(str): Original source of bytes. Used as key of bytes 
        raw_bytes(bytes): Sequence of image bytes
        resize_wh(Tuple[int, int]): Target size of resizing

    Returns:
        A tuple of source url and bytes
    """

    target_width, target_height = resize_wh

    with Image.open(BytesIO(raw_bytes)) as img:
        img: Image.Image = img.convert("RGBA")

        src_width, src_height = img.size

        if src_width == 0 or src_height == 0:
            raise ValueError(f"Invalid image: {None}")
        
        # Fit to small one (Resize mode = pad)
        scale = min(target_width / src_width, target_height / src_height)

        new_width = max(1, int(round(src_width * scale)))
        new_height = max(1, int(round(src_height * scale)))

        # Resizing to target
        resized = img.resize((new_width, new_height), resample=Image.Resampling.BOX)

        # Transparent background 
        bg = Image.new("RGBA", (target_width, target_height), BACKGROUND)

        # Get left-top coordinate (Center)
        left = (target_width - new_width) // 2
        top = (target_height - new_height) // 2

        # paste centered; use alpha as mask to preserve transparency
        bg.paste(resized, (left, top), mask=resized)

        # PNG compress and return as bytes
        out = BytesIO()
        bg.save(out, format="PNG", optimize=True)
        return url, out.getvalue()

class ImageManager(BaseContextManager):
    """
    Manage image resizing and writing

    Use ProcessPool to resize and encoding asynchronously
    """
    def __init__(self, num_workers: int = 6, use_resizing: bool = True, resize_size: Tuple[int, int] = (1024, 1024)):
        self.executor = ProcessPoolExecutor(max_workers=num_workers)
        self.resize_width = resize_size[0]
        self.resize_height = resize_size[1]

        self.use_resizing = use_resizing

    def resize_and_encode(
        self, url_bytes: Iterator[Tuple[str, bytes]], return_future: bool = True
    ) -> Iterator[Tuple[str, bytes]] | List[Future[Tuple[str, bytes]]]:
        """
        Resize images and return as PNG bytes or original bytes 

        If use_resizing is True, decode bytes and resize it then return as PNG bytes.

        If use_resizing is False, return input as is.

        Args:
            url_bytes(Iterator[Tuple[str, bytes]]): Iterator of tuple (url, bytes)
            return_future(bool): If True, return Futures, otherwise, return results as iterator
        
        Returns:
            A itarator of tuple (url, bytes) when return_future is False, 
            A list of Futures of tuple (url, bytes) when return_future is True. The bytes is resized PNG or same as input
        """

        # If no resizing, return input as is
        if not self.use_resizing:
            if return_future: 
                futs: List[Future[Tuple[str, bytes]]] = []
                for item in url_bytes:
                    f: Future[Tuple[str, bytes]] = Future()
                    f.set_result(item)
                    futs.append(f)
                logger.warning("return_future is True and use_resizing is False! It may slows down pipeline")
                return futs
            return url_bytes

        futures = []

        for url, bytes in url_bytes:
            
            future = self.executor.submit(_encode_png_resized_padded, url, bytes, (self.resize_width, self.resize_height))

            futures.append(future)

        # To prevent generator laziness, use inner generator function; 
        # If there is yield keyword on function, it's considered as generator.
        def _iter_results() -> Iterator[Tuple[str, bytes]]:
            for f in as_completed(futures):
                yield f.result()

        if return_future:
            return futures
        else:
            return _iter_results()

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
    def __enter__(self) -> ImageManager:
        return self