import sys
import configparser
import os
import shutil  # Added missing import

from . import init
from .Tools.process.Rename import RenameFolders
from .Tools.process.QuickBMS import QBMS_MAIN

def read_config(file_path: str) -> str:
    """Reads and displays the contents of a configuration file."""
    config = configparser.ConfigParser()
    config.read(file_path)

    strdirectory = config.get('Directories', 'strdirectory')
    outdirectory = config.get('Directories', 'outdirectory')

    return strdirectory, outdirectory

def main() -> None:
    """Main function to determine and execute the program mode."""
    mode = init.main()
    if mode == "independent":
        print("Running in independent mode.")
        strdirectory, outdirectory = read_config("bmsConf.ini")
        print(f"Directory: {strdirectory}")
        if not os.path.exists(strdirectory):
            userinput = input("enter path to your TheSimpsonGame USRDIR/ folder: ")
            dirtocopy = userinput
            def copy_with_progress(src, dst):
                for root, dirs, files in os.walk(src):
                    for dir_name in dirs:
                        dir_path = os.path.join(root, dir_name)
                        relative_path = os.path.relpath(dir_path, src)
                        target_dir = os.path.join(dst, relative_path)
                        os.makedirs(target_dir, exist_ok=True)
                    for file_name in files:
                        file_path = os.path.join(root, file_name)
                        relative_path = os.path.relpath(file_path, src)
                        target_file = os.path.join(dst, relative_path)
                        shutil.copy2(file_path, target_file)
                        print(f"Copied: {file_path} -> {target_file}")

            # copy files from dirtocopy to and create strdirectory
            os.makedirs(strdirectory, exist_ok=True)
            copy_with_progress(dirtocopy, strdirectory)

    elif mode == "module":
        print("Running in module mode.")

    RenameFolders.main()

    QBMS_MAIN.main()

if __name__ == "__main__":
    main()
