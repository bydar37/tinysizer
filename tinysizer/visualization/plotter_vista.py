import pyvista as pv
import numpy as np
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
        
    def plot_mesh(self, nodes, elements):
        print("Plot mesh called with:", len(nodes) if nodes else 0, "nodes and", 
              len(elements.get('CQUAD4', [])) + len(elements.get('CTRIA3', [])), "elements")
        
        if not nodes:
            print("No nodes provided")
            return
            
        # Clear existing actors
        self.plotter.clear()
        self.add_axes()
        
        # Create points array
        points = []
        node_id_to_idx = {}
        idx = 0
        
        # Process nodes
        for nid, grid_obj in nodes.items():
            try:
                # Extract coordinates from pyNastran GRID objects
                if hasattr(grid_obj, 'xyz'):
                    coords = grid_obj.xyz
                elif hasattr(grid_obj, 'get_position'):
                    coords = grid_obj.get_position()
                else:
                    print(f"Skipping node {nid} - no coordinate data found")
                    continue
                    
                # Add the point
                points.append(coords)
                
                # Store the mapping from node ID to point index
                node_id_to_idx[nid] = idx
                idx += 1
                
            except Exception as e:
                print(f"Error processing node {nid}: {str(e)}")
        
        points = np.array(points)
        print(f"Successfully processed {len(points)} nodes")
        
        # Create mesh objects for different element types
        quad_faces = []
        tri_faces = []
        
        # Process quad elements (CQUAD4)
        for elem in elements.get('CQUAD4', []):
            try:
                # Check if elem is a tuple of (eid, node_ids) or just a dictionary/object
                if isinstance(elem, tuple) and len(elem) == 2:
                    eid, node_ids = elem
                elif hasattr(elem, 'node_ids'):  # pyNastran element object
                    eid = elem.eid
                    node_ids = elem.node_ids
                elif isinstance(elem, dict):  # Dictionary representation
                    eid = elem.get('eid')
                    node_ids = elem.get('nodes')
                else:
                    print(f"Unsupported quad element format: {type(elem)}")
                    continue
                
                # PyVista expects faces as [n, id1, id2, ..., idn] where n is the number of points
                face_indices = []
                valid_element = True
                
                for nid in node_ids:
                    if nid in node_id_to_idx:
                        face_indices.append(node_id_to_idx[nid])
                    else:
                        print(f"Node {nid} from element {eid} not found in node map")
                        valid_element = False
                        break
                
                if valid_element:
                    # Format for PyVista: [4, idx0, idx1, idx2, idx3]
                    quad_faces.append([4] + face_indices)
                    
            except Exception as e:
                print(f"Error processing quad element: {str(e)}")
        
        # Process triangular elements (CTRIA3)
        for elem in elements.get('CTRIA3', []):
            try:
                # Check element format
                if isinstance(elem, tuple) and len(elem) == 2:
                    eid, node_ids = elem
                elif hasattr(elem, 'node_ids'):
                    eid = elem.eid
                    node_ids = elem.node_ids
                elif isinstance(elem, dict):
                    eid = elem.get('eid')
                    node_ids = elem.get('nodes')
                else:
                    print(f"Unsupported triangle element format: {type(elem)}")
                    continue
                
                face_indices = []
                valid_element = True
                
                for nid in node_ids:
                    if nid in node_id_to_idx:
                        face_indices.append(node_id_to_idx[nid])
                    else:
                        print(f"Node {nid} from element {eid} not found in node map")
                        valid_element = False
                        break
                
                if valid_element:
                    # Format for PyVista: [3, idx0, idx1, idx2]
                    tri_faces.append([3] + face_indices)
                    
                if len(tri_faces) % 1000 == 0 and len(tri_faces) > 0:
                    print(f"Processed {len(tri_faces)} triangle elements...")
                    
            except Exception as e:
                print(f"Error processing triangle element: {str(e)}")
        
        print(f"Successfully processed {len(quad_faces)} quads and {len(tri_faces)} triangles")
        
        # Create and display meshes
        if quad_faces or tri_faces:
            # Combine all faces for a single mesh
            faces = quad_faces + tri_faces
            if faces:
                # Convert to the format PyVista expects
                faces_array = []
                for face in faces:
                    faces_array.extend(face)
                
                # Create the mesh
                mesh = pv.PolyData(points, faces=faces_array)
                
                # Add the mesh to the plotter
                self.plotter.add_mesh(mesh, show_edges=True, color=[0.8, 0.8, 0.8], 
                                      edge_color='black', line_width=1.5, opacity=0.7)
                
                print(f"Created mesh with {mesh.n_points} points and {mesh.n_cells} cells")
            
        # If no elements were added, at least show the nodes as points
        if not quad_faces and not tri_faces:
            point_cloud = pv.PolyData(points)
            self.plotter.add_mesh(point_cloud, render_points_as_spheres=True, 
                                  point_size=10, color='red')
            print("No elements found, displaying points only")
        
        # Reset camera and render
        self.plotter.reset_camera()
        self.plotter.update()
        
        self.has_rendered = True
        print("Rendering complete")
    
    def set_display_mode(self, mode):
        """Set the display mode for the geometry visualization"""
        if mode == "wireframe":
            # Get all current meshes and update their style
            actors = self.plotter.renderer.GetActors()
            if actors.GetNumberOfItems() > 0:
                for i in range(actors.GetNumberOfItems()):
                    actor = actors.GetItemAsObject(i)
                    actor.GetProperty().SetRepresentationToWireframe()
                self.plotter.update()
        elif mode == "surface":
            actors = self.plotter.renderer.GetActors()
            if actors.GetNumberOfItems() > 0:
                for i in range(actors.GetNumberOfItems()):
                    actor = actors.GetItemAsObject(i)
                    actor.GetProperty().SetRepresentationToSurface()
                self.plotter.update()
    
    def reset_view(self):
        """Reset the camera view"""
        self.plotter.reset_camera()
        self.plotter.update()
        
    def closeEvent(self, event):
        """Handle cleanup when widget is closed"""
        self.plotter.close()
        super().closeEvent(event)