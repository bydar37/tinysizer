from PySide6.QtWidgets import QApplication
from tinysizer.gui.window import MainWindow
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())