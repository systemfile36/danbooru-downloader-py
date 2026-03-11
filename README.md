# danbooru-downloader-py 

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![License](https://img.shields.io/badge/License-AGPL--3.0-yellow)

A CLI tool for downloading and managing [Danbooru](https://danbooru.donmai.us) image datasets. 

This project is a **Python reimplementation inspired by [the original DanbooruDownloader (C#)](https://github.com/KichangKim/DanbooruDownloader)**. 
The goal of this project is to provide a more extensible and dataset-oriented downloader with improved parallelism and modular architecture.

---

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Danbooru Querey Syntax](#danbooru-querey-syntax)
- [License](#license)
- [Acknowledgement](#acknowledgement)

## Features

- Fast dataset dumping using **multi-threading and multi-processing**
- Flexible **Danbooru query support**
- Optional **image resizing during download**
- Modular architecture designed for dataset workflows
- CLI-based operation suitable for automation and scripting

---

## Installation

### Install from source

```bash
git clone https://github.com/systemfile36/danbooru-downloader-py.git
cd danbooru-downloader-py
pip install .
```

---

## Quick Start

### `dump` Examples

```bash
danbooru-downloader-py dump "./data" \
  -sp 1 -ep 2 \
  --limit 200 \
  --query "blonde_hair order:md5" \
  --exts "png,jpg" \
  --use-resizing \
  --target-size 512 512 \
  --username YOUR_USERNAME \
  --api-key YOUR_API_KEY
```

This command downloads images from Danbooru matching the query (`blonde_hair order:md5`) and resize them to '512 x 512', then stores resized images in the specified dataset directory

---

## Usage

### `dump` Command

The main functionality of this tool is the **`dump` command**, which downloads
Danbooru posts and optionally performs preprocessing such as resizing.

Internally, this command uses parallel workers (threads for DB I/O, network I/O; processes for image prreprocessing) to significantly accelerate large dataset downloads.

#### Command Signature

```
danbooru-downloader-py dump ROOT [OPTIONS]
```

#### Arguments

| Argument | Description                                                        |
| -------- | ------------------------------------------------------------------ |
| `ROOT`   | Root directory where downloaded images and metadata will be stored |

#### Options

| Option                | Description                                |
| --------------------- | ------------------------------------------ |
| `-sp`, `--start-page` | Start page of the API query (default: 1)   |
| `-ep`, `--end-page`   | End page of the API query (required)       |
| `--limit`             | Number of posts per page (default: 200)    |
| `--query`             | Danbooru search tags or metatags. <br> Or the path of line-seperated text file for batched query |
| `--exts`              | Allowed image extensions (comma-separated) |
| `--use-resizing`      | Enable resizing during download            |
| `--target-size`       | Target resize resolution (WIDTH HEIGHT)    |
| `--username`          | Danbooru username                          |
| `--api-key`           | Danbooru API key                           |

#### Example

```bash
danbooru-downloader-py dump "./data" \
  -sp 1 \
  -ep 2 \
  --limit 200 \
  --query "blonde_hair order:md5" \
  --exts "png,jpg" \
  --use-resizing \
  --target-size 512 512 \
  --username USERNAME \
  --api-key API_KEY
```

Or

```bash
danbooru-downloader-py dump "./data" \
  -sp 1 \
  -ep 2 \
  --limit 200 \
  --query "batched_query.txt" \
  --exts "png,jpg" \
  --use-resizing \
  --target-size 512 512 \
  --username USERNAME \
  --api-key API_KEY
```

`batched_query.txt` will be like as follow:

```plaintext
# The line that start with '#' will be ignored
blonde_hair score:>50
red_hair score:>50
black_hair red_eyes
......
```

#### Output

Images that downloaded by `dump` command are saved as following structure.

```
Data/
  images/
    00/
      00000000000000000000000000000000.png
      00000000000000000000000000000000-danbooru.json
    01/
    ...
    ff/
  danbooru.sqlite
```

The filename of images is its MD5 hash. And `*-danbooru.json` file contains the metadata of image post.

All of metadata is also saved to `danbooru.sqlite`. 

Table structure is same as follows:

```sql
CREATE TABLE IF NOT EXISTS posts
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
```

## Danbooru Querey Syntax

Queries for `--query` option for `dump` command follow the Danbooru API format

```
/posts.json?tags={QUERY}
```

To see further help, See the official cheatsheet:

https://danbooru.donmai.us/wiki_pages/help:cheatsheet

### Tags Search Examples

```
# Search for posts that have both blonde_hair and blue_eyes
blonde_hair blue_eyes 

# Search for posts that have blonde_hair and don't have blue_eyes
black_hair -blue_eyes 

# Search for posts that have either red_hair, or brown_hair, or both.
red_hair or brown_hair

# Wildcard pattern search. 
shirt_*
```


### Metatags Search Examples

```
# Search for posts uploaded after '2010-01-01'
date:>=2010-01-01

# Search for posts uploaded between '2010-01-01' and '2015-01-01'
date:2010-01-01..2015-01-01

# Search for posts uploaded between 2 weeks and 1 year ago.
age:2weeks..1year

# Search for posts that are rated sensitive. 
# 'g' for general, 's' for sensitive, 'q' for questionble, 'e' for explicit
rating:s
rating:sensitive

# Search for posts that are rated either general or sensitive
rating:g,s

# Search for posts with a score over 100
score:>100
```

### Order

```
# Order search results in ascending order based on post ID
order:id
order:id_asc

# Order search results in descending order based on post ID
order:id_desc

# Order search results in descending order based on post score
order:score

# Order posts by MD5. Ordering posts in a random (but fixed) order.
order:md5
```

---

## License

Licensed under the GNU AGPL v3.0. See [LICENSE](./LICENSE)

---

## Acknowledgement

This project was inspired by the original 
[DanbooruDownloader](https://github.com/<original_repo_link>) project.

The original implementation was written in C# and released under the MIT License.
While the overall idea of downloading Danbooru posts is similar, this repository
is a complete reimplementation written in Python with a different architecture.