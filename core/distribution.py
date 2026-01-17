from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

import pandas as pd


def _to_decimal(value: object) -> Decimal:
    return Decimal(str(value).replace(",", "."))


def align_employee_total(
    df_emp: pd.DataFrame,
    target_total: float,
    pick: str = "max_amount",
) -> pd.DataFrame:
    """
    Округляет строки до 2 знаков и докидывает/убирает разницу (в копейках)
    в выбранную строку, чтобы итог по сотруднику совпал с ФОТ.

    pick:
      - "max_amount": докидываем в строку с максимальной суммой
      - "max_days":   докидываем в строку с максимальным количеством дней
    """
    if df_emp.empty:
        return df_emp

    df_emp = df_emp.copy()

    target_cents = int((_to_decimal(target_total) * 100).to_integral_value(rounding=ROUND_HALF_UP))

    cents_list = []
    for value in df_emp["Сумма с учетом занятости"].tolist():
        rounded = _to_decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        cents_list.append(int((rounded * 100).to_integral_value(rounding=ROUND_HALF_UP)))

    df_emp["_cents"] = cents_list

    distributed_cents = int(df_emp["_cents"].sum())
    diff_cents = target_cents - distributed_cents

    if diff_cents != 0:
        if pick == "max_days" and "Количество дней" in df_emp.columns:
            idx = df_emp["Количество дней"].idxmax()
        else:
            idx = df_emp["_cents"].idxmax()
        df_emp.loc[idx, "_cents"] = int(df_emp.loc[idx, "_cents"]) + int(diff_cents)

    df_emp["Сумма с учетом занятости"] = (df_emp["_cents"] / 100).round(2)
    df_emp.drop(columns=["_cents"], inplace=True)
    return df_emp


def distribute_by_periods_simple(
    salary_data: pd.DataFrame,
    distribution_data: pd.DataFrame,
) -> pd.DataFrame:
    """
    Распределяет зарплату по под-периодам с учетом смены кругов и % занятости.
    ВАЖНО: не округляет построчно сразу; округление + выравнивание делается
    одним шагом в конце по каждому сотруднику (в копейках).
    """
    result_rows = []

    for _, salary_row in salary_data.iterrows():
        employee = salary_row["Сотрудник"]
        total_salary = float(str(salary_row["ФОТ"]).replace(",", "."))
        salary_start = pd.to_datetime(salary_row["Начало периода"])
        salary_end = pd.to_datetime(salary_row["Конец периода"])
        total_days = (salary_end - salary_start).days + 1
        daily_salary = total_salary / total_days

        emp_distributions = distribution_data[
            distribution_data["Сотрудник"] == employee
        ].copy()

        if emp_distributions.empty:
            continue

        emp_distributions["Дата начала"] = pd.to_datetime(emp_distributions["Дата начала"])
        emp_distributions = emp_distributions.sort_values("Дата начала")

        temp_rows = []

        for _, dist_row in emp_distributions.iterrows():
            period_start = max(dist_row["Дата начала"], salary_start)

            next_dist_rows = emp_distributions[emp_distributions["Дата начала"] > dist_row["Дата начала"]]
            if not next_dist_rows.empty:
                next_start = next_dist_rows["Дата начала"].min() - pd.Timedelta(days=1)
                period_end = min(next_start, salary_end)
            else:
                period_end = salary_end

            if period_end < period_start:
                continue

            period_days = (period_end - period_start).days + 1
            period_salary = daily_salary * period_days

            sum_with_percent = period_salary * dist_row["% занятости"] / 100

            result_row = {
                "Сотрудник": employee,
                "Сумма": total_salary,
                "Период выплаты": f"{salary_start.strftime('%d.%m.%Y')} - {salary_end.strftime('%d.%m.%Y')}",
                "Распределяемый период (начало)": period_start.strftime("%d.%m.%Y"),
                "Распределяемый период (конец)": period_end.strftime("%d.%m.%Y"),
                "Количество дней": period_days,
                "% занятости": dist_row["% занятости"],
                "Сумма с учетом занятости": sum_with_percent,
            }

            exclude_columns = ["Сотрудник", "% занятости", "Дата начала"]
            circle_columns = [
                col
                for col in distribution_data.columns
                if col not in exclude_columns
            ]
            for col in circle_columns:
                result_row[col] = dist_row[col]

            temp_rows.append(result_row)

        df_temp = pd.DataFrame(temp_rows)
        if not df_temp.empty:
            df_temp = align_employee_total(df_temp, total_salary, pick="max_amount")

        result_rows.extend(df_temp.to_dict("records"))

    return pd.DataFrame(result_rows)
