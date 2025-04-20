#!/usr/bin/env python3
import os
import shutil
import re
import json
import platform
import subprocess
import sys
import urllib.request
import urllib.error
from pathlib import Path

# --- Configuration ---
GITHUB_BASE_URL = "https://raw.githubusercontent.com/neno-is-ooo/roo-taskmaster-patch/main/"
MCP_SERVER_NAME = "taskmaster-ai"
DEFAULT_MCP_COMMAND = "npx"
DEFAULT_MCP_ARGS = ["-y", "task-master-mcp"]
DEFAULT_MCP_ENV = {
    "ANTHROPIC_API_KEY": "sk-ant-apADDYOURKEY",
    "PERPLEXITY_API_KEY": "pplx-ADDYOURKEY",
    "MODEL": "claude-3-5-sonnet-20240620", # Updated default model
    "PERPLEXITY_MODEL": "llama-3-sonar-large-32k-online", # Updated default model
    "MAX_TOKENS": "8000", # Adjusted default
    "TEMPERATURE": "0.2",
    "DEFAULT_SUBTASKS": "5",
    "DEFAULT_PRIORITY": "medium"
}
DEFAULT_MCP_ALWAYS_ALLOW = [
    "get_task", "set_task_status", "update_subtask", "get_tasks", "update",
    "update_task", "generate", "next_task", "expand_task", "add_task",
    "add_subtask", "remove_subtask", "analyze_project_complexity",
    "clear_subtasks", "expand_all", "remove_dependency",
    "validate_dependencies", "fix_dependencies", "complexity_report",
    "add_dependency", "remove_task", "parse_prd", "initialize_project" # Added missing ones
]
ROO_MODES = ['architect', 'ask', 'boomerang', 'code', 'debug', 'test']

# --- ANSI Color Codes ---
COLOR_RESET = "\033[0m"
COLOR_BLUE = "\033[94m"
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_RED = "\033[91m"
COLOR_CYAN = "\033[96m"
COLOR_BOLD = "\033[1m"

# --- Helper Functions ---

def print_step(message):
    """Prints a formatted step message with color."""
    print("\n\n" + "=" * 60) # More spacing
    print(f"{COLOR_BOLD}{COLOR_CYAN}🚀 STEP: {message}{COLOR_RESET}")
    print("=" * 60)

def print_info(message):
    """Prints an informational message with color."""
    print(f"{COLOR_GREEN}ℹ️ [INFO] {message}{COLOR_RESET}") # Added color

def print_warning(message):
    """Prints a warning message with color."""
    print(f"{COLOR_YELLOW}⚠️ [WARN] {message}{COLOR_RESET}") # Added color

def print_error(message):
    """Prints an error message with color."""
    print(f"{COLOR_RED}❌ [ERROR] {message}{COLOR_RESET}") # Added color

def print_question(message):
    """Prints a question prompt with color."""
    return input(f"{COLOR_BLUE}❓ {message}{COLOR_RESET} ") # Use input directly

def print_code(code_str, language="json"):
    """Prints a code block."""
    print(f"```{language}")
    print(code_str)
    print("```")

# This function runs commands interactively, showing live output (like npm init prompts)
def run_command_interactive(command_list, check=False, shell=False, cwd=None):
    """Runs a shell command interactively, showing live output."""
    command_str = " ".join(command_list) if isinstance(command_list, list) else command_list
    print_info(f"Running command interactively: {COLOR_BOLD}{command_str}{COLOR_RESET}" + (f" in {cwd}" if cwd else ""))
    print_info("Output will appear below. The script will wait for this command to finish...")
    try:
        # Use Popen for more control if needed, but run should work for inheriting stdio
        process = subprocess.run(
            command_list,
            check=check, # Often False for interactive setup commands that might exit 0 after prompts
            shell=shell,
            cwd=cwd,
            # Let the subprocess inherit stdin, stdout, stderr from the script's process
            # This allows user interaction and shows live output
            stdin=None, # Inherit
            stdout=None, # Inherit
            stderr=None # Inherit
        )
        print_info(f"Interactive command '{command_str}' finished with exit code {process.returncode}.")
        # Success determination might depend on the command. check=False means we don't raise error on non-zero exit.
        # We might assume success if no exception occurred, or check returncode if needed.
        return process.returncode == 0 # Return True if exit code is 0
    except subprocess.CalledProcessError as e:
        # This is only reached if check=True and it fails
        print_error(f"Interactive command failed with exit code {e.returncode}: {command_str}")
        return False
    except FileNotFoundError:
        print_error(f"Command not found: {command_list[0]}. Is it installed and in PATH?")
        return False
    except Exception as e:
        print_error(f"An unexpected error occurred while running interactive command: {e}")
        return False

# This function runs commands and captures their output (useful for checks)
def run_command_capture(command_list, check=True, shell=False, cwd=None):
    """Runs a shell command verbosely and captures output."""
    command_str = " ".join(command_list) if isinstance(command_list, list) else command_list
    print_info(f"Running command (capturing output): {COLOR_BOLD}{command_str}{COLOR_RESET}" + (f" in {cwd}" if cwd else ""))
    try:
        process = subprocess.run(
            command_list,
            check=check,
            shell=shell,
            text=True,
            stdout=subprocess.PIPE, # Capture stdout
            stderr=subprocess.PIPE, # Capture stderr
            cwd=cwd
        )
        if process.stdout:
            print(f"{COLOR_GREEN}[STDOUT]{COLOR_RESET}\n{process.stdout.strip()}")
        if process.stderr:
            print(f"{COLOR_YELLOW}[STDERR]{COLOR_RESET}\n{process.stderr.strip()}")
        print_info(f"Command '{command_str}' executed successfully (captured).")
        return True, process.stdout, process.stderr
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed with exit code {e.returncode}: {command_str}")
        if e.stdout:
            print(f"{COLOR_RED}[STDOUT]{COLOR_RESET}\n{e.stdout.strip()}")
        if e.stderr:
            print(f"{COLOR_RED}[STDERR]{COLOR_RESET}\n{e.stderr.strip()}")
        return False, e.stdout, e.stderr
    except FileNotFoundError:
        print_error(f"Command not found: {command_list[0]}. Is it installed and in PATH?")
        return False, "", ""
    except Exception as e:
        print_error(f"An unexpected error occurred while running command: {e}")
        return False, "", ""


def ask_yes_no(prompt, default=None):
    """Asks a yes/no question with color."""
    while True:
        options = "[y/n]"
        if default == 'y':
            options = f"[{COLOR_BOLD}Y{COLOR_RESET}/n]"
        elif default == 'n':
            # Corrected logic for default 'n'
            options = f"[y/{COLOR_BOLD}N{COLOR_RESET}]"
        # else: options remains "[y/n]"

        # Use print_question for colored input prompt
        response = print_question(f"{prompt} {options}:").lower().strip() # Pass options here

        if not response and default is not None: # Check default is not None
            return default == 'y'
        elif response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            print_warning("Please answer 'yes' or 'no'.")

def get_mcp_settings_path():
    """Determines the path to the Roo Code MCP settings file."""
    system = platform.system()
    home = Path.home()
    # Assuming VSCodium paths, adjust if using standard VSCode
    codium_app_support_name = "VSCodium" # Change to "Code" for standard VSCode if needed

    if system == "Darwin": # macOS
        path = home / "Library" / "Application Support" / codium_app_support_name / "User" / "globalStorage" / "rooveterinaryinc.roo-cline" / "settings" / "mcp_settings.json"
    elif system == "Linux":
        path = home / ".config" / codium_app_support_name / "User" / "globalStorage" / "rooveterinaryinc.roo-cline" / "settings" / "mcp_settings.json"
    elif system == "Windows":
        appdata = os.getenv('APPDATA')
        if not appdata:
            print_error("Could not determine APPDATA directory on Windows.")
            return None
        path = Path(appdata) / codium_app_support_name / "User" / "globalStorage" / "rooveterinaryinc.roo-cline" / "settings" / "mcp_settings.json"
    else:
        print_error(f"Unsupported operating system: {system}")
        return None

    # Don't print path here, print it when actually used/checked later
    # print_info(f"Detected MCP settings path: {path}")
    return path

def read_json_file(path):
    """Reads a JSON file."""
    if not path or not path.exists():
        # This is not necessarily a warning, could be expected
        # print_warning(f"File not found: {path}")
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print_error(f"Error decoding JSON from file: {path}")
        return None
    except IOError as e:
        print_error(f"Error reading file {path}: {e}")
        return None

def write_json_file(path, data):
    """Writes data to a JSON file."""
    if not path:
        print_error("Invalid path provided for writing JSON.")
        return False
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2) # Use indent=2 for readability
        print_info(f"Successfully wrote JSON data to {path}")
        return True
    except IOError as e:
        print_error(f"Error writing file {path}: {e}")
        return False
    except Exception as e:
        print_error(f"An unexpected error occurred writing JSON to {path}: {e}")
        return False

def fetch_and_write(url, local_path):
    """Fetches content from a URL using urllib and writes it to a local file."""
    local_path = Path(local_path)
    try:
        print_info(f"Fetching {url}...")
        # Add a user-agent header to potentially avoid blocking
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(url, headers=headers)

        with urllib.request.urlopen(req, timeout=30) as response: # Added timeout
            if response.getcode() == 200:
                content = response.read().decode('utf-8')
                print_info(f"Writing content to {local_path}...")
                local_path.parent.mkdir(parents=True, exist_ok=True)
                with open(local_path, "w", encoding='utf-8') as f:
                    f.write(content)
                print_info(f"Successfully wrote {local_path}")
                return True
            else:
                print_error(f"Error fetching {url}: HTTP status code {response.getcode()}")
                return False
    except urllib.error.HTTPError as e:
        print_error(f"HTTP Error fetching {url}: {e.code} {e.reason}")
        return False
    except urllib.error.URLError as e:
        print_error(f"URL Error fetching {url}: {e.reason}")
        return False
    except IOError as e:
        print_error(f"Error writing to {local_path}: {e}")
        return False
    except Exception as e:
        print_error(f"An unexpected error occurred while processing {url}: {e}")
        return False

def process_cursor_files(roo_dir_path):
    """Copies .cursor contents into .roo, modifies files, and removes .cursor."""
    print_step("Processing legacy .cursor directory (if exists)  legacy files 🧹")
    cursor_dir = Path(".cursor")
    roo_dir = roo_dir_path # Already a Path object

    if cursor_dir.exists() and cursor_dir.is_dir():
        print_info(f"Found {cursor_dir}. Merging contents into {roo_dir}...")
        # --- FIX: Use copytree with dirs_exist_ok=True to merge ---
        try:
            # Ensure the target directory exists
            roo_dir.mkdir(parents=True, exist_ok=True)
            # Copy contents, merging with existing directory (Requires Python 3.8+)
            shutil.copytree(cursor_dir, roo_dir, dirs_exist_ok=True)
            print_info(f"Merged contents of {cursor_dir} into {roo_dir}.")
        except TypeError:
            # Fallback for Python < 3.8 which doesn't support dirs_exist_ok
            print_warning("Python version < 3.8 detected. Using manual file copy for merging.")
            try:
                for item in os.listdir(cursor_dir):
                    s = cursor_dir / item
                    d = roo_dir / item
                    if s.is_dir():
                        # For directories, try copytree again for sub-merging if possible
                        # This might still fail on very old Python, but covers more cases
                        try:
                            shutil.copytree(s, d, dirs_exist_ok=True)
                        except TypeError: # Inner copytree failed
                             print_warning(f"Manual recursive copy needed for {s}. Skipping complex merge for older Python.")
                             # Implement a full recursive manual copy if absolutely needed,
                             # but for now, we'll just warn and skip deep merge for simplicity.
                    elif s.is_file(): # Only copy if it's a file
                        shutil.copy2(s, d) # copy2 preserves metadata
                print_info(f"Manually merged contents of {cursor_dir} into {roo_dir}.")
            except Exception as e_fallback:
                 print_error(f"Error during manual merge of {cursor_dir} into {roo_dir}: {e_fallback}")
                 # Don't return here, try to continue with modification/deletion
        except Exception as e:
            print_error(f"Error merging {cursor_dir} into {roo_dir}: {e}")
            # Don't return here, try to continue with modification/deletion

        # --- Modification Step (Runs even if merge had issues, on whatever is in .roo) ---
        print_info(f"Modifying files within {roo_dir} (if merge occurred)...")
        files_processed = 0
        files_renamed = 0
        if roo_dir.exists(): # Check if target dir exists before walking
            for root, _, files in os.walk(roo_dir):
                root_path = Path(root)
                for file in files:
                    # Skip files that should have been fetched from GitHub
                    # Check relative path to avoid modifying fetched rules
                    relative_path_parts = (root_path / file).relative_to(roo_dir).parts
                    if len(relative_path_parts) > 1 and relative_path_parts[0].startswith("rules-"):
                        # print_info(f"Skipping modification for potential rule file: {relative_path_parts}")
                        continue
                    if file == ".roomodes": # This should be fetched to root, not in .roo
                         continue

                    file_path = root_path / file
                    try:
                        # Read only if it's a text file (basic check)
                        if file.endswith(('.md', '.txt', '.json', '.js', '.py', '.sh', '.yaml', '.yml')):
                            with open(file_path, "r", encoding='utf-8', errors='ignore') as f:
                                content = f.read()

                            original_content = content
                            content = re.sub(r"\.mdc", ".md", content)
                            content = re.sub(r"cursor/", "roo/", content)
                            content = re.sub(r"Cursor", "Roo Code", content)
                            content = re.sub(r"cursor_", "roo_", content)
                            content = re.sub(r"\[Cursor\]\(https://www.cursor.so/\)", "[Roo Code](https://www.roocode.com/)", content)

                            if content != original_content:
                                with open(file_path, "w", encoding='utf-8') as f:
                                    f.write(content)
                                files_processed += 1

                        # Handle .mdc files and cursor_rules.mdc specifically
                        if file.endswith(".mdc"):
                            new_name = file[:-4] + ".md"
                            new_path = root_path / new_name
                            print_info(f"Renaming {file_path} to {new_path}")
                            os.rename(file_path, new_path)
                            files_renamed += 1
                            if file == "cursor_rules.mdc":
                                roo_rules_path = root_path / "roo_rules.md"
                                print_info(f"Renaming {new_path} to {roo_rules_path}")
                                os.rename(new_path, roo_rules_path) # Rename again

                    except Exception as file_e:
                        print_error(f"Error processing file {file_path}: {file_e}")
            print_info(f"Finished modifying files. Processed: {files_processed}, Renamed: {files_renamed}")
        else:
             print_warning(f"{roo_dir} does not exist, skipping modification step.")


        # --- Deletion Step ---
        print_info(f"Removing original {cursor_dir} directory...")
        try:
            shutil.rmtree(cursor_dir)
            print_info(f"Successfully removed {cursor_dir}.")
        except OSError as e:
            print_error(f"Error removing {cursor_dir}: {e}")

    else:
        print_info(f"{cursor_dir} directory not found. Skipping merge, modification, and deletion of .cursor.")
        # Ensure .roo directory exists anyway for fetched rules later
        roo_dir.mkdir(parents=True, exist_ok=True)

def remove_windsurf_rules():
    """Removes the .windsurfrules file if it exists."""
    windsurf_file = Path(".windsurfrules")
    if windsurf_file.exists():
        print_step("Removing legacy .windsurfrules file 🧹")
        print_info(f"Found {windsurf_file}. Removing...")
        try:
            os.remove(windsurf_file)
            print_info(f"Successfully removed {windsurf_file}.")
        except OSError as e:
            print_error(f"Error removing {windsurf_file}: {e}")
    else:
        print_info(".windsurfrules file not found, skipping removal.")


# --- Helper function to mask keys ---
def mask_sensitive_mcp_data(mcp_entry):
    """Creates a copy of an MCP server entry with sensitive env vars masked."""
    if not isinstance(mcp_entry, dict):
        return mcp_entry # Return as-is if not a dict

    # Deep copy to avoid modifying the original config object in memory
    masked_entry = json.loads(json.dumps(mcp_entry))

    if "env" in masked_entry and isinstance(masked_entry["env"], dict):
        for key in masked_entry["env"]:
            # Mask keys commonly used for secrets
            if "KEY" in key.upper() or "TOKEN" in key.upper() or "SECRET" in key.upper():
                 value = masked_entry["env"].get(key) # Use .get for safety
                 # Show first/last few chars for identification if key is long enough string
                 if isinstance(value, str) and len(value) > 8:
                     masked_entry["env"][key] = f"{value[:4]}****{value[-4:]} [MASKED]"
                 elif isinstance(value, str) and value: # Mask non-empty short strings
                     masked_entry["env"][key] = "[MASKED]"
                 # Leave empty strings or non-strings alone, or mask them too? Masking seems safer.
                 elif value: # Mask other non-empty values
                     masked_entry["env"][key] = "[MASKED]"
                 # else: leave empty/None as is
    return masked_entry

# --- Main Script Logic ---

def main():
    print_step("Starting Task Master AI Installation and Setup")
    install_globally = None
    install_command = []

    # 1. Ask install type
    while install_globally is None:
        # Use print_question for colored input
        choice = print_question("Install taskmaster-ai globally (-g) or locally (l)? [g/l]:").lower().strip()
        if choice == 'g':
            install_globally = True
            install_command = ["npm", "install", "-g", "task-master-ai"]
        elif choice == 'l':
            install_globally = False
            install_command = ["npm", "install", "task-master-ai"]
        else:
            print_warning("Invalid choice. Please enter 'g' or 'l'.")

    # 2. Execute installation (Capture output for npm install)
    print_step(f"Installing taskmaster-ai {'globally' if install_globally else 'locally'} 📦")
    # Use run_command_capture here as we don't need interaction, just success/fail and logs
    success, _, _ = run_command_capture(install_command, shell=platform.system() == "Windows")
    if not success:
        print_error("Installation failed. Please check the errors above and ensure npm is installed and configured correctly.")
        sys.exit(1)

    # 3. Check MCP Configuration
    print_step("Checking Roo Code MCP Configuration ⚙️")
    mcp_config_path = get_mcp_settings_path()
    mcp_config = None
    taskmaster_mcp_exists = False
    config_read_error = False

    if mcp_config_path:
        print_info(f"Checking MCP settings path: {mcp_config_path}")
        if mcp_config_path.exists():
            mcp_config = read_json_file(mcp_config_path)
            if mcp_config is None:
                # read_json_file already printed an error
                config_read_error = True
                mcp_config = {"mcpServers": {}} # Attempt recovery
            # Check the structure carefully
            elif isinstance(mcp_config.get("mcpServers"), dict) and MCP_SERVER_NAME in mcp_config["mcpServers"]:
                taskmaster_mcp_exists = True
                print_info(f"Found existing '{MCP_SERVER_NAME}' configuration.")
            elif "mcpServers" not in mcp_config or not isinstance(mcp_config.get("mcpServers"), dict):
                 print_warning("MCP config 'mcpServers' key is missing or not a dictionary. Ensuring key exists.")
                 mcp_config["mcpServers"] = {} # Ensure the key exists as a dict
                 # Taskmaster doesn't exist in this case
            else:
                 # mcpServers exists and is a dict, but taskmaster isn't in it
                 print_info(f"'{MCP_SERVER_NAME}' configuration not found in mcpServers.")
        else:
            print_info(f"MCP settings file not found at expected location. Will offer to create/configure.")
            mcp_config = {"mcpServers": {}} # Initialize structure for potential writing
    else:
        print_warning("Could not determine MCP settings path. Skipping MCP check and configuration.")
        # Cannot proceed with MCP config if path is unknown
        mcp_config = None # Ensure mcp_config is None if path is None

    # 4. Configure MCP (if needed and possible)
    # Only proceed if path is known, config read didn't fail critically, and taskmaster doesn't exist yet
    if mcp_config is not None and mcp_config_path and not taskmaster_mcp_exists and not config_read_error:
        if ask_yes_no(f"Configure '{MCP_SERVER_NAME}' in Roo Code MCP settings now?", default='y'):
            print_info("Starting MCP configuration wizard...")
            # Use print_question for colored prompts
            anthropic_key = print_question("Enter your Anthropic API Key (leave blank to use placeholder):").strip()
            perplexity_key = print_question("Enter your Perplexity API Key (leave blank to use placeholder):").strip()

            temp_str = print_question("Enter desired model temperature [0.0-1.0] (default: 0.2):").strip()
            temperature = 0.2
            try:
                temp_float = float(temp_str)
                if 0.0 <= temp_float <= 1.0:
                    temperature = temp_float
                else:
                    print_warning("Invalid temperature value. Using default 0.2.")
            except ValueError:
                if temp_str: # Only warn if they entered something invalid
                    print_warning("Invalid temperature format. Using default 0.2.")

            new_mcp_entry = {
                "command": DEFAULT_MCP_COMMAND,
                "args": DEFAULT_MCP_ARGS,
                "env": DEFAULT_MCP_ENV.copy(), # Make a copy to modify
                "alwaysAllow": DEFAULT_MCP_ALWAYS_ALLOW
            }
            if anthropic_key:
                new_mcp_entry["env"]["ANTHROPIC_API_KEY"] = anthropic_key
            else:
                print_warning("Anthropic API Key not provided. Using placeholder.")
            if perplexity_key:
                new_mcp_entry["env"]["PERPLEXITY_API_KEY"] = perplexity_key
            else:
                print_warning("Perplexity API Key not provided. Using placeholder.")
            new_mcp_entry["env"]["TEMPERATURE"] = str(temperature) # Store as string

            print_info("Generated MCP configuration snippet (Keys will be masked in final check):")
            # Print masked version even here for safety
            print_code(json.dumps({MCP_SERVER_NAME: mask_sensitive_mcp_data(new_mcp_entry)}, indent=2))

            if ask_yes_no("Add this configuration to your mcp_settings.json?", default='y'):
                # Ensure mcpServers key exists before assignment
                if "mcpServers" not in mcp_config or not isinstance(mcp_config.get("mcpServers"), dict):
                    mcp_config["mcpServers"] = {}
                mcp_config["mcpServers"][MCP_SERVER_NAME] = new_mcp_entry
                if write_json_file(mcp_config_path, mcp_config):
                    print_info("MCP configuration updated successfully. ✅")
                    # Update flag to reflect change
                    taskmaster_mcp_exists = True
                else:
                    print_error("Failed to write updated MCP configuration.")
            else:
                print_info("MCP configuration skipped.")
        else:
            print_info("Skipping automatic MCP configuration.")
            print_info("You can manually add the following configuration to your mcp_settings.json:")
            manual_config_display = {
                MCP_SERVER_NAME: mask_sensitive_mcp_data({ # Mask the default env for display
                    "command": DEFAULT_MCP_COMMAND,
                    "args": DEFAULT_MCP_ARGS,
                    "env": DEFAULT_MCP_ENV,
                    "alwaysAllow": DEFAULT_MCP_ALWAYS_ALLOW
                })
            }
            print_code(json.dumps(manual_config_display, indent=2))
            print_info("See Roo Code documentation for more details: https://docs.roocode.com/features/mcp/using-mcp-in-roo")

    elif taskmaster_mcp_exists:
        print_info("Taskmaster MCP configuration already exists. Skipping setup.")
    elif config_read_error:
         print_warning("Skipping MCP setup due to error reading the config file.")
    # Implicit else: mcp_config_path is None, warning already printed


    # 5. Download Custom Modes/Rules
    print_step("Downloading custom Roo modes and rules 📄")
    roo_dir = Path(".roo")
    # Ensure .roo exists *before* fetching rules into it
    roo_dir.mkdir(parents=True, exist_ok=True)

    # Fetch .roomodes to project root
    roomodes_url = f"{GITHUB_BASE_URL}.roomodes"
    local_roomodes_path = Path(".roomodes") # Place in project root
    fetch_and_write(roomodes_url, local_roomodes_path)

    # Fetch rules files into .roo/rules-{mode}/
    rules_fetched = 0
    for mode in ROO_MODES:
        rule_file_name = f"{mode}-rules"
        rule_url = f"{GITHUB_BASE_URL}rules-{mode}/{rule_file_name}"
        local_rule_dir = roo_dir / f"rules-{mode}"
        local_rule_path = local_rule_dir / rule_file_name
        # Ensure the specific rule directory exists before writing
        local_rule_dir.mkdir(parents=True, exist_ok=True)
        if fetch_and_write(rule_url, local_rule_path):
            rules_fetched += 1
    print_info(f"Fetched {rules_fetched}/{len(ROO_MODES)} rule files into {roo_dir}.")


    # 6. Choose Run Type for Init
    init_command = []
    if install_globally:
        print_step("Choose how to run Task Master initialization 🤔")
        while not init_command:
            # Use print_question for colored input
            run_choice = print_question("Run 'task-master init' globally (g) or locally via npx (l)? [g/l]:").lower().strip()
            if run_choice == 'g':
                init_command = ["task-master", "init"]
            elif run_choice == 'l':
                # Ensure correct npx command if package name differs from CLI command
                init_command = ["npx", "task-master", "init"] # Use 'task-master init' via npx
            else:
                print_warning("Invalid choice. Please enter 'g' or 'l'.")
    else:
        # If installed locally, must use npx
        init_command = ["npx", "task-master", "init"] # Use 'task-master init' via npx
        print_info("Task Master installed locally, will use 'npx task-master init' for initialization.")

    # 7. Initialize Task Master Project (Run interactively)
    print_step("Initializing Task Master project ✨")
    print_info("This will create project structure (like tasks/, scripts/) and configuration files.")
    print_info("You might be prompted for project details (name, description etc.).")
    print_info(f"The following command will run directly in your terminal:")
    print(f"➡️  {COLOR_BOLD}{' '.join(init_command)}{COLOR_RESET}")
    # Use the interactive run command function
    # Set check=False because 'init' often exits successfully even after user prompts/interaction
    success = run_command_interactive(init_command, check=False, shell=platform.system() == "Windows")
    # We rely on the user seeing the output and any errors directly
    if success:
         print_info("Task Master initialization command finished successfully (exit code 0).")
    else:
         # This could be non-zero exit code, or failure to run the command itself
         print_warning("Task Master initialization command finished, possibly with errors or non-zero exit code. Please review the output above.")


    # 8. Process Cursor/Windsurf Files (Transformation and Deletion)
    # This part runs *after* init and *after* fetching rules
    process_cursor_files(roo_dir) # Handles .cursor -> .roo merge, modify, delete .cursor
    remove_windsurf_rules() # Handles deleting .windsurfrules


    # 9. Final Message
    print_step("Setup Complete! 🎉")
    print_info("Task Master AI should be installed and the project initialized.")

    # --- FIX: Re-read MCP config here to get the absolute final state ---
    print_info("Verifying final MCP configuration state...")
    final_mcp_config = None
    final_taskmaster_mcp_exists = False
    # Use the same path detection logic, store the path used for the final check
    mcp_config_path_final_check = get_mcp_settings_path()
    if mcp_config_path_final_check and mcp_config_path_final_check.exists():
        final_mcp_config = read_json_file(mcp_config_path_final_check)
        # Check the structure carefully
        if final_mcp_config and isinstance(final_mcp_config.get("mcpServers"), dict) and MCP_SERVER_NAME in final_mcp_config["mcpServers"]:
            final_taskmaster_mcp_exists = True
            print_info("Taskmaster MCP configuration is present in the final check.")
        else:
            # This is the case where it *should* be missing if user declined or it failed, or file is malformed
            print_warning("Taskmaster MCP configuration is MISSING or file structure is unexpected in the final check.")
            print_info(f"Checked file: {mcp_config_path_final_check}")
    else:
        print_warning("Could not read or find MCP settings file for final verification.")

    # --- FIX: Logic based on final state ---
    if final_taskmaster_mcp_exists:
        # Only ask to show if it actually exists
        if ask_yes_no("Do you want to see the final MCP configuration snippet for Taskmaster (API keys masked)?", default='n'):
             # Ensure final_mcp_config is not None before accessing
             if final_mcp_config:
                 final_mcp_entry = final_mcp_config.get("mcpServers", {}).get(MCP_SERVER_NAME)
                 if final_mcp_entry:
                     # --- FIX: Mask sensitive data before printing ---
                     masked_entry = mask_sensitive_mcp_data(final_mcp_entry) # Ensure helper exists below
                     print_info("Current Taskmaster MCP configuration snippet (Keys Masked):")
                     print_code(json.dumps({MCP_SERVER_NAME: masked_entry}, indent=2))
                 else:
                     # This case means the file structure was weird despite the key being present
                     print_error("Could not retrieve final MCP configuration snippet (unexpected error).")
             else:
                  print_error("Could not retrieve final MCP configuration snippet (config read failed).")
    # If final_taskmaster_mcp_exists is False, the warning was already printed above.

    print(f"\n{COLOR_BOLD}Final Reminders:{COLOR_RESET}")
    if mcp_config_path_final_check: # Use the path determined in the final check
        print(f"- Verify API keys in MCP settings if placeholders were used: {COLOR_CYAN}{mcp_config_path_final_check}{COLOR_RESET}")
    else:
        print("- Verify API keys in your MCP settings file (path could not be determined).")
    print("- You can now use Taskmaster via `task-master ...` (if global) or `npx task-master ...` (if local).")
    print("- Ask your Roo Boomerang agent to use `taskmaster-ai` in this project.")
    print(f"\n{COLOR_GREEN}Enjoy!{COLOR_RESET}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print_error(f"An unexpected critical error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
