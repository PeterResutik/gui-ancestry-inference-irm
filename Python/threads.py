from PyQt5.QtCore import QThread, pyqtSignal
import pandas as pd

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