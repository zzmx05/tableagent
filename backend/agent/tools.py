"""Tool registry used by the model-driven agent loop."""
import json
import uuid
from hrs.repository import HRSRepository
from typing import Any, Callable, Dict

from dataset_manager import dataset_manager
from pathlib import Path

from hrs.catalog import HRSVariableCatalog
from hrs.families import HRSVariableFamilyIndex
from hrs.semantic import HRSSemanticSearch
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

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent

HRS_METADATA_PATH = PROJECT_ROOT / "data" / "metadata" / "hrs_variables.json"

hrs_catalog = HRSVariableCatalog(HRS_METADATA_PATH)
hrs_families = HRSVariableFamilyIndex(hrs_catalog)
hrs_semantic = HRSSemanticSearch(hrs_catalog, hrs_families)
HRS_DATA_PATH = PROJECT_ROOT / "data" / "master" / "randhrs1992_2022v1.parquet"
hrs_repository = HRSRepository(HRS_DATA_PATH)

def _extract_hrs_dataset(args, context):
    variables = args.get("variables") or []

    if not variables:
        raise ValueError("必须提供需要提取的HRS变量")

    columns = ["HHIDPN"]

    for variable in variables:
        name = str(variable).strip().upper()
        if name and name not in columns:
            columns.append(name)

    hrs_repository.validate_columns(columns)
    df = hrs_repository.extract(columns)

    dataset_id = f"hrs_{uuid.uuid4().hex[:12]}"
    metadata = dataset_manager.create_dataset(df, dataset_id=dataset_id)

    preview = json.loads(df.head(20).to_json(orient="values", force_ascii=False))

    return {
        "dataset_id": dataset_id,
        "version": metadata["current_version"],
        "rows": int(len(df)),
        "columns": columns,
        "preview": preview,
    }

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

        ctx = dict(context or {})
        ctx["_operation_name"] = name
        ctx["_operation_parameters"] = arguments or {}

        result = self._handlers[name](
            arguments or {},
            ctx
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

    try:
        dataset_path = dataset_manager.current_path(dataset_id)
    except FileNotFoundError as e:
        raise ValueError(str(e)) from e

    if not dataset_path.exists():
        raise ValueError(
            f"找不到数据集: {dataset_id}"
        )

    return dataset_path


def _df(context):
    dataset_id = context.get("dataset_id")

    if not dataset_id:
        raise ValueError(
            "当前会话没有 dataset_id，无法找到真实表格"
        )

    try:
        return dataset_manager.load_version(dataset_id)
    except FileNotFoundError as e:
        raise ValueError(str(e)) from e


def _save_df(df, context):
    dataset_id = context.get("dataset_id")

    if not dataset_id:
        raise ValueError(
            "当前会话没有 dataset_id，无法找到真实表格"
        )

    dataset_manager.save_new_version(
        dataset_id,
        df,
        operation_name=context.get("_operation_name", "update"),
        parameters=context.get("_operation_parameters", {}),
    )


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

    # _save_df(new_df, context)

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

    # _save_df(new_df, context)

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

    # _save_df(new_df, context)

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

    # _save_df(new_df, context)

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

    # _save_df(new_df, context)

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

    # _save_df(new_df, context)

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

    # _save_df(new_df, context)

    return {
        "result": result,
        "dataset_id": context["dataset_id"]
    }


def _drop_duplicates(args, context):
    df = _df(context)

    new_df, result = drop_duplicates(df)

    # _save_df(new_df, context)

    return {
        "result": result,
        "dataset_id": context["dataset_id"]
    }

def _search_hrs_variables(args, context):
    query = str(args.get("query") or "").strip()
    limit = int(args.get("limit") or 10)

    if not query:
        raise ValueError("HRS变量搜索必须提供 query")

    results = hrs_semantic.search_families(query, limit=limit)

    return {
        "query": query,
        "count": len(results),
        "candidates": [
            {
                "role": item.role,
                "base_name": item.base_name,
                "score": item.score,
                "match_type": item.match_type,
                "representative_name": item.representative_name,
                "representative_label": item.representative_label,
                "wave_count": item.wave_count,
                "waves": list(item.waves),
            }
            for item in results
        ],
    }


def _resolve_hrs_variables(args, context):
    role = str(args.get("role") or "").strip().lower()
    base_name = str(args.get("base_name") or "").strip().upper()
    years = args.get("years") or []
    waves = args.get("waves") or []

    if not role:
        raise ValueError("必须提供 role")

    if not base_name:
        raise ValueError("必须提供 base_name")

    family = hrs_families.get_family(role=role, base_name=base_name)

    if family is None:
        raise ValueError(f"找不到HRS变量族: {role}:{base_name}")

    selected_members = []

    if years:
        for year in years:
            member = family.get_member_for_year(int(year))
            if member is not None and member not in selected_members:
                selected_members.append(member)

    elif waves:
        selected_members = list(family.get_members_for_waves(tuple(int(wave) for wave in waves)))

    else:
        selected_members = list(family.members)

    return {
        "role": family.role,
        "base_name": family.base_name,
        "requested_years": years,
        "requested_waves": waves,
        "variables": [
            {
                "name": member.name,
                "wave": member.wave,
                "years": list(member.years),
                "label": member.label,
            }
            for member in selected_members
        ],
    }

# Registry
def build_registry():

    r = ToolRegistry()

    r.register(
        "search_hrs_variables",
        "根据研究概念搜索真实的HRS变量族。用户询问HRS中的婚姻、抑郁、认知、退休、健康等研究变量时使用。返回真实候选变量族，不要自己猜测HRS变量名。",
        {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "用于搜索HRS metadata的英文研究概念，例如 marital status、depressed、cognition、retirement"
                },
                "limit": {
                    "type": "integer",
                    "description": "最多返回多少个候选变量族，默认10"
                }
            },
            "required": ["query"],
            "additionalProperties": False
        },
        _search_hrs_variables
    )

    r.register(
        "resolve_hrs_variables",
        "把已经确认的HRS变量族转换成指定年份或波次的真实HRS变量名。必须使用搜索得到的真实role和base_name，不得自己创造变量名。",
        {
            "type": "object",
            "properties": {
                "role": {
                    "type": "string",
                    "enum": ["respondent", "spouse", "household"]
                },
                "base_name": {
                    "type": "string",
                    "description": "真实HRS变量族base name，例如MSTAT"
                },
                "years": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "需要的调查年份，例如[2020, 2022]"
                },
                "waves": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "需要的HRS波次，例如[15, 16]"
                }
            },
            "required": ["role", "base_name"],
            "additionalProperties": False
        },
        _resolve_hrs_variables
    )

    r.register(
        "extract_hrs_dataset",
        "把已经确认的真实HRS变量从内置HRS数据中提取为工作数据集。只有在用户明确要求提取、处理、分析这些变量时使用。必须使用resolve_hrs_variables得到的真实变量名，不得猜测变量名。",
        {
            "type": "object",
            "properties": {
                "variables": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "需要提取的真实HRS变量名，例如['R15MSTAT']"
                }
            },
            "required": ["variables"],
            "additionalProperties": False
        },
        _extract_hrs_dataset
    )

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