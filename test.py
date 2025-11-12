from storage import movie_storage_sql as storage

movies = storage.list_movies(current_user['id'])
for title, data in movies.items():
    print(title, data.get('imdb_id'))