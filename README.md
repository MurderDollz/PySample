# WEB-BASED RECIPE BLOG SYSTEM

A platform for sharing, discovering, and organizing recipe creations.

## Project Overview

This is a web-based recipe blog system built with Flask that allows users to share recipes, discover new dishes, and organize their culinary creations.

## Features (Planned)

- User authentication (register, login, profile management)
- Recipe creation, editing, and deletion
- Recipe categorization and tagging
- Recipe search and filtering
- User favorites and collections
- Comments and ratings on recipes
- Responsive design for all devices

## Current Status

This is the initial landing page implementation with:
- Home page with featured recipes
- About page
- Contact page
- Basic styling and UI elements

## Setup Instructions

1. Clone this repository:
```
git clone <repository-url>
```

2. Create a virtual environment and activate it:
```
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

3. Install the required dependencies:
```
pip install -r requirements.txt
```

4. Run the Flask application:
```
python app.py
```

5. Open your browser and navigate to:
```
http://localhost:5000
```

## Project Structure

- `app.py` - Main Flask application file
- `templates/` - HTML templates
- `static/` - Static files (CSS, JS, images)
  - `css/` - Stylesheets
  - `js/` - JavaScript files
  - `images/` - Image files

## Technologies Used

- Flask - Python web framework
- Bootstrap - Front-end framework
- MySQL (planned for future) - Database
- HTML/CSS/JavaScript - Front-end development 