import pandas as pd


def get_table_statistics(df: pd.DataFrame) -> dict:
    """
    获取表格基本统计信息。
    """

    result = {
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "column_names": df.columns.tolist(),
        "missing_values": {
            column: int(df[column].isna().sum())
            for column in df.columns
        }
    }

    return result


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
            raise ValueError(
                f"列 '{column}' 不存在"
            )

        result_df = df.dropna(
            subset=[column]
        )

    else:
        result_df = df.dropna()

    after_rows = len(result_df)

    result = {
        "before_rows": int(before_rows),
        "after_rows": int(after_rows),
        "deleted_rows": int(
            before_rows - after_rows
        )
    }

    return result_df, result