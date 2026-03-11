# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Dongha Lim
#
# This file is part of danbooru-downloader-py
from pathlib import Path
import danbooru_downloader_py.file_io as file_io

TEMP_DIR_NAME = "_temp"

IMG_DIR_NAME = "images"

META_DB_NAME = "danbooru.sqlite"

META_FILE_SUFFIX = "-danbooru.json"

# Hex chars
HEX_CHARS = "0123456789abcdef"

class ProjectPaths:
    """
    Manage paths of project
    """
    def __init__(self, root: str | Path):

        self.root = file_io.ensure_path(root).resolve()

        self.img_dir = self.root / IMG_DIR_NAME
        self.db_path = self.root / META_DB_NAME

        file_io.safe_mkdir(self.img_dir)

        # Make subdirectories
        self._make_image_subdir()
    
    def _make_image_subdir(self):
        """
        Make subdirectories under img_dir. 

        The names of subdirs will be 2-digit hex number (lower-case)

        Example:
            image/
              00/
              01/
              ...
              ff/
        """

        for a in HEX_CHARS:
            for b in HEX_CHARS:
                file_io.safe_mkdir(self.img_dir / f"{a + b}")
    
    def get_db_path(self) -> Path:
        return self.db_path
    
    def get_image_path(self, md5: str, ext: str = 'png') -> Path | None:
        """
        Get local image path from MD5 hash

        Example:
            {md5} -> {img_dir}/{md5[:2]/{md5}.png
        """

        if len(md5) < 2:
            return None

        return self.img_dir / md5[:2] / f"{md5}.{ext}"

    def get_meta_path(self, md5: str) -> Path | None:
        """
        Get local image path from MD5 hash

        Example:
            {md5} -> {img_dir}/{md5[:2]/{md5}-danbooru.json
        """

        if len(md5) < 2:
            return None
        
        return self.img_dir / md5[:2] / f"{md5}{META_FILE_SUFFIX}"