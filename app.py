
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Study 1: GHCNh QC — 2005–2025",
    page_icon="🌧️",
    layout="wide",
)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

CATEGORY_COLORS = {
    "A": "#d62728",
    "B": "#1f77b4",
    "C": "#7f7f7f",
}

QC_ORDER = [
    "QC1 — Excellent",
    "QC2 — Good",
    "QC3 — Caution",
    "QC4 — Poor",
    "Not evaluated",
]

QC_COLORS = {
    "QC1 — Excellent": "#2ca02c",
    "QC2 — Good": "#1f77b4",
    "QC3 — Caution": "#9467bd",
    "QC4 — Poor": "#d62728",
    "Not evaluated": "#7f7f7f",
}


GAP_TYPE_ORDER = [
    "REPORTING_OUTAGE",
    "PRECIP_SOURCE_GAP",
    "MIXED_OUTAGE",
]

GAP_TYPE_COLORS = {
    "REPORTING_OUTAGE": "#76b7eb",
    "PRECIP_SOURCE_GAP": "#006ecb",
    "MIXED_OUTAGE": "#ff2d2d",
}


def read_csv(name):
    p = DATA_DIR / name

    if not p.exists():
        st.error(
            f"Missing dashboard file: {p}"
        )
        st.stop()

    return pd.read_csv(
        p,
        low_memory=False,
    )


def download_csv(
    df,
    filename,
):
    st.download_button(
        "Download CSV",
        data=df.to_csv(
            index=False
        ).encode("utf-8"),
        file_name=filename,
        mime="text/csv",
    )


def station_map(
    df,
    color_col=None,
    colors=None,
    title=None,
):
    d = df.dropna(
        subset=[
            "LATITUDE",
            "LONGITUDE",
        ]
    ).copy()

    if d.empty:
        st.info(
            "No mapped stations."
        )
        return

    category_orders = None

    if color_col == "CAT_CODE":
        category_orders = {
            "CAT_CODE": [
                "A",
                "B",
                "C",
            ]
        }

    elif color_col == "QC_CLASS_DISPLAY":
        category_orders = {
            "QC_CLASS_DISPLAY": QC_ORDER
        }

    elif color_col == "GEOGRAPHY_STATUS":
        category_orders = {
            "GEOGRAPHY_STATUS": [
                "Exact state agreement",
                "True state mismatch",
                "Other / metadata review",
            ]
        }

    fig = px.scatter_geo(
        d,
        lat="LATITUDE",
        lon="LONGITUDE",
        scope="usa",
        projection="albers usa",
        color=color_col,
        color_discrete_map=colors,
        category_orders=category_orders,
        hover_name=(
            "NAME"
            if "NAME" in d.columns
            else None
        ),
        hover_data=[
            c
            for c in [
                "STATION_ID",
                "STATE",
                "QC_CLASS_DISPLAY",
                "VALID_PCT_2005_2025",
            ]
            if c in d.columns
        ],
        title=title,
    )

    if color_col == "CAT_CODE":
        # Draw C, then B, then A so A stays visually on top,
        # but use legendrank so the legend still reads A, B, C.
        draw_order = {
            "C": 0,
            "B": 1,
            "A": 2,
        }

        legend_order = {
            "A": 1,
            "B": 2,
            "C": 3,
        }

        fig.data = tuple(
            sorted(
                fig.data,
                key=lambda t:
                    draw_order.get(
                        t.name,
                        9,
                    ),
            )
        )

        for trace in fig.data:
            trace.legendrank = legend_order.get(
                trace.name,
                99,
            )

            if trace.name == "A":
                trace.marker.size = 8
                trace.marker.opacity = 1.0

            elif trace.name == "B":
                trace.marker.size = 5.5
                trace.marker.opacity = 0.75

            elif trace.name == "C":
                trace.marker.size = 4.5
                trace.marker.opacity = 0.5

    elif color_col == "QC_CLASS_DISPLAY":
        rank = {
            label: i + 1
            for i, label in enumerate(
                QC_ORDER
            )
        }

        for trace in fig.data:
            trace.legendrank = rank.get(
                trace.name,
                99,
            )

    elif color_col == "GEOGRAPHY_STATUS":
        geo_rank = {
            "Exact state agreement": 1,
            "True state mismatch": 2,
            "Other / metadata review": 3,
        }

        for trace in fig.data:
            trace.legendrank = geo_rank.get(
                trace.name,
                99,
            )

    fig.update_layout(
        height=560,
        legend_title_text="",
        margin=dict(
            l=0,
            r=0,
            t=40,
            b=0,
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


master = read_csv(
    "stations_master.csv"
)

qc = read_csv(
    "a_station_qc.csv"
)

annual = read_csv(
    "a_station_year.csv"
)

monthly = read_csv(
    "a_station_month.csv"
)

gaps = read_csv(
    "a_gap_events.csv"
)

network = read_csv(
    "a_network_months.csv"
)

hazard = read_csv(
    "a_hazard_candidates.csv"
)

for df in [
    master,
    qc,
    annual,
    monthly,
    gaps,
    hazard,
]:
    if "STATION_ID" in df.columns:
        df["STATION_ID"] = (
            df["STATION_ID"]
            .astype("string")
            .str.strip()
        )

for c in [
    "LATITUDE",
    "LONGITUDE",
    "VALID_PCT_2005_2025",
    "WORST_YEAR",
    "WORST_YEAR_PCT",
    "N_MONTHS_LT90",
    "LONGEST_CONTINUOUS_GAP_H",
]:
    if c in qc.columns:
        qc[c] = pd.to_numeric(
            qc[c],
            errors="coerce",
        )

for c in [
    "YEAR",
    "PRECIP_VALID_PCT",
    "WEATHER_REPORT_PCT",
    "PRECIP_OBSERVED_PCT",
]:
    if c in annual.columns:
        annual[c] = pd.to_numeric(
            annual[c],
            errors="coerce",
        )

for c in [
    "YEAR",
    "MONTH",
    "VALID_PCT",
    "MISSING_HOURS",
    "NO_WEATHER_REPORT_HOURS",
    "NO_REPORT_SHARE_PCT",
]:
    if c in monthly.columns:
        monthly[c] = pd.to_numeric(
            monthly[c],
            errors="coerce",
        )

for c in [
    "CORE_GAP_HOURS",
    "EVENT_NO_REPORT_SHARE_PCT",
]:
    if c in gaps.columns:
        gaps[c] = pd.to_numeric(
            gaps[c],
            errors="coerce",
        )

for c in [
    "YEAR",
    "MONTH",
    "N_STATIONS_EVALUATED",
    "PCT_STATIONS_LT90",
]:
    if c in network.columns:
        network[c] = pd.to_numeric(
            network[c],
            errors="coerce",
        )

if "FLAGGED_FOR_REVIEW" in network.columns:
    network[
        "FLAGGED_FOR_REVIEW"
    ] = (
        network[
            "FLAGGED_FOR_REVIEW"
        ]
        .astype("string")
        .str.lower()
        .isin(
            [
                "true",
                "1",
                "yes",
            ]
        )
    )

for df in [
    gaps,
    hazard,
]:
    for c in [
        "CORE_GAP_START_UTC",
        "CORE_GAP_END_UTC",
    ]:
        if c in df.columns:
            df[c] = pd.to_datetime(
                df[c],
                utc=True,
                errors="coerce",
            )


st.sidebar.title(
    "Study 1: GHCNh QC Dashboard"
)

st.sidebar.caption(
    "Primary Category A QC period: 2005–2025 (21 years)"
)

page = st.sidebar.radio(
    "Navigate",
    [
        "1 — Station Network Overview",
        "2 — Category A Quality Control",
        "3 — Monthly Completeness Explorer",
        "4 — Hourly Gap Explorer",
        "5 — Network-wide Completeness Check",
        "6 — Hazard Cross-check Candidates",
        "7 — Station Annual Explorer",
        "8 — Low-Completeness Review",
        "9 — State / Geography Audit",
    ],
)


if page == "1 — Station Network Overview":

    st.title(
        "Land-Screened GHCNh Station Network"
    )

    counts = (
        master["CAT_CODE"]
        .value_counts()
        .reindex(
            ["A", "B", "C"],
            fill_value=0,
        )
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "All retained stations",
        f"{len(master):,}",
    )

    c2.metric(
        "A — First Order",
        f"{int(counts.get('A', 0)):,}",
    )

    c3.metric(
        "B — ASOS/AWOS",
        f"{int(counts.get('B', 0)):,}",
    )

    c4.metric(
        "C — Other",
        f"{int(counts.get('C', 0)):,}",
    )

    f1, f2 = st.columns([1, 2])

    with f1:
        cats = st.multiselect(
            "Categories",
            options=["A", "B", "C"],
            default=["A", "B", "C"],
        )

    with f2:
        states = sorted(
            master["STATE"]
            .dropna()
            .astype(str)
            .str.strip()
            .loc[lambda s: s.ne("")]
            .unique()
        )

        selected_states = st.multiselect(
            "Spatial states",
            options=states,
            default=[],
            placeholder="All states",
        )

    view = master[
        master["CAT_CODE"].isin(cats)
    ].copy()

    if selected_states:
        view = view[
            view["STATE"]
            .astype(str)
            .str.strip()
            .isin(selected_states)
        ].copy()

    left, right = st.columns([2.2, 1])

    with left:
        station_map(
            view,
            "CAT_CODE",
            CATEGORY_COLORS,
            "Retained stations by category",
        )

    with right:
        cc = (
            view.groupby(
                "CAT_CODE",
                as_index=False,
            )
            .size()
            .rename(
                columns={"size": "N_STATIONS"}
            )
        )

        if not cc.empty:
            fig = px.bar(
                cc,
                x="CAT_CODE",
                y="N_STATIONS",
                color="CAT_CODE",
                color_discrete_map=CATEGORY_COLORS,
                text="N_STATIONS",
                title="Filtered station counts",
                category_orders={
                    "CAT_CODE": ["A", "B", "C"]
                },
            )

            fig.update_layout(
                showlegend=False,
                xaxis_title="",
                yaxis_title="Stations",
                height=410,
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

        st.markdown(
            """
**A — First Order**  
NOAA/NCEI HOMR PLCD / First Order stations.

**B — ASOS/AWOS**  
Confirmed ASOS/AWOS stations, excluding A.

**C — Other**  
Other retained GHCNh stations.
"""
        )

    st.subheader(
        f"Filtered station table — {len(view):,} stations"
    )

    st.dataframe(
        view,
        use_container_width=True,
        hide_index=True,
        height=500,
    )

    download_csv(
        view,
        "station_network_filtered.csv",
    )


elif page == "2 — Category A Quality Control":

    st.title(
        "Category A Quality Control — 2005–2025"
    )

    st.caption(
        "This page keeps the richer diagnostic layout from the earlier "
        "dashboard while using the current 2005–2025 Category A rebuild."
    )

    evaluated = qc[
        qc["CORE_STATUS"].eq("EVALUATED")
    ].copy()

    counts = (
        qc["QC_CLASS_DISPLAY"]
        .value_counts()
        .reindex(
            QC_ORDER,
            fill_value=0,
        )
    )

    cols = st.columns(6)

    cols[0].metric(
        "A stations",
        f"{len(qc):,}",
    )

    for col, label in zip(
        cols[1:],
        QC_ORDER,
    ):
        col.metric(
            label.replace(" — ", " "),
            f"{int(counts.get(label, 0)):,}",
        )

    f1, f2 = st.columns(2)

    with f1:
        class_options = [
            x
            for x in QC_ORDER
            if x in set(
                qc["QC_CLASS_DISPLAY"]
                .dropna()
                .astype(str)
            )
        ]

        selected_classes = st.multiselect(
            "QC classes",
            options=class_options,
            default=class_options,
        )

    with f2:
        states = sorted(
            qc["STATE"]
            .dropna()
            .astype(str)
            .str.strip()
            .loc[lambda s: s.ne("")]
            .unique()
        )

        selected_states = st.multiselect(
            "States",
            options=states,
            default=[],
            placeholder="All states",
        )

    view = qc[
        qc["QC_CLASS_DISPLAY"].isin(
            selected_classes
        )
    ].copy()

    if selected_states:
        view = view[
            view["STATE"]
            .astype(str)
            .str.strip()
            .isin(selected_states)
        ].copy()

    left, right = st.columns([2.1, 1])

    with left:
        station_map(
            view,
            "QC_CLASS_DISPLAY",
            QC_COLORS,
            "Category A stations by QC class",
        )

    with right:
        class_count = (
            view["QC_CLASS_DISPLAY"]
            .value_counts()
            .reindex(
                QC_ORDER,
                fill_value=0,
            )
            .rename_axis("QC_CLASS_DISPLAY")
            .reset_index(name="N_STATIONS")
        )

        class_count = class_count[
            class_count["N_STATIONS"].gt(0)
        ]

        if not class_count.empty:
            fig = px.bar(
                class_count,
                x="QC_CLASS_DISPLAY",
                y="N_STATIONS",
                color="QC_CLASS_DISPLAY",
                color_discrete_map=QC_COLORS,
                text="N_STATIONS",
                title="Filtered QC-class counts",
                category_orders={
                    "QC_CLASS_DISPLAY": QC_ORDER
                },
            )

            fig.update_layout(
                showlegend=False,
                xaxis_title="",
                yaxis_title="Stations",
                height=430,
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

    eval_view = view[
        view["CORE_STATUS"].eq("EVALUATED")
    ].copy()

    st.subheader(
        "Overall vs worst-year completeness"
    )

    if eval_view.empty:
        st.info(
            "No evaluated stations match the current filters."
        )

    else:
        plot_df = eval_view.copy()

        plot_df["LONGEST_GAP_DAYS"] = (
            pd.to_numeric(
                plot_df[
                    "LONGEST_CONTINUOUS_GAP_H"
                ],
                errors="coerce",
            )
            .fillna(0)
            / 24.0
        )

        fig = px.scatter(
            plot_df,
            x="VALID_PCT_2005_2025",
            y="WORST_YEAR_PCT",
            size="LONGEST_GAP_DAYS",
            color="QC_CLASS_DISPLAY",
            color_discrete_map=QC_COLORS,
            category_orders={
                "QC_CLASS_DISPLAY": QC_ORDER
            },
            hover_name="NAME",
            hover_data=[
                c
                for c in [
                    "STATION_ID",
                    "STATE",
                    "WORST_YEAR",
                    "N_MONTHS_LT90",
                    "LONGEST_CONTINUOUS_GAP_H",
                    "N_STRUCTURAL_GAPS_GE720H",
                ]
                if c in plot_df.columns
            ],
        )

        fig.add_vline(
            x=95,
            line_dash="dash",
        )

        fig.add_hline(
            y=90,
            line_dash="dot",
        )

        qc_rank = {
            label: i + 1
            for i, label in enumerate(
                QC_ORDER
            )
        }

        for trace in fig.data:
            trace.legendrank = qc_rank.get(
                trace.name,
                99,
            )

        fig.update_layout(
            xaxis_title=(
                "Overall valid precipitation (%)"
            ),
            yaxis_title=(
                "Worst-year valid precipitation (%)"
            ),
            height=520,
            legend_title_text="QC class",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    st.subheader(
        f"Category A QC table — {len(view):,} stations"
    )

    display_cols = [
        c
        for c in [
            "STATION_ID",
            "NAME",
            "STATE",
            "CORE_STATUS",
            "QC_CLASS_DISPLAY",
            "VALID_PCT_2005_2025",
            "WORST_YEAR",
            "WORST_YEAR_PCT",
            "N_MONTHS_LT90",
            "LONGEST_CONTINUOUS_GAP_H",
            "N_STRUCTURAL_GAPS_GE720H",
            "HAS_2025_SOURCE",
            "EXPECTED_HOURS_2005_2025",
            "VALID_HOURS_2005_2025",
            "LATITUDE",
            "LONGITUDE",
        ]
        if c in view.columns
    ]

    table = view[display_cols].copy()

    if "VALID_PCT_2005_2025" in table.columns:
        table = table.sort_values(
            "VALID_PCT_2005_2025",
            ascending=False,
            na_position="last",
        )

    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True,
        height=520,
    )

    download_csv(
        table,
        "category_A_qc_2005_2025_filtered.csv",
    )

    with st.expander(
        "QC classification criteria"
    ):
        criteria = pd.DataFrame(
            [
                [
                    "QC1 — Excellent",
                    "Overall valid ≥99%; worst year ≥95%; ≤4 months below 90%; longest continuous gap <168 h; no gap ≥720 h.",
                ],
                [
                    "QC2 — Good",
                    "Overall valid ≥98%; worst year ≥90%; ≤9 months below 90%; longest continuous gap <720 h; no gap ≥720 h.",
                ],
                [
                    "QC3 — Caution",
                    "Overall valid ≥95%, but does not satisfy all QC1 or QC2 criteria.",
                ],
                [
                    "QC4 — Poor",
                    "Overall valid precipitation completeness <95%.",
                ],
                [
                    "Not evaluated",
                    "Complete 2005–2025 core not available.",
                ],
            ],
            columns=["Class", "Criteria"],
        )

        st.dataframe(
            criteria,
            use_container_width=True,
            hide_index=True,
        )


elif page == "3 — Monthly Completeness Explorer":

    st.title(
        "Monthly Completeness Explorer — 2005–2025"
    )

    choices = (
        monthly[
            ["STATION_ID", "NAME", "STATE"]
        ]
        .drop_duplicates()
        .copy()
    )

    choices["LABEL"] = (
        choices["NAME"].astype(str)
        + " | "
        + choices["STATE"].astype(str)
        + " | "
        + choices["STATION_ID"].astype(str)
    )

    label = st.selectbox(
        "Station",
        sorted(
            choices["LABEL"].tolist()
        ),
    )

    sid = choices.loc[
        choices["LABEL"].eq(label),
        "STATION_ID",
    ].iloc[0]

    m = monthly[
        monthly["STATION_ID"].eq(sid)
    ].copy()

    qrow = qc[
        qc["STATION_ID"].eq(sid)
    ]

    if not qrow.empty:
        q = qrow.iloc[0]

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "QC class",
            q.get(
                "QC_CLASS_DISPLAY",
                "—",
            ),
        )

        c2.metric(
            "2005–2025 valid",
            (
                f"{q['VALID_PCT_2005_2025']:.2f}%"
                if pd.notna(
                    q.get(
                        "VALID_PCT_2005_2025",
                        np.nan,
                    )
                )
                else "—"
            ),
        )

        c3.metric(
            "Months below 90%",
            (
                f"{int(q['N_MONTHS_LT90']):,}"
                if pd.notna(
                    q.get(
                        "N_MONTHS_LT90",
                        np.nan,
                    )
                )
                else "—"
            ),
        )

        c4.metric(
            "Longest gap",
            (
                f"{q['LONGEST_CONTINUOUS_GAP_H'] / 24.0:.1f} days"
                if pd.notna(
                    q.get(
                        "LONGEST_CONTINUOUS_GAP_H",
                        np.nan,
                    )
                )
                else "—"
            ),
        )

    m["MONTH_START"] = pd.to_datetime(
        dict(
            year=m["YEAR"],
            month=m["MONTH"],
            day=1,
        ),
        errors="coerce",
    )

    fig = go.Figure()

    complete = m[
        m["MONTH_GAP_TYPE"].eq(
            "COMPLETE"
        )
    ]

    fig.add_trace(
        go.Scatter(
            x=complete["MONTH_START"],
            y=complete["VALID_PCT"],
            mode="markers",
            name="Complete",
            marker=dict(
                color="black",
                size=5,
                opacity=0.7,
            ),
        )
    )

    specs = [
        (
            "PRECIP_SOURCE_GAP",
            "Precipitation-source gap",
            "#1f77b4",
            "diamond",
        ),
        (
            "MIXED_GAP",
            "Mixed gap",
            "#9467bd",
            "triangle-up",
        ),
        (
            "MINOR_REPORTING_GAP",
            "Minor reporting gap",
            "#17a2a4",
            "square",
        ),
        (
            "STATION_REPORTING_GAP",
            "Station-reporting gap",
            "#d62728",
            "x",
        ),
    ]

    for code, name, color, symbol in specs:
        g = m[
            m["MONTH_GAP_TYPE"].eq(code)
        ]

        if g.empty:
            continue

        fig.add_trace(
            go.Scatter(
                x=g["MONTH_START"],
                y=g["VALID_PCT"],
                mode="markers",
                name=name,
                marker=dict(
                    color=color,
                    size=11,
                    symbol=symbol,
                ),
            )
        )

    for threshold in [90, 95, 98, 99, 100]:
        fig.add_hline(
            y=threshold,
            line_dash=(
                "dot"
                if threshold in [90, 100]
                else "dash"
            ),
        )

    fig.update_layout(
        title="Monthly precipitation completeness",
        xaxis_title="",
        yaxis_title="Valid (%)",
        yaxis_range=[0, 101],
        height=500,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    gap_months = m[
        ~m["MONTH_GAP_TYPE"].eq(
            "COMPLETE"
        )
        &
        m["DETAIL_STATUS"].eq(
            "EVALUATED"
        )
    ].copy()

    st.subheader(
        f"Gap months — {len(gap_months):,}"
    )

    gap_cols = [
        c
        for c in [
            "YEAR",
            "MONTH",
            "MONTH_GAP_TYPE",
            "VALID_PCT",
            "MISSING_HOURS",
            "NO_WEATHER_REPORT_HOURS",
            "REPORT_BUT_PRECIP_INVALID_HOURS",
            "NO_REPORT_SHARE_PCT",
        ]
        if c in gap_months.columns
    ]

    st.dataframe(
        gap_months[gap_cols],
        use_container_width=True,
        hide_index=True,
        height=460,
    )

    download_csv(
        gap_months[gap_cols],
        f"{sid}_monthly_gap_review_2005_2025.csv",
    )


elif page == "4 — Hourly Gap Explorer":

    st.title(
        "Hourly Gap Explorer — 2005–2025"
    )

    if gaps.empty:
        st.info(
            "No ≥24-hour gap events."
        )

    else:
        min_h = st.selectbox(
            "Minimum duration",
            [
                24,
                48,
                72,
                120,
                168,
                720,
            ],
            index=0,
        )

        gv = gaps[
            gaps[
                "CORE_GAP_HOURS"
            ].ge(
                min_h
            )
        ].copy()

        n_gap_stations = (
            gv[
                "STATION_ID"
            ]
            .nunique()
            if not gv.empty
            else 0
        )

        m1, m2 = st.columns(2)

        m1.metric(
            "Gap events",
            f"{len(gv):,}",
        )

        m2.metric(
            "Stations with qualifying gaps",
            f"{n_gap_stations:,}",
        )

        if gv.empty:
            st.info(
                "No gap events meet the selected minimum duration."
            )

        else:
            # ----------------------------------------------------
            # MAP: one equal-size marker per qualifying station.
            # Color = type of that station's longest qualifying gap.
            # Equal sizing avoids one extreme station hiding the rest.
            # ----------------------------------------------------
            station_gap = (
                gv.groupby(
                    "STATION_ID",
                    as_index=False,
                )
                .agg(
                    N_GAP_EVENTS=(
                        "CORE_GAP_HOURS",
                        "size",
                    ),
                    LONGEST_GAP_H=(
                        "CORE_GAP_HOURS",
                        "max",
                    ),
                    TOTAL_GAP_HOURS=(
                        "CORE_GAP_HOURS",
                        "sum",
                    ),
                )
            )

            station_meta = master[
                [
                    c
                    for c in [
                        "STATION_ID",
                        "NAME",
                        "STATE",
                        "LATITUDE",
                        "LONGITUDE",
                    ]
                    if c in master.columns
                ]
            ].drop_duplicates(
                "STATION_ID"
            )

            gap_map = station_gap.merge(
                station_meta,
                on="STATION_ID",
                how="left",
            )

            if "EVENT_GAP_TYPE_REFINED" in gv.columns:
                longest_type = (
                    gv.sort_values(
                        "CORE_GAP_HOURS"
                    )
                    .drop_duplicates(
                        "STATION_ID",
                        keep="last",
                    )
                    [
                        [
                            "STATION_ID",
                            "EVENT_GAP_TYPE_REFINED",
                        ]
                    ]
                    .rename(
                        columns={
                            "EVENT_GAP_TYPE_REFINED":
                                "LONGEST_GAP_TYPE"
                        }
                    )
                )

                gap_map = gap_map.merge(
                    longest_type,
                    on="STATION_ID",
                    how="left",
                )

            else:
                gap_map["LONGEST_GAP_TYPE"] = (
                    "Qualifying gap"
                )

            gap_map["LONGEST_GAP_DAYS"] = (
                pd.to_numeric(
                    gap_map["LONGEST_GAP_H"],
                    errors="coerce",
                )
                / 24.0
            )

            gap_map = gap_map.dropna(
                subset=[
                    "LATITUDE",
                    "LONGITUDE",
                ]
            ).copy()

            if not gap_map.empty:
                present_types = (
                    gap_map["LONGEST_GAP_TYPE"]
                    .dropna()
                    .astype(str)
                    .unique()
                    .tolist()
                )

                gap_order = (
                    [
                        x
                        for x in GAP_TYPE_ORDER
                        if x in present_types
                    ]
                    +
                    sorted(
                        [
                            x
                            for x in present_types
                            if x not in GAP_TYPE_ORDER
                        ]
                    )
                )

                fig_map = px.scatter_geo(
                    gap_map,
                    lat="LATITUDE",
                    lon="LONGITUDE",
                    scope="usa",
                    projection="albers usa",
                    color="LONGEST_GAP_TYPE",
                    color_discrete_map=GAP_TYPE_COLORS,
                    category_orders={
                        "LONGEST_GAP_TYPE":
                            gap_order
                    },
                    hover_name="NAME",
                    hover_data={
                        "STATION_ID": True,
                        "STATE": True,
                        "N_GAP_EVENTS": True,
                        "LONGEST_GAP_DAYS": ":,.1f",
                        "LONGEST_GAP_H": ":,.0f",
                        "TOTAL_GAP_HOURS": ":,.0f",
                        "LATITUDE": False,
                        "LONGITUDE": False,
                        "LONGEST_GAP_TYPE": True,
                    },
                    title=(
                        f"Stations with gaps ≥ {min_h:,} hours"
                    ),
                )

                gap_rank = {
                    label: i + 1
                    for i, label in enumerate(
                        gap_order
                    )
                }

                for trace in fig_map.data:
                    trace.marker.size = 12
                    trace.marker.opacity = 0.88
                    trace.legendrank = gap_rank.get(
                        trace.name,
                        99,
                    )

                fig_map.update_layout(
                    height=560,
                    legend_title_text="Gap type",
                    margin=dict(
                        l=0,
                        r=0,
                        t=55,
                        b=0,
                    ),
                )

                st.plotly_chart(
                    fig_map,
                    use_container_width=True,
                )

            else:
                st.info(
                    "Qualifying gap stations do not have map coordinates."
                )

        st.subheader(
            "Gap-event table"
        )

        st.dataframe(
            gv.sort_values(
                "CORE_GAP_HOURS",
                ascending=False,
            ),
            use_container_width=True,
            hide_index=True,
            height=600,
        )


elif page == "5 — Network-wide Completeness Check":

    st.title(
        "Network-wide Completeness Check — 2005–2025"
    )

    n = network.copy()

    n["MONTH_START"] = pd.to_datetime(
        dict(
            year=n["YEAR"],
            month=n["MONTH"],
            day=1,
        )
    )

    flagged = n[
        n["FLAGGED_FOR_REVIEW"]
    ].copy()

    peak_pct = pd.to_numeric(
        n["PCT_STATIONS_LT90"],
        errors="coerce",
    ).max()

    worst_month = "—"

    if not n.empty and pd.notna(peak_pct):
        worst_row = n.loc[
            pd.to_numeric(
                n["PCT_STATIONS_LT90"],
                errors="coerce",
            ).idxmax()
        ]

        worst_month = str(
            worst_row.get(
                "YEAR_MONTH",
                "—",
            )
        )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Months evaluated",
        f"{len(n):,}",
    )

    c2.metric(
        "Flagged months",
        f"{len(flagged):,}",
    )

    c3.metric(
        "Peak stations <90%",
        (
            f"{peak_pct:.2f}%"
            if pd.notna(peak_pct)
            else "—"
        ),
    )

    c4.metric(
        "Worst network month",
        worst_month,
    )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=n["MONTH_START"],
            y=n["PCT_STATIONS_LT90"],
            mode="lines+markers",
            name="All months",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=flagged["MONTH_START"],
            y=flagged["PCT_STATIONS_LT90"],
            mode="markers",
            name="Flagged",
            marker=dict(
                color="#d62728",
                size=11,
                symbol="diamond",
            ),
        )
    )

    fig.add_hline(
        y=5.0,
        line_dash="dash",
        line_color="black",
    )

    fig.update_layout(
        title=(
            "Current Category A stations below 90% monthly completeness"
        ),
        xaxis_title="Month",
        yaxis_title=(
            "Stations below 90% completeness (%)"
        ),
        height=520,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    c1, c2 = st.columns(2)

    with c1:
        if "MEDIAN_VALID_PCT" in n.columns:
            fig = px.line(
                n,
                x="MONTH_START",
                y="MEDIAN_VALID_PCT",
                title=(
                    "Network median monthly completeness"
                ),
            )

            fig.add_hline(
                y=95,
                line_dash="dash",
            )

            fig.add_hline(
                y=90,
                line_dash="dot",
            )

            fig.update_layout(
                xaxis_title="Month",
                yaxis_title="Median valid (%)",
                height=400,
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

    with c2:
        if (
            "N_STATIONS_LT90" in n.columns
            and
            not flagged.empty
        ):
            fig = px.bar(
                flagged,
                x="YEAR_MONTH",
                y="N_STATIONS_LT90",
                title="Stations below 90% in flagged months",
            )

            fig.update_layout(
                xaxis_title="Flagged month",
                yaxis_title="Stations",
                height=400,
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

    st.subheader(
        f"Flagged months — {len(flagged):,}"
    )

    flag_cols = [
        c
        for c in [
            "YEAR_MONTH",
            "N_STATIONS_EVALUATED",
            "N_STATIONS_LT90",
            "PCT_STATIONS_LT90",
            "MEDIAN_VALID_PCT",
        ]
        if c in flagged.columns
    ]

    st.dataframe(
        flagged[flag_cols],
        use_container_width=True,
        hide_index=True,
    )

    download_csv(
        flagged[flag_cols],
        "network_flagged_months_2005_2025.csv",
    )


elif page == "6 — Hazard Cross-check Candidates":

    st.title(
        "Hazard Cross-check Candidates — 2005–2025"
    )

    st.caption(
        "Candidate reporting/mixed outages are retained for external "
        "hazard cross-checking; this page does not automatically label "
        "an outage as a weather hazard."
    )

    if hazard.empty:
        st.info(
            "No candidates."
        )

    else:
        f1, f2 = st.columns([1, 2])

        with f1:
            min_h = st.selectbox(
                "Minimum duration",
                [24, 48, 72, 120, 168, 720],
                index=1,
            )

        with f2:
            states = sorted(
                hazard["STATE"]
                .dropna()
                .astype(str)
                .str.strip()
                .loc[lambda s: s.ne("")]
                .unique()
            )

            selected_states = st.multiselect(
                "States",
                options=states,
                default=[],
                placeholder="All states",
            )

        hv = hazard[
            hazard["CORE_GAP_HOURS"].ge(
                min_h
            )
        ].copy()

        if selected_states:
            hv = hv[
                hv["STATE"]
                .astype(str)
                .str.strip()
                .isin(selected_states)
            ].copy()

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Candidate events",
            f"{len(hv):,}",
        )

        c2.metric(
            "Stations represented",
            (
                f"{hv['STATION_ID'].nunique():,}"
                if not hv.empty
                else "0"
            ),
        )

        c3.metric(
            "States represented",
            (
                f"{hv['STATE'].nunique():,}"
                if not hv.empty
                else "0"
            ),
        )

        c4.metric(
            "Longest candidate",
            (
                f"{hv['CORE_GAP_HOURS'].max() / 24.0:,.1f} days"
                if not hv.empty
                else "—"
            ),
        )

        if hv.empty:
            st.info(
                "No candidate events meet the current filters."
            )

        else:
            station_meta = master[
                [
                    c
                    for c in [
                        "STATION_ID",
                        "LATITUDE",
                        "LONGITUDE",
                    ]
                    if c in master.columns
                ]
            ].drop_duplicates(
                "STATION_ID"
            )

            map_df = (
                hv.groupby(
                    [
                        "STATION_ID",
                        "NAME",
                        "STATE",
                    ],
                    as_index=False,
                )
                .agg(
                    N_CANDIDATES=(
                        "CORE_GAP_HOURS",
                        "size",
                    ),
                    LONGEST_GAP_H=(
                        "CORE_GAP_HOURS",
                        "max",
                    ),
                    TOTAL_GAP_HOURS=(
                        "CORE_GAP_HOURS",
                        "sum",
                    ),
                )
                .merge(
                    station_meta,
                    on="STATION_ID",
                    how="left",
                )
            )

            map_df = map_df.dropna(
                subset=[
                    "LATITUDE",
                    "LONGITUDE",
                ]
            )

            if not map_df.empty:
                fig = px.scatter_geo(
                    map_df,
                    lat="LATITUDE",
                    lon="LONGITUDE",
                    scope="usa",
                    projection="albers usa",
                    size="LONGEST_GAP_H",
                    size_max=24,
                    color="LONGEST_GAP_H",
                    hover_name="NAME",
                    hover_data={
                        "STATION_ID": True,
                        "STATE": True,
                        "N_CANDIDATES": True,
                        "LONGEST_GAP_H": ":,.0f",
                        "TOTAL_GAP_HOURS": ":,.0f",
                        "LATITUDE": False,
                        "LONGITUDE": False,
                    },
                    title=(
                        f"Hazard cross-check candidate locations ≥ {min_h:,} h"
                    ),
                )

                fig.update_layout(
                    height=540,
                    margin=dict(
                        l=0,
                        r=0,
                        t=50,
                        b=0,
                    ),
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True,
                )

            timeline = hv.copy()

            timeline["STATION_LABEL"] = (
                timeline["NAME"].astype(str)
                + " | "
                + timeline["STATE"].astype(str)
                + " | "
                + timeline["STATION_ID"].astype(str)
            )

            timeline = (
                timeline.sort_values(
                    "CORE_GAP_HOURS",
                    ascending=False,
                )
                .head(60)
            )

            fig = px.timeline(
                timeline,
                x_start="CORE_GAP_START_UTC",
                x_end="CORE_GAP_END_UTC",
                y="STATION_LABEL",
                color=(
                    "EVENT_GAP_TYPE_REFINED"
                    if "EVENT_GAP_TYPE_REFINED"
                    in timeline.columns
                    else None
                ),
                hover_data=[
                    c
                    for c in [
                        "CORE_GAP_HOURS",
                        "NO_WEATHER_REPORT_HOURS",
                        "REPORT_BUT_PRECIP_INVALID_HOURS",
                        "EVENT_NO_REPORT_SHARE_PCT",
                        "PCT_STATIONS_LT90",
                    ]
                    if c in timeline.columns
                ],
                title=(
                    "Timing of longest hazard cross-check candidates "
                    "(up to 60 events)"
                ),
            )

            fig.update_yaxes(
                autorange="reversed"
            )

            fig.update_layout(
                height=max(
                    420,
                    min(
                        1100,
                        30
                        * timeline[
                            "STATION_LABEL"
                        ].nunique()
                        + 180,
                    ),
                ),
                xaxis_title="Date",
                yaxis_title="Station",
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

        st.subheader(
            f"Candidate-event table — {len(hv):,}"
        )

        st.dataframe(
            hv.sort_values(
                "CORE_GAP_HOURS",
                ascending=False,
            ),
            use_container_width=True,
            hide_index=True,
            height=600,
        )

        download_csv(
            hv,
            "hazard_crosscheck_candidates_filtered.csv",
        )


elif page == "7 — Station Annual Explorer":

    st.title(
        "Station Annual Explorer — 2005–2025"
    )

    choices = (
        qc[
            ["STATION_ID", "NAME", "STATE"]
        ]
        .drop_duplicates()
        .copy()
    )

    choices["LABEL"] = (
        choices["NAME"].astype(str)
        + " | "
        + choices["STATE"].astype(str)
        + " | "
        + choices["STATION_ID"].astype(str)
    )

    label = st.selectbox(
        "Station",
        sorted(
            choices["LABEL"].tolist()
        ),
    )

    sid = choices.loc[
        choices["LABEL"].eq(label),
        "STATION_ID",
    ].iloc[0]

    a = annual[
        annual["STATION_ID"].eq(sid)
    ].sort_values(
        "YEAR"
    ).copy()

    q = qc[
        qc["STATION_ID"].eq(sid)
    ].iloc[0]

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "QC class",
        q["QC_CLASS_DISPLAY"],
    )

    c2.metric(
        "2005–2025 valid",
        (
            f"{q['VALID_PCT_2005_2025']:.2f}%"
            if pd.notna(
                q["VALID_PCT_2005_2025"]
            )
            else "—"
        ),
    )

    c3.metric(
        "Worst year",
        (
            f"{int(q['WORST_YEAR'])} ({q['WORST_YEAR_PCT']:.2f}%)"
            if (
                pd.notna(q["WORST_YEAR"])
                and
                pd.notna(q["WORST_YEAR_PCT"])
            )
            else "—"
        ),
    )

    c4.metric(
        "Longest continuous gap",
        (
            f"{q['LONGEST_CONTINUOUS_GAP_H'] / 24.0:.1f} days"
            if pd.notna(
                q["LONGEST_CONTINUOUS_GAP_H"]
            )
            else "—"
        ),
    )

    if a.empty:
        st.warning(
            "This station has no annual rows."
        )
        st.stop()

    fig = px.line(
        a,
        x="YEAR",
        y="PRECIP_VALID_PCT",
        markers=True,
        hover_data=[
            c
            for c in [
                "ANNUAL_STATUS",
                "EXPECTED_HOURS",
                "WEATHER_REPORT_PCT",
                "PRECIP_OBSERVED_PCT",
                "PRECIP_VALID_HOURS",
            ]
            if c in a.columns
        ],
        title=(
            f"{q['NAME']} — annual valid precipitation completeness"
        ),
    )

    annual_valid = pd.to_numeric(
        a["PRECIP_VALID_PCT"],
        errors="coerce",
    ).dropna()

    if annual_valid.empty:
        annual_y_range = [0, 101]

    else:
        min_valid = float(
            annual_valid.min()
        )

        # For high-completeness stations, avoid wasting most of the
        # figure on the empty 0–90% range. For poorer stations, expand
        # downward enough to show the actual low values.
        annual_y_min = max(
            0.0,
            min(
                90.0,
                float(
                    np.floor(
                        min_valid - 2.0
                    )
                ),
            ),
        )

        annual_y_range = [
            annual_y_min,
            100.5,
        ]

    fig.update_layout(
        xaxis_title="Year",
        yaxis_title=(
            "Valid hourly precipitation (%)"
        ),
        yaxis_range=annual_y_range,
        height=480,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    c1, c2 = st.columns(2)

    with c1:
        availability_cols = [
            c
            for c in [
                "WEATHER_REPORT_PCT",
                "PRECIP_OBSERVED_PCT",
                "PRECIP_VALID_PCT",
            ]
            if c in a.columns
        ]

        if availability_cols:
            long_df = (
                a[["YEAR"] + availability_cols]
                .melt(
                    id_vars="YEAR",
                    var_name="METRIC",
                    value_name="PCT",
                )
            )

            fig = px.line(
                long_df,
                x="YEAR",
                y="PCT",
                color="METRIC",
                markers=True,
                title=(
                    "Weather-report vs precipitation availability"
                ),
            )

            fig.update_layout(
                xaxis_title="Year",
                yaxis_title=(
                    "Percent of expected hours"
                ),
                yaxis_range=[0, 101],
                height=420,
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

    with c2:
        if (
            "EXPECTED_HOURS" in a.columns
            and
            "PRECIP_VALID_HOURS" in a.columns
        ):
            missing_df = a[
                [
                    "YEAR",
                    "EXPECTED_HOURS",
                    "PRECIP_VALID_HOURS",
                ]
            ].copy()

            missing_df["MISSING_HOURS"] = (
                pd.to_numeric(
                    missing_df[
                        "EXPECTED_HOURS"
                    ],
                    errors="coerce",
                )
                -
                pd.to_numeric(
                    missing_df[
                        "PRECIP_VALID_HOURS"
                    ],
                    errors="coerce",
                )
            )

            fig = px.bar(
                missing_df,
                x="YEAR",
                y="MISSING_HOURS",
                title=(
                    "Missing / invalid precipitation hours by year"
                ),
            )

            fig.update_layout(
                xaxis_title="Year",
                yaxis_title="Hours",
                height=420,
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

    table_cols = [
        c
        for c in [
            "YEAR",
            "ANNUAL_STATUS",
            "EXPECTED_HOURS",
            "WEATHER_REPORT_HOURS",
            "WEATHER_REPORT_PCT",
            "PRECIP_OBSERVED_HOURS",
            "PRECIP_OBSERVED_PCT",
            "PRECIP_VALID_HOURS",
            "PRECIP_VALID_PCT",
        ]
        if c in a.columns
    ]

    st.subheader(
        "Annual table"
    )

    st.dataframe(
        a[table_cols],
        use_container_width=True,
        hide_index=True,
        height=460,
    )

    download_csv(
        a[table_cols],
        f"{sid}_annual_completeness_2005_2025.csv",
    )


elif page == "8 — Low-Completeness Review":

    st.title(
        "Low-Completeness Review — 2005–2025"
    )

    st.caption(
        "Stations are not automatically removed because they fall "
        "below a threshold. This page is for diagnosis."
    )

    evaluated = qc[
        qc["CORE_STATUS"].eq(
            "EVALUATED"
        )
    ].copy()

    f1, f2 = st.columns([1, 2])

    with f1:
        threshold = st.slider(
            "Completeness threshold (%)",
            min_value=50.0,
            max_value=100.0,
            value=95.0,
            step=0.5,
        )

    with f2:
        states = sorted(
            evaluated["STATE"]
            .dropna()
            .astype(str)
            .str.strip()
            .loc[lambda s: s.ne("")]
            .unique()
        )

        selected_states = st.multiselect(
            "States",
            options=states,
            default=[],
            placeholder="All states",
        )

    review = evaluated[
        pd.to_numeric(
            evaluated[
                "VALID_PCT_2005_2025"
            ],
            errors="coerce",
        ).lt(
            threshold
        )
    ].copy()

    if selected_states:
        review = review[
            review["STATE"]
            .astype(str)
            .str.strip()
            .isin(selected_states)
        ].copy()

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        f"Stations <{threshold:.1f}%",
        f"{len(review):,}",
    )

    c2.metric(
        "States represented",
        (
            f"{review['STATE'].nunique():,}"
            if not review.empty
            else "0"
        ),
    )

    c3.metric(
        "Median valid",
        (
            f"{review['VALID_PCT_2005_2025'].median():.2f}%"
            if not review.empty
            else "—"
        ),
    )

    c4.metric(
        "Lowest valid",
        (
            f"{review['VALID_PCT_2005_2025'].min():.2f}%"
            if not review.empty
            else "—"
        ),
    )

    station_map(
        review,
        "QC_CLASS_DISPLAY",
        QC_COLORS,
        (
            "Stations below selected "
            "2005–2025 completeness threshold"
        ),
    )

    if not review.empty:
        plot_df = review.copy()

        plot_df["LONGEST_GAP_DAYS"] = (
            pd.to_numeric(
                plot_df[
                    "LONGEST_CONTINUOUS_GAP_H"
                ],
                errors="coerce",
            )
            .fillna(0)
            / 24.0
        )

        fig = px.scatter(
            plot_df,
            x="VALID_PCT_2005_2025",
            y="WORST_YEAR_PCT",
            size="LONGEST_GAP_DAYS",
            color="QC_CLASS_DISPLAY",
            color_discrete_map=QC_COLORS,
            hover_name="NAME",
            hover_data=[
                c
                for c in [
                    "STATION_ID",
                    "STATE",
                    "WORST_YEAR",
                    "N_MONTHS_LT90",
                    "LONGEST_CONTINUOUS_GAP_H",
                    "N_STRUCTURAL_GAPS_GE720H",
                ]
                if c in plot_df.columns
            ],
            title="Low-completeness diagnostics",
            category_orders={
                "QC_CLASS_DISPLAY": QC_ORDER
            },
        )

        fig.add_vline(
            x=90,
            line_dash="dot",
        )

        fig.add_hline(
            y=90,
            line_dash="dot",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    display_cols = [
        c
        for c in [
            "STATION_ID",
            "NAME",
            "STATE",
            "QC_CLASS_DISPLAY",
            "CORE_STATUS",
            "HAS_2025_SOURCE",
            "EXPECTED_HOURS_2005_2025",
            "VALID_HOURS_2005_2025",
            "VALID_PCT_2005_2025",
            "WORST_YEAR",
            "WORST_YEAR_PCT",
            "N_MONTHS_LT90",
            "LONGEST_CONTINUOUS_GAP_H",
            "N_STRUCTURAL_GAPS_GE720H",
            "LATITUDE",
            "LONGITUDE",
        ]
        if c in review.columns
    ]

    st.subheader(
        f"Stations to inspect — {len(review):,}"
    )

    table = review[display_cols].copy()

    if "VALID_PCT_2005_2025" in table.columns:
        table = table.sort_values(
            "VALID_PCT_2005_2025",
            na_position="last",
        )

    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True,
        height=520,
    )

    download_csv(
        table,
        "category_A_low_completeness_review_2005_2025.csv",
    )


elif page == "9 — State / Geography Audit":

    st.title(
        "State and Coordinate Audit"
    )

    st.caption(
        "`STATE` is the coordinate-based state used for map/filter "
        "behavior. `STATE_GHCNH` preserves the original GHCNh metadata "
        "when available."
    )

    geo = master.copy()

    if "STATE_MISMATCH" in geo.columns:
        mismatch_flag = (
            geo["STATE_MISMATCH"]
            .astype("string")
            .str.strip()
            .str.lower()
            .isin(
                ["true", "1", "yes", "y", "t"]
            )
        )
    else:
        mismatch_flag = pd.Series(
            False,
            index=geo.index,
        )

    if "STATE_CHECK" in geo.columns:
        state_check = (
            geo["STATE_CHECK"]
            .astype("string")
            .str.strip()
        )

        exact_flag = state_check.eq(
            "AGREE_EXACT"
        )
    else:
        exact_flag = ~mismatch_flag

    other_flag = (
        ~exact_flag
        &
        ~mismatch_flag
    )

    geo["GEOGRAPHY_STATUS"] = np.select(
        [
            exact_flag,
            mismatch_flag,
            other_flag,
        ],
        [
            "Exact state agreement",
            "True state mismatch",
            "Other / metadata review",
        ],
        default="Other / metadata review",
    )

    total_n = int(len(geo))
    exact_n = int(exact_flag.sum())
    mismatch_n = int(mismatch_flag.sum())
    other_n = int(other_flag.sum())

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Total retained stations",
        f"{total_n:,}",
    )

    c2.metric(
        "Exact state agreement",
        f"{exact_n:,}",
    )

    c3.metric(
        "True state mismatches",
        f"{mismatch_n:,}",
    )

    c4.metric(
        "Other / metadata review",
        f"{other_n:,}",
    )

    f1, f2 = st.columns(2)

    with f1:
        status_options = [
            "Exact state agreement",
            "True state mismatch",
            "Other / metadata review",
        ]

        selected_statuses = st.multiselect(
            "Geography statuses",
            options=status_options,
            default=status_options,
        )

    with f2:
        cats = st.multiselect(
            "Categories",
            options=["A", "B", "C"],
            default=["A", "B", "C"],
        )

    view = geo[
        geo["GEOGRAPHY_STATUS"].isin(
            selected_statuses
        )
        &
        geo["CAT_CODE"].isin(cats)
    ].copy()

    st.metric(
        "Stations shown",
        f"{len(view):,}",
    )

    station_map(
        view,
        "GEOGRAPHY_STATUS",
        None,
        "Stations selected for geographic audit",
    )

    display_cols = [
        c
        for c in [
            "STATION_ID",
            "NAME",
            "CAT_CODE",
            "STATE_GHCNH",
            "STATE",
            "STATE_CHECK",
            "STATE_MISMATCH",
            "GEOGRAPHY_STATUS",
            "DIST_TO_GHCNH_STATE_KM",
            "STATE_ASSIGN_METHOD",
            "STATE_ASSIGN_DIST_KM",
            "LATITUDE",
            "LONGITUDE",
            "LAND_MASK_SOURCE",
        ]
        if c in view.columns
    ]

    st.subheader(
        "Geographic audit table"
    )

    table = view[display_cols].copy()

    sort_cols = [
        c
        for c in [
            "GEOGRAPHY_STATUS",
            "CAT_CODE",
            "STATE",
            "NAME",
        ]
        if c in table.columns
    ]

    if sort_cols:
        table = table.sort_values(
            sort_cols
        )

    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True,
        height=520,
    )

    download_csv(
        table,
        "state_geography_audit_filtered.csv",
    )


