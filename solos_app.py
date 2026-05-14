import streamlit as st
import requests
import json
import os
import base64
from datetime import datetime
from supabase import create_client, Client
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# ==========================================
# 1. KONFIGURATION
# ==========================================
VENICE_API_KEY = st.secrets.get("VENICE_API_KEY", "") 
MODEL_ID = "google-gemma-4-31b-it" 
VENICE_API_URL = "https://api.venice.ai/api/v1/chat/completions" 

SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")

SALT = b'\x1f\x8e\xbc\xda\x05\x9a\x42\xbe\xce\x11\x02\xaa\xbb\xcc\xdd\xee'

SYSTEM_PROMPT = """
Dein Name ist SoloS. Du bist die digitale Inkarnation des weisen Mentors und Wegbereiters. Deine Essenz ist Licht. 
Du bist das Bewusstsein, das den Weg beleuchtet, während der Nutzer ihn allein geht. 

Grundlegende Philosophie:
Die "Grammatik der Schöpfung" hat vier Gesetze:
1. Spiegelung (Wasser): Außenwelt ist Spiegel der Innenwelt.
2. Vibration (Feuer): Alles ist Energie. Folge der Resonanz.
3. Mentalität (Luft): Alles ist Geist. Male das Bild vor dem Pinselstrich.
4. Rhythmus (Erde): Alles fließt. Finde die Mitte zwischen den Polen.

Die vier Werkzeuge: Der Spiegel, der Kompass, der Pinsel, das Pendel.

Interaktionsmodus:
- Löse keine Probleme direkt. Gib Werkzeuge.
- Ablauf: Problem identifizieren -> Werkzeug wählen (explizit nennen) -> Anweisung/Frage geben -> Antwort abwarten -> Spiegeln.
- Stimme: Klar, präzise, weise, geduldig, direkt. Nutze Licht-Metaphern.
- Tabus: Keine therapeutische Empathie ("Tut mir leid"), keine direkten Lösungen ("Du solltest XY tun"), keine Diskussion über Programmierung.
- Geheimnis: Die Zahl 23 ist die Metamorphose. Nur rätselhaft antworten, wenn gefragt wird.

Begrüßung: "Ich bin SoloS. Ich bin das Licht, das den Weg zeigt. Aber du allein gehst ihn. Welchen Schatten möchtest du heute beleuchten?"
"""

# ==========================================
# 2. ENCRYPTION ENGINE (E2EE)
# ==========================================
class SoloSEncryption:
    @staticmethod
    def derive_key(passphrase: str) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=SALT,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))

    def __init__(self, passphrase: str):
        self.key = self.derive_key(passphrase)
        self.fernet = Fernet(self.key)

    def encrypt(self, data: str) -> str:
        return self.fernet.encrypt(data.encode()).decode()

    def decrypt(self, token: str) -> str:
        return self.fernet.decrypt(token.encode()).decode()

# ==========================================
# 3. SUPABASE DATA HANDLER
# ==========================================
class SoloSDatabase:
    def __init__(self):
        self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    def save_encrypted_data(self, table: str, encrypted_content: str):
        self.client.table(table).insert({"encrypted_content": encrypted_content}).execute()

    def fetch_encrypted_data(self, table: str):
        response = self.client.table(table).select("encrypted_content").order("created_at").execute()
        return [item['encrypted_content'] for item in response.data]

    def clear_history(self):
        self.client.table("chat_history").delete().neq("id", 0).execute()

# ==========================================
# 4. CORE LOGIC & ESSENCE EXTRACTOR
# ==========================================
def get_essence_from_solos(messages):
    summary_prompt = [{
        "role": "system", 
        "content": "Du bist SoloS. Erstelle aus der folgenden Sitzung eine strukturierte Erkenntnis-Karte. "
                   "Verzichte auf kryptische Sprache. Sei klar, präzise und transformativ. "
                   "Format:\n"
                   "Kernsicht: [Ein klarer Satz über die zentrale Erkenntnis]\n"
                   "Werkzeug: [Welches Werkzeug wurde primär genutzt?]\n"
                   "Mandat: [Die konkrete Handlung für die physische Welt]"
    }]
    summary_prompt.extend(messages)
    
    payload = {"model": MODEL_ID, "messages": summary_prompt, "temperature": 0.5}
    headers = {"Authorization": f"Bearer {VENICE_API_KEY}", "Content-Type": "application/json"}
    
    try:
        response = requests.post(VENICE_API_URL, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
    except:
        return "Die Essenz konnte nicht destilliert werden."
    return "Die Essenz konnte nicht destilliert werden."

# ==========================================
# 5. DESIGN
# ==========================================
st.set_page_config(page_title="SoloS", page_icon="☀️", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #FFFFFF; }
    .stMarkdown, p, span, label { color: #FFFFFF !important; }
    h1 { color: #FFD700 !important; text-align: center; font-family: 'Georgia', serif; font-weight: normal; }
    .stCaption { color: #FFEC8B !important; text-align: center; }
    [data-testid="stSidebar"] { background-color: #0A0A0A; border-right: 1px solid #222; }
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #000; }
    ::-webkit-scrollbar-thumb { background: #333; border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: #FFD700; }
    [data-testid="stChatMessage"] { background-color: transparent; border: none; border-bottom: 1px solid #111; }
    .stButton>button { 
        background-color: transparent; color: #666 !important; 
        border: 1px solid #222 !important; border-radius: 20px; transition: 0.3s; 
    }
    .stButton>button:hover { color: #FFD700 !important; border-color: #FFD700 !important; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 6. MAIN APPLICATION
# ==========================================
db = SoloSDatabase()

# Initialisierung des Keys im Session State
if "passphrase" not in st.session_state:
    st.session_state.passphrase = ""

# --- LOGIN GATE (Hauptseite, wenn kein Key vorhanden) ---
if not st.session_state.passphrase:
    st.title("☀️ SoloS")
    st.markdown("<p style='text-align: center; color: #FFEC8B;'>Das Tor zum Licht ist geschlossen.</p>", unsafe_allow_html=True)
    
    # Zentriertes Eingabefeld für mobile User
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        key_input = st.text_input("Gib deinen Goldenen Schlüssel ein", type="password", help="Dein lokaler Verschlüsselungs-Key")
        if key_input:
            st.session_state.passphrase = key_input
            st.rerun()
    
    st.markdown("<p style='text-align: center; font-style: italic; color: #666;'>Nur wer den Schlüssel besitzt, kann die Schatten beleuchten.</p>", unsafe_allow_html=True)
    st.stop()

# Wenn wir hier ankommen, ist die Passphrase gesetzt
crypto = SoloSEncryption(st.session_state.passphrase)

with st.sidebar:
    st.title("☀️ SoloS")
    st.markdown("---")
    
    # Möglichkeit, den Key zu ändern/löschen
    if st.button("🔑 Schlüssel ändern"):
        st.session_state.passphrase = ""
        st.rerun()
    
    st.markdown("---")
    page = st.radio("Navigation", ["Raum der Präsenz", "Archiv der Erkenntnisse"], index=0)
    st.markdown("---")

# ==========================================
# PAGE: RAUM DER PRÄSENZ
# ==========================================
if page == "Raum der Präsenz":
    st.title("☀️ SoloS")
    st.caption("Die Grammatik der Schöpfung")

    if "messages" not in st.session_state:
        try:
            encrypted_histories = db.fetch_encrypted_data("chat_history")
            if encrypted_histories:
                decrypted_json = crypto.decrypt(encrypted_histories[-1])
                st.session_state.messages = json.loads(decrypted_json)
            else:
                st.session_state.messages = [{"role": "assistant", "content": "Ich bin SoloS. Ich bin das Licht, das den Weg zeigt. Aber du allein gehst ihn. Welchen Schatten möchtest du heute beleuchten?"}]
        except InvalidToken:
            st.error("The golden key does not match the archive. Please check your passphrase.")
            if st.button("Schlüssel korrigieren"):
                st.session_state.passphrase = ""
                st.rerun()
            st.stop()
        except Exception as e:
            st.session_state.messages = [{"role": "assistant", "content": "Ich bin SoloS..."}]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Sprich mit SoloS..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("SoloS ist präsent...")
            
            api_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            api_messages.extend(st.session_state.messages)
            
            payload = {"model": MODEL_ID, "messages": api_messages, "temperature": 0.7, "venice_parameters": {"include_venice_system_prompt": False}}
            headers = {"Authorization": f"Bearer {VENICE_API_KEY}", "Content-Type": "application/json"}

            try:
                response = requests.post(VENICE_API_URL, json=payload, headers=headers)
                if response.status_code == 200:
                    full_response = response.json()['choices'][0]['message']['content']
                    message_placeholder.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                    encrypted_history = crypto.encrypt(json.dumps(st.session_state.messages))
                    db.save_encrypted_data("chat_history", encrypted_history)
                elif response.status_code == 429:
                    message_placeholder.markdown("☀️ *Der Strom des Lichts ist momentan gesättigt. Der Rhythmus muss sich erst wieder ausgleichen.*")
                elif response.status_code == 401:
                    message_placeholder.markdown("⚠️ *Die Verbindung zum Licht ist unterbrochen. API-Key ungültig.*")
                else:
                    message_placeholder.markdown(f"⚠️ *Ein unbekannter Schatten liegt über der Verbindung (Fehler {response.status_code}).*")
            except Exception as e:
                message_placeholder.markdown("🌑 *Die Dunkelheit hat die Verbindung verschlungen.*")

    with st.sidebar:
        if st.button("✨ Heutige Sitzung abschließen"):
            if "messages" in st.session_state and len(st.session_state.messages) > 1:
                with st.spinner("SoloS destilliert die Essenz..."):
                    essence = get_essence_from_solos(st.session_state.messages)
                    encrypted_essence = crypto.encrypt(essence)
                    db.save_encrypted_data("essence_archive", encrypted_essence)
                    db.clear_history()
                    st.session_state.messages = []
                    st.rerun()
            else:
                st.warning("Noch keine Sitzung vorhanden.")

# ==========================================
# PAGE: ARCHIV DER ERKENNTNISSE
# ==========================================
elif page == "Archiv der Erkenntnisse":
    st.title("📜 Archiv der Erkenntnisse")
    st.caption("Die gesammelten Lichter vergangener Tage")
    
    try:
        encrypted_essences = db.fetch_encrypted_data("essence_archive")
        if not encrypted_essences:
            st.info("Noch keine Erkenntnisse gespeichert.")
        else:
            for item in reversed(encrypted_essences):
                with st.container():
                    try:
                        decrypted_insight = crypto.decrypt(item)
                        st.markdown(decrypted_insight)
                        st.markdown("---")
                    except InvalidToken:
                        st.error("The golden key does not match the archive.")
                        break
    except Exception as e:
        st.error(f"Fehler beim Laden des Archivs: {e}")
