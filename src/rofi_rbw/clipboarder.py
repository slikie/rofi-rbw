import time
from subprocess import run

from .abstractionhelper import is_installed, is_wayland


class Clipboarder:
    @staticmethod
    def best_option(name: str = None) -> "Clipboarder":
        try:
            return next(clipboarder for clipboarder in Clipboarder.__subclasses__() if clipboarder.name() == name)()
        except StopIteration:
            try:
                return next(clipboarder for clipboarder in Clipboarder.__subclasses__() if clipboarder.supported())()
            except StopIteration:
                return Clipboarder()

    @staticmethod
    def supported() -> bool:
        pass

    @staticmethod
    def name() -> str:
        pass

    def copy_to_clipboard(self, characters: str) -> None:
        raise NoClipboarderFoundException()

    def clear_clipboard_after(self, clear: int) -> None:
        raise NoClipboarderFoundException()


class XSelClipboarder(Clipboarder):
    __last_copied_characters: str

    @staticmethod
    def supported() -> bool:
        return not is_wayland() and is_installed("xsel")

    @staticmethod
    def name() -> str:
        return "xsel"

    def copy_to_clipboard(self, characters: str) -> None:
        run(["xsel", "--input", "--clipboard"], input=characters, encoding="utf-8")

        self.__last_copied_characters = characters

    def fetch_clipboard_content(self) -> str:
        return run(
            [
                "xsel",
                "--output",
                "--clipboard",
            ],
            capture_output=True,
            encoding="utf-8",
        ).stdout

    def clear_clipboard_after(self, clear: int) -> None:
        if clear > 0:
            time.sleep(clear)

            # Only clear clipboard if nothing has been copied since the password
            if self.fetch_clipboard_content() == self.__last_copied_characters:
                run(["xsel", "--clear", "--clipboard"])
                self.__last_copied_characters = None


class XClipClipboarder(Clipboarder):
    __last_copied_characters: str

    @staticmethod
    def supported() -> bool:
        return not is_wayland() and is_installed("xclip")

    @staticmethod
    def name() -> str:
        return "xclip"

    def copy_to_clipboard(self, characters: str) -> None:
        run(["xclip", "-in", "-selection", "clipboard"], input=characters, encoding="utf-8")

        self.__last_copied_characters = characters

    def fetch_clipboard_content(self) -> str:
        return run(["xclip", "-o", "-selection", "clipboard"], capture_output=True, encoding="utf-8").stdout

    def clear_clipboard_after(self, clear: int) -> None:
        if clear > 0:
            time.sleep(clear)

            # Only clear clipboard if nothing has been copied since the password
            if self.fetch_clipboard_content() == self.__last_copied_characters:
                self.copy_to_clipboard("")
                self.__last_copied_characters = None


class WlClipboarder(Clipboarder):
    @staticmethod
    def supported() -> bool:
        return is_wayland() and is_installed("wl-copy")

    @staticmethod
    def name() -> str:
        return "wl-copy"

    def copy_to_clipboard(self, characters: str) -> None:
        run(["wl-copy"], input=characters, encoding="utf-8")

    def clear_clipboard_after(self, clear: int) -> None:
        if clear > 0:
            time.sleep(clear)
            run(["wl-copy", "--clear"])


class NoClipboarderFoundException(Exception):
    def __str__(self) -> str:
        return "Could not find a valid way to copy to clipboard. Please check the required dependencies."
