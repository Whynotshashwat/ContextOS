import json
from pathlib import Path
from datetime import datetime
from typing import Optional


class Memory:

    def __init__(self, contextos_dir: Path):
        self.contextos_dir = contextos_dir
        self.memory_path = contextos_dir / "memory.json"
        self.decisions_path = contextos_dir / "decisions.json"
        self.snapshots_dir = contextos_dir / "snapshots"
        self.logs_dir = contextos_dir / "logs"
        self._ensure_files()

    # --- Setup ---

    def _ensure_files(self):
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        if not self.memory_path.exists():
            self._write_json(self.memory_path, {
                "snapshots": [],
                "compressed_history": [],
                "last_compressed": None
            })

        if not self.decisions_path.exists():
            self._write_json(self.decisions_path, {
                "decisions": []
            })

    # --- Helpers ---

    def _write_json(self, path: Path, data: dict):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _read_json(self, path: Path) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    # --- Decisions ---

    def add_decision(
        self,
        task_id: str,
        selected_option: str,
        rationale: str = "user selected"
    ) -> dict:
        data = self._read_json(self.decisions_path)
        decision = {
            "id": f"d{len(data['decisions']) + 1}",
            "task_id": task_id,
            "selected_option": selected_option,
            "rationale": rationale,
            "timestamp": datetime.now().isoformat()
        }
        data["decisions"].append(decision)
        self._write_json(self.decisions_path, data)
        return decision

    def get_decisions(self) -> list:
        data = self._read_json(self.decisions_path)
        return data["decisions"]

    def get_decisions_for_task(self, task_id: str) -> list:
        return [
            d for d in self.get_decisions()
            if d["task_id"] == task_id
        ]

    # --- Snapshots ---

    def take_snapshot(self, aicf_data: dict, label: str = "") -> str:
        data = self._read_json(self.memory_path)
        snapshot_id = f"snap_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        snapshot_path = self.snapshots_dir / f"{snapshot_id}.json"

        snapshot = {
            "id": snapshot_id,
            "label": label,
            "timestamp": datetime.now().isoformat(),
            "aicf": aicf_data
        }

        self._write_json(snapshot_path, snapshot)

        data["snapshots"].append({
            "id": snapshot_id,
            "label": label,
            "timestamp": snapshot["timestamp"]
        })

        # Keep max 10 snapshots
        if len(data["snapshots"]) > 10:
            oldest = data["snapshots"].pop(0)
            old_path = self.snapshots_dir / f"{oldest['id']}.json"
            if old_path.exists():
                old_path.unlink()

        self._write_json(self.memory_path, data)
        return snapshot_id

    def get_snapshots(self) -> list:
        data = self._read_json(self.memory_path)
        return data["snapshots"]

    def restore_snapshot(self, snapshot_id: str) -> Optional[dict]:
        snapshot_path = self.snapshots_dir / f"{snapshot_id}.json"
        if not snapshot_path.exists():
            return None
        data = self._read_json(snapshot_path)
        return data["aicf"]

    # --- Compressed History ---

    def add_to_history(self, entry: dict):
        data = self._read_json(self.memory_path)
        entry["timestamp"] = datetime.now().isoformat()
        data["compressed_history"].append(entry)
        data["last_compressed"] = datetime.now().isoformat()
        self._write_json(self.memory_path, data)

    def get_history(self) -> list:
        data = self._read_json(self.memory_path)
        return data["compressed_history"]

    # --- Logs ---

    def log(self, message: str, level: str = "INFO"):
        log_file = self.logs_dir / f"{datetime.now().strftime('%Y-%m-%d')}.log"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] [{level}] {message}\n")