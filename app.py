import sys
import os
from PyQt6 import uic
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFontMetrics, QIcon
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QVBoxLayout, QWidget, QScrollArea, QFrame, QLabel, QHBoxLayout, QMessageBox

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Load the main UI file
        uic.loadUi("DocuSeek.ui", self)
        
        # Connect Button
        self.selectDir.clicked.connect(self.dirSelect)
        self.searchButton.clicked.connect(self.processFiles)
        self.querySearch.returnPressed.connect(self.processFiles)

        # Variable
        self.dirName = None
        self.fileName = []
        
        self.updateDirLabel(self.dirName)

        # Scroll Area Setup (Result section)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaLayout = QVBoxLayout(self.scrollAreaWidgetContents)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaLayout.setSpacing(20)

    # Update Directory Label Function
    def updateDirLabel(self, text):
        if text is None or text.strip() == "":
            text = "No Directory Selected"
        metrics = QFontMetrics(self.dirLabel.font())
        elided_text = metrics.elidedText(text, Qt.TextElideMode.ElideRight, self.dirLabel.width()) # Truncate Overflow Directory Path
        self.dirLabel.setText(elided_text)
        self.dirLabel.setToolTip(text) # Tooltip For Directory Path
        
    # Select Directory Function
    def dirSelect(self):
        dir_name = QFileDialog.getExistingDirectory(self, "Select Directory")
        if dir_name:
            self.dirName = dir_name
            self.updateDirLabel(self.dirName)
            self.scanDirectoryForFiles(dir_name)
        else:
            self.dirName = None
            self.updateDirLabel(self.dirName)

    def scanDirectoryForFiles(self, directory):
        # Clear Scroll Area
        for i in range(self.scrollAreaLayout.count()):
            widget = self.scrollAreaLayout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        # Valid Extensions
        valid_extensions = [".pdf", ".docx", ".txt"]
        self.fileName.clear()

        found_files = False

        # Scan For All Sub Directory
        for root, dirs, files in os.walk(directory):
            for filename in files:
                filepath = os.path.join(root, filename)
                _, ext = os.path.splitext(filepath)
                if ext.lower() in valid_extensions:
                    found_files = True
                    self.fileName.append({'filename': filename, 'filepath': filepath})

                    # Create a widget for the file and add it to the scroll area
                    custom_widget = CustomWidget(filename, filepath)
                    self.scrollAreaLayout.addWidget(custom_widget)

        if not found_files:
            self.showToast("No supported files found in this directory or its subdirectories.", "No Supported Files", QMessageBox.Icon.Critical)
        else:
            self.showToast("Files successfully loaded.", "Success")
            
    # Function To Show Messagebox
    def showToast(self, message, title, icon=QMessageBox.Icon.NoIcon):
        msg = QMessageBox()
        msg.setIcon(icon)
        msg.setText(message)
        msg.setWindowTitle(title)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

    # Placeholder For File Processing 
    def processFiles(self):
        if not self.dirName:
            self.showToast("Please select a directory before processing.", "No Directory Selected", QMessageBox.Icon.Warning)
            return

        query = self.querySearch.text()
        
        if not query:
            self.showToast("Please enter a query.", "Empty Query", QMessageBox.Icon.Warning)
            return

        self.showToast(f"Processing files with query: '{query}'", "Query Entered", QMessageBox.Icon.Information)


# Widget For Displaying Files
class CustomWidget(QFrame):
    def __init__(self, filename, filepath):
        super().__init__()
        uic.loadUi("filesFrame.ui", self)

        self.filename = filename
        self.filepath = filepath

        self.docTitle.setText(self.filename)
        self.setIcon(filepath)
        
        # Placeholder For Details Button
        self.pushButton.clicked.connect(lambda: self.showToast(self.filename, "Details", QMessageBox.Icon.Information))


    # Set Icon Function Based On File Extension
    def setIcon(self, filepath):
        file_extension = os.path.splitext(filepath)[1].lower()
        if file_extension == ".pdf":
            icon = QIcon("assets/pdfIcon.png") 
        elif file_extension == ".docx":
            icon = QIcon("assets/docsIcon.png")
        elif file_extension == ".txt":
            icon = QIcon("assets/txtIcon.png") 
        else:
            return

        self.docImage.setPixmap(icon.pixmap(80, 80))
        self.docImage.setAlignment(Qt.AlignmentFlag.AlignCenter)  
        
        # Placeholder For Similarity
        self.similarityLabel.setText("Similarity goes here")

        
    # Function To Show Messagebox
    def showToast(self, message, title, icon=QMessageBox.Icon.NoIcon):
        msg = QMessageBox()
        msg.setIcon(icon)
        msg.setText(message)
        msg.setWindowTitle(title)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())