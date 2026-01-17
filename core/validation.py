from __future__ import annotations

from typing import Iterable

import pandas as pd

REQUIRED_SALARY_COLUMNS = ["Сотрудник", "ФОТ", "Начало периода", "Конец периода"]
REQUIRED_DISTRIBUTION_COLUMNS = ["Сотрудник", "% занятости", "Дата начала"]


def normalize_salary_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.str.strip()
    if "Сумма" in df.columns and "ФОТ" not in df.columns:
        df = df.rename(columns={"Сумма": "ФОТ"})
    return df


def parse_date_columns(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    df = df.copy()
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], format="mixed")
    return df


def find_missing_columns(df: pd.DataFrame, required: Iterable[str]) -> list[str]:
    return [col for col in required if col not in df.columns]


def prepare_salary_data(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    df = normalize_salary_columns(df)
    missing = find_missing_columns(df, REQUIRED_SALARY_COLUMNS)
    if missing:
        return df, missing
    df = parse_date_columns(df, ["Начало периода", "Конец периода"])
    return df, []


def prepare_distribution_data(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    df = df.copy()
    df.columns = df.columns.str.strip()
    missing = find_missing_columns(df, REQUIRED_DISTRIBUTION_COLUMNS)
    if missing:
        return df, missing
    df = parse_date_columns(df, ["Дата начала"])
    return df, []
