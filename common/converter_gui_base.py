"""
converter_gui_base.py
Shared Tkinter utilities for the FSIF and FCIF converter GUIs.

Provides:
  - TkLogHandler : a logging.Handler that writes coloured records to a
                   Tkinter Text widget on the main thread.
  - LogMixin     : a mixin that adds clear_log, copy_log_to_clipboard,
                   _show_copy_feedback and _hide_copy_feedback to a GUI class.
"""

import tkinter as tk
from tkinter import messagebox, scrolledtext
import logging
from typing import Optional
from contextlib import contextmanager
import sys


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


class TkLogHandler(logging.Handler):
    """
    A logging.Handler that appends formatted records to a Tkinter Text widget
    on the main thread via root.after().

    Colour tags applied to the widget:
      'error'   — logging.ERROR and above
      'warning' — logging.WARNING
      'success' — INFO records for which ``is_success(record, formatted_msg)``
                  returns True
      'info'    — all other INFO records

    Parameters
    ----------
    text_widget : tk.Text
        The scrolled-text widget to write into (must have the four tags
        configured by the host widget: 'error', 'warning', 'success', 'info').
    root : tk.Tk
        The root window, used for ``root.after()`` scheduling.
    is_success : callable(record, formatted_msg) -> bool, optional
        Returns True when an INFO-level record should receive the 'success'
        tag.  Defaults to always-False (no special success colouring).
    """

    def __init__(self, text_widget, root, is_success=None):
        super().__init__()
        self.text_widget = text_widget
        self.root = root
        self._is_success = is_success if is_success is not None else (lambda record, msg: False)

    def emit(self, record):
        msg = self.format(record)
        self.root.after(0, self._append_log, msg, record)

    def _append_log(self, message, record):
        self.text_widget.config(state='normal')

        tag = self._get_tag(record, message)
        if tag:
            self.text_widget.insert(tk.END, message + '\n', tag)
        else:
            self.text_widget.insert(tk.END, message + '\n')

        self.text_widget.see(tk.END)
        self.text_widget.config(state='disabled')

    def _get_tag(self, record, message):
        if record.levelno >= logging.ERROR:
            return 'error'
        if record.levelno >= logging.WARNING:
            return 'warning'
        if record.levelno >= logging.INFO:
            if self._is_success(record, message):
                return 'success'
            return 'info'
        return None


class LogMixin:
    """
    Mixin that provides clipboard and log-area helpers to a ConverterGUI class.

    The host class must define the following instance attributes before any of
    these methods are called:
      self.root                  — tk.Tk root window
      self.log_text              — scrolledtext.ScrolledText widget
      self.copy_feedback_label   — tk.Label for transient "Copied!" feedback
      self.copy_feedback_after_id — set to None on __init__; managed here
    """

    # Type annotations for attributes supplied by the host class.
    # These are declarations only (no runtime effect) and let type checkers
    # understand the mixin contract without requiring abstract properties.
    root: tk.Tk
    log_text: scrolledtext.ScrolledText
    copy_feedback_label: tk.Label
    copy_feedback_after_id: Optional[str]

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

    @contextmanager
    def conversion_runner(self, target_logger, is_success_cb):
        """
        Context manager to set up logging and stdout/stderr redirection
        for a single conversion run.
        """
        log_handler = TkLogHandler(self.log_text, self.root, is_success=is_success_cb)
        log_handler.setFormatter(logging.Formatter('%(message)s'))
        log_handler.setLevel(logging.INFO)

        old_level = target_logger.level
        target_logger.setLevel(logging.INFO)
        target_logger.addHandler(log_handler)

        old_stdout = sys.stdout
        old_stderr = sys.stderr

        stdout_redirector = RedirectText(self.log_text, self.root)
        stderr_redirector = RedirectText(self.log_text, self.root, tag='error')
        sys.stdout = stdout_redirector
        sys.stderr = stderr_redirector

        try:
            yield
        except Exception as e:
            target_logger.exception(f"Critical Error: {e}")
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            target_logger.removeHandler(log_handler)
            target_logger.setLevel(old_level)
