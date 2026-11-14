"""
Découpage du corpus (chunking) par sections Markdown.

Justification : les fiches sont des textes réglementaires organisés par titres (H1 > H2 > H3),
chaque section traitant d'un sujet précis (un barème, une condition, un montant). On coupe donc
sur les titres plutôt qu'à taille fixe, pour qu'un passage ne mélange pas deux règles.
Chaque chunk est préfixé par son chemin de titres (« Bourses CROUS > Échelons et montants »)
afin de rester compréhensible isolément, pour le retriever comme pour le LLM.
Une section plus longue que RAG_CHUNK_SIZE est recoupée par paragraphes / items de liste.
"""
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List

from src.config import RAG_CHUNK_SIZE

HEADER_RE = re.compile(r"^(#{1,3})\s+(.*)$")


@dataclass
class DocumentChunk:
    chunk_id: str
    doc_name: str
    section_title: str
    content: str  # texte injecté dans le prompt (préfixé par le chemin de titres)


def _split_long(lines: List[str], max_chars: int) -> List[str]:
    """Regroupe des lignes en blocs d'au plus ~max_chars sans couper une ligne."""
    blocks, current = [], []
    for line in lines:
        if current and sum(len(l) for l in current) + len(line) > max_chars:
            blocks.append("\n".join(current).strip())
            current = []
        current.append(line)
    if current:
        blocks.append("\n".join(current).strip())
    return [b for b in blocks if b]


class DocumentChunker:
    def __init__(self, chunk_size: int = RAG_CHUNK_SIZE):
        self.chunk_size = chunk_size

    def process_document(self, file_path: Path) -> List[DocumentChunk]:
        doc_name = file_path.name
        titles = {1: "", 2: "", 3: ""}
        sections: List[tuple] = []  # (chemin de titres, lignes)
        current: List[str] = []

        def flush():
            body = [l for l in current if l.strip()]
            if body:
                path = " > ".join(t for t in (titles[1], titles[2], titles[3]) if t)
                sections.append((path, body))

        for line in file_path.read_text(encoding="utf-8").splitlines():
            m = HEADER_RE.match(line.strip())
            if m:
                flush()
                current = []
                level = len(m.group(1))
                titles[level] = m.group(2).strip()
                for deeper in range(level + 1, 4):
                    titles[deeper] = ""
            else:
                current.append(line)
        flush()

        chunks: List[DocumentChunk] = []
        for path, body in sections:
            for block in _split_long(body, self.chunk_size):
                if len(block) < 30:
                    continue
                chunks.append(DocumentChunk(
                    chunk_id=f"{doc_name}#{len(chunks) + 1:02d}",
                    doc_name=doc_name,
                    section_title=path,
                    content=f"[{path}]\n{block}",
                ))
        return chunks

    def process_directory(self, dir_path: Path) -> List[DocumentChunk]:
        chunks: List[DocumentChunk] = []
        for file_path in sorted(dir_path.glob("*.md")):
            chunks.extend(self.process_document(file_path))
        return chunks
