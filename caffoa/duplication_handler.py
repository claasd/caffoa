import logging


class DuplicationHandler:
    def __init__(self, mode: str):
        self.mode = mode.strip().lower()
        self.names = list()

    def should_generate(self, name: str):
        if self.mode == "once":
            if name in self.names:
                logging.warning(f"Skipping {name}, already written earlier")
                return False
        return True

    def store_generated(self, name : str):
        self.names.append(name)