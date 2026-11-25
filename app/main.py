"""Kestrel Returns Risk API.

Starts from a clean clone: needs only models/returns_risk_model.pkl and models/lookups.json
(both produced by train_clean.py; neither contains customer data). No paid API, no network.
"""
import json
from pathlib import Path
from typing import Literal, Optional

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

BASE = Path(__file__).resolve().parent.parent
model = joblib.load(BASE / "models" / "returns_risk_model.pkl")
LK = json.loads((BASE / "models" / "lookups.json").read_text())
THRESHOLD = LK["threshold"]
ECON = LK["economics"]
RATES = LK["rates"]
OVERALL = LK["overall_return_rate"]

app = FastAPI(
    title="Kestrel Returns Risk API",
    description="Scores one order before dispatch. Recommends a confirmation call, never an automatic hold.",
    version="2.0",
)


class OrderInput(BaseModel):
    order_id: str
    sku: str
    sales_channel: Literal["app", "web", "marketplace", "partner_outlet"]
    payment_mode: Literal["prepaid_upi", "prepaid_card", "cod", "emi"]
    discount_pct: float = Field(ge=0, le=90)
    qty: int = Field(gt=0, le=50)
    order_value_inr: float = Field(gt=0)
    promised_delivery_days: int = Field(ge=0, le=60)
    is_gift: Literal["Y", "N"] = "N"
    customer_prior_orders: int = Field(ge=0)
    customer_prior_returns: int = Field(ge=0)
    # Customer attributes are passed in, so no customer table has to ship with the service.
    shield_member: Literal["Y", "N"] = "N"
    state: Optional[str] = None
    delivery_pincode: Optional[str] = None  # "000000" = walk-in, no address; omitted = address assumed present
    customer_id: Optional[str] = None       # echoed back only
    order_placed_at: Optional[str] = None   # accepted, not used by the model (no signal in validation)


def pct(x: float) -> str:
    return f"{round(x * 100)}%"


def build_row(o: OrderInput, product: dict):
    warnings = []
    value = o.order_value_inr
    expected = product["list_price"] * o.qty * (1 - o.discount_pct / 100)
    ratio = value / expected if expected else 1.0
    if ratio > 50:  # Oct-2025 payment gateway stored paise (x100)
        value /= 100
        warnings.append(
            f"Order value looked ~100x too high versus list price (paise from the new gateway?); "
            f"used Rs {value:,.2f}."
        )
    elif not 0.5 <= ratio <= 2:
        warnings.append(
            f"Order value Rs {value:,.0f} is far from list price x qty after discount "
            f"(Rs {expected:,.0f}); check the amount."
        )
    state = o.state if o.state in LK["states"] else LK["states"][0]
    if o.state and o.state not in LK["states"]:
        warnings.append(f"Unknown state '{o.state}'; state was ignored.")
    # Only an explicit 000000 means "walk-in, no address". A missing field must NOT be read as no address.
    no_addr = int((o.delivery_pincode or "").strip() in ("0", "000000"))
    row = {
        "discount_pct": o.discount_pct,
        "qty": o.qty,
        "promised_delivery_days": o.promised_delivery_days,
        "customer_prior_orders": o.customer_prior_orders,
        "customer_prior_returns": o.customer_prior_returns,
        "log_val": float(np.log1p(value)),
        "prior_ret_rate": (o.customer_prior_returns + 0.1) / (o.customer_prior_orders + 1),
        "has_prior_ret": int(o.customer_prior_returns > 0),
        "no_address": no_addr,
        "gift": int(o.is_gift == "Y"),
        "shield": int(o.shield_member == "Y"),
        "cod": int(o.payment_mode == "cod"),
        "list_price_inr": product["list_price"],
        "payment_mode": o.payment_mode,
        "sales_channel": o.sales_channel,
        "sku": o.sku,
        "family": product["family"],
        "state": state,
    }
    return pd.DataFrame([row]), value, warnings


# original feature -> reader-friendly group
GROUPS = {
    "payment": ["cod", "payment_mode"],
    "history": ["customer_prior_returns", "prior_ret_rate", "has_prior_ret", "customer_prior_orders"],
    "shield": ["shield"],
    "product": ["family", "sku", "list_price_inr"],
    "value": ["log_val"],
    "delivery": ["promised_delivery_days"],
    "discount": ["discount_pct"],
    "gift": ["gift"],
    "channel": ["sales_channel"],
    "address": ["no_address"],
    "state": ["state"],
    "qty": ["qty"],
}


def group_contributions(df: pd.DataFrame) -> dict:
    pre, clf = model.named_steps["preprocessor"], model.named_steps["classifier"]
    x = pre.transform(df)
    x = x.toarray() if hasattr(x, "toarray") else np.asarray(x)
    contrib = x.reshape(-1) * clf.coef_[0]
    names = pre.get_feature_names_out()
    out = {g: 0.0 for g in GROUPS}
    for name, c in zip(names, contrib):
        kind, rest = name.split("__", 1)
        for g, members in GROUPS.items():
            if kind == "num" and rest in members:
                out[g] += c
            elif kind == "cat" and any(rest.startswith(m + "_") for m in members):
                out[g] += c
    # categorical groups: express relative to a typical order, not to the dropped baseline
    for feat, avg in LK["cat_avg_contribution"].items():
        for g, members in GROUPS.items():
            if feat in members:
                out[g] -= avg
    return out


def reason_text(g: str, o: OrderInput, product: dict) -> str:
    if g == "payment":
        return (f"Cash on delivery: {pct(RATES['payment_mode']['cod'])} of COD orders came back, "
                f"against {pct(RATES['payment_mode']['prepaid_upi'])} for UPI.")
    if g == "history":
        return (f"Customer already has {o.customer_prior_returns} return(s) in {o.customer_prior_orders} order(s). "
                f"Customers with any earlier return came back {pct(RATES['prior_return']['has_any'])} of the time "
                f"vs {pct(RATES['prior_return']['none'])}.")
    if g == "shield":
        return (f"Shield member (free returns): {pct(RATES['shield']['Y'])} return rate vs "
                f"{pct(RATES['shield']['N'])}. Use a friendly call; do not hold the order.")
    if g == "product":
        return (f"{product['family']} is a higher-return product line: "
                f"{pct(RATES['family'][product['family']])} vs {pct(OVERALL)} overall.")
    if g == "value":
        return (f"Above-average order value: orders of Rs 10,000+ are returned {pct(RATES['value_10k_plus']['yes'])} "
                f"of the time vs {pct(RATES['value_10k_plus']['no'])}.")
    if g == "delivery":
        return (f"Longer-than-average delivery promise ({o.promised_delivery_days} days); promises of 7+ days are returned "
                f"{pct(RATES['long_delivery_7plus']['yes'])} vs {pct(RATES['long_delivery_7plus']['no'])}.")
    if g == "discount":
        return (f"Above-average discount ({o.discount_pct:g}%); discounts of 20%+ are returned "
                f"{pct(RATES['discount_20plus']['yes'])} vs {pct(RATES['discount_20plus']['no'])}.")
    if g == "gift":
        return f"Gift order: {pct(RATES['gift']['Y'])} returned vs {pct(RATES['gift']['N'])}."
    if g == "channel":
        return (f"Sales channel '{o.sales_channel}' returns {pct(RATES['sales_channel'][o.sales_channel])} "
                f"vs {pct(OVERALL)} overall.")
    if g == "address":
        return "No delivery address captured (walk-in order)."
    return {"state": "Delivery state pattern.", "qty": "Order quantity."}[g]


def explain(df, o, product, top_n=3):
    contrib = group_contributions(df)
    ranked = [g for g, c in sorted(contrib.items(), key=lambda kv: -kv[1])
              if c > 0.05 and g not in ("state", "qty")]  # too weak to show an employee as a "reason"
    reasons = [reason_text(g, o, product) for g in ranked[:top_n]]
    return reasons or ["No strong risk driver: this order looks like a typical low-risk order."]


@app.get("/")
def home():
    return {"message": "Kestrel Returns Risk API is running", "threshold": THRESHOLD}


@app.post("/predict")
def predict(o: OrderInput):
    product = LK["products"].get(o.sku)
    if product is None:
        raise HTTPException(status_code=404, detail=f"Unknown SKU '{o.sku}'. Known: {sorted(LK['products'])}")
    df, value_used, warnings = build_row(o, product)
    p = float(model.predict_proba(df)[0, 1])
    call = p >= THRESHOLD
    saving = p * ECON["call_prevention_rate"] * ECON["return_cost_inr"]
    action = "Pre-dispatch confirmation call" if call else "Standard dispatch"
    return {
        "order_id": o.order_id,
        "customer_id": o.customer_id,
        "return_risk_probability": round(p, 4),
        "threshold": THRESHOLD,
        "recommended_action": action,
        "reasons": explain(df, o, product),
        "expected_net_value_of_call_inr": round(saving - ECON["call_cost_inr"], 1),
        "order_value_used_inr": round(value_used, 2),
        "warnings": warnings,
        "explanation_note": (
            "Probabilities are calibrated on past Kestrel orders; reasons are patterns in that history, not proof "
            "of cause. We recommend calls rather than holds: a hold only prevents a return if the customer cancels "
            "(~12%)."
        ),
    }