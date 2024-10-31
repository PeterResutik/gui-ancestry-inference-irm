import sys
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QTabWidget, QWidget
from prepare_files_tab import PrepareFilesTab
from appearance_tab import AppearanceTab
from ancestry_tab import AncestryTab
from help_tab import HelpTab

class DataAnalyzerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Data Analyzer")
        self.setGeometry(100, 100, 1100, 580)

        self.init_ui()

    def init_ui(self):
        # Create the tab widget
        self.tab_widget = QTabWidget(self)
        
        # Set style for tab text (change color, set font size, and set minimum tab width)
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane { border: 1px solid lightgray; }
            QTabBar::tab { background: lightgray; padding: 10px; font-size: 12px; min-width: 120px; }
            QTabBar::tab:selected { background-color: white; font-weight: bold; }
            QTabBar::tab:hover { background-color: lightblue; }
        """)

        # Add tabs
        self.tab_widget.addTab(PrepareFilesTab(), "Prepare Files")
        # self.tab_widget.addTab(AppearanceTab(), "Appearance")
        # self.tab_widget.addTab(AncestryTab(), "Ancestry")
        self.tab_widget.addTab(HelpTab(), "Help")

        # Set main layout
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)

def main():
    app = QApplication(sys.argv)
    analyzer = DataAnalyzerApp()
    analyzer.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
