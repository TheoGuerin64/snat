import json
import logging
from dataclasses import dataclass
from string import Template
from typing import Any, Callable

from PyQt6 import QtCore, QtNetwork, QtWidgets

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
    func: REPLY_FUNC
    error: ERROR_FUNC
    raw: bool
    other: Any = None


class SteamApi:
    def __init__(self, parent: QtWidgets.QWidget, api_key: str, user_id: str) -> None:
        self.requests: dict[QtNetwork.QNetworkReply, RequestData] = {}
        self.api_key = api_key
        self.user_id = user_id

        self.manager = QtNetwork.QNetworkAccessManager(parent)
        self.manager.finished.connect(self.handle_response)

    def make_get_request(self, url: str, func: REPLY_FUNC, error: ERROR_FUNC,
                         raw: bool = False, other: Any = None) -> None:
        request = QtNetwork.QNetworkRequest(QtCore.QUrl(url))
        reply = self.manager.get(request)
        assert reply is not None
        self.requests[reply] = RequestData(func, error, raw, other)

    def handle_response(self, reply: QtNetwork.QNetworkReply):
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
        url = OWNED_GAMES_URL.substitute(api_key=self.api_key, user_id=self.user_id)
        self.make_get_request(url, func, error)

    def get_game_schemas(self, app_ids: list[int], func: REPLY_FUNC, error: ERROR_FUNC) -> None:
        for app_id in app_ids:
            url = GAME_SCHEMA_URL.substitute(api_key=self.api_key, user_id=self.user_id, app_id=app_id)
            self.make_get_request(url, func, error, other=app_id)

    def get_game_achievements(self, app_id: int, func: REPLY_FUNC, error: ERROR_FUNC) -> None:
        url = USER_ACHIEVEMENTS_URL.substitute(api_key=self.api_key, user_id=self.user_id, app_id=app_id)
        self.make_get_request(url, func, error, other=app_id)
