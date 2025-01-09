import streamlit as st
import pandas as pd
import numpy as np
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime
from streamlit_extras.switch_page_button import switch_page

# Configuration de la page
st.set_page_config(
    page_title="Assistant cinématographique - by Los Sanchos",
    page_icon="🍿",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# Ajoutez cette fonction au début du code
def hide_sidebar_completely():
    st.markdown("""
        <style>
            section[data-testid="stSidebar"] {
                display: none !important;
            }
            button[kind="header"] {
                display: none !important;
            }
            .st-emotion-cache-1544g2n {
                padding-left: 1rem !important;
            }
        </style>
    """, unsafe_allow_html=True)

# Appelez cette fonction au début de chaque page
hide_sidebar_completely()


# Fonction pour charger les données
def load_data():
    url = "https://raw.githubusercontent.com/florianhoarau/streamlit_imdb/main/tconst.tsv.gz"
    return pd.read_csv(url, sep='\t')

# Fonction pour préparer les données
def prepare_data(df_movies):
    df_movies['genres'] = df_movies['genres'].fillna('Sans catégorie')
    df_movies['genres'] = df_movies['genres'].apply(lambda x: x.replace("'","").replace("[","").replace("]","").split(","))
    df_movies['genres'] = df_movies['genres'].apply(lambda x: [genre.strip() for genre in x if genre.strip()])
    df_movies['budget'] = df_movies['budget'].fillna(df_movies['budget'].mean())
    df_movies['castage'].fillna(50, inplace=True)
    df_movies['castage']=df_movies['castage'].apply(lambda x: 50 if x<1 else x)
    all_genres = df_movies['genres'].explode().value_counts().nlargest(23).index.tolist()
    
    for genre in all_genres:
        df_movies[f'genre_{genre}'] = df_movies['genres'].apply(lambda x: 1 if genre in x else 0)
    
    return df_movies, all_genres

# Page d'accueil
def home():    
    st.title('👋 Bienvenue sur votre Assistant cinématographique !')
    st.write('Vous ne savez pas quel film regarder ? Pas de panique, Los Sanchos sont là pour vous aider !')
    st.write('Pour commencer, choisissez l\'une de nos deux méthodes de recommandation :')
    st.write('- 🎯 Recommandations par paramètres : Définissez vos critères (genre, durée, année...) et laissez-nous vous suggérer des films')
    st.write('- 🎬 Recommandations par films préférés : Dites-nous quels films vous aimez et nous trouverons des suggestions similaires basées sur vos préférences')
    st.write('')
    st.subheader('Veuillez choisir une option :')
    col1, col2 = st.columns(2)
    with col1:
        if st.button('🎯 Recommandations par paramètres', use_container_width=True, key='params'):
            st.session_state.page = 'params'
            st.rerun()
    with col2:
        if st.button('🎬 Recommandations par films préférés', use_container_width=True, key='prefs'):
            switch_page("recherche film")

# Système de recommandation par paramètres
def params_recommendations():    
    st.title('🎥 Assistant cinématographique')
    
    # Bouton retour
    if st.button('← Retour au choix du système'):
        st.session_state.page = 'home'
        st.rerun()

    # Créer deux colonnes
    col_params, col_results = st.columns(2)
    
    # Colonne des paramètres
    with col_params:
        st.header('🎮 Paramètres')
        
        age = st.number_input('Quel est votre âge ?', min_value=0, max_value=120, value=18)
        if age < 5:
            st.error('👶 Tu es bien trop jeune pour trouver ton bonheur ici')
            st.stop()
        elif age <= 12:
            st.info('🎈 Seuls les films d\'animation seront proposés')
        elif age <= 17:
            st.info('🎈 Seuls les films d\'aventure et comédies de moins de 100 minutes seront proposés')

        note_optionnelle = st.checkbox("Je souhaite définir une note")
        selected_rate = 0.0
        if note_optionnelle:
            selected_rate = st.slider('⭐ Autour de quelle note souhaitez-vous chercher ?', 
                                    min_value=0.0, max_value=10.0, value=7.0, step=0.1)

        duration_ranges = {
            'Toutes les durées': None,
            'Court (< 90 min)': (60, 90),
            'Moyen (90-120 min)': (90, 120),
            'Long (120-150 min)': (120, 150),
            'Très long (> 150 min)': (150, 240)
        }
        selected_duration = st.radio('⏱️ Durée', list(duration_ranges.keys()))
        selected_runtime_range = duration_ranges[selected_duration]

    # Colonne des résultats
    with col_results:
        st.header('🎬 Résultats')
        
        try:
            df_movies = load_data()
            df_movies, unique_genres = prepare_data(df_movies)
            
            feature_columns = ['castage', 'rate', 'year', 'runtimeMinutes', 'budget'] + [f'genre_{genre}' for genre in unique_genres]
            X = df_movies[feature_columns].copy()
            X = X.fillna(0)
            scaler = MinMaxScaler()
            X[['castage', 'rate', 'year', 'runtimeMinutes', 'budget']] = scaler.fit_transform(X[['castage', 'rate', 'year', 'runtimeMinutes', 'budget']])
            model = NearestNeighbors(n_neighbors=20, metric='euclidean')
            model.fit(X)
            
            # Continuer avec les paramètres dans la colonne de gauche
            with col_params:
                year_selection_type = st.radio("📅 Sélection de l'année",
                                         ['Par décennie', 'Par année'])
                
                min_year = int(df_movies['year'].min())
                max_year = int(df_movies['year'].max())
                
                if year_selection_type == 'Par décennie':
                    decades = ['Toutes les décennies'] + [f"{decade}s" for decade in range(min_year - (min_year % 10), max_year + 10, 10)[:-1]]
                    selected_decade = st.radio('📆 Décennie', decades)
                    
                    if selected_decade == 'Toutes les décennies':
                        selected_year = min_year
                        all_decades = True
                    else:
                        selected_year = int(selected_decade[:-1])
                        all_decades = False
                else:
                    selected_year = st.slider('📅 Année',
                                            min_value=min_year,
                                            max_value=max_year,
                                            value=2000)
                    all_decades = False

                if 6 <= age <= 12:
                    available_genres = ['Animation']
                elif 13 <= age <= 17:
                    available_genres = ['Adventure', 'Comedy']
                else:
                    available_genres = ['Tous les films'] + unique_genres
                
                genre = st.selectbox('🎭 Genre', available_genres)

                if st.button('🔍 Rechercher'):
                    try:
                        def get_movie_recommendations(rate, year, runtime_range, selected_genre, df, model, scaler, feature_columns, age, all_decades=False):
                            input_features = np.zeros(len(feature_columns))
                            
                            runtime = (runtime_range[0] + runtime_range[1]) / 2 if runtime_range else df['runtimeMinutes'].mean()
                            budget = df['budget'].mean()
                            
                            values_array = np.array([[age, rate, year, runtime, budget]])
                            normalized_values = scaler.transform(values_array)
                            
                            for i, feature in enumerate(['castage', 'rate', 'year', 'runtimeMinutes', 'budget']):
                                input_features[feature_columns.index(feature)] = normalized_values[0][i]
                            
                            genre_column = f'genre_{selected_genre}'
                            if genre_column in df.columns:
                                genre_idx = feature_columns.index(genre_column)
                                input_features[genre_idx] = 1
                            
                            distances, indices = model.kneighbors([input_features], n_neighbors=20)
                            recommendations = df.iloc[indices[0]]
                            
                            if 6 <= age <= 12:
                                recommendations = recommendations[recommendations['genres'].apply(
                                    lambda x: 'Animation' in x
                                )]
                            elif 13 <= age <= 17:
                                recommendations = recommendations[
                                    (recommendations['genres'].apply(lambda x: any(genre in x for genre in ['Adventure', 'Comedy']))) &
                                    (recommendations['runtimeMinutes'] <= 100)
                                ]
                            
                            if not all_decades:
                                if year_selection_type == 'Par année':
                                    recommendations = recommendations[recommendations['year'] == year]
                                else:
                                    decade_start = year
                                    decade_end = year + 9
                                    recommendations = recommendations[(recommendations['year'] >= decade_start) &
                                                                   (recommendations['year'] <= decade_end)]
                            
                            if runtime_range:
                                recommendations = recommendations[(recommendations['runtimeMinutes'] >= runtime_range[0]) &
                                                               (recommendations['runtimeMinutes'] <= runtime_range[1])]
                            
                            return recommendations.head(10)
                        
                        # Afficher les résultats dans la colonne de droite
                        with col_results:
                            recommendations = get_movie_recommendations(
                                selected_rate, selected_year, selected_runtime_range,
                                genre, df_movies, model, scaler, feature_columns,
                                age, all_decades
                            )
                            
                            if recommendations.empty:
                                st.warning('❌ Aucun film ne correspond à vos critères')
                            else:
                                for _, movie in recommendations.iterrows():
                                    st.write(f"**{movie['title']}** ({int(movie['year'])}) ⭐ {movie['rate']:.1f}")
                                    st.write(f"⏱️ Durée: {int(movie['runtimeMinutes'])} minutes")
                                    st.write(f"🎭 Genres : {', '.join(movie['genres'])}")
                                    st.write("---")
                    except Exception as e:
                        with col_results:
                            st.error(f"❌ Une erreur s'est produite : {str(e)}")
        except FileNotFoundError:
            with col_results:
                st.error("❌ Le fichier de données n'a pas été trouvé.")
        except Exception as e:
            with col_results:
                st.error(f"❌ Une erreur s'est produite : {str(e)}")

def prefs_recommendations():
    st.title('🎥 Assistant cinématographique')
    
    if st.button('← Retour au choix du système'):
        st.session_state.page = 'home'
        st.rerun()
        
    st.write("👋 Vous avez choisi les recommandations par films préférés !")
    st.write("💡 Pensez à un film que vous aimez particulièrement et laissez-nous vous guider.")

# Gestion de la navigation
if 'page' not in st.session_state:
    st.session_state.page = 'home'

if st.session_state.page == 'home':
    home()
elif st.session_state.page == 'params':
    params_recommendations()
elif st.session_state.page == 'prefs':
    prefs_recommendations()