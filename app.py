import pandas as pd
import streamlit as st

st.set_page_config(page_title="NIDS Dashboard", layout="wide")


@st.cache_data
def load():
    return (
        pd.read_csv("model_results.csv"),
        pd.read_csv("detection_by_attack_type.csv"),
        pd.read_csv("feature_importance.csv"),
        pd.read_csv("test_predictions.csv"),
    )


results, by_type, imp, preds = load()

st.title("Network intrusion detection on NSL-KDD")
st.caption("Machine learning models that classify network connections as normal or attack, evaluated on the NSL-KDD test set.")

# headline numbers for the best model
best = results[results["Model"] == "XGBoost"].iloc[0]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Accuracy", f"{best['Accuracy']:.1%}")
c2.metric("Attack precision", f"{best['Precision']:.1%}")
c3.metric("Attack recall", f"{best['Recall']:.1%}")
c4.metric("False alarm rate", f"{best['False alarm rate']:.1%}")
st.caption("Figures are for XGBoost, the best of the three models.")

# model comparison
st.header("Model comparison")
left, right = st.columns(2)
left.dataframe(results, hide_index=True)
right.bar_chart(results.set_index("Model")[["Precision", "Recall", "F1"]], stack=False)

# detection by attack type
st.header("Detection rate by attack type")
st.write("Flooding and scanning attacks are caught almost perfectly. Attack types that are rare or missing in the training data are where the model fails.")
min_rows = st.slider("Only show attack types with at least this many test rows", 0, 1000, 100, step=50)
shown = by_type[by_type["test_rows"] >= min_rows].copy()
shown["In training data"] = shown["seen_in_training"].map({True: "Seen in training", False: "Not in training"})
st.bar_chart(shown, x="label", y="detection_rate", color="In training data")
st.caption("A missing bar means none of that attack type was detected.")

# feature importance
st.header("Most important features")
import altair as alt
chart = alt.Chart(imp.head(15)).mark_bar().encode(
    x=alt.X("importance:Q", title="Importance"),
    y=alt.Y("feature:N", sort="-x", title=None),
)
st.altair_chart(chart, use_container_width=True)

# explore the predictions
st.header("Explore individual connections")
labels = ["All"] + sorted(preds["label"].unique().tolist())
choice = st.selectbox("Traffic type", labels)
only_missed = st.checkbox("Show only attacks the model missed")

view = preds.copy()
if choice != "All":
    view = view[view["label"] == choice]
if only_missed:
    view = view[(view["target"] == 1) & (view["xgb_pred"] == 0)]

st.write(f"{len(view):,} connections")
cols = ["label", "protocol_type", "service", "flag", "src_bytes", "dst_bytes", "xgb_proba", "correct"]
st.dataframe(view[cols].head(500), hide_index=True)
