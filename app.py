import pandas as pd
import streamlit as st
import plotly.express as px
from streamlit_lottie import st_lottie
import requests
import base64
from io import BytesIO

def load_lottie_url(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()


# --- Config de la page ---
st.set_page_config(page_title="Dashboard Client", layout="wide")

# --- Fonction pour fond d'écran ---
def get_base64(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_background(image_path):
    encoded_image = get_base64(image_path)
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpg;base64,{encoded_image}");
            background-size: cover;
            background-attachment: fixed;
            background-position: center;
            color: #ffffff;
        }}
        .main-title {{
            font-size: 48px;
            font-weight: bold;
            color: #00ffcc;
            text-shadow: 1px 1px 3px black;
        }}
        .section-title {{
            font-size: 28px;
            font-weight: 600;
            margin-top: 40px;
            color: #ffffff;
            text-shadow: 1px 1px 2px black;
        }}
        .faq {{
            background-color: rgba(0, 0, 0, 0.5);
            border-radius: 8px;
            padding: 15px;
            margin-top: 30px;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# --- Appliquer fond ---
set_background("background.jpg")

# --- Titre principal ---
st.markdown('<p class="main-title">📊 Dashboard Client Personnalisable</p>', unsafe_allow_html=True)

# --- Animation Lottie ---
lottie_client = load_lottie_url("https://assets10.lottiefiles.com/packages/lf20_jcikwtux.json")

st_lottie(
    lottie_client,
    speed=1,
    reverse=False,
    loop=True,
    quality="high",
    height=300,
    key="client_intro"
)

# --- Introduction enrichie ---
st.markdown("""
<div style='background-color: rgba(0, 0, 0, 0.5); padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
    <h4 style='color: #00ffcc;'>🛠️ Ce que vous pouvez faire avec ce dashboard :</h4>
    <ul style='color: white;'>
        <li>📈 <strong>Analyser les performances de vos meilleurs clients</strong> en un seul clic</li>
        <li>💰 Voir qui dépense le plus, combien de fois, et pour quel montant moyen</li>
        <li>📊 Visualiser les résultats avec des <strong>graphiques interactifs</strong> (camemberts, barres, etc.)</li>
        <li>📥 Télécharger un <strong>fichier Excel modèle</strong> pour faciliter l’importation</li>
        <li>📤 Importer facilement vos propres données de vente depuis Excel</li>
        <li>📧 Me contacter directement pour obtenir un <strong>dashboard personnalisé</strong> adapté à vos besoins</li>
    </ul>
    <p style='color: #cccccc;'>Que vous soyez commerçant, entrepreneur ou indépendant, ce tableau de bord est fait pour vous simplifier la vie et vous aider à prendre de meilleures décisions stratégiques.</p>
</div>
""", unsafe_allow_html=True)

st.write("Bienvenue ! Suivez les étapes ci-dessous pour analyser vos ventes :")

# --- Étapes à suivre ---
st.markdown("""
### 🧭 Étapes :
1. 📥 **Téléchargez le fichier modèle Excel** ci-dessous.
2. 📤 **Glissez-déposez votre fichier** ou importez-le via le sélecteur ci-dessous.
""")

# --- Fichier modèle à télécharger ---
sample_data = pd.DataFrame({
    "Client": [
        "Entreprise Alpha", "Société Beta", "Groupe Gamma",
        "SARL Delta", "Holding Epsilon", "Agence Zeta",
        "Industrie Eta", "Entreprise Theta", "Groupe Iota", "SARL Kappa"
    ],
    "Quantity": [120, 85, 150, 95, 110, 80, 135, 90, 100, 75],
    "Total Price": [12000, 8500, 15000, 9500, 11000, 8000, 13500, 9000, 10000, 7500]
})

def generate_excel_template(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Modèle')
    output.seek(0)
    return output

st.download_button(
    label="📄 Télécharger le fichier modèle",
    data=generate_excel_template(sample_data),
    file_name="modele_ventes.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# --- Téléversement du fichier rempli ---
st.markdown("### 📤 Téléversez votre fichier rempli ici :")
uploaded_file = st.file_uploader("Glissez-déposez ou cliquez pour importer un fichier Excel", type=["xlsx", "xls"])

# --- Traitement des données si le fichier est téléversé ---
if uploaded_file:
    df = pd.read_excel(uploaded_file)

    if {"Client", "Quantity", "Total Price"}.issubset(df.columns):
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

        st.markdown('<p class="section-title">🏆 Top 10 Clients</p>', unsafe_allow_html=True)

        col1, col2 = st.columns([2, 1])
        with col1:
            st.dataframe(top_clients.style.format({
                "total_spent": "€{:.2f}",
                "average_order_value": "€{:.2f}",
            }).highlight_max(color='darkblue'))

        with col2:
            st.metric("💶 Total Dépensé", f"{top_clients['total_spent'].sum():,.2f} €")
            st.metric("👥 Nombre de Clients", f"{top_clients.shape[0]}")

        # --- Graphique Barres ---
        st.markdown('<p class="section-title">📈 Total Dépensé par Client</p>', unsafe_allow_html=True)
        fig_bar = px.bar(
            top_clients,
            x='total_spent',
            y='Client',
            orientation='h',
            text='total_spent',
            labels={'total_spent': 'Total (€)', 'Client': 'Client'},
            color='total_spent',
            color_continuous_scale='Agsunset'
        )
        fig_bar.update_layout(yaxis={'categoryorder': 'total ascending'}, template="plotly_dark")
        st.plotly_chart(fig_bar, use_container_width=True)

        # --- Graphique Camembert ---
        st.markdown('<p class="section-title">🥧 Répartition des Dépenses</p>', unsafe_allow_html=True)
        fig_pie = px.pie(
            top_clients,
            names='Client',
            values='total_spent',
            title='Part des Dépenses par Client',
            color_discrete_sequence=px.colors.sequential.RdBu
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)

        # --- Export Excel Résultats ---
        def to_excel(df):
            output = BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False, sheet_name="Top Clients")
            output.seek(0)
            return output.getvalue()

        excel_data = to_excel(top_clients)
        st.download_button(
            label="📥 Télécharger les résultats (.xlsx)",
            data=excel_data,
            file_name="top_clients.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.error("❌ Le fichier doit contenir les colonnes : Client, Quantity, Total Price.")

# --- FAQ ---
st.markdown('<p class="section-title">❓ FAQ</p>', unsafe_allow_html=True)
with st.expander("➡️ Que faire si mon fichier n'est pas accepté ?"):
    st.markdown("""
    Vérifiez que votre fichier contient bien **les 3 colonnes suivantes** :
    - Client
    - Quantity
    - Total Price

    Vous pouvez utiliser le **fichier modèle fourni** pour éviter toute erreur.
    """)

with st.expander("➡️ Puis-je utiliser un fichier CSV ?"):
    st.markdown("Non. Actuellement, seuls les fichiers **Excel (.xlsx)** sont pris en charge. Le support des CSV viendra bientôt.")

with st.expander("➡️ Mes données sont-elles stockées quelque part ?"):
    st.markdown("Non. Toutes vos données restent **locales dans votre session** Streamlit et ne sont **jamais enregistrées**.")

with st.expander("➡️ Comment personnaliser l’analyse selon mes besoins ?"):
    st.markdown("Vous pouvez modifier le modèle ou contacter le développeur via la section ci-dessous pour des solutions sur-mesure.")

# --- Contact ---
st.markdown('<p class="section-title">📬 Contact</p>', unsafe_allow_html=True)
st.markdown("""
Vous avez une question, une demande spécifique ou vous souhaitez une **personnalisation du dashboard** ?
""")
# --- Section Contact ---
st.markdown('<p class="section-title">📞 Contactez-nous</p>', unsafe_allow_html=True)

with st.form("contact_form"):
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Votre nom")
        email = st.text_input("Votre adresse e-mail")
    with col2:
        company = st.text_input("Nom de votre entreprise (facultatif)")
        phone = st.text_input("Numéro WhatsApp (facultatif)")

    message = st.text_area("Votre message")

    submitted = st.form_submit_button("Envoyer")

    if submitted:
        if name and email and message:
            whatsapp_number = "+229 57074157"

            full_message = f"""
Bonjour ! Je m'appelle {name} ({email}){" de " + company if company else ""}.
Je suis intéressé par votre dashboard client personnalisable.
Voici mon message :
{message}
""".strip().replace('\n', '%0A')

            whatsapp_url = f"https://wa.me/{whatsapp_number}?text={full_message.replace(' ', '%20')}"

            st.success("✅ Merci ! Cliquez ci-dessous pour nous contacter sur WhatsApp.")
            st.markdown(f'<a href="{whatsapp_url}" target="_blank"><button style="background-color:#25D366;color:white;padding:10px 20px;border:none;border-radius:8px;font-size:16px;cursor:pointer;">📱 Envoyer sur WhatsApp</button></a>', unsafe_allow_html=True)
        else:
            st.warning("⚠️ Merci de remplir au moins votre nom, votre e-mail et le message.")

# --- Témoignages ---
st.markdown('<p class="section-title">💬 Témoignages</p>', unsafe_allow_html=True)
st.markdown("""
> 🗣️ *"Simple, rapide et très utile pour visualiser mes meilleurs clients en un clin d'œil."*  
> — **Sarah K., gérante d'une boutique de vêtements**

> 🗣️ *"Le fichier modèle m'a beaucoup aidé, et la visualisation est top ! Je recommande."*  
> — **Marc D., artisan peintre**

> 🗣️ *"Enfin un outil qui ne demande pas d'inscription et qui respecte mes données."*  
> — **Julie R., freelance**
""")
