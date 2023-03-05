import concurrent
import logging
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, Future
import time
from os import cpu_count
from typing import List, Tuple, Callable, Optional

from markdown_toolset.article_processor import ArticleProcessor, IN_FORMATS_LIST, OUT_FORMATS_LIST
from markdown_toolset.deduplicators import DeduplicationVariant

from .item_parameters import ItemParameters


_logger = logging.getLogger(__name__)


class AppLogic:
    """
    Main logic class.
    """
    def __init__(self, done_callback: Callable,
                 on_item_success: Optional[Callable] = None,
                 on_item_fail: Optional[Callable] = None):
        self._core_count = cpu_count() + 1
        self._pool = ThreadPoolExecutor(max_workers=self._core_count)
        self._futures = []
        self._done_callback = done_callback
        self._on_item_success = on_item_success
        self._on_item_fail = on_item_fail

    def add_items(self, items: List[Tuple[str, int, ItemParameters]]):
        if self.running:
            return

        self._futures.clear()
        for i in items:
            _logger.debug('Adding worker for "%s"', i[0])
            f = self._pool.submit(self._worker, *i)
            self._futures.append(f)
            f.add_done_callback(self._future_done)

    @property
    def running(self) -> bool:
        for f in self._futures:
            if f.running():
                return True
        return False

    def stop(self):
        for f in self._futures:
            f: Future
            f.cancel()

        for f in self._futures:
            f.result()

    def _future_done(self, future: Future):
        print('Callback', future)

        result = future.result()

        if result and self._on_item_success is not None:
            self._on_item_success(*result)
        elif not result and self._on_item_fail is not None:
            self._on_item_fail(*result)

        if not self.running:
            self._done_callback()

    @staticmethod
    def _create_article_processor(**kwargs):
        return ArticleProcessor(**kwargs)

    def _worker(self, file_path: str, index: int, item: ItemParameters):
        _logger.debug('Starting worker for "%s"', file_path)
        a_proc = self._create_article_processor(
            article_file_path_or_url=file_path,
            skip_list=item.skip_list, downloading_timeout=item.downloading_timeout,
            output_format=OUT_FORMATS_LIST[item.output_format], output_path=item.output_path,
            remove_source=item.remove_source, images_public_path=item.images_public_path,
            input_formats=IN_FORMATS_LIST, skip_all_incorrect=item.skip_all_incorrect,
            download_incorrect_mime=item.download_incorrect_mime,
            deduplication_type=[i for i in DeduplicationVariant.__members__.values()][item.deduplication_type],
            images_dirname=item.images_dir_name,
            save_hierarchy=item.save_hierarchy
        )
        _logger.info('Processing "%s"', file_path)
        output_file_path = a_proc.process()
        _logger.info('Processing "%s" completed', file_path)
        return index, output_file_path
