import os
import requests
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

DB_URL = "sqlite:///movies.db"
engine = create_engine(DB_URL, echo=True)

# Create the movies table if it does not exist
with engine.begin() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT UNIQUE NOT NULL,
            year INTEGER NOT NULL,
            rating REAL NOT NULL
        )
    """))

load_dotenv()
OMDB_API_KEY = os.getenv("OMDB_API_KEY")


def add_movie_from_omdb(title: str) -> bool:
    """Search for a movie via OMDb and add it to the database."""
    if not OMDB_API_KEY:
        print("OMDb API key not found in environment.")
        return False

    try:
        # Step 1: Search all possible matches
        search_url = f"http://www.omdbapi.com/?apikey={OMDB_API_KEY}&s={title}"
        search_response = requests.get(search_url).json()

        if search_response.get("Response") == "False":
            print(f"No movies found for '{title}'.")
            return False

        movies = search_response.get("Search", [])
        if not movies:
            print(f"No movies found for '{title}'.")
            return False

        # Step 2: If multiple matches → let user choose
        if len(movies) > 1:
            print("\nMultiple matches found:")
            for i, movie in enumerate(movies, start=1):
                print(f"{i}. {movie['Title']} ({movie.get('Year', 'N/A')})")
            choice = input("Enter the number of the correct movie: ").strip()
            try:
                choice = int(choice)
                selected = movies[choice - 1]
            except (ValueError, IndexError):
                print("Invalid choice.")
                return False
        else:
            selected = movies[0]

        imdb_id = selected["imdbID"]

        # Step 3: Fetch detailed info for the selected movie
        detail_url = f"http://www.omdbapi.com/?apikey={OMDB_API_KEY}&i={imdb_id}"
        detail_response = requests.get(detail_url).json()

        if detail_response.get("Response") == "False":
            print("Could not fetch movie details.")
            return False

        title = detail_response["Title"]
        year = int(detail_response["Year"].split("–")[0])
        rating = float(detail_response.get("imdbRating", 0)) if detail_response.get("imdbRating") != "N/A" else 0.0

        # Step 4: Add to database
        from movie_storage_sql import engine
        with engine.begin() as conn:
            conn.execute(
                text("INSERT OR IGNORE INTO movies (title, year, rating) VALUES (:title, :year, :rating)"),
                {"title": title, "year": year, "rating": rating}
            )
        print(f"✅ Added '{title}' ({year}) with rating {rating}/10.")
        return True

    except Exception as e:
        print(f"Error during OMDb lookup: {e}")
        return False

def list_movies() -> dict[str, dict[str, int | float]]:
    """Retrieve all movies from the database."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT title, year, rating FROM movies"))
            movies = result.fetchall()
        return {row.title: {"year": row.year, "rating": row.rating} for row in movies}
    except SQLAlchemyError as e:
        print(f"Database error while listing movies: {e}")
        return {}

def get_movie(title: str) -> dict[str, int | float] | None:
    """Retrieve a single movie by title."""
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT title, year, rating FROM movies WHERE title = :title"),
                {"title": title}
            ).fetchone()
            if result:
                return {"title": result.title, "year": result.year, "rating": result.rating}
            else:
                print(f"No movie found with title '{title}'.")
                return None
    except SQLAlchemyError as e:
        print(f"Database error while retrieving movie '{title}': {e}")
        return None

def add_movie(title: str, year: int, rating: float) -> bool:
    """Add a new movie to the database."""
    try:
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO movies (title, year, rating)
                    VALUES (:title, :year, :rating)
                """),
                {"title": title, "year": year, "rating": rating}
            )
            print(f"Movie '{title}' added successfully.")
            return True
    except SQLAlchemyError as e:
        print(f"Database error while adding movie '{title}': {e}")
        return False

def update_movie(title: str, rating: float) -> bool:
    """Update the rating of a movie in the database."""
    try:
        with engine.begin() as conn:
            result = conn.execute(
                text("UPDATE movies SET rating = :rating WHERE title = :title"),
                {"title": title, "rating": rating}
            )
            if result.rowcount:
                print(f"Movie '{title}' updated successfully to rating {rating}.")
                return True
            else:
                print(f"No movie found with title '{title}'.")
                return False
    except SQLAlchemyError as e:
        print(f"Database error while updating movie '{title}': {e}")
        return False

def delete_movie(title: str) -> bool:
    """Delete a movie by title from the database."""
    try:
        with engine.begin() as conn:
            result = conn.execute(
                text("DELETE FROM movies WHERE title = :title"),
                {"title": title}
            )
            if result.rowcount:
                print(f"Movie '{title}' deleted successfully.")
                return True
            else:
                print(f"No movie found with title '{title}'.")
                return False
    except SQLAlchemyError as e:
        print(f"Database error while deleting movie '{title}': {e}")
        return False
