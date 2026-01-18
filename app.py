import streamlit as st
import sqlite3
import pandas as pd

# Configuration de la page
st.set_page_config(
    page_title="Base de Données de Films",
    page_icon="🎬",
    layout="wide"
)
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor() 

# Titre principal
st.title("🎬 Base de Données de Films")
st.markdown("---")

def load_data():
    # Charger les données initiales
    try:
        with sqlite3.connect('data/movies.db') as conn:
            movies_df = pd.read_sql_query("SELECT * FROM movies", conn)
            genres_df = pd.read_sql_query("SELECT * FROM genres", conn)
            movie_genres_df = pd.read_sql_query("SELECT * FROM movie_genres", conn)

    except Exception as e:
        st.error(f"❌ Erreur de connexion à la base de données : {e}")
        st.stop()
    return movies_df, genres_df, movie_genres_df

def search_movies(movies_df, movie_genres_df, search_query, selected_genre, year_range):
    # Filtrer les films selon les critères de recherche
    filtered_movies = movies_df.copy()

    if search_query:
        filtered_movies = filtered_movies[
            filtered_movies['primaryTitle'].str.contains(search_query, case=False, na=False) |
            filtered_movies['tconst'].astype(str).str.contains(search_query)
        ]

    if selected_genre != "Tous":
        movie_ids = movie_genres_df[movie_genres_df['genre'] == selected_genre]['tconst'].unique()
        filtered_movies = filtered_movies[filtered_movies['tconst'].isin(movie_ids)]

    filtered_movies = filtered_movies[
        (filtered_movies['startYear'] >= year_range[0]) &
        (filtered_movies['startYear'] <= year_range[1])
    ]

    return filtered_movies

movies_df, genres_df, movie_genres_df = load_data()

# Sidebar pour les filtres
with st.sidebar:
    st.header("🔍 Filtres de Recherche")
    
    # Recherche par texte
    search_query = st.text_input("Rechercher un film (titre ou ID):", "")
    
    # Filtre par genre
    genres_list = ["Tous"] + sorted(genres_df['genre'].tolist()) if not genres_df.empty else ["Tous"]
    selected_genre = st.selectbox("Filtrer par genre:", genres_list)
    
    # Filtre par année
    min_year = int(movies_df['startYear'].min())
    max_year = int(movies_df['startYear'].max())
    year_range = st.slider(
        "Année de sortie:",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year),
        step=1
    )
       
    # Statistiques
    st.markdown("---")
    st.header("📊 Statistiques")
    st.metric("Nombre total de films", len(movies_df))
    st.metric("Nombre de genres différents", len(genres_df))
    st.metric("Années couvertes", f"{min_year} - {max_year}")
    
    # Aperçu des données
    with st.expander("📁 Voir les tables"):
        st.caption("Table Movies (10 premières lignes)")
        st.dataframe(movies_df.head(10), width="content", hide_index=True)
        
        st.caption("Table Genres")
        st.dataframe(genres_df, width="stretch", hide_index=True)

# Section principale
tab1, tab2, tab3 = st.tabs(["🎬 Liste des Films", "📊 Statistiques", "ℹ️ Informations"])

with tab1:
    st.header("Liste des Films")

    filtered_movies = search_movies(movies_df, movie_genres_df, search_query, selected_genre, year_range)

    if not filtered_movies.empty:
        movies_show = filtered_movies.reset_index(drop=True)
    else:
        movies_show = movies_df.copy()


    st.success(f"📽️ {len(movies_show)} films trouvés")

    # Options d'affichage
    # col1, col2 = st.columns([3, 1])
    # with col1:
    movies_per_page = st.selectbox(
        "Films par page:",
        [10, 25, 50, 100],
        index=0,
        key="movies_per_page"
    )

    # Pagination
    total_pages = max(1, len(movies_show) // movies_per_page + 
                    (1 if len(movies_show) % movies_per_page > 0 else 0))

    if total_pages > 1:
        page = st.number_input(
            "Page:",
            min_value=1,
            max_value=total_pages,
            value=1,
            step=1,
            key="page_number"
        )
    else:
        page = 1
    
    start_idx = (page - 1) * movies_per_page
    end_idx = min(start_idx + movies_per_page, len(movies_show))

    # Afficher les films
    for idx in range(start_idx, end_idx):
        movie = movies_show.iloc[idx]
        with st.container():
            col1, col2, col3 = st.columns([3, 2, 2])
            
            with col1:
                st.subheader(movie['primaryTitle'])
                genre = movie_genres_df[movie_genres_df['tconst'] == movie['tconst']]['genre'].tolist()
                genre_str = ', '.join(genre)
                st.caption(genre_str)
                
                st.caption(f"imdbID: {movie['tconst']}")

            with col2:
                st.metric("Année", movie['startYear'])
                
            with col3:
                st.metric("Durée", f"{movie['runtimeMinutes']} min")

            # Détails expansibles
            with st.expander("📋 Plus d'informations", expanded=False):
                details_col1, details_col2 = st.columns(2)
                with details_col1:
                    st.write(f"**Titre :** {movie['primaryTitle']}")
                    st.write(f"**imdbID :** `{movie['tconst']}`")
                    st.write(f"**Année :** {movie['startYear']}")
                with details_col2:
                    st.write(f"**Durée :** {movie['runtimeMinutes']} minutes")
                    st.write(f"**Genres :** {genre_str}")

            st.markdown("---")

    # Informations de pagination
    st.caption(f"📄 Page {page}/{total_pages} - Films {start_idx + 1} à {end_idx} sur {len(movies_show)}")

    # Bouton pour exporter les résultats# Bouton pour exporter les résultats
    if st.button("💾 Exporter les résultats CSV"):
        csv = movies_show.to_csv(index=False)
        st.download_button(
            label="Télécharger CSV",
            data=csv,
            file_name="films_filtres.csv",
            mime="text/csv"
        )  


with tab2:
    st.header("Statistiques des Films")

    years_count = movies_df['startYear'].value_counts().sort_index()
    st.subheader("Nombre de Films par Année")
    st.bar_chart(years_count)

    genre_count = movie_genres_df['genre'].value_counts()
    st.subheader("Nombre de Films par Genre")
    st.bar_chart(genre_count)

    movie_per_year = movies_df.groupby('startYear').size()
    st.subheader("Films Ajoutés par Année")
    st.bar_chart(movie_per_year, y_label="Nombre de Films", x_label="Année")

with tab3:
    st.header("ℹ️ À propos de cette base de données")
    
    st.markdown("""
    ### 📋 Structure de la base de données
    
    Cette application utilise une base de données SQLite avec 3 tables principales:
    
    1. **movies** - Informations sur les films
       - `tconst` : Identifiant unique
       - `primaryTitle` : Titre principal
       - `startYear` : Année de sortie
       - `runtimeMinutes` : Durée en minutes
    
    2. **genres** - Liste de tous les genres disponibles
       - `genre` : Nom du genre
    
    3. **movie_genres** - Table de relation films/genres
       - `tconst` : Identifiant du film
       - `genre` : Genre associé
    
    ### 🔧 Fonctionnalités
    
    - 🔍 Recherche de films par titre ou ID
    - 🎭 Filtrage par genre
    - 📅 Filtrage par période
    - 📊 Visualisation des statistiques
    - 📄 Navigation paginée
    - 💾 Export des résultats
    
    ### 📊 Données
    """)

    # Afficher les métriques dynamiques
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total des films", len(movies_df) if not movies_df.empty else 0)
    with col2:
        st.metric("Genres disponibles", len(genres_df) if not genres_df.empty else 0)
    with col3:
        st.metric("Période couverte", f"{min_year} - {max_year}")

    st.markdown("""
    ### 🛠️ Technologies utilisées
    
    - **Streamlit** : Interface utilisateur
    - **Pandas** : Manipulation des données
    - **SQLite** : Base de données
    - **Python** : Langage de programmation
    
    ### 📍 Emplacement de la base de données
    
    La base de données se trouve dans le fichier :
    ```
    data/movies.db
    ```
    
    ### 🚀 Comment exécuter cette application
    
    1. Assurez-vous que Python est installé
    2. Installez les dépendances : `pip install streamlit pandas`
    3. Lancez l'application : `streamlit run app.py`
    """)

    # Aperçu des données brutes
    with st.expander("🔍 Aperçu des données brutes"):

        tab_movies, tab_genres, tab_relations = st.tabs(["Films", "Genres", "Relations"])
        
        with tab_movies:
            st.dataframe(movies_df.head(20), width="stretch", hide_index=True)
        
        with tab_genres:
            st.dataframe(genres_df, width="stretch")
        
        with tab_relations:
            if not movie_genres_df.empty:
                st.dataframe(movie_genres_df.head(20), width="stretch")
            else:
                st.info("Table des relations vide")

# Footer
st.markdown("---")
st.caption("🎬 Base de données de films • Interface Streamlit • " + 
           f"{len(movies_df)} films • {len(genres_df)} genres")
