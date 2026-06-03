"""
app.py  (project root)  --  the demo web app
============================================
A small LOCAL web page (built with Streamlit) that loads the trained model and predicts
blood glucose. Runs on your laptop, no GPU, no internet needed.

Run it:   streamlit run app.py
Then your browser opens at http://localhost:8501

It has two tabs:
  1. "Try a real example"  -- pick a real ECG window from the D1NAMO data; see the three
     models' predictions, the Choquet fusion, and the TRUE glucose side by side.
  2. "Upload an ECG window" -- upload a CSV with an `EcgWaveform` column; the app cleans it,
     extracts the 80 paper features, and predicts the glucose.
"""

from __future__ import annotations

import os

import joblib
import numpy as np
import pandas as pd
import streamlit as st

from src.d1namo import _BP_B, _BP_A, FS, WINDOW_SAMPLES, DATA_ROOT
from src.features_temporal import extract_temporal_features
from scipy.signal import filtfilt

MODEL_PATH = "bg_model.pkl"
CACHE_PATH = os.path.join(DATA_ROOT, "features_temporal.csv")

st.set_page_config(page_title="Noninvasive Blood Glucose (Choquet fusion)", layout="wide")


# ----------------------------------------------------------------------------------
# Load the trained model once (cached by Streamlit so it doesn't reload every click).
# ----------------------------------------------------------------------------------
@st.cache_resource
def load_bundle():
    if not os.path.exists(MODEL_PATH):
        return None
    return joblib.load(MODEL_PATH)


@st.cache_data
def load_cache():
    if not os.path.exists(CACHE_PATH):
        return None
    return pd.read_csv(CACHE_PATH)


bundle = load_bundle()

st.title("🩸 Noninvasive Blood Glucose Monitoring")
st.caption("Random Forest + Gradient Boosting + Bagging → **Choquet integral fusion** → BG output "
           "(reproduction of Li et al., 2024, on the D1NAMO ECG dataset)")

if bundle is None:
    st.error("No trained model found. Please run **`python train.py`** first to create "
             "`bg_model.pkl`.")
    st.stop()

model = bundle["model"]
feature_names = bundle["feature_names"]

# ---- sidebar: what's inside the model ----------------------------------------------
with st.sidebar:
    st.header("About this model")
    st.metric("Hold-out RMSE", f"{bundle['metrics']['rmse']:.2f} mmol/L")
    st.metric("Hold-out MARD", f"{bundle['metrics']['mard']:.1f} %")
    st.write(f"**Trained on:** {bundle['n_samples']} ECG windows "
             f"from {bundle['n_patients']} patients")
    st.write(f"**Glucose range seen:** {bundle['glucose_min']:.1f}–{bundle['glucose_max']:.1f} mmol/L")
    st.divider()
    st.subheader("Choquet fusion settings")
    for name, d in zip(model.model_names_, bundle["densities"]):
        st.write(f"density({name}) = **{d:.3f}**")
    st.write(f"λ (interaction) = **{bundle['lambda']:.3f}**")
    st.caption("λ < 0 means the models are treated as partly redundant (no double-counting).")


def show_prediction(feature_row: pd.DataFrame, true_glucose: float | None = None):
    """Run the model on one feature row and display the breakdown."""
    preds = model.predict_all(feature_row)        # dict of every method's prediction

    # The headline number.
    fused = float(preds["Choquet"][0])
    c1, c2 = st.columns(2)
    c1.metric("Predicted blood glucose (Choquet fusion)", f"{fused:.2f} mmol/L")
    if true_glucose is not None:
        err = abs(fused - true_glucose)
        c2.metric("Actual (reference)", f"{true_glucose:.2f} mmol/L",
                  delta=f"{fused - true_glucose:+.2f} error")

    # The breakdown: each model vs the fusion.
    st.subheader("How each model voted, and how Choquet fused them")
    rows = []
    for name in model.model_names_ + ["PlainAverage", "WeightedAverage", "Choquet"]:
        rows.append({"method": name, "prediction (mmol/L)": float(preds[name][0])})
    breakdown = pd.DataFrame(rows).set_index("method")
    st.bar_chart(breakdown)
    st.dataframe(breakdown, use_container_width=True)


tab1, tab2 = st.tabs(["1) Try a real example", "2) Upload an ECG window"])

# ---- TAB 1: pick a real example from the dataset -----------------------------------
with tab1:
    cache = load_cache()
    if cache is None:
        st.warning("Feature cache not found yet. Run the extraction "
                   "(`python -m src.d1namo`) or wait for it to finish.")
    else:
        st.write("Pick a real ECG window that was recorded from a patient, and see what the "
                 "model predicts versus the glucose the CGM device actually measured.")
        patients = sorted(cache["subject"].astype(str).unique())
        patient = st.selectbox("Patient", patients)
        subset = cache[cache["subject"].astype(str) == patient].reset_index(drop=True)
        idx = st.slider("Which window (reading) for this patient?", 0, len(subset) - 1, 0)

        row = subset.iloc[[idx]]
        true_g = float(row["glucose"].iloc[0])
        feats = row[feature_names]                 # just the 80 feature columns, in order
        show_prediction(feats, true_glucose=true_g)

# ---- TAB 2: upload your own ECG window ---------------------------------------------
with tab2:
    st.write("Upload a CSV with an **`EcgWaveform`** column (a strip of ECG at 250 Hz). "
             f"The app uses the last {WINDOW_SAMPLES} samples (~16 s), cleans them, extracts "
             "the 80 features, and predicts glucose.")
    up = st.file_uploader("ECG CSV", type=["csv"])
    if up is not None:
        df = pd.read_csv(up)
        if "EcgWaveform" not in df.columns:
            st.error("That CSV has no `EcgWaveform` column.")
        elif len(df) < WINDOW_SAMPLES:
            st.error(f"Need at least {WINDOW_SAMPLES} samples; got {len(df)}.")
        else:
            raw = df["EcgWaveform"].to_numpy(dtype=float)[-WINDOW_SAMPLES:]
            cleaned = filtfilt(_BP_B, _BP_A, raw)          # Level-1 band-pass filter
            st.line_chart(pd.DataFrame({"cleaned ECG": cleaned}))
            feats_dict = extract_temporal_features(cleaned, FS)
            feats = pd.DataFrame([feats_dict])[feature_names]
            show_prediction(feats, true_glucose=None)
