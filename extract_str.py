import os
import subprocess
import argparse

global QUICKBMS_EXE, BMS_SCRIPT, STR_INPUT_DIR, OUTPUT_BASE_DIR
# Hardcoded paths
QUICKBMS_EXE = r"A:\Dev\Games\TheSimpsonsGame\PAL\Modules\Extract\Tools\quickbms\exe\quickbms.exe"
BMS_SCRIPT = r"A:\Dev\Games\TheSimpsonsGame\PAL\Modules\Extract\Tools\quickbms\simpsons_str.bms"
STR_INPUT_DIR = r"A:\Dev\Games\TheSimpsonsGame\PAL\Source\USRDIR"
OUTPUT_BASE_DIR = r"A:\Dev\Games\TheSimpsonsGame\PAL\Modules\Extract\GameFiles\QbmsOuttmp"

def extract_str_file(file_path: str):
    global QUICKBMS_EXE, BMS_SCRIPT, STR_INPUT_DIR, OUTPUT_BASE_DIR
    if not file_path.endswith('.str'):
        print(f"Skipping non-.str file: {file_path}")
        return

    # Create output directory for this str file
    relative_path = os.path.relpath(file_path, start=STR_INPUT_DIR)
    output_dir = os.path.join(OUTPUT_BASE_DIR, os.path.splitext(relative_path)[0] + "_str")
    os.makedirs(output_dir, exist_ok=True)

    print(f"Extracting {file_path} to {output_dir}...")

    try:
        subprocess.run(
            [QUICKBMS_EXE, "-o", BMS_SCRIPT, file_path, output_dir],
            check=True
        )
        print(f"Done: {file_path}")
    except subprocess.CalledProcessError as e:
        print(f"Extraction failed for {file_path}: {e}")

def main():
    global QUICKBMS_EXE, BMS_SCRIPT, STR_INPUT_DIR, OUTPUT_BASE_DIR
    parser = argparse.ArgumentParser(description="Extract .str files via QuickBMS")
    parser.add_argument("-e", "--quickbms", default=QUICKBMS_EXE, help="Path to quickbms.exe")
    parser.add_argument("-s", "--script",    default=BMS_SCRIPT,  help="Path to .bms script")
    parser.add_argument("-i", "--input",     default=STR_INPUT_DIR, help="Input directory or file")
    parser.add_argument("-o", "--output",    default=OUTPUT_BASE_DIR, help="Base output directory")
    parser.add_argument("paths", nargs="*", help="Files or directories to process")
    args = parser.parse_args()

    # Override globals

    QUICKBMS_EXE, BMS_SCRIPT, STR_INPUT_DIR, OUTPUT_BASE_DIR = (
        args.quickbms, args.script, args.input, args.output
    )

    targets = args.paths or [STR_INPUT_DIR]
    for path in targets:
        if os.path.isdir(path):
            for root, _, files in os.walk(path):
                for f in files:
                    extract_str_file(os.path.join(root, f))
        else:
            extract_str_file(path)

if __name__ == "__main__":
    main()
