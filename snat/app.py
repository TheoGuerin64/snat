from PyQt6 import QtCore, QtGui, QtWidgets

from . import __version__
from .achievement_list import AchievementList
from .game_list import GameListBar
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
        self.steam_api = SteamApi(self, self.settings)
        self.game_list = self.settings.typedValue("game_list_cache", dict) or {}
        self.init_ui()

        self.game_list_bar.loaded.connect(self.on_games_loaded)
        self.game_list_bar.selected.connect(self.on_game_selected)

        if self.game_list is not None:
            selected_game = self.settings.typedValue("selected_game", int)
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
        self.settings.setValue("game_list_cache", self.game_list)

    def on_game_selected(self, app_id: int) -> None:
        """Save the selected game and load the achievements"""
        self.settings.setValue("selected_game", app_id)
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
        stored_position = self.settings.typedValue("position", QtCore.QPoint)
        if stored_position is not None:
            self.move(stored_position)

        stored_size = self.settings.typedValue("size", QtCore.QSize)
        if stored_size is not None:
            self.resize(stored_size)

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
            self.settings.setValue("position", event.pos())

    def resizeEvent(self, event: QtGui.QResizeEvent | None) -> None:
        """Override the resize event to save the size"""
        super().resizeEvent(event)
        if event is not None:
            self.settings.setValue("size", event.size())
