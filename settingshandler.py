from typing import Any
from os.path import isfile
import pickle


class SettingsHandler:
    def __init__(self, filename):
        self.file = filename
        if not isfile(self.file):
            pickle.dump({}, open(self.file, 'bx'))

    def get_state(self, quality: str, default: Any = None) -> Any:
        settings: dict = pickle.load(open(self.file, 'br'))
        return settings.get(quality, default)

    def set_state(self, quality, value: Any) -> None:
        settings: dict = pickle.load(open(self.file, "br"))
        settings[quality] = value
        pickle.dump(settings, open(self.file, 'bw'))

    def register_state(self, quality, default_value: Any = None):
        if self.get_state(quality) is None:
            self.set_state(quality, default_value)
