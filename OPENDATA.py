import streamlit as st
from streamlit_folium import st_folium
import folium
from folium.plugins import HeatMap
import requests
from gtts import gTTS
import base64
import time
import pandas as pd
import re

# ==========================================
# 1. CONFIGURATION (DONNÉES PARIS)
# ==========================================
CHOIX_DISPONIBLES = {
    "📅 Sorties & Événements": {
        "api_id": "que-faire-a-paris-",
        "col_titre": "title",
        "col_adresse": "address_name",
        "icone": "calendar", 
        "couleur": "orange", 
        "infos_sup": [
            ("date_start", "📅 Date"),
            ("price_type", "💶 Prix"),
            ("lead_text", "ℹ️ Info")
        ],
        "image_col": "cover_url"
    },
    " 🛜 Bornes Wi-Fi": {
        "api_id": "sites-disposant-du-service-paris-wi-fi",
        "col_titre": "nom_site", "col_adresse": "arc_adresse",
        "icone": "wifi", "couleur": "purple", "infos_sup": [("etat2", "✅ État"), ("cp", "📮 CP")]
    },
    " 🚽 Sanisettes (Toilettes)": {
        "api_id": "sanisettesparis",
        "col_titre": "libelle", "col_adresse": "adresse",
        "icone": "tint", "couleur": "cadetblue", "infos_sup": [("horaire", "🕒 Horaires"), ("acces_pmr", "♿ PMR")]
    },
    " ⛲️ Fontaines à boire": {
        "api_id": "fontaines-a-boire",
        "col_titre": "voie", "col_adresse": "commune",
        "icone": "tint", "couleur": "blue", "infos_sup": [("dispo", "💧 Dispo"), ("type_objet", "⚙️ Type")]
    },
    " 🏗️ Chantiers Perturbants": {
        "api_id": "chantiers-perturbants",
        "col_titre": "objet", "col_adresse": "voie",
        "icone": "exclamation-triangle", "couleur": "red", "infos_sup": [("date_fin", "📅 Fin"), ("impact_circulation", "🚗 Impact")]
    },
    " 🔬 Laboratoires d'Analyses": {
        "api_id": "laboratoires-danalyses-medicales",
        "col_titre": "laboratoire", "col_adresse": "adresse",
        "icone": "flask", "couleur": "orange", "infos_sup": [("telephone", "📞 Tél"), ("horaires", "🕒 Horaires")]
    },
    " 🆘 Défibrillateurs": {
        "api_id": "defibrillateurs",
        "col_titre": "nom_etabl", "col_adresse": "adr_post",
        "icone": "heartbeat", "couleur": "darkred", "infos_sup": [("acces_daw", "🚪 Accès")]
    },
    " 🏫 Collèges": {
        "api_id": "etablissements-scolaires-colleges",
        "col_titre": "libelle", "col_adresse": "adresse",
        "icone": "graduation-cap", "couleur": "darkblue", "infos_sup": [("public_prive", "🏫 Secteur")]
    },
    " 🎓 Écoles Maternelles": {
        "api_id": "etablissements-scolaires-maternelles",
        "col_titre": "libelle", "col_adresse": "adresse",
        "icone": "child", "couleur": "pink", "infos_sup": [("public_prive", "🏫 Secteur")]
    }
}

COLONNES_CP_A_SCANNER = ["cp", "cp_arrondissement", "code_postal", "code_post", "arondissement", "arrondissement", "arr_insee", "address_zipcode"]

# --- MODIFICATION ICI : TON LOGO LOCAL ---
URL_LOGO = "logo_pulse.png" 
# -----------------------------------------

# ==========================================
# 2. FONCTIONS UTILES
# ==========================================

def extraire_cp_intelligent(site_data, col_adresse_config):
    cp_trouve = None
    for col in COLONNES_CP_A_SCANNER:
        val = str(site_data.get(col, ""))
        match = re.search(r'75\d{3}', val)
        if match:
            cp_trouve = match.group(0)
            break
    if not cp_trouve:
        adresse = str(site_data.get(col_adresse_config, ""))
        match = re.search(r'75\d{3}', adresse)
        if match:
            cp_trouve = match.group(0)
    if cp_trouve:
        if cp_trouve.startswith("751") and len(cp_trouve) == 5:
            return f"750{cp_trouve[3:]}"
        return cp_trouve
    return "Inconnu"

def jouer_son_automatique(texte):
    try:
        tts = gTTS(text=texte, lang='fr')
        nom_fichier = "temp_voice.mp3"
        tts.save(nom_fichier)
        with open(nom_fichier, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
        md = f"""<audio autoplay><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>"""
        st.sidebar.markdown(md, unsafe_allow_html=True)
        time.sleep(2)
    except:
        pass

@st.cache_data 
def charger_donnees(api_id, cible=500):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'}
    url = f"https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/{api_id}/records"
    tous_les_resultats = []
    
    for offset in range(0, cible, 100):
        params = {"limit": 100, "offset": offset}
        try:
            response = requests.get(url, params=params, headers=headers)
            data = response.json()
            if "results" not in data: break
            batch = data.get("results", [])
            tous_les_resultats.extend(batch)
            if len(batch) < 100: break
        except: break
    return tous_les_resultats

# ==========================================
# 3. INTERFACE STREAMLIT
# ==========================================
st.set_page_config(page_title="Paris Pulse", page_icon="🗼", layout="wide")

if 'dernier_choix' not in st.session_state:
    st.session_state.dernier_choix = None

# --- EN-TÊTE PRINCIPAL ---
col_logo, col_titre = st.columns([2, 10])

with col_logo:
    # Affiche ton image locale (si elle est dans le dossier)
    try:
        st.image(URL_LOGO, width=1500)
    except:
        st.warning("Image 'logo_pulse.png' introuvable.")

with col_titre:
    st.title("Paris Pulse")
    st.markdown("#### Le tableau de bord intelligent de la capitale 🗼💓")

st.divider()

# --- SIDEBAR ---
with st.sidebar:
    try:
        st.image(URL_LOGO, width=60)
    except:
        pass # Pas d'erreur si l'image manque dans la sidebar
        
    st.header("⚙️ Paramètres")
    activer_voix = st.checkbox("Activer l'assistant vocal", value=True)
    st.divider()
    st.header("🔍 Sélection")
    choix_utilisateur = st.selectbox("Catégorie :", list(CHOIX_DISPONIBLES.keys()))
    st.divider()
    st.header("📍 Zone & Filtres")
    mode_filtre = st.toggle("Activer le filtrage par zone", value=False)
    
    filtre_texte = ""
    if mode_filtre:
        st.caption("Tapez un numéro (ex: 13) ou un lieu (ex: Rivoli).")
        filtre_texte = st.text_input("Recherche :")
    else:
        st.info("Mode Carte Globale activé.")

# --- LOGIQUE ---
if choix_utilisateur != st.session_state.dernier_choix:
    if activer_voix:
        jouer_son_automatique(f"Chargement : {choix_utilisateur}")
    st.session_state.dernier_choix = choix_utilisateur

config = CHOIX_DISPONIBLES[choix_utilisateur]

with st.spinner("Chargement des données..."):
    limit_req = 200 if "que-faire" in config["api_id"] else 500
    raw_data = charger_donnees(config["api_id"], cible=limit_req)

tous_resultats = raw_data if isinstance(raw_data, list) else []

# --- FILTRAGE ---
resultats_finaux = []
if len(tous_resultats) > 0:
    if mode_filtre and filtre_texte:
        input_clean = filtre_texte.lower().strip()
        mots_a_chercher = []
        
        if input_clean.isdigit():
            num = int(input_clean)
            if 1 <= num <= 20:
                mots_a_chercher.extend([f"750{num:02d}", f"751{num:02d}", f"{num}e", f"{num}ème"])
        
        if not mots_a_chercher: 
            mots_a_chercher.append(input_clean)
        
        for site in tous_resultats:
            trouve = False
            valeurs_texte = str(site.values()).lower()
            for variante in mots_a_chercher:
                if variante in valeurs_texte:
                    trouve = True
                    break
            if trouve:
                resultats_finaux.append(site)
        
        if not resultats_finaux:
            st.warning(f"⚠️ Aucun résultat pour '{filtre_texte}'")
        else:
            st.success(f"✅ Filtre actif : {len(resultats_finaux)} lieux.")
    else:
        resultats_finaux = tous_resultats
        st.success(f"🌍 Carte Globale : {len(resultats_finaux)} lieux.")
else:
    st.info("Pas de données.")

# --- AFFICHAGE ---
tab_carte, tab_stats, tab_donnees = st.tabs(["🗺️ Carte", "📊 Statistiques", "📋 Données"])

with tab_carte:
    style_vue = st.radio("Vue :", ["📍 Points", "🔥 Densité"], horizontal=True)
    m = folium.Map(location=[48.8566, 2.3522], zoom_start=12)
    coords_heatmap = []
    
    for site in resultats_finaux:
        lat, lon = None, None
        geo = site.get("geo_point_2d")
        geom = site.get("geometry")
        lat_lon_special = site.get("lat_lon")
        
        if geo: 
            lat, lon = geo.get("lat"), geo.get("lon")
        elif geom and geom.get("type") == "Point":
            lon, lat = geom.get("coordinates")
        elif lat_lon_special and isinstance(lat_lon_special, dict): 
            lat, lon = lat_lon_special.get("lat"), lat_lon_special.get("lon")
            
        if lat and lon:
            coords_heatmap.append([lat, lon])
            if style_vue == "📍 Points":
                titre = site.get(config["col_titre"]) or "Lieu"
                titre = titre.replace('"', '') 
                adresse = site.get(config["col_adresse"]) or ""
                
                html_image = ""
                if "image_col" in config:
                    url_img = site.get(config["image_col"])
                    if isinstance(url_img, dict): url_img = url_img.get("url")
                    if url_img: html_image = f'<img src="{url_img}" width="200px" style="border-radius:5px; margin-bottom:10px;"><br>'

                popup_content = f"{html_image}<b>{titre}</b><br><i>{adresse}</i>"
                infos_html = ""
                for k, v in config["infos_sup"]:
                    val = site.get(k)
                    if val: 
                        if len(str(val)) > 100: val = str(val)[:100] + "..."
                        infos_html += f"<br><b>{v}:</b> {val}"
                popup_content += infos_html

                folium.Marker(
                    [lat, lon], popup=folium.Popup(popup_content, max_width=250),
                    icon=folium.Icon(color=config["couleur"], icon=config["icone"], prefix="fa")
                ).add_to(m)

    if style_vue == "🔥 Densité" and coords_heatmap:
        HeatMap(coords_heatmap, radius=15).add_to(m)

    st_folium(m, width=1000, height=600)

with tab_stats:
    st.subheader("📊 Analyse")
    col1, col2 = st.columns(2)
    with col1: st.metric("Total", len(resultats_finaux))
    
    if len(resultats_finaux) > 0:
        liste_cp = []
        for s in resultats_finaux:
            cp = extraire_cp_intelligent(s, config["col_adresse"])
            if cp == "Inconnu": cp = str(s.get("address_zipcode", "Inconnu"))
            if cp != "Inconnu" and "75" in cp: liste_cp.append(cp)
        
        if len(liste_cp) > 0:
            df = pd.DataFrame(liste_cp, columns=["Arrondissement"])
            compte = df["Arrondissement"].value_counts().sort_index()
            st.bar_chart(compte)
        else:
            st.info("Graphique non disponible (Codes postaux non détectés).")

with tab_donnees:
    st.dataframe(resultats_finaux)
