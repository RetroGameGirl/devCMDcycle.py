# devCMDcycle - Atari 7800 Development Commander v2.37

## A Note on this Version

**IMPORTANT:** This version (2.37) is provided for historical purposes. It has been superseded by a newer version. Users are encouraged to seek out the latest version for the most up-to-date features and bug fixes.

Please be aware that this is a significant update to devCMDcycle. While the code originated as a collection of personal scripts, it has been substantially rewritten to be a far more powerful and flexible development front-end. The core concept of a simple, single-window interface remains, but it is now powered by a fully customizable toolchain and automation engine.

It is shared in the hope that it will be useful, but as always, it reflects an organic evolution rather than a planned software design. Use at your own risk, and thank you for your interest!

## Features

* **Dynamic Toolchain System:** No longer limited to two compilers, you can now create, edit, and save complete build environments ("Toolchains"). Each toolchain has its own executable path, custom button layouts, and optional command-line flags.
* **Fully Configurable UI:** Define up to 10 custom action buttons per toolchain. You can name them, color-code them, and assign any command or sequence of commands to them.
* **Composite Actions:** A single button can trigger a sequence of other buttons. For example, a "Build & Run (Debug)" button can be configured to execute your "Build" button, then your "Apply Header" button, then your "Run (Debug)" button, all in order.
* **Live Status Console:** View real-time, color-coded output from your command-line tools directly within the app.
* **Interactive Command Input:** Interact with tools that require input (like the `7800header` utility) from within the app's console.
* **Advanced Auto-Typer:** The "Header Wizard" has been replaced with a powerful, profile-based automation system. Create multi-step scripts that can send special keystrokes (`CTRL+C`), and even generate dynamic text input boxes in the UI for things like naming your ROM.
* **Toolchain-Specific Options:** Create custom checkboxes for each toolchain (e.g., "Generate List File," "Add Debug Info") that append flags to your commands. A live preview shows you exactly what command will be run.
* **Project-Specific Configuration:** Automatically creates a `devCMDcycle_237.ini` file in your project's root directory to save all paths, toolchains, and settings specific to that project.

## Requirements

Before running `devCMDcycle`, you must have the following software installed on your system.

### Core Dependencies

* **Python 3.x:** The script is written in modern Python.
* **Tkinter:** This GUI library is included with most Python installations on Windows and macOS. On Linux, you may need to install it separately:
    ```bash
    # For Debian/Ubuntu-based systems
    sudo apt-get install python3-tk
    ```

### Atari 7800 External Tools

This application is a front-end; it does not include the actual development tools. You must install them and ensure they are either in your system's `PATH` or have their full paths configured in the application's settings.

* **Assembler:** `7800asm`
* **C Compiler:** `cc65` toolchain (specifically the `cl65` command)
* **Header Utility:** `7800header`
* **Signing Utility:** `7800sign`
* **Emulator:** An Atari 7800 emulator like A7800 or MAME.
* **Text Editor:** Your preferred code editor (e.g., VS Code, Sublime Text, Xed).

## Installation & Setup

1.  **Get the code:**
    Place the `devCMDcycle.py` file in a convenient location. For easiest access, add this location to your system's `PATH`.

2.  **Run the application:**
    The key to keeping project settings separate is to run the script from within your project's source code directory.
    ```bash
    # First, navigate to your project folder
    cd /path/to/my/game_project/

    # Then, run the script
    devCMDcycle.py
    ```

3.  **Initial Configuration:**
    * Running the script from within your project folder will create a new, project-specific configuration file (`devCMDcycle_237.ini`).
    * Click the **Settings** button in the application.
    * In the **Paths** section, set the global paths for your Editor, Emulator, Header Tool, Signer Tool, and Terminal.
    * Click the **Edit Toolchains...** button.
    * Select a default toolchain (e.g., `7800ASMDevKit`), or click "Add New" to create your own.
    * For the selected toolchain, set the **Executable Path** to point to the main compiler/assembler (e.g., `7800asm` or `cl65`).
    * Configure the 10 custom buttons with names, colors, and the commands they should run.
    * Click **Save & Close** on all settings windows.

Your development environment is now configured for this project.

## Basic Usage

1.  **Select Source File:** In the "Project" frame, browse for your main assembly (`.s`, `.asm`) or C (`.c`) source file.
2.  **Select Toolchain:** Choose the appropriate toolchain you configured for this project type (e.g., "7800ASMDevKit").
3.  **Choose Options:** If you configured any "Toolchain Options," check the ones you need for this build. The command preview will update live.
4.  **Build & Run:** Click your custom action buttons (e.g., Build, Build & Run).
5.  **Monitor Output:** The "Status Window" will display the output from the build process. Any errors will be shown in red.
6.  **Play!** If the build is successful, your emulator will launch with your game.

## Understanding Toolchains

A "Toolchain" is a complete build environment. You can create different toolchains for assembly, C, or even for different assemblers. You can edit them by clicking **Settings -> Edit Toolchains...**.

Each toolchain has:

* An **Executable Path:** The path to its main tool (e.g., `7800asm`). This path can be used in commands via the `%t` placeholder.
* **10 Custom Buttons:** Each button has a name, color, and a command.
* **Toolchain Options:** A set of checkboxes that add extra flags to your commands.

## Command Placeholders

When configuring button commands, you can use these placeholders:

| Placeholder | Description                                                        |
| :---------- | :----------------------------------------------------------------- |
| `%f`        | Full path to the current source file                               |
| `%s`        | Path to the source file without its extension (the "stem")         |
| `%o`        | Alias for `%s`. Used for specifying output file paths.             |
| `%t`        | Path to the main executable of the selected toolchain.             |
| `%e`        | Path to the configured text editor.                                |
| `%m`        | Path to the configured emulator.                                   |
| `%h`        | Path to the configured `7800header` tool.                          |
| `%g`        | Path to the configured `7800sign` tool.                            |
| `%term`     | Path to the configured external terminal.                          |
| `EXTERNAL:` | Prefix to run a command in a separate process (non-blocking).      |
| `%NOP`      | No Operation. Used for buttons that only trigger an auto-typer.    |

## The Auto-Typer System

The Auto-Typer allows you to automate interaction with command-line tools. You can create multiple profiles by going to **Settings -> Manage Auto-Typer Profiles...**.

Each profile can have multiple steps, and each step can contain a list of commands that are "typed" into the running process. A command is triggered if its "Label Button" matches the action button that started the process.

### Special Auto-Typer Placeholders

In the profile editor, you can use special placeholders in your commands:

| Placeholder | Description                                                                                    |
| :---------- | :--------------------------------------------------------------------------------------------- |
| `%C<key>`   | Sends a `CTRL+key` combination (e.g., `%C<c>` sends `CTRL+C`).                                   |
| `%A<key>`   | Sends an `ALT+key` combination (e.g., `%A<f>` sends `ALT+F`).                                    |
| `%b<num>`   | Creates a text input box of `<num>` width in the Settings UI. The text entered by the user will be substituted here. |

## License

This program is free software, distributed under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

For more details, see the full license text at <https://www.gnu.org/licenses/gpl-3.0.html>.

---
_Created by RetroGameGirl (atariage)_
