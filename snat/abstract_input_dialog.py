import logging
from abc import abstractmethod

from PyQt6 import QtCore, QtNetwork, QtWidgets

from .utils import ABCQtMeta, LinkLabel


class AbstractInputDialog(QtWidgets.QDialog, metaclass=ABCQtMeta):
    """Base class for dialogs that require user input.

    Abstract constants:
        TITLE (str): The title of the dialog
        TEXT (str): The text to display above the input box
        INPUT_NAME (str): The name of the input box

    Abstract methods:
        validate: Validates the input

    Args:
        parent (QtWidgets.QWidget | None): The parent widget
    """

    TITLE: str
    TEXT: str
    INPUT_NAME: str

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.init_ui()

    def init_ui(self) -> None:
        """Initializes the UI."""
        self.setWindowTitle(self.TITLE)

        layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(layout)

        self.label = LinkLabel(self.TEXT, self)
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
        """Validates the input.

        Args:
            input (str): The input to validate

        Returns:
            bool: Input is valid
        """
        return False

    def accept(self) -> None:
        """Override to validate the input before accepting."""
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
    """Base class for dialogs that require user input and make a request.

    Abstract constants:
        TITLE (str): The title of the dialog
        TEXT (str): The text to display above the input box
        INPUT_NAME (str): The name of the input box

    Abstract methods:
        validate: Validates the input
        url: Returns the URL to request
        validate_reply: Validates the reply from the request

    Args:
        parent (QtWidgets.QWidget | None): The parent widget
    """

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.manager = QtNetwork.QNetworkAccessManager(self)
        self.manager.finished.connect(self.handle_response)

    @abstractmethod
    def url(self, text: str) -> str:
        """Returns the URL to request.

        Args:
            text (str): The input text

        Returns:
            str: The URL
        """
        return "Error"

    @abstractmethod
    def validate_reply(self, reply: QtNetwork.QNetworkReply) -> bool:
        """Validates the reply from the request.

        Args:
            reply (QtNetwork.QNetworkReply): The reply from the request

        Returns:
            bool: Reply is valid
        """
        return False

    def make_request(self) -> None:
        """Makes the GET request."""
        self.setDisabled(True)
        url = QtCore.QUrl(self.url(self.input.text()))
        request = QtNetwork.QNetworkRequest(url)
        self.manager.get(request)

    def handle_response(self, reply: QtNetwork.QNetworkReply):
        """Handles the response from the request.

        Args:
            reply (QtNetwork.QNetworkReply): The reply from the request
        """
        if self.validate_reply(reply):
            super().accept()
        else:
            QtWidgets.QMessageBox.critical(self, "Error", "Invalid input")
            logging.warning("Invalid input")
        self.setDisabled(False)

    def accept(self) -> None:
        """Override to validate the input before accepting."""
        if self.input.text() == "":
            QtWidgets.QMessageBox.critical(self, "Error", f"No {self.INPUT_NAME} provided")
            logging.warning(f"No {self.INPUT_NAME} provided")
            return

        if not self.validate(self.input.text()):
            QtWidgets.QMessageBox.critical(self, "Error", f"Invalid {self.INPUT_NAME}")
            logging.warning(f"Invalid {self.INPUT_NAME}")
            return

        self.make_request()
