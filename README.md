# Movie Project

A simple Python project to manage and display a movie collection.  
Movies can be added manually or fetched automatically from the OMDb API.  
The project also generates a static HTML website to showcase all movies.

## Features

- Add movies manually or via OMDb API
- List, update, delete movies
- Display movie statistics
- Random movie selection
- Search movies by title
- Generate a website with a movie grid and posters

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/MovieProject.git
   cd MovieProject
   
2. Create a virtual environment:
    ```bash
   python -m venv venv
    source venv/bin/activate  # Linux/macOS
    venv\Scripts\activate     # Windows
   
3. Install dependencies:
    ```bash
    pip install -r requirements.txt

4. Create a .env file and add your OMDb API key:
    ```env
   OMDB_API_KEY=your_api_key_here

5. Run the program:
    ```bash
   python run.py

# Directory Structure

MovieProject/
│

├── run.py

├── storage/
│   └── movie_storage_sql.py

├── data/
│   └── movies.db

├── _static/
│   ├── index_template.html
│   └── style.css

├── requirements.txt

├── .gitignore

└── .env

# Usage

Start the app via python run.py.

Follow the menu to add movies, list them, search, generate website, etc.

Generated website index.html will be in the root folder.

# Dependencies

- requests
- SQLAlchemy
- python-dotenv
- matplotlib
- termcolor


    