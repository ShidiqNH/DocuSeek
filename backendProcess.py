import os
import re
import csv
from sklearn.metrics.pairwise import cosine_similarity
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from collections import Counter
import PyPDF2
from docx import Document
from sklearn.feature_extraction.text import TfidfVectorizer


class DocumentProcessor:
    def __init__(self, stopwordFile="stopwordbahasa.csv"):
        # Initialize Stemmer
        factory = StemmerFactory()
        self.stemmer = factory.create_stemmer()

        # Load stopwords
        self.stopwords = self.loadStopwords(stopwordFile)

    def loadStopwords(self, filepath):
        stopwords = set()
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                stopwords = {row[0].strip() for row in csv.reader(f) if row}
        except Exception as e:
            print(f"Error loading stopwords from {filepath}: {e}")
        return stopwords

    def readPdf(self, filepath):
        try:
            with open(filepath, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                return "".join(page.extract_text() for page in reader.pages)
        except Exception as e:
            print(f"Error reading PDF file {filepath}: {e}")
            return ""

    def readDocx(self, filepath):
        try:
            doc = Document(filepath)
            return "\n".join(p.text for p in doc.paragraphs)
        except Exception as e:
            print(f"Error reading DOCX file {filepath}: {e}")
            return ""

    def readTxt(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"Error reading TXT file {filepath}: {e}")
            return ""

    def loadDocuments(self, filepaths):
        documents = []
        for filepath in filepaths:
            if filepath.endswith(".pdf"):
                content = self.readPdf(filepath)
            elif filepath.endswith(".docx"):
                content = self.readDocx(filepath)
            elif filepath.endswith(".txt"):
                content = self.readTxt(filepath)
            else:
                content = ""
            if content:
                documents.append({"filepath": filepath, "filename": os.path.basename(filepath), "original": content})
        return documents

    # Remove Stopword and Stemming Function
    def removeStopwordsAndStem(self, filepaths):
        documents = self.loadDocuments(filepaths)
        results = []

        for doc in documents:
            stemmed, stemMap = self.preprocess(doc["original"])
            kataPenting = len(stemmed.split())
            results.append({
                "filename": doc["filename"],
                "filepath": doc["filepath"],
                "original": doc["original"],
                "stemmed": stemmed,
                "stem": stemMap,
                "kataPenting": kataPenting
            })

        return results

    # Preprocess Document Function
    def preprocess(self, text):
        tokens = re.findall(r'\b\w+\b', text.lower())
        filteredTokens = [token for token in tokens if token not in self.stopwords]
        stemmedTokens = []
        stemMap = []
        for token in filteredTokens:
            stemmedWord = self.stemmer.stem(token)
            stemmedTokens.append(stemmedWord)
            stemMap.append({"Kata asal": token, "Kata dasar": stemmedWord})
        return " ".join(stemmedTokens), stemMap

    # Calculate Similarity Using VSM Only
    def calculateVSMOnly(self, query, documents):
        vocabulary = set()
        documentVectors = []
        processedQuery, _ = self.preprocess(query)

        # Process documents
        for doc in documents:
            processedDoc, _ = self.preprocess(doc["original"])
            documentVectors.append(Counter(processedDoc.split()))
            vocabulary.update(processedDoc.split())

        vocabulary = list(vocabulary)
        queryVector = [processedQuery.split().count(term) for term in vocabulary]
        documentMatrix = [[vec.get(term, 0) for term in vocabulary] for vec in documentVectors]

        # Calculate cosine similarity
        similarities = cosine_similarity([queryVector], documentMatrix).flatten()
        return similarities

    # Calculate Similarity Using TF-IDF and VSM
    def calculateTFIDFAndVSM(self, query, documents):
        processedQuery, _ = self.preprocess(query)
        processedDocuments = [self.preprocess(doc["original"])[0] for doc in documents]

        # Calculate TF-IDF for documents
        vectorizer = TfidfVectorizer(norm=None)
        tfidfMatrix = vectorizer.fit_transform(processedDocuments)

        # Transform the query into a TF-IDF vector
        queryVector = vectorizer.transform([processedQuery])

        # Calculate cosine similarity
        return cosine_similarity(queryVector, tfidfMatrix).flatten()

    # Process Similarity Function
    def processSimilarity(self, query, filepaths, method="tfidf"):
        # Load documents
        documents = self.loadDocuments(filepaths)

        # Calculate similarity scores
        if method == "vsm":
            similarities = self.calculateVSMOnly(query, documents)
        elif method == "tfidf":
            similarities = self.calculateTFIDFAndVSM(query, documents)
        else:
            raise ValueError(f"Unknown method: {method}. Use 'vsm' or 'tfidf'.")

        results = []
        for doc, similarity in zip(documents, similarities):
            results.append({
                "filename": doc["filename"],
                "filepath": doc["filepath"],
                "similarity": similarity
            })

        # Sort Results
        return sorted(results, key=lambda x: x["similarity"], reverse=True)
