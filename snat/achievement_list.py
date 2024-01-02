import logging
from typing import Any

from PyQt6 import QtCore, QtGui, QtNetwork, QtWidgets

from .game_list import Achievement, GameList
from .steam_api import SteamApi


class EmptyIcon(QtGui.QIcon):
    """An icon that is empty and transparent"""

    def __init__(self) -> None:
        super().__init__()
        self.addPixmap(self.load_pixmap())

    def load_pixmap(self) -> QtGui.QPixmap:
        """Load the pixmap from the cache or create it if it doesn't exist"""
        pixmap = QtGui.QPixmapCache.find("empty_icon")
        if pixmap is None:
            logging.debug("empty_icon not found in cache")
            pixmap = QtGui.QPixmap(QtCore.QSize(64, 64))
            pixmap.fill(QtGui.QColor("transparent"))
            QtGui.QPixmapCache.insert("empty_icon", pixmap)
        return pixmap


class AchievementWidget(QtWidgets.QListWidgetItem):
    """A widget that displays an achievement

    Attributes:
        icon_url (str): URL of the icon

    Args:
        name (str): Name of the achievement
        icon_url (str): URL of the icon
        steam_api (snat.steam_api.SteamApi): SteamApi instance
    """

    def __init__(self, name: str, icon_url: str, steam_api: SteamApi) -> None:
        super().__init__(EmptyIcon(), name)
        self.icon_url = icon_url
        self.load_icon(steam_api)

    def load_icon(self, steam_api: SteamApi) -> None:
        """Load the icon from the cache or request it if it doesn't exist

        Args:
            steam_api (snat.steam_api.SteamApi): SteamApi instance
        """
        pixmap = QtGui.QPixmapCache.find(self.icon_url)
        if pixmap is not None:
            self.setIcon(QtGui.QIcon(pixmap))
        else:
            steam_api.make_get_request(self.icon_url, self.handle_icon_response, self.handle_icon_error, True)

    def handle_icon_response(self, icon: bytes, other: None) -> None:
        """Load the icon from the response and add it to the cache

        Args:
            icon (bytes): Icon data
            other (None): Unused
        """
        pixmap = QtGui.QPixmap()
        pixmap.loadFromData(icon)
        self.setIcon(QtGui.QIcon(pixmap))
        QtGui.QPixmapCache.insert(self.icon_url, pixmap)

    def handle_icon_error(self, error: QtNetwork.QNetworkReply.NetworkError, other: None) -> None:
        """Leave the icon empty

        Args:
            error (QtNetwork.QNetworkReply.NetworkError): Network error
            other (None): Unused
        """
        logging.warning("Failed to load icon")


class AchievementList(QtWidgets.QListWidget):
    """A list that displays achievements

    Constants:
        WELCOME_MESSAGE (str): Message that is displayed when no game is selected
        COMPLETED_MESSAGE (str): Message that is displayed when all achievements are completed

    Attributes:
        steam_api (snat.steam_api.SteamApi): SteamApi instance
        game_list (snat.game_list.GameList): GameList instance

    Args:
        parent (QtWidgets.QWidget): Parent widget
        steam_api (snat.steam_api.SteamApi): SteamApi instance
        game_list (snat.game_list.GameList): GameList instance
    """

    WELCOME_MESSAGE = "Select a game to view its achievements"
    COMPLETED_MESSAGE = "You've completed all achievements for this game!"

    def __init__(self, parent: QtWidgets.QWidget, steam_api: SteamApi, game_list: GameList) -> None:
        super().__init__(parent)
        self.steam_api = steam_api
        self.game_list = game_list

    def add_achievements(self, achievements: list[Achievement]) -> None:
        """Add achievements to the list

        Args:
            achievements (list[snat.game_list.Achievement]): Achievements to add
        """
        if achievements:
            self.setEnabled(True)
            for achievement in achievements:
                self.addItem(AchievementWidget(achievement.name, achievement.icon, self.steam_api))
        else:
            self.setEnabled(False)
            self.addItem(self.COMPLETED_MESSAGE)

    def load_user_achievements(self, app_id: int | None) -> None:
        """Load the user achievements for the given app_id

        Args:
            app_id (int | None): The app_id to load the achievements for
        """
        self.clear()
        if app_id is None or app_id == -1:
            self.setEnabled(False)
            self.addItem(self.WELCOME_MESSAGE)
            return

        self.steam_api.get_user_achievements(app_id, self.handle_user_achiev_response, self.handle_user_achiev_error)

    def handle_user_achiev_response(self, data: Any, app_id: int) -> None:
        """Load the user achievements from the response

        Args:
            data (Any): Response data
            app_id (int): app_id of the game
        """
        game = self.game_list.get(app_id)
        if game is None:
            logging.error(f"Failed to load schema for app_id {app_id}")
            return

        achievements: list[Achievement] = []
        for raw_achievement in data["playerstats"]["achievements"]:
            if not raw_achievement["achieved"]:
                achievements.append(game.schema[raw_achievement["apiname"]])
        self.add_achievements(achievements)

    def handle_user_achiev_error(self, error: QtNetwork.QNetworkReply.NetworkError, other: None) -> None:
        """Display an error message and disable the list

        Args:
            error (QtNetwork.QNetworkReply.NetworkError): Network error
            other (None): Unused
        """
        self.setEnabled(False)
        QtWidgets.QMessageBox.critical(self, "Error", "Failed to load achievements!\n"
                                       "(You can try to change the game)")
        logging.error("Failed to load achievements")
