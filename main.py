import pandas as pd
import numpy as np
import sqlite3

def reduce_memory_usage(df):
    # Drop unnecessary columns
    df = df.drop(columns=["titleType", "originalTitle", "endYear"])
    # Replace '\N' with NaN and drop rows with any NaN values
    df = df.apply(lambda col: col.replace('\\N', np.nan))
    df = df.dropna(axis=0, how='any').reset_index()
    return df

def clean_data(df):
    # Convert columns to appropriate data types
    df['startYear'] = pd.to_numeric(df['startYear'], errors='coerce')
    df['runtimeMinutes'] = pd.to_numeric(df['runtimeMinutes'], errors='coerce')
    df = df[(df['startYear'] >= 2015) & (df['runtimeMinutes'] >= 90) & (df['isAdult'] == 0)]
    df = df.drop(columns=["isAdult"]).reset_index()
    return df

def create_tables(df):
    # Create separate tables for movies, genres, and movie genres relationships
    movies_df = df[['tconst', 'primaryTitle', 'startYear', 'runtimeMinutes']]
    genres_array = df["genres"].str.split(',').explode().unique()
    genres_df = pd.DataFrame(genres_array, columns=["genre"])
    movie_genre_df = (
        df[['tconst', 'genres']]
        .assign(genre=lambda x: x['genres'].str.split(','))
        .explode('genre')
        .assign(genre=lambda x: x['genre'].str.strip())
        .drop(columns='genres')
        .reset_index(drop=True)
    )
    return movies_df, genres_df, movie_genre_df

def main():
    # Load data
    df = pd.read_csv('data/movies.csv')
    
    # Reduce memory usage
    df = reduce_memory_usage(df)
    
    # Clean data
    df = clean_data(df)
    
    # Create tables
    movies_df, genres_df, movie_genre_df = create_tables(df)

    del df
    
    # # Save tables to CSV files
    # movies_df.to_csv('movies.csv', index=False)
    # genres_df.to_csv('genres.csv', index=False)
    # movie_genre_df.to_csv('movie_genres.csv', index=False)

    # Save movies table to SQLite database
    conn = sqlite3.connect('data/movies.db')
    movies_df.to_sql('movies', conn, if_exists='replace', index=False)
    genres_df.to_sql('genres', conn, if_exists='replace', index=False)
    movie_genre_df.to_sql('movie_genres', conn, if_exists='replace', index=False)
    conn.close()

    del movies_df, genres_df, movie_genre_df

if __name__ == "__main__":
    main()