<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=6366f1&height=120&section=header&text=DocuSense&fontSize=42&fontColor=ffffff&fontAlignY=38&desc=Intelligent%20Document%20Analysis%20%26%20Semantic%20Search&descAlignY=60&descSize=15&descColor=a5b4fc" width="100%"/>

[![License: MIT](https://img.shields.io/badge/License-MIT-6366f1?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![NLP](https://img.shields.io/badge/NLP-Sentence%20Transformers-14b8a6?style=flat-square)]()
[![OCR](https://img.shields.io/badge/OCR-Enabled-f59e0b?style=flat-square)]()

</div>

---

## Overview

DocuSense is an intelligent document analysis platform that combines OCR, semantic search, summarization, and interactive Q&A across heterogeneous document types. It transforms static document collections into queryable knowledge bases — enabling natural language interaction with any document corpus.

> *The gap between storing documents and understanding them is what DocuSense closes.*

---

## Architecture

```
Document Input (PDF, Image, Text)
         │
         ▼
┌─────────────────┐
│  OCR Pipeline   │   Tesseract + preprocessing for scanned docs
│                 │   Text extraction for native PDFs
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Semantic Index │   Sentence Transformers embeddings
│                 │   Vector storage for similarity search
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌──────────────┐
│Summarize│ │ Semantic Q&A │
│Pipeline │ │   Pipeline   │
└────────┘ └──────────────┘
```

---

## Key Features

| Feature | Description |
|---|---|
| **OCR Recognition** | Extracts text from scanned documents and images |
| **Semantic Search** | Meaning-based search across entire document corpus |
| **Auto Summarization** | Abstractive and extractive document summarization |
| **Interactive Q&A** | Natural language queries answered from document context |
| **Multi-Format** | PDF, images, plain text, and mixed document types |

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Embeddings** | Sentence Transformers |
| **OCR** | Tesseract / pytesseract |
| **NLP** | Transformers, spaCy |
| **Backend** | Python |
| **Language** | Python 3.10+ |

---

## Getting Started

```bash
git clone https://github.com/royxlead/docusense-python.git
cd docusense-python
pip install -r requirements.txt
python app.py
```

---

## Research Context

DocuSense explores the practical limits of dense retrieval and semantic search on heterogeneous real-world documents — including scanned PDFs where OCR quality directly affects retrieval performance. The semantic search layer uses bi-encoder architecture for efficient similarity computation across large document collections.

---

## Related Work

- [CURA](https://github.com/royxlead/cura-python) — Domain-specific RAG for medical documents
- [Auto-Researcher](https://github.com/royxlead/auto-researcher-python) — Multi-agent academic paper analysis

---

<div align="center">

**[Portfolio](https://royxlead.netlify.app) · [LinkedIn](https://linkedin.com/in/royxlead) · [ORCID](https://orcid.org/0009-0009-6582-2295)**

<img src="https://capsule-render.vercel.app/api?type=waving&color=6366f1&height=80&section=footer" width="100%"/>

</div>
