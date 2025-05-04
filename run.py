import sys
import os
import time
from pathlib import Path

from .printer import print, print_error, print_verbose, print_debug, colours

from . import conf
from .Tools.process.Rename import RenameFolders
from .Tools.process.QuickBMS import QBMS_MAIN
from .Tools.process.Flat import flat

def main() -> None:
    """Main function to determine and execute the program mode."""

    module_dir = Path(__file__).resolve().parent

    print(colours.CYAN, "Running init.")
    #time.sleep(5)
    project_dir = conf.main(module_dir)
    print(colours.GREEN, "Completed init.")

    #time.sleep(5)
    print(colours.CYAN, "Running rename folders.")
    #time.sleep(5)
    RenameFolders.main(project_dir, module_dir)
    print(colours.GREEN, "Completed rename folders.")

    #time.sleep(5)
    print(colours.CYAN, "Running QuickBMS.")
    #time.sleep(5)
    QBMS_MAIN.main(project_dir, module_dir)
    print(colours.GREEN, "Completed QuickBMS.")

    #time.sleep(5)
    print(colours.CYAN, "Running flattener.")
    #time.sleep(5)
    flat.main(project_dir, module_dir)
    print(colours.GREEN, "Completed flattener.")


if __name__ == "__main__":
    main()
