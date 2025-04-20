
import os
import re
import subprocess
from datetime import datetime
import configparser

def find_conf_ini(start_path):
    """Traverse the directory tree upwards to find bmsConf.ini."""
    current_path = start_path
    while True:
        moduleConfigPath = os.path.join(current_path, "bmsConf.ini")
        if os.path.exists(moduleConfigPath):
            return moduleConfigPath
        parent_path = os.path.dirname(current_path)
        if parent_path == current_path:  # Reached the root directory
            break
        current_path = parent_path
    return None

def main():

	# Find bmsConf.ini by traversing upwards
	start_directory = os.path.abspath(os.path.dirname(__file__))
	moduleConfigPath = find_conf_ini(start_directory)

	if not moduleConfigPath:
		print("Error: bmsConf.ini not found in any parent directory.")
		exit(1)

	print(f"bmsConf.ini found at: {moduleConfigPath}")


	# Read the path to the main ini file from bmsConf.ini
	moduleConfig = configparser.ConfigParser()
	moduleConfig.read(moduleConfigPath)

	try:
		str_directory = moduleConfig.get("Directories", "StrDirectory")
		out_directory = moduleConfig.get("Directories", "OutDirectory")
		log_file_path = moduleConfig.get("Directories", "LogFilePath")
		bms_script = moduleConfig.get("Scripts", "BmsScriptPath")
	except Exception as e:
		print(f"Error reading paths from main ini file: {e}")
		exit(1)

	# Ensure log file exists
	if not os.path.exists(log_file_path):
		print(f"Creating log file at {log_file_path}")
		try:
			with open(log_file_path, 'w') as log_file:
				log_file.write("")
			print("Log file created successfully.")
		except Exception as e:
			print(f"Error creating log file: {e}")
			exit(1)
	else:
		print(f"Log file already exists at {log_file_path}")

	# Parameters
	overwrite_option = "s"  # Default to 's' (skip all)

	quickbms = moduleConfig.get("Scripts", "QuickBMSEXEPath")

	# Get all .str files in the source directory
	str_files = []
	for root, _, files in os.walk(str_directory):
		for file in files:
			if file.endswith(".str"):
				str_files.append(os.path.join(root, file))

	print(f"Found {len(str_files)} .str files to process.")

	# Process each .str file
	for file_path in str_files:
		print(f"Processing file: {file_path}")

		# Construct the output directory
		relative_path = os.path.relpath(file_path, start=str_directory)
		output_directory = os.path.join(out_directory, os.path.splitext(relative_path)[0] + "_str")

		print(f"Output Directory: {output_directory}")

		# Ensure the output directory exists
		os.makedirs(output_directory, exist_ok=True)

		# Construct the command to run
		args = []
		if overwrite_option == "a":
			args = ["-o", bms_script, file_path, output_directory]
		elif overwrite_option == "r":
			args = ["-K", bms_script, file_path, output_directory]
		elif overwrite_option == "s":
			args = ["-k", bms_script, file_path, output_directory]
		else:
			args = [bms_script, file_path, output_directory]

		print(f"QuickBMS Command: {quickbms} {' '.join(args)}")

		# Execute the QuickBMS command
		try:
			result = subprocess.run([quickbms] + args, capture_output=True, text=True)
			quickbms_output = result.stdout
			print("# Start quickBMS Output")
			print(quickbms_output)
			print("# End quickBMS Output")
		except Exception as e:
			print(f"Error executing QuickBMS: {e}")
			continue

		# Extract coverage percentages
		coverage_regex = re.compile(r'coverage file\s+(-?\d+)\s+([\d.]+)%\s+\d+\s+\d+\s+\.\s+offset\s+([0-9a-fA-F]+)')
		matches = coverage_regex.findall(quickbms_output)

		if matches:
			print("Coverage Percentages:")
			for match in matches:
				file_number, percentage, offset = match
				print(f"  File: {file_number}, Percentage: {percentage}%, Offset: 0x{offset}")

				# Log the file name and percentage to the log file
				try:
					log_entry = f'Time = [{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}], Path = "{file_path}", File = "{file_number}", Percentage = "{percentage}%", Offset = "0x{offset}"\n'
					with open(log_file_path, 'a') as log_file:
						log_file.write(log_entry)
				except Exception as e:
					print(f"Error writing to log file: {e}")
		else:
			print("No coverage information found.")

		print(f"Processed {os.path.basename(file_path)} -> Output Directory: {output_directory}")

	print("QuickBMS processing completed.")

if __name__ == "__main__":
	main()