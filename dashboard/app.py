import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from datetime import datetime


# ============================================================
# CONFIG
# ============================================================

API_BASE = "http://127.0.0.1:8000"
PAGE_TITLE = "RIS-Agent | AI Risk Intelligence"

st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>
        .stApp {
            background:
                radial-gradient(
                    circle at 85% 5%,
                    rgba(43, 91, 170, 0.16),
                    transparent 28%
                ),
                radial-gradient(
                    circle at 15% 85%,
                    rgba(0, 210, 255, 0.08),
                    transparent 30%
                ),
                #070b12;
        }

        [data-testid="stHeader"] {
            background: rgba(7, 11, 18, 0.88);
        }

        [data-testid="stSidebar"] {
            background: #090e17;
            border-right: 1px solid rgba(255,255,255,0.07);
        }

        [data-testid="stSidebar"] * {
            color: #dbe4f0;
        }

        .block-container {
            padding-top: 1.8rem;
            padding-bottom: 3rem;
            max-width: 1500px;
        }

        [data-testid="stMetric"] {
            background: rgba(16, 23, 35, 0.82);
            border: 1px solid rgba(255,255,255,0.075);
            border-radius: 16px;
            padding: 18px 20px;
            box-shadow: 0 12px 35px rgba(0,0,0,0.25);
        }

        [data-testid="stMetricLabel"] {
            color: #7f8da3 !important;
            font-size: 0.78rem !important;
            text-transform: uppercase;
            letter-spacing: 0.09em;
        }

        [data-testid="stMetricValue"] {
            color: #f4f8ff !important;
            font-weight: 700 !important;
        }

        .stButton > button {
            width: 100%;
            border-radius: 10px;
            border: 1px solid rgba(255,255,255,0.10);
            background: #111a29;
            color: #e8f0fb;
            min-height: 42px;
            transition: all 0.18s ease;
        }

        .stButton > button:hover {
            border-color: rgba(64, 170, 255, 0.65);
            background: #172338;
            transform: translateY(-1px);
        }

        div[data-baseweb="select"] > div,
        .stTextInput input,
        .stNumberInput input,
        .stTextArea textarea {
            background: #0e1623 !important;
            border-color: rgba(255,255,255,0.10) !important;
            color: #e8f0fb !important;
            border-radius: 10px !important;
        }

        button[data-baseweb="tab"] {
            color: #8190a6;
        }

        button[data-baseweb="tab"][aria-selected="true"] {
            color: #66c7ff;
        }

        [data-testid="stExpander"] {
            background: rgba(13, 20, 32, 0.70);
            border: 1px solid rgba(255,255,255,0.07);
            border-radius: 14px;
        }

        [data-testid="stDataFrame"] {
            border-radius: 12px;
            overflow: hidden;
        }

        .stAlert {
            border-radius: 12px;
        }

        div[role="radiogroup"] label {
            padding: 7px 10px;
            border-radius: 8px;
        }

        div[data-testid="stVerticalBlock"] > div {
            gap: 0.65rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# API HELPERS
# ============================================================

def api_get(path, params=None, timeout=8):

    try:

        response = requests.get(
            f"{API_BASE}{path}",
            params=params,
            timeout=timeout,
        )

        response.raise_for_status()

        return response.json()

    except Exception as exc:

        return {
            "_error": str(exc)
        }


def api_post(path, payload=None, timeout=60):

    try:

        response = requests.post(
            f"{API_BASE}{path}",
            json=payload,
            timeout=timeout,
        )

        response.raise_for_status()

        return response.json()

    except Exception as exc:

        return {
            "_error": str(exc)
        }


def is_error(data):

    return (
        isinstance(data, dict)
        and "_error" in data
    )


def first_list(data, preferred=None):

    if isinstance(data, list):
        return data

    if not isinstance(data, dict):
        return []

    if preferred:

        for key in preferred:

            value = data.get(key)

            if isinstance(value, list):
                return value

    for value in data.values():

        if isinstance(value, list):
            return value

    return []


def safe_float(value, default=0.0):

    try:
        return float(value)

    except Exception:
        return default


def money(value):

    return f"₹{safe_float(value):,.2f}"


def risk_color(level):

    level = str(level).upper()

    if level == "HIGH":
        return "🔴"

    if level == "MEDIUM":
        return "🟠"

    if level == "LOW":
        return "🟢"

    return "⚪"


def action_label(action):

    return {
        "ALLOW": "ALLOW",
        "REVIEW_TRANSACTION": "REVIEW",
        "BLOCK_TRANSACTION": "BLOCK",
    }.get(
        action,
        action or "—",
    )


def clear_data_cache():

    st.cache_data.clear()


def human_details(details):

    if details is None:
        return ""

    if isinstance(details, dict):

        parts = []

        for key, value in details.items():

            if isinstance(value, (dict, list)):
                value = str(value)

            parts.append(
                f"{key}: {value}"
            )

        return " • ".join(parts)

    return str(details)


# ============================================================
# RESPONSE SAFETY HELPERS
# ============================================================

def normalize_investigation(data):

    if not isinstance(data, dict):
        return {}

    nested = data.get(
        "investigation"
    )

    if isinstance(nested, dict):
        return nested

    return data


def get_policy_result(result):

    if not isinstance(result, dict):
        return {}

    policy = result.get(
        "policy_decision"
    )

    if isinstance(policy, dict):
        return policy

    investigation = normalize_investigation(
        result.get(
            "investigation",
            {}
        )
    )

    policy = investigation.get(
        "policy_decision",
        investigation.get(
            "policy",
            {}
        ),
    )

    return (
        policy
        if isinstance(policy, dict)
        else {}
    )


def get_action_result(result):

    if not isinstance(result, dict):
        return {}

    action = result.get(
        "action_result"
    )

    if isinstance(action, dict):
        return action

    investigation = normalize_investigation(
        result.get(
            "investigation",
            {}
        )
    )

    action = investigation.get(
        "action_result",
        investigation.get(
            "action",
            {}
        ),
    )

    return (
        action
        if isinstance(action, dict)
        else {}
    )


def get_case_result(result):

    if not isinstance(result, dict):
        return {}

    case = result.get(
        "case"
    )

    if isinstance(case, dict):
        return case

    investigation = normalize_investigation(
        result.get(
            "investigation",
            {}
        )
    )

    case = investigation.get(
        "case",
        {}
    )

    return (
        case
        if isinstance(case, dict)
        else {}
    )


def get_transaction_result(result):

    if not isinstance(result, dict):
        return {}

    transaction = result.get(
        "transaction"
    )

    if isinstance(transaction, dict):
        return transaction

    return {}


def get_actual_status(action_result, transaction=None):

    if not isinstance(action_result, dict):
        action_result = {}

    if not isinstance(transaction, dict):
        transaction = {}

    return action_result.get(
        "status",
        action_result.get(
            "actual_status",
            transaction.get(
                "status",
                "—",
            ),
        ),
    )


def is_action_verified(action_result):

    if not isinstance(action_result, dict):
        return False

    verified = action_result.get(
        "verified",
        False,
    )

    verification_status = str(
        action_result.get(
            "verification_status",
            "",
        )
    ).upper()

    return (
        verified is True
        or verification_status == "VERIFIED"
    )


# ============================================================
# DISPLAY DATAFRAME SAFETY
# ============================================================

def make_display_safe(df):

    if df is None or df.empty:
        return df

    result = df.copy()

    for column in result.columns:

        if result[column].dtype == "object":

            result[column] = result[column].map(
                lambda value:
                    ""
                    if value is None
                    else str(value)
            )

    return result


# ============================================================
# DATA LOADERS
# ============================================================

@st.cache_data(ttl=4)
def load_transactions():

    data = api_get(
        "/dashboard/transactions"
    )

    if is_error(data):
        return pd.DataFrame()

    rows = first_list(
        data,
        [
            "transactions",
            "data",
            "items",
            "results",
        ],
    )

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    rename_map = {
        "transaction": "transaction_id",
        "risk": "risk_score",
        "riskLevel": "risk_level",
    }

    df = df.rename(
        columns=rename_map
    )

    if "risk_score" in df.columns:

        df["risk_score"] = pd.to_numeric(
            df["risk_score"],
            errors="coerce",
        ).fillna(0)

    if "amount" in df.columns:

        df["amount"] = pd.to_numeric(
            df["amount"],
            errors="coerce",
        ).fillna(0)

    return df


@st.cache_data(ttl=4)
def load_users():

    data = api_get(
        "/users"
    )

    if is_error(data):
        return pd.DataFrame()

    rows = first_list(
        data,
        [
            "users",
            "data",
            "items",
            "results",
        ],
    )

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(rows)


@st.cache_data(ttl=4)
def load_cases():

    data = api_get(
        "/dashboard/cases"
    )

    if is_error(data):
        return pd.DataFrame()

    rows = first_list(
        data,
        [
            "cases",
            "data",
            "items",
            "results",
        ],
    )

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(rows)


@st.cache_data(ttl=4)
def load_audit():

    data = api_get(
        "/dashboard/audit"
    )

    if is_error(data):
        return pd.DataFrame()

    rows = first_list(
        data,
        [
            "audit",
            "audit_logs",
            "logs",
            "data",
            "items",
            "results",
        ],
    )

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(rows)


@st.cache_data(ttl=4)
def load_health():

    return api_get(
        "/health"
    )


@st.cache_data(ttl=4)
def load_model_health():

    return api_get(
        "/model/health"
    )


def get_transaction(transaction_id):

    return api_get(
        f"/transactions/{transaction_id}"
    )


def get_investigation(transaction_id):

    return api_get(
        f"/transactions/{transaction_id}/investigation",
        timeout=15,
    )


def get_case(case_id):

    return api_get(
        f"/cases/{case_id}"
    )


def get_case_for_transaction(transaction_id):

    return api_get(
        f"/transactions/{transaction_id}/case"
    )


# ============================================================
# PLOTLY THEME
# ============================================================

PLOT_BG = "rgba(0,0,0,0)"
PLOT_PAPER = "rgba(0,0,0,0)"
FONT_COLOR = "#dce7f5"
GRID_COLOR = "rgba(255,255,255,0.06)"


def style_fig(fig, height=330):

    fig.update_layout(
        height=height,
        paper_bgcolor=PLOT_PAPER,
        plot_bgcolor=PLOT_BG,
        font=dict(
            color=FONT_COLOR
        ),
        margin=dict(
            l=10,
            r=10,
            t=40,
            b=10,
        ),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(
                color="#aab8ca"
            ),
        ),
    )

    fig.update_xaxes(
        gridcolor=GRID_COLOR,
        zerolinecolor=GRID_COLOR,
    )

    fig.update_yaxes(
        gridcolor=GRID_COLOR,
        zerolinecolor=GRID_COLOR,
    )

    return fig


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title(
        "🛡️ RIS-AGENT"
    )

    st.caption(
        "AI PAYMENT RISK INTELLIGENCE"
    )

    health = load_health()
    model_health = load_model_health()

    backend_ok = not is_error(
        health
    )

    model_ok = not is_error(
        model_health
    )

    if backend_ok:

        st.success(
            "● BACKEND ONLINE"
        )

    else:

        st.error(
            "● BACKEND OFFLINE"
        )

    if model_ok:

        st.success(
            "● MODEL ONLINE"
        )

    else:

        st.warning(
            "● MODEL STATUS UNKNOWN"
        )

    st.divider()

    pages = [
        "Overview",
        "Transactions",
        "Investigations",
        "Cases",
        "Audit Trail",
        "Live Demo",
    ]

    page = st.radio(
        "CONTROL CENTER",
        pages,
    )

    st.divider()

    if st.button(
        "↻ Refresh data"
    ):

        clear_data_cache()
        st.rerun()

    st.caption(
        "Risk intelligence • v1"
    )

    st.caption(
        "ML → RAG → Agent → Policy"
    )


# ============================================================
# LOAD COMMON DATA
# ============================================================

transactions_df = load_transactions()
cases_df = load_cases()
audit_df = load_audit()
users_df = load_users()


if not transactions_df.empty:

    if "risk_level" not in transactions_df.columns:

        if "risk_score" in transactions_df.columns:

            transactions_df[
                "risk_level"
            ] = transactions_df[
                "risk_score"
            ].apply(
                lambda x:
                    "HIGH"
                    if x >= 0.70
                    else "MEDIUM"
                    if x >= 0.30
                    else "LOW"
            )

        else:

            transactions_df[
                "risk_level"
            ] = "UNKNOWN"

    transactions_df[
        "risk_level"
    ] = (
        transactions_df[
            "risk_level"
        ]
        .fillna("UNKNOWN")
        .astype(str)
        .str.upper()
    )


# ============================================================
# HEADER
# ============================================================

header_left, header_right = st.columns(
    [4, 1]
)

with header_left:

    st.title(
        "AI Risk Intelligence Center"
    )

    st.caption(
        "Real-time payment monitoring, "
        "investigation and controlled response."
    )


with header_right:

    st.metric(
        "SYSTEM STATUS",
        "LIVE"
        if backend_ok
        else "OFFLINE",
        "ML + RAG + AGENT",
    )


# ============================================================
# OVERVIEW
# ============================================================

if page == "Overview":

    total = len(
        transactions_df
    )

    high_count = (
        int(
            (
                transactions_df[
                    "risk_level"
                ]
                == "HIGH"
            ).sum()
        )
        if not transactions_df.empty
        else 0
    )

    blocked_count = (
        int(
            (
                transactions_df.get(
                    "status",
                    pd.Series(
                        dtype=str
                    ),
                )
                .astype(str)
                .str.upper()
                == "BLOCKED"
            ).sum()
        )
        if not transactions_df.empty
        else 0
    )

    open_cases = (
        int(
            (
                cases_df.get(
                    "status",
                    pd.Series(
                        dtype=str
                    ),
                )
                .astype(str)
                .str.upper()
                == "OPEN"
            ).sum()
        )
        if not cases_df.empty
        else 0
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "TRANSACTIONS",
        f"{total:,}",
    )

    c2.metric(
        "HIGH RISK",
        f"{high_count:,}",
        "Requires investigation",
    )

    c3.metric(
        "OPEN CASES",
        f"{open_cases:,}",
        "Human attention",
    )

    c4.metric(
        "BLOCKED",
        f"{blocked_count:,}",
        "Controlled actions",
    )

    st.write("")

    st.subheader(
        "Investigation Pipeline"
    )

    st.caption(
        "How RIS-Agent moves from a payment event to a controlled decision."
    )

    pipeline = st.columns(9)

    stages = [
        ("01", "TRANSACTION", "Payment event"),
        ("02", "ML", "Pattern detection"),
        ("03", "RAG", "Risk knowledge"),
        ("04", "AGENT", "Investigation"),
        ("05", "POLICY", "Safety gate"),
    ]

    for idx, (
        number,
        title,
        desc,
    ) in enumerate(stages):

        with pipeline[idx * 2]:

            st.metric(
                number,
                title,
            )

            st.caption(
                desc
            )

        if idx < len(stages) - 1:

            with pipeline[
                idx * 2 + 1
            ]:

                st.markdown(
                    "### →"
                )

    st.write("")

    left, right = st.columns(
        [1.15, 0.85]
    )

    with left:

        st.subheader(
            "Risk Distribution"
        )

        if not transactions_df.empty:

            dist = (
                transactions_df[
                    "risk_level"
                ]
                .value_counts()
                .rename_axis(
                    "risk_level"
                )
                .reset_index(
                    name="count"
                )
            )

            fig = px.pie(
                dist,
                names="risk_level",
                values="count",
                hole=0.64,
            )

            fig.update_traces(
                textposition="inside",
                textinfo="percent+label",
                hovertemplate=(
                    "%{label}: "
                    "%{value}"
                    "<extra></extra>"
                ),
            )

            style_fig(
                fig,
                350,
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

        else:

            st.info(
                "No transaction data available."
            )

    with right:

        st.subheader(
            "AI Activity"
        )

        st.caption(
            "Latest decisions recorded by the system."
        )

        if not audit_df.empty:

            activity = audit_df.copy()

            if "created_at" in activity.columns:

                activity = activity.sort_values(
                    "created_at",
                    ascending=False,
                )

            display_cols = [
                c
                for c in [
                    "created_at",
                    "actor",
                    "action",
                    "case_id",
                ]
                if c in activity.columns
            ]

            display_activity = (
                activity[
                    display_cols
                ].head(8)
                if display_cols
                else activity.head(8)
            )

            st.dataframe(
                make_display_safe(
                    display_activity
                ),
                use_container_width=True,
                hide_index=True,
            )

        else:

            st.info(
                "No audit activity yet."
            )

    st.write("")

    left, right = st.columns(
        [1.2, 0.8]
    )

    with left:

        st.subheader(
            "Risk Network"
        )

        if not transactions_df.empty:

            graph_df = (
                transactions_df
                .head(24)
                .copy()
            )

            if "transaction_id" in graph_df.columns:

                if "user_id" not in graph_df.columns:

                    graph_df[
                        "user_id"
                    ] = "unknown"

                users = list(
                    pd.Series(
                        graph_df[
                            "user_id"
                        ].astype(str)
                    ).unique()
                )

                fig = go.Figure()

                user_positions = {}
                txn_positions = {}

                for i, user in enumerate(users):

                    y = (
                        1
                        - (
                            i + 1
                        )
                        / (
                            len(users) + 1
                        )
                    )

                    user_positions[
                        user
                    ] = (
                        0.12,
                        y,
                    )

                for i, row in (
                    graph_df
                    .reset_index(
                        drop=True
                    )
                    .iterrows()
                ):

                    y = (
                        1
                        - (
                            i + 1
                        )
                        / (
                            len(graph_df) + 1
                        )
                    )

                    txn_positions[
                        str(
                            row[
                                "transaction_id"
                            ]
                        )
                    ] = (
                        0.80,
                        y,
                    )

                for _, row in graph_df.iterrows():

                    user = str(
                        row[
                            "user_id"
                        ]
                    )

                    txn = str(
                        row[
                            "transaction_id"
                        ]
                    )

                    ux, uy = user_positions.get(
                        user,
                        (0.12, 0.5),
                    )

                    tx, ty = txn_positions.get(
                        txn,
                        (0.80, 0.5),
                    )

                    fig.add_trace(
                        go.Scatter(
                            x=[ux, tx],
                            y=[uy, ty],
                            mode="lines",
                            line=dict(
                                width=1,
                                color="rgba(90,160,220,0.18)",
                            ),
                            hoverinfo="skip",
                            showlegend=False,
                        )
                    )

                fig.add_trace(
                    go.Scatter(
                        x=[
                            p[0]
                            for p in user_positions.values()
                        ],
                        y=[
                            p[1]
                            for p in user_positions.values()
                        ],
                        mode="markers+text",
                        text=[
                            f"U-{u}"
                            for u in user_positions.keys()
                        ],
                        textposition="middle left",
                        marker=dict(
                            size=18,
                            color="#55b7ff",
                            line=dict(
                                width=1,
                                color="#cceeff",
                            ),
                        ),
                        name="Users",
                    )
                )

                tx_x = []
                tx_y = []
                tx_text = []
                tx_sizes = []
                tx_colors = []

                for _, row in graph_df.iterrows():

                    txn = str(
                        row[
                            "transaction_id"
                        ]
                    )

                    x, y = txn_positions[
                        txn
                    ]

                    tx_x.append(x)
                    tx_y.append(y)

                    tx_text.append(
                        f"{txn}<br>"
                        f"Risk: {row.get('risk_level', 'UNKNOWN')}<br>"
                        f"Amount: {money(row.get('amount', 0))}"
                    )

                    level = str(
                        row.get(
                            "risk_level",
                            ""
                        )
                    ).upper()

                    tx_sizes.append(
                        19
                        if level == "HIGH"
                        else 16
                        if level == "MEDIUM"
                        else 13
                    )

                    tx_colors.append(
                        "#ff4d5a"
                        if level == "HIGH"
                        else "#f3ad45"
                        if level == "MEDIUM"
                        else "#42d392"
                    )

                fig.add_trace(
                    go.Scatter(
                        x=tx_x,
                        y=tx_y,
                        mode="markers",
                        marker=dict(
                            size=tx_sizes,
                            color=tx_colors,
                            line=dict(
                                width=1,
                                color="#ffffff",
                            ),
                        ),
                        text=tx_text,
                        hovertemplate=(
                            "%{text}"
                            "<extra></extra>"
                        ),
                        name="Transactions",
                    )
                )

                fig.update_layout(
                    height=470,
                    showlegend=True,
                    xaxis=dict(
                        visible=False,
                        range=[0, 1],
                    ),
                    yaxis=dict(
                        visible=False,
                        range=[0, 1],
                    ),
                    paper_bgcolor=PLOT_PAPER,
                    plot_bgcolor=PLOT_BG,
                    font=dict(
                        color=FONT_COLOR
                    ),
                    margin=dict(
                        l=10,
                        r=10,
                        t=20,
                        b=10,
                    ),
                    legend=dict(
                        orientation="h",
                        y=1.05,
                        x=0,
                    ),
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True,
                )

            else:

                st.info(
                    "Transaction IDs are not available for the graph."
                )

        else:

            st.info(
                "No transaction data available."
            )

    with right:

        st.subheader(
            "Recent Risk Events"
        )

        if not transactions_df.empty:

            event_cols = [
                c
                for c in [
                    "transaction_id",
                    "amount",
                    "risk_score",
                    "risk_level",
                    "status",
                    "payment_method",
                ]
                if c in transactions_df.columns
            ]

            events = (
                transactions_df
                .sort_values(
                    "risk_score",
                    ascending=False,
                )[event_cols]
                .head(8)
                .copy()
            )

            st.dataframe(
                make_display_safe(
                    events
                ),
                use_container_width=True,
                hide_index=True,
            )

        else:

            st.info(
                "No risk events available."
            )


# ============================================================
# TRANSACTIONS
# ============================================================

elif page == "Transactions":

    st.subheader(
        "Transaction Monitor"
    )

    st.caption(
        "Search, inspect and apply controlled actions to payment events."
    )

    if transactions_df.empty:

        st.warning(
            "No transactions returned by the backend."
        )

        st.stop()

    search = st.text_input(
        "Search transaction",
        placeholder="TXN00504",
    )

    f1, f2, f3 = st.columns(3)

    with f1:

        risk_options = [
            "ALL"
        ] + sorted(
            transactions_df[
                "risk_level"
            ]
            .dropna()
            .unique()
            .tolist()
        )

        risk_filter = st.selectbox(
            "Risk level",
            risk_options,
        )

    with f2:

        status_options = [
            "ALL"
        ]

        if "status" in transactions_df.columns:

            status_options += sorted(
                transactions_df[
                    "status"
                ]
                .dropna()
                .astype(str)
                .str.upper()
                .unique()
                .tolist()
            )

        status_filter = st.selectbox(
            "Status",
            status_options,
        )

    with f3:

        method_options = [
            "ALL"
        ]

        if "payment_method" in transactions_df.columns:

            method_options += sorted(
                transactions_df[
                    "payment_method"
                ]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

        method_filter = st.selectbox(
            "Payment method",
            method_options,
        )

    filtered = transactions_df.copy()

    if search:

        mask = (
            filtered
            .astype(str)
            .apply(
                lambda col:
                    col.str.contains(
                        search,
                        case=False,
                        na=False,
                    )
            )
            .any(axis=1)
        )

        filtered = filtered[
            mask
        ]

    if risk_filter != "ALL":

        filtered = filtered[
            filtered[
                "risk_level"
            ]
            == risk_filter
        ]

    if (
        status_filter != "ALL"
        and "status" in filtered.columns
    ):

        filtered = filtered[
            filtered[
                "status"
            ]
            .astype(str)
            .str.upper()
            == status_filter
        ]

    if (
        method_filter != "ALL"
        and "payment_method"
        in filtered.columns
    ):

        filtered = filtered[
            filtered[
                "payment_method"
            ]
            .astype(str)
            == method_filter
        ]

    table_cols = [
        c
        for c in [
            "transaction_id",
            "amount",
            "currency",
            "payment_method",
            "status",
            "risk_score",
            "risk_level",
            "country",
            "failed_attempts",
            "user_txn_count_1h",
        ]
        if c in filtered.columns
    ]

    st.dataframe(
        make_display_safe(
            filtered[
                table_cols
            ].head(100)
        ),
        use_container_width=True,
        hide_index=True,
    )

    if (
        "transaction_id"
        not in filtered.columns
        or filtered.empty
    ):

        st.info(
            "No matching transactions."
        )

        st.stop()

    selected_id = st.selectbox(
        "Inspect transaction",
        filtered[
            "transaction_id"
        ]
        .astype(str)
        .tolist(),
    )

    transaction = get_transaction(
        selected_id
    )

    if is_error(transaction):

        st.error(
            transaction["_error"]
        )

        st.stop()

    tx = transaction.get(
        "transaction",
        transaction,
    )

    if not isinstance(tx, dict):
        tx = {}

    risk = transaction.get(
        "risk_assessment",
        transaction.get(
            "risk",
            {},
        ),
    )

    if not isinstance(risk, dict):
        risk = {}

    st.divider()

    left, center, right = st.columns(
        [1.0, 1.2, 1.0]
    )

    with left:

        st.subheader(
            "Transaction"
        )

        st.metric(
            "AMOUNT",
            money(
                tx.get(
                    "amount",
                    0,
                )
            ),
        )

        st.write(
            f"**ID:** "
            f"{tx.get('transaction_id', selected_id)}"
        )

        st.write(
            f"**Method:** "
            f"{tx.get('payment_method', '—')}"
        )

        st.write(
            f"**Status:** "
            f"{tx.get('status', '—')}"
        )

        st.write(
            f"**Country:** "
            f"{tx.get('country', '—')}"
        )

        st.write(
            f"**User:** "
            f"{tx.get('user_id', '—')}"
        )

    with center:

        st.subheader(
            "Risk Score"
        )

        score = safe_float(
            risk.get(
                "risk_score",
                tx.get(
                    "risk_score",
                    0,
                ),
            )
        )

        level = risk.get(
            "risk_level",
            tx.get(
                "risk_level",
                "UNKNOWN",
            ),
        )

        gauge = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=score * 100,
                number={
                    "suffix": "%",
                    "font": {
                        "size": 38,
                        "color": "#f3f7fc",
                    },
                },
                gauge={
                    "axis": {
                        "range": [
                            0,
                            100,
                        ],
                        "tickcolor": "#66758b",
                    },
                    "bar": {
                        "color": "#ff4d5a"
                    },
                    "bgcolor": "#111a28",
                    "borderwidth": 0,
                    "steps": [
                        {
                            "range": [
                                0,
                                30,
                            ],
                            "color": "rgba(66,211,146,0.18)",
                        },
                        {
                            "range": [
                                30,
                                70,
                            ],
                            "color": "rgba(243,173,69,0.18)",
                        },
                        {
                            "range": [
                                70,
                                100,
                            ],
                            "color": "rgba(255,77,90,0.18)",
                        },
                    ],
                },
            )
        )

        style_fig(
            gauge,
            300,
        )

        st.plotly_chart(
            gauge,
            use_container_width=True,
        )

        st.metric(
            "RISK LEVEL",
            f"{risk_color(level)} "
            f"{str(level).upper()}",
        )

    with right:

        st.subheader(
            "Risk Signals"
        )

        signal_items = [
            (
                "Failed attempts",
                tx.get(
                    "failed_attempts",
                    0,
                ),
            ),
            (
                "1h velocity",
                tx.get(
                    "user_txn_count_1h",
                    0,
                ),
            ),
            (
                "Account age",
                tx.get(
                    "account_age_days",
                    "—",
                ),
            ),
            (
                "Hour",
                tx.get(
                    "hour",
                    "—",
                ),
            ),
            (
                "Model",
                risk.get(
                    "model_version",
                    tx.get(
                        "model_version",
                        "—",
                    ),
                ),
            ),
        ]

        for label, value in signal_items:

            st.write(
                f"**{label}:** {value}"
            )

        st.write("")

        st.subheader(
            "Controlled Action"
        )

        action_options = [
            "ALLOW",
            "REVIEW_TRANSACTION",
            "BLOCK_TRANSACTION",
        ]

        action = st.selectbox(
            "Select action",
            action_options,
            format_func=action_label,
            key=f"action_{selected_id}",
        )

        if st.button(
            "Execute action",
            key=f"execute_{selected_id}",
        ):

            result = api_post(
                f"/transactions/{selected_id}/action",
                {
                    "action": action
                },
            )

            if is_error(result):

                st.error(
                    result["_error"]
                )

            else:

                if is_action_verified(
                    result
                ):

                    st.success(
                        f"{action_label(action)} "
                        "action executed and verified."
                    )

                else:

                    st.warning(
                        f"{action_label(action)} "
                        "action executed but verification failed."
                    )

                clear_data_cache()
                st.rerun()


# ============================================================
# INVESTIGATIONS
# ============================================================

elif page == "Investigations":

    st.subheader(
        "Investigation Workspace"
    )

    st.caption(
        "Review the real ML → RAG → Agent → Policy → Action evidence chain."
    )

    if transactions_df.empty:

        st.warning(
            "No transactions available."
        )

        st.stop()

    if "risk_score" in transactions_df.columns:

        investigation_df = (
            transactions_df
            .sort_values(
                "risk_score",
                ascending=False,
            )
        )

    else:

        investigation_df = transactions_df

    if "transaction_id" not in investigation_df.columns:

        st.error(
            "Transaction IDs are not available."
        )

        st.stop()

    ids = (
        investigation_df[
            "transaction_id"
        ]
        .astype(str)
        .tolist()
    )

    if not ids:

        st.info(
            "No transactions available for investigation."
        )

        st.stop()

    selected_id = st.selectbox(
        "Select transaction",
        ids,
    )

    investigation_result = get_investigation(
        selected_id
    )

    if is_error(investigation_result):

        st.error(
            "Investigation could not be loaded: "
            + investigation_result["_error"]
        )

        st.stop()

    tx = get_transaction_result(
        investigation_result
    )

    investigation = normalize_investigation(
        investigation_result
    )

    policy = get_policy_result(
        investigation_result
    )

    action_result = get_action_result(
        investigation_result
    )

    case = get_case_result(
        investigation_result
    )

    if not tx:

        tx_data = get_transaction(
            selected_id
        )

        if not is_error(tx_data):

            tx = tx_data.get(
                "transaction",
                tx_data,
            )

    if not isinstance(tx, dict):
        tx = {}

    score = safe_float(
        investigation.get(
            "risk_score",
            tx.get(
                "risk_score",
                0,
            ),
        )
    )

    level = investigation.get(
        "risk_level",
        tx.get(
            "risk_level",
            "UNKNOWN",
        ),
    )

    recommendation = investigation.get(
        "recommendation",
        investigation.get(
            "recommended_action",
            "—",
        ),
    )

    st.divider()

    a, b, c, d = st.columns(4)

    a.metric(
        "TRANSACTION",
        selected_id,
    )

    b.metric(
        "RISK SCORE",
        f"{score:.1%}",
    )

    c.metric(
        "RISK LEVEL",
        f"{risk_color(level)} "
        f"{str(level).upper()}",
    )

    d.metric(
        "AGENT DECISION",
        action_label(
            recommendation
        ),
    )

    st.write("")

    st.subheader(
        "Investigation Pipeline"
    )

    stages = [
        (
            "TRANSACTION",
            "Payment event captured",
        ),
        (
            "ML",
            "Pattern detector produces risk score",
        ),
        (
            "RAG",
            "Relevant risk rules retrieved",
        ),
        (
            "AGENT",
            "Investigator evaluates evidence",
        ),
        (
            "POLICY",
            "Deterministic safety gate",
        ),
        (
            "ACTION",
            "Approved response verified",
        ),
    ]

    stage_cols = st.columns(
        len(stages)
    )

    for col, (
        title,
        desc,
    ) in zip(
        stage_cols,
        stages,
    ):

        with col:

            st.metric(
                title,
                "✓",
            )

            st.caption(
                desc
            )

    st.divider()

    left, right = st.columns(
        [1.05, 0.95]
    )

    with left:

        st.subheader(
            "Transaction Context"
        )

        context_cols = [
            c
            for c in [
                "transaction_id",
                "user_id",
                "amount",
                "currency",
                "payment_method",
                "merchant_id",
                "status",
                "country",
                "device_id",
                "ip_id",
                "failed_attempts",
                "account_age_days",
                "hour",
                "user_txn_count_1h",
            ]
            if c in tx
        ]

        context_rows = [
            {
                "Field": c.replace(
                    "_",
                    " ",
                ).title(),
                "Value": (
                    money(tx.get(c))
                    if c == "amount"
                    else str(tx.get(c))
                ),
            }
            for c in context_cols
        ]

        if context_rows:

            st.dataframe(
                make_display_safe(
                    pd.DataFrame(
                        context_rows
                    )
                ),
                use_container_width=True,
                hide_index=True,
            )

    with right:

        st.subheader(
            "Agent Decision"
        )

        st.metric(
            "RECOMMENDED ACTION",
            action_label(
                recommendation
            ),
        )

        st.write(
            f"**Risk score:** {score:.2%}"
        )

        st.write(
            f"**Risk level:** "
            f"{risk_color(level)} {str(level).upper()}"
        )

        st.write(
            f"**Model:** "
            f"{investigation.get('model_version', '—')}"
        )

        st.write(
            f"**Transaction context available:** "
            f"{'YES' if investigation.get('transaction_context_available') else 'NO'}"
        )

        st.caption(
            "This recommendation comes directly from the "
            "AI investigation service. The dashboard does "
            "not independently calculate the decision."
        )

    st.divider()

    st.subheader(
        "Detected Risk Evidence"
    )

    evidence = investigation.get(
        "evidence",
        investigation.get(
            "risk_evidence",
            [],
        ),
    )

    if evidence:

        if isinstance(
            evidence,
            list,
        ):

            evidence_rows = []

            for item in evidence:

                if isinstance(
                    item,
                    dict,
                ):

                    evidence_rows.append(
                        {
                            "Rule": item.get(
                                "id",
                                item.get(
                                    "rule_code",
                                    "—",
                                ),
                            ),
                            "Title": item.get(
                                "title",
                                "Risk signal",
                            ),
                            "Category": item.get(
                                "category",
                                "—",
                            ),
                            "Severity": item.get(
                                "severity",
                                "—",
                            ),
                            "Recommended action": item.get(
                                "recommended_action",
                                "—",
                            ),
                        }
                    )

            if evidence_rows:

                st.dataframe(
                    make_display_safe(
                        pd.DataFrame(
                            evidence_rows
                        )
                    ),
                    use_container_width=True,
                    hide_index=True,
                )

                for item in evidence:

                    if isinstance(
                        item,
                        dict,
                    ):

                        title = item.get(
                            "title",
                            item.get(
                                "id",
                                "Risk signal",
                            ),
                        )

                        with st.expander(
                            str(title)
                        ):

                            st.write(
                                item.get(
                                    "content",
                                    item.get(
                                        "description",
                                        "No detailed content returned.",
                                    ),
                                )
                            )

        else:

            st.write(
                evidence
            )

    else:

        st.success(
            "No risk evidence matched this transaction."
        )

    st.divider()

    st.subheader(
        "RAG Retrieved Knowledge"
    )

    retrieved_rules = investigation.get(
        "retrieved_rules",
        [],
    )

    if retrieved_rules:

        if isinstance(
            retrieved_rules,
            list,
        ):

            rag_rows = []

            for rule in retrieved_rules:

                if isinstance(
                    rule,
                    dict,
                ):

                    distance = rule.get(
                        "similarity_distance"
                    )

                    if distance is not None:

                        try:
                            distance = round(
                                float(distance),
                                4,
                            )
                        except Exception:
                            pass

                    rag_rows.append(
                        {
                            "Rule": rule.get(
                                "id",
                                "—",
                            ),
                            "Title": rule.get(
                                "title",
                                "—",
                            ),
                            "Severity": rule.get(
                                "severity",
                                "—",
                            ),
                            "Similarity distance": distance
                            if distance is not None
                            else "—",
                        }
                    )

            if rag_rows:

                st.dataframe(
                    make_display_safe(
                        pd.DataFrame(
                            rag_rows
                        )
                    ),
                    use_container_width=True,
                    hide_index=True,
                )

                st.caption(
                    "Lower similarity distance generally means "
                    "the retrieved rule was semantically closer "
                    "to the investigation query."
                )

        else:

            st.write(
                retrieved_rules
            )

    else:

        st.info(
            "No retrieved RAG rules were returned."
        )

    st.divider()

    left, right = st.columns(
        [1, 1]
    )

    with left:

        st.subheader(
            "Policy Decision"
        )

        policy_result = policy.get(
            "policy_result",
            "—",
        )

        if str(policy_result).upper() == "APPROVED":

            st.success(
                f"✓ POLICY {policy_result}"
            )

        elif str(policy_result).upper() == "REJECTED":

            st.error(
                f"✗ POLICY {policy_result}"
            )

        else:

            st.info(
                f"POLICY {policy_result}"
            )

        st.write(
            f"**Reason:** "
            f"{policy.get('reason', '—')}"
        )

        st.write(
            f"**Policy version:** "
            f"{policy.get('policy_version', '—')}"
        )

    with right:

        st.subheader(
            "Controlled Response"
        )

        if action_result:

            c1, c2 = st.columns(2)

            with c1:

                st.metric(
                    "ACTION",
                    action_label(
                        action_result.get(
                            "action",
                            "—",
                        )
                    ),
                )

            with c2:

                st.metric(
                    "RESULT",
                    get_actual_status(
                        action_result,
                        tx,
                    ),
                )

            if is_action_verified(
                action_result
            ):

                st.success(
                    "✓ ACTION VERIFIED"
                )

            else:

                st.error(
                    "✗ ACTION VERIFICATION FAILED"
                )

            st.caption(
                action_result.get(
                    "message",
                    action_result.get(
                        "verification_status",
                        "—",
                    ),
                )
            )

        else:

            st.warning(
                "No action result returned."
            )

    if case:

        st.divider()

        st.subheader(
            "Investigation Case"
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "CASE",
            f"#{case.get('id', '—')}",
        )

        c2.metric(
            "PRIORITY",
            case.get(
                "priority",
                "—",
            ),
        )

        c3.metric(
            "STATUS",
            case.get(
                "status",
                "—",
            ),
        )

        st.info(
            case.get(
                "investigation_summary",
                "No investigation summary available.",
            )
        )

    st.divider()

    st.subheader(
        "Investigation Activity"
    )

    if (
        not audit_df.empty
        and "case_id"
        in audit_df.columns
    ):

        case_id = case.get(
            "id"
        ) if isinstance(
            case,
            dict,
        ) else None

        if case_id is not None:

            case_audit = audit_df[
                audit_df[
                    "case_id"
                ].astype(str)
                == str(case_id)
            ].copy()

        else:

            case_audit = pd.DataFrame()

        if not case_audit.empty:

            cols = [
                c
                for c in [
                    "created_at",
                    "actor",
                    "action",
                    "details",
                ]
                if c in case_audit.columns
            ]

            if "details" in case_audit.columns:

                case_audit[
                    "details"
                ] = case_audit[
                    "details"
                ].apply(
                    human_details
                )

            st.dataframe(
                make_display_safe(
                    case_audit[
                        cols
                    ]
                ),
                use_container_width=True,
                hide_index=True,
            )

        else:

            st.info(
                "No investigation audit events found for this case."
            )

    else:

        st.info(
            "No audit data available."
        )

    with st.expander(
        "🔍 View Complete Investigation JSON"
    ):

        st.json(
            investigation_result
        )


# ============================================================
# CASES
# ============================================================

elif page == "Cases":

    st.subheader(
        "Case Management"
    )

    st.caption(
        "High-risk activity requiring review or escalation."
    )

    if cases_df.empty:

        st.info(
            "No cases have been created yet."
        )

        st.stop()

    display = cases_df.copy()

    if "created_at" in display.columns:

        display = display.sort_values(
            "created_at",
            ascending=False,
        )

    display_cols = [
        c
        for c in [
            "id",
            "transaction_id",
            "user_id",
            "status",
            "priority",
            "assigned_to",
            "investigation_summary",
            "created_at",
        ]
        if c in display.columns
    ]

    st.dataframe(
        make_display_safe(
            display[
                display_cols
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    case_ids = (
        display[
            "id"
        ].tolist()
        if "id" in display.columns
        else []
    )

    if case_ids:

        selected_case = st.selectbox(
            "Open case",
            case_ids,
        )

        case = get_case(
            int(
                selected_case
            )
        )

        if is_error(case):

            st.error(
                case["_error"]
            )

            st.stop()

        left, right = st.columns(
            [1.2, 0.8]
        )

        with left:

            st.subheader(
                f"Case #{case.get('id', selected_case)}"
            )

            st.write(
                f"**Transaction:** "
                f"{case.get('transaction_id', '—')}"
            )

            st.write(
                f"**Status:** "
                f"{case.get('status', '—')}"
            )

            st.write(
                f"**Priority:** "
                f"{case.get('priority', '—')}"
            )

            st.write(
                f"**Assigned to:** "
                f"{case.get('assigned_to', 'Unassigned')}"
            )

            st.write("")

            st.write(
                "**Investigation summary**"
            )

            st.info(
                case.get(
                    "investigation_summary",
                    "No summary available.",
                )
            )

        with right:

            st.subheader(
                "Case Controls"
            )

            if (
                str(
                    case.get(
                        "status",
                        "",
                    )
                ).upper()
                == "OPEN"
            ):

                if st.button(
                    "Resolve case",
                    key=f"resolve_{selected_case}",
                ):

                    result = api_post(
                        f"/cases/{int(selected_case)}/resolve"
                    )

                    if is_error(result):

                        st.error(
                            result["_error"]
                        )

                    else:

                        st.success(
                            "Case resolved."
                        )

                        clear_data_cache()
                        st.rerun()

            else:

                st.success(
                    "Case is resolved."
                )


# ============================================================
# AUDIT TRAIL
# ============================================================

elif page == "Audit Trail":

    st.subheader(
        "Audit Trail"
    )

    st.caption(
        "Every investigation, policy decision, action and verification is recorded."
    )

    if audit_df.empty:

        st.info(
            "No audit events available."
        )

        st.stop()

    audit_display = (
        audit_df.copy()
    )

    if "details" in audit_display.columns:

        audit_display[
            "details"
        ] = (
            audit_display[
                "details"
            ]
            .apply(
                human_details
            )
        )

    if "created_at" in audit_display.columns:

        audit_display = audit_display.sort_values(
            "created_at",
            ascending=False,
        )

    cols = [
        c
        for c in [
            "created_at",
            "case_id",
            "actor",
            "action",
            "details",
        ]
        if c in audit_display.columns
    ]

    st.dataframe(
        make_display_safe(
            audit_display[
                cols
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.subheader(
        "Audit Summary"
    )

    if "action" in audit_display.columns:

        summary = (
            audit_display[
                "action"
            ]
            .value_counts()
            .rename_axis(
                "action"
            )
            .reset_index(
                name="events"
            )
        )

        fig = px.bar(
            summary,
            x="action",
            y="events",
        )

        style_fig(
            fig,
            320,
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )


# ============================================================
# LIVE DEMO
# ============================================================

elif page == "Live Demo":

    st.subheader(
        "🎬 Live Investigation Mode"
    )

    st.caption(
        "Create a controlled payment event and watch the real backend run "
        "ML → RAG → Agent → Policy → Action."
    )

    st.warning(
        "This creates a real transaction in your local RIS-Agent database. "
        "Use it for the buildathon demo."
    )

    # --------------------------------------------------------
    # USER SELECTION
    # --------------------------------------------------------

    if users_df.empty:

        st.error(
            "No users are available. "
            "Create a user through POST /users first."
        )

        st.stop()

    if "id" not in users_df.columns:

        st.error(
            "User data returned by the backend does not contain user IDs."
        )

        st.stop()

    user_options = []

    for _, row in users_df.iterrows():

        try:

            user_options.append(
                int(row["id"])
            )

        except Exception:

            continue

    if not user_options:

        st.error(
            "No valid users were returned by the backend."
        )

        st.stop()

    user_lookup = {}

    for _, row in users_df.iterrows():

        try:

            user_id = int(
                row["id"]
            )

        except Exception:

            continue

        user_lookup[
            user_id
        ] = {
            "name": row.get(
                "name",
                "Unknown",
            ),
            "email": row.get(
                "email",
                "—",
            ),
        }

    with st.form(
        "live_demo_form"
    ):

        st.markdown(
            "### Payment Event"
        )

        selected_user_id = st.selectbox(
            "User",
            user_options,
            format_func=lambda user_id:
                (
                    f"User {user_id} — "
                    f"{user_lookup.get(user_id, {}).get('name', 'Unknown')}"
                ),
        )

        selected_user = user_lookup.get(
            selected_user_id,
            {},
        )

        st.caption(
            f"Account: "
            f"{selected_user.get('email', '—')}"
        )

        c1, c2, c3 = st.columns(3)

        with c1:

            amount = st.number_input(
                "Amount (INR)",
                min_value=1.0,
                value=15000.0,
                step=500.0,
            )

            payment_method = st.selectbox(
                "Payment method",
                [
                    "UPI",
                    "CARD",
                    "NETBANKING",
                    "WALLET",
                ],
            )

        with c2:

            failed_attempts = st.number_input(
                "Failed attempts",
                min_value=0,
                max_value=20,
                value=5,
                step=1,
            )

            account_age_days = st.number_input(
                "Account age (days)",
                min_value=0,
                max_value=5000,
                value=5,
                step=1,
            )

        with c3:

            velocity = st.number_input(
                "Transactions in 1 hour",
                min_value=0,
                max_value=100,
                value=12,
                step=1,
            )

            country = st.selectbox(
                "Country",
                [
                    "IN",
                    "US",
                    "SG",
                    "AE",
                    "GB",
                ],
            )

        submitted = st.form_submit_button(
            "▶ START LIVE INVESTIGATION",
            use_container_width=True,
        )

    # --------------------------------------------------------
    # EXECUTE PIPELINE
    # --------------------------------------------------------

    if submitted:

        timestamp = datetime.now()

        payload = {
            "user_id": int(
                selected_user_id
            ),
            "amount": float(
                amount
            ),
            "currency": "INR",
            "payment_method": payment_method,
            "merchant_id": "MERCHANT_DEMO",
            "country": country,
            "device_id": "DEVICE_DEMO",
            "ip_id": "IP_DEMO",
            "failed_attempts": int(
                failed_attempts
            ),
            "account_age_days": int(
                account_age_days
            ),
            "hour": timestamp.hour,
            "user_txn_count_1h": int(
                velocity
            ),
        }

        with st.spinner(
            "RIS-Agent is investigating the transaction..."
        ):

            result = api_post(
                "/transactions",
                payload,
                timeout=60,
            )

        if is_error(result):

            st.error(
                "Live investigation failed: "
                + result["_error"]
            )

        else:

            # ------------------------------------------------
            # BACKEND RESPONSE
            # ------------------------------------------------

            tx_result = get_transaction_result(
                result
            )

            if not isinstance(
                tx_result,
                dict,
            ):

                tx_result = {}

            risk_result = result.get(
                "risk_assessment",
                {}
            )

            if not isinstance(
                risk_result,
                dict,
            ):

                risk_result = {}

            investigation = normalize_investigation(
                result.get(
                    "investigation",
                    {}
                )
            )

            policy = get_policy_result(
                result
            )

            action_result = get_action_result(
                result
            )

            case = get_case_result(
                result
            )

            # ------------------------------------------------
            # FALLBACK RISK INFORMATION
            # ------------------------------------------------

            if not risk_result:

                risk_result = {
                    "risk_score":
                        investigation.get(
                            "risk_score",
                            0,
                        ),
                    "risk_level":
                        investigation.get(
                            "risk_level",
                            "UNKNOWN",
                        ),
                    "model_version":
                        investigation.get(
                            "model_version",
                            "—",
                        ),
                }

            actual_transaction_id = (
                tx_result.get(
                    "transaction_id",
                    "UNKNOWN",
                )
            )

            st.success(
                "Investigation completed for "
                f"{actual_transaction_id}"
            )

            # ------------------------------------------------
            # TOP METRICS
            # ------------------------------------------------

            st.divider()

            a, b, c, d = st.columns(4)

            a.metric(
                "TRANSACTION",
                actual_transaction_id,
            )

            score = safe_float(
                risk_result.get(
                    "risk_score",
                    investigation.get(
                        "risk_score",
                        0,
                    ),
                )
            )

            b.metric(
                "RISK SCORE",
                f"{score:.1%}",
            )

            risk_level = risk_result.get(
                "risk_level",
                investigation.get(
                    "risk_level",
                    "UNKNOWN",
                ),
            )

            c.metric(
                "RISK LEVEL",
                (
                    f"{risk_color(risk_level)} "
                    f"{risk_level}"
                ),
            )

            recommendation = investigation.get(
                "recommendation",
                investigation.get(
                    "recommended_action",
                    "—",
                ),
            )

            d.metric(
                "AGENT DECISION",
                action_label(
                    recommendation
                ),
            )

            # ------------------------------------------------
            # PIPELINE
            # ------------------------------------------------

            st.write("")

            st.subheader(
                "Investigation Flow"
            )

            flow = st.columns(6)

            flow_labels = [
                (
                    "1",
                    "Transaction",
                    "Captured",
                ),
                (
                    "2",
                    "ML",
                    "Risk scored",
                ),
                (
                    "3",
                    "RAG",
                    "Evidence retrieved",
                ),
                (
                    "4",
                    "Agent",
                    "Investigated",
                ),
                (
                    "5",
                    "Policy",
                    "Decision gated",
                ),
                (
                    "6",
                    "Action",
                    "Executed",
                ),
            ]

            for col, (
                number,
                title,
                desc,
            ) in zip(
                flow,
                flow_labels,
            ):

                with col:

                    st.metric(
                        number,
                        title,
                    )

                    st.caption(
                        desc
                    )

            # ------------------------------------------------
            # AGENT + POLICY
            # ------------------------------------------------

            st.divider()

            left, right = st.columns(
                2
            )

            with left:

                st.subheader(
                    "Agent Findings"
                )

                evidence = investigation.get(
                    "evidence",
                    investigation.get(
                        "risk_evidence",
                        [],
                    ),
                )

                if evidence:

                    if isinstance(
                        evidence,
                        list,
                    ):

                        for item in evidence:

                            if isinstance(
                                item,
                                dict,
                            ):

                                title = item.get(
                                    "title",
                                    item.get(
                                        "rule_code",
                                        item.get(
                                            "id",
                                            "Risk signal",
                                        ),
                                    ),
                                )

                                description = item.get(
                                    "description",
                                    item.get(
                                        "content",
                                        "",
                                    ),
                                )

                                with st.expander(
                                    str(title)
                                ):

                                    st.write(
                                        description
                                    )

                                    severity = item.get(
                                        "severity"
                                    )

                                    if severity:

                                        st.caption(
                                            f"Severity: {severity}"
                                        )

                            else:

                                st.write(
                                    f"• {item}"
                                )

                    else:

                        st.write(
                            evidence
                        )

                else:

                    st.info(
                        "The backend did not return a detailed evidence list."
                    )

                # ------------------------------------------------
                # RAG RULES
                # ------------------------------------------------

                retrieved_rules = investigation.get(
                    "retrieved_rules",
                    [],
                )

                if retrieved_rules:

                    st.write("")

                    with st.expander(
                        "RAG Retrieved Candidates"
                    ):

                        if isinstance(
                            retrieved_rules,
                            list,
                        ):

                            rag_rows = []

                            for rule in retrieved_rules:

                                if isinstance(
                                    rule,
                                    dict,
                                ):

                                    rag_rows.append(
                                        {
                                            "Rule": rule.get(
                                                "id",
                                                "—",
                                            ),
                                            "Title": rule.get(
                                                "title",
                                                "—",
                                            ),
                                            "Severity": rule.get(
                                                "severity",
                                                "—",
                                            ),
                                        }
                                    )

                            if rag_rows:

                                st.dataframe(
                                    make_display_safe(
                                        pd.DataFrame(
                                            rag_rows
                                        )
                                    ),
                                    use_container_width=True,
                                    hide_index=True,
                                )

                            else:

                                st.write(
                                    retrieved_rules
                                )

                        else:

                            st.write(
                                retrieved_rules
                            )

            with right:

                st.subheader(
                    "Policy Decision"
                )

                policy_result = policy.get(
                    "policy_result",
                    "—",
                )

                if str(
                    policy_result
                ).upper() == "APPROVED":

                    st.success(
                        f"Policy: {policy_result}"
                    )

                elif str(
                    policy_result
                ).upper() == "REJECTED":

                    st.error(
                        f"Policy: {policy_result}"
                    )

                else:

                    st.info(
                        f"Policy: {policy_result}"
                    )

                st.write(
                    f"**Reason:** "
                    f"{policy.get('reason', '—')}"
                )

                st.write(
                    f"**Policy version:** "
                    f"{policy.get('policy_version', '—')}"
                )

                st.write("")

                st.subheader(
                    "Controlled Response"
                )

                if action_result:

                    a1, a2 = st.columns(2)

                    with a1:

                        st.metric(
                            "ACTION",
                            action_label(
                                action_result.get(
                                    "action",
                                    "—",
                                )
                            ),
                        )

                    with a2:

                        st.metric(
                            "RESULT",
                            get_actual_status(
                                action_result,
                                tx_result,
                            ),
                        )

                    # ------------------------------------------------
                    # ROBUST VERIFICATION
                    # ------------------------------------------------

                    if is_action_verified(
                        action_result
                    ):

                        st.success(
                            "✓ ACTION VERIFIED"
                        )

                    else:

                        st.error(
                            "✗ ACTION VERIFICATION FAILED"
                        )

                    st.caption(
                        action_result.get(
                            "message",
                            action_result.get(
                                "verification_status",
                                "—",
                            ),
                        )
                    )

                else:

                    st.warning(
                        "No action result returned."
                    )

            # ------------------------------------------------
            # CASE
            # ------------------------------------------------

            if case:

                st.divider()

                st.subheader(
                    "Investigation Case"
                )

                c1, c2, c3 = st.columns(3)

                c1.metric(
                    "CASE",
                    f"#{case.get('id', '—')}",
                )

                c2.metric(
                    "PRIORITY",
                    case.get(
                        "priority",
                        "—",
                    ),
                )

                c3.metric(
                    "STATUS",
                    case.get(
                        "status",
                        "—",
                    ),
                )

                st.info(
                    case.get(
                        "investigation_summary",
                        "No investigation summary available.",
                    )
                )

            # ------------------------------------------------
            # TRANSACTION CONTEXT
            # ------------------------------------------------

            st.divider()

            st.subheader(
                "Transaction Context"
            )

            context = [
                (
                    "User",
                    tx_result.get(
                        "user_id",
                        selected_user_id,
                    ),
                ),
                (
                    "Amount",
                    money(
                        tx_result.get(
                            "amount",
                            amount,
                        )
                    ),
                ),
                (
                    "Payment method",
                    tx_result.get(
                        "payment_method",
                        payment_method,
                    ),
                ),
                (
                    "Country",
                    tx_result.get(
                        "country",
                        country,
                    ),
                ),
                (
                    "Failed attempts",
                    tx_result.get(
                        "failed_attempts",
                        failed_attempts,
                    ),
                ),
                (
                    "Account age",
                    tx_result.get(
                        "account_age_days",
                        account_age_days,
                    ),
                ),
                (
                    "1h velocity",
                    tx_result.get(
                        "user_txn_count_1h",
                        velocity,
                    ),
                ),
                (
                    "Final status",
                    get_actual_status(
                        action_result,
                        tx_result,
                    ),
                ),
            ]

            context_df = pd.DataFrame(
                [
                    {
                        "Field": str(
                            label
                        ),
                        "Value": str(
                            value
                        ),
                    }
                    for label, value
                    in context
                ]
            )

            st.dataframe(
                make_display_safe(
                    context_df
                ),
                use_container_width=True,
                hide_index=True,
            )

            # ------------------------------------------------
            # RAW RESPONSE
            # ------------------------------------------------

            with st.expander(
                "🔍 View Complete Backend JSON"
            ):

                st.json(
                    result
                )

            clear_data_cache()


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "RIS-Agent • AI Risk Investigation System • "
    "ML pattern detection + dynamic RAG + agent investigation + "
    "deterministic policy enforcement"
)
