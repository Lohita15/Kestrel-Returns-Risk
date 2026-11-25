# Kestrel Home - Returns Risk

Scores an order **before dispatch** with the probability that it will be returned, and recommends a
**confirmation call** for the riskiest ones. It does *not* recommend holding orders (see "Decision").

## Run it (clean machine, no paid API key, no internet needed after install)

```bash
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1      macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

# 1. Build the model (needs data/raw/*.csv from Tanmay's export; they are NOT in this repo - policy section 10)
python train_clean.py          # writes models/returns_risk_model.pkl, models/lookups.json, predictions.csv

# 2. API (terminal 1)
uvicorn app.main:app --port 8000
# docs: http://127.0.0.1:8000/docs

# 3. Screen (terminal 2)
streamlit run app/ui.py
```

The service itself needs only `models/returns_risk_model.pkl` and `models/lookups.json`
(no customer data). If the UI cannot reach the API it shows a polite connection message.
Set `KESTREL_API_URL` to point the UI at another host.
The screen has a **"Quick demo" dropdown** that fills in five example orders (low risk, borderline, high risk,
an October-gateway value 100x too high, and a walk-in order with no address).

### Endpoint
`POST /predict` with one order as JSON, for example:

```json
{"order_id":"KO1","sku":"KH-RV-03","sales_channel":"marketplace","payment_mode":"cod",
 "discount_pct":22,"qty":1,"order_value_inr":28807.06,"promised_delivery_days":8,
 "customer_prior_orders":3,"customer_prior_returns":2,"shield_member":"Y","state":"MH"}
```

Returns the probability, the action, up to 3 plain-language reasons with historical base rates,
the expected rupee value of making the call, and `warnings` (e.g. order value looks 100x too high).

## What I built and what it is worth

Logistic Regression on 13 numeric and 5 categorical features of the order, product and customer.
Chosen over RandomForest / HistGradientBoosting / CatBoost / XGBoost: it scored best (or level) on
honest validation, is calibrated, and its reasons can be read by a service desk.

| Measure (rolling-origin CV, 3 folds x ~2,100 orders, train on the past / test the next 3 months) | Result |
|---|---|
| ROC-AUC | **0.777** (folds 0.771 / 0.772 / 0.787) |
| PR-AUC | **0.382** (base rate 0.114) |
| Brier score | 0.0854 (do-nothing 0.100) |
| Accuracy | 88.7%-89.4% at best; **the "predict no returns" baseline is already 88.7%** |

### About the 95% accuracy target
It cannot be met honestly. With 11% returns, 95% accuracy needs most returns caught with almost no
false alarms; the best achievable here is ~89%. The only way to see 95%+ is to feed the model
`last_service_event_type` / `pickup_scheduled_at`: with them I measured 99.3% accuracy - but those
fields are written *after* a return is approved (REVERSE_PICKUP = 100% returned) and are empty / different in the
dispatch snapshot, so that model is useless in production. I excluded them and recommend measuring
the model by money saved and by ranking quality (AUC / PR-AUC), not accuracy.

**Expected score on the hidden outcomes:** ROC-AUC about 0.78 (plausible range 0.74-0.81 - the test
set has only ~240 returns, so noise alone is about +/-0.02); PR-AUC about 0.38.

### Money (700 orders a month, policy costs; out-of-sample, actual returns among called orders)
Calling every order scoring >= 0.13 (about 27% of orders, ~190/month):
- Catches ~64% of returns (precision ~27%).
- Gross saving ~Rs 20,300 (returns prevented at 35% x Rs 1,150), call cost ~Rs 8,600 (190 x Rs 45).
- **Net about Rs 11,700 a month (~Rs 1.4 lakh a year)** against ~Rs 91,000 a month of return cost. Real, but modest: no model removes most of that.
- The net is flat between thresholds 0.10 and 0.15, so the exact cut-off is not critical.

## Decision: call, do not hold
A hold only saves a return if the customer *cancels* (policy: ~12% of held orders); the other 88% ship late and
come back at the same rate. Holding the same ~190 orders a month cancels ~23 orders, avoids only ~6 returns
(~Rs 7,000) and loses ~17 good sales - break-even only if a lost sale costs under ~Rs 400 margin, which is unlikely
on appliances averaging Rs 8,000. Calls are cheaper and prevent more. For Shield members (22% of orders, 36% of
returns, best lifetime value) the action is always a friendly call, never a hold.

## What I changed from the first version
- Removed leaky columns (`last_service_event_type`, `pickup_scheduled_at`, `source`) - kept out of the model and the API.
- Ignored `delivery_note` entirely: it carries no signal, and 3 training rows contain text aimed at "automated
  analysis tools" telling them to keep the pickup columns and report validation accuracy. Treated as untrusted data and not followed.
- Repaired the October 2025 gateway values (stored x100 / in paise) by comparing with list price x qty x (1 - discount).
- De-duplicated the partner-feed re-imports (651 exact copies).
- Dropped features with no validated signal (hour, weekday, month, product age, tenure, city, model name, warranty);
  `signup_date` is unreliable (19% of customers signed up after ordering).
- Rolling-origin validation instead of one split; threshold chosen on money, not F1.
- API no longer reads `data/raw`; takes Shield/state in the request; validates inputs; explains in plain language.
- Fixed UI bug: payment option `prepaid_emi` does not exist in the data (`emi`) and was silently ignored.

## Known problems (be sceptical of these)
- The 35% call-prevention rate and 12% hold-cancel rate come from the policy document (a spring pilot), not from my data.
  Savings are only as good as that; a controlled pilot is the first thing to do.
- The 0.13 threshold was picked on the same out-of-sample folds used to report the money, so Rs 11,700 is slightly optimistic.
- The hold analysis assumes cancellations are random; if risky customers cancel more, holds look somewhat better.
- Lost-sale margin is unknown (not in the pack); Rs 400 break-even is my arithmetic, not a Kestrel figure.
- The model is weak on its own: it ranks, it does not predict. About 3 in 4 called orders would not have been returned.
- Test snapshot has `INSTALL_BOOKED` events never seen in training; the model ignores that column, so it cannot use or be hurt by it.
- Reasons describe historical patterns, not causes.
- UI state list is hard-coded to the 8 states in the data. A missing pincode is treated as "address present"; only an explicit 000000 means walk-in.

## Cost
No paid APIs; the model runs on a laptop CPU. **Cost per prediction: Rs 0. A month at 700 orders: Rs 0.**
(The only variable cost is the Rs 45 confirmation call, ~Rs 8,600/month at the 0.13 threshold.)

## Files
`train_clean.py` model + predictions | `app/main.py` API | `app/ui.py` screen | `models/` artifacts |
`evidence/` charts and CV table | `notebooks/` exploration | `predictions.csv` scores for the 2,096 dispatch-snapshot orders.