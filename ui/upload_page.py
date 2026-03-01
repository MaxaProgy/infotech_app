import streamlit as st
import pandas as pd

from parsers.cdr_parser import parse_cdr
from parsers.tariff_parser import parse_tariffs
from parsers.subscriber_parser import parse_subscribers


def render_sidebar():
    with st.sidebar:
        st.header("Загрузка файлов")

        # CDR upload
        cdr_file = st.file_uploader("CDR файл (разделитель |)", type=["txt", "csv", "cdr"])
        if cdr_file is not None:
            records, errors = parse_cdr(cdr_file)
            st.session_state["parsed_cdr"] = records
            st.success(f"CDR: {len(records)} записей загружено")
            if errors:
                st.warning(f"CDR: {errors} ошибочных строк пропущено")

        # Tariff upload
        tariff_file = st.file_uploader("Файл тарифов (разделитель ;)", type=["txt", "csv"])
        if tariff_file is not None:
            tariffs, errors = parse_tariffs(tariff_file)
            st.session_state["parsed_tariffs"] = tariffs
            st.success(f"Тарифы: {len(tariffs)} записей загружено")
            if errors:
                st.warning(f"Тарифы: {errors} ошибочных строк пропущено")

        # Subscriber upload
        sub_file = st.file_uploader("Абонентская база (разделитель ;)", type=["txt", "csv"])
        if sub_file is not None:
            subscribers, errors = parse_subscribers(sub_file)
            st.session_state["subscribers"] = subscribers
            st.success(f"Абоненты: {len(subscribers)} записей загружено")
            if errors:
                st.warning(f"Абоненты: {errors} ошибочных строк пропущено")

        # Status indicators
        st.divider()
        all_loaded = all(
            k in st.session_state and st.session_state[k]
            for k in ("parsed_cdr", "parsed_tariffs", "subscribers")
        )

        if st.button("Запустить тарификацию", disabled=not all_loaded, type="primary"):
            st.session_state["run_tarification"] = True
            st.rerun()

        if not all_loaded:
            st.info("Загрузите все три файла для запуска тарификации")


def render_upload_tab():
    st.subheader("Превью загруженных данных")

    if "parsed_cdr" in st.session_state and st.session_state["parsed_cdr"]:
        records = st.session_state["parsed_cdr"]
        st.markdown(f"**CDR** — {len(records)} записей")
        rows = []
        for r in records[:5]:
            rows.append({
                "Время начала": str(r.start_time),
                "Откуда": r.calling_party,
                "Куда": r.called_party,
                "Направление": r.call_direction,
                "Статус": r.disposition,
                "Длительность (сек)": r.duration,
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
    else:
        st.info("CDR файл не загружен")

    if "parsed_tariffs" in st.session_state and st.session_state["parsed_tariffs"]:
        tariffs = st.session_state["parsed_tariffs"]
        st.markdown(f"**Тарифы** — {len(tariffs)} записей")
        rows = []
        for t in tariffs[:5]:
            rows.append({
                "Префикс": t.prefix,
                "Направление": t.destination,
                "Руб/мин": str(t.rate_per_min),
                "Соединение": str(t.connection_fee),
                "Время": f"{t.timeband[0].strftime('%H:%M')}-{t.timeband[1].strftime('%H:%M')}",
                "Дни": _weekday_str(t.weekday),
                "Приоритет": t.priority,
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
    else:
        st.info("Файл тарифов не загружен")

    if "subscribers" in st.session_state and st.session_state["subscribers"]:
        subs = st.session_state["subscribers"]
        st.markdown(f"**Абоненты** — {len(subs)} записей")
        rows = [{"Номер": k, "ФИО": v} for k, v in list(subs.items())[:5]]
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
    else:
        st.info("Файл абонентов не загружен")


def _weekday_str(days: set[int]) -> str:
    names = {1: "Пн", 2: "Вт", 3: "Ср", 4: "Чт", 5: "Пт", 6: "Сб", 7: "Вс"}
    sorted_days = sorted(days)
    return ", ".join(names.get(d, str(d)) for d in sorted_days)
