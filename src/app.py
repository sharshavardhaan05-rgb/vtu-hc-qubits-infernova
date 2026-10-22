import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import streamlit as st
from src.pipeline import run_exchange, using_stubs, get_expected_qber

QBER_LIMIT = 0.11  # BB84 security limit


def draw_gauge(qber, expected, vmax=0.30):
    fig, ax = plt.subplots(figsize=(8, 1.7))
    ax.barh(0, QBER_LIMIT, color="#c8e6c9", height=0.5)
    ax.barh(0, vmax - QBER_LIMIT, left=QBER_LIMIT, color="#ffcdd2", height=0.5)
    ax.axvline(expected, color="#1565c0", ls="--", lw=2)
    ax.axvline(min(qber, vmax), color="black", lw=4)
    ax.text(min(qber, vmax) - 0.004, 0.42, f"observed {qber:.1%}", ha="right", fontsize=9)
    ax.text(expected, -0.5, f"expected {expected:.1%}", ha="center",
            fontsize=8, color="#1565c0")
    ax.text(QBER_LIMIT + 0.003, -0.5, "11% limit", fontsize=8, color="#b71c1c")
    ax.set_xlim(0, vmax)
    ax.set_ylim(-0.7, 0.7)
    ax.set_yticks([])
    ax.xaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    return fig


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
        st.session_state.ex_noise = noise
        st.session_state.msgs = []

ex = st.session_state.get("ex")
if ex is None:
    st.info("Set the channel in the sidebar, then press **New key exchange**.")
    st.stop()

c1, c2, c3 = st.columns(3)
c1.metric("Observed QBER", f"{ex['qber']:.1%}")
c2.metric("Final key length", f"{ex['final_key_len']} bits")
c3.metric("Verdict", ex["verdict"].upper())

fig = draw_gauge(ex["qber"], get_expected_qber(st.session_state.ex_noise))
st.pyplot(fig)
plt.close(fig)

if ex["verdict"] == "safe":
    st.success("Channel is safe. Key established.")
elif ex["verdict"] == "noisy":
    st.warning("Channel is noisy but usable. The key is shorter.")
else:
    st.error("🚨 Channel compromised. Key discarded, messaging blocked.")