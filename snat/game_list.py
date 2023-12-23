import logging
from dataclasses import dataclass, field
from typing import Any

from PyQt6 import QtCore, QtWidgets

from .steam_api import SteamApi
from .utils import DotAnimationLabel

GameList = dict[int, "Game"]


@dataclass
class Achievement:
    name: str
    icon: str

    @staticmethod
    def from_raw(raw: dict[str, Any]) -> "Achievement":
        return Achievement(raw["displayName"], raw["icon"])


@dataclass
class Game:
    name: str
    schema: dict[Any, Achievement] = field(default_factory=dict)

    @staticmethod
    def from_raw(raw: dict[str, Any]) -> "Game":
        return Game(raw["name"])


class GameListBar(QtWidgets.QWidget):
    selected = QtCore.pyqtSignal(int)
    loaded = QtCore.pyqtSignal()

    def __init__(self, parent: QtWidgets.QWidget, steam_api: SteamApi, game_list: GameList) -> None:
        super().__init__(parent)
        self.steam_api = steam_api
        self.game_list = game_list
        self.schema_downloaded_count: int
        self.schema_downloaded_max: int
        self.init_ui()
        if game_list:
            self.add_games()
        else:
            self.load_owned_games()

        self.game_list_widget.currentIndexChanged.connect(self.index_changed)
        self.refresh.clicked.connect(self.refresh_game_list)

    def init_ui(self) -> None:
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.game_list_widget = QtWidgets.QComboBox(self)
        self.game_list_widget.setStyleSheet("QComboBox { combobox-popup: 0; }")
        layout.addWidget(self.game_list_widget)

        self.refresh = QtWidgets.QPushButton("⟳", self)
        self.refresh.setToolTip("Refresh")
        self.refresh.setFixedWidth(self.refresh.sizeHint().height())
        layout.addWidget(self.refresh)

        self.progress_dialog = QtWidgets.QProgressDialog(self)
        self.progress_dialog.setCancelButton(None)
        self.progress_dialog.setAutoReset(False)
        self.progress_dialog.setAutoClose(False)
        self.progress_dialog.setLabel(DotAnimationLabel(self.progress_dialog))
        self.progress_dialog.close()

    def add_games(self) -> None:
        self.game_list_widget.addItem("All Games")
        for app_id, game in sorted(self.game_list.items(), key=lambda game: game[1].name.lower()):
            self.game_list_widget.addItem(game.name, app_id)

    def select_game(self, app_id: int) -> None:
        index = self.game_list_widget.findData(app_id)
        if index == -1:
            index = 0
        self.game_list_widget.setCurrentIndex(index)
        self.selected.emit(app_id)

    def load_owned_games(self) -> None:
        self.progress_dialog.setLabelText("Download owned games list")
        self.progress_dialog.setValue(0)
        self.progress_dialog.open()
        self.schema_downloaded_count = 0
        self.steam_api.get_owned_games(self.handle_owned_games_data, self.handle_owned_games_error)

    def handle_owned_games_data(self, data: Any, _) -> None:
        for owned_game in data["response"]["games"]:
            if owned_game["playtime_forever"] > 0:
                self.game_list[owned_game["appid"]] = Game.from_raw(owned_game)

        self.schema_downloaded_max = len(self.game_list)
        self.progress_dialog.setLabelText("Download games schemas")
        self.progress_dialog.setMaximum(self.schema_downloaded_max)
        app_ids = list(self.game_list.keys())
        self.steam_api.get_game_schemas(app_ids, self.handle_game_schemas_data, self.handle_game_schemas_error)

    def handle_owned_games_error(self, *_) -> None:
        self.progress_dialog.close()
        QtWidgets.QMessageBox.critical(self, "Error", "Failed to load owned games!\n"
                                       "(You can try to refresh the game list or restart the application)")
        logging.error("Failed to load owned games")

    @staticmethod
    def is_game_schema_valid(schema: Any) -> bool:
        return (
            "game" in schema
            and "availableGameStats" in schema["game"]
            and "achievements" in schema["game"]["availableGameStats"]
        )

    def handle_game_schemas_data(self, data: Any, app_id: int) -> None:
        if self.schema_downloaded_count == -1:
            return

        if self.is_game_schema_valid(data):
            for raw_achievement in data["game"]["availableGameStats"]["achievements"]:
                self.game_list[app_id].schema[raw_achievement["name"]] = Achievement.from_raw(raw_achievement)
        else:
            del self.game_list[app_id]
            logging.info("Invalid schema for app_id %d", app_id)

        self.schema_downloaded_count += 1
        self.progress_dialog.setValue(self.schema_downloaded_count)
        if self.schema_downloaded_count == self.schema_downloaded_max:
            self.add_games()
            self.loaded.emit()
            self.progress_dialog.close()

    def handle_game_schemas_error(self, *_) -> None:
        if self.schema_downloaded_count == -1:
            return

        self.schema_downloaded_count = -1
        self.progress_dialog.close()
        QtWidgets.QMessageBox.critical(self, "Error", "Failed to load games schemas!\n"
                                       "(You can try to refresh the game list or restart the application)")
        logging.error("Failed to load games schemas")

    def index_changed(self, index: int) -> None:
        app_id = self.game_list_widget.itemData(index)
        if app_id is None:
            self.selected.emit(-1)
        else:
            self.selected.emit(app_id)

    def refresh_game_list(self) -> None:
        self.game_list_widget.clear()
        self.game_list.clear()
        self.load_owned_games()
