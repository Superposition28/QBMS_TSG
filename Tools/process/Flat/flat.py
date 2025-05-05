# flat.py
# Applies flattening universally from RootDir's *contents* directly into DestinationDir.
# python flat.py ".\Source\RootDir" ".\Destination\Flattened"

import sys
import os
import shutil
import hashlib
import re
import time
import json
from pathlib import Path
try:
    from ....printer import print, print_error, print_verbose, print_debug, colours
except ImportError:
    from printer import print, print_error, print_verbose, print_debug, colours


# -- Begin Global Variables --

global root_dir, destination_dir, VERBOSE, DEBUG, SANITIZATION_RULES

# --- Global Flags ---
VERBOSE = "VERBOSE" in os.environ and os.environ["VERBOSE"].lower() == "true"
DEBUG = "DEBUG" in os.environ and os.environ["DEBUG"].lower() == "true"


# --- Sanitization Rules ---
SANITIZATION_RULES = [
    # "build++PS3++pal_en" → "EU_EN"
    {"pattern": re.escape("build++PS3++pal_en"), "replacement": "EU_EN", "is_regex": True},

    # "story_mode++story_mode_design.str++story_mode_design_str" → "story_mode_design_STR"
    {"pattern": re.escape("story_mode++story_mode_design.str++story_mode_design_str"), "replacement": "story_mode_design_STR", "is_regex": True},

    # "challenge_mode++challenge_mode_designSTR" → "challenge_mode_design_STR"
    {"pattern": re.escape("challenge_mode++challenge_mode_designSTR"), "replacement": "challenge_mode_design_STR", "is_regex": True},

    # "texture_dictionary++whatever++chars" → "Textures"
    {"pattern": r"^texture_dictionary\+\+.*?\+\+chars$", "replacement": "Textures", "is_regex": True},

    # "ASSET_RWS++texture_dictionary++GlobalFolder++costumes" → "RWS+Textures"
    {"pattern": re.escape("ASSET_RWS++texture_dictionary++GlobalFolder++costumes"), "replacement": "RWS+Textures", "is_regex": True},

    # "texture_dictionary++vehicles++design" → "vehicles_Textures"
    {"pattern": r"^texture_dictionary\+\+(.*?)\+\+design$", "replacement": r"\1_Textures", "is_regex": True},

    #\ASSET_RWS\texture_dictionary++gamehub  → ASSET_RWS\texture_dictionary
    {"pattern": r"^ASSET_RWS\\texture_dictionary\+\+gamehub$", "replacement": r"ASSET_RWS\\texture_dictionary", "is_regex": True},


    # "vehicle_Textures++Act_1_folderstream" → "Textures"
    {"pattern": r"^.*?_Textures\+\+Act_.*_folderstream$", "replacement": "Textures", "is_regex": True},

    # "{something}.str++{something}_str" → "{something}STR"
    {"pattern": r"^(.*)\.str\+\+(.*)_str$", "replacement": r"\1STR", "is_regex": True},

    # "assets_rws++props++props" → "ASSET_RWS"
    {"pattern": r"^assets_rws\+\+(.*?)\+\+\1$", "replacement": "ASSET_RWS", "is_regex": True},

    # "audio++{something}" → ""
    {"pattern": r"^audio\+\+", "replacement": "", "is_regex": True},

    # "streams++colossaldonut++story_mode" → "streams"
    #{"pattern": r"streams\+\+[^\\]+\+\+[^\\]+", "replacement": "streams++level++story", "is_regex": True}
    {"pattern": r"streams\+\+[^\\]+\+\+[^\\]+", "replacement": "streams", "is_regex": True}

    #81DE1738_str++EU_EN++assets++localization → EN++EU_EN++assets++local
    {"pattern": r"^81DE1738_str\+\+EU_EN\+\+assets\+\+localization$", "replacement": "EN++EU_EN++assets++local", "is_regex": True},
    #CD99D1BE_str++EU_EN++assets++localization → FR++EU_EN++assets++local
    {"pattern": r"^CD99D1BE_str\+\+EU_EN\+\+assets\+\+localization$", "replacement": "FR++EU_EN++assets++local", "is_regex": True},
    #6255953C_str++EU_EN++assets++localization → IT++EU_EN++assets++local
    {"pattern": r"^6255953C_str\+\+EU_EN\+\+assets\+\+localization$", "replacement": "IT++EU_EN++assets++local", "is_regex": True},
    #2919CD42_str++EU_EN++assets++localization → ES++EU_EN++assets++local
    {"pattern": r"^2919CD42_str\+\+EU_EN\+\+assets\+\+localization$", "replacement": "ES++EU_EN++assets++local", "is_regex": True},
    #95F47026_str++EU_EN++assets++localization → SS++EU_EN++assets++local
    {"pattern": r"^95F47026_str\+\+EU_EN\+\+assets\+\+localization$", "replacement": "SS++EU_EN++assets++local", "is_regex": True},

]

# --- Hash Calculation ---
def get_file_sha256(file_path: str) -> str:
    """
    Calculate the SHA256 hash of a file.

    Args:
        file_path (str): The path to the file.

    Returns:
        str: The SHA256 hash of the file as a hexadecimal string.
    """
    try:
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found at '{file_path}'.")
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            # Read and update hash string value in blocks of 4K
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as ex:
        print_error(f"Error calculating SHA256 hash for file '{file_path}': {ex}")
        sys.exit(1)

def sanitize_name(input_name: str) -> str:
    """
    Sanitize the given input name based on predefined sanitization rules.

    Args:
        input_name (str): The name to be sanitized.

    Returns:
        str: The sanitized name after applying the rules.
    """
    print_verbose(f"Sanitizing name: '{input_name}'")
    output_name = input_name
    for rule in SANITIZATION_RULES:
        before = output_name
        try:
            if rule["is_regex"]:
                output_name = re.sub(rule["pattern"], rule["replacement"], output_name)
            else:
                # For non-regex, treat pattern as literal string
                output_name = output_name.replace(rule["pattern"], rule["replacement"])
            if before != output_name:
                print_verbose(f"Rule applied: Pattern='{rule['pattern']}', Replacement='{rule['replacement']}'")
                print_verbose(f"  Before: '{before}'")
                print_verbose(f"  After:  '{output_name}'")
        except re.error as e:
            print_error(f"Regex error in rule pattern '{rule['pattern']}': {e}")
            # Decide whether to continue or exit
            # sys.exit(1)
    print_verbose(f"Sanitized name result: '{output_name}'")
    return output_name

# --- Recursive Processing Function ---
def process_source_directory(source_path, destination_parent_path, accumulated_flattened_name, base_destination_dir, original_root_dir_abs):
    print(colours.GREEN, f"Processing Source Directory: '{source_path}'")
    print(colours.DARK_GREEN, f" -> Destination Parent Path: '{destination_parent_path}'")
    print(colours.DARK_GREEN, f" -> Accumulated Flattened Name: '{accumulated_flattened_name}'")
    print_verbose(f"Processing Source: '{source_path}' -> Dest Parent: '{destination_parent_path}' (Accumulated Name: '{accumulated_flattened_name}')")

    if accumulated_flattened_name:
        accumulated_flattened_name = sanitize_name(accumulated_flattened_name)

    child_dirs = []
    child_files = []
    child_count = 0

    try:
        # Get direct children
        for item in os.listdir(source_path):
            item_path = os.path.join(source_path, item)
            if os.path.isdir(item_path):
                child_dirs.append(item_path)
            elif os.path.isfile(item_path):
                child_files.append(item_path)
        child_count = len(child_dirs) + len(child_files)
    except Exception as ex:
        print_error(f"Error reading contents of '{source_path}': {ex}.")
        sys.exit(1)

    # --- Case 1: Flattening Condition ---
    if child_count == 1 and len(child_dirs) == 1:
        single_child_dir = child_dirs[0]
        source_base_name = os.path.basename(source_path)
        child_base_name = os.path.basename(single_child_dir)

        new_accumulated_name = f"{source_base_name}++{child_base_name}" if not accumulated_flattened_name \
                            else f"{accumulated_flattened_name}++{child_base_name}"

        print_verbose(f"Flattening: '{source_base_name}' contains only '{child_base_name}'. New accumulated name: '{new_accumulated_name}'")
        print_debug(f"Flattening {source_path} into {single_child_dir}")

        # Recurse into the single child directory
        process_source_directory(single_child_dir, destination_parent_path, new_accumulated_name, base_destination_dir, original_root_dir_abs)
        return

    # --- Case 2: Branching or Terminal Condition ---
    else:
        final_dir_name = os.path.basename(source_path) if not accumulated_flattened_name else accumulated_flattened_name

        final_dest_dir_path = ""
        is_processing_actual_root_dir = (source_path == original_root_dir_abs and not accumulated_flattened_name)

        # *** Handle Root Directory ***
        if is_processing_actual_root_dir:
            final_dest_dir_path = destination_parent_path
            print_verbose(f"Processing root directory's children directly into '{final_dest_dir_path}'")
            # time.sleep(1) # Optional pause
        else:
            if not final_dir_name: # Check against creating folders without name
                print_error(f"Calculated final directory name is empty for source '{source_path}'. This shouldn't happen unless processing root drive. Aborting.")
                sys.exit(1)

            final_dest_dir_path = os.path.join(destination_parent_path, final_dir_name)

            if not os.path.exists(final_dest_dir_path):
                try:
                    relative_dest_path = os.path.relpath(final_dest_dir_path, base_destination_dir)
                    print(colours.GREEN, f"  Creating directory: '{relative_dest_path}'")
                    print_verbose(f"Creating concrete destination directory: '{final_dest_dir_path}'")
                    os.makedirs(final_dest_dir_path)
                except Exception as ex:
                    print_error(f"Error creating directory '{final_dest_dir_path}': {ex}.")
                    sys.exit(1)
            else:
                print_verbose(f"Destination directory '{final_dest_dir_path}' already exists.")
            # time.sleep(1) # Optional pause

        # Process Files
        if child_files:
            print_verbose(f"Processing {len(child_files)} files in '{source_path}'.")
            for file_path in child_files:
                file_name = os.path.basename(file_path)
                destination_file_path = os.path.join(final_dest_dir_path, file_name)
                relative_dest_file_path = os.path.relpath(destination_file_path, base_destination_dir)

                try:
                    print(colours.BLUE, f"    Copying file: '{file_name}' -> '{relative_dest_file_path}'")
                    print_verbose(f"Copying file '{file_path}' to '{destination_file_path}'")
                    shutil.copy2(file_path, destination_file_path) # copy2 preserves metadata

                    # Perform hash check
                    print_verbose(f"Verifying hash for '{file_name}'...")
                    source_hash = get_file_sha256(file_path)
                    destination_hash = get_file_sha256(destination_file_path)

                    if source_hash != destination_hash:
                        print_error(f"Hash mismatch for file '{file_name}'. Dest: '{relative_dest_file_path}'.")
                        print_error(f"  Source SHA256: {source_hash}")
                        print_error(f"  Destination SHA256: {destination_hash}")
                        sys.exit(1)
                    else:
                        print_verbose(f"SHA256 hash match confirmed for '{file_name}'.")
                except Exception as ex:
                    print_error(f"Error during copy/verify for file '{file_path}' to '{destination_file_path}': {ex}.")
                    sys.exit(1)

        # Process Subdirectories
        if child_dirs:
            print_verbose(f"Processing {len(child_dirs)} subdirectories in '{source_path}'.")
            for dir_path in child_dirs:
                process_source_directory(dir_path,
                                    final_dest_dir_path, # New parent
                                    "",                  # Reset accumulated name
                                    base_destination_dir,
                                    original_root_dir_abs)

        if child_count == 0:
            print_verbose(f"Source directory '{source_path}' is empty.")

        return # Processing for this level complete

# --- End Main Functions ---

# --- Main Function ---

def main(project_dir: str, module_dir: str) -> None:
    """
    Main function to execute the universal recursive flattening process.

    Args:
        project_dir (str): The directory containing the project configuration.
        module_dir (str): The directory containing the module files.

    Returns:
        None
    """

    global root_dir, destination_dir

    # Load configuration from JSON file
    try:
        with open(os.path.join(project_dir, "project.json"), 'r') as f:
            config = json.load(f)["Extract"]
    except Exception as e:
        print_error(f"Error loading project.json: {e}")
        sys.exit(1)

    try:
        root_dir = config["Directories"]["OutDirectory"]
        destination_dir = config["Directories"]["FlatDirectory"]
    except Exception as e:
        print_error(f"Error reading paths from project.json: {e}")
        sys.exit(1)


    # --- Main Script ---
    print(colours.YELLOW, "Starting universal recursive flattening copy process (root contents -> destination)...")
    print(colours.CYAN, f"Source Root Directory: '{root_dir}'")
    print(colours.CYAN, f"Destination Directory: '{destination_dir}'")

    root_dir_abs = os.path.abspath(root_dir)
    destination_dir_abs = os.path.abspath(destination_dir)

    # Validate RootDir
    if not os.path.isdir(root_dir_abs):
        print_error(f"Root directory '{root_dir_abs}' not found or is not a directory.")
        sys.exit(1)

    # Ensure DestinationDir exists
    if not os.path.exists(destination_dir_abs):
        print(colours.YELLOW, f"Destination directory '{destination_dir_abs}' not found. Creating...")
        try:
            os.makedirs(destination_dir_abs)
            print(colours.GREEN, "Destination directory created successfully.")
        except Exception as ex:
            print_error(f"Failed to create destination directory '{destination_dir_abs}': {ex}")
            sys.exit(1)
    elif not os.path.isdir(destination_dir_abs):
        print_error(f"Destination path '{destination_dir_abs}' exists but is not a directory.")
        sys.exit(1)


    print(colours.YELLOW, "Starting processing from root directory's contents...")
    print(colours.GRAY, "--------------------------------------------------")

    try:
        # Initial call to the recursive function
        process_source_directory(root_dir_abs, destination_dir_abs, "", destination_dir_abs, root_dir_abs)
    except Exception as ex:
        print_error(f"An unexpected error occurred during processing: {ex}")
        import traceback
        print_error(traceback.format_exc())
        sys.exit(1)

    print(colours.GRAY, "--------------------------------------------------")
    print(colours.GREEN, "Universal recursive flattening copy process completed.")
    print(colours.GREEN, f"Source directory contents from: '{root_dir_abs}'")
    print(colours.GREEN, f"Destination directory: '{destination_dir_abs}'")

# --- End Main Function ---

