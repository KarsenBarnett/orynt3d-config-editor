import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import json
from core import scanner, indexer, mapper, editor, generator, logger

class AutocompleteCombobox(ttk.Combobox):
    def set_completion_list(self, completion_list):
        self._completion_list = sorted(completion_list, key=str.lower)
        self['values'] = self._completion_list
        self._hits = []
        self.position = 0
        self.bind('<KeyRelease>', self.handle_keyrelease)

    def autocomplete(self, delta=0):
        if delta:
            self.delete(self.position, tk.END)
        else:
            self.position = len(self.get())
        # Collect hits
        hits = [elem for elem in self._completion_list if elem.lower().startswith(self.get().lower())]
        if hits != self._hits:
            self._hits = hits
            self.hit_index = 0
        if hits == []:
            return
        self.delete(0, tk.END)
        self.insert(0, hits[self.hit_index])
        self.select_range(self.position, tk.END)

    def handle_keyrelease(self, event):
        if event.keysym == "BackSpace":
            self.position = self.index(tk.END)
        elif event.keysym == "Left":
            if self.position < self.index(tk.END):
                self.position = self.position - 1
        elif event.keysym == "Right":
            self.position = self.index(tk.END)
        else:
            self.autocomplete()

class TagEditorGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Image Tag Editor GUI")
        self.geometry("900x700")

        # Load attribute data from mapper
        self.required_keys = mapper.get_required_keys()
        self.attributes_yaml = mapper.load_attribute_yaml()

        self.create_widgets()
        self.current_folder = None
        self.xmp_files = []
        self.filtered_files = []
        self.current_file_index = None

        # Redirect logger output to GUI log panel
        logger.set_log_callback(self.append_log)

    def create_widgets(self):
        # Folder and search frame
        top_frame = ttk.Frame(self)
        top_frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(top_frame, text="Folder:").pack(side='left')
        self.folder_var = tk.StringVar()
        folder_entry = ttk.Entry(top_frame, textvariable=self.folder_var, width=50)
        folder_entry.pack(side='left', padx=5)
        ttk.Button(top_frame, text="Browse", command=self.browse_folder).pack(side='left', padx=5)

        ttk.Label(top_frame, text="Search Files/Tags:").pack(side='left', padx=(20, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.filter_file_list)
        search_entry = ttk.Entry(top_frame, textvariable=self.search_var, width=25)
        search_entry.pack(side='left')

        # File listbox
        files_frame = ttk.Frame(self)
        files_frame.pack(fill='both', expand=False, padx=10, pady=5)

        ttk.Label(files_frame, text="XMP Files:").pack(anchor='w')
        self.file_listbox = tk.Listbox(files_frame, height=10)
        self.file_listbox.pack(fill='both', expand=True)
        self.file_listbox.bind("<<ListboxSelect>>", self.on_file_select)

        # Attributes frame with scroll
        attr_outer = ttk.Frame(self)
        attr_outer.pack(fill='both', expand=True, padx=10, pady=5)

        canvas = tk.Canvas(attr_outer)
        scrollbar = ttk.Scrollbar(attr_outer, orient="vertical", command=canvas.yview)
        self.attr_frame = ttk.Frame(canvas)

        self.attr_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.attr_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        self.attr_widgets = {}
        for key in self.required_keys:
            frame = ttk.Frame(self.attr_frame)
            frame.pack(fill='x', pady=2, padx=2)
            ttk.Label(frame, text=key + ":", width=15).pack(side='left')

            values_list = self.attributes_yaml.get(key, [])
            combo = AutocompleteCombobox(frame, width=50)
            combo.set_completion_list(values_list)
            combo.pack(side='left', fill='x', expand=True)
            self.attr_widgets[key] = combo

        # Save button
        save_frame = ttk.Frame(self)
        save_frame.pack(fill='x', padx=10, pady=5)
        ttk.Button(save_frame, text="Save Config", command=self.save_config).pack(side='right')

        # Logs panel
        logs_frame = ttk.LabelFrame(self, text="Logs")
        logs_frame.pack(fill='both', expand=False, padx=10, pady=5)
        self.log_text = tk.Text(logs_frame, height=10, state='disabled', bg='#222', fg='#eee')
        self.log_text.pack(fill='both', expand=True)

    def append_log(self, message):
        self.log_text.configure(state='normal')
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state='disabled')

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_var.set(folder)
            self.load_files(folder)

    def load_files(self, folder):
        self.current_folder = folder
        self.xmp_files = scanner.find_xmp_files(folder)
        self.filtered_files = self.xmp_files.copy()
        self.update_file_listbox()

    def update_file_listbox(self):
        self.file_listbox.delete(0, tk.END)
        for f in self.filtered_files:
            self.file_listbox.insert(tk.END, os.path.basename(f))
        self.clear_attributes()

    def filter_file_list(self, *args):
        query = self.search_var.get().lower()
        if not query:
            self.filtered_files = self.xmp_files.copy()
        else:
            self.filtered_files = []
            for f in self.xmp_files:
                filename = os.path.basename(f).lower()
                if query in filename:
                    self.filtered_files.append(f)
                    continue
                # Try to load tags and check for query match
                raw_tags = indexer.get_tags_from_xmp(f)
                tags_str = " ".join(raw_tags).lower()
                if query in tags_str:
                    self.filtered_files.append(f)
        self.update_file_listbox()

    def clear_attributes(self):
        for combo in self.attr_widgets.values():
            combo.set('')

    def on_file_select(self, event):
        selection = self.file_listbox.curselection()
        if not selection:
            return
        index = selection[0]
        xmp_path = self.filtered_files[index]
        self.current_file_index = index

        raw_tags = indexer.get_tags_from_xmp(xmp_path)
        mapped_tags = mapper.map_tags(raw_tags)
        existing_attrs = self.load_existing_attributes(os.path.dirname(xmp_path))
        mapped_tags.update(existing_attrs)

        for key in self.required_keys:
            values = mapped_tags.get(key, [])
            combo = self.attr_widgets[key]
            combo.set(", ".join(values) if values else '')

    def load_existing_attributes(self, folder):
        config_path = os.path.join(folder, "config.orynt3d")
        if not os.path.isfile(config_path):
            return {}
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            attr_list = data.get("modelmeta", {}).get("attributes", [])
            attr_dict = {}
            for item in attr_list:
                k = item.get("key")
                v = item.get("value")
                if k and v:
                    attr_dict.setdefault(k, []).append(v)
            return attr_dict
        except Exception as e:
            logger.log(f"Failed to load existing config attributes: {e}")
            return {}

    def save_config(self):
        if self.current_file_index is None:
            messagebox.showwarning("No file selected", "Please select an XMP file to save.")
            return

        xmp_path = self.filtered_files[self.current_file_index]
        folder = os.path.dirname(xmp_path)

        edited_tags = {}
        for key, combo in self.attr_widgets.items():
            val = combo.get().strip()
            if val:
                # Split by comma and validate each value against YAML list if exists
                parts = [v.strip() for v in val.split(",") if v.strip()]
                allowed_values = self.attributes_yaml.get(key, [])
                invalid_vals = [v for v in parts if allowed_values and v not in allowed_values]
                if invalid_vals:
                    messagebox.showerror(
                        "Invalid value",
                        f"Invalid value(s) for '{key}': {', '.join(invalid_vals)}.\nPlease use valid options."
                    )
                    return
                edited_tags[key] = parts

        # Optional: hook to your editor.py
        edited_tags = editor.edit_tags(edited_tags)
        generator.generate_config(folder, edited_tags)
        logger.log(f"Config file saved for {folder}")
        messagebox.showinfo("Success", f"Config file saved for:\n{folder}")

def main():
    app = TagEditorGUI()
    app.mainloop()

if __name__ == "__main__":
    main()
