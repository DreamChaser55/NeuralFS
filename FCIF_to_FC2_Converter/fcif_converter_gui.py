import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import threading
import os
import sys
import traceback
from pathlib import Path
from fcif_to_fc2 import process_campaign

class RedirectText:
    def __init__(self, text_widget, root, tag=None):
        self.text_widget = text_widget
        self.root = root
        self.tag = tag

    def write(self, string):
        self.root.after(0, self._append_raw, string)

    def flush(self):
        pass

    def _append_raw(self, string):
        self.text_widget.config(state='normal')

        tag_to_use = self.tag
        if not tag_to_use:
            lower = string.lower()
            if "[error]" in lower or "[failed]" in lower:
                tag_to_use = 'error'
            elif "[warning]" in lower:
                tag_to_use = 'warning'
            elif "[success]" in lower or "[passed]" in lower:
                tag_to_use = 'success'
            elif "[info]" in lower:
                tag_to_use = 'info'

        if tag_to_use:
            self.text_widget.insert(tk.END, string, tag_to_use)
        else:
            self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END)
        self.text_widget.config(state='disabled')


class ConverterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("FCIF to FC2 Converter")
        self.root.geometry("1000x700")

        # Variables
        self.input_path_var = tk.StringVar()
        self.output_path_var = tk.StringVar()
        self.first_mission_path_var = tk.StringVar()

        self.is_converting = False
        self.copy_feedback_after_id = None

        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill="both", expand=True)

        paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill="both", expand=True)

        left_frame = ttk.Frame(paned_window)
        right_frame = ttk.Frame(paned_window)

        paned_window.add(left_frame, weight=1)
        paned_window.add(right_frame, weight=1)

        # Input Selection
        input_frame = ttk.LabelFrame(left_frame, text="Input Selection", padding="5")
        input_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(input_frame, text="Select .fcif campaign file:").pack(anchor="w")

        input_row = ttk.Frame(input_frame)
        input_row.pack(fill="x")

        ttk.Entry(input_row, textvariable=self.input_path_var).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(input_row, text="Browse...", command=self.browse_input).pack(side="left")

        # Output Selection
        self.output_row_frame = ttk.Frame(input_frame, padding=(0, 5, 0, 0))
        self.output_row_frame.pack(fill="x", pady=(5, 0))

        ttk.Label(self.output_row_frame, text="Output File (Optional):").pack(anchor="w")

        output_inner = ttk.Frame(self.output_row_frame)
        output_inner.pack(fill="x")

        ttk.Entry(output_inner, textvariable=self.output_path_var).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(output_inner, text="Save As...", command=self.browse_output).pack(side="left")

        # First Mission FSIF (Optional)
        first_mission_frame = ttk.LabelFrame(left_frame, text="First Mission Loadout Check (Optional)", padding="5")
        first_mission_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(
            first_mission_frame,
            text="First mission .fsif file — checks that all ships and weapons used\n"
                 "in the first mission are present in starting_loadout:",
            justify="left",
        ).pack(anchor="w")

        first_mission_row = ttk.Frame(first_mission_frame)
        first_mission_row.pack(fill="x", pady=(4, 0))

        ttk.Entry(first_mission_row, textvariable=self.first_mission_path_var).pack(
            side="left", fill="x", expand=True, padx=(0, 5)
        )
        ttk.Button(first_mission_row, text="Browse...", command=self.browse_first_mission).pack(side="left")

        # Converter Actions
        actions_frame = ttk.Frame(left_frame)
        actions_frame.pack(fill="x", pady=10)

        self.convert_btn = ttk.Button(actions_frame, text="Convert", command=self.start_conversion)
        self.convert_btn.pack(side="left")

        self.copy_log_btn = ttk.Button(actions_frame, text="Copy log", command=self.copy_log_to_clipboard)
        self.copy_log_btn.pack(side="left", padx=(8, 0))

        self.copy_feedback_label = tk.Label(actions_frame, text="", fg="green")
        self.copy_feedback_label.pack(side="left", padx=(8, 0))

        # Log Area
        log_frame = ttk.LabelFrame(right_frame, text="Log Output", padding="5")
        log_frame.pack(fill="both", expand=True)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, state='disabled')
        self.log_text.pack(fill="both", expand=True)

        self.log_text.tag_config('error', foreground='red')
        self.log_text.tag_config('warning', foreground='#ff8c00')  # Dark Orange
        self.log_text.tag_config('success', foreground='green')
        self.log_text.tag_config('info', foreground='blue')

    def browse_input(self):
        path = filedialog.askopenfilename(filetypes=[("FCIF files", "*.fcif"), ("All files", "*.*")])
        if path:
            self.input_path_var.set(str(Path(path)))

    def browse_first_mission(self):
        path = filedialog.askopenfilename(filetypes=[("FSIF files", "*.fsif"), ("All files", "*.*")])
        if path:
            self.first_mission_path_var.set(str(Path(path)))

    def browse_output(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".fc2",
            filetypes=[("FC2 Campaign", "*.fc2"), ("All files", "*.*")]
        )
        if path:
            self.output_path_var.set(str(Path(path)))

    def clear_log(self):
        self.log_text.config(state='normal')
        self.log_text.delete('1.0', tk.END)
        self.log_text.config(state='disabled')

    def copy_log_to_clipboard(self):
        log_content = self.log_text.get('1.0', tk.END).strip()

        if not log_content:
            messagebox.showinfo("Copy log", "Log is empty, nothing to copy.")
            return

        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(log_content)
            self.root.update()
            self._show_copy_feedback()
        except tk.TclError as e:
            messagebox.showerror("Copy log", f"Failed to copy log to clipboard.\n{e}")

    def _show_copy_feedback(self):
        if self.copy_feedback_after_id is not None:
            self.root.after_cancel(self.copy_feedback_after_id)
            self.copy_feedback_after_id = None

        self.copy_feedback_label.config(text="Copied!")
        self.copy_feedback_after_id = self.root.after(1000, self._hide_copy_feedback)

    def _hide_copy_feedback(self):
        self.copy_feedback_label.config(text="")
        self.copy_feedback_after_id = None

    def log(self, message):
        self.root.after(0, self._append_log, message)

    def _append_log(self, message):
        self.log_text.config(state='normal')

        tag = None
        lower = message.lower()
        if "[error]" in lower or "[failed]" in lower:
            tag = 'error'
        elif "[warning]" in lower:
            tag = 'warning'
        elif "[success]" in lower or "[passed]" in lower:
            tag = 'success'
        elif "[info]" in lower:
            tag = 'info'

        if tag:
            self.log_text.insert(tk.END, message + "\n", tag)
        else:
            self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

    def start_conversion(self):
        if self.is_converting:
            return

        input_path = self.input_path_var.get()
        if not input_path:
            messagebox.showerror("Error", "Please select an input path.")
            return

        if not os.path.exists(input_path):
            messagebox.showerror("Error", "Input path does not exist.")
            return

        self.clear_log()
        self.is_converting = True
        self.convert_btn.config(state='disabled')
        self.log("-" * 50)
        self.log("Starting conversion task...")

        thread = threading.Thread(target=self.run_conversion_task, args=(input_path,))
        thread.daemon = True
        thread.start()

    def run_conversion_task(self, input_path):
        output_path = self.output_path_var.get().strip() or None

        # Save old stdout/stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr

        # Redirect stdout/stderr to the log widget
        stdout_redirector = RedirectText(self.log_text, self.root)
        stderr_redirector = RedirectText(self.log_text, self.root, tag='error')
        sys.stdout = stdout_redirector
        sys.stderr = stderr_redirector

        try:
            first_mission = self.first_mission_path_var.get().strip() or None
            self.log(f"Processing single file: {input_path}")
            process_campaign(input_path, output_file=output_path, first_mission=first_mission, log_func=self.log)
            self.log("\nTask completed.")
        except Exception as e:
            self.log(f"Critical Error: {e}")
            traceback.print_exc()
        finally:
            # Restore stdout/stderr
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            self.root.after(0, self.reset_ui)

    def reset_ui(self):
        self.is_converting = False
        self.convert_btn.config(state='normal')

if __name__ == "__main__":
    root = tk.Tk()
    app = ConverterGUI(root)
    root.mainloop()
