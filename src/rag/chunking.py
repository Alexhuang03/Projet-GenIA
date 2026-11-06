"""
Module de découpage documentaire (Chunking) avec métadonnées
Justification : Les documents réglementaires et administratifs sont organisés hiérarchiquement
par sections (Titres H1/H2). Le découpage segmente par paragraphe tout en préservant le titre
de la section pour que chaque chunk soit sémantiquement autonome.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import List
import re
from src.config import RAG_CHUNK_SIZE, RAG_CHUNK_OVERLAP


@dataclass
class DocumentChunk:
    chunk_id: str
    doc_name: str
    section_title: str
    content: str
    char_length: int


class DocumentChunker:
    def __init__(self, chunk_size: int = RAG_CHUNK_SIZE, overlap: int = RAG_CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def process_document(self, file_path: Path) -> List[DocumentChunk]:
        """Découpe un fichier markdown en chunks enrichis avec leurs métadonnées de section."""
        text = file_path.read_text(encoding="utf-8")
        doc_name = file_path.name
        
        chunks: List[DocumentChunk] = []
        current_section = "Introduction"
        
        # Découpage par bloc de lignes
        lines = text.split("\n")
        current_block: List[str] = []
        current_len = 0
        chunk_idx = 0

        for line in lines:
            # Détection de titre Markdown (H1, H2, H3)
            header_match = re.match(r"^(#{1,3})\s+(.*)$", line.strip())
            if header_match:
                # Flush du bloc précédent si non vide
                if current_block:
                    block_text = "\n".join(current_block).strip()
                    if len(block_text) > 30: # Ignorer les blocs quasi vides
                        chunk_idx += 1
                        full_content = f"[{current_section}]\n{block_text}"
                        chunks.append(DocumentChunk(
                            chunk_id=f"{doc_name}_chunk_{chunk_idx:02d}",
                            doc_name=doc_name,
                            section_title=current_section,
                            content=full_content,
                            char_length=len(full_content)
                        ))
                    current_block = []
                    current_len = 0
                current_section = header_match.group(2).strip()
                continue

            if not line.strip():
                if current_len >= self.chunk_size:
                    chunk_idx += 1
                    block_text = "\n".join(current_block).strip()
                    full_content = f"[{current_section}]\n{block_text}"
                    chunks.append(DocumentChunk(
                        chunk_id=f"{doc_name}_chunk_{chunk_idx:02d}",
                        doc_name=doc_name,
                        section_title=current_section,
                        content=full_content,
                        char_length=len(full_content)
                    ))
                    # Conservation du chevauchement (overlap)
                    overlap_lines = current_block[-2:] if len(current_block) >= 2 else current_block
                    current_block = list(overlap_lines)
                    current_len = sum(len(l) for l in current_block)
                continue

            current_block.append(line)
            current_len += len(line)

        # Dernier bloc restant
        if current_block:
            block_text = "\n".join(current_block).strip()
            if len(block_text) > 30:
                chunk_idx += 1
                full_content = f"[{current_section}]\n{block_text}"
                chunks.append(DocumentChunk(
                    chunk_id=f"{doc_name}_chunk_{chunk_idx:02d}",
                    doc_name=doc_name,
                    section_title=current_section,
                    content=full_content,
                    char_length=len(full_content)
                ))

        return chunks

    def process_directory(self, dir_path: Path) -> List[DocumentChunk]:
        """Traite tous les fichiers Markdown du corpus."""
        all_chunks = []
        for file_path in sorted(dir_path.glob("*.md")):
            all_chunks.extend(self.process_document(file_path))
        return all_chunks
