import json
import os
from pathlib import Path
from typing import Any, Iterable, List
import shutil

JSON_INDENT = 2

def ensure_path(path: str | Path) -> Path:
    """
    Ensure `path` as `pathlib.Path`
    """
    if isinstance(path, Path):
        return path
    elif isinstance(path, str):
        return Path(path)
    else:
        raise ValueError(f"Unexpected type: {type(path)}")

def check_path(path: str | Path | None) -> bool:
    return False if not path else os.path.exists(path)

def check_path_raise(path: str | Path | None) -> str | Path:
    """
    Check the 'path' exists. 
    
    If 'path' is invalid, raise Error, otherwise, return 'path'
    """
    if check_path(path):
        return path
    else:
        raise ValueError(f"Invalid path: {path}")

def resolve_path(path: str | Path, root: Path) -> Path:
    """
    Resolve a path relative to root.

    Args:
        path(str | Path): Absolute or relative path to `root`
        root(str | Path): Root used for relative resolution
    
    Retusn:
        Resolved absolute Path.
    """

    path = ensure_path(path)
    if path.is_absolute():
        return path
    return (root / path).resolve()

def read_json(path: str | Path, encoding="utf-8"):
    with open(path, "r", encoding=encoding) as fs:
        return json.load(fs)
    
def write_json(path: str | Path, target: Any, encoding="utf-8") -> Path:
    with open(path, "w", encoding=encoding) as fs:
        json.dump(target, fs, ensure_ascii=False, indent=JSON_INDENT)
    
    return ensure_path(path)

def write_str(path: str | Path, string: str, encoding="utf-8"):
    with open(path, "w", encoding=encoding) as fs:
        fs.write(string)

def write_bytes(path: str | Path, raw_bytes: bytes) -> Path:
    """
    Write bytes to given path.
    """
    path = ensure_path(path)

    path.write_bytes(raw_bytes)

    return path

def write_array_as_txt(path: str | Path, arr: Iterable[Any], sep: str = '\n', encoding="utf-8"):
    """
    Write array as text file. Concatenate `arr` by `sep` and write it to `path`
    """
    text = sep.join([str(e) for e in arr])
    
    with open(path, "w", encoding=encoding) as fs:
        fs.write(text)

def read_array_from_txt(path: str | Path, sep: str = '\n', encoding="utf-8") -> list:
    """
    Read text file as array. Read text and split to `sep`
    """

    with open(path, "r", encoding=encoding) as fs:
        text = fs.read(fs)

    return text.split(sep)

def safe_mkdir(path: Path | str) -> None:
    """
    Create a new directory at given path.

    If there is missing parents, it will be created as needed.
    """
    path = ensure_path(path)

    path.mkdir(parents=True, exist_ok=True)

def copy_file(src: str | Path, dst: str | Path, overwrite: bool = False) -> None:
    """
    Copy file with metadata (mtime, mode).

    Args:
        src(Path | str): Path of source file
        dst(Path | str): Path of destination location
        overwrite(bool): If True and `dst` is already exists, overwrite it
    """
    src = ensure_path(src)
    dst = ensure_path(dst)

    if dst.exists() and not overwrite:
        return
    safe_mkdir(dst.parent)
    shutil.copy2(src, dst)

def file_size(path: Path) -> int:
    """
    Return size of file at given path
    """
    return path.stat().st_size

def get_files_as_list(root: Path | str, pattern: str, as_str: bool = True) -> List[str]:
    """
    Return all files matching the given pattern under root as list of string.
    
    This function search root recursively by using `rglob`

    Args:
        root(Path | str): Path of root to search
        pattern(str): Pattern string of `rglob`
        as_str(bool): If True, return file list as `List[str]`, otherwise, as `List[Path]`. Default is True
    """

    root = ensure_path(root)

    if as_str:
        return [str(p) for p in root.rglob(pattern) if p.is_file()]
    else:
        return [p for p in root.rglob(pattern) if p.is_file()]