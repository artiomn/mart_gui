from pathlib import Path
from typing import Union, List, Optional


class ItemParameters:
    """

    """
    default_remove_source = 1
    default_save_hierarchy = 1
    default_download_incorrect_mime = 1
    default_skip_all_incorrect = 1
    default_downloading_timeout = -1
    default_output_format = 0
    default_input_format = 0
    default_deduplication_type = 0
    default_output_path = Path.cwd().as_posix()
    default_images_public_path = ''
    default_images_dir_name = ''

    def __init__(self):
        self.downloaded: bool = False
        self.skip_list: Union[str, List[str]] = []
        self.downloading_timeout: int = self.default_downloading_timeout
        self.output_format: int = self.default_output_format
        self.output_path: str = self.default_output_path
        self.images_public_path: str = self.default_images_public_path
        self.input_format: int = self.default_input_format
        self.deduplication_type: int = self.default_deduplication_type
        self.images_dir_name: str = 'images'

        self.skip_all_incorrect: int = 0
        self.download_incorrect_mime: int = 0
        self.remove_source: int = 0
        self.save_hierarchy: int = 0

        self.output_file_path: Optional[str] = None

    def set_default(self, property_name: str):
        setattr(self, property_name, getattr(self, f'default_{property_name}'))
