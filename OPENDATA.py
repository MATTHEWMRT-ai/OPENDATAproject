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
# 1. CONFIGURATION MULTI-VILLES & MOTS-CLÉS
# ==========================================

CONFIG_VILLES = {
    "Paris 🗼": {
        "coords_center": [48.8566, 2.3522],
        "zoom_start": 12,
        "api_url": "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets",
        "cp_prefix": "75",
        "alias": ["paris", "paname", "75"],  # Mots-clés pour trouver la ville
        "categories": {
            "📅 Sorties & Événements": {
                "api_id": "que-faire-a-paris-",
                "col_titre": "title", "col_adresse": "address_name",
                "icone": "calendar", "couleur": "orange",
                "infos_sup": [("date_start", "📅 Date"), ("price_type", "💶 Prix"), ("lead_text", "ℹ️ Info")],
                "image_col": "cover_url",
                "mots_cles": ["sorties", "evenements", "concert", "expo", "agenda", "culture"]
            },
            "Bornes Wi-Fi": {
                "api_id": "sites-disposant-du-service-paris-wi-fi",
                "col_titre": "nom_site", "col_adresse": "arc_adresse",
                "icone": "wifi", "couleur": "purple", 
                "infos_sup": [("etat2", "✅ État"), ("cp", "📮 CP")],
                "mots_cles": ["wifi", "internet", "web", "connection"]
            },
            "Sanisettes (Toilettes)": {
                "api_id": "sanisettesparis",
                "col_titre": "libelle", "col_adresse": "adresse",
                "icone": "tint", "couleur": "blue", 
                "infos_sup": [("horaire", "🕒 Horaires"), ("acces_pmr", "♿ PMR")],
                "mots_cles": ["toilettes", "wc", "sanisettes", "pipi"]
            },
            "Fontaines à boire": {
                "api_id": "fontaines-a-boire",
                "col_titre": "voie", "col_adresse": "commune",
                "icone": "glass", "couleur": "cadetblue", 
                "infos_sup": [("dispo", "💧 Dispo"), ("type_objet", "⚙️ Type")],
                "mots_cles": ["eau", "boire", "fontaine", "soif"]
            },
            "Chantiers Perturbants": {
                "api_id": "chantiers-perturbants",
                "col_titre": "objet", "col_adresse": "voie",
                "icone": "exclamation-triangle", "couleur": "red", 
                "infos_sup": [("date_fin", "📅 Fin"), ("impact_circulation", "🚗 Impact")],
                "mots_cles": ["travaux", "chantier", "route", "circulation"]
            },
            "Laboratoires d'Analyses": {
                "api_id": "laboratoires-danalyses-medicales",
                "col_titre": "laboratoire", "col_adresse": "adresse",
                "icone": "flask", "couleur": "green", 
                "infos_sup": [("telephone", "📞 Tél"), ("horaires", "🕒 Horaires")],
                "mots_cles": ["sante", "medecin", "laboratoire", "analyse", "sang"]
            },
            "Défibrillateurs": {
                "api_id": "defibrillateurs",
                "col_titre": "nom_etabl", "col_adresse": "adr_post",
                "icone": "heartbeat", "couleur": "darkred", 
                "infos_sup": [("acces_daw", "🚪 Accès")],
                "mots_cles": ["coeur", "defibrillateur", "urgence", "secours"]
            },
            "Collèges": {
                "api_id": "etablissements-scolaires-colleges",
                "col_titre": "libelle", "col_adresse": "adresse",
                "icone": "graduation-cap", "couleur": "darkblue", 
                "infos_sup": [("public_prive", "🏫 Secteur")],
                "mots_cles": ["ecole", "college", "education", "scolaire"]
            },
            "Écoles Maternelles": {
                "api_id": "etablissements-scolaires-maternelles",
                "col_titre": "libelle", "col_adresse": "adresse",
                "icone": "child", "couleur": "pink", 
                "infos_sup": [("public_prive", "🏫 Secteur")],
                "mots_cles": ["ecole", "maternelle", "enfant", "bebe"]
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
                "mots_cles": ["parking", "garer", "voiture", "stationnement", "auto"]
            },
            "🚲 Stations Vélo Star (Temps réel)": {
                "api_id": "etat-des-stations-le-velo-star-en-temps-reel",
                "col_titre": "nom", 
                "col_adresse": "nom", 
                "icone": "bicycle", "couleur": "red",
                "infos_sup": [("nombrevelosdisponibles", "🚲 Vélos dispo"), ("nombreemplacementsdisponibles", "🅿️ Places dispo")],
                "mots_cles": ["velo", "bicyclette", "cyclisme", "star"]
            },
             "🚌 Bus en Circulation (Temps réel)": {
                "api_id": "position-des-bus-en-circulation-sur-le-reseau-star-en-temps-reel",
                "col_titre": "nomcourtligne", 
                "col_adresse": "destination",
                "icone": "bus", "couleur": "cadetblue",
                "infos_sup": [("destination", "🏁 Vers"), ("ecartsecondes", "⏱️ Écart (sec)")],
                "mots_cles": ["bus", "transport", "commun", "star"]
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
                "col_titre": "nom_court_ligne",
                "col_adresse": "tranche_horaire_libelle", 
                "icone": "bar-chart", "couleur": "gray",
                "infos_sup": [("niveau_frequentation_libelle", "👥 Charge"), ("tranche_horaire_libelle", "🕒 Heure")],
                "no_map": True,
                "mots_cles": ["stats", "frequentation", "monde", "charge"]
            }
        }
    }
}

COLONNES_CP_A_SCANNER = ["cp", "code_postal", "code_post", "zipcode", "commune", "location_address", "cp_arrondissement", "address_zipcode"]
URL_LOGO = "logo_pulse.png" 

# ==========================================
# 2. FONCTIONS UTILES & RECHERCHE
# ==========================================

def moteur_recherche(requete, config):
    """
    Cherche une ville et une catégorie basées sur les mots-clés.
    Retourne (ville_trouvee, categorie_trouvee) ou (None, None).
    """
    requete = requete.lower().strip()
    ville_trouvee = None
    cat_trouvee = None

    # 1. Identifier la ville
    for ville_nom, ville_data in config.items():
        mots_ville = [ville_nom.lower().split()[0]] + ville_data.get("alias", [])
        if any(mot in requete for mot in mots_ville):
            ville_trouvee = ville_nom
            break
    
    # Si pas de ville trouvée, on ne peut pas deviner la catégorie (car elles dépendent de la ville)
    # On pourrait améliorer ça en cherchant dans toutes les villes, mais restons simple pour l'instant.
    if not ville_trouvee:
        # Essai de trouver juste la catégorie dans la ville actuelle (si gérée hors de cette fonction)
        # Ici on retourne None pour forcer une recherche précise "Ville + Mot clé" ou juste "Ville"
        pass

    # 2. Identifier la catégorie DANS la ville trouvée (ou chercher globalement si on voulait)
    if ville_trouvee:
        categories = config[ville_trouvee]["categories"]
        for cat_nom, cat_data in categories.items():
            mots_cat = [cat_nom.lower()] + cat_data.get("mots_cles", [])
            # Nettoyage simple
            if any(k in requete for k in mots_cat):
                cat_trouvee = cat_nom
                break
            
    return ville_trouvee, cat_trouvee

def parser_horaires_robust(texte_horaire):
    try:
        if not isinstance(texte_horaire, str): return 0, 0, 0
        nums = [int(s) for s in re.findall(r'\d+', texte_horaire)]
        debut, fin = 0, 0
        if len(nums) == 2:
            debut, fin = nums[0], nums[1]
        elif len(nums) == 4:
            debut, fin = nums[0], nums[2]
        elif len(nums) >= 6:
            debut, fin = nums[0], nums[3]
        duree = fin - debut
        if fin < debut: 
            fin += 24
            duree = fin - debut
        return debut, fin, duree
    except:
        pass
    return 0, 0, 0

def recuperer_coordonnees(site):
    """ Gestion complète des formats de coordonnées (Paris/Rennes/GeoJSON) """
    
    # 1. Paris Sorties : "lat_lon": {"lat": ..., "lon": ...}
    if "lat_lon" in site:
        ll = site["lat_lon"]
        if isinstance(ll, dict): return ll.get("lat"), ll.get("lon")
    
    # 2. Rennes Parking : "geo": {"lat": ..., "lon": ...}
    if "geo" in site:
        g = site["geo"]
        if isinstance(g, dict): return g.get("lat"), g.get("lon")
        if isinstance(g, list) and len(g) == 2: return g[0], g[1]

    # 3. Rennes Bus/Velo : "coordonnees"
    if "coordonnees" in site:
        c = site["coordonnees"]
        if isinstance(c, dict): return c.get("lat"), c.get("lon")
        if isinstance(c, list) and len(c) == 2: return c[0], c[1]

    # 4. GeoJSON standard : "geometry": {"coordinates": [lon, lat]}
    geom = site.get("geometry")
    if geom and isinstance(geom, dict) and geom.get("type") == "Point":
        coords = geom.get("coordinates")
        if coords and len(coords) == 2: return coords[1], coords[0] 

    # 5. Fallbacks
    if "geo_point_2d" in site:
        geo = site["geo_point_2d"]
        if isinstance(geo, dict): return geo.get("lat"), geo.get("lon")
        if isinstance(geo, list) and len(geo) == 2: return geo[0], geo[1]

    geoloc = site.get("geolocalisation")
    if geoloc:
        if isinstance(geoloc, dict): return geoloc.get("lat"), geoloc.get("lon")
        if isinstance(geoloc, list) and len(geoloc) == 2: return geoloc[0], geoloc[1]
        
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

# ==========================================
# 3. INITIALISATION & SIDEBAR
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
</style>
""", unsafe_allow_html=True)

# --- INIT SESSION STATE ---
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

# --- SIDEBAR & RECHERCHE ---
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
    
    # 1. Select Ville (Lié au State)
    ville_actuelle = st.selectbox(
        "Choisir une ville :", 
        options=list(CONFIG_VILLES.keys()),
        key="ville_selectionnee"
    )
    
    config_ville = CONFIG_VILLES[ville_actuelle]
    all_categories = config_ville["categories"]
    
    st.divider()
    
    # 2. Select Catégorie (Logique dynamique)
    if st.session_state.cat_selectionnee not in all_categories:
        st.session_state.cat_selectionnee = list(all_categories.keys())[0]

    liste_cats = list(all_categories.keys())
    try:
        index_cat = liste_cats.index(st.session_state.cat_selectionnee)
    except ValueError:
        index_cat = 0
        
    choix_utilisateur_brut = st.selectbox(
        "Choisir une donnée :", 
        options=liste_cats,
        index=index_cat
    )
    # Update manuel du state
    st.session_state.cat_selectionnee = choix_utilisateur_brut
    
    st.divider()
    st.header("⚙️ Paramètres")
    activer_voix = st.checkbox("Activer l'assistant vocal", value=True)
    
    # Définition du type de vue
    config_data = all_categories[choix_utilisateur_brut]
    if config_data.get("no_map"):
        type_visu = "STATS"
    else:
        type_visu = "CARTE"

    # Filtres
    mode_filtre = False
    filtre_texte = ""
    if type_visu == "CARTE":
        st.header("🔎 Filtres")
        mode_filtre = st.toggle("Filtrer par zone", value=False)
        if mode_filtre:
            filtre_texte = st.text_input("Recherche zone :")

# --- CHARGEMENT ---
choix_utilisateur = choix_utilisateur_brut
cle_unique = f"{ville_actuelle}_{choix_utilisateur}"

if cle_unique != st.session_state.dernier_choix:
    if activer_voix:
        jouer_son_automatique(f"Chargement : {ville_actuelle}, {choix_utilisateur}")
    st.session_state.dernier_choix = cle_unique

with st.spinner(f"Chargement des données de {ville_actuelle}..."):
    limit_req = 1500 if "frequentation" in config_data["api_id"] else 500
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
            # --- CORRECTION DU RAFRAICHISSEMENT ---
            st_folium(m, width=1000, height=600, returned_objects=[])
        else:
            st.warning("⚠️ Aucune coordonnée GPS trouvée (Vérifiez les données brutes).")

with tab_stats:
    st.subheader(f"📊 Analyse : {ville_actuelle}")
    
    if len(resultats_finaux) > 0:
        if config_data["api_id"] == "mkt-frequentation-niveau-freq-max-ligne":
            df = pd.DataFrame(resultats_finaux)
            
            map_cols = {
                'nom_court_ligne': 'ligne',
                'niveau_frequentation_libelle': 'frequentation',
                'tranche_horaire_libelle': 'tranche_horaire',
                'jours_application_libelle': 'jour',
                'jour_semaine': 'jour' 
            }
            df = df.rename(columns=map_cols)

            if 'jour' not in df.columns:
                cols_jour = [c for c in df.columns if "jour" in c.lower()]
                if cols_jour: df['jour'] = df[cols_jour[0]]

            if 'jour' in df.columns:
                périodes_dispo = df['jour'].unique().tolist()
                choix_jour = st.selectbox("📅 Choisir la période à analyser :", périodes_dispo)
                df = df[df['jour'] == choix_jour]
                st.success(f"Analyse filtrée pour : {choix_jour} ({len(df)} relevés)")
            
            if "frequentation" in df.columns:
                df["frequentation"] = df["frequentation"].fillna("Non ouverte").replace("", "Non ouverte")

            if "ligne" in df.columns and "frequentation" in df.columns and "tranche_horaire" in df.columns:
                parsed_data = df['tranche_horaire'].apply(lambda x: pd.Series(parser_horaires_robust(x)))
                parsed_data.columns = ['heure_debut', 'heure_fin', 'duree_heures']
                df = pd.concat([df, parsed_data], axis=1)
                
                df_clean = df[df['duree_heures'] > 0]
                
                if not df_clean.empty:
                    st.write("### 🟢 Répartition de la charge (%)")
                    chart = alt.Chart(df_clean).mark_bar().encode(
                        y=alt.Y('ligne', sort='descending', title="Ligne"),
                        x=alt.X('sum(duree_heures)', stack='normalize', axis=alt.Axis(format='%'), title="Répartition du temps"),
                        color=alt.Color('frequentation:N', 
                                        scale=alt.Scale(domain=['Faible', 'Moyenne', 'Forte', 'Non ouverte'],
                                                        range=['#2ecc71', '#f1c40f', '#e74c3c', '#95a5a6']),
                                        legend=alt.Legend(title="Charge")),
                        tooltip=['ligne', 'frequentation', 'sum(duree_heures)']
                    ).interactive()
                    st.altair_chart(chart, use_container_width=True)
                else:
                    st.warning("Aucune donnée horaire valide.")
        else:
            # Stats génériques (Bar Chart par CP)
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
