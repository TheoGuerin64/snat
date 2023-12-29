from PyQt6 import QtCore, QtGui, QtWidgets

from . import __version__
from .achievement_list import AchievementList
from .game_list import GameList, GameListBar
from .settings import Settings
from .steam_api import SteamApi


class MainWidget(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget, settings: Settings) -> None:
        super().__init__(parent)
        self.settings = settings
        self.steam_api = SteamApi(self, self.settings.steam_api_key, self.settings.steam_user_id)
        self.game_list: GameList = self.settings.game_list_cache
        self.init_ui()

        self.game_list_bar.loaded.connect(self.on_games_loaded)
        self.game_list_bar.selected.connect(self.on_game_selected)

        if self.game_list is not None and self.settings.selected_game is not None:
            self.game_list_bar.select_game(self.settings.selected_game)

    def init_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(layout)

        self.game_list_bar = GameListBar(self, self.steam_api, self.game_list)
        layout.addWidget(self.game_list_bar)

        self.achievement_list = AchievementList(self, self.steam_api, self.game_list)
        layout.addWidget(self.achievement_list)

    def on_games_loaded(self) -> None:
        self.settings.game_list_cache = self.game_list

    def on_game_selected(self, app_id: int) -> None:
        self.settings.selected_game = app_id
        self.achievement_list.load_achievements(app_id)


class App(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        QtCore.QCoreApplication.setApplicationName("Snat")
        QtCore.QCoreApplication.setOrganizationName("Theo Guerin")
        QtCore.QCoreApplication.setApplicationVersion(__version__)

        self.settings = Settings(self)
        if self.settings.position is not None:
            self.move(self.settings.position)
        if self.settings.size is not None:
            self.resize(self.settings.size)

        self.setCentralWidget(MainWidget(self, self.settings))

    def moveEvent(self, event: QtGui.QMoveEvent | None) -> None:
        super().moveEvent(event)
        self.settings.position = self.pos()

    def resizeEvent(self, event: QtGui.QResizeEvent | None) -> None:
        super().resizeEvent(event)
        self.settings.size = self.size()
