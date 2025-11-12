import json
import os
import tkinter as tk
from tkinter import scrolledtext, messagebox
from pygments import lex
from pygments.lexers import JavaLexer
from pygments.styles import get_style_by_name
from difflib import ndiff

DATA_PATH = os.path.join(os.path.dirname(__file__), "selected_samples.json")
STYLE = get_style_by_name("monokai")


def _ensure_token_tag(text_widget, token):
    """
    Ensure to fit C/JAVA code
    """
    tag = str(token)
    style_str = STYLE.styles.get(token)

    try:
        text_widget.tag_configure(tag)
    except tk.TclError:
        pass

    if style_str:
        fg_color = None
        bg_color = None
        parts = style_str.split()
        for part in parts:
            if part.startswith("bg:"):
                bg_color = part[3:]
            elif part.startswith("#"):
                fg_color = part

        kwargs = {}
        if fg_color:
            kwargs["foreground"] = fg_color
        if bg_color:
            kwargs["background"] = bg_color

        if kwargs:
            try:
                text_widget.tag_configure(tag, **kwargs)
            except tk.TclError:
                pass

    return tag



def _insert_lexed(text_widget, code_str, extra_tags=None):
    extra_tags = extra_tags or []
    for token, content in lex(code_str, JavaLexer()):
        token_tag = _ensure_token_tag(text_widget, token)
        text_widget.insert(tk.END, content, (token_tag, *extra_tags))


def highlight_code(text_widget, code):
    text_widget.config(state="normal")
    text_widget.delete(1.0, tk.END)
    _insert_lexed(text_widget, code)
    text_widget.config(state="disabled")


def highlight_diff_with_syntax(text_widget, orig_code, adv_code, show_deleted=True):
    orig_lines = orig_code.splitlines()
    adv_lines = adv_code.splitlines()
    diff = list(ndiff(orig_lines, adv_lines))
    text_widget.config(state="normal")
    text_widget.delete(1.0, tk.END)
    text_widget.tag_configure("added", background="#1b3d1b")
    text_widget.tag_configure("deleted", background="#4a1a1a")

    for line in diff:
        if line.startswith("? "):
            continue
        content = line[2:] + "\n"
        if line.startswith("+ "):
            _insert_lexed(text_widget, content, extra_tags=["added"])
        elif line.startswith("- "):
            if show_deleted:
                _insert_lexed(text_widget, content, extra_tags=["deleted"])
        else:
            _insert_lexed(text_widget, content)
    text_widget.config(state="disabled")


def highlight_adv_with_added(text_widget, orig_code, adv_code):
    orig_lines = orig_code.splitlines()
    adv_lines = adv_code.splitlines()
    diff = list(ndiff(orig_lines, adv_lines))
    text_widget.config(state="normal")
    text_widget.delete(1.0, tk.END)
    text_widget.tag_configure("added", background="#1b3d1b")

    for line in diff:
        if line.startswith("? "):
            continue
        if line.startswith("- "):
            continue
        tag_extra = ["added"] if line.startswith("+ ") else []
        content = line[2:] + "\n"
        _insert_lexed(text_widget, content, extra_tags=tag_extra)
    text_widget.config(state="disabled")


# ===================== login page =====================
class UsernamePrompt:
    def __init__(self, root):
        self.root = root
        self.root.title("Code Evaluation Login")
        self.root.geometry("400x180")
        tk.Label(root, text="Enter your username:", font=("Arial", 12)).pack(pady=20)
        self.entry = tk.Entry(root, font=("Arial", 12))
        self.entry.pack(pady=5)
        tk.Button(root, text="Start Evaluation", command=self.start).pack(pady=10)
        self.username = None

    def start(self):
        name = self.entry.get().strip()
        if not name:
            messagebox.showerror("Error", "Please enter a username before starting.")
            return
        self.username = name
        self.root.destroy()


# ===================== main page =====================
class CodeReviewer:
    def __init__(self, root, username):
        self.root = root
        self.username = username
        self.RESULT_PATH = f"{username}_results.json"
        self.diff_mode = False

        self.root.title(f"Code Evaluation - User: {username}")
        self.root.geometry("1200x720")

        with open(DATA_PATH, "r", encoding="utf-8") as f:
            self.data = json.load(f)

        self.index = 0

        # result adopt list[dict]
        self.results_list = []
        self.result_index_by_key = {}  # {(Index, Model, Task, Method): idx_in_results_list}

        # attempt to find old saved data
        if os.path.exists(self.RESULT_PATH):
            try:
                with open(self.RESULT_PATH, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                if isinstance(loaded, dict):
                    for k, v in loaded.items():
                        self.results_list.append({
                            "Index": int(k),
                            "Model": "",
                            "Task": "",
                            "Method": v.get("method", ""),
                            "naturalness": v.get("naturalness", 0),
                            "semantic": v.get("semantic", 0),
                        })
                elif isinstance(loaded, list):
                    self.results_list = loaded
                else:
                    self.results_list = []
            except Exception:
                self.results_list = []

        # set co-index
        for i, rec in enumerate(self.results_list):
            key = (rec.get("Index"),
                   rec.get("Model", ""),
                   rec.get("Task", ""),
                   rec.get("Method", ""))
            self.result_index_by_key[key] = i

        # main container
        self.container = tk.Frame(root, bg="#1e1e1e")
        self.container.pack(fill=tk.BOTH, expand=True)

        # === two code screen label ===
        self.label_left = tk.Label(
            self.container, text="Original Code",
            bg="#1e1e1e", fg="#cccccc", font=("Arial", 11, "bold")
        )
        self.label_left.place(relx=0.0, rely=0.0, relwidth=0.5, relheight=0.04)

        self.label_right = tk.Label(
            self.container, text="Adversarial Code",
            bg="#1e1e1e", fg="#cccccc", font=("Arial", 11, "bold")
        )
        self.label_right.place(relx=0.5, rely=0.0, relwidth=0.5, relheight=0.04)
        
        # === two code screen screen ===
        self.text_left = scrolledtext.ScrolledText(
            self.container, wrap=tk.WORD,
            bg="#272822", fg="#ffffff", font=("Consolas", 10),
            padx=10, pady=10, borderwidth=0
        )
        self.text_right = scrolledtext.ScrolledText(
            self.container, wrap=tk.WORD,
            bg="#272822", fg="#ffffff", font=("Consolas", 10),
            padx=10, pady=10, borderwidth=0
        )
        self.text_left.place(relx=0, rely=0.04, relwidth=0.5, relheight=0.89)
        self.text_right.place(relx=0.5, rely=0.04, relwidth=0.5, relheight=0.89)
        self.root.bind("<Configure>", self.on_resize)

        # evaluation part
        bottom = tk.Frame(root, bg="#f5f5f5")
        bottom.place(relx=0, rely=0.93, relwidth=1, relheight=0.07)

        self.progress_label = tk.Label(bottom, text="", font=("Arial", 10, "bold"), fg="#0078D7", bg="#f5f5f5")
        self.progress_label.pack(side=tk.LEFT, padx=10)

        # eval label
        tk.Label(bottom, text="Naturalness:", font=("Arial", 10, "bold"), bg="#f5f5f5").pack(side=tk.LEFT, padx=(5, 2))
        self.naturalness_var = tk.IntVar()
        self.naturalness_labels = []
        for i in range(1, 6):
            lbl = self.make_rating_label(bottom, str(i), lambda v=i: self.set_rating("naturalness", v))
            lbl.pack(side=tk.LEFT, padx=3)
            self.naturalness_labels.append(lbl)

        tk.Label(bottom, text="  Semantic:", font=("Arial", 10, "bold"), bg="#f5f5f5").pack(side=tk.LEFT, padx=(10, 2))
        self.semantic_var = tk.IntVar()
        self.semantic_labels = []
        for i in range(1, 6):
            lbl = self.make_rating_label(bottom, str(i), lambda v=i: self.set_rating("semantic", v))
            lbl.pack(side=tk.LEFT, padx=3)
            self.semantic_labels.append(lbl)

        # tool bar
        tk.Button(bottom, text="Previous", command=self.prev_code).pack(side=tk.RIGHT, padx=6)
        tk.Button(bottom, text="Save and Next", command=self.next_code).pack(side=tk.RIGHT, padx=6)
        tk.Button(bottom, text="Save", command=self.save_score).pack(side=tk.RIGHT, padx=6)
        self.diff_button = tk.Button(bottom, text="Diff View: OFF", command=self.toggle_diff_view)
        self.diff_button.pack(side=tk.RIGHT, padx=6)

        # notice part
        self.feedback_label = tk.Label(root, text="", font=("Arial", 9), bg="#222222", fg="white")
        self.feedback_label.place_forget()

        self.show_code()

    def _item_composite_key(self, item):
        return (
            item.get("Index"),
            item.get("Model", ""),
            item.get("Task", ""),
            item.get("Method", ""),
        )

    def _find_result_idx_for_item(self, item):
        return self.result_index_by_key.get(self._item_composite_key(item))

    # -------- Label rating ----------
    def make_rating_label(self, parent, text, command):
        label = tk.Label(parent, text=text, font=("Arial", 12, "bold"),
                         fg="black", bg="#f5f5f5", cursor="hand2", padx=6)
        label.bind("<Button-1>", lambda e: command())
        label.bind("<Enter>", lambda e: label.config(fg="#ff4d4f"))
        label.bind("<Leave>", lambda e: self.update_colors())
        return label

    # -------- Code Diff ON/OFF ----------
    def toggle_diff_view(self):
        self.diff_mode = not self.diff_mode
        self.diff_button.config(text=f"Diff View: {'ON' if self.diff_mode else 'OFF'}")
        self.show_code()

    def on_resize(self, event=None):
        self.label_left.place(relx=0.0, rely=0.0, relwidth=0.5, relheight=0.04)
        self.label_right.place(relx=0.5, rely=0.0, relwidth=0.5, relheight=0.04)
        self.text_left.place(relx=0, rely=0.04, relwidth=0.5, relheight=0.89)
        self.text_right.place(relx=0.5, rely=0.04, relwidth=0.5, relheight=0.89)

    # -------- rating part ----------
    def set_rating(self, which, value):
        if which == "naturalness":
            self.naturalness_var.set(value)
        else:
            self.semantic_var.set(value)
        self.update_colors()

    def update_colors(self):
        for i, lbl in enumerate(self.naturalness_labels, start=1):
            if self.naturalness_var.get() == i:
                lbl.config(fg="#d00000", relief="sunken")
            else:
                lbl.config(fg="black", relief="flat")
        for i, lbl in enumerate(self.semantic_labels, start=1):
            if self.semantic_var.get() == i:
                lbl.config(fg="#d00000", relief="sunken")
            else:
                lbl.config(fg="black", relief="flat")

    # -------- save and navigation ----------
    def show_feedback(self, msg):
        self.feedback_label.config(text=msg, bg="#222222", fg="white")
        self.feedback_label.place(relx=0.95, rely=0.95, anchor="se")

        def fade(step=0):
            if step < 10:
                gray = 255 - step * 20
                self.feedback_label.config(fg=f"#{gray:02x}{gray:02x}{gray:02x}")
                self.root.after(80, lambda: fade(step + 1))
            else:
                self.feedback_label.place_forget()
        fade()

    def save_score(self):
        n, s = self.naturalness_var.get(), self.semantic_var.get()
        if n == 0 or s == 0:
            self.show_feedback("Please rate both items before saving")
            return False

        item = self.data[self.index]
        rec = {
            "Index": item.get("Index"),
            "Model": item.get("Model", ""),
            "Task": item.get("Task", ""),
            "Method": item.get("Method", ""),
            "naturalness": n,
            "semantic": s
        }

        key = self._item_composite_key(item)
        existing_idx = self.result_index_by_key.get(key)

        if existing_idx is None:
            # add
            self.results_list.append(rec)
            self.result_index_by_key[key] = len(self.results_list) - 1
        else:
            # update
            self.results_list[existing_idx] = rec

        with open(self.RESULT_PATH, "w", encoding="utf-8") as f:
            json.dump(self.results_list, f, indent=2, ensure_ascii=False)

        self.show_feedback(f"✔ Sample {self.index + 1} saved")
        return True

    def check_completion(self):
        missing = []
        for item in self.data:
            if self._find_result_idx_for_item(item) is None:
                miss_label = f'{item.get("Index")}#{item.get("Method","")}'
                missing.append(miss_label)

        if missing:
            messagebox.showwarning(
                "Incomplete",
                "You have not rated all samples.\nPlease return to: " + ", ".join(missing)
            )
            return False
        else:
            messagebox.showinfo("Completed", "All samples are rated.\nThank you for your participation!")
            self.root.destroy()
            return True

    def next_code(self):
        if not self.save_score():
            return
        if self.index < len(self.data) - 1:
            self.index += 1
            self.show_code()
        else:
            if messagebox.askyesno("Evaluation Completed",
                                   "You reached the last sample.\nDo you want to finish now?"):
                self.check_completion()
            else:
                self.show_feedback("You can review previous samples.")

    def prev_code(self):
        if self.index > 0:
            self.index -= 1
            self.show_code()
        else:
            self.show_feedback("First sample reached")

    # -------- show code ----------
    def show_code(self):
        item = self.data[self.index]
        orig = item["Original"]
        adv = item["Adversarial"]

        # highlit code
        highlight_code(self.text_left, orig)
        if self.diff_mode:
            highlight_diff_with_syntax(self.text_right, orig, adv, show_deleted=True)
        else:
            highlight_adv_with_added(self.text_right, orig, adv)

        # progress showing
        total = len(self.data)
        self.progress_label.config(text=f"Sample {self.index + 1} / {total}")
        self.root.title(f"Code Evaluation - {self.index + 1}/{total} - User: {self.username}")

        # show old eval result      
        self.naturalness_var.set(0)
        self.semantic_var.set(0)
        idx_in_results = self._find_result_idx_for_item(item)
        if idx_in_results is not None:
            rec = self.results_list[idx_in_results]
            self.naturalness_var.set(int(rec.get("naturalness", 0)))
            self.semantic_var.set(int(rec.get("semantic", 0)))
        self.update_colors()
        
        # idx_in_results = self._find_result_idx_for_item(item)
        # if idx_in_results is not None:
        #     rec = self.results_list[idx_in_results]
        #     self.naturalness_var.set(int(rec.get("naturalness", 0)))
        #     self.semantic_var.set(int(rec.get("semantic", 0)))
        # else:
        #     self.naturalness_var.set(1)
        #     self.semantic_var.set(1)
        # self.update_colors()


if __name__ == "__main__":
    temp_root = tk.Tk()
    prompt = UsernamePrompt(temp_root)
    temp_root.mainloop()

    if prompt.username:
        root = tk.Tk()
        app = CodeReviewer(root, prompt.username)
        root.mainloop()
