import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import threading
import glob
import os
import sys
import traceback
import logging
from pathlib import Path

# Make the project root importable so converter_gui_base can be found when
# this script is run directly from its own subdirectory.
sys.path.insert(0, str(Path(__file__).parent.parent))
from converter_gui_base import TkLogHandler, LogMixin
from fsif_to_fs2 import process_mission


def _is_success(record, msg):
    """Success-detection strategy for the FSIF converter log handler."""
    if record.levelno == logging.INFO:
        lower = msg.lower()
        return "[success]" in lower or "[passed]" in lower
    return False


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
        if self.tag:
            self.text_widget.insert(tk.END, string, self.tag)
        else:
            self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END)
        self.text_widget.config(state='disabled')


class ConverterGUI(LogMixin):
    def __init__(self, root):
        self.root = root
        self.root.title("FSIF to FS2 Converter")
        self.root.geometry("1000x700")
        try:
            self.root.state('zoomed')
        except Exception:
            pass

        # Variables
        self.mode_var = tk.StringVar(value="file")
        self.input_path_var = tk.StringVar()
        self.output_path_var = tk.StringVar()

        self.tts_enabled_var = tk.BooleanVar(value=False)
        self.tts_provider_var = tk.StringVar(value="google")
        self.tts_mode_var = tk.StringVar(value="unique")
        self.tts_dry_run_var = tk.BooleanVar(value=False)
        self.tts_out_root_var = tk.StringVar()
        self.api_key_var = tk.StringVar()
        self.tts_rate_limit_var = tk.DoubleVar(value=0.0)

        # Check for file-based API keys
        api_keys_dir = Path(__file__).resolve().parent.parent / "API_keys"
        self.google_key_file = api_keys_dir / "Gemini_API_key.txt"
        self.elevenlabs_key_file = api_keys_dir / "Elevenlabs_API_key.txt"
        self.inworld_key_file = api_keys_dir / "Inworld_API_key.txt"
        
        self.has_google_key_file = self.google_key_file.exists()
        self.has_elevenlabs_key_file = self.elevenlabs_key_file.exists()
        self.has_inworld_key_file = self.inworld_key_file.exists()

        self.is_converting = False
        self.copy_feedback_after_id = None

        self.create_widgets()

        # Setup GUI logging handler
        self.gui_handler = TkLogHandler(self.log_text, self.root, is_success=_is_success)
        self.gui_handler.setFormatter(logging.Formatter('%(message)s'))
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(self.gui_handler)

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill="both", expand=True)

        paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill="both", expand=True)

        left_frame = ttk.Frame(paned_window)
        right_frame = ttk.Frame(paned_window)

        paned_window.add(left_frame, weight=1)
        paned_window.add(right_frame, weight=1)

        # Mode Selection
        mode_frame = ttk.LabelFrame(left_frame, text="Conversion Mode", padding="5")
        mode_frame.pack(fill="x", pady=(0, 10))

        ttk.Radiobutton(mode_frame, text="Single File", variable=self.mode_var,
                        value="file", command=self.update_input_mode).pack(side="left", padx=5)
        ttk.Radiobutton(mode_frame, text="Batch (Folder)", variable=self.mode_var,
                        value="folder", command=self.update_input_mode).pack(side="left", padx=5)

        # Input Selection
        input_frame = ttk.LabelFrame(left_frame, text="Input Selection", padding="5")
        input_frame.pack(fill="x", pady=(0, 10))

        self.input_label = ttk.Label(input_frame, text="Select .fsif file:")
        self.input_label.pack(anchor="w")

        input_row = ttk.Frame(input_frame)
        input_row.pack(fill="x")

        ttk.Entry(input_row, textvariable=self.input_path_var).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(input_row, text="Browse...", command=self.browse_input).pack(side="left")

        # Output Selection (Optional, Single File Mode Only)
        self.output_row_frame = ttk.Frame(input_frame, padding=(0, 5, 0, 0))
        self.output_row_frame.pack(fill="x")

        self.output_label = ttk.Label(self.output_row_frame, text="Output File (Optional):")
        self.output_label.pack(anchor="w")

        output_inner = ttk.Frame(self.output_row_frame)
        output_inner.pack(fill="x")

        ttk.Entry(output_inner, textvariable=self.output_path_var).pack(side="left", fill="x", expand=True,
                                                                        padx=(0, 5))
        ttk.Button(output_inner, text="Save As...", command=self.browse_output).pack(side="left")

        # TTS Options
        tts_frame = ttk.LabelFrame(left_frame, text="TTS Options", padding="5")
        tts_frame.pack(fill="x", pady=(0, 10))

        ttk.Checkbutton(tts_frame, text="Enable Automatic TTS Generation",
                        variable=self.tts_enabled_var, command=self.toggle_tts_options).pack(anchor="w")

        self.tts_options_inner = ttk.Frame(tts_frame)
        self.tts_options_inner.pack(fill="x", padx=20, pady=5)

        # Provider Selection
        provider_frame = ttk.LabelFrame(self.tts_options_inner, text="Provider", padding=5)
        provider_frame.pack(fill="x", pady=(0, 5))
        
        ttk.Radiobutton(provider_frame, text="Google (Gemini TTS)", variable=self.tts_provider_var, 
                        value="google", command=self.update_api_key_visibility).pack(side="left", padx=5)
        ttk.Radiobutton(provider_frame, text="ElevenLabs TTS", variable=self.tts_provider_var, 
                        value="elevenlabs", command=self.update_api_key_visibility).pack(side="left", padx=5)
        ttk.Radiobutton(provider_frame, text="Inworld TTS", variable=self.tts_provider_var, 
                        value="inworld", command=self.update_api_key_visibility).pack(side="left", padx=5)

        # Filename Conflicts Strategy Section
        strategy_frame = ttk.LabelFrame(self.tts_options_inner, text="Filename Conflicts Strategy", padding=5)
        strategy_frame.pack(fill="x", pady=(0, 5))
        
        ttk.Radiobutton(strategy_frame, text="Unique Names (preserve existing files and generate new ones with different names)",
                        variable=self.tts_mode_var, value="unique").pack(anchor="w")
        ttk.Radiobutton(strategy_frame, text="Overwrite Existing Files", 
                        variable=self.tts_mode_var, value="overwrite").pack(anchor="w")
        ttk.Radiobutton(strategy_frame, text="Keep Existing Files (Skip TTS)", 
                        variable=self.tts_mode_var, value="keep").pack(anchor="w")

        ttk.Checkbutton(self.tts_options_inner, text="Dry Run (Simulate generation)",
                        variable=self.tts_dry_run_var).pack(anchor="w")

        # TTS Paths
        tts_paths_frame = ttk.Frame(self.tts_options_inner)
        tts_paths_frame.pack(fill="x", pady=5)

        ttk.Label(tts_paths_frame, text="Output Root (Optional):").grid(row=0, column=0, sticky="w")
        ttk.Entry(tts_paths_frame, textvariable=self.tts_out_root_var).grid(row=0, column=1, sticky="ew", padx=5)
        ttk.Button(tts_paths_frame, text="Browse...", command=self.browse_tts_root).grid(row=0, column=2)

        # Rate Limit row
        ttk.Label(tts_paths_frame, text="Rate Limit Delay (seconds):").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(tts_paths_frame, textvariable=self.tts_rate_limit_var).grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        # API Key row - Dynamic based on provider
        self.api_key_label = ttk.Label(tts_paths_frame, text="API Key (Optional):")
        self.api_key_label.grid(row=2, column=0, sticky="w", pady=5)
        
        self.api_key_entry = ttk.Entry(tts_paths_frame, textvariable=self.api_key_var, show="*")
        self.api_key_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        
        self.api_key_info = ttk.Label(tts_paths_frame, text="", foreground="green")
        self.api_key_info.grid(row=2, column=0, columnspan=3, sticky="w", pady=5)
        
        # Initial UI state update
        self.update_api_key_visibility()

        tts_paths_frame.columnconfigure(1, weight=1)

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

    def update_input_mode(self):
        mode = self.mode_var.get()
        if mode == "file":
            self.input_label.config(text="Select .fsif file:")
            self.output_row_frame.pack(fill="x", pady=(5, 0))  # Show output row
        else:
            self.input_label.config(text="Select folder containing .fsif files:")
            self.output_row_frame.pack_forget()  # Hide output row

    def browse_input(self):
        mode = self.mode_var.get()
        if mode == "file":
            path = filedialog.askopenfilename(filetypes=[("FSIF files", "*.fsif"), ("All files", "*.*")])
        else:
            path = filedialog.askdirectory()

        if path:
            self.input_path_var.set(str(Path(path)))

    def browse_output(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".fs2",
            filetypes=[("FS2 Mission", "*.fs2"), ("All files", "*.*")]
        )
        if path:
            self.output_path_var.set(str(Path(path)))

    def browse_tts_root(self):
        path = filedialog.askdirectory()
        if path:
            self.tts_out_root_var.set(str(Path(path)))

    def _set_state_recursive(self, widget, state):
        """Recursively set state for a widget and all its children."""
        try:
            widget.configure(state=state)
        except tk.TclError:
            # Not all widgets support the 'state' option (e.g., ttk.Frame, ttk.LabelFrame)
            pass

        for child in widget.winfo_children():
            self._set_state_recursive(child, state)

    def toggle_tts_options(self):
        state = 'normal' if self.tts_enabled_var.get() else 'disabled'
        self._set_state_recursive(self.tts_options_inner, state)
        if state == 'normal':
            self.update_api_key_visibility() # Restore correct state for inner widgets

    def update_api_key_visibility(self):
        if not self.tts_enabled_var.get():
            return

        provider = self.tts_provider_var.get()
        has_file = False
        filename = ""
        
        if provider == "google":
            self.api_key_label.config(text="Gemini API Key:")
            has_file = self.has_google_key_file
            filename = "API_keys/Gemini_API_key.txt"
        elif provider == "elevenlabs":
            self.api_key_label.config(text="ElevenLabs API Key:")
            has_file = self.has_elevenlabs_key_file
            filename = "API_keys/Elevenlabs_API_key.txt"
        else:
            self.api_key_label.config(text="Inworld API Key:")
            has_file = self.has_inworld_key_file
            filename = "API_keys/Inworld_API_key.txt"
            
        if has_file:
            self.api_key_label.grid_remove()
            self.api_key_entry.grid_remove()
            self.api_key_info.config(text=f"✓ API key loaded from {filename}")
            self.api_key_info.grid()
        else:
            self.api_key_info.grid_remove()
            self.api_key_label.grid()
            self.api_key_entry.grid()

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
        logging.info("-" * 50)
        logging.info("Starting conversion task...")

        thread = threading.Thread(target=self.run_conversion_task, args=(input_path,))
        thread.daemon = True
        thread.start()

    def run_conversion_task(self, input_path):
        tts_settings = self._build_tts_settings()

        mode = self.mode_var.get()
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
            if mode == "file":
                logging.info(f"Processing single file: {input_path}")
                success = process_mission(input_path, output_file=output_path, tts_settings=tts_settings)
                if not success:
                    logging.error("Conversion failed.")
            else:
                # Folder mode
                logging.info(f"Scanning folder: {input_path}")
                search_pattern = os.path.join(input_path, "*.fsif")
                files = glob.glob(search_pattern)

                if not files:
                    logging.info("No .fsif files found in the selected directory.")
                else:
                    logging.info(f"Found {len(files)} file(s).")
                    succeeded = 0
                    failed = 0
                    for i, file_path in enumerate(files, 1):
                        logging.info(f"\n[{i}/{len(files)}] Processing {os.path.basename(file_path)}...")
                        if process_mission(file_path, tts_settings=tts_settings):
                            succeeded += 1
                        else:
                            failed += 1

                    if failed == 0:
                        logging.info(f"\nAll {succeeded} file(s) converted successfully.")
                    else:
                        logging.error(f"\n{succeeded}/{len(files)} file(s) succeeded, {failed} failed.")

        except Exception as e:
            logging.error(f"Critical Error: {e}")
            traceback.print_exc()
        finally:
            # Restore stdout/stderr
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            self.root.after(0, self.reset_ui)

    def reset_ui(self):
        self.is_converting = False
        self.convert_btn.config(state='normal')

    def _build_tts_settings(self):
        """Build normalized TTS settings dict from current GUI state."""
        provider = self.tts_provider_var.get()
        api_key = self.api_key_var.get().strip() or None

        return {
            'enabled': self.tts_enabled_var.get(),
            'provider': provider,
            'out_root': self.tts_out_root_var.get().strip() or None,
            'mode': self.tts_mode_var.get(),
            'dry_run': self.tts_dry_run_var.get(),
            'api_key': api_key,
            'rate_limit_delay': self.tts_rate_limit_var.get()
        }


if __name__ == "__main__":
    root = tk.Tk()
    # Attempt to set icon if exists, optional
    # root.iconbitmap('icon.ico')
    app = ConverterGUI(root)
    root.mainloop()
