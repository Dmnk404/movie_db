import os
import requests
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

DB_URL = "sqlite:///data/movies.db"
engine = create_engine(DB_URL, echo=True)

load_dotenv()
OMDB_API_KEY = os.getenv("OMDB_API_KEY")


def create_tables() -> None:
    """Create all necessary tables if they do not exist."""
    with engine.begin() as conn:
        # Users table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL
            )
        """))

        # Movies table with user_id foreign key, note, and imdb_id
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                year INTEGER NOT NULL,
                rating REAL NOT NULL,
                poster_url TEXT NOT NULL,
                note TEXT DEFAULT '',
                imdb_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """))


def create_user(username: str) -> bool:
    try:
        with engine.begin() as conn:
            conn.execute(text("INSERT INTO users (username) VALUES (:username)"), {"username": username})
        return True
    except SQLAlchemyError as e:
        print(f"Error creating user: {e}")
        return False

def select_user() -> dict:
    """
    Prompt the user to select an existing user or create a new one.
    Returns the selected user's dictionary with 'id' and 'username'.
    """
    while True:
        users = list_users()
        print("Select a user:")
        for i, u in enumerate(users, start=1):
            print(f"{i}. {u['username']}")
        print(f"{len(users) + 1}. Create new user")

        choice = input("Enter choice: ").strip()
        try:
            choice = int(choice)
            if 1 <= choice <= len(users):
                user = users[choice - 1]
                print(f"Welcome back, {user['username']}! 🎬")
                return user
            elif choice == len(users) + 1:
                username = input("Enter new username: ").strip()
                if not username:
                    print("Username cannot be empty.")
                    continue
                if create_user(username):
                    # Reload user to get correct ID
                    user = next(u for u in list_users() if u['username'] == username)
                    print(f"User '{username}' created and selected.")
                    return user
                else:
                    print("Failed to create user. Try again.")
            else:
                print("Invalid choice. Try again.")
        except ValueError:
            print("Invalid input. Enter a number.")

def list_users() -> list[dict]:
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT id, username FROM users"))
            return result.mappings().all()
    except SQLAlchemyError as e:
        print(f"Error listing users: {e}")
        return []


def add_movie_from_omdb(title: str, user_id: int) -> bool:
    """Search for a movie via OMDb and add it for the given user."""
    if not OMDB_API_KEY:
        print("OMDb API key not found in environment.")
        return False

    try:
        # Step 1: Search for matching movies
        search_url = f"http://www.omdbapi.com/?apikey={OMDB_API_KEY}&s={title}"
        search_response = requests.get(search_url, timeout=10).json()

        if search_response.get("Response") == "False":
            print(f"No movies found for '{title}'.")
            return False

        movies = search_response.get("Search", [])
        if not movies:
            print(f"No movies found for '{title}'.")
            return False

        # Step 2: Let user choose if multiple results exist
        if len(movies) > 1:
            print("\nMultiple matches found:")
            for i, movie in enumerate(movies, start=1):
                print(f"{i}. {movie['Title']} ({movie.get('Year', 'N/A')})")
            try:
                choice = int(input("Enter the number of the correct movie: ").strip())
                selected = movies[choice - 1]
            except (ValueError, IndexError):
                print("Invalid choice.")
                return False
        else:
            selected = movies[0]

        imdb_id = selected["imdbID"]

        # Step 3: Fetch full details
        detail_url = f"http://www.omdbapi.com/?apikey={OMDB_API_KEY}&i={imdb_id}"
        detail_response = requests.get(detail_url, timeout=10).json()

        if detail_response.get("Response") == "False":
            print("Could not fetch movie details.")
            return False

        title = detail_response["Title"]
        year = int(detail_response["Year"].split("–")[0])
        rating = float(detail_response["imdbRating"]) if detail_response.get("imdbRating") not in [None, "N/A"] else 0.0
        poster_url = detail_response.get("Poster", "N/A")

        # Step 4: Save to DB with user_id
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT OR IGNORE INTO movies 
                    (title, year, rating, poster_url, note, imdb_id, user_id)
                    VALUES (:title, :year, :rating, :poster_url, :note, :imdb_id, :user_id)
                """),
                {
                    "title": title,
                    "year": year,
                    "rating": rating,
                    "poster_url": poster_url,
                    "note": "",
                    "imdb_id": imdb_id,
                    "user_id": user_id
                }
            )

        print(f"✅ Added '{title}' ({year}) with rating {rating}/10 for user ID {user_id}.")
        return True

    except requests.RequestException as e:
        print(f"Network error while contacting OMDb: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error during OMDb lookup: {e}")
        return False


def list_movies(user_id: int) -> dict[str, dict[str, int | float | str]]:
    """Retrieve all movies for a given user."""
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT title, year, rating, poster_url, note, imdb_id FROM movies WHERE user_id = :user_id"),
                {"user_id": user_id}
            )
            movies = result.fetchall()
        return {
            row.title: {
                "year": row.year,
                "rating": row.rating,
                "poster_url": row.poster_url,
                "note": row.note,
                "imdb_id": row.imdb_id,
            }
            for row in movies
        }
    except SQLAlchemyError as e:
        print(f"Database error while listing movies: {e}")
        return {}

def get_movie(title: str, user_id: int) -> dict[str, int | float | str] | None:
    """Retrieve a single movie by title for a given user, including note."""
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT title, year, rating, note FROM movies WHERE title = :title AND user_id = :user_id"),
                {"title": title, "user_id": user_id}
            ).fetchone()
            if result:
                return {"title": result.title, "year": result.year, "rating": result.rating, "note": result.note}
            else:
                print(f"No movie found with title '{title}' for this user.")
                return None
    except SQLAlchemyError as e:
        print(f"Database error while retrieving movie '{title}': {e}")
        return None

def add_movie(title: str, year: int, rating: float, user_id: int) -> bool:
    """Add a new movie for a given user."""
    try:
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO movies (title, year, rating, poster_url, user_id)
                    VALUES (:title, :year, :rating, 'N/A', :user_id)
                """),
                {"title": title, "year": year, "rating": rating, "user_id": user_id}
            )
            print(f"Movie '{title}' added successfully for user ID {user_id}.")
            return True
    except SQLAlchemyError as e:
        print(f"Database error while adding movie '{title}': {e}")
        return False


def update_movie(title: str, rating: float | None, note: str | None, user_id: int) -> bool:
    """Update the rating and/or note of a movie for a given user."""
    try:
        set_clauses = []
        params = {"title": title, "user_id": user_id}

        if rating is not None:
            set_clauses.append("rating = :rating")
            params["rating"] = rating
        if note is not None:
            set_clauses.append("note = :note")
            params["note"] = note

        if not set_clauses:
            print("Nothing to update.")
            return False

        set_clause = ", ".join(set_clauses)

        with engine.begin() as conn:
            result = conn.execute(
                text(f"UPDATE movies SET {set_clause} WHERE title = :title AND user_id = :user_id"),
                params
            )

        if result.rowcount:
            print(f"Movie '{title}' updated successfully for user ID {user_id}.")
            return True
        else:
            print(f"No movie found with title '{title}' for this user.")
            return False

    except SQLAlchemyError as e:
        print(f"Database error while updating movie '{title}': {e}")
        return False

def delete_movie(title: str, user_id: int) -> bool:
    """Delete a movie by title for a given user."""
    try:
        with engine.begin() as conn:
            result = conn.execute(
                text("DELETE FROM movies WHERE title = :title AND user_id = :user_id"),
                {"title": title, "user_id": user_id}
            )
            if result.rowcount:
                print(f"Movie '{title}' deleted successfully for user ID {user_id}.")
                return True
            else:
                print(f"No movie found with title '{title}' for this user.")
                return False
    except SQLAlchemyError as e:
        print(f"Database error while deleting movie '{title}': {e}")
        return False
