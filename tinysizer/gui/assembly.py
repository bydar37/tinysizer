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
        layout.addSpacing(5)
        ids_layout = QVBoxLayout()
        ids_layout.addWidget(QLabel("Property IDs:"))
        self.ids_input = QTextEdit()
        self.ids_input.setPlaceholderText("Enter property IDs...")
        self.ids_input.setMaximumHeight(80)
        ids_layout.addWidget(self.ids_input)
        layout.addLayout(ids_layout)
        
        # Example label
        example_label = QLabel("Example: 501, 502, 503 or 501:603 or combination of both")
        example_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(example_label)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def parse_property_ids(self, text):
        """Parse property IDs from text input"""
        id_strings=set()
        text=text.replace(","," ")
        tokens=text.split()

        for token in tokens:
            if ':' in token:
                try:
                    start, end = map(int, token.split(':')) #kind of token.split(":")[0] and [1],
                    id_strings.update(range(start, end + 1))
                except ValueError:
                    raise ValueError(f"Invalid range format: '{token}'")
            else:
                try:
                    id_strings.add(int(token))
                except ValueError:
                    raise ValueError(f"Invalid number: '{token}'")

        property_ids = [id_str for id_str in id_strings]
          
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


    
    
    
            
 