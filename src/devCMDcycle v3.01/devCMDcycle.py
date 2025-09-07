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
import io
import pprint
import shutil
import glob


# Conditional import for Unix-like systems for better terminal emulation
if sys.platform != "win32":
    import pty

# --- Global Constants ---
CONFIG_FILE_NAME = 'devCMDcycle_301.ini'
APP_VERSION = "3.01"
INI_BACKUP_DIR = "ini_backup"
SCRIPT_BACKUP_DIR = "script_backup"

"""
################################################################################
#
# UNDELETABLE ITEMS & DEFAULT CONFIGURATION
#
# This section defines the core structure of the application's settings.
#
# UNDELETABLE_ITEMS:
# This dictionary contains system-critical items that are essential for the
# application's stability. These items cannot be deleted by the user through
# the UI and are not saved to the user's .ini file. They are merged into the
# configuration at runtime to ensure they are always present.
#
# DEFAULT_CONFIG:
# This dictionary contains all the default settings for the application. It is
# the blueprint for the `devCMDcycle_210.ini` file that is automatically
# created when the program runs for the first time. It serves as a complete
# reference for all configuration options.
#
################################################################################
"""

UNDELETABLE_ITEMS = {
    'AutoTyperProfiles': {
        '-- No Profile Selected --': str(
            {'master_enabled': 'False', **{f'Step {i}': {'name': f'Step {i}', 'column': 1, 'commands': []} for i in range(1, 6)}}
        )
    },
    'Toolchains': {
        '-- Select Toolchain --': {
            'autotyper_profile': '-- No Profile Selected --',
            'build_steps': str([]),
            'custom_buttons': str(
                {f'Button{i}': {'name': '', 'command': '', 'color': '#F0F0F0'} for i in range(1, 11)}
            ),
            'path': '',
            'toolchain_options': str([])
        }
    }
}


DEFAULT_CONFIG = {
    'Actions': {
        'add_header': '%h %s.bin',
        'add_header_a78': '%h %o.a78',
        'compile_cc65': '%t -t atari7800 -o %o.a78 %f',
        'compile_dasm': '%t %f',
        'edit': '%e %f',
        'run': '%m a7800 -cart %o.a78',
        'run_debug': '%m a7800 -cart %o.a78 -debug',
        'sign_rom': '%g %o.a78'
    },
    'AutoTyperProfiles': {
        '-- No Profile Selected --': str(
    {   'master_enabled': 'False',
        'Step 1': {'name': 'Step 1', 'column': 1, 'commands': []},
        'Step 2': {'name': 'Step 2', 'column': 1, 'commands': []},
        'Step 3': {'name': 'Step 3', 'column': 1, 'commands': []},
        'Step 4': {'name': 'Step 4', 'column': 1, 'commands': []},
        'Step 5': {'name': 'Step 5', 'column': 1, 'commands': []}}    ),
        '7800AsmDevKit Header': str(
    {   'master_enabled': 'False',
        'Step 1': {   'name': 'Cartridge & Memory',
                      'column': 1,
                      'commands': [   {'label': 'Button4', 'command': 'set linear', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button4', 'command': 'set supergame', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button4', 'command': 'set souper', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button4', 'command': 'set bankset', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button4', 'command': 'set absolute', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button4', 'command': 'set activision', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button4', 'command': 'set rom@4000', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button4', 'command': 'set bank6@4000', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button4', 'command': 'set ram@4000', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button4', 'command': 'set mram@4000', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button4', 'command': 'set hram@4000', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button4', 'command': 'set bankram', 'enabled': 'False', 'text': ''}]},
        'Step 2': {   'name': 'Hardware & IRQs',
                      'column': 1,
                      'commands': [   {'label': 'Button4', 'command': 'set pokey@440', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button4', 'command': 'set pokey@450', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button4', 'command': 'set pokey@800', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button4', 'command': 'set pokey@4000', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button4', 'command': 'set ym2151@460', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button4', 'command': 'set covox@430', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button4', 'command': 'set adpcm@420', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button4', 'command': 'set irqpokey1', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button4', 'command': 'set irqpokey2', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button4', 'command': 'set irqym2151', 'enabled': 'False', 'text': ''}]},
        'Step 3': {   'name': 'Controllers',
                      'column': 2,
                      'commands': [   {'label': 'Button4', 'command': 'set 7800joy1', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button4', 'command': 'set 7800joy2', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button4', 'command': 'set lightgun1', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button4', 'command': 'set lightgun2', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button4', 'command': 'set paddle1', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button4', 'command': 'set paddle2', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button4', 'command': 'set 2600joy1', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button4', 'command': 'set 2600joy2', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button4', 'command': 'set keypad1', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button4', 'command': 'set keypad2', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button4', 'command': 'set mega78001', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button4', 'command': 'set mega78002', 'enabled': 'False', 'text': ''}]},
        'Step 4': {   'name': 'Misc & TV',
                      'column': 2,
                      'commands': [   {'label': 'Button4', 'command': 'set hsc', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button4', 'command': 'set savekey', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button4', 'command': 'set xm', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button4', 'command': 'set tvpal', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button4', 'command': 'set tvntsc', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button4', 'command': 'set composite', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button4', 'command': 'set mregion', 'enabled': 'False', 'text': ''}]},
        'Step 5': {   'name': 'Final Actions',
                      'column': 3,
                      'commands': [   {'label': 'Button4', 'command': 'name "%b25"', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button4', 'command': 'save', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button4', 'command': 'strip', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button4', 'command': 'fix', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button4', 'command': 'exit', 'enabled': 'False', 'text': ''}]}}    ),
        'cc65 Header': str(
    {   'master_enabled': 'False',
        'Step 1': {   'name': 'Cartridge & Memory',
                      'column': 1,
                      'commands': [   {'label': 'Button5', 'command': 'set linear', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button5', 'command': 'set supergame', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button5', 'command': 'set souper', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button5', 'command': 'set bankset', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button5', 'command': 'set absolute', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button5', 'command': 'set activision', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button5', 'command': 'set rom@4000', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button5', 'command': 'set bank6@4000', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button5', 'command': 'set ram@4000', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button5', 'command': 'set mram@4000', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button5', 'command': 'set hram@4000', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button5', 'command': 'set bankram', 'enabled': 'False', 'text': ''}]},
        'Step 2': {   'name': 'Hardware & IRQs',
                      'column': 1,
                      'commands': [   {'label': 'Button5', 'command': 'set pokey@440', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button5', 'command': 'set pokey@450', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button5', 'command': 'set pokey@800', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button5', 'command': 'set pokey@4000', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button5', 'command': 'set ym2151@460', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button5', 'command': 'set covox@430', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button5', 'command': 'set adpcm@420', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button5', 'command': 'set irqpokey1', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button5', 'command': 'set irqpokey2', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button5', 'command': 'set irqym2151', 'enabled': 'False', 'text': ''}]},
        'Step 3': {   'name': 'Controllers',
                      'column': 2,
                      'commands': [   {'label': 'Button5', 'command': 'set 7800joy1', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button5', 'command': 'set 7800joy2', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button5', 'command': 'set lightgun1', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button5', 'command': 'set lightgun2', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button5', 'command': 'set paddle1', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button5', 'command': 'set paddle2', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button5', 'command': 'set 2600joy1', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button5', 'command': 'set 2600joy2', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button5', 'command': 'set keypad1', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button5', 'command': 'set keypad2', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button5', 'command': 'set mega78001', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button5', 'command': 'set mega78002', 'enabled': 'False', 'text': ''}]},
        'Step 4': {   'name': 'Misc & TV',
                      'column': 2,
                      'commands': [   {'label': 'Button5', 'command': 'set hsc', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button5', 'command': 'set savekey', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button5', 'command': 'set xm', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button5', 'command': 'set tvpal', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button5', 'command': 'set tvntsc', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button5', 'command': 'set composite', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button5', 'command': 'set mregion', 'enabled': 'False', 'text': ''}]},
        'Step 5': {   'name': 'Final Actions',
                      'column': 3,
                      'commands': [   {'label': 'Button5', 'command': 'name "%b25"', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button5', 'command': 'save', 'enabled': 'True', 'text': ''},
                                      {'label': 'Button5', 'command': 'strip', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button5', 'command': 'fix', 'enabled': 'False', 'text': ''},
                                      {'label': 'Button5', 'command': 'exit', 'enabled': 'False', 'text': ''}]}}    )
    },
    'CleanStates': {
        '.a78': 'True',
        '.a78.backup': 'True',
        '.a78.map': 'True',
        '.bin': 'True',
        '.dbg': 'True',
        '.list.txt': 'True',
        '.lst': 'True',
        '.map': 'True',
        '.o': 'True',
        '.s.a78': 'True',
        '.s.a78.backup': 'True',
        '.s.bin': 'True',
        '.s.list.txt': 'True',
        '.s.symbol.txt': 'True',
        '.sym': 'True',
        '.symbol.txt': 'True'
    },
    'DefaultGeometry': {
        'autotyper_profile_editor': '1100x900',
        'main_window': '800x1000',
        'settings_window': '1360x825',
        'toolchain_editor': '1285x853',
        'toolchain_options_editor': '1000x900'
    },
    'Geometry': {
        'autotyper_profile_editor': '1100x900',
        'main_window': '800x1000',
        'settings_window': '1217x825',
        'toolchain_editor': '1285x853',
        'toolchain_options_editor': '1000x900'
    },
    'Options': {
        'active_auto_typer_profile': '-- No Profile Selected --',
        'always_on_top': 'False',
        'clean_extensions': '.a78,.o,.bin,.s.a78,.s.bin,.lst,.list.txt,.s.list.txt,.sym,.symbol.txt,.s.symbol.txt,.map,.a78.map,.dbg,.a78.backup,.s.a78.backup',
        'dark_mode': 'False',
        'header_command_delay': '0.5',
        'header_initial_delay': '1.0'
    },
    'Paths': {
        'editor': 'xed',
        'emulator': 'a7800',
        'header_tool': '7800header',
        'last_source': '',
        'last_toolchain': '-- Select Toolchain --',
        'signer_tool': '7800sign',
        'terminal': 'gnome-terminal'
    },
    'ToolchainStates': {
        '7800ASMDevKit_Generate_List_File': 'False',
        '7800ASMDevKit_Generate_Symbol_File': 'False',
        '7800ASMDevKit_Run_in_debug_mode': 'True',
        '7800ASMDevKit_Run_with_Debug': 'False',
        'cc65_Add_Debug_Info': 'False',
        'cc65_Create_Map_File': 'False',
        'cc65_Run_(debug)': 'True',
        'cc65_Run_in_debug_mode': 'False'
    },
    'Toolchains': {
        '7800ASMDevKit': {
            'autotyper_profile': '7800AsmDevKit Header',
            'build_steps': str(
    ['compile_dasm', 'add_header']    ),
            'custom_buttons': str(
    {   'Button1': {'name': 'Terminal', 'command': 'EXTERNAL:%term', 'color': '#e0e0e0'},
        'Button2': {'name': 'Edit', 'command': 'EXTERNAL:%e %f', 'color': '#e0e0e0'},
        'Button3': {'name': 'Build', 'command': '%t %f', 'color': '#add8e6'},
        'Button4': {'name': 'Header', 'command': '%h %s.s.bin', 'color': '#add8e6'},
        'Button5': {'name': 'Build>Header', 'command': 'Button3,Button4', 'color': '#c1a9c3'},
        'Button6': {'name': 'Run', 'command': 'EXTERNAL:%m a7800 -cart %s.s.a78', 'color': '#90ee90'},
        'Button7': {'name': 'Build>Header>Run', 'command': 'Button3,Button4,Button6', 'color': '#c1a9c3'},
        'Button8': {'name': '', 'command': '', 'color': '#e0e0e0'},
        'Button9': {'name': '', 'command': '', 'color': '#e0e0e0'},
        'Button10': {'name': '', 'command': '', 'color': '#F0F0F0'}}    ),
            'path': '7800asm',
            'toolchain_options': str(
    [   {'name': 'Generate List File', 'flag': '-l', 'target': 'Button3'},
        {'name': 'Generate Symbol File', 'flag': '-s', 'target': 'Button3'},
        {'name': 'Run in debug mode', 'flag': '-debug', 'target': 'Button6'}]    )
        },
        'cc65': {
            'autotyper_profile': 'cc65 Header',
            'build_steps': str(
    ['compile_cc65', 'sign_rom', 'add_header_a78']    ),
            'custom_buttons': str(
    {   'Button1': {'name': 'Terminal', 'command': 'EXTERNAL:%term', 'color': '#e0e0e0'},
        'Button2': {'name': 'Edit', 'command': 'EXTERNAL:%e %f', 'color': '#e0e0e0'},
        'Button3': {'name': 'Build', 'command': '%t -t atari7800 -o %s.bin %f', 'color': '#add8e6'},
        'Button4': {'name': 'Sign', 'command': '%g %s.bin', 'color': '#add8e6'},
        'Button5': {'name': 'Header', 'command': '%h %s.bin', 'color': '#add8e6'},
        'Button6': {'name': 'Run', 'command': 'EXTERNAL:%m a7800 -cart %s.a78', 'color': '#90ee90'},
        'Button7': {'name': 'Build>Sign>Header', 'command': 'Button3,Button4,Button5', 'color': '#c3a9c3'},
        'Button8': {'name': '', 'command': '', 'color': '#e0e0e0'},
        'Button9': {'name': 'Build>Sign>Header>Run', 'command': 'Button3,Button4,Button5,Button6', 'color': '#c1a9c3'},
        'Button10': {'name': '', 'command': '', 'color': '#e0e0e0'}}    ),
            'path': 'cl65',
            'toolchain_options': str(
    [   {'name': 'Create Map File', 'flag': '-m %s.map', 'target': 'Button3'},
        {'name': 'Add Debug Info', 'flag': '-g', 'target': 'Button3'},
        {'name': 'Run in debug mode', 'flag': '-debug', 'target': 'Button6'}]    )
        }
    }
}

# --- Helper Classes ---

# --- Integrated Dialog Classes from Converter ---
class CustomDialog(tk.Toplevel):
    """Base class for custom dialogs to handle centering and styling."""
    def __init__(self, parent, title):
        super().__init__(parent)
        self.title(title)
        self.transient(parent)
        self.grab_set()
        self.withdraw() # Hide until ready to show

    def center_and_show(self, parent):
        self.update_idletasks()
        parent_x, parent_y = parent.winfo_x(), parent.winfo_y()
        parent_w, parent_h = parent.winfo_width(), parent.winfo_height()
        dialog_w, dialog_h = self.winfo_width(), self.winfo_height()
        x = parent_x + (parent_w // 2) - (dialog_w // 2)
        y = parent_y + (parent_h // 2) - (dialog_h // 2)
        self.geometry(f"+{x}+{y}")

        self.attributes('-topmost', True)
        self.deiconify()
        self.lift()
        self.focus_force()

        self.wait_window(self)

    def destroy(self):
        self.attributes('-topmost', False)
        super().destroy()

class ConfirmationDialog(CustomDialog):
    """A custom modal dialog for confirming actions."""
    def __init__(self, parent, title, message):
        super().__init__(parent, title)
        self.result = False
        
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill="both", expand=True)
        message_label = ttk.Label(main_frame, text=message, wraplength=450, justify='left')
        message_label.pack(pady=(0, 20))
        button_frame = ttk.Frame(main_frame); button_frame.pack(fill="x")
        button_frame.columnconfigure(0, weight=1); button_frame.columnconfigure(1, weight=1)
        
        proceed_button = ttk.Button(button_frame, text="Proceed", command=self.on_proceed, style="Accent.TButton")
        proceed_button.grid(row=0, column=0, padx=5, sticky='e')
        cancel_button = ttk.Button(button_frame, text="Cancel", command=self.on_cancel)
        cancel_button.grid(row=0, column=1, padx=5, sticky='w')
        
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.center_and_show(parent)

    def on_proceed(self): self.result = True; self.destroy()
    def on_cancel(self): self.result = False; self.destroy()

class InfoDialog(CustomDialog):
    """A custom modal dialog for showing information or errors."""
    def __init__(self, parent, title, message):
        super().__init__(parent, title)
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill="both", expand=True)
        message_label = ttk.Label(main_frame, text=message, wraplength=450, justify='left')
        message_label.pack(pady=(0, 20))
        button_frame = ttk.Frame(main_frame); button_frame.pack()
        ok_button = ttk.Button(button_frame, text="OK", command=self.destroy, style="Accent.TButton")
        ok_button.pack()
        
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.center_and_show(parent)

class RollbackDialog(CustomDialog):
    """A custom dialog for choosing a rollback action."""
    def __init__(self, parent, title, message):
        super().__init__(parent, title)
        self.result = None
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill="both", expand=True)
        message_label = ttk.Label(main_frame, text=message, wraplength=450, justify='left')
        message_label.pack(pady=(0, 20))
        button_frame = ttk.Frame(main_frame); button_frame.pack(fill="x")
        
        restore_button = ttk.Button(button_frame, text="Restore Latest", command=self.on_restore, style="Accent.TButton")
        restore_button.pack(side="left", expand=True, padx=5)
        choose_button = ttk.Button(button_frame, text="Choose File", command=self.on_choose)
        choose_button.pack(side="left", expand=True, padx=5)
        cancel_button = ttk.Button(button_frame, text="Cancel", command=self.on_cancel)
        cancel_button.pack(side="left", expand=True, padx=5)
        
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.center_and_show(parent)

    def on_restore(self): self.result = "latest"; self.destroy()
    def on_choose(self): self.result = "choose"; self.destroy()
    def on_cancel(self): self.result = None; self.destroy()


class UpdateSuccessDialog(CustomDialog):
    """A custom dialog for choosing what to do after a successful DEFAULT_CONFIG update."""
    def __init__(self, parent, title, message):
        super().__init__(parent, title)
        self.result = "continue"  # Default action if window is closed

        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill="both", expand=True)
        message_label = ttk.Label(main_frame, text=message, wraplength=450, justify='left')
        message_label.pack(pady=(0, 20))

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=5)
        
        continue_button = ttk.Button(button_frame, text="Continue Using Current INI", command=self.on_continue)
        continue_button.pack(side="left", expand=True, padx=5)

        reset_button = ttk.Button(button_frame, text="Backup INI & Use New Defaults", command=self.on_reset, style="Accent.TButton")
        reset_button.pack(side="right", expand=True, padx=5)
        
        self.protocol("WM_DELETE_WINDOW", self.on_continue)
        self.center_and_show(parent)

    def on_continue(self):
        self.result = "continue"
        self.destroy()

    def on_reset(self):
        self.result = "reset"
        self.destroy()


class AnsiColorHandler:
    """Processes ANSI color codes for display in a Tkinter Text widget."""
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.ansi_escape = re.compile(r'\x1B\[([0-9;?]*)m')
        self.light_map = {'30': 'black', '31': 'red', '32': 'green', '33': 'yellow', '34': 'blue', '35': 'magenta', '36': 'cyan', '37': 'white'}
        self.setup_tags()

    def setup_tags(self):
        for code, color in self.light_map.items():
            self.text_widget.tag_configure(f"ansi_{color}", foreground=color)
        try:
            bold_font = tkfont.Font(self.text_widget, self.text_widget.cget("font"))
            bold_font.configure(weight="bold")
            self.text_widget.tag_configure("ansi_bold", font=bold_font)
        except tk.TclError:
            pass

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

class AutoTyperProfileEditor(tk.Toplevel):
    """A Toplevel window for creating and managing Auto-Typer profiles."""
    def __init__(self, parent, app_controller, on_close_callback):
        super().__init__(parent)
        self.transient(parent)
        self.grab_set()
        self.title("Auto-Typer Profile Editor")
        self.app = app_controller
        self.on_close_callback = on_close_callback
        self.command_rows = defaultdict(list)
        self.tab_name_vars = {}
        self.tab_column_vars = {}

        saved_geom = self.app.config.get('Geometry', {}).get('autotyper_profile_editor')
        if not saved_geom or saved_geom == '':
            saved_geom = self.app.config.get('DefaultGeometry', {}).get('autotyper_profile_editor', '1100x700')
        self.geometry(saved_geom)

        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill='both', expand=True)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        self.create_top_bar(main_frame)
        self.create_editor_area(main_frame)
        
        self.populate_profile_list()
        self.load_profile_data()
        
        self.protocol("WM_DELETE_WINDOW", self.save_and_close)

    def create_top_bar(self, parent):
        frame = ttk.LabelFrame(parent, text="Profile Management", padding=10)
        frame.grid(row=0, column=0, sticky='ew', pady=(0, 10))
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Select Profile:").grid(row=0, column=0, sticky='w')
        self.profile_var = tk.StringVar()
        self.profile_combo = ttk.Combobox(frame, textvariable=self.profile_var, state='readonly')
        self.profile_combo.grid(row=0, column=1, sticky='ew', padx=5)
        self.profile_combo.bind("<<ComboboxSelected>>", self.load_profile_data)

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=0, column=2)
        ttk.Button(button_frame, text="Add New", command=self.add_new_profile).pack(side='left', padx=2)
        ttk.Button(button_frame, text="Copy", command=self.copy_profile).pack(side='left', padx=2)
        ttk.Button(button_frame, text="Rename", command=self.rename_profile).pack(side='left', padx=2)
        ttk.Button(button_frame, text="Delete", command=self.delete_profile, style="Danger.TButton").pack(side='left', padx=2)

    def create_editor_area(self, parent):
        container = ttk.Frame(parent)
        container.grid(row=1, column=0, sticky='nsew')
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)

        # --- Left Side: Notebook ---
        left_side = ttk.Frame(container)
        left_side.grid(row=0, column=0, sticky='nsew')
        left_side.rowconfigure(0, weight=1)
        left_side.columnconfigure(0, weight=1)

        self.notebook = ttk.Notebook(left_side)
        self.notebook.pack(fill='both', expand=True)
        self.tab_frames = {}

        for i in range(1, 6):
            tab_key = f'Step {i}'
            tab_container = ttk.Frame(self.notebook, padding=10)
            self.notebook.add(tab_container, text=tab_key)
            self.tab_frames[tab_key] = self.create_tab_content(tab_container, tab_key)
        
        # --- Bottom Buttons ---
        button_frame = ttk.Frame(left_side)
        button_frame.pack(fill='x', pady=(10,0))
        ttk.Button(button_frame, text="Save & Close", command=self.save_and_close, style="Save.TButton").pack(side='right')

        # --- Right Side: Legend ---
        self.create_legend(container)

    def create_tab_content(self, parent, tab_key):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(2, weight=1)

        # --- Tab Name and Column ---
        top_frame = ttk.Frame(parent)
        top_frame.grid(row=0, column=0, sticky='ew', pady=(0, 10))
        top_frame.columnconfigure(1, weight=1)
        
        ttk.Label(top_frame, text="Step Name:").grid(row=0, column=0, sticky='w')
        self.tab_name_vars[tab_key] = tk.StringVar()
        name_entry = ttk.Entry(top_frame, textvariable=self.tab_name_vars[tab_key])
        name_entry.grid(row=0, column=1, sticky='ew', padx=(5,10))
        name_entry.bind("<FocusOut>", self.save_profile_data)

        ttk.Label(top_frame, text="Display Column:").grid(row=0, column=2, sticky='w')
        self.tab_column_vars[tab_key] = tk.IntVar(value=1)
        col_combo = ttk.Combobox(top_frame, textvariable=self.tab_column_vars[tab_key], values=[1, 2, 3], state='readonly', width=5)
        col_combo.grid(row=0, column=3, sticky='w', padx=5)
        col_combo.bind("<<ComboboxSelected>>", self.save_profile_data)

        # --- Scrollable Command List ---
        cmd_container = ttk.LabelFrame(parent, text="Commands (execute top to bottom)", padding=10)
        cmd_container.grid(row=2, column=0, sticky='nsew')
        cmd_container.rowconfigure(0, weight=1)
        cmd_container.columnconfigure(0, weight=1)

        canvas = tk.Canvas(cmd_container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(cmd_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # --- Add Command Button ---
        ttk.Button(parent, text="Add New Command", command=lambda k=tab_key, f=scrollable_frame: self.add_command_row(k, f)).grid(row=3, column=0, sticky='w', pady=(10,0))
        
        return scrollable_frame

    def create_legend(self, parent):
        frame = ttk.LabelFrame(parent, text="Placeholders", padding=10)
        frame.grid(row=0, column=1, sticky='nsw', padx=(10,0))
        legend = {
            '%C<key>': 'CTRL+key (e.g., %C<c>)',
            '%A<key>': 'ALT+key (e.g., %A<f>)',
            '%b<num>': 'User text input box'
        }
        for i, (key, desc) in enumerate(legend.items()):
            ttk.Label(frame, text=f"{key}:", font=('Helvetica', 10, 'bold')).grid(row=i, column=0, sticky='e', pady=1)
            ttk.Label(frame, text=desc).grid(row=i, column=1, sticky='w', padx=5)

    def add_command_row(self, tab_key, parent_frame, data=None):
        if data is None: data = {'label': 'Button1', 'command': '', 'enabled': 'False', 'text': ''}
        
        row_frame = ttk.Frame(parent_frame, padding=(0, 3))
        row_frame.pack(fill='x', expand=True)
        row_frame.columnconfigure(2, weight=1) # Label
        row_frame.columnconfigure(4, weight=1) # Command

        label_var = tk.StringVar(value=data.get('label', 'Button1'))
        cmd_var = tk.StringVar(value=data.get('command', ''))
        
        # --- Get current button names for the dropdown ---
        toolchain_name = self.app.toolchain_type.get()
        toolchain_data = self.app.config.get('Toolchains', {}).get(toolchain_name, {})
        try:
            buttons_data = ast.literal_eval(toolchain_data.get('custom_buttons', '{}'))
        except (ValueError, SyntaxError):
            buttons_data = {}
        
        self.button_display_map = {
            (buttons_data.get(f'Button{i}', {}).get('name') or f'Button{i}'): f'Button{i}'
            for i in range(1, 11)
        }
        self.button_key_map = {v: k for k, v in self.button_display_map.items()}

        def on_label_select(*args):
            display_name = label_display_var.get()
            actual_key = self.button_display_map.get(display_name)
            if actual_key:
                label_var.set(actual_key)
            self.save_profile_data()

        label_display_var = tk.StringVar()
        initial_key = label_var.get()
        initial_display = self.button_key_map.get(initial_key, initial_key)
        label_display_var.set(initial_display)
        
        label_combo = ttk.Combobox(row_frame, textvariable=label_display_var, values=sorted(list(self.button_display_map.keys())), state='readonly', width=15)
        cmd_entry = ttk.Entry(row_frame, textvariable=cmd_var)
        
        label_display_var.trace_add('write', on_label_select)
        cmd_entry.bind("<FocusOut>", self.save_profile_data)

        ttk.Label(row_frame, text="Label Button:").grid(row=0, column=1, padx=(0, 2))
        label_combo.grid(row=0, column=2, sticky='ew')
        ttk.Label(row_frame, text="Command:").grid(row=0, column=3, padx=(10, 2))
        cmd_entry.grid(row=0, column=4, sticky='ew')

        btn_frame = ttk.Frame(row_frame)
        btn_frame.grid(row=0, column=0, padx=(0, 10))
        ttk.Button(btn_frame, text="▲", width=2, command=lambda f=row_frame, k=tab_key: self.move_row(f, k, -1)).pack(side='left')
        ttk.Button(btn_frame, text="▼", width=2, command=lambda f=row_frame, k=tab_key: self.move_row(f, k, 1)).pack(side='left')
        ttk.Button(btn_frame, text="X", width=2, style="Danger.TButton", command=lambda f=row_frame, k=tab_key: self.delete_row(f, k)).pack(side='left', padx=(5,0))
        
        self.command_rows[tab_key].append({'frame': row_frame, 'vars': {'label': label_var, 'command': cmd_var}})

    def populate_profile_list(self):
        # Filter out undeletable items from the list shown to the user
        undeletable = UNDELETABLE_ITEMS.get('AutoTyperProfiles', {}).keys()
        user_profiles = self.app.config.get('AutoTyperProfiles', {})
        profiles = sorted([p for p in user_profiles.keys() if p not in undeletable])
        
        self.profile_combo['values'] = profiles
        current = self.app.config['Options'].get('active_auto_typer_profile')
        if current in profiles:
            self.profile_var.set(current)
        elif profiles:
            self.profile_var.set(profiles[0])
        else:
            self.profile_var.set("") # Clear if no user profiles exist

    def load_profile_data(self, *args):
        # Clear existing UI
        for key in self.command_rows:
            for row in self.command_rows[key]:
                row['frame'].destroy()
            self.command_rows[key].clear()

        profile_name = self.profile_var.get()
        if not profile_name: return

        try:
            profile_str = self.app.config.get('AutoTyperProfiles', {}).get(profile_name, '{}')
            profile_data = ast.literal_eval(profile_str)
        except (ValueError, SyntaxError):
            profile_data = {}

        for tab_key, tab_frame in self.tab_frames.items():
            data = profile_data.get(tab_key, {})
            self.tab_name_vars[tab_key].set(data.get('name', tab_key))
            self.tab_column_vars[tab_key].set(data.get('column', 1))
            for cmd_item in data.get('commands', []):
                self.add_command_row(tab_key, tab_frame, cmd_item)

    def save_profile_data(self, *args):
        profile_name = self.profile_var.get()
        if not profile_name: return

        try:
            current_profile_str = self.app.config.get('AutoTyperProfiles', {}).get(profile_name, '{}')
            current_profile_data = ast.literal_eval(current_profile_str)
        except (ValueError, SyntaxError):
            current_profile_data = {}
            
        master_enabled_state = current_profile_data.get('master_enabled', 'False')

        new_profile_data = {'master_enabled': master_enabled_state}
        for tab_key, rows in self.command_rows.items():
            old_commands = current_profile_data.get(tab_key, {}).get('commands', [])
            
            new_commands = []
            for i, r in enumerate(rows):
                new_cmd = {
                    'label': r['vars']['label'].get(), 
                    'command': r['vars']['command'].get()
                }
                if i < len(old_commands):
                    new_cmd['enabled'] = old_commands[i].get('enabled', 'False')
                    new_cmd['text'] = old_commands[i].get('text', '')
                else: # New command
                    new_cmd['enabled'] = 'False'
                    new_cmd['text'] = ''
                new_commands.append(new_cmd)

            new_profile_data[tab_key] = {
                'name': self.tab_name_vars[tab_key].get(),
                'column': self.tab_column_vars[tab_key].get(),
                'commands': new_commands
            }
        
        self.app.config['AutoTyperProfiles'][profile_name] = str(new_profile_data)
        self.app.save_config() # Save immediately

    def add_new_profile(self):
        new_name = simpledialog.askstring("New Profile", "Enter a name for the new profile:", parent=self)
        if not new_name or not new_name.strip(): return
        new_name = new_name.strip()
        
        if new_name in UNDELETABLE_ITEMS.get('AutoTyperProfiles', {}):
             messagebox.showerror("Error", f"'{new_name}' is a reserved name.", parent=self)
             return

        if new_name in self.app.config['AutoTyperProfiles']:
            messagebox.showerror("Error", f"Profile '{new_name}' already exists.", parent=self)
            return

        blank_profile = {'master_enabled': 'False', **{f'Step {i}': {'name': f'Step {i}', 'column': 1, 'commands': []} for i in range(1, 6)}}
        self.app.config['AutoTyperProfiles'][new_name] = str(blank_profile)
        self.app.save_config()
        self.populate_profile_list()
        self.profile_var.set(new_name)
        self.load_profile_data()

    def copy_profile(self):
        old_name = self.profile_var.get()
        if not old_name:
            messagebox.showerror("Error", "No profile selected to copy.", parent=self)
            return

        if old_name in UNDELETABLE_ITEMS.get('AutoTyperProfiles', {}):
            messagebox.showerror("Error", "Cannot copy a reserved profile.", parent=self)
            return

        while True:
            new_name = simpledialog.askstring("Copy Profile", "Enter a new name for the copied profile:", parent=self)

            if new_name is None:  # User cancelled
                break

            new_name = new_name.strip()
            if not new_name:
                messagebox.showerror("Error", "Name cannot be empty.", parent=self)
                continue

            if new_name == old_name:
                messagebox.showerror("Error", "Name must not match the existing profile.", parent=self)
                continue
            
            if new_name in self.app.config['AutoTyperProfiles']:
                messagebox.showerror("Error", f"Profile '{new_name}' already exists.", parent=self)
                continue

            if new_name in UNDELETABLE_ITEMS.get('AutoTyperProfiles', {}):
                messagebox.showerror("Error", f"'{new_name}' is a reserved name.", parent=self)
                continue

            # If all checks pass, copy the profile
            profile_data_to_copy = self.app.config['AutoTyperProfiles'][old_name]
            self.app.config['AutoTyperProfiles'][new_name] = profile_data_to_copy
            self.app.save_config()
            
            self.populate_profile_list()
            self.profile_var.set(new_name)
            self.load_profile_data()
            break

    def rename_profile(self):
        old_name = self.profile_var.get()
        if not old_name: return
        
        if old_name in UNDELETABLE_ITEMS.get('AutoTyperProfiles', {}):
            messagebox.showerror("Error", "Cannot rename a reserved profile.", parent=self)
            return
        
        new_name = simpledialog.askstring("Rename Profile", f"Enter new name for '{old_name}':", initialvalue=old_name, parent=self)
        if not new_name or not new_name.strip() or new_name == old_name: return
        new_name = new_name.strip()

        if new_name in self.app.config['AutoTyperProfiles']:
            messagebox.showerror("Error", f"Profile '{new_name}' already exists.", parent=self)
            return
        
        if new_name in UNDELETABLE_ITEMS.get('AutoTyperProfiles', {}):
            messagebox.showerror("Error", f"'{new_name}' is a reserved name.", parent=self)
            return

        profile_data = self.app.config['AutoTyperProfiles'].pop(old_name)
        self.app.config['AutoTyperProfiles'][new_name] = profile_data

        if self.app.config.get('Options', {}).get('active_auto_typer_profile') == old_name:
            self.app.config['Options']['active_auto_typer_profile'] = new_name

        for toolchain_key, toolchain_data in self.app.config.get('Toolchains', {}).items():
            if toolchain_data.get('autotyper_profile') == old_name:
                self.app.config['Toolchains'][toolchain_key]['autotyper_profile'] = new_name
                
        self.app.save_config()
        
        self.populate_profile_list()
        self.profile_var.set(new_name)

    def delete_profile(self):
        profile_name = self.profile_var.get()
        if not profile_name: return
        
        if profile_name in UNDELETABLE_ITEMS.get('AutoTyperProfiles', {}):
            messagebox.showerror("Error", "Cannot delete a reserved profile.", parent=self)
            return

        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete profile '{profile_name}'?", parent=self):
            if profile_name in self.app.config['AutoTyperProfiles']:
                del self.app.config['AutoTyperProfiles'][profile_name]

            if self.app.config.get('Options', {}).get('active_auto_typer_profile') == profile_name:
                self.app.config['Options']['active_auto_typer_profile'] = '-- No Profile Selected --'

            for toolchain_key in list(self.app.config.get('Toolchains', {}).keys()):
                if self.app.config['Toolchains'][toolchain_key].get('autotyper_profile') == profile_name:
                    self.app.config['Toolchains'][toolchain_key]['autotyper_profile'] = '-- No Profile Selected --'
            
            self.app.save_config()

            self.populate_profile_list()
            self.profile_var.set(self.profile_combo['values'][0] if self.profile_combo['values'] else '')
            self.load_profile_data()

    def delete_row(self, row_frame, tab_key):
        row_to_delete = next((r for r in self.command_rows[tab_key] if r['frame'] == row_frame), None)
        if row_to_delete:
            row_to_delete['frame'].destroy()
            self.command_rows[tab_key].remove(row_to_delete)
            self.save_profile_data()

    def move_row(self, row_frame, tab_key, direction):
        rows = self.command_rows[tab_key]
        idx = next((i for i, r in enumerate(rows) if r['frame'] == row_frame), -1)
        
        if idx == -1: return
        new_idx = idx + direction
        if not (0 <= new_idx < len(rows)): return

        rows[idx], rows[new_idx] = rows[new_idx], rows[idx]
        
        for r in rows: r['frame'].pack_forget()
        for r in rows: r['frame'].pack(fill='x', expand=True)
        self.save_profile_data()

    def save_and_close(self):
        self.save_profile_data()
        self.app.config['Geometry']['autotyper_profile_editor'] = self.geometry()
        self.app.save_config()
        if self.on_close_callback:
            self.on_close_callback()
        self.destroy()

class SettingsWindow(tk.Toplevel):
    """A Toplevel window for managing all global settings."""
    def __init__(self, parent, app_controller, on_close_callback):
        super().__init__(parent)
        self.transient(parent)
        self.title("Global Settings")
        self.app = app_controller
        self.on_close_callback = on_close_callback
        
        saved_geom = self.app.config.get('Geometry', {}).get('settings_window')
        if not saved_geom or saved_geom == '':
            saved_geom = self.app.config.get('DefaultGeometry', {}).get('settings_window', '900x700')
        self.geometry(saved_geom)

        self.vars = {}
        self.clean_vars = {}
        self.autotyper_state_vars = {} 
        self.master_switch_var = tk.BooleanVar()
        
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill="both", expand=True)
        main_frame.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1) 

        # --- Left Column ---
        left_col = ttk.Frame(main_frame)
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        paths_frame = self.create_paths_frame(left_col)
        paths_frame.pack(fill='x', pady=5)
        
        ttk.Button(left_col, text="Edit Toolchains", command=self.open_toolchain_editor).pack(fill='x', pady=10)
        ttk.Button(left_col, text="Manage Auto-Typer Profiles", command=self.open_auto_typer_editor).pack(fill='x', pady=5)
        ttk.Button(left_col, text="Edit Default Config", command=self.open_config_editor).pack(fill='x', pady=5)
        ttk.Button(left_col, text="Reset to Default Config", command=self.reset_config_to_defaults, style="Danger.TButton").pack(fill='x', pady=5)


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
        ttk.Button(button_frame, text="Save & Close", command=self.save_and_close, style="Save.TButton").pack()
        
        self.protocol("WM_DELETE_WINDOW", self.save_and_close)
        self.load_settings_into_ui()

    def create_paths_frame(self, parent):
        frame = ttk.LabelFrame(parent, text="Paths to Tools", padding=10)
        frame.columnconfigure(1, weight=1)
        paths = self.app.get_default_config()['Paths'].keys()
        for i, key in enumerate(p for p in paths if not p.startswith('last_')):
            ttk.Label(frame, text=f"{key.replace('_', ' ').title()}:").grid(row=i, column=0, sticky='w', pady=2)
            self.vars[key] = tk.StringVar(name=f"settings_path_{key}")
            entry = ttk.Entry(frame, textvariable=self.vars[key])
            entry.grid(row=i, column=1, sticky='ew', padx=5)
            entry.bind("<FocusOut>", lambda e, k=key: self._on_path_var_change(k))
            ttk.Button(frame, text="...", width=3, command=lambda v=self.vars[key]: self.browse_file(v)).grid(row=i, column=2)
        return frame

    def create_header_settings(self, parent):
        frame = ttk.LabelFrame(parent, text="Auto-Typer Settings", padding=10)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        profile_frame = ttk.Frame(frame)
        profile_frame.grid(row=0, column=0, sticky='ew', pady=(0, 10))
        profile_frame.columnconfigure(1, weight=1)
        ttk.Label(profile_frame, text="Active Profile:").grid(row=0, column=0, padx=(0, 5))
        self.vars['active_auto_typer_profile'] = tk.StringVar()
        self.profile_combo = ttk.Combobox(profile_frame, textvariable=self.vars['active_auto_typer_profile'], state='readonly')
        self.profile_combo.grid(row=0, column=1, sticky='ew')
        self.profile_combo.bind("<<ComboboxSelected>>", self.rebuild_dynamic_autotyper_ui)
        
        container = ttk.Frame(frame)
        container.grid(row=1, column=0, sticky='nsew')
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)
        
        canvas = tk.Canvas(container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.dynamic_autotyper_frame = ttk.Frame(canvas, padding=5)
        self.dynamic_autotyper_frame.columnconfigure(0, weight=1)
        self.dynamic_autotyper_frame.columnconfigure(1, weight=1)
        self.dynamic_autotyper_frame.columnconfigure(2, weight=1)


        self.dynamic_autotyper_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.dynamic_autotyper_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        controls_frame = ttk.Frame(frame)
        controls_frame.grid(row=2, column=0, sticky='ew', pady=(10, 0))

        ttk.Label(controls_frame, text="Initial Delay (s):").grid(row=0, column=0, sticky='w')
        self.vars['header_initial_delay'] = tk.StringVar(name='settings_header_initial_delay')
        self.vars['header_initial_delay'].trace_add('write', lambda *a, k='header_initial_delay': self._on_option_var_change(k, *a))
        ttk.Entry(controls_frame, textvariable=self.vars['header_initial_delay'], width=5).grid(row=0, column=1, sticky='w')

        ttk.Label(controls_frame, text="Command Delay (s):").grid(row=1, column=0, sticky='w', pady=(2,0))
        self.vars['header_command_delay'] = tk.StringVar(name='settings_header_command_delay')
        self.vars['header_command_delay'].trace_add('write', lambda *a, k='header_command_delay': self._on_option_var_change(k, *a))
        ttk.Entry(controls_frame, textvariable=self.vars['header_command_delay'], width=5).grid(row=1, column=1, sticky='w', pady=(2,0))
        
        self.master_switch_var.trace_add('write', self._on_master_switch_change)
        cb = ttk.Checkbutton(controls_frame, text="Enable Auto-Typer (Master Switch)", variable=self.master_switch_var)
        cb.grid(row=2, column=0, columnspan=2, sticky='w', pady=(10,0))
        return frame

    def rebuild_dynamic_autotyper_ui(self, *args):
        for widget in self.dynamic_autotyper_frame.winfo_children():
            widget.destroy()
        self.autotyper_state_vars.clear()

        new_profile = self.vars['active_auto_typer_profile'].get()
        if not new_profile: return
        
        self.app.config['Options']['active_auto_typer_profile'] = new_profile
        
        current_toolchain = self.app.toolchain_type.get()
        if current_toolchain and current_toolchain not in UNDELETABLE_ITEMS.get('Toolchains', {}):
            self.app.config['Toolchains'][current_toolchain]['autotyper_profile'] = new_profile
            
        self.app.save_config()

        try:
            profile_data_str = self.app.config.get('AutoTyperProfiles', {}).get(new_profile, '{}')
            profile_data = ast.literal_eval(profile_data_str)
        except (ValueError, SyntaxError):
            profile_data = {}
            
        is_master_enabled = profile_data.get('master_enabled', 'False').lower() == 'true'
        self.master_switch_var.set(is_master_enabled)

        columns = [ttk.Frame(self.dynamic_autotyper_frame) for _ in range(3)]
        for i, col in enumerate(columns):
            col.grid(row=0, column=i, sticky='new', padx=(0, 10) if i < 2 else 0)
        
        steps_by_column = defaultdict(list)
        for step_key, step_data in sorted(profile_data.items()):
            if not isinstance(step_data, dict): continue
            steps_by_column[step_data.get('column', 1)].append((step_key, step_data))

        toolchain_name = self.app.toolchain_type.get()
        toolchain_data = self.app.config.get('Toolchains', {}).get(toolchain_name, {})
        try:
            buttons_data = ast.literal_eval(toolchain_data.get('custom_buttons', '{}'))
        except (ValueError, SyntaxError):
            buttons_data = {}

        for col_num, steps in sorted(steps_by_column.items()):
            parent_col = columns[col_num - 1]
            for step_key, step in steps:
                if not step.get('commands'): continue

                step_frame = ttk.LabelFrame(parent_col, text=step.get('name', step_key), padding=5)
                step_frame.pack(fill='x', expand=True, pady=(0, 10))
                
                for j, command_item in enumerate(step.get('commands', [])):
                    label_key = command_item.get('label', 'Button1')
                    command_str = command_item.get('command', '')
                    label_button_name = buttons_data.get(label_key, {}).get('name', label_key) or label_key

                    row_frame = ttk.Frame(step_frame); row_frame.pack(fill='x', pady=1)

                    is_enabled = command_item.get('enabled', 'False').lower() == 'true'
                    check_var = tk.BooleanVar(value=is_enabled)
                    ttk.Checkbutton(row_frame, variable=check_var).pack(side='left')
                    
                    key = (new_profile, step_key, j)
                    match = re.search(r'%b(\d+)', command_str)
                    if match:
                        text_var = tk.StringVar(value=command_item.get('text', ''))
                        
                        label_entry_frame = ttk.Frame(row_frame)
                        label_entry_frame.pack(side='left', fill='x', expand=True, padx=(5,0))
                        ttk.Label(label_entry_frame, text=f"{label_button_name}:").pack(side='left', padx=(0, 5))
                        ttk.Entry(label_entry_frame, textvariable=text_var, width=int(match.group(1))).pack(side='left', fill='x', expand=True)
                        
                        self.autotyper_state_vars[key] = (check_var, text_var)
                        text_var.trace_add('write', lambda *a, k=key: self._on_autotyper_state_change(k))
                    else:
                        preview = command_str.replace('%C', 'CTRL+').replace('%A', 'ALT+')
                        ttk.Label(row_frame, text=f"{label_button_name}: {preview}").pack(side='left', anchor='w', padx=(5,0))
                        self.autotyper_state_vars[key] = (check_var, None)
                    
                    check_var.trace_add('write', lambda *a, k=key: self._on_autotyper_state_change(k))
        
        self.app.update_autotyper_indicator()

    def refresh_profile_display(self):
        if not self.winfo_exists(): return
        
        all_profiles = sorted(list(self.app.config.get('AutoTyperProfiles', {}).keys()))
        self.profile_combo['values'] = all_profiles
        
        active_profile = self.app.config.get('Options', {}).get('active_auto_typer_profile')
        if active_profile in self.profile_combo['values']:
            self.vars['active_auto_typer_profile'].set(active_profile)
        else:
            self.vars['active_auto_typer_profile'].set('-- No Profile Selected --')
        
        self.rebuild_dynamic_autotyper_ui()


    def create_clean_settings_frame(self, parent):
        frame = ttk.LabelFrame(parent, text="Clean File Extensions", padding=10)
        frame.columnconfigure(0, weight=1)
        
        ttk.Label(frame, text="Comma-separated list of extensions to generate checklist:", wraplength=380).pack(anchor='w')
        self.vars['clean_extensions'] = tk.StringVar(name='settings_clean_extensions')
        entry = ttk.Entry(frame, textvariable=self.vars['clean_extensions'])
        entry.pack(fill='x', expand=True, pady=(5,10))
        entry.bind("<FocusOut>", lambda e, k='clean_extensions': self._on_option_var_change(k))
        
        ttk.Separator(frame, orient='horizontal').pack(fill='x', pady=5)
        
        self.clean_checkbox_frame = ttk.Frame(frame)
        self.clean_checkbox_frame.pack(fill='x')
        
        self.vars['clean_extensions'].trace_add('write', self.refresh_clean_checkboxes)
        return frame

    def refresh_clean_checkboxes(self, *args):
        if not self.winfo_exists() or not hasattr(self, 'clean_checkbox_frame') or not self.clean_checkbox_frame.winfo_exists():
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
            var.trace_add('write', lambda *a, e=ext: self._on_clean_state_change(e))

    def _on_clean_state_change(self, ext):
        if not self.winfo_exists(): return
        if ext in self.clean_vars:
            self.app.config['CleanStates'][ext] = str(self.clean_vars[ext].get())
            self.app.save_config()

    def _on_path_var_change(self, key):
        if not self.winfo_exists(): return
        if key in self.vars:
            self.app.config['Paths'][key] = str(self.vars[key].get())
            self.app.save_config()

    def create_misc_options_frame(self, parent):
        frame = ttk.LabelFrame(parent, text="Misc Options", padding=10)
        self.vars['dark_mode'] = tk.BooleanVar(name='settings_dark_mode')
        self.vars['dark_mode'].trace_add('write', lambda *a, k='dark_mode': self._on_option_var_change(k, *a))
        ttk.Checkbutton(frame, text="Dark Mode (Requires Restart)", variable=self.vars['dark_mode']).pack(anchor='w')

        return frame

    def load_settings_into_ui(self):
        for section_name in ['Paths', 'Options']:
            for key, value in self.app.config.get(section_name, {}).items():
                if key in self.vars:
                    var = self.vars[key]
                    if isinstance(var, tk.BooleanVar): var.set(value.lower() == 'true')
                    else: var.set(value)
        
        self.refresh_profile_display()
        self.refresh_clean_checkboxes()

    def open_toolchain_editor(self):
        ToolchainEditorWindow(self, self.app)

    def open_config_editor(self):
        ConfigEditorWindow(self, self.app)

    def reset_config_to_defaults(self):
        self.app.reset_config_to_defaults()

    def open_auto_typer_editor(self):
        AutoTyperProfileEditor(self, self.app, self.load_settings_into_ui)

    def _on_autotyper_state_change(self, key):
        if not self.winfo_exists(): return 

        check_var, text_var = self.autotyper_state_vars.get(key, (None, None))
        if not check_var: return
        
        profile_name, step_key, index = key
        
        try:
            profile_str = self.app.config.get('AutoTyperProfiles', {}).get(profile_name, '{}')
            profile_data = ast.literal_eval(profile_str)
            
            command_item = profile_data[step_key]['commands'][index]
            command_item['enabled'] = str(check_var.get())
            if text_var:
                command_item['text'] = text_var.get()

            self.app.config['AutoTyperProfiles'][profile_name] = str(profile_data)
            self.app.save_config()
        except (ValueError, SyntaxError, KeyError, IndexError):
            pass 

    def _on_master_switch_change(self, *args):
        if not self.winfo_exists(): return
        
        profile_name = self.vars['active_auto_typer_profile'].get()
        if not profile_name: return

        try:
            profile_str = self.app.config.get('AutoTyperProfiles', {}).get(profile_name, '{}')
            profile_data = ast.literal_eval(profile_str)
            
            profile_data['master_enabled'] = str(self.master_switch_var.get())
            
            self.app.config['AutoTyperProfiles'][profile_name] = str(profile_data)
            self.app.save_config()
            self.app.update_autotyper_indicator()
        except (ValueError, SyntaxError, KeyError):
            pass

    def _on_option_var_change(self, key, *args):
        if not self.winfo_exists(): return
        if key in self.vars:
            self.app.config['Options'][key] = str(self.vars[key].get())
            self.app.save_config()

    def save_and_close(self):
        self.app.config['Geometry']['settings_window'] = self.geometry()
        self.app.config['CleanStates'] = {ext: str(var.get()) for ext, var in self.clean_vars.items()}
        self.app.save_config()
        self.app.populate_ui_from_config()
        if self.on_close_callback:
            self.on_close_callback()
        self.destroy()

    def browse_file(self, var):
        #if path := filedialog.askopenfilename(): var.set(path)
         if path := filedialog.askopenfilename(initialdir=os.getcwd()):var.set(path)

class ToolchainEditorWindow(tk.Toplevel):
    """A Toplevel window for creating, editing, and deleting toolchains."""
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
        self.loading_data = False
        self.toolchain_path_var = tk.StringVar()
        self.autotyper_profile_var = tk.StringVar()
        
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

        ttk.Label(frame, text="Auto-Typer Profile:").grid(row=3, column=0, sticky='w', padx=5, pady=2)
        self.autotyper_profile_combo = ttk.Combobox(frame, textvariable=self.autotyper_profile_var, state='readonly')
        self.autotyper_profile_combo.grid(row=3, column=1, sticky='ew', padx=5)
        self.autotyper_profile_var.trace_add('write', self.save_current_toolchain_data)

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=0, column=2, rowspan=4, padx=5)
        ttk.Button(button_frame, text="Add New", command=self.add_new_toolchain).pack(fill='x', pady=1)
        ttk.Button(button_frame, text="Copy", command=self.copy_toolchain).pack(fill='x', pady=1)
        ttk.Button(button_frame, text="Delete", command=self.delete_toolchain, style="Danger.TButton").pack(fill='x', pady=1)

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

            color_btn = ttk.Button(frame, text="Color", width=8, command=lambda k=key: self.choose_color(k))
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

    def create_bottom_frame(self, parent):
        frame = ttk.Frame(parent, padding=(0,10,0,0))
        frame.grid(row=2, column=0, columnspan=2, sticky='ew')
        
        button_container = ttk.Frame(frame)
        button_container.pack(side='right')
        ttk.Button(button_container, text="Toolchain Options Setup", command=self.open_toolchain_options_editor).pack(side='left', padx=(0, 10))
        ttk.Button(button_container, text="Save & Close", command=self.save_and_close, style="Save.TButton").pack(side='left')

    def open_toolchain_options_editor(self):
        toolchain_name = self.last_saved_toolchain.get()
        if not toolchain_name:
            messagebox.showerror("Error", "Please select a toolchain first.", parent=self)
            return
        ToolchainOptionsEditor(self, self.app, toolchain_name)

    def populate_toolchain_list(self):
        undeletable = UNDELETABLE_ITEMS.get('Toolchains', {}).keys()
        user_toolchains = self.app.config.get('Toolchains', {})
        toolchains = sorted([t for t in user_toolchains.keys() if t not in undeletable])
        self.combobox['values'] = toolchains

    def load_toolchain_data(self, *args):
        self.loading_data = True
        toolchain_name = self.combobox.get()
        
        # Populate autotyper dropdown
        all_profiles = sorted(list(self.app.config.get('AutoTyperProfiles', {}).keys()))
        self.autotyper_profile_combo['values'] = all_profiles

        if not toolchain_name:
            self.toolchain_name_var.set("")
            self.toolchain_path_var.set("")
            self.autotyper_profile_var.set('-- No Profile Selected --')
            self.last_saved_toolchain.set("")
            for i in range(1, 11):
                key = f'Button{i}'
                self.vars[f'{key}_name'].set('')
                self.vars[f'{key}_command'].set('')
                self.vars[f'{key}_color'].set('#F0F0F0')
                self.color_labels[key].config(background='#F0F0F0')
                self.update_preview(key)
            self.loading_data = False
            return

        self.toolchain_name_var.set(toolchain_name)
        self.last_saved_toolchain.set(toolchain_name)

        toolchain_data = self.app.config.get('Toolchains', {}).get(toolchain_name, {})
        self.toolchain_path_var.set(toolchain_data.get('path', ''))
        
        profile = toolchain_data.get('autotyper_profile', '-- No Profile Selected --')
        if profile in all_profiles:
            self.autotyper_profile_var.set(profile)
        else:
            self.autotyper_profile_var.set('-- No Profile Selected --')

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
        
        self.loading_data = False

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

    def on_name_change(self, *args):
        if self.loading_data: return
        old_name = self.last_saved_toolchain.get()
        new_name = self.toolchain_name_var.get().strip()
        if not old_name or not new_name or old_name == new_name:
            return
        
        if new_name in self.app.config['Toolchains']:
            self.combobox.set(new_name)
            self.load_toolchain_data()
            return
            
        if new_name in UNDELETABLE_ITEMS.get('Toolchains', {}):
             # Revert name and show error, but don't stop execution
            self.toolchain_name_var.set(old_name)
            messagebox.showerror("Error", f"'{new_name}' is a reserved name.", parent=self)
            return

        self.app.config['Toolchains'][new_name] = self.app.config['Toolchains'].pop(old_name)
        self.last_saved_toolchain.set(new_name)

        current_values = list(self.combobox['values'])
        if old_name in current_values:
            idx = current_values.index(old_name)
            current_values[idx] = new_name
            self.combobox['values'] = sorted(current_values)
            self.combobox.set(new_name)

    def save_current_toolchain_data(self, *args):
        if self.loading_data: return

        toolchain_name = self.last_saved_toolchain.get()
        if not toolchain_name or toolchain_name not in self.app.config['Toolchains']:
            return

        buttons_data = {f'Button{i}': {
                'name': self.vars[f'Button{i}_name'].get(),
                'command': self.vars[f'Button{i}_command'].get(),
                'color': self.vars[f'Button{i}_color'].get()
            } for i in range(1, 11)}
        self.app.config['Toolchains'][toolchain_name]['custom_buttons'] = str(buttons_data)
        self.app.config['Toolchains'][toolchain_name]['path'] = self.toolchain_path_var.get()
        self.app.config['Toolchains'][toolchain_name]['autotyper_profile'] = self.autotyper_profile_var.get()
        self.app.needs_ui_rebuild = True
        self.app.save_config()

    def add_new_toolchain(self):
        new_name = simpledialog.askstring("New Toolchain", "Enter a name for the new toolchain:", parent=self)
        if not new_name or not new_name.strip(): return
        new_name = new_name.strip()

        if new_name in self.app.config['Toolchains'] or new_name in UNDELETABLE_ITEMS.get('Toolchains', {}):
            messagebox.showerror("Error", f"Toolchain '{new_name}' already exists or is a reserved name.", parent=self)
            return

        self.app.config['Toolchains'][new_name] = copy.deepcopy(DEFAULT_CONFIG['Toolchains']['7800ASMDevKit'])
        blank_buttons = {f'Button{i}': {'name': '', 'command': '', 'color': '#F0F0F0'} for i in range(1, 11)}
        self.app.config['Toolchains'][new_name]['custom_buttons'] = str(blank_buttons)
        self.app.config['Toolchains'][new_name]['autotyper_profile'] = '-- No Profile Selected --'

        self.app.save_config()
        self.populate_toolchain_list()
        self.combobox.set(new_name)
        self.load_toolchain_data()

    def copy_toolchain(self):
        old_name = self.combobox.get()
        if not old_name:
            messagebox.showerror("Error", "No toolchain selected to copy.", parent=self)
            return

        if old_name in UNDELETABLE_ITEMS.get('Toolchains', {}):
            messagebox.showerror("Error", "Cannot copy a reserved toolchain.", parent=self)
            return

        while True:
            new_name = simpledialog.askstring("Copy Toolchain", "Enter a new name for the copied toolchain:", parent=self)

            if new_name is None: # User cancelled
                break

            new_name = new_name.strip()
            if not new_name:
                messagebox.showerror("Error", "Name cannot be empty.", parent=self)
                continue
            
            if new_name == old_name:
                messagebox.showerror("Error", "Name must not match the existing toolchain.", parent=self)
                continue

            if new_name in self.app.config['Toolchains']:
                messagebox.showerror("Error", f"Toolchain '{new_name}' already exists.", parent=self)
                continue

            if new_name in UNDELETABLE_ITEMS.get('Toolchains', {}):
                messagebox.showerror("Error", f"'{new_name}' is a reserved name.", parent=self)
                continue
                
            # If all checks pass, copy the toolchain
            toolchain_data_to_copy = copy.deepcopy(self.app.config['Toolchains'][old_name])
            self.app.config['Toolchains'][new_name] = toolchain_data_to_copy
            self.app.save_config()

            self.populate_toolchain_list()
            self.combobox.set(new_name)
            self.load_toolchain_data()
            self.app.needs_ui_rebuild = True
            break

    def delete_toolchain(self):
        toolchain_name = self.combobox.get()
        if not toolchain_name: return
        
        if toolchain_name in UNDELETABLE_ITEMS.get('Toolchains', {}):
            messagebox.showerror("Error", "Cannot delete a reserved toolchain.", parent=self)
            return

        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the '{toolchain_name}' toolchain?", parent=self):
            del self.app.config['Toolchains'][toolchain_name]
            self.app.save_config()
            self.populate_toolchain_list()
            if self.combobox['values']:
                self.combobox.current(0)
            else:
                self.combobox.set('')

            # FIX: Explicitly update the main application's state variable
            self.app.toolchain_type.set(self.combobox.get())

            self.load_toolchain_data()
            self.app.needs_ui_rebuild = True

    def choose_color(self, button_key):
        initial_color = self.vars[f'{button_key}_color'].get()
        color_code = colorchooser.askcolor(title="Choose button color", initialcolor=initial_color, parent=self)
        if color_code and color_code[1]:
            self.vars[f'{button_key}_color'].set(color_code[1])
            self.color_labels[key].config(background=color_code[1])

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
    def __init__(self, parent, app_controller, toolchain_name):
        super().__init__(parent)
        self.transient(parent)
        self.grab_set()
        self.title(f"Toolchain Options for '{toolchain_name}'")
        self.app = app_controller
        self.toolchain_name = toolchain_name
        self.option_rows = [] 
        self.preview_option_vars = {} 
        self.preview_command_labels = {} 
        self.toolchain_editor_window = parent if isinstance(parent, ToolchainEditorWindow) else None

        saved_geom = self.app.config.get('Geometry', {}).get('toolchain_options_editor')
        if not saved_geom or saved_geom == '':
            saved_geom = self.app.config.get('DefaultGeometry', {}).get('toolchain_options_editor', '800x700')
        self.geometry(saved_geom)

        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill="both", expand=True)
        main_frame.rowconfigure(1, weight=1)
        main_frame.columnconfigure(0, weight=1)

        self.create_scrollable_area(main_frame)
        self.create_preview_area(main_frame)
        self.create_bottom_buttons(main_frame)
        
        self.load_options()
        self.protocol("WM_DELETE_WINDOW", self.save_and_close)

    def create_scrollable_area(self, parent):
        container = ttk.LabelFrame(parent, text="Configurable Options", padding=10)
        container.grid(row=0, column=0, sticky='ew', pady=(0,10))
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)
        
        canvas = tk.Canvas(container, highlightthickness=0, height=200)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas, padding=5)

        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

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
        
        if not options_list:
            self.rebuild_preview_options()

    def create_option_row(self, option_data=None):
        if option_data is None: option_data = {}
        
        row_frame = ttk.Frame(self.scrollable_frame)
        row_frame.pack(fill='x', pady=5)
        row_frame.columnconfigure(2, weight=1)
        row_frame.columnconfigure(4, weight=1)

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

        toolchain_data = self.app.config.get('Toolchains', {}).get(self.toolchain_name, {})
        try:
            buttons_data = ast.literal_eval(toolchain_data.get('custom_buttons', '{}'))
        except (ValueError, SyntaxError):
            buttons_data = {}
        
        button_display_map = {
            (buttons_data.get(f'Button{i}', {}).get('name') or f'Button{i}'): f'Button{i}'
            for i in range(1, 11) if buttons_data.get(f'Button{i}', {}).get('name', '').strip()
        }
        button_key_map = {v: k for k, v in button_display_map.items()}

        target_var = tk.StringVar(value=option_data.get('target', ''))
        target_display_var = tk.StringVar()

        def on_target_select(*args):
            display_name = target_display_var.get()
            actual_key = button_display_map.get(display_name)
            if actual_key:
                target_var.set(actual_key)
            self.rebuild_preview_options()

        target_combo = ttk.Combobox(row_frame, textvariable=target_display_var, state='readonly', width=15,
                                    values=sorted(list(button_display_map.keys())))
        target_combo.grid(row=0, column=6)

        initial_display = button_key_map.get(target_var.get())
        if initial_display:
            target_display_var.set(initial_display)
        elif target_combo['values']:
            default_display = target_combo['values'][0]
            target_display_var.set(default_display)
            target_var.set(button_display_map[default_display])

        target_display_var.trace_add('write', on_target_select)
        flag_var.trace_add('write', lambda *a, tv=target_var: self.update_preview_command_string(tv.get()))
        
        self.option_rows.append({
            'frame': row_frame,
            'vars': {'name': name_var, 'flag': flag_var, 'target': target_var}
        })
        self.rebuild_preview_options()

    def delete_option(self, row_frame):
        idx_to_del = next((i for i, row in enumerate(self.option_rows) if row['frame'] == row_frame), -1)
        if idx_to_del != -1:
            self.option_rows[idx_to_del]['frame'].destroy()
            self.option_rows.pop(idx_to_del)
            self.rebuild_preview_options()

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

    def update_preview_command_string(self, target_button):
        if not target_button or target_button not in self.preview_command_labels:
            return

        base_command = ''
        try:
            if self.toolchain_editor_window and self.toolchain_editor_window.winfo_exists():
                base_command = self.toolchain_editor_window.vars.get(f'{target_button}_command').get()
            else:
                toolchain_data = self.app.config.get('Toolchains', {}).get(self.toolchain_name, {})
                buttons_data = ast.literal_eval(toolchain_data.get('custom_buttons', '{}'))
                base_command = buttons_data.get(target_button, {}).get('command', '')
        except (ValueError, SyntaxError, AttributeError):
            base_command = ''
        
        resolved_cmd = self.app.resolve_command_placeholders(
            action_key=None, command_override=base_command,
            replacements_override={'f': '/path/to/project/source.ext', 's': '/path/to/project/source', 'o': '/path/to/project/source'},
            resolve_tool_paths=True, target_button=None, toolchain_context=self.toolchain_name
        )
        
        source_stem, source_path_full = "/path/to/project/source", "/path/to/project/source.ext"
        
        for row in self.option_rows:
            if row['vars']['target'].get() == target_button:
                option_name = row['vars']['name'].get()
                var = self.preview_option_vars.get(option_name)
                if var and var.get():
                    flag = row['vars']['flag'].get().replace('%s', source_stem).replace('%o', source_stem).replace('%f', source_path_full)
                    resolved_cmd += f" {flag}"
        
        self.preview_command_labels[target_button].config(text=resolved_cmd)

    def create_bottom_buttons(self, parent):
        frame = ttk.Frame(parent)
        frame.grid(row=2, column=0, sticky='ew', pady=(10,0))
        ttk.Button(frame, text="Create New Option", command=self.create_option_row).pack(side='left')
        ttk.Button(frame, text="Save & Close", command=self.save_and_close, style="Save.TButton").pack(side='right')

    def save_and_close(self):
        new_options_list = []
        for row in self.option_rows:
            name, flag, target = row['vars']['name'].get().strip(), row['vars']['flag'].get().strip(), row['vars']['target'].get()
            if name and flag and target:
                new_options_list.append({'name': name, 'flag': flag, 'target': target})

        self.app.config['Toolchains'][self.toolchain_name]['toolchain_options'] = str(new_options_list)
        self.app.config['Geometry']['toolchain_options_editor'] = self.geometry()
        
        self.app.save_config()
        self.app.on_toolchain_selected()
        self.destroy()

# --- Integrated Config Editor Class ---
class ConfigEditorWindow(tk.Toplevel):
    """A GUI tool to edit the application's default configuration."""
    def __init__(self, parent, app_controller):
        super().__init__(parent)
        self.transient(parent)
        self.grab_set()
        self.app = app_controller
        self.master = parent
        self.title(f"Default Config Editor - v{APP_VERSION}")
        self.geometry("1000x800")
        self.minsize(600, 600)
        self.update_timer, self.scroll_timer = None, None
        self.previous_output_content = ""
        
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)
        main_frame.rowconfigure(0, weight=1); main_frame.rowconfigure(2, weight=1)
        main_frame.columnconfigure(0, weight=1)

        input_labelframe = ttk.LabelFrame(main_frame, text="INI File Content (Live Edit)", padding="5")
        input_labelframe.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        input_labelframe.rowconfigure(0, weight=1); input_labelframe.columnconfigure(0, weight=1)
        
        self.input_yscrollbar = ttk.Scrollbar(input_labelframe, orient="vertical")
        self.input_text = tk.Text(input_labelframe, wrap="word", height=10, undo=True, font=("Courier New", 10), yscrollcommand=self.on_input_scroll)
        self.input_yscrollbar.config(command=self.input_text.yview)
        self.input_text.grid(row=0, column=0, sticky="nsew"); self.input_yscrollbar.grid(row=0, column=1, sticky="ns")
        self.input_text.bind("<KeyRelease>", self.schedule_update)

        controls_container = ttk.Frame(main_frame); controls_container.grid(row=1, column=0, pady=10, sticky='ew')
        controls_container.columnconfigure(0, weight=1)
        
        update_rollback_frame = ttk.LabelFrame(controls_container, text="Actions", padding=10)
        update_rollback_frame.grid(row=0, column=0, sticky='ew')
        update_rollback_frame.columnconfigure(0, weight=1); update_rollback_frame.columnconfigure(1, weight=1)
        
        ttk.Button(update_rollback_frame, text="Update devCMDcycle.py", command=self.update_dev_cycle_file, style="Accent.TButton").grid(row=0, column=0, sticky='ew', padx=(0,5))
        ttk.Button(update_rollback_frame, text="Roll Back", command=self.rollback_file, style="Danger.TButton").grid(row=0, column=1, sticky='ew', padx=(5,0))

        manual_ops_frame = ttk.Frame(controls_container); manual_ops_frame.grid(row=0, column=1, sticky='ns', padx=5)
        ttk.Button(manual_ops_frame, text="Copy to Clipboard", command=self.copy_to_clipboard).pack(expand=True, fill='both', pady=(0,2))
        ttk.Button(manual_ops_frame, text="Close", command=self.destroy).pack(expand=True, fill='both', pady=(2,0))
        
        output_labelframe = ttk.LabelFrame(main_frame, text="Generated DEFAULT_CONFIG Code (Live Preview)", padding="5")
        output_labelframe.grid(row=2, column=0, sticky="nsew", pady=(10, 0))
        output_labelframe.rowconfigure(0, weight=1); output_labelframe.columnconfigure(0, weight=1)
        y_scrollbar = ttk.Scrollbar(output_labelframe, orient="vertical"); x_scrollbar = ttk.Scrollbar(output_labelframe, orient="horizontal")
        self.output_text = tk.Text(output_labelframe, wrap="none", height=10, state="disabled", font=("Courier New", 10), yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set, background="#fdf5e6")
        self.output_text.tag_configure("highlight", background="#ffffd0")
        y_scrollbar.config(command=self.output_text.yview); x_scrollbar.config(command=self.output_text.xview)
        self.output_text.grid(row=0, column=0, sticky="nsew"); y_scrollbar.grid(row=0, column=1, sticky="ns"); x_scrollbar.grid(row=1, column=0, columnspan=2, sticky="ew")

        self.load_current_config_as_ini()

    def load_current_config_as_ini(self):
        config_to_convert = self.app.config
        parser = configparser.ConfigParser(interpolation=None); parser.optionxform = str
        
        for section, data in config_to_convert.items():
            if section == 'Toolchains':
                for name, t_data in data.items():
                    if name not in UNDELETABLE_ITEMS.get('Toolchains', {}):
                        parser[f'Toolchain:{name}'] = {k: str(v) for k, v in t_data.items()}
            elif isinstance(data, dict):
                 parser[section] = {k: str(v) for k, v in data.items()}

        string_io = io.StringIO()
        parser.write(string_io)
        self.input_text.delete("1.0", tk.END)
        self.input_text.insert("1.0", string_io.getvalue())
        self.schedule_update()

    def on_input_scroll(self, *args):
        self.input_yscrollbar.set(*args)
        if self.scroll_timer: self.after_cancel(self.scroll_timer)
        self.scroll_timer = self.after(100, self.sync_views)

    def sync_views(self):
        try:
            index = self.input_text.index(tk.INSERT)
            input_line_num = int(index.split('.')[0])
            
            current_section = next((self.input_text.get(f"{i}.0", f"{i}.end").strip()[1:-1] 
                                    for i in range(input_line_num, 0, -1) if self.input_text.get(f"{i}.0", f"{i}.end").strip().startswith('[')), None)
            if not current_section: return

            py_key = f"'{current_section.split(':', 1)[1]}': {{" if current_section.startswith("Toolchain:") else f"'{current_section}': {{"
            
            if pos := self.output_text.search(py_key, "1.0", tk.END): self.output_text.see(pos)
        except (ValueError, tk.TclError): pass

    def schedule_update(self, event=None):
        if self.update_timer: self.after_cancel(self.update_timer)
        self.update_timer = self.after(500, self.convert_ini_to_py)

    def _format_value(self, value):
        try:
            obj = ast.literal_eval(value)
            if isinstance(obj, (dict, list)):
                pretty_string = pprint.pformat(obj, indent=4, width=120, sort_dicts=False)
                return f"str(\n{''.join(['    ' + line for line in pretty_string.splitlines(True)])}    )"
            return repr(value)
        except (ValueError, SyntaxError): return repr(value)

    def convert_ini_to_py(self):
        try:
            ini_string = self.input_text.get("1.0", tk.END)
            if not ini_string.strip(): self.update_output_text(""); return
            parser = configparser.ConfigParser(interpolation=None); parser.optionxform = str
            parser.read_string(ini_string); config_dict, toolchains = {}, {}
            for section in parser.sections():
                if section.startswith('Toolchain:'): toolchains[section.split(':', 1)[1]] = dict(parser.items(section))
                else: config_dict[section] = dict(parser.items(section))
            if toolchains: config_dict['Toolchains'] = toolchains
            
            output_lines = ["DEFAULT_CONFIG = {"]
            for i, (section_name, section_data) in enumerate(sorted(config_dict.items())):
                output_lines.append(f"    '{section_name}': {{")
                for j, (key, value) in enumerate(sorted(section_data.items())):
                    end_char = ',' if j < len(section_data) - 1 else ''
                    if section_name == 'Toolchains':
                        output_lines.append(f"        '{key}': {{")
                        for k, (sub_key, sub_val) in enumerate(sorted(value.items())):
                            output_lines.append(f"            '{sub_key}': {self._format_value(sub_val)}{',' if k < len(value) - 1 else ''}")
                        output_lines.append(f"        }}{end_char}")
                    else:
                        output_lines.append(f"        '{key}': {self._format_value(value)}{end_char}")
                output_lines.append(f"    }}{',' if i < len(config_dict) - 1 else ''}")
            output_lines.append("}")
            
            new_output_content = '\n'.join(output_lines)
            self.update_output_text_with_highlight(new_output_content)
            self.previous_output_content = new_output_content
            self.sync_views()
        except configparser.Error: pass
        
    def update_dev_cycle_file(self):
        target_py_file = os.path.abspath(__file__)
        script_backup_dir = os.path.join(os.path.dirname(target_py_file), SCRIPT_BACKUP_DIR)
        os.makedirs(script_backup_dir, exist_ok=True)

        backup_num = 1
        while os.path.exists(backup_path := os.path.join(script_backup_dir, f"{os.path.basename(target_py_file)}_backup{backup_num}")):
            backup_num += 1
            
        confirm_msg = f"This will replace the DEFAULT_CONFIG in:\n{os.path.basename(target_py_file)}\n\nA backup will be created as:\n{os.path.basename(backup_path)}\n\nAre you sure?"
        if not ConfirmationDialog(self.master, "Confirm Update", confirm_msg).result: return

        generated_config = self.output_text.get("1.0", tk.END).strip()
        try:
            shutil.copy2(target_py_file, backup_path)
            with open(target_py_file, 'r', encoding='utf-8') as f: lines = f.readlines()

            start_line_index, indent = next(((i, line[:len(line) - len(line.lstrip())]) 
                                            for i, line in enumerate(lines) if line.lstrip().startswith("DEFAULT_CONFIG")), (-1, ""))
            if start_line_index == -1: raise ValueError("Could not find `DEFAULT_CONFIG = ...` block.")

            brace_count, has_started, end_line_index = 0, False, -1
            for i in range(start_line_index, len(lines)):
                if '{' in lines[i]: has_started = True
                brace_count += lines[i].count('{') - lines[i].count('}')
                if has_started and brace_count == 0: end_line_index = i; break
            
            if end_line_index == -1: raise ValueError("Could not find closing brace for DEFAULT_CONFIG.")

            indented_config_lines = [indent + line for line in generated_config.splitlines(True)]
            if not indented_config_lines[-1].endswith('\n'): indented_config_lines[-1] += '\n'
            new_content_lines = lines[:start_line_index] + indented_config_lines + lines[end_line_index + 1:]

            with open(target_py_file, 'w', encoding='utf-8') as f: f.writelines(new_content_lines)
            
            success_msg = "Update successful!\n\nWhat would you like to do now?"
            if UpdateSuccessDialog(self.master, "Update Complete", success_msg).result == "reset":
                self.app.reset_config_to_defaults(confirmed=True)
        except Exception as e:
            InfoDialog(self.master, "Update Error", f"An error occurred:\n{e}")
            if os.path.exists(backup_path): shutil.move(backup_path, target_py_file)
    
    def rollback_file(self):
        target_py_file = os.path.abspath(__file__)
        script_backup_dir = os.path.join(os.path.dirname(target_py_file), SCRIPT_BACKUP_DIR)
        os.makedirs(script_backup_dir, exist_ok=True)
        
        backups = sorted(glob.glob(os.path.join(script_backup_dir, f"{os.path.basename(target_py_file)}_backup*")))
        if not backups: return InfoDialog(self.master, "No Backups", f"No backups found in:\n{script_backup_dir}")

        choice = RollbackDialog(self.master, "Roll Back Script", f"Latest backup: {os.path.basename(backups[-1])}").result
        if not choice: return
        
        backup_to_restore = backups[-1] if choice == "latest" else filedialog.askopenfilename(
            title="Select a backup file", initialdir=script_backup_dir,
            filetypes=(("Backup Files", f"{os.path.basename(target_py_file)}_backup*"), ("All files", "*.*"))
        )
        if not backup_to_restore: return

        try:
            shutil.copy2(backup_to_restore, target_py_file)
            InfoDialog(self.master, "Success", f"Restored from '{os.path.basename(backup_to_restore)}'.\n\nRestart required.")
        except Exception as e:
            InfoDialog(self.master, "Rollback Error", f"An error occurred:\n{e}")

    def update_output_text(self, text):
        self.output_text.config(state="normal")
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", text)
        self.output_text.config(state="disabled")

    def update_output_text_with_highlight(self, new_text):
        self.output_text.config(state="normal")
        self.output_text.delete("1.0", tk.END); self.output_text.insert("1.0", new_text)
        self.output_text.tag_remove("highlight", "1.0", tk.END)
        old_lines, new_lines = self.previous_output_content.splitlines(), new_text.splitlines()
        
        for i in range(min(len(old_lines), len(new_lines))):
            if old_lines[i] != new_lines[i]: self.output_text.tag_add("highlight", f"{i + 1}.0", f"{i + 1}.end")
        if len(new_lines) > len(old_lines): self.output_text.tag_add("highlight", f"{len(old_lines) + 1}.0", f"{len(new_lines)}.end")
        self.output_text.config(state="disabled")

    def copy_to_clipboard(self): self.clipboard_clear(); self.clipboard_append(self.output_text.get("1.0", tk.END))

class DevCommanderApp:
    """The main application class."""
    def __init__(self, root):
        self.root = root
        self.root.title(f"Developer Command Cycle v{APP_VERSION}")
        self.config = {}
        self.process, self.master_fd = None, None
        self.output_queue = queue.Queue()
        self.command_running = False
        self.source_file = tk.StringVar()
        self.toolchain_type = tk.StringVar()
        self.always_on_top_var = tk.BooleanVar()
        self.initial_on_top_state, self.needs_ui_rebuild = False, False
        self.toolchain_option_vars, self.action_buttons = {}, {}
        self.settings_window_instance = None

        self.load_config()
        
        saved_geom = self.config.get('Geometry', {}).get('main_window') or self.config.get('DefaultGeometry', {}).get('main_window', '800x600')
        self.root.geometry(saved_geom)
        
        self.apply_theme()
        self.configure_styles()
        self.setup_ui()
        self.populate_ui_from_config()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.after(100, self.process_output_queue)

    def get_default_config(self):
        return copy.deepcopy(DEFAULT_CONFIG)

    def load_config(self):
        parser = configparser.ConfigParser(interpolation=None, allow_no_value=True)
        parser.optionxform = str

        if os.path.exists(CONFIG_FILE_NAME):
            self.config = defaultdict(dict)
            parser.read(CONFIG_FILE_NAME)
            for section in parser.sections():
                if section.startswith('Toolchain:'):
                    _, name = section.split(':', 1)
                    if 'Toolchains' not in self.config: self.config['Toolchains'] = {}
                    self.config['Toolchains'][name] = dict(parser.items(section))
                else:
                    self.config[section].update(dict(parser.items(section)))
        else:
            self.config = self.get_default_config()
            self.save_config()

        # Merge undeletable items to ensure they are always present at runtime
        for section, items in UNDELETABLE_ITEMS.items():
            if section not in self.config: self.config[section] = {}
            self.config[section].update(items)

    def save_config(self):
        parser = configparser.ConfigParser(interpolation=None)
        parser.optionxform = str
        
        config_to_save = copy.deepcopy(self.config)
        
        # Filter out undeletable items before saving to INI
        for section, items in UNDELETABLE_ITEMS.items():
            if section in config_to_save:
                for key in items:
                    if key in config_to_save[section]:
                        del config_to_save[section][key]

        for section, data in config_to_save.items():
            if section == 'Toolchains':
                for name, t_data in data.items():
                    parser[f'Toolchain:{name}'] = {k: str(v) for k, v in t_data.items()}
            elif isinstance(data, dict):
                 parser[section] = {k: str(v) for k, v in data.items()}
            
        with open(CONFIG_FILE_NAME, 'w') as f: parser.write(f)

    def apply_theme(self):
        is_dark = self.config.get('Options', {}).get('dark_mode', 'False').lower() == 'true'
        style = ttk.Style()
        try:
            theme_to_use = 'clam' # Default theme
            if sys.platform == "win32" and not is_dark:
                try:
                    # Attempt to use the native-looking Vista theme on Windows Light Mode
                    style.theme_use('vista')
                    theme_to_use = 'vista'
                except tk.TclError:
                    # Fallback if 'vista' is not available
                    style.theme_use('clam')
            
            if is_dark:
                self.root.configure(bg='#2E2E2E')
                style.theme_use('clam')
                style.configure('.', background='#2E2E2E', foreground='white', fieldbackground='#3C3C3C', lightcolor='#555555', darkcolor='#1E1E1E')
                style.map('TCombobox', fieldbackground=[('readonly','#3C3C3C')])
                style.map('.', background=[('active', '#4a6984')], foreground=[('active', 'white')])
            elif theme_to_use != 'vista': # Apply default light theme if not Vista
                self.root.configure(bg='SystemButtonFace')
                style.theme_use(theme_to_use)

        except tk.TclError: 
            # Final fallback in case any theme fails
            pass

    def configure_styles(self):
        style = ttk.Style()
        style.configure("TButton", padding=5, font=('Helvetica', 10))
        style.configure("Danger.TButton", background="#dc3545", foreground="white", font=('Helvetica', 10, 'bold'))
        style.map("Danger.TButton", background=[('active', '#c82333')])
        style.configure("Accent.TButton", foreground="white", font=('Helvetica', 10, 'bold'))
        style.configure("Save.TButton", background="#add8e6", foreground="black", font=('Helvetica', 10, 'bold'))
        style.map("Save.TButton", background=[('active', '#a2c8d0')])

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill='both', expand=True)
        main_frame.columnconfigure(0, weight=1); main_frame.rowconfigure(3, weight=1)
        
        top_container = ttk.Frame(main_frame); top_container.grid(row=0, column=0, sticky='ew')
        top_container.columnconfigure(0, weight=1)
        self.create_project_widgets(top_container).grid(row=0, column=0, sticky='ewns')
        self.create_top_right_widgets(top_container).grid(row=0, column=1, sticky='ne', padx=10)
        
        self.dynamic_options_frame = ttk.LabelFrame(main_frame, text="Toolchain Options", padding=10)
        self.dynamic_options_frame.grid(row=1, column=0, sticky='ew', pady=5)
        
        self.actions_frame = ttk.LabelFrame(main_frame, text="Actions", padding=10)
        self.actions_frame.grid(row=2, column=0, sticky='ew', pady=5)
        
        self.create_status_widgets(main_frame).grid(row=3, column=0, sticky='nsew', pady=5)

    def populate_ui_from_config(self):
        paths = self.config.get('Paths', {})
        self.source_file.set(paths.get('last_source', ''))
        self.source_file.trace_add('write', self._save_paths_to_config)
        
        all_toolchains = sorted(list(self.config.get('Toolchains', {}).keys()))
        self.toolchain_combo['values'] = all_toolchains
        
        last_toolchain = paths.get('last_toolchain')
        
        # Set the initial selection
        if last_toolchain and last_toolchain in all_toolchains:
            self.toolchain_type.set(last_toolchain)
        else:
            self.toolchain_type.set('-- Select Toolchain --')

        self.toolchain_type.trace_add('write', self.on_toolchain_selected)
        self.on_toolchain_selected()
        self.apply_misc_options()
        self.update_autotyper_indicator()

    def _save_paths_to_config(self, *args):
        self.config['Paths']['last_source'] = self.source_file.get()
        # Do not save here, let actions trigger saves to avoid excessive writes

    def apply_misc_options(self):
        on_top = self.config.get('Options', {}).get('always_on_top', 'False').lower() == 'true'
        self.always_on_top_var.set(on_top)
        self.root.wm_attributes("-topmost", on_top)
        self.initial_on_top_state = on_top
        if hasattr(self, 'restart_label'):
            self.always_on_top_var.trace_add('write', self._check_topmost_change)

    def _check_topmost_change(self, *args):
        changed = self.always_on_top_var.get() != self.initial_on_top_state
        self.restart_label.config(text="Restart Required" if changed else "")
        self.config['Options']['always_on_top'] = str(self.always_on_top_var.get())
        self.save_config() # Save this change immediately

    def create_project_widgets(self, parent):
        frame = ttk.LabelFrame(parent, text="Project", padding=10)
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text="Source File:").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.source_file).grid(row=0, column=1, sticky='ew')
        ttk.Button(frame, text="...", command=self.browse_source_file, width=3).grid(row=0, column=2, padx=5)
        ttk.Label(frame, text="Toolchain:").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        self.toolchain_combo = ttk.Combobox(frame, textvariable=self.toolchain_type, state='readonly', exportselection=False)
        self.toolchain_combo.grid(row=1, column=1, sticky='w')
        return frame

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

    def rebuild_action_buttons(self):
        for widget in self.actions_frame.winfo_children(): widget.destroy()
        self.action_buttons.clear()
        
        for i in range(4): self.actions_frame.columnconfigure(i, weight=1)
        
        ttk.Button(self.actions_frame, text="Settings", command=lambda: self.log_and_run("Settings", self.open_settings)).grid(row=0, column=0, padx=2, pady=2, sticky='ew')
        ttk.Button(self.actions_frame, text="Open Folder", command=lambda: self.log_and_run("Open Folder", self.open_project_folder)).grid(row=0, column=1, padx=2, pady=2, sticky='ew')
        ttk.Button(self.actions_frame, text="Clean", command=lambda: self.log_and_run("Clean", self.clean_project), style="Danger.TButton").grid(row=0, column=2, padx=2, pady=2, sticky='ew')

        toolchain_name = self.toolchain_type.get()
        if not toolchain_name: return
        toolchain_data = self.config.get('Toolchains', {}).get(toolchain_name, {})
        try: buttons_data = ast.literal_eval(toolchain_data.get('custom_buttons', '{}'))
        except (ValueError, SyntaxError): buttons_data = {}

        style = ttk.Style()
        grid_map = {'Button1': (0, 3, 1), 'Button2': (1, 0, 1), 'Button3': (1, 1, 1), 'Button4': (1, 2, 1), 'Button5': (1, 3, 1), 
                    'Button6': (2, 0, 2), 'Button7': (2, 2, 2), 'Button8': (3, 0, 2), 'Button9': (3, 2, 2), 'Button10':(4, 0, 4)}
        
        for i in range(1, 11):
            key = f"Button{i}"
            if name := buttons_data.get(key, {}).get('name'):
                color = buttons_data[key].get('color', '#F0F0F0')
                style_name = f"{key}.TButton"
                try:
                    r, g, b = self.root.winfo_rgb(color)
                    text_color = 'black' if (r*299 + g*587 + b*114) / 65535 > 0.5 else 'white'
                    style.configure(style_name, background=color, foreground=text_color, padding=5, font=('Helvetica', 10))
                    style.map(style_name, background=[('active', color)], foreground=[('active', text_color)])
                except tk.TclError: style.configure(style_name, background=color)

                row, col, span = grid_map.get(key)
                btn = ttk.Button(self.actions_frame, text=name, style=style_name, command=lambda k=key: self.execute_custom_button(k))
                btn.grid(row=row, column=col, columnspan=span, sticky='ew', padx=2, pady=2)
                self.action_buttons[key] = btn

    def create_status_widgets(self, parent):
        frame = ttk.LabelFrame(parent, text="Status Window", padding=10)
        frame.rowconfigure(0, weight=1); frame.columnconfigure(0, weight=1)
        
        self.output_text = tk.Text(frame, wrap='word', state='disabled', background='black', foreground='white', insertbackground='white')
        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=self.output_text.yview)
        self.output_text.config(yscrollcommand=scrollbar.set)
        self.output_text.grid(row=0, column=0, sticky='nsew'); scrollbar.grid(row=0, column=1, sticky='ns')
        self.ansi_handler = AnsiColorHandler(self.output_text)
        try:
            bold_font = tkfont.Font(self.output_text, self.output_text.cget("font"), weight="bold")
            italic_font = tkfont.Font(self.output_text, self.output_text.cget("font"), slant="italic")
            self.output_text.tag_configure("success", foreground="#28a745", font=bold_font)
            self.output_text.tag_configure("error", foreground="#dc3545", font=bold_font)
            self.output_text.tag_configure("info", foreground="#17a2b8")
            self.output_text.tag_configure("user_input", foreground="#007bff", font=italic_font)
            self.output_text.tag_configure("prompt", foreground="#ffc107", font=italic_font)
        except tk.TclError: pass

        input_frame = ttk.Frame(frame); input_frame.grid(row=1, column=0, columnspan=2, sticky='ew', pady=(5,0))
        input_frame.columnconfigure(1, weight=1)
        self.autotyper_label = ttk.Label(input_frame, text="", foreground='#ff4444', font=('Helvetica', 10, 'bold'))
        self.autotyper_label.grid(row=0, column=0, padx=(0,5))
        self.input_entry = ttk.Entry(input_frame); self.input_entry.grid(row=0, column=1, sticky='ew')
        self.input_entry.bind("<Return>", self.send_input_to_process); self.input_entry.bind("<KP_Enter>", self.send_input_to_process)
        ttk.Button(input_frame, text="Enter", command=self.send_input_to_process).grid(row=0, column=2, padx=5)
        self.break_button = ttk.Button(input_frame, text="Break", command=self.send_break_signal, state='disabled')
        self.break_button.grid(row=0, column=3, padx=5)
        return frame

    def on_toolchain_selected(self, *args):
        for widget in self.dynamic_options_frame.winfo_children():
            widget.destroy()
        self.toolchain_option_vars.clear()
        
        toolchain_name = self.toolchain_type.get()
        
        self.config['Paths']['last_toolchain'] = toolchain_name
        self.save_config() 
        
        if not toolchain_name or toolchain_name in UNDELETABLE_ITEMS.get('Toolchains', {}): 
            self.rebuild_action_buttons()
            return

        toolchain_data = self.config.get('Toolchains', {}).get(toolchain_name, {})
        
        new_profile = toolchain_data.get('autotyper_profile')
        all_profiles = self.config.get('AutoTyperProfiles', {})
        
        if new_profile and new_profile in all_profiles:
            if self.config['Options'].get('active_auto_typer_profile') != new_profile:
                self.config['Options']['active_auto_typer_profile'] = new_profile
                self.log_output(f"Switched auto-typer profile to: {new_profile}", tag='info')
        else:
            self.config['Options']['active_auto_typer_profile'] = '-- No Profile Selected --'
            if new_profile: 
                 self.log_output(f"Warning: Toolchain specifies profile '{new_profile}', but it was not found. Falling back.", tag='error')

        self.save_config() 
        self.update_autotyper_indicator()
        
        try: toolchain_options = ast.literal_eval(toolchain_data.get('toolchain_options', '[]'))
        except (ValueError, SyntaxError): toolchain_options = []
        try: buttons_data = ast.literal_eval(toolchain_data.get('custom_buttons', '{}'))
        except (ValueError, SyntaxError): buttons_data = {}

        self.toolchain_options_cb_frame = ttk.Frame(self.dynamic_options_frame)
        self.toolchain_options_cb_frame.pack(side='left', fill='x', expand=True)
        self.toolchain_options_cb_frame.bind('<Configure>', self._update_preview_wraps)

        preview_targets = set()
        for option in toolchain_options:
            name, flag, target = option.get('name', ''), option.get('flag', ''), option.get('target', 'None')
            key = f"{toolchain_name}_{name.replace(' ', '_')}"
            var = tk.BooleanVar(name=f"toolchain_var_{key}", value=self.config.get('ToolchainStates', {}).get(key, 'False').lower() == 'true')
            ttk.Checkbutton(self.toolchain_options_cb_frame, text=name, variable=var).pack(anchor='w')
            self.toolchain_option_vars[name] = (var, target, flag)
            var.trace_add('write', lambda *a, t=target: self._update_toolchain_state_and_preview(t))
            preview_targets.add(target)

        self.preview_labels = {}
        for target in sorted(list(preview_targets)):
            if target == 'None': continue
            button_name = buttons_data.get(target, {}).get('name', target)
            preview_container = ttk.Frame(self.toolchain_options_cb_frame)
            preview_container.pack(fill='x', pady=(5,0))
            ttk.Label(preview_container, text=f"{button_name or target} Preview:", foreground="gray").pack(side='left', anchor='nw', padx=(0,5))
            
            preview_label = ttk.Label(preview_container, text="", relief='sunken', padding=2, justify='left')
            preview_label.pack(fill='x', expand=True)
            self.preview_labels[target] = preview_label
            self._update_toolchain_state_and_preview(target)
        
        self.rebuild_action_buttons()
        if self.settings_window_instance and self.settings_window_instance.winfo_exists():
            self.settings_window_instance.refresh_profile_display()

    def _update_preview_wraps(self, event=None):
        if not hasattr(self, 'preview_labels') or not hasattr(self, 'toolchain_options_cb_frame'): return
        width = self.toolchain_options_cb_frame.winfo_width()
        if width > 20:
            for label in self.preview_labels.values():
                label.config(wraplength=width - 110)

    def _update_toolchain_state_and_preview(self, target_button=None):
        toolchain_name = self.toolchain_type.get()
        if not toolchain_name: return

        if 'ToolchainStates' not in self.config: self.config['ToolchainStates'] = {}
        for name, (var, _, _) in self.toolchain_option_vars.items():
            key = f"{toolchain_name}_{name.replace(' ', '_')}"
            self.config['ToolchainStates'][key] = str(var.get())

        if target_button and target_button in self.preview_labels:
            try:
                toolchain_data = self.config['Toolchains'][toolchain_name]
                buttons_data = ast.literal_eval(toolchain_data.get('custom_buttons', '{}'))
                base_command = buttons_data.get(target_button, {}).get('command', '')
            except (KeyError, ValueError, SyntaxError): base_command = ''

            preview_cmd = self.resolve_command_placeholders(
                action_key=None, command_override=base_command,
                replacements_override={'t': toolchain_data.get('path', toolchain_name)}, 
                resolve_tool_paths=False, target_button=target_button
            )
            self.preview_labels[target_button].config(text=preview_cmd)
        
        self.save_config()

    def on_closing(self):
        self._save_paths_to_config()
        self.config['Geometry']['main_window'] = self.root.geometry()
        self.save_config()
        if self.process and self.process.poll() is None: self.process.terminate()
        self.root.destroy()
    #commented out to make this change for windows, as it refused to open the right directory
    #def browse_source_file(self):
    #   if path := filedialog.askopenfilename():
    #        self.source_file.set(path)
    #        self.save_config()
    
    def browse_source_file(self):
        current_source = self.source_file.get()
        if current_source and os.path.isfile(current_source):
            # If a valid source file is already loaded, start in its directory.
            initial_dir = os.path.dirname(current_source)
        else:
            # Otherwise, start in the current working directory.
            initial_dir = os.getcwd()

        if path := filedialog.askopenfilename(initialdir=initial_dir):
            self.source_file.set(path)
            self.save_config()

    def browse_output_file(self):
        InfoDialog(self.root, "Information", "The output path is now determined automatically based on the Source File.")

    def log_output(self, text, raw=False, tag=None):
        def _log():
            self.output_text.config(state='normal')
            if raw: self.ansi_handler.write(text)
            else: self.output_text.insert(tk.END, text + '\n', (tag,) if tag else ())
            self.output_text.see(tk.END)
            self.output_text.config(state='disabled')
        if self.root.winfo_exists(): self.root.after(0, _log)

    def process_output_queue(self):
        try:
            while True: self.log_output(self.output_queue.get_nowait(), raw=True)
        except queue.Empty: pass
        finally: self.root.after(100, self.process_output_queue)

    def is_autotyper_active(self):
        profile_name = self.config['Options'].get('active_auto_typer_profile')
        if not profile_name or profile_name == '-- No Profile Selected --':
            return False
        try:
            profile_str = self.config['AutoTyperProfiles'].get(profile_name, '{}')
            profile_data = ast.literal_eval(profile_str)
            return profile_data.get('master_enabled', 'False').lower() == 'true'
        except (ValueError, SyntaxError):
            return False

    def update_autotyper_indicator(self):
        self.autotyper_label.config(text="A-R" if self.is_autotyper_active() else "")

    def _on_settings_close(self):
        self.settings_window_instance = None

    def open_settings(self):
        if self.settings_window_instance and self.settings_window_instance.winfo_exists():
            self.settings_window_instance.lift()
            self.settings_window_instance.focus_force()
        else:
            self.settings_window_instance = SettingsWindow(self.root, self, self._on_settings_close)

    def open_about_window(self):
        about_win = tk.Toplevel(self.root)
        about_win.title(f"Developer Command Cycle v{APP_VERSION} - User Manual")
        about_win.geometry("800x700"); about_win.transient(self.root); about_win.grab_set()

        text_area = tk.Text(about_win, wrap='word', relief='flat', font=('Helvetica', 10), padx=10, pady=10)
        scrollbar = ttk.Scrollbar(about_win, orient='vertical', command=text_area.yview)
        text_area.config(yscrollcommand=scrollbar.set)
        text_area.pack(side="left", fill="both", expand=True); scrollbar.pack(side="right", fill="y")
        
        fonts = {'h1': tkfont.Font(font=text_area['font'], size=16, weight='bold', underline=True),
                 'h2': tkfont.Font(font=text_area['font'], size=12, weight='bold'),
                 'h3': tkfont.Font(font=text_area['font'], size=10, weight='bold', underline=True),
                 'bold': tkfont.Font(font=text_area['font'], weight='bold'), 'italic': tkfont.Font(font=text_area['font'], slant='italic'),
                 'mono': ("Courier", 9)}
        text_area.tag_configure("h1", font=fonts['h1'], spacing3=15, justify='center')
        text_area.tag_configure("h2", font=fonts['h2'], spacing1=10, spacing3=5)
        text_area.tag_configure("h3", font=fonts['h3'], spacing1=8, spacing3=4)
        text_area.tag_configure("bold", font=fonts['bold']); text_area.tag_configure("italic", font=fonts['italic'])
        text_area.tag_configure("mono", font=fonts['mono'], background="#f0f0f0", lmargin1=20, lmargin2=20, rmargin=20, spacing1=5, spacing3=5, wrap='none')

        manual_content = [
                (f"Developer Command Cycle v{APP_VERSION} - User Manual\n", "h1"),
                (f"Author: RetroGameGirl (v{APP_VERSION})\n\n", ""),
                (f"Script Location:\n", "h3"),
                (f"The currently running script is located at:\n{os.path.abspath(__file__)}\n\n", "mono"),
                (f"Current Working Directory:\n", "h3"),
                (f"The project INI file will be loaded from or saved to:\n{os.getcwd()}\n\n", "mono"),
                ("1. INTRODUCTION\n", "h2"),
                ("Welcome to the Developer Command Cycle. This tool is a graphical front-end for automating command-line build processes. While it began as a personal utility for Atari 7800 homebrew development, it has evolved into a flexible, toolchain-based application suitable for any command-line driven project.\n\n"
                 "The core philosophy is to provide a simple, persistent UI for complex build chains, removing the need to repeatedly type commands. Everything is designed to be highly configurable through graphical menus, from tool paths to custom action buttons.\n\n", ""),
                ("2. QUICK START: YOUR FIRST BUILD\n", "h2"),
                ("Follow these steps to get your first project running:\n\n"
                  " 0. Ensure that the script is in a folder that is in your system path.\n"
                 f" 1.  **Launch in Your Project Folder:** Run the `devCMDcycle.py` script from the command line inside your project's main directory. It will create a fresh `{CONFIG_FILE_NAME}` file there for you.\n"
                 " 2.  **Select Your Source File:** On the main window, click the `...` button next to 'Source File' and choose your primary code file (e.g., `main.asm`, `main.c`).\n"
                 " 3.  **Configure Your Tool:** Click `Settings`, then `Edit Toolchains`. Select a toolchain to modify (e.g., `7800ASMDevKit`) and in the 'Executable Path' field, enter the command for your compiler or assembler (e.g., `dasm`). Click `Save & Close`.\n"
                 " 4.  **Build Your Project:** Back on the main window, click a pre-configured action like `Build`. The output from your tool will appear in the Status Window below.\n\n" " 5. Or just use the drop down toolchains that I orginally setup for my own Atari 7800 build environment and modify that. :)\n\n", " "),
                ("3. CONFIGURATION & DATA\n", "h2"),
                ("The application's state is managed through a single configuration file and a backup directory.\n\n", ""),
                ("Key Features:\n", "h3"),
                (f" • Project-Specific Configurations: The application saves its configuration to a `{CONFIG_FILE_NAME}` file in your current working directory, allowing you to maintain a unique setup for each project based on your preset Default_Configuration.\n"
                 " • Live-Saving INI: All configurations are saved to the local `.ini` file in real-time. Any change in the settings windows is committed as soon as you make it.\n"
                 " • Portable & Path-Aware: The application is self-contained and can be run from your system's PATH, automatically detecting its own location for self-modification tasks.\n"
                 " • Fully Configurable UI: Define toolchain button configurations, custom action buttons with colors, toolchain-specific command-line options, and multi-step Auto-Typer profiles.\n"
                 " • Integrated Default Toolchain and Auto-Typer profile Editor: These built-in editors allow you to safely modify the script's own factory default settings, with automatic backup and rollback capabilities.\n"
                 " • Auto-Typer System: Create profiles for automating interactions with command-line tools that require user input.\n\n", ""),
                ("The INI File:\n", "h3"),
                (f"All settings are stored in `{CONFIG_FILE_NAME}`, located in your project's working directory (wherever you run the script from). This file is created automatically on the first run, allowing for per-project configurations.", ""),
                ("Crucially, any change you make in the Settings, Toolchain, or Auto-Typer windows is saved to this file the moment it happens", "bold"),
                (" (e.g., when you toggle a checkbox or click away from a text field). This ensures your configuration is always up-to-date without needing to manually save before closing a window.\n\n", ""),
                ("The Backup Folders:\n", "h3"),
                (f"The application automatically creates two backup folders to protect your data:\n"
                 f" • `{INI_BACKUP_DIR}`: Created in your project's current working directory. This folder stores backups of your `{CONFIG_FILE_NAME}` file whenever you reset to the default configuration.\n"
                 f" • `{SCRIPT_BACKUP_DIR}`: Created in the same directory where the `devCMDcycle.py` script itself is located. This stores backups of the actual program file whenever you use the built-in editor to update its internal `DEFAULT_CONFIG`.\n"
                 "This separation keeps your project-specific settings and the core application backups organized and safe.\n\n", ""),
                ("4. THE MAIN WINDOW\n", "h2"),
                ("The main window is your central hub for managing and building your project.\n\n", ""),
                ("Project Frame:\n", "h3"),
                (" • Source File: This is the path to your primary source file (e.g., your .s, .asm, or .c file). This path is used by command placeholders like %f (full path) and %s (path without extension).\n", ""),
                (" • Toolchain: Select the active build configuration. Each toolchain defines its own set of custom buttons and command-line options.\n\n", ""),
                ("Toolchain Options Frame:\n", "h3"),
                ("This area displays checkboxes for optional command-line flags specific to the selected toolchain. Enabling an option adds its corresponding flag to the command of its target button. A live preview of the final command is shown below the checkboxes for clarity.\n\n", ""),
                ("Actions Frame:\n", "h3"),
                ("This contains all the executable actions.\n", ""),
                (" • Settings: Opens the Global Settings window.\n", ""),
                (" • Open Folder: Opens the directory containing your source file in the system's file explorer.\n", ""),
                (" • Clean: Deletes temporary build files from your project directory based on the extensions configured in Settings.\n", ""),
                (" • Custom Buttons (Button 1-10): These are fully configurable. They can run a single command, an external program, or a sequence of other button actions.\n\n", ""),
                ("Status Window:\n", "h3"),
                ("This is where all output from your build tools is displayed in real-time. It supports ANSI color codes for better readability. An input box at the bottom allows you to send commands to interactive tools, and the 'Break' button can terminate a running process.\n\n", ""),
                ("5. ADVANCED FEATURES & COMMANDS\n", "h2"),
                ("The true power of the application lies in its flexible command system.\n\n", ""),
                ("Command Placeholders:\n", "h3"),
                ("When configuring buttons, you can use these special placeholders which will be automatically replaced with the correct paths at runtime:\n"
                 " • `%f`: Full path to the Source File (e.g., `/path/to/project/source.ext`)\n"
                 " • `%s`: Source file stem, without the extension (e.g., `/path/to/project/source`)\n"
                 " • `%o`: Output file stem (same as `%s` by default)\n"
                 " • `%t`: Full path to the selected Toolchain executable\n"
                 " • `%e`: Path to the default Editor\n"
                 " • `%m`: Path to the default Emulator\n"
                 " • `%h`: Path to the Header Tool\n"
                 " • `%g`: Path to the Signer Tool\n"
                 " • `%term`: Path to the Terminal\n\n", ""),
                ("Composite & External Commands:\n", "h3"),
                (" • **Composite Actions:** You can chain multiple button actions together by listing their internal names, separated by commas, in a button's command field. For example, a command of `Button3,Button4,Button6` will execute the actions for Button 3, then Button 4, and finally Button 6 in sequence. This is perfect for creating a complete 'Build, Header, and Run' sequence with one click.\n"
                 " • **External Commands:** If you need to run a command in a new, separate terminal window (useful for GUIs or interactive tools), simply add the prefix `EXTERNAL:` to the command string. For example: `EXTERNAL:%m a7800 -cart %s.a78`.\n\n", ""),
                ("6. THE SETTINGS WINDOW\n", "h2"),
                ("This window allows you to configure global settings and access the toolchain editors.\n\n", ""),
                ("Paths to Tools:\n", "h3"),
                ("Define the paths to your command-line executables. These are essential for the command placeholders (%e, %m, %h, etc.) to work correctly. If you provide just a name (e.g., `dasm`), the program will rely on your system's PATH to find it.\n\n", ""),
                ("Copying Existing Toolchains & Profiles\n", "h3"),
                ("To streamline the creation of new configurations, both the Toolchain Editor and the Auto-Typer Profile Editor have a 'Copy' button. This allows you to duplicate a selected configuration and give it a new name. The application will validate the new name to ensure it doesn't already exist or conflict with a reserved system name.\n\n", ""),
                ("Editing and Resetting the Default Config\n", "h3"),
                ("The settings menu includes powerful tools for managing the application's built-in default configuration.\n"
                 " • Edit Default Config: This opens a live editor that lets you modify the internal `DEFAULT_CONFIG` dictionary using the familiar INI format. When you click 'Update devCMDcycle.py', the script is patched, a backup is created, and you are given the option to immediately reset your current INI to use the new defaults.\n"
                 " • Roll Back: This restores the script from a previously created backup, undoing any changes to the defaults.\n"
                 " • Reset to Factory Defaults: This provides a safe way to reset your `.ini` file. It backs up your current INI and exits, allowing a fresh configuration to be generated on the next start.\n\n", ""),
                ("The Auto-Typer Profile Editor\n", "h3"),
                ("This window is the heart of the dynamic auto-typer system. You can create multiple profiles, each with up to 5 tabbed steps. Within each step, you can define a sequence of commands to be automatically typed into interactive prompts. It supports special placeholders like %b<num> to create text entry boxes in the main UI for dynamic input.\n\n", ""),
                ("7. LICENSE INFORMATION\n", "h2"),
                ("This software is licensed under the GNU General Public License version 3.\n"
                 "See [https://www.gnu.org/licenses/gpl-3.0.html](https://www.gnu.org/licenses/gpl-3.0.html) for details.\n", "")
            ]





        for text, tag in manual_content: text_area.insert(tk.END, text, (tag,) if tag else ())
        text_area.config(state='disabled')

    def resolve_command_placeholders(self, action_key, replacements_override=None, resolve_tool_paths=True, command_override=None, target_button=None, toolchain_context=None):
        command_template = command_override if command_override is not None else self.config.get('Actions', {}).get(action_key, '')
        
        paths = self.config.get('Paths', {}); source_path_full = self.source_file.get()
        source_stem = os.path.splitext(source_path_full)[0] if source_path_full else ''
        
        replacements = {'f': shlex.quote(source_path_full), 's': shlex.quote(source_stem), 'o': shlex.quote(source_stem)}
        if resolve_tool_paths:
            replacements.update({k: shlex.quote(paths.get(v, '')) for k, v in 
                                 [('e', 'editor'), ('m', 'emulator'), ('h', 'header_tool'), ('g', 'signer_tool'), ('term', 'terminal')]})

        current_toolchain_name = toolchain_context or self.toolchain_type.get()
        if current_toolchain_name:
            toolchain_path = self.config.get('Toolchains', {}).get(current_toolchain_name, {}).get('path', '')
            replacements['t'] = shlex.quote(toolchain_path) if resolve_tool_paths and toolchain_path else toolchain_path or current_toolchain_name
        
        if replacements_override: replacements.update(replacements_override)
        
        resolved_cmd = command_template
        for key, value in replacements.items(): resolved_cmd = resolved_cmd.replace(f'%{key}', value)

        if target_button:
            for _, (var, target, flag_template) in self.toolchain_option_vars.items():
                if var.get() and target == target_button:
                    resolved_cmd += f" {flag_template.replace('%s', source_stem).replace('%o', source_stem).replace('%f', source_path_full)}"
        return resolved_cmd

    def log_and_run(self, button_name, action, *args, **kwargs):
        self.log_output(f"\n--- {button_name} button pressed ---", tag='info'); action(*args, **kwargs)

    def run_command(self, on_success, command_override, target_button, autotyper_trigger_key=None):
        if self.command_running and self.process and self.process.poll() is None:
            self.log_output("Error: An internal command is already running.", tag='error')
            if on_success: self.root.after(10, on_success)
            return

        final_command_str = self.resolve_command_placeholders(action_key=None, command_override=command_override, target_button=target_button)
        is_external, is_nop = final_command_str.strip().startswith('EXTERNAL:'), final_command_str.strip() == '%NOP'

        if is_external:
            self.run_external_command(final_command_str.strip()[len('EXTERNAL:'):].strip(), on_success)
            if autotyper_trigger_key: self.execute_internal_command("", on_success=None, autotyper_trigger_key=autotyper_trigger_key, close_after_typing=True)
        elif is_nop or not final_command_str.strip():
            if autotyper_trigger_key: self.execute_internal_command("", on_success, autotyper_trigger_key=autotyper_trigger_key, close_after_typing=True)
            elif on_success: self.root.after(10, on_success)
        else:
            self.log_output(f"$ {final_command_str}", tag='user_input')
            self.execute_internal_command(final_command_str, on_success, autotyper_trigger_key=autotyper_trigger_key)

    def run_external_command(self, command_to_run, on_success=None):
        self.log_output(f"$ (External) {command_to_run}", tag='user_input')
        try:
            use_shell = sys.platform == "win32"
            subprocess.Popen(command_to_run if use_shell else shlex.split(command_to_run), 
                             cwd=os.path.dirname(self.source_file.get()) or None, shell=use_shell, 
                             creationflags=subprocess.DETACHED_PROCESS if use_shell else 0)
            if on_success: self.root.after(10, on_success)
        except Exception as e:
            self.log_output(f"Error launching external process: {e}", tag='error')
            if on_success: self.root.after(10, on_success)

    def execute_internal_command(self, command_string, on_success, autotyper_trigger_key=None, close_after_typing=False):
        if self.command_running:
            self.log_output("Error: An internal command is already running.", tag='error')
            if on_success: self.root.after(10, on_success)
            return

        working_dir, is_dummy = (os.path.dirname(self.source_file.get()) if self.source_file.get() else None), not command_string.strip()
        try:
            self.set_command_running_state(True)
            reader_thread_arg = None
            if sys.platform != "win32":
                cmd_list = ['/bin/sh', '-i'] if is_dummy else shlex.split(command_string)
                self.master_fd, slave_fd = pty.openpty()
                self.process = subprocess.Popen(cmd_list, stdin=slave_fd, stdout=slave_fd, stderr=subprocess.STDOUT, cwd=working_dir, preexec_fn=os.setsid)
                os.close(slave_fd)
                reader_thread_arg = self.master_fd
            else:
                # WINDOWS FIX: Use text=True and pass the stream object, not the file descriptor.
                self.process = subprocess.Popen('cmd.exe' if is_dummy else command_string, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, cwd=working_dir, text=True, bufsize=1, creationflags=subprocess.CREATE_NO_WINDOW, shell=True)
                reader_thread_arg = self.process.stdout

            threading.Thread(target=self._read_stream_to_queue, args=(reader_thread_arg,), daemon=True).start()
            self.root.after(100, self.poll_process, on_success)
            if autotyper_trigger_key:
                threading.Thread(target=self._run_automated_header_sequence, args=(autotyper_trigger_key, close_after_typing), daemon=True).start()
        except Exception as e: 
            self.log_output(f"An error occurred: {e}", tag='error'); self.set_command_running_state(False)

    def _read_stream_to_queue(self, stream_obj_or_fd):
        # WINDOWS FIX: This function now handles both the Windows text stream object
        # and the Unix file descriptor correctly.
        if sys.platform == "win32":
            # On Windows, read line by line from the text stream object. This avoids the deadlock.
            try:
                for line in iter(stream_obj_or_fd.readline, ''):
                    if not self.command_running: break
                    self.output_queue.put(line)
                stream_obj_or_fd.close()
            except (IOError, ValueError):
                # This can happen if the process closes abruptly.
                pass
        else:
            # On Unix-like systems, continue to read from the raw file descriptor.
            try:
                while self.command_running:
                    data = os.read(stream_obj_or_fd, 1024)
                    if not data: break
                    self.output_queue.put(data.decode('utf-8', errors='replace'))
            except (OSError, ValueError):
                pass
            finally:
                if self.master_fd is not None:
                    try: os.close(self.master_fd)
                    except OSError: pass


    def poll_process(self, on_success_callback):
        if not self.command_running or not self.process: return
        if self.process.poll() is None: return self.root.after(100, self.poll_process, on_success_callback)
        
        tag, msg = ('success', 'successfully') if self.process.returncode == 0 else ('error', 'with error')
        self.log_output(f"\n--- Process finished {msg} (Code: {self.process.returncode}) ---\n", tag=tag)
        if on_success_callback and self.process.returncode == 0: self.root.after(10, on_success_callback)
        
        self.process, self.master_fd = None, None
        self.set_command_running_state(False)

    def set_command_running_state(self, is_running):
        self.command_running = is_running
        if self.root.winfo_exists():
            self.break_button.config(state='normal' if is_running else 'disabled')
            if is_running: self.input_entry.focus_set()

    def _run_automated_header_sequence(self, trigger_key, close_after=False):
        try:
            opts = self.config['Options']
            initial_delay = float(opts.get('header_initial_delay', 1.0))
            command_delay = float(opts.get('header_command_delay', 0.5))
            profile_name = opts.get('active_auto_typer_profile')
            if not profile_name: return
            profile_data = ast.literal_eval(self.config['AutoTyperProfiles'].get(profile_name, '{}'))
        except (ValueError, SyntaxError, KeyError): return self.log_output("Error: Could not parse auto-typer profile.", tag='error')
            
        time.sleep(initial_delay)
        for step_key, step in sorted(profile_data.items()):
            if not isinstance(step, dict): continue
            if not self.command_running: break
            for item in step.get('commands', []):
                if not self.command_running: break
                if item.get('label') == trigger_key and item.get('enabled', 'False').lower() == 'true':
                    command_str = re.sub(r'%b\d+', lambda m: item.get('text', ''), item.get('command', ''))
                    self._send_auto_typer_command(command_str)
                    time.sleep(command_delay)
            
        self.root.after(0, lambda: self.input_entry.delete(0, tk.END))
        if close_after and self.process and self.process.poll() is None:
            time.sleep(0.5)
            self.log_output("\n--- Auto-typer sequence finished, closing dummy process. ---", tag='info')
            self._send_bytes_to_process(b'exit\n')
            if sys.platform == "win32": self.process.terminate()

    def _send_auto_typer_command(self, command):
        parts = re.split(r'(%[CA]<.>)', command)
        for part in filter(None, parts):
            if not self.command_running: break
            if match := re.match(r'%([CA])<(.)>', part):
                mod, key = match.groups()
                self.log_output(f"Sending {mod.replace('C', 'CTRL').replace('A', 'ALT')}+{key}", tag='prompt')
                if mod == 'C': self._send_bytes_to_process(bytes([ord(key.lower()) - ord('a') + 1]))
                elif mod == 'A': self._send_bytes_to_process(b'\x1b' + key.lower().encode())
            else:
                self.log_output(f"$ {part}", tag='user_input')
                for char in part: self._send_bytes_to_process(char.encode()); time.sleep(0.03)
        self._send_bytes_to_process(b'\n')

    def _send_bytes_to_process(self, data_bytes):
        if self.command_running and self.process and self.process.poll() is None:
            try:
                if sys.platform != "win32" and self.master_fd: os.write(self.master_fd, data_bytes)
                else: self.process.stdin.write(data_bytes.decode('utf-8', 'replace')); self.process.stdin.flush()
            except (IOError, OSError, BrokenPipeError): self.log_output("Info: Process closed.", tag='info')

    def send_input_to_process(self, event=None, command_to_send=None):
        data = command_to_send if command_to_send is not None else self.input_entry.get() + '\n'
        if self.command_running and self.process and self.process.poll() is None:
            self.log_output(data.strip(), tag='user_input')
            self._send_bytes_to_process(data.encode())
            if command_to_send is None: self.input_entry.delete(0, tk.END)
        elif not self.command_running and command_to_send is None:
            self.run_command(on_success=None, command_override=self.input_entry.get(), target_button=None)
            self.input_entry.delete(0, tk.END)

    def send_break_signal(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.log_output("\n--- Sent break signal ---\n", tag='error')

    def execute_custom_button(self, button_key):
        try:
            toolchain = self.config['Toolchains'][self.toolchain_type.get()]
            buttons_data = ast.literal_eval(toolchain.get('custom_buttons', '{}'))
            command = buttons_data.get(button_key, {}).get('command', '').strip()
            name = buttons_data.get(button_key, {}).get('name', button_key)
        except (KeyError, ValueError, SyntaxError): return

        self.log_output(f"\n--- '{name}' button pressed ---", tag='info')
        def is_autotyper_trigger(key):
            if not self.is_autotyper_active(): return False
            profile_name = self.config['Options'].get('active_auto_typer_profile')
            try:
                profile_data = ast.literal_eval(self.config['AutoTyperProfiles'].get(profile_name, '{}'))
                return any(cmd.get('label') == key and cmd.get('enabled', 'False').lower() == 'true'
                           for step in profile_data.values() if isinstance(step, dict) for cmd in step.get('commands', []))
            except (ValueError, SyntaxError): return False

        if not command and not is_autotyper_trigger(button_key): return
        
        action_queue = deque([b.strip() for b in command.split(',') if b.strip()] if ',' in command 
                             else [command or '%NOP'])
        
        def run_next_in_chain():
            if not action_queue: return
            item = action_queue.popleft()
            is_composite_step = ',' in command
            target_button = item if is_composite_step else button_key
            actual_cmd = buttons_data.get(target_button, {}).get('command', item) if is_composite_step else item
            
            self.run_command(on_success=run_next_in_chain if action_queue else None, command_override=actual_cmd,
                             target_button=target_button, autotyper_trigger_key=target_button if is_autotyper_trigger(target_button) else None)
        run_next_in_chain()

    def clean_project(self):
        source = self.source_file.get()
        if not source: return self.log_output("Error: No source file specified.", tag='error')
        
        extensions = {ext for ext, state in self.config.get('CleanStates', {}).items() if state.lower() == 'true'}
        if not extensions: return self.log_output("No file types checked for cleaning.", tag='info')

        source_stem = os.path.splitext(source)[0]
        deleted_files = []
        for f in {source_stem + ext for ext in extensions}:
            if os.path.exists(f):
                try: os.remove(f); deleted_files.append(os.path.basename(f))
                except OSError as e: self.log_output(f"Error deleting {f}: {e}", tag='error')
        
        self.log_output(f"Cleaned: {', '.join(deleted_files)}" if deleted_files else "No matching files found.", 
                        tag='success' if deleted_files else 'info')

    def open_project_folder(self):
        source = self.source_file.get()
        if not source or not os.path.isdir(d := os.path.dirname(source)):
            return self.log_output("Error: Source directory does not exist.", tag='error')
        try:
            if sys.platform == "win32": os.startfile(d)
            elif sys.platform == "darwin": subprocess.Popen(["open", d])
            else: subprocess.Popen(["xdg-open", d])
        except Exception as e: self.log_output(f"Error opening folder: {e}", tag='error')

    def reset_config_to_defaults(self, confirmed=False):
        if not os.path.exists(CONFIG_FILE_NAME):
            return InfoDialog(self.root, "Nothing to Reset", "No .ini file was found.")

        os.makedirs(INI_BACKUP_DIR, exist_ok=True)
        backup_num = 1
        while os.path.exists(backup_path := os.path.join(INI_BACKUP_DIR, f"{os.path.basename(CONFIG_FILE_NAME)}_backup{backup_num}")):
            backup_num += 1

        if not confirmed:
            confirm_msg = (f"This will back up your current INI to:\n{backup_path}\n\n"
                           "The application will close. Restart to generate a new default configuration.")
            if not ConfirmationDialog(self.root, "Confirm Reset & Exit", confirm_msg).result: return
            
        try:
            shutil.move(CONFIG_FILE_NAME, backup_path)
            InfoDialog(self.root, "Reset Complete", "Configuration backed up. The application will now close.")
            self.root.destroy()
        except Exception as e:
            InfoDialog(self.root, "Error", f"Could not back up the INI file:\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = DevCommanderApp(root)
    root.mainloop()

