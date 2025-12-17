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
# 1. CONFIGURATION MULTI-VILLES
# ==========================================

# Configuration globale pour gérer plusieurs villes
CONFIG_VILLES = {
    "Paris 🗼": {
        "coords_center": [48.8566, 2.3522],
        "zoom_start": 12,
        "api_url": "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets",
        "cp_prefix": "75", # Pour filtrer les codes postaux
        "categories": {
            "📅 Sorties & Événements": {
                "api_id": "que-faire-a-paris-",
                "col_titre": "title", "col_adresse": "address_name",
                "icone": "calendar", "couleur": "orange",
                "infos_sup": [("date_start", "📅 Date"), ("price_type", "💶 Prix"), ("lead_text", "ℹ️ Info")],
                "image_col": "cover_url"
            },
            "Bornes Wi-Fi": {
                "api_id": "sites-disposant-du-service-paris-wi-fi",
                "col_titre": "nom_site", "col_adresse": "arc_adresse",
                "icone": "wifi", "couleur": "purple", 
                "infos_sup": [("etat2", "✅ État"), ("cp", "📮 CP")]
            },
            "Sanisettes (Toilettes)": {
                "api_id": "sanisettesparis",
                "col_titre": "libelle", "col_adresse": "adresse",
                "icone": "tint", "couleur": "blue", 
                "infos_sup": [("horaire", "🕒 Horaires"), ("acces_pmr", "♿ PMR")]
            },
            "Chantiers Perturbants": {
                "api_id": "chantiers-perturbants",
                "col_titre": "objet", "col_adresse": "voie",
                "icone": "exclamation-triangle", "couleur": "red", 
                "infos_sup": [("date_fin", "📅 Fin"), ("impact_circulation", "🚗 Impact")]
            }
        }
    },
    "Rennes 🏁": {
        "coords_center": [48.1172, -1.6777],
        "zoom_start": 13,
        "api_url": "https://data.rennesmetropole.fr/api/explore/v2.1/catalog/datasets",
        "cp_prefix": "35",
        "categories": {
            "📅 Agenda du Territoire": {
                "api_id": "agenda-du-territoire-de-rennes-metropole", # ID Dataset Rennes
                "col_titre": "titre", 
                "col_adresse": "location_address",
                "icone": "calendar", "couleur": "orange",
                "infos_sup": [("debut", "📅 Début"), ("categorie", "🏷️ Catégorie"), ("descriptif", "ℹ️ Info")],
                 # Pas d'image facile sur cet API, mais on garde la logique
            },
            "🚌 Arrêts Bus & Métro (STAR)": {
                "api_id": "arrets-et-stations-du-reseau-star",
                "col_titre": "nom", 
                "col_adresse": "commune", # Pas d'adresse précise, on met la commune
                "icone": "bus", "couleur": "blue",
                "infos_sup": [("mobilier", "🚏 Type"), ("acces_pmr", "♿ PMR")]
            },
            "🚽 Sanitaires Publics": {
                "api_id": "topologie-des-sanitaires-publics",
                "col_titre": "nom", 
                "col_adresse": "adresse",
                "icone": "tint", "couleur": "cadetblue",
                "infos_sup": [("quartier", "📍 Quartier"), ("acces_pmr", "♿ PMR")]
            }
        }
    }
}

COLONNES_CP_A_SCANNER = ["cp", "code_postal", "code_post", "zipcode", "commune", "location_address"]
URL_LOGO = "logo_pulse.png" # Ton logo local

# ==========================================
# 2. FONCTIONS UTILES
# ==========================================

def extraire_cp_intelligent(site_data, col_adresse_config, prefixe_cp="75"):
    """ Extrait le CP en fonction de la ville (75 ou 35) """
    cp_trouve = None
    # Regex dynamique : cherche 75xxx ou 35xxx
    regex = rf'{prefixe_cp}\d{{3}}' 
    
    for col in COLONNES_CP_A_SCANNER:
        val = str(site_data.get(col, ""))
        match = re.search(regex, val)
        if match:
            cp_trouve = match.group(0)
            break
            
    if not cp_trouve:
        adresse = str(site_data.get(col_adresse_config, ""))
        match = re.search(regex, adresse)
        if match:
            cp_trouve = match.group(0)
            
    if cp_trouve:
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
def charger_donnees(base_url, api_id, cible=500):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'}
    # L'URL est maintenant dynamique selon la ville !
    url = f"{base_url}/{api_id}/records"
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
st.set_page_config(page_title="City Pulse", page_icon="🌍", layout="wide")

# --- CSS PERSONNALISÉ ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@100;400;700&display=swap');
    h1 { color: #F63366; font-family: 'Roboto', sans-serif; font-weight: 700; text-transform: uppercase; letter-spacing: 2px; }
    h3, h4 { color: #262730; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }
</style>
""", unsafe_allow_html=True)

if 'dernier_choix' not in st.session_state:
    st.session_state.dernier_choix = None

# --- EN-TÊTE PRINCIPAL ---
col_logo, col_titre = st.columns([2, 10])

with col_logo:
    try:
        st.image(URL_LOGO, width=150)
    except:
        st.warning("Logo introuvable")

with col_titre:
    # Titre générique maintenant
    st.title("City Pulse") 
    st.markdown("#### Le tableau de bord intelligent de vos villes 🌍💓")

st.divider()

# --- SIDEBAR (SÉLECTEUR DE VILLE) ---
with st.sidebar:
    try: st.image(URL_LOGO, width=60)
    except: pass
        
    st.header("📍 Destination")
    # 1. On choisit la ville D'ABORD
    ville_actuelle = st.selectbox("Choisir une ville :", list(CONFIG_VILLES.keys()))
    
    # On charge la config de la ville choisie
    config_ville = CONFIG_VILLES[ville_actuelle]
    choix_categories = config_ville["categories"]
    
    st.divider()
    st.header("⚙️ Paramètres")
    activer_voix = st.checkbox("Activer l'assistant vocal", value=True)
    
    st.divider()
    st.header("🔍 Données")
    # 2. Le menu catégorie s'adapte à la ville choisie
    choix_utilisateur = st.selectbox("Catégorie :", list(choix_categories.keys()))
    
    st.divider()
    st.header("🔎 Filtres")
    mode_filtre = st.toggle("Filtrer par zone", value=False)
    filtre_texte = ""
    if mode_filtre:
        st.caption("Numéro d'arrondissement ou code postal.")
        filtre_texte = st.text_input("Recherche :")

# --- LOGIQUE ---
# Détection changement pour voix
cle_unique = f"{ville_actuelle}_{choix_utilisateur}"
if cle_unique != st.session_state.dernier_choix:
    if activer_voix:
        jouer_son_automatique(f"Chargement : {ville_actuelle}, {choix_utilisateur}")
    st.session_state.dernier_choix = cle_unique

# Récupération de la config spécifique du dataset choisi
config_data = choix_categories[choix_utilisateur]

with st.spinner(f"Chargement des données de {ville_actuelle}..."):
    # On passe l'URL de base de la ville (Paris ou Rennes) à la fonction
    limit_req = 200 if "agenda" in config_data["api_id"] or "que-faire" in config_data["api_id"] else 500
    raw_data = charger_donnees(config_ville["api_url"], config_data["api_id"], cible=limit_req)

tous_resultats = raw_data if isinstance(raw_data, list) else []

# --- FILTRAGE ---
resultats_finaux = []
if len(tous_resultats) > 0:
    if mode_filtre and filtre_texte:
        input_clean = filtre_texte.lower().strip()
        mots_a_chercher = []
        
        # Logique CP simple (marche pour Paris 75013 et Rennes 35000)
        if input_clean.isdigit():
            mots_a_chercher.append(input_clean)
        else:
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
        st.success(f"🌍 {ville_actuelle} : {len(resultats_finaux)} lieux trouvés.")
else:
    st.info("Pas de données disponibles pour cette catégorie.")

# --- AFFICHAGE ---
tab_carte, tab_stats, tab_donnees = st.tabs(["🗺️ Carte", "📊 Statistiques", "📋 Données"])

with tab_carte:
    style_vue = st.radio("Vue :", ["📍 Points", "🔥 Densité"], horizontal=True)
    
    # CENTRAGE DYNAMIQUE SELON LA VILLE
    m = folium.Map(location=config_ville["coords_center"], zoom_start=config_ville["zoom_start"])
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
                titre = site.get(config_data["col_titre"]) or "Lieu"
                titre = str(titre).replace('"', '') 
                adresse = site.get(config_data["col_adresse"]) or ""
                
                html_image = ""
                if "image_col" in config_data:
                    url_img = site.get(config_data["image_col"])
                    if isinstance(url_img, dict): url_img = url_img.get("url")
                    if url_img: html_image = f'<img src="{url_img}" width="200px" style="border-radius:5px; margin-bottom:10px;"><br>'

                popup_content = f"{html_image}<b>{titre}</b><br><i>{adresse}</i>"
                infos_html = ""
                for k, v in config_data["infos_sup"]:
                    val = site.get(k)
                    if val: 
                        if len(str(val)) > 100: val = str(val)[:100] + "..."
                        infos_html += f"<br><b>{v}:</b> {val}"
                popup_content += infos_html

                folium.Marker(
                    [lat, lon], popup=folium.Popup(popup_content, max_width=250),
                    icon=folium.Icon(color=config_data["couleur"], icon=config_data["icone"], prefix="fa")
                ).add_to(m)

    if style_vue == "🔥 Densité" and coords_heatmap:
        HeatMap(coords_heatmap, radius=15).add_to(m)

    st_folium(m, width=1000, height=600)

with tab_stats:
    st.subheader(f"📊 Analyse : {ville_actuelle}")
    col1, col2 = st.columns(2)
    with col1: st.metric("Total éléments", len(resultats_finaux))
    
    if len(resultats_finaux) > 0:
        liste_cp = []
        for s in resultats_finaux:
            # On utilise le préfixe de la ville (75 ou 35) pour l'extraction
            cp = extraire_cp_intelligent(s, config_data["col_adresse"], prefixe_cp=config_ville["cp_prefix"])
            if cp == "Inconnu": cp = str(s.get("address_zipcode", "Inconnu"))
            
            # On vérifie que le CP correspond bien à la ville (contient 75 ou 35)
            if cp != "Inconnu" and config_ville["cp_prefix"] in cp: 
                liste_cp.append(cp)
        
        if len(liste_cp) > 0:
            df = pd.DataFrame(liste_cp, columns=["Zone / CP"])
            compte = df["Zone / CP"].value_counts().sort_index()
            st.bar_chart(compte)
            st.info("Répartition par Code Postal / Quartier.")
        else:
            st.info("Données géographiques (CP) insuffisantes pour un graphique.")

with tab_donnees:
    st.dataframe(resultats_finaux)
