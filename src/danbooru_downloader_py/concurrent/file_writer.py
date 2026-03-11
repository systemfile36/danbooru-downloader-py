# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Dongha Lim
#
# This file is part of danbooru-downloader-py
from __future__ import annotations
from pathlib import Path
from typing import Any, Iterable, Iterator, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed, Future

from danbooru_downloader_py.concurrent import Task
from danbooru_downloader_py.concurrent.base_context_manager import BaseContextManager
import danbooru_downloader_py.file_io as file_io

RETRY_COUNT = 1

RETRY_DELAY = 0.2

from danbooru_downloader_py.utils.logger_factory import get_module_logger

logger = get_module_logger(__name__)

class FileWriter(BaseContextManager):
    """
    Write file to disk asynchronously by ThreadPoolExecutor 
    """

    def __init__(self, num_workers: int = 6):
        self.executor = ThreadPoolExecutor(max_workers=num_workers)

    def _retry_cond(e: BaseException) -> bool:
        logger.error(e)
        return True

    def _get_task(self, func, **kwargs) -> Task:
        """
        Task Template
        """
        return Task(retry_count=RETRY_COUNT, retry_condition=self._retry_cond, retry_delay=RETRY_DELAY, 
                    func=func, **kwargs)

    def write_bytes(self, path: str | Path, raw_bytes: bytes, return_future: bool = True) -> Path | Future[Path]:
        """
        Write bytes to given path.

        If return_future is True, write bytes asynchronously and return Future

        If return_future is False, write bytes asynchronously and return path
        """

        task = self._get_task(file_io.write_bytes, path=path, raw_bytes=raw_bytes)

        if return_future:
            return self.executor.submit(task.run)
        else:
            return task.run()

    def write_bytes_many(self, path_bytes: Iterable[Tuple[str | Path, bytes]], return_future: bool = True) -> List[Path] | List[Future[Path]]:
        """
        Write bytes to given path.

        If return_future is True, write bytes asynchronously and return list of Future

        If return_future is False, write bytes asynchronously and return result as list of path
        """

        tasks = [self._get_task(file_io.write_bytes, path=path, raw_bytes=raw_bytes) for path, raw_bytes in path_bytes]
        futures = [self.executor.submit(task.run) for task in tasks]

        # To prevent generator laziness, use inner generator function; 
        # If there is yield keyword on function, it's considered as generator.
        def _iter_results() -> Iterator[Tuple[str, bytes]]:
            for f in as_completed(futures):
                yield f.result()

        if return_future:
            return futures
        else: 
            return _iter_results()

    def write_json(
        self, 
        path: str | Path, target: Any, encoding: str = "utf-8", 
        return_future: bool =True
    ) -> Path | Future[Path]:
        """
        Write JSON to given path.

        If return_future is True, write bytes asynchronously and return Future

        If return_future is False, write bytes asynchronously and return result as Path
        """

        task = self._get_task(file_io.write_json, path=path, target=target, encoding=encoding)

        future = self.executor.submit(task.run)

        if return_future:
            return future
        else:
            return future.result()

    def write_json_many(
        self, path_target: Iterable[Tuple[str | Path, Any]], encoding: str = "utf-8", return_future: bool = True
    ) -> List[Path] | List[Future[Path]]:
        """
        Write JSON to given path.

        If return_future is True, write bytes asynchronously and return list of Future

        If return_future is False, write bytes asynchronously and return result as list of Path
        """
        tasks = [self._get_task(file_io.write_json, path=path, target=target, encoding=encoding) for path, target in path_target]
        futures = [self.executor.submit(task.run) for task in tasks]

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
        Close and finalize executor, session
        """
        self.executor.shutdown(wait=True, cancel_futures=False)
    
    def __del__(self):
        try: 
            self.close()
        except Exception:
            pass

    # Create __enter__ manually for type hint
    def __enter__(self) -> FileWriter:
        return self