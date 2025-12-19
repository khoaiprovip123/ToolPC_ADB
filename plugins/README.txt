Place your python plugin files (.py) here.
Plugin file structure example:

NAME = 'My Plugin'
VERSION = '1.0'
DESCRIPTION = 'Does something cool'
AUTHOR = 'You'

def on_load(context):
    print('Plugin Loaded!')
    # context is the MainWindow instance
