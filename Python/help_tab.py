from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit

class HelpTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Help text
        help_text = QTextEdit()
        help_text.setPlainText(
            "Help Guide\n\n"
            "1. Go to the 'Prepare Files' tab to load your data and prepare files for analysis.\n"
            "2. Use the 'Appearance' and 'Ancestry' tabs for corresponding analyses (coming soon).\n"
            "3. If you need further assistance, contact support."
        )
        help_text.setReadOnly(True)
        layout.addWidget(help_text)

        self.setLayout(layout)
