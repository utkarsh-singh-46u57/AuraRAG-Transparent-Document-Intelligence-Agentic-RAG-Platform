from typing import List, Optional
import re
from app.models.domain import DocumentChunk
from app.services.document_parser import ParsedDocument, ParsedBlock
from app.config import settings

class RecursiveChunker:
    """
    Recursively splits parsed document blocks into structured chunks
    while preserving page numbers, paragraph positions, section headings,
    and bounding boxes.
    """

    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self.chunk_size = chunk_size or settings.DEFAULT_CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.DEFAULT_CHUNK_OVERLAP

    def _split_text_recursively(self, text: str) -> List[str]:
        """
        Recursively splits text using paragraph, sentence, and word boundaries.
        """
        if len(text) <= self.chunk_size:
            return [text.strip()] if text.strip() else []

        separators = ["\n\n", "\n", ". ", "? ", "! ", " ", ""]
        return self._recursive_split(text, separators, self.chunk_size, self.chunk_overlap)

    def _recursive_split(self, text: str, separators: List[str], max_len: int, overlap: int) -> List[str]:
        if not separators:
            # Fallback to hard split
            return [text[i:i + max_len] for i in range(0, len(text), max_len - overlap)]

        sep = separators[0]
        remaining_seps = separators[1:]
        
        parts = text.split(sep) if sep else list(text)
        chunks = []
        current_chunk = []
        current_len = 0

        for part in parts:
            part_len = len(part) + len(sep)
            if current_len + part_len <= max_len:
                current_chunk.append(part)
                current_len += part_len
            else:
                if current_chunk:
                    joined = sep.join(current_chunk).strip()
                    if joined:
                        chunks.append(joined)
                    # Handle overlap by keeping the trailing items
                    overlap_chunk = []
                    overlap_len = 0
                    for prev_part in reversed(current_chunk):
                        if overlap_len + len(prev_part) + len(sep) <= overlap:
                            overlap_chunk.insert(0, prev_part)
                            overlap_len += len(prev_part) + len(sep)
                        else:
                            break
                    current_chunk = overlap_chunk
                    current_len = overlap_len

                # If single part is larger than max_len, split it with next separator
                if len(part) > max_len:
                    sub_chunks = self._recursive_split(part, remaining_seps, max_len, overlap)
                    chunks.extend(sub_chunks)
                    current_chunk = []
                    current_len = 0
                else:
                    current_chunk.append(part)
                    current_len += len(part) + len(sep)

        if current_chunk:
            final_joined = sep.join(current_chunk).strip()
            if final_joined:
                chunks.append(final_joined)

        return chunks

    def chunk_document(self, parsed_doc: ParsedDocument) -> List[DocumentChunk]:
        """
        Generates structured DocumentChunks from parsed blocks.
        """
        chunks: List[DocumentChunk] = []
        current_heading: Optional[str] = None
        chunk_sequence = 1

        for block in parsed_doc.blocks:
            if block.is_heading:
                current_heading = block.text.split("\n")[0][:80]

            # Split block text if larger than chunk size
            sub_texts = self._split_text_recursively(block.text)

            for sub_idx, sub_text in enumerate(sub_texts):
                if not sub_text:
                    continue

                chunk_id = f"chk_p{block.page_number:02d}_b{block.block_number:02d}_{chunk_sequence:03d}"
                chunks.append(
                    DocumentChunk(
                        document_id=parsed_doc.document_id,
                        chunk_id=chunk_id,
                        page_number=block.page_number,
                        paragraph_number=block.block_number,
                        section_heading=current_heading,
                        text=sub_text,
                        bbox=block.bbox,
                        char_count=len(sub_text),
                        token_estimate=max(1, len(sub_text) // 4)
                    )
                )
                chunk_sequence += 1

        return chunks

chunker = RecursiveChunker()
