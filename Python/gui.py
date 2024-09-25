import customtkinter as ctk
from tkinter import filedialog, messagebox
from concurrent.futures import ThreadPoolExecutor
import queue
import os
import pandas as pd

# Directory configurations
DATA_DIRECTORY = "path_to_your_data_directory"
DATA_DIRECTORY_INPUT = "path_to_your_input_directory"

# Appearance and theme settings
ctk.set_default_color_theme("blue")

class DataAnalyzerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Data Analyzer")
        self.geometry("1100x580")
        self.resizable(False, False)  # Prevent window resizing

        # Configure grid layout (4x4)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_columnconfigure(3, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=1)

        self.queue = queue.Queue()
        self.executor = ThreadPoolExecutor(max_workers=4)  # Adjust based on your need
        self.create_widgets()
        self.setup_layout()
        self.process_queue()

        self.is_loading = False  # Prevent concurrent clicks

    def create_widgets(self):
        self.load_button = ctk.CTkButton(self, text="Load Data", command=self.on_load_data)

        self.label_sample = ctk.CTkLabel(self, text="Person to be analyzed:")
        self.sample_entry = ctk.CTkEntry(self, width=200)
        
        self.analyze_button = ctk.CTkButton(self, text="Analyze", command=self.on_analyze_data)
        self.appearance_button = ctk.CTkButton(self, text="Create Appearance File", command=lambda: self.on_create_file('appearance'))
        self.ancestry_button = ctk.CTkButton(self, text="Create Ancestry File", command=lambda: self.on_create_file('ancestry'))

        # Placeholder for genotype entries and MAF labels
        self.genotype_entries = {}
        self.maf_labels = {}

        self.text_output = ctk.CTkTextbox(self, height=200, width=600)
        self.text_output.configure(state="disabled")

    def setup_layout(self):
        # Load button
        self.load_button.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        # Sample label and entry
        self.label_sample.grid(row=0, column=1, padx=10, pady=10, sticky="e")
        self.sample_entry.grid(row=0, column=2, padx=10, pady=10, sticky="w")

        # Adjust row spacing (use grid_rowconfigure)
        for row in range(1, 5):  # Rows corresponding to the markers
            self.grid_rowconfigure(row, weight=1)

        # Analyze, appearance, and ancestry buttons
        self.analyze_button.grid(row=5, column=0, padx=10, pady=10, sticky="w")
        self.appearance_button.grid(row=5, column=1, padx=10, pady=10, sticky="e")
        self.ancestry_button.grid(row=5, column=2, padx=10, pady=10, sticky="w")

        # Text output at the bottom, spanning across three columns
        self.text_output.grid(row=6, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

    def on_load_data(self):
        if not self.is_loading:
            self.is_loading = True
            self.executor.submit(self.load_data_thread)

    def load_data_thread(self):
        try:
            filepath = filedialog.askopenfilename()
            if filepath:
                data = self.load_data(filepath)
                self.after(0, self.on_data_loaded, data)
        except Exception as e:
            self.after(0, lambda: self.display_message(f"Error: {str(e)}"))
        finally:
            self.after(0, lambda: setattr(self, 'is_loading', False))

    def on_data_loaded(self, data):
        self.data = data
        self.display_message("Data loaded successfully.")
        # Optionally populate markers here or wait for analysis

    def load_data(self, filename):
        """Load data from a file."""
        try:
            data = pd.read_csv(filename)
            return data
        except Exception as e:
            raise Exception(f"Failed to load data: {str(e)}")

    def populate_markers(self, sample_name):
        """Extract markers, genotypes, and MAF for the specific markers and populate the UI."""
        markers_of_interest = ["rs16830500", "rs10497191", "rs7568054", "rs2302013"]

        # Filter the data to include only the markers of interest
        marker_filtered = self.data[self.data['Target ID'].isin(markers_of_interest)]
        sample_filtered = marker_filtered[marker_filtered['SampleName'] == sample_name]

        for i, marker in enumerate(markers_of_interest):
            if marker in sample_filtered['Target ID'].values:
                row = sample_filtered[sample_filtered['Target ID'] == marker].iloc[0]

                genotype = row['Genotype']
                maf = row['Maj Allele Freq']

                # Create and place labels and entry fields in the UI
                marker_label = ctk.CTkLabel(self, text=f"Marker {i+1} ({marker}):")
                marker_label.grid(row=i+1, column=0, padx=10, pady=2, sticky="e")
                
                genotype_entry = ctk.CTkEntry(self, width=100)
                genotype_entry.insert(0, genotype)  # Default genotype from data
                genotype_entry.grid(row=i+1, column=1, padx=10, pady=2, sticky="w")
                self.genotype_entries[marker] = genotype_entry
                
                maf_label = ctk.CTkLabel(self, text=f"MAF: {maf}%")
                maf_label.grid(row=i+1, column=2, padx=10, pady=2, sticky="w")
                self.maf_labels[marker] = maf_label
            else:
                self.display_message(f"Marker {marker} not found in the data.")

    def on_analyze_data(self):
        if not self.is_loading:
            self.is_loading = True
            sample = self.sample_entry.get()
            self.populate_markers(sample)
            if hasattr(self, 'data') and sample:
                self.executor.submit(self.analyze_data_thread, sample)
            else:
                messagebox.showerror("Error", "Data not loaded or no sample provided.")
                self.is_loading = False

    def analyze_data_thread(self, sample):
        try:
            # Overwrite genotype values from the UI before analysis
            for marker, entry in self.genotype_entries.items():
                self.data.loc[self.data['Target ID'] == marker, 'Genotype'] = entry.get()
            
            analysis_result = self.analyze_data(self.data, sample)
            self.after(0, lambda: self.display_message(f"Analysis Results for {sample}:\n{analysis_result.to_string(index=False)}"))
        except Exception as e:
            self.after(0, lambda: self.display_message(f"Error: {str(e)}"))
        finally:
            self.after(0, lambda: setattr(self, 'is_loading', False))

    def analyze_data(self, data, sample_name):
        """Analyze data to extract genotypes and major allele frequencies for specific markers and a given sample."""
        markers = self.genotype_entries.keys()  # Use the markers present in the UI
        try:
            # Filter data for the specific markers and sample name
            marker_filtered = data[data['Target ID'].isin(markers)]
            sample_filtered = marker_filtered[marker_filtered['SampleName'] == sample_name]
            
            # Selecting necessary columns if they exist
            if 'Genotype' in data.columns and 'Maj Allele Freq' in data.columns:
                result = sample_filtered[['Target ID', 'Genotype', 'Maj Allele Freq']]
            else:
                raise Exception("Required columns are missing in the data.")
            
            return result
        except Exception as e:
            raise Exception(f"Failed to analyze data: {str(e)}")

    def on_create_file(self, analysis_type):
        if not self.is_loading:
            self.is_loading = True
            sample = self.sample_entry.get()
            if hasattr(self, 'data') and sample:
                self.executor.submit(self.create_file_thread, sample, analysis_type)
            else:
                messagebox.showerror("Error", "Data not loaded or no sample provided.")
                self.is_loading = False

    def create_file_thread(self, sample, analysis_type):
        try:
            filename = self.create_analysis_input_file(self.data, sample, analysis_type)
            self.after(0, lambda: self.display_message(f"{analysis_type.capitalize()} file created: {filename}"))
        except Exception as e:
            self.after(0, lambda: self.display_message(f"Error: {str(e)}"))
        finally:
            self.after(0, lambda: setattr(self, 'is_loading', False))

    def create_analysis_input_file(self, data, sample_name, analysis_type):
        """Create input file for specific analysis type."""
        # Define the header as specified
        header = ["sampleid", "rs312262906_A", "rs11547464_A", "rs885479_T", "rs1805008_T", "rs1805005_T", "rs1805006_A", "rs1805007_T", "rs1805009_C", "rs201326893_A", "rs2228479_A", "rs1110400_C", "rs28777_C", "rs16891982_C", "rs12821256_G", "rs4959270_A", "rs12203592_T", "rs1042602_T", "rs1800407_A", "rs2402130_G", "rs12913832_T", "rs2378249_C", "rs12896399_T", "rs1393350_T", "rs683_G", "rs3114908_T", "rs1800414_C", "rs10756819_G", "rs2238289_C", "rs17128291_C", "rs6497292_C", "rs1129038_G", "rs1667394_C", "rs1126809_A", "rs1470608_A", "rs1426654_G", "rs6119471_C", "rs1545397_T", "rs6059655_T", "rs12441727_A", "rs3212355_A", "rs8051733_C"]  # This list should be completed based on your specific needs

        # Filter data for the specific sample
        sample_data = data[data['SampleName'] == sample_name]

        # Create DataFrame for output
        output_data = pd.DataFrame(columns=header)
        output_data.loc[0, 'sampleid'] = sample_name

        # Fill in the genotype data
        for column in header[1:]:  # Skip the first 'sampleid' column
            marker = column.split('_')[0]
            # Find the row in the sample_data where 'Target ID' matches the marker
            row = sample_data[sample_data['Target ID'] == marker]
            if not row.empty:
                output_data.loc[0, column] = row.iloc[0]['Genotype']  # Get genotype from the first matching row
            else:
                output_data.loc[0, column] = 'NA'  # Or some default value if the marker is not found

        # Save to CSV
        filename = os.path.join(DATA_DIRECTORY_INPUT, f"{sample_name}_{analysis_type}_input.csv")
        output_data.to_csv(filename, index=False)

        return filename

    def display_message(self, message):
        def update_text():
            self.text_output.configure(state="normal")
            self.text_output.insert("end", message + "\n")
            self.text_output.configure(state="disabled")
        self.after(50, update_text)  # Schedule update to run after 50ms

    def process_queue(self):
        try:
            result = self.queue.get_nowait()
            self.display_message(result)
        except queue.Empty:
            pass
        finally:
            self.after(100, self.process_queue)  # Check queue every 100 ms

def main():
    app = DataAnalyzerApp()
    app.mainloop()

if __name__ == "__main__":
    main()
