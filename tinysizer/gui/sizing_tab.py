from tinysizer.visualization.plotter_vista import PyVistaMeshPlotter
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import (QComboBox, QTableWidget, QTableWidgetItem, QFormLayout, QGroupBox,
                                QWidget,QVBoxLayout, QPushButton, QDialog, QSpacerItem, QHeaderView,
                                QHBoxLayout,QSizePolicy, QMenu,QFrame,QSplitter, QDialogButtonBox, QCheckBox,QMainWindow,QLabel)

class SizingTab(QWidget):               
    def __init__(self, parent=None, tabs=None):
        super().__init__(parent)
        self.parent = parent
        self.tabs = tabs
        self.sizing_pyv_plotter = None  # Initialize plotter as None
        load_stylesheet = lambda path: open(path, "r").read()
        self.setStyleSheet(load_stylesheet("tinysizer/gui/styles/dark_theme.qss"))
        self.setup_ui()
        #self.hide_parent_tree()

    '''
    def hide_parent_tree(self):
        """Hide the parent's tree widget"""
        if self.parent and hasattr(self.parent, 'tree_widget'):
            self.parent.tree_widget.hide()
    '''
    
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        if self.parent and hasattr(self.parent, 'dock'):
            self.parent.dock.hide()
    
        # Create a placeholder label initially
        self.placeholder_label = QLabel("Load a model file to enable sizing functionality")
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setStyleSheet("font-size: 14pt; color: gray;")
        main_layout.addWidget(self.placeholder_label)

        # Create the actual content but hide it initially
        self.content_widget = QWidget()
        self.content_widget.hide()
        main_layout.addWidget(self.content_widget)

    def update_with_model_data(self, model_data):
        """Update the sizing tab with loaded model data"""
        if not model_data:
            return
        
        # Hide placeholder and show content
        self.placeholder_label.hide()
        self.content_widget.show()
        
        # Create the content layout if it doesn't exist
        if not self.content_widget.layout():
            content_layout = QVBoxLayout(self.content_widget)
            content_layout.setContentsMargins(0, 0, 0, 0)
            
            # Create two main rows with a splitter (top bigger than bottom)
            splitter = QSplitter(Qt.Vertical)
            top_widget = QWidget()
            bottom_widget = QWidget()
            splitter.addWidget(top_widget)
            splitter.addWidget(bottom_widget)
            splitter.setSizes([600, 300])  # Make the top section bigger (2:1 ratio)
            content_layout.addWidget(splitter)
            
            # TOP SECTION LAYOUT (6 rows height, 3 columns width)
            top_layout = QHBoxLayout(top_widget)
            top_layout.setContentsMargins(0, 0, 0, 0)
            
            # Left column (1/3 width) - Control panel with widgets
            left_panel = QWidget()
            left_layout = QFormLayout(left_panel)
            left_layout.setVerticalSpacing(20)
            left_layout.setContentsMargins(10, 100, 10, 10)
            
            # Create the four widgets with labels
            # 1. Assembly dropdown
            self.assembly_combo = QComboBox()
            self.assembly_combo.setMinimumWidth(150)
            left_layout.addRow("Assembly:", self.assembly_combo)
            
            # 2. Property dropdown
            self.property_combo = QComboBox()
            self.property_combo.setMinimumWidth(150)
            left_layout.addRow("Property:", self.property_combo)
            self.property_combo.currentTextChanged.connect(self.on_property_selected)
            
            # 3. Material selection (button to open dialog)
            self.material_btn = QPushButton("Select Materials...")
            self.material_btn.clicked.connect(self.open_material_selection)
            left_layout.addRow("Material:", self.material_btn)
            
            # 4. Failures selection (button to open dialog)
            self.failures_btn = QPushButton("Select Failures...")
            self.failures_btn.clicked.connect(self.open_failure_selection)
            left_layout.addRow("Failures:", self.failures_btn)
            
            # Add spacer to push everything to the top
            left_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
            
            # Right section (2/3 width) - PyVista viewer
            right_panel = QWidget()
            right_layout = QVBoxLayout(right_panel)
            right_layout.setContentsMargins(0, 0, 0, 0)
            
            # Add PyVista plotter frame
            plotter_frame = QFrame()
            plotter_frame.setFrameShape(QFrame.StyledPanel)
            plotter_frame.setMinimumSize(400, 300)
            plotter_layout = QVBoxLayout(plotter_frame)
            plotter_layout.setContentsMargins(0, 0, 0, 0)
            
            # Create a new PyVista plotter instance for this tab
            self.sizing_pyv_plotter = PyVistaMeshPlotter()
            self.sizing_pyv_plotter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.sizing_pyv_plotter.setMinimumHeight(300)
            plotter_layout.addWidget(self.sizing_pyv_plotter)
            right_layout.addWidget(plotter_frame)
            
            # Add the left and right panels to the top layout with proper sizing
            top_layout.addWidget(left_panel, 1)  # 1/3 width
            top_layout.addWidget(right_panel, 2)  # 2/3 width
            
            # BOTTOM SECTION LAYOUT (3 rows height, 4 columns width)
            bottom_layout = QHBoxLayout(bottom_widget)
            bottom_layout.setContentsMargins(10, 10, 10, 10)
            
            # Left part (3/4 width) - Editable table
            table_frame = QFrame()
            table_frame.setFrameShape(QFrame.StyledPanel)
            table_layout = QVBoxLayout(table_frame)
            
            # Create table with 7 columns and 3 rows
            self.sizing_table = QTableWidget(2, 7)
            
            # Set column headers (placeholder titles)
            headers = ["Dimension", "Min", "Max", "Step", "Result", "RF", "Failure"]
            self.sizing_table.setHorizontalHeaderLabels(headers)
            
            # Set default values for first column (can be replaced with actual parameters)
            parameters = ["Thickness", "Width"]
            for row in range(2):
                self.sizing_table.setItem(row, 0, QTableWidgetItem(parameters[row]))
            
            # Make the table expand to available space
            self.sizing_table.horizontalHeader().setStretchLastSection(True)
            self.sizing_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            
            table_layout.addWidget(self.sizing_table)
            
            # Right part (1/4 width) - Analyze/Size button with dropdown
            button_frame = QFrame()
            button_layout = QVBoxLayout(button_frame)
            button_layout.setAlignment(Qt.AlignCenter)
            button_layout.addSpacing(50)
            
            # Create a button that will show a dropdown menu when clicked
            self.analyze_size_btn = QPushButton("Analyze/Size")
            self.analyze_size_btn.setMinimumHeight(40)
            self.analyze_size_btn.clicked.connect(self.show_analyze_size_options)
            self.analyze_size_btn.setObjectName("sizeButton")
            button_layout.addWidget(self.analyze_size_btn)
            
            # Add spacer to push everything to the top
            button_layout.addItem(QSpacerItem(15, 60, QSizePolicy.Minimum, QSizePolicy.Expanding))
            
            # Add the table and button to the bottom layout with proper sizing
            bottom_layout.addWidget(table_frame, 3)  # 3/4 width
            bottom_layout.addWidget(button_frame, 1)  # 1/4 width
        
        # Now plot the model data on the sizing plotter
        '''
        if self.sizing_pyv_plotter:
            self.sizing_pyv_plotter.plot_mesh(model_data)
        '''

    def update_assembly_combo(self):
        self.assembly_combo.clear()
        if self.parent and self.parent.assemblies:
            self.assembly_combo.addItems(list(self.parent.assemblies.keys()))

    def update_property_combo(self, assembly_name=None):
        self.property_combo.clear()
        if assembly_name is None:
            assembly_name = self.assembly_combo.currentText()
        if self.parent and self.parent.assemblies and assembly_name in self.parent.assemblies:
            properties = self.parent.assemblies[assembly_name]
            self.property_combo.addItems([str(p) for p in properties])
            #self.sizing_pyv_plotter.plot_sizing_tab(self.parent.model_data,properties)
    
    def on_property_selected(self, pid): #pid str aliyor
        try:
            property_id = int(pid)
            self.sizing_pyv_plotter.plot_sizing_tab(self.parent.model_data, property_id)
        except ValueError:
            print(f"Invalid property ID: {pid}")
            return

        


    def create_sizing_tab(self):
        """Legacy method - kept for compatibility but functionality moved to update_with_model_data"""
        print(f"Sizing tab model data -> {self.parent.model_data if self.parent else None}")
        # This method is now handled by update_with_model_data
        pass

    def open_material_selection(self):
        #same code here
        """Opens a dialog for multiple material selection"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Materials")
        dialog.setMinimumSize(300, 400)
        
        layout = QVBoxLayout(dialog)
        
        # Create a list of materials with checkboxes
        materials = ["Aluminum 6061-T6", "Steel AISI 4130", "Titanium Ti-6Al-4V", 
                    "Composite Carbon/Epoxy", "Aluminum 7075-T6", "Steel 4340"]
        
        material_group = QGroupBox("Available Materials")
        material_layout = QVBoxLayout(material_group)
        
        material_checkboxes = []
        for material in materials:
            checkbox = QCheckBox(material)
            material_layout.addWidget(checkbox)
            material_checkboxes.append(checkbox)
        
        layout.addWidget(material_group)
        
        # Add OK and Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.exec_()

    def open_failure_selection(self):
        #same code here
        """Opens a dialog for multiple failure criteria selection"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Failure Criteria")
        dialog.setMinimumSize(300, 400)
        
        layout = QVBoxLayout(dialog)
        
        # Create a list of failure criteria with checkboxes
        failures = ["Von Mises", "Maximum Principal Stress", "Tsai-Wu", 
                "Tsai-Hill", "Maximum Strain", "Maximum Stress", "Hoffman"]
        
        failure_group = QGroupBox("Available Failure Criteria")
        failure_layout = QVBoxLayout(failure_group)
        
        failure_checkboxes = []
        for failure in failures:
            checkbox = QCheckBox(failure)
            failure_layout.addWidget(checkbox)
            failure_checkboxes.append(checkbox)
        
        layout.addWidget(failure_group)
        
        # Add OK and Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.exec_()

    def show_analyze_size_options(self):
        #same code here
        """Shows a dropdown menu with Analyze and Size options"""
        menu = QMenu(self)
        
        # Create actions with icons
        analyze_action = QAction(QIcon("tinysizer/gui/pics/aircraft.png"), "Analyze", self)
        size_action = QAction(QIcon("tinysizer/gui/pics/aircraft.png"), "Size", self)
        
        # Connect actions to functions
        analyze_action.triggered.connect(self.run_analysis)
        size_action.triggered.connect(self.run_sizing)
        
        # Add actions to menu
        menu.addAction(analyze_action)
        menu.addAction(size_action)
        
        # Show the menu below the button
        menu.exec_(self.analyze_size_btn.mapToGlobal(QPoint(0, self.analyze_size_btn.height())))

    def run_analysis(self):
        #same code here
        """Run the analysis operation"""
        print("Running analysis...")
        # Add your analysis code here

    def run_sizing(self):
        #same code here
        """Run the sizing operation"""
        print("Running sizing...")
        # Add your sizing code here