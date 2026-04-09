"""
Document ingestion orchestrator.
Ties together document parsing, chunking, and storage.
"""

import logging
import os
from pathlib import Path
from typing import List
from ingestion.docling_parser import DoclingParser, parse_all_documents
from ingestion.hierarchical_chunker import HierarchicalChunker, chunk_parsed_documents
from vector_store import get_vector_store
from metadata_schema import Chunk
from config import COLLECTION_CONFIGS, DocumentCollection

logger = logging.getLogger(__name__)


class DocumentIngester:
    """
    Orchestrates end-to-end document ingestion:
    1. Parse documents with Docling
    2. Create hierarchical chunks
    3. Embed and store in Qdrant
    """
    
    def __init__(self):
        """Initialize ingester."""
        self.parser = DoclingParser()
        self.chunker = HierarchicalChunker()
        self.vector_store = get_vector_store()
    
    def ingest_collection(
        self,
        collection_name: DocumentCollection,
        docs_folder_path: str,
    ) -> bool:
        """
        Ingest all documents from a collection folder.
        
        Args:
            collection_name: DocumentCollection enum value
            docs_folder_path: Path to folder containing documents
            
        Returns:
            Tuple of (success_boolean, list_of_filenames)
        """
        ingested_files = []
        try:
            logger.info(f"Starting ingestion for collection: {collection_name.value}")
            
            # Get collection config
            config = COLLECTION_CONFIGS.get(collection_name)
            if not config:
                logger.error(f"Unknown collection: {collection_name}")
                return False, []
            
            access_roles = config["access_roles"]
            
            # Resolve path relative to this script
            if not os.path.isabs(docs_folder_path):
                base_dir = os.path.dirname(os.path.abspath(__file__))
                docs_folder_path = os.path.join(base_dir, docs_folder_path)
            
            # Check if folder exists
            if not os.path.exists(docs_folder_path):
                logger.error(f"Documents folder not found: {docs_folder_path}")
                return False, []
            
            logger.info(f"Scanning folder: {docs_folder_path}")
            
            # Step 1: Parse all documents
            parsed_docs = parse_all_documents(docs_folder_path)
            if not parsed_docs:
                logger.warning(f"No documents found in {docs_folder_path}")
                return False, []
            
            logger.info(f"Discovered {len(parsed_docs)} documents in {collection_name.value}")
            for doc in parsed_docs:
                logger.info(f"  - {doc['filename']}")
                ingested_files.append(doc['filename'])
            
            # Step 2: Create hierarchical chunks
            all_chunks = []
            for doc in parsed_docs:
                chunks = self.chunker.chunk_document(
                    filename=doc["filename"],
                    collection=collection_name.value,
                    access_roles=access_roles,
                    text=doc.get("text", ""),
                )
                all_chunks.extend(chunks)
            
            if not all_chunks:
                logger.warning(f"No chunks created for {collection_name.value}")
                return True, ingested_files
            
            # Step 3: Store in vector database
            success = self.vector_store.store_chunks(
                chunks=all_chunks,
                collection_name=collection_name.value,
            )
            
            if success:
                logger.info(
                    f"Successfully ingested collection '{collection_name.value}': "
                    f"{len(parsed_docs)} documents → {len(all_chunks)} chunks"
                )
            
            return success, ingested_files
        
        except Exception as e:
            logger.error(f"Error ingesting collection {collection_name.value}: {str(e)}")
            return False, []
    
    def ingest_all_collections(self) -> dict:
        """
        Ingest all configured document collections.
        
        Returns:
            Dictionary mapping collection names to ingestion success status
        """
        results = {}
        
        for collection in DocumentCollection:
            config = COLLECTION_CONFIGS.get(collection)
            if not config:
                logger.warning(f"No config found for collection: {collection.value}")
                results[collection.value] = False
                continue
            
            folder_path = config["path"]
            success, files = self.ingest_collection(collection, folder_path)
            results[collection.value] = {
                "success": success,
                "files": files,
                "count": len(files)
            }
        
        # Summary
        successful = sum(1 for v in results.values() if v["success"])
        logger.info(f"Ingestion complete: {successful}/{len(results)} collections successful")
        
        return results
    
    def verify_ingestion(self) -> dict:
        """
        Verify that all collections have been properly ingested.
        
        Returns:
            Dictionary with verification results
        """
        stats = {}
        
        for collection in DocumentCollection:
            collection_stats = self.vector_store.get_collection_stats(collection.value)
            if collection_stats:
                stats[collection.value] = collection_stats
            else:
                stats[collection.value] = {
                    "name": collection.value,
                    "points_count": 0,
                    "vectors_count": 0,
                }
        
        return stats


def main():
    """
    Run ingestion for all collections.
    This is called when the module is run directly.
    """
    import logging.config
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    logger.info("="*60)
    logger.info("FinBot Document Ingestion")
    logger.info("="*60)
    
    ingester = DocumentIngester()
    results = ingester.ingest_all_collections()
    
    logger.info("\n" + "="*60)
    logger.info("Ingestion Results:")
    logger.info("="*60)
    
    for collection, result in results.items():
        status = "✓ SUCCESS" if result["success"] else "✗ FAILED"
        logger.info(f"{collection:20s} {status} ({result['count']} files)")
        for file in result["files"]:
            logger.info(f"  - {file}")
    
    logger.info("\n" + "="*60)
    logger.info("Collection Statistics:")
    logger.info("="*60)
    
    stats = ingester.verify_ingestion()
    for collection, stat in stats.items():
        logger.info(
            f"{collection:20s} {stat['points_count']:4d} chunks "
            f"({stat['vectors_count']:4d} vectors)"
        )
    
    logger.info("="*60)


if __name__ == "__main__":
    main()
