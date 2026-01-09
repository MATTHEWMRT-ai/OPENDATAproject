import streamlit as st
from streamlit_folium import st_folium
import folium
from folium.plugins import HeatMap
import requests
import pandas as pd
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
# 1. INTELLIGENCE (Classification & Heuristiques)
# ==========================================

# Mots-clés pour classer les datasets
CATEGORIES_RULES = {
    "🚲 Mobilité": ["velo", "cyclab", "bicloo", "trottinette", "stationnement", "parking", "metro", "bus", "tram", "transport", "gare", "pieton", "sncf"],
    "🎭 Culture & Sorties": ["cinema", "theatre", "musee", "culture", "bibliotheque", "exposition", "agenda", "evenement", "patrimoine", "concert", "visite"],
    "🌳 Nature & Cadre de vie": ["jardin", "parc", "arbre", "eau", "fontaine", "dechet", "proprete", "tri", "banc", "toilette", "caniparc", "vert"],
    "🏫 Services Publics": ["ecole", "creche", "college", "lycee", "administration", "public", "mairie", "vote", "election", "citoyen", "organisme"],
    "🏥 Santé & Social": ["sante", "hopital", "medecin", "pharmacie", "defibrillateur", "social", "handicap", "accessibilite", "urgence", "aide"]
}

# Mapping Mots-clés -> Icônes FontAwesome & Couleurs
ICON_RULES = [
    (["parking", "stationnement"], "parking", "blue"),
    (["velo", "cycliste", "bicloo", "piste"], "bicycle", "red"),
    (["bus", "tram", "metro", "transport", "tan", "star"], "bus", "cadetblue"),
    (["parc", "jardin", "arbre", "square"], "tree", "green"),
    (["eau", "fontaine", "piscine"], "tint", "lightblue"),
    (["toilette", "sanisette", "wc"], "venus-mars", "gray"),
    (["wifi", "internet", "numerique"], "wifi", "purple"),
    (["musee", "art", "culture", "biblio"], "paint-brush", "orange"),
    (["ecole", "college", "enseignement", "scolaire"], "graduation-cap", "pink"),
    (["sante", "defibrillateur", "hopital", "secours"], "heartbeat", "darkred"),
    (["poubelle", "dechet", "tri", "verre"], "trash", "darkgreen"),
]

def detecter_style(texte_analyse):
    """Devine l'icône et la couleur basées sur le texte"""
    texte = texte_analyse.lower()
    for mots_cles, icone, couleur in ICON_RULES:
        if any(mot in texte for mot in mots_cles):
            return icone, couleur
    return "map-marker", "blue"

def detecter_categorie(texte_analyse):
    """Devine la catégorie"""
    texte = texte_analyse.lower()
    for cat, mots in CATEGORIES_RULES.items():
        if any(mot in texte for mot in mots):
            return cat
    return "📂 Divers / Autres"

def analyser_structure_dataset(dataset_item):
    """
    Analyse les champs pour trouver Titre, Adresse et Géolocalisation.
    """
    fields = dataset_item.get("fields", [])
    field_names = [f["name"] for f in fields]
    
    # 1. Vérification Géolocalisation (Indispensable pour la carte)
    col_geo = None
    # Priorité 1 : Champ type geo_point_2d
    for f in fields:
        if f["type"] == "geo_point_2d":
            col_geo = f["name"]
            break
    
    # Priorité 2 : Recherche lat/lon explicites
    if not col_geo:
        has_lat = any(x in field_names for x in ["lat", "latitude", "y_wgs84"])
        has_lon = any(x in field_names for x in ["lon", "long", "longitude", "x_wgs84"])
        if has_lat and has_lon:
            col_geo = "AUTO_DETECT_LAT_LON"
            
    if not col_geo:
        return None # On ignore ce dataset s'il n'a pas de coordonnées

    # 2. Détection Titre
    col_titre = None
    scores_titre = ["nom", "titre", "libelle", "intitule", "name", "label", "id", "identifiant"]
    for candidat in scores_titre:
        found = [n for n in field_names if candidat in n.lower()]
        if found:
            col_titre = found[0]
            break
    if not col_titre and field_names: col_titre = field_names[0]

    # 3. Détection Adresse
    col_adresse = None
    scores_adresse = ["adresse", "voie", "rue", "localisation", "address", "commune", "ville"]
    for candidat in scores_adresse:
        found = [n for n in field_names if candidat in n.lower()]
        if found:
            col_adresse = found[0]
            break
            
    # 4. Métadonnées (Titre du dataset, mots-clés)
    metas = dataset_item.get("metas", {}).get("default", {})
    titre_ds = metas.get("title", dataset_item.get("dataset_id"))
    mots_cles = metas.get("keyword", []) 
    if mots_cles is None: mots_cles = [] # Sécurité si null
    
    texte_analyse = f"{titre_ds} {' '.join(mots_cles)}"
    icone, couleur = detecter_style(texte_analyse)
    cat = detecter_categorie(texte_analyse)

    return {
        "api_id": dataset_item.get("dataset_id"),
        "titre_dataset": titre_ds,
        "categorie": cat,
        "col_titre": col_titre,
        "col_adresse": col_adresse,
        "col_geo": col_geo,
        "icone": icone,
        "couleur": couleur,
        "infos_sup": field_names[:6] # On garde les 6 premières colonnes pour l'info-bulle
    }

# ==========================================
# 2. CONFIGURATION API & FONCTIONS BACKEND
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
    },
     "Strasbourg 🥨": {
        "api_url": "https://data.strasbourg.eu/api/explore/v2.1",
        "coords": [48.5734, 7.7521],
        "zoom": 13
    }
}

# HEADERS : Indispensable pour ne pas être bloqué par l'API
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) CityPulse/1.0'
}

@st.cache_data(ttl=3600)
def scanner_catalogue(api_base_url):
    """Scanne le catalogue et gère les erreurs API proprement"""
    url = f"{api_base_url}/catalog/datasets"
    
    # Stratégie 1 : On essaie de trier par popularité (records_count)
    params = {"limit": 60, "order_by": "records_count desc"}
    
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=10)
        r.raise_for_status()
        results = r.json().get("results", [])
    
    except Exception:
        # Stratégie 2 (Fallback) : Si l'option de tri plante (Erreur 400), on tente sans tri
        try:
            params_simple = {"limit": 60}
            r = requests.get(url, params=params_simple, headers=HEADERS, timeout=10)
            r.raise_for_status()
            results = r.json().get("results", [])
        except Exception as e_final:
            st.error(f"❌ Impossible de lire le catalogue de cette ville. ({e_final})")
            return {}

    catalogue_organise = {}
    found_count = 0
    
    for ds in results:
        config = analyser_structure_dataset(ds)
        if config:
            found_count += 1
            cat = config["categorie"]
            if cat not in catalogue_organise:
                catalogue_organise[cat] = {}
            catalogue_organise[cat][config["titre_dataset"]] = config
            
    if found_count == 0 and len(results) > 0:
        st.warning("⚠️ Des données existent, mais aucune n'a de coordonnées GPS exploitables pour une carte.")
            
    return catalogue_organise

@st.cache_data(ttl=600)
def charger_donnees_api(api_base_url, dataset_id):
    """Charge les données du dataset sélectionné"""
    url = f"{api_base_url}/catalog/datasets/{dataset_id}/records"
    params = {"limit": 99} # Limite pour fluidité
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=10)
        r.raise_for_status()
        return r.json().get("results", [])
    except Exception as e:
        st.error(f"Erreur lors du chargement des points : {e}")
        return []

def recuperer_gps(item, col_geo):
    """Extrait lat/lon depuis le JSON, peu importe le format"""
    lat, lon = None, None
    
    # Cas 1 : Colonne GeoJSON/GeoPoint (Standard Opendatasoft)
    if col_geo and col_geo != "AUTO_DETECT_LAT_LON":
        val = item.get(col_geo)
        if isinstance(val, dict):
            lat, lon = val.get("lat"), val.get("lon")
            if not lat and "geometry" in val: # Parfois imbriqué
                coords = val.get("geometry", {}).get("coordinates")
                if coords: lon, lat = coords
                
    # Cas 2 : Auto détection dans les colonnes lat/lon
    if not lat:
        keys = item.keys()
        k_lat = next((k for k in keys if k in ["lat", "latitude", "y_wgs84"]), None)
        k_lon = next((k for k in keys if k in ["lon", "long", "longitude", "x_wgs84"]), None)
        if k_lat and k_lon:
            try:
                lat = float(item[k_lat])
                lon = float(item[k_lon])
            except: pass
            
    return lat, lon

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
    with st.spinner(f"📡 Scan des données de {ville_nom}..."):
        catalogue = scanner_catalogue(ville_conf["api_url"])
    
    if not catalogue:
        st.error("Aucune donnée cartographique trouvée. Essayez une autre ville ou vérifiez l'API.")
        st.stop()
        
    st.header("2. Les Données")
    
    # Menu Catégorie
    cats_dispo = sorted(list(catalogue.keys()))
    cat_choisie = st.selectbox("Thématique :", cats_dispo)
    
    # Menu Dataset
    datasets_dispo = catalogue[cat_choisie]
    dataset_nom = st.selectbox("Jeu de données :", list(datasets_dispo.keys()))
    
    # Config finale
    config_dataset = datasets_dispo[dataset_nom]
    
    st.success(f"📍 Mode : {config_dataset['col_geo']}")
    st.info(f"🎨 Style : {config_dataset['icone']}")

    st.divider()
    activer_filtre = st.toggle("Activer filtre texte")
    txt_filtre = ""
    if activer_filtre:
        txt_filtre = st.text_input("Recherche (ex: Centre, Gare...) :")

# --- MAIN ---

# Chargement
with st.spinner(f"Chargement de : {dataset_nom}..."):
    data = charger_donnees_api(ville_conf["api_url"], config_dataset["api_id"])

# Filtrage local
data_finale = []
if activer_filtre and txt_filtre:
    for d in data:
        if txt_filtre.lower() in str(d).lower():
            data_finale.append(d)
else:
    data_finale = data

st.markdown(f"### {dataset_nom} ({len(data_finale)} lieux)")

# Onglets d'affichage
tab_map, tab_stats, tab_raw = st.tabs(["🗺️ Carte Interactive", "📊 Analyse", "💾 Données Brutes"])

with tab_map:
    # Initialisation carte
    m = folium.Map(location=ville_conf["coords"], zoom_start=ville_conf["zoom"])
    coords_heat = []
    
    for item in data_finale:
        lat, lon = recuperer_gps(item, config_dataset["col_geo"])
        
        if lat and lon:
            coords_heat.append([lat, lon])
            
            # Popup intelligent
            titre = item.get(config_dataset["col_titre"], "Sans titre")
            adresse = item.get(config_dataset["col_adresse"], "")
            
            html = f"<b>{titre}</b><br><i>{adresse}</i><hr>"
            for col in config_dataset["infos_sup"]:
                val = item.get(col)
                if val: html += f"<span style='font-size:10px; color:grey;'><b>{col}:</b> {str(val)[:40]}</span><br>"
            
            folium.Marker(
                [lat, lon],
                popup=folium.Popup(html, max_width=300),
                icon=folium.Icon(color=config_dataset["couleur"], icon=config_dataset["icone"], prefix="fa")
            ).add_to(m)
            
    if coords_heat:
        st_folium(m, width="100%", height=600)
    else:
        st.warning("Aucune coordonnée valide trouvée dans ce jeu de données.")

with tab_stats:
    if len(data_finale) > 0:
        df = pd.DataFrame(data_finale)
        
        col1, col2 = st.columns(2)
        with col1: st.metric("Nombre d'éléments", len(df))
        with col2: st.metric("Colonnes", len(df.columns))
            
        # Graphique automatique sur les champs texte courts (catégories)
        cat_cols = [c for c in df.columns if df[c].dtype == 'object' and df[c].nunique() < 15]
        if cat_cols:
            st.subheader("Distribution automatique")
            c_g = st.selectbox("Grouper par :", cat_cols)
            chart = alt.Chart(df).mark_bar().encode(
                x=alt.X(c_g, sort='-y', axis=alt.Axis(labelLimit=200)),
                y='count()',
                color=c_g,
                tooltip=[c_g, 'count()']
            ).interactive()
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Ce dataset contient des données trop variées pour générer un graphique automatique.")

with tab_raw:
    st.dataframe(data_finale)
