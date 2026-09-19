import tkinter as tk
from tkinter import messagebox


class CodeRecallApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Code Recall")
        self.root.geometry("1000x700")

        self.code_lines = []
        self.current_line = 0
        self.function_line = 0

        self.setup_screen()

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    # =========================================================
    # SETUP SCREEN
    # =========================================================

    def setup_screen(self):

        self.clear_screen()

        tk.Label(
            self.root,
            text="CODE RECALL",
            font=("Arial", 28, "bold")
        ).pack(pady=30)

        tk.Label(
            self.root,
            text="Paste your NeetCode solution below:",
            font=("Arial", 14)
        ).pack()

        self.code_input = tk.Text(
            self.root,
            font=("Consolas", 13),
            wrap="none"
        )

        self.code_input.pack(
            padx=30,
            pady=20,
            fill="both",
            expand=True
        )

        tk.Button(
            self.root,
            text="START RECALL",
            font=("Arial", 14, "bold"),
            command=self.start
        ).pack(pady=20)

    # =========================================================
    # START
    # =========================================================

    def start(self):

        code = self.code_input.get("1.0", "end-1c")

        if not code.strip():
            messagebox.showerror(
                "Error",
                "Please paste your code first."
            )
            return

        self.code_lines = code.splitlines()

        # Find the function definition
        self.function_line = None

        for i, line in enumerate(self.code_lines):

            if line.strip().startswith("def "):
                self.function_line = i
                break

        if self.function_line is None:

            messagebox.showerror(
                "Error",
                "I couldn't find a function starting with 'def'."
            )

            return

        # First line AFTER the function signature
        self.current_line = self.function_line + 1

        self.recall_screen()

    # =========================================================
    # RECALL SCREEN
    # =========================================================

    def recall_screen(self):

        self.clear_screen()

        tk.Label(
            self.root,
            text="CODE RECALL",
            font=("Arial", 26, "bold")
        ).pack(pady=(20, 5))

        self.progress = tk.Label(
            self.root,
            text="",
            font=("Arial", 12)
        )

        self.progress.pack()

        tk.Label(
            self.root,
            text="Type the missing line:",
            font=("Arial", 13)
        ).pack(pady=10)

        # Code display
        frame = tk.Frame(self.root)
        frame.pack(
            padx=30,
            pady=10,
            fill="both",
            expand=True
        )

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")

        self.code_display = tk.Text(
            frame,
            font=("Consolas", 14),
            bg="#1e1e1e",
            fg="white",
            insertbackground="white",
            wrap="none",
            state="disabled",
            yscrollcommand=scrollbar.set
        )

        self.code_display.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.config(
            command=self.code_display.yview
        )

        # Answer box
        self.answer = tk.Entry(
            self.root,
            font=("Consolas", 14)
        )

        self.answer.pack(
            padx=30,
            pady=10,
            fill="x"
        )

        self.answer.bind(
            "<Return>",
            lambda event: self.check()
        )

        # Buttons
        buttons = tk.Frame(self.root)
        buttons.pack(pady=10)

        tk.Button(
            buttons,
            text="CHECK",
            font=("Arial", 12, "bold"),
            command=self.check
        ).pack(side="left", padx=5)

        tk.Button(
            buttons,
            text="HINT",
            command=self.hint
        ).pack(side="left", padx=5)

        tk.Button(
            buttons,
            text="RESTART",
            command=self.restart
        ).pack(side="left", padx=5)

        self.feedback = tk.Label(
            self.root,
            text="",
            font=("Arial", 12)
        )

        self.feedback.pack(pady=5)

        self.update_code()

        self.answer.focus()

    # =========================================================
    # DISPLAY CODE
    # =========================================================

    def update_code(self):

        self.code_display.config(state="normal")
        self.code_display.delete("1.0", "end")

        # Show everything up to the current line
        for i in range(self.current_line + 1):

            line = self.code_lines[i]

            if i < self.current_line:

                # Already completed
                self.code_display.insert(
                    "end",
                    line + "\n"
                )

            else:

                # Missing line
                indentation = line[
                    :len(line) - len(line.lstrip())
                ]

                self.code_display.insert(
                    "end",
                    indentation +
                    "____________________________\n"
                )

        self.code_display.config(state="disabled")

        # Progress
        completed = self.current_line - self.function_line - 1

        total = len(self.code_lines) - self.function_line - 1

        self.progress.config(
            text=f"Progress: {completed}/{total}"
        )

        self.code_display.see("end")

    # =========================================================
    # CHECK ANSWER
    # =========================================================

    def check(self):

        if self.current_line >= len(self.code_lines):
            return

        answer = self.answer.get().strip()

        if not answer:
            return

        expected = self.code_lines[
            self.current_line
        ].strip()

        if self.normalise(answer) == self.normalise(expected):

            self.feedback.config(
                text="✓ Correct!"
            )

            self.current_line += 1

            self.answer.delete(
                0,
                "end"
            )

            if self.current_line >= len(self.code_lines):

                self.finished()

            else:

                self.update_code()

        else:

            self.feedback.config(
                text="✗ Wrong. Try again."
            )

            self.answer.select_range(
                0,
                "end"
            )

    # =========================================================
    # NORMALISE
    # =========================================================

    def normalise(self, text):

        return " ".join(text.split())

    # =========================================================
    # HINT
    # =========================================================

    def hint(self):

        if self.current_line >= len(self.code_lines):
            return

        expected = self.code_lines[
            self.current_line
        ].strip()

        if "=" in expected:
            self.feedback.config(
                text="Hint: this line assigns something."
            )

        elif expected.startswith("for"):
            self.feedback.config(
                text="Hint: this line starts a loop."
            )

        elif expected.startswith("if"):
            self.feedback.config(
                text="Hint: this line checks a condition."
            )

        elif expected.startswith("return"):
            self.feedback.config(
                text="Hint: this line returns something."
            )

        else:
            self.feedback.config(
                text="Hint: think about the next step."
            )

    # =========================================================
    # FINISHED
    # =========================================================

    def finished(self):

        self.code_display.config(state="normal")
        self.code_display.delete("1.0", "end")

        for line in self.code_lines:
            self.code_display.insert(
                "end",
                line + "\n"
            )

        self.code_display.config(state="disabled")

        self.answer.config(
            state="disabled"
        )

        self.progress.config(
            text="Complete!"
        )

        self.feedback.config(
            text="🎉 You recalled the whole solution!"
        )

    # =========================================================
    # RESTART
    # =========================================================

    def restart(self):

        self.current_line = self.function_line + 1

        self.recall_screen()


# =============================================================
# RUN PROGRAM
# =============================================================

root = tk.Tk()

app = CodeRecallApp(root)

root.mainloop()