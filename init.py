"""
This module handles the initialization of the Video module, including
finding or creating the 'project.ini' file and generating a module-specific
configuration file.
"""

import os
from pathlib import Path
import configparser
import logging

from typing import Optional

logger = logging.getLogger(__name__)

def generate_empty_config(file_path: str | Path) -> None:
    """
    Generates an empty configuration file with default sections.

    Args:
        file_path (str | Path): The path where the configuration file will be created.
    """
    config = configparser.ConfigParser()

    config['FilePaths'] = {}
    config['ToolPaths'] = {}
    config['Configs'] = {}

    file_path = Path(file_path).resolve()
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, 'w') as configfile:
        config.write(configfile)

    logger.info(f"Default configuration file created at {file_path}")


def find_or_create_project_ini(start_path: Optional[Path] = None) -> tuple[Path, str]:
    """
    Finds or creates a 'project.ini' file in the specified directory or its parent directories.

    Args:
        start_path (Path, optional): The starting directory to search for 'project.ini'. Defaults to the script's directory.

    Returns:
        tuple[Path, str]: A tuple containing the resolved path to 'project.ini' and the mode ('independent' or 'module').
    """
    if start_path is None:
        start_path = Path(__file__).resolve().parent

    current = start_path
    max_levels = 2
    project_ini = None
    mode = "independent"

    for level in range(max_levels + 1):
        candidate = current / "project.ini"
        if candidate.exists():
            project_ini = candidate
            # If found above local folder, it's part of a larger project = module
            if level > 0:
                mode = "module"
            break
        current = current.parent

    if project_ini is None:
        # Create default project.ini using reusable config generator
        project_ini = start_path / "project.ini"
        generate_empty_config(project_ini)
        mode = "independent"
    else:
        logger.info(f"Found project.ini at {project_ini}")

    return project_ini.resolve(), mode


def create_module_conf(module_name: str, project_ini_path: Path, mode: str) -> tuple[Path, configparser.ConfigParser]:
    """
    Creates a configuration file for the specified module.

    Args:
        module_name (str): The name of the module.
        project_ini_path (Path): The path to the project.ini file.
        mode (str): The mode of the module (e.g., 'independent' or 'module').

    Returns:
        tuple[Path, configparser.ConfigParser]: A tuple containing the resolved path to the created configuration file and the config object.
    """
    module_dir = Path(__file__).resolve().parent
    conf_path = module_dir / "conf.ini"

    conf = configparser.ConfigParser()
    conf['MODULE'] = {
        'module_name': module_name,
        'mode': mode,
        'project_ini_path': str(project_ini_path)
    }

    with open(conf_path, 'w') as f:
        conf.write(f)
    logger.info(f"Created conf.ini for module '{module_name}' at {conf_path}")

    return conf_path.resolve(), conf


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    project_ini, mode = find_or_create_project_ini()
    create_module_conf(module_name="Video", project_ini_path=project_ini, mode=mode)
