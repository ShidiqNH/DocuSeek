import sys
import os
from PyQt6 import uic
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFontMetrics, QIcon
from PyQt6.QtWidgets import *
from backendProcess import DocumentProcessor

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Load the main UI file
        uic.loadUi("DocuSeek.ui", self)

        # Connect Buttons
        self.selectDir.clicked.connect(self.dirSelect)
        self.searchButton.clicked.connect(self.processFiles)
        self.aboutButton.clicked.connect(self.aboutPage)
        self.querySearch.returnPressed.connect(self.processFiles)
        self.actionTfidfVsm.triggered.connect(lambda: self.setMethod("tfidf"))
        self.actionVsm.triggered.connect(lambda: self.setMethod("vsm"))

        # Initialize Document Processor
        self.processor = DocumentProcessor()

        # Variables
        self.dirName = None
        self.fileName = []
        self.methodSelected = "tfidf"  # Default method
        self.results = []  # Store results

        self.updateDirLabel(self.dirName)

        # Scroll Area Setup (Result section)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaLayout = QVBoxLayout(self.scrollAreaWidgetContents)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaLayout.setSpacing(20)

    # Function To Change Method
    def setMethod(self, method):
        self.methodSelected = method
        self.showToast(f"Method set to {method.upper()}", "Method Changed", QMessageBox.Icon.Information)

    # Update Directory Label Function
    def updateDirLabel(self, text):
        if not text:
            text = "No Directory Selected"
        metrics = QFontMetrics(self.dirLabel.font())
        elided_text = metrics.elidedText(text, Qt.TextElideMode.ElideRight, self.dirLabel.width())
        self.dirLabel.setText(elided_text)
        self.dirLabel.setToolTip(text)

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

    # Scan Directory Function
    def scanDirectoryForFiles(self, directory):
        # Clear Scroll Area
        for i in range(self.scrollAreaLayout.count()):
            widget = self.scrollAreaLayout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # Supported file extensions
        valid_extensions = [".pdf", ".docx", ".txt"]
        self.fileName.clear()

        # Scan For All Sub Directory
        found_files = False
        for root, _, files in os.walk(directory):
            for filename in files:
                filepath = os.path.join(root, filename)
                _, ext = os.path.splitext(filepath)
                if ext.lower() in valid_extensions:
                    found_files = True
                    self.fileName.append({"filename": filename, "filepath": filepath})

                    # Create a widget for the file and add it to the scroll area
                    custom_widget = CustomWidget(filename, filepath)
                    self.scrollAreaLayout.addWidget(custom_widget)

        if not found_files:
            self.showToast("No supported files found in the selected directory.", "No Files Found", QMessageBox.Icon.Critical)
        else:
            self.showToast("Files loaded successfully.", "Success", QMessageBox.Icon.Information)

    # Process Query Function
    def processFiles(self):
        if not self.dirName:
            self.showToast("Please select a directory before processing.", "No Directory Selected", QMessageBox.Icon.Warning)
            return

        query = self.querySearch.text()
        if not query:
            self.showToast("Please enter a query.", "Empty Query", QMessageBox.Icon.Warning)
            return

        # Extract file paths
        filepaths = [file["filepath"] for file in self.fileName]

        try:
            # Process similarities using the selected method
            self.results = self.processor.processSimilarity(query, filepaths, method=self.methodSelected)

            # Update the UI with results
            self.updateResultsUI()

        except Exception as e:
            self.showToast(f"Error processing files: {e}", "Error", QMessageBox.Icon.Critical)


    # Update Result Section
    def updateResultsUI(self):
        # Clear previous widgets
        for i in range(self.scrollAreaLayout.count()):
            widget = self.scrollAreaLayout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # Add widgets for each result
        for result in self.results:
            widget = CustomWidget(result["filename"], result["filepath"], result["similarity"])
            self.scrollAreaLayout.addWidget(widget)

    # Function To Show Messagebox
    def showToast(self, message, title, icon=QMessageBox.Icon.NoIcon):
        msg = QMessageBox()
        msg.setIcon(icon)
        msg.setText(message)
        msg.setWindowTitle(title)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

    # Show About
    def aboutPage(self):
        aboutWindow = AboutWindow(self)
        aboutWindow.exec()


class CustomWidget(QFrame):
    def __init__(self, filename, filepath, similarity=None):
        super().__init__()
        uic.loadUi("filesFrame.ui", self)

        self.filename = filename
        self.filepath = filepath
        self.similarity = similarity

        self.docTitle.setText(self.filename)
        self.setIcon(filepath)
        self.detailButton.clicked.connect(self.detailPage)

        # Update similarity label
        if self.similarity is not None:
            # Convert similarity to percentage and cap it at 100%
            display_similarity = min(self.similarity * 100, 100)
            self.similarityLabel.setText(f"Similarity: {display_similarity:.2f}%")
        else:
            self.similarityLabel.setText("Similarity: None")  # Default when not computed

    # Open Detail Window
    def detailPage(self):
        # Run the removeStopwordsAndStem function
        processor = DocumentProcessor()
        result = processor.removeStopwordsAndStem([self.filepath])

        # Ensure the result is not empty
        if result:
            detail_data = result[0]  # Get the first document's result
            self.detailWindow = DetailWidget(
                filename=detail_data["filename"],
                filepath=detail_data["filepath"],
                original=detail_data["original"],
                stemmed=detail_data["stemmed"],
                stem=detail_data["stem"],
                kataPenting=detail_data["kataPenting"],  # Pass the additional field
                similarity=self.similarity  # Pass similarity to the DetailWidget
            )
            self.detailWindow.setWindowTitle("File Details")
            self.detailWindow.show()
        else:
            QMessageBox.warning(self, "Error", "Failed to process the file for details.")

    def setIcon(self, filepath):
        ext = os.path.splitext(filepath)[1].lower()
        icon_map = {
            ".pdf": "assets/pdfIcon.png",
            ".docx": "assets/docsIcon.png",
            ".txt": "assets/txtIcon.png",
        }
        icon_path = icon_map.get(ext)
        if icon_path:
            icon = QIcon(icon_path)
            self.docImage.setPixmap(icon.pixmap(80, 80))
            self.docImage.setAlignment(Qt.AlignmentFlag.AlignCenter)


class DetailWidget(QFrame):
    def __init__(self, filename, filepath, original, stemmed, stem, kataPenting, similarity=None):
        super().__init__()
        uic.loadUi("detailFrame.ui", self)

        self.filename = filename
        self.filepath = filepath
        self.original = original
        self.stemmed = stemmed
        self.stem = stem
        self.kataPenting = kataPenting
        self.similarity = similarity
        
        self.compareButton.clicked.connect(self.comparePage)

        # Set details in the UI
        self.docTitle.setText(self.filename)
        self.dasarLabel.setText(f"Kata penting : {self.kataPenting}")  # Display word count
        self.setIcon(filepath)  # Set the document icon

        # Update similarity label
        if self.similarity is not None:
            # Convert similarity to percentage and cap it at 100%
            display_similarity = min(self.similarity * 100, 100)
            self.similarityLabel.setText(f"Similarity: {display_similarity:.2f}%")
        else:
            self.similarityLabel.setText("Similarity: None")  # Default when not computed

        # Populate stem mapping in the table
        self.stemTable.setRowCount(len(self.stem))
        for row, mapping in enumerate(self.stem):
            self.stemTable.setItem(row, 0, QTableWidgetItem(mapping["Kata asal"]))
            self.stemTable.setItem(row, 1, QTableWidgetItem(mapping["Kata dasar"]))

    # Open Compare Window
    def comparePage(self):
        # DocumentWidget for original text
        self.originalWidget = DocumentWidget()
        self.originalWidget.docTitle.setText(f"{self.filename} - Original")
        self.originalWidget.documentView.setPlainText(self.original)
        self.originalWidget.setWindowTitle("Original Document")
        self.originalWidget.show()

        # DocumentWidget for stemmed text
        self.stemmedWidget = DocumentWidget()
        self.stemmedWidget.docTitle.setText(f"{self.filename} - Stemmed")
        self.stemmedWidget.documentView.setPlainText(self.stemmed)
        self.stemmedWidget.setWindowTitle("Stemmed Document")
        self.stemmedWidget.show()

    def setIcon(self, filepath):
        ext = os.path.splitext(filepath)[1].lower()
        icon_map = {
            ".pdf": "assets/pdfIcon.png",
            ".docx": "assets/docsIcon.png",
            ".txt": "assets/txtIcon.png",
        }
        icon_path = icon_map.get(ext)
        if icon_path:
            icon = QIcon(icon_path)
            self.docImage.setPixmap(icon.pixmap(80, 80))
            self.docImage.setAlignment(Qt.AlignmentFlag.AlignCenter)

class DocumentWidget(QFrame):
    def __init__(self):
        super().__init__()
        uic.loadUi("documentView.ui", self)

class AboutWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi("aboutPage.ui", self)
        self.setWindowTitle("About DocuSeek")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())