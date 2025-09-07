# devCMDcycle.py v2.19

**IMPORTANT:** This version (2.19) is provided for historical purposes. It has been superseded by a newer version. Users are encouraged to seek out the latest version for the most up-to-date features and bug fixes.

A toolchain-agnostic GUI orchestrator for streamlining any command-line development workflow.

# What is devCMDcycle.py?

devCMDcycle.py is a powerful front-end for managing software build environments. Originally designed for Atari 7800 retro development, it has evolved into a flexible tool that can be configured to handle any command-line-driven workflow. It provides a simple, clickable interface to manage complex build steps, eliminating the need to memorize and type repetitive commands.
Whether you are developing for a retro console, compiling C++ code, or managing a web project, devCMDcycle.py acts as your central launchpad.

# Key Features

 * Customizable Toolchains: Define different build environments for each of your projects. A developer could have a "Toolchain" for 6502 assembly, another for a C-based project using GCC, and a third for Node.js.
 * Action Grid with Composite Commands: Configure a grid of up to 10 custom buttons to run any command. A single button press can trigger a sequence of other actions (e.g., Button3,Button8,Button4 to Build, then Apply Header, then Run).
 * Dynamic Command-Line Options: Create user-friendly checkboxes for your toolchains that add optional flags to your commands (e.g., enable a "Debug Mode" flag or a "Generate List File" flag).
 * Live Command Preview: See exactly what command will be executed in real-time as you toggle options, preventing configuration errors.
 * Integrated Status Window: View all output from your build tools in a real-time console that supports ANSI color codes for readability.
 * Legacy Tool Compatibility: Features a unique "Auto-Typer" that can send a sequence of commands to older, interactive command-line tools that don't support simple flags.

# Getting Started

 * Ensure you have Python 3.x and the Tkinter library installed.
 * put the script in your path and run the script from your project's directory: devCMDcycle.py
 * Select your main source file and the appropriate toolchain.
 * Configure your toolchains, paths, and custom buttons via the Settings menu.
Configuration

The true power of devCMDcycle.py lies in its configuration. All settings are stored in a simple .ini file, making your setups portable.

The application uses a placeholder system to make commands flexible:

 * %f: Full path to the current source file
 * %s: Source file path without its extension
 * %t: Path to the main executable of the selected toolchain
 * %e: Path to the configured text editor
 * %m: Path to the configured emulator
 * EXTERNAL: prefix: Spawns a command as a new process outside of the status window (e.g., EXTERNAL:%e %f to open a file in your editor).


# iniCMDcycle.py
This is a utility to convert the generated ini toolchain data to something that can be included as a default in the devCMDcycle.py source.
