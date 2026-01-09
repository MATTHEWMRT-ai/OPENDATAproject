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
import altair as alt

# ==========================================
# 0. CONFIGURATION PAGE
# ==========================================
st.set_page_config(
    page_title="City Pulse Dynamic", 
    page_icon="🌍", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# ==========================================
# 1. INTELLIGENCE ARTIFICIELLE (Heuristiques)
# ==========================================

# Mots-clés pour classer les datasets dans des catégories
CATEGORIES_RULES = {
    "🚲 Mobilité": ["velo", "cyclab", "bicloo", "trottinette", "stationnement", "parking", "metro", "bus", "tram", "transport", "gare"],
    "🎭 Culture & Sorties": ["cinema", "theatre", "musee", "culture", "bibliotheque", "exposition", "agenda", "evenement", "patrimoine"],
    "🌳 Nature & Cadre de vie": ["jardin", "parc", "arbre", "eau", "fontaine", "dechet", "proprete", "tri", "banc", "toilette"],
    "🏫 Services Publics": ["ecole", "creche", "college", "lycee", "administration", "public", "mairie", "vote", "election"],
    "🏥 Santé & Social": ["sante", "hopital", "medecin", "pharmacie", "defibrillateur", "social", "handicap", "accessibilite"]
}

# Mapping Mots-clés -> Icônes FontAwesome (v4) + Couleurs
ICON_RULES = [
    (["parking", "stationnement"], "parking", "blue"),
    (["velo", "cycliste", "bicloo"], "bicycle", "red"),
    (["bus", "tram", "metro", "transport"], "bus", "cadetblue"),
    (["parc", "jardin", "arbre"], "tree", "green"),
    (["eau", "fontaine", "piscine"], "tint", "lightblue"),
    (["toilette", "sanisette"], "venus-mars", "gray"),
    (["wifi", "internet"], "wifi", "purple"),
    (["musee", "art", "culture"], "paint-brush", "orange"),
    (["ecole", "college", "enseignement"], "graduation-cap", "pink"),
    (["sante", "defibrillateur", "hopital"], "heartbeat", "darkred"),
    (["poubelle", "dechet", "tri"], "trash", "darkgreen"),
]

def detecter_style(texte_analyse):
    """Devine l'icône et la couleur basées sur le texte (titre + tags)"""
    texte = texte_analyse.lower()
    for mots_cles, icone, couleur in ICON_RULES:
        if any(mot in texte for mot in mots_cles):
            return icone, couleur
    return "map-marker", "blue" # Défaut

def detecter_categorie(texte_analyse):
    """Devine la catégorie"""
    texte = texte_analyse.lower()
    for cat, mots in CATEGORIES_RULES.items():
        if any(mot in texte for mot in mots):
            return cat
    return "📂 Divers / Autres"

def analyser_structure_dataset(dataset_item):
    """
    Analyse les champs (fields) pour identifier titre, adresse et géo.
    Retourne une config ou None si pas de géolocalisation.
    """
    fields = dataset_item.get("fields", [])
    field_names = [f["name"] for f in fields]
    
    # 1. Vérification Géolocalisation (CRITIQUE)
    col_geo = None
    # Priorité 1 : Champ type geo_point_2d (Standard Opendatasoft)
    for f in fields:
        if f["type"] == "geo_point_2d":
            col_geo = f["name"]
            break
    
    # Priorité 2 : Recherche de lat/lon séparés
    if not col_geo:
        has_lat = any(x in field_names for x in ["lat", "latitude", "y_wgs84"])
        has_lon = any(x in field_names for x in ["lon", "long", "longitude", "x_wgs84"])
        if has_lat and has_lon:
            col_geo = "AUTO_DETECT_LAT_LON" # Marqueur spécial
            
    if not col_geo:
        return None # Pas de carte possible, on ignore ce dataset

    # 2. Détection Titre (Heuristique)
    col_titre = None
    scores_titre = ["nom", "titre", "libelle", "intitule", "name", "label", "id"]
    for candidat in scores_titre:
        found = [n for n in field_names if candidat in n.lower()]
        if found:
            col_titre = found[0] # Le plus court ou le premier qui match
            break
    if not col_titre: col_titre = field_names[0] # Fallback

    # 3. Détection Adresse
    col_adresse = None
    scores_adresse = ["adresse", "voie", "rue", "localisation", "address", "commune"]
    for candidat in scores_adresse:
        found = [n for n in field_names if candidat in n.lower()]
        if found:
            col_adresse = found[0]
            break
            
    # 4. Métadonnées pour le style
    metas = dataset_item.get("metas", {}).get("default", {})
    titre_ds = metas.get("title", dataset_item.get("dataset_id"))
    mots_cles = metas.get("keyword", [])
    texte_analyse = f"{titre_ds} {' '.join(mots_cles)}"
    
    icone, couleur = detecter_style(texte_analyse)
    cat = detecter_categorie(texte_analyse)

    return {
        "api_id": dataset_item.get("dataset_id"),
        "titre_dataset": titre_ds,
        "categorie": cat,
        "col_titre": col_titre,
        "col_adresse": col_adresse,
        "col_geo": col_geo, # Nom de la colonne geo ou "AUTO_DETECT..."
        "icone": icone,
        "couleur": couleur,
        "infos_sup": field_names[:5] # On garde les 5 premières colonnes pour l'info bulle
    }

# ==========================================
# 2. CONFIGURATION API & FONCTIONS
# ==========================================

VILLES_CONFIG = {
    "Paris 🗼": {
        "api_url": "https://opendata.paris.fr/api/explore/v2.1",
        "coords": [48.8566, 2.3522],
        "zoom": 12
    },
    "Rennes 🏁": {
        "api_url": "https://data.rennesmetropole.fr/api/explore/v2.1",
        "coords": [48.1172, -1.6777],
        "zoom": 13
    },
    "Nantes 🐘": {
        "api_url": "https://data.nantesmetropole.fr/api/explore/v2.1",
        "coords": [47.2184, -1.5536],
        "zoom": 13
    },
    "Toulouse 🚀": {
        "api_url": "https://data.toulouse-metropole.fr/api/explore/v2.1",
        "coords": [43.6047, 1.4442],
        "zoom": 13
    }
}

@st.cache_data(ttl=3600)
def scanner_catalogue(api_base_url):
    """Récupère les datasets populaires et construit la config dynamique"""
    url = f"{api_base_url}/catalog/datasets"
    # On prend les 60 datasets les plus populaires (records_count desc)
    params = {"limit": 60, "order_by": "metas.records_count desc"}
    
    try:
        r = requests.get(url, params=params).json()
        raw_datasets = r.get("results", [])
    except:
        return {}

    catalogue_organise = {}
    
    for ds in raw_datasets:
        config = analyser_structure_dataset(ds)
        if config:
            cat = config["categorie"]
            if cat not in catalogue_organise:
                catalogue_organise[cat] = {}
            # On utilise le titre comme clé
            catalogue_organise[cat][config["titre_dataset"]] = config
            
    return catalogue_organise

@st.cache_data
def charger_donnees_api(api_base_url, dataset_id):
    url = f"{api_base_url}/catalog/datasets/{dataset_id}/records"
    params = {"limit": 100} # Limite à 100 pour la rapidité de démo
    try:
        r = requests.get(url, params=params).json()
        return r.get("results", [])
    except:
        return []

def recuperer_gps(item, col_geo):
    """Extrait latitude/longitude peu importe le format"""
    lat, lon = None, None
    
    # Cas 1 : Colonne GeoJSON/GeoPoint spécifique
    if col_geo and col_geo != "AUTO_DETECT_LAT_LON":
        val = item.get(col_geo)
        if isinstance(val, dict):
            lat, lon = val.get("lat"), val.get("lon")
            if not lat: # Parfois format geometry
                coords = val.get("geometry", {}).get("coordinates")
                if coords: lon, lat = coords # GeoJSON est souvent Lon, Lat
                
    # Cas 2 : Auto détection lat/lon dans les colonnes
    if not lat:
        # On cherche brutalement dans les clés
        keys = item.keys()
        k_lat = next((k for k in keys if k in ["lat", "latitude", "y_wgs84"]), None)
        k_lon = next((k for k in keys if k in ["lon", "long", "longitude", "x_wgs84"]), None)
        
        if k_lat and k_lon:
            try:
                lat = float(item[k_lat])
                lon = float(item[k_lon])
            except: pass
            
    return lat, lon

def jouer_son(texte):
    try:
        # Simplifié pour éviter les erreurs de fichier
        b64 = base64.b64encode(gTTS(text=texte, lang='fr').save("temp.mp3") or open("temp.mp3", "rb").read()).decode()
        st.sidebar.markdown(f'<audio autoplay><source src="data:audio/mp3;base64,{b64}"></audio>', unsafe_allow_html=True)
    except: pass

# ==========================================
# 3. INTERFACE STREAMLIT
# ==========================================

st.title("🌍 City Pulse : Explorateur Dynamique")
st.markdown("Ce tableau de bord **scanne automatiquement** les Open Data des villes pour générer des cartes.")

# --- SIDEBAR ---
with st.sidebar:
    st.header("1. La Ville")
    ville_nom = st.selectbox("Choisir une métropole :", list(VILLES_CONFIG.keys()))
    ville_conf = VILLES_CONFIG[ville_nom]
    
    st.divider()
    
    # SCAN DU CATALOGUE
    with st.spinner(f"📡 Scan des satellites au dessus de {ville_nom}..."):
        catalogue = scanner_catalogue(ville_conf["api_url"])
    
    if not catalogue:
        st.error("Erreur de connexion à l'API ou pas de données géo trouvées.")
        st.stop()
        
    st.header("2. Les Données")
    
    # Menu Catégorie
    cats_dispo = sorted(list(catalogue.keys()))
    cat_choisie = st.selectbox("Thématique :", cats_dispo)
    
    # Menu Dataset
    datasets_dispo = catalogue[cat_choisie]
    dataset_nom = st.selectbox("Jeu de données :", list(datasets_dispo.keys()))
    
    # Config finale récupérée
    config_dataset = datasets_dispo[dataset_nom]
    
    st.info(f"📍 Colonne géo détectée : `{config_dataset['col_geo']}`")
    st.info(f"🎨 Style auto : {config_dataset['icone']} ({config_dataset['couleur']})")

    st.divider()
    activer_filtre = st.toggle("Activer filtre texte")
    if activer_filtre:
        txt_filtre = st.text_input("Filtrer par mot-clé :")

# --- MAIN ---

# Chargement Données
with st.spinner("Téléchargement des données..."):
    data = charger_donnees_api(ville_conf["api_url"], config_dataset["api_id"])

# Filtrage
data_finale = []
if activer_filtre and txt_filtre:
    for d in data:
        if txt_filtre.lower() in str(d).lower():
            data_finale.append(d)
else:
    data_finale = data

st.success(f"✅ {len(data_finale)} éléments chargés pour : {dataset_nom}")

# Onglets
tab_map, tab_stats, tab_raw = st.tabs(["🗺️ Carte Interactive", "📊 Analyse Rapide", "💾 Données Brutes"])

with tab_map:
    m = folium.Map(location=ville_conf["coords"], zoom_start=ville_conf["zoom"])
    
    coords_for_heat = []
    
    # Boucle d'affichage
    for item in data_finale:
        lat, lon = recuperer_gps(item, config_dataset["col_geo"])
        
        if lat and lon:
            coords_for_heat.append([lat, lon])
            
            # Construction Popup
            titre = item.get(config_dataset["col_titre"], "Sans titre")
            adresse = item.get(config_dataset["col_adresse"], "")
            
            html = f"<b>{titre}</b><br><i>{adresse}</i><hr>"
            for col in config_dataset["infos_sup"]:
                val = item.get(col)
                if val: html += f"<small><b>{col}:</b> {str(val)[:50]}</small><br>"
            
            folium.Marker(
                [lat, lon],
                popup=folium.Popup(html, max_width=300),
                icon=folium.Icon(color=config_dataset["couleur"], icon=config_dataset["icone"], prefix="fa")
            ).add_to(m)
            
    st_folium(m, width="100%", height=600)

with tab_stats:
    if len(data_finale) > 0:
        df = pd.DataFrame(data_finale)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Nombre de points", len(df))
        with col2:
            st.metric("Colonnes disponibles", len(df.columns))
            
        # Tentative de graphiques auto sur les champs texte (catégoriels)
        colonnes_cat = [c for c in df.columns if df[c].dtype == 'object' and df[c].nunique() < 20]
        
        if colonnes_cat:
            st.subheader("Répartition automatique")
            col_graph = st.selectbox("Analyser la colonne :", colonnes_cat)
            
            chart = alt.Chart(df).mark_bar().encode(
                x=alt.X(col_graph, sort='-y'),
                y='count()',
                color=col_graph
            ).interactive()
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Pas de colonnes catégorielles simples trouvées pour un graphique auto.")

with tab_raw:
    st.dataframe(data_finale)
