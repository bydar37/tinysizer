import vtk
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkRenderer,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
    vtkDataSetMapper
)
from vtkmodules.vtkRenderingAnnotation import vtkAxesActor  # Changed import location
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import (
    vtkCellArray,
    vtkUnstructuredGrid,
    vtkQuad,
    vtkTriangle,
    VTK_QUAD,
    VTK_TRIANGLE
)
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera
from PySide6.QtWidgets import QFrame, QVBoxLayout

class VTKMeshPlotter(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.vtkWidget = QVTKRenderWindowInteractor(self)
        
        # Create a renderer and add it to the widget
        self.renderer = vtk.vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(self.renderer)
        
        # Initialize the interactor
        self.iren = self.vtkWidget.GetRenderWindow().GetInteractor()
        if self.iren is None:
            print("ERROR: Interactor is None!")
        else:
            self.iren.Initialize()
        
        # Set background color
        self.renderer.SetBackground(0.2, 0.2, 0.3)  # Dark blue-gray
        
        # Add axes for reference
        self.add_axes()
        
        # Set flag for tracking if we've rendered anything
        self.has_rendered = False
        
        # Store these for later use
        self.VTK_QUAD = vtk.VTK_QUAD
        self.VTK_TRIANGLE = vtk.VTK_TRIANGLE

        
    def setup_vtk(self):
        """Initialize VTK rendering"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create VTK widget
        self.vtkWidget = QVTKRenderWindowInteractor(self)
        layout.addWidget(self.vtkWidget)
        
        # Create renderer
        self.renderer = vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(self.renderer)
        
        # Set background
        self.renderer.SetBackground(0.2, 0.3, 0.4)  # Dark blue background
        
        # Initialize interactor
        self.interactor = self.vtkWidget.GetRenderWindow().GetInteractor()
        style = vtkInteractorStyleTrackballCamera()
        self.interactor.SetInteractorStyle(style)
        
        # Add axes
        self.add_axes()
        
        # Start interactor
        self.interactor.Initialize()
        self.vtkWidget.GetRenderWindow().Render()
        print("VTK widget initialized")
        
    def add_axes(self):
        """Add coordinate axes to scene"""
        axes = vtkAxesActor()
        axes.SetTotalLength(10.0, 10.0, 10.0)  # Make axes bigger for visibility
        axes.GetXAxisCaptionActor2D().GetTextActor().SetTextScaleModeToNone()
        axes.GetYAxisCaptionActor2D().GetTextActor().SetTextScaleModeToNone()
        axes.GetZAxisCaptionActor2D().GetTextActor().SetTextScaleModeToNone()
        self.renderer.AddActor(axes)
        
    def plot_mesh(self, nodes, elements):
        print("Plot mesh called with:", len(nodes) if nodes else 0, "nodes and", 
            len(elements.get('CQUAD4', [])) + len(elements.get('CTRIA3', [])), "elements")
        
        if not nodes:
            print("No nodes provided")
            return
            
        # Clear existing actors except axes
        self.renderer.RemoveAllViewProps()
        self.add_axes()
        
        # Create points
        points = vtkPoints()
        
        # Create a mapping from node IDs to VTK point indices
        node_id_to_idx = {}
        idx = 0
        
        # First pass: just display the nodes to verify they're being processed
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
                    
                # Insert the point
                points.InsertNextPoint(coords[0], coords[1], coords[2])
                
                # Store the mapping from node ID to VTK point index
                node_id_to_idx[nid] = idx
                idx += 1
                
                if idx % 1000 == 0:
                    print(f"Processed {idx} nodes...")
                
            except Exception as e:
                print(f"Error processing node {nid}: {str(e)}")
        
        print(f"Successfully processed {points.GetNumberOfPoints()} nodes")
        
        # Create unstructured grid
        #grid = vtkUnstructuredGrid()
        #grid.SetPoints(points)
        
        # Create cell arrays
        quad_cells = vtkCellArray()
        tri_cells = vtkCellArray()
        
        quad_count = 0
        tri_count = 0
        
        # Process quad elements - Fix the element structure handling
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
                    
                quad = vtkQuad()
                valid_element = True
                
                for i, nid in enumerate(node_ids):
                    if nid in node_id_to_idx:
                        quad.GetPointIds().SetId(i, node_id_to_idx[nid])
                    else:
                        print(f"Node {nid} from element {eid} not found in node map")
                        valid_element = False
                        break
                        
                if valid_element:
                    quad_cells.InsertNextCell(quad)
                    quad_count += 1
                    
                if quad_count % 1000 == 0:
                    print(f"Processed {quad_count} quad elements...")
            except Exception as e:
                print(f"Error processing quad element: {str(e)}")
        
        # Process triangular elements - Fix the element structure handling
        for elem in elements.get('CTRIA3', []):
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
                    print(f"Unsupported triangle element format: {type(elem)}")
                    continue
                    
                tri = vtkTriangle()
                valid_element = True
                
                for i, nid in enumerate(node_ids):
                    if nid in node_id_to_idx:
                        tri.GetPointIds().SetId(i, node_id_to_idx[nid])
                    else:
                        print(f"Node {nid} from element {eid} not found in node map")
                        valid_element = False
                        break
                        
                if valid_element:
                    tri_cells.InsertNextCell(tri)
                    tri_count += 1
                    
                if tri_count % 1000 == 0:
                    print(f"Processed {tri_count} triangle elements...")
            except Exception as e:
                print(f"Error processing triangle element: {str(e)}")
        
        print(f"Successfully processed {quad_count} quads and {tri_count} triangles")
        
        # Add cells to the grid - separate actors for different element types
        if quad_count > 0:
            #quad_grid = vtkUnstructuredGrid()
            quad_poly=vtk.vtkPolyData()
            quad_poly.SetPoints(points)
            #quad_grid.SetCells(VTK_QUAD, quad_cells)
            quad_poly.SetPolys(quad_cells)
            
            quad_mapper = vtkDataSetMapper()
            #quad_mapper.SetInputData(quad_grid)
            quad_mapper.SetInputData(quad_poly)
            
            quad_actor = vtkActor()
            quad_actor.SetMapper(quad_mapper)
            quad_actor.GetProperty().SetColor(0.8, 0.8, 0.8)  # Light gray
            quad_actor.GetProperty().SetEdgeVisibility(True)
            quad_actor.GetProperty().SetEdgeColor(0, 0, 0)  # Black edges
            quad_actor.GetProperty().SetPointSize(4)  # Larger points
            quad_actor.GetProperty().SetLineWidth(1.5)  # Thicker lines
            quad_actor.GetProperty().SetOpacity(0.7)  # Slightly transparent
            
            self.renderer.AddActor(quad_actor)
            
        if tri_count > 0:
            #tri_grid = vtkUnstructuredGrid()
            tri_poly=vtk.vtkPolyData()
            tri_poly.SetPoints(points)
            #tri_grid.SetCells(VTK_TRIANGLE, tri_cells)
            tri_poly.SetPolys(tri_cells)

            tri_mapper = vtkDataSetMapper()
            #tri_mapper.SetInputData(tri_grid)
            tri_mapper.SetInputData(tri_poly)
            
            tri_actor = vtkActor()
            tri_actor.SetMapper(tri_mapper)
            tri_actor.GetProperty().SetColor(0.9, 0.7, 0.7)  # Pinkish
            tri_actor.GetProperty().SetEdgeVisibility(True)
            tri_actor.GetProperty().SetEdgeColor(0, 0, 0)  # Black edges
            tri_actor.GetProperty().SetPointSize(4)  # Larger points
            tri_actor.GetProperty().SetLineWidth(1.5)  # Thicker lines
            tri_actor.GetProperty().SetOpacity(0.7)  # Slightly transparent
            
            self.renderer.AddActor(tri_actor)
        
        # If no elements were added, at least show the nodes
        if quad_count == 0 and tri_count == 0:
            point_grid = vtkUnstructuredGrid()
            point_grid.SetPoints(points)
            
            point_mapper = vtkDataSetMapper()
            point_mapper.SetInputData(point_grid)
            
            point_actor = vtkActor()
            point_actor.SetMapper(point_mapper)
            point_actor.GetProperty().SetColor(1.0, 0.0, 0.0)  # Red
            point_actor.GetProperty().SetPointSize(5)  # Large points
            point_actor.GetProperty().SetRenderPointsAsSpheres(True)  # Render as spheres
            
            self.renderer.AddActor(point_actor)
            print("No elements found, displaying points only")
        
        # Reset camera view and render the scene
        self.renderer.ResetCamera()
        
        # Force the render window to update
        self.vtkWidget.GetRenderWindow().Render()
        
        # Enable the interactor
        if self.iren and not self.iren.GetInitialized():
            print("Starting the interactor")
            self.iren.Start()
        
        self.has_rendered = True
        print("Rendering complete")
        
    def reset_view(self):
        """Reset the camera view"""
        if self.renderer:
            self.renderer.ResetCamera()
            self.vtkWidget.GetRenderWindow().Render()
        
    def closeEvent(self, event):
        """Handle cleanup when widget is closed"""
        if self.vtkWidget is not None:
            self.vtkWidget.Finalize()
        super().closeEvent(event)

    def __del__(self):
        """Clean up VTK objects"""
        if hasattr(self, 'vtkWidget'):
            self.vtkWidget.Finalize()