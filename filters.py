from __future__ import annotations

import pandas as pd
import streamlit as st

from data import (
    LIFECYCLE_STAGES,
    load_modality_taxonomy,
    load_therapeutic_area_taxonomy,
)


_BOOL_TRUE = ["TRUE", "Y", "YES", "1"]


def _active_taxonomy_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Return active taxonomy rows sorted by Display_Order, robust to string booleans."""
    if df.empty:
        return df.copy()

    out = df.copy()
    if "Is_Active" in out.columns:
        active = out["Is_Active"].astype(str).str.strip().str.upper().isin(_BOOL_TRUE)
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


def _company_label(row: pd.Series) -> str:
    """Return a readable company label for sidebar controls."""
    name = str(row.get("Company Name", "")).strip()
    ticker = row.get("Ticker")
    ticker_s = "" if pd.isna(ticker) else str(ticker).strip()
    if ticker_s and ticker_s.lower() != "nan":
        return f"{name} ({ticker_s})"
    return name


def _ordered_company_ids(master: pd.DataFrame) -> list[str]:
    """Return company IDs ordered by display name."""
    if master.empty or "Unique_ID" not in master.columns:
        return []
    cols = ["Unique_ID", "Company Name"] + (["Ticker"] if "Ticker" in master.columns else [])
    ordered = master[cols].copy()
    ordered["_label"] = ordered.apply(_company_label, axis=1)
    return ordered.sort_values("_label")["Unique_ID"].dropna().astype(str).tolist()


def _company_label_map(master: pd.DataFrame) -> dict[str, str]:
    """Map Unique_ID to a readable company label."""
    if master.empty or "Unique_ID" not in master.columns:
        return {}
    labels = {}
    for _, row in master.iterrows():
        uid = row.get("Unique_ID")
        if pd.notna(uid):
            labels[str(uid)] = _company_label(row)
    return labels


def _first_or_none(values: list[str]) -> str | None:
    return values[0] if values else None


# ── Select-all callbacks ─────────────────────────────────────────────

def _sync_select_all_to_multiselect(all_key: str, list_key: str, options: list[str]) -> None:
    """Checkbox callback: checking selects all, unchecking clears the list."""
    if st.session_state.get(all_key, False):
        st.session_state[list_key] = list(options)
    else:
        st.session_state[list_key] = []


def _sync_multiselect_to_select_all(all_key: str, list_key: str, options: list[str]) -> None:
    """Multiselect callback: keep the select-all checkbox in sync."""
    selected = st.session_state.get(list_key, [])
    st.session_state[all_key] = bool(options) and set(selected) == set(options)


def init_filter_state(master: pd.DataFrame) -> None:
    """Initialize st.session_state keys with defaults. No-op if already set."""
    if "filter_lifecycle" not in st.session_state:
        st.session_state.filter_lifecycle = "All companies"

    try:
        ta_df = _active_taxonomy_rows(load_therapeutic_area_taxonomy())
        active_tas = ta_df["Therapeutic_Area"].dropna().astype(str).tolist()
    except Exception:
        active_tas = []

    if "filter_all_tas" not in st.session_state:
        st.session_state.filter_all_tas = True
    if "filter_ta_single" not in st.session_state:
        st.session_state.filter_ta_single = _first_or_none(active_tas)
    # Backwards-compatible key from the older multiselect version.
    if "filter_tas" not in st.session_state:
        st.session_state.filter_tas = active_tas

    try:
        mo_df = _active_taxonomy_rows(load_modality_taxonomy())
        active_modalities = mo_df["Modality_Name"].dropna().astype(str).tolist()
    except Exception:
        active_modalities = []

    if "filter_all_modalities" not in st.session_state:
        st.session_state.filter_all_modalities = True
    if "filter_modality_single" not in st.session_state:
        st.session_state.filter_modality_single = _first_or_none(active_modalities)
    # Backwards-compatible key from the older multiselect version.
    if "filter_modalities" not in st.session_state:
        st.session_state.filter_modalities = active_modalities

    if "filter_company_uids" not in st.session_state:
        st.session_state.filter_company_uids = _ordered_company_ids(master)

    if "filter_all_companies" not in st.session_state:
        st.session_state.filter_all_companies = True

    if "selected_company_uid" not in st.session_state:
        ids = _ordered_company_ids(master)
        st.session_state.selected_company_uid = ids[0] if ids else None


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

    # ── Therapeutic-area exposure dropdown ───────────────────────────
    active_ta_df = _active_taxonomy_rows(ta_taxonomy)
    ta_options = active_ta_df["Therapeutic_Area"].dropna().astype(str).tolist()

    missing_ta_cols = [
        col for col in active_ta_df.get("Profile_Column", pd.Series(dtype=str)).dropna().astype(str)
        if col not in profile.columns
    ]
    if missing_ta_cols:
        st.sidebar.warning(
            "Missing Therapeutic Area columns in profile: " + ", ".join(missing_ta_cols)
        )

    # Keep selected value valid after taxonomy/display-name edits.
    if st.session_state.get("filter_ta_single") not in ta_options:
        st.session_state.filter_ta_single = _first_or_none(ta_options)

    st.sidebar.checkbox("Select all therapeutic areas", key="filter_all_tas")

    if st.session_state.get("filter_all_tas", False):
        st.sidebar.selectbox(
            "Therapeutic area exposure",
            options=["All therapeutic areas"],
            index=0,
            disabled=True,
            help="Select all is enabled, so therapeutic area does not restrict the universe.",
        )
    else:
        st.sidebar.selectbox(
            "Therapeutic area exposure",
            options=ta_options,
            key="filter_ta_single",
            help="Active-in filter: keeps companies with Y in the selected therapeutic-area exposure column.",
        )

    # ── Modality exposure dropdown ───────────────────────────────────
    active_mo_df = _active_taxonomy_rows(mo_taxonomy)
    mo_options = active_mo_df["Modality_Name"].dropna().astype(str).tolist()

    missing_mo_cols = [
        col for col in active_mo_df.get("Profile_Column", pd.Series(dtype=str)).dropna().astype(str)
        if col not in profile.columns
    ]
    if missing_mo_cols:
        st.sidebar.warning("Missing Modality columns in profile: " + ", ".join(missing_mo_cols))

    # Keep selected value valid after taxonomy/display-name edits.
    if st.session_state.get("filter_modality_single") not in mo_options:
        st.session_state.filter_modality_single = _first_or_none(mo_options)

    st.sidebar.checkbox("Select all modalities", key="filter_all_modalities")

    if st.session_state.get("filter_all_modalities", False):
        st.sidebar.selectbox(
            "Modality exposure",
            options=["All modalities"],
            index=0,
            disabled=True,
            help="Select all is enabled, so modality does not restrict the universe.",
        )
    else:
        st.sidebar.selectbox(
            "Modality exposure",
            options=mo_options,
            key="filter_modality_single",
            help="Active-in filter: keeps companies with Y in the selected modality column.",
        )

    # ── Company universe dropdown ────────────────────────────────────
    # Company filtering remains a multi-select because users may want a custom peer group.
    # The focused company selector in app.py remains the single selectbox for detail views.
    company_options = _ordered_company_ids(master)
    company_labels = _company_label_map(master)

    current_companies = [str(x) for x in st.session_state.get("filter_company_uids", [])]
    st.session_state.filter_company_uids = [x for x in current_companies if x in company_options]
    if st.session_state.get("filter_all_companies", False):
        st.session_state.filter_company_uids = list(company_options)

    st.sidebar.checkbox(
        "Select all companies",
        key="filter_all_companies",
        on_change=_sync_select_all_to_multiselect,
        args=("filter_all_companies", "filter_company_uids", company_options),
    )
    st.sidebar.multiselect(
        "Company filter",
        options=company_options,
        key="filter_company_uids",
        format_func=lambda uid: company_labels.get(str(uid), str(uid)),
        help="Shrinks the dashboard universe to the selected companies. The detail selector below chooses the focused company.",
        on_change=_sync_multiselect_to_select_all,
        args=("filter_all_companies", "filter_company_uids", company_options),
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
    full_ids = set(lc_df.loc[active_counts == 5, "Unique_ID"].astype(str))

    master_uids = set(master["Unique_ID"].dropna().astype(str))
    if lifecycle_choice == "Full-cycle only":
        pool_ids = master_uids.intersection(full_ids)
    elif lifecycle_choice == "Non-full-cycle only":
        pool_ids = master_uids - full_ids
    else:
        pool_ids = master_uids

    profile_merged = pd.DataFrame({"Unique_ID": list(pool_ids)}).merge(
        profile.assign(Unique_ID=profile["Unique_ID"].astype(str)),
        on="Unique_ID",
        how="left",
    )

    # Therapeutic area: select all = no restriction; otherwise filter to one selected exposure.
    ta_tax = _active_taxonomy_rows(load_therapeutic_area_taxonomy())
    all_tas = ta_tax["Therapeutic_Area"].dropna().astype(str).tolist()
    if not st.session_state.get("filter_all_tas", True):
        selected_ta = st.session_state.get("filter_ta_single")
        if selected_ta not in all_tas:
            pool_ids = set()
        else:
            selected_cols = (
                ta_tax[ta_tax["Therapeutic_Area"] == selected_ta]["Profile_Column"]
                .dropna()
                .astype(str)
                .tolist()
            )
            valid_cols = [c for c in selected_cols if c in profile_merged.columns]
            if valid_cols:
                ta_mask = _normalise_yn_flags(profile_merged, valid_cols).eq("Y")
                passed_ta = profile_merged.loc[ta_mask.any(axis=1), "Unique_ID"].astype(str)
                pool_ids = pool_ids.intersection(set(passed_ta))
            else:
                pool_ids = set()

    # Modality: select all = no restriction; otherwise filter to one selected exposure.
    mo_tax = _active_taxonomy_rows(load_modality_taxonomy())
    all_modalities = mo_tax["Modality_Name"].dropna().astype(str).tolist()
    if not st.session_state.get("filter_all_modalities", True):
        selected_modality = st.session_state.get("filter_modality_single")
        if selected_modality not in all_modalities:
            pool_ids = set()
        else:
            selected_cols = (
                mo_tax[mo_tax["Modality_Name"] == selected_modality]["Profile_Column"]
                .dropna()
                .astype(str)
                .tolist()
            )
            valid_cols = [c for c in selected_cols if c in profile_merged.columns]
            if valid_cols:
                mo_mask = _normalise_yn_flags(profile_merged, valid_cols).eq("Y")
                passed_mo = profile_merged.loc[mo_mask.any(axis=1), "Unique_ID"].astype(str)
                pool_ids = pool_ids.intersection(set(passed_mo))
            else:
                pool_ids = set()

    # Company universe filter: all selected = no restriction; empty = no universe.
    all_companies = _ordered_company_ids(master)
    selected_companies = [str(x) for x in st.session_state.get("filter_company_uids", []) if str(x) in all_companies]
    if not selected_companies:
        pool_ids = set()
    elif set(selected_companies) != set(all_companies):
        pool_ids = pool_ids.intersection(set(selected_companies))

    current_sel = st.session_state.selected_company_uid
    if current_sel not in pool_ids and pool_ids:
        fin_pool = financials_latest[financials_latest["Unique_ID"].astype(str).isin(pool_ids)].copy()
        if not fin_pool.empty:
            largest = fin_pool.sort_values("Market_Cap_USD_M", ascending=False).iloc[0]["Unique_ID"]
            st.session_state.selected_company_uid = str(largest)
        else:
            master_pool = master[master["Unique_ID"].astype(str).isin(pool_ids)].copy()
            if not master_pool.empty:
                first = master_pool.sort_values("Company Name").iloc[0]["Unique_ID"]
                st.session_state.selected_company_uid = str(first)

    return pool_ids
