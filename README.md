# devCMDcycle.py
# Developer Command Cycle v3.01

**Author:** RetroGameGirl (atariage)

**License:** [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.html)

A toolchain-agnostic GUI orchestrator for streamlining any command-line development workflow.

# What is devCMDcycle.py?

devCMDcycle.py is a powerful front-end for managing software build environments. Originally designed for Atari 7800 retro development, it has evolved into a flexible tool that can be configured to handle any command-line-driven workflow. It provides a simple, clickable interface to manage complex build steps, eliminating the need to memorize and type repetitive commands.
Whether you are developing for a retro console, compiling C++ code, or managing a web project, devCMDcycle.py acts as your central launchpad.

![alt text for the image](https://github.com/RetroGameGirl/devCMDcycle.py/blob/main/screenshots/devCMDcycle_301_screenshot.png?raw=true)


## Key Features

* **Project-Specific Configurations:** Automatically creates a `devCMDcycle_301.ini` file in your project directory, allowing you to maintain a unique setup for each project.
* **Fully Configurable UI:**
    * Define multiple **Toolchains**, each with its own executable path and settings.
    * Create up to 10 **Custom Action Buttons** per toolchain with custom names, colors, and commands.
    * Set up toolchain-specific **Command-Line Options** with checkboxes for easy toggling.
* **Powerful Command System:**
    * Use **placeholders** (e.g., `%f` for source file, `%t` for toolchain path) to create dynamic commands.
    * Chain multiple button actions into a single **Composite Command** (e.g., `Button3,Button4,Button6`).
    * Run commands in a separate terminal window using the `EXTERNAL:` prefix.
* **Auto-Typer System:**
    * Create detailed **Auto-Typer Profiles** to automate interactions with interactive command-line tools (e.g., for creating ROM headers).
    * Supports multi-step sequences and dynamic user input via `%b<num>` placeholders.
* **Safe and Self-Contained:**
    * Includes a built-in editor to safely modify the script's own factory default settings.
    * Automatically creates backups of your configuration (`.ini`) and the script itself when modified.
* **Live Previews:** The UI provides real-time previews of the final commands as you toggle options, helping to prevent errors.
* **Portable:** The application is a single Python script with no external dependencies beyond a standard Python 3 installation with Tkinter.

## Getting Started

Follow these steps to get your first project running:

1.  **Place the Script:** Put the `devCMDcycle.py` script in a directory that is part of your system's PATH for easy access.
2.  **Launch in Your Project Folder:** Assuming you have python installed and setup, open a terminal or command prompt, navigate to your project's main directory, and run the script:
    ```bash
     devCMDcycle.py
    ```
    A `devCMDcycle_301.ini` file will be created in this directory.
3.  **Select Your Source File:** In the main window, click the `...` button next to "Source File" and choose your primary code file (e.g., `main.asm`, `game.c`).
4.  **Configure a Toolchain:**
    * Select a pre-configured toolchain (e.g., `7800ASMDevKit`) or add a new one in the settings.
    * In the "Executable Path" field, enter the command for your compiler/assembler (e.g., `dasm`, `cl65`).
    * Customize the 10 action buttons below with names and commands.
    * Click **Save & Close**.
5.  **Build Your Project:** Back on the main window, select your configured toolchain from the dropdown and click one of your custom action buttons (e.g., "Build"). The output from your tool will appear in the Status Window.

## Configuration

The application's state is managed through a single configuration file and dedicated backup directories.

* **`devCMDcycle_301.ini`:** This file stores all your settings for the project in the current directory. Every change made in the UI (settings, toolchains, options) is saved to this file in real-time.
* **`ini_backup/`:** This folder is created in your project directory. It stores backups of your `.ini` file whenever you use the "Reset to Default Config" feature.
* **`script_backup/`:** This folder is created in the same directory where `devCMDcycle.py` is located. It stores backups of the script itself whenever you use the integrated "Default Config Editor" to modify its internal defaults.

## Advanced Usage

### Command Placeholders

Use these placeholders in your button commands to dynamically insert paths.

| Placeholder | Description                                    |
| :---------- | :--------------------------------------------- |
| `%f`        | Full path to the Source File                   |
| `%s`        | Source file stem (path without extension)      |
| `%o`        | Output file stem (defaults to the same as `%s`) |
| `%t`        | Full path to the selected Toolchain executable |
| `%e`        | Path to the default Editor                     |
| `%m`        | Path to the default Emulator                   |
| `%h`        | Path to the Header Tool                        |
| `%g`        | Path to the Signer Tool                        |
| `%term`     | Path to the Terminal application               |

### The Auto-Typer System

The Auto-Typer allows you to automate CLI tools that require interactive input.

* **Profiles:** Create profiles in `Settings -> Manage Auto-Typer Profiles`. Each profile can have multiple steps.
* **Triggering:** An auto-type sequence is triggered when you press a custom action button that is linked as a "Label Button" within an enabled step in the active profile.
* **Dynamic Input:** Use the placeholder `%b<num>` in a command (e.g., `name "%b25"`) to create a text input box of size `<num>` in the Settings window. The text you enter there will be typed automatically.
* **Special Keys:** Use `%C<key>` for `CTRL+key` and `%A<key>` for `ALT+key`.

## Dependencies

* **Python 3.x**
* **Tkinter** (usually included with standard Python installations)

The script is cross-platform and has been tested on Linux and Windows.
