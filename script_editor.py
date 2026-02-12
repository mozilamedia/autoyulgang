import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import json
from pathlib import Path


class ScriptEditor:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("Script Editor")
        self.window.geometry("850x650")
        
        self.script_data = {
            'script_name': 'New Script',
            'description': '',
            'steps': []
        }
        
        self.selected_index = None  # Track selected step index
        
        self.setup_ui()
        self.load_current_script()
        
    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Top buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(button_frame, text="Import Script", command=self.import_script).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Export Script", command=self.export_script).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Save to script.json", command=self.save_script).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="New Script", command=self.new_script).pack(side=tk.LEFT, padx=5)
        
        # Script info section
        info_frame = ttk.LabelFrame(main_frame, text="Script Information", padding="10")
        info_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(info_frame, text="Script Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_entry = ttk.Entry(info_frame, width=50)
        self.name_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        ttk.Label(info_frame, text="Description:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.desc_entry = ttk.Entry(info_frame, width=50)
        self.desc_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        info_frame.columnconfigure(1, weight=1)
        
        # Steps section
        steps_frame = ttk.LabelFrame(main_frame, text="Steps", padding="10")
        steps_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Steps listbox with scrollbar
        list_frame = ttk.Frame(steps_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.steps_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=12)
        self.steps_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.steps_listbox.yview)
        
        self.steps_listbox.bind('<<ListboxSelect>>', self.on_step_select)
        
        # Step buttons
        step_btn_frame = ttk.Frame(steps_frame)
        step_btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(step_btn_frame, text="Add Step", command=self.add_step).pack(side=tk.LEFT, padx=5)
        ttk.Button(step_btn_frame, text="Edit Step", command=self.edit_step).pack(side=tk.LEFT, padx=5)
        ttk.Button(step_btn_frame, text="Delete Step", command=self.delete_step).pack(side=tk.LEFT, padx=5)
        ttk.Button(step_btn_frame, text="Move Up", command=self.move_up).pack(side=tk.LEFT, padx=5)
        ttk.Button(step_btn_frame, text="Move Down", command=self.move_down).pack(side=tk.LEFT, padx=5)
        
        # Step editor section
        editor_frame = ttk.LabelFrame(main_frame, text="Step Editor", padding="10")
        editor_frame.grid(row=2, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0))
        
        ttk.Label(editor_frame, text="Step ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.step_id_entry = ttk.Entry(editor_frame, width=30)
        self.step_id_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(editor_frame, text="Template File:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.template_entry = ttk.Entry(editor_frame, width=30)
        self.template_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(editor_frame, text="Wait After Click (s):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.wait_spinbox = ttk.Spinbox(editor_frame, from_=0, to=3600, width=30)
        self.wait_spinbox.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)
        self.wait_spinbox.set(0)
        
        ttk.Label(editor_frame, text="Depends On (IDs):").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.depends_entry = ttk.Entry(editor_frame, width=30)
        self.depends_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(editor_frame, text="Depends Mode:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.depends_mode_var = tk.StringVar(value="any")
        depends_combo = ttk.Combobox(editor_frame, textvariable=self.depends_mode_var, values=["any", "all"], width=28, state="readonly")
        depends_combo.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(editor_frame, text="Description:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.step_desc_text = scrolledtext.ScrolledText(editor_frame, width=30, height=6)
        self.step_desc_text.grid(row=5, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        ttk.Button(editor_frame, text="Update Step", command=self.update_step).grid(row=6, column=0, columnspan=2, pady=10)
        
        editor_frame.columnconfigure(1, weight=1)
        editor_frame.rowconfigure(5, weight=1)
        
        # Configure grid weights
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
    def load_current_script(self):
        """Load script.json if exists"""
        script_path = Path("script.json")
        if script_path.exists():
            try:
                with open(script_path, 'r', encoding='utf-8') as f:
                    self.script_data = json.load(f)
                self.refresh_ui()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load script.json: {str(e)}")
    
    def refresh_ui(self):
        """Refresh all UI elements with current script data"""
        # Save current selection
        saved_index = self.selected_index
        
        # Update script info
        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, self.script_data.get('script_name', ''))
        
        self.desc_entry.delete(0, tk.END)
        self.desc_entry.insert(0, self.script_data.get('description', ''))
        
        # Update steps list
        self.steps_listbox.delete(0, tk.END)
        for idx, step in enumerate(self.script_data.get('steps', []), 1):
            step_id = step.get('id', f'step{idx}')
            template = step.get('template', 'unknown')
            wait = step.get('wait_after_click', 0)
            depends = step.get('depends_on', [])
            depends_str = f" [depends: {', '.join(depends)}]" if depends else ""
            self.steps_listbox.insert(tk.END, f"{step_id}: {template} (wait: {wait}s){depends_str}")
        
        # Restore selection if valid
        if saved_index is not None and saved_index < len(self.script_data.get('steps', [])):
            self.steps_listbox.selection_set(saved_index)
            self.steps_listbox.see(saved_index)
    
    def on_step_select(self, event):
        """When a step is selected in the listbox"""
        selection = self.steps_listbox.curselection()
        
        # Only update if there's an actual selection
        # Don't reset to None if selection is empty (might be temporary focus loss)
        if selection:
            idx = selection[0]
            self.selected_index = idx  # Save selected index
            
            if idx < len(self.script_data['steps']):
                step = self.script_data['steps'][idx]
                
                self.step_id_entry.delete(0, tk.END)
                self.step_id_entry.insert(0, step.get('id', ''))
                
                self.template_entry.delete(0, tk.END)
                self.template_entry.insert(0, step.get('template', ''))
                
                self.wait_spinbox.set(step.get('wait_after_click', 0))
                
                # Load dependencies
                depends_on = step.get('depends_on', [])
                self.depends_entry.delete(0, tk.END)
                self.depends_entry.insert(0, ', '.join(depends_on))
                
                self.depends_mode_var.set(step.get('depends_mode', 'any'))
                
                self.step_desc_text.delete(1.0, tk.END)
                self.step_desc_text.insert(1.0, step.get('description', ''))
        # If selection is empty, keep the current selected_index (might be temporary focus loss)
    
    def add_step(self):
        """Add a new step"""
        step_id = self.step_id_entry.get().strip()
        template = self.template_entry.get().strip()
        
        if not template:
            messagebox.showwarning("Warning", "Please enter a template filename")
            return
        
        if not step_id:
            # Auto-generate ID from template name
            step_id = template.replace('.', '_')
        
        try:
            wait = int(self.wait_spinbox.get())
        except:
            wait = 0
        
        description = self.step_desc_text.get(1.0, tk.END).strip()
        
        # Parse dependencies
        depends_str = self.depends_entry.get().strip()
        depends_on = [d.strip() for d in depends_str.split(',') if d.strip()]
        
        new_step = {
            'id': step_id,
            'template': template,
            'wait_after_click': wait,
            'description': description
        }
        
        if depends_on:
            new_step['depends_on'] = depends_on
            new_step['depends_mode'] = self.depends_mode_var.get()
        
        self.script_data['steps'].append(new_step)
        self.refresh_ui()
        
        # Clear editor
        self.step_id_entry.delete(0, tk.END)
        self.template_entry.delete(0, tk.END)
        self.wait_spinbox.set(0)
        self.depends_entry.delete(0, tk.END)
        self.depends_mode_var.set('any')
        self.step_desc_text.delete(1.0, tk.END)
    
    def edit_step(self):
        """Edit selected step"""
        selection = self.steps_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a step to edit")
            return
        
        # Just load the step into editor, user will click Update Step
        self.on_step_select(None)
    
    def update_step(self):
        """Update the selected step with current editor values"""
        # Use saved index instead of curselection
        if self.selected_index is None:
            messagebox.showwarning("Warning", "Please select a step to update")
            return
        
        idx = self.selected_index
        if idx >= len(self.script_data['steps']):
            messagebox.showwarning("Warning", "Selected step no longer exists")
            self.selected_index = None
            return
        
        step_id = self.step_id_entry.get().strip()
        template = self.template_entry.get().strip()
        
        if not template:
            messagebox.showwarning("Warning", "Please enter a template filename")
            return
        
        if not step_id:
            # Auto-generate ID from template name
            step_id = template.replace('.', '_')
        
        try:
            wait = int(self.wait_spinbox.get())
        except:
            wait = 0
        
        description = self.step_desc_text.get(1.0, tk.END).strip()
        
        # Parse dependencies
        depends_str = self.depends_entry.get().strip()
        depends_on = [d.strip() for d in depends_str.split(',') if d.strip()]
        
        updated_step = {
            'id': step_id,
            'template': template,
            'wait_after_click': wait,
            'description': description
        }
        
        if depends_on:
            updated_step['depends_on'] = depends_on
            updated_step['depends_mode'] = self.depends_mode_var.get()
        
        self.script_data['steps'][idx] = updated_step
        self.refresh_ui()
        self.steps_listbox.selection_set(idx)
    
    def delete_step(self):
        """Delete selected step"""
        selection = self.steps_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a step to delete")
            return
        
        idx = selection[0]
        if messagebox.askyesno("Confirm", f"Delete step {idx + 1}?"):
            del self.script_data['steps'][idx]
            self.refresh_ui()
    
    def move_up(self):
        """Move selected step up"""
        selection = self.steps_listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        if idx > 0:
            self.script_data['steps'][idx], self.script_data['steps'][idx - 1] = \
                self.script_data['steps'][idx - 1], self.script_data['steps'][idx]
            self.refresh_ui()
            self.steps_listbox.selection_set(idx - 1)
    
    def move_down(self):
        """Move selected step down"""
        selection = self.steps_listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        if idx < len(self.script_data['steps']) - 1:
            self.script_data['steps'][idx], self.script_data['steps'][idx + 1] = \
                self.script_data['steps'][idx + 1], self.script_data['steps'][idx]
            self.refresh_ui()
            self.steps_listbox.selection_set(idx + 1)
    
    def save_script(self):
        """Save script to script.json"""
        # Update script info from entries
        self.script_data['script_name'] = self.name_entry.get().strip()
        self.script_data['description'] = self.desc_entry.get().strip()
        
        try:
            with open('script.json', 'w', encoding='utf-8') as f:
                json.dump(self.script_data, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Success", "Script saved to script.json")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save script: {str(e)}")
    
    def import_script(self):
        """Import script from file"""
        filename = filedialog.askopenfilename(
            title="Import Script",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    self.script_data = json.load(f)
                self.refresh_ui()
                messagebox.showinfo("Success", f"Script imported from {Path(filename).name}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import script: {str(e)}")
    
    def export_script(self):
        """Export script to file"""
        # Update script info from entries
        self.script_data['script_name'] = self.name_entry.get().strip()
        self.script_data['description'] = self.desc_entry.get().strip()
        
        filename = filedialog.asksaveasfilename(
            title="Export Script",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.script_data, f, indent=2, ensure_ascii=False)
                messagebox.showinfo("Success", f"Script exported to {Path(filename).name}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export script: {str(e)}")
    
    def new_script(self):
        """Create a new empty script"""
        if messagebox.askyesno("Confirm", "Create new script? Current changes will be lost."):
            self.script_data = {
                'script_name': 'New Script',
                'description': '',
                'steps': []
            }
            self.refresh_ui()
            
            # Clear editor
            self.step_id_entry.delete(0, tk.END)
            self.template_entry.delete(0, tk.END)
            self.wait_spinbox.set(0)
            self.depends_entry.delete(0, tk.END)
            self.depends_mode_var.set('any')
            self.step_desc_text.delete(1.0, tk.END)


def main():
    root = tk.Tk()
    root.withdraw()  # Hide main window
    editor = ScriptEditor(root)
    root.mainloop()


if __name__ == "__main__":
    main()
