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

#################################################################
#
# Standard library imports for GUI, file operations, subprocess
# management, and system integration.
#
#################################################################
import tkinter as tk
from tkinter import filedialog, ttk
from tkinter import font as tkfont
import subprocess
import os
import sys
import configparser
import shlex
import queue
import threading
import re
import time

#################################################################
#
# Conditional import of the 'pty' module. This is used for more
# robust pseudo-terminal control, which is only available on
# Unix-like systems (Linux, macOS). It is skipped on Windows.
#
#################################################################
if sys.platform != "win32":
    import pty

#################################################################
#
# Global constants for the application's configuration file
# and the maximum number of projects to keep in history.
#
#################################################################
GLOBAL_CONFIG_FILE = 'devCMDcycle_115.ini'
MAX_HISTORY = 10

#################################################################
#
# get_default_config
#
# Creates and returns a default configuration structure. This is
# used to generate the initial .ini file if one doesn't exist,
# ensuring the application has all necessary settings to start.
# It defines paths to external tools, command-line templates,
# and various application options.
#
#################################################################
def get_default_config():
    """Returns a ConfigParser object with the default application settings."""
    default_config = configparser.ConfigParser(interpolation=None)
    default_config['Tools'] = {'editor': 'xed', '7800asm_script': '7800asm', 'cc65_compiler': 'cl65', 'emulator': 'a7800', 'terminal': 'gnome-terminal', 'header_tool': '7800header', 'signer_tool': '7800sign'}
    default_config['Paths'] = {'last_source': '', 'code_home_dir': os.getcwd(), 'last_output_file': ''}
    default_config['ProjectHistory'] = {}
    default_config['Commands'] = {
        'editor_cmd': '%e %s', 'dasm_build_cmd': '%a %s', 'cc65_build_cmd': '%c -t atari7800 -O -o %o %s',
        'header_cmd': '%h %b', 'signer_cmd': '%g %o', 'run_cmd': "%m a7800 -cart '%o'", 'debug_run_cmd': "%m a7800 -cart '%o' -debug"
    }
    default_config['Options'] = {
        'header_auto_send_command': 'False', 'header_auto_command': 'save',
        'header_initial_delay': '1.0',
        'header_command_delay': '0.5',
        'output_window_size': '40 lines',
        'header_timeout': '5',
        'status_window_width': '100',
        'always_on_top': 'False'
    }
    default_config['CompilerOptions'] = {'dasm_auto_header': 'True', 'cc65_auto_header': 'True', 'cc65_auto_signer': 'True', 'cc65_create_map': 'False', 'cc65_add_debug': 'False'}
    default_config['HeaderWizard'] = {
        'header_wizard_opt_save': 'False', 'header_wizard_opt_strip': 'False',
        'header_wizard_opt_fix': 'False', 'header_wizard_opt_exit': 'False'
    }
    default_config['CleanOptions'] = {
        'clean_a78': 'False', 'clean_bin': 'False', 'clean_list': 'False',
        'clean_symbol': 'False', 'clean_sym': 'False', 'clean_lst': 'False',
        'clean_o': 'False', 'clean_map': 'False', 'clean_dbg': 'False',
        'clean_backup': 'False', 'clean_s_list_txt': 'False', 'clean_s_symbol_txt': 'False'
    }
    return default_config

#################################################################
#
# AnsiColorHandler Class
#
# This class is responsible for interpreting ANSI escape codes
# commonly found in command-line output. It allows the Tkinter
# Text widget to display colored text by mapping ANSI codes to
# Tkinter tags, which are pre-configured with specific colors
# and styles (e.g., bold).
#
#################################################################
class AnsiColorHandler:
    """Handles parsing ANSI escape codes for color in a tkinter Text widget."""
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.ansi_escape = re.compile(r'\x1B\[([0-9;?]*)([a-zA-Z])')
        self.color_map = {
            '30': 'black', '31': 'red', '32': 'green', '33': 'yellow',
            '34': 'blue', '35': 'magenta', '36': 'cyan', '37': 'white'
        }
        self.current_tags = []
        self.setup_tags()

    #############################################################
    # setup_tags
    #
    # Pre-configures the Tkinter Text widget with tags for each
    # ANSI color and style. This makes applying styles efficient.
    #############################################################
    def setup_tags(self):
        """Configure tags for all the basic ANSI colors."""
        for code, color_name in self.color_map.items():
            self.text_widget.tag_configure(f"ansi_{color_name}", foreground=color_name)
        
        try:
            default_font = tkfont.nametofont(self.text_widget.cget("font"))
            bold_font = tkfont.Font(**default_font.configure())
            bold_font.configure(weight="bold")
            self.text_widget.tag_configure("ansi_bold", font=bold_font)
        except tk.TclError:
            self.text_widget.tag_configure("ansi_bold", font=(self.text_widget.cget("font"), 10, "bold"))

    #############################################################
    # write
    #
    # Processes an incoming string, separates text from ANSI
    # codes, and inserts the text into the widget with the
    # appropriate style tags. It maintains the current style state.
    #############################################################
    def write(self, text):
        """Write text to the widget, processing ANSI codes as they appear."""
        # First, explicitly remove screen clearing, cursor movement, and other non-styling codes
        text = re.sub(r'\x1B\[[0-9;?]*[HJK]', '', text)
        text = text.replace('\r', '')

        start = 0
        for match in self.ansi_escape.finditer(text):
            # Insert text before the escape code with the current style
            self.text_widget.insert(tk.END, text[start:match.start()], tuple(self.current_tags))
            start = match.end()
            
            params = match.group(1)
            command = match.group(2)

            if command == 'm':
                if not params or params == '0': # Reset all attributes
                    self.current_tags = []
                    continue
                
                codes = params.split(';')
                for code in codes:
                    if code == '0':
                        self.current_tags = []
                    elif code == '1': # Bold
                        if "ansi_bold" not in self.current_tags:
                            self.current_tags.append("ansi_bold")
                    elif code in self.color_map: # Color codes
                        # Remove other color tags, but keep style tags like bold
                        self.current_tags = [t for t in self.current_tags if not t.startswith('ansi_') or t == 'ansi_bold']
                        self.current_tags.append(f"ansi_{self.color_map[code]}")
        
        # Insert any remaining text after the last escape code with the current style
        self.text_widget.insert(tk.END, text[start:], tuple(self.current_tags))

#################################################################
#
# HeaderWizardFrame Class
#
# A Tkinter LabelFrame that provides a graphical interface for
# constructing the command string for the '7800header' utility.
# It contains checkboxes for various header options, which
# dynamically update a command string stored in a Tkinter Var.
# This simplifies the process of creating complex headers.
#
#################################################################
class HeaderWizardFrame(ttk.LabelFrame):
    """A frame containing a wizard to build the 7800header command."""
    def __init__(self, parent, vars_dict):
        super().__init__(parent, text="Header Command Wizard", padding=10)
        self.vars = vars_dict

        # Define all options available in the header tool
        self.cart_opts = ['linear', 'supergame', 'souper', 'bankset', 'absolute', 'activision']
        self.mem_opts = ['rom@4000', 'bank6@4000', 'ram@4000', 'mram@4000', 'hram@4000', 'bankram']
        self.chip_opts = ['pokey@440', 'pokey@450', 'pokey@800', 'pokey@4000', 'ym2151@460', 'covox@430', 'adpcm@420']
        self.irq_opts = ['irqpokey1', 'irqpokey2', 'irqym2151']
        self.controller_opts = ['7800joy1', '7800joy2', 'lightgun1', 'lightgun2', 'paddle1', 'paddle2', 'tball1', 'tball2', '2600joy1', '2600joy2',
                                'driving1', 'driving2', 'keypad1', 'keypad2', 'stmouse1', 'stmouse2', 'amouse1', 'amouse2', 'snes1', 'snes2', 'mega78001', 'mega78002']
        self.misc_opts = ['hsc', 'savekey', 'xm', 'tvpal', 'tvntsc', 'composite', 'mregion']

        self.create_widgets()
        self.link_vars()

    #############################################################
    # create_widgets
    #
    # Lays out the GUI elements (Checkbuttons, Entries, Labels)
    # for the wizard, organizing them into logical groups.
    #############################################################
    def create_widgets(self):
        # --- Option Checkboxes ---
        def create_check_frame(parent, title, opts):
            frame = ttk.LabelFrame(parent, text=title, padding=5)
            for i, opt in enumerate(opts):
                key = f"header_wizard_opt_{opt.replace('@', '_').replace('/', '_')}"
                self.vars[key] = tk.BooleanVar()
                ttk.Checkbutton(frame, text=opt, variable=self.vars[key]).grid(row=i, column=0, sticky='w')
            return frame

        opts_frame = ttk.Frame(self)
        opts_frame.pack(fill='x', expand=True)

        create_check_frame(opts_frame, "Cart Format", self.cart_opts).pack(side='left', anchor='n', padx=2)
        create_check_frame(opts_frame, "Memory", self.mem_opts).pack(side='left', anchor='n', padx=2)
        create_check_frame(opts_frame, "Sound/IRQ", self.chip_opts + self.irq_opts).pack(side='left', anchor='n', padx=2)
        create_check_frame(opts_frame, "Controllers", self.controller_opts).pack(side='left', anchor='n', padx=2)
        create_check_frame(opts_frame, "Misc", self.misc_opts).pack(side='left', anchor='n', padx=2)

        # --- Command Entries ---
        cmd_frame = ttk.LabelFrame(self, text="Commands", padding=5)
        cmd_frame.pack(fill='x', expand=True, pady=5)
        cmd_frame.columnconfigure(1, weight=1)

        self.vars['header_wizard_name_en'] = tk.BooleanVar()
        self.vars['header_wizard_name'] = tk.StringVar()
        ttk.Label(cmd_frame, text="Game Name:").grid(row=0, column=1, sticky='w', padx=5)
        ttk.Checkbutton(cmd_frame, text="name", variable=self.vars['header_wizard_name_en']).grid(row=1, column=0, sticky='w')
        ttk.Entry(cmd_frame, textvariable=self.vars['header_wizard_name']).grid(row=1, column=1, sticky='ew', padx=5)

        # Changed to checkboxes
        self.vars['header_wizard_opt_save'] = tk.BooleanVar()
        self.vars['header_wizard_opt_strip'] = tk.BooleanVar()
        self.vars['header_wizard_opt_fix'] = tk.BooleanVar()
        self.vars['header_wizard_opt_exit'] = tk.BooleanVar()
        
        ttk.Label(cmd_frame, text="Final Action(s):").grid(row=2, column=0, columnspan=2, sticky='w', padx=5, pady=(5,0))
        ttk.Checkbutton(cmd_frame, text="save", variable=self.vars['header_wizard_opt_save']).grid(row=3, column=0, sticky='w')
        ttk.Checkbutton(cmd_frame, text="strip", variable=self.vars['header_wizard_opt_strip']).grid(row=4, column=0, sticky='w')
        ttk.Checkbutton(cmd_frame, text="fix", variable=self.vars['header_wizard_opt_fix']).grid(row=5, column=0, sticky='w')
        ttk.Checkbutton(cmd_frame, text="exit", variable=self.vars['header_wizard_opt_exit']).grid(row=6, column=0, sticky='w')

    #############################################################
    # link_vars
    #
    # Attaches a trace to each Tkinter variable in the wizard.
    # This ensures that any change to a checkbox or entry field
    # will automatically trigger the _build_command method.
    #############################################################
    def link_vars(self):
        """Add traces to all variables to rebuild the command string on change."""
        for key in self.vars:
            if key.startswith('header_wizard_'):
                self.vars[key].trace_add('write', self._build_command)
        self._build_command() # Initial build

    #############################################################
    # _build_command
    #
    # Callback function that constructs the final command string
    # based on the current state of all the wizard's widgets.
    # The result is stored in the 'header_auto_command' variable.
    #############################################################
    def _build_command(self, *args):
        """Constructs the command string from the wizard's state."""
        commands = []
        final_actions = []

        all_opts = self.cart_opts + self.mem_opts + self.chip_opts + self.irq_opts + self.controller_opts + self.misc_opts

        for opt in all_opts:
            key = f"header_wizard_opt_{opt.replace('@', '_').replace('/', '_')}"
            if key in self.vars and self.vars[key].get():
                commands.append(f"set {opt}")

        if 'header_wizard_name_en' in self.vars and self.vars['header_wizard_name_en'].get() and self.vars['header_wizard_name'].get():
            commands.append(f"name \"{self.vars['header_wizard_name'].get()}\"")

        # Handle the new final action checkboxes and ensure they are last
        final_actions_to_check = ['save', 'strip', 'fix', 'exit']
        for action in final_actions_to_check:
            key = f"header_wizard_opt_{action}"
            if self.vars[key].get():
                final_actions.append(action)

        commands.extend(final_actions)

        if 'header_auto_command' in self.vars:
            self.vars['header_auto_command'].set("; ".join(commands))

#################################################################
#
# SettingsWindow Class
#
# A Toplevel window that provides a comprehensive UI for managing
# all global application settings. This includes file paths for
# external tools, command-line templates for actions, and other
# behavioral options. It interacts directly with the main app's
# configuration object.
#
#################################################################
class SettingsWindow(tk.Toplevel):
    """A comprehensive window for managing global paths and command-line templates."""
    def __init__(self, parent_widget, app_controller):
        super().__init__(parent_widget)
        self.transient(parent_widget)
        self.title("Global Settings")
        self.geometry("1200x1050")

        self.app = app_controller
        self.config = self.app.global_config

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.tool_map = {
            'editor': '%e', '7800asm_script': '%a', 'cc65_compiler': '%c',
            'header_tool': '%h', 'signer_tool': '%g', 'emulator': '%m'
        }
        
        # Define all the boolean variables for the clean options
        self.clean_vars = {
            'clean_a78': tk.BooleanVar(), 'clean_bin': tk.BooleanVar(), 'clean_list': tk.BooleanVar(),
            'clean_symbol': tk.BooleanVar(), 'clean_sym': tk.BooleanVar(), 'clean_lst': tk.BooleanVar(),
            'clean_o': tk.BooleanVar(), 'clean_map': tk.BooleanVar(), 'clean_dbg': tk.BooleanVar(),
            'clean_backup': tk.BooleanVar(), 'clean_s_list_txt': tk.BooleanVar(), 'clean_s_symbol_txt': tk.BooleanVar()
        }

        self.vars = {
            'code_home_dir': tk.StringVar(), 'editor': tk.StringVar(), '7800asm_script': tk.StringVar(),
            'cc65_compiler': tk.StringVar(), 'emulator': tk.StringVar(), 'terminal': tk.StringVar(),
            'header_tool': tk.StringVar(), 'signer_tool': tk.StringVar(),
            'editor_cmd': tk.StringVar(), 'dasm_build_cmd': tk.StringVar(), 'cc65_build_cmd': tk.StringVar(),
            'header_cmd': tk.StringVar(), 'signer_cmd': tk.StringVar(), 'run_cmd': tk.StringVar(),
            'debug_run_cmd': tk.StringVar(),
            'header_auto_send_command': tk.BooleanVar(), 'header_auto_command': tk.StringVar(),
            'header_initial_delay': tk.StringVar(),
            'header_command_delay': tk.StringVar(),
            'header_timeout': tk.StringVar(),
            'status_window_width': tk.StringVar(),
            'always_on_top': tk.BooleanVar(),
            'cc65_auto_header': tk.BooleanVar(),
            'cc65_auto_signer': tk.BooleanVar(),
            'cc65_create_map': tk.BooleanVar(),
            'cc65_add_debug': tk.BooleanVar(),
        }
        self.preview_vars = {key: tk.StringVar() for key in self.vars if '_cmd' in key}

        # --- Main Layout Frames ---
        left_frame = ttk.Frame(self)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        left_frame.rowconfigure(3, weight=1)

        right_frame = ttk.Frame(self)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        paths_frame = ttk.LabelFrame(left_frame, text="Paths", padding=10)
        paths_frame.grid(row=0, column=0, sticky="ew", pady=5)
        paths_frame.columnconfigure(1, weight=1)

        commands_frame = ttk.LabelFrame(left_frame, text="Command Line Templates", padding=10)
        commands_frame.grid(row=1, column=0, sticky="ew", pady=5)
        commands_frame.columnconfigure(1, weight=1)

        preview_frame = ttk.LabelFrame(left_frame, text="Live Command Preview", padding=10)
        preview_frame.grid(row=2, column=0, sticky="ew", pady=5)
        preview_frame.columnconfigure(1, weight=1)

        options_frame = ttk.LabelFrame(left_frame, text="Options", padding=10)
        options_frame.grid(row=3, column=0, sticky="nsew", pady=5)
        options_frame.columnconfigure(0, weight=1)

        self.header_wizard = HeaderWizardFrame(right_frame, self.vars)
        self.header_wizard.grid(row=1, column=0, sticky="ew", pady=5)
        self.create_clean_options_frame(right_frame)

        self.create_legend(right_frame)
        self.load_vars_from_config() # Load after wizard vars are created

        self.create_path_entry(paths_frame, "Code Home Directory", self.vars['code_home_dir'], 0, is_dir=True)
        ttk.Separator(paths_frame, orient='horizontal').grid(row=1, column=0, columnspan=3, sticky='ew', pady=5)
        self.create_path_entry(paths_frame, "Editor", self.vars['editor'], 2)
        self.create_path_entry(paths_frame, "7800asm Script", self.vars['7800asm_script'], 3)
        self.create_path_entry(paths_frame, "CC65 Compiler", self.vars['cc65_compiler'], 4)
        self.create_path_entry(paths_frame, "Header Tool", self.vars['header_tool'], 5)
        self.create_path_entry(paths_frame, "Signer Tool", self.vars['signer_tool'], 6)
        ttk.Entry(paths_frame, textvariable=self.vars['terminal']).grid(row=8, column=1, sticky='ew', padx=5, pady=2)
        ttk.Label(paths_frame, text="Terminal:", padding=2).grid(row=8, column=0, sticky='w', padx=5)
        self.create_path_entry(paths_frame, "Emulator", self.vars['emulator'], 7)

        self.create_command_entry(commands_frame, "Editor:", self.vars['editor_cmd'], 1)
        self.create_command_entry(commands_frame, "7800Asm:", self.vars['dasm_build_cmd'], 2)
        self.create_command_entry(commands_frame, "CC65:", self.vars['cc65_build_cmd'], 3)
        self.create_command_entry(commands_frame, "Header:", self.vars['header_cmd'], 4)
        self.create_command_entry(commands_frame, "Signer:", self.vars['signer_cmd'], 5)
        self.create_command_entry(commands_frame, "Run:", self.vars['run_cmd'], 6)
        self.create_preview_entry(preview_frame, "Editor:", self.preview_vars['editor_cmd'], 1)
        self.create_preview_entry(preview_frame, "7800Asm:", self.preview_vars['dasm_build_cmd'], 2)
        self.create_preview_entry(preview_frame, "CC65:", self.preview_vars['cc65_build_cmd'], 3)
        self.create_preview_entry(preview_frame, "Header:", self.preview_vars['header_cmd'], 4)
        self.create_preview_entry(preview_frame, "Signer:", self.preview_vars['signer_cmd'], 5)
        self.create_preview_entry(preview_frame, "Run:", self.preview_vars['run_cmd'], 6)
        self.create_preview_entry(preview_frame, "Debug:", self.preview_vars['debug_run_cmd'], 7)
        
        ttk.Checkbutton(options_frame, text="Auto-run Header Tool commands", variable=self.vars['header_auto_send_command']).pack(anchor='w')
        header_options_frame = ttk.Frame(options_frame)
        header_options_frame.pack(fill='x', expand=True, pady=5)
        ttk.Label(header_options_frame, text="Header Timeout (s, 0=infinite):").grid(row=1, column=0, sticky='w')
        ttk.Entry(header_options_frame, textvariable=self.vars['header_timeout']).grid(row=1, column=1, sticky='ew')
        ttk.Label(header_options_frame, text="Status Window Width (chars):").grid(row=2, column=0, sticky='w')
        ttk.Entry(header_options_frame, textvariable=self.vars['status_window_width']).grid(row=2, column=1, sticky='ew')
        
        # New Entries for delays
        ttk.Label(header_options_frame, text="Initial Header Delay (s):").grid(row=3, column=0, sticky='w')
        ttk.Entry(header_options_frame, textvariable=self.vars['header_initial_delay']).grid(row=3, column=1, sticky='ew')
        ttk.Label(header_options_frame, text="Command Delay (s):").grid(row=4, column=0, sticky='w')
        ttk.Entry(header_options_frame, textvariable=self.vars['header_command_delay']).grid(row=4, column=1, sticky='ew')

        header_options_frame.columnconfigure(1, weight=1)
        save_button = ttk.Button(left_frame, text="Save & Close", command=self.save_and_close, style="Accent.TButton")
        save_button.grid(row=4, column=0, pady=10)
        for key in self.vars:
            if not key.startswith('header_wizard_'):
                self.vars[key].trace_add('write', self.update_previews)
        self.update_previews()

    #############################################################
    # create_clean_options_frame
    #
    # Builds the UI frame that contains checkboxes for each file
    # type that can be deleted by the "Clean" action.
    #############################################################
    def create_clean_options_frame(self, parent):
        frame = ttk.LabelFrame(parent, text="Clean Options", padding=10)
        frame.grid(row=0, column=0, sticky='ew', padx=5, pady=5)
        
        # File types to be cleaned
        file_types = [
            ('.a78', 'clean_a78'), ('.bin', 'clean_bin'), ('.list.txt', 'clean_list'),
            ('.symbol.txt', 'clean_symbol'), ('.s.list.txt', 'clean_s_list_txt'), ('.s.symbol.txt', 'clean_s_symbol_txt'),
            ('.sym', 'clean_sym'), ('.lst', 'clean_lst'),
            ('.o', 'clean_o'), ('.map', 'clean_map'), ('.dbg', 'clean_dbg'),
            ('.a78.backup', 'clean_backup')
        ]

        # Use grid for a two-column layout
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        
        row = 0
        col = 0
        for text, var_name in file_types:
            self.clean_vars[var_name] = tk.BooleanVar()
            ttk.Checkbutton(frame, text=text, variable=self.clean_vars[var_name]).grid(row=row, column=col, sticky='w', padx=5, pady=2)
            col += 1
            if col > 1:
                col = 0
                row += 1

    #############################################################
    # create_legend
    #
    # Creates a small frame to display the meaning of the
    # placeholders (e.g., %s, %o) used in command templates.
    #############################################################
    def create_legend(self, parent):
        legend_frame = ttk.LabelFrame(parent, text="Placeholders", padding=10)
        legend_frame.grid(row=2, column=0, sticky="ew", pady=5)
        
        placeholders = [
            ('%s:', 'Source'), ('%o:', 'Output'),
            ('%b:', 'Binary'), ('%e:', 'Editor'),
            ('%a:', '7800asm'), ('%c:', 'CC65'),
            ('%h:', 'Header'), ('%g:', 'Signer'),
            ('%m:', 'Emulator')
        ]
        
        row = 0
        for i, (ph, desc) in enumerate(placeholders):
            col = (i % 2) * 2
            if i % 2 == 0 and i > 0:
                row += 1
            
            ttk.Label(legend_frame, text=f"{ph}").grid(row=row, column=col, sticky='w', padx=5, pady=2)
            ttk.Label(legend_frame, text=f"{desc}").grid(row=row, column=col+1, sticky='w', padx=(25, 5), pady=2)

    #############################################################
    # load_vars_from_config
    #
    # Populates the Tkinter variables in the settings window with
    # values loaded from the global configuration object.
    #############################################################
    def load_vars_from_config(self):
        for key, var in self.vars.items():
            section, config_key = self.get_config_location(key)
            if isinstance(var, tk.BooleanVar):
                var.set(self.config.getboolean(section, config_key, fallback=False))
            else:
                var.set(self.config.get(section, config_key, fallback=''))

        # Load clean options
        for var_name, var in self.clean_vars.items():
            var.set(self.config.getboolean('CleanOptions', var_name, fallback=False))

    #############################################################
    # update_previews
    #
    # Dynamically generates and displays a preview of what each
    # command will look like with placeholders resolved. This gives
    # the user immediate feedback as they edit templates.
    #############################################################
    def update_previews(self, *args):
        replacements = {'%s': '/path/to/project.s', '%o': '/path/to/project.a78', '%b': '/path/to/project.bin'}
        for tool, placeholder in self.tool_map.items():
            replacements[placeholder] = self.vars[tool].get() or placeholder
        for key, var in self.preview_vars.items():
            template = self.vars[key].get()
            resolved_cmd = template
            for placeholder, value in replacements.items():
                resolved_cmd = resolved_cmd.replace(placeholder, shlex.quote(value))
            var.set(resolved_cmd)
    
    #############################################################
    # create_path_entry, create_command_entry, create_preview_entry
    #
    # Helper methods to reduce boilerplate code when creating the
    # various labeled entry fields in the settings window.
    #############################################################
    def create_path_entry(self, parent, label, var, row, is_dir=False):
        ttk.Label(parent, text=label + ":").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Entry(parent, textvariable=var).grid(row=row, column=1, sticky="ew", padx=5, pady=2)
        cmd = (lambda v=var: self.browse_for_dir(v)) if is_dir else (lambda v=var: self.browse_for_file(v))
        ttk.Button(parent, text="Browse...", command=cmd).grid(row=row, column=2, padx=5, pady=2)
    
    def create_command_entry(self, parent, label, var, row):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Entry(parent, textvariable=var).grid(row=row, column=1, sticky="ew", padx=5, pady=2)
    
    def create_preview_entry(self, parent, label, var, row):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Entry(parent, textvariable=var, state='readonly').grid(row=row, column=1, sticky="ew", padx=5, pady=2)
    
    #############################################################
    # browse_for_file, browse_for_dir
    #
    # Event handlers for the "Browse..." buttons, opening the
    # appropriate system dialog to select a file or directory.
    #############################################################
    def browse_for_file(self, var):
        if path := filedialog.askopenfilename(): var.set(path)
    
    def browse_for_dir(self, var):
        if path := filedialog.askdirectory(): var.set(path)
    
    #############################################################
    # save_and_close
    #
    # Saves all settings from the window back to the main app's
    # configuration object, writes the config to the .ini file,
    # and then closes the settings window.
    #############################################################
    def save_and_close(self):
        # Update the main app's variables with the values from the settings window
        
        # Save all the clean options
        for var_name, var in self.clean_vars.items():
            self.app.clean_options_vars[var_name].set(var.get())
        
        for var_key, var in self.vars.items():
            section, config_key = self.get_config_location(var_key)
            if not self.config.has_section(section): self.config.add_section(section)
            self.config.set(section, config_key, str(var.get()))
        
        # Update the main app's header auto-run variable separately
        self.app.header_auto_send_command_var.set(self.vars['header_auto_send_command'].get())
        self.app.topmost_var.set(self.vars['always_on_top'].get()) # Ensure this is also updated

        # Save clean options
        if not self.config.has_section('CleanOptions'): self.config.add_section('CleanOptions')
        for var_name, var in self.clean_vars.items():
            self.config.set('CleanOptions', var_name, str(var.get()))

        self.app.save_global_config()
        self.app.apply_ui_settings() # Apply UI changes immediately
        self.destroy()

    #############################################################
    # get_config_location
    #
    # A helper method to determine which section of the .ini file
    # a particular setting belongs to, based on its variable key.
    #############################################################
    def get_config_location(self, var_key):
        if var_key.startswith('header_wizard_'): return ('HeaderWizard', var_key)
        if '_cmd' in var_key: return ('Commands', var_key)
        if var_key in ['header_auto_send_command', 'header_auto_command', 'header_initial_delay', 'header_command_delay', 'header_timeout', 'status_window_width', 'always_on_top']: return ('Options', var_key)
        if var_key in ['cc65_create_map', 'cc65_add_debug', 'dasm_auto_header', 'cc65_auto_header', 'cc65_auto_signer']: return ('CompilerOptions', var_key)
        if var_key == 'code_home_dir': return ('Paths', var_key)
        return ('Tools', var_key)

#################################################################
#
# DevHelperApp Class
#
# This is the main class for the application. It orchestrates
# the entire user interface, manages application state, handles
# user actions, and controls the execution of external
# command-line development tools.
#
#################################################################
class DevHelperApp:
    def __init__(self, root):
        self.root = root
        self.project_history = []
        self.global_config = configparser.ConfigParser(interpolation=None)
        
        #########################################################
        #
        # Tkinter variables to hold the application's state.
        # Using these allows the UI to automatically update when
        # the state changes.
        #
        #########################################################
        self.source_file = tk.StringVar()
        self.output_file = tk.StringVar()
        self.compiler_type = tk.StringVar()
        self.cc65_create_map = tk.BooleanVar()
        self.cc65_add_debug = tk.BooleanVar()
        self.dasm_auto_header = tk.BooleanVar(value=True)
        self.cc65_auto_header = tk.BooleanVar(value=True)
        self.cc65_auto_signer = tk.BooleanVar(value=True)
        self.output_size_var = tk.StringVar()
        self.topmost_var = tk.BooleanVar(value=False)
        self.header_auto_send_command_var = tk.BooleanVar()
        
        self.initial_topmost_state = False
        self.restart_label = None
        
        #########################################################
        #
        # State variables for managing the subprocess execution,
        # including the process object, output queue, and threads.
        #
        #########################################################
        self.process = None
        self.master_pty = None
        self.output_queue = queue.Queue()
        self.reader_thread = None
        self.command_running = False
        self.automated_header_thread = None
        self.ghost_label_var = tk.StringVar(value="")

        # Clean options variables
        self.clean_options_vars = {
            'clean_a78': tk.BooleanVar(), 'clean_bin': tk.BooleanVar(), 'clean_list': tk.BooleanVar(),
            'clean_symbol': tk.BooleanVar(), 'clean_sym': tk.BooleanVar(), 'clean_lst': tk.BooleanVar(),
            'clean_o': tk.BooleanVar(), 'clean_map': tk.BooleanVar(), 'clean_dbg': tk.BooleanVar(),
            'clean_backup': tk.BooleanVar(), 'clean_s_list_txt': tk.BooleanVar(), 'clean_s_symbol_txt': tk.BooleanVar()
        }

        #########################################################
        #
        # UI setup: configure styles, create widgets, load the
        # configuration, and set up traces to auto-save changes.
        #
        #########################################################
        self.configure_styles()
        self.root.title("devCMDcycle v1.15")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.create_project_widgets(main_frame)
        self.create_compiler_option_widgets(main_frame)
        self.create_action_widgets(main_frame)
        self.create_top_right_widgets(main_frame)
        self.create_status_widgets(main_frame)

        self.load_global_config()
        self.source_file.trace_add('write', self.save_global_config)
        self.output_file.trace_add('write', self.save_global_config)
        self.compiler_type.trace_add('write', self.save_global_config)
        self.cc65_create_map.trace_add('write', self.save_global_config)
        self.cc65_add_debug.trace_add('write', self.save_global_config)
        self.dasm_auto_header.trace_add('write', self.save_global_config)
        self.cc65_auto_header.trace_add('write', self.save_global_config)
        self.cc65_auto_signer.trace_add('write', self.save_global_config)
        self.output_size_var.trace_add('write', self.save_global_config)
        self.topmost_var.trace_add('write', self._check_topmost_change)
        self.header_auto_send_command_var.trace_add('write', self._update_ghost_icon)
        
        for var in self.clean_options_vars.values():
            var.trace_add('write', self.save_global_config)
        
        last_source = self.global_config.get('Paths', 'last_source', fallback='')
        if last_source and os.path.exists(last_source):
            self.set_active_project(last_source, startup=True)
        
        self.apply_ui_settings()
        self.root.after(100, self.process_output_queue)
        
    #############################################################
    # configure_styles
    #
    # Defines custom styles for ttk widgets to give the
    # application a more modern and visually informative look.
    # For example, creating 'Success' and 'Accent' button styles.
    #############################################################
    def configure_styles(self):
        style = ttk.Style()
        style.configure("TButton", padding=6, font=('Helvetica', 10))
        style.configure("Success.TButton", background="#28a745", foreground="white", font=('Helvetica', 10, 'bold'))
        style.map("Success.TButton", background=[('active', '#218838')])
        style.configure("Accent.TButton", background="#007bff", foreground="white", font=('Helvetica', 10, 'bold'))
        style.map("Accent.TButton", background=[('active', '#0069d9')])
        style.configure("Danger.Outline.TButton", bordercolor="#dc3545", foreground="#dc3545")
        style.map("Danger.Outline.TButton", foreground=[('active', 'white')], background=[('active', '#dc3545')])
        
        style.layout("TCheckbutton",
            [('Checkbutton.padding',
              {'sticky': 'nswe', 'children':
               [('Checkbutton.focus',
                 {'sticky': 'nswe', 'children':
                  [('Checkbutton.indicator', {'side': 'left', 'sticky': ''}),
                   ('Checkbutton.label', {'side': 'right', 'sticky': 'nswe'})]}
                )]}
            )])
        style.configure("TCheckbutton", font=('Helvetica', 10))
        style.map("TCheckbutton", indicatorcolor=[('selected', 'black')])
        style.map("TCheckbutton", indicatorbackground=[('selected', 'white')])

    #############################################################
    # create_project_widgets
    #
    # Builds the "Project" section of the UI, which includes
    # entry fields for the source and output files, browse buttons,
    # and the compiler selection combobox.
    #############################################################
    def create_project_widgets(self, parent):
        frame = ttk.LabelFrame(parent, text="Project", padding=10)
        frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Source File:").grid(row=0, column=0, sticky=tk.W, pady=2, padx=5)
        ttk.Entry(frame, textvariable=self.source_file, width=50).grid(row=0, column=1, sticky="ew")
        ttk.Button(frame, text="Browse...", command=self.browse_file).grid(row=0, column=2, padx=(5, 0))

        ttk.Label(frame, text="Output ROM:").grid(row=1, column=0, sticky=tk.W, pady=2, padx=5)
        ttk.Entry(frame, textvariable=self.output_file, width=50).grid(row=1, column=1, sticky="ew")
        ttk.Button(frame, text="Browse...", command=self.browse_output_file).grid(row=1, column=2, padx=(5, 0))

        ttk.Label(frame, text="Compiler:").grid(row=2, column=0, sticky=tk.W, pady=2, padx=5)
        self.compiler_combo = ttk.Combobox(frame, textvariable=self.compiler_type, values=['7800AsmDevKit', 'CC65'], state='readonly')
        self.compiler_combo.grid(row=2, column=1, sticky="w")
        self.compiler_combo.bind("<<ComboboxSelected>>", self.on_compiler_selected)

    #############################################################
    # create_compiler_option_widgets
    #
    # Builds the dynamic "Compiler Options" area. It creates
    # separate frames for 7800Asm and CC65 options, which are
    # shown or hidden based on the current compiler selection.
    #############################################################
    def create_compiler_option_widgets(self, parent):
        container = ttk.Frame(parent)
        container.grid(row=1, column=0, sticky="ew")

        self.dasm_options_frame = ttk.LabelFrame(container, text="7800AsmDevKit Options", padding=10)
        ttk.Checkbutton(self.dasm_options_frame, text="Run Header Tool after build", variable=self.dasm_auto_header).pack(anchor="w", pady=(5,0))

        self.cc65_options_frame = ttk.LabelFrame(container, text="CC65 Options", padding=10)
        ttk.Checkbutton(self.cc65_options_frame, text="Create Map File (.map)", variable=self.cc65_create_map).pack(anchor="w")
        ttk.Checkbutton(self.cc65_options_frame, text="Add Debug Info (-g)", variable=self.cc65_add_debug).pack(anchor="w")
        
        ttk.Checkbutton(self.cc65_options_frame, text="Run Signer Tool after build", variable=self.cc65_auto_signer).pack(anchor="w", pady=(5,0))
        ttk.Checkbutton(self.cc65_options_frame, text="Run Header Tool after build", variable=self.cc65_auto_header).pack(anchor="w", pady=(5,0))

    #############################################################
    # create_action_widgets
    #
    # Builds the "Actions" section of the UI, containing all the
    # main command buttons like Build, Run, Edit, Settings, etc.
    #############################################################
    def create_action_widgets(self, parent):
        frame = ttk.LabelFrame(parent, text="Actions", padding=10)
        frame.grid(row=2, column=0, columnspan=2, pady=10, sticky="ew")
        frame.columnconfigure((0, 1, 2, 3), weight=1)
        
        # Action Buttons in the main actions frame
        ttk.Button(frame, text="Settings ⚙️", command=lambda: self.log_and_run("Settings", self.open_settings)).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ttk.Button(frame, text="Open Folder 📂", command=lambda: self.log_and_run("Open Folder", self.open_project_folder)).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(frame, text="Clean 🧹", command=lambda: self.log_and_run("Clean", self.clean_project), style="Danger.Outline.TButton").grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        ttk.Button(frame, text="Exit Commander", command=self.on_closing).grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        ttk.Button(frame, text="Edit", command=lambda: self.log_and_run("Edit", self.edit_file)).grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        ttk.Button(frame, text="Build", command=lambda: self.log_and_run("Build", self.build_rom), style="Success.TButton").grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(frame, text="Run", command=lambda: self.log_and_run("Run", self.run_emulator), style="Accent.TButton").grid(row=1, column=2, padx=5, pady=5, sticky="ew")
        ttk.Button(frame, text="Run (Debug)", command=lambda: self.log_and_run("Run (Debug)", self.run_emulator, debug=True), style="Accent.TButton").grid(row=1, column=3, padx=5, pady=5, sticky="ew")
        
        ttk.Button(frame, text="Build & Run 🚀", command=lambda: self.log_and_run("Build & Run", self.build_and_run), style="Success.TButton").grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        # New "Build & Run(Debug)" button
        ttk.Button(frame, text="Build & Run(Debug)", command=lambda: self.log_and_run("Build & Run(Debug)", self.build_and_run_debug), style="Accent.TButton").grid(row=2, column=2, columnspan=2, padx=5, pady=5, sticky="ew")
        
        ttk.Button(frame, text="Apply Header", command=lambda: self.log_and_run("Apply Header", self.apply_header)).grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        ttk.Button(frame, text="Apply Signer", command=lambda: self.log_and_run("Apply Signer", self.apply_signer)).grid(row=3, column=2, columnspan=2, padx=5, pady=5, sticky="ew")
    
    #############################################################
    # create_top_right_widgets
    #
    # Builds the miscellaneous widgets in the top-right corner,
    # including the "Always on Top" checkbox and the "About" button.
    #############################################################
    def create_top_right_widgets(self, parent):
        """Creates a container for the top-right widgets to ensure alignment."""
        # 1. Create a single container frame.
        container = ttk.Frame(parent)
        container.grid(row=1, column=1, sticky="ne", padx=5, pady=5)

        # 2. Create and pack the "Window Options" frame inside the container.
        topmost_container = ttk.LabelFrame(container, text="Window Options", padding=5)
        topmost_container.pack(fill='x', expand=True)
        
        ttk.Checkbutton(topmost_container, text="Always on Top", variable=self.topmost_var).grid(row=0, column=0, sticky='w')
        self.restart_label = ttk.Label(topmost_container, text="", font=('Helvetica', 8, 'italic'), foreground='red')
        self.restart_label.grid(row=1, column=0, sticky='w')

        # 3. Create and pack the "About" frame inside the container, below the previous one.
        about_frame = ttk.LabelFrame(container, text="About", padding=5)
        about_frame.pack(fill='x', expand=True, pady=(5,0))
        about_frame.columnconfigure(0, weight=1) # Make button expand
        
        ttk.Button(about_frame, text="About This App", command=self.create_about_window).grid(row=0, column=0, sticky='ew')

    #############################################################
    # create_about_window
    #
    # Creates the "About" Toplevel window, which displays help
    # text, version information, and license details in a
    # scrollable text area.
    #############################################################
    def create_about_window(self):
        """Creates a new, scrollable Toplevel window with application info."""
        about_win = tk.Toplevel(self.root)
        about_win.title("About devCMDcycle v1.15")
        about_win.geometry("800x700")
        about_win.transient(self.root) # Keep it on top of the main window
        about_win.grab_set() # Modal behavior

        main_frame = ttk.Frame(about_win, padding=10)
        main_frame.pack(fill='both', expand=True)
        main_frame.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)

        text_area = tk.Text(main_frame, wrap='word', height=10, width=50, font=("Helvetica", 10))
        scrollbar = ttk.Scrollbar(main_frame, orient='vertical', command=text_area.yview)
        text_area.config(yscrollcommand=scrollbar.set)

        text_area.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')

        # --- Content for the About Window ---
        about_content = """
devCMDcycle.py
Version: 1.15
Author: RetroGameGirl (AtariAge)

================================
TABLE OF CONTENTS
================================
1. Introduction
2. The Main Window
    2.1. Project Frame
    2.2. Compiler Options
    2.3. Window Options & About
    2.4. Actions Frame
    2.5. Status Window
3. Core Workflow: First Steps
4. The Settings Window
    4.1. Paths
    4.2. Command Line Templates
    4.3. Live Command Preview
    4.4. Options
    4.5. Header Command Wizard
    4.6. Clean Options
5. License Information

================================
1. INTRODUCTION
================================
Welcome to the Dev Command cycle.  

First: Use at your own risk.  See the license information at the bottom of this about.  There may be mistakes in this code, I know there are absolutely dead functions as I spaghetti strung it together, I did learn to code using 8-bit basic on a trash-80.

I prefer coding in a standard text editor and found that a lot of the modern IDE plugins for Atari development were more complex than I needed. This script started as my personal build process and has evolved into something worth sharing.

It's been primarily tested on *nix-based systems, but it should be portable enough to work on other platforms.

Requirements:

Python Environment

- Python 3.x: The script uses modern syntax like f-strings, so a recent version of Python 3 is required.

- Tkinter: This is the library used for the GUI. It's included with most Python installs on Windows and macOS, but on Linux, you may need to install it separately (e.g., sudo apt-get install python3-tk).

Operating System:

The script is designed to be cross-platform (Windows, macOS, Linux). However, it performs best on Linux or macOS because it uses the pty module for cleaner interactive terminal control, which isn't available on Windows. It will still function on Windows, but the console behavior might differ slightly.

External Atari 7800 Tools:

This is the most critical part. The Dev Commander is a front-end; it doesn't include the compilers or emulators. You must install these tools yourself and ensure they are available in your system's PATH.

- 7800asm: The assembler for your .s or .asm source files.

- cc65 toolchain: Specifically, the cl65 compiler for C projects.

- 7800header: Utility to add the required header to your ROM.

- 7800sign: Utility to sign your ROM, typically used with cc65.

- An Atari 7800 Emulator: The default is a7800, but this can be configured to use MAME or another emulator.

- A Text Editor: Your preferred editor for writing code (defaults to xed).

What It Does:

This tool is a graphical front-end for the common command-line utilities used in Atari 7800 development. The goal is to simplify the workflow, allowing you to build ROMs and launch them in an emulator with a few clicks instead of typing out commands for each step of the process.

================================
2. THE MAIN WINDOW
================================
First off, the quirks, which I do not intend to fix:  if you use 7800AsmDevKit, do not change the output file path, leave it at the default, which is the same as your source path.  If you move it, and do not otherwise implement a script to copy the file to that location etc, the emulator will not run.  If you use CC65, testing has shown that this works properly.

The main window is your central hub for all development activities.

2.1. Project Frame
This is where you define the core files for your project.
- Source File: Your main assembly (.s, .asm) or C (.c) file. Use "Browse..." to select it. The application will automatically guess the compiler based on the file extension.
- Output ROM: The final, playable .a78 ROM file. A default name and location will be generated based on your source file, but you can change it.
- Compiler: Choose between '7800AsmDevKit' (for assembly projects) and 'CC65' (for C projects). This selection determines which build commands and options are used.

2.2. Compiler Options
This section dynamically changes based on the selected compiler.
- 7800AsmDevKit Options:
    - Run Header Tool after build: If checked, the 7800header tool will automatically run after a successful assembly to add the necessary cartridge header to your binary file. This is highly recommended.
- CC65 Options:
    - Create Map File: Generates a .map file detailing the memory layout of your compiled program.
    - Add Debug Info: Adds debugging symbols to your build, useful for more advanced debugging with compatible emulators.
    - Run Signer/Header Tool: Automatically runs the signing and header utilities after a successful build, which is required for most CC65 projects.

2.3. Window Options & About
- Always on Top: Keeps the Commander window on top of all other applications. A restart is required for this change to take full effect.
- About This App: Opens this help window.

2.4. Actions Frame
This contains all the primary commands.
- Settings: Opens the detailed Settings Window.
- Open Folder: Opens the project's directory in your system's file manager.
- Clean: Deletes generated files (like .bin, .a78, .map) from your project directory based on rules configured in Settings.
- Edit: Opens your selected Source File in the default text editor configured in Settings.
- Build: Compiles your source code.
- Run: Launches the Output ROM in the emulator.
- Run (Debug): Launches the ROM in the emulator with debug flags enabled.
- Build & Run / Build & Run(Debug): A convenient one-click option to perform a build and then immediately launch the emulator.
- Apply Header/Signer: Manually run the header or signer tools on the appropriate output file.

2.5. Status Window
This is your feedback console.
- Output Size: Adjust the height of the text area.
- Text Area: All output from the command-line tools is displayed here in real-time. Success messages are green, errors are red.
- Input Bar: When a tool runs that requires user input (like the 7800header tool in interactive mode), you can type commands here and press Enter. The "Break" button can be used to terminate a running process.
- If you see "A-R" next to the input bar, you have Auto-Run enabled in the settings to type in your header information for you.  If you do not have it do a final command, you can still interact with it in this mode after it is done doing its typing.

================================
3. CORE WORKFLOW: FIRST STEPS
================================
1.  Go to Settings and ensure the paths to your tools (7800asm, cl65, a7800, etc.) are correct.
2.  In the main window, click "Browse..." and select your project's main source file.
3.  Select your toolchain.
4.  Set your options in the settings and toolchain options.
5.  Verify the Compiler and Output ROM path are correct.
6.  Click "Build & Run".
7.  The Status Window will show the build process. If successful, the emulator will launch with your game. If there are errors, they will be displayed in red.

================================
4. THE SETTINGS WINDOW
================================
This is where you customize the Commander to fit your environment.

4.1. Paths
Set the full path to all the external tools you use, as well as a default "Code Home Directory" for the file browser.

4.2. Command Line Templates
Customize the exact commands that are run. Special placeholders are used:
- %s: Source File
- %o: Output File
- %b: Binary File (the intermediate .bin file)
- %e, %a, %c, %h, %g, %m: The respective tools defined in the Paths section.

4.3. Live Command Preview
This read-only section shows you what a command will look like with all placeholders resolved, helping you debug your templates.

4.4. Options
- Auto-run Header Tool commands: Enables a powerful automation feature. When checked, the Commander will automatically send a sequence of commands (defined in the Header Wizard) to the 7800header tool, allowing for fully automated, "headless" header generation.
- Delays: Configure delays for the automation to ensure the tool is ready to receive commands.
- On the Status window, if you see A-R next to the input bar, the Auto-Run option is active.

4.5. Header Command Wizard
This powerful tool lets you visually build the command sequence for the 7800header tool. Check the options you need (e.g., cart format, memory type, controllers) and the wizard will generate the command string for you. This is used by the "Auto-run" feature.

4.6. Clean Options
Select which file extensions should be deleted when you use the "Clean" action on the main window.

================================
5. LICENSE INFORMATION
================================
          
This software is licensed under the GNU General Public License version 3.
See [https://www.gnu.org/licenses/gpl-3.0.html](https://www.gnu.org/licenses/gpl-3.0.html) for details.

"""
        text_area.insert('1.0', about_content)
        text_area.config(state='disabled') # Make it read-only

    #############################################################
    # create_status_widgets
    #
    # Builds the "Status Window" at the bottom of the UI. This
    # includes the main text area for command output, a scrollbar,
    # an input field for interactive commands, and controls for
    # resizing the output area.
    #############################################################
    def create_status_widgets(self, parent):
        frame = ttk.LabelFrame(parent, text="Status Window", padding=10)
        frame.grid(row=3, column=0, columnspan=2, sticky="ew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        size_frame = ttk.Frame(frame)
        size_frame.grid(row=0, column=0, sticky='ew', pady=(0,5))
        ttk.Label(size_frame, text="Output Size:").pack(side='left', padx=(0,5))
        size_combo = ttk.Combobox(size_frame, textvariable=self.output_size_var, 
                                  values=['10 lines', '20 lines', '30 lines', 
                                          '40 lines', '50 lines', '60 lines'], 
                                  state='readonly', width=20)
        size_combo.pack(side='left')
        size_combo.bind("<<ComboboxSelected>>", self.resize_output_window)

        self.output_text = tk.Text(frame, height=10, width=100, wrap=tk.WORD, background="black", foreground="white", insertbackground="white")
        self.output_text.grid(row=1, column=0, sticky="nsew")
        self.ansi_handler = AnsiColorHandler(self.output_text)

        scrollbar = ttk.Scrollbar(frame, command=self.output_text.yview)
        scrollbar.grid(row=1, column=1, sticky='ns')
        self.output_text.config(yscrollcommand=scrollbar.set)
        
        try:
            default_font = tkfont.nametofont(self.output_text.cget("font"))
            bold_font = tkfont.Font(**default_font.configure())
            italic_font = tkfont.Font(**default_font.configure())
            italic_font.configure(slant="italic")
        except tk.TclError:
            bold_font = (self.output_text.cget("font"), 10, "bold")
            italic_font = (self.output_text.cget("font"), 10, "italic")

        self.output_text.tag_configure("success", foreground="#28a745", font=bold_font)
        self.output_text.tag_configure("error", foreground="#dc3545", font=bold_font)
        self.output_text.tag_configure("info", foreground="#17a2b8")
        self.output_text.tag_configure("autocommand", foreground="#007bff", font=italic_font)
        
        self.input_frame = ttk.Frame(frame)
        self.input_frame.grid(row=2, column=0, sticky="ew", pady=(5,0))
        # Use four columns with a fixed, stable layout.
        self.input_frame.columnconfigure(0, weight=0) # For AR label
        self.input_frame.columnconfigure(1, weight=1) # For entry bar
        self.input_frame.columnconfigure(2, weight=0) # For Enter button
        self.input_frame.columnconfigure(3, weight=0) # For Break button
        
        # Ghost label for Auto-run header command
        self.ghost_label = ttk.Label(self.input_frame, font=('Helvetica', 10, 'bold'), foreground='red')
        # We will position the ghost label in a fixed grid cell.
        self.ghost_label.grid(row=0, column=0, padx=(5,0), sticky='w')
        
        self.input_entry = ttk.Entry(self.input_frame)
        self.input_entry.grid(row=0, column=1, sticky="ew", padx=(5,0))
        self.input_entry.bind('<Return>', self.send_command)
        
        self.input_button = ttk.Button(self.input_frame, text="Enter", command=self.send_command)
        self.input_button.grid(row=0, column=2, padx=(5,0))

        self.break_button = ttk.Button(self.input_frame, text="Break", command=self.send_break_signal, state='disabled')
        self.break_button.grid(row=0, column=3, padx=(5,0))

        self.update_output("Ready. Select a project or browse for a source file.")
        
    #############################################################
    # set_command_running_state
    #
    # Manages the enabled/disabled state of the interactive input
    # widgets (Break button, input entry) based on whether a
    # subprocess is currently running.
    #############################################################
    def set_command_running_state(self, is_running):
        """Manages the state of the interactive buttons based on whether a command is active."""
        self.command_running = is_running
        self.break_button.config(state='normal' if is_running else 'disabled')
        if is_running:
            self.input_entry.focus_set()

    #############################################################
    # send_command
    #
    # Handles the 'Enter' key press or button click for the input
    # bar. If a process is running, it sends the input to the
    # process's stdin. Otherwise, it attempts to execute the
    # command in the system shell.
    #############################################################
    def send_command(self, event=None):
        """Sends a command to the running subprocess and logs it."""
        command = self.input_entry.get()
        self.input_entry.delete(0, tk.END)

        if self.command_running and self.process and self.process.poll() is None:
            self._log(f"\n$ {command}", "autocommand")
            if sys.platform != "win32":
                os.write(self.master_pty, (command + '\n').encode())
            else:
                self.process.stdin.write(command + '\n')
                self.process.stdin.flush()
        elif not self.command_running:
            self.execute_shell_command(command)

    #############################################################
    # execute_shell_command
    #
    # Executes a simple shell command (like 'ls' or 'dir') when
    # no other process is running. This provides basic shell
    # functionality within the app's status window.
    #############################################################
    def execute_shell_command(self, command):
        """Executes a basic shell command like ls, dir, etc."""
        self.process = None
        self._log(f"\n$ {command}", "autocommand")
        
        cwd = os.path.dirname(self.source_file.get()) if self.source_file.get() else os.getcwd()

        if not command.strip():
            return

        try:
            if sys.platform == "win32":
                cmd_list = ['cmd', '/c', command]
            else:
                cmd_list = shlex.split(command)

            self.execute_command(cmd_list, "Shell command finished.", cwd=cwd, is_shell_cmd=True)

        except Exception as e:
            self._log(f"❌ Error executing shell command: {e}", "error")

    #############################################################
    # send_break_signal
    #
    # Attempts to terminate the currently running subprocess.
    # This is the action for the "Break" button.
    #############################################################
    def send_break_signal(self):
        """Sends a termination signal to the running subprocess."""
        if self.command_running and self.process and self.process.poll() is None:
            self._log("--- Sending break signal ---", "error")
            try:
                self.process.terminate()
            except Exception as e:
                self._log(f"❌ Failed to send break signal: {e}", "error")
        else:
            self._log("No process running to send a break signal to.", "info")
            
    #############################################################
    # process_output_queue
    #
    # This method is called periodically by the Tkinter main loop.
    # It checks a queue for any new output from the running
    # subprocess (which is read by a separate thread) and logs it
    # to the output text widget. This keeps the GUI responsive.
    #############################################################
    def process_output_queue(self):
        """Periodically checks the queue for new output from the subprocess thread."""
        try:
            while True:
                line = self.output_queue.get_nowait()
                self._log_raw(line)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_output_queue)

    #############################################################
    # resize_output_window
    #
    # Adjusts the height of the output text widget based on the
    # selection in the "Output Size" combobox.
    #############################################################
    def resize_output_window(self, event=None):
        size_map = {
            '10 lines': 10, '20 lines': 20, '30 lines': 30,
            '40 lines': 40, '50 lines': 50, '60 lines': 60
        }
        new_height = size_map.get(self.output_size_var.get(), 40)
        self.output_text.config(height=new_height)

    #############################################################
    # apply_ui_settings
    #
    # Applies settings from the configuration that can be changed
    # dynamically without restarting the application, such as
    # window size and the "Always on Top" attribute.
    #############################################################
    def apply_ui_settings(self):
        """Applies UI settings from the config file that don't require a restart."""
        self.resize_output_window()
        try:
            width = int(self.global_config.get('Options', 'status_window_width', fallback=100))
            self.output_text.config(width=width)
        except ValueError:
            self.output_text.config(width=100)
        
        self.root.wm_attributes("-topmost", self.topmost_var.get())
        self._update_ghost_icon()

    #############################################################
    # _update_ghost_icon, I originally wanted a "ghost typer"
    #
    # Shows or hides the "A-R" (Auto-Run) label next to the input
    # bar based on whether the header auto-run option is enabled.
    #############################################################
    def _update_ghost_icon(self, *args):
        # Explicitly grid and configure widgets based on the auto-run state.
        if self.header_auto_send_command_var.get():
            # Show the label and configure the entry to occupy one column
            self.ghost_label.grid(row=0, column=0, padx=(5,0), sticky='w')
            self.ghost_label.config(text="A-R")
            self.input_entry.grid(row=0, column=1, sticky="ew", padx=(5,0), columnspan=1)
        else:
            # Hide the label and configure the entry to span the space
            self.ghost_label.grid_remove()
            self.input_entry.grid(row=0, column=0, sticky="ew", padx=(5,0), columnspan=2)

    #############################################################
    # update_compiler_options_view
    #
    # Shows or hides the specific option frames for 7800Asm and
    # CC65 based on the current selection in the compiler combobox.
    #############################################################
    def update_compiler_options_view(self, event=None):
        if self.compiler_type.get() == '7800AsmDevKit':
            self.cc65_options_frame.grid_remove(); self.dasm_options_frame.grid(row=0, column=0, sticky="ew")
        elif self.compiler_type.get() == 'CC65':
            self.dasm_options_frame.grid_remove(); self.cc65_options_frame.grid(row=0, column=0, sticky="ew")
        else:
            self.dasm_options_frame.grid_remove(); self.cc65_options_frame.grid_remove()

    #############################################################
    # load_global_config
    #
    # Reads the .ini configuration file from disk and populates
    # all the application's state variables with the loaded values.
    # If the file doesn't exist, it creates a default one first.
    #############################################################
    def load_global_config(self):
        if not os.path.exists(GLOBAL_CONFIG_FILE): self.create_default_global_config()
        self.global_config.read(GLOBAL_CONFIG_FILE, encoding='utf-8')
        
        self.source_file.set(self.global_config.get('Paths', 'last_source', fallback=''))
        self.output_file.set(self.global_config.get('Paths', 'last_output_file', fallback=''))
        self.compiler_type.set(self.global_config.get('Paths', 'last_compiler', fallback='7800AsmDevKit'))
        
        self.cc65_create_map.set(self.global_config.getboolean('CompilerOptions', 'cc65_create_map', fallback=False))
        self.cc65_add_debug.set(self.global_config.getboolean('CompilerOptions', 'cc65_add_debug', fallback=False))
        self.dasm_auto_header.set(self.global_config.getboolean('CompilerOptions', 'dasm_auto_header', fallback=True))
        self.cc65_auto_header.set(self.global_config.getboolean('CompilerOptions', 'cc65_auto_header', fallback=True))
        self.cc65_auto_signer.set(self.global_config.getboolean('CompilerOptions', 'cc65_auto_signer', fallback=True))
        
        self.output_size_var.set(self.global_config.get('Options', 'output_window_size', fallback='40 lines'))
        # Load the initial state and store it
        initial_topmost_state = self.global_config.getboolean('Options', 'always_on_top', fallback=False)
        self.topmost_var.set(initial_topmost_state)
        self.initial_topmost_state = initial_topmost_state

        # Set the header auto-run var based on the config
        self.header_auto_send_command_var.set(self.global_config.getboolean('Options', 'header_auto_send_command', fallback=False))

        # Load clean options
        if self.global_config.has_section('CleanOptions'):
            for var_name in self.clean_options_vars:
                self.clean_options_vars[var_name].set(self.global_config.getboolean('CleanOptions', var_name, fallback=False))
        else:
            for var in self.clean_options_vars.values():
                var.set(False)

        if self.global_config.has_section('ProjectHistory'):
            self.project_history = [v for k, v in self.global_config.items('ProjectHistory')]
        
        self.update_compiler_options_view()
        self._update_ghost_icon()

    #############################################################
    # create_default_global_config
    #
    # Writes the default configuration to the .ini file.
    #############################################################
    def create_default_global_config(self):
        """Creates the default global config file if it doesn't exist."""
        default_config = get_default_config()
        with open(GLOBAL_CONFIG_FILE, 'w', encoding='utf-8') as configfile:
            default_config.write(configfile)

    #############################################################
    # on_closing
    #
    # Handles the window close event. It ensures the current
    # configuration is saved and terminates any running subprocess
    # before destroying the main window.
    #############################################################
    def on_closing(self):
        self.save_global_config()
        
        if self.process and self.process.poll() is None:
            self.process.terminate()

        self.root.destroy()
        
    #############################################################
    # save_global_config
    #
    # Persists the current state of the application's variables
    # to the .ini file on disk. This is typically called automatically
    # when state changes or when the application is closing.
    #############################################################
    def save_global_config(self, *args):
        self.global_config.set('Paths', 'last_source', self.source_file.get())
        self.global_config.set('Paths', 'last_output_file', self.output_file.get())
        self.global_config.set('Paths', 'last_compiler', self.compiler_type.get())
        
        if not self.global_config.has_section('CompilerOptions'): self.global_config.add_section('CompilerOptions')
        self.global_config.set('CompilerOptions', 'cc65_create_map', str(self.cc65_create_map.get()))
        self.global_config.set('CompilerOptions', 'cc65_add_debug', str(self.cc65_add_debug.get()))
        self.global_config.set('CompilerOptions', 'dasm_auto_header', str(self.dasm_auto_header.get()))
        self.global_config.set('CompilerOptions', 'cc65_auto_header', str(self.cc65_auto_header.get()))
        self.global_config.set('CompilerOptions', 'cc65_auto_signer', str(self.cc65_auto_signer.get()))

        if not self.global_config.has_section('ProjectHistory'): self.global_config.add_section('ProjectHistory')
        self.global_config.remove_section('ProjectHistory')
        self.global_config.add_section('ProjectHistory')
        for i, path in enumerate(self.project_history):
            self.global_config.set('ProjectHistory', f'path{i}', path)

        if not self.global_config.has_section('Options'): self.global_config.add_section('Options')
        self.global_config.set('Options', 'output_window_size', str(self.output_size_var.get()))
        self.global_config.set('Options', 'always_on_top', str(self.topmost_var.get()))
        self.global_config.set('Options', 'header_auto_send_command', str(self.header_auto_send_command_var.get()))
        
        # Save clean options
        if not self.global_config.has_section('CleanOptions'): self.global_config.add_section('CleanOptions')
        for var_name, var in self.clean_options_vars.items():
            self.global_config.set('CleanOptions', var_name, str(var.get()))

        with open(GLOBAL_CONFIG_FILE, 'w', encoding='utf-8') as f:
            self.global_config.write(f)

    #############################################################
    # set_active_project
    #
    # Updates the application state when a new source file is
    # selected. It sets the source file path, derives a default
    # output ROM path, and guesses the compiler type based on
    # the file extension.
    #############################################################
    def set_active_project(self, filepath, startup=False):
        self.source_file.set(filepath)
        
        if not self.output_file.get():
            base_name = os.path.splitext(os.path.basename(filepath))[0]
            output = os.path.join(os.path.dirname(filepath), f"{base_name}.a78")
            self.output_file.set(output)
        
        if filepath.lower().endswith('.c'):
            self.compiler_type.set('CC65')
        else:
            self.compiler_type.set('7800AsmDevKit')

        if not startup: self.update_output(f"Switched to project: {filepath}")
        self.apply_ui_settings()

    #############################################################
    # _log_raw, _log, _clear_log_and_log
    #
    # Methods for writing messages to the status output window.
    # _log_raw: Handles raw text, processing ANSI codes.
    # _log: Writes a simple message with a specific style tag.
    # _clear_log_and_log: Clears the log before writing a message.
    #############################################################
    def _log_raw(self, message):
        """Logs raw text to the output, processing ANSI codes."""
        self.output_text.config(state=tk.NORMAL)
        self.ansi_handler.write(message)
        self.output_text.see(tk.END)
        self.output_text.config(state=tk.DISABLED)
        self.root.update_idletasks()

    def _log(self, message, tag="info"):
        """Logs a simple message with a specific tag, no ANSI processing."""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.insert(tk.END, message + "\n", tag)
        self.output_text.see(tk.END)
        self.output_text.config(state=tk.DISABLED)
        self.root.update_idletasks()

    def _clear_log_and_log(self, message, tag="info"):
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, message + "\n", tag)
        self.output_text.config(state=tk.DISABLED)
        self.root.update_idletasks()

    #############################################################
    # _read_stream_to_queue
    #
    # This function runs in a separate thread. It continuously
    # reads from the output stream of a subprocess and puts the
    # data into a queue, which the main GUI thread can then
    # process without blocking.
    #############################################################
    def _read_stream_to_queue(self, stream_fd, queue_instance):
        """Reads data from a stream file descriptor and puts it into a queue."""
        try:
            while True:
                data = os.read(stream_fd, 1024)
                if not data:
                    break
                queue_instance.put(data.decode('utf-8', errors='replace'))
        except Exception as e:
            pass

    #############################################################
    # log_and_run
    #
    # A wrapper function for all button actions. It first logs
    # which button was pressed and the command that will be
    # executed, and then calls the actual action function.
    #############################################################
    def log_and_run(self, button_name, action, *args, **kwargs):
        """Logs the button press and then executes the action."""
        self._log(f"\n--- {button_name} button pressed ---", "success")
        
        command_to_run = "Command placeholder..."
        if self.source_file.get():
            if self.compiler_type.get() == '7800AsmDevKit':
                target_file = f"{os.path.splitext(self.source_file.get())[0]}.bin"
            else:
                target_file = self.output_file.get()

        if button_name == "Build":
            if self.compiler_type.get() == '7800AsmDevKit':
                cmd_template = self.global_config.get('Commands', 'dasm_build_cmd')
                command_to_run = self.resolve_command(cmd_template)
            else:
                cmd_template = self.global_config.get('Commands', 'cc65_build_cmd')
                if self.cc65_create_map.get(): cmd_template += f" -m '{os.path.splitext(self.output_file.get())[0]}.map'"
                if self.cc65_add_debug.get(): cmd_template += ' -g'
                command_to_run = self.resolve_command(cmd_template)
        elif button_name == "Build & Run":
            if self.compiler_type.get() == '7800AsmDevKit':
                command_to_run = self.resolve_command(self.global_config.get('Commands', 'dasm_build_cmd'))
            else:
                command_to_run = self.resolve_command(self.global_config.get('Commands', 'cc65_build_cmd'))
        elif button_name == "Run":
            command_to_run = self.resolve_command(self.global_config.get('Commands', 'run_cmd'))
        elif button_name == "Run (Debug)":
            command_to_run = self.resolve_command(self.global_config.get('Commands', 'debug_run_cmd'))
        elif button_name == "Apply Header":
            header_auto = self.global_config.getboolean('Options', 'header_auto_send_command')
            if not self.source_file.get():
                command_to_run = f"{self.global_config.get('Tools', 'header_tool')} %b"
            else:
                if header_auto:
                    tool = self.global_config.get('Tools', 'header_tool')
                    auto_cmds = self.global_config.get('Options', 'header_auto_command', fallback='save').replace(';', ' ')
                    command_to_run = f"Simulating commands for '{os.path.basename(tool)}'..."
                else:
                    tool = self.global_config.get('Tools', 'header_tool')
                    command_to_run = [shlex.quote(tool), shlex.quote(target_file)]
        elif button_name == "Apply Signer":
            command_to_run = self.resolve_command(self.global_config.get('Commands', 'signer_cmd'))
        elif button_name == "Edit":
            command_to_run = self.resolve_command(self.global_config.get('Commands', 'editor_cmd'))
        elif button_name == "Open Folder":
            command_to_run = ["open", os.path.dirname(self.source_file.get())]
        elif button_name == "Clean":
            command_to_run = "Clean operation initiated."
        elif button_name == "Settings":
            command_to_run = ["Open settings window..."]
        elif button_name == "Build & Run(Debug)":
            command_to_run = "Build and run in debug mode initiated."
        
        if isinstance(command_to_run, list):
            display_cmd = ' '.join(shlex.quote(arg) for arg in command_to_run)
        else:
            display_cmd = command_to_run
            
        self._log(f"Command: {display_cmd}", "info")
        
        action(*args, **kwargs)

    #############################################################
    # execute_command
    #
    # The core function for running external processes. It uses
    # subprocess.Popen to launch the command. On non-Windows
    # systems, it uses 'pty' for better terminal emulation. It
    # starts a reader thread to capture output and then starts
    # polling the process to check for completion.
    #############################################################
    def execute_command(self, cmd_list, success_msg, on_success_callback=None, check_output_file=None, input_data=None, cwd=None, is_shell_cmd=False):
        """
        A unified command execution function.
        Handles both interactive and non-interactive commands, routing all output to the GUI.
        """
        if self.command_running:
            self._log("A process is already running. Please wait for it to finish.", "error")
            return False
        
        self.set_command_running_state(True)

        try:
            if sys.platform != "win32":
                self.master_pty, slave_pty = pty.openpty()
                self.process = subprocess.Popen(
                    cmd_list,
                    stdin=slave_pty,
                    stdout=slave_pty,
                    stderr=subprocess.STDOUT,
                    cwd=cwd,
                )
                os.close(slave_pty)
                self.reader_thread = threading.Thread(
                    target=self._read_stream_to_queue,
                    args=(self.master_pty, self.output_queue),
                    daemon=True
                )
            else:
                self.process = subprocess.Popen(
                    cmd_list,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    cwd=cwd,
                    universal_newlines=True,
                    shell=is_shell_cmd,
                    bufsize=1
                )
                self.reader_thread = threading.Thread(
                    target=self._read_stream_to_queue,
                    args=(self.process.stdout.fileno(), self.output_queue),
                    daemon=True
                )

            while not self.output_queue.empty():
                self.output_queue.get()

            self.reader_thread.start()
            
            self.root.after(100, self.poll_process, success_msg, check_output_file, on_success_callback)
            return True

        except FileNotFoundError:
            self._log(f"❌ Command failed: Executable not found.\nIs '{cmd_list[0]}' in your system's PATH or configured correctly in Settings?", "error")
            self.process = None
            self.set_command_running_state(False)
            return False
        except Exception as e:
            self._log(f"❌ An unexpected error occurred: {e}", "error")
            self.process = None
            self.set_command_running_state(False)
            return False

    #############################################################
    # poll_process
    #
    # Periodically checks if the running subprocess has finished.
    # Once the process completes, it logs the exit code and, if
    # successful, triggers an optional callback function for
    # chained commands (e.g., run header after build).
    #############################################################
    def poll_process(self, success_msg, check_output_file, on_success_callback):
        if self.process is None:
            self.set_command_running_state(False)
            return

        if self.process.poll() is None:
            self.root.after(100, self.poll_process, success_msg, check_output_file, on_success_callback)
            return

        return_code = self.process.returncode
        self.process = None
        self.set_command_running_state(False)

        if return_code != 0 and return_code not in [-15, 1]:
            self._log(f"\n--- Process finished with exit code {return_code} ---\n", "error")
        else:
            if check_output_file and not os.path.exists(check_output_file):
                self._log(f"❌ Command ran but did not create the expected expected output file: {os.path.basename(check_output_file)}.", "error")
            else:
                self._log(f"\n--- {success_msg} (Exit Code: {return_code}) ---\n", "success")
                if on_success_callback:
                    self.root.after(10, on_success_callback)

    #############################################################
    # build_rom
    #
    # The main logic for the "Build" action. It determines which
    # compiler to use and sets up a chain of commands. For example,
    # for 7800Asm, it might build and then automatically apply the
    # header. For CC65, it might build, sign, and then apply the
    # header.
    #############################################################
    def build_rom(self, on_final_success=None):
        if not self.source_file.get(): 
            self._log("Error: No source file selected.", "error")
            return

        self._log("Starting build...", "info")
        self.save_global_config()
        project_dir = os.path.dirname(self.source_file.get())

        if self.compiler_type.get() == '7800AsmDevKit':
            next_step = on_final_success
            if self.dasm_auto_header.get():
                next_step = lambda: self.apply_header(on_success_callback=on_final_success)
            self.build_with_7800asm(cwd=project_dir, on_success_callback=next_step)
        elif self.compiler_type.get() == 'CC65':
            next_step_after_build = None
            if self.cc65_auto_signer.get():
                if self.cc65_auto_header.get():
                    next_step_after_build = lambda: self.apply_signer(on_success_callback=lambda: self.apply_header(on_success_callback=on_final_success))
                else:
                    next_step_after_build = lambda: self.apply_signer(on_success_callback=on_final_success)
            elif self.cc65_auto_header.get():
                 next_step_after_build = lambda: self.apply_header(on_success_callback=on_final_success)
            else:
                next_step_after_build = on_final_success
            
            self.build_with_cc65(cwd=project_dir, on_success_callback=next_step_after_build)
        else:
            self._log(f"Error: Unknown compiler selected.", "error")

    #############################################################
    # build_and_run_debug
    #
    # A convenience function for the "Build & Run (Debug)" button.
    # It initiates a build and sets the final success callback to
    # launch the emulator in debug mode.
    #############################################################
    def build_and_run_debug(self):
        """Builds the ROM and then runs the emulator in debug mode."""
        if not self.source_file.get(): 
            self._log("Error: No source file selected.", "error")
            return
        
        self.build_rom(on_final_success=lambda: self.run_emulator(debug=True))

    #############################################################
    # resolve_command
    #
    # Takes a command template string (e.g., "%a %s") and replaces
    # the placeholders (%a, %s, %o, etc.) with their actual values
    # from the application's current state and configuration. It
    # returns a list of arguments suitable for subprocess.Popen.
    #############################################################
    def resolve_command(self, cmd_template, replacements_override=None):
        """Resolves placeholders in a command template string."""
        source = self.source_file.get()
        output = self.output_file.get()

        replacements = {
            '%s': source, 
            '%o': output, 
            '%b': f"{os.path.splitext(source)[0]}.bin",
            '%e': self.global_config.get('Tools', 'editor'), 
            '%a': self.global_config.get('Tools', '7800asm_script'),
            '%c': self.global_config.get('Tools', 'cc65_compiler'), 
            '%h': self.global_config.get('Tools', 'header_tool'),
            '%g': self.global_config.get('Tools', 'signer_tool'), 
            '%m': self.global_config.get('Tools', 'emulator')
        }
        
        if replacements_override:
            replacements.update(replacements_override)

        resolved_cmd = cmd_template
        for placeholder, value in replacements.items():
                if value: resolved_cmd = resolved_cmd.replace(placeholder, shlex.quote(value))
        
        return shlex.split(resolved_cmd)

    #############################################################
    # build_with_7800asm
    #
    # Executes the build process specifically for the 7800asm
    # toolchain. It also handles the renaming of the output file
    # from 'source.s.bin' to 'source.bin'.
    #############################################################
    def build_with_7800asm(self, cwd, on_success_callback=None):
        source = self.source_file.get()
        cmd_template = self.global_config.get('Commands', 'dasm_build_cmd')
        cmd_list = self.resolve_command(cmd_template)
        
        def rename_asm_output():
            try:
                dasm_output = f"{source}.bin"
                final_bin = f"{os.path.splitext(source)[0]}.bin"
                if os.path.exists(final_bin): 
                    os.remove(final_bin)
                if os.path.exists(dasm_output):
                    os.rename(dasm_output, final_bin)
                    self._log("✅ Renamed intermediate file.", "success")
                    self._log(f"Command: os.rename('{dasm_output}', '{final_bin}')", "info")
                if on_success_callback:
                    on_success_callback()
            except (OSError, FileNotFoundError) as e:
                self._log(f"❌ Failed to rename intermediate file: {e}", "error")

        self.execute_command(cmd_list, "Assembly successful!", on_success_callback=rename_asm_output, cwd=cwd)

    #############################################################
    # build_with_cc65
    #
    # Executes the build process for the CC65 toolchain, adding
    # any extra flags for map file creation or debug info.
    #############################################################
    def build_with_cc65(self, cwd, on_success_callback=None):
        cmd_template = self.global_config.get('Commands', 'cc65_build_cmd')
        if self.cc65_create_map.get(): cmd_template += f" -m '{os.path.splitext(self.output_file.get())[0]}.map'"
        if self.cc65_add_debug.get(): cmd_template += ' -g'
        cmd_list = self.resolve_command(cmd_template)
        self.execute_command(cmd_list, "Build successful!", check_output_file=self.output_file.get(), on_success_callback=on_success_callback, cwd=cwd)

    #############################################################
    # apply_header
    #
    # Runs the '7800header' tool. It can operate in two modes:
    # 1. Interactive: Launches the tool and lets the user type
    #    commands into the status window's input bar.
    # 2. Automated: If enabled, it launches the tool and then
    #    starts a separate thread to automatically send a
    #    pre-defined sequence of commands to it.
    #############################################################
    def apply_header(self, on_success_callback=None, from_button=True):
        if not self.source_file.get():
             self._log(f"Error: Header input file not found: <NO SOURCE FILE SELECTED>", "error")
             return

        target_file = f"{os.path.splitext(self.source_file.get())[0]}.bin" if self.compiler_type.get() == '7800AsmDevKit' else self.output_file.get()
        if not os.path.exists(target_file):
            self._log(f"Error: Header input file not found: {os.path.basename(target_file)}", "error")
            return

        self._log("Applying header...", "info")
        project_dir = os.path.dirname(self.source_file.get())
        success_msg = "Header applied successfully!"
        
        if self.global_config.getboolean('Options', 'header_auto_send_command'):
            tool = self.global_config.get('Tools', 'header_tool')
            cmd_list = [shlex.quote(tool), shlex.quote(target_file)]
            is_launched = self.execute_command(cmd_list, success_msg, on_success_callback=on_success_callback, cwd=project_dir)
            
            if is_launched:
                self._log("🚀 Launching automated header tool in a new thread...", "info")
                
                self.automated_header_thread = threading.Thread(
                    target=self._run_automated_header_sequence,
                    daemon=True,
                    args=(on_success_callback,)
                )
                self.automated_header_thread.start()
        else:
            cmd_template = self.global_config.get('Commands', 'header_cmd')
            cmd_list = shlex.split(f"{shlex.quote(self.global_config.get('Tools', 'header_tool'))} {shlex.quote(target_file)}")
            self.execute_command(cmd_list, success_msg, on_success_callback=on_success_callback, cwd=project_dir)

    #############################################################
    # _run_automated_header_sequence
    #
    # This method runs in a dedicated thread to handle the automated
    # sending of commands to the '7800header' tool. It waits for
    # specified delays and then simulates typing and sending each
    # command from the configured command string.
    #############################################################
    def _run_automated_header_sequence(self, on_success_callback):
        """
        New, self-contained method to handle the automated command sequence.
        This runs in a separate thread and simulates user input.
        """
        initial_delay = float(self.global_config.get('Options', 'header_initial_delay', fallback=1.0))
        command_delay = float(self.global_config.get('Options', 'header_command_delay', fallback=0.5))
        commands_string = self.global_config.get('Options', 'header_auto_command', fallback='save')
        commands_list = commands_string.split(';')

        if initial_delay > 0:
            time.sleep(initial_delay)
        
        for command in commands_list:
            command = command.strip()
            if not command:
                continue

            if self.process and self.process.poll() is None:
                self.root.after(10, self._simulate_and_send_typing, command)
                time.sleep(command_delay)
            else:
                self._log("Automated sequence aborted: Process terminated prematurely.", "error")
                return

        if self.process and self.process.poll() is None:
            if sys.platform == "win32":
                self.process.stdin.close()
            
    #############################################################
    # _simulate_and_send_typing
    #
    # A helper function, called from the main UI thread, that
    # simulates a user typing a command into the input entry and
    # pressing Enter. This provides visual feedback during the
    # automated header sequence.
    #############################################################
    def _simulate_and_send_typing(self, command):
        """
        Simulates typing a command into the entry box and sending it.
        This method MUST be called from the main UI thread.
        """
        self.input_entry.delete(0, tk.END)
        
        for char in command:
            self.input_entry.insert(tk.END, char)
            self.root.update_idletasks()
            time.sleep(0.05)
            
        self.send_command()

    #############################################################
    # apply_signer
    #
    # Runs the '7800sign' utility on the output ROM file.
    #############################################################
    def apply_signer(self, on_success_callback=None):
        if not self.output_file.get() or not os.path.exists(self.output_file.get()):
            self._log("Error: Output file not found. Build first.", "error")
            return
        self._log("Applying signer...", "info")
        project_dir = os.path.dirname(self.source_file.get())
        cmd_list = self.resolve_command(self.global_config.get('Commands', 'signer_cmd'))
        self.execute_command(cmd_list, "ROM signed successfully!", cwd=project_dir, on_success_callback=on_success_callback)

    #############################################################
    # on_compiler_selected, on_project_selected
    #
    # Event handlers for UI elements. They trigger updates when
    # the user changes the selected compiler or project.
    #############################################################
    def on_compiler_selected(self, event): 
        self.save_global_config()
        self.update_compiler_options_view()
    
    def on_project_selected(self, event):
        # This function is now effectively unused since the dropdown is removed
        filepath = self.source_file.get()
        if filepath:
            self.set_active_project(filepath)

    #############################################################
    # browse_file, browse_output_file
    #
    # Event handlers for the "Browse..." buttons that open the
    # system file dialogs for selecting source and output files.
    #############################################################
    def browse_file(self):
        home_dir = self.global_config.get('Paths', 'code_home_dir', fallback=None)
        if home_dir and not os.path.isdir(home_dir): home_dir = None
        if path := filedialog.askopenfilename(initialdir=home_dir, filetypes=(("Source Files", "*.c *.s *.asm"),("All files", "*.*"))):
            self.set_active_project(path)

    def browse_output_file(self):
        source = self.source_file.get()
        initial_dir = os.path.dirname(source) if source else os.getcwd()
        if path := filedialog.asksaveasfilename(
            initialdir=initial_dir,
            defaultextension=".a78",
            filetypes=[("Atari 7800 ROM", "*.a78"), ("All files", "*.*")]
        ):
            self.output_file.set(path)

    #############################################################
    # update_project_history
    #
    # Manages the list of recent projects.
    #############################################################
    def update_project_history(self, new_path):
        if new_path in self.project_history: self.project_history.remove(new_path)
        self.project_history.insert(0, new_path)
        self.project_history = self.project_history[:MAX_HISTORY]

    #############################################################
    # open_settings
    #
    # Creates and displays the SettingsWindow.
    #############################################################
    def open_settings(self): SettingsWindow(self.root, self)

    #############################################################
    # update_output
    #
    # Clears and updates the status window with a new message.
    #############################################################
    def update_output(self, message, tag="info"):
        self._clear_log_and_log(message, tag)

    #############################################################
    # edit_file
    #
    # Launches the configured external text editor to open the
    # current source file.
    #############################################################
    def edit_file(self):
        if not self.source_file.get(): 
            self._log("Error: No source file selected.", "error")
            return
        cmd_template = self.global_config.get('Commands', 'editor_cmd')
        
        replacements = {'%s': self.source_file.get(), '%e': self.global_config.get('Tools', 'editor')}
        resolved_cmd = cmd_template
        for p, v in replacements.items(): resolved_cmd = resolved_cmd.replace(p, f"'{v}'")
        try: 
            subprocess.Popen(shlex.split(resolved_cmd))
        except (FileNotFoundError, OSError) as e: 
            self._log(f"Error: Could not run editor command '{resolved_cmd}'.\n{e}", "error")

    #############################################################
    # open_project_folder
    #
    # Opens the directory containing the current source file in
    # the system's default file manager.
    #############################################################
    def open_project_folder(self):
        source = self.source_file.get()
        if not source: 
            self._log("Error: No source file selected.", "error")
            return
        folder = os.path.dirname(source)
        try:
            if sys.platform == "win32": 
                os.startfile(folder)
            elif sys.platform == "darwin": 
                subprocess.Popen(["open", folder])
            else: 
                subprocess.Popen(["xdg-open", folder])
        except (FileNotFoundError, OSError) as e: 
            self._log(f"Error opening folder. {e}", "error")

    #############################################################
    # build_and_run
    #
    # A convenience function for the "Build & Run" button. It
    # initiates a build and sets the final success callback to
    # launch the emulator.
    #############################################################
    def build_and_run(self):
        if not self.source_file.get(): 
            self._log("Error: No source file selected.", "error")
            return
        
        self.build_rom(on_final_success=self.run_emulator)

    #############################################################
    # build_and_run_debug
    #
    # A convenience function for the "Build & Run (Debug)" button.
    # It initiates a build and sets the final success callback to
    # launch the emulator in debug mode.
    #############################################################
    def build_and_run_debug(self):
        """Builds the ROM and then runs the emulator in debug mode."""
        if not self.source_file.get(): 
            self._log("Error: No source file selected.", "error")
            return
        
        self.build_rom(on_final_success=lambda: self.run_emulator(debug=True))

    #############################################################
    # run_emulator
    #
    # Launches the configured external emulator with the current
    # output ROM file. It can pass a debug flag if requested.
    #############################################################
    def run_emulator(self, debug=False):
        rom_path = self.output_file.get()
        if not rom_path or not os.path.exists(rom_path): 
            self._log("Error: ROM file not found. Build first.", "error")
            return
        self._log("Starting emulator...", "info")
        template_key = 'debug_run_cmd' if debug else 'run_cmd'
        project_dir = os.path.dirname(self.source_file.get())
        cmd_list = self.resolve_command(self.global_config.get('Commands', template_key))
        self.execute_command(cmd_list, "Emulator session finished.", cwd=project_dir)

    #############################################################
    # clean_project
    #
    # Deletes generated files from the project directory based on
    # the file extensions selected in the "Clean Options" in the
    # settings. This helps keep the project folder tidy.
    #############################################################
    def clean_project(self):
        """
        Cleans the project directory by removing all generated files.
        """
        source = self.source_file.get()
        if not source: 
            self._log("Error: No source file selected.", "error")
            return False

        self._log("Cleaning project...", "info")

        clean_vars = self.clean_options_vars

        generated_exts = []
        if clean_vars['clean_a78'].get():
            generated_exts.append('.a78')
        if clean_vars['clean_bin'].get():
            generated_exts.append('.bin')
        if clean_vars['clean_list'].get():
            generated_exts.append('.list.txt')
        if clean_vars['clean_symbol'].get():
            generated_exts.append('.symbol.txt')
        if clean_vars['clean_sym'].get():
            generated_exts.append('.sym')
        if clean_vars['clean_lst'].get():
            generated_exts.append('.lst')
        if clean_vars['clean_o'].get():
            generated_exts.append('.o')
        if clean_vars['clean_map'].get():
            generated_exts.append('.map')
        if clean_vars['clean_dbg'].get():
            generated_exts.append('.dbg')
        if clean_vars['clean_backup'].get():
            generated_exts.append('.a78.backup')
            
        files_to_delete = set()
        
        if 'clean_s_list_txt' in clean_vars and clean_vars['clean_s_list_txt'].get():
            files_to_delete.add(source + '.list.txt')
        if 'clean_s_symbol_txt' in clean_vars and clean_vars['clean_s_symbol_txt'].get():
            files_to_delete.add(source + '.symbol.txt')
        
        source_dir = os.path.dirname(source)
        source_base_name = os.path.splitext(os.path.basename(source))[0]
        output = self.output_file.get()
        output_dir = os.path.dirname(output) if output else source_dir
        output_base_name = os.path.splitext(os.path.basename(output))[0] if output else source_base_name
        
        for ext in generated_exts:
            file_path = os.path.join(source_dir, f"{source_base_name}{ext}")
            files_to_delete.add(file_path)

        if output_dir != source_dir:
            for ext in generated_exts:
                file_path = os.path.join(output_dir, f"{output_base_name}{ext}")
                files_to_delete.add(file_path)

        if clean_vars['clean_bin'].get() and source.lower().endswith('.s'):
            file_to_check = os.path.join(source_dir, f"{source_base_name}.bin")
            files_to_delete.add(file_to_check)
        
        if output and clean_vars['clean_a78'].get():
            files_to_delete.add(output)
        
        cleaned_files = []
        for f in files_to_delete:
            if os.path.exists(f) and os.path.isfile(f):
                try:
                    os.remove(f)
                    cleaned_files.append(os.path.basename(f))
                except OSError as e:
                    self._log(f"Error deleting {f}: {e}", "error")
                    return False

        if cleaned_files:
            self._log(f"Cleaned: {', '.join(cleaned_files)}", "success")
        else:
            self._log("No generated files to clean.", "info")

        return True

    #############################################################
    # _check_topmost_change
    #
    # A callback that checks if the "Always on Top" setting has
    # been changed from its initial state and displays a message
    # informing the user that a restart is required.
    #############################################################
    def _check_topmost_change(self, *args):
        if self.topmost_var.get() != self.initial_topmost_state:
            self.restart_label.config(text="App Restart Required")
        else:
            self.restart_label.config(text="")

#################################################################
#
# Main execution block. This is the entry point of the script.
# It initializes the Tkinter root window, creates an instance
# of the main application class, and starts the GUI event loop.
#
#################################################################
if __name__ == "__main__":
    root = tk.Tk()
    app = DevHelperApp(root)
    root.mainloop()

