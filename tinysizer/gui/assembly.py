from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QLabel, QPushButton, QDialogButtonBox, QTextEdit,
                             QMessageBox, QMenu, QWidget, QApplication)
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QFont, QAction
import re

class AssemblyDialog(QDialog):
    assembly_created = Signal(str, list)  # Signal emits assembly name and property IDs list
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Create Assembly")
        self.setModal(True)
        self.resize(400, 200)
        
        layout = QVBoxLayout(self)
        
        # Assembly name input
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Assembly Name:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter assembly name...")
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)
        
        # Property IDs input
        ids_layout = QVBoxLayout()
        ids_layout.addWidget(QLabel("Property IDs (comma-separated):"))
        self.ids_input = QTextEdit()
        self.ids_input.setPlaceholderText("Enter property IDs: 501, 502, 503...")
        self.ids_input.setMaximumHeight(80)
        ids_layout.addWidget(self.ids_input)
        layout.addLayout(ids_layout)
        
        # Example label
        example_label = QLabel("Example: 501, 502, 503 or 501,502,503")
        example_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(example_label)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def parse_property_ids(self, text):
        """Parse property IDs from text input"""
        if not text.strip():
            return []
            
        # Remove all whitespace and split by comma
        ids_text = re.sub(r'\s+', '', text)
        id_strings = ids_text.split(',')
        
        property_ids = []
        for id_str in id_strings:
            if id_str.strip():  # Skip empty strings
                try:
                    # Try to convert to integer
                    property_id = int(id_str)
                    property_ids.append(property_id)
                except ValueError:
                    # If not integer, keep as string
                    property_ids.append(id_str.strip())
                    
        return property_ids
        
    def accept(self):
        """Handle OK button click"""
        assembly_name = self.name_input.text().strip()
        property_ids_text = self.ids_input.toPlainText().strip()
        
        if not assembly_name:
            QMessageBox.warning(self, "Warning", "Please enter an assembly name.")
            return
            
        if not property_ids_text:
            QMessageBox.warning(self, "Warning", "Please enter at least one property ID.")
            return
            
        # Parse property IDs
        property_ids = self.parse_property_ids(property_ids_text)
        
        if not property_ids:
            QMessageBox.warning(self, "Warning", "Please enter valid property IDs.")
            return
            
        # Emit signal with assembly data
        self.assembly_created.emit(assembly_name, property_ids)
        super().accept()


#BUGGY, HIC DEVREDE DEGIL BU ...
class AssemblyManager(QWidget):
    """Example widget that demonstrates right-click menu usage"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Assembly Manager Example")
        self.resize(300, 200)
        
        # Enable context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
        # Store assemblies
        self.assemblies = {}
        
        layout = QVBoxLayout(self)
        info_label = QLabel("Right-click anywhere to create assembly")
        info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_label)
        
        self.status_label = QLabel("No assemblies created")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
    def show_context_menu(self, position):
        """Show context menu on right click"""
        context_menu = QMenu(self)
        
        # Create assembly action
        create_action = QAction("Create Assembly", self)
        create_action.triggered.connect(self.create_assembly)
        context_menu.addAction(create_action)
        
        # Show other actions if assemblies exist
        if self.assemblies:
            context_menu.addSeparator()
            list_action = QAction("List Assemblies", self)
            list_action.triggered.connect(self.list_assemblies)
            context_menu.addAction(list_action)
            
            clear_action = QAction("Clear All", self)
            clear_action.triggered.connect(self.clear_assemblies)
            context_menu.addAction(clear_action)
        
        # Show menu at cursor position
        context_menu.exec_(self.mapToGlobal(position))
        
    def create_assembly(self):
        """Open assembly creation dialog"""
        dialog = AssemblyDialog(self)
        dialog.assembly_created.connect(self.on_assembly_created)
        dialog.exec_()
        
    def on_assembly_created(self, name, property_ids):
        """Handle assembly creation"""
        self.assemblies[name] = property_ids
        print(f"Assembly '{name}' created with properties: {property_ids}")
        
        # Update status
        self.update_status()
        
        # Show confirmation
        QMessageBox.information(self, "Success", 
                              f"Assembly '{name}' created successfully!\n"
                              f"Properties: {', '.join(map(str, property_ids))}")
        
    def update_status(self):
        """Update status label"""
        count = len(self.assemblies)
        if count == 0:
            self.status_label.setText("No assemblies created")
        else:
            self.status_label.setText(f"{count} assembly(ies) created")
            
    def list_assemblies(self):
        """Show all assemblies"""
        if not self.assemblies:
            QMessageBox.information(self, "Assemblies", "No assemblies created yet.")
            return
            
        assembly_list = []
        for name, props in self.assemblies.items():
            props_str = ', '.join(map(str, props))
            assembly_list.append(f"• {name}: [{props_str}]")
            
        message = "Created Assemblies:\n\n" + '\n'.join(assembly_list)
        QMessageBox.information(self, "Assemblies", message)
        
    def clear_assemblies(self):
        """Clear all assemblies"""
        reply = QMessageBox.question(self, "Clear All", 
                                   "Are you sure you want to clear all assemblies?",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.assemblies.clear()
            self.update_status()
            print("All assemblies cleared")

