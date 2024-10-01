from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QLineEdit, QTextEdit, QPushButton, QFileDialog, QComboBox, QMessageBox, QToolButton, QToolTip
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from datetime import datetime
import pandas as pd
from threads import LoadDataThread, AnalyzeDataThread

class PrepareFilesTab(QWidget):
    def __init__(self):
        super().__init__()
        self.data = None  # Data loaded from CSV
        self.sample_dropdown = None  # Dropdown for sample selection
        self.is_loading = False  # To prevent concurrent clicks
        self.genotype_entries = {}  # To store genotype entries for markers
        self.maf_labels = {}  # To store MAF labels for markers
        self.original_genotypes = {}  # To store original genotypes for comparison
        self.modified_genotypes = {}  # To track modified genotypes
        # self.log_file = "genotype_changes_log.txt"  # Log file for genotype changes
        
        # Prepare timestamp for filenames
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Log file with timestamp
        self.log_file = f"genotype_changes_log_{self.timestamp}.txt"
        
        self.markers_of_interest = ["rs312262906", "rs2196051", "rs1495085", "rs2789823", "rs7148809", "rs310644"]  # Markers of interest
        self.init_ui()

    def init_ui(self):
        layout = QGridLayout()

        # Sample label
        self.label_sample = QLabel("Person to be analyzed:")
        layout.addWidget(self.label_sample, 0, 0)

        # Sample dropdown (QComboBox for selecting samples)
        self.sample_dropdown = QComboBox()
        self.sample_dropdown.currentIndexChanged.connect(self.on_sample_changed)
        layout.addWidget(self.sample_dropdown, 0, 1)

        # Load data button
        self.load_button = QPushButton("Load Data")
        self.load_button.clicked.connect(self.on_load_data)
        layout.addWidget(self.load_button, 0, 2)

        # Analyze button
        self.analyze_button = QPushButton("Analyze")
        self.analyze_button.clicked.connect(self.on_analyze_data)
        layout.addWidget(self.analyze_button, 0, 3)

        # Text output for logs and messages
        self.text_output_prepare = QTextEdit()
        self.text_output_prepare.setReadOnly(True)

        # Create editable genotype fields and MAF labels for each marker
        for i, marker in enumerate(self.markers_of_interest):
            marker_label = QLabel(f"Genotype for {marker}:")
            layout.addWidget(marker_label, i + 1, 0, Qt.AlignRight)

            genotype_entry = QLineEdit()
            layout.addWidget(genotype_entry, i + 1, 1)

            # Connect to textChanged and editingFinished signals
            # genotype_entry.textChanged.connect(lambda new_value, marker=marker: self.on_genotype_temp_change(marker, new_value))
            genotype_entry.editingFinished.connect(lambda marker=marker: self.on_genotype_change(marker))  # Detect genotype changes after editing is complete

            maf_label = QLabel(f"MAF: N/A")
            layout.addWidget(maf_label, i + 1, 2)

            # Add the hover info button
            info_button = QToolButton()
            info_button.setText("i")  # Icon (i) for information
            # info_button.setToolTip(f"This is the Major Allele Frequency (MAF) for {marker}.")
            info_button.clicked.connect(lambda _, marker=marker: self.show_info(marker))  # Connect button click
            layout.addWidget(info_button, i + 1, 5)  # Hover info button to the right of the MAF label

            self.genotype_entries[marker] = genotype_entry
            self.maf_labels[marker] = maf_label

                # Button to filter markers by MAF between 65 and 85
        self.filter_maf_button = QPushButton("List Markers with MAF > 65 and < 85")
        self.filter_maf_button.clicked.connect(self.list_markers_by_maf)
        layout.addWidget(self.filter_maf_button, len(self.markers_of_interest) + 1, 0, 1, 6)

        # Save changes button to save modified data to CSV
        self.save_button = QPushButton("Save Changes to CSV")
        self.save_button.clicked.connect(self.save_to_csv)
        layout.addWidget(self.save_button, len(self.markers_of_interest) + 2, 0, 1, 6)

        # Button to create appearance input file
        self.create_file_button = QPushButton("Create Appearance Input File")
        self.create_file_button.clicked.connect(self.create_analysis_input_file)
        layout.addWidget(self.create_file_button, len(self.markers_of_interest) +3, 0, 1, 6)

        # Text output area for logs and messages
        self.text_output_prepare = QTextEdit()
        self.text_output_prepare.setReadOnly(True)

         # Spanning across columns

        # Add the output text area below the genotype fields and span across all columns
        # layout.addWidget(self.text_output_prepare, len(self.markers_of_interest) + 2, 0, 1, 6)

        layout.addWidget(self.text_output_prepare, len(self.markers_of_interest) + 4, 0, 1, 6)



        self.setLayout(layout)

    # def create_appearance_file(self):
    #     """Create input file for appearance analysis."""
    #     if self.data is not None:
    #         # Get the selected sample from the dropdown
    #         sample_name = self.sample_dropdown.currentText()

    #         # Ensure a sample is selected
    #         if not sample_name:
    #             QMessageBox.critical(self, "Error", "Please select a sample before creating the appearance input file.")
    #             return

    #         # Call the function to create the input file
    #         filename = self.create_analysis_input_file(self.data, sample_name)

    #         if filename:
    #             self.display_message(f"Appearance input file created: {filename}")
    #         else:
    #             self.display_message("Failed to create appearance input file.")
    #     else:
    #         QMessageBox.critical(self, "Error", "No data loaded to create appearance input file.")

    def on_sample_changed(self):
        """Triggered when the sample is changed in the dropdown."""
        sample_name = self.sample_dropdown.currentText()
        self.populate_genotype_fields(sample_name)  # Update genotype fields

    def create_analysis_input_file(self, data: pd.DataFrame):
        """Create input file for appearance analysis."""
        header = [
            "sampleid", "rs312262906_A", "rs11547464_A", "rs885479_T", "rs1805008_T", "rs1805005_T", "rs1805006_A", 
            "rs1805007_T", "rs1805009_C", "rs201326893_A", "rs2228479_A", "rs1110400_C", "rs28777_C", "rs16891982_C", 
            "rs12821256_G", "rs4959270_A", "rs12203592_T", "rs1042602_T", "rs1800407_A", "rs2402130_G", "rs12913832_T", 
            "rs2378249_C", "rs12896399_T", "rs1393350_T", "rs683_G", "rs3114908_T", "rs1800414_C", "rs10756819_G", 
            "rs2238289_C", "rs17128291_C", "rs6497292_C", "rs1129038_G", "rs1667394_C", "rs1126809_A", "rs1470608_A", 
            "rs1426654_G", "rs6119471_C", "rs1545397_T", "rs6059655_T", "rs12441727_A", "rs3212355_A", "rs8051733_C"
        ]

        sample_name = self.sample_dropdown.currentText()

        # Create DataFrame for output
        output_data = pd.DataFrame(columns=header)
        output_data.loc[0, 'sampleid'] = sample_name

        transformations = {
        'rs312262906_A': {'C/C': '0', 'CC': '0', 'A/A': '2', 'AA': '2', 'C/A': '1', 'CA': '1', 'A/C': '1', 'AC': '1'},
        'rs11547464_A': {'G/G': '0', 'GG': '0', 'A/A': '2', 'AA': '2', 'G/A': '1', 'GA': '1', 'A/G': '1', 'AG': '1'},
        'rs885479_T': {'G/G': '0', 'GG': '0', 'A/A': '2', 'AA': '2', 'G/A': '1', 'GA': '1', 'A/G': '1', 'AG': '1'},
        'rs1805008_T': {'C/C': '0', 'CC': '0', 'T/T': '2', 'TT': '2', 'C/T': '1', 'CT': '1', 'T/C': '1', 'TC': '1'},
        'rs1805005_T': {'G/G': '0', 'GG': '0', 'T/T': '2', 'TT': '2', 'G/T': '1', 'GT': '1', 'T/G': '1', 'TG': '1'},
        'rs1805006_A': {'C/C': '0', 'CC': '0', 'A/A': '2', 'AA': '2', 'C/A': '1', 'CA': '1', 'A/C': '1', 'AC': '1'},
        'rs1805007_T': {'C/C': '0', 'CC': '0', 'T/T': '2', 'TT': '2', 'C/T': '1', 'CT': '1', 'T/C': '1', 'TC': '1'},
        'rs1805009_C': {'G/G': '0', 'GG': '0', 'C/C': '2', 'CC': '2', 'G/C': '1', 'GC': '1', 'C/G': '1', 'CG': '1'},
        'rs201326893_A': {'C/C': '0', 'CC': '0', 'A/A': '2', 'AA': '2', 'C/A': '1', 'CA': '1', 'A/C': '1', 'AC': '1'},
        'rs2228479_A': {'G/G': '0', 'GG': '0', 'A/A': '2', 'AA': '2', 'G/A': '1', 'GA': '1', 'A/G': '1', 'AG': '1'},
        'rs1110400_C': {'T/T': '0', 'TT': '0', 'C/C': '2', 'CC': '2', 'T/C': '1', 'TC': '1', 'C/T': '1', 'CT': '1'},
        'rs28777_C': {'A/A': '0', 'AA': '0', 'C/C': '2', 'CC': '2', 'A/C': '1', 'AC': '1', 'C/A': '1', 'CA': '1'},
        'rs16891982_C': {'G/G': '0', 'GG': '0', 'C/C': '2', 'CC': '2', 'G/C': '1', 'GC': '1', 'C/G': '1', 'CG': '1'},
        'rs12821256_G': {'T/T': '0', 'TT': '0', 'C/C': '2', 'CC': '2', 'T/C': '1', 'TC': '1', 'C/T': '1', 'CT': '1'},
        'rs4959270_A': {'C/C': '0', 'CC': '0', 'A/A': '2', 'AA': '2', 'C/A': '1', 'CA': '1', 'A/C': '1', 'AC': '1'},
        'rs12203592_T': {'C/C': '0', 'CC': '0', 'T/T': '2', 'TT': '2', 'C/T': '1', 'CT': '1', 'T/C': '1', 'TC': '1'},
        'rs1042602_T': {'C/C': '0', 'CC': '0', 'A/A': '2', 'AA': '2', 'C/A': '1', 'CA': '1', 'A/C': '1', 'AC': '1'},
        'rs1800407_A': {'C/C': '0', 'CC': '0', 'T/T': '2', 'TT': '2', 'C/T': '1', 'CT': '1', 'T/C': '1', 'TC': '1'},
        'rs2402130_G': {'A/A': '0', 'AA': '0', 'G/G': '2', 'GG': '2', 'G/A': '1', 'GA': '1', 'A/G': '1', 'AG': '1'},
        'rs12913832_T': {'G/G': '0', 'GG': '0', 'A/A': '2', 'AA': '2', 'G/A': '1', 'GA': '1', 'A/G': '1', 'AG': '1'},
        'rs2378249_C': {'A/A': '0', 'AA': '0', 'G/G': '2', 'GG': '2', 'A/G': '1', 'AG': '1', 'G/A': '1', 'GA': '1'},
        'rs12896399_T': {'G/G': '0', 'GG': '0', 'T/T': '2', 'TT': '2', 'G/T': '1', 'GT': '1', 'T/G': '1', 'TG': '1'},
        'rs1393350_T': {'G/G': '0', 'GG': '0', 'A/A': '2', 'AA': '2', 'G/A': '1', 'GA': '1', 'A/G': '1', 'AG': '1'},
        'rs683_G': {'A/A': '0', 'AA': '0', 'C/C': '2', 'CC': '2', 'C/A': '1', 'CA': '1', 'A/C': '1', 'AC': '1'},
        'rs3114908_T': {'C/C': '0', 'CC': '0', 'T/T': '2', 'TT': '2', 'C/T': '1', 'CT': '1', 'T/C': '1', 'TC': '1'},
        'rs1800414_C': {'T/T': '0', 'TT': '0', 'C/C': '2', 'CC': '2', 'T/C': '1', 'TC': '1', 'C/T': '1', 'CT': '1'},
        'rs10756819_G': {'A/A': '0', 'AA': '0', 'G/G': '2', 'GG': '2', 'A/G': '1', 'AG': '1', 'G/A': '1', 'GA': '1'},
        'rs2238289_C': {'A/A': '0', 'AA': '0', 'G/G': '2', 'GG': '2', 'A/G': '1', 'AG': '1', 'G/A': '1', 'GA': '1'},
        'rs17128291_C': {'A/A': '0', 'AA': '0', 'G/G': '2', 'GG': '2', 'A/G': '1', 'AG': '1', 'G/A': '1', 'GA': '1'},
        'rs6497292_C': {'A/A': '0', 'AA': '0', 'G/G': '2', 'GG': '2', 'A/G': '1', 'AG': '1', 'G/A': '1', 'GA': '1'},
        'rs1129038_G': {'T/T': '0', 'TT': '0', 'C/C': '2', 'CC': '2', 'T/C': '1', 'TC': '1', 'C/T': '1', 'CT': '1'},
        'rs1667394_C': {'T/T': '0', 'TT': '0', 'C/C': '2', 'CC': '2', 'T/C': '1', 'TC': '1', 'C/T': '1', 'CT': '1'},
        'rs1126809_A': {'G/G': '0', 'GG': '0', 'A/A': '2', 'AA': '2', 'G/A': '1', 'GA': '1', 'A/G': '1', 'AG': '1'},
        'rs1470608_A': {'G/G': '0', 'GG': '0', 'T/T': '2', 'TT': '2', 'G/T': '1', 'GT': '1', 'T/G': '1', 'TG': '1'},
        'rs1426654_G': {'A/A': '0', 'AA': '0', 'G/G': '2', 'GG': '2', 'G/A': '1', 'GA': '1', 'A/G': '1', 'AG': '1'},
        'rs6119471_C': {'C/C': '0', 'CC': '0', 'G/G': '2', 'GG': '2', 'C/G': '1', 'CG': '1', 'G/C': '1', 'GC': '1'},
        'rs1545397_T': {'A/A': '0', 'AA': '0', 'T/T': '2', 'TT': '2', 'A/T': '1', 'AT': '1', 'T/A': '1', 'TA': '1'},
        'rs6059655_T': {'G/G': '0', 'GG': '0', 'A/A': '2', 'AA': '2', 'G/A': '1', 'GA': '1', 'A/G': '1', 'AG': '1'},
        'rs12441727_A': {'G/G': '0', 'GG': '0', 'A/A': '2', 'AA': '2', 'G/A': '1', 'GA': '1', 'A/G': '1', 'AG': '1'},
        'rs3212355_A': {'C/C': '0', 'CC': '0', 'T/T': '2', 'TT': '2', 'C/T': '1', 'CT': '1', 'T/C': '1', 'TC': '1'},
        'rs8051733_C': {'A/A': '0', 'AA': '0', 'G/G': '2', 'GG': '2', 'G/A': '1', 'GA': '1', 'A/G': '1', 'AG': '1'},
    
        # Default transformation for unknown genotypes
        './.': 'NA', 'C': 'NA', 'A': 'NA', 'G': 'NA', 'T': 'NA'
        }

        # Fill in the genotype data
        for column in header[1:]:  # Skip the first 'sampleid' column
            marker = column.split('_')[0]

            # Check if the marker has a modified genotype, else use the original data
            if marker in self.modified_genotypes:
                original_genotype = self.modified_genotypes[marker]

                # Apply the transformation if the marker is in the transformation dictionary
                if column in transformations and original_genotype in transformations[column]:
                    output_data.loc[0, column] = transformations[column][original_genotype]
                else:
                    output_data.loc[0, column] = 'NA'  # Handle missing transformations

            else:
                # Use the original genotype from the data
                row = self.data[self.data['Target ID'] == marker]
                if not row.empty:
                    original_genotype = row.iloc[0]['Genotype']
                    # Apply transformation if needed
                    if column in transformations and original_genotype in transformations[column]:
                        output_data.loc[0, column] = transformations[column][original_genotype]
                    else:
                        output_data.loc[0, column] = 'NA'  # Handle missing transformations
                else:
                    output_data.loc[0, column] = 'NA'

        # # Save to CSV with a timestamp, consistent with the other CSV saving logic
        # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # filename = os.path.join(DATA_DIRECTORY_INPUT, f"{sample_name}_{analysis_type}_input_{timestamp}.csv")
        # output_data.to_csv(filename, index=False)
        
        appearance_file_path = f"{sample_name}_appearance_input_file_{self.timestamp}.csv"
        output_data.to_csv(appearance_file_path, index=False)
        self.display_message(f"Appearance data saved to {appearance_file_path}.")



    def show_info(self, marker):
            """Shows a message box with detailed information for each marker."""
            info_text = {
                "rs312262906": "This is an indel marker and you need to check the genotype yourself in IGV.",
                "rs2196051": "MAF <40 - GG?, 40< MAF <80 - AG, > 80 AA.",
                "rs1495085": "80 < MAF - homozygous.",
                "rs2789823": "80 < MAF - homozygous.",
                "rs7148809": "80 < MAF - homozygous.",
                "rs310644": "C could be lost, don't trust TT."
            }

            message = info_text.get(marker, "No additional information available for this marker.")
            QMessageBox.information(self, f"Information for {marker}", message)


    # def on_genotype_temp_change(self, marker, new_value):
    #     """Handle temporary genotype changes and log live updates in the white area."""
    #     # Update the live change in the white area (if you want to log temporary changes too)
    #     self.display_message(f"Genotype for {marker} is being edited, current value: {new_value}")



    def on_genotype_change(self, marker):
            """Handle genotype change detection when the user finishes editing."""
            new_genotype = self.genotype_entries[marker].text()
            original_genotype = self.original_genotypes.get(marker, new_genotype)  # Fallback to new_genotype if not set

            # Check if there's an actual change (ignore if the genotype hasn't changed)
            if original_genotype != new_genotype:
                # Store the new genotype in the modified_genotypes dictionary
                self.modified_genotypes[marker] = new_genotype

                # Log the change from original to new
                self.display_message(f"Genotype for {marker} changed from {original_genotype} to {new_genotype}.")

                # Log change in the log file
                with open(self.log_file, 'a') as log:
                    log.write(f"Genotype for {marker} changed from {original_genotype} to {new_genotype}.\n")

                # Update the original_genotypes to reflect the current state
                self.original_genotypes[marker] = new_genotype

    def save_to_csv(self):
        """Save modified genotypes to a CSV file."""
        if self.data is not None:
            modified_data = self.data.copy()

            # Get the selected sample from the dropdown
            sample = self.sample_dropdown.currentText()

            # Ensure we update the correct rows based on both 'SampleName' and 'Target ID'
            for marker, genotype in self.modified_genotypes.items():
                # Update the row where both 'SampleName' and 'Target ID' match
                mask = (modified_data['SampleName'] == sample) & (modified_data['Target ID'] == marker)
                modified_data.loc[mask, 'Genotype'] = genotype

            # Save to a CSV file with a timestamp
            modified_file_path = f"modified_input_file_{self.timestamp}.csv"
            modified_data.to_csv(modified_file_path, index=False)
            self.display_message(f"Modified data saved to {modified_file_path}.")
        else:
            QMessageBox.critical(self, "Error", "No data loaded to save.")

    def on_load_data(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Open File", "", "CSV Files (*.csv);;All Files (*)")
        if filepath:
            self.load_thread = LoadDataThread(filepath)
            self.load_thread.data_loaded.connect(self.on_data_loaded)
            self.load_thread.error_occurred.connect(self.on_error)
            self.load_thread.start()

    def on_data_loaded(self, data: pd.DataFrame):
        self.data = data
        self.populate_sample_dropdown()
        self.display_message("Data loaded successfully.")

    def populate_sample_dropdown(self):
        if self.data is not None and 'SampleName' in self.data.columns:
            unique_samples = self.data['SampleName'].unique()
            self.sample_dropdown.clear()
            self.sample_dropdown.addItems(unique_samples)

    def populate_genotype_fields(self, sample_name):
        if self.data is not None:
            sample_filtered = self.data[self.data['SampleName'] == sample_name]

            for marker in self.markers_of_interest:
                row = sample_filtered[sample_filtered['Target ID'] == marker]
                if not row.empty:
                    genotype = row.iloc[0]['Genotype']
                    maf = row.iloc[0]['Maj Allele Freq']

                    # Set the genotype value in the corresponding QLineEdit field
                    self.genotype_entries[marker].setText(genotype)

                    # Store the original genotype for comparison later
                    self.original_genotypes[marker] = genotype

                    # Set the MAF value in the corresponding QLabel field
                    self.maf_labels[marker].setText(f"MAF: {maf:.2f}%")
                else:
                    self.genotype_entries[marker].setText("")
                    self.maf_labels[marker].setText(f"MAF: N/A")

    def on_analyze_data(self):
        if self.is_loading:
            return
        self.is_loading = True

        # Get the selected sample from the dropdown
        sample = self.sample_dropdown.currentText()
        if self.data is not None and sample:
            self.populate_genotype_fields(sample)
            self.analyze_thread = AnalyzeDataThread(self.data, sample, self.genotype_entries)
            # self.analyze_thread.analysis_completed.connect(self.on_analysis_completed)
            self.analyze_thread.error_occurred.connect(self.on_error)
            self.analyze_thread.finished.connect(lambda: setattr(self, 'is_loading', False))
            self.analyze_thread.start()
        else:
            QMessageBox.critical(self, "Error", "Data not loaded or no sample provided.")
            self.is_loading = False

    # def on_analysis_completed(self, result: pd.DataFrame):
    #     self.display_message(f"Analysis Results:\n{result.to_string(index=False)}")

    def list_markers_by_maf(self):
        """List all markers with MAF between 65 and 85 in the white area."""
        if self.data is not None:
            # Get the selected sample from the dropdown
            sample = self.sample_dropdown.currentText()
            sample_filtered = self.data[self.data['SampleName'] == sample]

            # Filter markers with MAF between 65 and 85
            filtered_markers = sample_filtered[
                (sample_filtered['Maj Allele Freq'] > 65) &
                (sample_filtered['Maj Allele Freq'] < 85)
            ]

            if not filtered_markers.empty:
                self.display_message("Markers with MAF between 65 and 85:")
                for _, row in filtered_markers.iterrows():
                    marker = row['Target ID']
                    genotype = row['Genotype']
                    maf = row['Maj Allele Freq']
                    self.display_message(f"Marker: {marker}, Genotype: {genotype}, MAF: {maf:.2f}%")
            else:
                self.display_message("No markers with MAF between 65 and 85.")
        else:
            self.display_message("No data loaded to list markers.")


    def on_error(self, error_msg: str):
        self.display_message(f"Error: {error_msg}")

    def display_message(self, message: str):
        self.text_output_prepare.append(message)
