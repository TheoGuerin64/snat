import argparse
import logging
import sys
from pathlib import Path

from PyQt6 import QtWidgets

from . import __version__
from .app import App


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Track your Steam achievements", epilog="Made by Theo Guerin")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")
    return parser.parse_args()


def configure_logging(debug: bool) -> None:
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG if debug else logging.WARNING)

    file_handler = logging.FileHandler(Path(__file__).parent.parent / "latest.log")
    file_handler.setLevel(logging.INFO)

    logging.basicConfig(
        level=logging.DEBUG,
        format="[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s",
        handlers=[stream_handler, file_handler]
    )


def start_app() -> None:
    app = QtWidgets.QApplication(sys.argv[:1])
    window = App()
    window.show()
    sys.exit(app.exec())


def main():
    args = parse_args()
    configure_logging(args.debug)
    logging.info("Starting Steam Achievement Tracker")
    start_app()


if __name__ == "__main__":
    main()
