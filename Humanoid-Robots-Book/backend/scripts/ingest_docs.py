#!/usr/bin/env python3
"""
Document Ingestion Script for RAG Chatbot
Chunks textbook markdown files and uploads to Qdrant with Gemini embeddings.

Usage:
    python scripts/ingest_docs.py --docs-dir ../docs [--dry-run]
"""

import os
import sys
import asyncio
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any
import tiktoken

from dotenv import load_dotenv  # Add this
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db.qdrant_setup import QdrantManager
from src.chat.gemini_service import GeminiService
from src.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Constants
CHUNK_SIZE = 512  # tokens
CHUNK_OVERLAP = 50  # tokens
BATCH_SIZE = 100  # embeddings per batch


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Chunk text into fixed-size segments with overlap.

    Args:
        text: Input text to chunk
        chunk_size: Target tokens per chunk
        overlap: Overlap tokens between chunks

    Returns:
        List of text chunks
    """
    try:
        encoding = tiktoken.get_encoding("cl100k_base")  # GPT-4 tokenizer
        tokens = encoding.encode(text)

        chunks = []
        start = 0

        while start < len(tokens):
            end = start + chunk_size
            chunk_tokens = tokens[start:end]
            chunk_text = encoding.decode(chunk_tokens)
            chunks.append(chunk_text)

            # Move to next chunk with overlap
            start = end - overlap

        return chunks

    except Exception as e:
        logger.error(f"Error chunking text: {e}")
        raise


def extract_metadata_from_path(file_path: Path, docs_dir: Path) -> Dict[str, str]:
    """
    Extract metadata from markdown file path.

    Args:
        file_path: Path to markdown file
        docs_dir: Root docs directory

    Returns:
        Dictionary with chapter_id, module_id, title, file_path
    """
    relative_path = file_path.relative_to(docs_dir)
    parts = relative_path.parts

    # Extract module and chapter from path
    # Example: docs/module-1-ros2-basics/chapter-2-pub-sub.md
    module_id = parts[0] if len(parts) > 1 else "unknown"
    chapter_file = file_path.stem  # e.g., "chapter-2-pub-sub"

    # Construct chapter ID
    chapter_id = f"{module_id}/{chapter_file}"

    # Extract title from first heading in file
    title = chapter_file.replace("-", " ").title()
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("# "):
                    title = line.strip("# \n")
                    break
    except Exception as e:
        logger.warning(f"Could not extract title from {file_path}: {e}")

    return {
        "chapter_id": chapter_id,
        "module_id": module_id,
        "title": title,
        "file_path": str(relative_path),
    }


async def process_markdown_file(
    file_path: Path,
    docs_dir: Path,
    gemini: GeminiService,
) -> List[Dict[str, Any]]:
    """
    Process a single markdown file: chunk and generate embeddings.

    Args:
        file_path: Path to markdown file
        docs_dir: Root docs directory
        gemini: Gemini service for embeddings

    Returns:
        List of document dictionaries ready for Qdrant upload
    """
    logger.info(f"Processing {file_path.name}...")

    try:
        # Read file content
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract metadata
        metadata = extract_metadata_from_path(file_path, docs_dir)

        # Chunk text
        chunks = chunk_text(content)
        logger.info(f"  Created {len(chunks)} chunks")

        # Generate embeddings
        logger.info(f"  Generating embeddings...")
        embeddings = await gemini.generate_batch_embeddings(chunks)

        # Create documents
        documents = []
        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            doc_id = f"{metadata['chapter_id']}_{idx:03d}".replace("/", "_")
            documents.append({
                "id": doc_id,
                "vector": embedding,
                "chapter_id": metadata["chapter_id"],
                "module_id": metadata["module_id"],
                "text": chunk,
                "metadata": {
                    "title": metadata["title"],
                    "section": f"Chunk {idx + 1}",
                    "file_path": metadata["file_path"],
                },
            })

        logger.info(f"  Processed {len(documents)} chunks from {file_path.name}")
        return documents

    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}", exc_info=True)
        return []


async def ingest_documents(
    docs_dir: Path,
    dry_run: bool = False,
    recreate_collection: bool = False,
) -> None:
    """
    Ingest all markdown files from docs directory.

    Args:
        docs_dir: Path to docs directory
        dry_run: If True, process but don't upload to Qdrant
        recreate_collection: If True, delete and recreate collection
    """
    logger.info(f"Starting ingestion from {docs_dir}")

    # Initialize services
    gemini = GeminiService()
    qdrant = QdrantManager()

    # Create or verify collection
    if not dry_run:
        logger.info(f"Setting up Qdrant collection: {settings.qdrant_collection_name}")
        qdrant.create_collection(recreate=recreate_collection)

    # Find all markdown files
    markdown_files = list(docs_dir.rglob("*.md"))
    logger.info(f"Found {len(markdown_files)} markdown files")

    # Process files
    all_documents = []
    for file_path in markdown_files:
        # Skip README and other non-chapter files
        if "README" in file_path.name or "intro" in file_path.name.lower():
            logger.info(f"Skipping {file_path.name}")
            continue

        documents = await process_markdown_file(file_path, docs_dir, gemini)
        all_documents.extend(documents)

    logger.info(f"\nTotal documents processed: {len(all_documents)}")

    # Upload to Qdrant
    if dry_run:
        logger.info("DRY RUN: Skipping Qdrant upload")
        logger.info(f"Would upload {len(all_documents)} chunks")
    else:
        logger.info("Uploading to Qdrant...")
        uploaded_count = qdrant.index_documents(all_documents, batch_size=BATCH_SIZE)
        logger.info(f"Successfully uploaded {uploaded_count} documents")

        # Print collection stats
        stats = qdrant.get_collection_stats()
        logger.info(f"\nCollection stats: {stats}")

    logger.info("Ingestion complete!")


def main():
    """Main entry point for ingestion script."""
    parser = argparse.ArgumentParser(description="Ingest textbook documents into Qdrant")
    parser.add_argument(
        "--docs-dir",
        type=Path,
        required=True,
        help="Path to docs directory containing markdown files",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Process files but don't upload to Qdrant",
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Delete and recreate Qdrant collection",
    )

    args = parser.parse_args()

    # Validate docs directory
    if not args.docs_dir.exists():
        logger.error(f"Docs directory not found: {args.docs_dir}")
        sys.exit(1)

    # Run ingestion
    try:
        asyncio.run(ingest_documents(
            docs_dir=args.docs_dir,
            dry_run=args.dry_run,
            recreate_collection=args.recreate,
        ))
    except KeyboardInterrupt:
        logger.warning("Ingestion interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
