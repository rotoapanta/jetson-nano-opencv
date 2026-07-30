#!/usr/bin/env python3
import logging, os
from logging.handlers import RotatingFileHandler

def setup_logging(log_file, level_name):
    level = getattr(logging, str(level_name).upper(), logging.INFO)
    directory = os.path.dirname(log_file)
    if directory and not os.path.isdir(directory):
        os.makedirs(directory)
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    root = logging.getLogger()
    root.setLevel(level)
    if not root.handlers:
        console = logging.StreamHandler()
        console.setFormatter(fmt)
        root.addHandler(console)
        file_handler = RotatingFileHandler(
            log_file, maxBytes=5 * 1024 * 1024, backupCount=5
        )
        file_handler.setFormatter(fmt)
        root.addHandler(file_handler)
    return logging.getLogger("jetson-vision")
