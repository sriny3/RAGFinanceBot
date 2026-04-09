"""
Document parsing module using Docling.
Parses PDFs, DOCX, Markdown, and CSV files while preserving structural hierarchy.
"""

import logging
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
import hashlib
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat

logger = logging.getLogger(__name__)


class DoclingParser:
    """
    Parser for documents using the Docling library.
    Extracts hierarchical structure from PDFs, DOCX, and Markdown.
    """
    
    def __init__(self):
        """Initialize the Docling parser with OCR disabled."""
        # Disable OCR to avoid RapidOCR and speed up parsing as per user request and requirements check
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True  # Enable OCR for scanned PDFs, but can be set to False if not needed
        
        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
    
    def parse_document(self, file_path: str) -> Optional[dict]:
        """
        Parse a document and extract its hierarchical structure.
        
        Args:
            file_path: Path to the document file (PDF, DOCX, Markdown, or CSV)
            
        Returns:
            Dictionary with document content and structure, or None if parsing fails
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                logger.error(f"File not found: {file_path}")
                return None
            
            logger.info(f"Parsing document: {path.name}")
            
            # Parse document using Docling
            result = self.converter.convert(path)
            
            if not result:
                logger.warning(f"No content extracted from {path.name}")
                return None
            
            return {
                "document": result.document,
                "filename": path.name,
                "path": str(path)
            }
            
        except Exception as e:
            logger.error(f"Error parsing document {file_path}: {str(e)}")
            return None
    
    def extract_hierarchy(self, doc_dict: dict) -> List[Tuple[int, Dict[str, Any], Optional[str]]]:
        """
        Extract hierarchical structure from parsed document using Docling 2.x export_to_dict.
        Returns list of (depth, element_info, parent_id) tuples.
        """
        if not doc_dict or "document" not in doc_dict:
            return []
        
        hierarchy = []
        doc = doc_dict["document"]
        filename = doc_dict["filename"]
        
        try:
            # Use export_to_dict for maximum compatibility across Docling 2 models
            doc_data = doc.export_to_dict()
            elements = doc_data.get("elements", [])
            
            for idx, item in enumerate(elements):
                element_id = f"{filename}_{idx}"
                level = item.get("level", 0)
                
                # Element Metadata
                element_info = {
                    "id": element_id,
                    "type": item.get("label", "text"),
                    "depth": level,
                    "text": item.get("text", ""),
                }
                
                if "heading" in item.get("label", "").lower():
                    element_info["is_heading"] = True
                
                # Parent tracking from dict
                parent_id = None
                parent_idx = item.get("parent")
                if parent_idx is not None and isinstance(parent_idx, int):
                    parent_id = f"{filename}_{parent_idx}"
                
                hierarchy.append((level, element_info, parent_id))
                
        except Exception as e:
            logger.error(f"Error extracting hierarchy from {filename}: {str(e)}")
            # Minimal fallback using markdown export if structure extraction fails entirely
            try:
                hierarchy = [(0, {
                    "id": f"{filename}_0", 
                    "type": "text", 
                    "depth": 0, 
                    "text": doc.export_to_markdown()
                }, None)]
            except:
                hierarchy = []
        
        return hierarchy

    def _generate_element_id(self, filename: str, level: int, ref: str) -> str:
        """Helper to generate consistent element IDs."""
        id_str = f"{filename}_{level}_{ref}"
        return hashlib.md5(id_str.encode()).hexdigest()

def parse_all_documents(docs_folder: str) -> List[dict]:
    """
    Parses all documents in the given folder.
    
    Args:
        docs_folder: Path to the directory containing documents.
        
    Returns:
        List of parsed document dictionaries.
    """
    parser = DoclingParser()
    parsed_docs = []
    
    folder_path = Path(docs_folder)
    if not folder_path.exists():
        logger.error(f"Documents folder not found: {docs_folder}")
        return []

    # Supported formats: pdf, docx, md, csv (Docling has built-in CSV backend)
    extensions = [".pdf", ".docx", ".md", ".csv"]
    for ext in extensions:
        # Use rglob for recursive search across subfolders
        # Note: glob in Path is case-sensitive on some systems; rglob handles recursion
        for file_path in folder_path.rglob(f"*{ext}"):
            doc_dict = parser.parse_document(str(file_path))
            if doc_dict:
                # Add relative path for better identification in case of name collisions
                try:
                    rel_path = file_path.relative_to(folder_path)
                    doc_dict["filename"] = str(rel_path)
                except ValueError:
                    pass
                
                # Add text field back for backward compatibility with tests/scripts
                try:
                    doc_dict["text"] = doc_dict["document"].export_to_markdown()
                except Exception as e:
                    logger.warning(f"Failed to export markdown for {file_path}: {e}")
                    doc_dict["text"] = ""
                parsed_docs.append(doc_dict)
                
    return parsed_docs
