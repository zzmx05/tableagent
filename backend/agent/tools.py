"""Tool registry used by the model-driven agent loop."""
from typing import Any, Callable, Dict
import pandas as pd
from tools.table_tools import get_table_statistics, drop_missing_values
from pathlib import Path
import os

DATA_ROOT = Path(
    os.getenv(
        "TABLE_AGENT_DATA",
        Path(__file__).resolve().parents[1] / "runtime" / "datasets"
    )
)

class ToolRegistry:
    def __init__(self):
        self._handlers: Dict[str, Callable[..., Any]] = {}
        self._schemas: Dict[str, Dict[str, Any]] = {}

    def register(self, name: str, description: str, parameters: Dict[str, Any], handler: Callable[..., Any]):
        self._handlers[name] = handler
        self._schemas[name] = {"type": "function", "function": {"name": name, "description": description, "parameters": parameters}}

    def schemas(self): return list(self._schemas.values())

    def execute(self, name: str, arguments: Dict[str, Any], context: Dict[str, Any]) -> Any:
        if name not in self._handlers: raise ValueError(f"未知工具: {name}")
        return self._handlers[name](arguments or {}, context or {})

def _df(context):
    dataset_id = context.get("dataset_id")

    if not dataset_id:
        raise ValueError(
            "当前会话没有 dataset_id，无法找到真实表格"
        )

    dataset_path = DATA_ROOT / f"{dataset_id}.pkl"

    if not dataset_path.exists():
        raise ValueError(
            f"找不到数据集: {dataset_id}"
        )

    return pd.read_pickle(dataset_path)

def _statistics(args, context): return get_table_statistics(_df(context))

def _drop_missing(args, context):
    df = _df(context)

    new_df, result = drop_missing_values(
        df,
        args.get("column")
    )

    dataset_id = context["dataset_id"]

    dataset_path = DATA_ROOT / f"{dataset_id}.pkl"

    new_df.to_pickle(dataset_path)

    return {
        "result": result,
        "dataset_id": dataset_id
    }

def build_registry():
    r = ToolRegistry()
    r.register("get_table_statistics", "统计当前表格的行数、列数、列名和每列缺失值数量。", {"type":"object","properties":{},"additionalProperties":False}, _statistics)
    r.register("drop_missing_values", "删除表格中包含缺失值的行；可指定 column，只依据该列判断。", {"type":"object","properties":{"column":{"type":["string","null"],"description":"指定列名；不指定则检查所有列"}},"required":[],"additionalProperties":False}, _drop_missing)
    return r

registry = build_registry()
