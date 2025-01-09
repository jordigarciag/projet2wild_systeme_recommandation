
import streamlit as st
import pandas as pd
import seaborn as sns
import operator
import requests
from unidecode import unidecode
from streamlit_extras.switch_page_button import switch_page
import time

headers = {
    "accept": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI4YTM0OGExMDhjMDVlMzI4ZmNkOWY4OWJiMDRmYWU2OSIsIm5iZiI6MTczMzg0NTA4MS40MzIsInN1YiI6IjY3NTg2MDU5OTkzNTliMDQ2OGE0Njc3ZSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.iybQH84AcS6kz6Ryzl83Y9Lg1VLbxGJmUaUc1e0AR-Y"
}

urln = "https://raw.githubusercontent.com/florianhoarau/streamlit_imdb/main/nconst.tsv.gz"
urlt = "https://raw.githubusercontent.com/florianhoarau/streamlit_imdb/main/tconst.tsv.gz"

dfn = pd.read_csv(urln, sep='\t')
dft = pd.read_csv(urlt, sep='\t')

st.set_page_config(
    page_title="Recherche Film",
    page_icon="",
    layout="wide"  # Cette ligne ajoute la vue élargie
)

st.sidebar.header("Recherche Film")

# Fonction pour masquer la barre latérale
def hide_sidebar():
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"][aria-expanded="true"] {
            display: none;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

# Masquer la barre latérale
hide_sidebar()

# bouton de retour
if st.button('← Retour au choix du système'):
    switch_page("dashboard systeme recommandation")

st.title("🎞️ Recommandation par film préféré")

# Création d'un conteneur pour centrer le contenu
container = st.container()
with container:
    movie_search = st.text_input("Veuillez saisir le titre d'un film et appuyez sur la touche Entrée pour afficher les résultats.", value="")
    
    col1, col2 = st.columns(2)
    with col1:
        case = st.checkbox("Ignorer majuscules", value=True, label_visibility="visible")
        accents = st.checkbox("Ignorer accents", value=True, label_visibility="visible")
    with col2:
        nb_cards = st.number_input("Nombre de résultats", min_value=3, max_value=45, value=12, step=3, label_visibility="visible")

if case & accents:
    df_movie_search = dft.loc[dft["title"].apply(lambda x: unidecode(x)).str.lower().str.contains(unidecode(movie_search.lower()))].sort_values('rank', ascending=False).head(nb_cards)
elif case:
    df_movie_search = dft.loc[dft["title"].str.lower().str.contains(movie_search.lower())].sort_values('rank', ascending=False).head(nb_cards)
elif accents:
    df_movie_search = dft.loc[dft["title"].apply(lambda x: unidecode(x)).str.contains(unidecode(movie_search))].sort_values('rank', ascending=False).head(nb_cards)    
else:
    df_movie_search = dft.loc[dft["title"].str.contains(movie_search)].sort_values('rank', ascending=False).head(nb_cards)

N_cards_per_row = 4  # Augmentation du nombre de cartes par ligne

if movie_search:
    for n_row, row in df_movie_search.reset_index().iterrows():
        i = n_row%N_cards_per_row
        if i==0:
            st.write("---")
            cols = st.columns(N_cards_per_row, gap="medium")
        # draw the card
        with cols[n_row%N_cards_per_row]:
            if st.button(f"**{row['title']}**"):
                st.session_state['tconst'] = row['tconst']
                time.sleep(1.5)
                switch_page('Fiche Film')
            
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
                
            st.markdown(f"**{row['rate']}**/10 _({int(row['vote'])})_")
            try:
                path=requests.get('https://api.themoviedb.org/3/find/'+row['tconst']+'?external_source=imdb_id&language=fr', headers=headers).json()['movie_results'][0]['poster_path']
                st.image(f"https://image.tmdb.org/t/p/w500{path}", width=300)  # Réduction de la taille des images
            except:
                st.image(f"blank_mov.png", width=300)

st.write("")
st.divider()
st.write("")

st.markdown("""
<style>
.big-button {
    background-color: #4CAF50;
    border: none;
    color: white;
    padding: 15px 32px;
    text-align: center;
    text-decoration: none;
    display: inline-block;
    font-size: 20px;
    margin: 4px 2px;
    cursor: pointer;
    border-radius: 8px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    width: 80%;
    transition: all 0.3s ease;
}
.big-button:hover {
    background-color: #45a049;
    box-shadow: 0 6px 12px rgba(0,0,0,0.2);
}
</style>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1,2,1])
with col2:
    if st.button('Cliquez ici pour obtenir une recommandation selon votre personnalité préférée', 
                 key='actor_button',
                 use_container_width=True):
        switch_page("recherche personnalité")
