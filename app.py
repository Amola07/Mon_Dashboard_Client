import pandas as pd
import streamlit as st
import plotly.express as px
from streamlit_lottie import st_lottie
import requests
import base64
from io import BytesIO

# --- Configuration de la page ---
st.set_page_config(page_title="Dashboard Client", layout="wide")

# --------------------- UTILITAIRES ---------------------
@st.cache_data
def load_lottie_url(url: str):
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None

def get_base64(file_path):
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def set_background(image_path):
    encoded_image = get_base64(image_path)
    st.markdown(f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpg;base64,{encoded_image}");
            background-size: cover;
            background-attachment: fixed;
            background-position: center;
            color: #ffffff;
        }}
        .main-title {{
            font-size: 3rem;
            font-weight: 800;
            color: #00ffcc;
            text-shadow: 1px 1px 3px black;
            margin-bottom: 20px;
        }}
        .section-title {{
            font-size: 1.8rem;
            font-weight: 600;
            margin-top: 40px;
            color: #ffffff;
            text-shadow: 1px 1px 2px black;
        }}
        .highlight-box {{
            background-color: rgba(0, 0, 0, 0.5);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 25px;
        }}
        ul li {{
            padding: 5px 0;
        }}
        </style>
    """, unsafe_allow_html=True)

def generate_excel(df, sheet_name="Sheet1"):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    output.seek(0)
    return output

# --------------------- DONNÉES DÉMO ---------------------
sample_data = pd.DataFrame({
    "Client": [
        "Entreprise Alpha", "Société Beta", "Groupe Gamma",
        "SARL Delta", "Holding Epsilon", "Agence Zeta",
        "Industrie Eta", "Entreprise Theta", "Groupe Iota", "SARL Kappa"
    ],
    "Quantity": [120, 85, 150, 95, 110, 80, 135, 90, 100, 75],
    "Total Price": [12000, 8500, 15000, 9500, 11000, 8000, 13500, 9000, 10000, 7500]
})

# --------------------- AFFICHAGE ---------------------
set_background("background.jpg")
st.markdown('<h1 class="main-title">📊 Dashboard Client Personnalisable</h1>', unsafe_allow_html=True)

# Animation
lottie_url = "https://assets10.lottiefiles.com/packages/lf20_jcikwtux.json"
lottie_client = load_lottie_url(lottie_url)
if lottie_client:
    st_lottie(lottie_client, speed=1, loop=True, height=300, key="client_intro")

# Introduction
st.markdown("""
<div class="highlight-box">
    <h4 style="color: #00ffcc;">🛠️ Ce que vous pouvez faire avec ce dashboard :</h4>
    <ul>
        <li>📈 <strong>Analyser les performances de vos meilleurs clients</strong></li>
        <li>💰 Identifier les gros acheteurs et la valeur moyenne de commande</li>
        <li>📊 Visualiser les résultats avec des <strong>graphiques interactifs</strong></li>
        <li>📥 Télécharger un <strong>fichier modèle</strong> pour importer vos données</li>
        <li>📤 Intégrer facilement vos ventes Excel</li>
        <li>📧 Obtenir un <strong>dashboard personnalisé</strong> sur demande</li>
    </ul>
    <p style='color: #ccc;'>Adapté aux commerçants, entrepreneurs et indépendants.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("## 🧭 Étapes à suivre")
st.markdown("1. 📄 **Téléchargez le modèle Excel**\n2. 📤 **Importez votre propre fichier**")

# Téléchargement modèle
st.download_button(
    label="📄 Télécharger le fichier modèle",
    data=generate_excel(sample_data, "Modèle"),
    file_name="modele_ventes.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# Upload fichier utilisateur
st.markdown("### 📤 Importez vos données")
uploaded_file = st.file_uploader("Fichier Excel (.xlsx)", type=["xlsx"])

# --------------------- TRAITEMENT DONNÉES ---------------------
if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        required_cols = {"Client", "Quantity", "Total Price"}
        if required_cols.issubset(df.columns):

            top_clients = (
                df.groupby("Client")
                  .agg(
                      total_spent=pd.NamedAgg(column="Total Price", aggfunc="sum"),
                      average_order_value=pd.NamedAgg(column="Total Price", aggfunc="mean"),
                      number_of_purchases=pd.NamedAgg(column="Total Price", aggfunc="count"),
                      total_quantity=pd.NamedAgg(column="Quantity", aggfunc="sum"),
                  )
                  .sort_values(by="total_spent", ascending=False)
                  .head(10)
                  .reset_index()
            )

            st.markdown('<h2 class="section-title">🏆 Top 10 Clients</h2>', unsafe_allow_html=True)

            col1, col2 = st.columns([2, 1])
            with col1:
                st.dataframe(top_clients.style.format({
                    "total_spent": "€{:.2f}",
                    "average_order_value": "€{:.2f}",
                }).highlight_max(color='darkblue'))

            with col2:
                st.metric("💶 Total Dépensé", f"{top_clients['total_spent'].sum():,.2f} €")
                st.metric("👥 Nombre de Clients", f"{top_clients.shape[0]}")

            # Graphiques
            st.markdown('<h2 class="section-title">📈 Total Dépensé par Client</h2>', unsafe_allow_html=True)
            st.plotly_chart(px.bar(
                top_clients, x='total_spent', y='Client',
                orientation='h', text='total_spent',
                labels={'total_spent': 'Total (€)', 'Client': 'Client'},
                color='total_spent', color_continuous_scale='Agsunset',
                template='plotly_dark'
            ).update_layout(yaxis={'categoryorder': 'total ascending'}), use_container_width=True)

            st.markdown('<h2 class="section-title">🥧 Répartition des Dépenses</h2>', unsafe_allow_html=True)
            st.plotly_chart(px.pie(
                top_clients, names='Client', values='total_spent',
                title='Part des Dépenses par Client',
                color_discrete_sequence=px.colors.sequential.RdBu
            ).update_traces(textposition='inside', textinfo='percent+label'), use_container_width=True)

            st.download_button(
                label="📥 Télécharger les résultats",
                data=generate_excel(top_clients, "Top Clients").getvalue(),
                file_name="top_clients.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        else:
            st.error("❌ Le fichier doit contenir : Client, Quantity, Total Price.")
    except Exception as e:
        st.error(f"❌ Erreur lors de la lecture du fichier : {e}")

# --------------------- FAQ ---------------------
st.markdown('<h2 class="section-title">❓ FAQ</h2>', unsafe_allow_html=True)
with st.expander("➡️ Que faire si mon fichier n'est pas accepté ?"):
    st.write("Assurez-vous qu’il contient bien les colonnes `Client`, `Quantity`, `Total Price`.")

with st.expander("➡️ Puis-je utiliser un CSV ?"):
    st.write("Pas pour l’instant. Le support CSV est prévu dans une future mise à jour.")

with st.expander("➡️ Mes données sont-elles stockées ?"):
    st.write("Non. Tout reste en local sur votre session Streamlit.")

# --------------------- CONTACT ---------------------
st.markdown('<h2 class="section-title">📬 Contact</h2>', unsafe_allow_html=True)
with st.form("contact_form"):
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Votre nom")
        email = st.text_input("Votre adresse e-mail")
    with col2:
        company = st.text_input("Entreprise (facultatif)")
        phone = st.text_input("Numéro WhatsApp (facultatif)")

    message = st.text_area("Votre message")
    submitted = st.form_submit_button("Envoyer")

    if submitted and name and email and message:
        whatsapp_number = "+22957074157"
        full_message = f"""
Bonjour ! Je m'appelle {name} ({email}){" de " + company if company else ""}.
Je suis intéressé par votre dashboard client personnalisable.
Voici mon message :
{message}
""".strip().replace('\n', '%0A')

        whatsapp_url = f"https://wa.me/{whatsapp_number}?text={full_message.replace(' ', '%20')}"
        st.success("✅ Cliquez ci-dessous pour nous contacter sur WhatsApp.")
        st.markdown(f'<a href="{whatsapp_url}" target="_blank"><button style="background-color:#25D366;color:white;padding:10px 20px;border:none;border-radius:8px;font-size:16px;">📱 Envoyer sur WhatsApp</button></a>', unsafe_allow_html=True)
    elif submitted:
        st.warning("⚠️ Merci de remplir au moins votre nom, votre e-mail et le message.")

# --------------------- TÉMOIGNAGES ---------------------
st.markdown('<h2 class="section-title">💬 Témoignages</h2>', unsafe_allow_html=True)
st.markdown("""
> 🗣️ *"Simple, rapide et très utile pour visualiser mes meilleurs clients."* — **Sarah K.**  
> 🗣️ *"La visualisation est top ! Je recommande."* — **Marc D.**  
> 🗣️ *"Enfin un outil sans inscription et respectueux de mes données."* — **Julie R.**
""")
