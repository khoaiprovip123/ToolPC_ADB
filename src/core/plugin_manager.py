# src/core/plugin_manager.py
"""
Core Plugin Manager Logic
Handles discovery and loading of external plugins.
"""

import os
import sys
import importlib.util
import logging
from dataclasses import dataclass
from typing import List, Optional, Any

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class PluginInfo:
    name: str
    version: str
    description: str
    author: str
    file_path: str
    module: Any
    enabled: bool = True

class PluginManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PluginManager, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance
        
    def __init__(self):
        if self.initialized:
            return
        self.plugins: List[PluginInfo] = []
        self.plugins_dir = os.path.join(os.getcwd(), 'plugins')
        self.context = None  # To be set by MainWindow
        self.initialized = True
        
        # Ensure plugins dir exists
        if not os.path.exists(self.plugins_dir):
            os.makedirs(self.plugins_dir)
            
            # Create a sample plugin README
            with open(os.path.join(self.plugins_dir, 'README.txt'), 'w', encoding='utf-8') as f:
                f.write("Place your python plugin files (.py) here.\n")
                f.write("Plugin file structure example:\n\n")
                f.write("NAME = 'My Plugin'\n")
                f.write("VERSION = '1.0'\n")
                f.write("DESCRIPTION = 'Does something cool'\n")
                f.write("AUTHOR = 'You'\n\n")
                f.write("def on_load(context):\n")
                f.write("    print('Plugin Loaded!')\n")
                f.write("    # context is the MainWindow instance\n")

    def set_context(self, context):
        """Set the application context (MainWindow) for plugins to use"""
        self.context = context

    def discover_plugins(self):
        """Scan plugins directory for .py files"""
        self.plugins.clear()
        if not os.path.exists(self.plugins_dir):
            return

        for filename in os.listdir(self.plugins_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                self.load_plugin(os.path.join(self.plugins_dir, filename))

    def load_plugin(self, file_path: str):
        """Load a single plugin file"""
        try:
            module_name = os.path.splitext(os.path.basename(file_path))[0]
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                
                # Verify required attributes
                name = getattr(module, 'NAME', module_name)
                version = getattr(module, 'VERSION', '0.0.1')
                desc = getattr(module, 'DESCRIPTION', 'No description')
                author = getattr(module, 'AUTHOR', 'Unknown')
                
                plugin_info = PluginInfo(
                    name=name,
                    version=str(version),
                    description=desc,
                    author=author,
                    file_path=file_path,
                    module=module
                )
                
                self.plugins.append(plugin_info)
                logger.info(f"Loaded plugin: {name} v{version}")
                
                # Execute on_load if context exists
                if self.context and hasattr(module, 'on_load'):
                    try:
                        module.on_load(self.context)
                    except Exception as e:
                        logger.error(f"Error initializing plugin {name}: {e}")
                        
        except Exception as e:
            logger.error(f"Failed to load plugin {file_path}: {e}")

    def reload_plugins(self):
        """Reload all plugins"""
        self.discover_plugins()

