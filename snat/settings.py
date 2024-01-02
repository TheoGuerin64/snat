import logging
from typing import TYPE_CHECKING, Callable, TypeVar, cast, overload

from PyQt6 import QtCore, QtWidgets

if TYPE_CHECKING:
    from .input_dialog import AbstractInputDialog

T = TypeVar("T")


class Settings(QtCore.QSettings):
    """Provides access to the application settings

    Settings:
        steam_api_key (str): Steam API key
        steam_user_id (str): Steam user ID
        game_list_cache (str): Cached game list
        selected_game (int): Selected game
        position (QtCore.QPoint): Window position
        size (QtCore.QSize): Window size

    Raises:
        RuntimeError: If a setting is not found and the user rejects the dialog

    Args:
        parent (QtWidgets.QWidget): Parent widget
    """

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.define_if_not_exists("steam_api_key", self.steam_api_key_dialog_factory)
        self.define_if_not_exists("steam_user_id", self.steam_user_id_dialog_factory)

    def define_if_not_exists(self, key: str, dialog_factory: Callable[[], "AbstractInputDialog"]) -> None:
        """ Shows the dialog and sets the value if it is not already set

        Raises:
            RuntimeError: If the dialog is rejected

        Args:
            key (str): Key to check
            dialog (AbstractRequestInputDialog): Dialog to show
        """
        if not self.contains(key):
            logging.info(f"Setting {key} not found, prompting user")
            dialog = dialog_factory()
            dialog.exec()
            if dialog.result() == QtWidgets.QDialog.DialogCode.Accepted:
                self.setValue(key, dialog.input.text())
            else:
                raise RuntimeError(f"No {key} provided")

    def steam_api_key_dialog_factory(self) -> "AbstractInputDialog":
        """Create the Steam API key dialog

        Returns:
            AbstractInputDialog: Steam API key dialog
        """
        from .input_dialog import SteamAPIKeyDialog
        return SteamAPIKeyDialog(self)

    def steam_user_id_dialog_factory(self) -> "AbstractInputDialog":
        """Create the Steam user ID dialog

        Returns:
            AbstractInputDialog: Steam user ID dialog
        """
        from .input_dialog import SteamUserIdDialog
        return SteamUserIdDialog(self)

    @overload
    def typedValue(self, key: str, expected_type: type[T], default_value: T) -> T:
        ...

    @overload
    def typedValue(self, key: str, expected_type: type[T], default_value: None = None) -> T | None:
        ...

    def typedValue(self, key: str, expected_type: type[T], default_value: T | None = None) -> T | None:
        """Loads the value from the settings and checks its type with a default value

        Args:
            key (str): Key to load
            expected_type (type[T]): Expected type
            default_value (T): Default value

        Returns:
            T: Value or default value if the key is not set
        """
        value = self.value(key, type=expected_type)
        if value is None:
            return default_value
        return cast(T, value)
