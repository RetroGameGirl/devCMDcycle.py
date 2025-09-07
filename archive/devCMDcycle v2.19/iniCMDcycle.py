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

import tkinter as tk
from tkinter import ttk, messagebox, font as tkfont
import configparser
import ast
import io
import pprint

#-----------------------------------------------------------------------------
# AboutWindow Class
#-----------------------------------------------------------------------------
# Creates a custom, scrollable Toplevel window to display detailed help text,
# including instructions, examples, and license information.
#-----------------------------------------------------------------------------
class AboutWindow(tk.Toplevel):
    """A custom, scrollable About window with detailed instructions."""
    def __init__(self, master):
        super().__init__(master)
        self.title("About & Instructions")
        self.geometry("1000x800")
        self.transient(master)
        self.grab_set()

        #--- Main Layout ---
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)
        main_frame.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)

        #--- Text Area ---
        text_area = tk.Text(main_frame, wrap='word', relief='flat', font=("Helvetica", 10))
        scrollbar = ttk.Scrollbar(main_frame, orient='vertical', command=text_area.yview)
        text_area.config(yscrollcommand=scrollbar.set)
        
        text_area.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')

        #--- Button ---
        button_frame = ttk.Frame(main_frame, padding=(0, 10, 0, 0))
        button_frame.grid(row=1, column=0, columnspan=2, sticky='e')
        ok_button = ttk.Button(button_frame, text="OK", command=self.destroy)
        ok_button.pack()

        #--- Content and Formatting ---
        self.add_content(text_area)

    def add_content(self, text_area):
        """Adds and formats the content for the About window."""
        #--- Define text styles ---
        h1_font = tkfont.Font(font=text_area['font'])
        h1_font.configure(size=14, weight='bold', underline=True)
        text_area.tag_configure("h1", font=h1_font, spacing3=10, justify='center')

        h2_font = tkfont.Font(font=text_area['font'])
        h2_font.configure(size=11, weight='bold')
        text_area.tag_configure("h2", font=h2_font, spacing1=8, spacing3=4)
        
        bold_font = tkfont.Font(font=text_area['font'])
        bold_font.configure(weight='bold')
        text_area.tag_configure("bold", font=bold_font)

        mono_font = ("Courier New", 9)
        text_area.tag_configure("code", font=mono_font, background="#f0f0f0", lmargin1=15, lmargin2=15, rmargin=10, spacing1=5, spacing3=5, wrap='word')

        #--- Content Sections ---
        title = "Toolchain INI to Dictionary Converter\n"
        credit = "A utility by RetroGameGirl\n"
        
        instructions_header = "Instructions\n"
        instructions_body = (
            "This tool helps you convert a toolchain configuration from a standard .ini file format into the Python dictionary format required by the main 7800 Dev Commander script.\n\n"
            "1.  Copy a complete toolchain section from a user's .ini file.\n"
            "2.  Paste the text into the top text box.\n"
            "3.  Click the 'Convert' button.\n"
            "4.  The formatted Python code will appear in the bottom text box.\n"
            "5.  Click 'Copy to Clipboard' and paste the result into the 'Toolchains' dictionary inside the DEFAULT_CONFIG of the main application."
        )

        example_header = "\nExample\n"
        example_input_header = "1. You would paste INI text like this into the top box:\n"
        example_input_code = (
            "[Toolchain:7800ASMDevKit]\n"
            "path = 7800asm\n"
            "build_steps = ['compile_dasm', 'add_header']\n"
            "header_action = add_header\n"
            "toolchain_options = [{'name': 'Generate List File', 'flag': '-l', 'target': 'Button3'}, {'name': 'Generate Symbol File', 'flag': '-s', 'target': 'Button3'}]\n"
            "auto_typer_button = Button8\n"
            "custom_buttons = {'Button1': {'name': 'Terminal', 'command': 'EXTERNAL:%term', 'color': '#e0e0e0'}, 'Button2': {'name': 'Edit', 'command': 'EXTERNAL:%e %f', 'color': '#e0e0e0'}, 'Button3': {'name': 'Build', 'command': '%t %f', 'color': '#90ee90'}, 'Button4': {'name': 'Run', 'command': 'EXTERNAL:%m a7800 -cart %s.s.a78', 'color': '#90ee90'}, 'Button5': {'name': 'Run (Debug)', 'command': 'EXTERNAL:%m a7800 -cart %s.s.a78 -debug', 'color': '#add8e6'}, 'Button6': {'name': 'Build & Run', 'command': 'Button3,Button8,Button4', 'color': '#90ee90'}, 'Button7': {'name': 'Build & Run (Debug)', 'command': 'Button3,Button8,Button5', 'color': '#add8e6'}, 'Button8': {'name': 'Apply Header', 'command': '%h %s.s.bin', 'color': '#e0e0e0'}, 'Button9': {'name': 'Apply Signer', 'command': '%g %s.s.a78', 'color': '#e0e0e0'}, 'Button10': {'name': '', 'command': '', 'color': '#F0F0F0'}}"
        )

        example_output_header = "\n2. The tool will generate this Python code in the bottom box:\n"
        example_output_code = (
            "    '7800ASMDevKit': {\n"
            "        'path': '7800asm',\n"
            "        'build_steps': \"['compile_dasm', 'add_header']\",\n"
            "        'header_action': 'add_header',\n"
            "        'toolchain_options': str(\n"
            "            [\n"
            "                {'flag': '-l', 'name': 'Generate List File', 'target': 'Button3'},\n"
            "                {'flag': '-s', 'name': 'Generate Symbol File', 'target': 'Button3'}\n"
            "            ]\n"
            "        ),\n"
            "        'auto_typer_button': 'Button8',\n"
            "        'custom_buttons': str(\n"
            "            {\n"
            "                'Button1': {'color': '#e0e0e0', 'command': 'EXTERNAL:%term', 'name': 'Terminal'},\n"
            "                'Button2': {'color': '#e0e0e0', 'command': 'EXTERNAL:%e %f', 'name': 'Edit'},\n"
            "                'Button3': {'color': '#90ee90', 'command': '%t %f', 'name': 'Build'},\n"
            "                'Button4': {'color': '#90ee90', 'command': 'EXTERNAL:%m a7800 -cart %s.s.a78', 'name': 'Run'},\n"
            "                'Button5': {'color': '#add8e6', 'command': 'EXTERNAL:%m a7800 -cart %s.s.a78 -debug', 'name': 'Run (Debug)'},\n"
            "                'Button6': {'color': '#90ee90', 'command': 'Button3,Button8,Button4', 'name': 'Build & Run'},\n"
            "                'Button7': {'color': '#add8e6', 'command': 'Button3,Button8,Button5', 'name': 'Build & Run (Debug)'},\n"
            "                'Button8': {'color': '#e0e0e0', 'command': '%h %s.s.bin', 'name': 'Apply Header'},\n"
            "                'Button9': {'color': '#e0e0e0', 'command': '%g %s.s.a78', 'name': 'Apply Signer'},\n"
            "                'Button10': {'color': '#F0F0F0', 'command': '', 'name': ''}\n"
            "            }\n"
            "        )\n"
            "    },"
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
            "along with this program. If not, see: https://www.gnu.org/licenses/gpl-3.0.html"
        )
        
        #--- Insert Content with Tags ---
        text_area.insert(tk.END, title, "h1")
        text_area.insert(tk.END, credit)
        text_area.insert(tk.END, instructions_header, "h2")
        text_area.insert(tk.END, instructions_body)
        text_area.insert(tk.END, example_header, "h2")
        text_area.insert(tk.END, example_input_header)
        text_area.insert(tk.END, f"\n{example_input_code}\n", "code")
        text_area.insert(tk.END, example_output_header)
        text_area.insert(tk.END, f"\n{example_output_code}\n", "code")
        text_area.insert(tk.END, license_header, "h2")
        text_area.insert(tk.END, license_body)
        
        text_area.config(state='disabled') # Make read-only

#-----------------------------------------------------------------------------
# ConverterApp Class
#-----------------------------------------------------------------------------
# This is the main application class. It builds and manages the GUI,
# and handles the core logic of converting the INI text to a Python dict.
#-----------------------------------------------------------------------------
class ConverterApp:
    """
    A GUI tool to convert a toolchain section from an INI file into a
    Python dictionary format for the DEFAULT_CONFIG.
    """
    def __init__(self, master):
        self.master = master
        self.master.title("Toolchain INI to Dictionary Converter")
        self.master.geometry("1000x800")
        self.master.minsize(600, 500)

        #--- Main Layout ---
        main_frame = ttk.Frame(self.master, padding="10")
        main_frame.pack(fill="both", expand=True)

        main_frame.rowconfigure(0, weight=1) 
        main_frame.rowconfigure(1, weight=0)
        main_frame.rowconfigure(2, weight=1) 
        main_frame.columnconfigure(0, weight=1)

        #--- Input Widgets ---
        input_labelframe = ttk.LabelFrame(main_frame, text="Paste INI Toolchain Section Here", padding="5")
        input_labelframe.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        input_labelframe.rowconfigure(0, weight=1)
        input_labelframe.columnconfigure(0, weight=1)
        
        self.input_text = tk.Text(input_labelframe, wrap="word", height=10, undo=True, font=("Courier New", 10))
        self.input_text.grid(row=0, column=0, sticky="nsew")

        #--- Control Widgets ---
        controls_frame = ttk.Frame(main_frame)
        controls_frame.grid(row=1, column=0, pady=5)
        
        self.instructions_button = ttk.Button(controls_frame, text="Instructions", command=self.show_about)
        self.instructions_button.pack(side="left", padx=10)
        
        self.convert_button = ttk.Button(controls_frame, text="Convert", command=self.convert_text)
        self.convert_button.pack(side="left", padx=10)
        
        self.copy_button = ttk.Button(controls_frame, text="Copy to Clipboard", command=self.copy_to_clipboard)
        self.copy_button.pack(side="left", padx=10)

        #--- Output Widgets ---
        output_labelframe = ttk.LabelFrame(main_frame, text="Copy Python Dictionary Code From Here", padding="5")
        output_labelframe.grid(row=2, column=0, sticky="nsew", pady=(10, 0))
        output_labelframe.rowconfigure(0, weight=1)
        output_labelframe.columnconfigure(0, weight=1)

        # Add scrollbars for the output text area
        y_scrollbar = ttk.Scrollbar(output_labelframe, orient="vertical")
        x_scrollbar = ttk.Scrollbar(output_labelframe, orient="horizontal")

        self.output_text = tk.Text(
            output_labelframe, 
            wrap="none", 
            height=10, 
            state="disabled", 
            font=("Courier New", 10),
            yscrollcommand=y_scrollbar.set,
            xscrollcommand=x_scrollbar.set
        )
        
        y_scrollbar.config(command=self.output_text.yview)
        x_scrollbar.config(command=self.output_text.xview)

        self.output_text.grid(row=0, column=0, sticky="nsew")
        y_scrollbar.grid(row=0, column=1, sticky="ns")
        x_scrollbar.grid(row=1, column=0, columnspan=2, sticky="ew")


    def show_about(self):
        #
        # Displays the custom About window.
        #
        AboutWindow(self.master)

    def convert_text(self):
        #
        # This is the core logic function. It parses the INI text from the
        # input box and generates the Python dictionary string in the output.
        #
        ini_string = self.input_text.get("1.0", tk.END)
        if not ini_string.strip():
            self.update_output_text("")
            return

        parser = configparser.ConfigParser(interpolation=None)
        parser.optionxform = str # Preserve case sensitivity

        try:
            # Use StringIO to read the string as if it were a file
            parser.read_file(io.StringIO(ini_string))
            
            output_parts = []
            
            for section in parser.sections():
                if not section.startswith('Toolchain:'):
                    continue
                
                toolchain_name = section.split(':', 1)[1]
                output_parts.append(f"        '{toolchain_name}': {{")

                for key, value in parser.items(section):
                    if key == 'custom_buttons' and value.strip():
                        try:
                            obj = ast.literal_eval(value)
                            if not isinstance(obj, dict):
                                raise ValueError("custom_buttons is not a dictionary")

                            # Sort keys numerically: 'Button1', 'Button2', ..., 'Button10'
                            sorted_keys = sorted(obj.keys(), key=lambda k: int(k.replace('Button', '')))
                            
                            # Manually build the pretty-printed string for the dictionary
                            dict_lines = []
                            for k in sorted_keys:
                                # Use pprint for the inner dictionary for clean formatting
                                inner_dict_str = pprint.pformat(obj[k], indent=4, width=200)
                                dict_lines.append(f"    '{k}': {inner_dict_str},")

                            # Remove the trailing comma from the last button entry
                            if dict_lines:
                                dict_lines[-1] = dict_lines[-1].rstrip(',')

                            formatted_obj_string = "{{\n{}\n}}".format('\n'.join(dict_lines))
                            
                            indented_string = '\n'.join(['            ' + line for line in formatted_obj_string.splitlines()])
                            formatted_value = f"str(\n{indented_string}\n            )"
                            output_parts.append(f"            '{key}': {formatted_value},")

                        except (ValueError, SyntaxError):
                            output_parts.append(f"            '{key}': {repr(value)},")

                    elif key == 'toolchain_options' and value.strip():
                        try:
                            # Standard pprint is fine for lists as order is preserved
                            obj = ast.literal_eval(value)
                            p = pprint.PrettyPrinter(indent=4, width=100, compact=True)
                            formatted_obj_string = p.pformat(obj)
                            
                            indented_string = '\n'.join(['            ' + line for line in formatted_obj_string.splitlines()])
                            formatted_value = f"str(\n{indented_string}\n            )"
                            output_parts.append(f"            '{key}': {formatted_value},")
                        except (ValueError, SyntaxError):
                            output_parts.append(f"            '{key}': {repr(value)},")
                    else:
                         output_parts.append(f"            '{key}': {repr(value)},")
                
                # Remove trailing comma from the last item in the toolchain dict
                if output_parts and output_parts[-1].endswith(','):
                    output_parts[-1] = output_parts[-1][:-1]
                    
                output_parts.append("        },")

            # Remove the trailing comma from the last toolchain entry
            if output_parts and output_parts[-1].endswith(','):
                output_parts[-1] = output_parts[-1][:-1]

            self.update_output_text('\n'.join(output_parts))

        except configparser.Error as e:
            self.update_output_text(f"# Error parsing INI data:\n# {e}")
            messagebox.showerror("INI Parse Error", str(e))

    def update_output_text(self, text):
        #
        # Safely updates the read-only output text widget.
        #
        self.output_text.config(state="normal")
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", text)
        self.output_text.config(state="disabled")

    def copy_to_clipboard(self):
        #
        # Copies the content of the output text box to the system clipboard.
        #
        self.master.clipboard_clear()
        self.master.clipboard_append(self.output_text.get("1.0", tk.END))

#-----------------------------------------------------------------------------
# Main Execution Block
#-----------------------------------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = ConverterApp(root)
    root.mainloop()


