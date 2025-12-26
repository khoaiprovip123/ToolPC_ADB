from dataclasses import dataclass

@dataclass
class AppInfo:
    """Application information model"""
    package: str
    name: str
    version: str
    version_code: int
    is_system: bool
    is_enabled: bool
    is_archived: bool  # New field for uninstalled system apps
    size: int  # bytes
    install_time: int  # timestamp
    update_time: int
    path: str
