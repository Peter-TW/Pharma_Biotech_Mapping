from __future__ import annotations

import pandas as pd
import streamlit as st

from data import (
    LIFECYCLE_STAGES,
    load_modality_taxonomy,
    load_therapeutic_area_taxonomy,
)


def _active_taxonomy_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Return active taxonomy rows sorted by Display_Order, robust to string booleans."""
    if df.empty:
        return df.copy()

    out = df.copy()
    if "Is_Active" in out.columns:
        active = out["Is_Active"].astype(str).str.strip().str.upper().isin(["TRUE", "Y", "YES", "1"])
        # If the loader already produced booleans, preserve them too.
        active = active | (out["Is_Active"] == True)
        out = out[active].copy()

    if "Display_Order" in out.columns:
        out["Display_Order"] = pd.to_numeric(out["Display_Order"], errors="coerce")
        out = out.sort_values("Display_Order")

    return out


def _normalise_yn_flags(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Normalize profile Y/N flag columns so lowercase/whitespace values still work."""
    return (
        df[cols]
        .fillna("N")
        .astype(str)
        .apply(lambda col: col.str.strip().str.upper())
    )


def init_filter_state(master: pd.DataFrame) -> None:
    """Initialize st.session_state keys with defaults. No-op if already set."""
    if "filter_lifecycle" not in st.session_state:
        st.session_state.filter_lifecycle = "All companies"

    if "filter_tas" not in st.session_state:
        try:
            ta_df = _active_taxonomy_rows(load_therapeutic_area_taxonomy())
            active_tas = ta_df["Therapeutic_Area"].dropna().astype(str).tolist()
        except Exception:
            active_tas = []
        st.session_state.filter_tas = active_tas

    if "filter_modalities" not in st.session_state:
        st.session_state.filter_modalities = []

    if "selected_company_uid" not in st.session_state:
        if not master.empty:
            st.session_state.selected_company_uid = master.iloc[0]["Unique_ID"]
        else:
            st.session_state.selected_company_uid = None


def render_sidebar_filters(
    master: pd.DataFrame,
    profile: pd.DataFrame,
    ta_taxonomy: pd.DataFrame,
    mo_taxonomy: pd.DataFrame,
) -> None:
    """Render all sidebar widgets. State is read from / written to st.session_state."""
    st.sidebar.radio(
        "Lifecycle filter",
        ["All companies", "Full-cycle only", "Non-full-cycle only"],
        key="filter_lifecycle",
    )

    active_ta_df = _active_taxonomy_rows(ta_taxonomy)
    ta_options = active_ta_df["Therapeutic_Area"].dropna().astype(str).tolist()

    # Prune stale selections after taxonomy/display-name edits.
    current_tas = st.session_state.get("filter_tas", [])
    st.session_state.filter_tas = [x for x in current_tas if x in ta_options]

    missing_ta_cols = [
        col for col in active_ta_df.get("Profile_Column", pd.Series(dtype=str)).dropna().astype(str)
        if col not in profile.columns
    ]
    if missing_ta_cols:
        st.sidebar.warning(
            "Missing Therapeutic Area columns in profile: " + ", ".join(missing_ta_cols)
        )

    st.sidebar.multiselect(
        "Therapeutic area exposure",
        options=ta_options,
        key="filter_tas",
        help="Active-in filter: keeps companies with Y in at least one selected therapeutic-area exposure column.",
    )

    with st.sidebar.expander("▼ Advanced filters", expanded=False):
        active_mo_df = _active_taxonomy_rows(mo_taxonomy)
        mo_options = active_mo_df["Modality_Name"].dropna().astype(str).tolist()

        # Prune stale selections after taxonomy/display-name edits.
        current_modalities = st.session_state.get("filter_modalities", [])
        st.session_state.filter_modalities = [x for x in current_modalities if x in mo_options]

        missing_mo_cols = [
            col for col in active_mo_df.get("Profile_Column", pd.Series(dtype=str)).dropna().astype(str)
            if col not in profile.columns
        ]
        if missing_mo_cols:
            st.warning("Missing Modality columns in profile: " + ", ".join(missing_mo_cols))

        st.multiselect(
            "Modality exposure",
            options=mo_options,
            key="filter_modalities",
            help="Advanced active-in filter: if selected, keeps companies with Y in at least one selected modality column.",
        )


def resolve_filtered_universe(
    master: pd.DataFrame,
    profile: pd.DataFrame,
    financials_latest: pd.DataFrame,
) -> set[str]:
    """Apply all active filters from session_state. Return set of Unique_IDs."""
    init_filter_state(master)

    lifecycle_choice = st.session_state.filter_lifecycle

    lc_df = master[["Unique_ID"] + LIFECYCLE_STAGES].copy()
    for col in LIFECYCLE_STAGES:
        lc_df[col] = lc_df[col].astype(str).str.strip().str.upper() == "TRUE"

    active_counts = lc_df[LIFECYCLE_STAGES].sum(axis=1)
    full_ids = set(lc_df.loc[active_counts == 5, "Unique_ID"])

    if lifecycle_choice == "Full-cycle only":
        pool_ids = set(master.loc[master["Unique_ID"].isin(full_ids), "Unique_ID"])
    elif lifecycle_choice == "Non-full-cycle only":
        pool_ids = set(master.loc[~master["Unique_ID"].isin(full_ids), "Unique_ID"])
    else:
        pool_ids = set(master["Unique_ID"])

    profile_merged = pd.DataFrame({"Unique_ID": list(pool_ids)}).merge(
        profile,
        on="Unique_ID",
        how="left",
    )

    selected_tas = st.session_state.get("filter_tas", [])
    if selected_tas:
        ta_tax = load_therapeutic_area_taxonomy()
        selected_cols = (
            ta_tax[ta_tax["Therapeutic_Area"].isin(selected_tas)]["Profile_Column"]
            .dropna()
            .astype(str)
            .tolist()
        )

        valid_cols = [c for c in selected_cols if c in profile_merged.columns]
        if valid_cols:
            ta_mask = _normalise_yn_flags(profile_merged, valid_cols).eq("Y")
            passed_ta = profile_merged.loc[ta_mask.any(axis=1), "Unique_ID"]
            pool_ids = pool_ids.intersection(set(passed_ta))
        else:
            pool_ids = set()
    else:
        # Explicitly clearing all therapeutic areas means no therapeutic-area universe is selected.
        pool_ids = set()

    selected_modalities = st.session_state.get("filter_modalities", [])
    if selected_modalities:
        mo_tax = load_modality_taxonomy()
        selected_cols = (
            mo_tax[mo_tax["Modality_Name"].isin(selected_modalities)]["Profile_Column"]
            .dropna()
            .astype(str)
            .tolist()
        )

        valid_cols = [c for c in selected_cols if c in profile_merged.columns]
        if valid_cols:
            mo_mask = _normalise_yn_flags(profile_merged, valid_cols).eq("Y")
            passed_mo = profile_merged.loc[mo_mask.any(axis=1), "Unique_ID"]
            pool_ids = pool_ids.intersection(set(passed_mo))
        else:
            pool_ids = set()

    current_sel = st.session_state.selected_company_uid
    if current_sel not in pool_ids and pool_ids:
        fin_pool = financials_latest[financials_latest["Unique_ID"].isin(pool_ids)].copy()
        if not fin_pool.empty:
            largest = fin_pool.sort_values("Market_Cap_USD_M", ascending=False).iloc[0]["Unique_ID"]
            st.session_state.selected_company_uid = largest
        else:
            master_pool = master[master["Unique_ID"].isin(pool_ids)].copy()
            if not master_pool.empty:
                first = master_pool.sort_values("Company Name").iloc[0]["Unique_ID"]
                st.session_state.selected_company_uid = first

    return pool_ids
