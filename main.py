import asyncio
import json
import os
import tkinter as tk
from tkinter import filedialog, messagebox

import edge_tts

SETTINGS_FILE = "settings.json"


async def _generate_audio(
        text: str,
        full_path: str
):
    tts = edge_tts.Communicate(
        text=text,
        voice="en-US-GuyNeural"
    )
    await tts.save(full_path)


def process_text(
        text: str,
        output_dir: str,
        filename: str,
        prefix: str,
        postfix: str
) -> str | None:
    try:
        safe_filename = filename.replace(".mp3", "").strip()
        full_name = f"{prefix}{safe_filename}{postfix}.mp3"
        full_path = os.path.join(output_dir, full_name)

        asyncio.run(
            _generate_audio(text, full_path)
        )

        return full_path

    except Exception as ex:
        print("TTS ERROR:", type(ex).__name__, ex)
        return None


# ==========================
# SETTINGS
# ==========================
def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_settings(data: dict):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ==========================
# GUI
# ==========================
class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Text Processing Tool")
        self.geometry("720x650")
        self.resizable(False, False)

        self.settings = load_settings()

        self.output_dir = tk.StringVar(value=self.settings.get("output_dir", ""))
        self.prefix_var = tk.StringVar(value=self.settings.get("prefix", ""))
        self.postfix_var = tk.StringVar(value=self.settings.get("postfix", ""))
        self.use_prefix = tk.BooleanVar(value=True)
        self.use_postfix = tk.BooleanVar(value=True)

        self._build_ui()

    def create_labeled_entry(
            self,
            label_text: str,
            text_variable: tk.StringVar | None = None,
            use_variable: tk.BooleanVar | None = None
    ) -> tk.Entry:
        tk.Label(self, text=label_text).pack(anchor="w", padx=10, pady=(10, 0))

        frame = tk.Frame(self)
        frame.pack(fill="x", padx=10)

        if use_variable is not None:
            tk.Checkbutton(frame, variable=use_variable).pack(side="left")

        entry = tk.Entry(frame, textvariable=text_variable)
        entry.pack(side="left", fill="x", expand=True, padx=5)

        tk.Button(
            frame,
            text="Clear",
            command=lambda: entry.delete(0, "end")
        ).pack(side="left")

        return entry
    def _build_ui(self):
        # ===== MAIN TEXT =====
        tk.Label(self, text="Input text").pack(anchor="w", padx=10)

        text_btns = tk.Frame(self)
        text_btns.pack(anchor="w", padx=10)

        tk.Button(text_btns, text="Clear", command=self.clear_text).pack(side="left")
        tk.Button(text_btns, text="Paste", command=self.paste_text).pack(side="left", padx=5)

        self.text_input = tk.Text(self, height=12, wrap="word")
        self.text_input.pack(fill="x", padx=10)
        self.text_input.bind("<Control-a>", self.select_all_text)

        # ===== FILENAME =====
        tk.Label(self, text="File name").pack(anchor="w", padx=10, pady=(10, 0))

        file_frame = tk.Frame(self)
        file_frame.pack(fill="x", padx=10)

        self.filename_entry = tk.Entry(file_frame)
        self.filename_entry.pack(side="left", fill="x", expand=True)
        tk.Button(file_frame, text="Clear",
                  command=lambda: self.filename_entry.delete(0, "end")).pack(side="left", padx=5)

        self.prefix_entry = self.create_labeled_entry(
            label_text="Prefix",
            text_variable=self.prefix_var,
            use_variable=self.use_prefix
        )

        self.postfix_entry = self.create_labeled_entry(
            label_text="Postfix",
            text_variable=self.postfix_var,
            use_variable=self.use_postfix
        )
        # ===== DIRECTORY =====
        tk.Label(self, text="Output directory").pack(anchor="w", padx=10, pady=(10, 0))

        dir_frame = tk.Frame(self)
        dir_frame.pack(fill="x", padx=10)

        tk.Button(dir_frame, text="Choose", command=self.choose_directory).pack(side="left")
        self.dir_label = tk.Label(
            dir_frame,
            text=self.output_dir.get() or "Not selected",
            anchor="w"
        )
        self.dir_label.pack(side="left", padx=10)

        # ===== ACTIONS =====
        actions = tk.Frame(self)
        actions.pack(pady=20)

        tk.Button(actions, text="Start", width=15, command=self.start).pack(side="left", padx=10)
        tk.Button(actions, text="Reset", width=15, command=self.reset_all).pack(side="left", padx=10)

    # ===== HELPERS =====
    def select_all_text(self, _event):
        self.text_input.tag_add("sel", "1.0", "end")
        return "break"

    def clear_text(self):
        self.text_input.delete("1.0", "end")

    def paste_text(self):
        try:
            self.text_input.insert("end", self.clipboard_get())
        except tk.TclError:
            pass

    def choose_directory(self):
        path = filedialog.askdirectory()
        if path:
            self.output_dir.set(path)
            self.dir_label.config(text=path)
            self.save_state()

    def start(self):
        text = self.text_input.get("1.0", "end").strip()
        filename = self.filename_entry.get().strip()
        prefix = self.prefix_entry.get().strip()
        postfix = self.postfix_entry.get().strip()
        output_dir = self.output_dir.get()

        if not text or not filename or not output_dir:
            messagebox.showerror("Error", "Fill all required fields")
            return

        self.save_state()

        result_path = process_text(
            text=text,
            output_dir=output_dir,
            filename=filename,
            prefix=prefix,
            postfix=postfix
        )

        if not result_path:
            messagebox.showerror("Error", "Error generate audio")
            return

        self.clipboard_clear()
        self.clipboard_append(result_path)
        self.update()

        messagebox.showinfo(
            "Done",
            "Audio generated.\nFile path copied to clipboard."
        )
    def reset_all(self):
        self.clear_text()
        self.filename_entry.delete(0, "end")

    def save_state(self):
        save_settings({
            "output_dir": self.output_dir.get(),
            "prefix": self.prefix_entry.get(),
            "postfix": self.postfix_entry.get()
        })


# ==========================
# START
# ==========================
if __name__ == "__main__":
    App().mainloop()
