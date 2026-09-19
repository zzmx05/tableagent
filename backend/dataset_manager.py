"""Versioned dataset storage.

Layout:
    runtime/datasets/
        {dataset_id}/
            metadata.json
            versions/
                v000.pkl
                v001.pkl
            operations/
                op_001.json
"""

from __future__ import annotations

import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

DATA_ROOT = Path(
    os.getenv(
        "TABLE_AGENT_DATA",
        Path(__file__).resolve().parent / "runtime" / "datasets",
    )
)

DATA_ROOT.mkdir(parents=True, exist_ok=True)

_VERSION_RE = re.compile(r"^v(\d{3})$")
_OP_RE = re.compile(r"^op_(\d{3})$")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def format_version(index: int) -> str:
    return f"v{index:03d}"


def parse_version(version: str) -> int:
    match = _VERSION_RE.match(version)
    if not match:
        raise ValueError(f"非法版本号: {version}")
    return int(match.group(1))


class DatasetManager:
    def __init__(self, root: Optional[Path] = None):
        self.root = Path(root) if root else DATA_ROOT
        self.root.mkdir(parents=True, exist_ok=True)

    def dataset_dir(self, dataset_id: str) -> Path:
        return self.root / dataset_id

    def metadata_path(self, dataset_id: str) -> Path:
        return self.dataset_dir(dataset_id) / "metadata.json"

    def versions_dir(self, dataset_id: str) -> Path:
        return self.dataset_dir(dataset_id) / "versions"

    def operations_dir(self, dataset_id: str) -> Path:
        return self.dataset_dir(dataset_id) / "operations"

    def version_path(self, dataset_id: str, version: str) -> Path:
        return self.versions_dir(dataset_id) / f"{version}.pkl"

    def exists(self, dataset_id: str) -> bool:
        self._maybe_migrate_legacy(dataset_id)
        return self.metadata_path(dataset_id).exists()

    def create_dataset(
        self,
        df: pd.DataFrame,
        dataset_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not dataset_id:
            dataset_id = f"ds_{uuid.uuid4().hex[:12]}"

        dataset_dir = self.dataset_dir(dataset_id)
        versions_dir = self.versions_dir(dataset_id)
        operations_dir = self.operations_dir(dataset_id)
        versions_dir.mkdir(parents=True, exist_ok=True)
        operations_dir.mkdir(parents=True, exist_ok=True)

        original = self.version_path(dataset_id, "v000")
        if original.exists():
            raise ValueError(f"数据集已存在，禁止覆盖原始版本: {dataset_id}")

        df.to_pickle(original)

        metadata = {
            "dataset_id": dataset_id,
            "created_time": _now_iso(),
            "current_version": "v000",
            "columns": [str(c) for c in df.columns],
            "rows": int(len(df)),
        }
        self._write_metadata(dataset_id, metadata)
        return metadata

    def get_current_version(self, dataset_id: str) -> str:
        return self._read_metadata(dataset_id)["current_version"]

    def load_version(
        self,
        dataset_id: str,
        version: Optional[str] = None,
    ) -> pd.DataFrame:
        if not self.exists(dataset_id):
            raise FileNotFoundError(f"找不到数据集: {dataset_id}")

        target = version or self.get_current_version(dataset_id)
        path = self.version_path(dataset_id, target)
        if not path.exists():
            raise FileNotFoundError(
                f"找不到数据集版本: {dataset_id}/{target}.pkl"
            )
        return pd.read_pickle(path)

    def current_path(self, dataset_id: str) -> Path:
        if not self.exists(dataset_id):
            raise FileNotFoundError(f"找不到数据集: {dataset_id}")
        return self.version_path(dataset_id, self.get_current_version(dataset_id))

    def save_new_version(
        self,
        dataset_id: str,
        df: pd.DataFrame,
        operation_name: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not self.exists(dataset_id):
            raise FileNotFoundError(f"找不到数据集: {dataset_id}")

        input_version = self.get_current_version(dataset_id)
        output_version = self._next_version(dataset_id)
        output_path = self.version_path(dataset_id, output_version)

        if output_version == "v000" or output_path.exists():
            raise ValueError(
                f"禁止覆盖已有版本: {dataset_id}/{output_version}.pkl"
            )

        df.to_pickle(output_path)

        operation = {
            "operation_name": operation_name,
            "input_version": input_version,
            "output_version": output_version,
            "parameters": parameters or {},
            "timestamp": _now_iso(),
        }
        op_id = self._next_operation_id(dataset_id)
        op_path = self.operations_dir(dataset_id) / f"{op_id}.json"
        op_path.write_text(
            json.dumps(operation, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )

        metadata = self._read_metadata(dataset_id)
        metadata["current_version"] = output_version
        metadata["columns"] = [str(c) for c in df.columns]
        metadata["rows"] = int(len(df))
        self._write_metadata(dataset_id, metadata)

        return {
            "dataset_id": dataset_id,
            "operation_id": op_id,
            **operation,
        }

    def list_versions(self, dataset_id: str) -> List[str]:
        if not self.exists(dataset_id):
            raise FileNotFoundError(f"找不到数据集: {dataset_id}")

        versions = []
        for path in self.versions_dir(dataset_id).glob("v*.pkl"):
            if _VERSION_RE.match(path.stem):
                versions.append(path.stem)
        return sorted(versions, key=parse_version)

    def rollback_version(self, dataset_id: str, version: str) -> Dict[str, Any]:
        if version not in self.list_versions(dataset_id):
            raise FileNotFoundError(
                f"找不到数据集版本: {dataset_id}/{version}"
            )

        df = self.load_version(dataset_id, version)
        metadata = self._read_metadata(dataset_id)
        metadata["current_version"] = version
        metadata["columns"] = [str(c) for c in df.columns]
        metadata["rows"] = int(len(df))
        self._write_metadata(dataset_id, metadata)
        return metadata

    def _next_version(self, dataset_id: str) -> str:
        versions = self.list_versions(dataset_id)
        if not versions:
            return "v000"
        return format_version(parse_version(versions[-1]) + 1)

    def _next_operation_id(self, dataset_id: str) -> str:
        ops_dir = self.operations_dir(dataset_id)
        ops_dir.mkdir(parents=True, exist_ok=True)
        numbers = []
        for path in ops_dir.glob("op_*.json"):
            match = _OP_RE.match(path.stem)
            if match:
                numbers.append(int(match.group(1)))
        nxt = (max(numbers) + 1) if numbers else 1
        return f"op_{nxt:03d}"

    def _read_metadata(self, dataset_id: str) -> Dict[str, Any]:
        path = self.metadata_path(dataset_id)
        if not path.exists():
            raise FileNotFoundError(f"找不到数据集: {dataset_id}")
        return json.loads(path.read_text(encoding="utf-8"))

    def _write_metadata(self, dataset_id: str, metadata: Dict[str, Any]) -> None:
        path = self.metadata_path(dataset_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        tmp.replace(path)

    def _maybe_migrate_legacy(self, dataset_id: str) -> None:
        if self.metadata_path(dataset_id).exists():
            return
        legacy = self.root / f"{dataset_id}.pkl"
        if not legacy.exists():
            return
        df = pd.read_pickle(legacy)
        self.create_dataset(df, dataset_id=dataset_id)


dataset_manager = DatasetManager()
