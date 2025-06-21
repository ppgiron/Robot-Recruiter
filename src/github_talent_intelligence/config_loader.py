import os

import yaml


def load_categories(config_path=None):
    """
    Load categories from the config.yaml file.
    If config_path is not provided, use the default in the current directory.
    """
    if config_path is None:
        # Default to config.yaml in the same directory as this file
        config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    return config.get("categories", {})
