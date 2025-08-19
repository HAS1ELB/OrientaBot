import os
import streamlit as st
from typing import Dict, Any, List, Optional

from src.config import AppConfig
from src.groq_client import GroqChatClient
from src.prompts import build_messages
from src.domain import BAC_TRACKS, FIELDS, CATEGORIES_ECOLES, build_profile_summary, suggested_fields_for_track, month_timeline_generic
from src.utils import clamp_float, extract_json_block, safe_float, trim_history

# ---------------------
# Initialisation
# ---------------------
st.set_page_config(page_title="OrientaBot (Maroc)", page_icon="🎓", layout="wide")
with open("src/styles.css", "r", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

config = AppConfig()
if not config.is_configured:
    st.error("GROQ_API_KEY manquant. Configurez votre .env.")
    st.stop()

if "profile" not in st.session_state:
    st.session_state.profile = {
        "name": "",
        "track": "",
        "avg": "",
        "subjects": {"Maths": "", "Physique": "", "SVT": "", "Français": "", "Anglais": ""},
        "city": "",
        "languages": ["Français"],
        "interests": [],
        "budget": "",
        "mobility": "",
        "constraints": ""
    }

if "history" not in st.session_state:
    st.session_state.history = []  # List[{"role":"user"/"assistant","content": "..."}]

if "last_json" not in st.session_state:
    st.session_state.last_json = None

if "temperature" not in st.session_state:
    st.session_state.temperature = 0.4

client = GroqChatClient(api_key=config.groq_api_key, model=config.groq_model)

# ---------------------
# Sidebar: Profil
# ---------------------
with st.sidebar:
    st.header("🧑‍🎓 Profil élève")
    name = st.text_input("Nom (optionnel)", value=st.session_state.profile.get("name", ""))
    track = st.selectbox("Filière du Bac", options=[""] + BAC_TRACKS, index=0)
    col1, col2 = st.columns(2)
    with col1:
        avg = st.text_input("Moyenne générale (ex: 14.5)", value=str(st.session_state.profile.get("avg", "")))
        city = st.text_input("Ville", value=st.session_state.profile.get("city", ""))
    with col2:
        budget = st.selectbox("Budget/Préférence", ["", "Public", "Privé", "Limité"], index=0)
        mobility = st.selectbox("Mobilité", ["", "Même ville", "Nationale", "Ouverte"], index=0)

    st.markdown("Notes par matière (optionnel):")
    c1, c2, c3 = st.columns(3)
    with c1:
        s_maths = st.text_input("Maths", value=st.session_state.profile["subjects"].get("Maths", ""))
        s_phys = st.text_input("Physique", value=st.session_state.profile["subjects"].get("Physique", ""))
    with c2:
        s_svt = st.text_input("SVT", value=st.session_state.profile["subjects"].get("SVT", ""))
        s_fr = st.text_input("Français", value=st.session_state.profile["subjects"].get("Français", ""))
    with c3:
        s_en = st.text_input("Anglais", value=st.session_state.profile["subjects"].get("Anglais", ""))

    languages = st.multiselect("Langues", ["Français", "Arabe", "Anglais", "Espagnol"], default=st.session_state.profile.get("languages", ["Français"]))
    interests = st.multiselect("Intérêts", FIELDS, default=st.session_state.profile.get("interests", []))
    constraints = st.text_area("Contraintes (ex: bourse, travail, santé…)", value=st.session_state.profile.get("constraints", ""))

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.subheader("⚙️ Paramètres")
    temperature = st.slider("Créativité (temperature)", min_value=0.0, max_value=1.0, value=st.session_state.temperature, step=0.05)

    if st.button("💾 Enregistrer le profil"):
        st.session_state.profile["name"] = name.strip()
        st.session_state.profile["track"] = track.strip()
        st.session_state.profile["avg"] = avg.strip()
        st.session_state.profile["subjects"] = {"Maths": s_maths.strip(), "Physique": s_phys.strip(), "SVT": s_svt.strip(), "Français": s_fr.strip(), "Anglais": s_en.strip()}
        st.session_state.profile["city"] = city.strip()
        st.session_state.profile["languages"] = languages
        st.session_state.profile["interests"] = interests
        st.session_state.profile["budget"] = budget.strip()
        st.session_state.profile["mobility"] = mobility.strip()
        st.session_state.profile["constraints"] = constraints.strip()
        st.session_state.temperature = temperature
        st.success("Profil mis à jour ✅")

    if st.button("🧹 Réinitialiser le chat"):
        st.session_state.history = []
        st.session_state.last_json = None
        st.experimental_rerun()

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.caption("Astuce: plus votre profil est précis, plus les recommandations seront pertinentes.")

# ---------------------
# Main: Chat UI
# ---------------------
st.title("🎓 OrientaBot – Conseiller d’orientation (Maroc)")
st.write("Discutons de ton projet d’études supérieures. Renseigne ton profil dans la barre latérale pour des conseils personnalisés.")

# Affichage du résumé du profil
with st.expander("Résumé du profil"):
    st.write(build_profile_summary(st.session_state.profile))
    if st.session_state.profile.get("track"):
        suggested = suggested_fields_for_track(st.session_state.profile["track"])
        if suggested:
            st.markdown("Suggestions de domaines (selon filière): " + ", ".join([f"`{d}`" for d in suggested]))

# Afficher historique
for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
user_input = st.chat_input("Écris ton message (ex: 'Voici mes notes et ce que j'aime...')")
if user_input:
    st.session_state.history.append({"role": "user", "content": user_input})

    # Préparer messages pour Groq
    trimmed = trim_history(st.session_state.history, max_messages=20)
    include_few_shots = True if len(st.session_state.history) <= 4 else False  # injecter few-shots au début seulement
    messages = build_messages(
        history=trimmed,
        profile=st.session_state.profile,
        locale=config.default_lang,
        include_few_shots=include_few_shots
    )

    with st.chat_message("assistant"):
        # Streaming de la réponse
        placeholder = st.empty()
        collected = []

        try:
            def _stream():
                for chunk in client.stream_chat(messages, temperature=st.session_state.temperature):
                    collected.append(chunk)
                    yield chunk

            streamed_text = st.write_stream(_stream())
            final_text = "".join(collected)
            st.session_state.history.append({"role": "assistant", "content": final_text})

            # Essayer d'extraire le JSON machine-readable
            js = extract_json_block(final_text)
            if js:
                st.session_state.last_json = js
                with st.expander("JSON machine-readable extrait"):
                    st.json(js)
        except Exception as e:
            err = f"Une erreur est survenue: {e}"
            st.error(err)
            st.session_state.history.append({"role": "assistant", "content": err})

# Footer
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
c1, c2 = st.columns([2,1])
with c1:
    st.caption("Important: Les procédures d’admission et calendriers évoluent chaque année. Vérifiez toujours les informations sur les sites officiels des établissements et du Ministère.")
with c2:
    if st.session_state.last_json:
        st.download_button(
            "Télécharger recommandations (JSON)",
            data=str(st.session_state.last_json),
            file_name="recommandations_orientabot.json",
            mime="application/json"
        )