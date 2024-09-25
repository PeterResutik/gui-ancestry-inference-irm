import sys
import os
import pandas as pd
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, QTextEdit, QPushButton, QGridLayout, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

# Directory configurations
DATA_DIRECTORY = "path_to_your_data_directory"
DATA_DIRECTORY_INPUT = "path_to_your_input_directory"

class LoadDataThread(QThread):
    data_loaded = pyqtSignal(pd.DataFrame)
    error_occurred = pyqtSignal(str)

    def __init__(self, filepath):
        super().__init__()
        self.filepath = filepath

    def run(self):
        try:
            data = pd.read_csv(self.filepath)
            self.data_loaded.emit(data)
        except Exception as e:
            self.error_occurred.emit(str(e))

class AnalyzeDataThread(QThread):
    analysis_completed = pyqtSignal(pd.DataFrame)
    error_occurred = pyqtSignal(str)

    def __init__(self, data, sample, genotype_entries):
        super().__init__()
        self.data = data
        self.sample = sample
        self.genotype_entries = genotype_entries

    def run(self):
        try:
            for marker, entry in self.genotype_entries.items():
                self.data.loc[self.data['Target ID'] == marker, 'Genotype'] = entry.text()

            markers = self.genotype_entries.keys()
            sample_filtered = self.data[
                (self.data['Target ID'].isin(markers)) &
                (self.data['SampleName'] == self.sample)
            ]
            result = sample_filtered[['Target ID', 'Genotype', 'Maj Allele Freq']]
            self.analysis_completed.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))

class DataAnalyzerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Data Analyzer")
        self.setGeometry(100, 100, 1100, 580)
        
        self.is_loading = False  # Prevent concurrent clicks
        self.genotype_entries = {}
        self.maf_labels = {}
        
        self.data = None

        self.init_ui()

    def init_ui(self):
        layout = QGridLayout()

        # Load button
        self.load_button = QPushButton("Load Data")
        self.load_button.clicked.connect(self.on_load_data)
        layout.addWidget(self.load_button, 0, 0)

        # Sample label and entry
        self.label_sample = QLabel("Person to be analyzed:")
        layout.addWidget(self.label_sample, 0, 1, Qt.AlignRight)

        self.sample_entry = QLineEdit()
        layout.addWidget(self.sample_entry, 0, 2)

        # Analyze button
        self.analyze_button = QPushButton("Analyze")
        self.analyze_button.clicked.connect(self.on_analyze_data)
        layout.addWidget(self.analyze_button, 5, 0)

        # Appearance and Ancestry buttons
        self.appearance_button = QPushButton("Create Appearance File")
        self.appearance_button.clicked.connect(lambda: self.on_create_file('appearance'))
        layout.addWidget(self.appearance_button, 5, 1, Qt.AlignRight)

        self.ancestry_button = QPushButton("Create Ancestry File")
        self.ancestry_button.clicked.connect(lambda: self.on_create_file('ancestry'))
        layout.addWidget(self.ancestry_button, 5, 2)

        # Text output
        self.text_output = QTextEdit()
        self.text_output.setReadOnly(True)
        layout.addWidget(self.text_output, 6, 0, 1, 3)

        self.setLayout(layout)

    def on_load_data(self):
        if self.is_loading:
            return
        self.is_loading = True

        filepath, _ = QFileDialog.getOpenFileName(self, "Open File", "", "CSV Files (*.csv);;All Files (*)")
        if filepath:
            self.load_thread = LoadDataThread(filepath)
            self.load_thread.data_loaded.connect(self.on_data_loaded)
            self.load_thread.error_occurred.connect(self.on_error)
            self.load_thread.finished.connect(lambda: setattr(self, 'is_loading', False))
            self.load_thread.start()

    def on_data_loaded(self, data):
        self.data = data
        self.display_message("Data loaded successfully.")

    def populate_markers(self, sample_name):
        markers_of_interest = ["rs16830500", "rs10497191", "rs7568054", "rs2302013"]

        sample_filtered = self.data[
            (self.data['Target ID'].isin(markers_of_interest)) &
            (self.data['SampleName'] == sample_name)
        ]

        for i, marker in enumerate(markers_of_interest):
            row = sample_filtered[sample_filtered['Target ID'] == marker]
            if not row.empty:
                genotype = row.iloc[0]['Genotype']
                maf = row.iloc[0]['Maj Allele Freq']

                marker_label = QLabel(f"Marker {i+1} ({marker}):")
                self.layout().addWidget(marker_label, i+1, 0, Qt.AlignRight)

                genotype_entry = QLineEdit()
                genotype_entry.setText(genotype)
                self.layout().addWidget(genotype_entry, i+1, 1)
                self.genotype_entries[marker] = genotype_entry

                maf_label = QLabel(f"MAF: {maf}%")
                self.layout().addWidget(maf_label, i+1, 2)
                self.maf_labels[marker] = maf_label
            else:
                self.display_message(f"Marker {marker} not found in the data.")

    def on_analyze_data(self):
        if self.is_loading:
            return
        self.is_loading = True

        sample = self.sample_entry.text()
        if self.data is not None and sample:
            self.populate_markers(sample)
            self.analyze_thread = AnalyzeDataThread(self.data, sample, self.genotype_entries)
            self.analyze_thread.analysis_completed.connect(self.on_analysis_completed)
            self.analyze_thread.error_occurred.connect(self.on_error)
            self.analyze_thread.finished.connect(lambda: setattr(self, 'is_loading', False))
            self.analyze_thread.start()
        else:
            QMessageBox.critical(self, "Error", "Data not loaded or no sample provided.")
            self.is_loading = False

    def on_analysis_completed(self, result):
        self.display_message(f"Analysis Results:\n{result.to_string(index=False)}")

    def on_create_file(self, analysis_type):
        if self.is_loading:
            return
        self.is_loading = True

        sample = self.sample_entry.text()
        if self.data is not None and sample:
            filename = self.create_analysis_input_file(self.data, sample, analysis_type)
            self.display_message(f"{analysis_type.capitalize()} file created: {filename}")
        else:
            QMessageBox.critical(self, "Error", "Data not loaded or no sample provided.")
        self.is_loading = False

    def create_analysis_input_file(self, data, sample_name, analysis_type):
        header = ["sampleid", "rs312262906_A", "rs11547464_A", "rs885479_T", "rs1805008_T", "rs1805005_T", "rs1805006_A",
                  "rs1805007_T", "rs1805009_C", "rs201326893_A", "rs2228479_A", "rs1110400_C", "rs28777_C",
                  "rs16891982_C", "rs12821256_G", "rs4959270_A", "rs12203592_T", "rs1042602_T", "rs1800407_A",
                  "rs2402130_G", "rs12913832_T", "rs2378249_C", "rs12896399_T", "rs1393350_T", "rs683_G", "rs3114908_T",
                  "rs1800414_C", "rs10756819_G", "rs2238289_C", "rs17128291_C", "rs6497292_C", "rs1129038_G",
                  "rs1667394_C", "rs1126809_A", "rs1470608_A", "rs1426654_G", "rs6119471_C", "rs1545397_T",
                  "rs6059655_T", "rs12441727_A", "rs3212355_A", "rs8051733_C"]

        sample_data = data[data['SampleName'] == sample_name]
        output_data = pd.DataFrame(columns=header)
        output_data.loc[0, 'sampleid'] = sample_name

        for column in header[1:]:
            marker = column.split('_')[0]
            row = sample_data[sample_data['Target ID'] == marker]
            output_data.loc[0, column] = row.iloc[0]['Genotype'] if not row.empty else 'NA'

        filename = os.path.join(DATA_DIRECTORY_INPUT, f"{sample_name}_{analysis_type}_input.csv")
        output_data.to_csv(filename, index=False)

        return filename

    def display_message(self, message):
        self.text_output.append(message)

    def on_error(self, message):
        QMessageBox.critical(self, "Error", message)
        self.is_loading = False

def main():
    app = QApplication(sys.argv)
    analyzer = DataAnalyzerApp()
    analyzer.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
