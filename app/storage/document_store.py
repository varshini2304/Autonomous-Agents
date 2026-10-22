import uuid
from pathlib import Path

class DocumentStore:
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir).resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._documents: dict[str, Path] = {}
    def save(self, path: Path) -> str:
        resolved = Path(path).resolve()
        if resolved.parent != self.output_dir or resolved.suffix.lower() != ".docx" or not resolved.is_file():
            raise ValueError("Document must be an existing DOCX inside the configured output directory")
        try:
            document_id = str(uuid.UUID(resolved.stem))
        except ValueError as exc:
            raise ValueError("Generated document filename must use a UUID") from exc
        self._documents[document_id] = resolved
        return document_id
    def get(self, document_id: str) -> Path | None:
        try:
            canonical_id = str(uuid.UUID(document_id))
        except (ValueError, TypeError, AttributeError):
            return None
        if canonical_id != document_id.lower():
            return None
        # The filename is the durable index. This works across API workers and
        # process restarts as long as they share the configured output volume.
        path = self._documents.get(canonical_id, self.output_dir / f"{canonical_id}.docx")
        resolved = path.resolve()
        if resolved.parent != self.output_dir or resolved.suffix.lower() != ".docx":
            return None
        return resolved if resolved.is_file() else None
