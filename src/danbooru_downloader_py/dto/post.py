from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from danbooru_downloader_py.project.project import ProjectPaths
import danbooru_downloader_py.file_io as file_io

@dataclass
class Post:
    """
    Class of Danbooru Post
    """

    id: str
    md5: str
    img_path: Path
    meta_path: Path
    ext: str
    img_url: str
    created: datetime
    updated: datetime
    is_pending: bool
    is_deleted: bool

    # Raw Danbooru post metadata
    raw: Dict[str, Any]

    is_valid: bool = False
    should_save_metadata: bool = False
    should_download_image: bool = False
    should_update_image: bool = False

    @classmethod
    def from_dict(cls, meta: Dict[str, Any], project_paths: ProjectPaths) -> Post:
        """
        Create Post instance from parsed metadata JSON dictionary
        """

        md5 = str(meta.get('md5', ''))
        ext = str(meta.get('file_ext', ''))

        # Create path from MD5
        img_path = project_paths.get_image_path(md5, ext)
        meta_path = project_paths.get_meta_path(md5)

        return cls(
            id = str(meta.get('id', -1)), 
            md5 = str(meta.get('md5', '')), 
            img_path = img_path,
            meta_path = meta_path,
            ext = ext, 
            img_url = str(meta.get('file_url', '')),
            created = datetime.fromisoformat(str(meta.get('created_at', '1970-01-01'))), 
            updated = datetime.fromisoformat(str(meta.get('updated_at', '1970-01-01'))),
            is_pending = bool(meta.get('is_pending', False)), 
            is_deleted = bool(meta.get('is_deleted', False)),

            raw = dict(meta) # Copy
        )
    
    