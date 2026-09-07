"""Tool registry used by the model-driven agent loop."""
from typing import Any, Callable, Dict
import pandas as pd
from tools.table_tools import get_table_statistics, drop_missing_values

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
    data = context.get("data")
    if data is None: raise ValueError("当前会话没有可供工具分析的表格数据")
    if isinstance(data, list) and data and isinstance(data[0], list):
        cols = context.get("columns") or [f"column_{i}" for i in range(len(data[0]))]
        data = [dict(zip(cols, row)) for row in data]
    return pd.DataFrame(data)

def _statistics(args, context): return get_table_statistics(_df(context))

def _drop_missing(args, context):
    df = _df(context)
    new_df, result = drop_missing_values(df, args.get("column"))
    return {"result": result, "data": new_df.to_dict(orient="records")}

def build_registry():
    r = ToolRegistry()
    r.register("get_table_statistics", "统计当前表格的行数、列数、列名和每列缺失值数量。", {"type":"object","properties":{},"additionalProperties":False}, _statistics)
    r.register("drop_missing_values", "删除表格中包含缺失值的行；可指定 column，只依据该列判断。", {"type":"object","properties":{"column":{"type":["string","null"],"description":"指定列名；不指定则检查所有列"}},"required":[],"additionalProperties":False}, _drop_missing)
    return r

registry = build_registry()
