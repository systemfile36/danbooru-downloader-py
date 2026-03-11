# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Dongha Lim
#
# This file is part of danbooru-downloader-py

import sqlite3
from typing import Any, Dict, Iterable

TABLE_QUERY = """CREATE TABLE IF NOT EXISTS posts
( 
    id INTEGER NOT NULL PRIMARY KEY,
    created_at INTEGER,
    uploader_id INTEGER,
    score INTEGER,
    source TEXT,
    md5 TEXT,
    last_comment_bumped_at INTEGER,
    rating TEXT,
    image_width INTEGER,
    image_height INTEGER,
    tag_string TEXT,
    is_note_locked INTEGER,
    fav_count INTEGER,
    file_ext TEXT,
    last_noted_at INTEGER,
    is_rating_locked INTEGER,
    parent_id INTEGER,
    has_children INTEGER,
    approver_id INTEGER,
    tag_count_general INTEGER,
    tag_count_artist INTEGER,
    tag_count_character INTEGER,
    tag_count_copyright INTEGER,
    file_size INTEGER,
    is_status_locked INTEGER,
    pool_string TEXT,
    up_score INTEGER,
    down_score INTEGER,
    is_pending INTEGER,
    is_flagged INTEGER,
    is_deleted INTEGER,
    tag_count INTEGER,
    updated_at INTEGER,
    is_banned INTEGER,
    pixiv_id INTEGER,
    pixiv_ugoira_frame_data TEXT,
    last_commented_at INTEGER,
    has_active_children INTEGER,
    bit_flags INTEGER,
    tag_count_meta INTEGER,
    keeper_data TEXT,
    uploader_name TEXT,
    has_large INTEGER,
    has_visible_children INTEGER,
    children_ids TEXT,
    is_favorited INTEGER,
    tag_string_general TEXT,
    tag_string_character TEXT,
    tag_string_copyright TEXT,
    tag_string_artist TEXT,
    tag_string_meta TEXT,
    file_url TEXT,
    large_file_url TEXT,
    preview_file_url TEXT
);
"""

def try_create_table(connect: sqlite3.Connection) -> None:
    """
    Try to create `posts` table if not exists
    """
    cur = connect.cursor()

    cur.execute(TABLE_QUERY)

    connect.commit()

    cur.close()

def insert_or_replace(connect: sqlite3.Connection, posts: Iterable[Dict[str, Any]]) -> None:
    """
    Try to insert posts to database.

    Args:
        connect(Connection): Connection of database to interact
        posts(Iterable[Dict[Any]]): Collection of posts metadata as Dict
    """

    posts_list = list(posts)
    if not posts_list:
        return

    cur = connect.cursor()

    for post in posts_list:
        post = dict(post)  # avoid mutating caller object
        post.pop("media_asset", None) # Remove 'media_asset' field

        keys = list(post.keys())
        if not keys:
            continue

        cols = ",".join(keys)
        placeholders = ",".join([f":{k}" for k in keys])
        query = f"INSERT OR REPLACE INTO posts ({cols}) VALUES ({placeholders})"

        cur.execute(query, post)

    connect.commit()
    cur.close()

def get_cursor_by_col(connect: sqlite3.Connection, condition: str, col_names: Iterable[str]) -> sqlite3.Cursor:
    """
    Get cursor containing result of `SELECT` with condition

    Args:
        connect(Connection): Connection of database to interact
        condition(str): String of condition for `WHERE`
        col_names(Iterable[str]): Iterable of columns names for `SELECT`

    Returns:
        Result as Cursor
    """

    cur = connect.cursor()

    query = f"SELECT {','.join(col_names)} FROM posts WHERE {condition}"

    return cur.execute(query)

def count_by_condition(connect: sqlite3.Connection, condition: str) -> int:
    """
    Get count of rows that matched condition

    Args:
        connect(Connection): Connection of database to interact
        condition(str): String of condition for `WHERE`

    Returns:
        The count of rows as integer
    """

    cur = connect.cursor()

    query = f"SELECT COUNT(*) FROM posts WHERE {condition}"

    out = int(cur.execute(query).fetchone()[0])

    cur.close()

    return out

def delete_by_condition(connect: sqlite3.Connection, condition: str) -> int:
    """
    Delete rows that matched condition

    Args:
        connect(Connection): Connection of database to interact
        condition(str): String of condition for `WHERE`
    
    Returns:
        The count of deleted rows
    """

    cur = connect.cursor()

    query = f"DELETE FROM posts WHERE {condition}"

    cur.execute(query)

    deleted = cur.rowcount

    connect.commit()

    cur.close()

    return deleted