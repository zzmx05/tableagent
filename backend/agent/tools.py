"""Tool registry used by the model-driven agent loop."""

from typing import Any, Callable, Dict
from pathlib import Path
import os

import pandas as pd

from tools.table_tools import (
    get_table_statistics,
    get_column_info,
    drop_missing_values,
    delete_column,
    add_row,
    rename_column,
    filter_rows,
    sort_rows,
    fill_missing_values,
    drop_duplicates,
)


DATA_ROOT = Path(
    os.getenv(
        "TABLE_AGENT_DATA",
        Path(__file__).resolve().parents[1]
        / "runtime"
        / "datasets"
    )
)


class ToolRegistry:

    def __init__(self):
        self._handlers: Dict[str, Callable[..., Any]] = {}
        self._schemas: Dict[str, Dict[str, Any]] = {}

    def register(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable[..., Any]
    ):
        self._handlers[name] = handler

        self._schemas[name] = {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters,
            }
        }

    def schemas(self):
        return list(self._schemas.values())

    def execute(
        self,
        name: str,
        arguments: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Any:

        print("\n" + "=" * 60)
        print("[TOOL CALL]")
        print("Tool:", name)
        print("Arguments:", arguments)
        print("Dataset ID:", context.get("dataset_id"))
        print("=" * 60)

        if name not in self._handlers:
            print("[TOOL ERROR] Unknown tool:", name)
            raise ValueError(
                f"未知工具: {name}"
            )

        result = self._handlers[name](
            arguments or {},
            context or {}
        )

        print("[TOOL RESULT]")
        print(result)
        print("=" * 60 + "\n")

        return result


def _dataset_path(context):
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

    return dataset_path


def _df(context):
    return pd.read_pickle(
        _dataset_path(context)
    )


def _save_df(df, context):
    dataset_path = _dataset_path(context)
    df.to_pickle(dataset_path)


# 查询类
def _statistics(args, context):
    return get_table_statistics(
        _df(context)
    )


def _column_info(args, context):
    return get_column_info(
        _df(context),
        args["column"]
    )


# 删除类
def _drop_missing(args, context):
    df = _df(context)

    new_df, result = drop_missing_values(
        df,
        args.get("column")
    )

    _save_df(new_df, context)

    return {
        "result": result,
        "dataset_id": context["dataset_id"]
    }


def _delete_column(args, context):
    df = _df(context)

    new_df, result = delete_column(
        df,
        args["column"]
    )

    _save_df(new_df, context)

    return {
        "result": result,
        "dataset_id": context["dataset_id"]
    }


# 修改类
def _add_row(args, context):
    df = _df(context)

    new_df, result = add_row(
        df,
        args["values"]
    )

    _save_df(new_df, context)

    return {
        "result": result,
        "dataset_id": context["dataset_id"]
    }


def _rename_column(args, context):
    df = _df(context)

    new_df, result = rename_column(
        df,
        args["old_name"],
        args["new_name"]
    )

    _save_df(new_df, context)

    return {
        "result": result,
        "dataset_id": context["dataset_id"]
    }


# 筛选类
def _filter_rows(args, context):
    df = _df(context)

    new_df, result = filter_rows(
        df,
        args["expression"]
    )

    _save_df(new_df, context)

    return {
        "result": result,
        "dataset_id": context["dataset_id"]
    }


def _sort_rows(args, context):
    df = _df(context)

    new_df, result = sort_rows(
        df,
        args["column"],
        args.get("ascending", True)
    )

    _save_df(new_df, context)

    return {
        "result": result,
        "dataset_id": context["dataset_id"]
    }


# 数据清洗类
def _fill_missing_values(args, context):
    df = _df(context)

    new_df, result = fill_missing_values(
        df,
        args["column"],
        args["value"]
    )

    _save_df(new_df, context)

    return {
        "result": result,
        "dataset_id": context["dataset_id"]
    }


def _drop_duplicates(args, context):
    df = _df(context)

    new_df, result = drop_duplicates(df)

    _save_df(new_df, context)

    return {
        "result": result,
        "dataset_id": context["dataset_id"]
    }


# Registry
def build_registry():

    r = ToolRegistry()

    # 查询类
    r.register(
        "get_table_statistics",
        "统计当前表格的行数、列数、列名和每列缺失值数量。",
        {
            "type": "object",
            "properties": {},
            "additionalProperties": False
        },
        _statistics
    )

    r.register(
        "get_column_info",
        "查看指定列的数据类型、缺失数量、唯一值数量和示例值。",
        {
            "type": "object",
            "properties": {
                "column": {
                    "type": "string",
                    "description": "列名"
                }
            },
            "required": ["column"],
            "additionalProperties": False
        },
        _column_info
    )

    # 删除类
    r.register(
        "drop_missing_values",
        "删除包含缺失值的行；可指定 column，只依据该列判断。",
        {
            "type": "object",
            "properties": {
                "column": {
                    "type": ["string", "null"],
                    "description": "指定列名；不指定则检查所有列"
                }
            },
            "required": [],
            "additionalProperties": False
        },
        _drop_missing
    )

    r.register(
        "delete_column",
        "删除指定的数据列。",
        {
            "type": "object",
            "properties": {
                "column": {
                    "type": "string",
                    "description": "要删除的列名"
                }
            },
            "required": ["column"],
            "additionalProperties": False
        },
        _delete_column
    )

    # 修改类
    r.register(
        "add_row",
        "在表格最后增加一行数据。",
        {
            "type": "object",
            "properties": {
                "values": {
                    "type": "object",
                    "description": "新行数据，例如 {'Name':'张三','Age':18}"
                }
            },
            "required": ["values"],
            "additionalProperties": False
        },
        _add_row
    )

    r.register(
        "rename_column",
        "修改指定列的名称。",
        {
            "type": "object",
            "properties": {
                "old_name": {
                    "type": "string",
                    "description": "原列名"
                },
                "new_name": {
                    "type": "string",
                    "description": "新列名"
                }
            },
            "required": ["old_name", "new_name"],
            "additionalProperties": False
        },
        _rename_column
    )

    # 筛选类
    r.register(
        "filter_rows",
        "按照条件筛选表格中的行。",
        {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "pandas query 条件，例如 Age >= 18"
                }
            },
            "required": ["expression"],
            "additionalProperties": False
        },
        _filter_rows
    )

    r.register(
        "sort_rows",
        "按照指定列对表格进行排序。",
        {
            "type": "object",
            "properties": {
                "column": {
                    "type": "string",
                    "description": "排序列"
                },
                "ascending": {
                    "type": "boolean",
                    "description": "是否升序"
                }
            },
            "required": ["column"],
            "additionalProperties": False
        },
        _sort_rows
    )

    # 数据清洗类
    r.register(
        "fill_missing_values",
        "使用指定值填充指定列中的缺失值。",
        {
            "type": "object",
            "properties": {
                "column": {
                    "type": "string",
                    "description": "需要填充的列"
                },
                "value": {
                    "description": "用于填充的值"
                }
            },
            "required": ["column", "value"],
            "additionalProperties": False
        },
        _fill_missing_values
    )

    r.register(
        "drop_duplicates",
        "删除完全重复的数据行。",
        {
            "type": "object",
            "properties": {},
            "additionalProperties": False
        },
        _drop_duplicates
    )

    return r


registry = build_registry()