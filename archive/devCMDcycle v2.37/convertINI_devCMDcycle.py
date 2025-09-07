#!/usr/bin/env python3
#

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
#
import tkinter as tk
from tkinter import ttk, messagebox, font as tkfont, filedialog
import configparser
import ast
import io
import pprint
import os
import re
import shutil
import glob

# --- Global Constants ---
APP_VERSION = "2.37"
DEFAULT_INI_NAME = "devCMDcycle_237.ini"
DEFAULT_PY_NAME = "devCMDcycle.py"

#-----------------------------------------------------------------------------
# AboutWindow Class
#-----------------------------------------------------------------------------
# Creates a custom, scrollable Toplevel window to display detailed help text.
#-----------------------------------------------------------------------------
class AboutWindow(tk.Toplevel):
    """A custom, scrollable About window with detailed instructions."""
    def __init__(self, master, app_version):
        super().__init__(master)
        self.title(f"About & Instructions - v{app_version}")
        self.geometry("1000x800")
        self.transient(master)
        self.grab_set()

        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)
        main_frame.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)

        text_area = tk.Text(main_frame, wrap='word', relief='flat', font=("Helvetica", 10))
        scrollbar = ttk.Scrollbar(main_frame, orient='vertical', command=text_area.yview)
        text_area.config(yscrollcommand=scrollbar.set)
        
        text_area.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')

        button_frame = ttk.Frame(main_frame, padding=(0, 10, 0, 0))
        button_frame.grid(row=1, column=0, columnspan=2, sticky='e')
        ok_button = ttk.Button(button_frame, text="OK", command=self.destroy)
        ok_button.pack()

        self.add_content(text_area, app_version)

    def add_content(self, text_area, app_version):
        """Adds and formats the content for the About window."""
        h1_font = tkfont.Font(font=text_area['font']); h1_font.configure(size=14, weight='bold', underline=True)
        text_area.tag_configure("h1", font=h1_font, spacing3=10, justify='center')
        h2_font = tkfont.Font(font=text_area['font']); h2_font.configure(size=11, weight='bold')
        text_area.tag_configure("h2", font=h2_font, spacing1=8, spacing3=4)
        bold_font = tkfont.Font(font=text_area['font']); bold_font.configure(weight='bold')
        text_area.tag_configure("bold", font=bold_font)

        title = f"INI to DEFAULT_CONFIG Converter for devCMDcycle.py v{app_version}\n"
        credit = "A utility by RetroGameGirl\n"
        instructions_header = "Instructions\n"
        instructions_body = (
            "This tool provides a live editor for converting `devCMDcycle.ini` format into the Python `DEFAULT_CONFIG` dictionary.\n\n"
            "Live Editing & Synced Scrolling:\n"
            "The top text box is for your INI content. Any changes you make will instantly update the Python code in the read-only 'Live Preview' box below. As you scroll or edit the INI content, the preview will automatically scroll to the corresponding section. Any lines in the preview that change will be temporarily highlighted, making it easy to see the impact of your edits.\n\n"
            "Automated Update:\n"
            "1.  Click 'Select INI File...' to load your config file, which will populate both boxes.\n"
            "2.  Click 'Select devCMDcycle.py...' to choose the Python script you want to update.\n"
            "3.  Click 'Update devCMDcycle.py'. This will ask for confirmation, then create a backup and patch the selected file with the Python code from the preview box.\n"
            "4.  If an update causes an issue, use the 'Roll Back' button to restore your script from a previously created backup.\n\n"
            "Manual Operations:\n"
            "At any time, you can click 'Copy to Clipboard' to copy the contents of the 'Live Preview' box, or 'Exit' to close the application."
        )
        license_header = "\nLicense Information\n"
        license_body = (
            "This program is free software: you can redistribute it and/or modify "
            "it under the terms of the GNU General Public License as published by "
            "the Free Software Foundation, either version 3 of the License, or "
            "(at your option) any later version.\n\n"
            "This program is distributed in the hope that it will be useful, "
            "but WITHOUT ANY WARRANTY; without even the implied warranty of "
            "MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the "
            "GNU General Public License for more details.\n\n"
            "You should have received a copy of the GNU General Public License "
            "along with this program. If not, see <https://www.gnu.org/licenses/>."
        )
        
        text_area.insert(tk.END, title, "h1")
        text_area.insert(tk.END, credit)
        text_area.insert(tk.END, instructions_header, "h2")
        text_area.insert(tk.END, instructions_body)
        text_area.insert(tk.END, license_header, "h2")
        text_area.insert(tk.END, license_body)
        text_area.config(state='disabled')

#-----------------------------------------------------------------------------
# Custom Dialog Classes
#-----------------------------------------------------------------------------
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
        self.deiconify()
        self.wait_window(self)

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
        
        proceed_button = ttk.Button(button_frame, text="Proceed", command=self.on_proceed, style="Update.TButton")
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
        ok_button = ttk.Button(button_frame, text="OK", command=self.destroy, style="Info.TButton")
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
        
        restore_button = ttk.Button(button_frame, text="Restore Latest", command=self.on_restore, style="Rollback.TButton")
        restore_button.pack(side="left", expand=True, padx=5)
        choose_button = ttk.Button(button_frame, text="Choose File...", command=self.on_choose, style="Select.TButton")
        choose_button.pack(side="left", expand=True, padx=5)
        cancel_button = ttk.Button(button_frame, text="Cancel", command=self.on_cancel)
        cancel_button.pack(side="left", expand=True, padx=5)
        
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.center_and_show(parent)

    def on_restore(self): self.result = "latest"; self.destroy()
    def on_choose(self): self.result = "choose"; self.destroy()
    def on_cancel(self): self.result = None; self.destroy()

#-----------------------------------------------------------------------------
# ConverterApp Class
#-----------------------------------------------------------------------------
# The main application class.
#-----------------------------------------------------------------------------
class ConverterApp:
    """
    A GUI tool to convert a full devCMDcycle.ini file into a
    Python dictionary format for the DEFAULT_CONFIG.
    """
    def __init__(self, master):
        self.master = master
        self.master.title(f"INI to DEFAULT_CONFIG Converter for devCMDcycle.py v{APP_VERSION}")
        self.master.geometry("1000x800")
        self.master.minsize(600, 600)

        self.dev_cycle_py_path = tk.StringVar()
        self.ini_path_var = tk.StringVar()
        self.update_timer = None
        self.scroll_timer = None
        self.previous_output_content = ""
        
        self.setup_styles()

        main_frame = ttk.Frame(self.master, padding="10")
        main_frame.pack(fill="both", expand=True)
        main_frame.rowconfigure(0, weight=1); main_frame.rowconfigure(2, weight=1)
        main_frame.columnconfigure(0, weight=1)

        input_labelframe = ttk.LabelFrame(main_frame, text="INI File Content (Live Edit)", padding="5")
        input_labelframe.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        input_labelframe.rowconfigure(0, weight=1); input_labelframe.columnconfigure(0, weight=1)
        
        self.input_yscrollbar = ttk.Scrollbar(input_labelframe, orient="vertical")
        self.input_text = tk.Text(input_labelframe, wrap="word", height=10, undo=True, font=("Courier New", 10), yscrollcommand=self.on_input_scroll)
        self.input_yscrollbar.config(command=self.input_text.yview)
        
        self.input_text.grid(row=0, column=0, sticky="nsew")
        self.input_yscrollbar.grid(row=0, column=1, sticky="ns")
        self.input_text.bind("<KeyRelease>", self.schedule_update)

        controls_container = ttk.Frame(main_frame); controls_container.grid(row=1, column=0, pady=10, sticky='ew')
        controls_container.columnconfigure(1, weight=1)

        instructions_frame = ttk.Frame(controls_container); instructions_frame.grid(row=0, column=0, sticky='ns', padx=(0, 5))
        self.instructions_button = ttk.Button(instructions_frame, text="Instructions", command=self.show_about, style="Info.TButton")
        self.instructions_button.pack(expand=True, fill='both')

        auto_frame = ttk.LabelFrame(controls_container, text="Automated Update", padding=10)
        auto_frame.grid(row=0, column=1, sticky='nsew', padx=5)
        ini_row = ttk.Frame(auto_frame); ini_row.pack(fill='x', expand=True, pady=(0, 5)); ini_row.columnconfigure(1, weight=1)
        ttk.Button(ini_row, text="Select INI File...", command=self.open_ini_file, style="Select.TButton").grid(row=0, column=0)
        ttk.Entry(ini_row, textvariable=self.ini_path_var, state='readonly').grid(row=0, column=1, sticky='ew', padx=5)
        py_row = ttk.Frame(auto_frame); py_row.pack(fill='x', expand=True, pady=(0, 10)); py_row.columnconfigure(1, weight=1)
        ttk.Button(py_row, text="Select devCMDcycle.py...", command=self.select_dev_cycle_py, style="Select.TButton").grid(row=0, column=0)
        ttk.Entry(py_row, textvariable=self.dev_cycle_py_path, state='readonly').grid(row=0, column=1, sticky='ew', padx=5)
        
        update_rollback_frame = ttk.Frame(auto_frame)
        update_rollback_frame.pack(fill='x', expand=True)
        update_rollback_frame.columnconfigure(0, weight=1)
        update_rollback_frame.columnconfigure(1, weight=1)
        
        self.update_button = ttk.Button(update_rollback_frame, text="Update devCMDcycle.py", command=self.update_dev_cycle_file, style="Update.TButton")
        self.update_button.grid(row=0, column=0, sticky='ew', padx=(0,5))
        self.rollback_button = ttk.Button(update_rollback_frame, text="Roll Back", command=self.rollback_file, style="Rollback.TButton")
        self.rollback_button.grid(row=0, column=1, sticky='ew', padx=(5,0))

        manual_ops_frame = ttk.Frame(controls_container); manual_ops_frame.grid(row=0, column=2, sticky='ns', padx=5)
        self.copy_button = ttk.Button(manual_ops_frame, text="Copy to Clipboard", command=self.copy_to_clipboard, style="Manual.TButton")
        self.copy_button.pack(expand=True, fill='both', pady=(0,2))
        self.exit_button = ttk.Button(manual_ops_frame, text="Exit", command=self.master.quit, style="Exit.TButton")
        self.exit_button.pack(expand=True, fill='both', pady=(2,0))
        
        output_labelframe = ttk.LabelFrame(main_frame, text="Generated DEFAULT_CONFIG Code (Live Preview)", padding="5")
        output_labelframe.grid(row=2, column=0, sticky="nsew", pady=(10, 0))
        output_labelframe.rowconfigure(0, weight=1); output_labelframe.columnconfigure(0, weight=1)
        y_scrollbar = ttk.Scrollbar(output_labelframe, orient="vertical"); x_scrollbar = ttk.Scrollbar(output_labelframe, orient="horizontal")
        self.output_text = tk.Text(output_labelframe, wrap="none", height=10, state="disabled", font=("Courier New", 10), yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set, background="#fdf5e6")
        self.output_text.tag_configure("highlight", background="#ffffd0")
        y_scrollbar.config(command=self.output_text.yview); x_scrollbar.config(command=self.output_text.xview)
        self.output_text.grid(row=0, column=0, sticky="nsew"); y_scrollbar.grid(row=0, column=1, sticky="ns"); x_scrollbar.grid(row=1, column=0, columnspan=2, sticky="ew")

    def setup_styles(self):
        style = ttk.Style(self.master)
        style.configure("Info.TButton", background="#cceeff", font=('Helvetica', 10))
        style.configure("Select.TButton", background="#d4edda", font=('Helvetica', 10))
        style.configure("Update.TButton", background="#a7d7c5", font=('Helvetica', 10, 'bold'))
        style.configure("Manual.TButton", background="#ffd8b1", font=('Helvetica', 10))
        style.configure("Rollback.TButton", background="#f8d7da", font=('Helvetica', 10, 'bold'))
        style.configure("Exit.TButton", background="#e9ecef", font=('Helvetica', 10))

    def on_input_scroll(self, *args):
        """Handle scroll events for the top INI text box."""
        self.input_yscrollbar.set(*args)
        if self.scroll_timer: self.master.after_cancel(self.scroll_timer)
        self.scroll_timer = self.master.after(100, self.sync_views)

    def sync_views(self):
        """Scroll the output preview to match the visible section of the input."""
        try:
            index = self.input_text.index(tk.INSERT)
            input_line_num = int(index.split('.')[0])
            
            current_section = None
            for i in range(input_line_num, 0, -1):
                line = self.input_text.get(f"{i}.0", f"{i}.end")
                if line.strip().startswith('['):
                    current_section = line.strip()[1:-1]
                    break
            
            if not current_section: return

            if current_section.startswith("Toolchain:"):
                py_key = f"'{current_section.split(':', 1)[1]}': {{"
            else:
                py_key = f"'{current_section}': {{"
            
            pos = self.output_text.search(py_key, "1.0", tk.END)
            if pos: self.output_text.see(pos)
        except (ValueError, tk.TclError): pass

    def schedule_update(self, event=None):
        if self.update_timer: self.master.after_cancel(self.update_timer)
        self.update_timer = self.master.after(500, self.convert_ini_to_py)

    def open_ini_file(self):
        filepath = filedialog.askopenfilename(
            title="Open INI File",
            filetypes=(
                ("Config INI", DEFAULT_INI_NAME),
                ("INI Files", "*.ini"),
                ("All Files", "*.*")
            )
        )
        if not filepath: return
        self.ini_path_var.set(filepath)
        try:
            with open(filepath, 'r', encoding='utf-8') as f: content = f.read()
            self.input_text.delete("1.0", tk.END); self.input_text.insert("1.0", content)
            self.schedule_update()
        except Exception as e: InfoDialog(self.master, "File Error", f"Failed to read file:\n{e}")

    def select_dev_cycle_py(self):
        filepath = filedialog.askopenfilename(
            title="Select devCMDcycle.py",
            filetypes=(
                ("Target Script", DEFAULT_PY_NAME),
                ("Python Scripts", "*.py"),
                ("All Files", "*.*")
            )
        )
        if filepath:
            self.dev_cycle_py_path.set(filepath)

    def show_about(self): AboutWindow(self.master, APP_VERSION)

    def _format_value(self, value):
        try:
            obj = ast.literal_eval(value)
            if isinstance(obj, (dict, list)):
                pretty_string = pprint.pformat(obj, indent=4, width=120, sort_dicts=False)
                return f"str(\n{''.join(['    ' + line for line in pretty_string.splitlines(True)])}    )"
            else: return repr(value)
        except (ValueError, SyntaxError): return repr(value)

    def convert_ini_to_py(self):
        try:
            ini_string = self.input_text.get("1.0", tk.END)
            if not ini_string.strip(): self.update_output_text(""); return
            parser = configparser.ConfigParser(interpolation=None); parser.optionxform = str
            parser.read_string(ini_string); config_dict = {}; toolchains = {}
            for section in parser.sections():
                if section.startswith('Toolchain:'): toolchains[section.split(':', 1)[1]] = dict(parser.items(section))
                else: config_dict[section] = dict(parser.items(section))
            if toolchains: config_dict['Toolchains'] = toolchains
            output_lines = ["DEFAULT_CONFIG = {"]
            for i, section_name in enumerate(sorted(config_dict.keys())):
                output_lines.append(f"    '{section_name}': {{")
                section_data = config_dict[section_name]
                for j, key in enumerate(sorted(section_data.keys())):
                    value = section_data[key]
                    if section_name == 'Toolchains':
                        output_lines.append(f"        '{key}': {{")
                        for k, sub_key in enumerate(sorted(value.keys())):
                            output_lines.append(f"            '{sub_key}': {self._format_value(value[sub_key])}{',' if k < len(value.keys()) - 1 else ''}")
                        output_lines.append(f"        }}{',' if j < len(section_data.keys()) - 1 else ''}")
                    else:
                        output_lines.append(f"        '{key}': {self._format_value(value)}{',' if j < len(section_data.keys()) - 1 else ''}")
                output_lines.append(f"    }}{',' if i < len(config_dict.keys()) - 1 else ''}")
            output_lines.append("}"); 
            
            new_output_content = '\n'.join(output_lines)
            self.update_output_text_with_highlight(new_output_content)
            self.previous_output_content = new_output_content
            self.sync_views()

        except configparser.Error: pass
        
    def update_dev_cycle_file(self):
        target_py_file = self.dev_cycle_py_path.get()
        if not target_py_file or not os.path.exists(target_py_file):
            InfoDialog(self.master, "File Not Found", "Please select a valid devCMDcycle.py file first.")
            return

        backup_num = 1
        while True:
            backup_path = f"{target_py_file}_backup{backup_num}"
            if not os.path.exists(backup_path): break
            backup_num += 1
            
        confirm_msg = f"This will replace the DEFAULT_CONFIG in:\n{os.path.basename(target_py_file)}\n\nA backup will be created as:\n{os.path.basename(backup_path)}\n\nAre you sure?"
        if not ConfirmationDialog(self.master, "Confirm Update", confirm_msg).result:
            return

        generated_config = self.output_text.get("1.0", tk.END).strip()
        try:
            shutil.copy2(target_py_file, backup_path)
        except Exception as e:
            InfoDialog(self.master, "Backup Error", f"Could not create backup:\n{e}")
            return
            
        try:
            with open(target_py_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            start_line_index = -1
            indent = ""
            for i, line in enumerate(lines):
                stripped_line = line.lstrip()
                if stripped_line.startswith("DEFAULT_CONFIG"):
                    start_line_index = i
                    indent = line[:len(line) - len(stripped_line)]
                    break

            if start_line_index == -1:
                InfoDialog(self.master, "Update Error", "Could not find `DEFAULT_CONFIG = ...` block in the target file.")
                os.remove(backup_path)
                return

            brace_count = 0
            end_line_index = -1
            has_started = False
            for i in range(start_line_index, len(lines)):
                line = lines[i]
                if '{' in line: has_started = True
                brace_count += line.count('{')
                brace_count -= line.count('}')
                if has_started and brace_count == 0:
                    end_line_index = i
                    break
            
            if end_line_index == -1:
                InfoDialog(self.master, "Update Error", "Could not find the closing brace '}' for the DEFAULT_CONFIG block.")
                os.remove(backup_path)
                return

            indented_config_lines = [indent + line for line in generated_config.splitlines(True)]
            if not indented_config_lines[-1].endswith('\n'): indented_config_lines[-1] += '\n'
            new_content_lines = lines[:start_line_index] + indented_config_lines + lines[end_line_index + 1:]

            with open(target_py_file, 'w', encoding='utf-8') as f:
                f.writelines(new_content_lines)
            InfoDialog(self.master, "Success", f"Update successful!\n\nBackup created at:\n{os.path.basename(backup_path)}")
        except Exception as e:
            InfoDialog(self.master, "Update Error", f"An error occurred:\n{e}")
            shutil.move(backup_path, target_py_file)
    
    def rollback_file(self):
        target_py_file = self.dev_cycle_py_path.get()
        if not target_py_file or not os.path.exists(target_py_file):
            InfoDialog(self.master, "File Not Found", "Please select the devCMDcycle.py file first.")
            return

        backups = sorted(glob.glob(f"{target_py_file}_backup*"))
        if not backups:
            InfoDialog(self.master, "No Backups", "No backup files found for the selected script.")
            return

        latest_backup = backups[-1]
        
        dialog = RollbackDialog(
            self.master, "Roll Back Script",
            f"Found latest backup: {os.path.basename(latest_backup)}\n\n"
            "Do you want to restore this backup, or choose a different one?"
        )
        choice = dialog.result

        backup_to_restore = None
        if choice == "latest":
            backup_to_restore = latest_backup
        elif choice == "choose":
            chosen_backup = filedialog.askopenfilename(
                title="Select a backup file to restore",
                initialdir=os.path.dirname(target_py_file),
                filetypes=(("Backup Files", f"{os.path.basename(target_py_file)}_backup*"), ("All files", "*.*"))
            )
            if not chosen_backup:
                return

            confirm_msg = f"You have selected:\n{os.path.basename(chosen_backup)}\n\nAre you sure you want to restore this file?"
            if ConfirmationDialog(self.master, "Confirm Restore", confirm_msg).result:
                backup_to_restore = chosen_backup
        else:
            return
            
        if not backup_to_restore or not os.path.exists(backup_to_restore):
            return

        try:
            shutil.copy2(backup_to_restore, target_py_file)
            InfoDialog(self.master, "Success", f"Successfully restored '{os.path.basename(target_py_file)}' from '{os.path.basename(backup_to_restore)}'.")
        except Exception as e:
            InfoDialog(self.master, "Rollback Error", f"An error occurred during restore:\n{e}")

    def update_output_text(self, text):
        self.output_text.config(state="normal")
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", text)
        self.output_text.config(state="disabled")

    def update_output_text_with_highlight(self, new_text):
        self.output_text.config(state="normal")
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", new_text)
        
        self.output_text.tag_remove("highlight", "1.0", tk.END)
        old_lines = self.previous_output_content.splitlines()
        new_lines = new_text.splitlines()
        
        min_len = min(len(old_lines), len(new_lines))
        for i in range(min_len):
            if old_lines[i] != new_lines[i]:
                self.output_text.tag_add("highlight", f"{i + 1}.0", f"{i + 1}.end")

        if len(new_lines) > len(old_lines):
            self.output_text.tag_add("highlight", f"{len(old_lines) + 1}.0", f"{len(new_lines)}.end")

        self.output_text.config(state="disabled")

    def copy_to_clipboard(self): self.master.clipboard_clear(); self.master.clipboard_append(self.output_text.get("1.0", tk.END))

if __name__ == "__main__":
    root = tk.Tk()
    app = ConverterApp(root)
    root.mainloop()


