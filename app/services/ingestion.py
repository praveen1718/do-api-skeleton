"""Business logic for ingestion + processing.

Kept deliberately separate from the HTTP layer (app/api) so it can be
unit-tested without spinning up a server, and swapped for a real
datastore later. Right now it uses an in-memory store — on the day,
replace `_store` with a DB/queue/object-storage client as required.
"""
from __future__ import annotations

from app.models.schemas import DataRecord, ProcessedResult


class IngestionService:
    def __init__(self, max_batch_size: int) -> None:
        self._max_batch_size = max_batch_size
        self._store: list[DataRecord] = []

    def ingest(self, records: list[DataRecord]) -> tuple[int, int]:
        """Store valid records. Returns (accepted, rejected).

        Pydantic already validated structure; here we apply *business*
        rules (batch caps, dedup) and count anything we choose to drop.
        """
        accepted = 0
        rejected = 0
        seen_ids = {r.id for r in self._store}

        for record in records[: self._max_batch_size]:
            if record.id in seen_ids:  # idempotency: skip duplicates
                rejected += 1
                continue
            self._store.append(record)
            seen_ids.add(record.id)
            accepted += 1

        # Anything beyond the batch cap is counted as rejected, not silently lost.
        rejected += max(0, len(records) - self._max_batch_size)
        return accepted, rejected

    def process(self) -> ProcessedResult:
        """A trivial aggregation to demonstrate the 'processing' half.

        Replace with the real transform the challenge asks for.
        """
        values = [r.value for r in self._store]
        if not values:
            return ProcessedResult(count=0, sum=0.0, mean=0.0, min=0.0, max=0.0)
        total = sum(values)
        return ProcessedResult(
            count=len(values),
            sum=total,
            mean=total / len(values),
            min=min(values),
            max=max(values),
        )

    def clear(self) -> None:
        self._store.clear()
