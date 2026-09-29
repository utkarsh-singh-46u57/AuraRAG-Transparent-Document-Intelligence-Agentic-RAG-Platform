import fitz  # PyMuPDF
from typing import List, Dict, Any, Optional
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class ParsedBlock(BaseModel):
    page_number: int
    block_number: int
    text: str
    bbox: list[float]  # [x0, y0, x1, y1] normalized or points
    is_heading: bool = False
    estimated_font_size: float = 12.0
    char_count: int = 0

class ParsedDocument(BaseModel):
    document_id: str
    filename: str
    total_pages: int
    total_characters: int
    blocks: List[ParsedBlock]
    is_scanned: bool = False
    page_dimensions: Dict[int, dict] = {}  # page -> {width, height}

class DocumentParser:
    """
    Extracts structured layout-aware text and bounding boxes from PDF documents
    using PyMuPDF (fitz) with OCR fallback detection.
    """

    def parse_pdf_bytes(self, file_bytes: bytes, filename: str, document_id: str) -> ParsedDocument:
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
        except Exception as e:
            logger.error(f"Failed to open PDF stream for {filename}: {str(e)}")
            raise ValueError(f"Invalid PDF file: {str(e)}")

        total_pages = len(doc)
        total_chars = 0
        all_blocks: List[ParsedBlock] = []
        page_dimensions: Dict[int, dict] = {}
        low_density_pages = 0

        for page_idx in range(total_pages):
            page_num = page_idx + 1
            page = doc[page_idx]
            rect = page.rect
            width, height = rect.width, rect.height
            page_dimensions[page_num] = {"width": width, "height": height}

            # Extract detailed block text with font sizes if possible
            # First extract blocks
            raw_blocks = page.get_text("blocks")  # (x0, y0, x1, y1, text, block_no, block_type)
            page_char_count = 0

            # Also check text dict for font size statistics
            page_dict = page.get_text("dict")
            avg_font_size = 11.0
            sizes = []
            for block in page_dict.get("blocks", []):
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line.get("spans", []):
                            if span.get("size"):
                                sizes.append(span["size"])
            if sizes:
                avg_font_size = sum(sizes) / len(sizes)

            for b_idx, block in enumerate(raw_blocks):
                # block type 0 is text, 1 is image
                if len(block) >= 5 and block[6] == 0 if len(block) > 6 else True:
                    x0, y0, x1, y1 = block[0], block[1], block[2], block[3]
                    text = str(block[4]).strip()
                    if not text:
                        continue

                    page_char_count += len(text)
                    total_chars += len(text)

                    # Normalize coordinates relative to page width and height for client rendering
                    norm_bbox = [
                        round((x0 / width) * 100.0, 2) if width > 0 else round(x0, 2),
                        round((y0 / height) * 100.0, 2) if height > 0 else round(y0, 2),
                        round((x1 / width) * 100.0, 2) if width > 0 else round(x1, 2),
                        round((y1 / height) * 100.0, 2) if height > 0 else round(y1, 2),
                    ]

                    # Detect if block appears to be a heading (short text, large font or uppercase/numbering)
                    is_heading = False
                    first_line = text.split("\n")[0].strip()
                    if len(text) < 120 and (first_line.isupper() or first_line.startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "Chapter", "Section", "Table of Contents"))):
                        is_heading = True

                    all_blocks.append(
                        ParsedBlock(
                            page_number=page_num,
                            block_number=b_idx,
                            text=text,
                            bbox=norm_bbox,
                            is_heading=is_heading,
                            estimated_font_size=avg_font_size,
                            char_count=len(text)
                        )
                    )

            if page_char_count < 50:
                low_density_pages += 1
                logger.info(f"Page {page_num} in {filename} has low text density ({page_char_count} chars). Scanned document hook active.")

        # If more than 60% of pages are low density, flag as scanned
        is_scanned = (low_density_pages / total_pages >= 0.6) if total_pages > 0 else False

        doc.close()

        return ParsedDocument(
            document_id=document_id,
            filename=filename,
            total_pages=total_pages,
            total_characters=total_chars,
            blocks=all_blocks,
            is_scanned=is_scanned,
            page_dimensions=page_dimensions
        )

document_parser = DocumentParser()
