from dataclasses import dataclass

@dataclass
class FileEntry:
    """Data model for a file system entry"""
    name: str
    path: str
    is_dir: bool
    size: str = ""
    date: str = ""
    permissions: str = ""
