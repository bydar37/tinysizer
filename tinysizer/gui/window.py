
import os
import numpy as np
from tinysizer.file import file_loader  # Import the file loader module
from tinysizer.visualization.plotter_vista import PyVistaMeshPlotter
from tinysizer.gui.sizing_tab import SizingTab
from tinysizer.gui.assembly import AssemblyDialog  
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QPainter, QIcon, QAction, QFont
from PySide6.QtWidgets import (QMainWindow, QApplication, QDockWidget, QComboBox, QTableWidget,
                              QTreeView, QTabWidget, QMenuBar, QStatusBar, QTreeWidget, QTableWidgetItem,
                              QWidget, QVBoxLayout, QPushButton, QLabel, QTreeWidgetItem, QToolBar,
                              QDialog, QFileDialog, QHBoxLayout, QLineEdit, QMessageBox, QSizePolicy,
                              QColorDialog,QMenu,QFrame)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        global WINDOW_HEIGHT,WINDOW_WIDTH
        WINDOW_HEIGHT,WINDOW_WIDTH=600,1200
        self.setWindowTitle("TinySizer")
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT) #width, height
        self.center_on_screen() # helper function, merkezliyor pencereyi -ymn
        self.model_data=None
        self.assembly_properties=None
        self.assemblies = {}  # Dictionary to store assemblies
        
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

        # Create but hide model tree initially
        self.dock = self.create_model_tree()
        self.dock.hide()
        
        # Initialize sizing tab but don't add it yet
        self.sizing_tab = SizingTab(parent=self)
        self.add_and_update_sizing_tab()

        self.create_utils_tab()
        self.create_export_tab()
        self.setup_tab_change_handler() #isme göre tree-dock getirmek icin, bu durumda sadece "geometry" icin geliyor -ymn

        # Disable all tabs except Main
        for i in range(1, self.tabs.count()):
            self.tabs.setTabEnabled(i, False)


    #########################################
    # T A B S
    #########################################
    def create_main_tab(self):
        #same code here
        main_tab = QWidget()
        main_layout = QHBoxLayout(main_tab)
        main_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins around main layout
        
        # Create error label first
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: red")
        self.error_label.hide()
        
        # make the menu bar
        self.create_menu_bar()

        # Left side - placeholder image (matching tree view dimensions)
        PIC_WIDTH=310
        image_label = QLabel()
        image_label.setMinimumWidth(0)
        image_label.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        image_label.setScaledContents(True) # STRETCHHHHHHHHHHHHHH
        
        try:
            pixmap = QPixmap("tinysizer/gui/pics/placeholder3.png")
            if pixmap.isNull():
                raise FileNotFoundError("Could not load image")
        except:
            # Create a default colored rectangle
            pixmap = QPixmap(PIC_WIDTH, WINDOW_HEIGHT)
            pixmap.fill(Qt.white)
                    
        # Draw text on the blank pixmap
        painter = QPainter(pixmap)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "")
        painter.end()
    
        # Initial scaling with aspect ratio maintained -> redundant oldugu söyleniyor ama height sacmalamadan bunu kaldiramadim -ymn
        scaled_pixmap = pixmap.scaled(
            PIC_WIDTH, WINDOW_HEIGHT, 
            Qt.IgnoreAspectRatio,  # Maintain aspect ratio
            Qt.SmoothTransformation
        )
        
        image_label.setPixmap(scaled_pixmap)
        image_label.setAlignment(Qt.AlignCenter)  # Center alignment for right-side image

        '''
        scaled_pixmap = pixmap.scaled(PIC_WIDTH, WINDOW_HEIGHT, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        image_label.setPixmap(scaled_pixmap)
        image_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        '''
        
        # Right side content wrapper with margins
        right_widget = QWidget()
        right_widget.setContentsMargins(20, 20, 20, 20)  # Add margins around content
        right_layout = QVBoxLayout(right_widget)
        
        # File inputs group
        file_group = QVBoxLayout()
        
        # BDF file selection with fixed width
        bdf_layout = QHBoxLayout()
        bdf_label = QLabel("BDF File:")
        bdf_label.setMinimumWidth(60)  # Fix the label width
        self.bdf_input = QLineEdit()
        self.bdf_input.setMinimumWidth(100)
        self.bdf_input.setPlaceholderText("Select BDF file (mandatory)")
        bdf_button = QPushButton("Browse")
        bdf_button.setMinimumWidth(60)
        bdf_button.clicked.connect(lambda: self.browse_file("BDF"))  # Add this line
        bdf_layout.addWidget(bdf_label)
        bdf_layout.addWidget(self.bdf_input, 1)
        bdf_layout.addWidget(bdf_button)
        
        # OP2 file selection with fixed width
        op2_layout = QHBoxLayout()
        op2_label = QLabel("OP2 File:")
        op2_label.setMinimumWidth(60)  # Fix the label width
        self.op2_input = QLineEdit()
        self.op2_input.setMinimumWidth(100)  # Set minimum width instead of fixed
        self.op2_input.setPlaceholderText("Select OP2 file (optional)")
        op2_button = QPushButton("Browse")
        op2_button.setMinimumWidth(60)  # Fix button width
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
        quit_button.setMinimumWidth(60)
        quit_button.clicked.connect(self.close)
        
        load_button = QPushButton("Load Files")
        load_button.setMinimumWidth(60)
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
        welcome_label.setMinimumWidth(WINDOW_WIDTH*0.4)  # Set fixed width
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
        main_layout.addWidget(image_label, 0)  # Fixed size for image
        main_layout.addWidget(right_widget, 1)  # Expandable content
        
        self.tabs.addTab(main_tab, QIcon("tinysizer/gui/pics/home.png"), "Home")


    def create_menu_bar(self):
        #same code here
        menu_bar=self.menuBar()

        # File Menu
        file_menu = menu_bar.addMenu("File")
        open_action = QAction("Open BDF", self)
        #open_action.triggered.connect(self.load_bdf_file)
        file_menu.addAction(open_action)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View Menu
        view_menu = menu_bar.addMenu("View")
        reset_view_action = QAction("Reset View", self)
        reset_view_action.triggered.connect(lambda: self.pyv_plotter.plotter.reset_camera())
        view_menu.addAction(reset_view_action)

        # Help Menu
        help_menu = menu_bar.addMenu("Help")
        shortcuts_action = QAction("Shortcuts", self)
        shortcuts_action.triggered.connect(self.show_shortcuts)
        help_menu.addAction(shortcuts_action)
        
        # Help Menu
        about_menu = menu_bar.addMenu("About")
        contact_action = QAction("Contact", self)
        #about_menu.triggered.connect(self.show_shortcuts)
        about_menu.addAction(contact_action)

    def create_geometry_tab(self):
        #same code here
        """Create geometry tab with VTK viewer"""
        geo_tab = QWidget()
        geo_tab.setMinimumSize(WINDOW_WIDTH * 0.5, WINDOW_HEIGHT * 0.5)
        layout = QVBoxLayout(geo_tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Results controls
        self.result_type_combo = QComboBox()
        self.subcase_combo = QComboBox()
        self.component_combo = QComboBox()
        self.display_result_button = QPushButton("Display Result")
        self.display_result_button.clicked.connect(self.display_result)
        self.display_result_button.setObjectName("displayResultButton")  # for styling

        # VTK plotter setup
        self.pyv_plotter = PyVistaMeshPlotter()
        self.pyv_plotter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.pyv_plotter.setMinimumHeight(400)
        layout.addWidget(self.pyv_plotter, 1)

        # Buttons info for both rows
        buttons_info = [
            ("Refresh", "tinysizer/gui/pics/refresh.png", self.refresh_geometry_view),
            ("Surface", "tinysizer/gui/pics/surface.png", lambda: self.set_display_mode("surface")),
            ("Wireframe", "tinysizer/gui/pics/wireframe.png", lambda: self.set_display_mode("wireframe")),
            ("Edges", "tinysizer/gui/pics/edges.png", lambda: self.set_display_mode("edges")),
            ("Opacity", "tinysizer/gui/pics/opacity.png", lambda: self.set_display_mode("opacity")),
            ("Shortcuts", "tinysizer/gui/pics/shortcuts2.png", lambda: self.show_shortcuts()),
            ("Placeholder", "tinysizer/gui/pics/edges.png", lambda: None)
        ]

        # === TOP ROW (small buttons) ===
        top_controls = QHBoxLayout()
        #top_controls.setContentsMargins(10 + self.display_result_button.sizeHint().width(), 0, 0, 0)
        top_controls.setContentsMargins(10,2,10,2)
        top_controls.setSpacing(0)

        # Create a QWidget container for top_controls to set the objectName
        top_controls_widget = QWidget()
        top_controls_widget.setObjectName("topControlsLayout")
        top_controls_widget.setLayout(top_controls)
        
        colorize_btn = QPushButton()
        colorize_btn.setIcon(QIcon("tinysizer/gui/pics/colorful.ico"))
        colorize_btn.setToolTip("Colorize")
        colorize_btn.setFixedSize(24, 24)
        colorize_btn.clicked.connect(lambda: self.pyv_plotter.colorize_by_property(self.model_data))
        top_controls.addWidget(colorize_btn)

        n=[7]
        # Split buttons into 3 groups of 6
        import random
        for group_idx in range(5):
            for i in range(1,random.choice(n),1):
                text, icon_path, callback = buttons_info[-1]
                btn = QPushButton()
                btn.setIcon(QIcon(icon_path))
                btn.setToolTip(text)
                btn.setFixedSize(24, 24)
                btn.clicked.connect(callback)
                top_controls.addWidget(btn)
            
            # Add some spacing between groups except after last group
            if group_idx < 4:
                top_controls.addSpacing(50)  # Adjust spacing as you want

        top_controls.addStretch(1)
        layout.addWidget(top_controls_widget)

        #---SEPERATOR
        separator = QFrame()
        separator.setObjectName("fadeSeparator")
        separator.setFrameShape(QFrame.HLine)
        separator.setFixedHeight(1)  # Set to 1–3 px for best results
        separator.setContentsMargins(0, 5, 0, 0)  # Left, Top, Right, Bottom
        layout.addWidget(separator)

        # === BOTTOM ROW (original bigger buttons + combos) ===
        controls = QHBoxLayout()

        left_controls = QHBoxLayout()
        left_controls.addWidget(self.display_result_button)
        left_controls.addWidget(QLabel("Result Type:"))
        left_controls.addWidget(self.result_type_combo)
        left_controls.addWidget(QLabel("Subcase:"))
        left_controls.addWidget(self.subcase_combo)
        left_controls.addWidget(QLabel("Component:"))
        left_controls.addWidget(self.component_combo)

        controls.addLayout(left_controls)
        controls.addStretch(1)  # Center spacing

        # Add bigger icon buttons in bottom row
        for text, icon_path, callback in buttons_info[:-1]:
            btn = QPushButton()
            btn.setIcon(QIcon(icon_path))
            btn.setToolTip(text)
            btn.setFixedSize(32, 32)  # original size on bottom row
            btn.clicked.connect(callback)
            controls.addWidget(btn)

        controls.addStretch(0)
        controls.setContentsMargins(10, 5, 10, 10)  # Eliminate padding around layout
        controls.setSpacing(5)  # Or 0 if you want zero spacing between buttons
        controls_widget = QWidget()
        controls_widget.setLayout(controls)
        controls_widget.setMaximumHeight(50)

        layout.addWidget(controls_widget)

        self.tabs.addTab(geo_tab, QIcon("tinysizer/gui/pics/tab_aircraft2.png"), "Geometry")
        return geo_tab

    '''
    def create_sizing_tab(self):
        """Creates the analysis settings tab"""
        sizing_tab = QWidget()
        layout = QVBoxLayout(sizing_tab)
        layout.addWidget(QLabel("Sizing Settings"))
        self.tabs.addTab(sizing_tab, QIcon("tinysizer/gui/pics/sizing.png"), "Sizing")
        sizing_tab.setContentsMargins(0, 0, 0, 0)  # Remove margins around main layout
    '''
    def create_utils_tab(self):
        """Creates the results visualization tab"""
        utils_tab = QWidget()
        layout = QVBoxLayout(utils_tab)

        placeholder_label = QLabel("TBD")
        placeholder_label.setAlignment(Qt.AlignCenter)
        placeholder_label.setStyleSheet("font-size: 14pt; color: gray;")
        layout.addWidget(placeholder_label)
        self.tabs.addTab(utils_tab, QIcon("tinysizer/gui/pics/utils.png"), "Utils")

    def create_export_tab(self):
        mesh_tab=QWidget()
        layout=QVBoxLayout(mesh_tab)

        placeholder_label = QLabel("TBD")
        placeholder_label.setAlignment(Qt.AlignCenter)
        placeholder_label.setStyleSheet("font-size: 14pt; color: gray;")
        layout.addWidget(placeholder_label)
        self.tabs.addTab(mesh_tab, QIcon("tinysizer/gui/pics/export.png"), "Export")


    #########################################
    # T R E E
    #########################################
    def create_model_tree(self):
        #same code here
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
        tree.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        tree.setMinimumWidth(250)
        tree.setHeaderHidden(True)

        #CONTEXT MENU-------------------
        tree.setContextMenuPolicy(Qt.CustomContextMenu)
        tree.customContextMenuRequested.connect(self.show_tree_context_menu)
    
        # Also handle regular clicks
        tree.itemClicked.connect(self.on_tree_item_clicked)

        # Store the tree and properties item as instance variables
        self.tree_widget = tree

        dock.setWidget(tree)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)
        
        return dock
    
    def populate_tree(self, model_data):
        """Clears and repopulates the model tree with fresh data"""

        self.tree_widget.clear() #her load ile stack up olmamasi icin temizliyoruz önce -ymn

        # Recreate top-level items
        self.properties_item = QTreeWidgetItem(["Properties"])
        self.assembly_item = QTreeWidgetItem(["Assemblies"])

        self.tree_widget.addTopLevelItems([self.properties_item, self.assembly_item])
        self.tree_widget.expandAll()

        # Populate new data under 'Properties'
        for property_type, property_ids in model_data.properties.items():
            type_item = QTreeWidgetItem([property_type])
            self.properties_item.addChild(type_item)

            property_ids_list=list(property_ids)
            property_ids_list.sort()
            for pid in property_ids_list:
                pid_item = QTreeWidgetItem([str(pid)])
                type_item.addChild(pid_item)

                # Store property ID for click handler
                pid_item.setData(0, Qt.UserRole, pid)


    def show_tree_context_menu(self, position):
        """Show context menu for tree items"""
        # Get the item at the clicked position
        item = self.tree_widget.itemAt(position)
        if not item:
            return
        
        # Get property ID if available
        property_id = item.data(0, Qt.UserRole)
        if not property_id:
            return  # No property ID stored in this item
        
        # Create context menu
        context_menu = QMenu()
        
        # Add actions and connect them directly
        isolate_action = context_menu.addAction("Isolate Elements")
        isolate_action.triggered.connect(lambda: self.isolate_elements_by_property(property_id))
        
        mask_action = context_menu.addAction("Mask Elements")
        mask_action.triggered.connect(lambda: self.mask_elements_by_property(property_id))
        
        color_action = context_menu.addAction("Color Elements")
        color_action.triggered.connect(lambda: self.handle_color_action(property_id))
        
        #reset_action = context_menu.addAction("Reset View")
        #reset_action.triggered.connect(self.pyv_plotter.reset_view)
        
        create_assembly_action = context_menu.addAction("Create Assembly")
        create_assembly_action.triggered.connect(self.create_assembly)
    
        # Just show the menu - no need to handle return value
        context_menu.exec_(self.tree_widget.mapToGlobal(position))

    def handle_color_action(self, property_id):
        """Handle color action separately"""
        from PySide6.QtWidgets import QColorDialog
        color = QColorDialog.getColor()
        if color.isValid():
            self.color_elements_by_property(property_id, color)

    def create_assembly(self):
        """Open the assembly creation dialog"""
        dialog = AssemblyDialog(parent=self)
        dialog.assembly_created.connect(self.on_assembly_created)
        dialog.exec_()

    '''
    def on_assembly_created(self, name, property_ids):
        """Handle when assembly is created"""
        print(f"Assembly '{name}' created with properties: {property_ids}")
        # Add your assembly logic here
        # For example:
        # if not hasattr(self, 'assemblies'):
        #     self.assemblies = {}
        # self.assemblies[name] = property_ids
    '''   

    def on_assembly_created(self, assembly_name, property_ids):
        """Handle the assembly creation"""
        # Store the assembly
       
        if assembly_name in self.assemblies.keys(): #THE GATE !!! -ymn     
            QMessageBox.critical(self, "Error", f"Assembly: {assembly_name} is already exist !")
            return
        
        self.assemblies[assembly_name] = property_ids
        self.sizing_tab.assembly_combo.currentTextChanged.connect(self.sizing_tab.update_property_combo)

        if hasattr(self, 'sizing_tab'):
            self.sizing_tab.update_assembly_combo()

        # Add to your properties tree under "Assembly" category
        self.add_assembly_to_tree(assembly_name, property_ids)
        
        text=f"Created assembly '{assembly_name}' with {len(property_ids)} properties"
        QMessageBox.information(self, "Success", text, QMessageBox.Ok)
        print(text)
        
    def add_assembly_to_tree(self, assembly_name, property_ids):
        """Add the new assembly to your properties tree"""
        # Find or create "Assembly" parent item
        #assembly_parent = self.find_or_create_assembly_parent()
        
        # Create new assembly item
        assembly_child = QTreeWidgetItem(self.assembly_item)
        assembly_child.setText(0, assembly_name)

        # Add property IDs as children (optional)
        for prop_id in property_ids:
            prop_item = QTreeWidgetItem(assembly_child)
            prop_item.setText(0, str(prop_id))
            
        # Expand the assembly parent
        self.assembly_item.setExpanded(True)
        
    def find_or_create_assembly_parent(self):
        """Find existing 'Assembly' parent or create new one"""
        root = self.tree_widget.invisibleRootItem()
        
        # Look for existing "Assembly" item
        for i in range(root.childCount()):
            child = root.child(i)
            if child.text(0) == "Assembly":
                return child
                
        # Create new "Assembly" parent if not found
        assembly_parent = QTreeWidgetItem(root)
        assembly_parent.setText(0, "Assembly")
        
        # Make it bold to distinguish as a category
        font = QFont()
        font.setBold(True)
        assembly_parent.setFont(0, font)
        
        return assembly_parent

    def isolate_elements_by_property(self, property_id):
        return None

    def mask_elements_by_property(self, property_id):
        return None

    def color_elements_by_property(self, property_id, color):
        if property_id in self.model_data.properties:
            for element in self.model_data.properties[property_id]:
                if hasattr(element, 'setBrush'):
                    from PySide6.QtGui import QBrush
                    element.setBrush(QBrush(color))

    def on_tree_item_clicked(self, item):
        """Handle clicks on tree items"""
        return None


    #########################################
    # R E A D  &  P L O T
    #########################################
    def validate_and_plot(self):
        model_data, load_status, error_message = file_loader.validate_and_load(
            self.bdf_input.text(), 
            self.op2_input.text()
        )
        
        # sadece bdf verildiyse
        if load_status == "only bdf":
            # Show success message
            QMessageBox.information(self, "Success", "BDF file loaded successfully!", QMessageBox.Ok)
            
            self.pyv_plotter.resize(self.pyv_plotter.size())
            
            # Update geometry view with loaded data
            # Note: We now pass the entire model_data object
            self.pyv_plotter.plot_mesh(model_data)
            self.populate_tree(model_data)
            
            # Enable tabs and switch to geometry
            for i in range(self.tabs.count()):
                self.tabs.setTabEnabled(i, True)
            self.tabs.currentChanged.connect(self.handle_tab_change)
            self.tabs.setCurrentIndex(1)  # change to geometry tab index 1
            self.error_label.hide()
            
            # Store model_data for later use in result selection
            self.model_data = model_data
            
            # Add sizing tab if it doesn't exist and update it with model data
            self.add_and_update_sizing_tab()

        # bdf ve op2 verildiyse
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
            
            # Add sizing tab if it doesn't exist and update it with model data
            self.add_and_update_sizing_tab()

        # bdf ve op2 verilmediyse
        else:
            QMessageBox.critical(self, "Error", error_message)
            #self.error_label.setText(error_message)
            #self.error_label.show()

            response = QMessageBox.question(self, "Random perhaps ?", "Wanna see something cool maybe ?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

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
    
    def add_and_update_sizing_tab(self):
        """Add sizing tab if it doesn't exist and update it with model data"""
        # Check if sizing tab already exists
        sizing_tab_exists = False
        sizing_tab_index = -1
        
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == "Sizing":
                sizing_tab_exists = True
                sizing_tab_index = i
                break
        
        if not sizing_tab_exists:
            # Add the sizing tab
            self.tabs.insertTab(2, self.sizing_tab, QIcon("tinysizer/gui/pics/sizing.png"), "Sizing")
        
        # Update the sizing tab with model data
        self.sizing_tab.update_with_model_data(self.model_data)

    def populate_result_controls(self, model_data):
        #same code here
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

    def display_result(self):
        #same code here
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
            try: subcase_id = int(subcase_text)
            except:  subcase_id = subcase_text #thickness icin -ymn

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
    
    def update_subcase_combo(self, model_data):
        """Update subcase combo based on selected result type"""
        if not hasattr(self, 'subcase_combo'):
            return
            
        self.subcase_combo.clear()
        
        result_type = self.result_type_combo.currentText()
        if not result_type:
            return
            
        subcases = model_data.get_available_subcases(result_type)
        self.subcase_combo.addItems([str(sc) for sc in subcases]) #subcaseleri liste halinde ekrana getiriyor
        
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


    #########################################
    # B U T T O N S
    ########################################
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

    def show_shortcuts(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Shortcuts")
        dialog.resize(520, 300)
        dialog.setFixedWidth(520)
        dialog.setWindowIcon(QIcon("tinysizer/gui/pics/shortcuts2.png"))

        # Define the content of the dialog as key-description pairs
        shortcuts = [
            ('q', 'Close the rendering window'),
            ('f', 'Focus and zoom in on a point'),
            ('v', 'Isometric camera view'),
            ('w', 'Switch all datasets to a wireframe representation'),
            ('r', 'Reset the camera to view all datasets'),
            ('s', 'Switch all datasets to a surface representation'),
            ('shift+click or middle-click', 'Pan the rendering scene'),
            ('left-click', 'Rotate the rendering scene in 3D'),
            ('ctrl+click', 'Rotate the rendering scene in 2D (view-plane)'),
            ('mouse-wheel or right-click', 'Continuously zoom the rendering scene'),
            ('shift+s', 'Save a screenshot (only on BackgroundPlotter)'),
            ('shift+c', 'Enable interactive cell selection/picking'),
            ('up/down', 'Zoom in and out'),
            ('+/-', 'Increase/decrease the point size and line widths'),
            ('\n','\n') #daha iyisini bulana kadar en iyisi bu, evet -ymn
        ]

        # Create a layout for the dialog window
        layout = QVBoxLayout(dialog)

        # Add each shortcut as a row in the layout
        for key, description in shortcuts:
            row_layout = QHBoxLayout()

            # Create the key label (aligned to the left)
            key_label = QLabel(f"<b>{key}</b>")  # Make the key bold
            key_label.setFixedWidth(200)  # Ensures alignment
            row_layout.addWidget(key_label)

            # Create the description label (aligned to the right)
            description_label = QLabel(description)
            description_label.setWordWrap(True)  # Ensure the text wraps if necessary
            row_layout.addWidget(description_label)

            # Add the row layout to the main layout
            layout.addLayout(row_layout)

        # Add some margin to the content
        layout.setContentsMargins(10, 10, 10, 10) 

        # Create and center the Close button
        close_btn = QPushButton("Close", dialog)
        close_btn.clicked.connect(dialog.close)

        button_layout = QHBoxLayout()
        button_layout.addWidget(close_btn)
        button_layout.setAlignment(close_btn, Qt.AlignCenter)  # Center the button

        #layout.addStretch(1)  # Space between list and button
        layout.addLayout(button_layout)
        #dialog.setAttribute(Qt.WA_OpaquePaintEvent)  # Ensure smooth painting to avoid flickering
        dialog.exec_()


    #########################################
    # H E L P E R S
    #########################################
    def browse_file(self, file_type):
        filename = file_loader.browse_file(self, file_type)
        if filename:
            if file_type == "BDF":
                self.bdf_input.setText(filename)
            else:
                self.op2_input.setText(filename)

    def handle_tab_change(self, index): #diger tab change fonksiyonları ile conflict, kapattim -ymn
        return
        """Show/hide tree view based on current tab"""
        if index == 0:  # Main tab
            self.dock.hide()
        else:
            self.dock.show()

    def center_on_screen(self):
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)


    def setup_tab_change_handler(self):
        """Setup handler to show/hide tree dock based on active tab"""
        # Connect to your tab widget's currentChanged signal
        # Replace 'self.tabs' with your actual tab widget reference
        if hasattr(self, 'tabs'):
            self.tabs.currentChanged.connect(self.on_tab_changed)

    def on_tab_changed(self, index):
        """Handle tab change to show/hide tree dock"""
        if not hasattr(self, 'dock'):
            return
        
        # Get tab text
        tab_text = self.tabs.tabText(index)
        print(f"Changed to Tab: {tab_text}")
        
        if tab_text == "Geometry":
            print("geo tab")
            self.dock.show()
        else:
            print("other tab")
            self.dock.hide()
    '''
    def resizeEvent(self, event):
        super().resizeEvent(event)

        if (hasattr(self, 'image_label') and 
            hasattr(self, 'original_pixmap') and 
            self.tabs.currentIndex() == 0):
            
            # Calculate available dimensions
            tab_height = self.tabs.tabBar().height()
            margins = 10
            available_height = self.height() - tab_height - margins
            available_width = min(310, self.width() // 3)

            # Avoid unnecessary scaling if size hasn't changed
            current_pixmap = self.image_label.pixmap()
            if current_pixmap is None or current_pixmap.size() != (available_width, available_height):
                scaled_pixmap = self.original_pixmap.scaled(
                    available_width, available_height,
                    Qt.IgnoreAspectRatio,
                    Qt.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)
    '''