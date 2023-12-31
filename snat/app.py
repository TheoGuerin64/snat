from PyQt6 import QtCore, QtGui, QtWidgets

from . import __version__
from .achievement_list import AchievementList
from .game_list import GameList, GameListBar
from .settings import Settings
from .steam_api import SteamApi


class GameDashboard(QtWidgets.QWidget):
    """Widget that displays the game list and the achievement list

    Attributes:
        settings (snat.settings.Settings): Settings instance
        steam_api (snat.steam_api.SteamApi): SteamApi
        game_list (snat.game_list.GameList): Game list

    Args:
        parent (PyQt6.QtWidgets.QWidget): Parent widget
        settings (snat.settings.Settings): Settings instance
    """

    def __init__(self, parent: QtWidgets.QWidget, settings: Settings) -> None:
        super().__init__(parent)
        self.settings = settings
        self.steam_api = SteamApi(self, self.settings.steam_api_key, self.settings.steam_user_id)
        self.game_list: GameList = self.settings.game_list_cache or GameList()
        self.init_ui()

        self.game_list_bar.loaded.connect(self.on_games_loaded)
        self.game_list_bar.selected.connect(self.on_game_selected)

        if self.game_list is not None:
            selected_game = self.settings.selected_game
            if selected_game is not None:
                self.game_list_bar.select_game(selected_game)

    def init_ui(self) -> None:
        """Create widgets and set the layout."""
        layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(layout)

        self.game_list_bar = GameListBar(self.steam_api, self.game_list, self)
        layout.addWidget(self.game_list_bar)

        self.achievement_list = AchievementList(self, self.steam_api, self.game_list)
        layout.addWidget(self.achievement_list)

    def on_games_loaded(self) -> None:
        """Cache the game list"""
        self.settings.game_list_cache = self.game_list

    def on_game_selected(self, app_id: int) -> None:
        """Cache the selected game and load the achievements"""
        self.settings.selected_game = app_id
        self.achievement_list.load_user_achievements(app_id)


class App(QtWidgets.QMainWindow):
    """The main application

    Attributes:
        settings (snat.settings.Settings): Settings instance

    Args:
        parent (PyQt6.QtWidgets.QWidget): Parent widget
    """

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.configure()
        self.settings = Settings(self)
        self.restore()
        self.init_ui()
        self.setCentralWidget(GameDashboard(self, self.settings))

    def configure(self) -> None:
        """Configure the application informations"""
        QtCore.QCoreApplication.setApplicationName("Snat")
        QtCore.QCoreApplication.setOrganizationName("Theo Guerin")
        QtCore.QCoreApplication.setApplicationVersion(__version__)

    def restore(self) -> None:
        """Restore the application state"""
        if self.settings.position is not None:
            self.move(self.settings.position)
        if self.settings.size is not None:
            self.resize(self.settings.size)

    def init_ui(self) -> None:
        """Set the window icon and create the menu bar"""
        self.setWindowIcon(QtGui.QIcon("asset:icon.ico"))
        self.init_menu_bar()

    def init_menu_bar(self) -> None:
        """Create the menu bar and its menus"""
        menu_bar = self.menuBar()
        if menu_bar is None:
            raise RuntimeError("No menu bar")

        file_menu = menu_bar.addMenu("&File")
        if file_menu is None:
            raise RuntimeError("No file menu")
        file_menu.addAction("&Exit", "Ctrl+Q", self.close)

        help_menu = menu_bar.addMenu("&Help")
        if help_menu is None:
            raise RuntimeError("No help menu")
        help_menu.addAction("&About", self.open_about)

    def open_about(self) -> None:
        from .about import AboutDialog
        AboutDialog(self).exec()

    def moveEvent(self, event: QtGui.QMoveEvent | None) -> None:
        """Override the move event to save the position"""
        super().moveEvent(event)
        if event is not None:
            self.settings.position = event.pos()

    def resizeEvent(self, event: QtGui.QResizeEvent | None) -> None:
        """Override the resize event to save the size"""
        super().resizeEvent(event)
        if event is not None:
            self.settings.size = event.size()
