import os


class BaseWriter:
    def __init__(self, version: int):
        self.version = version
        self.template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"data/v{version}")
        self.base_template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"data/base")

    def load_template(self, name):
        path = os.path.join(self.template_folder, name)
        if not os.path.exists(path):
            path = os.path.join(self.base_template_folder, name)

        with open(path, "r", encoding="utf-8") as f:
            return f.read()
