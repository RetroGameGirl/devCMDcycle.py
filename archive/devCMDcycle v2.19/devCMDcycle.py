#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
####################################################################################
# Copyright (C) 2025 RetroGameGirl (atariage)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
####################################################################################
"""

import tkinter as tk
from tkinter import filedialog, ttk, font as tkfont, messagebox, simpledialog, colorchooser
from collections import deque, defaultdict
import subprocess
import os
import sys
import configparser
import shlex
import queue
import threading
import re
import copy
import time
import ast

# Conditional import for Unix-like systems for better terminal emulation
if sys.platform != "win32":
    import pty

# --- Global Constants ---
CONFIG_FILE_NAME = 'devCMDcycle_219.ini'

"""
################################################################################
#
# DEFAULT CONFIGURATION
#
# This dictionary contains all the default settings for the application. It is
# the blueprint for the `devCMDcycle_219.ini` file that is
# automatically created when the program runs for the first time.
#
# This section serves as a complete reference for all configuration options.
# You can directly edit these values, but it is recommended to use the in-app
# Settings menu for safety.
#
# ---
# General Structure:
# The configuration is a Python dictionary with keys representing sections.
# Inside each section, there are key-value pairs for specific settings.
# Many values, especially lists and dictionaries, are stored as Python-formatted
# strings. The program uses `ast.literal_eval()` to safely convert these strings
# back into Python objects at runtime. This allows complex data structures to be
# stored and retrieved from the flat .ini file.
#
# ---
# Placeholder System:
# The `Actions` and `Toolchains` sections use special placeholders to make
# commands portable. The program replaces these with the correct paths at runtime.
#
# Common Placeholders:
#   %f: Full path to the current source file (e.g., /home/user/mygame/main.s)
#   %s: Path to the source file without its extension (e.g., /home/user/mygame/main)
#   %o: Alias for %s. Used for specifying output file paths.
#   %t: Path to the main executable of the selected toolchain.
#   %e: Path to the configured text editor.
#   %m: Path to the configured emulator.
#   %h: Path to the configured 7800header tool.
#   %g: Path to the configured 7800sign tool.
#   %term: Path to the configured external terminal.
#   %cmd: The command to be passed to the external terminal when using `EXTERNAL:`.
#   EXTERNAL: this is needed to span an application process outside of the status window
#             for instance, terminals, editors, command prompts, other software, etc.
#
# ---
# Composite Commands:
# Buttons can execute a sequence of other buttons. This is done by listing the
# target button keys, separated by commas (e.g., `'Button3,Button8,Button4'`).
# When you click the button, the program executes each action in the list, in
# order, waiting for one to finish before starting the next.
#
# ---
# External Commands:
# To run a command in an external terminal, you must first configure the `terminal`
# path in the `[Paths]` section of the Settings menu. Then, in a button's
# command field, use the `EXTERNAL:` prefix followed by your desired command.
# 
# `'EXTERNAL:%term'`, which just opens a new terminal window.
#
################################################################################
"""

DEFAULT_CONFIG = {
    'Paths': {
        'last_source': '',
        'last_toolchain': '-- Select Toolchain --',
        'editor': 'xed',
        'emulator': 'a7800',
        'header_tool': '7800header',
        'signer_tool': '7800sign',
        'terminal': 'gnome-terminal' if sys.platform != "win32" else 'cmd'
    },
    'Actions': {
        'edit': "%e %f",
        'run': "%m a7800 -cart %o.a78",
        'run_debug': "%m a7800 -cart %o.a78 -debug",
        'compile_dasm': "%t %f",
        'compile_cc65': "%t -t atari7800 -o %o.a78 %f",
        'add_header': "%h %s.bin",
        'add_header_a78': "%h %o.a78",
        'sign_rom': "%g %o.a78",
        
    },
    'Options': {
        'header_auto_send_command': 'False',
        'header_auto_command': 'save; exit',
        'header_initial_delay': '1.0',
        'header_command_delay': '0.5',
        'always_on_top': 'False',
        'dark_mode': 'False',
        'clean_extensions': '.a78,.o,.bin,.s.a78,.s.bin,.lst,.list.txt,.s.list.txt,.sym,.symbol.txt,.s.symbol.txt,.map,.a78.map,.dbg,.a78.backup,.s.a78.backup'
    },
    'Geometry': {
        'main_window': '',
        'settings_window': '',
        'toolchain_editor': '',
        'toolchain_options_editor': ''
    },
    'DefaultGeometry': {
        'main_window': '800x1000',
        'settings_window': '1120x920',
        'toolchain_editor': '1210x900',
        'toolchain_options_editor': '800x700'
    },
    'HeaderWizard': {},
    'CleanStates': {},
    'ToolchainStates': {},
    'Toolchains': {
        '-- Select Toolchain --': {
            'path': '',
            'build_steps': '[]',
            'header_action': '',
            'toolchain_options': '[]',
            'auto_typer_button': 'None',
            'custom_buttons': str({
                'Button1': {'name': '', 'command': '', 'color':  '#add8e6'},
                'Button2': {'name': '', 'command': '', 'color': '#F0F0F0'},
                'Button3': {'name': '', 'command': '', 'color': '#F0F0F0'},
                'Button4': {'name': '', 'command': '', 'color': '#F0F0F0'},
                'Button5': {'name': '', 'command': '', 'color': '#F0F0F0'},
                'Button6': {'name': '', 'command': '', 'color': '#F0F0F0'},
                'Button7': {'name': '', 'command': '', 'color': '#F0F0F0'},
                'Button8': {'name': '', 'command': '', 'color': '#F0F0F0'},
                'Button9': {'name': '', 'command': '', 'color': '#F0F0F0'},
                'Button10': {'name': '', 'command': '', 'color': '#F0F0F0'}
            })
        },
        '7800ASMDevKit': {
            'path': '7800asm',
            'build_steps': "['compile_dasm', 'add_header']",
            'header_action': 'add_header',
            'toolchain_options': str([
                {'name': 'Generate List File', 'flag': '-l', 'target': 'Button3'},
                {'name': 'Generate Symbol File', 'flag': '-s', 'target': 'Button3'}
            ]),
            'auto_typer_button': 'Button8',
            'custom_buttons': str({
                'Button1': {'name': 'Terminal', 'command': 'EXTERNAL:%term', 'color': '#e0e0e0'},
                'Button2': {'name': 'Edit', 'command': 'EXTERNAL:%e %f', 'color': '#e0e0e0'},
                'Button3': {'name': 'Build', 'command': '%t %f', 'color': '#90ee90'},
                'Button4': {'name': 'Run', 'command': 'EXTERNAL:%m a7800 -cart %s.s.a78', 'color': '#90ee90'},
                'Button5': {'name': 'Run (Debug)', 'command': 'EXTERNAL:%m a7800 -cart %s.s.a78 -debug', 'color': '#add8e6'},
                'Button6': {'name': 'Build & Run', 'command': 'Button3,Button8,Button4', 'color': '#90ee90'},
                'Button7': {'name': 'Build & Run (Debug)', 'command': 'Button3,Button8,Button5', 'color': '#add8e6'},
                'Button8': {'name': 'Apply Header', 'command': '%h %s.s.bin', 'color': '#e0e0e0'},
                'Button9': {'name': 'Apply Signer', 'command': '%g %s.s.a78', 'color': '#e0e0e0'},
                'Button10': {'name': '', 'command': '', 'color': '#F0F0F0'}
            })
        },
        'cc65': {
            'path': 'cl65',
            'build_steps': "['compile_cc65', 'sign_rom', 'add_header_a78']",
            'header_action': 'add_header_a78',
            'toolchain_options': str([
                {'name': 'Create Map File', 'flag': '-m %s.map', 'target': 'Button3'},
                {'name': 'Add Debug Info', 'flag': '-g', 'target': 'Button3'}
            ]),
            'auto_typer_button': 'Button8',
            'custom_buttons': str({
                'Button1': {'name': 'Terminal', 'command': 'EXTERNAL:%term', 'color': '#e0e0e0'},
                'Button2': {'name': 'Edit', 'command': 'EXTERNAL:%e %f', 'color': '#e0e0e0'},
                'Button3': {'name': 'Build', 'command': '%t -t atari7800 -o %s.bin %f', 'color': '#90ee90'},
                'Button4': {'name': 'Run', 'command': 'EXTERNAL:%m a7800 -cart %s.a78', 'color': '#90ee90'},
                'Button5': {'name': 'Run (Debug)', 'command': 'EXTERNAL:%m a7800 -cart %s.a78 -debug', 'color': '#add8e6'},
                'Button6': {'name': 'Build & Run', 'command': 'Button3,Button9,Button8,Button4', 'color': '#90ee90'},
                'Button7': {'name': 'Build & Run (Debug)', 'command': 'Button3,Button9,Button8,Button5', 'color': '#add8e6'},
                'Button8': {'name': 'Apply Header', 'command': '%h %s.bin', 'color': '#e0e0e0'},
                'Button9': {'name': 'Apply Signer', 'command': '%g %s.bin', 'color': '#e0e0e0'},
                'Button10': {'name': '', 'command': '', 'color': '#F0F0F0'}
            })
        }
    }
}

# --- Helper Classes ---

class AnsiColorHandler:
    """Processes ANSI color codes for display in a Tkinter Text widget."""
#
# Initializes the AnsiColorHandler object.
#
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.ansi_escape = re.compile(r'\x1B\[([0-9;?]*)m')
        self.light_map = {'30': 'black', '31': 'red', '32': 'green', '33': 'yellow', '34': 'blue', '35': 'magenta', '36': 'cyan', '37': 'white'}
        self.setup_tags()
#
# Configures Tkinter text tags for different ANSI colors and styles.
#
    def setup_tags(self):
        for code, color in self.light_map.items():
            self.text_widget.tag_configure(f"ansi_{color}", foreground=color)
        try:
            bold_font = tkfont.Font(self.text_widget, self.text_widget.cget("font"))
            bold_font.configure(weight="bold")
            self.text_widget.tag_configure("ansi_bold", font=bold_font)
        except tk.TclError:
            pass
#
# Writes text to the associated text widget, processing and applying ANSI
# escape codes for color and style.
#
    def write(self, text):
        text = re.sub(r'\x1B\[[0-9;?]*[HJK]', '', text).replace('\r', '')
        segments = self.ansi_escape.split(text)
        current_tags = []
        for i, segment in enumerate(segments):
            if i % 2 == 0:
                if segment:
                    self.text_widget.insert(tk.END, segment, tuple(current_tags))
            else:
                if segment == '0' or not segment:
                    current_tags = []
                    continue
                for p in segment.split(';'):
                    if p in self.light_map:
                        current_tags = [t for t in current_tags if not (t.startswith('ansi_') and t != 'ansi_bold')]
                        current_tags.append(f"ansi_{self.light_map[p]}")
                    elif p == '1':
                        if "ansi_bold" not in current_tags:
                            current_tags.append("ansi_bold")

class HeaderWizardFrame(ttk.LabelFrame):
    """A frame containing a wizard to build the 7800header command."""
#
# Initializes the HeaderWizardFrame, setting up options and creating widgets.
#
    def __init__(self, parent, app_controller):
        super().__init__(parent, text="Header Command Wizard", padding=10)
        self.app = app_controller
        self.vars = {}
        self.cart_opts = ['linear', 'supergame', 'souper', 'bankset', 'absolute', 'activision']
        self.mem_opts = ['rom@4000', 'bank6@4000', 'ram@4000', 'mram@4000', 'hram@4000', 'bankram']
        self.chip_opts = ['pokey@440', 'pokey@450', 'pokey@800', 'pokey@4000', 'ym2151@460', 'covox@430', 'adpcm@420']
        self.irq_opts = ['irqpokey1', 'irqpokey2', 'irqym2151']
        self.controller_opts = ['7800joy1', '7800joy2', 'lightgun1', 'lightgun2', 'paddle1', 'paddle2', 'tball1', 'tball2', '2600joy1', '2600joy2', 'driving1', 'driving2', 'keypad1', 'keypad2', 'stmouse1', 'stmouse2', 'amouse1', 'amouse2', 'snes1', 'snes2', 'mega78001', 'mega78002']
        self.misc_opts = ['hsc', 'savekey', 'xm', 'tvpal', 'tvntsc', 'composite', 'mregion']
        self.create_widgets()
        self.link_vars()
#
# Creates and arranges all the UI widgets for the header wizard.
#
    def create_widgets(self):
        opts_frame = ttk.Frame(self)
        opts_frame.pack(fill='x', expand=True)
        def create_check_frame(parent, title, opts):
            frame = ttk.LabelFrame(parent, text=title, padding=5)
            for i, opt in enumerate(opts):
                key = f"h_wiz_{opt.replace('@', '_').replace('/', '_')}"
                self.vars[key] = tk.BooleanVar()
                ttk.Checkbutton(frame, text=opt, variable=self.vars[key]).grid(row=i, column=0, sticky='w')
            return frame
        create_check_frame(opts_frame, "Cart", self.cart_opts).pack(side='left', anchor='n', padx=2)
        create_check_frame(opts_frame, "Memory", self.mem_opts).pack(side='left', anchor='n', padx=2)
        create_check_frame(opts_frame, "Sound/IRQ", self.chip_opts + self.irq_opts).pack(side='left', anchor='n', padx=2)
        create_check_frame(opts_frame, "Controllers", self.controller_opts).pack(side='left', anchor='n', padx=2)
        create_check_frame(opts_frame, "Misc", self.misc_opts).pack(side='left', anchor='n', padx=2)
        cmd_frame = ttk.LabelFrame(self, text="Commands", padding=5)
        cmd_frame.pack(fill='x', expand=True, pady=5)
        cmd_frame.columnconfigure(1, weight=1)
        self.vars['h_wiz_name_en'] = tk.BooleanVar()
        self.vars['h_wiz_name'] = tk.StringVar()
        ttk.Checkbutton(cmd_frame, text="name", variable=self.vars['h_wiz_name_en']).grid(row=0, column=0, sticky='w')
        ttk.Entry(cmd_frame, textvariable=self.vars['h_wiz_name']).grid(row=0, column=1, sticky='ew')
        actions = ['save', 'strip', 'fix', 'exit']
        ttk.Label(cmd_frame, text="Final Action(s):").grid(row=1, column=0, columnspan=2, sticky='w', pady=(5,0))
        for i, action in enumerate(actions):
            key = f"h_wiz_act_{action}"
            self.vars[key] = tk.BooleanVar()
            ttk.Checkbutton(cmd_frame, text=action, variable=self.vars[key]).grid(row=i+2, column=0, sticky='w')
#
# Links Tkinter variables to the _build_command method to enable automatic updates.
#
    def link_vars(self):
        for key in self.vars:
            self.vars[key].trace_add('write', self._build_command)
        self._build_command()
#
# Constructs the header tool command string based on the current state of the wizard's UI elements.
#
    def _build_command(self, *args):
        commands = []
        all_opts = self.cart_opts + self.mem_opts + self.chip_opts + self.irq_opts + self.controller_opts + self.misc_opts
        for opt in all_opts:
            key = f"h_wiz_{opt.replace('@', '_').replace('/', '_')}"
            if self.vars.get(key) and self.vars[key].get():
                commands.append(f"set {opt}")
        if self.vars['h_wiz_name_en'].get() and self.vars['h_wiz_name'].get():
            commands.append(f"name \"{self.vars['h_wiz_name'].get()}\"")
        for action in ['save', 'strip', 'fix', 'exit']:
            if self.vars.get(f"h_wiz_act_{action}") and self.vars[f"h_wiz_act_{action}"].get():
                commands.append(action)
        self.app.config['Options']['header_auto_command'] = "; ".join(commands)

class SettingsWindow(tk.Toplevel):
    """A Toplevel window for managing all global settings."""
#
# Initializes the SettingsWindow, which provides a UI for configuring global application settings.
#
    def __init__(self, parent, app_controller):
        super().__init__(parent)
        self.transient(parent)
        self.title("Global Settings")
        self.app = app_controller
        
        saved_geom = self.app.config.get('Geometry', {}).get('settings_window')
        if not saved_geom or saved_geom == '':
            saved_geom = self.app.config.get('DefaultGeometry', {}).get('settings_window', '900x700')
        self.geometry(saved_geom)

        self.vars = {}
        self.clean_vars = {}
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill="both", expand=True)
        main_frame.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1) 

        # --- Left Column ---
        left_col = ttk.Frame(main_frame)
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        paths_frame = self.create_paths_frame(left_col)
        paths_frame.pack(fill='x', pady=5)
        
        ttk.Button(left_col, text="Edit Toolchains...", command=self.open_toolchain_editor).pack(fill='x', pady=10)

        misc_frame = self.create_misc_options_frame(left_col)
        misc_frame.pack(fill='x', pady=5)
        
        clean_frame = self.create_clean_settings_frame(left_col)
        clean_frame.pack(fill='x', pady=5)
        
        # --- Right Column ---
        right_col = ttk.Frame(main_frame)
        right_col.grid(row=0, column=1, sticky="nsew")
        header_frame = self.create_header_settings(right_col)
        header_frame.pack(fill='both', expand=True, pady=5)
        
        # --- Bottom Button ---
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=1, sticky='e', pady=(10,0))
        ttk.Button(button_frame, text="Save & Close", command=self.save_and_close, style="Accent.TButton").pack()
        
        self.protocol("WM_DELETE_WINDOW", self.save_and_close)
        self.load_settings_into_ui()
#
# Creates and returns a frame for configuring tool paths.
#
    def create_paths_frame(self, parent):
        frame = ttk.LabelFrame(parent, text="Paths to Tools", padding=10)
        frame.columnconfigure(1, weight=1)
        paths = self.app.get_default_config()['Paths'].keys()
        for i, key in enumerate(p for p in paths if not p.startswith('last_')):
            ttk.Label(frame, text=f"{key.replace('_', ' ').title()}:").grid(row=i, column=0, sticky='w', pady=2)
            self.vars[key] = tk.StringVar(name=f"settings_path_{key}")
            ttk.Entry(frame, textvariable=self.vars[key]).grid(row=i, column=1, sticky='ew', padx=5)
            ttk.Button(frame, text="...", width=3, command=lambda v=self.vars[key]: self.browse_file(v)).grid(row=i, column=2)
        return frame
#
# Creates and returns a frame for configuring header auto-typer settings.
#
    def create_header_settings(self, parent):
        frame = ttk.LabelFrame(parent, text="Header Auto-Typer Settings", padding=10)
        
        self.header_wizard = HeaderWizardFrame(frame, self.app)
        self.header_wizard.pack(fill='x', pady=5)
        
        controls_frame = ttk.Frame(frame)
        controls_frame.pack(fill='x', pady=5, anchor='s')

        ttk.Label(controls_frame, text="Initial Delay (s):").grid(row=0, column=0, sticky='w')
        self.vars['header_initial_delay'] = tk.StringVar(name='settings_header_initial_delay')
        ttk.Entry(controls_frame, textvariable=self.vars['header_initial_delay'], width=5).grid(row=0, column=1, sticky='w')

        ttk.Label(controls_frame, text="Command Delay (s):").grid(row=1, column=0, sticky='w', pady=(2,0))
        self.vars['header_command_delay'] = tk.StringVar(name='settings_header_command_delay')
        ttk.Entry(controls_frame, textvariable=self.vars['header_command_delay'], width=5).grid(row=1, column=1, sticky='w', pady=(2,0))
        
        self.vars['header_auto_send_command'] = tk.BooleanVar(name='settings_header_auto_send_command')
        cb = ttk.Checkbutton(controls_frame, text="Enable Auto-Typer for Header Tool", variable=self.vars['header_auto_send_command'])
        cb.grid(row=2, column=0, columnspan=2, sticky='w', pady=(10,0))
        return frame
#
# Creates and returns a frame for configuring which file extensions to clean.
#
    def create_clean_settings_frame(self, parent):
        frame = ttk.LabelFrame(parent, text="Clean File Extensions", padding=10)
        frame.columnconfigure(0, weight=1)
        
        ttk.Label(frame, text="Comma-separated list of extensions to generate checklist:", wraplength=380).pack(anchor='w')
        self.vars['clean_extensions'] = tk.StringVar(name='settings_clean_extensions')
        entry = ttk.Entry(frame, textvariable=self.vars['clean_extensions'])
        entry.pack(fill='x', expand=True, pady=(5,10))
        
        ttk.Separator(frame, orient='horizontal').pack(fill='x', pady=5)
        
        self.clean_checkbox_frame = ttk.Frame(frame)
        self.clean_checkbox_frame.pack(fill='x')
        
        self.vars['clean_extensions'].trace_add('write', self.refresh_clean_checkboxes)
        return frame
#
# Regenerates the checklist of file extensions for the cleaning process based
# on the current configuration.
#
    def refresh_clean_checkboxes(self, *args):
        if not self.winfo_exists() or not self.clean_checkbox_frame.winfo_exists():
            return
            
        for widget in self.clean_checkbox_frame.winfo_children():
            widget.destroy()
        self.clean_vars.clear()
        
        extensions_str = self.vars['clean_extensions'].get()
        extensions = [ext.strip() for ext in extensions_str.split(',') if ext.strip()]
        
        clean_states = self.app.config.get('CleanStates', {})
        
        num_cols = 4
        for i, ext in enumerate(extensions):
            var = tk.BooleanVar(name=f"clean_var_{ext}")
            is_enabled = clean_states.get(ext, 'False').lower() == 'true'
            var.set(is_enabled)
            
            self.clean_vars[ext] = var
            cb = ttk.Checkbutton(self.clean_checkbox_frame, text=ext, variable=var)
            cb.grid(row=i // num_cols, column=i % num_cols, sticky='w')
#
# Creates and returns a frame for miscellaneous application options.
#
    def create_misc_options_frame(self, parent):
        frame = ttk.LabelFrame(parent, text="Misc Options", padding=10)
        self.vars['dark_mode'] = tk.BooleanVar(name='settings_dark_mode')
        ttk.Checkbutton(frame, text="Dark Mode (Requires Restart)", variable=self.vars['dark_mode']).pack(anchor='w')
        return frame
#
# Populates the settings UI with values from the current application configuration.
#
    def load_settings_into_ui(self):
        for section_name in ['Paths', 'Options']:
            for key, value in self.app.config.get(section_name, {}).items():
                if key in self.vars:
                    var = self.vars[key]
                    if isinstance(var, tk.BooleanVar): var.set(value.lower() == 'true')
                    else: var.set(value)
        self.refresh_clean_checkboxes()
        for key, value in self.app.config.get('HeaderWizard', {}).items():
             if key in self.header_wizard.vars:
                var = self.header_wizard.vars[key]
                if isinstance(var, tk.BooleanVar): var.set(value.lower() == 'true')
                else: var.set(value)
#
# Opens the toolchain editor window.
#
    def open_toolchain_editor(self):
        ToolchainEditorWindow(self, self.app)
#
# Saves all current settings from the UI back to the application's configuration and closes the window.
#
    def save_and_close(self):
        self.app.config['Geometry']['settings_window'] = self.geometry()
        for section_key in ['Paths', 'Options']:
            if section_key not in self.app.config: self.app.config[section_key] = {}
            for key in self.app.get_default_config()[section_key]:
                if key in self.vars:
                    self.app.config[section_key][key] = str(self.vars[key].get())

        self.app.config['CleanStates'] = {ext: str(var.get()) for ext, var in self.clean_vars.items()}
        for key, var in self.header_wizard.vars.items():
             self.app.config['HeaderWizard'][key] = str(var.get())
        
        self.app.save_config()
        self.app.populate_ui_from_config()
        self.destroy()
#
# Opens a file dialog to allow the user to select a file, updating the provided Tkinter variable with the chosen path.
#
    def browse_file(self, var):
        if path := filedialog.askopenfilename(): var.set(path)

class ToolchainEditorWindow(tk.Toplevel):
    """A Toplevel window for creating, editing, and deleting toolchains."""
#
# Initializes the ToolchainEditorWindow, which allows for managing toolchain configurations.
#
    def __init__(self, parent, app_controller):
        super().__init__(parent)
        self.transient(parent)
        self.grab_set()
        self.title("Toolchain Editor")
        self.app = app_controller
        self.vars = {}
        self.preview_vars = {}
        self.color_labels = {}
        self.last_saved_toolchain = tk.StringVar()
        self.auto_typer_button_var = tk.StringVar()
        self.loading_data = False # Flag to prevent saving during UI population
        self.toolchain_path_var = tk.StringVar()
        
        saved_geom = self.app.config.get('Geometry', {}).get('toolchain_editor')
        if not saved_geom or saved_geom == '':
            saved_geom = self.app.config.get('DefaultGeometry', {}).get('toolchain_editor', '1200x900')
        self.geometry(saved_geom)

        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill="both", expand=True)
        main_frame.rowconfigure(1, weight=1)
        main_frame.columnconfigure(0, weight=1) 
 
        self.create_top_frame(main_frame)
        self.create_buttons_frame(main_frame)
        self.create_legend_frame(main_frame)
        self.create_bottom_frame(main_frame)
        
        self.protocol("WM_DELETE_WINDOW", self.save_and_close)
        self.populate_toolchain_list()
        self.combobox.bind("<<ComboboxSelected>>", self.load_toolchain_data)
        if self.app.toolchain_type.get() in self.combobox['values']:
            self.combobox.set(self.app.toolchain_type.get())
        self.load_toolchain_data()
#
# Creates and configures the top frame of the toolchain editor window, including toolchain selection and management controls.
#
    def create_top_frame(self, parent):
        frame = ttk.LabelFrame(parent, text="Toolchain Management", padding=10)
        frame.grid(row=0, column=0, columnspan=2, sticky='ew', pady=(0, 10))
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Select Toolchain:").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.combobox = ttk.Combobox(frame, state='readonly', exportselection=False)
        self.combobox.grid(row=0, column=1, sticky='ew', padx=5)

        ttk.Label(frame, text="Toolchain Name:").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        self.toolchain_name_var = tk.StringVar()
        self.toolchain_name_var.trace_add('write', self.on_name_change)
        ttk.Entry(frame, textvariable=self.toolchain_name_var).grid(row=1, column=1, sticky='ew', padx=5)
        
        ttk.Label(frame, text="Executable Path:").grid(row=2, column=0, sticky='w', padx=5, pady=2)
        self.toolchain_path_var.trace_add('write', self.save_current_toolchain_data)
        ttk.Entry(frame, textvariable=self.toolchain_path_var).grid(row=2, column=1, sticky='ew', padx=5)

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=0, column=2, rowspan=3, padx=5)
        ttk.Button(button_frame, text="Add New", command=self.add_new_toolchain).pack(fill='x', pady=1)
        ttk.Button(button_frame, text="Delete", command=self.delete_toolchain, style="Danger.TButton").pack(fill='x', pady=1)
#
# Creates the frame containing the configuration options for custom action buttons.
#
    def create_buttons_frame(self, parent):
        container = ttk.LabelFrame(parent, text="Button Configuration", padding=10)
        container.grid(row=1, column=0, sticky='nsew', padx=(0,10))
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        canvas = tk.Canvas(container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Calculate a pixel width for 40 characters to enforce a fixed size
        default_font = tkfont.nametofont("TkDefaultFont")
        pixel_width = default_font.measure("0") * 40

        left_col = ttk.Frame(scrollable_frame)
        left_col.grid(row=0, column=0, sticky='new', padx=(0, 10))
        right_col = ttk.Frame(scrollable_frame)
        right_col.grid(row=0, column=1, sticky='new')

        for i in range(1, 11):
            parent_col = left_col if i <= 5 else right_col
            key = f'Button{i}'
            self.vars[f'{key}_name'] = tk.StringVar()
            self.vars[f'{key}_command'] = tk.StringVar()
            self.vars[f'{key}_color'] = tk.StringVar(value='#F0F0F0')
            self.preview_vars[key] = tk.StringVar()

            if i > 1 and i != 6:
                ttk.Separator(parent_col, orient='horizontal').pack(fill='x', pady=(15, 5))

            frame = ttk.Frame(parent_col, padding=5)
            frame.pack(fill='x', expand=True)
            
            name_frame = ttk.Frame(frame)
            name_frame.grid(row=0, column=0, columnspan=2, sticky='ew')
            name_frame.columnconfigure(1, weight=1)
            ttk.Label(name_frame, text=f"{key}:").pack(side='left', padx=(0,5))
            name_entry = ttk.Entry(name_frame, textvariable=self.vars[f'{key}_name'])
            name_entry.pack(side='left', fill='x', expand=True)

            color_btn = ttk.Button(frame, text="Color...", width=8, command=lambda k=key: self.choose_color(k))
            color_btn.grid(row=0, column=2, sticky='e', padx=5)
            self.color_labels[key] = tk.Label(frame, text='    ', background='#F0F0F0', relief='sunken')
            self.color_labels[key].grid(row=0, column=3, sticky='e')

            ttk.Label(frame, text="Command:").grid(row=1, column=0, sticky='w', pady=(5,0))
            
            cmd_entry = ttk.Entry(frame, textvariable=self.vars[f'{key}_command'], width=40)
            cmd_entry.grid(row=1, column=1, columnspan=3, sticky='w', pady=(5,0))
            
            ttk.Label(frame, text="Preview:").grid(row=2, column=0, sticky='w', pady=(2,0))

            preview_label = ttk.Label(frame, textvariable=self.preview_vars[key], relief='sunken', padding=2, anchor='w', wraplength=pixel_width, justify='left')
            preview_label.grid(row=2, column=1, columnspan=3, sticky='w', pady=(2,0))

            for var in [self.vars[f'{key}_name'], self.vars[f'{key}_command'], self.vars[f'{key}_color']]:
                var.trace_add('write', self.save_current_toolchain_data)
            self.vars[f'{key}_command'].trace_add('write', lambda *a, k=key: self.update_preview(k))
            name_entry.bind("<FocusOut>", self.save_current_toolchain_data)
            cmd_entry.bind("<FocusOut>", self.save_current_toolchain_data)
#
# Creates and displays a legend of available command placeholders.
#
    def create_legend_frame(self, parent):
        frame = ttk.LabelFrame(parent, text="Placeholders", padding=10)
        frame.grid(row=1, column=1, sticky='nsw')
        legend = {
            '%f': 'Full Source Path', '%s': 'Source Stem (no ext)', '%o': 'Output Stem (no ext)', 
            '%e': 'Editor Path', '%m': 'Emulator Path', '%h': 'Header Tool Path', 
            '%g': 'Signer Tool Path', '%t': 'Toolchain Path', '%term': 'Terminal Path',
            'EXTERNAL': 'This will spawn the command as an \nexternal process'
        }
        items = sorted(list(legend.items()))
        for i, (key, desc) in enumerate(items):
            ttk.Label(frame, text=f"{key}:", font=('Helvetica', 10, 'bold')).grid(row=i, column=0, sticky='e', pady=1)
            ttk.Label(frame, text=desc).grid(row=i, column=1, sticky='w', padx=5)
#
# Creates the bottom frame of the toolchain editor, containing the auto-typer selection and action buttons.
#
    def create_bottom_frame(self, parent):
        frame = ttk.Frame(parent, padding=(0,10,0,0))
        frame.grid(row=2, column=0, columnspan=2, sticky='ew')
        
        # Auto-typer selection
        typer_frame = ttk.Frame(frame)
        typer_frame.pack(side='left')
        ttk.Label(typer_frame, text="Auto-Typer Trigger Button:").pack(side='left', padx=(0,5))
        self.auto_typer_button_var.trace_add('write', self.save_current_toolchain_data)
        typer_combo = ttk.Combobox(typer_frame, textvariable=self.auto_typer_button_var, state='readonly', width=10,
                                   values=['None'] + [f'Button{i}' for i in range(1, 11)])
        typer_combo.pack(side='left')
        ttk.Label(typer_frame, text="Current:").pack(side='left', padx=(10, 5))
        ttk.Label(typer_frame, textvariable=self.auto_typer_button_var, font=('Helvetica', 10, 'bold')).pack(side='left')

        # Existing buttons
        button_container = ttk.Frame(frame)
        button_container.pack(side='right')
        ttk.Button(button_container, text="Toolchain Options Setup...", command=self.open_toolchain_options_editor).pack(side='left', padx=(0, 10))
        ttk.Button(button_container, text="Save & Close", command=self.save_and_close, style="Accent.TButton").pack(side='left')
#
# Opens the editor for configuring toolchain-specific command-line options.
#
    def open_toolchain_options_editor(self):
        toolchain_name = self.last_saved_toolchain.get()
        if not toolchain_name:
            messagebox.showerror("Error", "Please select a toolchain first.", parent=self)
            return
        ToolchainOptionsEditor(self, self.app, toolchain_name)
#
# Populates the toolchain selection combobox with the available toolchains from the configuration.
#
    def populate_toolchain_list(self):
        toolchains = sorted(list(self.app.config.get('Toolchains', {}).keys()))
        self.combobox['values'] = toolchains
#
# Loads the data for the currently selected toolchain into the editor's UI fields.
#
    def load_toolchain_data(self, *args):
        self.loading_data = True
        toolchain_name = self.combobox.get()
        if not toolchain_name:
            self.toolchain_name_var.set("")
            self.toolchain_path_var.set("")
            for i in range(1, 11):
                key = f'Button{i}'
                self.vars[f'{key}_name'].set('')
                self.vars[f'{key}_command'].set('')
                self.vars[f'{key}_color'].set('#F0F0F0')
                self.color_labels[key].config(background='#F0F0F0')
                self.update_preview(key)
            self.auto_typer_button_var.set('None')
            self.loading_data = False
            return

        self.toolchain_name_var.set(toolchain_name)
        self.last_saved_toolchain.set(toolchain_name)

        toolchain_data = self.app.config.get('Toolchains', {}).get(toolchain_name, {})
        self.toolchain_path_var.set(toolchain_data.get('path', ''))
        
        try:
            buttons_data = ast.literal_eval(toolchain_data.get('custom_buttons', '{}'))
        except (ValueError, SyntaxError):
            buttons_data = {}
        
        for i in range(1, 11):
            key = f'Button{i}'
            data = buttons_data.get(key, {})
            self.vars[f'{key}_name'].set(data.get('name', ''))
            self.vars[f'{key}_command'].set(data.get('command', ''))
            color = data.get('color', '#F0F0F0')
            self.vars[f'{key}_color'].set(color)
            self.color_labels[key].config(background=color)
            self.update_preview(key)
        
        auto_typer_btn = toolchain_data.get('auto_typer_button', 'None')
        self.auto_typer_button_var.set(auto_typer_btn)
        self.loading_data = False
#
# Updates the command preview label for a specific button to show how placeholders will be resolved.
#
    def update_preview(self, button_key):
        command_str = self.vars[f'{button_key}_command'].get().strip()
        if command_str.lower().startswith('button'):
            preview_text = f"Composite Action: {command_str}"
        else:
            paths = self.app.config.get('Paths', {})
            preview_text = self.app.resolve_command_placeholders(
                action_key=None, 
                command_override=command_str,
                replacements_override={
                    'f': '/path/to/project/source.ext', 's': '/path/to/project/source', 'o': '/path/to/project/source',
                    'e': paths.get('editor', 'editor'), 'm': paths.get('emulator', 'emulator'), 
                    'h': paths.get('header_tool', 'header'), 'g': paths.get('signer_tool', 'signer'), 
                    't': self.toolchain_path_var.get() or 'tool', 
                    'term': paths.get('terminal', 'terminal'), 'cmd': '...'
                }
            )
        self.preview_vars[button_key].set(preview_text)
#
# Handles changes to the toolchain name, renaming it in the configuration and updating the UI accordingly.
#
    def on_name_change(self, *args):
        old_name = self.last_saved_toolchain.get()
        new_name = self.toolchain_name_var.get().strip()
        if not old_name or not new_name or old_name == new_name:
            return
        
        if new_name in self.app.config['Toolchains']:
            self.combobox.set(new_name)
            self.load_toolchain_data()
            return

        self.app.config['Toolchains'][new_name] = self.app.config['Toolchains'].pop(old_name)
        self.last_saved_toolchain.set(new_name)

        current_values = list(self.combobox['values'])
        if old_name in current_values:
            idx = current_values.index(old_name)
            current_values[idx] = new_name
            self.combobox['values'] = sorted(current_values)
            self.combobox.set(new_name)
#
# Saves the current state of the toolchain's UI fields back into the application's configuration.
#
    def save_current_toolchain_data(self, *args):
        if self.loading_data:
            return

        toolchain_name = self.last_saved_toolchain.get()
        if not toolchain_name or toolchain_name not in self.app.config['Toolchains']:
            return

        buttons_data = {f'Button{i}': {
                'name': self.vars[f'Button{i}_name'].get(),
                'command': self.vars[f'Button{i}_command'].get(),
                'color': self.vars[f'Button{i}_color'].get()
            } for i in range(1, 11)}
        self.app.config['Toolchains'][toolchain_name]['custom_buttons'] = str(buttons_data)
        self.app.config['Toolchains'][toolchain_name]['auto_typer_button'] = self.auto_typer_button_var.get()
        self.app.config['Toolchains'][toolchain_name]['path'] = self.toolchain_path_var.get()
        self.app.needs_ui_rebuild = True
#
# Prompts the user for a name and adds a new, blank toolchain to the configuration.
#
    def add_new_toolchain(self):
        new_name = simpledialog.askstring("New Toolchain", "Enter a name for the new toolchain:", parent=self)
        if not new_name or not new_name.strip(): return
        new_name = new_name.strip()

        if new_name in self.app.config['Toolchains']:
            messagebox.showerror("Error", f"Toolchain '{new_name}' already exists.", parent=self)
            return

        self.app.config['Toolchains'][new_name] = copy.deepcopy(DEFAULT_CONFIG['Toolchains']['7800ASMDevKit'])
        blank_buttons = {f'Button{i}': {'name': '', 'command': '', 'color': '#F0F0F0'} for i in range(1, 11)}
        self.app.config['Toolchains'][new_name]['custom_buttons'] = str(blank_buttons)

        self.populate_toolchain_list()
        self.combobox.set(new_name)
        self.load_toolchain_data()
#
# Deletes the currently selected toolchain after user confirmation.
#
    def delete_toolchain(self):
        toolchain_name = self.combobox.get()
        if not toolchain_name: return
        
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the '{toolchain_name}' toolchain?", parent=self):
            del self.app.config['Toolchains'][toolchain_name]
            self.populate_toolchain_list()
            if self.combobox['values']:
                self.combobox.current(0)
            else:
                self.combobox.set('')
            self.load_toolchain_data()
            self.app.needs_ui_rebuild = True
#
# Opens a color chooser dialog to set the background color for a specific button.
#
    def choose_color(self, button_key):
        initial_color = self.vars[f'{button_key}_color'].get()
        color_code = colorchooser.askcolor(title="Choose button color", initialcolor=initial_color, parent=self)
        if color_code and color_code[1]:
            self.vars[f'{button_key}_color'].set(color_code[1])
            self.color_labels[button_key].config(background=color_code[1])
#
# Saves the current toolchain data and closes the editor window.
#
    def save_and_close(self):
        self.save_current_toolchain_data()
        self.app.config['Geometry']['toolchain_editor'] = self.geometry()
        self.app.save_config()
        if self.app.needs_ui_rebuild:
            self.app.on_toolchain_selected()
            self.app.needs_ui_rebuild = False
        self.destroy()

class ToolchainOptionsEditor(tk.Toplevel):
    """A Toplevel window for managing toolchain-specific command line options."""
#
# Initializes the ToolchainOptionsEditor window for a specific toolchain.
#
    def __init__(self, parent, app_controller, toolchain_name):
        super().__init__(parent)
        self.transient(parent)
        self.grab_set()
        self.title(f"Toolchain Options for '{toolchain_name}'")
        self.app = app_controller
        self.toolchain_name = toolchain_name
        self.option_rows = [] # List of dicts: {'frame': frame, 'vars': vars_dict}
        self.preview_option_vars = {} # Vars for the checkboxes in the preview pane
        self.preview_command_labels = {} # Labels for the command string preview
        self.toolchain_editor_window = parent if isinstance(parent, ToolchainEditorWindow) else None

        saved_geom = self.app.config.get('Geometry', {}).get('toolchain_options_editor')
        if not saved_geom or saved_geom == '':
            saved_geom = self.app.config.get('DefaultGeometry', {}).get('toolchain_options_editor', '800x700')
        self.geometry(saved_geom)

        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill="both", expand=True)
        main_frame.rowconfigure(1, weight=1) # Give weight to the preview area
        main_frame.columnconfigure(0, weight=1)

        self.create_scrollable_area(main_frame)
        self.create_preview_area(main_frame)
        self.create_bottom_buttons(main_frame)
        
        self.load_options()
        # Initial population of preview is handled by load_options -> create_option_row
        self.protocol("WM_DELETE_WINDOW", self.save_and_close)
#
# Creates a scrollable area for configuring toolchain options.
#
    def create_scrollable_area(self, parent):
        container = ttk.LabelFrame(parent, text="Configurable Options", padding=10)
        container.grid(row=0, column=0, sticky='ew', pady=(0,10))
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)
        
        canvas = tk.Canvas(container, highlightthickness=0, height=200) # Give it a minimum height
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas, padding=5)

        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
#
# Loads existing toolchain options from configuration and populates the UI.
#
    def load_options(self):
        for row in self.option_rows:
            row['frame'].destroy()
        self.option_rows.clear()
        
        toolchain_data = self.app.config.get('Toolchains', {}).get(self.toolchain_name, {})
        try:
            options_list = ast.literal_eval(toolchain_data.get('toolchain_options', '[]'))
        except (ValueError, SyntaxError):
            options_list = []
        
        for option in options_list:
            self.create_option_row(option)
        
        # If no options exist, still build the empty preview
        if not options_list:
            self.rebuild_preview_options()
#
# Creates a new row in the UI for configuring a single toolchain option.
#
    def create_option_row(self, option_data=None):
        if option_data is None: option_data = {}
        
        row_frame = ttk.Frame(self.scrollable_frame)
        row_frame.pack(fill='x', pady=5)
        row_frame.columnconfigure(2, weight=1) # Name entry
        row_frame.columnconfigure(4, weight=1) # Flag entry

        del_btn = ttk.Button(row_frame, text="DEL", style="Danger.TButton", width=4,
                             command=lambda f=row_frame: self.delete_option(f))
        del_btn.grid(row=0, column=0, padx=(0, 10))

        ttk.Label(row_frame, text="Name:").grid(row=0, column=1, padx=(0, 2))
        name_var = tk.StringVar(value=option_data.get('name', ''))
        ttk.Entry(row_frame, textvariable=name_var).grid(row=0, column=2, sticky='ew')
        name_var.trace_add('write', self.rebuild_preview_options)

        ttk.Label(row_frame, text="Flag:").grid(row=0, column=3, padx=(10, 2))
        flag_var = tk.StringVar(value=option_data.get('flag', ''))
        ttk.Entry(row_frame, textvariable=flag_var).grid(row=0, column=4, sticky='ew')

        ttk.Label(row_frame, text="Target:").grid(row=0, column=5, padx=(10, 2))
        target_var = tk.StringVar(value=option_data.get('target', ''))
        target_combo = ttk.Combobox(row_frame, textvariable=target_var, state='readonly', width=10,
                                    values=[f'Button{i}' for i in range(1, 11)])
        target_combo.grid(row=0, column=6)
        if not target_var.get() and target_combo['values']:
            target_var.set(target_combo['values'][0])
        target_var.trace_add('write', self.rebuild_preview_options)
        
        # Add trace to flag_var *after* target_var is set
        flag_var.trace_add('write', lambda *a, tv=target_var: self.update_preview_command_string(tv.get()))

        self.option_rows.append({
            'frame': row_frame,
            'vars': {'name': name_var, 'flag': flag_var, 'target': target_var}
        })
        self.rebuild_preview_options()
#
# Deletes a specific option row from the UI and internal list.
#
    def delete_option(self, row_frame):
        idx_to_del = -1
        for i, row in enumerate(self.option_rows):
            if row['frame'] == row_frame:
                idx_to_del = i
                break
        
        if idx_to_del != -1:
            self.option_rows[idx_to_del]['frame'].destroy()
            self.option_rows.pop(idx_to_del)
            self.rebuild_preview_options()
#
# Creates the area for a live preview of the toolchain options.
#
    def create_preview_area(self, parent):
        container = ttk.LabelFrame(parent, text="Live Preview", padding=10)
        container.grid(row=1, column=0, sticky='nsew', pady=(0, 10))
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        canvas = tk.Canvas(container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.preview_options_frame = ttk.Frame(canvas)

        self.preview_options_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.preview_options_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
#
# Rebuilds the preview of toolchain options based on the current configuration.
#
    def rebuild_preview_options(self, *args):
        for widget in self.preview_options_frame.winfo_children():
            widget.destroy()
        self.preview_option_vars.clear()
        self.preview_command_labels.clear()

        options_by_target = defaultdict(list)
        for row in self.option_rows:
            target = row['vars']['target'].get()
            name = row['vars']['name'].get()
            if target and name:
                options_by_target[target].append(name)

        if not options_by_target:
             ttk.Label(self.preview_options_frame, text="No options defined. Add an option above to see a preview.").pack(pady=10)
             return

        for target_button in sorted(options_by_target.keys()):
            target_frame = ttk.LabelFrame(self.preview_options_frame, text=f"{target_button} Preview", padding=5)
            target_frame.pack(fill='x', expand=True, pady=(0, 10), padx=5)
            target_frame.columnconfigure(0, weight=1)

            for option_name in options_by_target[target_button]:
                var = tk.BooleanVar()
                key = f"{self.toolchain_name}_{option_name.replace(' ', '_')}"
                saved_state = self.app.config.get('ToolchainStates', {}).get(key, 'False').lower() == 'true'
                var.set(saved_state)
                cb = ttk.Checkbutton(target_frame, text=option_name, variable=var)
                cb.pack(anchor='w')
                var.trace_add('write', lambda *a, tb=target_button: self.update_preview_command_string(tb))
                self.preview_option_vars[option_name] = var
            
            preview_label = ttk.Label(target_frame, text="", relief='sunken', padding=2, wraplength=700, justify='left')
            preview_label.pack(fill='x', expand=True, pady=(5,0))
            self.preview_command_labels[target_button] = preview_label
            self.update_preview_command_string(target_button)
#
# Updates the preview of the command string for a specific target button,
# incorporating any selected option flags.
#
    def update_preview_command_string(self, target_button):
        if not target_button or target_button not in self.preview_command_labels:
            return

        base_command = ''
        try:
            if self.toolchain_editor_window:
                base_command = self.toolchain_editor_window.vars.get(f'{target_button}_command').get()
            else:
                # Fallback to saved config if parent isn't the editor
                toolchain_data = self.app.config.get('Toolchains', {}).get(self.toolchain_name, {})
                buttons_data = ast.literal_eval(toolchain_data.get('custom_buttons', '{}'))
                base_command = buttons_data.get(target_button, {}).get('command', '')
        except (ValueError, SyntaxError, AttributeError):
            base_command = ''
        
        resolved_cmd = self.app.resolve_command_placeholders(
            action_key=None,
            command_override=base_command,
            replacements_override={
                'f': '/path/to/project/source.ext', 's': '/path/to/project/source', 'o': '/path/to/project/source'
            },
            resolve_tool_paths=True,
            target_button=None, # We add flags manually
            toolchain_context=self.toolchain_name
        )
        
        source_stem = "/path/to/project/source"
        source_path_full = source_stem + ".ext"
        
        for row in self.option_rows:
            if row['vars']['target'].get() == target_button:
                option_name = row['vars']['name'].get()
                var = self.preview_option_vars.get(option_name)
                if var and var.get():
                    flag_template = row['vars']['flag'].get()
                    flag = flag_template.replace('%s', source_stem).replace('%o', source_stem).replace('%f', source_path_full)
                    resolved_cmd += f" {flag}"
        
        self.preview_command_labels[target_button].config(text=resolved_cmd)
#
# Creates the bottom buttons for the toolchain options editor.
#
    def create_bottom_buttons(self, parent):
        frame = ttk.Frame(parent)
        frame.grid(row=2, column=0, sticky='ew', pady=(10,0))
        ttk.Button(frame, text="Create New Option", command=self.create_option_row).pack(side='left')
        ttk.Button(frame, text="Save & Close", command=self.save_and_close, style="Accent.TButton").pack(side='right')
#
# Saves the current toolchain options configuration and closes the window.
#
    def save_and_close(self):
        new_options_list = []
        for row in self.option_rows:
            name = row['vars']['name'].get().strip()
            flag = row['vars']['flag'].get().strip()
            target = row['vars']['target'].get()
            if name and flag and target:
                new_options_list.append({'name': name, 'flag': flag, 'target': target})

        self.app.config['Toolchains'][self.toolchain_name]['toolchain_options'] = str(new_options_list)
        self.app.config['Geometry']['toolchain_options_editor'] = self.geometry()
        
        self.app.save_config()
        self.app.on_toolchain_selected() # Refresh the main window's options
        self.destroy()

class DevCommanderApp:
    """The main application class."""
#
# Initializes the main application, setting up the UI, loading configuration,
# and preparing for user interaction.
#
    def __init__(self, root):
        self.root = root
        self.root.title("Developer Command Cycle v2.19")
        self.config = {}
        self.process = None
        self.output_queue = queue.Queue()
        self.command_running = False
        self.master_fd = None
        self.source_file = tk.StringVar()
        self.toolchain_type = tk.StringVar()
        self.always_on_top_var = tk.BooleanVar()
        self.initial_on_top_state = False
        self.toolchain_option_vars = {}
        self.action_buttons = {}
        self.needs_ui_rebuild = False

        self.load_config()
        
        saved_geom = self.config.get('Geometry', {}).get('main_window')
        if not saved_geom or saved_geom == '':
            saved_geom = self.config.get('DefaultGeometry', {}).get('main_window', '800x600')
        self.root.geometry(saved_geom)
        
        self.apply_theme()
        self.configure_styles()
        self.setup_ui()
        self.populate_ui_from_config()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.after(100, self.process_output_queue)
#
# Returns a deep copy of the default configuration dictionary.
#
    def get_default_config(self):
        return copy.deepcopy(DEFAULT_CONFIG)
#
# Loads the application's configuration from an INI file, merging it with the default settings.
#
    def load_config(self):
        self.config = self.get_default_config()
        parser = configparser.ConfigParser(interpolation=None, allow_no_value=True)
        parser.optionxform = str # Make config parser case-sensitive
        if not os.path.exists(CONFIG_FILE_NAME):
            self.save_config() # This will save the now-explicit DEFAULT_CONFIG
        parser.read(CONFIG_FILE_NAME)
        for section in parser.sections():
            if section.startswith('Toolchain:'):
                _, name = section.split(':', 1)
                if name not in self.config['Toolchains']: self.config['Toolchains'][name] = {}
                if 'custom_buttons' not in self.config['Toolchains'][name]:
                    self.config['Toolchains'][name]['custom_buttons'] = str({f'Button{i}': {'name': '', 'command': '', 'color': '#F0F0F0'} for i in range(1, 11)})

                for key, value in parser.items(section): self.config['Toolchains'][name][key] = value
            else:
                self.config.setdefault(section, {}).update(dict(parser.items(section)))
#
# Saves the current application configuration to an INI file.
#
    def save_config(self):
        parser = configparser.ConfigParser(interpolation=None)
        parser.optionxform = str # Make config parser case-sensitive
        config_to_save = copy.deepcopy(self.config)
        for section, items in config_to_save.items():
            if section != 'Toolchains' and isinstance(items, dict):
                parser[section] = {k: str(v) for k, v in items.items()}

        for name, data in config_to_save.get('Toolchains', {}).items():
            section_name = f'Toolchain:{name}'
            parser[section_name] = {k: str(v) for k, v in data.items()}
        with open(CONFIG_FILE_NAME, 'w') as f: parser.write(f)
#
# Applies a light or dark theme to the application based on the current configuration.
#
    def apply_theme(self):
        is_dark = self.config.get('Options', {}).get('dark_mode', 'False').lower() == 'true'
        style = ttk.Style()
        try:
            theme = 'clam' if is_dark else 'default'
            if sys.platform == "win32": theme = 'vista'
            if is_dark:
                self.root.configure(bg='#2E2E2E')
                style.theme_use('clam')
                style.configure('.', background='#2E2E2E', foreground='white', fieldbackground='#3C3C3C', lightcolor='#555555', darkcolor='#1E1E1E')
                style.map('TCombobox', fieldbackground=[('readonly','#3C3C3C')])
                style.map('.', background=[('active', '#4a6984')], foreground=[('active', 'white')])
            else:
                self.root.configure(bg='SystemButtonFace')
                style.theme_use(theme)
        except tk.TclError: pass
#
# Configures custom ttk styles for various widgets used in the application.
#
    def configure_styles(self):
        style = ttk.Style()
        style.configure("TButton", padding=5, font=('Helvetica', 10))
        style.configure("Danger.TButton", background="#dc3545", foreground="white", font=('Helvetica', 10, 'bold'))
        style.map("Danger.TButton", background=[('active', '#c82333')])
        style.configure("Accent.TButton", foreground="white", font=('Helvetica', 10, 'bold'))
#
# Sets up the main user interface layout and widgets for the application.
#
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill='both', expand=True)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        top_container = ttk.Frame(main_frame)
        top_container.grid(row=0, column=0, sticky='ew')
        top_container.columnconfigure(0, weight=1)
        self.create_project_widgets(top_container).grid(row=0, column=0, sticky='ewns')
        self.create_top_right_widgets(top_container).grid(row=0, column=1, sticky='ne', padx=10)
        self.dynamic_options_frame = ttk.LabelFrame(main_frame, text="Toolchain Options", padding=10)
        self.dynamic_options_frame.grid(row=1, column=0, sticky='ew', pady=5)
        self.actions_frame = ttk.LabelFrame(main_frame, text="Actions", padding=10)
        self.actions_frame.grid(row=2, column=0, sticky='ew', pady=5)
        self.create_status_widgets(main_frame).grid(row=3, column=0, sticky='nsew', pady=5)
#
# Populates the user interface with values loaded from the application configuration.
#
    def populate_ui_from_config(self):
        paths = self.config.get('Paths', {})
        self.source_file.set(paths.get('last_source', ''))
        self.source_file.trace_add('write', self._save_paths_to_config)
        toolchains = sorted(list(self.config.get('Toolchains', {}).keys()))
        self.toolchain_combo['values'] = toolchains
        if toolchains:
             last_toolchain = paths.get('last_toolchain', toolchains[0])
             self.toolchain_type.set(last_toolchain if last_toolchain in toolchains else toolchains[0])
        self.toolchain_type.trace_add('write', self.on_toolchain_selected)
        self.on_toolchain_selected()
        self.apply_misc_options()
        self.update_autotyper_indicator()
#
# Saves the current source file path to the configuration.
#
    def _save_paths_to_config(self, *args):
        self.config['Paths']['last_source'] = self.source_file.get()
#
# Applies miscellaneous options from the configuration to the application's behavior.
#
    def apply_misc_options(self):
        opts = self.config.get('Options', {})
        on_top = opts.get('always_on_top', 'False').lower() == 'true'
        self.always_on_top_var.set(on_top)
        self.root.wm_attributes("-topmost", on_top)
        self.initial_on_top_state = on_top
        if hasattr(self, 'restart_label'):
            self.always_on_top_var.trace_add('write', self._check_topmost_change)
#
# Checks if the 'always on top' setting has changed and updates the UI to indicate if a restart is required.
#
    def _check_topmost_change(self, *args):
        changed = self.always_on_top_var.get() != self.initial_on_top_state
        self.restart_label.config(text="Restart Required" if changed else "")
        self.config['Options']['always_on_top'] = str(self.always_on_top_var.get())
#
# Creates and returns a frame containing widgets for project-related settings like source file and toolchain selection.
#
    def create_project_widgets(self, parent):
        frame = ttk.LabelFrame(parent, text="Project", padding=10)
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text="Source File:").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.source_file).grid(row=0, column=1, sticky='ew')
        ttk.Button(frame, text="...", command=self.browse_source_file, width=3).grid(row=0, column=2, padx=5)
        ttk.Label(frame, text="Toolchain:").grid(row=2, column=0, sticky='w', padx=5, pady=2)
        self.toolchain_combo = ttk.Combobox(frame, textvariable=self.toolchain_type, state='readonly', exportselection=False)
        self.toolchain_combo.grid(row=2, column=1, sticky='w')
        return frame
#
# Creates and returns a frame containing widgets for the top-right corner of the main window,
# including 'Always on Top' checkbox, 'About', and 'Exit' buttons.
#
    def create_top_right_widgets(self, parent):
        frame = ttk.Frame(parent, padding=(0, 5))
        frame.columnconfigure(0, weight=1)
        cb = ttk.Checkbutton(frame, text="Always on Top", variable=self.always_on_top_var)
        cb.grid(row=0, column=0, sticky='w')
        self.restart_label = ttk.Label(frame, text="", foreground='#ff4444', font=('Helvetica', 8, 'italic'))
        self.restart_label.grid(row=1, column=0, sticky='w', padx=(20,0))
        ttk.Button(frame, text="About", command=self.open_about_window).grid(row=2, column=0, sticky='ew', pady=(10,2))
        ttk.Button(frame, text="Exit", command=self.on_closing).grid(row=3, column=0, sticky='ew', pady=2)
        return frame
#
# Rebuilds the action buttons in the main window based on the currently selected toolchain's configuration.
#
    def rebuild_action_buttons(self):
        frame = self.actions_frame
        for widget in frame.winfo_children():
            widget.destroy()
        self.action_buttons.clear()
        
        for i in range(4): frame.columnconfigure(i, weight=1)
        
        ttk.Button(frame, text="Settings", command=lambda: self.log_and_run("Settings", self.open_settings)).grid(row=0, column=0, padx=2, pady=2, sticky='ew')
        ttk.Button(frame, text="Open Folder", command=lambda: self.log_and_run("Open Folder", self.open_project_folder)).grid(row=0, column=1, padx=2, pady=2, sticky='ew')
        ttk.Button(frame, text="Clean", command=lambda: self.log_and_run("Clean", self.clean_project), style="Danger.TButton").grid(row=0, column=2, padx=2, pady=2, sticky='ew')

        toolchain_name = self.toolchain_type.get()
        if not toolchain_name: return
        toolchain_data = self.config.get('Toolchains', {}).get(toolchain_name, {})
        try: buttons_data = ast.literal_eval(toolchain_data.get('custom_buttons', '{}'))
        except (ValueError, SyntaxError): buttons_data = {}

        style = ttk.Style()
        grid_map = {
            'Button1': (0, 3, 1), 'Button2': (1, 0, 1), 'Button3': (1, 1, 1),
            'Button4': (1, 2, 1), 'Button5': (1, 3, 1), 'Button6': (2, 0, 2),
            'Button7': (2, 2, 2), 'Button8': (3, 0, 2), 'Button9': (3, 2, 2),
            'Button10':(4, 0, 4)
        }
        
        for i in range(1, 11):
            key = f"Button{i}"
            data = buttons_data.get(key, {})
            name = data.get('name')
            if name:
                color = data.get('color', '#F0F0F0')
                style_name = f"{key}.TButton"
                try:
                    r, g, b = self.root.winfo_rgb(color)
                    brightness = (r*299 + g*587 + b*114) / 65535 
                    text_color = 'black' if brightness > 0.5 else 'white'
                    style.configure(style_name, background=color, foreground=text_color, padding=5, font=('Helvetica', 10))
                    style.map(style_name, background=[('active', color)], foreground=[('active', text_color)])
                except tk.TclError: 
                    style.configure(style_name, background=color)

                row, col, span = grid_map.get(key)
                btn = ttk.Button(frame, text=name, style=style_name, command=lambda k=key: self.execute_custom_button(k))
                btn.grid(row=row, column=col, columnspan=span, sticky='ew', padx=2, pady=2)
                self.action_buttons[key] = btn
#
# Creates and returns a frame containing the status window for displaying command output and user input.
#
    def create_status_widgets(self, parent):
        frame = ttk.LabelFrame(parent, text="Status Window", padding=10)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        bg_color, fg_color = 'black', 'white'
        self.output_text = tk.Text(frame, wrap='word', state='disabled', background=bg_color, foreground=fg_color, insertbackground=fg_color)
        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=self.output_text.yview)
        self.output_text.config(yscrollcommand=scrollbar.set)
        self.output_text.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')
        self.ansi_handler = AnsiColorHandler(self.output_text)
        try:
            bold_font = tkfont.Font(self.output_text, self.output_text.cget("font"))
            italic_font = tkfont.Font(self.output_text, self.output_text.cget("font"))
            bold_font.configure(weight="bold")
            italic_font.configure(slant="italic")
            self.output_text.tag_configure("success", foreground="#28a745", font=bold_font)
            self.output_text.tag_configure("error", foreground="#dc3545", font=bold_font)
            self.output_text.tag_configure("info", foreground="#17a2b8")
            self.output_text.tag_configure("user_input", foreground="#007bff", font=italic_font)
        except tk.TclError: pass
        input_frame = ttk.Frame(frame)
        input_frame.grid(row=1, column=0, columnspan=2, sticky='ew', pady=(5,0))
        input_frame.columnconfigure(1, weight=1)
        self.autotyper_label = ttk.Label(input_frame, text="", foreground='#ff4444', font=('Helvetica', 10, 'bold'))
        self.autotyper_label.grid(row=0, column=0, padx=(0,5))
        self.input_entry = ttk.Entry(input_frame)
        self.input_entry.grid(row=0, column=1, sticky='ew')
        self.input_entry.bind("<Return>", self.send_input_to_process)
        self.input_entry.bind("<KP_Enter>", self.send_input_to_process)
        ttk.Button(input_frame, text="Enter", command=self.send_input_to_process).grid(row=0, column=2, padx=5)
        self.break_button = ttk.Button(input_frame, text="Break", command=self.send_break_signal, state='disabled')
        self.break_button.grid(row=0, column=3, padx=5)
        return frame
#
# Handles the event of selecting a new toolchain, updating the UI accordingly.
#
    def on_toolchain_selected(self, *args):
        for widget in self.dynamic_options_frame.winfo_children():
            widget.destroy()
        self.toolchain_option_vars.clear()
        
        toolchain_name = self.toolchain_type.get()
        if not toolchain_name: 
            self.rebuild_action_buttons()
            return
        self.config['Paths']['last_toolchain'] = toolchain_name
        
        toolchain_data = self.config.get('Toolchains', {}).get(toolchain_name, {})
        try:
            toolchain_options = ast.literal_eval(toolchain_data.get('toolchain_options', '[]'))
        except (ValueError, SyntaxError):
            toolchain_options = []

        try:
            buttons_data = ast.literal_eval(toolchain_data.get('custom_buttons', '{}'))
        except (ValueError, SyntaxError):
            buttons_data = {}

        container = ttk.Frame(self.dynamic_options_frame)
        container.pack(fill='x', expand=True)
        cb_frame = ttk.Frame(container)
        cb_frame.pack(side='left', fill='x', expand=True)

        # Keep track of which targets have previews
        preview_targets = set()

        for option in toolchain_options:
            name = option.get('name', 'Unnamed Option')
            flag = option.get('flag', '')
            target = option.get('target', 'None')

            key = f"{toolchain_name}_{name.replace(' ', '_')}"
            var = tk.BooleanVar(name=f"toolchain_var_{key}")
            saved_state = self.config.get('ToolchainStates', {}).get(key, 'False').lower() == 'true'
            var.set(saved_state)
            cb = ttk.Checkbutton(cb_frame, text=name, variable=var)
            cb.pack(anchor='w')
            self.toolchain_option_vars[name] = (var, target, flag)
            var.trace_add('write', lambda *a, t=target: self._update_toolchain_state_and_preview(t))
            preview_targets.add(target)

        self.preview_labels = {}
        for target in sorted(list(preview_targets)):
            if target == 'None': continue
            
            button_name = buttons_data.get(target, {}).get('name', target)
            preview_text = f"{button_name} Preview:" if button_name else f"{target} Preview:"

            preview_container = ttk.Frame(cb_frame)
            preview_container.pack(fill='x', pady=(5,0))
            ttk.Label(preview_container, text=preview_text, foreground="gray").pack(side='left', anchor='nw', padx=(0,5))
            
            preview_label = ttk.Label(preview_container, text="", relief='sunken', padding=2, wraplength=400, justify='left')
            preview_label.pack(fill='x', expand=True)
            self.preview_labels[target] = preview_label
            self._update_toolchain_state_and_preview(target)
        
        self.rebuild_action_buttons()
#
# Updates the saved state of toolchain options and refreshes the command preview for the specified target button.
#
    def _update_toolchain_state_and_preview(self, target_button=None):
        toolchain_name = self.toolchain_type.get()
        if not toolchain_name: return

        if 'ToolchainStates' not in self.config: self.config['ToolchainStates'] = {}
        for name, (var, _, _) in self.toolchain_option_vars.items():
            key = f"{toolchain_name}_{name.replace(' ', '_')}"
            self.config['ToolchainStates'][key] = str(var.get())

        if target_button and target_button in self.preview_labels:
            toolchain_data = self.config.get('Toolchains', {}).get(toolchain_name, {})
            try:
                buttons_data = ast.literal_eval(toolchain_data.get('custom_buttons', '{}'))
                base_command = buttons_data.get(target_button, {}).get('command', '')
            except (ValueError, SyntaxError):
                base_command = ''

            preview_cmd = self.resolve_command_placeholders(
                action_key=None,
                command_override=base_command,
                replacements_override={'t': toolchain_data.get('path', toolchain_name)}, 
                resolve_tool_paths=False,
                target_button=target_button # Pass the target to include flags
            )
            
            self.preview_labels[target_button].config(text=preview_cmd)
#
# Handles the application closing event, saving configuration before exiting.
#
    def on_closing(self):
        self._save_paths_to_config()
        self.config['Geometry']['main_window'] = self.root.geometry()
        self.save_config()
        if self.process and self.process.poll() is None: self.process.terminate()
        self.root.destroy()
#
# Opens a file dialog to allow the user to browse for a source file.
#
    def browse_source_file(self):
        if path := filedialog.askopenfilename():
            self.source_file.set(path)
#
# Informs the user that the output path is now determined automatically.
#
    def browse_output_file(self):
        messagebox.showinfo("Information", "The output path is now determined automatically based on the Source File.", parent=self.root)
#
# Logs output text to the status window, optionally applying a style tag.
#
    def log_output(self, text, raw=False, tag=None):
        def _log():
            self.output_text.config(state='normal')
            if raw: self.ansi_handler.write(text)
            else: self.output_text.insert(tk.END, text + '\n', (tag,) if tag else ())
            self.output_text.see(tk.END)
            self.output_text.config(state='disabled')
        if self.root.winfo_exists(): self.root.after(0, _log)
#
# Processes the output queue from background processes and displays it in the status window.
#
    def process_output_queue(self):
        try:
            while True: self.log_output(self.output_queue.get_nowait(), raw=True)
        except queue.Empty: pass
        finally: self.root.after(100, self.process_output_queue)
#
# Updates the UI indicator for the auto-typer feature based on its current enabled/disabled state.
#
    def update_autotyper_indicator(self):
        is_enabled = self.config['Options'].get('header_auto_send_command', 'False').lower() == 'true'
        self.autotyper_label.config(text="A-R" if is_enabled else "")
#
# Opens the settings window.
#
    def open_settings(self):
        self._save_paths_to_config()
        SettingsWindow(self.root, self)
#
# Opens the "About" window containing the user manual.
#
    def open_about_window(self):
        about_win = tk.Toplevel(self.root)
        about_win.title("Developer Command Cycle v2.19 - User Manual")
        about_win.geometry("800x700")
        about_win.transient(self.root)
        about_win.grab_set()

        text_area = tk.Text(about_win, wrap='word', relief='flat', font=('Helvetica', 10), padx=10, pady=10)
        scrollbar = ttk.Scrollbar(about_win, orient='vertical', command=text_area.yview)
        text_area.config(yscrollcommand=scrollbar.set)
        
        text_area.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # --- Define text styles ---
        h1_font = tkfont.Font(font=text_area['font'])
        h1_font.configure(size=16, weight='bold', underline=True)
        text_area.tag_configure("h1", font=h1_font, spacing3=15, justify='center')

        h2_font = tkfont.Font(font=text_area['font'])
        h2_font.configure(size=12, weight='bold')
        text_area.tag_configure("h2", font=h2_font, spacing1=10, spacing3=5)

        bold_font = tkfont.Font(font=text_area['font'])
        bold_font.configure(weight='bold')
        text_area.tag_configure("bold", font=bold_font)
        
        italic_font = tkfont.Font(font=text_area['font'])
        italic_font.configure(slant='italic')
        text_area.tag_configure("italic", font=italic_font)

        mono_font = ("Courier", 9)
        text_area.tag_configure("mono", font=mono_font, background="#f0f0f0", lmargin1=20, lmargin2=20, rmargin=20, spacing1=5, spacing3=5, wrap='none')

        # --- Manual Content ---
        manual_content = [
            ("Developer Command Cycle v2.19 - User Manual\n", "h1"),
            ("Author: RetroGameGirl (v2.19)\n\n", ""),
            ("1. INTRODUCTION\n", "h2"),
            ("Welcome to the Developer Command Cycle.\n\nFirst: Use at your own risk. See the license information at the bottom of this manual. There may be mistakes in this code; I know there are absolutely dead functions as I spaghetti strung it together, I did learn to code using 8-bit basic on a trash-80.\n\nI prefer coding in a standard text editor and found that a lot of the modern IDE plugins for Atari development were more complex than I needed. This script started as my personal build process and has evolved into something worth sharing.\n\nIt's been primarily tested on *nix-based systems, but it should be portable enough to work on other platforms.\n\n", ""),
            ("This application is designed to be run from the command line within your project's directory. For easier access, you can add the script's location to your system's PATH. To begin, simply select your main source file and the appropriate toolchain. If your toolchain is missing, you can configure it easily. The recommended way to add a new toolchain is through the 'Settings' menu, which will safely update the configuration file. As an alternative for advanced users, new toolchains can be defined directly within the DEFAULT_CONFIG section of the script.\n\n", ""),
            
            
            ("Requirements:\n", "bold"),
            ("Python Environment:\n", "bold"),
            (" - Python 3.x: The script uses modern syntax like f-strings, so a recent version of Python 3 is required.\n", ""),
            (" - Tkinter: This is the library used for the GUI. It's included with most Python installs on Windows and macOS, but on Linux, you may need to install it separately (e.g., sudo apt-get install python3-tk).\n\n", ""),
            ("Operating System:\n", "bold"),
            (" - The script is designed to be cross-platform (Windows, macOS, Linux). However, it performs best on Linux or macOS because it uses the pty module for cleaner interactive terminal control, which isn't available on Windows. It will still function on Windows, but the console behavior might differ slightly.\n\n", ""),
            ("External Atari 7800 Tools:\n", "bold"),
            (" - 7800asm: The assembler for your .s or .asm source files.\n", ""),
            (" - cc65 toolchain: Specifically, the cl65 compiler for C projects.\n", ""),
            (" - 7800header: Utility to add the required header to your ROM.\n", ""),
            (" - 7800sign: Utility to sign your ROM, typically used with cc65.\n", ""),
            (" - An Atari 7800 Emulator: The default is a7800, but this can be configured to use MAME or another emulator.\n", ""),
            (" - A Text Editor: Your preferred editor for writing code (defaults to xed).\n\n", ""),
            ("What It Does:\n", "bold"),
            ("This tool is a graphical front-end for the common command-line utilities such as those used in Atari 7800 development. The goal is to simplify the workflow, allowing you to build ROMs and launch them in an emulator with a few clicks instead of typing out commands for each step of the process.\n\n", ""),
            ("The Main Window\n", "h2"),
            ("The main window is your central hub for managing and building your project.\n\n", ""),
            ("Project Frame:\n", "bold"),
            (" • Source File: This is the path to your primary source file (e.g., your .s, .asm, or .c file). This path is used by command placeholders like %f (full path) and %s (path without extension).\n", ""),
            (" • Toolchain: Select the active build configuration. Each toolchain defines its own set of custom buttons and command-line options.\n\n", ""),
            ("Quirk:\n", "bold"),
            (" • If your assembly file does not have a .s extension, you will need to manually edit the custom_buttons and build_steps in the Toolchain Editor for your chosen toolchain to ensure the correct output file extensions are used. For example, if you use .asm, you will need to update the file extensions in the build command from .s.a78 or .s.bin to .asm.a78 or .asm.bin.\n\n", ""),
            
            ("Toolchain Options Frame:\n", "bold"),
            ("This area displays checkboxes for optional command-line flags specific to the selected toolchain. Enabling an option adds its corresponding flag to the command of its target button. A live preview of the final command is shown below the checkboxes for clarity.\n\n", ""),
            
            ("Actions Frame:\n", "bold"),
            ("This contains all the executable actions.\n", ""),
            (" • Settings: Opens the Global Settings window.\n", ""),
            (" • Open Folder: Opens the directory containing your source file in the system's file explorer.\n", ""),
            (" • Clean: Deletes temporary build files (like .bin, .map, .o) from your project directory based on the extensions configured in Settings.\n", ""),
            (" • Custom Buttons (Button 1-10): These are fully configurable. They can run a single command, an external program, or a sequence of other button actions.\n\n", ""),
            
            ("Status Window:\n", "bold"),
            ("This is where all output from your build tools is displayed in real-time. It supports ANSI color codes for better readability. An input box at the bottom allows you to send commands to interactive tools (like 7800header itself), and the 'Break' button can terminate a running process.\n\n", ""),
            
            ("The Settings Window\n", "h2"),
            ("This window allows you to configure global settings and access the toolchain editors.\n\n", ""),
            ("Paths to Tools:\n", "bold"),
            ("Define the full paths to your command-line executables (e.g., your editor, emulator, header tool). These are essential for the command placeholders (%e, %m, %h, etc.) to work correctly.\n\n", ""),
            ("Quirk:\n", "bold"),
            (" • If you do not specify a full path to a tool (e.g., you just type dasm instead of /path/to/dasm), the program will rely on your system's PATH environment variable to find the executable. If the tool is not in your PATH, the command will fail with a \"File not found\" error.\n\n", ""),
            ("Edit Toolchains...:\n", "bold"),
            ("This is the gateway to the application's core feature. It opens the Toolchain Editor window.\n\n", ""),
            ("Clean File Extensions:\n", "bold"),
            ("Manage the list of file extensions that the 'Clean' button will remove. You can also enable or disable cleaning for each extension type using the checkboxes.\n\n", ""),
            ("Header Auto-Typer Settings:\n", "bold"),
            ("This is a special feature for the interactive '7800header' tool. When enabled, it automatically types a predefined sequence of commands into the tool's prompt. The Command Wizard helps you build this command sequence visually.\n\n", ""),
            
            ("The Toolchain Editor\n", "h2"),
            ("Here, you can create and customize different build environments (toolchains).\n\n", ""),
            ("Button Configuration:\n", "bold"),
            ("For each of the 10 custom buttons, you can set:\n", ""),
            (" • Name: The label that appears on the button.\n", ""),
            (" • Command: The command to execute. This can be a single command line, a sequence of other buttons (e.g., 'Button3,Button8,Button4'), or an external command prefixed with 'EXTERNAL:' (e.g., 'EXTERNAL:%term').\n", ""),
            (" • Color: The button's background color.\n\n", ""),
            ("Toolchain Options Setup...:\n", "bold"),
            ("Opens a dedicated window to create the optional checkboxes that appear on the main screen for this toolchain.\n\n", ""),
            
            ("The Toolchain Options Setup Window\n", "h2"),
            ("This window lets you define optional, user-toggleable command-line flags.\n\n", ""),
            ("Configurable Options:\n", "bold"),
            ("For each option you create, you define:\n", ""),
            (" • Name: The descriptive text that will appear next to the checkbox (e.g., 'Generate List File').\n", ""),
            (" • Flag: The actual command-line flag to be added when the box is checked (e.g., '-l%s.list'). Placeholders can be used here.\n", ""),
            (" • Target: The button (e.g., 'Button3') to which this flag should be added.\n\n", ""),
            ("Live Preview:\n", "bold"),
            ("This section provides a complete, interactive preview of how your options will appear and function on the main window. You can toggle the checkboxes to see the final command string update in real-time for each target button.\n\n", ""),
            
            ("Walkthrough: Setting Up a New Toolchain\n", "h2"),
            ("Let's go through the steps to get a new toolchain configured from scratch. This is where the true power of the program lies.\n\n", ""),
            ("Step 1: Create Your New Toolchain\n", "bold"),
            ("1. From the main window, click the **Settings** button.\n", ""),
            ("2. Inside the **Global Settings** window, click on **Edit Toolchains...**.\n", ""),
            ("3. A new window, the **Toolchain Editor**, will appear. Click the **Add New** button on the right side. A small pop-up dialog will ask you for a name for your new toolchain.\n", ""),
            ("4. Type in a descriptive name, like `MyDASM`, and press `OK`. The new toolchain is now active in the editor.\n\n", ""),
            ("Step 2: Configure the Main Executable\n", "bold"),
            ("1. In the **Toolchain Editor** window, under the **Toolchain Management** section, find the **Executable Path** field. This is where you tell the program where your main build tool is located.\n", ""),
            ("2. If your tool is in your system's `PATH`, you can just type its name, like `dasm`. If not, type the full path to the executable, for example, `C:\\dasm\\dasm.exe`.\n\n", ""),
            ("Step 3: Define Your Build Buttons\n", "bold"),
            ("1. Scroll down to the **Button Configuration** section. This is where you set up what each button does.\n", ""),
            ("2. For **Button 3**, set the **Name** to `Build`. Then, for the **Command**, enter the command you use to build your code. For DASM, this would be: `%t %f -o %o.bin`. This command says: \"Run the tool (`%t`) on the source file (`%f`) and output a `.bin` file named after the source file (`-o %o.bin`).\"\n", ""),
            ("3. For **Button 4**, set the **Name** to `Run`. The command should run the emulator on your final ROM file. For the a7800 emulator, a good command is `%m a7800 -cart %o.a78`.\n", ""),
            ("4. For **Button 8**, set the **Name** to `Add Header`. The command for this would be `%h %o.bin`. The `%h` placeholder runs the `7800header` tool, and the command tells it to process your newly created `.bin` file.\n", ""),
            ("5. Now, let's create a composite button. For **Button 6**, set the **Name** to `Build & Run`. The **Command** for this one will be a comma-separated list of other button commands: `Button3,Button8,Button4`. When you click this button, it will run your build command, then add the header, and finally run the emulator, all in one go. Handy, isn't it?\n\n", ""),
            ("Step 4: Configure Options for Your Buttons\n", "bold"),
            ("1. Back at the bottom of the **Toolchain Editor** window, click the **Toolchain Options Setup...** button. This opens a new window for creating optional flags.\n", ""),
            ("2. Click the **Create New Option** button. You'll see fields for a new option.\n", ""),
            ("3. Let's add an option to generate a list file. For this option, set the **Name** to `Generate List File`, the **Flag** to `-l%s.list`, and the **Target** to `Button3`. This means when you check the box on the main screen, the `-l%s.list` flag will automatically be added to your `Build` command (Button3).\n", ""),
            ("4. You can add more options for your other buttons as needed. For example, a symbol file might be `-s%s.sym` and target `Button3`.\n\n", ""),
            ("Step 5: Save and Test\n", "bold"),
            ("1. When you're done, click **Save & Close** on the Options window, and then **Save & Close** on the Toolchain Editor window.\n", ""),
            ("2. Back on the main screen, make sure your new toolchain is selected. When you check the box for `Generate List File`, you'll see the command preview update in real time. Click your `Build & Run` button and watch the magic happen!\n\n", ""),
            
            ("Command Placeholders\n", "h2"),
            ("Placeholders are special codes that are replaced with actual paths or values when a command is executed. This makes your toolchains portable and easy to manage.\n\n", ""),
            ("%f: Full path to the source file.\n", "mono"),
            ("%s: Source file path without the extension.\n", "mono"),
            ("%o: Output file path (same as %s).\n", "mono"),
            ("%e: Path to the configured editor.\n", "mono"),
            ("%m: Path to the configured emulator.\n", "mono"),
            ("%h: Path to the 7800header tool.\n", "mono"),
            ("%g: Path to the 7800signer tool.\n", "mono"),
            ("%t: Path to the current toolchain's main executable.\n", "mono"),
            ("%term: Path to the configured terminal.\n", "mono"),
            ("EXTERNAL:<command> this will launch <commanand> as a new process outside of the status window\n", "mono"),
            ("      Example: 'EXTERNAL:xed %f' (Linux) or 'EXTERNAL:notepad++ %f' (Windows)\n        launches a text editor with the current file, assuming the program is in your system's PATH.\n\n", "mono"),


            ("License Information\n", "h2"),
            ("This software is licensed under the GNU General Public License version 3.\nSee [https://www.gnu.org/licenses/gpl-3.0.html](https://www.gnu.org/licenses/gpl-3.0.html) for details.\n", "")
                    

        ]


        for text, tag in manual_content:
            text_area.insert(tk.END, text, (tag,) if tag else ())
            
        text_area.config(state='disabled')

#
# Resolves command placeholders in a given command string, replacing them with their actual values.
#
    def resolve_command_placeholders(self, action_key, replacements_override=None, resolve_tool_paths=True, command_override=None, target_button=None, toolchain_context=None):
        command_template = command_override if command_override is not None else self.config.get('Actions', {}).get(action_key, '')
        
        paths = self.config.get('Paths', {})
        source_path_full = self.source_file.get()
        source_stem = os.path.splitext(source_path_full)[0] if source_path_full else ''
        
        replacements = {}
        if resolve_tool_paths:
            replacements.update({
                'e': shlex.quote(paths.get('editor', '')), 'm': shlex.quote(paths.get('emulator', '')),
                'h': shlex.quote(paths.get('header_tool', '')), 'g': shlex.quote(paths.get('signer_tool', '')),
                'term': shlex.quote(paths.get('terminal', ''))
            })
        
        replacements.update({
            'f': shlex.quote(source_path_full),
            's': shlex.quote(source_stem),
            'o': shlex.quote(source_stem), # Make %o an alias for %s
        })

        current_toolchain_name = toolchain_context if toolchain_context is not None else self.toolchain_type.get()
        if current_toolchain_name:
            toolchain_data = self.config.get('Toolchains', {}).get(current_toolchain_name, {})
            toolchain_path = toolchain_data.get('path', '')
            if resolve_tool_paths and toolchain_path:
                 replacements['t'] = shlex.quote(toolchain_path)
            else:
                 replacements['t'] = toolchain_path or current_toolchain_name
        
        if replacements_override: replacements.update(replacements_override)
        
        resolved_cmd = command_template
        for key, value in replacements.items():
            resolved_cmd = resolved_cmd.replace(f'%{key}', value)

        # Append toolchain-specific flags only if a target button is specified
        if target_button:
            for _, (var, target, flag_template) in self.toolchain_option_vars.items():
                if var.get() and target == target_button:
                    flag = flag_template.replace('%s', source_stem).replace('%o', source_stem).replace('%f', source_path_full)
                    resolved_cmd += f" {flag}"
        
        return resolved_cmd
#
# Logs the name of a button press and then executes the associated action.
#
    def log_and_run(self, button_name, action, *args, **kwargs):
        self.log_output(f"\n--- {button_name} button pressed ---", tag='info')
        action(*args, **kwargs)
#
# Runs a command, handling both internal and external execution based on the command string.
#
    def run_command(self, action_key, on_success=None, command_override=None, is_auto_typer_target=False, target_button=None):
        if self.command_running:
            self.log_output("Error: A command is already running.", tag='error')
            return
        
        final_command_str = self.resolve_command_placeholders(action_key=action_key, command_override=command_override, target_button=target_button)

        if final_command_str.strip().startswith('EXTERNAL:'):
            return self.run_external_command(final_command_str.strip()[len('EXTERNAL:'):].strip(), on_success)
        if not final_command_str.strip():
            self.log_output("Error: Command is empty after resolving placeholders.", tag='error')
            return

        self.log_output(f"$ {final_command_str}", tag='user_input')
        self.execute_internal_command(final_command_str, on_success, is_auto_typer_target=is_auto_typer_target)
#
#
# Executes a non-blocking "fire-and-forget" command, either in a new terminal or directly.
#
    def run_external_command(self, command_to_run, on_success=None):
        final_cmd = command_to_run

        self.log_output(f"$ (External) {final_cmd}", tag='user_input')
        try:
            flags = 0
            if sys.platform == "win32":
                flags = subprocess.DETACHED_PROCESS
            
            # On Windows, use shell=True for flexibility. On others, split the command.
            use_shell = sys.platform == "win32"
            cmd_arg = final_cmd if use_shell else shlex.split(final_cmd)

            subprocess.Popen(cmd_arg, cwd=os.path.dirname(self.source_file.get()) or None, shell=use_shell, creationflags=flags)
        except Exception as e:
            self.log_output(f"Error launching external process: {e}", tag='error')
        
        if on_success:
            self.root.after(10, on_success)
#
# Executes a command internally within the application, capturing and displaying its output.
#
# Executes a command internally within the application, capturing and displaying its output.
#
    def execute_internal_command(self, command_string, on_success, is_auto_typer_target=False):
        working_dir = os.path.dirname(self.source_file.get()) if self.source_file.get() else None

        try:
            self.set_command_running_state(True)
            if sys.platform != "win32":
                try: 
                    cmd_list = shlex.split(command_string)
                except ValueError as e: 
                    self.set_command_running_state(False)
                    return self.log_output(f"Error parsing command: {e}", tag='error')

                self.master_fd, slave_fd = pty.openpty()
                self.process = subprocess.Popen(cmd_list, stdin=slave_fd, stdout=slave_fd, stderr=subprocess.STDOUT, cwd=working_dir)
                os.close(slave_fd)
                reader_fd = self.master_fd
            else:
                # On Windows, pass the raw command string to the shell, don't split it.
                self.process = subprocess.Popen(command_string, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, cwd=working_dir, text=True, bufsize=1, creationflags=subprocess.CREATE_NO_WINDOW, shell=True)
                reader_fd = self.process.stdout.fileno()

            self.reader_thread = threading.Thread(target=self._read_stream_to_queue, args=(reader_fd,), daemon=True)
            self.reader_thread.start()
            self.root.after(100, self.poll_process, on_success)
            
            auto_typer_enabled = self.config['Options'].get('header_auto_send_command', 'False').lower() == 'true'
            if is_auto_typer_target and auto_typer_enabled:
                threading.Thread(target=self._run_automated_header_sequence, daemon=True).start()
        except FileNotFoundError: self.log_output(f"Error: Command not found.", tag='error'); self.set_command_running_state(False)
        except Exception as e: self.log_output(f"An error occurred: {e}", tag='error'); self.set_command_running_state(False)
#
#
# Reads data from a stream and puts it into a queue for processing by the main thread.
#
    def _read_stream_to_queue(self, stream_fd):
        try:
            while self.command_running:
                data = os.read(stream_fd, 1024)
                if not data: break
                self.output_queue.put(data.decode('utf-8', errors='replace'))
        except (OSError, ValueError): pass
        finally:
            if sys.platform != "win32" and self.master_fd is not None:
                try: os.close(self.master_fd)
                except OSError: pass
#
# Polls the running process to check if it has completed, and handles success or error states.
#
    def poll_process(self, on_success_callback):
        if not self.command_running or not self.process: return
        if self.process.poll() is None:
            return self.root.after(100, self.poll_process, on_success_callback)
        
        if self.process.returncode == 0:
            self.log_output(f"\n--- Process finished successfully (Code: {self.process.returncode}) ---\n", tag='success')
            if on_success_callback: self.root.after(10, on_success_callback)
        else:
            self.log_output(f"\n--- Process finished with error (Code: {self.process.returncode}) ---\n", tag='error')
        
        self.process = None
        self.master_fd = None
        self.set_command_running_state(False)
#
# Sets the state of the application to indicate whether a command is currently running.
#
    def set_command_running_state(self, is_running):
        self.command_running = is_running
        if self.root.winfo_exists():
            self.break_button.config(state='normal' if is_running else 'disabled')
            if is_running: self.input_entry.focus_set()
#
# Runs an automated sequence of commands for the header tool, with configurable delays.
#
    def _run_automated_header_sequence(self):
        try:
            initial = float(self.config['Options'].get('header_initial_delay', 1.0))
            command = float(self.config['Options'].get('header_command_delay', 0.5))
        except ValueError: initial, command = 1.0, 0.5
        time.sleep(initial)
        for cmd in [c.strip() for c in self.config['Options'].get('header_auto_command', 'save; exit').split(';')]:
            if not self.command_running: break
            self.root.after(0, lambda c=cmd: self.input_entry.delete(0, tk.END) or self.input_entry.insert(0, c))
            time.sleep(len(cmd) * 0.05)
            self.send_input_to_process(command_to_send=cmd + '\n')
            time.sleep(command)
        self.root.after(0, lambda: self.input_entry.delete(0, tk.END))
#
# Sends input from the input entry to the currently running process.
#
    def send_input_to_process(self, event=None, command_to_send=None):
        data = command_to_send if command_to_send is not None else self.input_entry.get() + '\n'
        if self.command_running and self.process and self.process.poll() is None:
            try:
                self.log_output(data.strip(), tag='user_input')
                if sys.platform != "win32" and self.master_fd: os.write(self.master_fd, data.encode())
                else: self.process.stdin.write(data); self.process.stdin.flush()
                if command_to_send is None: self.input_entry.delete(0, tk.END)
            except (IOError, OSError, BrokenPipeError): self.log_output("Info: Process closed.", tag='info')
        elif not self.command_running and command_to_send is None:
            self.run_command(None, command_override=self.input_entry.get())
            self.input_entry.delete(0, tk.END)
#
# Sends a break signal to terminate the currently running process.
#
    def send_break_signal(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.log_output("\n--- Sent break signal ---\n", tag='error')
#
# Applies the header to the output file using the configured header tool and action.
#
    def apply_header(self):
        toolchain = self.config.get('Toolchains', {}).get(self.toolchain_type.get(), {})
        action_key = toolchain.get('header_action')
        if action_key: self.run_command(action_key)
        else: self.log_output(f"Error: 'header_action' not defined for toolchain.", tag='error')
#
# Executes the build process, running a sequence of build steps defined in the current toolchain.
#
    def build(self, on_final_success=None):
        toolchain = self.config.get('Toolchains', {}).get(self.toolchain_type.get(), {})
        try: build_steps = ast.literal_eval(toolchain.get('build_steps', '[]'))
        except (ValueError, SyntaxError): build_steps = []
        if not build_steps: return self.log_output(f"Error: No 'build_steps' defined.", tag='error')
        
        action_queue = deque(build_steps)
        def run_next_action():
            if action_queue: self.run_command(action_queue.popleft(), on_success=run_next_action, target_button='Button3') # Assume build is Button3
            elif on_final_success: on_final_success()
        run_next_action()
#
# Executes the command associated with a custom button, handling both single and composite commands.
#
    def execute_custom_button(self, button_key):
        toolchain = self.config.get('Toolchains', {}).get(self.toolchain_type.get(), {})
        try: buttons_data = ast.literal_eval(toolchain.get('custom_buttons', '{}'))
        except (ValueError, SyntaxError): buttons_data = {}
        
        data = buttons_data.get(button_key, {})
        command = data.get('command', '').strip()
        name = data.get('name', button_key)
        self.log_output(f"\n--- '{name}' button pressed ---", tag='info')
        if not command: return

        auto_typer_button = toolchain.get('auto_typer_button', 'None')
        action_queue = deque([b.strip() for b in command.split(',') if b.strip()])
        is_composite = ',' in command

        def run_next_in_chain():
            if not action_queue: return
            
            item_from_queue = action_queue.popleft()
            
            target_for_options = None
            actual_cmd = None

            if is_composite:
                # item_from_queue is a ButtonKey, e.g., 'Button3'
                target_for_options = item_from_queue
                cmd_data = buttons_data.get(target_for_options, {})
                actual_cmd = cmd_data.get('command', target_for_options)
            else:
                # item_from_queue is the raw command string
                target_for_options = button_key
                actual_cmd = item_from_queue

            is_target_for_autotyper = (target_for_options == auto_typer_button)
            
            if not actual_cmd: return run_next_in_chain()

            callback = run_next_in_chain if action_queue else None
            
            self.run_command(None, command_override=actual_cmd, on_success=callback, is_auto_typer_target=is_target_for_autotyper, target_button=target_for_options)
        
        run_next_in_chain()
#
# Cleans the project directory by deleting files with extensions specified in the configuration.
#
    def clean_project(self):
        source = self.source_file.get()
        if not source: return self.log_output("Error: No source file specified.", tag='error')
        
        clean_states = self.config.get('CleanStates', {})
        extensions = {ext for ext, state in clean_states.items() if state.lower() == 'true'}
        if not extensions: return self.log_output("No file types checked for cleaning.", tag='info')

        source_stem = os.path.splitext(source)[0]
        files_to_delete = {source_stem + ext for ext in extensions}
        
        deleted_files = []
        for f in sorted(list(files_to_delete)):
            if os.path.exists(f):
                try: os.remove(f); deleted_files.append(os.path.basename(f))
                except OSError as e: self.log_output(f"Error deleting {f}: {e}", tag='error')
        
        self.log_output(f"Cleaned: {', '.join(deleted_files)}" if deleted_files else "No matching files found.", 
                        tag='success' if deleted_files else 'info')
#
# Opens the project folder in the system's default file manager.
#
    def open_project_folder(self):
        source = self.source_file.get()
        if not source or not os.path.isdir(d := os.path.dirname(source)):
            return self.log_output("Error: Source directory does not exist.", tag='error')
        try:
            if sys.platform == "win32": os.startfile(d)
            elif sys.platform == "darwin": subprocess.Popen(["open", d])
            else: subprocess.Popen(["xdg-open", d])
        except Exception as e: self.log_output(f"Error opening folder: {e}", tag='error')

if __name__ == "__main__":
    root = tk.Tk()
    app = DevCommanderApp(root)
    root.mainloop()

