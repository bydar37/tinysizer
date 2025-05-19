import pyvista as pv
import numpy as np
import pandas as pd
from PySide6.QtWidgets import QFrame, QVBoxLayout
from pyvistaqt import QtInteractor

class PyVistaMeshPlotter(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create layout that fills the entire frame
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create PyVista plotter with Qt interactor
        # Setting interactive=True enables mouse interaction
        self.plotter = QtInteractor(self, auto_update=True)
        layout.addWidget(self.plotter)
        
        # Set background color
        self.plotter.set_background([0.2, 0.2, 0.3])  # Dark blue-gray
        
        # Add axes for reference
        self.add_axes()
        
        # Set flag for tracking if we've rendered anything
        self.has_rendered = False
        
    def add_axes(self):
        """Add coordinate axes to scene"""
        self.plotter.add_axes(xlabel='X', ylabel='Y', zlabel='Z', 
                              line_width=2, labels_off=False)


    #THE MAIN GUY, PLOTU YAPAN FONKSIYON   
    def plot_mesh(self, model_data, result_type=None, subcase_id=None, component=None):
        """
        Plot mesh from ModelData with optional results visualization
        
        Parameters:
        -----------
        model_data : ModelData
            The loaded model data object (from CODE 1)
        result_type : str, optional
            Type of result to visualize (e.g., 'DISPLACEMENT', 'STRESS')
        subcase_id : int, optional
            Subcase ID to visualize
        component : str, optional
            Specific component to visualize (e.g., 'von_mises', 'T1', 'T2', 'T3')
        """
        
        # Check if model_data is valid
        if not model_data or not model_data.element_id:
            print("No model data provided")
            return
            
        print(f"Plot mesh called with {len(model_data.element_id)} elements")
        
        # Clear existing actors
        self.plotter.clear()
        self.add_axes()
        
        # Extract nodes and coordinates from model_data.element_id structure
        coords_result = model_data.get_node_coordinates()
        if coords_result is None:
            print("No node coordinates found")
            return
            
        points, node_id_to_idx = coords_result
        print(f"Successfully processed {len(points)} nodes")
        
        # Extract element connectivity
        connectivity_result = model_data.get_element_connectivity()
        if connectivity_result is None:
            print("No element connectivity found")
            return
            
        (cells, cell_types, element_data), coords = connectivity_result
        
        # Create mesh using PyVista
        mesh = pv.UnstructuredGrid(cells, cell_types, points)
        
        # Process and add results if requested
        if result_type and subcase_id is not None:
            # Get result data using model_data's method
            result_data = model_data.get_result_data(result_type, subcase_id, component)
            
            if result_data:
                # Get the appropriate label for the scalars
                scalar_label = component if component else result_type.lower()
                
                if result_type == 'DISPLACEMENT':
                    # Displacement is a nodal result
                    node_values = np.zeros(len(points))
                    
                    # Map displacement values to nodes
                    # For displacement, we need to extract from elements back to nodes
                    node_displacement_map = {}
                    for elid, value in result_data.items():
                        if elid in model_data.element_id:
                            element_nodes = model_data.element_id[elid].get("nodes", {})
                            for nid in element_nodes:
                                if nid not in node_displacement_map:
                                    node_displacement_map[nid] = []
                                node_displacement_map[nid].append(value)
                    
                    # Average displacement values for nodes connected to multiple elements
                    for nid, values in node_displacement_map.items():
                        if nid in node_id_to_idx:
                            print(nid,np.mean(values))
                            idx = node_id_to_idx[nid]
                            print(idx)
                            node_values[idx] = np.mean(values)
                    
                    # Add as point data
                    mesh.point_data[scalar_label] = node_values
                    
                    # Add the mesh with the results
                    self.plotter.add_mesh(mesh, scalars=scalar_label, show_edges=True,
                                        cmap='jet', edge_color='black', line_width=1.5,
                                        scalar_bar_args={"title": f"{result_type} ({scalar_label})"})

                elif result_type == 'FORCE':
                    # Displacement is a nodal result
                    node_values = np.zeros(len(points))
                    
                    # Map displacement values to nodes
                    # For displacement, we need to extract from elements back to nodes
                    node_displacement_map = {}
                    for elid, value in result_data.items():
                        if elid in model_data.element_id:
                            element_nodes = model_data.element_id[elid].get("nodes", {})
                            for nid in element_nodes:
                                if nid not in node_displacement_map:
                                    node_displacement_map[nid] = []
                                node_displacement_map[nid].append(value)
                    
                    # Average displacement values for nodes connected to multiple elements
                    for nid, values in node_displacement_map.items():
                        if nid in node_id_to_idx:
                            idx = node_id_to_idx[nid]
                            node_values[idx] = np.mean(values)
                    
                    # Add as point data
                    mesh.point_data[scalar_label] = node_values
                    
                    # Add the mesh with the results
                    self.plotter.add_mesh(mesh, scalars=scalar_label, show_edges=True,
                                        cmap='jet', edge_color='black', line_width=1.5,
                                        scalar_bar_args={"title": f"{result_type} ({scalar_label})"})
                      
                else:
                    # Element results (stress, strain, force, etc.)
                    element_values = np.zeros(len(element_data))
                    
                    # Map element results to cells
                    for i, eid in enumerate(element_data):
                        if eid in result_data:
                            element_values[i] = result_data[eid]
                    
                    # Add as cell data
                    mesh.cell_data[scalar_label] = element_values
                    
                    # Add the mesh with the results
                    self.plotter.add_mesh(mesh, scalars=scalar_label, show_edges=True,
                                        cmap='jet', edge_color='black', line_width=1.5,
                                        scalar_bar_args={"title": f"{result_type} ({scalar_label})"})
            else:
                # No result data found, add mesh with default appearance
                self.plotter.add_mesh(mesh, show_edges=True, color=[0.8, 0.8, 0.8], 
                                    edge_color='black', line_width=1.5, opacity=1.0)
        else:
            # No results specified, add mesh with default appearance
            self.plotter.add_mesh(mesh, show_edges=True, color=[0.8, 0.8, 0.8], 
                                edge_color='black', line_width=1.5, opacity=1.0)
        
        print(f"Created mesh with {mesh.n_points} points and {mesh.n_cells} cells")
        
        # Reset camera and update
        self.plotter.reset_camera()
        self.plotter.update()
        self.has_rendered = True
        
        print("Rendering complete")
    
    def reset_view(self):
        """Reset the camera view"""
        self.plotter.reset_camera()
        self.plotter.update()
        
    def closeEvent(self, event):
        """Handle cleanup when widget is closed"""
        self.plotter.close()
        super().closeEvent(event)

    #öylesine xD
    def plot_something_random(self):
        import random
        
        example_datasets = dir(pv.examples)  # This gives you a list of available example datasets
        example_datasets = [dataset for dataset in example_datasets if not dataset.startswith('_')]
        random_example = random.choice(example_datasets)

        try:
            dataset = getattr(pv.examples, random_example)()  # Call the example function
            # Clear the previous plot (if any)
            self.plotter.clear()
            # Add the new dataset to the plotter
            self.plotter.add_mesh(dataset, show_edges=True, edge_color='black')
            # Optionally, reset camera to fit the new plot
            self.plotter.reset_camera()
            self.plotter.update()
        except Exception as e:
            print(f"Random plot failed {e}, trying again...")
            self.plot_something_random()

        # Plot the dataset
        self.has_rendered = True
        print(f"Plotting: {random_example}")