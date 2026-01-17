import pandas as pd

from core.distribution import align_employee_total, distribute_by_periods_simple


def test_align_employee_total_matches_target():
    df = pd.DataFrame(
        {
            "Сотрудник": ["Иванов", "Иванов"],
            "Количество дней": [10, 5],
            "Сумма с учетом занятости": [50.005, 49.995],
        }
    )

    aligned = align_employee_total(df, target_total=100.0)
    assert round(aligned["Сумма с учетом занятости"].sum(), 2) == 100.0


def test_distribute_by_periods_simple_splits_periods():
    salary_data = pd.DataFrame(
        {
            "Сотрудник": ["Иванов"],
            "ФОТ": [100.0],
            "Начало периода": ["2025-01-01"],
            "Конец периода": ["2025-01-10"],
        }
    )

    distribution_data = pd.DataFrame(
        {
            "Сотрудник": ["Иванов", "Иванов"],
            "% занятости": [100, 100],
            "Дата начала": ["2025-01-01", "2025-01-06"],
            "Главный круг": ["A", "B"],
        }
    )

    result = distribute_by_periods_simple(salary_data, distribution_data)

    assert len(result) == 2
    assert round(result["Сумма с учетом занятости"].sum(), 2) == 100.0
