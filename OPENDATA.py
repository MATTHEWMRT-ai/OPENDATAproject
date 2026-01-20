import streamlit as st
from streamlit_folium import st_folium
import folium
from folium.plugins import HeatMap, MarkerCluster # AJOUT DU CLUSTERING
import requests
from gtts import gTTS
import base64
import time
import pandas as pd
import re
import altair as alt
from streamlit_mic_recorder import speech_to_text

# ==========================================
# 0. CONFIGURATION PAGE
# ==========================================
st.set_page_config(
    page_title="City Pulse", 
    page_icon="🌍", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# ==========================================
# 1. CONFIGURATION DONNÉES COMPLÈTE
# ==========================================

CONFIG_VILLES = {
    "Paris 🗼": {
        "coords_center": [48.8566, 2.3522],
        "zoom_start": 12,
        "api_url": "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets",
        "cp_prefix": "75",
        "alias": ["paris", "paname", "75"],
        "categories": {
            "🚽 Sanisettes (Toilettes)": {
                "api_id": "sanisettesparis",
                "col_titre": "libelle", "col_adresse": "adresse",
                "icone": "tint", "couleur": "blue", 
                "infos_sup": [("horaire", "🕒 Horaires"), ("acces_pmr", "♿ PMR")],
                "mots_cles": ["toilettes", "wc", "pipi", "sanisette"]
            },
            "⛲️ Fontaines à boire": {
                "api_id": "fontaines-a-boire",
                "col_titre": "voie", "col_adresse": "commune",
                "icone": "glass", "couleur": "cadetblue", 
                "infos_sup": [("dispo", "💧 Dispo"), ("type_objet", "⚙️ Type")],
                "mots_cles": ["eau", "boire", "fontaine"]
            },
            "🎓 Écoles Maternelles": {
                "api_id": "etablissements-scolaires-maternelles",
                "col_titre": "libelle", "col_adresse": "adresse",
                "icone": "child", "couleur": "pink", 
                "infos_sup": [("public_prive", "🏫 Secteur")],
                "mots_cles": ["ecole", "maternelle", "enfant"]
            },
             "🌳 Espaces Verts (Parcs)": {
                "api_id": "espaces_verts",
                "col_titre": "nom_ev", "col_adresse": "adresse_numero",
                "icone": "tree", "couleur": "green",
                "infos_sup": [("categorie", "🏷️ Type"), ("surface_totale_reelle", "📏 m²")],
                "mots_cles": ["parc", "jardin", "promenade", "nature"]
            },
            "📅 Sorties & Événements": {
                "api_id": "que-faire-a-paris-",
                "col_titre": "title", "col_adresse": "address_name",
                "icone": "calendar", "couleur": "orange",
                "infos_sup": [("date_start", "📅 Date"), ("price_type", "💶 Prix"), ("lead_text", "ℹ️ Info")],
                "image_col": "cover_url",
                "mots_cles": ["sorties", "evenements", "concert", "expo", "culture"]
            },
            "🛜 Bornes Wi-Fi": {
                "api_id": "sites-disposant-du-service-paris-wi-fi",
                "col_titre": "nom_site", "col_adresse": "arc_adresse",
                "icone": "wifi", "couleur": "purple", 
                "infos_sup": [("etat2", "✅ État"), ("cp", "📮 CP")],
                "mots_cles": ["wifi", "internet", "web"]
            },
            "🏗️ Chantiers Perturbants": {
                "api_id": "chantiers-perturbants",
                "col_titre": "objet", "col_adresse": "voie",
                "icone": "exclamation-triangle", "couleur": "red", 
                "infos_sup": [("date_fin", "📅 Fin"), ("impact_circulation", "🚗 Impact")],
                "mots_cles": ["travaux", "chantier", "route"]
            },
            "🔬 Laboratoires d'Analyses": {
                "api_id": "laboratoires-danalyses-medicales",
                "col_titre": "laboratoire", "col_adresse": "adresse",
                "icone": "flask", "couleur": "green", 
                "infos_sup": [("telephone", "📞 Tél"), ("horaires", "🕒 Horaires")],
                "mots_cles": ["sante", "medecin", "laboratoire","MST"]
            },
            "🆘 Défibrillateurs": {
                "api_id": "defibrillateurs",
                "col_titre": "nom_etabl", "col_adresse": "adr_post",
                "icone": "heartbeat", "couleur": "darkred", 
                "infos_sup": [("acces_daw", "🚪 Accès")],
                "mots_cles": ["coeur", "defibrillateur", "urgence"]
            },
            "🏫 Collèges": {
                "api_id": "etablissements-scolaires-colleges",
                "col_titre": "libelle", "col_adresse": "adresse",
                "icone": "graduation-cap", "couleur": "darkblue", 
                "infos_sup": [("public_prive", "🏫 Secteur")],
                "mots_cles": ["college", "education"]
            },
            "📉 Qualité de l'Air (Courbes)": {
                "api_id": "custom_meteo",
                "col_titre": "", "col_adresse": "",
                "icone": "area-chart", "couleur": "gray",
                "infos_sup": [],
                "mots_cles": ["pollution", "air", "courbe", "graphique", "meteo"]
            }
        }
    },
    "Rennes 🏁": {
        "coords_center": [48.1172, -1.6777],
        "zoom_start": 13,
        "api_url": "https://data.rennesmetropole.fr/api/explore/v2.1/catalog/datasets",
        "cp_prefix": "35",
        "alias": ["rennes", "bretagne", "35"],
        "categories": {
            "🅿️ Parkings (Citédia)": {
                "api_id": "export-api-parking-citedia",
                "col_titre": "key",
                "col_adresse": "organname",
                "icone": "parking", "couleur": "blue",
                "infos_sup": [("status", "✅ État"), ("free", "🟢 Places Libres"), ("max", "🔢 Total")],
                "mots_cles": ["parking", "garer", "voiture", "stationnement"]
            },
            "🚲 Stations Vélo Star (Temps réel)": {
                "api_id": "etat-des-stations-le-velo-star-en-temps-reel",
                "col_titre": "nom", 
                "col_adresse": "nom", 
                "icone": "bicycle", "couleur": "red",
                "infos_sup": [("nombrevelosdisponibles", "🚲 Vélos dispo"), ("nombreemplacementsdisponibles", "🅿️ Places dispo")],
                "mots_cles": ["velo", "bicyclette", "star"]
            },
             "🚌 Bus en Circulation (Temps réel)": {
                "api_id": "position-des-bus-en-circulation-sur-le-reseau-star-en-temps-reel",
                "col_titre": "nomcourtligne", 
                "col_adresse": "destination",
                "icone": "bus", "couleur": "cadetblue",
                "infos_sup": [("destination", "🏁 Vers"), ("ecartsecondes", "⏱️ Écart (sec)")],
                "mots_cles": ["bus", "transport", "star"]
            },
            "🚽 Toilettes Publiques": {
                "api_id": "toilettes_publiques_vdr",
                "col_titre": "nom_toilettes", 
                "col_adresse": "voie",
                "icone": "tint", "couleur": "green",
                "infos_sup": [("quartier", "📍 Quartier"), ("acces_pmr", "♿ PMR")],
                "mots_cles": ["toilettes", "wc", "pipi"]
            },
            "📊 Fréquentation Lignes (Stats uniquement)": {
                "api_id": "mkt-frequentation-niveau-freq-max-ligne",
                "col_titre": "ligne",
                "col_adresse": "tranche_horaire", 
                "icone": "bar-chart", "couleur": "gray",
                "infos_sup": [("frequentation", "👥 Charge"), ("tranche_horaire", "🕒 Heure")],
                "no_map": True,
                "mots_cles": ["stats", "frequentation", "monde", "charge"]
            },
            "📉 Qualité de l'Air (Courbes)": {
                "api_id": "custom_meteo",
                "col_titre": "", "col_adresse": "",
                "icone": "area-chart", "couleur": "gray",
                "infos_sup": [],
                "mots_cles": ["pollution", "air", "courbe", "graphique", "meteo"]
            }
        }
    },
    "Nantes 🐘": {
        "coords_center": [47.2184, -1.5536],
        "zoom_start": 13,
        "api_url": "https://data.nantesmetropole.fr/api/explore/v2.1/catalog/datasets",
        "cp_prefix": "44",
        "alias": ["nantes", "naoned", "44"],
        "categories": {
            "🌳 Parcs et Jardins": {
                "api_id": "244400404_parcs-jardins-nantes",
                "col_titre": "nom_complet", "col_adresse": "adresse",
                "icone": "tree", "couleur": "green",
                "infos_sup": [("type", "🏷️ Type"), ("jeux_enfants", "🛝 Jeux")],
                "mots_cles": ["parc", "jardin", "nature", "promenade"]
            },
            "🚽 Toilettes Publiques": {
                "api_id": "244400404_toilettes-publiques-nantes-metropole",
                "col_titre": "nom", "col_adresse": "adresse",
                "icone": "tint", "couleur": "blue",
                "infos_sup": [("acces_pmr", "♿ PMR"), ("commune", "📍 Ville")],
                "mots_cles": ["wc", "toilettes", "hygiene"]
            },
            "❄️ Îlots de Fraîcheur": {
                "api_id": "244400404_ilot-fraicheur-nantes-metropole",
                "col_titre": "nom", "col_adresse": "commune",
                "icone": "snowflake", "couleur": "lightblue",
                "infos_sup": [("categorie", "🏷️ Categorie"), ("commune", "📍 Ville")],
                "mots_cles": ["frais", "canicule", "climat", "nature"]
            },
            "🎉 Salles à Louer": {
                "api_id": "244400404_salles-nantes-disponibles-location",
                "col_titre": "nom_de_la_salle", 
                "col_adresse": "adresse",
                "icone": "building", "couleur": "orange",
                "infos_sup": [("telephone", "📞 Tél"), ("web", "🌐 Web"), ("capacite_reunion", "👥 Capacité")],
                "mots_cles": ["salle", "fete", "location", "mariage"]
            },
            "📅 Agenda & Événements": {
                "api_id": "244400404_agenda-evenements-nantes-metropole_v2",
                "col_titre": "nom", "col_adresse": "lieu",
                "icone": "calendar", "couleur": "pink",
                "infos_sup": [("date", "📅 Date"), ("rubrique", "🏷️ Type"), ("description", "ℹ️ Info")],
                "image_col": "media_1",
                "mots_cles": ["sortie", "evenement", "culture", "concert"]
            },
            "🏊 Piscines": {
                "api_id": "244400404_piscines-nantes-metropole",
                "col_titre": "libelle", "col_adresse": "adresse",
                "icone": "swimmer", "couleur": "blue",
                "infos_sup": [("telephone", "📞 Tél"), ("horaires_periode_scolaire", "🕒 Horaires")],
                "mots_cles": ["piscine", "nage", "sport", "eau"]
            },
            "🚲 Bicloo (Stations Vélos)": {
                "api_id": "244400404_stations-velos-libre-service-nantes-metropole",
                "col_titre": "nom", "col_adresse": "adresse",
                "icone": "bicycle", "couleur": "red",
                "infos_sup": [("status", "✅ État"), ("bike_stands", "🅿️ Bornes")],
                "mots_cles": ["velo", "bicloo", "cyclisme", "transport"]
            },
            "❤️ Défibrillateurs": {
                "api_id": "244400404_defibrillateurs-nantes",
                "col_titre": "nom_site", "col_adresse": "adresse",
                "icone": "heartbeat", "couleur": "green",
                "infos_sup": [("acces", "🚪 Accès"), ("emplacement", "📍 Emplacement")],
                "mots_cles": ["sante", "urgence", "coeur", "secours","défibrilateur"]
            },
            "🅿️ Parcs Relais (Dispo)": {
                "api_id": "244400404_parcs-relais-nantes-metropole-disponibilites",
                "col_titre": "nom_du_parc", "col_adresse": "adresse",
                "icone": "parking", "couleur": "purple",
                "infos_sup": [("grp_disponible", "🟢 Places Dispo"), ("grp_exploitation", "🔢 Total")],
                "mots_cles": ["parking", "voiture", "tan", "stationnement","garer"]
            },
            "🛜 WiFi Public Extérieur": {
                "api_id": "244400404_wifi-public-exterieur-nantes-metropole",
                "col_titre": "nom", "col_adresse": "adresse",
                "icone": "wifi", "couleur": "cadetblue",
                "infos_sup": [("etat", "✅ État"), ("localisation", "📍 Lieu")],
                "mots_cles": ["wifi", "internet", "web", "connexion"]
            },
            "📉 Qualité de l'Air (Courbes)": {
                "api_id": "custom_meteo",
                "col_titre": "", "col_adresse": "",
                "icone": "area-chart", "couleur": "gray",
                "infos_sup": [],
                "mots_cles": ["pollution", "air", "courbe", "graphique", "meteo"]
            }
        }
    }
}

COLONNES_CP_A_SCANNER = ["cp", "code_postal", "code_post", "zipcode", "commune", "location_address", "cp_arrondissement", "address_zipcode", "arrondissement"]
URL_LOGO = "logo_pulse.png" 

# ==========================================
# 2. FONCTIONS UTILES (BACKEND)
# ==========================================

def moteur_recherche(requete, config):
    """ Recherche Ville + Catégorie (ex: 'Wifi Paris') """
    requete = requete.lower().strip()
    ville_trouvee = None
    cat_trouvee = None

    for ville_nom, ville_data in config.items():
        mots_ville = [ville_nom.lower().split()[0]] + ville_data.get("alias", [])
        if any(mot in requete for mot in mots_ville):
            ville_trouvee = ville_nom
            break
    
    if ville_trouvee:
        categories = config[ville_trouvee]["categories"]
        for cat_nom, cat_data in categories.items():
            mots_cat = [cat_nom.lower()] + cat_data.get("mots_cles", [])
            if any(k in requete for k in mots_cat):
                cat_trouvee = cat_nom
                break
    return ville_trouvee, cat_trouvee

def convert_time_to_float(time_str):
    try:
        if not isinstance(time_str, str): return None
        parts = time_str.split(':')
        h = int(parts[0])
        m = int(parts[1])
        if h < 4: h += 24
        return h + (m / 60.0)
    except:
        return None

def recuperer_coordonnees(site):
    """ 
    Détective de coordonnées V3 (Spécial geom_x_y + Polygones) 
    """
    
    # 1. PRIORITÉ : Vérifier le champ 'geom_x_y' qui pose problème
    if "geom_x_y" in site:
        val = site["geom_x_y"]
        if isinstance(val, dict):
            lat = val.get('lat') or val.get('latitude') or val.get('y')
            lon = val.get('lon') or val.get('longitude') or val.get('x')
            if lat is not None and lon is not None:
                return float(lat), float(lon)
        if isinstance(val, list) and len(val) == 2:
            return float(val[0]), float(val[1])

    # 2. Cas classiques
    if "location" in site:
        loc = site["location"]
        if isinstance(loc, dict): return loc.get("lat"), loc.get("lon")
    if "latitude" in site and "longitude" in site:
        try: return float(site["latitude"]), float(site["longitude"])
        except: pass
    if "lat_lon" in site:
        ll = site["lat_lon"]
        if isinstance(ll, dict): return ll.get("lat"), ll.get("lon")
    if "geo" in site:
        g = site["geo"]
        if isinstance(g, dict): return g.get("lat"), g.get("lon")
        
    for cle in ["geolocalisation", "coordonnees", "geo_point_2d", "xy"]:
        val = site.get(cle)
        if val:
            if isinstance(val, dict): return val.get("lat"), val.get("lon")
            if isinstance(val, list) and len(val) == 2: return val[0], val[1]
            if isinstance(val, str) and "," in val:
                try:
                    parts = val.split(",")
                    return float(parts[0].strip()), float(parts[1].strip())
                except: pass

    # 3. GESTION DES POLYGONES (Pour l'Occupation du Sol et Parcs)
    geom = site.get("geometry")
    if geom and isinstance(geom, dict):
        g_type = geom.get("type")
        coords = geom.get("coordinates")
        
        if g_type == "Point" and coords:
            return coords[1], coords[0]
            
        elif g_type in ["Polygon", "MultiPolygon"] and coords:
            try:
                def flatten(container):
                    for i in container:
                        if isinstance(i, list) and len(i) == 2 and isinstance(i[0], (int, float)):
                            yield i
                        elif isinstance(i, list):
                            yield from flatten(i)
                all_points = list(flatten(coords))
                if all_points:
                    avg_lon = sum(p[0] for p in all_points) / len(all_points)
                    avg_lat = sum(p[1] for p in all_points) / len(all_points)
                    return avg_lat, avg_lon
            except: pass

    return None, None

def extraire_cp_intelligent(site_data, col_adresse_config, prefixe_cp="75"):
    """
    Extraction INTELLIGENTE pour Paris (gère 'PARIS 12E', '75012', etc.)
    """
    regex_std = rf'{prefixe_cp}\d{{3}}'
    
    # 1. Scan des colonnes candidates
    for col in COLONNES_CP_A_SCANNER:
        val = str(site_data.get(col, "")).strip()
        
        # A. Cas standard : 75012
        match = re.search(regex_std, val)
        if match:
            return match.group(0)
            
        # B. Cas Spécial Paris : "PARIS 12E ARRDT" (pour Fontaines)
        if prefixe_cp == "75" and "paris" in val.lower():
            match_arr = re.search(r"paris\s*(\d+)", val.lower())
            if match_arr:
                num = int(match_arr.group(1))
                if 1 <= num <= 20:
                    return f"75{num:03d}" # Transforme 12 en 75012

    # 2. Scan de l'adresse brute
    adresse = str(site_data.get(col_adresse_config, ""))
    match = re.search(regex_std, adresse)
    if match:
        return match.group(0)
    
    # 3. Scan adresse brute pour "Paris Xe"
    if prefixe_cp == "75" and "paris" in adresse.lower():
        match_arr = re.search(r"paris\s*(\d+)", adresse.lower())
        if match_arr:
            num = int(match_arr.group(1))
            if 1 <= num <= 20:
                return f"75{num:03d}"

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
        time.sleep(1)
    except:
        pass

# CACHE ACTIF (2 HEURES)
@st.cache_data(ttl=7200, show_spinner=False) 
def charger_donnees(base_url, api_id, cible=500):
    headers = {'User-Agent': 'Mozilla/5.0'}
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

@st.cache_data
def charger_meteo_pollution(lat, lon):
    url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "pm10,pm2_5,nitrogen_dioxide,ozone,aerosol_optical_depth",
        "timezone": "Europe/Paris",
        "past_days": 3,
        "forecast_days": 2
    }
    try:
        r = requests.get(url, params=params)
        data = r.json()
        hourly = data.get("hourly", {})
        df = pd.DataFrame(hourly)
        mapper = {
            "time": "Heure",
            "pm10": "Particules PM10",
            "pm2_5": "Particules PM2.5",
            "nitrogen_dioxide": "Dioxyde d'Azote (NO2)",
            "ozone": "Ozone (O3)",
            "aerosol_optical_depth": "Densité Aérosol"
        }
        df = df.rename(columns=mapper)
        return df
    except Exception as e:
        return pd.DataFrame()

# Fonction simple pour météo temps réel (Widget Sidebar)
def get_current_weather(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": "true"
    }
    try:
        r = requests.get(url, params=params)
        return r.json().get("current_weather", {})
    except: return None

# ==========================================
# 3. INTERFACE STREAMLIT
# ==========================================

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

if 'ville_selectionnee' not in st.session_state:
    st.session_state.ville_selectionnee = list(CONFIG_VILLES.keys())[0]
if 'cat_selectionnee' not in st.session_state:
    st.session_state.cat_selectionnee = list(CONFIG_VILLES[st.session_state.ville_selectionnee]["categories"].keys())[0]
if 'dernier_choix' not in st.session_state:
    st.session_state.dernier_choix = None

col_logo, col_titre = st.columns([2, 10])
with col_logo:
    try: st.image(URL_LOGO, width=150)
    except: st.warning("Logo introuvable")

with col_titre:
    st.title("City Pulse") 
    st.markdown("#### Le tableau de bord intelligent de vos villes 🌍💓")

st.divider()

# --- SIDEBAR & LOGIQUE AVEC LISTES DYNAMIQUES & MICRO ---
with st.sidebar:
    try: st.image(URL_LOGO, width=60)
    except: pass
    
    st.header("🔍 Recherche Magique")
    
    def valider_recherche():
        requete = st.session_state.recherche_input
        if requete:
            ville, cat = moteur_recherche(requete, CONFIG_VILLES)
            if ville:
                st.session_state.ville_selectionnee = ville
                if cat:
                    st.session_state.cat_selectionnee = cat
                    st.success(f"Go : {cat} à {ville}")
                else:
                    st.warning(f"Ville changée pour {ville}. Précisez la catégorie.")
            else:
                st.error("Je n'ai pas compris (ex: 'Wifi Paris').")

    # --- ZONE DE RECHERCHE AVEC MICRO ---
    col_text, col_mic = st.columns([8, 2])
    with col_mic:
        text_vocal = speech_to_text(language='fr', start_prompt="🎤 Parler", stop_prompt="🛑 Arrêter", just_once=True, key='STT')

    if text_vocal:
        st.session_state.recherche_input = text_vocal
        valider_recherche() # On lance la recherche
        st.rerun() # On recharge la page pour afficher le texte dans la barre

    with col_text:
        st.text_input(
            "Ex: 'Parking Rennes', 'Wifi Paris'", 
            key="recherche_input", 
            on_change=valider_recherche, 
            label_visibility="collapsed"
        )

    st.divider()
    st.header("📍 Destination")
    
    # 1. Choix de la Ville
    ville_actuelle = st.selectbox("Choisir une ville :", options=list(CONFIG_VILLES.keys()), key="ville_selectionnee")
    config_ville = CONFIG_VILLES[ville_actuelle]
    all_categories = config_ville["categories"]
    
    # --- WIDGET MÉTÉO (NOUVEAU) ---
    weather_now = get_current_weather(config_ville["coords_center"][0], config_ville["coords_center"][1])
    if weather_now:
        temp = weather_now.get("temperature")
        st.info(f"⛅ Météo actuelle : **{temp}°C**")
    
    st.divider()
    
    # --- LOGIQUE DE LISTES DYNAMIQUES (THEME -> DONNEE) ---
    THEMES = {
        "🚍 Transport": ["parking", "vélo", "bus", "bicloo", "parcs relais", "métro"],
        "🌿 Nature & Air": ["vert", "jardin", "air", "pollution", "parc", "fraîcheur", "occupation"],
        "🎭 Culture & Sorties": ["sortie", "événement", "agenda", "salle", "piscine"],
        "⚕️ Santé & Sécurité": ["défibrillateur", "laboratoire", "secours", "urgence"],
        "🚸 Éducation & Enfance": ["école", "collège", "crèche", "maternelle"],
        "🛠️ Services & Vie Pratique": ["wifi", "toilette", "sanisette", "fontaine", "chantier"]
    }

    def trouver_theme(nom_cat):
        nom_clean = nom_cat.lower()
        for theme, mots_cles in THEMES.items():
            if any(mot in nom_clean for mot in mots_cles):
                return theme
        return "📂 Autres" 

    cats_par_theme = {}
    for cat in all_categories.keys():
        th = trouver_theme(cat)
        if th not in cats_par_theme: cats_par_theme[th] = []
        cats_par_theme[th].append(cat)
    
    # --- FIX: FORCER LE THEME SI UNE RECHERCHE A ÉTÉ FAITE ---
    theme_par_defaut = 0
    cat_actuelle = st.session_state.cat_selectionnee
    
    # On trouve le thème de la catégorie actuelle
    theme_trouve = trouver_theme(cat_actuelle)
    liste_themes = sorted(list(cats_par_theme.keys()))
    
    if theme_trouve in liste_themes:
        theme_par_defaut = liste_themes.index(theme_trouve)

    theme_selectionne = st.selectbox("1️⃣ Filtrer par Thème :", liste_themes, index=theme_par_defaut)
    
    # Liste filtrée
    liste_cats_filtree = cats_par_theme[theme_selectionne]
    
    index_cat = 0
    if st.session_state.cat_selectionnee in liste_cats_filtree:
        index_cat = liste_cats_filtree.index(st.session_state.cat_selectionnee)
        
    choix_utilisateur_brut = st.selectbox("2️⃣ Choisir la donnée :", options=liste_cats_filtree, index=index_cat)
    
    st.session_state.cat_selectionnee = choix_utilisateur_brut
    
    st.divider()
    st.header("⚙️ Paramètres")
    activer_voix = st.checkbox("Activer l'assistant vocal", value=True)
    
    config_data = all_categories[choix_utilisateur_brut]
    if config_data.get("no_map"):
        type_visu = "STATS"
    else:
        type_visu = "CARTE"

    mode_filtre = False
    filtre_texte = ""
    if type_visu == "CARTE" and config_data.get("api_id") != "custom_meteo":
        st.header("🔎 Filtres")
        mode_filtre = st.toggle("Filtrer par zone", value=False)
        if mode_filtre:
            filtre_texte = st.text_input("Recherche zone :")

# --- CHARGEMENT DES DONNÉES ---
choix_utilisateur = choix_utilisateur_brut
cle_unique = f"{ville_actuelle}_{choix_utilisateur}"

if cle_unique != st.session_state.dernier_choix:
    if activer_voix:
        jouer_son_automatique(f"Chargement : {ville_actuelle}, {choix_utilisateur}")
    st.session_state.dernier_choix = cle_unique

# =========================================================
# BRANCHEMENT A : SI C'EST NOS COURBES 
# =========================================================
if config_data.get("api_id") == "custom_meteo":
    st.subheader(f"📉 Évolution de la pollution : {ville_actuelle}")
    
    with st.spinner("Récupération des données atmosphériques..."):
        lat, lon = config_ville["coords_center"]
        df_meteo = charger_meteo_pollution(lat, lon)
    
    if not df_meteo.empty:
        cols_dispo = [c for c in df_meteo.columns if c != "Heure"]
        
        choix_courbe = st.multiselect(
            "Choisissez les indicateurs à tracer :", 
            options=cols_dispo, 
            default=["Particules PM10", "Ozone (O3)"]
        )
        
        if choix_courbe:
            df_long = df_meteo.melt('Heure', value_vars=choix_courbe, var_name='Indicateur', value_name='Concentration')
            
            chart = alt.Chart(df_long).mark_line(point=True).encode(
                x=alt.X('Heure:T', title="Temps"),
                y=alt.Y('Concentration:Q', title="Concentration (µg/m³)"),
                color='Indicateur:N',
                tooltip=['Heure', 'Indicateur', 'Concentration']
            ).properties(height=450).interactive()
            
            st.altair_chart(chart, use_container_width=True)
            st.info("💡 Note : Données via Open-Meteo (Historique 3j + Prévisions 48h).")
        else:
            st.warning("Veuillez sélectionner au moins une donnée à afficher.")
            
        with st.expander("Voir les données brutes"):
            st.dataframe(df_meteo)
    else:
        st.error("Impossible de récupérer les données météo.")

# =========================================================
# BRANCHEMENT B : LE CODE CLASSIQUE (CARTES / API)
# =========================================================
else:
    with st.spinner(f"Chargement des données de {ville_actuelle}..."):
        limit_req = 1000 if "frequentation" in config_data["api_id"] else 600
        raw_data = charger_donnees(config_ville["api_url"], config_data["api_id"], cible=limit_req)

    tous_resultats = raw_data if isinstance(raw_data, list) else []

    # --- FILTRAGE TEXTUEL ---
    resultats_finaux = []
    if len(tous_resultats) > 0:
        if mode_filtre and filtre_texte:
            input_clean = filtre_texte.lower().strip()
            mots_a_chercher = [input_clean]
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
            if type_visu == "CARTE":
                st.success(f"🌍 {ville_actuelle} : {len(resultats_finaux)} lieux trouvés.")
    else:
        st.info("Pas de données disponibles pour cette catégorie.")

    # --- AFFICHAGE ---
    if type_visu == "STATS":
        tab_stats, tab_donnees = st.tabs(["📊 Statistiques", "📋 Données"])
        tab_carte = None 
    else:
        tab_carte, tab_stats, tab_donnees = st.tabs(["🗺️ Carte", "📊 Statistiques", "📋 Données"])

    if tab_carte:
        with tab_carte:
            # --- SÉLECTEUR DE STYLE DE CARTE ---
            c1, c2 = st.columns([1, 1])
            with c1:
                style_vue = st.radio("Vue :", ["📍 Points", "🔥 Densité"], horizontal=True)
            with c2:
                fond_carte = st.selectbox("Fond de plan :", ["Clair (Défaut)", "Sombre (Nuit)", "Satellite"])
            
            # Configuration du fond
            tiles_layer = "OpenStreetMap" # Défaut
            attr = None
            if fond_carte == "Sombre (Nuit)":
                tiles_layer = "CartoDB dark_matter"
                attr = "CartoDB"
            elif fond_carte == "Satellite":
                tiles_layer = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                attr = "Esri"

            m = folium.Map(
                location=config_ville["coords_center"], 
                zoom_start=config_ville["zoom_start"],
                tiles=tiles_layer,
                attr=attr
            )
            
            # --- CLUSTERING POUR LA PERF ---
            marker_cluster = MarkerCluster().add_to(m) if style_vue == "📍 Points" else None
            coords_heatmap = []
            
            for site in resultats_finaux:
                lat, lon = recuperer_coordonnees(site)

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

                        # LIEN GOOGLE MAPS
                        gmaps_link = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}"
                        
                        popup_content = f"""
                        {html_image}
                        <b>{titre}</b><br>
                        <i>{adresse}</i><br>
                        <a href="{gmaps_link}" target="_blank" style="text-decoration:none;">
                            <button style="margin-top:5px;cursor:pointer;">📍 Y aller</button>
                        </a>
                        """
                        
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
                        ).add_to(marker_cluster if marker_cluster else m)

            if style_vue == "🔥 Densité" and coords_heatmap:
                HeatMap(coords_heatmap, radius=15).add_to(m)
            
            if coords_heatmap or style_vue == "📍 Points":
                
                # --- BOUTON DE TELECHARGEMENT ---
                carte_html = m.get_root().render()
                st.download_button(
                    label="💾 Télécharger la carte interactive (HTML)",
                    data=carte_html,
                    file_name=f"carte_{ville_actuelle}_{choix_utilisateur}.html",
                    mime="text/html"
                )
                
                st_folium(m, width=1000, height=600, returned_objects=[])
            else:
                st.warning("⚠️ Aucune coordonnée GPS trouvée.")

    with tab_stats:
        st.subheader(f"📊 Analyse : {ville_actuelle}")
        
        if len(resultats_finaux) > 0:
            # --- CAS SPÉCIAL : BUS RENNES (Fréquentation) ---
            if config_data["api_id"] == "mkt-frequentation-niveau-freq-max-ligne":
                df = pd.DataFrame(resultats_finaux)
                df.columns = [c.lower() for c in df.columns]
                df = df.loc[:, ~df.columns.duplicated()]
                
                if "frequentation" in df.columns: col_target = "frequentation"
                elif "niveau_frequentation" in df.columns: col_target = "niveau_frequentation"
                else: col_target = None

                map_dict = {
                    "ligne": "ligne", "tranche_horaire": "tranche_horaire",
                    "jour_semaine": "jour", col_target: "frequentation"
                }

                if col_target and "ligne" in df.columns and "tranche_horaire" in df.columns:
                    df = df.rename(columns={k:v for k,v in map_dict.items() if k in df.columns})
                    if 'jour' in df.columns:
                        df['jour'] = df['jour'].fillna("Indéfini")
                        périodes = sorted(df['jour'].unique().astype(str).tolist())
                        if périodes:
                            idx = next((i for i, p in enumerate(périodes) if "lundi" in p.lower()), 0)
                            choix_jour = st.selectbox("📅 Choisir le jour à afficher :", périodes, index=idx)
                            df = df[df['jour'] == choix_jour]

                    df["frequentation"] = df["frequentation"].fillna("Non ouverte").replace("", "Non ouverte")
                    def normaliser_freq(val):
                        val = str(val).lower().strip()
                        if "faible" in val: return "Faible"
                        if "moyen" in val: return "Moyenne"
                        if "haute" in val or "forte" in val: return "Forte"
                        return "Non ouverte"
                    df["frequentation"] = df["frequentation"].apply(normaliser_freq)

                    df['heure_debut'] = df['tranche_horaire'].apply(convert_time_to_float)
                    df = df.sort_values(by=['ligne', 'heure_debut'])
                    df['heure_fin'] = df.groupby('ligne')['heure_debut'].shift(-1)
                    df['heure_fin'] = df['heure_fin'].fillna(df['heure_debut'] + 0.5)
                    df['duree'] = df['heure_fin'] - df['heure_debut']
                    df_clean = df[df['duree'] > 0].copy()

                    if not df_clean.empty:
                        st.write(f"### 🟢 Répartition de la charge ({choix_jour})")
                        masquer_non_ouvert = st.checkbox("Masquer les périodes 'Non ouverte'", value=True)
                        df_viz = df_clean.copy()
                        if masquer_non_ouvert:
                            df_viz = df_viz[df_viz['frequentation'] != "Non ouverte"]

                        dom = ['Faible', 'Moyenne', 'Forte', 'Non ouverte']
                        rng = ['#2ecc71', '#f1c40f', '#8e44ad', '#FF0000']

                        chart = alt.Chart(df_viz).mark_bar().encode(
                            y=alt.Y('ligne', title="Ligne"),
                            x=alt.X('sum(duree)', stack='normalize', axis=alt.Axis(format='%'), title="% Temps Actif"),
                            color=alt.Color('frequentation:N', scale=alt.Scale(domain=dom, range=rng), legend=alt.Legend(title="Charge")),
                            tooltip=['ligne', 'frequentation', alt.Tooltip('sum(duree)', format='.1f', title='Heures')]
                        ).interactive()
                        st.altair_chart(chart, use_container_width=True)
                        
                        st.write("### 📅 Planning Horaire")
                        heatmap = alt.Chart(df_clean).mark_rect().encode(
                            x=alt.X('heure_debut:Q', title="Heure (5h - 01h+)", scale=alt.Scale(domain=[4, 28])),
                            x2='heure_fin:Q',
                            y=alt.Y('ligne:N', sort='ascending'),
                            color=alt.Color('frequentation:N', scale=alt.Scale(domain=dom, range=rng)),
                            tooltip=['ligne', 'tranche_horaire', 'frequentation']
                        ).properties(height=max(400, len(df_clean['ligne'].unique())*20)).interactive()
                        st.altair_chart(heatmap, use_container_width=True)
                    else:
                        st.warning("⚠️ Pas de données horaires valides.")
                else:
                    st.error("⚠️ Colonnes API Bus introuvables.")

            # --- CAS GÉNÉRAL ---
            else:
                col1, col2 = st.columns(2)
                with col1: st.metric("Total éléments", len(resultats_finaux))
                
                liste_cp = []
                for s in resultats_finaux:
                    cp = extraire_cp_intelligent(s, config_data["col_adresse"], prefixe_cp=config_ville["cp_prefix"])
                    if cp == "Inconnu": cp = str(s.get("address_zipcode", "Inconnu"))
                    if cp != "Inconnu" and config_ville["cp_prefix"] in cp: 
                        liste_cp.append(cp)
                
                if len(liste_cp) > 0:
                    df = pd.DataFrame(liste_cp, columns=["Zone / CP"])
                    compte = df["Zone / CP"].value_counts().sort_index()
                    st.bar_chart(compte)
                else:
                    st.info("Données géographiques insuffisantes pour un graphique.")
        else:
            st.info("Pas de données à analyser.")

    with tab_donnees:
        st.dataframe(resultats_finaux)
        if len(resultats_finaux) > 0:
             with st.expander("🔍 Débogage (Voir format 1er élément)"):
                 st.write(resultats_finaux[0])

# ==========================================
# 4. SECTION : LABO DE CORRÉLATIONS (V2)
# ==========================================
st.divider()
st.header("🧪 Labo de Corrélations")
st.markdown("""
Recherche de liens entre deux données. 
* **Paris** : Regroupement par Arrondissement (CP).
* **Nantes/Rennes** : Regroupement par Zone Géographique (Carrés de ~1km²).
""")

with st.expander("Créer une analyse croisée", expanded=True):
    col_a, col_b = st.columns(2)
    
    liste_cats_dispo = list(CONFIG_VILLES[ville_actuelle]["categories"].keys())
    # On enlève "Meteo" car pas de CP
    liste_cats_dispo = [c for c in liste_cats_dispo if "Meteo" not in c and "Courbe" not in c]
    
    cat_a = col_a.selectbox("Axe X (Donnée A)", liste_cats_dispo, index=0)
    idx_b = 1 if len(liste_cats_dispo) > 1 else 0
    cat_b = col_b.selectbox("Axe Y (Donnée B)", liste_cats_dispo, index=idx_b)
    
    if st.button("Lancer la corrélation"):
        if cat_a == cat_b:
            st.warning("Choisissez deux catégories différentes.")
        else:
            with st.spinner("Calcul des zones et croisements..."):
                conf_a = CONFIG_VILLES[ville_actuelle]["categories"][cat_a]
                conf_b = CONFIG_VILLES[ville_actuelle]["categories"][cat_b]
                
                data_a = charger_donnees(CONFIG_VILLES[ville_actuelle]["api_url"], conf_a["api_id"])
                data_b = charger_donnees(CONFIG_VILLES[ville_actuelle]["api_url"], conf_b["api_id"])
                
                # --- FONCTION INTELLIGENTE : SI PAS PARIS, ON UTILISE LA GRILLE GPS ---
                def get_zone_id(item, conf, ville_nom, prefix):
                    # 1. Essayer le Code Postal (Prioritaire pour Paris)
                    if "Paris" in ville_nom:
                        cp = extraire_cp_intelligent(item, conf.get("col_adresse", ""), prefix)
                        if prefix in str(cp) and "Inconnu" not in str(cp):
                            return cp
                    
                    # 2. Sinon (Nantes/Rennes), on fait un maillage GPS (Grid System)
                    lat, lon = recuperer_coordonnees(item)
                    if lat and lon:
                        # MODIFICATION ICI : Retour à round(2) pour éviter NaN
                        grid_lat = round(lat, 2) 
                        grid_lon = round(lon, 2)
                        return f"Zone GPS {grid_lat}/{grid_lon}"
                    
                    return None

                def compter_par_zone_intelligente(data, conf, ville_nom, prefix):
                    zones = []
                    for item in data:
                        z = get_zone_id(item, conf, ville_nom, prefix)
                        if z: zones.append(z)
                    return pd.Series(zones).value_counts()

                # Création des séries
                prefixe_ville = CONFIG_VILLES[ville_actuelle]["cp_prefix"]
                serie_a = compter_par_zone_intelligente(data_a, conf_a, ville_actuelle, prefixe_ville)
                serie_b = compter_par_zone_intelligente(data_b, conf_b, ville_actuelle, prefixe_ville)
                
                # Fusion
                df_corr = pd.concat([serie_a, serie_b], axis=1, keys=['Data_A', 'Data_B']).dropna()
                df_corr['Zone'] = df_corr.index
                
                if not df_corr.empty and len(df_corr) > 2:
                    st.write(f"### Résultat sur {len(df_corr)} zones détectées")
                    
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        chart_corr = alt.Chart(df_corr).mark_circle(size=100).encode(
                            x=alt.X('Data_A', title=f"Nombre : {cat_a}"),
                            y=alt.Y('Data_B', title=f"Nombre : {cat_b}"),
                            color=alt.Color('Zone', legend=None),
                            tooltip=['Zone', 'Data_A', 'Data_B']
                        ).interactive()
                        st.altair_chart(chart_corr, use_container_width=True)
                    
                    with c2:
                        corr = df_corr['Data_A'].corr(df_corr['Data_B'])
                        st.metric("Corrélation", f"{corr:.2f}")
                        if corr > 0.5: st.success("📈 Lien Positif")
                        elif corr < -0.5: st.warning("📉 Lien Négatif")
                        else: st.info("😐 Pas de lien net")
                else:
                    st.error("Pas assez de données géographiques communes.")
                    st.write("Conseil : Vérifiez que les deux catégories ont bien des coordonnées GPS.")
