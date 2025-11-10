import movie_storage_sql as storage
import random
import sys
from statistics import median
from collections import Counter
import matplotlib.pyplot as plt



MAIN_MENU = ("Exit",
            "List movies",
            "Add movie",
            "Delete movie",
            "Update movie",
            "Stats",
            "Random movie",
            "Search movie",
            "Movies sorted by rating",
            "Create Rating Histogram",
             "Filter Movies")


def colored_text(text, color_code):
    """Uses ANSI escape codes to change color"""
    return f"\033[{color_code}m{text}\033[0m"


def print_menu(menu):
    """Prints the menu"""
    print(colored_text("\033[1mMenu:", 34))
    for idx, menu_item in enumerate(menu, start=0):
        print(colored_text(f"{idx}. {menu_item}", 36))


def wait_for_input():
    """Ask and wait for user input"""
    input(colored_text("Press enter to continue", 33))


def return_user_choice():
    """Asks for and return user input"""
    choice = input(colored_text("Enter choice (1-9): ", 33))
    print()
    return choice

def movie_exists(movies, movie_name):
    """Checks if movie exists in given dict"""
    return movie_name in movies

def close_programm():
    """Ends the program"""
    print("Bye!")
    sys.exit()


def command_list_movies():
    """Retrieve and display all movies from the database."""
    movies = storage.list_movies()
    print(f"{len(movies)} movies in total")
    for movie, data in movies.items():
        print(f"{movie} ({data['year']}): {data['rating']}")

def add_movie(movies):
    """Adds movie to given dict"""
    while True:
        new_movie = input(colored_text("Enter new Movie Name: ", 33).strip())
        if new_movie == "":
            print("Please enter a movie name.")
            continue
        elif movie_exists(movies, new_movie):
            print(colored_text(f"Movie {new_movie} already exist!", 31))
            continue
        break
    while True:
        try:
            movies_year = int(input(colored_text("Enter Movie Year: ", 33)))
            break
        except ValueError:
             print(colored_text("Please enter valid Movie Year!", 31))
    while True:
        try:
            movie_rating = float(input(colored_text("Enter new movie rating (0-10): ", 33)))
            if 0 <= movie_rating <= 10:
                break
            print(colored_text(f"Rating {movie_rating} is invalid", 31))
        except ValueError:
            print(colored_text("Please enter valid rating (0-10).", 31))
    movies[new_movie] =\
        {"Rating": movie_rating,
        "Year": movies_year}
    print(colored_text(f"Movie {new_movie} successfully added", 32))
    return movies

def del_movie(movies):
    """Deletes movie from dict"""
    while True:
        movie_name = input(colored_text("Enter movie name to delete: ", 33))
        if not movie_exists(movies, movie_name):
            print(colored_text(f"Movie {movie_name} doesn't exist!", 31))
            continue
        else:
            movies.pop(movie_name)
            print(colored_text(f"Movie {movie_name} successfully deleted", 32))
        return movies


def update_movie(movies):
    """Updates movie from dict"""
    while True:
        movie_name = input(colored_text("Enter movie name: ", 33))
        if not movie_exists(movies, movie_name):
            print(colored_text(f"Movie {movie_name} doesn't exist!", 31))
            continue
        else:
            col_prompt = (colored_text("Enter new rating (0-10): ", 33))
            new_rating = float(input(col_prompt))
            if 0 <= new_rating <= 10:
                movies[movie_name]["Rating"] = new_rating
            else:
                print(colored_text(f"Rating {new_rating} is invalid", 31))
                continue
        return movies


def show_stats(movies):
    """Prints movie statistics"""

    if not movies:
        print(colored_text("No movies available to show stats.", 31))
        return

    ratings = [info["Rating"] for info in movies.values()]

    average_rating = sum(ratings) / len(ratings)
    median_rating = median(ratings)
    best_rating = max(ratings)
    worst_rating = min(ratings)

    best_movies = [(movie, info["Rating"]) for movie, info in movies.items() if info["Rating"] == best_rating]
    worst_movies = [(movie, info["Rating"]) for movie, info in movies.items() if info["Rating"] == worst_rating]

    print(colored_text(f"Average rating: {average_rating:.2f}", 36))
    print(colored_text(f"Median rating: {median_rating:.2f}", 36))

    print(colored_text("Best movie(s): ", 36), end="")
    for movie, rating in best_movies:
        print(colored_text(f"{movie} ({rating}) ", 36), end="")
    print()

    print(colored_text("Worst movie(s): ", 36), end="")
    for movie, rating in worst_movies:
        print(colored_text(f"{movie} ({rating}) ", 36), end="")
    print()



def random_movie(movies):
    """Prints random movie from dict"""
    movie, rating = random.choice(list(movies.items()))
    print(colored_text(f"Your movie tonight: {movie}, it's rated {rating}", 36))


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


def search_movie(movies):
    """Search for movie in dict"""
    user_query = input(colored_text("Enter part of movie name: ", 33)).lower()
    similar_matches = []

    results = [(movie, rating) for movie, rating in movies.items() if user_query in movie.lower()]

    if results:
        for movie, rating in results:
            print(colored_text(f"{movie}, {rating}", 36))
        return

    for movie, rating in movies.items():
        movie_lower = movie.lower()
        if count_matches(user_query, movie_lower):
            distance = calculate_distance(
            user_query, movie_lower) / max(len(user_query),
            len(movie_lower))

            if distance <= 0.7:
                similar_matches.append((movie, rating, distance))

    if similar_matches:
        similar_matches.sort(key=lambda x: x[2])

        print(colored_text(f"Didn't find '{user_query}', but found similar matches:", 36))
        for movie, rating, distance in similar_matches:
            print(colored_text
            (f"{movie}, Rating: {rating} (Similarity Score: {round(1 - distance, 2)})", 36))
    else:
        print(colored_text
        (f"No matches found for '{user_query}'.", 31))


def print_sorted_movies(movies):
    """Prints sorted movie list by rating or year."""
    if not movies:
        print(colored_text("No movies available to sort.", 31))
        return
    while True:
        print(colored_text("Sort movies by:", 33))
        print("1. Rating (highest first)")
        print("2. Year (chronological)")

        choice = input(colored_text("Enter choice (1 or 2): ", 33)).strip()

        if choice == "1":
            # Sort by rating descending
            sorted_movies = sorted(movies.items(), key=lambda item: item[1]["Rating"], reverse=True)
            print(colored_text("\nMovies sorted by rating (highest first):", 34))
            break
        elif choice == "2":
            order = input(colored_text("Show latest movies first? (y/n): ", 33)).strip().lower()
            reverse_order = order == "y"
            # Sort by year
            sorted_movies = sorted(movies.items(), key=lambda item: item[1]["Year"], reverse=reverse_order)
            direction = "newest first" if reverse_order else "oldest first"
            print(colored_text(f"\nMovies sorted by year ({direction}):", 34))
            break
        else:
            print(colored_text("Invalid choice. Try again.", 31))
            continue

    for movie, info in sorted_movies:
        print(colored_text(f"{movie} ({info['Year']}), Rating: {info['Rating']}", 36))


def create_rating_histogram(movies):
    """Create a rating histogram."""
    if not movies:
        print(colored_text("No movies available to create histogram.", 31))
        return

    ratings = [info["Rating"] for info in movies.values()]
    plt.hist(ratings, bins="auto", color='skyblue', edgecolor='black')
    plt.xlabel("Ratings")
    plt.ylabel("Frequency")
    plt.title('Rating Histogram')

    name = input(colored_text("Enter save file name: ", 33)).strip()
    if not name:
        print(colored_text("Filename cannot be empty.", 31))
        return

    plt.savefig(f"{name}.png")
    print(colored_text(f"Histogram saved as {name}.png", 32))
    plt.clf()

def filter_movies(movies):
    """Filter movies by rating and/or year."""
    if not movies:
        print(colored_text("No movies available to filter.", 31))
        return

    while True:
        try:
            print(colored_text("Filter movies by:", 33))

            min_rating_input = input(colored_text(
                "Enter minimum rating (leave blank for no minimum)(0-10): ", 33)).strip()
            min_rating = float(min_rating_input) if min_rating_input else 0

            min_year_input = input(colored_text(
                "Enter start year (leave blank for no limit): ", 33)).strip()
            min_year = int(min_year_input) if min_year_input else 0

            max_year_input = input(colored_text(
                "Enter end year (leave blank for no limit): ", 33)).strip()
            max_year = int(max_year_input) if max_year_input else float('inf')

            break

        except ValueError:
            print(colored_text("Invalid input. Try again.", 31))

    # Apply filters
    filtered_movies = {}
    for movie, info in movies.items():
        year = info.get("Year")
        rating = info.get("Rating")
        if year is None or rating is None:
            continue  # Skip incomplete entries
        if min_year <= year <= max_year and rating >= min_rating:
            filtered_movies[movie] = info

    # Print results
    if not filtered_movies:
        print(colored_text("No movies matched your filter.", 31))
    else:
        print(colored_text("Filtered movies:", 34))
        for movie, info in filtered_movies.items():
            print(colored_text(f"{movie} ({info['Year']}): {info['Rating']}", 36))




MENU_ACTIONS = {
    "0": close_programm,
    "1": list_movies,
    "2": add_movie,
    "3": del_movie,
    "4": update_movie,
    "5": show_stats,
    "6": random_movie,
    "7": search_movie,
    "8": print_sorted_movies,
    "9": create_rating_histogram,
    "10": filter_movies
}


def main():
    """Main function of the program."""

    print("********** My Movies Database **********")

    while True:
        print()
        print_menu(MAIN_MENU)
        print()

        movies = movie_storage.get_movies()

        try:
            answer = return_user_choice()
            action = MENU_ACTIONS.get(answer)
            if answer == "0":
                action()
            elif action:
                if answer in ("2", "3", "4"):
                    movies = action(movies)
                    movie_storage.save_movies(movies)  # Änderungen persistent machen
                else:
                    action(movies)

            print()
            wait_for_input()
        except TypeError:
            print(colored_text("That's not a valid choice. Please try again.", 31))


if __name__ == "__main__":
    main()
