import streamlit as st
import pandas as pd
import seaborn as sns
import operator
import requests
from unidecode import unidecode
from streamlit_extras.switch_page_button import switch_page
import time
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import MinMaxScaler

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

# Configuration de la page
st.set_page_config(page_title="Fiche Film 🎬", page_icon="🎥", layout="wide")

# Hide sidebar completely
st.markdown("""
    <style>
        [data-testid="collapsedControl"] {display: none;}
        section[data-testid='stSidebar'] {display: none;}
    </style>
""", unsafe_allow_html=True)

# Initialisation de la session state
if 'tconst' not in st.session_state:
    st.session_state.tconst = 'tt0111161'  # Film par défaut

try:
    # Requête initiale pour obtenir l'ID TMDB
    apii = requests.get(f'https://api.themoviedb.org/3/find/{st.session_state.tconst}?external_source=imdb_id&language=fr', headers=headers).json()['movie_results'][0]
    tmdbid = apii['id']
    
    # Requête pour les détails du film
    tmdbapi = requests.get(f'https://api.themoviedb.org/3/movie/{str(tmdbid)}?language=fr-FR', headers=headers).json()
    
    # Requête pour les crédits
    credits = requests.get(f'https://api.themoviedb.org/3/movie/{str(tmdbid)}/credits?language=fr-FR', headers=headers).json()
    
    # bouton de retour
    if st.button('← Retour à la recherche film'):
        switch_page("Recherche Film")
    
    # Affichage du titre
    st.title(f"🎬 {apii['title']} ({tmdbapi['release_date'][:4]})")
    st.caption(f"TMDB ID: {tmdbid} | IMDB ID: {st.session_state.tconst}")
    
    # Layout en colonnes
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Genres
        genres = ", ".join([genre['name'] for genre in tmdbapi['genres']])
        st.write(f"🎭 **Genres:** {genres}")
        
        # Réalisateur
        director = next((crew for crew in credits['crew'] if crew['job'] == 'Director'), {'name': 'Non disponible', 'id': None})
        st.write(f"🎥 **Réalisateur:** {director['name']}")
        
        # Synopsis
        st.write("📝 **Synopsis:**")
        st.write(f"{apii['overview']}")
        
        # Acteurs principaux (6 premiers) avec boutons en 3 colonnes
        st.write("👥 **Acteurs principaux:**")
        actor_cols = st.columns(3)
        for idx, cast in enumerate(credits['cast'][:6]):
            with actor_cols[idx % 3]:
                actor_details = requests.get(f'https://api.themoviedb.org/3/person/{cast["id"]}/external_ids', headers=headers).json()
                if 'imdb_id' in actor_details:
                    imdb_id = actor_details['imdb_id']
                    if st.button(f"{cast['name']}", key=f"actor_{cast['id']}", use_container_width=True):
                        st.session_state['nconst'] = imdb_id
                        time.sleep(1.5)
                        switch_page('Fiche Personnalité')
        
        # Informations supplémentaires intégrées dans la même colonne
        st.write(f"⭐ **Note moyenne:** {tmdbapi['vote_average']}/10 ({tmdbapi['vote_count']} votes)")
        st.write(f"💰 **Budget:** {tmdbapi['budget']:,} $")
        st.write(f"💸 **Recettes:** {tmdbapi['revenue']:,} $")
        st.write(f"⏱️ **Durée:** {tmdbapi['runtime']} minutes")

    with col2:
        st.image(f"https://image.tmdb.org/t/p/w500{apii['poster_path']}", width=500)
    st.divider()
    st.header("🎯 Voici notre recommandation personnalisée pour vous...")

except Exception as e:
    st.error(f"Une erreur s'est produite. Veuillez vérifier l'ID du film. ❌ Details: {str(e)}")

dfml = dft.drop(columns=['title','actor','actress','director','writer','id','production_countries','revenue','spoken_languages','vote','rank'])
dfml['genres'] = dfml['genres'].apply(lambda x: x.replace("'","").replace("[","").replace("]","").split(",")).apply(lambda x: list(filter(None, [ele.strip() for ele in x])))
dfml=pd.merge(left=dfml, right=dfml['genres'].explode().str.get_dummies().reset_index().groupby(by=['index']).sum().reset_index().drop(columns=['index']), how='left', left_index=True, right_index=True)
dfml.drop(columns=['tconst','genres'], inplace=True)
dfml['original_language']=dfml['original_language'].apply(lambda x: 1 if x=='fr' else 0)
dfml.rename(columns={"original_language": "fr"}, inplace=True)

# Normalisation des features numériques
scaler = MinMaxScaler()
dftsca = scaler.fit_transform(dfml)

# Modèle KNN
model = NearestNeighbors(n_neighbors=4, metric='euclidean')
model.fit(dftsca)
distances, indices = model.kneighbors([dftsca[dft.loc[dft['tconst']==st.session_state.tconst].index[0]]])

cols = st.columns(3, gap="large")
for ncols in range(3):
    with cols[ncols]:
        movie_title = dft.iloc[indices[0][ncols+1]]['title']
        
        # Récupération des informations du film recommandé
        rec_movie_id = dft.iloc[indices[0][ncols+1]]['tconst']
        try:
            rec_movie_api = requests.get(f'https://api.themoviedb.org/3/find/{rec_movie_id}?external_source=imdb_id&language=fr', headers=headers).json()['movie_results'][0]
            rec_tmdbid = rec_movie_api['id']
            
            # Récupération des détails du film
            rec_details = requests.get(f'https://api.themoviedb.org/3/movie/{str(rec_tmdbid)}?language=fr-FR', headers=headers).json()
            rec_credits = requests.get(f'https://api.themoviedb.org/3/movie/{str(rec_tmdbid)}/credits?language=fr-FR', headers=headers).json()
            release_year = rec_details['release_date'][:4]
            
            # Affichage du titre avec l'année
            if st.button(f"**{movie_title}** ({release_year})"):
                st.session_state['tconst'] = dft.iloc[indices[0][ncols+1]]['tconst']
                time.sleep(1.5)
                switch_page('Fiche Film')
            
            # Affichage de l'image
            st.image(f"https://image.tmdb.org/t/p/w500{rec_movie_api['poster_path']}", width=300)
            
            # Affichage des genres
            genres = ", ".join([genre['name'] for genre in rec_details['genres']])
            st.write(f"🎭 **Genres:** {genres}")
            
            # Affichage du réalisateur
            director = next((crew for crew in rec_credits['crew'] if crew['job'] == 'Director'), {'name': 'Non disponible'})
            st.write(f"🎥 **Réalisateur:** {director['name']}")
            
            # Affichage de la note et nombre de votes
            st.write(f"⭐ **Note:** {rec_details['vote_average']}/10 ({rec_details['vote_count']} votes)")
            
            # Affichage de la durée
            st.write(f"⏱️ **Durée:** {rec_details['runtime']} minutes")
            
        except Exception as e:
            st.error(f"Erreur lors de la récupération des détails du film: {str(e)}")
        
        st.markdown(
        """
        <style>
        button {
            background: none!important;
            border: none;
            padding: 0!important;
            color: black !important;
            text-decoration: none;
            cursor: pointer;
            border: none !important;
        }
        button:hover {
            text-decoration: none;
            color: black !important;
        }
        button:focus {
            outline: none !important;
            box-shadow: none !important;
            color: black !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
        )