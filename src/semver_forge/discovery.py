from pathlib import Path
from .git import root
from .config import find_config

def discover(path=None):
    repo=root(path)
    return repo, find_config(repo)
