# flat.py
# Applies flattening universally from RootDir's *contents* directly into DestinationDir.
# python flat.py ".\Source\RootDir" ".\Destination\Flattened"

import sys
import os
import shutil
import hashlib
import re
import time
import configparser
from pathlib import Path

# --- ANSI Color Codes ---
class Colors:
    RESET = '\033[0m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    GRAY = '\033[90m'
    DARK_GREEN = '\033[32m' # Using standard green for dark green


# -- Begin Global Variables --

global root_dir, destination_dir, VERBOSE, DEBUG, SANITIZATION_RULES

# --- Global Flags ---
VERBOSE = "VERBOSE" in os.environ and os.environ["VERBOSE"].lower() == "true"
DEBUG = "DEBUG" in os.environ and os.environ["DEBUG"].lower() == "true"

# --- Sanitization Rules ---
SANITIZATION_RULES = [
    {"pattern": re.escape("build++PS3++pal_en"), "replacement": "EU_EN", "is_regex": True},
    {"pattern": re.escape("story_mode++story_mode_design.str++story_mode_design_str"), "replacement": "story_mode_design_STR", "is_regex": True},
    {"pattern": re.escape("challenge_mode++challenge_mode_designSTR"), "replacement": "challenge_mode_design_STR", "is_regex": True},
    {"pattern": r"^texture_dictionary\+\+.*?\+\+chars$", "replacement": "Textures", "is_regex": True},
    {"pattern": re.escape("ASSET_RWS++texture_dictionary++GlobalFolder++costumes"), "replacement": "RWS+Textures", "is_regex": True},
    {"pattern": r"^texture_dictionary\+\+(.*?)\+\+design$", "replacement": r"\1_Textures", "is_regex": True},
    {"pattern": r"^.*?_Textures\+\+Act_.*_folderstream$", "replacement": "Textures", "is_regex": True},
    {"pattern": r"^(.*)\.str\+\+(.*)_str$", "replacement": r"\1STR", "is_regex": True},
    {"pattern": r"^assets_rws\+\+(.*?)\+\+\1$", "replacement": "ASSET_RWS", "is_regex": True},
    {"pattern": r"^audio\+\+", "replacement": "", "is_regex": True}
]

# -- End Global Variables --
# -- Begin Helper Functions --

# --- Logging Functions ---
def log(message, color=Colors.GRAY):
    print(f"{color}{message}{Colors.RESET}")

def log_info(message):
    log(message, Colors.CYAN)

def log_success(message):
    log(message, Colors.GREEN)

def log_warning(message):
    log(message, Colors.YELLOW)

def log_error(message):
    print(f"{Colors.RED}{message}{Colors.RESET}", file=sys.stderr)

def log_verbose(message):
    # Set VERBOSE = True to enable verbose logging
    if VERBOSE:
        log(f"VERBOSE: {message}", Colors.GRAY)

def log_debug(message):
    # Set DEBUG = True to enable debug logging
    if DEBUG:
        log(f"DEBUG: {message}", Colors.MAGENTA)

# -- End Helper Functions --
# -- Begin Main Functions --

# --- Hash Calculation ---
def get_file_sha256(file_path):
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
        log_error(f"Error calculating SHA256 hash for file '{file_path}': {ex}")
        sys.exit(1)

def sanitize_name(input_name):
    log_verbose(f"Sanitizing name: '{input_name}'")
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
                log_verbose(f"Rule applied: Pattern='{rule['pattern']}', Replacement='{rule['replacement']}'")
                log_verbose(f"  Before: '{before}'")
                log_verbose(f"  After:  '{output_name}'")
        except re.error as e:
            log_error(f"Regex error in rule pattern '{rule['pattern']}': {e}")
            # Decide whether to continue or exit
            # sys.exit(1)
    log_verbose(f"Sanitized name result: '{output_name}'")
    return output_name

# --- Recursive Processing Function ---
def process_source_directory(source_path, destination_parent_path, accumulated_flattened_name, base_destination_dir, original_root_dir_abs):
    log(f"Processing Source Directory: '{source_path}'", Colors.GREEN)
    log(f" -> Destination Parent Path: '{destination_parent_path}'", Colors.DARK_GREEN)
    log(f" -> Accumulated Flattened Name: '{accumulated_flattened_name}'", Colors.DARK_GREEN)
    log_verbose(f"Processing Source: '{source_path}' -> Dest Parent: '{destination_parent_path}' (Accumulated Name: '{accumulated_flattened_name}')")

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
        log_error(f"Error reading contents of '{source_path}': {ex}.")
        sys.exit(1)

    # --- Case 1: Flattening Condition ---
    if child_count == 1 and len(child_dirs) == 1:
        single_child_dir = child_dirs[0]
        source_base_name = os.path.basename(source_path)
        child_base_name = os.path.basename(single_child_dir)

        new_accumulated_name = f"{source_base_name}++{child_base_name}" if not accumulated_flattened_name \
                            else f"{accumulated_flattened_name}++{child_base_name}"

        log_verbose(f"Flattening: '{source_base_name}' contains only '{child_base_name}'. New accumulated name: '{new_accumulated_name}'")
        log_debug(f"Flattening {source_path} into {single_child_dir}")

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
            log_verbose(f"Processing root directory's children directly into '{final_dest_dir_path}'")
            # time.sleep(1) # Optional pause
        else:
            if not final_dir_name: # Check against creating folders without name
                log_error(f"Calculated final directory name is empty for source '{source_path}'. This shouldn't happen unless processing root drive. Aborting.")
                sys.exit(1)

            final_dest_dir_path = os.path.join(destination_parent_path, final_dir_name)

            if not os.path.exists(final_dest_dir_path):
                try:
                    relative_dest_path = os.path.relpath(final_dest_dir_path, base_destination_dir)
                    log(f"  Creating directory: '{relative_dest_path}'", Colors.GREEN)
                    log_verbose(f"Creating concrete destination directory: '{final_dest_dir_path}'")
                    os.makedirs(final_dest_dir_path)
                except Exception as ex:
                    log_error(f"Error creating directory '{final_dest_dir_path}': {ex}.")
                    sys.exit(1)
            else:
                log_verbose(f"Destination directory '{final_dest_dir_path}' already exists.")
            # time.sleep(1) # Optional pause

        # Process Files
        if child_files:
            log_verbose(f"Processing {len(child_files)} files in '{source_path}'.")
            for file_path in child_files:
                file_name = os.path.basename(file_path)
                destination_file_path = os.path.join(final_dest_dir_path, file_name)
                relative_dest_file_path = os.path.relpath(destination_file_path, base_destination_dir)

                try:
                    log(f"    Copying file: '{file_name}' -> '{relative_dest_file_path}'", Colors.BLUE)
                    log_verbose(f"Copying file '{file_path}' to '{destination_file_path}'")
                    shutil.copy2(file_path, destination_file_path) # copy2 preserves metadata

                    # Perform hash check
                    log_verbose(f"Verifying hash for '{file_name}'...")
                    source_hash = get_file_sha256(file_path)
                    destination_hash = get_file_sha256(destination_file_path)

                    if source_hash != destination_hash:
                        log_error(f"Hash mismatch for file '{file_name}'. Dest: '{relative_dest_file_path}'.")
                        log_error(f"  Source SHA256: {source_hash}")
                        log_error(f"  Destination SHA256: {destination_hash}")
                        sys.exit(1)
                    else:
                        log_verbose(f"SHA256 hash match confirmed for '{file_name}'.")
                except Exception as ex:
                    log_error(f"Error during copy/verify for file '{file_path}' to '{destination_file_path}': {ex}.")
                    sys.exit(1)

        # Process Subdirectories
        if child_dirs:
            log_verbose(f"Processing {len(child_dirs)} subdirectories in '{source_path}'.")
            for dir_path in child_dirs:
                process_source_directory(dir_path,
                                    final_dest_dir_path, # New parent
                                    "",                  # Reset accumulated name
                                    base_destination_dir,
                                    original_root_dir_abs)

        if child_count == 0:
            log_verbose(f"Source directory '{source_path}' is empty.")

        return # Processing for this level complete

# --- End Main Functions ---

def read_config(file_path: str) -> str:
    """Reads and displays the contents of a configuration file."""
    config = configparser.ConfigParser()

    configPath = Path(__file__).resolve().parent / "..\\..\\..\\" / file_path
    print(f"Config file path: {configPath}")
    config.read(configPath)

    print(f"Config file contents: {config.sections()}")

    global root_dir, destination_dir

    root_dir = config.get('Directories', 'OutDirectory')
    destination_dir = config.get('Directories', 'FlatDirectory')


# --- Main Function ---

def main():

    global root_dir, destination_dir
    read_config("bmsConf.ini")


    # --- Main Script ---
    log_info("Starting universal recursive flattening copy process (root contents -> destination)...")
    log_info(f"Source Root Directory: '{root_dir}'")
    log_info(f"Destination Directory: '{destination_dir}'")

    root_dir_abs = os.path.abspath(root_dir)
    destination_dir_abs = os.path.abspath(destination_dir)

    # Validate RootDir
    if not os.path.isdir(root_dir_abs):
        log_error(f"Root directory '{root_dir_abs}' not found or is not a directory.")
        sys.exit(1)

    # Ensure DestinationDir exists
    if not os.path.exists(destination_dir_abs):
        log_warning(f"Destination directory '{destination_dir_abs}' not found. Creating...")
        try:
            os.makedirs(destination_dir_abs)
            log_success("Destination directory created successfully.")
        except Exception as ex:
            log_error(f"Failed to create destination directory '{destination_dir_abs}': {ex}")
            sys.exit(1)
    elif not os.path.isdir(destination_dir_abs):
        log_error(f"Destination path '{destination_dir_abs}' exists but is not a directory.")
        sys.exit(1)


    log_info("Starting processing from root directory's contents...")
    log("--------------------------------------------------", Colors.GRAY)

    try:
        # Initial call to the recursive function
        process_source_directory(root_dir_abs, destination_dir_abs, "", destination_dir_abs, root_dir_abs)
    except Exception as ex:
        log_error(f"An unexpected error occurred during processing: {ex}")
        import traceback
        log_error(traceback.format_exc())
        sys.exit(1)

    log("--------------------------------------------------", Colors.GRAY)
    log_info("Universal recursive flattening copy process completed.")
    log_success(f"Source directory contents from: '{root_dir_abs}'")
    log_success(f"Destination directory: '{destination_dir_abs}'")

# --- End Main Function ---

if __name__ == "__main__":
    # --- Argument Parsing & Validation ---
    if len(sys.argv) < 3:
        print("Usage: python flat.py <RootDir> <DestinationDir>")
    else:
        global root_dir, destination_dir
        root_dir = sys.argv[1]
        destination_dir = sys.argv[2]

    main()

# --- End of Script ---
