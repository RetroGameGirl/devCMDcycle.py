# devCMDcycle - Atari 7800 Development Commander

---
### A Note on this Version

Please be aware that this is the initial version of `devCMDcycle`. The code originated as a collection of personal scripts I wrote to simplify my own Atari 7800 development workflow.  It only really works properly on a linux system as I did not bother to check it on windows.

I am sharing it primarily for historical purposes and as a snapshot of my personal development process at the time. While it is functional, it reflects an organic evolution rather than a planned software design. Use at your own risk, and thank you for your interest!

---

## Features

* **Unified Interface:** Manage your entire build/run/debug cycle from a single, clean window.
* **Compiler Support:** Seamlessly switch between **7800AsmDevKit** (for assembly) and **CC65** (for C) projects.
* **One-Click Actions:** Buttons for common tasks like "Build", "Run", "Edit", "Clean", and combined actions like "Build & Run".
* **Live Status Console:** View real-time, color-coded output from your command-line tools directly within the app.
* **Interactive Command Input:** Interact with tools that require input (like the `7800header` utility) from within the app's console.
* **Header Automation:** A powerful "Header Command Wizard" allows you to visually build and automatically apply complex `7800header` commands, enabling a "headless" build process.
* **Highly Configurable:** Easily set paths to your tools and customize the exact command-line arguments for every action through a detailed settings panel.
* **Project Management:** Automatically saves your last-used project and settings for a quick start.
* **Cross-Platform:** Built with Python's standard library to be compatible with Linux, macOS, and Windows.

## Requirements

Before running `devCMDcycle`, you must have the following software installed on your system.

#### Core Dependencies

* **Python 3.x:** The script is written in modern Python.
* **Tkinter:** This GUI library is included with most Python installations on Windows and macOS. On Linux, you may need to install it separately:
    ```bash
    # For Debian/Ubuntu-based systems
    sudo apt-get install python3-tk
    ```

#### Atari 7800 External Tools

This application is a front-end; it does **not** include the actual development tools. You must install them and ensure they are either in your system's `PATH` or have their full paths configured in the application's settings.

* **Assembler:** [7800asm](https://github.com/7800-devtools/7800asm)
* **C Compiler:** [cc65 toolchain](https://cc65.github.io/) (specifically the `cl65` command)
* **Header Utility:** `7800header`
* **Signing Utility:** `7800sign`
* **Emulator:** An Atari 7800 emulator like [A7800](https://a7800.a-7800.com/) or MAME.
* **Text Editor:** Your preferred code editor (e.g., VS Code, Sublime Text, Xed).

## Installation & Setup

1.  **Get the code:**
    Place the `devCMDcycle.py` file in a convenient location that is part of your system's `PATH`.

2.  **Run the application:**
    The key to keeping project settings separate is to run the script from *within your project's source code directory*.
    ```bash
    # First, navigate to your project folder
    cd /path/to/my/game_project/
    
    # Then, run the script
    devCMDcycle.py
    ```

3.  **Initial Configuration:**
    * Running the script from within your project folder will create a project-specific configuration file (`devCMDcycle_115.ini`) inside that same folder.
    * Click the **Settings** button in the application.
    * In the **Paths** section, click "Browse..." for each tool (`Editor`, `7800asm Script`, `Emulator`, etc.) and navigate to the correct executable file on your system.
    * Review the **Command Line Templates** to ensure they match the arguments required by your tools.
    * Click **Save & Close**.

Your development environment is now configured for this project. Repeat step 2 for each new project to create separate configurations.

## Usage

1.  **Select Source File:** In the "Project" frame, click "Browse..." and select your main assembly (`.s`, `.asm`) or C (`.c`) source file.
2.  **Check Configuration:** The application will automatically detect the compiler and generate a default name for the "Output ROM" (`.a78` file).
3.  **Choose Options:** Select any compiler-specific options (e.g., "Run Header Tool after build").
4.  **Build & Run:** Click the **Build & Run** button.
5.  **Monitor Output:** The "Status Window" will display the output from the build process. Any errors will be shown in red.
6.  **Play!** If the build is successful, your emulator will launch with your game.

## License

This program is free software, distributed under the terms of the **GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.**

For more details, see the full license text at [https://www.gnu.org/licenses/gpl-3.0.html](https://www.gnu.org/licenses/gpl-3.0.html).

---
*Created by RetroGameGirl (atariage)*
