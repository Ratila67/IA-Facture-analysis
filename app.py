import glob
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st

from main import analyze_and_match_receipt

RECEIPTS_GLOB = "dataset/receipts/*.jpg"


def format_money(amount: Any, currency: str) -> str:
    if amount is None:
        return "-"
    return f"{amount} {currency or ''}".strip()


def list_receipt_paths() -> List[str]:
    return sorted(glob.glob(RECEIPTS_GLOB))


def render_styles() -> None:
    st.markdown(
        """
        <style>
            .stApp {
                background: radial-gradient(circle at top right, #18142d, #0d1021 45%, #0a0c17);
                color: #eef2ff;
            }
            .hero {
                padding: 1rem 1.2rem;
                border-radius: 16px;
                background: linear-gradient(120deg, rgba(123,97,255,.35), rgba(67,233,123,.18));
                border: 1px solid rgba(255,255,255,.12);
                margin-bottom: 1rem;
            }
            .glass-card {
                border-radius: 14px;
                padding: 1rem;
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255,255,255,.14);
                margin-bottom: 0.8rem;
            }
            .kpi {
                border-radius: 12px;
                padding: 0.8rem;
                background: rgba(0, 0, 0, 0.18);
                border: 1px solid rgba(255,255,255,.12);
                text-align: center;
            }
            .ok-badge {
                color: #a7f3d0;
                font-weight: 700;
            }
            .warn-badge {
                color: #fde68a;
                font-weight: 700;
            }
            .err-badge {
                color: #fca5a5;
                font-weight: 700;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_matching_status(match_strategy: str) -> None:
    if match_strategy == "amount_and_currency":
        label = "Match fort: montant + devise"
        css_class = "ok-badge"
    elif match_strategy == "amount_only":
        label = "Match partiel: montant uniquement"
        css_class = "warn-badge"
    else:
        label = "Aucun match trouve"
        css_class = "err-badge"

    st.markdown(
        f"""
        <div class="glass-card">
            <span class="{css_class}">{label}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_matches_table(matches: List[Dict[str, Any]]) -> None:
    if not matches:
        st.info("Aucune transaction correspondante dans les releves.")
        return

    rows = []
    for tx in matches:
        rows.append(
            {
                "date": tx.get("date"),
                "amount": tx.get("amount"),
                "currency": tx.get("currency"),
                "vendor": tx.get("vendor"),
                "statement_file": tx.get("statement_file"),
                "currency_match": "oui" if tx.get("currency_match") else "non",
            }
        )

    st.dataframe(rows, use_container_width=True, hide_index=True)


def main() -> None:
    st.set_page_config(page_title="Receipt Matcher Studio", page_icon="🧾", layout="wide")
    render_styles()

    st.markdown(
        """
        <div class="hero">
            <h2 style="margin:0;">Receipt Matcher Studio</h2>
            <p style="margin:0.3rem 0 0 0;">
                Selectionne un ticket, lance l'analyse IA, et verifie le rapprochement bancaire en un clic.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    receipt_paths = list_receipt_paths()
    if not receipt_paths:
        st.error("Aucun receipt trouve dans dataset/receipts.")
        return

    with st.sidebar:
        st.header("Controle")
        selected_receipt = st.selectbox(
            "Choisis un receipt",
            options=receipt_paths,
            format_func=lambda p: Path(p).name,
        )
        run_analysis = st.button("Analyser maintenant", type="primary", use_container_width=True)

    left_col, right_col = st.columns([1.1, 1.4])

    with left_col:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("Apercu ticket")
        st.image(selected_receipt, use_container_width=True, caption=Path(selected_receipt).name)
        st.markdown("</div>", unsafe_allow_html=True)

    if run_analysis:
        with st.spinner("Analyse IA en cours..."):
            result = analyze_and_match_receipt(selected_receipt)
        st.session_state["last_result"] = result
        st.session_state["last_receipt"] = selected_receipt

    with right_col:
        result = st.session_state.get("last_result")
        last_receipt = st.session_state.get("last_receipt")

        if not result or last_receipt != selected_receipt:
            st.info("Clique sur 'Analyser maintenant' pour lancer le matching.")
            return

        receipt_data = result["receipt_analysis"]
        matching_data = result["matching"]
        matches = matching_data["matched_transactions"]

        st.subheader("Resultats")

        kpi_col_1, kpi_col_2, kpi_col_3 = st.columns(3)
        with kpi_col_1:
            st.markdown(
                f'<div class="kpi"><div>Total TTC</div><h3>{format_money(receipt_data.get("total_ttc"), receipt_data.get("currency"))}</h3></div>',
                unsafe_allow_html=True,
            )
        with kpi_col_2:
            st.markdown(
                f'<div class="kpi"><div>Marchand</div><h3>{receipt_data.get("merchant") or "-"}</h3></div>',
                unsafe_allow_html=True,
            )
        with kpi_col_3:
            st.markdown(
                f'<div class="kpi"><div>Transactions trouvees</div><h3>{matching_data.get("matched_count", 0)}</h3></div>',
                unsafe_allow_html=True,
            )

        render_matching_status(matching_data.get("match_strategy", "none"))

        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("**Transactions bancaires correspondantes**")
        render_matches_table(matches)
        st.markdown("</div>", unsafe_allow_html=True)

        with st.expander("Voir le JSON complet"):
            st.json(result)


if __name__ == "__main__":
    main()
