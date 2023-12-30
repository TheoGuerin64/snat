from PyQt6 import QtCore, QtGui, QtWidgets

from . import __version__
from .about import AboutDialog
from .achievement_list import AchievementList
from .game_list import GameList, GameListBar
from .settings import Settings
from .steam_api import SteamApi


class MainWidget(QtWidgets.QWidget):
    """The main widget of the application

    Args:
        parent (QtWidgets.QWidget): The parent widget
        settings (Settings): The Settings instance to use
    """

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
        """Initialize the UI"""
        layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(layout)

        self.game_list_bar = GameListBar(self, self.steam_api, self.game_list)
        layout.addWidget(self.game_list_bar)

        self.achievement_list = AchievementList(self, self.steam_api, self.game_list)
        layout.addWidget(self.achievement_list)

    def on_games_loaded(self) -> None:
        """Called when the game list has been loaded"""
        self.settings.game_list_cache = self.game_list

    def on_game_selected(self, app_id: int) -> None:
        """Called when a game has been selected"""
        self.settings.selected_game = app_id
        self.achievement_list.load_achievements(app_id)


class App(QtWidgets.QMainWindow):
    """The main application window"""
    def __init__(self) -> None:
        super().__init__()
        self.configure()
        self.settings = Settings(self)
        self.restore()
        self.init_ui()

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
        """Initialize the UI"""
        self.setWindowIcon(QtGui.QIcon("asset:icon.ico"))
        self.init_menu_bar()
        self.setCentralWidget(MainWidget(self, self.settings))

    def init_menu_bar(self) -> None:
        """Initialize the menu bar"""
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
        help_menu.addAction("&About", lambda: AboutDialog(self).exec())

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
