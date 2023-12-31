import argparse
import logging
import sys
from pathlib import Path

from PyQt6 import QtCore, QtWidgets

from . import __version__
from .app import App


def parse_args() -> argparse.Namespace:
    """Parse the command line arguments.

    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Track your Steam achievements", epilog="Made by Theo Guerin")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")
    return parser.parse_args()


def configure_logging(debug: bool) -> None:
    """Configure the logging system.

    Args:
        debug (bool): Whether to enable debug logging
    """
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG if debug else logging.WARNING)

    file_handler = logging.FileHandler(Path(__file__).parent / "latest.log")
    file_handler.setLevel(logging.INFO)

    logging.basicConfig(
        level=logging.DEBUG,
        format="[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s",
        handlers=[stream_handler, file_handler]
    )


def config_search_path() -> None:
    """Configure the search path for Qt resources."""
    QtCore.QDir.addSearchPath("asset", str(Path(__file__).parent / "asset"))


def start_app() -> None:
    """Start the Qt application."""
    app = QtWidgets.QApplication(sys.argv[:1])
    window = App()
    window.show()
    sys.exit(app.exec())


def main() -> None:
    """Main entry point of the application."""
    args = parse_args()
    configure_logging(args.debug)
    config_search_path()
    logging.info(f"Start Steam Achievement Tracker {__version__} with PyQt6 {QtCore.PYQT_VERSION_STR}")
    start_app()


if __name__ == "__main__":
    main()
