import logging
from pickle import dumps, loads
from string import Template

from PyQt6 import QtCore, QtNetwork, QtWidgets

from .abstract_input_dialog import AbstractRequestInputDialog
from .game_list import GameList

API_KEY_URL = "https://steamcommunity.com/dev/apikey"
TEST_STEAM_API_KEY_URL = Template("https://api.steampowered.com/ISteamWebAPIUtil/GetSupportedAPIList/v1"
                                  "?key=$api_key")
TEST_STEAM_ID_URL = Template("https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2"
                             "?key=$api_key&steamids=$steam_id")


class SteamAPIKeyDialog(AbstractRequestInputDialog):
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
    TITLE = "Steam ID"
    TEXT = "Please enter your Steam ID:"
    INPUT_NAME = "Steam ID"

    def __init__(self, api_key: str) -> None:
        super().__init__()
        self.api_key = api_key

    def validate(self, text: str) -> bool:
        return len(text) == 17 and text.isnumeric()

    def url(self, text: str) -> str:
        return TEST_STEAM_ID_URL.substitute(api_key=self.api_key, steam_id=text)

    def validate_reply(self, reply: QtNetwork.QNetworkReply) -> bool:
        if reply.error() != QtNetwork.QNetworkReply.NetworkError.NoError:
            return False
        text = reply.readAll().data().decode()
        return text != "{\"response\":{\"players\":[]}}"


class Settings(QtCore.QSettings):
    def __init__(self, parent: QtWidgets.QWidget):
        """ Raises RuntimeError if a dialog is rejected """
        super().__init__(parent)
        self.define_if_not_exists("steam_api_key", SteamAPIKeyDialog())
        self.define_if_not_exists("steam_user_id", SteamUserIdDialog(self.value("steam_api_key")))

    def define_if_not_exists(self, key: str, dialog: AbstractRequestInputDialog) -> None:
        """ Raises RuntimeError if the dialog is rejected """
        if not self.contains(key):
            logging.info(f"Setting {key} not found, prompting user")
            dialog.exec()
            if dialog.result() == QtWidgets.QDialog.DialogCode.Accepted:
                self.setValue(key, dialog.input.text())
            else:
                raise RuntimeError(f"No {key} provided")

    @property
    def steam_api_key(self) -> str:
        return self.value("steam_api_key")

    @property
    def steam_user_id(self) -> str:
        return self.value("steam_user_id")

    @property
    def game_list_cache(self) -> GameList:
        cache = self.value("schemes", None)
        if cache is None:
            return GameList()
        logging.info("Loading game list from cache")

        try:
            return loads(cache)
        except Exception as exception:
            logging.warning("Failed to load game list from cache", exc_info=exception)
            return GameList()

    @game_list_cache.setter
    def game_list_cache(self, value: GameList) -> None:
        self.setValue("schemes", dumps(value))

    @property
    def selected_game(self) -> int | None:
        value = self.value("selected_game", None)
        if value is None:
            return None
        return int(value)

    @selected_game.setter
    def selected_game(self, value: int) -> None:
        self.setValue("selected_game", str(value))

    @property
    def position(self) -> QtCore.QPoint | None:
        return self.value("position", None)

    @position.setter
    def position(self, value: QtCore.QPoint) -> None:
        self.setValue("position", value)

    @property
    def size(self) -> QtCore.QSize | None:
        return self.value("size", None)

    @size.setter
    def size(self, value: QtCore.QSize) -> None:
        self.setValue("size", value)
