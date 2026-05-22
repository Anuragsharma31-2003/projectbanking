"""
ingest.py – CLI utility to pre-load documents into ChromaDB before starting the API.

Usage:
    python ingest.py                        # ingest everything in data/
    python ingest.py --file data/loans.pdf  # ingest a single file
    python ingest.py --clear                # wipe the vector DB first
"""
import argparse
import logging
import shutil
from pathlib import Path

from . import config
from . import rag_pipeline as rag

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


def clear_db():
    if config.CHROMA_DIR.exists():
        shutil.rmtree(config.CHROMA_DIR)
        logger.info("Cleared ChromaDB at %s", config.CHROMA_DIR)


def ingest_directory(directory: Path):
    supported = {".pdf", ".txt", ".md"}
    files     = [f for f in directory.iterdir() if f.suffix.lower() in supported]
    if not files:
        logger.warning("No supported files found in %s", directory)
        return

    total = 0
    for fpath in files:
        try:
            n = rag.ingest_file(fpath)
            total += n
            logger.info("  ✓  %-40s → %d chunks", fpath.name, n)
        except Exception as exc:
            logger.error("  ✗  %-40s → %s", fpath.name, exc)

    logger.info("Done. Total chunks ingested: %d", total)
    logger.info("Vector DB size: %d", rag.get_collection_count())


def main():
    parser = argparse.ArgumentParser(description="FinBot document ingestion CLI")
    parser.add_argument("--file",  type=Path, help="Single file to ingest")
    parser.add_argument("--dir",   type=Path, default=config.DATA_DIR, help="Directory of docs")
    parser.add_argument("--clear", action="store_true", help="Clear vector DB before ingesting")
    args = parser.parse_args()

    if args.clear:
        clear_db()

    if args.file:
        if not args.file.exists():
            logger.error("File not found: %s", args.file)
            sys.exit(1)
        n = rag.ingest_file(args.file)
        logger.info("Ingested %d chunks from %s", n, args.file.name)
    else:
        if not args.dir.exists():
            logger.error("Directory not found: %s", args.dir)
            sys.exit(1)
        ingest_directory(args.dir)


if __name__ == "__main__":
    main()
