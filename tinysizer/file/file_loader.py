from PySide6.QtWidgets import QFileDialog, QMessageBox
from pyNastran.bdf.bdf import BDF
from pyNastran.op2.op2 import OP2
import random
import numpy as np
import os

class ModelData:
    def __init__(self):
        self.properties = {}
        self.nodes = {}
        self.elements = {
            'CQUAD4': [],
            'CTRIA3': [],
            'CBAR': [],
            'CBEAM': []
        }
        self.element_ids = {}  # Dictionary to store element IDs by type
        self.attributes = {
        }
        self.results = {
            'DISPLACEMENT': {},
            'STRESS': {},
            'STRAIN': {},
            'FORCE_SHELL': {}, # For CQUAD4 and CTRIA3 forces
            'FORCE_BAR': {},   # For CBAR forces
            'EIGENVECTORS': {},
            'THICKNESS':{},
            'ÖMER JOINTS':{},
            'BURAK BUFFETS':{},
        }
        self.coordinate_systems = {}
        self.bdf = None
        self.op2= None
        self.is_loaded = None

            
    def get_result_data(self, result_type, subcase_id, component=None):
        """
        Simplified method to extract result values for visualization
        
        Parameters:
        -----------
        result_type : str
            Type of result ('DISPLACEMENT', 'STRESS', 'STRAIN', 'FORCE', 'FORCE_BAR', etc.)
        subcase_id : int
            Subcase ID number
        component : str, optional
            Specific component name
            
        Returns:
        --------
        dict
            Dictionary with IDs (element or node) as keys and result values as values
        """

        result_data={}
        # Handle thickness as a special case - it doesn't come from OP2 results
        if result_type == 'THICKNESS':
            if self.bdf and self.bdf.elements:
                for elid, element in self.bdf.elements.items():
                    try:
                        prop = self.bdf.properties[element.pid]
                        if prop.type == "PSHELL":
                            thickness = prop.t
                        elif prop.type == "PCOMP":
                            thickness = prop.thicknesses[0]
                        else:
                            thickness = 0
                        result_data[elid] = thickness
                    except (KeyError, AttributeError, IndexError) as e:
                        print(f"Warning: Could not get thickness for element {elid}: {e}")
                        result_data[elid] = 0
            return result_data
        

        if "ömer" in result_type.lower():
            if self.bdf and self.bdf.elements:
                for elid, element in self.bdf.elements.items():
                    try:
                        thickness=random.randint(0,10)
                        result_data[elid] = elid**2
                    except (KeyError, AttributeError, IndexError) as e:
                        print(f"Warning: Could not get thickness for element {elid}: {e}")
                        result_data[elid] = 0
            return result_data
        
        if "burak" in result_type.lower():
            if self.bdf and self.bdf.elements:
                for elid, element in self.bdf.elements.items():
                    try:
                        thickness=random.randint(0,10)
                        result_data[elid] = elid**1.2
                    except (KeyError, AttributeError, IndexError) as e:
                        print(f"Warning: Could not get thickness for element {elid}: {e}")
                        result_data[elid] = 0
            return result_data
        
        # Check if the requested result exists
        if result_type not in self.results or subcase_id not in self.results[result_type]:
            return {}
        
        # Get the result objects for this type and subcase
        result_objects = self.results[result_type].get(subcase_id, [])
        
        # For each result object (there might be multiple for some result types)
        for result_obj in result_objects:
            # Handle dataframe-based results (most common in newer versions)
            if hasattr(result_obj, 'dataframe'):
                df = result_obj.dataframe.reset_index()
                
                # Extract data based on result type
                if result_type == 'DISPLACEMENT' or result_type == 'EIGENVECTORS':
                    # Get the ID column name (could be NodeID, node_id, or GridID)
                    df.drop("Type", axis=1, inplace=True)  # Type sonucunu cikariyorum
                    id_col = next((col for col in df.columns if 'id' in col.lower() and ('node' in col.lower() or 'grid' in col.lower())), None)
                    
                    if id_col:
                        if component and component in df.columns:
                            # Get specific component
                            for _, row in df.iterrows():
                                result_data[int(row[id_col])] = row[component]
                        else:
                            # Calculate displacement magnitude from T1, T2, T3
                            t_comps = [c for c in df.columns if c in ["t1", "t2", "t3"]]

                            if t_comps:
                                for _, row in df.iterrows():
                                    magnitude = np.sqrt(sum(row[c]**2 for c in t_comps))
                                    result_data[int(row[id_col])] = magnitude
                
                elif result_type == 'FORCE_SHELL':
                    # Get the element ID column
                    id_col = next((col for col in df.columns if 'id' in col.lower() and ('elem' in col.lower() or col.upper() == 'EID')), None)
                    
                    if id_col:
                        if component and component in df.columns:
                            # Get specific component
                            for _, row in df.iterrows():
                                result_data[int(row[id_col])] = row[component]
                        else:
                            # Calculate appropriate magnitude based on available components
                            # For shell forces: combine membrane forces (mx, my, mxy)
                            # For bar forces: might be different
                            
                            # For membranes - prioritize force components
                            m_comps = [c for c in df.columns if c in ['mx', 'my', 'mxy']]
                            b_comps = [c for c in df.columns if c in ['bmx', 'bmy', 'bmxy']]
                            t_comps = [c for c in df.columns if c in ['tx', 'ty']]
                            
                            # Choose components for magnitude calculation (prioritize membrane forces)
                            comps_to_use = m_comps if m_comps else (b_comps if b_comps else t_comps)
                            
                            if comps_to_use:
                                for _, row in df.iterrows():
                                    magnitude = np.sqrt(sum(row[c]**2 for c in comps_to_use))
                                    result_data[int(row[id_col])] = magnitude
                            elif len(df.columns) > 1:  # Just use the first numeric column that's not the ID
                                # Find first numeric data column
                                data_cols = [c for c in df.columns if c != id_col and not c.endswith('ID')]
                                if data_cols:
                                    for _, row in df.iterrows():
                                        result_data[int(row[id_col])] = row[data_cols[0]]
                
                elif result_type == 'FORCE_BAR':
                    # Get the element ID column
                    id_col = next((col for col in df.columns if 'id' in col.lower() and ('elem' in col.lower() or col.upper() == 'EID')), None)
                    
                    if id_col:
                        if component and component in df.columns:
                            # Get specific component
                            for _, row in df.iterrows():
                                result_data[int(row[id_col])] = row[component] 

                elif result_type == 'STRESS' or result_type == 'STRAIN':
                    # Get the element ID column
                    id_col = next((col for col in df.columns if 'id' in col.lower() and ('elem' in col.lower() or col.upper() == 'EID')), None)
                    
                    if id_col:
                        if component and component in df.columns:
                            # Get specific component
                            for _, row in df.iterrows():
                                result_data[int(row[id_col])] = row[component]
                        elif 'von_mises' in df.columns:
                            # Use von Mises as default for stress/strain
                            for _, row in df.iterrows():
                                result_data[int(row[id_col])] = row['von_mises']
                        elif 'max_principal' in df.columns:
                            # Use max principal as alternative
                            for _, row in df.iterrows():
                                result_data[int(row[id_col])] = row['max_principal']
                        elif len(df.columns) > 1:
                            # Just use the first numeric column that's not the ID
                            data_cols = [c for c in df.columns if c != id_col and not c.endswith('ID')]
                            if data_cols:
                                for _, row in df.iterrows():
                                    result_data[int(row[id_col])] = row[data_cols[0]]

            # Handle non-dataframe formats (legacy or specialized formats)
            else:
                # Try to get available components for this result
                components = getattr(result_obj, 'components', [])
                
                # For element-node based results
                if hasattr(result_obj, 'element_node'):
                    ids = result_obj.element_node[:, 0]  # First column is usually element IDs
                    
                    if component and component in components:
                        # Get specific component
                        comp_idx = components.index(component)
                        for i, eid in enumerate(ids):
                            result_data[int(eid)] = result_obj.data[i, comp_idx]
                    elif hasattr(result_obj, 'von_mises'):
                        # Use von Mises if available
                        for i, eid in enumerate(ids):
                            result_data[int(eid)] = result_obj.von_mises[i]
                    elif hasattr(result_obj, 'data') and result_obj.data.size > 0:
                        # Use first component as default
                        for i, eid in enumerate(ids):
                            result_data[int(eid)] = result_obj.data[i, 0] if result_obj.data[i].size > 0 else 0
                
                # For dictionary-based data
                elif hasattr(result_obj, 'data') and isinstance(result_obj.data, dict):
                    for eid, values in result_obj.data.items():
                        if component and component in components:
                            # Get specific component
                            comp_idx = components.index(component)
                            if isinstance(values, (list, tuple, np.ndarray)) and len(values) > comp_idx:
                                result_data[int(eid)] = values[comp_idx]
                        elif isinstance(values, (list, tuple, np.ndarray)):
                            # Calculate magnitude or use first component
                            if len(values) >= 3:  # Assume xyz or similar
                                result_data[int(eid)] = np.sqrt(values[0]**2 + values[1]**2 + values[2]**2)
                            elif len(values) > 0:
                                result_data[int(eid)] = values[0]
                        elif isinstance(values, (int, float)):
                            result_data[int(eid)] = values

        return result_data


    def get_node_coordinates(self):
        """Return node coordinates as a numpy array for PyVista"""
        if not self.nodes:
            return None
        
        coords = np.zeros((len(self.nodes), 3))
        for i, (nid, node) in enumerate(self.nodes.items()):
            coords[i] = node.get_position()
        return coords

    def get_element_connectivity(self, element_type):
        """Return element connectivity for PyVista"""
        if not self.elements[element_type]:
            return None
        
        conn_list = []
        for elem_info in self.elements[element_type]:
            _, _, _, node_ids = elem_info
            if element_type == 'CQUAD4':
                conn_list.append([4] + list(node_ids))
            elif element_type == 'CTRIA3':
                conn_list.append([3] + list(node_ids))
            elif element_type == 'CBAR':
                conn_list.append([2] + list(node_ids))
        
        return conn_list if conn_list else None


    def get_available_subcases(self, result_type=None):
        """Get available subcases for a specific result type or all result types"""
        if result_type:
            if result_type in self.results:
                return list(self.results[result_type].keys())
            return []
        
        # Get all subcases from all result typesls
        subcases = set()
        for res_type in self.results:
            subcases.update(self.results[res_type].keys())
        return sorted(list(subcases))
    
    def get_available_components(self, result_type, subcase_id):
        """Get available components for a specific result type and subcase"""
        if result_type not in self.results or subcase_id not in self.results[result_type]:
            return []
        
        components = set()
        for result_obj in self.results[result_type].get(subcase_id, []):
            if hasattr(result_obj, 'components'):
                components.update(result_obj.components)
            elif hasattr(result_obj, 'dataframe'):
                # For dataframe-based results (like displacement)
                columns = result_obj.dataframe.columns
                # Filter out non-component columns
                for col in columns:
                    if col not in ['NodeID', 'ElementID', 'GridID', 'SubcaseID']:
                        components.add(col)
        
        return sorted(list(components))
    
    def prepare_mesh_data_for_pyvista(self):
        """Prepare data in a format suitable for PyVista"""
        mesh_data = {
            'nodes': self.get_node_coordinates(),
            'elements': {}
        }
        
        for elem_type in self.elements:
            if self.elements[elem_type]:
                mesh_data['elements'][elem_type] = self.get_element_connectivity(elem_type)
        
        return mesh_data
    
#OP2'DAN DATAYI CEKTIGIMIZ YER...
def extract_op2_results(model_data, model_results):
    """
    Simplified function to extract results from an OP2 object into the ModelData structure
    
    Parameters:
    -----------
    model_data : ModelData
        The data structure to store results in
    model_results : OP2
        The pyNastran OP2 object containing results
    
    Returns:
    --------
    ModelData
        Updated model_data with results extracted
    """
    # Extract displacement results
    if hasattr(model_results, 'displacements'):
        for subcase_id, displacement in model_results.displacements.items():
            model_data.results["DISPLACEMENT"][subcase_id] = [displacement]
            print(f"Loaded displacement results for subcase {subcase_id}")
    
    # Extract stress results
    if hasattr(model_results, 'element_stresses'):
        for subcase_id, stress_objs in model_results.element_stresses.items():
            model_data.results["STRESS"][subcase_id] = list(stress_objs.values())
            print(f"Loaded stress results for subcase {subcase_id}")
    
    # Extract strain results
    if hasattr(model_results, 'element_strains'):
        for subcase_id, strain_objs in model_results.element_strains.items():
            model_data.results["STRAIN"][subcase_id] = list(strain_objs.values())
            print(f"Loaded strain results for subcase {subcase_id}")
    
    # Extract shell forces (CQUAD4, CTRIA3)
    for force_attr in ['cquad4_force', 'ctria3_force']:
        if hasattr(model_results, force_attr):
            force_data = getattr(model_results, force_attr)
            if isinstance(force_data, dict):
                for subcase_id, force_obj in force_data.items():
                    if subcase_id not in model_data.results["FORCE_SHELL"]:
                        model_data.results["FORCE_SHELL"][subcase_id] = []
                    model_data.results["FORCE_SHELL"][subcase_id].append(force_obj)
                    print(f"Loaded {force_attr} results for subcase {subcase_id}")
    
    # Extract bar forces (CBAR)
    if hasattr(model_results, 'cbar_force'):
        for subcase_id, force_obj in model_results.cbar_force.items():
            if subcase_id not in model_data.results["FORCE_BAR"]:
                model_data.results["FORCE_BAR"][subcase_id] = []
            model_data.results["FORCE_BAR"][subcase_id].append(force_obj)
            print(f"Loaded cbar_force results for subcase {subcase_id}")
    
    # Extract eigenvector results
    if hasattr(model_results, 'eigenvectors'):
        for subcase_id, eigenvector in model_results.eigenvectors.items():
            model_data.results["EIGENVECTORS"][subcase_id] = [eigenvector]
            print(f"Loaded eigenvector results for subcase {subcase_id}")
    
    # Extract thickness results
    if model_data.bdf:
        model_data.results.setdefault("THICKNESS", {})[" "] = []
        print(f"Thickness is stored !")

    # Extract thickness results
    if model_data.bdf:
        model_data.results.setdefault("BURAK BUFFETS", {})[" "] = []

    # Extract thickness results  
    if model_data.bdf:
        model_data.results.setdefault("ÖMER JOİNTS", {})[" "] = []

    else:
        print("(WARNING) Thickness data is missing.")

    return model_data
    

def validate_and_load(bdf_file, op2_file=None):
    """Validate and load BDF and OP2 files, makes model_data.result fulfilled"""
    # Reset current data
    model_data = ModelData()
    
    if not os.path.exists(bdf_file):
        return model_data, None, "BDF file path is empty"
    
    # Load BDF file
    try:
        print(f"Loading BDF file: {bdf_file}")
        model = BDF()
        try:
            try: model.read_bdf(bdf_file, punch=True, xref=True)
            except: model.read_bdf(bdf_file, punch=False, xref=True)
        except:
            try: model.read_bdf(bdf_file, punch=True, xref=False)
            except: model.read_bdf(bdf_file, punch=False, xref=False)
        
        '''
        pid2eid=model.get_property_id_to_element_ids_map()
        #store property ids for later -ymn
        for pid, property in model.properties.items():
            if pid not in self.properties:
                self.properties[pid]=[]
                self.properties[pid].extend(pid2eid[pid])
            else:
                self.properties[pid].extend(pid2eid[pid])
        '''
        
        # Extract nodes
        model_data.nodes = model.nodes
        model_data.bdf = model
        print(f"Loaded {len(model_data.nodes)} nodes")
        
        # Extract element IDs by type for easier reference
        for eid, element in model.elements.items():
            elem_type = element.type
            model_data.element_ids.setdefault(elem_type, []).append(eid)
        
        # Extract elements by type
        for eid, element in model.elements.items():
            elem_type = element.type
            pid = element.pid
            typ = model.properties[pid].type if pid in model.properties else 'UNKNOWN'
            
            if elem_type in model_data.elements:
                model_data.elements[elem_type].append((typ, pid, eid, element.node_ids))
            
            # Store property information
            model_data.properties.setdefault(typ, {}).setdefault(pid, {})
            prop = model.properties.get(pid)
            if prop:
                # Store relevant property attributes
                for attr_name in dir(prop):
                    if not attr_name.startswith('_') and attr_name not in ['type', 'pid']:
                        try:
                            attr_value = getattr(prop, attr_name)
                            if not callable(attr_value):
                                model_data.properties[typ][pid][attr_name] = attr_value
                        except:
                            pass
                        
        # thickness extraction -ymn
        for eid, element in model.elements.items():
            model_data.attributes.setdefault

        # Store coordinate systems if available
        if hasattr(model, 'coords'):
            model_data.coordinate_systems = model.coords
            
        # Count elements by type
        for elem_type in model_data.elements:
            print(f"Loaded {len(model_data.elements[elem_type])} {elem_type} elements")
        
        model_data.is_loaded = "only bdf"
        text = "BDF file loaded successfully"

    except Exception as e:
        text = f"Error loading BDF file: {str(e)}\n"
        print(text)
        return model_data, False, text
    
    # Load OP2 file if provided
    if op2_file and os.path.exists(op2_file):
        try:
            print(f"Loading OP2 file: {op2_file}")
            model_results = OP2()
            model_results.read_op2(op2_file, build_dataframe=True)
            
            # Store the OP2 model for direct access if needed
            model_data.op2 = model_results
            
            # Extract results using the simplified function
            model_data = extract_op2_results(model_data, model_results)
            
            model_data.is_loaded = "both"
            text = "BDF and OP2 files loaded successfully"
            
        except Exception as e:
            error_msg = f"Error loading OP2 file: {str(e)}\n"
            print(error_msg)
            text = error_msg
    
    return model_data, model_data.is_loaded, text

def browse_file(parent, file_type):
    """Open file browser dialog and return selected file"""
    from PySide6.QtWidgets import QFileDialog
    
    file_filter = "BDF files (*.bdf);;All files (*.*)" if file_type == "BDF" else "OP2 files (*.op2);;All files (*.*)"
    filename, _ = QFileDialog.getOpenFileName(parent, f"Select {file_type} File", "", file_filter)
    return filename


def read_file(filename):
    """Try to read a file to verify it exists and is readable"""
    try:
        with open(filename, 'r') as f:
            return True
    except:
        return False