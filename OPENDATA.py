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
# 1. CONFIGURATION MULTI-VILLES
# ==========================================

CONFIG_VILLES = {
    "Paris 🗼": {
        "coords_center": [48.8566, 2.3522],
        "zoom_start": 12,
        "api_url": "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets",
        "cp_prefix": "75",
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
            "Fontaines à boire": {
                "api_id": "fontaines-a-boire",
                "col_titre": "voie", "col_adresse": "commune",
                "icone": "glass", "couleur": "cadetblue", 
                "infos_sup": [("dispo", "💧 Dispo"), ("type_objet", "⚙️ Type")]
            },
            "Chantiers Perturbants": {
                "api_id": "chantiers-perturbants",
                "col_titre": "objet", "col_adresse": "voie",
                "icone": "exclamation-triangle", "couleur": "red", 
                "infos_sup": [("date_fin", "📅 Fin"), ("impact_circulation", "🚗 Impact")]
            },
            "Laboratoires d'Analyses": {
                "api_id": "laboratoires-danalyses-medicales",
                "col_titre": "laboratoire", "col_adresse": "adresse",
                "icone": "flask", "couleur": "green", 
                "infos_sup": [("telephone", "📞 Tél"), ("horaires", "🕒 Horaires")]
            },
            "Défibrillateurs": {
                "api_id": "defibrillateurs",
                "col_titre": "nom_etabl", "col_adresse": "adr_post",
                "icone": "heartbeat", "couleur": "darkred", 
                "infos_sup": [("acces_daw", "🚪 Accès")]
            },
            "Collèges": {
                "api_id": "etablissements-scolaires-colleges",
                "col_titre": "libelle", "col_adresse": "adresse",
                "icone": "graduation-cap", "couleur": "darkblue", 
                "infos_sup": [("public_prive", "🏫 Secteur")]
            },
            "Écoles Maternelles": {
                "api_id": "etablissements-scolaires-maternelles",
                "col_titre": "libelle", "col_adresse": "adresse",
                "icone": "child", "couleur": "pink", 
                "infos_sup": [("public_prive", "🏫 Secteur")]
            }
        }
    },
    "Rennes 🏁": {
        "coords_center": [48.1172, -1.6777],
        "zoom_start": 13,
        "api_url": "https://data.rennesmetropole.fr/api/explore/v2.1/catalog/datasets",
        "cp_prefix": "35",
        "categories": {
            "🅿️ Parkings (Citédia)": {
                "api_id": "export-api-parking-citedia",
                "col_titre": "key",
                "col_adresse": "organname",
                "icone": "parking", "couleur": "blue",
                "infos_sup": [("status", "✅ État"), ("free", "🟢 Places Libres"), ("max", "🔢 Total")]
            },
            "🚲 Stations Vélo Star (Temps réel)": {
                "api_id": "etat-des-stations-le-velo-star-en-temps-reel",
                "col_titre": "nom", 
                "col_adresse": "nom", 
                "icone": "bicycle", "couleur": "red",
                "infos_sup": [("nombrevelosdisponibles", "🚲 Vélos dispo"), ("nombreemplacementsdisponibles", "🅿️ Places dispo")]
            },
             "🚌 Bus en Circulation (Temps réel)": {
                "api_id": "position-des-bus-en-circulation-sur-le-reseau-star-en-temps-reel",
                "col_titre": "nomcourtligne", 
                "col_adresse": "destination",
                "icone": "bus", "couleur": "cadetblue",
                "infos_sup": [("destination", "🏁 Vers"), ("ecartsecondes", "⏱️ Écart (sec)")]
            },
            "🚽 Toilettes Publiques": {
                "api_id": "toilettes_publiques_vdr",
                "col_titre": "nom_toilettes", 
                "col_adresse": "voie",
                "icone": "tint", "couleur": "green",
                "infos_sup": [("quartier", "📍 Quartier"), ("acces_pmr", "♿ PMR")]
            },
            "📊 Fréquentation Lignes (Stats uniquement)": {
                "api_id": "mkt-frequentation-niveau-freq-max-ligne",
                "col_titre": "ligne", 
                "col_adresse": "tranche_horaire",
                "icone": "bar-chart", "couleur": "gray",
                "infos_sup": [("frequentation", "👥 Charge"), ("jour_semaine", "📅 Jour")],
                "no_map": True
            }
        }
    }
}

COLONNES_CP_A_SCANNER = ["cp", "code_postal", "code_post", "zipcode", "commune", "location_address", "cp_arrondissement", "address_zipcode"]
URL_LOGO = "logo_pulse.png" 

# ==========================================
# 2. FONCTIONS UTILES (Parser d'heures)
# ==========================================

def parser_horaires_rennes(texte_horaire):
    """
    Transforme '06h00-07h00' ou '6:00-7:00' en chiffres (6, 7)
    pour que le graphique puisse tracer la durée.
    """
    try:
        # Nettoyage : on remplace 'h' par ':' et on coupe
        if not isinstance(texte_horaire, str): return 0, 0
        texte_clean = texte_horaire.lower().replace('h', ':').replace(' ', '')
        
        parts = texte_clean.split('-')
        if len(parts) == 2:
            debut_str = parts[0].split(':')[0] # On prend juste l'heure (ex: 16 de 16:30)
            fin_str = parts[1].split(':')[0]
            
            debut = int(debut_str)
            fin = int(fin_str)
            
            # Gestion de minuit (ex: 22h-01h -> 22 à 25)
            if fin < debut:
                fin += 24
                
            return debut, fin
    except:
        pass
    return 0, 0

def recuperer_coordonnees(site):
    """ Fonction 'Détective' qui cherche les coordonnées GPS partout """
    lat, lon = None, None
    geom = site.get("geometry")
    if geom and isinstance(geom, dict) and geom.get("type") == "Point":
        coords = geom.get("coordinates")
        if coords and len(coords) == 2: return coords[1], coords[0] 

    geo = site.get("geo_point_2d")
    if geo and isinstance(geo, dict): return geo.get("lat"), geo.get("lon")

    lat_lon = site.get("lat_lon")
    if lat_lon and isinstance(lat_lon, dict): return lat_lon.get("lat"), lat_lon.get("lon")

    geoloc = site.get("geolocalisation")
    if geoloc and isinstance(geoloc, dict): return geoloc.get("lat"), geoloc.get("lon")
    
    coords_rennes = site.get("coordonnees")
    if coords_rennes and isinstance(coords_rennes, dict): return coords_rennes.get("lat"), coords_rennes.get("lon")
        
    if "latitude" in site and "longitude" in site:
        try: return float(site["latitude"]), float(site["longitude"])
        except: pass
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
        time.sleep(2)
    except:
        pass

@st.cache_data 
def charger_donnees(base_url, api_id, cible=500):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'}
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

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@100;400;700&display=swap');
    h1 { color: #F63366; font-family: 'Roboto', sans-serif; font-weight: 700; text-transform: uppercase; letter-spacing: 2px; }
    h3, h4 { color: #262730; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    .streamlit-expanderHeader {font-weight: bold; color: #F63366;}
</style>
""", unsafe_allow_html=True)

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

# --- SIDEBAR ---
with st.sidebar:
    try: st.image(URL_LOGO, width=60)
    except: pass
        
    st.header("📍 Destination")
    ville_actuelle = st.selectbox("Choisir une ville :", list(CONFIG_VILLES.keys()))
    config_ville = CONFIG_VILLES[ville_actuelle]
    all_categories = config_ville["categories"]
    
    st.divider()
    st.header("⚙️ Paramètres")
    activer_voix = st.checkbox("Activer l'assistant vocal", value=True)
    
    st.divider()
    st.header("🔍 Données")
    
    cats_cartes = {k: v for k, v in all_categories.items() if not v.get("no_map")}
    cats_stats = {k: v for k, v in all_categories.items() if v.get("no_map")}
    
    type_visu = st.radio("Type de visualisation :", ["🗺️ Cartes Interactives", "📊 Statistiques & Analyses"])
    
    choix_utilisateur = None
    if type_visu == "🗺️ Cartes Interactives":
        choix_utilisateur = st.selectbox("Choisir une carte :", list(cats_cartes.keys()))
    else:
        if cats_stats:
            choix_utilisateur = st.selectbox("Choisir une analyse :", list(cats_stats.keys()))
        else:
            st.info("Aucune donnée purement statistique pour cette ville.")
            choix_utilisateur = list(cats_cartes.keys())[0]

    st.divider()
    mode_filtre = False
    filtre_texte = ""
    if type_visu == "🗺️ Cartes Interactives":
        st.header("🔎 Filtres")
        mode_filtre = st.toggle("Filtrer par zone", value=False)
        if mode_filtre:
            st.caption("Numéro d'arrondissement ou code postal.")
            filtre_texte = st.text_input("Recherche :")

# --- CHARGEMENT ---
cle_unique = f"{ville_actuelle}_{choix_utilisateur}"
if cle_unique != st.session_state.dernier_choix:
    if activer_voix:
        jouer_son_automatique(f"Chargement : {ville_actuelle}, {choix_utilisateur}")
    st.session_state.dernier_choix = cle_unique

config_data = all_categories[choix_utilisateur]

with st.spinner(f"Chargement des données de {ville_actuelle}..."):
    limit_req = 1000 if "frequentation" in config_data["api_id"] else 500
    raw_data = charger_donnees(config_ville["api_url"], config_data["api_id"], cible=limit_req)

tous_resultats = raw_data if isinstance(raw_data, list) else []

# --- FILTRAGE ---
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
        if type_visu == "🗺️ Cartes Interactives":
            st.success(f"🌍 {ville_actuelle} : {len(resultats_finaux)} lieux trouvés.")
else:
    st.info("Pas de données disponibles pour cette catégorie.")

# --- AFFICHAGE ---
if config_data.get("no_map"):
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
            st_folium(m, width=1000, height=600)
        else:
            st.warning("⚠️ Aucune coordonnée GPS trouvée pour ces données.")

with tab_stats:
    st.subheader(f"📊 Analyse : {ville_actuelle}")
    
    if len(resultats_finaux) > 0:
        if config_data["api_id"] == "mkt-frequentation-niveau-freq-max-ligne":
            df = pd.DataFrame(resultats_finaux)
            
            if "frequentation" in df.columns:
                df["frequentation"] = df["frequentation"].fillna("Inconnue")
                df["frequentation"] = df["frequentation"].apply(lambda x: str(x).strip()) # Nettoyage

            if "ligne" in df.columns and "frequentation" in df.columns and "tranche_horaire" in df.columns:
                
                # PREPARATION DONNEES TEMPORELLES
                # On applique la fonction qui transforme "06h-07h" en [6, 7]
                df[['heure_debut', 'heure_fin']] = df['tranche_horaire'].apply(lambda x: pd.Series(parser_horaires_rennes(x)))
                
                st.write("### 🟢 État de charge des lignes")
                # Graphique 1 : Barres empilées
                chart = alt.Chart(df).mark_bar().encode(
                    x=alt.X('ligne', sort='-y', title="Ligne"),
                    y=alt.Y('count()', title="Nb Relevés"),
                    # On laisse Altair gérer les couleurs automatiquement pour éviter les erreurs de mapping
                    color=alt.Color('frequentation', legend=alt.Legend(title="Niveau Charge")),
                    tooltip=['ligne', 'frequentation', 'count()']
                ).interactive()
                st.altair_chart(chart, use_container_width=True)
                
                st.write("### 📅 Disponibilité & Charge Horaire")
                st.caption("La barre s'étend sur toute la durée de la tranche horaire.")
                
                # Graphique 2 : Heatmap étendue (Gantt style)
                heatmap = alt.Chart(df).mark_bar().encode(
                    x=alt.X('heure_debut', title="Heure (Début)", scale=alt.Scale(domain=[0, 24])),
                    x2='heure_fin', # C'est ça qui fait la barre longue !
                    y=alt.Y('ligne', title="Ligne"),
                    color=alt.Color('frequentation', title="Charge"),
                    tooltip=['ligne', 'tranche_horaire', 'frequentation']
                ).interactive()
                st.altair_chart(heatmap, use_container_width=True)
                    
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
