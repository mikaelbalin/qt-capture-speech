from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QSplitter,
    QMenuBar,
    QStatusBar,
    QAction,
    QMessageBox,
)
from PyQt5.QtCore import Qt, QTimer
import logging

from ..core.interfaces import ConfigManagerInterface
from ..core.container import DIContainer
from .camera_widget import CameraWidget
from .speech_widget import SpeechWidget


class MainWindow(QMainWindow):
    """Main application window with proper dependency injection."""

    def __init__(self, container: DIContainer, config: ConfigManagerInterface):
        super().__init__()
        self.container = container
        self.config = config
        self.logger = logging.getLogger(__name__)

        self.camera_widget = None
        self.speech_widget = None

        self.setup_ui()
        self.setup_widgets()
        self.setup_menu()
        self.setup_status_bar()

        # Cleanup timer
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self.periodic_cleanup)
        self.cleanup_timer.start(30000)  # Every 30 seconds

    def setup_ui(self):
        """Setup main window UI."""
        # Window properties
        title = self.config.get("gui.window.title", "Camera & Speech Recognition")
        width = self.config.get("gui.window.width", 800)
        height = self.config.get("gui.window.height", 600)

        self.setWindowTitle(title)
        self.setGeometry(100, 100, width, height)

        # Central widget with splitter
        central_widget = QWidget()
        layout = QHBoxLayout()

        self.splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(self.splitter)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def setup_widgets(self):
        """Setup child widgets with dependency injection."""
        try:
            # Get services from container
            camera_service = self.container.get("CameraServiceInterface")
            speech_service = self.container.get("SpeechServiceInterface")
            file_manager = self.container.get("FileManagerInterface")

            # Create widgets
            self.camera_widget = CameraWidget(camera_service, file_manager)
            self.speech_widget = SpeechWidget(speech_service, file_manager)

            # Add to splitter
            self.splitter.addWidget(self.camera_widget)
            self.splitter.addWidget(self.speech_widget)

            # Set equal sizes
            self.splitter.setSizes([400, 400])

        except Exception as e:
            self.logger.error(f"Error setting up widgets: {str(e)}")
            QMessageBox.critical(
                self, "Initialization Error", f"Failed to initialize widgets: {str(e)}"
            )

    def setup_menu(self):
        """Setup application menu."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu("View")

        reset_layout_action = QAction("Reset Layout", self)
        reset_layout_action.triggered.connect(self.reset_layout)
        view_menu.addAction(reset_layout_action)

        # Help menu
        help_menu = menubar.addMenu("Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_status_bar(self):
        """Setup status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def reset_layout(self):
        """Reset window layout to default."""
        if self.splitter:
            self.splitter.setSizes([400, 400])

    def show_about(self):
        """Show about dialog."""
        app_name = self.config.get("app.name", "Qt Camera Speech Recognition")
        version = self.config.get("app.version", "2.0.0")

        QMessageBox.about(
            self,
            "About",
            f"{app_name}\nVersion: {version}\n\n"
            "A Qt application for camera capture and speech recognition.",
        )

    def periodic_cleanup(self):
        """Periodic cleanup to free resources."""
        try:
            # This could include garbage collection or resource monitoring
            pass
        except Exception as e:
            self.logger.error(f"Error during periodic cleanup: {str(e)}")

    def closeEvent(self, event):
        """Handle window close event."""
        try:
            self.logger.info("Application closing...")

            # Cleanup widgets
            if self.camera_widget:
                self.camera_widget.cleanup()

            if self.speech_widget:
                self.speech_widget.cleanup()

            # Stop cleanup timer
            if self.cleanup_timer.isActive():
                self.cleanup_timer.stop()

            # Cleanup container
            self.container.clear()

            event.accept()

        except Exception as e:
            self.logger.error(f"Error during application shutdown: {str(e)}")
            event.accept()  # Accept anyway to prevent hanging
