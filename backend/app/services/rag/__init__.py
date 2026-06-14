"""Retrieval-Augmented Generation package.

Components:
    - chunking: token-aware text splitting
    - embeddings: local (offline) + OpenAI embedders
    - vector_store: ChromaDB + in-memory fallback
    - factory: wiring driven by application settings
"""
