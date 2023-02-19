from pathlib import Path
from typing import Union, List, Optional


class ItemParameters:
    def __init__(self):
        self.downloaded: bool = False
        self.skip_list: Union[str, List[str]] = []
        self.downloading_timeout: int = -1
        self.output_format: int = 0
        self.output_path: str = Path.cwd().as_posix()
        self.images_public_path: str = ''
        self.input_format: int = 0
        self.deduplication_type: int = 0
        self.images_dir_name: str = 'images'

        self.skip_all_incorrect: bool = False
        self.download_incorrect_mime: bool = False
        self.remove_source: bool = False
        self.save_hierarchy: bool = False

        self.output_file_path: Optional[str] = None
