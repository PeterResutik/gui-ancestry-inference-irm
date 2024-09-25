import pandas as pd
from config import DATA_DIRECTORY, DATA_DIRECTORY_INPUT
import os

def load_data(filename):
    """Load data from a file."""
    full_path = f"{filename}"
    try:
        data = pd.read_csv(full_path)
        return data
    except Exception as e:
        raise Exception(f"Failed to load data: {str(e)}")

def analyze_data(data, sample_name):
    """Analyze data to extract genotypes and major allele frequencies for specific markers and a given sample."""
    markers = ['rs16830500', 'rs10497191', 'rs7568054', 'rs2302013']
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

# def create_analysis_input_file(data, sample_name, analysis_type):
#     """Create input file for specific analysis type."""
#     # Define the header as specified
#     header = ["sampleid", "rs312262906_A", "rs11547464_A", "rs885479_T", "rs1805008_T", "rs1805005_T", "rs1805006_A", "rs1805007_T", "rs1805009_C", "rs201326893_A", "rs2228479_A", "rs1110400_C", "rs28777_C", "rs16891982_C", "rs12821256_G", "rs4959270_A", "rs12203592_T", "rs1042602_T", "rs1800407_A", "rs2402130_G", "rs12913832_T", "rs2378249_C", "rs12896399_T", "rs1393350_T", "rs683_G", "rs3114908_T", "rs1800414_C", "rs10756819_G", "rs2238289_C", "rs17128291_C", "rs6497292_C", "rs1129038_G", "rs1667394_C", "rs1126809_A", "rs1470608_A", "rs1426654_G", "rs6119471_C", "rs1545397_T", "rs6059655_T", "rs12441727_A", "rs3212355_A", "rs8051733_C"]  # This list should be completed based on your specific needs

#     # Filter data for the specific sample
#     sample_data = data[data['SampleName'] == sample_name]

#     # Create DataFrame for output
#     output_data = pd.DataFrame(columns=header)
#     output_data.loc[0, 'sampleid'] = sample_name

#     # Fill in the genotype data
#     for column in header[1:]:  # Skip the first 'sampleid' column
#         marker = column.split('_')[0]
#         # Find the row in the sample_data where 'Target ID' matches the marker
#         row = sample_data[sample_data['Target ID'] == marker]
#         if not row.empty:
#             output_data.loc[0, column] = row.iloc[0]['Genotype']  # Get genotype from the first matching row
#         else:
#             output_data.loc[0, column] = 'NA'  # Or some default value if the marker is not found

#     # Save to CSV
#     filename = os.path.join(DATA_DIRECTORY_INPUT, f"{sample_name}_{analysis_type}_input.csv")
#     output_data.to_csv(filename, index=False)

#     return filename