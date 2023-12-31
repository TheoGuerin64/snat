from PyQt6 import QtCore, QtGui, QtWidgets

from . import __version__
from .utils import LinkLabel

GITHUB_REPOSITORY_URL = "https://github.com/TheoGuerin64/snat"
GITHUB_PROFIL_URL = "https://github.com/TheoGuerin64"
CHANGELOG_URL = "https://github.com/TheoGuerin64/snat/blob/main/CHANGELOG.md"
LICENSE_URL = "https://github.com/TheoGuerin64/snat/blob/main/LICENSE"


class AboutDialog(QtWidgets.QDialog):
    """Dialog that display information about the application.

    Args:
        parent (PyQt6.QtWidgets.QWidget): Parent widget
    """

    def __init__(self, parent: QtWidgets.QWidget) -> None:
        super().__init__(parent)
        self.init_ui()

    def init_ui(self) -> None:
        """Configure the window, create widgets and set the layout."""
        self.setWindowTitle("About")
        self.setWindowIcon(QtGui.QIcon("asset:icon.ico"))

        layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(layout)

        top = self.create_top_layout()
        layout.addLayout(top)

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok, self)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

        self.setFixedSize(self.sizeHint())

    def create_top_layout(self) -> QtWidgets.QHBoxLayout:
        """Create the top layout, add logo and form.

        Returns:
            PyQt6.QtWidgets.QHBoxLayout: Top layout
        """
        top_layout = QtWidgets.QHBoxLayout()

        label = QtWidgets.QLabel(self)
        label.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        label.setPixmap(QtGui.QPixmap("asset:icon.ico").scaledToHeight(64))
        top_layout.addWidget(label)

        form = self.create_form()
        top_layout.addLayout(form)

        return top_layout

    def create_form(self) -> QtWidgets.QFormLayout:
        """Create the form layout and add rows.

        Returns:
            PyQt6.QtWidgets.QFormLayout: Form layout
        """
        form = QtWidgets.QFormLayout()
        version_url = f"{CHANGELOG_URL}#{__version__.replace('.', '')}"
        form.addRow("Version", LinkLabel(f"{__version__} (<a href={version_url}>changelog</a>)", self))
        form.addRow("Author", LinkLabel(f"<a href={GITHUB_PROFIL_URL}>Théo Guérin</a>", self))
        form.addRow("License", LinkLabel(f"<a href={LICENSE_URL}>GPLv3</a>", self))
        form.addRow("Github", LinkLabel(f"<a href={GITHUB_REPOSITORY_URL}>Snat</a>", self))
        form.addRow("PyQt6", QtWidgets.QLabel("6.0.3"))
        return form
