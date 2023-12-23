import logging
from abc import abstractmethod

from PyQt6 import QtCore, QtNetwork, QtWidgets

from .utils import ABCQtMeta


class AbstractInputDialog(QtWidgets.QDialog, metaclass=ABCQtMeta):
    TITLE: str
    TEXT: str
    INPUT_NAME: str

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.init_ui()

    def init_ui(self) -> None:
        self.setWindowTitle(self.TITLE)

        layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(layout)

        self.label = QtWidgets.QLabel(self.TEXT, self)
        self.label.setOpenExternalLinks(True)
        layout.addWidget(self.label)

        self.input = QtWidgets.QLineEdit(self)
        self.input.setPlaceholderText(self.INPUT_NAME.title())
        layout.addWidget(self.input)

        self.button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel, self)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    @abstractmethod
    def validate(self, input: str) -> bool:
        return False

    def accept(self) -> None:
        if self.input.text() == "":
            QtWidgets.QMessageBox.critical(self, "Error", f"No {self.INPUT_NAME} provided")
            logging.warning(f"No {self.INPUT_NAME} provided")
            return

        if not self.validate(self.input.text()):
            QtWidgets.QMessageBox.critical(self, "Error", f"Invalid {self.INPUT_NAME}")
            logging.warning(f"Invalid {self.INPUT_NAME}")
            return

        super().accept()


class AbstractRequestInputDialog(AbstractInputDialog):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.manager = QtNetwork.QNetworkAccessManager(self)
        self.manager.finished.connect(self.handle_response)

    @abstractmethod
    def url(self, text: str) -> str:
        return "Error"

    @abstractmethod
    def validate_reply(self, reply: QtNetwork.QNetworkReply) -> bool:
        return False

    def make_request(self) -> None:
        self.setDisabled(True)
        url = QtCore.QUrl(self.url(self.input.text()))
        request = QtNetwork.QNetworkRequest(url)
        self.manager.get(request)

    def handle_response(self, reply: QtNetwork.QNetworkReply):
        if self.validate_reply(reply):
            super().accept()
        else:
            QtWidgets.QMessageBox.critical(self, "Error", "Invalid input")
            logging.warning("Invalid input")
        self.setDisabled(False)

    def accept(self) -> None:
        if self.input.text() == "":
            QtWidgets.QMessageBox.critical(self, "Error", f"No {self.INPUT_NAME} provided")
            logging.warning(f"No {self.INPUT_NAME} provided")
            return

        if not self.validate(self.input.text()):
            QtWidgets.QMessageBox.critical(self, "Error", f"Invalid {self.INPUT_NAME}")
            logging.warning(f"Invalid {self.INPUT_NAME}")
            return

        self.make_request()
