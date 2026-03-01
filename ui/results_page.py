import math
from decimal import Decimal

import pandas as pd
import streamlit as st

from engine.models import TarifiedRecord
from ui.components import format_duration, format_money


def render_summary_tab():
    results: list[TarifiedRecord] = st.session_state.get("results", [])
    if not results:
        st.info("Сначала выполните тарификацию")
        return

    st.subheader("Итоги по абонентам")

    summary: dict[str, dict] = {}
    for r in results:
        if r.cost is None:
            continue
        key = r.cdr.calling_party
        if key not in summary:
            summary[key] = {
                "name": r.subscriber_name or "—",
                "calls": 0,
                "seconds": 0,
                "total": Decimal("0"),
            }
        summary[key]["calls"] += 1
        summary[key]["seconds"] += r.cdr.billable_sec
        summary[key]["total"] += r.cost

    if not summary:
        st.warning("Нет тарифицированных звонков")
        return

    rows = []
    grand_calls = 0
    grand_seconds = 0
    grand_total = Decimal("0")
    for number, data in sorted(summary.items()):
        rows.append({
            "Номер": number,
            "ФИО": data["name"],
            "Кол-во звонков": data["calls"],
            "Минуты": math.ceil(data["seconds"] / 60),
            "Сумма (руб)": format_money(data["total"]),
        })
        grand_calls += data["calls"]
        grand_seconds += data["seconds"]
        grand_total += data["total"]

    rows.append({
        "Номер": "ИТОГО",
        "ФИО": "",
        "Кол-во звонков": grand_calls,
        "Минуты": math.ceil(grand_seconds / 60),
        "Сумма (руб)": format_money(grand_total),
    })

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # Untarified calls
    untarified = [r for r in results if r.cost is None and r.cdr.call_direction == "outgoing" and r.cdr.disposition == "answered"]
    if untarified:
        st.divider()
        st.subheader(f"Нетарифицированные исходящие звонки ({len(untarified)})")
        urows = []
        for r in untarified:
            urows.append({
                "Время": str(r.cdr.start_time),
                "Откуда": r.cdr.calling_party,
                "Куда": r.cdr.called_party,
                "Длительность": format_duration(r.cdr.billable_sec),
                "Абонент": r.subscriber_name or "—",
            })
        st.dataframe(pd.DataFrame(urows), use_container_width=True, hide_index=True)


def render_detail_tab():
    results: list[TarifiedRecord] = st.session_state.get("results", [])
    if not results:
        st.info("Сначала выполните тарификацию")
        return

    st.subheader("Детализация звонков")

    # Collect unique callers for filter
    callers = sorted({r.cdr.calling_party for r in results})
    caller_labels = {c: f"{c} ({st.session_state.get('subscribers', {}).get(c, '—')})" for c in callers}

    selected = st.selectbox(
        "Фильтр по абоненту",
        options=["Все"] + callers,
        format_func=lambda x: "Все абоненты" if x == "Все" else caller_labels.get(x, x),
    )

    filtered = results if selected == "Все" else [r for r in results if r.cdr.calling_party == selected]

    for idx, r in enumerate(filtered):
        direction = r.tariff.destination if r.tariff else "—"
        cost_str = format_money(r.cost)
        prefix_str = r.tariff.prefix if r.tariff else "—"
        rate_str = f"{r.tariff.rate_per_min}/мин" if r.tariff else "—"

        cols = st.columns([2, 2, 1.5, 2, 2, 1.5])
        cols[0].write(str(r.cdr.start_time))
        cols[1].write(r.cdr.called_party)
        cols[2].write(format_duration(r.cdr.billable_sec))
        cols[3].write(direction)
        cols[4].write(f"{prefix_str} ({rate_str})")
        cols[5].write(cost_str)

        if r.tariff:
            with st.expander(f"Детали тарифа — запись {idx + 1}", expanded=False):
                tcols = st.columns(2)
                tcols[0].markdown(f"""
- **Префикс:** {r.tariff.prefix}
- **Направление:** {r.tariff.destination}
- **Тариф:** {r.tariff.rate_per_min} руб/мин
- **Соединение:** {r.tariff.connection_fee} руб
""")
                tcols[1].markdown(f"""
- **Время действия:** {r.tariff.timeband[0].strftime('%H:%M')}–{r.tariff.timeband[1].strftime('%H:%M')}
- **Дни недели:** {_weekday_str(r.tariff.weekday)}
- **Приоритет:** {r.tariff.priority}
- **Действует:** {r.tariff.effective_date} — {r.tariff.expiry_date}
""")


def _weekday_str(days: set[int]) -> str:
    names = {1: "Пн", 2: "Вт", 3: "Ср", 4: "Чт", 5: "Пт", 6: "Сб", 7: "Вс"}
    return ", ".join(names.get(d, str(d)) for d in sorted(days))
