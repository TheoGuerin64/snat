import json
import logging
from dataclasses import dataclass
from string import Template
from typing import Any, Callable

from PyQt6 import QtCore, QtNetwork, QtWidgets

from .settings import Settings

REPLY_FUNC = Callable[[Any, Any], None]
ERROR_FUNC = Callable[[QtNetwork.QNetworkReply.NetworkError, Any], None]

OWNED_GAMES_URL = Template("https://api.steampowered.com/IPlayerService/GetOwnedGames/v1"
                           "?key=$api_key&steamid=$user_id&include_appinfo=true&include_played_free_games=true")
GAME_SCHEMA_URL = Template("http://api.steampowered.com/ISteamUserStats/GetSchemaForGame/v2"
                           "?key=$api_key&steamid=$user_id&appid=$app_id")
USER_ACHIEVEMENTS_URL = Template("https://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v1"
                                 "?key=$api_key&steamid=$user_id&appid=$app_id")


@dataclass
class RequestData:
    """Data class for storing request data

    Attributes:
        func (REPLY_FUNC): Function to call on success
        error (ERROR_FUNC): Function to call on error
        raw (bool): Whether the response should be parsed as JSON
        other (Any): Other data to pass to the functions
    """

    func: REPLY_FUNC
    error: ERROR_FUNC
    raw: bool
    other: Any = None


class SteamApi:
    """Provides access to the Steam API

    Attributes:
        requests (dict[QtNetwork.QNetworkReply, RequestData]): Map of requests to their data
        api_key (str): Steam API key
        user_id (str): Steam user ID
        manager (QtNetwork.QNetworkAccessManager): Network access manager

    Args:
        parent (QtWidgets.QWidget): Parent widget
        settings (snat.settings.Settings): Settings instance
    """

    def __init__(self, parent: QtWidgets.QWidget, settings: Settings) -> None:
        self.requests: dict[QtNetwork.QNetworkReply, RequestData] = {}

        self.api_key = settings.typedValue("steam_api_key", str)
        if self.api_key is None:
            raise RuntimeError("No Steam API key found")
        self.user_id = settings.typedValue("steam_user_id", str)
        if self.user_id is None:
            raise RuntimeError("No Steam user ID found")

        self.manager = QtNetwork.QNetworkAccessManager(parent)
        self.manager.finished.connect(self.handle_response)

    def make_get_request(self, url: str, func: REPLY_FUNC, error: ERROR_FUNC,
                         raw: bool = False, other: Any = None) -> None:
        """Make a GET request to the given URL

        Args:
            url (str): URL to make the request to
            func (REPLY_FUNC): Function to call on success
            error (ERROR_FUNC): Function to call on error
            raw (bool, optional): Whether the response should be parsed as JSON.
            other (Any, optional): Other data to pass to the functions.

        Raises:
            RuntimeError: If the request creation fails
        """
        request = QtNetwork.QNetworkRequest(QtCore.QUrl(url))
        reply = self.manager.get(request)
        if reply is None:
            raise RuntimeError("Network error")
        self.requests[reply] = RequestData(func, error, raw, other)

    def handle_response(self, reply: QtNetwork.QNetworkReply) -> None:
        """Process the response and call the appropriate functions

        Args:
            reply (QtNetwork.QNetworkReply): Network reply
        """
        request_data = self.requests.pop(reply)
        match reply.error():
            case QtNetwork.QNetworkReply.NetworkError.NoError:
                data = reply.readAll().data()
                if not request_data.raw:
                    data = json.loads(data.decode())
                request_data.func(data, request_data.other)
            case _:
                request_data.error(reply.error(), request_data.other)
                status_code = reply.attribute(QtNetwork.QNetworkRequest.Attribute.HttpStatusCodeAttribute)
                url = reply.url().toString()
                logging.warning("GET Status ERROR (%d) %s", status_code, url)

    def get_owned_games(self, func: REPLY_FUNC, error: ERROR_FUNC) -> None:
        """Get the list of owned games

        Args:
            func (REPLY_FUNC): Function to call on success
            error (ERROR_FUNC): Function to call on error
        """
        url = OWNED_GAMES_URL.substitute(api_key=self.api_key, user_id=self.user_id)
        self.make_get_request(url, func, error)

    def get_game_schemas(self, app_ids: list[int], func: REPLY_FUNC, error: ERROR_FUNC) -> None:
        """Get the schemas for the given app IDs

        Args:
            app_ids (list[int]): App IDs to get the schemas for
            func (REPLY_FUNC): Function to call on success
            error (ERROR_FUNC): Function to call on error
        """
        for app_id in app_ids:
            url = GAME_SCHEMA_URL.substitute(api_key=self.api_key, user_id=self.user_id, app_id=app_id)
            self.make_get_request(url, func, error, other=app_id)

    def get_user_achievements(self, app_id: int, func: REPLY_FUNC, error: ERROR_FUNC) -> None:
        """Get the user achievements for the given app ID

        Args:
            app_id (int): App ID to get the achievements for
            func (REPLY_FUNC): Function to call on success
            error (ERROR_FUNC): Function to call on error
        """
        url = USER_ACHIEVEMENTS_URL.substitute(api_key=self.api_key, user_id=self.user_id, app_id=app_id)
        self.make_get_request(url, func, error, other=app_id)
