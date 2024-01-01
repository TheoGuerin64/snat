import logging
from abc import abstractmethod
from string import Template

from PyQt6 import QtCore, QtNetwork, QtWidgets

from .utils import ABCQtMeta, LinkLabel

API_KEY_URL = "https://steamcommunity.com/dev/apikey"
TEST_STEAM_API_KEY_URL = Template("https://api.steampowered.com/ISteamWebAPIUtil/GetSupportedAPIList/v1"
                                  "?key=$api_key")
TEST_STEAM_ID_URL = Template("https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2"
                             "?key=$api_key&steamids=$steam_id")


class AbstractInputDialog(QtWidgets.QDialog, metaclass=ABCQtMeta):
    """Base class for dialogs that require user input.

    Abstract constants:
        TITLE (str): Title of the dialog
        TEXT (str): Text to display above the input box
        INPUT_NAME (str): Name of the input box

    Abstract methods:
        validate: Validates the input

    Args:
        parent (PyQt6.QtWidgets.QWidget | None): Parent widget
    """

    TITLE: str
    TEXT: str
    INPUT_NAME: str

    def __init__(self, settings: QtCore.QSettings, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.init_ui()

    def init_ui(self) -> None:
        """Configure the window, create widgets and set the layout."""
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
    """Override AbstractInputDialog to make a request after validating the input.

    Abstract constants:
        TITLE (str): Title of the dialog
        TEXT (str): Text to display above the input box
        INPUT_NAME (str): Name of the input box

    Abstract methods:
        validate: Validates the input
        url: Returns the URL to request
        validate_reply: Validates the reply from the request

    Attributes:
        manager (PyQt6.QtNetwork.QNetworkAccessManager): Network access manager

    Args:
        settings (PyQt6.QtCore.QSettings): Settings instance
        parent (PyQt6.QtWidgets.QWidget | None): Parent widget
    """

    def __init__(self, settings: QtCore.QSettings, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(settings, parent)
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
            reply (PyQt6.QtNetwork.QNetworkReply): The reply from the request

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

    def handle_response(self, reply: QtNetwork.QNetworkReply) -> None:
        """Handles the response from the request.

        Args:
            reply (PyQt6.QtNetwork.QNetworkReply): The reply from the request
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


class SteamAPIKeyDialog(AbstractRequestInputDialog):
    """Prompts the user for their Steam API key"""

    TITLE = "Steam API Key"
    TEXT = f"Please enter your Steam API key (<a href='{API_KEY_URL}'>{API_KEY_URL}</a>):"
    INPUT_NAME = "key"

    def validate(self, text: str) -> bool:
        return len(text) == 32 and text.isalnum()

    def url(self, text: str) -> str:
        return TEST_STEAM_API_KEY_URL.substitute(api_key=text)

    def validate_reply(self, reply: QtNetwork.QNetworkReply) -> bool:
        return reply.error() == QtNetwork.QNetworkReply.NetworkError.NoError


class SteamUserIdDialog(AbstractRequestInputDialog):
    """Prompts the user for their Steam ID"""

    TITLE = "Steam ID"
    TEXT = "Please enter your Steam ID:"
    INPUT_NAME = "Steam ID"

    def __init__(self, settings: QtCore.QSettings) -> None:
        super().__init__(settings)
        self.api_key = settings.value("steam_api_key", type=str)

    def validate(self, text: str) -> bool:
        return len(text) == 17 and text.isnumeric()

    def url(self, text: str) -> str:
        return TEST_STEAM_ID_URL.substitute(api_key=self.api_key, steam_id=text)

    def validate_reply(self, reply: QtNetwork.QNetworkReply) -> bool:
        if reply.error() != QtNetwork.QNetworkReply.NetworkError.NoError:
            return False
        text = reply.readAll().data().decode()
        return text != "{\"response\":{\"players\":[]}}"
