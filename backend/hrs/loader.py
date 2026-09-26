from pathlib import Path
from typing import Any

import pandas as pd
import pyreadstat


def load_hrs_sav(
    path: str | Path,
) -> tuple[pd.DataFrame, Any]:
    """
    读取 RAND HRS SPSS .sav 文件。

    返回：
        df   - HRS 数据
        meta - SPSS metadata
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"HRS 文件不存在: {path}")

    if path.suffix.lower() != ".sav":
        raise ValueError(f"不是 SPSS .sav 文件: {path}")

    df, meta = pyreadstat.read_sav(
        str(path),
        apply_value_formats=False,
    )

    return df, meta