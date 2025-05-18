from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QPainter, QIcon
from PySide6.QtWidgets import (QMainWindow, QApplication, QDockWidget, QComboBox,
                              QTreeView, QTabWidget, QMenuBar, QStatusBar, QTreeWidget,
                              QWidget, QVBoxLayout, QPushButton, QLabel, QTreeWidgetItem,
                              QDialog, QFileDialog, QHBoxLayout, QLineEdit, QMessageBox, QSizePolicy)
from tinysizer.file import file_loader  # Import the file loader module
#from tinysizer.visualization.plotter import VTKMeshPlotter
from tinysizer.visualization.plotter_vista import PyVistaMeshPlotter

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        global WINDOW_HEIGHT,WINDOW_WIDTH
        WINDOW_HEIGHT,WINDOW_WIDTH=600,400
        self.setWindowTitle("TinySizer")
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT) #width, height
        
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
        self.bdf_input.setPlaceholderText("Select BDF file (mandatory)")
        bdf_button = QPushButton("Browse")
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
        self.op2_input.setPlaceholderText("Select OP2 file (optional)")
        op2_button = QPushButton("Browse")
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
        load_button.clicked.connect(self.validate_and_plot)
        
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
        
        self.tabs.addTab(main_tab, QIcon("tinysizer/gui/pics/home.png"), "Home")

    def browse_file(self, file_type):
        filename = file_loader.browse_file(self, file_type)
        if filename:
            if file_type == "BDF":
                self.bdf_input.setText(filename)
            else:
                self.op2_input.setText(filename)

    
    def validate_and_plot(self):
        model_data, load_status, error_message = file_loader.validate_and_load(
            self.bdf_input.text(), 
            self.op2_input.text()
        )
        
        if load_status == "only bdf":
            # Show success message
            QMessageBox.information(self, "Success", "BDF file loaded successfully!", QMessageBox.Ok)
            
            self.pyv_plotter.resize(self.pyv_plotter.size())
            
            # Update geometry view with loaded data
            # Note: We now pass the entire model_data object
            self.pyv_plotter.plot_mesh(model_data)

            # Enable tabs and switch to geometry
            for i in range(self.tabs.count()):
                self.tabs.setTabEnabled(i, True)
            self.tabs.currentChanged.connect(self.handle_tab_change)
            self.tabs.setCurrentIndex(1)  # change to geometry tab index 1
            self.error_label.hide()
            
            # Store model_data for later use in result selection
            self.model_data = model_data

        elif load_status == "both":
            # Show success message
            QMessageBox.information(self, "Success", "BDF & OP2 files loaded successfully!", QMessageBox.Ok)

            self.pyv_plotter.resize(self.pyv_plotter.size())
            
            # Update geometry view with loaded data - just show the model initially
            self.pyv_plotter.plot_mesh(model_data)
            
            # Populate result selection controls if they exist
            self.populate_result_controls(model_data)

            # Enable tabs and switch to geometry
            for i in range(self.tabs.count()):
                self.tabs.setTabEnabled(i, True)
            self.tabs.currentChanged.connect(self.handle_tab_change)
            self.tabs.setCurrentIndex(1)  # change to geometry tab index 1
            self.error_label.hide()
            
            # Store model_data for later use
            self.model_data = model_data

        else:
            QMessageBox.critical(self, "Error", error_message)
            #self.error_label.setText(error_message)
            #self.error_label.show()

            response = QMessageBox.question(self, "Random perhaps ?", "Do you want to load a random model to see something cool maybe ?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if response == QMessageBox.Yes:
                # Resize and update the plotter if necessary
                self.pyv_plotter.resize(self.pyv_plotter.size())

                # Call plot_something_random() to load a random model and display it
                self.pyv_plotter.plot_something_random()  # Call the method to plot a random model
                
                # Enable tabs and switch to the geometry tab (index 1)
                for i in range(self.tabs.count()):
                    self.tabs.setTabEnabled(i, True)
                
                # Connect the tab change event (this is optional depending on your needs)
                self.tabs.currentChanged.connect(self.handle_tab_change)
                self.tabs.setCurrentIndex(1)  # Switch to the geometry tab
                self.error_label.hide()

            else:
                pass

    def handle_tab_change(self, index):
        """Show/hide tree view based on current tab"""
        if index == 0:  # Main tab
            self.dock.hide()
        else:
            self.dock.show()

    def populate_result_controls(self, model_data):
        """Populate UI controls for result selection (if they exist)"""
        # Check if the necessary UI components exist
        if hasattr(self, 'result_type_combo') and hasattr(self, 'subcase_combo') and hasattr(self, 'component_combo'):
            # Clear existing items
            self.result_type_combo.clear()
            self.subcase_combo.clear()
            self.component_combo.clear()
            
            # Add available result types
            available_result_types = []
            for result_type in model_data.results:
                if model_data.results[result_type]:  # Only add types that have data
                    available_result_types.append(result_type)
                    
            self.result_type_combo.addItems(available_result_types)
            
            # Connect signals for updating dependent controls
            self.result_type_combo.currentTextChanged.connect(lambda: self.update_subcase_combo(model_data))
            self.subcase_combo.currentTextChanged.connect(lambda: self.update_component_combo(model_data))
            
            # Initial population of subcase combo
            if available_result_types:
                self.update_subcase_combo(model_data)

    def update_subcase_combo(self, model_data):
        """Update subcase combo based on selected result type"""
        if not hasattr(self, 'subcase_combo'):
            return
            
        self.subcase_combo.clear()
        
        result_type = self.result_type_combo.currentText()
        if not result_type:
            return
            
        subcases = model_data.get_available_subcases(result_type)
        self.subcase_combo.addItems([str(sc) for sc in subcases])
        
        # Update components as well
        if subcases:
            self.update_component_combo(model_data)

    def update_component_combo(self, model_data):
        """Update component combo based on selected result type and subcase"""
        if not hasattr(self, 'component_combo'):
            return
            
        self.component_combo.clear()
        
        result_type = self.result_type_combo.currentText()
        subcase_text = self.subcase_combo.currentText()
        
        if not result_type or not subcase_text:
            return
        
        try:
            subcase_id = int(subcase_text)
            components = model_data.get_available_components(result_type, subcase_id)
            
            # Add "Magnitude" option for displacement
            if result_type == "DISPLACEMENT":
                self.component_combo.addItem("Magnitude")
                
            self.component_combo.addItems(components)
        except ValueError:
            pass

    def display_result(self):
        """Display selected result"""
        if not hasattr(self, 'model_data'):
            QMessageBox.warning(self, "Warning", "No model data available!", QMessageBox.Ok)
            return
        
        result_type = self.result_type_combo.currentText()
        subcase_text = self.subcase_combo.currentText()
        component = self.component_combo.currentText()
        
        if not result_type or not subcase_text:
            QMessageBox.warning(self, "Warning", "Please select result type and subcase!", QMessageBox.Ok)
            return
        
        try:
            subcase_id = int(subcase_text)
            
            # Handle "Magnitude" special case
            if component == "Magnitude":
                component = None
                
            # Plot the mesh with the selected result
            self.pyv_plotter.plot_mesh(
                self.model_data,
                result_type=result_type,
                subcase_id=subcase_id,
                component=component
            )
            
        except ValueError:
            QMessageBox.warning(self, "Warning", "Invalid subcase ID!", QMessageBox.Ok)
            return
        
    #----------------------
    def create_geometry_tab(self):
        """Create geometry tab with VTK viewer"""
        geo_tab = QWidget()
        geo_tab.setMinimumSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        layout = QVBoxLayout(geo_tab)
        layout.setContentsMargins(0, 0, 0, 0)  # Reduce margins
        layout.setSpacing(5)  # Compact spacing
        
        #results
        # Add these to your UI setup
        self.result_type_combo = QComboBox()
        self.subcase_combo = QComboBox()
        self.component_combo = QComboBox()
        self.display_result_button = QPushButton("Display Result")
        self.display_result_button.clicked.connect(self.display_result)
        self.display_result_button.setObjectName("displayResultButton")  # for styling

        # Add them to your layout
        # Create VTK plotter with explicit size policy
        self.pyv_plotter = PyVistaMeshPlotter()
        self.pyv_plotter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.pyv_plotter.setMinimumHeight(400)  # Set a minimum height
        layout.addWidget(self.pyv_plotter, 1)  # The 1 gives this widget a stretch factor


        # having this portion at the instead of meshplotter
        controls = QHBoxLayout()
        
        left_controls = QHBoxLayout()
        left_controls.addWidget(self.display_result_button)
        left_controls.addWidget(QLabel("Result Type:"))
        left_controls.addWidget(self.result_type_combo)
        left_controls.addWidget(QLabel("Subcase:"))
        left_controls.addWidget(self.subcase_combo)
        left_controls.addWidget(QLabel("Component:"))
        left_controls.addWidget(self.component_combo)
        
        # Add left controls to main controls layout
        controls.addLayout(left_controls)
        controls.addStretch(1)  # Add stretch to center the buttons

        # Add a button to trigger rendering (helpful for debugging)
        refresh_btn = QPushButton()
        refresh_btn.setIcon(QIcon("tinysizer/gui/pics/refresh.png"))
        refresh_btn.setToolTip("Refresh View (R)")
        refresh_btn.setFixedSize(32, 32)  # Set a fixed size for the button
        refresh_btn.clicked.connect(self.refresh_geometry_view)
        controls.addWidget(refresh_btn)
        
        # Add display options
        surface_btn = QPushButton()
        surface_btn.setIcon(QIcon("tinysizer/gui/pics/surface.png"))
        surface_btn.setToolTip("Surface (S)")
        surface_btn.setFixedSize(32, 32)
        surface_btn.clicked.connect(lambda: self.set_display_mode("surface"))
        controls.addWidget(surface_btn)

        wireframe_btn = QPushButton()
        wireframe_btn.setIcon(QIcon("tinysizer/gui/pics/wireframe.png"))
        wireframe_btn.setToolTip("Wireframe (W)")
        wireframe_btn.setFixedSize(32, 32)
        wireframe_btn.clicked.connect(lambda: self.set_display_mode("wireframe"))
        controls.addWidget(wireframe_btn)
        
        edges_btn = QPushButton()
        edges_btn.setIcon(QIcon("tinysizer/gui/pics/edges.png"))
        edges_btn.setToolTip("Edges")
        edges_btn.setFixedSize(32, 32)
        edges_btn.clicked.connect(lambda: self.set_display_mode("edges"))
        controls.addWidget(edges_btn)

        opacity_btn = QPushButton()
        opacity_btn.setIcon(QIcon("tinysizer/gui/pics/opacity.png"))
        opacity_btn.setToolTip("Opacity")
        opacity_btn.setFixedSize(32, 32)
        opacity_btn.clicked.connect(lambda: self.set_display_mode("opacity"))
        controls.addWidget(opacity_btn)

        controls.addStretch(0)  # Add stretch to center the buttons
        
        # Create a widget for the controls to overlay on the vtk_plotter
        controls_widget = QWidget()
        controls_widget.setLayout(controls)
        controls_widget.setMaximumHeight(50)  # Limit the height of the controls
        
        # Add the controls at the bottom
        layout.addWidget(controls_widget)

        self.tabs.addTab(geo_tab, QIcon("tinysizer/gui/pics/tab_aircraft2.png"), "Geometry")
        return geo_tab  # Return the tab for reference if needed

    def set_display_mode(self, mode):
        """Set the display mode for the geometry visualization"""
        actors = self.pyv_plotter.plotter.renderer.GetActors()
        if mode == "wireframe":
            if actors.GetNumberOfItems() > 0:
                for i in range(actors.GetNumberOfItems()):
                    actor = actors.GetItemAsObject(i)
                    actor.GetProperty().SetRepresentationToWireframe()
                self.pyv_plotter.plotter.update()
        elif mode == "surface":
            if actors.GetNumberOfItems() > 0:
                for i in range(actors.GetNumberOfItems()):
                    actor = actors.GetItemAsObject(i)
                    actor.GetProperty().SetRepresentationToSurface()
                self.pyv_plotter.plotter.update()
        elif mode == "edges":
            actor = actors.GetItemAsObject(0)
            current_visibility = actor.GetProperty().GetEdgeVisibility()
            actor.GetProperty().SetEdgeVisibility(not current_visibility)
            self.pyv_plotter.plotter.update()
        elif mode == "opacity":
            #actor = actors.GetItemAsObject(0)
            actor = actors.GetItemAsObject(0)
            current_opacity = actor.GetProperty().GetOpacity()
            new_opacity = 1.0 if current_opacity == 0.5 else 0.5
            print(f"Opacity is set to {new_opacity}")
            actor.GetProperty().SetOpacity(new_opacity)
            self.pyv_plotter.plotter.update()

    def refresh_geometry_view(self):
        """Refresh/reset the geometry view"""
        if hasattr(self, 'pyv_plotter') and self.pyv_plotter is not None:
            print("Refreshing geometry view...")
            self.pyv_plotter.reset_view()
            # If rendering hasn't happened yet but data is available, force an update
            if not self.pyv_plotter.has_rendered:
                if not hasattr(self, 'pyv_plotter') or self.pyv_plotter is None:
                    print("VTK plotter not available")
                    return
                    
                if not hasattr(self.bdf_data, 'is_loaded') or not self.bdf_data.is_loaded:
                    print("No model data loaded")
                    return

    #---------------------------
    def create_sizing_tab(self):
        """Creates the analysis settings tab"""
        sizing_tab = QWidget()
        layout = QVBoxLayout(sizing_tab)
        layout.addWidget(QLabel("Sizing Settings"))
        self.tabs.addTab(sizing_tab, QIcon("tinysizer/gui/pics/sizing.png"), "Sizing")

    def create_utils_tab(self):
        """Creates the results visualization tab"""
        utils_tab = QWidget()
        layout = QVBoxLayout(utils_tab)
        layout.addWidget(QLabel("Utilities Viewer"))
        self.tabs.addTab(utils_tab, QIcon("tinysizer/gui/pics/utils.png"), "Utils")

    def create_export_tab(self):
        mesh_tab=QWidget()
        layout=QVBoxLayout(mesh_tab)
        layout.addWidget(QLabel("Export stuff"))
        self.tabs.addTab(mesh_tab, QIcon("tinysizer/gui/pics/export.png"), "Export")

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

