# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Dongha Lim
#
# This file is part of danbooru-downloader-py
import time
from typing import Any, Callable, TypeVar
import threading
T = TypeVar("T")
RetryCond = Callable[[BaseException], bool]

class Task:
    """
    Retryable Task Object
    """
    def __init__(
        self, 
        retry_count: int, 
        retry_condition: RetryCond, 
        retry_delay: int, 
        func: Callable[[], Any], 
        # Optional Event for checking the task is done
        done: threading.Event | None = None,
        **kwargs):

        self.retry_count = retry_count
        self.retry_condition = retry_condition
        self.retry_delay = retry_delay

        self.func = func
        self.kwargs = kwargs

        # Caching result of func
        self.result = None

        self.done = done

        # Will be setted when no-retryable exception occured or retry count exceeded
        self.error: BaseException | None = None

    def run(self) -> Any:
        """
        Run a job with retry.

        Execute `func` with `**kwargs` and return
        """

        attempt = 0
        remaining = self.retry_count

        try:
            while True:
                try:
                    result = self.func(**self.kwargs)

                    # Save to field
                    self.result = result

                    return result

                except BaseException as e:
                    if not self.retry_condition(e):
                        self.error = e
                        raise

                    if remaining < 0:
                        self.error = e
                        raise 

                    # Backoff (1.5^attempt)
                    delay = self.retry_delay * (1.5 ** attempt)

                    remaining -= 1
                    attempt +=1

                    time.sleep(delay)

                    continue
        finally:
            # Set as done whether task is success or not
            if self.done is not None:
                self.done.set()
            
    def update_kwargs(self, kwargs: dict):
        """
        Update inner kwargs for lazy update
        """
        self.kwargs.update(kwargs)