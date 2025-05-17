from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QPainter, QIcon
from PySide6.QtWidgets import (QMainWindow, QApplication, QDockWidget, 
                              QTreeView, QTabWidget, QMenuBar, QStatusBar, QTreeWidget,
                              QWidget, QVBoxLayout, QPushButton, QLabel, QTreeWidgetItem,
                              QDialog, QFileDialog, QHBoxLayout, QLineEdit, QMessageBox, QSizePolicy)
from tinysizer.file import file_loader  # Import the file loader module
from tinysizer.visualization.plotter import VTKMeshPlotter
from tinysizer.file.file_loader import BDFData

class FileInputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Input Files")
        self.setModal(True)
        
        # Set window flags to make parent window grayed out
        self.setWindowFlags(self.windowFlags() | Qt.CustomizeWindowHint | Qt.WindowStaysOnTopHint)
        
        layout = QVBoxLayout(self)
        
        # BDF file selection
        bdf_layout = QHBoxLayout()
        self.bdf_input = QLineEdit()
        self.bdf_input.setPlaceholderText("Select BDF file...")
        bdf_button = QPushButton("Browse")
        bdf_button.clicked.connect(lambda: self.browse_file("BDF"))
        bdf_layout.addWidget(QLabel("BDF File:"))
        bdf_layout.addWidget(self.bdf_input)
        bdf_layout.addWidget(bdf_button)
        
        # OP2 file selection
        op2_layout = QHBoxLayout()
        self.op2_input = QLineEdit()
        self.op2_input.setPlaceholderText("Select OP2 file...")
        op2_button = QPushButton("Browse")
        op2_button.clicked.connect(lambda: self.browse_file("OP2"))
        op2_layout.addWidget(QLabel("OP2 File:"))
        op2_layout.addWidget(self.op2_input)
        op2_layout.addWidget(op2_button)
        
        # Button layout for OK and Cancel
        button_layout = QHBoxLayout()
        
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        
        # Add all to main layout
        layout.addLayout(bdf_layout)
        layout.addLayout(op2_layout)
        layout.addLayout(button_layout)
        
        # Validate input before allowing OK
        ok_button.setEnabled(False)
        self.bdf_input.textChanged.connect(lambda: self.validate_inputs(ok_button))
        self.op2_input.textChanged.connect(lambda: self.validate_inputs(ok_button))
    
    def browse_file(self, file_type):
        file_filter = "BDF files (*.bdf);;All files (*.*)" if file_type == "BDF" else "OP2 files (*.op2);;All files (*.*)"
        filename, _ = QFileDialog.getOpenFileName(self, f"Select {file_type} File", "", file_filter)
        if filename:
            if file_type == "BDF":
                self.bdf_input.setText(filename)
            else:
                self.op2_input.setText(filename)
    
    def get_files(self):
        return self.bdf_input.text(), self.op2_input.text()

    def validate_inputs(self, ok_button):
        """Enable OK button only if both files are selected"""
        ok_button.setEnabled(bool(self.bdf_input.text() and self.op2_input.text()))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        global WINDOW_HEIGHT,WINDOW_WIDTH
        WINDOW_HEIGHT,WINDOW_WIDTH=800,1200
        self.setWindowTitle("TinySizer")
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        
        #stylsheet
        load_stylesheet = lambda path: open(path, "r").read()
        self.setStyleSheet(load_stylesheet("tinysizer/gui/styles/dark_theme.qss"))
        
        # Create central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Create tab widget
        self.tabs = QTabWidget()
        layout = QVBoxLayout(self.central_widget)
        layout.addWidget(self.tabs)
        
        # Create all tabs but only enable Main initially
        self.create_main_tab()
        self.create_geometry_tab()
        self.create_sizing_tab()
        self.create_utils_tab()
        self.create_export_tab()

        # Create but hide model tree initially
        self.dock = self.create_model_tree()
        self.dock.hide()
        
        # Disable all tabs except Main
        for i in range(1, self.tabs.count()):
            self.tabs.setTabEnabled(i, False)

    def create_main_tab(self):
        main_tab = QWidget()
        main_layout = QHBoxLayout(main_tab)
        main_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins around main layout
        
        # Create error label first
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: red")
        self.error_label.hide()
        
        # Left side - placeholder image (matching tree view dimensions)
        PIC_WIDTH=310
        image_label = QLabel()
        image_label.setMinimumWidth(250)  # Match typical tree view width
        image_label.setFixedWidth(PIC_WIDTH)    # Fix the width
        try:
            pixmap = QPixmap("tinysizer/gui/pics/placeholder3.png")
            if pixmap.isNull():
                raise FileNotFoundError("Could not load image")
        except:
            # Create a default colored rectangle if image loading fails
            pixmap = QPixmap(PIC_WIDTH, WINDOW_HEIGHT)  # Match window height
            pixmap.fill(Qt.white)
            
            # Draw text on the blank pixmap
            painter = QPainter(pixmap)
            painter.drawText(pixmap.rect(), Qt.AlignCenter, "TinySizer FEA")
            painter.end()
        
        # Scale pixmap to fit the height while maintaining width
        #scaled_pixmap = pixmap.scaled(PIC_WIDTH, 800, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        scaled_pixmap = pixmap.scaled(PIC_WIDTH, WINDOW_HEIGHT, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        image_label.setPixmap(scaled_pixmap)
        image_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        # Right side content wrapper with margins
        right_widget = QWidget()
        right_widget.setContentsMargins(20, 20, 20, 20)  # Add margins around content
        right_layout = QVBoxLayout(right_widget)
        
        # File inputs group
        file_group = QVBoxLayout()
        
        # BDF file selection with fixed width
        bdf_layout = QHBoxLayout()
        bdf_label = QLabel("BDF File:")
        bdf_label.setFixedWidth(60)  # Fix the label width
        self.bdf_input = QLineEdit()
        self.bdf_input.setMinimumWidth(300)
        self.bdf_input.setPlaceholderText("Select BDF file...")
        bdf_button = QPushButton("Browse BDF")
        bdf_button.setFixedWidth(100)
        bdf_button.clicked.connect(lambda: self.browse_file("BDF"))  # Add this line
        bdf_layout.addWidget(bdf_label)
        bdf_layout.addWidget(self.bdf_input, 1)
        bdf_layout.addWidget(bdf_button)
        
        # OP2 file selection with fixed width
        op2_layout = QHBoxLayout()
        op2_label = QLabel("OP2 File:")
        op2_label.setFixedWidth(60)  # Fix the label width
        self.op2_input = QLineEdit()
        self.op2_input.setMinimumWidth(300)  # Set minimum width instead of fixed
        self.op2_input.setPlaceholderText("Select OP2 file...")
        op2_button = QPushButton("Browse OP2")
        op2_button.setFixedWidth(100)  # Fix button width
        op2_button.clicked.connect(lambda: self.browse_file("OP2"))
        op2_layout.addWidget(op2_label)
        op2_layout.addWidget(self.op2_input, 1)  # Add stretch factor 1
        op2_layout.addWidget(op2_button)
        
        file_group.addLayout(bdf_layout)
        file_group.addLayout(op2_layout)
        
        # Add spacing after file inputs
        file_group.addSpacing(10)
        
        # Button layout with Load and Quit
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        quit_button = QPushButton("Quit")
        quit_button.setFixedWidth(100)
        quit_button.clicked.connect(self.close)
        
        load_button = QPushButton("Load Files")
        load_button.setFixedWidth(100)
        load_button.clicked.connect(self.validate_and_load_files)
        
        button_layout.addWidget(quit_button)
        button_layout.addWidget(load_button)
        
        # Welcome text section with large spacing above
        welcome_layout = QVBoxLayout()
        welcome_layout.addSpacing(50)  # Large gap before welcome text
        
        welcome_label = QLabel(
            "Welcome to TinySizer Alpha v1.0\n\n"
            'Contrary to popular belief, Lorem Ipsum is not simply random text. It has roots in a piece of classical Latin literature from 45 BC, making it over 2000 years old. Richard McClintock, a Latin professor at Hampden-Sydney College in Virginia, looked up one of the more obscure Latin words, consectetur, from a Lorem Ipsum passage, and going through the cites of the word in classical literature, discovered the undoubtable source. Lorem Ipsum comes from sections 1.10.32 and 1.10.33 of "de Finibus Bonorum et Malorum" (The Extremes of Good and Evil) by Cicero, written in 45 BC. This book is a treatise on the theory of ethics, very popular during the Renaissance. The first line of Lorem Ipsum, "Lorem ipsum dolor sit amet..", comes from a line in section 1.10.32.'
        )
        welcome_label.setStyleSheet("font-size: 10pt;")
        welcome_label.setAlignment(Qt.AlignLeft)
        welcome_label.setWordWrap(True)  # Enable word wrap
        welcome_label.setFixedWidth(800)  # Set fixed width
        welcome_layout.addWidget(welcome_label)
        welcome_layout.addSpacing(30)

        updates_label = QLabel(
            "Latest Updates:\n"
            "• Added BDF/OP2 file support\n"
            "• Improved visualization capabilities\n"
            "• Enhanced geometry handling"
        )
        updates_label.setStyleSheet("font-size: 10pt;")
        updates_label.setAlignment(Qt.AlignLeft)
        welcome_layout.addWidget(updates_label)
        welcome_layout.addStretch()
        
        # Create a container for the main content (everything except copyright)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add all content to content layout
        content_layout.addLayout(file_group)
        content_layout.addLayout(button_layout)
        content_layout.addWidget(self.error_label)
        content_layout.addLayout(welcome_layout)
        content_layout.addStretch(1)  # Push everything up
        
        # Create copyright container
        copyright_container = QWidget()
        copyright_layout = QHBoxLayout(copyright_container)
        copyright_layout.setContentsMargins(0, 0, 0, 0) #l,t,r,b
        
        copyright_label = QLabel("© 2025 TinySizer. All rights reserved.")
        copyright_label.setStyleSheet("""
            color: gray;
            font-size: 8pt;
        """)
        copyright_layout.addStretch(1)
        copyright_layout.addWidget(copyright_label)
        
        # Add content and copyright to main right layout
        right_layout.addWidget(content_widget, 1)  # Give it stretch factor
        right_layout.addWidget(copyright_container, 0)  # No stretch
        
        # Add both layouts to main layout
        main_layout.addWidget(right_widget, 1)  # No stretch for image
        main_layout.addWidget(image_label, 0)  # Stretch factor 1 for content
        
        self.tabs.addTab(main_tab, QIcon("tinysizer/gui/pics/tab_aircraft.ico"), "Main")

    def browse_file(self, file_type):
        filename = file_loader.browse_file(self, file_type)
        if filename:
            if file_type == "BDF":
                self.bdf_input.setText(filename)
            else:
                self.op2_input.setText(filename)

    def initialize_vtk_view(self):
        """Initialize the VTK view after the widget has been shown"""
        if hasattr(self, 'vtk_plotter') and self.vtk_plotter is not None:
            # Force a resize event to ensure the VTK widget updates its size
            self.vtk_plotter.resize(self.vtk_plotter.size())
            print("VTK view initialized with size:", 
                  self.vtk_plotter.size().width(), 
                  self.vtk_plotter.size().height())
            
            # If we already have data, render it
            if hasattr(self, 'bdf_data') and hasattr(self.bdf_data, 'is_loaded') and self.bdf_data.is_loaded:
                print("Rendering existing model data")
                self.update_geometry_view()

    def validate_and_load_files(self):
        bdf_data, success, error_message = file_loader.validate_and_load_files(
            self.bdf_input.text(), 
            self.op2_input.text()
        )
        
        if success:
            # Show success message
            QMessageBox.information(self, "Success", "Files loaded successfully!", QMessageBox.Ok)
            
            self.vtk_plotter.resize(self.vtk_plotter.size())
            
            # Update geometry view with loaded data
            self.vtk_plotter.plot_mesh(
                bdf_data.nodes,
                bdf_data.elements
            )
            
            # Enable tabs and switch to geometry
            for i in range(self.tabs.count()):
                self.tabs.setTabEnabled(i, True)
            self.tabs.currentChanged.connect(self.handle_tab_change)
            self.tabs.setCurrentIndex(1) #change to geometry tab index 1
            self.error_label.hide()
        else:
            self.error_label.setText(error_message)
            self.error_label.show()

    def handle_tab_change(self, index):
        """Show/hide tree view based on current tab"""
        if index == 0:  # Main tab
            self.dock.hide()
        else:
            self.dock.show()

    #----------------------
    def create_geometry_tab(self):
        """Create geometry tab with VTK viewer"""
        geo_tab = QWidget()
        geo_tab.setMinimumSize(800, 600)
        layout = QVBoxLayout(geo_tab)
        layout.setContentsMargins(0, 0, 0, 0)  # Reduce margins
        layout.setSpacing(5)  # Compact spacing
        
        # Add controls
        controls = QHBoxLayout()
        #controls.addWidget(QLabel("Geometry Controls"))
        controls.addWidget(QWidget())

        # Add a button to trigger rendering (helpful for debugging)
        refresh_btn = QPushButton("Refresh View")
        refresh_btn.clicked.connect(self.refresh_geometry_view)
        controls.addWidget(refresh_btn)

        # Add display options
        wireframe_btn = QPushButton("Wireframe")
        wireframe_btn.clicked.connect(lambda: self.set_display_mode("wireframe"))
        controls.addWidget(wireframe_btn)

        surface_btn = QPushButton("Surface")
        surface_btn.clicked.connect(lambda: self.set_display_mode("surface"))
        controls.addWidget(surface_btn)

        # Add stretch to keep controls aligned left
        controls.addStretch(1)  
        layout.addLayout(controls)
        
        # Create VTK plotter with explicit size policy
        self.vtk_plotter = VTKMeshPlotter()
        self.vtk_plotter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.vtk_plotter.setMinimumHeight(400)  # Set a minimum height
        layout.addWidget(self.vtk_plotter, 1)  # The 1 gives this widget a stretch factor

        # Ensure rendering happens after the widget is shown
        #QTimer.singleShot(100, self.initialize_vtk_view)
        
        self.tabs.addTab(geo_tab, QIcon("tinysizer/gui/pics/tab_aircraft.ico"), "Geometry")
        return geo_tab  # Return the tab for reference if needed

    def set_display_mode(self, mode):
        """Set the display mode for the geometry"""
        if hasattr(self, 'vtk_plotter') and self.vtk_plotter is not None:
            if mode == "wireframe":
                for actor in self.vtk_plotter.renderer.GetActors():
                    actor.GetProperty().SetRepresentationToWireframe()  # Enable wireframe mode
            elif mode == "surface":
                for actor in self.vtk_plotter.renderer.GetActors():
                    actor.GetProperty().SetRepresentationToSurface()  # Render as solid surfaces
            else:
                for actor in self.vtk_plotter.renderer.GetActors():
                    actor.GetProperty().SetRepresentationToSurface()  # Render as solid surfaces
            self.vtk_plotter.vtkWidget.GetRenderWindow().Render()

    def refresh_geometry_view(self):
        """Refresh/reset the geometry view"""
        if hasattr(self, 'vtk_plotter') and self.vtk_plotter is not None:
            print("Refreshing geometry view...")
            self.vtk_plotter.reset_view()
            # If rendering hasn't happened yet but data is available, force an update
            if not self.vtk_plotter.has_rendered:
                self.update_geometry_view()

    def update_geometry_view(self):
        """Update the geometry view with the current model data"""
        print("Updating geometry view...")
        if not hasattr(self, 'vtk_plotter') or self.vtk_plotter is None:
            print("VTK plotter not available")
            return
            
        if not hasattr(bdf_data, 'is_loaded') or not bdf_data.is_loaded:
            print("No model data loaded")
            return

    #---------------------------
    def create_sizing_tab(self):
        """Creates the analysis settings tab"""
        sizing_tab = QWidget()
        layout = QVBoxLayout(sizing_tab)
        layout.addWidget(QLabel("Sizing Settings"))
        self.tabs.addTab(sizing_tab, QIcon("tinysizer/gui/pics/tab_aircraft.ico"), "Sizing")

    def create_utils_tab(self):
        """Creates the results visualization tab"""
        utils_tab = QWidget()
        layout = QVBoxLayout(utils_tab)
        layout.addWidget(QLabel("Utilities Viewer"))
        self.tabs.addTab(utils_tab, QIcon("tinysizer/gui/pics/tab_aircraft.ico"), "Utils")

    def create_export_tab(self):
        mesh_tab=QWidget()
        layout=QVBoxLayout(mesh_tab)
        layout.addWidget(QLabel("Export stuff"))
        self.tabs.addTab(mesh_tab, QIcon("tinysizer/gui/pics/tab_aircraft.ico"), "Export")

    def create_model_tree(self):
        """Creates dockable model tree widget"""
        dock = QDockWidget("Model Tree", self)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        
        # Set all dock widget features in one place
        dock.setFeatures(
            QDockWidget.DockWidgetFloatable | 
            QDockWidget.DockWidgetMovable | 
            QDockWidget.DockWidgetClosable
        )
        
        tree = QTreeWidget()
        tree.setHeaderLabel("Structure name")
        tree.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        tree.setMinimumWidth(250)
        
        # Add some example items
        geometry = QTreeWidgetItem(["Geometry"])
        geometry.addChild(QTreeWidgetItem(["Parts"]))
        geometry.addChild(QTreeWidgetItem(["Assemblies"]))
        
        mesh = QTreeWidgetItem(["Mesh"])
        mesh.addChild(QTreeWidgetItem(["Elements"]))
        mesh.addChild(QTreeWidgetItem(["Nodes"]))
        
        loads = QTreeWidgetItem(["Loads & BCs"])
        loads.addChild(QTreeWidgetItem(["Forces"]))
        loads.addChild(QTreeWidgetItem(["Constraints"]))
        
        tree.addTopLevelItems([geometry, mesh, loads])
        tree.expandAll()
        
        dock.setWidget(tree)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)
        
        return dock

