from PySide6.QtWidgets import QFileDialog, QMessageBox
from pyNastran.bdf.bdf import BDF
from pyNastran.op2.op2 import OP2
import pyvista as pv
import numpy as np
import os

class ModelData:
    """
    element_id[elid] = {
    "type": element_type,
    "pid": property_id,
    "nodes": {nid: coordinates},
    "thickness": value,
    "width": value,  # for bars
    "property_type": property_type,
    "results": {
        subcase_id: {
            "DISPLACEMENT": 
                    {'t1': value, 't2': value...},
            "STRESS":
                    {...}
    """
    def __init__(self):
        self.element_id = {}  # Store everything based on element IDs
        self.is_loaded = None
        self.op2_data = None  # Store the OP2 object for direct access if needed
        
    def get_result_data(self, result_type, subcase_id, component=None):
        """
        Extract result values for visualization from element_id structure
        
        Parameters:
        -----------
        result_type : str
            Type of result ('DISPLACEMENT', 'STRESS', 'STRAIN', 'FORCE_SHELL', 'FORCE_BAR', etc.)
        subcase_id : int
            Subcase ID number
        component : str, optional
            Specific component name
            
        Returns:
        --------
        dict
            Dictionary with IDs (element or node) as keys and result values as values
        """
        result_data = {}
        # Iterate through all elements to extract results
        for elid, eldata in self.element_id.items():
            results = eldata.get("results", {})
            subcase_results = results.get(subcase_id, {})
            data = subcase_results.get(result_type)

            if data:
                if component:
                    # Only include the specific component
                    value = data.get(component.lower())
                    if value is not None:
                        result_data[elid] = value
                else:
                    # Include the full result dictionary
                    result_data[elid] = data

        return result_data

    def get_node_coordinates(self):
        """Return node coordinates as a numpy array for PyVista"""
        if not self.element_id:
            return None
        
        # Collect all unique nodes from elements
        all_nodes = {}
        for elid, eldata in self.element_id.items():
            if "nodes" in eldata:
                all_nodes.update(eldata["nodes"])
        
        if not all_nodes:
            return None
        
        # Sort nodes by ID for consistent ordering
        sorted_nodes = sorted(all_nodes.items())
        coords = np.array([pos for nid, pos in sorted_nodes])
        return coords, {nid: idx for idx, (nid, pos) in enumerate(sorted_nodes)}

    def get_element_connectivity(self):
        """Return element connectivity for PyVista"""
        if not self.element_id:
            return None, None
        
        # Get node mapping
        coords_result = self.get_node_coordinates()
        if coords_result is None:
            return None, None
        coords, node_map = coords_result
        
        cells = []
        cell_types = []
        element_data = []
        
        for elid, eldata in self.element_id.items():
            if "nodes" not in eldata:
                continue
                
            element_nodes = list(eldata["nodes"].keys())
            mapped_nodes = [node_map[nid] for nid in element_nodes if nid in node_map]
            
            # Determine cell type based on element type and number of nodes
            elem_type = eldata.get("type", "UNKNOWN")
            
            if elem_type in ["CQUAD4", "QUAD4"] or len(mapped_nodes) == 4:
                cells.extend([4] + mapped_nodes)
                cell_types.append(pv.CellType.QUAD)
            elif elem_type in ["CTRIA3", "TRIA3"] or len(mapped_nodes) == 3:
                cells.extend([3] + mapped_nodes)
                cell_types.append(pv.CellType.TRIANGLE)
            elif elem_type in ["CBAR", "BAR"] or len(mapped_nodes) == 2:
                cells.extend([2] + mapped_nodes)
                cell_types.append(pv.CellType.LINE)
            elif len(mapped_nodes) == 6:
                cells.extend([6] + mapped_nodes)
                cell_types.append(pv.CellType.WEDGE)
            elif len(mapped_nodes) == 8:
                cells.extend([8] + mapped_nodes)
                cell_types.append(pv.CellType.HEXAHEDRON)
            else:
                print(f"Warning: Unsupported element {elid} with {len(mapped_nodes)} nodes")
                continue
                
            element_data.append(elid)
        
        return (cells, cell_types, element_data), coords

    def get_available_subcases(self, result_type=None):
        """Get available subcases for a specific result type or all result types"""
        subcases = set()
        
        for elid, eldata in self.element_id.items():
            if "results" in eldata:
                for subcase_id, subcase_results in eldata["results"].items():
                    if result_type:
                        if result_type in subcase_results:
                            subcases.add(subcase_id)
                    else:
                        subcases.add(subcase_id)
        
        return sorted(list(subcases))
    
    def get_available_result_types(self, subcase_id=None):
        """Get available result types for a specific subcase or all subcases"""
        result_types = set()
        
        for elid, eldata in self.element_id.items():
            if "results" in eldata:
                if subcase_id:
                    if subcase_id in eldata["results"]:
                        result_types.update(eldata["results"][subcase_id].keys())
                else:
                    for sc_id, subcase_results in eldata["results"].items():
                        result_types.update(subcase_results.keys())
        
        return sorted(list(result_types))


def extract_op2_results(model_data, model_results):
    """
    Extract results from an OP2 object into the ModelData structure based on element IDs
    
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
    # Create a mapping from node IDs to element IDs for displacement results
    nid_to_elid = {}
    for elid, eldata in model_data.element_id.items():
        if "nodes" in eldata:
            for nid in eldata["nodes"]:
                nid_to_elid.setdefault(nid, []).append(elid)
    
    # Extract displacement results
    if hasattr(model_results, 'displacements'):
        for subcase_id, displacement in model_results.displacements.items():
            if hasattr(displacement, 'dataframe'):
                df = displacement.dataframe.reset_index()
                # Remove 'Type' column if it exists
                if 'Type' in df.columns:
                    df.drop("Type", axis=1, inplace=True)
                
                # Find node ID column
                id_col = next((col for col in df.columns if 'id' in col.lower() and ('node' in col.lower() or 'grid' in col.lower())), None)
                
                if id_col:
                    for _, row in df.iterrows():
                        nid = int(row[id_col])
                        # Get displacement components
                        columns = ["t1", "t2", "t3", "r1", "r2", "r3"]
                        values = {col: row[col] for col in columns if col in df.columns}
                        
                        mag=(row["t1"]**2+row["t2"]**2+row["t3"]**2)**0.5
                        values.update({"magnitude": mag})
                                                                     
                        # Assign to all elements connected to this node
                        if nid in nid_to_elid:
                            for elid in nid_to_elid[nid]:
                                eldata = model_data.element_id[elid]
                                eldata.setdefault("results", {})
                                eldata["results"].setdefault(subcase_id, {})
                                eldata["results"][subcase_id]["DISPLACEMENT"] = values #stores the last value, maybe average ?
            
            print(f"Loaded displacement results for subcase {subcase_id}")
            
    # Extract stress results
    if hasattr(model_results, 'element_stresses'):
        for subcase_id, stress_objs in model_results.element_stresses.items():
            for stress_type, stress_obj in stress_objs.items():
                if hasattr(stress_obj, 'dataframe'):
                    df = stress_obj.dataframe.reset_index()
                    
                    # Find element ID column
                    id_col = next((col for col in df.columns if 'id' in col.lower() and ('elem' in col.lower() or col.upper() == 'EID')), None)
                    
                    if id_col:
                        for _, row in df.iterrows():
                            elid = int(row[id_col])
                            
                            if elid in model_data.element_id:
                                eldata = model_data.element_id[elid]
                                eldata.setdefault("results", {})
                                eldata["results"].setdefault(subcase_id, {})
                                
                                # Store stress components
                                if 'von_mises' in df.columns:
                                    eldata["results"][subcase_id]["STRESS"] = row['von_mises']
                                else:
                                    # Store all available stress components
                                    stress_comps = [col for col in df.columns if col != id_col and not col.endswith('ID')]
                                    if stress_comps:
                                        values = tuple(row[col] for col in stress_comps)
                                        eldata["results"][subcase_id]["STRESS"] = values[0] if len(values) == 1 else values
            
            print(f"Loaded stress results for subcase {subcase_id}")
    
    # Extract strain results (similar to stress)
    if hasattr(model_results, 'element_strains'):
        for subcase_id, strain_objs in model_results.element_strains.items():
            for strain_type, strain_obj in strain_objs.items():
                if hasattr(strain_obj, 'dataframe'):
                    df = strain_obj.dataframe.reset_index()
                    
                    id_col = next((col for col in df.columns if 'id' in col.lower() and ('elem' in col.lower() or col.upper() == 'EID')), None)
                    
                    if id_col:
                        for _, row in df.iterrows():
                            elid = int(row[id_col])
                            
                            if elid in model_data.element_id:
                                eldata = model_data.element_id[elid]
                                eldata.setdefault("results", {})
                                eldata["results"].setdefault(subcase_id, {})
                                
                                if 'von_mises' in df.columns:
                                    eldata["results"][subcase_id]["STRAIN"] = row['von_mises']
                                else:
                                    strain_comps = [col for col in df.columns if col != id_col and not col.endswith('ID')]
                                    if strain_comps:
                                        values = tuple(row[col] for col in strain_comps)
                                        eldata["results"][subcase_id]["STRAIN"] = values[0] if len(values) == 1 else values
            
            print(f"Loaded strain results for subcase {subcase_id}")
    
    # Extract force results
    for force_attr in ['cquad4_force', 'ctria3_force']:
        if hasattr(model_results, force_attr):
            force_data = getattr(model_results, force_attr)
            if isinstance(force_data, dict):
                for subcase_id, force_obj in force_data.items():
                    if hasattr(force_obj, 'dataframe'):
                        df = force_obj.dataframe.reset_index()
                        
                        id_col = next((col for col in df.columns if 'id' in col.lower() and ('elem' in col.lower() or col.upper() == 'EID')), None)
                        
                        if id_col:
                            for _, row in df.iterrows():
                                elid = int(row[id_col])
                                
                                if elid in model_data.element_id:
                                    eldata = model_data.element_id[elid]
                                    eldata.setdefault("results", {})
                                    eldata["results"].setdefault(subcase_id, {})
                                    
                                    # Store force components
                                    force_comps = [col for col in df.columns if col != id_col and not col.endswith('ID')]
                                    if force_comps:
                                        values = tuple(row[col] for col in force_comps)
                                        eldata["results"][subcase_id]["FORCE_SHELL"] = values[0] if len(values) == 1 else values
                    
                    print(f"Loaded {force_attr} results for subcase {subcase_id}")
    
    # Extract bar forces
    if hasattr(model_results, 'cbar_force'):
        for subcase_id, force_obj in model_results.cbar_force.items():
            if hasattr(force_obj, 'dataframe'):
                df = force_obj.dataframe.reset_index()
                
                id_col = next((col for col in df.columns if 'id' in col.lower() and ('elem' in col.lower() or col.upper() == 'EID')), None)
                
                if id_col:
                    for _, row in df.iterrows():
                        elid = int(row[id_col])
                        
                        if elid in model_data.element_id:
                            eldata = model_data.element_id[elid]
                            eldata.setdefault("results", {})
                            eldata["results"].setdefault(subcase_id, {})
                            
                            force_comps = [col for col in df.columns if col != id_col and not col.endswith('ID')]
                            if force_comps:
                                values = tuple(row[col] for col in force_comps)
                                eldata["results"][subcase_id]["FORCE_BAR"] = values[0] if len(values) == 1 else values
            
            print(f"Loaded cbar_force results for subcase {subcase_id}")
    
    return model_data

def validate_and_load(bdf_file, op2_file=None):
    """Validate and load BDF and OP2 files into element_id structure"""
    # Reset current data
    model_data = ModelData()
    
    if not os.path.exists(bdf_file):
        return model_data, None, "BDF file path does not exist"
    
    # Load BDF file
    try:
        print(f"Loading BDF file: {bdf_file}")
        model = BDF()
        try:
            try: 
                model.read_bdf(bdf_file, punch=True, xref=True)
            except: 
                model.read_bdf(bdf_file, punch=False, xref=True)
        except:
            try: 
                model.read_bdf(bdf_file, punch=True, xref=False)
            except: 
                model.read_bdf(bdf_file, punch=False, xref=False)
        
        print(f"Loaded {len(model.nodes)} nodes")
        print(f"Loaded {len(model.elements)} elements")
        
        # Process elements and store everything based on element IDs
        for elid, element in model.elements.items():
            elem_type = element.type
            pid = element.pid
            nids = element.node_ids
            
            # Get property information
            property_obj = model.properties.get(pid)
            
            # Initialize element data
            model_data.element_id[elid] = {
                "type": elem_type,
                "pid": pid,
                "nodes": {nid: model.nodes[nid].get_position() for nid in nids}
            }
            
            # Extract property-specific attributes
            if property_obj:
                prop_type = property_obj.type
                model_data.element_id[elid]["property_type"] = prop_type
                
                if prop_type in ["PSHELL"]:
                    thickness = getattr(property_obj, 't', 0.0)
                    model_data.element_id[elid]["thickness"] = thickness
                    
                elif prop_type in ["PBARL"]:
                    dim = getattr(property_obj, 'dim', [0.0, 0.0])
                    if len(dim) >= 2:
                        model_data.element_id[elid]["thickness"] = dim[0]
                        model_data.element_id[elid]["width"] = dim[1]
                    
                elif prop_type in ["PCOMP"]:
                    thicknesses = getattr(property_obj, 'thicknesses', [0.0])
                    model_data.element_id[elid]["thickness"] = thicknesses[0] if thicknesses else 0.0
                
                else:
                    print(f"Unknown property type: {prop_type}")
        
        model_data.is_loaded = "only bdf"
        text = "BDF file loaded successfully"

    except Exception as e:
        text = f"Error loading BDF file: {str(e)}"
        print(text)
        return model_data, False, text
    
    # Load OP2 file if provided
    if op2_file and os.path.exists(op2_file):
        try:
            print(f"Loading OP2 file: {op2_file}")
            model_results = OP2()
            model_results.read_op2(op2_file, build_dataframe=True)
            
            # Store the OP2 model for direct access if needed
            model_data.op2_data = model_results
            
            # Extract results using the function
            model_data = extract_op2_results(model_data, model_results)
            
            model_data.is_loaded = "both"
            text = "BDF and OP2 files loaded successfully"
            
        except Exception as e:
            error_msg = f"Error loading OP2 file: {str(e)}"
            print(error_msg)
            text += f"\n{error_msg}"
    
    return model_data, model_data.is_loaded, text

def browse_file(parent, file_type):
    """Open file browser dialog and return selected file"""
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