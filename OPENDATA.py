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
            "🚽 Sanisettes (Toilettes)": {
                "api_id": "sanisettesparis",
                "col_titre": "libelle", "col_adresse": "adresse",
                "icone": "tint", "couleur": "blue", 
                "infos_sup": [("horaire", "🕒 Horaires"), ("acces_pmr", "♿ PMR")],
                "mots_cles": ["toilettes", "wc", "pipi"]
            },
            "⛲️ Fontaines à boire": {
                "api_id": "fontaines-a-boire",
                "col_titre": "voie", "col_adresse": "commune",
                "icone": "glass", "couleur": "cadetblue", 
                "infos_sup": [("dispo", "💧 Dispo"), ("type_objet", "⚙️ Type")],
                "mots_cles": ["eau", "boire", "fontaine"]
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
            "🎓 Écoles Maternelles": {
                "api_id": "etablissements-scolaires-maternelles",
                "col_titre": "libelle", "col_adresse": "adresse",
                "icone": "child", "couleur": "pink", 
                "infos_sup": [("public_prive", "🏫 Secteur")],
                "mots_cles": ["ecole", "maternelle", "enfant"]
            },
            # --- NOUVELLE CATEGORIE ---
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

COLONNES_CP_A_SCANNER = ["cp", "code_postal", "code_post", "zipcode", "commune", "location_address", "cp_arrondissement", "address_zipcode"]
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
    """ Détective de coordonnées """
    if "location" in site:
        loc = site["location"]
        if isinstance(loc, dict): 
            return loc.get("lat"), loc.get("lon")

    if "latitude" in site and "longitude" in site:
        try:
            return float(site["latitude"]), float(site["longitude"])
        except: pass
        
    if "lat_lon" in site:
        ll = site["lat_lon"]
        if isinstance(ll, dict): return ll.get("lat"), ll.get("lon")
    if "geo" in site:
        g = site["geo"]
        if isinstance(g, dict): return g.get("lat"), g.get("lon")
        
    for cle in ["geolocalisation", "coordonnees", "geo_point_2d"]:
        val = site.get(cle)
        if val:
            if isinstance(val, dict): return val.get("lat"), val.get("lon")
            if isinstance(val, list) and len(val) == 2: return val[0], val[1]
            if isinstance(val, str) and "," in val:
                try:
                    parts = val.split(",")
                    return float(parts[0].strip()), float(parts[1].strip())
                except: pass

    geom = site.get("geometry")
    if geom and isinstance(geom, dict) and geom.get("type") == "Point":
        coords = geom.get("coordinates")
        if coords and len(coords) == 2: return coords[1], coords[0] 
        
    return None, None

def extraire_cp_intelligent(site_data, col_adresse_config, prefixe_cp="75"):
    cp_trouve = None
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
        if prefixe_cp == "75" and cp_trouve.startswith("751") and len(cp_trouve) == 5:
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
        time.sleep(1)
    except:
        pass

@st.cache_data 
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
    """
    Récupère l'historique et le prévisionnel pollution/météo
    Via Open-Meteo (Gratuit, pas de clé API nécessaire)
    """
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
        
        # Transformation en DataFrame
        hourly = data.get("hourly", {})
        df = pd.DataFrame(hourly)
        
        # Renommer pour faire joli sur le graph
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

# --- SIDEBAR & LOGIQUE ---
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

    st.text_input("Ex: 'Parking Rennes', 'Wifi Paris'", key="recherche_input", on_change=valider_recherche)

    st.divider()
    st.header("📍 Destination")
    
    ville_actuelle = st.selectbox("Choisir une ville :", options=list(CONFIG_VILLES.keys()), key="ville_selectionnee")
    config_ville = CONFIG_VILLES[ville_actuelle]
    all_categories = config_ville["categories"]
    
    st.divider()
    
    if st.session_state.cat_selectionnee not in all_categories:
        st.session_state.cat_selectionnee = list(all_categories.keys())[0]

    liste_cats = list(all_categories.keys())
    try:
        index_cat = liste_cats.index(st.session_state.cat_selectionnee)
    except ValueError:
        index_cat = 0
        
    choix_utilisateur_brut = st.selectbox("Choisir une donnée :", options=liste_cats, index=index_cat)
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
# 🔴 BRANCHEMENT A : SI C'EST NOS COURBES (NOUVEAU CODE)
# =========================================================
if config_data.get("api_id") == "custom_meteo":
    st.subheader(f"📉 Évolution de la pollution : {ville_actuelle}")
    
    with st.spinner("Récupération des données atmosphériques..."):
        lat, lon = config_ville["coords_center"]
        df_meteo = charger_meteo_pollution(lat, lon)
    
    if not df_meteo.empty:
        # 1. Sélecteur de courbe (Ce que ton prof veut !)
        cols_dispo = [c for c in df_meteo.columns if c != "Heure"]
        
        # Widget pour choisir les courbes
        choix_courbe = st.multiselect(
            "Choisissez les indicateurs à tracer :", 
            options=cols_dispo, 
            default=["Particules PM10", "Ozone (O3)"]
        )
        
        if choix_courbe:
            # 2. Tracer la courbe avec Altair
            # On transforme le tableau pour qu'il soit lisible par Altair (format long)
            df_long = df_meteo.melt('Heure', value_vars=choix_courbe, var_name='Indicateur', value_name='Concentration')
            
            chart = alt.Chart(df_long).mark_line(point=True).encode(
                x=alt.X('Heure:T', title="Temps"), # T pour Time
                y=alt.Y('Concentration:Q', title="Concentration (µg/m³)"),
                color='Indicateur:N',
                tooltip=['Heure', 'Indicateur', 'Concentration']
            ).properties(height=450).interactive()
            
            st.altair_chart(chart, use_container_width=True)
            
            st.info("💡 Note : Les données incluent l'historique récent (3 jours) et les prévisions pour les 48h à venir.")
        else:
            st.warning("Veuillez sélectionner au moins une donnée à afficher dans le menu ci-dessus.")
            
        with st.expander("Voir les données brutes"):
            st.dataframe(df_meteo)
    else:
        st.error("Impossible de récupérer les données météo pour cette localisation.")

# =========================================================
# 🔵 BRANCHEMENT B : LE CODE CLASSIQUE (CARTES / API)
# =========================================================
else:
    with st.spinner(f"Chargement des données de {ville_actuelle}..."):
        limit_req = 500 if "frequentation" in config_data["api_id"] else 500
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
            style_vue = st.radio("Vue :", ["📍 Points", "🔥 Densité"], horizontal=True)
            m = folium.Map(location=config_ville["coords_center"], zoom_start=config_ville["zoom_start"])
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
            
            if coords_heatmap or style_vue == "📍 Points":
                st_folium(m, width=1000, height=600, returned_objects=[])
            else:
                st.warning("⚠️ Aucune coordonnée GPS trouvée (Vérifiez les données brutes dans l'onglet Données).")

    with tab_stats:
        st.subheader(f"📊 Analyse : {ville_actuelle}")
        
        if len(resultats_finaux) > 0:
            # --- CAS SPÉCIAL : BUS RENNES (Fréquentation) ---
            if config_data["api_id"] == "mkt-frequentation-niveau-freq-max-ligne":
                df = pd.DataFrame(resultats_finaux)
                
                # 1. Normalisation des colonnes
                df.columns = [c.lower() for c in df.columns]
                df = df.loc[:, ~df.columns.duplicated()]
                
                # 2. SÉLECTION STRICTE DE LA COLONNE
                if "frequentation" in df.columns: col_target = "frequentation"
                elif "niveau_frequentation" in df.columns: col_target = "niveau_frequentation"
                else: col_target = None

                map_dict = {
                    "ligne": "ligne",
                    "tranche_horaire": "tranche_horaire",
                    "jour_semaine": "jour",
                    col_target: "frequentation"
                }

                if col_target and "ligne" in df.columns and "tranche_horaire" in df.columns:
                    df = df.rename(columns={k:v for k,v in map_dict.items() if k in df.columns})

                    # 3. FILTRE JOUR
                    if 'jour' in df.columns:
                        df['jour'] = df['jour'].fillna("Indéfini")
                        périodes = sorted(df['jour'].unique().astype(str).tolist())
                        if périodes:
                            idx = next((i for i, p in enumerate(périodes) if "lundi" in p.lower()), 0)
                            choix_jour = st.selectbox("📅 Choisir le jour à afficher :", périodes, index=idx)
                            df = df[df['jour'] == choix_jour]

                    # 4. NETTOYAGE ET CONVERSION
                    df["frequentation"] = df["frequentation"].fillna("Non ouverte").replace("", "Non ouverte")
                    
                    def normaliser_freq(val):
                        val = str(val).lower().strip()
                        if "faible" in val: return "Faible"
                        if "moyen" in val: return "Moyenne"
                        if "haute" in val or "forte" in val: return "Forte"
                        return "Non ouverte"

                    df["frequentation"] = df["frequentation"].apply(normaliser_freq)

                    # --- LOGIQUE DE TEMPS (GANTT) ---
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
                            color=alt.Color('frequentation:N', 
                                            scale=alt.Scale(domain=dom, range=rng),
                                            legend=alt.Legend(title="Charge")),
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

            # --- CAS GÉNÉRAL (Bar chart des Codes Postaux) ---
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
