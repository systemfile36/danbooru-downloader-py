# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Dongha Lim
#
# This file is part of danbooru-downloader-py
import abc
from contextlib import AbstractContextManager

class BaseContextManager(AbstractContextManager):
    """
    Base Abstract ContextManager
    """

    @abc.abstractmethod
    def close(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
