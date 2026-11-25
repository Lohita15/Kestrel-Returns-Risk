"""Leak-free Kestrel returns model. Run from repo root:  python train_clean.py
Reads data/raw/*.csv, writes models/returns_risk_model.pkl, predictions.csv, evidence/cv_results.csv
"""
import warnings; warnings.filterwarnings("ignore")
from pathlib import Path
import json, joblib, numpy as np, pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

RAW = Path("data/raw")
tr = pd.read_csv(RAW / "train.csv"); te = pd.read_csv(RAW / "test_unlabelled.csv")
cu = pd.read_csv(RAW / "customers.csv"); pr = pd.read_csv(RAW / "products.csv")

# 1. one row per order (partner-feed re-imports are exact copies; keep CRM)
tr = (tr.assign(_p=tr.source.map({"crm": 0, "partner_feed": 1})).sort_values("_p")
        .drop_duplicates("order_id").drop(columns="_p"))
tr["t"] = pd.to_datetime(tr.order_placed_at); te["t"] = pd.to_datetime(te.order_placed_at)
tr = tr.sort_values("t").reset_index(drop=True)

def build(d):
    d = d.merge(cu[["customer_id", "state", "shield_member"]], on="customer_id", how="left") \
         .merge(pr[["sku", "family", "list_price_inr"]], on="sku", how="left")
    expected = d.list_price_inr * d.qty * (1 - d.discount_pct / 100)
    # Oct-2025 gateway stored values x100 (paise): repair by comparing with list price
    d["value_fixed"] = np.where(d.order_value_inr / expected > 50, d.order_value_inr / 100, d.order_value_inr)
    d["log_val"] = np.log1p(d.value_fixed)
    d["no_address"] = (d.delivery_pincode == 0).astype(int)
    d["prior_ret_rate"] = (d.customer_prior_returns + 0.1) / (d.customer_prior_orders + 1)
    d["has_prior_ret"] = (d.customer_prior_returns > 0).astype(int)
    d["gift"] = (d.is_gift == "Y").astype(int)
    d["shield"] = (d.shield_member == "Y").astype(int)
    d["cod"] = (d.payment_mode == "cod").astype(int)
    return d
trf, tef = build(tr), build(te)

# NOT used on purpose: last_service_event_type, pickup_scheduled_at (written AFTER a return is approved;
# absent/different in the dispatch snapshot), source, delivery_note (noise; 3 rows carry injected text),
# signup_date (19% of customers signed up after ordering), hour/dow/month/age (no signal in CV).
NUM = ["discount_pct", "qty", "promised_delivery_days", "customer_prior_orders", "customer_prior_returns",
       "log_val", "prior_ret_rate", "has_prior_ret", "no_address", "gift", "shield", "cod", "list_price_inr"]
CAT = ["payment_mode", "sales_channel", "sku", "family", "state"]
def make():
    return Pipeline([("preprocessor", ColumnTransformer([("num", StandardScaler(), NUM),
                      ("cat", OneHotEncoder(handle_unknown="ignore"), CAT)])),
                     ("classifier", LogisticRegression(C=0.1, max_iter=3000))])

# 2. rolling-origin CV (train on past, score the next 3 months) - 3 folds
rows, edges = [], ["2025-10-01", "2026-01-01", "2026-04-01", "2026-07-01"]
for a, b in zip(edges[:-1], edges[1:]):
    t_, v = trf[trf.t < a], trf[(trf.t >= a) & (trf.t < b)]
    p = make().fit(t_, t_.returned).predict_proba(v)[:, 1]
    rows.append(dict(valid_from=a, n=len(v), auc=roc_auc_score(v.returned, p),
                     pr_auc=average_precision_score(v.returned, p), brier=brier_score_loss(v.returned, p)))
cv = pd.DataFrame(rows); print(cv.round(4)); print(cv[["auc", "pr_auc", "brier"]].mean().round(4))
Path("evidence").mkdir(exist_ok=True); cv.to_csv("evidence/cv_results.csv", index=False)

# 3. final fit on all history, score the dispatch snapshot
final = make().fit(trf, trf.returned)
Path("models").mkdir(exist_ok=True); joblib.dump(final, "models/returns_risk_model.pkl")
out = pd.DataFrame({"order_id": tef.order_id, "score": final.predict_proba(tef)[:, 1]})
assert len(out) == 2096 and out.order_id.is_unique and out.score.between(0, 1).all()
out.to_csv("predictions.csv", index=False); print("wrote predictions.csv", out.score.describe().round(3).to_dict())

# 4. Small, non-personal lookup file so the API starts on a clean machine (no customer data, no data/raw).
def rate(mask): return round(float(trf.returned[mask].mean()), 4)
cls = final.named_steps["classifier"]; pre = final.named_steps["preprocessor"]
names = list(pre.get_feature_names_out()); coef = dict(zip(names, cls.coef_[0]))
# average contribution of each categorical group on training data (so reasons are "vs typical order")
cat_avg = {}
for c in CAT:
    freq = trf[c].value_counts(normalize=True)
    cat_avg[c] = float(sum(f * coef.get(f"cat__{c}_{v}", 0.0) for v, f in freq.items()))
lookups = {
    "threshold": 0.13,
    "products": pr.set_index("sku")[["family", "list_price_inr"]].rename(columns={"list_price_inr": "list_price"}).to_dict("index"),
    "states": sorted(cu.state.unique().tolist()),
    "cat_avg_contribution": cat_avg,
    "overall_return_rate": rate(trf.returned >= 0),
    "rates": {
        "payment_mode": {k: rate(trf.payment_mode == k) for k in trf.payment_mode.unique()},
        "sales_channel": {k: rate(trf.sales_channel == k) for k in trf.sales_channel.unique()},
        "family": {k: rate(trf.family == k) for k in trf.family.unique()},
        "shield": {"Y": rate(trf.shield == 1), "N": rate(trf.shield == 0)},
        "gift": {"Y": rate(trf.gift == 1), "N": rate(trf.gift == 0)},
        "prior_return": {"has_any": rate(trf.customer_prior_returns > 0), "none": rate(trf.customer_prior_returns == 0)},
        "long_delivery_7plus": {"yes": rate(trf.promised_delivery_days >= 7), "no": rate(trf.promised_delivery_days < 7)},
        "discount_20plus": {"yes": rate(trf.discount_pct >= 20), "no": rate(trf.discount_pct < 20)},
        "value_10k_plus": {"yes": rate(trf.value_fixed >= 10000), "no": rate(trf.value_fixed < 10000)},
    },
    "economics": {"return_cost_inr": 1150, "call_cost_inr": 45, "call_prevention_rate": 0.35, "hold_cancel_rate": 0.12},
}
json.dump(lookups, open("models/lookups.json", "w"), indent=1)
print("wrote models/lookups.json")