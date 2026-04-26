# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Dongha Lim
#
# This file is part of danbooru-downloader-py
from __future__ import annotations
from pathlib import Path
import sqlite3
from typing import Any, Dict, Iterable
import threading
import queue

from danbooru_downloader_py.concurrent import Task
from danbooru_downloader_py.concurrent.base_context_manager import BaseContextManager
from danbooru_downloader_py.utils import sqlite_utils
from danbooru_downloader_py.utils.logger_factory import get_module_logger

logger = get_module_logger(__name__)

RETRY_COUNT = 3
RETRY_DELAY = 1

class DatabaseManager(BaseContextManager):
    """
    Manage SQLite database using functions of utils.sqlite_utils

    Use one worker thread for write to database asynchronously
    """
    def __init__(self, db_path: str | Path):
        
        self.db_path = db_path

        self.q: queue.Queue[Task] = queue.Queue(maxsize=50)

        self.conn_main = sqlite3.connect(self.db_path)
        sqlite_utils.try_create_table(self.conn_main)

        self.thread = threading.Thread(target=self._worker, daemon=True)

        self.thread.start()

    def _worker(self):
        # Create worker's own connection to prevent sqlite exception
        with sqlite3.connect(self.db_path) as conn_worker:
            sqlite_utils.try_create_table(conn_worker)
            while True:
                # Queue.get called; unfinished +1
                task = self.q.get()
                try:
                    if task is None: # Exit sentinel 
                        break
                    
                    # Inject worker thread's connect to kwargs explicitly
                    task.update_kwargs({"connect": conn_worker})

                    task.run()
                finally:
                    # Queue.task_done called; unfinished -1
                    self.q.task_done()

    def insert_or_replace(self, posts: Iterable[Dict[str, Any]], as_async: bool = True) -> None:
        """
        Try to insert or replace posts metadata to database.

        Args:
            posts(Iterable[Dict[str, Any]]): Iterable of dictionary of post metadata
            as_async(bool): If True, execute query asynchronously, otherwise, execute synchronously
        """
        
        if as_async:
            # Connection will be injected at worker thread
            task = self._get_task(func=sqlite_utils.insert_or_replace, connect=None, posts=posts)
            self.q.put(task)
        else:
            # Synchronous
            done = threading.Event()
            # Connection will be injected at worker thread
            task = self._get_task(func=sqlite_utils.insert_or_replace, done=done, connect=None, posts=posts)
            self.q.put(task)
            # Wait until task has done
            done.wait()

            # Throw error if task.error is not None
            if task.error:
                raise task.error

    def get_cursor_by_col(self, condition: str, col_names: Iterable[str]) -> sqlite3.Cursor:
        """
        Execute SELECT query to database. 

        Args:
            condition(str): SQL condition string for WHERE
            col_names(Iterable[str]): Iterable columns names for project operate
        
        Returns:
            A Cursor that contain SELECT query result
        """
        # Select logic will be executed at main thread
        return sqlite_utils.get_cursor_by_col(self.conn_main, condition, col_names)
    
    def delete_by_condition(self, condition: str) -> int:
        """
        Execute DELETE query to database:

        Args:
            condition(str): SQL condition string for WHERE

        Returns:
            The count of affected lines
        """
        # Delete logic will be executed at worker thread synchronously

        # Synchronous
        done = threading.Event()
        task = self._get_task(func=sqlite_utils.delete_by_condition, done=done, connect=None, condition=condition)
        self.q.put(task)
        done.wait()

        if task.error:
            raise task.error
        return task.result

    def _get_task(self, func, done=None, **kwargs) -> Task:
        """
        Task Template
        """
        return Task(retry_count=RETRY_COUNT, retry_condition=self._retry_cond, retry_delay=RETRY_DELAY, 
                    func=func, done=done, **kwargs)

    @staticmethod
    def _retry_cond(e: BaseException) -> bool:
        logger.error(e)
        return True

    def close(self) -> None:
        """
        Close and finalize all connection, thread, tasks
        """
        # Wait queued tasks then put sentinel
        self.q.join()
        self.q.put(None)

        # Stop worker thread and close connection
        self.thread.join()
        self.conn_main.close()

    def __del__(self):
        try: 
            self.close()
        except Exception:
            pass
    
    # Create __enter__ manually for type hint
    def __enter__(self) -> DatabaseManager:
        return self