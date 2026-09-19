import tkinter as tk
from tkinter import messagebox
import ast
import re


# ============================================================
# CODE CHECKING
# ============================================================

def normalise_code(code):
    """
    Basic normalisation:
    - Removes leading/trailing whitespace
    - Removes comments
    - Normalises whitespace
    """
    code = code.strip()

    # Remove comments
    if "#" in code:
        in_string = False
        quote = None
        result = ""

        i = 0
        while i < len(code):
            char = code[i]

            if char in ("'", '"'):
                if not in_string:
                    in_string = True
                    quote = char
                elif char == quote:
                    in_string = False

            if char == "#" and not in_string:
                break

            result += char
            i += 1

        code = result.strip()

    return code


class VariableNormaliser(ast.NodeTransformer):
    """
    Changes variable names into generic names.

    Example:

        total = 0
        for i in range(5):
            total += i

    becomes structurally equivalent to:

        result = 0
        for number in range(5):
            result += number
    """

    def __init__(self):
        self.variables = {}

    def get_name(self, name):
        if name not in self.variables:
            self.variables[name] = f"VAR_{len(self.variables)}"
        return self.variables[name]

    def visit_Name(self, node):
        node.id = self.get_name(node.id)
        return node


def ast_structure(code):
    """
    Converts valid Python code into a normalised AST.
    """

    code = normalise_code(code)

    try:
        tree = ast.parse(code)

        normaliser = VariableNormaliser()
        tree = normaliser.visit(tree)

        ast.fix_missing_locations(tree)

        return ast.dump(tree, annotate_fields=False, include_attributes=False)

    except SyntaxError:
        return None


def expressions_equivalent(user_code, target_code):
    """
    Checks whether two pieces of Python code have
    the same basic AST structure while allowing
    different variable names.
    """

    user_ast = ast_structure(user_code)
    target_ast = ast_structure(target_code)

    if user_ast is None or target_ast is None:
        return False

    if user_ast == target_ast:
        return True

    # --------------------------------------------------------
    # Handle:
    #
    # x += 1
    #
    # versus:
    #
    # x = x + 1
    # --------------------------------------------------------

    try:
        user_tree = ast.parse(normalise_code(user_code))
        target_tree = ast.parse(normalise_code(target_code))

        user_tree = simplify_tree(user_tree)
        target_tree = simplify_tree(target_tree)

        user_normaliser = VariableNormaliser()
        target_normaliser = VariableNormaliser()

        user_tree = user_normaliser.visit(user_tree)
        target_tree = target_normaliser.visit(target_tree)

        ast.fix_missing_locations(user_tree)
        ast.fix_missing_locations(target_tree)

        return (
            ast.dump(
                user_tree,
                annotate_fields=False,
                include_attributes=False
            )
            ==
            ast.dump(
                target_tree,
                annotate_fields=False,
                include_attributes=False
            )
        )

    except SyntaxError:
        return False


def simplify_tree(tree):
    """
    Converts some common alternative Python syntax
    into a more comparable form.
    """

    class Simplifier(ast.NodeTransformer):

        def visit_AugAssign(self, node):
            """
            Converts:

                x += y

            conceptually into:

                x = x + y
            """

            target = node.target

            if isinstance(target, ast.Name):
                left = ast.Name(
                    id=target.id,
                    ctx=ast.Load()
                )

                value = ast.BinOp(
                    left=left,
                    op=node.op,
                    right=node.value
                )

                return ast.Assign(
                    targets=[target],
                    value=value
                )

            return self.generic_visit(node)

    return Simplifier().visit(tree)


# ============================================================
# CODE RECALL APPLICATION
# ============================================================

class CodeRecallApp:

    def __init__(self, root):

        self.root = root
        self.root.title("Code Recall")
        self.root.geometry("900x650")
        self.root.minsize(750, 550)

        self.code_lines = []
        self.current_line = 0
        self.attempts = 0
        self.started = False

        self.create_setup_screen()

    # ========================================================
    # SETUP SCREEN
    # ========================================================

    def create_setup_screen(self):

        self.clear_window()

        title = tk.Label(
            self.root,
            text="CODE RECALL",
            font=("Arial", 28, "bold")
        )
        title.pack(pady=(30, 5))

        subtitle = tk.Label(
            self.root,
            text="Paste code below and recall it one line at a time.",
            font=("Arial", 13)
        )
        subtitle.pack(pady=(0, 20))

        self.code_input = tk.Text(
            self.root,
            font=("Consolas", 13),
            height=20,
            width=90,
            undo=True
        )
        self.code_input.pack(
            padx=30,
            pady=10,
            fill="both",
            expand=True
        )

        button = tk.Button(
            self.root,
            text="START RECALL",
            font=("Arial", 14, "bold"),
            padx=30,
            pady=10,
            command=self.start_recall
        )
        button.pack(pady=20)

    # ========================================================
    # START RECALL
    # ========================================================

    def start_recall(self):

        code = self.code_input.get("1.0", tk.END).strip()

        if not code:
            messagebox.showwarning(
                "No code",
                "Paste some code first."
            )
            return

        # Keep blank lines because they are part of the code.
        self.code_lines = code.splitlines()

        # Remove completely empty lines at beginning/end
        while self.code_lines and not self.code_lines[0].strip():
            self.code_lines.pop(0)

        while self.code_lines and not self.code_lines[-1].strip():
            self.code_lines.pop()

        if not self.code_lines:
            messagebox.showwarning(
                "No code",
                "No usable code was found."
            )
            return

        self.current_line = 0
        self.attempts = 0
        self.started = True

        self.create_recall_screen()

    # ========================================================
    # RECALL SCREEN
    # ========================================================

    def create_recall_screen(self):

        self.clear_window()

        # Title
        self.title_label = tk.Label(
            self.root,
            text="CODE RECALL",
            font=("Arial", 26, "bold")
        )
        self.title_label.pack(pady=(20, 5))

        # Progress
        self.progress_label = tk.Label(
            self.root,
            font=("Arial", 12)
        )
        self.progress_label.pack(pady=5)

        # Instructions
        self.instruction_label = tk.Label(
            self.root,
            text=(
                "Enter the next line of code.\n"
                "Variable names can be different."
            ),
            font=("Arial", 12)
        )
        self.instruction_label.pack(pady=15)

        # Answer area
        self.answer_box = tk.Text(
            self.root,
            height=5,
            font=("Consolas", 15),
            wrap="none"
        )
        self.answer_box.pack(
            padx=60,
            pady=10,
            fill="x"
        )

        # Submit
        self.submit_button = tk.Button(
            self.root,
            text="CHECK",
            font=("Arial", 13, "bold"),
            padx=30,
            pady=8,
            command=self.check_answer
        )
        self.submit_button.pack(pady=10)

        # Feedback
        self.feedback_label = tk.Label(
            self.root,
            text="",
            font=("Arial", 12),
            wraplength=700,
            justify="center"
        )
        self.feedback_label.pack(pady=15)

        # Hint
        self.hint_button = tk.Button(
            self.root,
            text="SHOW HINT",
            font=("Arial", 10),
            command=self.show_hint
        )
        self.hint_button.pack(pady=5)

        # Restart
        restart_button = tk.Button(
            self.root,
            text="QUIT / NEW CODE",
            command=self.create_setup_screen
        )
        restart_button.pack(side="bottom", pady=15)

        self.answer_box.bind(
            "<Control-Return>",
            lambda event: self.check_answer()
        )

        self.update_progress()

        self.answer_box.focus_set()

    # ========================================================
    # CHECK ANSWER
    # ========================================================

    def check_answer(self):

        if self.current_line >= len(self.code_lines):
            return

        user_answer = self.answer_box.get(
            "1.0",
            tk.END
        ).strip()

        if not user_answer:
            self.feedback_label.config(
                text="Type something first.",
            )
            return

        target = self.code_lines[self.current_line]

        self.attempts += 1

        if expressions_equivalent(user_answer, target):

            self.feedback_label.config(
                text="✓ Correct!",
            )

            self.current_line += 1
            self.attempts = 0

            self.answer_box.delete(
                "1.0",
                tk.END
            )

            self.update_progress()

            if self.current_line >= len(self.code_lines):
                self.finish()

        else:

            self.feedback_label.config(
                text=(
                    "✗ Not quite.\n"
                    "Check your logic and try again."
                )
            )

            self.answer_box.delete(
                "1.0",
                tk.END
            )

    # ========================================================
    # HINT
    # ========================================================

    def show_hint(self):

        if self.current_line >= len(self.code_lines):
            return

        target = self.code_lines[self.current_line].strip()

        if not target:
            self.feedback_label.config(
                text="This line is blank."
            )
            return

        # Don't reveal the whole line.
        #
        # Example:
        #
        # total = 0
        #
        # becomes:
        #
        # Variable assignment
        #
        if "=" in target and not target.startswith(
            ("if ", "while ", "for ")
        ):
            hint = "Hint: this line contains an assignment."

        elif target.startswith("for "):
            hint = "Hint: this line starts a loop."

        elif target.startswith("while "):
            hint = "Hint: this line starts a while loop."

        elif target.startswith("if "):
            hint = "Hint: this line contains a condition."

        elif target.startswith("elif "):
            hint = "Hint: this is another conditional branch."

        elif target.startswith("else"):
            hint = "Hint: this is the alternative branch."

        elif target.startswith("def "):
            hint = "Hint: this line defines a function."

        elif target.startswith("return"):
            hint = "Hint: this line returns something."

        elif target.startswith("print"):
            hint = "Hint: this line outputs something."

        elif target.startswith("import"):
            hint = "Hint: this line imports something."

        elif target.startswith("from "):
            hint = "Hint: this line imports from a module."

        else:
            hint = "Hint: think about what happens at this stage."

        self.feedback_label.config(
            text=hint
        )

    # ========================================================
    # PROGRESS
    # ========================================================

    def update_progress(self):

        if self.current_line >= len(self.code_lines):
            return

        self.progress_label.config(
            text=(
                f"Line {self.current_line + 1} "
                f"of {len(self.code_lines)}"
            )
        )

        self.feedback_label.config(
            text=""
        )

    # ========================================================
    # FINISHED
    # ========================================================

    def finish(self):

        self.clear_window()

        title = tk.Label(
            self.root,
            text="🎉 CODE COMPLETE!",
            font=("Arial", 28, "bold")
        )
        title.pack(pady=60)

        message = tk.Label(
            self.root,
            text=(
                "You successfully recalled the entire program.\n\n"
                "The program accepted different variable names\n"
                "where the underlying structure was the same."
            ),
            font=("Arial", 14),
            justify="center"
        )
        message.pack(pady=20)

        again_button = tk.Button(
            self.root,
            text="PRACTISE AGAIN",
            font=("Arial", 13, "bold"),
            padx=30,
            pady=10,
            command=self.restart_same_code
        )
        again_button.pack(pady=20)

        new_button = tk.Button(
            self.root,
            text="NEW CODE",
            font=("Arial", 12),
            command=self.create_setup_screen
        )
        new_button.pack(pady=10)

    # ========================================================
    # RESTART SAME CODE
    # ========================================================

    def restart_same_code(self):

        self.current_line = 0
        self.attempts = 0
        self.started = True

        self.create_recall_screen()

    # ========================================================
    # CLEAR WINDOW
    # ========================================================

    def clear_window(self):

        for widget in self.root.winfo_children():
            widget.destroy()


# ============================================================
# RUN PROGRAM
# ============================================================

if __name__ == "__main__":

    root = tk.Tk()

    app = CodeRecallApp(root)

    root.mainloop()