from PySide6.QtWidgets import QFileDialog, QMessageBox
from pyNastran.bdf.bdf import BDF
import os

class BDFData:
    def __init__(self):
        self.nodes = {}
        self.elements = {
            'CQUAD4': [],
            'CTRIA3': [],
            'CBAR': [],
            'CBEAM': []
        }
        self.properties = {}
        self.is_loaded=False

# Global variable to store current BDF data
bdf_data = BDFData()

"""
def browse_file(parent, file_type):
    #Handle file browsing for BDF and OP2 files
    file_filter = "BDF files (*.bdf);;All files (*.*)" if file_type == "BDF" else "OP2 files (*.op2);;All files (*.*)"
    filename, _ = QFileDialog.getOpenFileName(parent, f"Select {file_type} File", "", file_filter)
    return filename
"""

def browse_file(parent, file_type):
    """Open file browser dialog and return selected file"""
    from PySide6.QtWidgets import QFileDialog
    
    file_filter = "BDF files (*.bdf);;All files (*.*)" if file_type == "BDF" else "OP2 files (*.op2);;All files (*.*)"
    filename, _ = QFileDialog.getOpenFileName(parent, f"Select {file_type} File", "", file_filter)
    return filename

'''
def load_bdf_file(filename):
    """Load BDF file and store data in current_bdf_data"""
    try:
        model = BDF()
        model.read_bdf(filename)
        
        # Extract nodes
        current_bdf_data.nodes = {nid: coords for nid, coords in model.nodes.items()}
        print(current_bdf_data.nodes)
        
        # Extract elements by type
        for eid, elem in model.elements.items():
            elem_type = elem.type
            if elem_type in current_bdf_data.elements:
                node_ids = elem.node_ids
                current_bdf_data.elements[elem_type].append((eid, node_ids))
        
        # Extract properties
        current_bdf_data.properties = {pid: prop for pid, prop in model.properties.items()}
        
        return True, None
        
    except Exception as e:
        return False, f"Error loading BDF: {str(e)}"
'''

def validate_and_load_files(bdf_file, op2_file):
    """Validate and load BDF and OP2 files"""
    #global bdf_data
    
    # Reset current data
    bdf_data = BDFData()
    
    # Validate file paths
    if not bdf_file:
        return False, "BDF file path is empty"
    
    if not op2_file:
        return False, "OP2 file path is empty"
    
    if not os.path.exists(bdf_file):
        return False, f"BDF file not found: {bdf_file}"
    
    if not os.path.exists(op2_file):
        return False, f"OP2 file not found: {op2_file}"
    
    # Load BDF file
    try:
        print(f"Loading BDF file: {bdf_file}")
        model = BDF()
        model.read_bdf(bdf_file)
        
        # Extract nodes
        bdf_data.nodes = model.nodes
        print(f"Loaded {len(bdf_data.nodes)} nodes")
        
        # Extract elements by type
        for eid, element in model.elements.items():
            elem_type = element.type
            if elem_type == 'CQUAD4':
                bdf_data.elements['CQUAD4'].append((eid, element.node_ids))
            elif elem_type == 'CTRIA3':
                bdf_data.elements['CTRIA3'].append((eid, element.node_ids))
        
        print(f"Loaded {len(bdf_data.elements['CQUAD4'])} CQUAD4 elements")
        print(f"Loaded {len(bdf_data.elements['CTRIA3'])} CTRIA3 elements")
        
        bdf_data.is_loaded = True
        return bdf_data, True, "Files loaded successfully"
        
    except Exception as e:
        error_msg = f"Error loading BDF file: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return False, error_msg

def read_file(filename):
    """Try to read a file to verify it exists and is readable"""
    try:
        with open(filename, 'r') as f:
            return True
    except:
        return False