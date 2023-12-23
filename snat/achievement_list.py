import logging
from typing import Any

from PyQt6 import QtCore, QtGui, QtWidgets

from .game_list import Achievement, GameList
from .steam_api import SteamApi


class EmptyIcon(QtGui.QIcon):
    def __init__(self) -> None:
        super().__init__()
        self.addPixmap(self.load_pixmap())

    def load_pixmap(self) -> QtGui.QPixmap:
        pixmap = QtGui.QPixmapCache.find("empty_icon")
        if pixmap is None:
            logging.debug("empty_icon not found in cache")
            pixmap = QtGui.QPixmap(QtCore.QSize(64, 64))
            pixmap.fill(QtGui.QColor("transparent"))
            QtGui.QPixmapCache.insert("empty_icon", pixmap)
        return pixmap


class AchievementWidget(QtWidgets.QListWidgetItem):
    def __init__(self, name: str, icon_url: str, steam_api: SteamApi) -> None:
        super().__init__(EmptyIcon(), name)
        self.icon_url = icon_url
        self.load_icon(steam_api)

    def load_icon(self, steam_api: SteamApi) -> None:
        pixmap = QtGui.QPixmapCache.find(self.icon_url)
        if pixmap is not None:
            self.setIcon(QtGui.QIcon(pixmap))
        else:
            steam_api.make_get_request(self.icon_url, self.handle_response, self.handle_error, True, self.icon_url)

    def handle_response(self, data: bytes, _) -> None:
        pixmap = QtGui.QPixmap()
        pixmap.loadFromData(data)
        self.setIcon(QtGui.QIcon(pixmap))
        QtGui.QPixmapCache.insert(self.icon_url, pixmap)

    def handle_error(self, *_) -> None:
        logging.warning("Failed to load icon")


class AchievementList(QtWidgets.QListWidget):
    WELCOME_MESSAGE = "Select a game to view its achievements"
    COMPLETED_MESSAGE = "You've completed all achievements for this game!"

    def __init__(self, parent: QtWidgets.QWidget, steam_api: SteamApi, game_list: GameList) -> None:
        super().__init__(parent)
        self.steam_api = steam_api
        self.game_list = game_list

    def add_achievements(self, achievements: list[Achievement]) -> None:
        match achievements:
            case []:
                self.setEnabled(False)
                self.addItem(self.COMPLETED_MESSAGE)
            case _:
                self.setEnabled(True)
                for achievement in sorted(achievements, key=lambda achievement: achievement.name.lower()):
                    self.addItem(AchievementWidget(achievement.name, achievement.icon, self.steam_api))

    def load_achievements(self, app_id: int | None) -> None:
        self.clear()
        if app_id is None or app_id == -1:
            self.setEnabled(False)
            self.addItem(self.WELCOME_MESSAGE)
            return

        self.steam_api.get_game_achievements(app_id, self.handle_game_achievements, self.handle_error)

    def handle_game_achievements(self, data: Any, app_id: int) -> None:
        game = self.game_list.get(app_id)
        if game is None:
            logging.error(f"Failed to load schema for app_id {app_id}")
            return
        achievements: list[Achievement] = []
        for raw_achievement in data["playerstats"]["achievements"]:
            if not raw_achievement["achieved"]:
                achievements.append(game.schema[raw_achievement["apiname"]])
        self.add_achievements(achievements)

    def handle_error(self, *_) -> None:
        self.setEnabled(False)
        QtWidgets.QMessageBox.critical(self, "Error", "Failed to load achievements!\n"
                                       "(You can try to change the game)")
        logging.error("Failed to load achievements")
