import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root

import streamlit as st
from src.pipeline import run_exchange, using_stubs

st.set_page_config(page_title="QuantaGuard Chat", page_icon="🛡️", layout="wide")
st.title("🛡️ QuantaGuard Chat")
st.caption("BB84 quantum key exchange → AES-GCM encrypted chat")

stubbed = using_stubs()
if stubbed:
    st.warning("Demo mode: stub versions in use for " + ", ".join(stubbed))

with st.sidebar:
    st.header("Channel")
    noise = st.slider("Noise level", 0.0, 1.0, 0.1, 0.05)
    eve = st.toggle("Eve is listening (intercept-resend)", value=False)
    if st.button("🔑 New key exchange", type="primary", use_container_width=True):
        st.session_state.ex = run_exchange(noise, eve)
        st.session_state.msgs = []

ex = st.session_state.get("ex")
if ex is None:
    st.info("Set the channel in the sidebar, then press **New key exchange**.")
    st.stop()

c1, c2, c3 = st.columns(3)
c1.metric("Observed QBER", f"{ex['qber']:.1%}")
c2.metric("Final key length", f"{ex['final_key_len']} bits")
c3.metric("Verdict", ex["verdict"].upper())

if ex["verdict"] == "safe":
    st.success("Channel is safe. Key established.")
elif ex["verdict"] == "noisy":
    st.warning("Channel is noisy but usable. The key is shorter.")
else:
    st.error("🚨 Channel compromised. Key discarded, messaging blocked.")