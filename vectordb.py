import os
import hashlib
import shutil

import PyPDF2
import pandas as pd
from docx import Document
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
import chromadb

from config import DATA_FOLDER, CHUNK_SIZE, CHUNK_OVERLAP, MAX_CONTEXT_CHUNKS


# ================= FILE LOADER =================

def read_file(path):
    text = ""
    try:
        if path.endswith(".pdf"):
            with open(path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for i, page in enumerate(reader.pages, 1):
                    text += f"\n--- Page {i} ---\n"
                    text += page.extract_text() or ""

        elif path.endswith(".xlsx"):
            excel = pd.ExcelFile(path)
            for sheet in excel.sheet_names:
                df = pd.read_excel(path, sheet_name=sheet, engine="openpyxl")
                text += f"\n=== SHEET: {sheet} ===\n"
                text += df.to_string(index=False)

        elif path.endswith(".csv"):
            df = pd.read_csv(path)
            text = df.to_string(index=False)

        elif path.endswith(".docx"):
            doc = Document(path)
            text = "\n".join([p.text for p in doc.paragraphs])

        elif path.endswith((".txt", ".md")):
            with open(path, encoding="utf-8") as f:
                text = f.read()

        elif path.endswith(".html"):
            soup = BeautifulSoup(open(path).read(), "html.parser")
            text = soup.get_text()

    except Exception as e:
        print(f"Error reading file {path}: {e}")

    return text.strip()


def chunk_text(text, file):
    words = text.split()
    chunks = []
    for i in range(0, len(words), CHUNK_SIZE - CHUNK_OVERLAP):
        chunk = " ".join(words[i:i + CHUNK_SIZE])
        if chunk.strip():
            chunks.append(f"[Source: {file}]\n{chunk}")
    return chunks


def load_files(folder=DATA_FOLDER):
    if not os.path.exists(folder):
        os.makedirs(folder)
        return []

    chunks = []
    for file in os.listdir(folder):
        path = os.path.join(folder, file)
        if not os.path.isfile(path):
            continue
        content = read_file(path)
        if content:
            chunks.extend(chunk_text(content, file))
    return chunks


# ================= VECTOR DB =================

class VectorDB:

    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self._init_client()

    def _init_client(self):
        if os.path.exists("db"):
            try:
                shutil.rmtree("db")
            except Exception as e:
                print(f"Warning: could not clear db folder: {e}")
        self.client = chromadb.PersistentClient(path="db")
        self.col = self.client.get_or_create_collection("docs")

    def _ensure_client(self):
        try:
            self.col.count()
        except Exception:
            self._init_client()

    def load(self, chunks):
        if not chunks:
            return
        self._ensure_client()
        embeds = self.model.encode(chunks).tolist()
        ids = [hashlib.md5(c.encode()).hexdigest()[:16] for c in chunks]
        self.col.add(documents=chunks, embeddings=embeds, ids=ids)

    def search(self, query):
        self._ensure_client()
        if not query or len(query.strip()) < 2:
            print("⚠️ Query too short, returning empty results")
            return []
        try:
            emb = self.model.encode([query]).tolist()
            res = self.col.query(query_embeddings=emb, n_results=MAX_CONTEXT_CHUNKS)
            results = res["documents"][0] if res["documents"] else []
            print(f"🔍 PDF search returned {len(results)} chunks")
            return results
        except Exception as e:
            print(f"❌ PDF search error: {e}")
            return []
