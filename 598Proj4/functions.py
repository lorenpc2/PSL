from typing import Dict

import numpy as np
import pandas as pd
import requests

# Define the URL for movie data
ratings_data_url = "https://liangfgithub.github.io/MovieData/movies.dat?raw=true"

# Fetch the data from the URL
response = requests.get(ratings_data_url)

# Split the data into lines and then split each line using "::"
movie_lines = response.text.split('\n')
movie_data = [line.split("::") for line in movie_lines if line]

# Create a DataFrame from the movie data
movies = pd.DataFrame(movie_data, columns=['movie_id', 'title', 'genres'])
movies['movie_id'] = movies['movie_id'].astype(int)

genres = list(
    sorted(set([genre for genres in movies.genres.unique() for genre in genres.split("|")]))
)

top_similarities_matrix = pd.read_csv("598Proj4/data/Smat_sub.csv")

# Precomputed movies ratings to be used as filler recommendations
# when myICBF cannot recommend at least ten movies
ci_movie_ratings = pd.read_csv("598Proj4/data/ci_movie_ratings.csv", index_col=[0]).rating

def get_displayed_movies():
    return movies.head(100)


def get_popular_movies(genre: str):
    # Results generated by the algorithm laid out in System I.  Hardcoding the results
    # for all possible genres in the dataset in order to improve app performance.
    genre_to_popular_movies = {
        "Action": np.array([257, 1180, 847, 1178, 1959, 2502, 1179, 108, 1192, 1203]),
        "Adventure": np.array([257, 1180, 1178, 3103, 1179, 1192, 907, 1186, 2836, 1239]),
        "Animation": np.array([1132, 0, 735, 3045, 711, 1205, 3360, 2286, 3682, 2931]),
        "Children's": np.array([0, 907, 3045, 1081, 33, 2286, 3682, 1058, 2692, 591]),
        "Comedy": np.array([2789, 3164, 1762, 3538, 1179, 2327, 1120, 2928, 1132, 0]),
        "Crime": np.array([847, 49, 3587, 604, 293, 1575, 1203, 1195, 1215, 3366]),
        "Documentary": np.array([777, 3811, 3269, 1131, 2861, 243, 126, 1172, 1995, 2790]),
        "Drama": np.array([2789, 315, 523, 847, 1178, 1959, 589, 3538, 3313, 977]),
        "Fantasy": np.array([257, 1081, 2728, 1058, 2559, 2803, 244, 2105, 782, 2899]),
        "Film-Noir": np.array([1575, 537, 901, 1232, 910, 3366, 1247, 1264, 2117, 918]),
        "Horror": np.array([3211, 1196, 1258, 1201, 1366, 2647, 1238, 1928, 1313, 2595]),
        "Musical": np.array([907, 1268, 887, 902, 2231, 1202, 1878, 933, 1052, 591]),
        "Mystery": np.array([1575, 892, 901, 1232, 1194, 912, 891, 574, 1264, 3661]),
        "Romance": np.array([1179, 900, 1192, 2327, 352, 1245, 1227, 957, 2623, 1211]),
        "Sci-Fi": np.array([257, 1178, 2502, 1192, 740, 585, 537, 1220, 1196, 1250]),
        "Thriller": np.array([2693, 589, 2502, 49, 604, 1575, 585, 892, 896, 1220]),
        "War": np.array([523, 1178, 1959, 108, 900, 1192, 740, 352, 1230, 1182]),
        "Western": np.array([3538, 1284, 2961, 1246, 3602, 1183, 586, 1263, 2968, 595]),
    }

    return movies.iloc[genre_to_popular_movies.get(genre, np.array([]))]


def get_recommended_movies(new_user_ratings: Dict[str, int]) -> pd.DataFrame:
    icbf_input_as_array = _convert_ratings_input(new_user_ratings)
    icbf_input_as_series = pd.Series(icbf_input_as_array)
    recommendations = myIBCF(icbf_input_as_series)
    return recommendations


def _convert_ratings_input(ratings_input: Dict[str, int]) -> np.array:
    """Convert dict of user ratings into input expected by myIBCF"""
    n_movies = top_similarities_matrix.shape[0]
    data = np.zeros(n_movies)
    data[:] = np.nan
    ret = pd.Series(data=data, index=top_similarities_matrix.index)
    for movie_id, rating in ratings_input.items():
        ret[f"m{movie_id}"] = rating
    return ret


def _convert_ratings_output(ibcf_output) -> pd.DataFrame:
    """Convert recommendations outputted by myICBF into dataframe with movie_id and title"""
    movie_ids = [int(x[1:]) for x in ibcf_output.index.values]
    df = pd.DataFrame(data=movie_ids, columns=["movie_id"]).merge(movies, on="movie_id", how="inner")
    return df


def myIBCF(w):
    S = pd.read_csv('598Proj4/data/Smat_sub.csv', index_col=0)
    R = pd.read_csv('598Proj4/data/Movie_Rmat.csv', index_col=0)
    M = pd.read_csv('data/movies.dat', sep='::', engine = 'python', encoding="ISO-8859-1", header=None)
    #M.columns = ['MovieID', 'Title', 'Genres']
    M.columns = ['movie_id', 'title', 'genres']
    M['movie_id'] = movies['movie_id'].astype(int)

    w_with_rate = w.dropna()
    rated_movies = w_with_rate.index
    predicted_ratings = w.copy()
    all_movies = S.index

    for movie in all_movies:
        if movie not in rated_movies:
            S_movie = S.loc[movie] # Similarity of the movie
            S_movie_index = S_movie.dropna().index # Only select movies with similarities
            useful_movies = S_movie_index.intersection(rated_movies) # Further choose movies with both similarities and ratings
            # print(useful_movies)
            # print(w['m2196'])

            U = np.sum(S_movie[useful_movies]*predicted_ratings[useful_movies])
            D = np.sum(S_movie[useful_movies])

            if D!=0:
                predicted_ratings[movie] = U/D

    predicted_ratings = predicted_ratings.drop(rated_movies)
    res = predicted_ratings.sort_values(ascending=False)[:10]
    res.index = map(lambda x: int(x[1:]), res.index)
    res = res.sort_index()

    final_df = M[M['movie_id'].isin(res.index)]
    final_df = final_df.drop(columns=['genres'])
    final_df['rate'] = res.values
    final_df = final_df.sort_values(by=['rate'], ascending=False)
    final_df = final_df.reset_index(drop=True)
    return final_df
