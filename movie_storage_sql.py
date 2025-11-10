from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Define the database URL
DB_URL = "sqlite:///movies.db"

# Create the engine
engine = create_engine(DB_URL, echo=True)

# Create the movies table if it does not exist
with engine.connect() as connection:
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT UNIQUE NOT NULL,
            year INTEGER NOT NULL,
            rating REAL NOT NULL
        )
    """))
    connection.commit()

def list_movies() -> dict[str, dict[str, float | int]]:
    """Retrieve all movies from the database.

    Returns:
        dict[str, dict]: A dictionary of movies, where each key is the title,
        and the value contains the year and rating.
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT title, year, rating FROM movies"))
            movies = result.fetchall()

        return {row.title: {"year": row.year, "rating": row.rating} for row in movies}
    except SQLAlchemyError as e:
        print(f"Database error while listing movies: {e}")
        return {}

def add_movie(title: str, year: int, rating: float) -> bool:
    """Add a new movie to the database.

    Args:
        title (str): The title of the movie.
        year (int): The release year.
        rating (float): The movie rating.

    Returns:
        bool: True if the movie was added successfully, False otherwise.
    """
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



def delete_movie(title: str) -> bool:
    """Delete a movie by title from the database.

    Returns:
        bool: True if a movie was deleted, False otherwise.
    """
    try:
        with engine.begin() as conn:  # handles commit/rollback automatically
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

def update_movie(title: str, rating: float) -> bool:
    """Update the rating of a movie in the database.

    Args:
        title (str): The title of the movie to update.
        rating (float): The new rating value.

    Returns:
        bool: True if the movie was updated, False if not found or on error.
    """
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