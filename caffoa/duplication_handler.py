import logging


class DuplicationHandler:
    instance = None

    def __init__(self, mode: str):
        self.mode = mode.strip().lower()
        self.names = list()

    def should_generate(self, name: str):
        if self.mode == "once":
            if name in self.names:
                logging.warning(f"Skipping {name}, already written earlier")
                return False
        return True

    def store_generated(self, name: str):
        self.names.append(name)


def get() -> DuplicationHandler:
    return DuplicationHandler.instance


def init(mode: str):
    DuplicationHandler.instance = DuplicationHandler(mode)


def should_generate(name) -> bool:
    return get().should_generate(name)


def store_generated(name):
    return get().store_generated(name)
