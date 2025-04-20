# Roo Code + Taskmaster Enhanced Setup

[![Python 3.x](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This repository provides a streamlined setup script (`install_taskmaster.py`) for integrating the [Task Master AI](https://github.com/eyaltoledano/claude-task-master) CLI tool with [Roo Code](https://www.roocode.com/), leveraging a curated set of Roo modes and rules fetched from the [neno-is-ooo/roo-taskmaster-patch](https://github.com/neno-is-ooo/roo-taskmaster-patch) repository.

## Overview

The `install_taskmaster.py` script automates several setup steps to ensure a consistent and effective development environment when using Roo Code agents (like Boomerang and Code) with Taskmaster for project management and execution.

## Features

*   **Automated Taskmaster Installation:** Installs the `task-master-ai` npm package either globally or locally.
*   **Guided Roo Code MCP Configuration:** Checks your Roo Code `mcp_settings.json` and interactively helps configure the `taskmaster-ai` server, prompting for necessary API keys (Anthropic, Perplexity).
*   **Custom Roo Modes & Rules:** Downloads pre-configured Roo modes (`.roomodes`) [Boomerang] and enhanced Roo rules (`.roo/rules-*/*`) specifically tailored for Taskmaster workflows from the `neno-is-ooo/roo-taskmaster-patch` repository.
*   **Legacy Configuration Handling:** Migrates configurations from older `.cursor` directories to the new `.roo` standard and removes legacy `.windsurfrules`.
*   **Interactive Project Initialization:** Runs the `task-master init` command interactively, allowing you to configure your Taskmaster project details.
*   **User-Friendly Output:** Provides clear, colored step-by-step feedback during the installation process.

## Why This Setup?

Using this script offers several advantages over a manual setup or relying solely on default Roo Code configurations:

1.  **Enhanced Safety & Control:** Instead of using generic default rules, Roo Code fetches specific modes and rules from a designated repository (`neno-is-ooo/roo-taskmaster-patch`). This gives you explicit control over the guidelines Roo operates under, preventing unexpected or undesirable behavior and ensuring the AI adheres to project standards.
2.  **Consistency:** Ensures all developers using Roo Code on the project work with the *exact same* set of rules and modes. This leads to more predictable AI agent behavior and consistent code generation/task execution across the team.
3.  **Optimized Workflow:** The custom rules fetched by the script are designed to align with the Taskmaster development workflow (e.g., understanding task dependencies, status updates, breakdown processes as defined in Taskmaster's methodology). This helps Roo agents interact more effectively with the Taskmaster system.
4.  **Streamlined Onboarding:** Simplifies the setup process for new team members joining a project that utilizes this Roo Code + Taskmaster combination. Running one script configures the necessary tools and AI guidelines.

## Prerequisites

*   **Python 3:** The script is written in Python 3.
*   **Node.js and npm:** Required to install `task-master-ai` and `task-master-mcp`.

## Usage

1.  **Obtain the script:** Clone this repository or download `install_taskmaster.py` directly into your project's root directory.
2.  **Navigate to your project:** Open your terminal and change the directory to your project's root folder.
3.  **Run the script:**
    ```bash
    python3 install_taskmaster.py
    ```
4.  **Follow prompts:** The script will guide you through the installation choices (global vs. local), API key entry (optional, placeholders can be used), and Taskmaster project initialization.

## Configuration

The script will prompt you for:

*   **Installation Type:** Global (`-g`) or local `npm install` for `task-master-ai`.
*   **API Keys:** Your Anthropic and Perplexity API keys for the Roo Code MCP configuration. You can leave these blank initially to use placeholders and update the `mcp_settings.json` file later.
*   **Taskmaster Project Details:** During the `task-master init` phase, you may be prompted for project name, description, etc.

The final Roo Code MCP configuration for `taskmaster-ai` will be stored in your system's Roo Code settings location (the script will attempt to detect and display this path).

## Files Fetched from `roo-taskmaster-patch`

The script fetches the following configuration files from the [neno-is-ooo/roo-taskmaster-patch](https://github.com/neno-is-ooo/roo-taskmaster-patch) repository:

*   `.roomodes`: Defines the available Roo Code modes (Architect, Ask, Boomerang, Code, Debug, Test). Placed in the project root.
*   `.roo/rules-*/{mode}-rules`: Contains specific rulesets for each Roo Code mode, tailored for working with Taskmaster. Placed within the `.roo` directory in your project.

## Customization

If you want to use your own set of Roo modes or rules, you can:

1.  Fork the `neno-is-ooo/roo-taskmaster-patch` repository.
2.  Modify the `.roomodes` and rule files in your fork.
3.  Update the `GITHUB_BASE_URL` variable at the top of `install_taskmaster.py` to point to your forked repository's raw content URL.

   
![snag-roo-tm](https://github.com/user-attachments/assets/db3db6ee-d885-459f-8672-872514826f61)

   

## License

This script is released under the MIT License. See the LICENSE file for details.
