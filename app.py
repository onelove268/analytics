from __future__ import annotations

from datetime import datetime
from io import BytesIO

import pandas as pd
import streamlit as st

from core.distribution import distribute_by_periods_simple
from core.formatting import get_employee_text
from core.validation import (
    REQUIRED_DISTRIBUTION_COLUMNS,
    REQUIRED_SALARY_COLUMNS,
    find_missing_columns,
    prepare_distribution_data,
    prepare_salary_data,
)

st.set_page_config(
    page_title="🤖 Бот для распределения затрат по кругам",
    page_icon="📊",
    layout="wide",
)

st.title("🤖 Бот для распределения затрат по кругам")
st.markdown("Автоматическое распределение затрат по кругам")

if "salary_data" not in st.session_state:
    st.session_state.salary_data = None
if "distribution_data" not in st.session_state:
    st.session_state.distribution_data = None
if "result_data" not in st.session_state:
    st.session_state.result_data = None
if "original_total_fot" not in st.session_state:
    st.session_state.original_total_fot = 0
if "missing_employees" not in st.session_state:
    st.session_state.missing_employees = None
if "circle_summary" not in st.session_state:
    st.session_state.circle_summary = None
if "circle_columns" not in st.session_state:
    st.session_state.circle_columns = []


with st.sidebar:
    st.header("📁 Загрузка данных")

    st.subheader("Файл с зарплатами")
    salary_file = st.file_uploader(
        "Загрузите CSV/Excel с ФОТ",
        type=["csv", "xlsx"],
        key="salary_uploader",
    )

    if salary_file:
        try:
            if salary_file.name.endswith(".csv"):
                salary_df = pd.read_csv(salary_file)
            else:
                salary_df = pd.read_excel(salary_file)

            salary_df, missing_columns = prepare_salary_data(salary_df)
            st.session_state.salary_data = salary_df

            if missing_columns:
                st.error(f"❌ В файле с зарплатами отсутствуют необходимые колонки: {missing_columns}")
            else:
                employee_count = len(salary_df)
                st.success(f"✅ Загружено {get_employee_text(employee_count)}")
        except Exception as exc:
            st.error(f"❌ Ошибка загрузки: {exc}")

    st.subheader("Файл с распределением")
    distribution_file = st.file_uploader(
        "Загрузите CSV/Excel с процентами",
        type=["csv", "xlsx"],
        key="distribution_uploader",
    )

    if distribution_file:
        try:
            if distribution_file.name.endswith(".csv"):
                distribution_df = pd.read_csv(distribution_file)
            else:
                distribution_df = pd.read_excel(distribution_file)

            distribution_df, missing_columns = prepare_distribution_data(distribution_df)
            st.session_state.distribution_data = distribution_df

            if missing_columns:
                st.error(f"❌ В файле с распределением отсутствуют необходимые колонки: {missing_columns}")
            else:
                unique_employees_count = distribution_df["Сотрудник"].nunique()
                st.success(f"✅ Загружено {get_employee_text(unique_employees_count)}")
        except Exception as exc:
            st.error(f"❌ Ошибка загрузки: {exc}")

    if st.button("🔄 Создать пример данных"):
        st.session_state.salary_data = pd.DataFrame(
            {
                "Сотрудник": ["Иванов Иван Иванович", "Петрова Мария Олеговна"],
                "ФОТ": [66687.67, 40000],
                "Начало периода": [datetime(2025, 11, 1), datetime(2025, 11, 1)],
                "Конец периода": [datetime(2025, 11, 15), datetime(2025, 11, 15)],
            }
        )

        st.session_state.distribution_data = pd.DataFrame(
            {
                "Сотрудник": [
                    "Иванов Иван Иванович",
                    "Иванов Иван Иванович",
                    "Петрова Мария Олеговна",
                ],
                "Главный круг": [
                    "3 | R&D",
                    "1100 | Board of director",
                    "800 | OPS",
                ],
                "Подкруг 1": [
                    "3.18 | C1. Team.Two (T2)",
                    "1110 | Board of director",
                    "8110 | Docs",
                ],
                "Подкруг 2": [
                    "3.18.1 | C1. Team.Two (T2) GEN",
                    "1111 | Board of director",
                    "8112 | K.Docs",
                ],
                "% занятости": [100, 100, 100],
                "Дата начала": [
                    datetime(2025, 11, 1),
                    datetime(2025, 11, 8),
                    datetime(2025, 11, 1),
                ],
            }
        )

        salary_count = len(st.session_state.salary_data)
        distribution_count = st.session_state.distribution_data["Сотрудник"].nunique()
        st.success(
            f"✅ Примеры данных созданы! Загружено {get_employee_text(salary_count)} с зарплатами и "
            f"{get_employee_text(distribution_count)} с распределением"
        )


tab1, tab2 = st.tabs(["📊 Данные", "🧮 Распределение"])

with tab1:
    st.header("Просмотр данных")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Данные по затратам")
        if st.session_state.salary_data is not None:
            employee_count = len(st.session_state.salary_data)
            total_fot = st.session_state.salary_data.get("ФОТ", pd.Series(dtype=float)).sum()
            st.write(f"**Всего: {get_employee_text(employee_count)}**")
            st.write(f"**Общий ФОТ: {total_fot:,.2f} руб.**")

            display_salary_data = st.session_state.salary_data.copy()
            for col in ["Начало периода", "Конец периода"]:
                if col in display_salary_data.columns:
                    display_salary_data[col] = display_salary_data[col].dt.strftime("%d.%m.%Y")

            st.dataframe(display_salary_data, use_container_width=True)
        else:
            st.info("📝 Загрузите файл с зарплатами в сайдбаре")

    with col2:
        st.subheader("Данные по сотрудникам")
        if st.session_state.distribution_data is not None:
            unique_employees_count = st.session_state.distribution_data["Сотрудник"].nunique()
            total_rows_count = len(st.session_state.distribution_data)
            st.write(
                f"**Всего: {get_employee_text(unique_employees_count)} ({total_rows_count} записей распределения)**"
            )
            st.info("💡 Используется только 'Дата начала'. Распределение действует до конца периода выплаты.")

            display_distribution_data = st.session_state.distribution_data.copy()
            if "Дата начала" in display_distribution_data.columns:
                display_distribution_data["Дата начала"] = display_distribution_data["Дата начала"].dt.strftime(
                    "%d.%m.%Y"
                )

            st.dataframe(display_distribution_data, use_container_width=True)
        else:
            st.info("📝 Загрузите файл с распределением в сайдбаре")

    if st.session_state.salary_data is not None and st.session_state.distribution_data is not None:
        st.divider()
        st.subheader("🔎 Проверка наличия распределений")

        salary_df = st.session_state.salary_data.copy()
        dist_df = st.session_state.distribution_data.copy()
        salary_df.columns = salary_df.columns.str.strip()
        dist_df.columns = dist_df.columns.str.strip()

        salary_employees = set(salary_df["Сотрудник"].dropna().unique())
        distribution_employees = set(dist_df["Сотрудник"].dropna().unique())

        missing_employees = salary_employees - distribution_employees

        if missing_employees:
            missing_table = salary_df[
                salary_df["Сотрудник"].isin(missing_employees)
            ][["Сотрудник", "ФОТ", "Начало периода", "Конец периода"]].copy()

            missing_table["Начало периода"] = missing_table["Начало периода"].dt.strftime("%d.%m.%Y")
            missing_table["Конец периода"] = missing_table["Конец периода"].dt.strftime("%d.%m.%Y")

            st.warning("⚠️ Найдены сотрудники, у которых есть ФОТ, но нет распределения")
            st.dataframe(missing_table, use_container_width=True)

            st.session_state.missing_employees = missing_table
        else:
            st.success("✅ Все сотрудники из файла с ФОТ имеют распределение")

with tab2:
    st.header("Распределение ФОТ")

    if st.session_state.salary_data is not None and st.session_state.distribution_data is not None:
        missing_salary_columns = find_missing_columns(
            st.session_state.salary_data,
            REQUIRED_SALARY_COLUMNS,
        )
        missing_distribution_columns = find_missing_columns(
            st.session_state.distribution_data,
            REQUIRED_DISTRIBUTION_COLUMNS,
        )

        if missing_salary_columns:
            st.error(f"❌ В файле с зарплатами отсутствуют необходимые колонки: {missing_salary_columns}")
        elif missing_distribution_columns:
            st.error(f"❌ В файле с распределением отсутствуют необходимые колонки: {missing_distribution_columns}")
        else:
            if st.button("🚀 Запустить распределение", type="primary"):
                with st.spinner("Выполняю распределение с учетом периодов..."):
                    try:
                        st.session_state.original_total_fot = st.session_state.salary_data["ФОТ"].sum()

                        result_data = distribute_by_periods_simple(
                            st.session_state.salary_data,
                            st.session_state.distribution_data,
                        )

                        if not result_data.empty:
                            st.session_state.result_data = result_data

                            exclude_columns = [
                                "Сотрудник",
                                "Сумма",
                                "Период выплаты",
                                "Распределяемый период (начало)",
                                "Распределяемый период (конец)",
                                "Количество дней",
                                "% занятости",
                                "Сумма с учетом занятости",
                            ]
                            circle_columns = [
                                col for col in result_data.columns if col not in exclude_columns
                            ]
                            st.session_state.circle_columns = circle_columns

                            total_employees = result_data["Сотрудник"].nunique()
                            total_records = len(result_data)
                            st.success(
                                "✅ Распределение завершено! "
                                f"Обработано {get_employee_text(total_employees)} ({total_records} периодов распределения)"
                            )
                        else:
                            st.error(
                                "❌ Не удалось выполнить распределение. "
                                "Проверьте соответствие периодов в файлах."
                            )

                    except Exception as exc:
                        st.error(f"❌ Ошибка при распределении: {exc}")
                        st.info("💡 Подсказка: Проверьте формат дат и соответствие имен сотрудников")

        if st.session_state.result_data is not None:
            st.subheader("Результаты распределения")

            total_employees = st.session_state.result_data["Сотрудник"].nunique()
            total_records = len(st.session_state.result_data)
            st.write(f"**Обработано: {get_employee_text(total_employees)} ({total_records} периодов распределения)**")

            accuracy_check = st.session_state.result_data.groupby("Сотрудник").agg(
                {
                    "Сумма": "first",
                    "Сумма с учетом занятости": "sum",
                }
            ).reset_index()
            accuracy_check["Разница"] = (
                accuracy_check["Сумма"] - accuracy_check["Сумма с учетом занятости"]
            ).round(2)

            perfect_matches = len(accuracy_check[abs(accuracy_check["Разница"]) < 0.01])
            significant_diff = len(accuracy_check[abs(accuracy_check["Разница"]) >= 0.01])

            if significant_diff > 0:
                st.warning(f"⚠️ Обнаружены расхождения у {significant_diff} сотрудников")
                st.dataframe(accuracy_check[abs(accuracy_check["Разница"]) >= 0.01])
            else:
                st.success(f"✅ Все суммы выровнены. Сошлось у {perfect_matches} сотрудников.")

            st.dataframe(st.session_state.result_data, use_container_width=True)

            st.subheader("Общая статистика")
            total_original_fot = float(st.session_state.original_total_fot)
            total_distributed_fot = float(st.session_state.result_data["Сумма с учетом занятости"].sum())

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Общий ФОТ", f"{total_original_fot:,.2f} руб.")
            with col2:
                st.metric("Распределенный ФОТ", f"{total_distributed_fot:,.2f} руб.")
            with col3:
                difference = total_original_fot - total_distributed_fot
                st.metric("Разница", f"{difference:.2f} руб.")

            st.subheader("Сводка по кругам")

            circle_summary_rows = []
            for _, row in st.session_state.result_data.iterrows():
                circle_summary_rows.append(
                    {
                        "Сотрудник": row["Сотрудник"],
                        "Главный круг": row.get("Главный круг", None),
                        "Подкруг 1": row.get("Подкруг 1", None),
                        "Подкруг 2": row.get("Подкруг 2", None),
                        "Сумма": row["Сумма с учетом занятости"],
                        "Количество периодов": 1,
                    }
                )

            circle_summary = pd.DataFrame(circle_summary_rows)

            if not circle_summary.empty:
                final_summary = circle_summary.groupby(
                    ["Сотрудник", "Главный круг", "Подкруг 1", "Подкруг 2"],
                    dropna=False,
                ).agg({"Сумма": "sum"}).reset_index()

                st.session_state.circle_summary = final_summary
                st.dataframe(final_summary, use_container_width=True)

            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                st.session_state.result_data.to_excel(writer, sheet_name="Распределение ФОТ", index=False)
                if st.session_state.circle_summary is not None:
                    st.session_state.circle_summary.to_excel(
                        writer,
                        sheet_name="Сводка по кругам",
                        index=False,
                    )

            output.seek(0)

            st.download_button(
                "📥 Скачать результаты распределения",
                output,
                "распределение_фот.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download-excel",
            )
    else:
        st.info("📝 Загрузите оба файла данных для начала распределения")

st.markdown("---")
st.markdown("🤖 *AI Бот для распределения ФОТ v1.0*")
