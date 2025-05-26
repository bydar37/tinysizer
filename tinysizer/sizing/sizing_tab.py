from tinysizer.visualization.plotter_vista import PyVistaMeshPlotter
from tinysizer.sizing.calculations import Calculator
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
        self.failures=None
        self.materials=None
        self.current_assembly_type = None  # Track current assembly type
        self.sizing_pyv_plotter = None  # Initialize plotter as None
        load_stylesheet = lambda path: open(path, "r").read() #why ?
        self.setStyleSheet(load_stylesheet("tinysizer/gui/styles/dark_theme.qss"))
        self.setup_ui()
        #self.hide_parent_tree()

    '''
    def hide_parent_tree(self):
        """Hide the parent's tree widget"""
        if self.parent and hasattr(self.parent, 'tree_widget'):
            self.parent.tree_widget.hide()
    '''
    
    def get_assembly_type(self, assembly_name):
        """Determine assembly type based on name patterns from Code 1"""
        if not assembly_name:
            return None
            
        # Check for explicit type suffixes from Code 1
        if assembly_name.endswith(" (Web)"):
            return "web"
        elif assembly_name.endswith(" (Cap)"):
            return "cap"
        elif assembly_name.endswith(" (Other)"):
            return "other"
        
        # If no suffix, check if assembly exists under Web Assembly or Cap Assembly tree
        if self.parent and hasattr(self.parent, 'assembly_item'):
            # Look through the tree structure to find where this assembly is located
            web_assembly_item = self.parent.get_web_assembly_item()
            cap_assembly_item = self.parent.get_cap_assembly_item()
            
            if web_assembly_item:
                for i in range(web_assembly_item.childCount()):
                    child = web_assembly_item.child(i)
                    if child.text(0) == assembly_name:
                        return "web"
            
            if cap_assembly_item:
                for i in range(cap_assembly_item.childCount()):
                    child = cap_assembly_item.child(i)
                    if child.text(0) == assembly_name:
                        return "cap"
        
        # Default fallback - could also check property types if needed
        return "other"
    
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
            left_layout.setContentsMargins(10, 10, 10, 10)
            
            # Create the four widgets with labels
            # 1. Assembly dropdown
            self.assembly_combo = QComboBox()
            self.assembly_combo.setMinimumWidth(150)
            # Connect assembly change to update assembly type and UI
            self.assembly_combo.currentTextChanged.connect(self.on_assembly_changed)
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
            
            # Create table with 6 visible columns and 2 rows (skip the "Dimension" title)
            self.sizing_table = QTableWidget(2, 8)

            # Set column headers WITHOUT the "Dimension" label
            headers = ["", "Min", "Max", "Step", "Result", "RF", "Failure", "Material"]
            self.sizing_table.setHorizontalHeaderLabels(headers)

            # Set default values in the first column (no header, just values)
            parameters = ["Thickness (mm)", "Width (mm)"]
            for row in range(2):
                item = QTableWidgetItem(parameters[row])
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)  # Read-only
                item.setTextAlignment(Qt.AlignCenter)
                
                # Optional: make text bold
                font = item.font()
                font.setBold(True)
                item.setFont(font)

                self.sizing_table.setItem(row, 0, item)
            
                for col in range(4, 8):  # columns 4 to 7 inclusive
                    item = QTableWidgetItem(self.sizing_table.item(row, col) or QTableWidgetItem())
                    item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)  # Read-only but selectable
                    #item.setTextAlignment(Qt.AlignCenter)  # optional centering
                    self.sizing_table.setItem(row, col, item)

            # Hide the vertical header (the top-left corner empty cell comes from this)
            self.sizing_table.verticalHeader().setVisible(False)
            self.sizing_table.verticalHeader().setDefaultSectionSize(40)  # Row height

            # Make the table expand to available space
            self.sizing_table.horizontalHeader().setStretchLastSection(True)
            self.sizing_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.sizing_table.setAlternatingRowColors(True)
            self.sizing_table.setSortingEnabled(False)

            table_layout.addWidget(self.sizing_table)
            
            # Right part (1/4 width) - Analyze/Size button with dropdown
            '''
            button_frame = QFrame()
            button_layout = QVBoxLayout(button_frame)
            button_layout.setAlignment(Qt.AlignCenter)
            button_layout.addSpacing(50)
            '''

            # Create a button that will show a dropdown menu when clicked
            button_wrapper = QWidget()
            button_wrapper_layout = QHBoxLayout(button_wrapper)
            button_wrapper_layout.setContentsMargins(0, 30, 0, 35)  # Top/Bottom space
            button_wrapper_layout.setAlignment(Qt.AlignCenter)      # Center the button

            # Create the button
            self.analyze_size_btn = QPushButton("Size")
            self.analyze_size_btn.setFixedSize(120, 60)  # Sleek size
            self.analyze_size_btn.clicked.connect(self.run_sizing)
            self.analyze_size_btn.setObjectName("sizeButton")

            # Add the button to the wrapper layout
            button_wrapper_layout.addWidget(self.analyze_size_btn)
            # Add the wrapper to the form layout (instead of just the button)
            left_layout.addRow(button_wrapper)
                        
            # Add spacer to push everything to the top
            #button_layout.addItem(QSpacerItem(15, 60, QSizePolicy.Minimum, QSizePolicy.Expanding))
            
            # Add the table and button to the bottom layout with proper sizing
            #bottom_layout.addWidget(table_frame, 3)  # 3/4 width
            #bottom_layout.addWidget(button_frame, 1)  # 1/4 width
            bottom_layout.addWidget(table_frame)  # Table takes full width

    def on_assembly_changed(self, assembly_name):
        """Handle assembly selection change and update UI accordingly"""
        if not assembly_name:
            return
            
        # Determine assembly type
        self.current_assembly_type = self.get_assembly_type(assembly_name)
        print(f"Assembly changed to: {assembly_name}, Type: {self.current_assembly_type}")
        
        # Update table based on assembly type
        self.update_table_for_assembly_type()
        
        # Update property combo
        self.update_property_combo(assembly_name)
        
        # Reset selections when assembly changes
        self.materials = None
        self.failures = None
        self.update_button_labels()

    def update_table_for_assembly_type(self):
        """Update table rows based on assembly type"""
        if not hasattr(self, 'sizing_table'):
            return
            
        if self.current_assembly_type == "web":
            # For web assemblies, disable the width row (row 1)
            self.sizing_table.setRowHidden(1, True)
            print("Disabled width row for web assembly")
        else:
            # For cap and other assemblies, show both rows
            self.sizing_table.setRowHidden(1, False)
            print("Enabled width row for cap/other assembly")

    def get_failure_options_for_assembly_type(self):
        """Return appropriate failure criteria based on assembly type"""
        if self.current_assembly_type == "web":
            # Web assemblies - typically shell elements, membrane/bending failures
            return ["Von Mises", "Maximum Principal Stress", "Maximum Strain", 
                   "Tsai-Wu", "Tsai-Hill", "Maximum Stress"]
        elif self.current_assembly_type == "cap":
            # Cap assemblies - typically beam/bar elements, axial/bending failures
            return ["Von Mises", "Maximum Principal Stress", "Maximum Strain",
                   "Euler Buckling", "Johnson Column", "Hoffman"]
        else:
            # Other/mixed assemblies - show all options
            return ["Von Mises", "Maximum Principal Stress", "Tsai-Wu", 
                   "Tsai-Hill", "Maximum Strain", "Maximum Stress", "Hoffman",
                   "Euler Buckling", "Johnson Column"]
    
    def update_button_labels(self):
        """Update button labels to show selections while keeping them clickable"""
        # Update materials button
        if self.materials and len(self.materials) > 0:
            if len(self.materials) == 1:
                self.material_btn.setText(f"{self.materials[0]}")
            else:
                self.material_btn.setText(f"{', '.join(self.materials[:2])}{'...' if len(self.materials) > 2 else ''}")
            self.material_btn.setStyleSheet("color: #888888;")  # Gray out button text
        else:
            self.material_btn.setText("Select Materials...")
        
        # Update failures button
        if self.failures and len(self.failures) > 0:
            if len(self.failures) == 1:
                self.failures_btn.setText(f"{self.failures[0]}")
            else:
                self.failures_btn.setText(f"{', '.join(self.failures[:2])}{'...' if len(self.failures) > 2 else ''}")
            self.failures_btn.setStyleSheet("color: #888888;")
        else:
            self.failures_btn.setText("Select Failures...")

    def update_assembly_combo(self):
        current_selection = self.assembly_combo.currentText()
        self.assembly_combo.clear()
        if self.parent and self.parent.assemblies:
            self.assembly_combo.addItems(list(self.parent.assemblies.keys()))
            # Try to restore previous selection
            if current_selection and current_selection in self.parent.assemblies:
                self.assembly_combo.setCurrentText(current_selection)

    def update_property_combo(self, assembly_name=None):
        self.property_combo.clear()
        self.property_combo.repaint()
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
            print(f"Invalid property ID: {pid}") #seems harmless as its triggered after assembly deletion -ymn
            self.sizing_pyv_plotter.plotter.clear()
            self.sizing_pyv_plotter.plotter.reset_camera()
            self.sizing_pyv_plotter.plotter.render()
            return

    def create_sizing_tab(self):
        """Legacy method - kept for compatibility but functionality moved to update_with_model_data"""
        print(f"Sizing tab model data -> {self.parent.model_data if self.parent else None}")
        # This method is now handled by update_with_model_data
        pass

    def open_material_selection(self):
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
            # Pre-check if material was previously selected
            if self.materials and material in self.materials:
                checkbox.setChecked(True)
            material_layout.addWidget(checkbox)
            material_checkboxes.append(checkbox)
        
        layout.addWidget(material_group)
        
        # Add OK and Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(lambda: self.save_material_selection(material_checkboxes, dialog))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.exec_()

    def save_material_selection(self, checkboxes, dialog):
        """Save the selected materials and update display"""
        self.materials = [cb.text() for cb in checkboxes if cb.isChecked()]
        self.update_button_labels()
        dialog.accept()

    def open_failure_selection(self):
        """Opens a dialog for multiple failure criteria selection with type-specific options"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Failure Criteria")
        dialog.setMinimumSize(300, 400)
        
        layout = QVBoxLayout(dialog)
        
        # Get failure options based on current assembly type
        failures = self.get_failure_options_for_assembly_type()
        
        failure_group = QGroupBox(f"Available Failure Criteria ({self.current_assembly_type or 'Unknown'} Assembly)")
        failure_layout = QVBoxLayout(failure_group)
        
        failure_checkboxes = []
        for failure in failures:
            checkbox = QCheckBox(failure)
            # Pre-check if failure was previously selected
            if self.failures and failure in self.failures:
                checkbox.setChecked(True)
            failure_layout.addWidget(checkbox)
            failure_checkboxes.append(checkbox)
        
        layout.addWidget(failure_group)
        
        # Add OK and Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(lambda: self.save_failure_selection(failure_checkboxes, dialog))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.exec_()
    
    def save_failure_selection(self, checkboxes, dialog):
        """Save the selected failures and update display"""
        self.failures = [cb.text() for cb in checkboxes if cb.isChecked()]
        self.update_button_labels()
        dialog.accept()

    def show_analyze_size_options(self): #OBSOLETE
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

    def run_sizing(self):
        """Enhanced run_analysis function"""
        print("Running analysis...")
        print(f"Assembly type: {self.current_assembly_type}")
        print(f"Selected materials: {self.materials or []}")
        print(f"Selected failures: {self.failures or []}")
        
        # Validation checks
        if not self.materials:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Warning", "Please select at least one material!")
            return
        
        if not self.failures:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Warning", "Please select at least one failure criterion!")
            return
        
        # Get current property ID
        current_property = self.property_combo.currentText()
        if not current_property:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Warning", "Please select a property!")
            return
        
        try:
            property_id = int(current_property)
        except ValueError:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Invalid property ID: {current_property}")
            return
        
        # Get thickness range from table
        try:
            min_thickness = float(self.sizing_table.item(0, 1).text() or "1.0")  # Min
            max_thickness = float(self.sizing_table.item(0, 2).text() or "10.0")  # Max
            step_thickness = float(self.sizing_table.item(0, 3).text() or "0.5")  # Step
            thickness_range = (min_thickness, max_thickness, step_thickness)
        except (ValueError, AttributeError):
            # Set default values if table cells are empty
            thickness_range = (1.0, 10.0, 0.5)
            print("Using default thickness range: 1.0 to 10.0 mm, step 0.5 mm")
        
        # Create analysis instance
        self.calculator = Calculator()
        
        # Run the sizing analysis
        results = self.calculator.rf_materialStrength(
            materials=self.materials,
            failure_types=self.failures,
            model_data=self.parent.model_data,
            property_id=property_id,
            thickness_range=thickness_range,
            assembly_type=self.current_assembly_type
        )
        
        if results:
            # Update table with results
            self.update_results_table(results)
            print("Analysis completed successfully!")
        else:
            print("Analysis failed or returned no results")

    def update_results_table(self, results):
        """Update the sizing table with analysis results"""
        if not results:
            return
        
        # Find the optimal result (first one that meets target RF)
        optimal_result = results[-1]  # Last result is typically the optimal one -> WHAT !?
        
        # Update the Result column (column 4) with optimal thickness
        result_item = QTableWidgetItem(f"{optimal_result['thickness']:.2f}")
        result_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)  # Read-only
        self.sizing_table.setItem(0, 4, result_item)  # Row 0 (Thickness), Column 4 (Result)
        
        # Update the RF column (column 5) with minimum RF
        rf_item = QTableWidgetItem(f"{optimal_result['min_rf']:.3f}")
        rf_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)  # Read-only
        self.sizing_table.setItem(0, 5, rf_item)  # Row 0 (Thickness), Column 5 (RF)
        
        # Update the Failure column (column 6) with failure type
        failure_item = QTableWidgetItem(self.failures[0] if self.failures else "N/A")
        failure_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)  # Read-only
        self.sizing_table.setItem(0, 6, failure_item)  # Row 0 (Thickness), Column 6 (Failure)
        
        # Update the Material column (column 6) with failure type
        material_item = QTableWidgetItem(self.materials[0] if self.failures else "N/A")
        material_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)  # Read-only
        self.sizing_table.setItem(0, 7, material_item)  # Row 0 (Thickness), Column 6 (Failure)

        print(f"Updated table: Thickness={optimal_result['thickness']:.2f}, RF={optimal_result['min_rf']:.3f}")

    def run_analysis(self):
        print("Running sizing...")
        print(f"Assembly type: {self.current_assembly_type}")
        print(f"Selected materials: {self.materials or []}")
        print(f"Selected failures: {self.failures or []}")