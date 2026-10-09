import json
import os
import threading
from typing import Dict, List, Optional
from app.models.audit import AuditRecord
from app.models.action import ActionContract

DB_FILE_PATH = os.path.join(os.path.dirname(__file__), "audit_store.json")

class AuditDatabase:
    def __init__(self, storage_path: str = DB_FILE_PATH):
        self.storage_path = storage_path
        self._lock = threading.Lock()
        self._records: Dict[str, AuditRecord] = {}
        self._load()

    def _load(self):
        with self._lock:
            if os.path.exists(self.storage_path):
                try:
                    with open(self.storage_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        for item in data:
                            rec = AuditRecord(**item)
                            self._records[rec.action_id] = rec
                except Exception as e:
                    print(f"[AuditDatabase] Error loading existing audit store: {e}")

    def _save(self):
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump([rec.model_dump() for rec in self._records.values()], f, indent=2)
        except Exception as e:
            print(f"[AuditDatabase] Error saving audit store: {e}")

    def save_record(self, record: AuditRecord):
        with self._lock:
            self._records[record.action_id] = record
            self._save()

    def get_record(self, action_id: str) -> Optional[AuditRecord]:
        with self._lock:
            return self._records.get(action_id)

    def list_records(self) -> List[AuditRecord]:
        with self._lock:
            # Sort newest first
            return sorted(list(self._records.values()), key=lambda r: r.timestamp, reverse=True)

    def clear(self):
        with self._lock:
            self._records.clear()
            self._save()

audit_db = AuditDatabase()
