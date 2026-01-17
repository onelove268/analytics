from __future__ import annotations


def get_employee_text(count: int) -> str:
    if count % 10 == 1 and count % 100 != 11:
        return f"{count} сотрудник"
    if count % 10 in [2, 3, 4] and count % 100 not in [12, 13, 14]:
        return f"{count} сотрудника"
    return f"{count} сотрудников"
