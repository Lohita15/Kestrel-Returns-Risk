# Kestrel Home — Returns Risk

A pre-dispatch returns-risk scoring service for Kestrel Home. It estimates the probability that an order will be returned and recommends a **customer confirmation call** when the score meets the configured threshold. It is decision support: it does **not** automatically hold or cancel orders.

## What is included

- `predictions.csv` — return-risk scores for the 2,096 orders in the supplied dispatch snapshot. Columns: `order_id`, `score`.
- `models/returns_risk_model.pkl` — fitted scikit-learn pipeline used by the API.
- `models/lookups.json` — product metadata, threshold, historical rates and explanation/economics information needed by the API. It does not contain the customer table.
- `app/main.py` — FastAPI prediction endpoint.
- `app/ui.py` — Streamlit screen that calls the API.
- `train_clean.py` — data preparation, rolling-origin validation, final model training and prediction generation.
- `evidence/` — validation results and supporting charts/screenshots.
- `notebooks/` — exploratory analysis.

## Run the application from a clean clone

The checked-in model and lookup artifacts let you run the API and UI without the original training datasets and without a paid API key. You do **not** need to run model training just to use the application.

Use Python 3.10 or later. From the repository root:

### 1. Create and activate a virtual environment

**Windows PowerShell**
```powershell
py -3.10 -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS / Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Start the API

Open terminal 1, from the repository root:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

- API health/info: <http://127.0.0.1:8000/>
- Interactive API documentation: <http://127.0.0.1:8000/docs>

### 4. Start the Streamlit screen

Open terminal 2, activate the same virtual environment, and run:

```bash
streamlit run app/ui.py
```

The screen uses `http://127.0.0.1:8000/predict` by default. To use a different API URL, set `KESTREL_API_URL` before starting Streamlit.

**Windows PowerShell**
```powershell
$env:KESTREL_API_URL = "http://127.0.0.1:8000/predict"
streamlit run app/ui.py
```

**macOS / Linux**
```bash
export KESTREL_API_URL="http://127.0.0.1:8000/predict"
streamlit run app/ui.py
```

The UI includes a Quick demo selector with example orders. It also allows manual entry. The UI requires the API to be running in a separate terminal.

> The application does not call a paid or hosted LLM/API. The Streamlit stylesheet may request the Inter font from Google Fonts; if internet access is unavailable, the browser will use a fallback font. Core prediction functionality is local.

## API usage

### `POST /predict`

Example request:

```json
{
  "order_id": "DEMO-001",
  "customer_id": "CUST-DEMO",
  "sku": "KH-AF-01",
  "sales_channel": "marketplace",
  "payment_mode": "cod",
  "discount_pct": 10,
  "qty": 1,
  "order_value_inr": 4679.1,
  "promised_delivery_days": 8,
  "is_gift": "N",
  "customer_prior_orders": 3,
  "customer_prior_returns": 1,
  "shield_member": "N",
  "state": "MH",
  "delivery_pincode": "400001",
  "order_placed_at": "2026-10-01 10:30:00"
}
```

Required fields: `order_id`, `sku`, `sales_channel`, `payment_mode`, `discount_pct`, `qty`, `order_value_inr`, `promised_delivery_days`, `customer_prior_orders`, and `customer_prior_returns`.

Optional fields: `is_gift`, `shield_member`, `state`, `delivery_pincode`, `customer_id`, and `order_placed_at`. `customer_id` is echoed in the response; the API does not perform a customer-table lookup. The `sku` must exist in `models/lookups.json`.

Valid values:
- `sales_channel`: `app`, `web`, `marketplace`, `partner_outlet`
- `payment_mode`: `prepaid_upi`, `prepaid_card`, `cod`, `emi`
- `is_gift` and `shield_member`: `Y` or `N`

The response includes the estimated return probability, configured threshold, recommended action, up to three employee-readable model reasons, estimated net value of a call, any input warnings, and an explanation note. Reasons describe patterns in historical data; they are not causal explanations.

## Modelling approach

The final model is a scikit-learn Pipeline using Logistic Regression, with:
- 13 numeric features, including order value (log-transformed), customer order/return history, delivery promise, discount, quantity, product list price, and derived indicators.
- 5 categorical features: payment mode, sales channel, SKU, product family, and state.
- Standard scaling for numeric inputs and one-hot encoding for categorical inputs.

The model was selected after comparing alternative approaches during experimentation. Logistic Regression was retained for its combination of ranking performance, probability behavior, simplicity and employee-readable feature contributions.

### Data preparation and leakage controls

The training script:
- removes duplicate order IDs caused by repeated partner-feed imports;
- repairs the identified gateway amount issue where some order values were stored approximately 100 times too high;
- derives customer and product attributes from the supplied lookup tables;
- excludes post-outcome/service-event fields such as `last_service_event_type` and `pickup_scheduled_at`;
- excludes operational/source fields and unreliable free-text or signup-date fields from model inputs.

The API uses the model and `models/lookups.json`; it does not read the raw customer or order CSV files at prediction time. The customer attributes used for a prediction are supplied in the request.

## Validation results

The training script uses three chronological rolling-origin folds. Each fold trains on earlier orders and evaluates on the following period.

| Validation period starts | Validation rows | ROC-AUC | PR-AUC | Brier score |
|---|---:|---:|---:|---:|
| 2025-10-01 | 2,082 | 0.771 | 0.343 | 0.0845 |
| 2026-01-01 | 2,126 | 0.772 | 0.390 | 0.0869 |
| 2026-04-01 | 2,126 | 0.787 | 0.413 | 0.0849 |
| **Mean** | — | **0.777** | **0.382** | **0.0854** |

The historical return prevalence is approximately 11.4%, so PR-AUC should be interpreted relative to that baseline. Accuracy alone is not a useful headline metric for this imbalanced problem: a model that predicts no returns can already achieve high accuracy while detecting none of the returns.

**Expected hidden-set performance is an estimate, not a guarantee.** Based on the chronological validation results, a reasonable planning estimate is PR-AUC around 0.38, with variation possible because the hidden labels and sample composition are unknown.

## Operational recommendation and economics

The current threshold in `models/lookups.json` is **0.13**. Orders at or above this score receive a pre-dispatch confirmation-call recommendation; other orders receive standard dispatch.

The economic illustration uses the assignment's policy assumptions:
- return cost: ₹1,150;
- confirmation-call cost: ₹45;
- estimated return-prevention rate among called orders: 35%.

At the selected threshold, the README's planning estimate is approximately 190 calls per month at 700 monthly orders. The estimated gross avoided return cost is about ₹20,300/month and estimated call cost is about ₹8,600/month, for estimated net value of about ₹11,700/month. These are scenario estimates, not measured realized savings. A controlled pilot should validate call effectiveness, workload and customer outcomes before operational rollout.

The recommendation is **call rather than blanket-hold**. The policy indicates that holds can create cancellations and delays; Shield members are high-lifetime-value customers and should not be subjected to blanket holds. The model should support prioritization, not replace employee judgement.

## Retraining (requires the original data files)

Retraining is optional. It is not required to run the checked-in API/UI.

To retrain, place the authorized source files in `data/raw/`:

```text
data/raw/
├── train.csv
├── test_unlabelled.csv
├── customers.csv
└── products.csv
```

Then, from the repository root with the dependencies installed:

```bash
python train_clean.py
```

The script writes/updates:
- `models/returns_risk_model.pkl`
- `models/lookups.json`
- `predictions.csv`
- `evidence/cv_results.csv`

The training script also expects the corresponding input columns and schema used in the supplied assignment data. Do not commit private/raw customer data to a public repository.

## Known limitations

- The validation periods are historical; hidden-set performance may differ.
- The call-prevention and hold-cancellation rates are assumptions from the supplied policy/pilot context, not causal effects established by this model.
- The threshold is a practical operating choice and should be reviewed with call-centre capacity and pilot outcomes.
- The model identifies associations in historical data. Its reasons do not establish causation.
- Unknown SKUs are rejected by the API. Customer IDs are not looked up; customer-history and Shield fields are passed in the request.
- The model is a ranking and prioritization aid, not a guarantee that an order will or will not be returned.

## Cost

There is no paid model/API dependency. Prediction runs locally on CPU. This excludes the cost of any hosting infrastructure and the operational cost of confirmation calls.

## Repository hygiene

The public repository should contain the application code, model artifacts needed to run it, evidence, documentation and the required root-level `predictions.csv`. Keep the original raw datasets and private operational documents out of the public repository.
