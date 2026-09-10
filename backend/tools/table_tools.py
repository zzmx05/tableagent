import pandas as pd

# 查询类 Tools
def get_table_statistics(df: pd.DataFrame) -> dict:
    """
    获取表格基本统计信息。
    """
    return {
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "column_names": [str(c) for c in df.columns],
        "missing_values": {
            str(column): int(df[column].isna().sum())
            for column in df.columns
        }
    }


def get_column_info(
    df: pd.DataFrame,
    column: str
) -> dict:
    """
    获取指定列的信息。
    """
    if column not in df.columns:
        raise ValueError(f"列 '{column}' 不存在")

    series = df[column]

    return {
        "column": str(column),
        "dtype": str(series.dtype),
        "rows": int(len(series)),
        "missing": int(series.isna().sum()),
        "unique": int(series.nunique(dropna=True)),
        "sample_values": [
            None if pd.isna(v) else v
            for v in series.head(10).tolist()
        ]
    }


# 删除类 Tools
def drop_missing_values(
    df: pd.DataFrame,
    column: str | None = None
) -> tuple[pd.DataFrame, dict]:
    """
    删除包含空值的行。

    column=None：
        删除任意字段存在空值的行。

    column指定：
        只根据指定字段判断。
    """
    before_rows = len(df)

    if column:
        if column not in df.columns:
            raise ValueError(f"列 '{column}' 不存在")

        result_df = df.dropna(subset=[column])
    else:
        result_df = df.dropna()

    after_rows = len(result_df)

    return result_df, {
        "before_rows": int(before_rows),
        "after_rows": int(after_rows),
        "deleted_rows": int(before_rows - after_rows)
    }


def delete_column(
    df: pd.DataFrame,
    column: str
) -> tuple[pd.DataFrame, dict]:
    """
    删除指定列。
    """
    if column not in df.columns:
        raise ValueError(f"列 '{column}' 不存在")

    result_df = df.drop(columns=[column])

    return result_df, {
        "deleted_column": column,
        "remaining_columns": [
            str(c) for c in result_df.columns
        ]
    }


# 修改类 Tools
def add_row(
    df: pd.DataFrame,
    values: dict
) -> tuple[pd.DataFrame, dict]:
    """
    在表格末尾增加一行。

    values:
        {"Name": "张三", "Age": 18}
    """
    if not isinstance(values, dict):
        raise ValueError("values 必须是对象")

    unknown_columns = [
        column
        for column in values.keys()
        if column not in df.columns
    ]

    if unknown_columns:
        raise ValueError(
            f"以下列不存在: {unknown_columns}"
        )

    row = {
        column: values.get(column, None)
        for column in df.columns
    }

    result_df = pd.concat(
        [df, pd.DataFrame([row])],
        ignore_index=True
    )

    return result_df, {
        "added_rows": 1,
        "new_rows": int(len(result_df))
    }


def rename_column(
    df: pd.DataFrame,
    old_name: str,
    new_name: str
) -> tuple[pd.DataFrame, dict]:
    """
    重命名指定列。
    """
    if old_name not in df.columns:
        raise ValueError(
            f"列 '{old_name}' 不存在"
        )

    if new_name in df.columns:
        raise ValueError(
            f"列 '{new_name}' 已经存在"
        )

    result_df = df.rename(
        columns={old_name: new_name}
    )

    return result_df, {
        "old_name": old_name,
        "new_name": new_name
    }


# 筛选类 Tools
def filter_rows(
    df: pd.DataFrame,
    expression: str
) -> tuple[pd.DataFrame, dict]:
    """
    根据 pandas query 表达式筛选行。

    示例：
        Age >= 18
        Country == 'China'
    """
    if not expression:
        raise ValueError("expression 不能为空")

    before_rows = len(df)

    try:
        result_df = df.query(expression)
    except Exception as e:
        raise ValueError(
            f"筛选表达式执行失败: {e}"
        )

    return result_df, {
        "expression": expression,
        "before_rows": int(before_rows),
        "after_rows": int(len(result_df)),
        "filtered_rows": int(
            before_rows - len(result_df)
        )
    }


def sort_rows(
    df: pd.DataFrame,
    column: str,
    ascending: bool = True
) -> tuple[pd.DataFrame, dict]:
    """
    根据指定列排序。
    """
    if column not in df.columns:
        raise ValueError(
            f"列 '{column}' 不存在"
        )

    result_df = df.sort_values(
        by=column,
        ascending=ascending
    ).reset_index(drop=True)

    return result_df, {
        "column": column,
        "ascending": ascending,
        "rows": int(len(result_df))
    }


# 数据清洗类 Tools
def fill_missing_values(
    df: pd.DataFrame,
    column: str,
    value
) -> tuple[pd.DataFrame, dict]:
    """
    使用指定值填充某一列的缺失值。
    """
    if column not in df.columns:
        raise ValueError(
            f"列 '{column}' 不存在"
        )

    missing_before = int(
        df[column].isna().sum()
    )

    result_df = df.copy()
    result_df[column] = result_df[column].fillna(value)

    missing_after = int(
        result_df[column].isna().sum()
    )

    return result_df, {
        "column": column,
        "filled_values": missing_before - missing_after,
        "missing_before": missing_before,
        "missing_after": missing_after
    }


def drop_duplicates(
    df: pd.DataFrame
) -> tuple[pd.DataFrame, dict]:
    """
    删除完全重复的行。
    """
    before_rows = len(df)

    result_df = df.drop_duplicates().reset_index(
        drop=True
    )

    after_rows = len(result_df)

    return result_df, {
        "before_rows": int(before_rows),
        "after_rows": int(after_rows),
        "deleted_duplicates": int(
            before_rows - after_rows
        )
    }