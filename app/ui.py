import streamlit as st
import requests
import html

# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Kestrel Home | Returns Intelligence",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

import os
API_URL = os.environ.get("KESTREL_API_URL", "http://127.0.0.1:8000/predict")

# =========================================================
# THEME TOGGLE
# =========================================================

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

dark_mode = st.session_state.dark_mode

# =========================================================
# THEME CSS
# =========================================================

if dark_mode:

    COLORS = {
        "background": "#0D1422",
        "surface": "#172438",
        "surface2": "#1D3048",
        "text": "#F1F5FB",
        "muted": "#A4B4C8",
        "border": "#30445D",
        "input": "#20334A",
        "accent": "#9A8BFF",
        "reason_bg": "#1B3048",
        "reason_text": "#E3ECF7",
        "metric_text": "#FFFFFF",
        "footer": "#9BAEC2",
        "warning_bg": "#44391F",
        "warning_border": "#8B7137",
        "success_bg": "#183D35",
        "success_border": "#32735E",
        "action_text": "#FFFFFF",
        "number_bg": "#34406B",
        "number_text": "#D5CEFF"
    }

else:

    COLORS = {
        "background": "#F3F5FC",
        "surface": "#FFFFFF",
        "surface2": "#F8FAFF",
        "text": "#17233B",
        "muted": "#7D8AA1",
        "border": "#E3E8F2",
        "input": "#F8FAFD",
        "accent": "#6658D3",
        "reason_bg": "#FFFFFF",
        "reason_text": "#43516A",
        "metric_text": "#17233B",
        "footer": "#8792A6",
        "warning_bg": "#FFF7E8",
        "warning_border": "#F0D59A",
        "success_bg": "#EAF8F2",
        "success_border": "#B9E8D1",
        "action_text": "#25334D",
        "number_bg": "#EEEAFE",
        "number_text": "#6658D3"
    }


st.markdown(
    f"""
    <style>

    @import url(
      'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'
    );

    :root {{
        color-scheme: {"dark" if dark_mode else "light"};
    }}

    .stApp {{
        background: {COLORS["background"]} !important;
        color: {COLORS["text"]} !important;
        font-family: 'Inter', sans-serif;
    }}

    header[data-testid="stHeader"] {{
        background: transparent;
    }}

    .block-container {{
        max-width: 1250px;
        padding: 1.5rem 2rem 3rem;
    }}

    /* GENERAL TEXT */

    .stApp,
    .stApp p,
    .stApp label,
    .stApp li {{
        color: {COLORS["text"]};
    }}

    .stApp h1,
    .stApp h2,
    .stApp h3 {{
        color: {COLORS["text"]};
    }}

    /* BRAND */

    .brand {{
        display: flex;
        align-items: center;
        gap: 14px;
        margin: 12px 0 25px;
    }}

    .brand-icon {{
        background: linear-gradient(135deg, #6658D3, #3989D8);
        width: 52px;
        height: 52px;
        border-radius: 15px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 25px;
        box-shadow: 0 5px 16px #6658D333;
    }}

    .brand-name {{
        font-size: 21px;
        font-weight: 800;
        color: {COLORS["text"]} !important;
        letter-spacing: .5px;
    }}

    .brand-sub {{
        color: {COLORS["muted"]} !important;
        font-size: 10px;
        letter-spacing: 2px;
    }}

    /* HERO */

    .hero {{
        background: linear-gradient(
            115deg, #5546C7, #397FD4, #269EAA
        );
        border-radius: 22px;
        padding: 38px;
        margin: 10px 0 30px;
        box-shadow: 0 12px 28px #5369C52B;
    }}

    .hero-tag {{
        color: #D9E8FF !important;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 2px;
    }}

    .hero-title {{
        color: #FFFFFF !important;
        font-size: 35px;
        font-weight: 800;
        margin: 15px 0 10px;
    }}

    .hero-desc {{
        color: #E9EEFF !important;
        font-size: 14px;
        line-height: 1.8;
        max-width: 720px;
    }}

    /* SECTION HEADINGS */

    .section-title {{
        font-size: 22px;
        font-weight: 750;
        color: {COLORS["text"]} !important;
        margin: 25px 0 12px;
    }}

    .section-caption {{
        color: {COLORS["muted"]} !important;
        font-size: 13px;
        margin-bottom: 18px;
    }}

    /* FORM */

    div[data-testid="stForm"] {{
        background: {COLORS["surface"]} !important;
        border: 1px solid {COLORS["border"]} !important;
        border-radius: 18px;
        padding: 26px;
        box-shadow: 0 5px 20px #25385812;
    }}

    div[data-testid="stForm"] h3 {{
        color: {COLORS["text"]} !important;
        font-size: 16px;
        font-weight: 700;
    }}

    div[data-testid="stForm"] label {{
        color: {COLORS["muted"]} !important;
        font-weight: 600;
    }}

    div[data-testid="stForm"] input {{
        background: {COLORS["input"]} !important;
        color: {COLORS["text"]} !important;
        border: 1px solid {COLORS["border"]} !important;
        border-radius: 9px;
    }}

    div[data-testid="stForm"] [data-baseweb="select"] > div {{
        background: {COLORS["input"]} !important;
        color: {COLORS["text"]} !important;
        border-color: {COLORS["border"]} !important;
    }}

    div[data-testid="stForm"] hr {{
        border-color: {COLORS["border"]} !important;
    }}

    /* BUTTONS */

    div[data-testid="stFormSubmitButton"] button {{
        background: linear-gradient(100deg, #6658D3, #3989D8);
        color: white !important;
        border: none;
        border-radius: 10px;
        font-weight: 700;
        min-height: 48px;
        box-shadow: 0 5px 13px #6658D333;
    }}

    div[data-testid="stFormSubmitButton"] button:hover {{
        filter: brightness(1.1);
        color: white !important;
    }}

    /* METRIC CARDS */

    .metric-card {{
        background: {COLORS["surface"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 17px;
        padding: 23px;
        min-height: 145px;
        box-shadow: 0 6px 20px #25385812;
    }}

    .metric-label {{
        color: {COLORS["muted"]} !important;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1px;
        margin-bottom: 13px;
    }}

    .metric-value {{
        color: {COLORS["metric_text"]} !important;
        font-size: 32px;
        font-weight: 800;
    }}

    .metric-foot {{
        color: {COLORS["muted"]} !important;
        font-size: 11px;
        margin-top: 9px;
    }}

    /* ACTION CARD */

    .action-card {{
        border-radius: 15px;
        padding: 22px;
        margin: 12px 0 20px;
    }}

    .action-warning {{
        background: {COLORS["warning_bg"]};
        border: 1px solid {COLORS["warning_border"]};
    }}

    .action-success {{
        background: {COLORS["success_bg"]};
        border: 1px solid {COLORS["success_border"]};
    }}

    .action-label {{
        font-size: 11px;
        color: {COLORS["muted"]} !important;
        font-weight: 700;
        letter-spacing: 1px;
        margin-bottom: 9px;
    }}

    .action-value {{
        color: {COLORS["action_text"]} !important;
        font-size: 19px;
        font-weight: 750;
    }}

    /* EXPLANATION CARDS */

    .reason-card {{
        display: flex;
        align-items: flex-start;
        gap: 13px;
        background: {COLORS["reason_bg"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 13px;
        padding: 16px;
        margin-bottom: 10px;
        box-shadow: 0 4px 12px #25385808;
    }}

    .reason-number {{
        min-width: 29px;
        height: 29px;
        border-radius: 9px;
        background: {COLORS["number_bg"]};
        color: {COLORS["number_text"]} !important;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 12px;
    }}

    .reason-text {{
        color: {COLORS["reason_text"]} !important;
        font-size: 13px;
        line-height: 1.7;
        padding-top: 4px;
    }}

    /* EXPANDERS */

    div[data-testid="stExpander"] {{
        background: {COLORS["surface"]} !important;
        border: 1px solid {COLORS["border"]} !important;
        border-radius: 12px;
    }}

    div[data-testid="stExpander"] summary,
    div[data-testid="stExpander"] p,
    div[data-testid="stExpander"] span {{
        color: {COLORS["text"]} !important;
    }}

    /* PROGRESS BAR */

    div[data-testid="stProgress"] > div > div {{
        background: linear-gradient(90deg, #6658D3, #36A5B5);
        border-radius: 20px;
    }}

    /* FOOTER */

    .footer {{
        text-align: center;
        color: {COLORS["footer"]} !important;
        font-size: 11px;
        line-height: 1.9;
        padding-top: 15px;
    }}

    </style>
    """,
    unsafe_allow_html=True
)

# =========================================================
# TOP BAR AND THEME BUTTON
# =========================================================

top_left, top_right = st.columns([8, 1])

with top_right:

    theme_button = "☀️ Light" if dark_mode else "🌙 Dark"

    if st.button(theme_button, key="theme_toggle"):
        st.session_state.dark_mode = not dark_mode
        st.rerun()

# =========================================================
# BRAND HEADER
# =========================================================

st.markdown("""
<div class="brand">
    <div class="brand-icon">📦</div>
    <div>
        <div class="brand-name">KESTREL HOME</div>
        <div class="brand-sub">RETURNS INTELLIGENCE</div>
    </div>
</div>

<div class="hero">
    <div class="hero-tag">SMARTER FULFILMENT DECISIONS</div>
    <div class="hero-title">Pre-dispatch intelligence</div>
    <div class="hero-desc">
        Predict return risk before an order is dispatched.
        Identify orders that may benefit from a customer
        confirmation call and make more informed fulfilment decisions.
    </div>
</div>
""", unsafe_allow_html=True)

# =========================================================
# ORDER INPUT FORM
# =========================================================

st.markdown(
    '<div class="section-title">📝 Order assessment</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-caption">'
    'Enter the order and customer information to generate a risk score.'
    '</div>',
    unsafe_allow_html=True
)


# =========================================================
# DEMO EXAMPLES (values taken from real orders; IDs replaced)
# =========================================================

EXAMPLES = {
    "Low risk - mixer grinder, UPI, new customer": dict(
        f_order_id="DEMO-1", f_customer_id="DEMO", f_sku="KH-MG-02", f_channel="app", f_payment="prepaid_upi",
        f_gift="N", f_discount=4.0, f_qty=1, f_value=3839.04, f_days=3, f_prior_orders=0, f_prior_returns=0,
        f_shield="N", f_state="TN", f_pincode="440479"),
    "Borderline - induction cooktop, 1 earlier return": dict(
        f_order_id="DEMO-2", f_customer_id="DEMO", f_sku="KH-IC-03", f_channel="web", f_payment="prepaid_upi",
        f_gift="N", f_discount=13.0, f_qty=1, f_value=3521.76, f_days=7, f_prior_orders=2, f_prior_returns=1,
        f_shield="N", f_state="TS", f_pincode="440378"),
    "High risk - COD gift, Shield member, 4 earlier returns": dict(
        f_order_id="DEMO-3", f_customer_id="DEMO", f_sku="KH-AF-02", f_channel="marketplace", f_payment="cod",
        f_gift="Y", f_discount=8.0, f_qty=1, f_value=5979.08, f_days=5, f_prior_orders=4, f_prior_returns=4,
        f_shield="Y", f_state="KA", f_pincode="440459"),
    "Data problem - October gateway value 100x too high": dict(
        f_order_id="DEMO-4", f_customer_id="DEMO", f_sku="KH-IC-03", f_channel="web", f_payment="prepaid_upi",
        f_gift="N", f_discount=13.0, f_qty=1, f_value=352176.0, f_days=7, f_prior_orders=2, f_prior_returns=1,
        f_shield="N", f_state="TS", f_pincode="440378"),
    "Walk-in partner outlet - no address (000000)": dict(
        f_order_id="DEMO-5", f_customer_id="DEMO", f_sku="KH-MG-02", f_channel="partner_outlet", f_payment="prepaid_upi",
        f_gift="N", f_discount=4.0, f_qty=1, f_value=3839.04, f_days=3, f_prior_orders=0, f_prior_returns=0,
        f_shield="N", f_state="TN", f_pincode="000000"),
}


for _k, _v in {"f_placed": "2026-10-01 10:30:00", "f_discount": 0.0, "f_qty": 1, "f_value": 5000.0,
               "f_days": 3, "f_prior_orders": 2, "f_prior_returns": 0}.items():
    st.session_state.setdefault(_k, _v)


def load_example():
    choice = st.session_state.get("example_choice")
    if choice in EXAMPLES:
        for key, value in EXAMPLES[choice].items():
            st.session_state[key] = value
        st.session_state["f_placed"] = "2026-10-01 10:30:00"


st.selectbox(
    "Quick demo: load an example order (or fill the form yourself)",
    ["- choose -"] + list(EXAMPLES),
    key="example_choice",
    on_change=load_example
)

with st.form("order_form"):

    st.markdown("### 01 · Order identification")

    col1, col2, col3 = st.columns(3)

    with col1:
        order_id = st.text_input("Order ID", key="f_order_id")

    with col2:
        customer_id = st.text_input("Customer ID", key="f_customer_id")

    with col3:
        sku = st.text_input("Product SKU", key="f_sku")

    st.divider()

    st.markdown("### 02 · Order details")

    col1, col2 = st.columns(2)

    with col1:

        order_placed_at = st.text_input(
            "Order date and time", key="f_placed")

        sales_channel = st.selectbox(
            "Sales channel",
            ["web", "app", "marketplace", "partner_outlet"], key="f_channel")

        payment_mode = st.selectbox(
            "Payment mode",
            [
                "prepaid_upi",
                "cod",
                "prepaid_card",
                "emi"
            ], key="f_payment")

    with col2:

        is_gift = st.selectbox(
            "Is this a gift?",
            ["N", "Y"], key="f_gift")

        discount_pct = st.number_input(
            "Discount (%)",
            min_value=0.0,
            max_value=100.0, key="f_discount")

        qty = st.number_input(
            "Quantity",
            min_value=1,
            step=1, key="f_qty")

    st.divider()

    st.markdown("### 03 · Purchase information")

    col1, col2 = st.columns(2)

    with col1:
        order_value_inr = st.number_input(
            "Order value (₹)",
            min_value=0.0, key="f_value")

    with col2:
        promised_delivery_days = st.number_input(
            "Promised delivery days",
            min_value=0,
            step=1, key="f_days")

    st.divider()

    st.markdown("### 04 · Customer history")

    col1, col2 = st.columns(2)

    with col1:
        customer_prior_orders = st.number_input(
            "Previous orders",
            min_value=0,
            step=1, key="f_prior_orders")

    with col2:
        customer_prior_returns = st.number_input(
            "Previous returns",
            min_value=0,
            step=1, key="f_prior_returns")

    col1, col2, col3 = st.columns(3)

    with col1:
        shield_member = st.selectbox(
            "Kestrel Shield member?",
            ["N", "Y"], key="f_shield")

    with col2:
        state = st.selectbox(
            "Delivery state",
            ["MH", "KA", "TS", "TN", "DL", "UP", "RJ", "MP"], key="f_state")

    with col3:
        delivery_pincode = st.text_input(
            "Delivery pincode (000000 = walk-in, no address)",
            key="f_pincode"
        )

    st.write("")

    submitted = st.form_submit_button(
        "🔍  Generate return risk assessment",
        use_container_width=True
    )

# =========================================================
# API REQUEST
# =========================================================

if submitted:

    if (
        not order_id.strip()
        or not sku.strip()
    ):

        st.warning(
            "Please enter the Order ID and Product SKU (or pick an example above)."
        )

    else:

        payload = {
            "order_id": order_id.strip(),
            "customer_id": customer_id.strip(),
            "sku": sku.strip(),
            "order_placed_at": order_placed_at,
            "sales_channel": sales_channel,
            "payment_mode": payment_mode,
            "discount_pct": discount_pct,
            "qty": qty,
            "order_value_inr": order_value_inr,
            "promised_delivery_days": promised_delivery_days,
            "is_gift": is_gift,
            "customer_prior_orders": customer_prior_orders,
            "customer_prior_returns": customer_prior_returns,
            "shield_member": shield_member,
            "state": state,
            "delivery_pincode": delivery_pincode.strip()
        }

        try:

            with st.spinner("Evaluating order risk..."):

                response = requests.post(
                    API_URL,
                    json=payload,
                    timeout=10
                )

            if response.status_code == 200:

                result = response.json()

                risk = float(result["return_risk_probability"])
                threshold = float(result["threshold"])
                action = result["recommended_action"]
                reasons = result.get("reasons", [])

                if not 0 <= risk <= 1:
                    st.error("The API returned an invalid probability.")
                    st.stop()

                for warning_text in result.get("warnings", []):
                    st.warning(warning_text)

                # =========================================
                # PREDICTION RESULTS
                # =========================================

                st.divider()

                st.markdown(
                    '<div class="section-title">'
                    '📊 Risk assessment results'
                    '</div>',
                    unsafe_allow_html=True
                )

                st.markdown(
                    f'<div class="section-caption">'
                    f'Analysis generated for order '
                    f'<b>{html.escape(str(result["order_id"]))}</b>'
                    f'</div>',
                    unsafe_allow_html=True
                )

                # =========================================
                # METRIC CARDS
                # =========================================

                col1, col2, col3 = st.columns(3)

                if risk >= threshold:
                    risk_color = "#D99024" if not dark_mode else "#F3B75B"
                    risk_status = "ELEVATED RISK"
                    status_color = risk_color
                else:
                    risk_color = "#15966B" if not dark_mode else "#62D2AE"
                    risk_status = "BELOW THRESHOLD"
                    status_color = risk_color

                with col1:

                    st.markdown(
                        f"""
                        <div class="metric-card">
                            <div class="metric-label">
                                ESTIMATED RETURN RISK
                            </div>
                            <div class="metric-value"
                                 style="color:{risk_color} !important">
                                {risk * 100:.2f}%
                            </div>
                            <div class="metric-foot">
                                Model-estimated probability
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                with col2:

                    st.markdown(
                        f"""
                        <div class="metric-card">
                            <div class="metric-label">
                                DECISION THRESHOLD
                            </div>
                            <div class="metric-value">
                                {threshold * 100:.0f}%
                            </div>
                            <div class="metric-foot">
                                Confirmation-call trigger
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                with col3:

                    st.markdown(
                        f"""
                        <div class="metric-card">
                            <div class="metric-label">
                                RISK STATUS
                            </div>
                            <div class="metric-value"
                                 style="font-size:21px;
                                 color:{status_color} !important">
                                {risk_status}
                            </div>
                            <div class="metric-foot">
                                Based on the selected threshold
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                # =========================================
                # PROBABILITY BAR
                # =========================================

                st.write("")

                st.markdown("**Return risk probability**")

                st.progress(max(0.0, min(1.0, risk)))

                st.caption(
                    f"{risk * 100:.2f}% estimated risk compared "
                    f"with the {threshold * 100:.0f}% "
                    "confirmation-call threshold."
                )

                # =========================================
                # RECOMMENDED ACTION
                # =========================================

                st.markdown(
                    '<div class="section-title">'
                    '🎯 Recommended next step'
                    '</div>',
                    unsafe_allow_html=True
                )

                action_class = (
                    "action-warning"
                    if risk >= threshold
                    else "action-success"
                )

                action_icon = "☎️" if risk >= threshold else "✅"

                st.markdown(
                    f"""
                    <div class="action-card {action_class}">
                        <div class="action-label">
                            RECOMMENDED ACTION
                        </div>
                        <div class="action-value">
                            {action_icon}&nbsp;&nbsp;
                            {html.escape(str(action))}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # =========================================
                # MODEL REASONS
                # =========================================

                st.markdown(
                    '<div class="section-title">'
                    '💡 What influenced this prediction?'
                    '</div>',
                    unsafe_allow_html=True
                )

                st.markdown(
                    '<div class="section-caption">'
                    'The strongest positive feature contributions '
                    'identified by the model.'
                    '</div>',
                    unsafe_allow_html=True
                )

                if reasons:

                    for index, reason in enumerate(reasons, start=1):

                        safe_reason = html.escape(str(reason))

                        st.markdown(
                            f"""
                            <div class="reason-card">
                                <div class="reason-number">
                                    {index}
                                </div>
                                <div class="reason-text">
                                    {safe_reason}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                else:

                    st.info(
                        "No individual feature explanations are available."
                    )

                with st.expander(
                    "How should these explanations be interpreted?"
                ):

                    st.write(
                        result.get(
                            "explanation_note",
                            "Explanations are based on model contributions."
                        )
                    )

                # =========================================
                # ORDER DETAILS
                # =========================================

                with st.expander("View prediction details"):

                    col1, col2 = st.columns(2)

                    with col1:
                        st.write("**Order ID**")
                        st.write(result["order_id"])

                        st.write("**Return risk probability**")
                        st.write(f"{risk:.4f}")

                    with col2:
                        st.write("**Decision threshold**")
                        st.write(f"{threshold:.2f}")

                        st.write("**Recommended action**")
                        st.write(action)

            else:

                st.error(
                    f"API error ({response.status_code})"
                )

                st.code(response.text)

        except requests.exceptions.ConnectionError:

            st.error(
                "Could not connect to FastAPI. "
                "Please start the API server first."
            )

        except requests.exceptions.Timeout:

            st.error(
                "The API request timed out. Please try again."
            )

        except (KeyError, ValueError, TypeError) as error:

            st.error(f"Unexpected API response: {error}")

        except requests.exceptions.RequestException as error:

            st.error(f"Request failed: {error}")

# =========================================================
# FOOTER
# =========================================================

st.divider()

st.markdown("""
<div class="footer">
    <b>KESTREL HOME</b> · RETURNS INTELLIGENCE PLATFORM<br>
    Machine learning-assisted decision support<br>
    Predictions are estimates and should support, not replace,
    operational judgement.
</div>
""", unsafe_allow_html=True)