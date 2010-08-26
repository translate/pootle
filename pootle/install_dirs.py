import os

CONFIG_DIR  = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR    = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
SOURCE_DIR  = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
WORKING_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

def config_path(filename):
    return os.path.join(CONFIG_DIR, filename)
def data_path(filename):
    return os.path.join(DATA_DIR, filename)
def source_path(filename):
    return os.path.join(SOURCE_DIR, filename)
def working_path(filename):
    return os.path.join(WORKING_DIR, filename)
