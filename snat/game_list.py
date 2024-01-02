import logging
from dataclasses import dataclass, field
from typing import Any

from PyQt6 import QtCore, QtNetwork, QtWidgets

from .steam_api import SteamApi
from .utils import DotAnimationLabel


@dataclass
class Achievement:
    """Dataclass representing an achievement

    Fields:
        name (str): Achievement name
        icon (str): Achievement icon url
    """

    name: str
    icon: str


@dataclass
class Game:
    """Game dataclass

    Fields:
        name (str): Game name
        schema (dict): Game achievements schema
    """

    name: str
    schema: dict[Any, Achievement] = field(default_factory=dict)


GameList = dict[int, Game]


class GameListBar(QtWidgets.QWidget):
    """Display the game list and handle the game selection.

    Signals:
        selected (int): Emitted when a game is selected
        loaded (): Emitted when the game list is loaded

    Attributes:
        steam_api (snat.steam_api.SteamApi): Steam API instance
        game_list (snat.game_list.GameList): Game list instance
        schema_downloaded_count (int): Number of downloaded schemas
        schema_downloaded_max (int): Maximum number of schemas to download

    Args:
        parent (PyQt6.QtWidgets.QWidget): Parent widget
        steam_api (snat.steam_api.SteamApi): Steam API instance
        game_list (snat.game_list.GameList): Game list instance
    """

    selected = QtCore.pyqtSignal(int)
    loaded = QtCore.pyqtSignal()

    def __init__(self, steam_api: SteamApi, game_list: GameList, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.steam_api = steam_api
        self.game_list = game_list
        self.schema_downloaded_count = 0
        self.schema_downloaded_max = 0
        self.init_ui()

        if game_list:
            self.add_games()
        else:
            self.load_owned_games()

        self.game_combo_box.currentIndexChanged.connect(self.index_changed)
        self.refresh.clicked.connect(self.refresh_game_list)

    def init_ui(self) -> None:
        """Create widgets and set the layout."""
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.game_combo_box = QtWidgets.QComboBox(self)
        self.game_combo_box.setStyleSheet("QComboBox { combobox-popup: 0; }")
        layout.addWidget(self.game_combo_box)

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
        """Add games from games list to the game list widget."""
        self.game_combo_box.addItem("All Games")
        for app_id, game in sorted(self.game_list.items(), key=lambda game: game[1].name.lower()):
            self.game_combo_box.addItem(game.name, app_id)

    def select_game(self, app_id: int) -> None:
        """Select a game in the game list widget.

        Args:
            app_id (int): Game app_id
        """
        index = self.game_combo_box.findData(app_id) if app_id != -1 else 0
        self.game_combo_box.setCurrentIndex(index)

    def load_owned_games(self) -> None:
        """Start the owned games downloading and open the progress dialog."""
        self.progress_dialog.setLabelText("Download owned games list")
        self.progress_dialog.setValue(0)
        self.progress_dialog.open()
        self.schema_downloaded_count = 0
        self.steam_api.get_owned_games(self.handle_owned_games_response, self.handle_owned_games_error)

    def handle_owned_games_response(self, data: Any, other: None) -> None:
        """Add owned games to the game list and start the schemas downloading.

        Args:
            data (Any): JSON data from the Steam API
            other (None): Unused
        """
        for owned_game in data["response"]["games"]:
            if owned_game["playtime_forever"] > 0:
                self.game_list[owned_game["appid"]] = Game(owned_game["name"])

        self.schema_downloaded_max = len(self.game_list)
        self.progress_dialog.setLabelText("Download games schemas")
        self.progress_dialog.setMaximum(self.schema_downloaded_max)
        app_ids = list(self.game_list.keys())
        self.steam_api.get_game_schemas(app_ids, self.handle_game_schemas_response, self.handle_game_schemas_error)

    def handle_owned_games_error(self, error: QtNetwork.QNetworkReply.NetworkError, other: None) -> None:
        """Show an error message.

        Args:
            error (QtNetwork.QNetworkReply.NetworkError): Network error
            other (None): Unused
        """
        self.progress_dialog.close()
        QtWidgets.QMessageBox.critical(self, "Error", "Failed to load owned games!\n"
                                       "(You can try to refresh the game list or restart the application)")
        logging.error("Failed to load owned games")

    @staticmethod
    def is_game_schema_valid(schema: Any) -> bool:
        """Check if a game schema is valid.

        Args:
            schema (Any): JSON data from the Steam API response

        Returns:
            bool: True if the schema is valid, False otherwise
        """
        return (
            "game" in schema
            and "availableGameStats" in schema["game"]
            and "achievements" in schema["game"]["availableGameStats"]
        )

    def add_achievements(self, app_id: int, data: Any) -> None:
        """Add achievements to the game schema.

        Args:
            app_id (int): Game app_id
            data (Any): JSON data from the Steam API response
        """
        schema = self.game_list[app_id].schema
        for raw_achievement in data["game"]["availableGameStats"]["achievements"]:
            schema[raw_achievement["name"]] = Achievement(
                raw_achievement["displayName"], raw_achievement["icon"])

    def handle_game_schemas_response(self, data: Any, app_id: int) -> None:
        """Process the game schema data.

        Check if the downloading failed.
        Add the achievements to the game schema, if the schema is invalid, remove the game from the game list.
        If all schemas are downloaded, add the games to the game list widget and emit the loaded signal.

        Args:
            data (Any): JSON data from the Steam API response
            app_id (int): Game app_id
        """
        if self.schema_downloaded_count == -1:
            return

        if self.is_game_schema_valid(data):
            self.add_achievements(app_id, data)
        else:
            del self.game_list[app_id]
            logging.info("Invalid schema for app_id %d", app_id)

        self.schema_downloaded_count += 1
        self.progress_dialog.setValue(self.schema_downloaded_count)
        if self.schema_downloaded_count == self.schema_downloaded_max:
            self.add_games()
            self.loaded.emit()
            self.progress_dialog.close()

    def handle_game_schemas_error(self, error: QtNetwork.QNetworkReply.NetworkError, app_id: int) -> None:
        """Stop the schemas downloading and show an error message.

        Args:
            error (QtNetwork.QNetworkReply.NetworkError): Network error
            app_id (int): Game app_id
        """
        if self.schema_downloaded_count == -1:
            return

        self.schema_downloaded_count = -1
        self.progress_dialog.close()
        QtWidgets.QMessageBox.critical(self, "Error", "Failed to load games schemas!\n"
                                       "(You can try to refresh the game list or restart the application)")
        logging.error("Failed to load %d schema", app_id)

    def index_changed(self, index: int) -> None:
        """Emit the selected signal with the selected game app_id.

        Args:
            index (int): Selected game index
        """
        app_id = self.game_combo_box.itemData(index)
        if app_id is None:
            self.selected.emit(-1)
        else:
            self.selected.emit(app_id)

    def refresh_game_list(self) -> None:
        """Clear the game list and reload the owned games."""
        self.game_combo_box.clear()
        self.game_list.clear()
        self.load_owned_games()
