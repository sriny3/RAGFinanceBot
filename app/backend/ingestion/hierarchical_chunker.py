"""
Hierarchical chunking module.
Breaks documents into chunks while preserving hierarchical context and creating parent summaries.
"""

import logging
from typing import List, Optional, Dict
from metadata_schema import Chunk, ChunkType
from config import CHUNKING_CONFIG

logger = logging.getLogger(__name__)


class HierarchicalChunker:
    """
    Chunks documents while preserving hierarchical structure.
    Creates parent section summaries and maintains linkage between chunks.
    """
    
    def __init__(
        self,
        max_leaf_tokens: int = CHUNKING_CONFIG["max_leaf_chunk_tokens"],
        overlap_tokens: int = CHUNKING_CONFIG["overlap_tokens"],
        min_chunk_tokens: int = CHUNKING_CONFIG["min_chunk_tokens"],
    ):
        """
        Initialize hierarchical chunker.
        
        Args:
            max_leaf_tokens: Maximum tokens in a leaf chunk
            overlap_tokens: Number of tokens to overlap between chunks
            min_chunk_tokens: Minimum tokens to keep a chunk
        """
        self.max_leaf_tokens = max_leaf_tokens
        self.overlap_tokens = overlap_tokens
        self.min_chunk_tokens = min_chunk_tokens
    
    def chunk_document(
        self,
        filename: str,
        collection: str,
        access_roles: List[str],
        text: str,
        hierarchy_info: Optional[List[dict]] = None,
    ) -> List[Chunk]:
        """
        Break a document into hierarchical chunks with metadata.
        
        Args:
            filename: Source document filename
            collection: Document collection (general, finance, etc.)
            access_roles: List of roles that can access this document
            text: Full document text
            hierarchy_info: Optional list of hierarchy elements with titles
            
        Returns:
            List of Chunk objects with complete metadata
        """
        chunks = []
        chunk_counter = 0
        
        # Split into paragraphs/sections
        paragraphs = self._split_into_paragraphs(text)
        
        # Build parent summary structure
        section_summaries = self._build_section_summaries(
            paragraphs,
            filename,
            collection,
            access_roles
        )
        
        for para_idx, paragraph in enumerate(paragraphs):
            if not paragraph.strip():
                continue
            
            # Determine section for this paragraph
            section_info = self._get_section_for_paragraph(
                para_idx, section_summaries
            )
            
            # Further split long paragraphs into leaf chunks
            leaf_chunks = self._split_paragraph_into_chunks(paragraph)
            
            for chunk_idx, chunk_text in enumerate(leaf_chunks):
                if len(chunk_text.strip().split()) < self.min_chunk_tokens:
                    continue
                
                # Determine chunk type
                chunk_type = self._get_chunk_type(chunk_text)
                
                # Create chunk object
                safe_filename = filename.replace(".", "_").replace("/", "__").replace("\\", "__")
                chunk = Chunk(
                    id=f"{safe_filename}_{chunk_counter}",
                    text=chunk_text,
                    source_document=filename,
                    collection=collection,
                    access_roles=access_roles,
                    section_title=section_info["section_title"],
                    subsection_title=section_info.get("subsection_title"),
                    page_number=section_info.get("page_number", 1),
                    chunk_type=chunk_type,
                    parent_chunk_id=section_info.get("parent_chunk_id"),
                    parent_summary=section_info.get("parent_summary"),
                    depth=section_info.get("depth", 0),
                )
                
                chunks.append(chunk)
                chunk_counter += 1
        
        logger.info(
            f"Created {len(chunks)} chunks from {filename} "
            f"({collection} collection, accessible by {access_roles})"
        )
        
        return chunks
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """
        Split text into logical paragraphs.
        
        Args:
            text: Full document text
            
        Returns:
            List of paragraphs
        """
        # Split by double newlines (paragraphs) or markdown headers
        paragraphs = []
        current = []
        
        for line in text.split("\n"):
            # Treat headers as paragraph breaks
            if line.strip().startswith("#") or (current and not line.strip()):
                if current:
                    paragraphs.append("\n".join(current).strip())
                    current = []
                if line.strip():
                    paragraphs.append(line.strip())
            else:
                current.append(line)
        
        if current:
            paragraphs.append("\n".join(current).strip())
        
        return [p for p in paragraphs if p.strip()]
    
    def _split_paragraph_into_chunks(self, paragraph: str) -> List[str]:
        """
        Split a paragraph into leaf chunks based on token limit.
        
        Args:
            paragraph: Paragraph text
            
        Returns:
            List of chunk texts
        """
        # Simple token estimation (words ≈ tokens)
        words = paragraph.split()
        chunks = []
        current_chunk = []
        current_word_count = 0
        
        for word in words:
            current_chunk.append(word)
            current_word_count += 1
            
            # If we hit max size, create chunk
            if current_word_count >= self.max_leaf_tokens:
                chunks.append(" ".join(current_chunk))
                # Keep overlap
                overlap_start = max(0, len(current_chunk) - self.overlap_tokens)
                current_chunk = current_chunk[overlap_start:]
                current_word_count = len(current_chunk)
        
        # Add remaining words
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks
    
    def _build_section_summaries(
        self,
        paragraphs: List[str],
        filename: str,
        collection: str,
        access_roles: List[str],
    ) -> Dict[int, dict]:
        """
        Build section summary information by identifying headers and grouping content.
        
        Args:
            paragraphs: List of paragraphs
            filename: Source filename
            collection: Document collection
            access_roles: Accessible roles
            
        Returns:
            Dictionary mapping paragraph indices to section info
        """
        section_info = {}
        current_section = None
        current_subsection = None
        current_depth = 0
        parents = {}  # depth -> parent_chunk_id mapping
        
        for idx, para in enumerate(paragraphs):
            para_stripped = para.strip()
            
            # Detect heading level
            depth = self._get_heading_level(para_stripped)
            
            if depth is not None:
                # This is a header
                title = para_stripped.lstrip("#").strip()
                
                if depth == 1:
                    current_section = title
                    current_subsection = None
                    parents[1] = f"{filename.replace('.', '_')}_section_{current_section.replace(' ', '_')}"
                elif depth == 2:
                    current_subsection = title
                    parents[2] = f"{filename.replace('.', '_')}_subsection_{title.replace(' ', '_')}"
                
                current_depth = depth
            
            # Store section info for this paragraph
            section_info[idx] = {
                "section_title": current_section or "General",
                "subsection_title": current_subsection,
                "parent_chunk_id": parents.get(current_depth),
                "parent_summary": None,  # Would be populated by LLM in production
                "depth": current_depth or 0,
                "page_number": 1,  # Would be extracted from actual documents
            }
        
        return section_info
    
    def _get_section_for_paragraph(
        self,
        para_idx: int,
        section_summaries: Dict[int, dict],
    ) -> dict:
        """
        Get section information for a specific paragraph.
        
        Args:
            para_idx: Paragraph index
            section_summaries: Section summary dictionary
            
        Returns:
            Section info for this paragraph
        """
        # Find the most recent header before this paragraph
        for idx in range(para_idx, -1, -1):
            if idx in section_summaries:
                return section_summaries[idx]
        
        # Default if no header found
        return {
            "section_title": "General",
            "depth": 0,
        }
    
    def _get_heading_level(self, text: str) -> Optional[int]:
        """
        Detect markdown heading level.
        
        Args:
            text: Text to check
            
        Returns:
            Heading level (1-6) or None if not a heading
        """
        if text.startswith("######"):
            return 6
        elif text.startswith("#####"):
            return 5
        elif text.startswith("####"):
            return 4
        elif text.startswith("###"):
            return 3
        elif text.startswith("##"):
            return 2
        elif text.startswith("#"):
            return 1
        return None
    
    def _get_chunk_type(self, text: str) -> ChunkType:
        """
        Determine chunk type based on content.
        
        Args:
            text: Chunk text
            
        Returns:
            ChunkType enum value
        """
        # Simple heuristics
        if "```" in text:
            return ChunkType.CODE
        elif "|" in text and "-" in text:  # Simple table detection
            return ChunkType.TABLE
        elif text.strip().startswith("#"):
            return ChunkType.HEADING
        else:
            return ChunkType.TEXT


def chunk_parsed_documents(
    parsed_docs: List[dict],
    collection: str,
    access_roles: List[str],
) -> List[Chunk]:
    """
    Chunk a list of parsed documents.
    
    Args:
        parsed_docs: List of document dictionaries from docling_parser
        collection: Document collection name
        access_roles: List of roles that can access these documents
        
    Returns:
        List of Chunk objects
    """
    chunker = HierarchicalChunker()
    all_chunks = []
    
    for doc in parsed_docs:
        chunks = chunker.chunk_document(
            filename=doc["filename"],
            collection=collection,
            access_roles=access_roles,
            text=doc.get("text", ""),
        )
        all_chunks.extend(chunks)
    
    logger.info(f"Chunked {len(parsed_docs)} documents into {len(all_chunks)} chunks")
    return all_chunks
