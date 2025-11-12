import random
import sys
from storage import movie_storage_sql as storage
from collections import Counter
from termcolor import colored as colored_text
from matplotlib import pyplot as plt
from storage.movie_storage_sql import engine, list_movies
from sqlalchemy import text

MAIN_MENU = ("Exit",
            "List movies",
            "Add movie from omdb",
            "Delete movie",
            "Update movie",
            "Stats",
            "Random movie",
            "Search movie",
            "Movies sorted by rating",
            "Create Rating Histogram",
             "Filter Movies",
             "Generate Website")

def print_menu(menu):
    """Prints the menu"""
    print(colored_text("\033[1mMenu:", 34))
    for idx, menu_item in enumerate(menu, start=0):
        print(colored_text(f"{idx}. {menu_item}", 36))


def wait_for_input():
    """Ask and wait for user input"""
    input(colored_text("Press enter to continue", 33))


def return_user_choice():
    """Ask for and return user input"""
    choice = input(colored_text("Enter choice (0–11): ", "yellow"))
    print()
    return choice

def movie_exists(movies, movie_name):
    """Checks if movie exists in given dict"""
    return movie_name in movies

def close_programm():
    """Ends the program"""
    print("Bye!")
    sys.exit()

def command_add_movie_omdb():
    """Add a movie using the OMDb API."""
    title = input(colored_text("Enter movie title: ", 33)).strip()
    if not title:
        print(colored_text("Title cannot be empty.", 31))
        return

    try:
        from storage.movie_storage_sql import add_movie_from_omdb
        success = add_movie_from_omdb(title)
        if success:
            print(colored_text(f"Movie '{title}' added successfully from OMDb.", 32))
        else:
            print(colored_text(f"No movie found for '{title}'.", 33))
    except Exception as e:
        print(colored_text(f"Error adding movie: {e}", 31))


def command_list_movies():
    """Retrieve and display all movies from the database."""
    movies = storage.list_movies()
    print(f"{len(movies)} movies in total")
    for title, data in movies.items():
        print(colored_text(f"🎬 {title} ({data['year']}) - {data['rating']}/10", 36))
        print(colored_text(f"Poster: {data['poster_url']}", 34))


def command_delete_movie():
    """Delete a movie using the SQL storage."""
    title = input(colored_text("Enter movie name to delete: ", 33)).strip()
    if not title:
        print(colored_text("Title cannot be empty.", 31))
        return
    storage.delete_movie(title)

def command_update_movie():
    """Update a movie's rating using the SQL storage."""
    title = input(colored_text("Enter movie name: ", 33)).strip()
    if not title:
        print(colored_text("Title cannot be empty.", 31))
        return

    try:
        new_rating = float(input(colored_text("Enter new rating (0-10): ", 33)))
        if 0 <= new_rating <= 10:
            storage.update_movie(title, new_rating)
        else:
            print(colored_text("Rating must be between 0 and 10.", 31))
    except ValueError:
        print(colored_text("Invalid rating input.", 31))

def show_stats():
    """Show basic statistics for movies."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*) as count,
                       AVG(rating) as avg_rating,
                       MIN(rating) as min_rating,
                       MAX(rating) as max_rating
                FROM movies
            """))
            stats = result.mappings().first()
            if stats["count"] == 0:
                print(colored_text("No movies in database.", 33))
                return

            print(colored_text("\n--- Movie Statistics ---", 36))
            print(f"Total movies: {stats['count']}")
            print(f"Average rating: {stats['avg_rating']:.2f}")
            print(f"Lowest rating: {stats['min_rating']:.1f}")
            print(f"Highest rating: {stats['max_rating']:.1f}")
    except Exception as e:
        print(colored_text(f"Error fetching statistics: {e}", 31))

def random_movie():
    """Select a random movie from the database."""
    try:
        movies = list_movies()
        if not movies:
            print(colored_text("No movies found.", 33))
            return

        title = random.choice(list(movies.keys()))
        data = movies[title]
        print(colored_text(f"🎥 Random movie: {title} ({data['year']}) - {data['rating']}/10", 36))
    except Exception as e:
        print(colored_text(f"Error selecting random movie: {e}", 31))

def calculate_distance(string1, string2, memo=None):
    """calculate levenshtein distance"""
    if memo is None:
        memo = {}
    if (string1, string2) in memo:
        return memo[(string1, string2)]

    if len(string1) == 0:
        return len(string2)
    if len(string2) == 0:
        return len(string1)
    if string1[0] == string2[0]:
        memo[(string1, string2)] = calculate_distance(string1[1:], string2[1:], memo)
        return memo[(string1, string2)]

    delete = calculate_distance(string1[1:], string2, memo)
    insert = calculate_distance(string1, string2[1:], memo)
    replace = calculate_distance(string1[1:], string2[1:], memo)

    memo[(string1, string2)] = 1 + min(delete, insert, replace)
    return memo[(string1, string2)]


def count_matches(string1, string2):
    """inaccurate pre-selection based on similar chars"""
    threshold = 0.7

    min_matches = int(len(string1) * threshold)
    string1_count = Counter(string1)
    string2_count = Counter(string2)
    matches = sum((string1_count & string2_count).values())
    return matches >= min_matches


def search_movie():
    """Search for a movie by partial title."""
    query = input(colored_text("Enter part of the movie title: ", 33)).strip()
    if not query:
        print(colored_text("Search query cannot be empty.", 31))
        return

    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT title, year, rating FROM movies WHERE title LIKE :query"),
                {"query": f"%{query}%"}
            )
            rows = result.mappings().all()

        if not rows:
            print(colored_text("No matching movies found.", 33))
            return

        print(colored_text(f"\nMovies matching '{query}':", 36))
        for row in rows:
            print(f"{row['title']} ({row['year']}) - {row['rating']}/10")
    except Exception as e:
        print(colored_text(f"Error during search: {e}", 31))

def print_sorted_movies():
    """Print all movies sorted by rating (descending)."""
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT title, year, rating FROM movies ORDER BY rating DESC")
            )
            rows = result.mappings().all()

        if not rows:
            print(colored_text("No movies found.", 33))
            return

        print(colored_text("\n--- Movies sorted by rating ---", 36))
        for row in rows:
            print(f"{row['title']} ({row['year']}) - {row['rating']}/10")
    except Exception as e:
        print(colored_text(f"Error sorting movies: {e}", 31))

def create_rating_histogram():
    """Create and show a histogram of movie ratings."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT rating FROM movies"))
            ratings = [row[0] for row in result.fetchall()]

        if not ratings:
            print(colored_text("No ratings available.", 33))
            return

        plt.hist(ratings, bins=10, edgecolor='black')
        plt.title("Movie Ratings Histogram")
        plt.xlabel("Rating")
        plt.ylabel("Frequency")
        plt.show()
    except Exception as e:
        print(colored_text(f"Error generating histogram: {e}", 31))

def filter_movies():
    """Filter movies by minimum rating or year."""
    try:
        min_rating = input(colored_text("Enter minimum rating (leave blank for none): ", 33)).strip()
        min_year = input(colored_text("Enter minimum year (leave blank for none): ", 33)).strip()

        conditions = []
        params = {}
        if min_rating:
            conditions.append("rating >= :min_rating")
            params["min_rating"] = float(min_rating)
        if min_year:
            conditions.append("year >= :min_year")
            params["min_year"] = int(min_year)

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

        with engine.connect() as conn:
            result = conn.execute(
                text(f"SELECT title, year, rating FROM movies {where_clause} ORDER BY rating DESC"),
                params
            )
            rows = result.mappings().all()

        if not rows:
            print(colored_text("No movies match the filter.", 33))
            return

        print(colored_text("\n--- Filtered Movies ---", 36))
        for row in rows:
            print(f"{row['title']} ({row['year']}) - {row['rating']}/10")
    except Exception as e:
        print(colored_text(f"Error filtering movies: {e}", 31))

def generate_website():
    """Generate an HTML website with all movies."""

    movies = list_movies()
    if not movies:
        print("No movies available to generate website.")
        return

    # Template-Datei laden
    with open("_static/index_template.html", "r", encoding="utf-8") as f:
        template = f.read()

    # Movie-Grid generieren
    movie_html_blocks = []
    for title, data in movies.items():
        movie_html_blocks.append(f"""
        <div class="movie">
            <img src="{data.get('poster_url', '')}" alt="{title} poster">
            <h2>{title}</h2>
            <p>{data.get('year', 'N/A')}</p>
            <p>⭐ {data.get('rating', 'N/A')}/10</p>
        </div>
        """)

    movie_grid = "\n".join(movie_html_blocks)

    # Platzhalter ersetzen
    website_html = template.replace("__TEMPLATE_TITLE__", "My Movie Collection")
    website_html = website_html.replace("__TEMPLATE_MOVIE_GRID__", movie_grid)

    # index.html schreiben
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(website_html)

    print("✅ Website was generated successfully.")
MENU_ACTIONS = {
    "0": close_programm,
    "1": command_list_movies,
    "2": command_add_movie_omdb,
    "3": command_delete_movie,
    "4": command_update_movie,
    "5": show_stats,
    "6": random_movie,
    "7": search_movie,
    "8": print_sorted_movies,
    "9": create_rating_histogram,
    "10": filter_movies,
    "11": generate_website
}


def main():
    """Main function of the program."""

    print("********** My Movies Database **********")

    while True:
        print()
        print_menu(MAIN_MENU)
        print()

        answer = return_user_choice()
        action = MENU_ACTIONS.get(answer)

        if answer == "0":
            action()
        elif action:
            action()
        else:
            print(colored_text("That's not a valid choice. Please try again.", 31))

        print()
        wait_for_input()


if __name__ == "__main__":
    storage.create_table()
    main()
