#!/bin/env python3

import sys
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import QAbstractItemView

from PyQt6.QtWidgets import QApplication

from markdown_toolset.article_processor import ArticleProcessor

from src.ui_classes import MainUi


def create_qt_ui(args):
    app = QApplication(args)

    window = MainUi()

    app.exec()


def create_article_processor():
    ArticleProcessor(article_file_path_or_url)

                 # skip_list: Union[str, List[str]] = '', downloading_timeout: int = -1,
                 # output_format: str = OUT_FORMATS_LIST[0], output_path: Union[Path, str] = Path.cwd(),
                 # remove_source: bool = False, images_public_path: Union[Path, str] = '',
                 # input_formats: List[str] = tuple(IN_FORMATS_LIST), skip_all_incorrect: bool = False,
                 # download_incorrect_mime: bool = False,
                 # deduplication_type: DeduplicationVariant = DeduplicationVariant.DISABLED,
                 # images_dirname: Union[Path, str] = 'images',
                 # save_hierarchy: bool = False):

create_qt_ui(sys.argv)
