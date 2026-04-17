import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import threading
import os
import sys
import traceback
import logging
from pathlib import Path

# Make the project root importable so converter_gui_base can be found when
# this script is run directly from its own subdirectory.
sys.path.insert(0, str(Path(__file__).parent.parent))
from converter_gui_base import TkLogHandler, LogMixin
from fcif_to_fc2 import process_campaign, SUCCESS_LEVEL, logger as fcif_logger


def _is_success(record, msg):
    """Success-detection strategy for the FCIF converter log handler."""
    return record.levelno == SUCCESS_LEVEL


class ConverterGUI(LogMixin):
    def __init__(self, root):
        self.root = root
        self.root.title("FCIF to FC2 Converter")
        self.root.geometry("1000x700")

        # Variables
        self.input_path_var = tk.StringVar()
        self.output_path_var = tk.StringVar()

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

    def browse_output(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".fc2",
            filetypes=[("FC2 Campaign", "*.fc2"), ("All files", "*.*")]
        )
        if path:
            self.output_path_var.set(str(Path(path)))

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

        thread = threading.Thread(target=self.run_conversion_task, args=(input_path,))
        thread.daemon = True
        thread.start()

    def run_conversion_task(self, input_path):
        output_path = self.output_path_var.get().strip() or None

        # Attach custom log handler for this conversion run
        log_handler = TkLogHandler(self.log_text, self.root, is_success=_is_success)
        log_handler.setFormatter(logging.Formatter('%(message)s'))
        log_handler.setLevel(logging.INFO)
        old_level = fcif_logger.level
        fcif_logger.setLevel(logging.INFO)
        fcif_logger.addHandler(log_handler)

        fcif_logger.info("-" * 50)
        fcif_logger.info("Starting conversion task...")

        try:
            fcif_logger.info(f"Processing single file: {input_path}")
            success = process_campaign(input_path, output_file=output_path)
            if not success:
                fcif_logger.error("Conversion failed.")
        except Exception as e:
            fcif_logger.error(f"Critical Error: {e}")
            traceback.print_exc()
        finally:
            fcif_logger.removeHandler(log_handler)
            fcif_logger.setLevel(old_level)
            self.root.after(0, self.reset_ui)

    def reset_ui(self):
        self.is_converting = False
        self.convert_btn.config(state='normal')


if __name__ == "__main__":
    root = tk.Tk()
    app = ConverterGUI(root)
    root.mainloop()
