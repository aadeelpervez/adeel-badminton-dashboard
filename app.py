
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="Badminton Analytics",
    page_icon="🏸",
    layout="wide"
)

st.title("🏸 Badminton Analytics Dashboard")
st.caption("Interactive data analysis and visualization")

file_path = Path(__file__).parent / "badminton.csv"

@st.cache_data
def load_data(path):
    return pd.read_csv(path)

try:
    df = load_data(str(file_path))
    df.columns = df.columns.astype(str).str.strip()

    st.sidebar.header("Dashboard Filters")
    search = st.sidebar.text_input("🔎 Search all columns")
    filtered = df.copy()

    text_cols = filtered.select_dtypes(
        include=["object", "category", "string", "bool"]
    ).columns.tolist()

    if text_cols:
        filter_col = st.sidebar.selectbox(
            "Filter by category", ["All"] + text_cols
        )

        if filter_col != "All":
            options = sorted(
                filtered[filter_col].dropna().astype(str).unique().tolist()
            )
            selected = st.sidebar.multiselect(
                f"Select {filter_col}", options, default=options
            )
            filtered = filtered[
                filtered[filter_col].fillna("").astype(str).isin(selected)
            ]

    if search:
        mask = filtered.astype(str).apply(
            lambda col: col.str.contains(
                search, case=False, na=False, regex=False
            )
        ).any(axis=1)
        filtered = filtered[mask]

    # KPI cards
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Records", f"{len(filtered):,}")
    c2.metric("Total Columns", len(filtered.columns))
    c3.metric("Missing Values", f"{filtered.isna().sum().sum():,}")
    c4.metric("Duplicate Rows", f"{filtered.duplicated().sum():,}")

    st.divider()

    if filtered.empty:
        st.warning("No records match your filters.")
        st.stop()

    numeric_cols = filtered.select_dtypes(include="number").columns.tolist()
    category_cols = filtered.select_dtypes(
        include=["object", "category", "string", "bool"]
    ).columns.tolist()

    overview, category_tab, numeric_tab, data_tab = st.tabs([
        "📊 Overview", "📂 Categories", "📈 Numeric Analysis", "📋 Data Explorer"
    ])

    with overview:
        left, right = st.columns(2)

        with left:
            st.subheader("Missing Values")
            missing = filtered.isna().sum()
            missing = missing[missing > 0].sort_values(ascending=False)

            if not missing.empty:
                missing_df = missing.rename_axis("Column").reset_index(
                    name="Missing Values"
                )
                fig = px.bar(
                    missing_df, x="Column", y="Missing Values",
                    text_auto=True, title="Data Quality Overview"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.success("No missing values in filtered data.")

        with right:
            st.subheader("Dataset Structure")
            types = filtered.dtypes.astype(str).value_counts()
            types_df = types.rename_axis("Data Type").reset_index(name="Count")
            fig = px.pie(
                types_df, names="Data Type", values="Count",
                hole=0.5, title="Column Data Types"
            )
            st.plotly_chart(fig, use_container_width=True)

    with category_tab:
        if category_cols:
            cat = st.selectbox(
                "Choose category", category_cols, key="category"
            )
            counts = (
                filtered[cat].fillna("Missing").astype(str)
                .value_counts().head(15)
                .rename_axis(cat).reset_index(name="Count")
            )

            left, right = st.columns(2)

            with left:
                fig = px.bar(
                    counts.sort_values("Count"),
                    x="Count", y=cat, orientation="h",
                    text="Count", title=f"Top Categories: {cat}"
                )
                st.plotly_chart(fig, use_container_width=True)

            with right:
                fig = px.pie(
                    counts, names=cat, values="Count",
                    hole=0.45, title=f"Category Share: {cat}"
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No categorical columns found.")

    with numeric_tab:
        if numeric_cols:
            num = st.selectbox(
                "Choose numeric column", numeric_cols, key="numeric"
            )
            values = pd.to_numeric(filtered[num], errors="coerce").dropna()

            if not values.empty:
                a, b, c = st.columns(3)
                a.metric("Average", f"{values.mean():,.2f}")
                b.metric("Median", f"{values.median():,.2f}")
                c.metric(
                    "Min – Max",
                    f"{values.min():,.2f} – {values.max():,.2f}"
                )

                left, right = st.columns(2)

                with left:
                    fig = px.histogram(
                        filtered, x=num, nbins=25, marginal="box",
                        title=f"Distribution: {num}"
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with right:
                    fig = px.box(
                        filtered, y=num, points="outliers",
                        title=f"Outlier Analysis: {num}"
                    )
                    st.plotly_chart(fig, use_container_width=True)

            if len(numeric_cols) >= 2:
                st.subheader("Correlation Heatmap")
                corr = filtered[numeric_cols].corr()
                fig = px.imshow(
                    corr, text_auto=".2f", aspect="auto",
                    color_continuous_scale="RdBu_r",
                    zmin=-1, zmax=1, title="Numeric Correlations"
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No numeric columns found.")

    with data_tab:
        st.subheader("Badminton Dataset")
        st.dataframe(filtered, use_container_width=True, hide_index=True)

        st.download_button(
            "⬇️ Download Filtered CSV",
            data=filtered.to_csv(index=False).encode("utf-8"),
            file_name="badminton_filtered.csv",
            mime="text/csv"
        )

except FileNotFoundError:
    st.error("badminton.csv nahi mili. CSV ko app.py ke same folder mein rakhein.")
except Exception as e:
    st.error(f"Dashboard error: {e}")
