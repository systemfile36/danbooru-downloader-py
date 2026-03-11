# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Dongha Lim
#
# This file is part of danbooru-downloader-py
from __future__ import annotations
from typing import Any, Dict, Iterator, List, Tuple
import threading
import requests
from urllib.parse import quote
from concurrent.futures import Future, ThreadPoolExecutor, as_completed

from danbooru_downloader_py.concurrent import Task
from danbooru_downloader_py.concurrent.base_context_manager import BaseContextManager

BASE_URL = "https://danbooru.donmai.us"

POST_ENDPOINT = BASE_URL + "/posts.json"

USER_AGENT = {"User-Agent": "PostmanRuntime/7.43.0"}

TIME_OUT = 30

from danbooru_downloader_py.utils.logger_factory import get_module_logger

logger = get_module_logger(__name__)

# Per-thread local data; seperated from namespace
_thread_local = threading.local()

def _get_session() -> requests.Session:
    # Try to get session from thread local data
    s = getattr(_thread_local, "session", None)
    if s is None:
        s = requests.Session()
        _thread_local.session = s
    return s

class HttpManager(BaseContextManager):
    """
    Manage HTTP requests to Danbooru API or image URL

    Use ThreadPoolExecutor
    """
    def __init__(self, num_workers: int = 4, retry_count: int = 10, retry_delay: int = 3):
        self.executor = ThreadPoolExecutor(max_workers=num_workers)

        self.session = requests.Session()

        # Add User-Agent to prevent receiving a 403 Forbidden response
        self.session.headers.update(USER_AGENT)

        self.retry_count = retry_count

        self.retry_delay = retry_delay

    def _retry_cond(e: BaseException) -> bool:
        logger.error(e)
        return True

    def _get_task(self, func, **kwargs) -> Task:
        """
        Task Template
        """
        return Task(retry_count=self.retry_count, retry_condition=self._retry_cond, retry_delay=self.retry_delay, 
                    func=func, **kwargs)

    def _get_posts(
        self,
        page: int, username: str, 
        api_key: str, query: str | None = None, 
        limit: int = 200
        ) -> List[Dict[str, Any]]:

        if query is None:
            encoded_query = quote("order:id_asc")
        else:
            encoded_query = quote(query)

        url = f"{POST_ENDPOINT}?tags={encoded_query}&page={page}&limit={limit}&login={quote(username)}&api_key={quote(api_key)}"

        res = self.session.get(url, timeout=TIME_OUT)

        res.raise_for_status()

        # Get parsed JSON (may be List[Dict[str, Any]])
        data = res.json()

        return data

    def get_posts(
        self, 
        page: int, username: str, 
        api_key: str, query: str | None = None,
        limit: int = 200
    ) -> List[Dict[str, Any]]:
        """
        Get posts using given parameters.

        Args:
            page(int): `page` parameter for paging API
            username(str): `login` parameter. Username of Danbooru
            api_key(str): `api_key` parameter. API key of Danbooru
            query(str | None): `tags` parameter. See help:cheatsheet on Danbooru wiki pages. 
                Default is 'order:id_asc'
            limit(int): 'limit' parameter for paging API. Default is 200
        """
        task = self._get_task(self._get_posts, page=page, username=username, api_key=api_key, query=query, limit=limit)

        return task.run()
    
    def _get_bytes(
        self, url: str
    ) -> Tuple[str, bytes]:
        """
        Get bytes from URL and return (URL, bytes)
        """

        # Use per-thread session to prevent thread-interfere
        s = _get_session()
        res = s.get(url, headers=self.session.headers, timeout=TIME_OUT)
        res.raise_for_status()

        return url, res.content

    def get_bytes(
        self, url_list: List[str], return_future: bool = True
    ) -> Iterator[Tuple[str, bytes]] | List[Future[Tuple[str, bytes]]]:
        """
        Download bytes from url list and yield tuple (url, bytes). 

        If return_future is True, get bytes asynchronously and return Future

        If return_future is False, get bytes asynchronously and return results as Iterator

        Args:
            url_list(List[str]): Urls to download.
            return_future(bool): If True, return future, otherwise, return result as Iterator
        
        Returns:
            Iterator that yield tuple (url, bytes) when return_future is False, 
            List of Futures of tuple (url, bytes) when return_future is True
        """

        tasks = [self._get_task(self._get_bytes, url=url) for url in url_list]
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
        self.session.close()
    
    def __del__(self):
        try: 
            self.close()
        except Exception:
            pass

    # Create __enter__ manually for type hint
    def __enter__(self) -> HttpManager:
        return self