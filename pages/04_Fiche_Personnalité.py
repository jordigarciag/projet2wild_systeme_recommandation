# Import des bibliothèques nécessaires
import streamlit as st
import pandas as pd
import seaborn as sns
import operator
import requests
from unidecode import unidecode
from streamlit_extras.switch_page_button import switch_page
import time

# Configuration des headers pour l'API TMDB
headers = {
    "accept": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI4YTM0OGExMDhjMDVlMzI4ZmNkOWY4OWJiMDRmYWU2OSIsIm5iZiI6MTczMzg0NTA4MS40MzIsInN1YiI6IjY3NTg2MDU5OTkzNTliMDQ2OGE0Njc3ZSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.iybQH84AcS6kz6Ryzl83Y9Lg1VLbxGJmUaUc1e0AR-Y"
}

# Chargement des données
urln = "https://raw.githubusercontent.com/florianhoarau/streamlit_imdb/main/nconst.tsv.gz"
urlt = "https://raw.githubusercontent.com/florianhoarau/streamlit_imdb/main/tconst.tsv.gz"
dfn = pd.read_csv(urln, sep='\t')
dft = pd.read_csv(urlt, sep='\t')

# Fonction pour masquer la barre latérale
def hide_sidebar():
    st.markdown(
        """
        <style>
        div[data-testid="stSidebarNav"] {
            display: none !important;
        }
        section[data-testid="stSidebar"] {
            display: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
# Configuration de la page
st.set_page_config(page_title="Fiche Personnalité", page_icon="👤",
                   layout="wide"  # Cette ligne ajoute la vue élargie
                   )
st.sidebar.header("Fiche Personnalité")

# Masquer la barre latérale
hide_sidebar()


st.sidebar.header("Fiche Personnalité")


# Initialize session state for nconst if not exists
if 'nconst' not in st.session_state:
    st.session_state.nconst = 'nm0000093'  # Default person ID (Brad Pitt)

try:
    # Requête pour obtenir les détails de la personne
    apii = requests.get(f'https://api.themoviedb.org/3/find/{st.session_state.nconst}?external_source=imdb_id&language=fr', headers=headers).json()['person_results'][0]
    tmdbid = apii['id']
    tmdbapi = requests.get(f'https://api.themoviedb.org/3/person/{str(tmdbid)}?language=fr-FR', headers=headers).json()
    
    # Requête pour obtenir les films
    movies = requests.get(f'https://api.themoviedb.org/3/person/{str(tmdbid)}/movie_credits?language=fr-FR', headers=headers).json()

    # bouton de retour
    if st.button('← Retour à la recherche film'):
        switch_page("Recherche Film")

    # Titre en grand
    st.title(f"👤 {tmdbapi['name']}")
    
    # Affichage de l'ID
    st.caption(f"ID: {st.session_state.nconst}")

    # Création du layout avec colonnes
    col1, col2 = st.columns([2, 1])
    
    # Menu latéral dans la première colonne
    with col1:
        st.write(f"🎂 **Date de naissance:** {tmdbapi.get('birthday', 'Non disponible')}")
        if tmdbapi.get('deathday'):
            st.write(f"✝️ **Date de décès:** {tmdbapi['deathday']}")
        st.write(f"🌍 **Lieu de naissance:** {tmdbapi.get('place_of_birth', 'Non disponible')}")
        
        with st.container(height=300):
            st.write("📝 **Biographie:**")
            st.write(f"{tmdbapi.get('biography', 'Biographie non disponible')}")

    # Contenu principal dans la deuxième colonne
    with col2:
        if tmdbapi.get('profile_path'):
            st.image(f"https://image.tmdb.org/t/p/w500{tmdbapi['profile_path']}", width=500)
        else:
            st.write("Pas d'image disponible")

    # Films remarquables
    st.subheader("🎬 Films remarquables")
    if movies.get('cast'):
        notable_movies = sorted(movies['cast'], key=lambda x: x.get('popularity', 0), reverse=True)[:3]
        movie_cols = st.columns([1,1,1])
        for idx, movie in enumerate(notable_movies):
            with movie_cols[idx]:
                movie_details = requests.get(f'https://api.themoviedb.org/3/movie/{movie["id"]}/external_ids', headers=headers).json()
                if 'imdb_id' in movie_details:
                    imdb_id = movie_details['imdb_id']
                    if st.button(f"{movie['title']} ({movie['release_date'][:4]})", key=f"movie_{movie['id']}", use_container_width=True):
                        st.session_state['tconst'] = imdb_id
                        time.sleep(1.5)
                        switch_page('Fiche Film')

    st.markdown("""
    <div style='padding: 1rem; 
                text-align: center;
                background-color: #fef9c3; 
                border-radius: 0.5rem;
                font-size: 1rem;'>
    🎞️ Sélectionnez un film pour obtenir des recommandations personnalisées   </div>
    """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"Une erreur s'est produite : {str(e)}")
    st.error(f"Type d'erreur : {type(e).__name__}")