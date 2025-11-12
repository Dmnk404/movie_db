import os
import random
import sys
from collections import Counter
from termcolor import colored as colored_text
from matplotlib import pyplot as plt
from storage import movie_storage_sql as storage

MAIN_MENU = (
    "Exit",
    "List movies",
    "Add movie from OMDb",
    "Delete movie",
    "Update movie",
    "Stats",
    "Random movie",
    "Search movie",
    "Movies sorted by rating",
    "Create Rating Histogram",
    "Filter Movies",
    "Generate Website",
    "Switch User"
)

def print_menu(menu):
    """Print the main menu."""
    print(colored_text("\033[1mMenu:", 34))
    for idx, menu_item in enumerate(menu):
        print(colored_text(f"{idx}. {menu_item}", 36))

def wait_for_input():
    """Pause until the user presses enter."""
    input(colored_text("Press enter to continue", 33))

def return_user_choice():
    """Prompt the user to enter a menu choice and return it."""
    choice = input(colored_text("Enter choice: ", "yellow")).strip()
    print()
    return choice

def close_program():
    """Exit the program."""
    print("Bye!")
    sys.exit()

# ----------------- Movie Commands -----------------

def command_list_movies(current_user):
    """List all movies for the current user."""
    movies = storage.list_movies(current_user['id'])
    if not movies:
        print(colored_text(f"{current_user['username']}, your movie collection is empty.", 33))
        return
    print(f"{len(movies)} movies in total")
    for title, data in movies.items():
        print(colored_text(f"🎬 {title} ({data['year']}) - {data['rating']}/10", 36))
        print(colored_text(f"Poster: {data['poster_url']}", 34))

def command_add_movie_omdb(current_user):
    """Add a movie from OMDb for the current user."""
    title = input(colored_text("Enter movie title: ", 33)).strip()
    if not title:
        print(colored_text("Title cannot be empty.", 31))
        return
    success = storage.add_movie_from_omdb(title, current_user['id'])
    if success:
        print(colored_text(f"Movie '{title}' added successfully.", 32))
    else:
        print(colored_text(f"No movie found for '{title}'.", 33))

def command_delete_movie(current_user):
    """Delete a movie by title for the current user."""
    title = input(colored_text("Enter movie name to delete: ", 33)).strip()
    if not title:
        print(colored_text("Title cannot be empty.", 31))
        return
    storage.delete_movie(title, current_user['id'])

def command_update_movie(current_user):
    """Update a movie's rating and add a note for the current user."""
    title = input("Enter movie name: ").strip()
    if not title:
        print("Title cannot be empty.")
        return

    try:
        new_rating = input("Enter new rating (leave blank to keep current): ").strip()
        new_rating = float(new_rating) if new_rating else None
    except ValueError:
        print("Invalid rating input.")
        return

    note = input("Enter movie note (leave blank to keep current): ").strip()
    note = note if note else None

    storage.update_movie(title, new_rating, note, current_user['id'])

def show_stats(current_user):
    """Display statistics about the user's movie collection."""
    try:
        stats = storage.get_stats(current_user['id'])
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

def random_movie(current_user):
    """Display a random movie from the user's collection."""
    movies = storage.list_movies(current_user['id'])
    if not movies:
        print(colored_text("No movies found.", 33))
        return
    title = random.choice(list(movies.keys()))
    data = movies[title]
    print(colored_text(f"🎥 Random movie: {title} ({data['year']}) - {data['rating']}/10", 36))

def search_movie(current_user):
    """Search for movies by partial title for the current user."""
    query = input(colored_text("Enter part of the movie title: ", 33)).strip()
    if not query:
        print(colored_text("Search query cannot be empty.", 31))
        return
    rows = storage.search_movies(query, current_user['id'])
    if not rows:
        print(colored_text("No matching movies found.", 33))
        return
    print(colored_text(f"\nMovies matching '{query}':", 36))
    for row in rows:
        print(f"{row['title']} ({row['year']}) - {row['rating']}/10")

def print_sorted_movies(current_user):
    """List movies sorted by rating (descending) for the current user."""
    rows = storage.sorted_movies(current_user['id'])
    if not rows:
        print(colored_text("No movies found.", 33))
        return
    print(colored_text("\n--- Movies sorted by rating ---", 36))
    for row in rows:
        print(f"{row['title']} ({row['year']}) - {row['rating']}/10")

def create_rating_histogram(current_user):
    """Display a histogram of movie ratings for the current user."""
    ratings = storage.get_ratings(current_user['id'])
    if not ratings:
        print(colored_text("No ratings available.", 33))
        return
    plt.hist(ratings, bins=10, edgecolor='black')
    plt.title("Movie Ratings Histogram")
    plt.xlabel("Rating")
    plt.ylabel("Frequency")
    plt.show()

def filter_movies(current_user):
    """Filter movies by minimum rating and/or year for the current user."""
    min_rating = input(colored_text("Enter minimum rating (leave blank for none): ", 33)).strip()
    min_year = input(colored_text("Enter minimum year (leave blank for none): ", 33)).strip()
    rows = storage.filter_movies(min_rating, min_year, current_user['id'])
    if not rows:
        print(colored_text("No movies match the filter.", 33))
        return
    print(colored_text("\n--- Filtered Movies ---", 36))
    for row in rows:
        print(f"{row['title']} ({row['year']}) - {row['rating']}/10")

def generate_website(user_id: int, username: str):
    """Generate an HTML website for the user's movies with clickable posters to IMDb."""
    movies = storage.list_movies(user_id)  # gibt dict mit title -> {year, rating, poster_url, note, imdb_id}

    if not movies:
        print("No movies available to generate website.")
        return

    # Template laden
    template_path = "_static/index_template.html"
    if not os.path.exists(template_path):
        print(f"Template file '{template_path}' not found.")
        return

    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    # Movie-Grid generieren
    movie_html_blocks = []
    for title, data in movies.items():
        imdb_id = data.get("imdb_id", "")
        note = data.get("note") or "No note available."
        rating = data.get("rating", "N/A")
        poster_url = data.get("poster_url", "")

        movie_html_blocks.append(f"""
            <div class="movie-card">
                <a href="https://www.imdb.com/title/{imdb_id}" target="_blank">
                    <img src="{poster_url}" alt="{title} poster">
                </a>
                <div class="movie-note">{note}</div>
                <h2>{title}</h2>
                <p>{data.get('year', 'N/A')} | ⭐ {rating}/10</p>
            </div>
        """)

    movie_grid = "\n".join(movie_html_blocks)

    # Platzhalter ersetzen
    website_html = template.replace("__TEMPLATE_TITLE__", f"{username}'s Movie Collection")
    website_html = website_html.replace("__TEMPLATE_MOVIE_GRID__", movie_grid)

    output_dir = "generated_site"
    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(output_dir, f"{username}_movies.html")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(website_html)

    print(f"✅ Website generated at '{output_file}'.")

def switch_user(_):
    """Switch the current user."""
    return storage.select_user()

def generate_website_menu(current_user):
    """Wrapper, um die Website für den aktuellen User zu erzeugen."""
    generate_website(current_user['id'], current_user['username'])

# ----------------- MENU ACTIONS -----------------
MENU_ACTIONS = {
    "0": close_program,
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
    "11": generate_website_menu,
    "12": switch_user
}

# ----------------- MAIN -----------------
def main():
    """Main loop: select user, display menu, and handle commands."""
    current_user = storage.select_user()

    while True:
        print()
        print_menu(MAIN_MENU)
        print()
        choice = return_user_choice()
        action = MENU_ACTIONS.get(choice)

        if action:
            if choice == "12":
                current_user = action(None)
            else:
                action(current_user)
        else:
            print(colored_text("That's not a valid choice. Please try again.", 31))
        print()
        wait_for_input()

if __name__ == "__main__":
    storage.create_tables()
    main()
