from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_mysqldb import MySQL
from flask_wtf.csrf import CSRFProtect, generate_csrf
import hashlib
import os
import uuid
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename

# Add function to calculate time difference for relative timestamps
def get_relative_time(timestamp):
    now = datetime.now()
    diff = now - timestamp
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return f"{int(seconds)} sec ago"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        return f"{minutes} min ago"
    elif seconds < 86400:
        hours = int(seconds // 3600)
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif seconds < 604800:
        days = int(seconds // 86400)
        return f"{days} day{'s' if days > 1 else ''} ago"
    elif seconds < 2592000:
        weeks = int(seconds // 604800)
        return f"{weeks} week{'s' if weeks > 1 else ''} ago"
    elif seconds < 31536000:
        months = int(seconds // 2592000)
        return f"{months} month{'s' if months > 1 else ''} ago"
    else:
        years = int(seconds // 31536000)
        return f"{years} year{'s' if years > 1 else ''} ago"

app = Flask(__name__)

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Secret key for sessions
app.secret_key = os.urandom(24)

# Exempt certain routes from CSRF protection if needed
# csrf.exempt(["some_route"])  # Uncomment and modify if you need to exempt specific routes

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'blog'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# File upload configuration
app.config['UPLOAD_FOLDER'] = 'static/uploads/profile_photos'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Initialize MySQL
mysql = MySQL(app)

# Ensure the upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database tables
def initialize_database():
    try:
        cur = mysql.connection.cursor()
        
        # Create recipe_likes table if it doesn't exist
        cur.execute("""
            CREATE TABLE IF NOT EXISTS recipe_likes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                recipe_id INT NOT NULL,
                user_id INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_like (recipe_id, user_id),
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Create recipe_comments table if not exists with replies_count column
        cur.execute("""
            CREATE TABLE IF NOT EXISTS recipe_comments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                recipe_id INT NOT NULL,
                user_id INT NOT NULL,
                comment_text TEXT NOT NULL,
                parent_comment_id INT NULL,
                reactions_count INT DEFAULT 0,
                replies_count INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Create comment_reactions table if not exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS comment_reactions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                comment_id INT NOT NULL,
                user_id INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_reaction (comment_id, user_id),
                FOREIGN KEY (comment_id) REFERENCES recipe_comments(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Check if recipes table has likes_count column
        cur.execute("""
            SELECT COUNT(*) as count 
            FROM information_schema.columns 
            WHERE table_name = 'recipes' 
            AND column_name = 'likes_count'
        """)
        
        if cur.fetchone()['count'] == 0:
            # Add likes_count column if it doesn't exist
            cur.execute("ALTER TABLE recipes ADD COLUMN likes_count INT DEFAULT 0")
            
            # Initialize likes_count for existing recipes
            cur.execute("""
                UPDATE recipes r 
                SET likes_count = (
                    SELECT COUNT(*) 
                    FROM recipe_likes 
                    WHERE recipe_id = r.id
                )
            """)
            
        # Check if recipes table has comments_count column
        cur.execute("""
            SELECT COUNT(*) as count 
            FROM information_schema.columns 
            WHERE table_name = 'recipes' 
            AND column_name = 'comments_count'
        """)
        
        if cur.fetchone()['count'] == 0:
            # Add comments_count column if it doesn't exist
            cur.execute("ALTER TABLE recipes ADD COLUMN comments_count INT DEFAULT 0")
            
            # Initialize comments_count for existing recipes
            cur.execute("""
                UPDATE recipes r 
                SET comments_count = (
                    SELECT COUNT(*) 
                    FROM recipe_comments 
                    WHERE recipe_id = r.id
                )
            """)
            
        # Check if recipe_comments table has reactions_count column
        cur.execute("""
            SELECT COUNT(*) as count 
            FROM information_schema.columns 
            WHERE table_name = 'recipe_comments' 
            AND column_name = 'reactions_count'
        """)
        
        if cur.fetchone()['count'] == 0:
            # Add reactions_count column if it doesn't exist
            cur.execute("ALTER TABLE recipe_comments ADD COLUMN reactions_count INT DEFAULT 0")
            
        # Initialize reactions_count for all comments
        cur.execute("""
            UPDATE recipe_comments rc 
            SET reactions_count = (
                SELECT COUNT(*) 
                FROM comment_reactions 
                WHERE comment_id = rc.id
            )
        """)
        
        # Initialize replies_count for all comments
        cur.execute("""
            UPDATE recipe_comments rc 
            SET replies_count = (
                SELECT COUNT(*) 
                FROM recipe_comments 
                WHERE parent_comment_id = rc.id
            )
        """)
        
        # Create featured_recipes table if it doesn't exist
        cur.execute("""
            CREATE TABLE IF NOT EXISTS featured_recipes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                recipe_id INT NOT NULL,
                featured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_featured (recipe_id),
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
            )
        """)
            
        # Additional initialization code for other tables could be added here
        
        mysql.connection.commit()
        cur.close()
        return True
        
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        # This is debug only, will be removed in production
        return False

# Database initialization can be triggered via endpoint instead of automatic execution
@app.route('/init-database')
def init_database_endpoint():
    # Only allow admin to initialize database
    if 'logged_in' in session and session.get('user_type') == 'admin':
        success = initialize_database()
        if success:
            return "Database initialized successfully."
        else:
            return "Error initializing database. Check server logs."
    else:
        return "Unauthorized access.", 403

# Function to check if file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Context processor to make user data available in all templates
@app.context_processor
def inject_user_data():
    user_data = None
    if 'logged_in' in session and session['user_id']:
        try:
            # Get user data
            cur = mysql.connection.cursor()
            if session['user_type'] == 'user':
                cur.execute("SELECT * FROM users WHERE id = %s", [session['user_id']])
            else:
                # Admin data has limited fields
                cur.execute("SELECT id, username, email FROM admins WHERE id = %s", [session['user_id']])
            user_data = cur.fetchone()
            cur.close()
        except Exception as e:
            print(f"Error fetching user data: {e}")
    
    # Add CSRF token to all templates
    return dict(current_user=user_data, csrf_token=generate_csrf)

@app.route('/')
def index():
    # Get featured recipes from database
    try:
        cur = mysql.connection.cursor()
        
        # Get featured recipes with author details
        cur.execute("""
            SELECT r.*, 
                   CONCAT(u.first_name, ' ', u.last_name) as author_name,
                   (r.prep_time + COALESCE(r.cook_time, 0)) as total_time
            FROM recipes r
            JOIN users u ON r.user_id = u.id
            JOIN featured_recipes fr ON r.id = fr.recipe_id
            WHERE r.privacy = 'public'
            ORDER BY fr.featured_at DESC
            LIMIT 6
        """)
        
        featured_recipes = cur.fetchall()
        
        # If no featured recipes are found, get the most liked recipes instead
        if not featured_recipes:
            cur.execute("""
                SELECT r.*, 
                       CONCAT(u.first_name, ' ', u.last_name) as author_name,
                       (r.prep_time + COALESCE(r.cook_time, 0)) as total_time
                FROM recipes r
                JOIN users u ON r.user_id = u.id
                WHERE r.privacy = 'public'
                ORDER BY r.likes_count DESC, r.created_at DESC
                LIMIT 6
            """)
            
            featured_recipes = cur.fetchall()
        
        cur.close()
        
    except Exception as e:
        print(f"Error fetching featured recipes: {str(e)}")
        featured_recipes = []
    
    # Get recipe categories
    categories = [
        {'name': 'Breakfast', 'icon': 'breakfast.png'},
        {'name': 'Lunch', 'icon': 'lunch.png'},
        {'name': 'Dinner', 'icon': 'dinner.png'},
        {'name': 'Desserts', 'icon': 'dessert.png'},
        {'name': 'Vegetarian', 'icon': 'vegetarian.png'},
        {'name': 'Quick Meals', 'icon': 'quick.png'}
    ]
    
    return render_template('index.html', 
                          title='Recipe Blog - Home',
                          featured_recipes=featured_recipes,
                          categories=categories,
                          now=datetime.now())

@app.route('/about')
def about():
    return render_template('about.html', title='About Us', now=datetime.now())

@app.route('/contact')
def contact():
    return render_template('contact.html', title='Contact Us', now=datetime.now())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username_email = request.form['username_email']
        password = request.form['password']
        
        # Check if admin login (admin/admin123)
        if username_email == 'admin' and password == 'admin123':
            # Hard-coded admin account for demo
            admin = {
                'id': 1,
                'username': 'admin',
                'email': 'admin@example.com'
            }
            
            # Set session
            session['logged_in'] = True
            session['user_id'] = admin['id']
            session['username'] = admin['username']
            session['user_type'] = 'admin'
            
            flash('You are now logged in as admin', 'success')
            return redirect(url_for('admin_dashboard'))
        
        # For other users, hash the password for database comparison
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        # Create cursor
        cur = mysql.connection.cursor()
        
        # Check if user login
        try:
            # Find user by email
            cur.execute("SELECT * FROM users WHERE email = %s AND password = %s", 
                       [username_email, hashed_password])
            user = cur.fetchone()
            
            cur.close()
            
            if user:
                # Check if the account is suspended
                if user.get('is_suspended', 0):
                    flash('This account has been suspended. Please contact the administrator.', 'danger')
                    return render_template('login.html', now=datetime.now())
                    
                # User login successful
                session['logged_in'] = True
                session['user_id'] = user['id']
                
                # Use display_name if available, otherwise create one from first_name and last_name
                if 'display_name' in user and user['display_name']:
                    display_name = user['display_name']
                else:
                    display_name = f"{user['first_name'].lower()}{user['last_name'].lower()}"
                    
                session['username'] = display_name
                session['user_type'] = 'user'
                
                flash(f'Welcome back, {user["first_name"]}!', 'success')
                return redirect(url_for('user_dashboard'))
            else:
                # Invalid login
                flash('Invalid email or password. Please try again.', 'danger')
        except Exception as e:
            flash(f'Login error: {str(e)}. Please try again.', 'danger')
            print(f"Database error: {str(e)}")
        
        return render_template('login.html', now=datetime.now())

    return render_template('login.html', title='Login', now=datetime.now())

@app.route('/debug-db')
def debug_db():
    """Debug route to check database structure"""
    try:
        cur = mysql.connection.cursor()
        cur.execute("SHOW COLUMNS FROM users")
        columns = cur.fetchall()
        
        # Get a sample user
        cur.execute("SELECT * FROM users LIMIT 1")
        sample_user = cur.fetchone()
        
        cur.close()
        
        # Format the data for display
        result = {
            'columns': [col['Field'] for col in columns] if columns else [],
            'sample_user': {k: str(v) for k, v in sample_user.items()} if sample_user else None
        }
        
        return render_template('debug.html', title='Database Debug', data=result, now=datetime.now())
    except Exception as e:
        return f"Database error: {str(e)}"

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get form fields
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        phone = request.form['phone']
        birthday = request.form['birthday'] if request.form['birthday'] else None
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Validation
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html', now=datetime.now())
        
        # Generate a display name (but don't store it as username in db)
        display_name = f"{first_name.lower()}{last_name.lower()}"
        
        # Hash the password
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        # Create cursor
        cur = mysql.connection.cursor()
        
        try:
            # Check if email already exists
            cur.execute("SELECT * FROM users WHERE email = %s", [email])
            existing_user = cur.fetchone()
            
            if existing_user:
                flash('Email already exists', 'danger')
                cur.close()
                return render_template('register.html', now=datetime.now())
            
            # Handle profile picture upload
            profile_pic_path = None
            if 'profile_pic' in request.files:
                profile_pic = request.files['profile_pic']
                if profile_pic.filename != '':
                    if allowed_file(profile_pic.filename):
                        # Create a unique filename
                        filename = secure_filename(profile_pic.filename)
                        unique_filename = f"user_{uuid.uuid4().hex}_{filename}"
                        profile_pic_path = f"uploads/profile_photos/{unique_filename}"
                        
                        # Save the file
                        try:
                            full_path = os.path.join(app.static_folder, 'uploads/profile_photos', unique_filename)
                            profile_pic.save(full_path)
                            print(f"Saved profile pic to: {full_path}")
                        except Exception as e:
                            flash(f'Error uploading profile picture: {e}', 'danger')
                            print(f"Profile pic upload error: {str(e)}")
                    else:
                        flash('Invalid file type. Allowed types are: png, jpg, jpeg, gif', 'danger')
                        return render_template('register.html', now=datetime.now())
            
            # Prepare current date for created_at
            current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Insert new user - only include columns that exist in the database
            # Get existing columns in the users table
            cur.execute("SHOW COLUMNS FROM users")
            columns_data = cur.fetchall()
            available_columns = [col['Field'] for col in columns_data]
            
            # Define fields and values we want to insert
            field_value_map = {
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'phone': phone,
                'birthday': birthday, 
                'profile_pic': profile_pic_path,
                'password': hashed_password,
                'created_at': current_date,
                'display_name': display_name  # Use display_name instead of username
            }
            
            # Filter out fields that don't exist in the database
            fields = []
            values = []
            for field, value in field_value_map.items():
                if field in available_columns:
                    fields.append(field)
                    values.append(value)
            
            placeholders = ', '.join(['%s'] * len(fields))
            columns = ', '.join(fields)
            
            query = f"INSERT INTO users ({columns}) VALUES ({placeholders})"
            
            print(f"Executing query: {query}")
            print(f"With fields: {fields}")
            
            cur.execute(query, values)
            
            # Commit to DB
            mysql.connection.commit()
            cur.close()
            
            # Show success message but don't log in or redirect
            success_message = f'Registration successful, {first_name}! Your account has been created. You can now log in.'
            print(f"Setting flash message: {success_message}")
            
            # Clear any existing flashed messages to ensure this one appears
            session.pop('_flashes', None)
            
            # Set the success message
            flash(success_message, 'success')
            
            # Render template with the success message
            return render_template('register.html', title='Register', now=datetime.now(), 
                                  show_success=True, success_message=success_message)
                
        except Exception as e:
            error_msg = str(e)
            flash(f'Error creating account: {error_msg}', 'danger')
            print(f"Registration error: {error_msg}")
            mysql.connection.rollback()
            cur.close()
            return render_template('register.html', now=datetime.now())
    
    return render_template('register.html', title='Register', now=datetime.now())

@app.route('/admin-dashboard')
def admin_dashboard():
    # Check if user is logged in as admin
    if 'logged_in' in session and session['user_type'] == 'admin':
        # Get counts for dashboard stats
        cur = mysql.connection.cursor()
        
        # Get user count
        cur.execute("SELECT COUNT(*) as total_users FROM users")
        total_users = cur.fetchone()['total_users']
        
        # Get recipe count
        cur.execute("SELECT COUNT(*) as total_recipes FROM recipes")
        total_recipes = cur.fetchone()['total_recipes']
        
        # Get new users today
        cur.execute("SELECT COUNT(*) as new_users FROM users WHERE DATE(created_at) = CURDATE()")
        new_users_today = cur.fetchone()['new_users']
        
        # Get comment count
        cur.execute("SELECT COUNT(*) as total_comments FROM recipe_comments")
        total_comments = cur.fetchone()['total_comments']
        
        # Get recipe uploads by month for the last 6 months
        cur.execute("""
            SELECT DATE_FORMAT(created_at, '%b %Y') as month, COUNT(*) as count
            FROM recipes
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
            GROUP BY DATE_FORMAT(created_at, '%b %Y'), MONTH(created_at), YEAR(created_at)
            ORDER BY YEAR(created_at), MONTH(created_at)
        """)
        recipe_uploads = cur.fetchall()
        
        # Get recipe counts by cuisine type for the pie chart
        cur.execute("""
            SELECT 
                CASE 
                    WHEN cuisine_type IS NULL THEN 'Other'
                    WHEN cuisine_type = '' THEN 'Other'
                    ELSE cuisine_type 
                END as cuisine,
                COUNT(*) as count
            FROM recipes
            GROUP BY cuisine
            ORDER BY count DESC
            LIMIT 5
        """)
        cuisine_data = cur.fetchall()
        
        # Get Latest Users - fetch the 5 most recent users
        cur.execute("""
            SELECT id, first_name, last_name, email, profile_pic, created_at 
            FROM users 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        latest_users = cur.fetchall()
        
        # Format created_at for each user to show relative time
        for user in latest_users:
            user['relative_time'] = get_relative_time(user['created_at'])
        
        # Get Recent Activities - combine recent comments, likes, and recipes
        cur.execute("""
            (SELECT 
                'recipe_created' as activity_type,
                r.id as entity_id,
                r.title as entity_name,
                u.id as user_id,
                CONCAT(u.first_name, ' ', u.last_name) as user_name,
                u.profile_pic,
                r.created_at as activity_time
            FROM recipes r
            JOIN users u ON r.user_id = u.id
            ORDER BY r.created_at DESC
            LIMIT 8)
            
            UNION ALL
            
            (SELECT 
                'recipe_comment' as activity_type,
                c.recipe_id as entity_id,
                r.title as entity_name,
                u.id as user_id,
                CONCAT(u.first_name, ' ', u.last_name) as user_name,
                u.profile_pic,
                c.created_at as activity_time
            FROM recipe_comments c
            JOIN users u ON c.user_id = u.id
            JOIN recipes r ON c.recipe_id = r.id
            ORDER BY c.created_at DESC
            LIMIT 8)
            
            UNION ALL
            
            (SELECT 
                'recipe_like' as activity_type,
                l.recipe_id as entity_id,
                r.title as entity_name,
                u.id as user_id,
                CONCAT(u.first_name, ' ', u.last_name) as user_name,
                u.profile_pic,
                l.created_at as activity_time
            FROM recipe_likes l
            JOIN users u ON l.user_id = u.id
            JOIN recipes r ON l.recipe_id = r.id
            ORDER BY l.created_at DESC
            LIMIT 8)
            
            ORDER BY activity_time DESC
            LIMIT 10
        """)
        recent_activities = cur.fetchall()
        
        # Format activity_time for each activity to show relative time
        for activity in recent_activities:
            activity['relative_time'] = get_relative_time(activity['activity_time'])
            
            # Create descriptive message based on activity_type
            if activity['activity_type'] == 'recipe_created':
                activity['message'] = f"created a new recipe: {activity['entity_name']}"
            elif activity['activity_type'] == 'recipe_comment':
                activity['message'] = f"commented on recipe: {activity['entity_name']}"
            elif activity['activity_type'] == 'recipe_like':
                activity['message'] = f"liked recipe: {activity['entity_name']}"
        
        cur.close()
        
        return render_template('admin/admin_dashboard.html', 
                              title='Admin Dashboard', 
                              total_users=total_users,
                              total_recipes=total_recipes,
                              new_users_today=new_users_today,
                              total_comments=total_comments,
                              latest_users=latest_users,
                              recent_activities=recent_activities,
                              recipe_uploads=recipe_uploads,
                              cuisine_data=cuisine_data,
                              now=datetime.now())
    return redirect(url_for('login'))

@app.route('/admin-manage-users')
def admin_manage_users():
    # Check if user is logged in as admin
    if 'logged_in' in session and session['user_type'] == 'admin':
        # Get all users with their activity counts
        cur = mysql.connection.cursor()
        
        cur.execute("""
            SELECT u.*, 
                   (SELECT COUNT(*) FROM recipes WHERE user_id = u.id) as recipes_count,
                   (SELECT COUNT(*) FROM recipe_comments WHERE user_id = u.id) as comments_count,
                   (SELECT COUNT(*) FROM recipe_likes WHERE user_id = u.id) as likes_count
            FROM users u
            ORDER BY u.id DESC
        """)
        
        users = cur.fetchall()
        cur.close()
        
        return render_template('admin/manage_users.html', 
                              title='Manage Users',
                              users=users)
    
    return redirect(url_for('login'))

@app.route('/admin-manage-recipes')
def admin_manage_recipes():
    # Check if user is logged in as admin
    if 'logged_in' in session and session['user_type'] == 'admin':
        # Get all recipes with author info
        cur = mysql.connection.cursor()
        
        cur.execute("""
            SELECT r.*, 
                   CONCAT(u.first_name, ' ', u.last_name) as author_name,
                   (SELECT COUNT(*) FROM recipe_likes WHERE recipe_id = r.id) as likes_count,
                   (SELECT COUNT(*) FROM recipe_comments WHERE recipe_id = r.id) as comments_count,
                   (r.id IN (SELECT recipe_id FROM featured_recipes)) as is_featured
            FROM recipes r
            JOIN users u ON r.user_id = u.id
            ORDER BY r.created_at DESC
        """)
        
        recipes = cur.fetchall()
        cur.close()
        
        return render_template('admin/manage_recipes.html', 
                              title='Manage Recipes',
                              recipes=recipes)
    
    return redirect(url_for('login'))

@app.route('/admin-categories')
def admin_categories():
    # Check if user is logged in as admin
    if 'logged_in' in session and session['user_type'] == 'admin':
        # Get recipes grouped by cuisine type
        cur = mysql.connection.cursor()
        
        # Get all distinct cuisine types
        cur.execute("SELECT DISTINCT cuisine_type FROM recipes WHERE cuisine_type IS NOT NULL ORDER BY cuisine_type")
        cuisine_types = [row['cuisine_type'] for row in cur.fetchall()]
        
        # Create a dictionary to store recipes for each cuisine type
        cuisine_recipes = {}
        
        # For each cuisine type, get all recipes
        for cuisine in cuisine_types:
            cur.execute("""
                SELECT r.*, 
                       CONCAT(u.first_name, ' ', u.last_name) as author_name,
                       (SELECT COUNT(*) FROM recipe_likes WHERE recipe_id = r.id) as likes_count,
                       (SELECT COUNT(*) FROM recipe_comments WHERE recipe_id = r.id) as comments_count,
                       (r.id IN (SELECT recipe_id FROM featured_recipes)) as is_featured
                FROM recipes r
                JOIN users u ON r.user_id = u.id
                WHERE r.cuisine_type = %s
                ORDER BY r.created_at DESC
            """, [cuisine])
            
            cuisine_recipes[cuisine] = cur.fetchall()
        
        cur.close()
        
        return render_template('admin/categories.html', 
                              title='Recipe Categories',
                              cuisine_types=cuisine_types,
                              cuisine_recipes=cuisine_recipes)
    
    return redirect(url_for('login'))

@app.route('/admin-analytics')
def admin_analytics():
    # Check if user is logged in as admin
    if 'logged_in' in session and session['user_type'] == 'admin':
        # Get analytics data
        cur = mysql.connection.cursor()
        
        # Get count of recipes by cuisine type
        cur.execute("""
            SELECT cuisine_type, COUNT(*) as count 
            FROM recipes 
            WHERE cuisine_type IS NOT NULL 
            GROUP BY cuisine_type 
            ORDER BY count DESC
        """)
        cuisine_data = cur.fetchall()
        
        # Get monthly recipe additions
        cur.execute("""
            SELECT DATE_FORMAT(created_at, '%Y-%m') as month, COUNT(*) as count
            FROM recipes
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
            GROUP BY DATE_FORMAT(created_at, '%Y-%m')
            ORDER BY month
        """)
        monthly_recipes = cur.fetchall()
        
        # Get top 5 most liked recipes
        cur.execute("""
            SELECT r.id, r.title, r.cuisine_type, COUNT(rl.id) as likes_count,
                   CONCAT(u.first_name, ' ', u.last_name) as author_name
            FROM recipes r
            JOIN recipe_likes rl ON r.id = rl.recipe_id
            JOIN users u ON r.user_id = u.id
            GROUP BY r.id
            ORDER BY likes_count DESC
            LIMIT 5
        """)
        top_liked_recipes = cur.fetchall()
        
        # Get top 5 most commented recipes
        cur.execute("""
            SELECT r.id, r.title, r.cuisine_type, COUNT(rc.id) as comments_count,
                   CONCAT(u.first_name, ' ', u.last_name) as author_name
            FROM recipes r
            JOIN recipe_comments rc ON r.id = rc.recipe_id
            JOIN users u ON r.user_id = u.id
            GROUP BY r.id
            ORDER BY comments_count DESC
            LIMIT 5
        """)
        top_commented_recipes = cur.fetchall()
        
        # Get user registration trend by month
        cur.execute("""
            SELECT DATE_FORMAT(created_at, '%Y-%m') as month, COUNT(*) as count
            FROM users
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
            GROUP BY DATE_FORMAT(created_at, '%Y-%m')
            ORDER BY month
        """)
        monthly_users = cur.fetchall()
        
        cur.close()
        
        return render_template('admin/analytics.html', 
                              title='Analytics',
                              cuisine_data=cuisine_data,
                              monthly_recipes=monthly_recipes,
                              top_liked_recipes=top_liked_recipes,
                              top_commented_recipes=top_commented_recipes,
                              monthly_users=monthly_users)
    
    return redirect(url_for('login'))

@app.route('/admin-settings', methods=['GET', 'POST'])
def admin_settings():
    # Check if user is logged in as admin
    if 'logged_in' in session and session['user_type'] == 'admin':
        # Create cursor
        cur = mysql.connection.cursor()
        
        # Initialize success message
        success_message = None
        
        # Handle form submission
        if request.method == 'POST':
            # Get form data
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            # Validate the data
            if current_password and new_password and confirm_password:
                # Hash the current password
                hash_current_password = hashlib.sha256(current_password.encode()).hexdigest()
                
                # Check if current password is correct
                cur.execute("SELECT * FROM admins WHERE id = %s AND password = %s", 
                          [session['user_id'], hash_current_password])
                admin = cur.fetchone()
                
                if admin:
                    # Check if new password and confirmation match
                    if new_password == confirm_password:
                        # Hash the new password
                        hash_new_password = hashlib.sha256(new_password.encode()).hexdigest()
                        
                        # Update the password
                        cur.execute("UPDATE admins SET password = %s WHERE id = %s", 
                                  [hash_new_password, session['user_id']])
                        mysql.connection.commit()
                        
                        success_message = "Password updated successfully!"
                    else:
                        flash("New password and confirmation do not match", "danger")
                else:
                    flash("Current password is incorrect", "danger")
            else:
                flash("All fields are required", "danger")
        
        # Get admin account details
        cur.execute("SELECT * FROM admins WHERE id = %s", [session['user_id']])
        admin_data = cur.fetchone()
        
        # Get system statistics for settings page
        cur.execute("SELECT COUNT(*) as total_users FROM users")
        total_users = cur.fetchone()['total_users']
        
        cur.execute("SELECT COUNT(*) as total_recipes FROM recipes")
        total_recipes = cur.fetchone()['total_recipes']
        
        cur.execute("SELECT COUNT(*) as total_likes FROM recipe_likes")
        total_likes = cur.fetchone()['total_likes']
        
        cur.execute("SELECT COUNT(*) as total_comments FROM recipe_comments")
        total_comments = cur.fetchone()['total_comments']
        
        # Close the cursor
        cur.close()
        
        return render_template('admin/settings.html', 
                              title='Admin Settings',
                              admin=admin_data,
                              total_users=total_users,
                              total_recipes=total_recipes,
                              total_likes=total_likes,
                              total_comments=total_comments,
                              success_message=success_message)
    
    return redirect(url_for('login'))

@app.route('/admin/recipe/<int:recipe_id>/details')
def admin_recipe_details(recipe_id):
    # Check if user is logged in as admin
    if 'logged_in' not in session or session['user_type'] != 'admin':
        return jsonify({"success": False, "error": "Unauthorized access"}), 403
    
    try:
        cur = mysql.connection.cursor()
        
        # Get recipe with author details
        cur.execute("""
            SELECT r.*, 
                   CONCAT(u.first_name, ' ', u.last_name) as author_name,
                   (SELECT COUNT(*) FROM recipe_likes WHERE recipe_id = r.id) as likes_count,
                   (SELECT COUNT(*) FROM recipe_comments WHERE recipe_id = r.id) as comments_count
            FROM recipes r
            JOIN users u ON r.user_id = u.id
            WHERE r.id = %s
        """, [recipe_id])
        
        recipe = cur.fetchone()
        
        if not recipe:
            cur.close()
            return jsonify({"success": False, "error": "Recipe not found"}), 404
        
        # Format dates for JSON
        recipe['created_at'] = recipe['created_at'].strftime('%b %d, %Y, %I:%M %p')
        recipe['updated_at'] = recipe['updated_at'].strftime('%b %d, %Y, %I:%M %p')
        
        cur.close()
        
        return jsonify({
            "success": True,
            "recipe": recipe
        })
        
    except Exception as e:
        print(f"Error getting recipe details: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/admin/recipe/<int:recipe_id>/delete', methods=['POST'])
def admin_delete_recipe(recipe_id):
    # Check if user is logged in as admin
    if 'logged_in' not in session or session['user_type'] != 'admin':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('login'))
    
    try:
        cur = mysql.connection.cursor()
        
        # Check if recipe exists
        cur.execute("SELECT * FROM recipes WHERE id = %s", [recipe_id])
        recipe = cur.fetchone()
        
        if not recipe:
            flash('Recipe not found', 'danger')
            return redirect(url_for('admin_manage_recipes'))
        
        # Delete recipe likes
        cur.execute("DELETE FROM recipe_likes WHERE recipe_id = %s", [recipe_id])
        
        # Delete recipe comments
        cur.execute("DELETE FROM recipe_comments WHERE recipe_id = %s", [recipe_id])
        
        # Delete from featured recipes if present
        cur.execute("DELETE FROM featured_recipes WHERE recipe_id = %s", [recipe_id])
        
        # Delete from saved recipes
        cur.execute("DELETE FROM saved_recipes WHERE recipe_id = %s", [recipe_id])
        
        # Delete the recipe
        cur.execute("DELETE FROM recipes WHERE id = %s", [recipe_id])
        
        mysql.connection.commit()
        cur.close()
        
        flash('Recipe deleted successfully', 'success')
        
    except Exception as e:
        flash(f'Error deleting recipe: {str(e)}', 'danger')
        print(f"Database error: {str(e)}")
    
    return redirect(url_for('admin_manage_recipes'))

@app.route('/admin/recipe/<int:recipe_id>/feature', methods=['POST'])
def admin_feature_recipe(recipe_id):
    # Check if user is logged in as admin
    if 'logged_in' not in session or session['user_type'] != 'admin':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('login'))
    
    feature = request.form.get('feature', 'true') == 'true'
    
    try:
        cur = mysql.connection.cursor()
        
        # Check if recipe exists
        cur.execute("SELECT * FROM recipes WHERE id = %s", [recipe_id])
        recipe = cur.fetchone()
        
        if not recipe:
            flash('Recipe not found', 'danger')
            return redirect(url_for('admin_manage_recipes'))
        
        # Check if already featured
        cur.execute("SELECT * FROM featured_recipes WHERE recipe_id = %s", [recipe_id])
        is_featured = cur.fetchone() is not None
        
        if feature and not is_featured:
            # Add to featured recipes
            cur.execute("INSERT INTO featured_recipes (recipe_id) VALUES (%s)", [recipe_id])
            flash('Recipe added to featured', 'success')
        elif not feature and is_featured:
            # Remove from featured recipes
            cur.execute("DELETE FROM featured_recipes WHERE recipe_id = %s", [recipe_id])
            flash('Recipe removed from featured', 'success')
        
        mysql.connection.commit()
        cur.close()
        
    except Exception as e:
        flash(f'Error updating featured status: {str(e)}', 'danger')
        print(f"Database error: {str(e)}")
    
    return redirect(url_for('admin_manage_recipes'))

@app.route('/admin/search-recipes')
def admin_search_recipes():
    # Check if user is logged in as admin
    if 'logged_in' not in session or session['user_type'] != 'admin':
        return jsonify({"success": False, "error": "Unauthorized access"}), 403
    
    search_term = request.args.get('q', '')
    
    if len(search_term) < 2:
        return jsonify([])
    
    try:
        cur = mysql.connection.cursor()
        
        # Search recipes by title or description
        search_pattern = f"%{search_term}%"
        cur.execute("""
            SELECT r.*, 
                   CONCAT(u.first_name, ' ', u.last_name) as author_name,
                   (SELECT COUNT(*) FROM recipe_likes WHERE recipe_id = r.id) as likes_count,
                   (SELECT COUNT(*) FROM recipe_comments WHERE recipe_id = r.id) as comments_count,
                   (r.id IN (SELECT recipe_id FROM featured_recipes)) as is_featured
            FROM recipes r
            JOIN users u ON r.user_id = u.id
            WHERE r.title LIKE %s OR r.description LIKE %s OR r.ingredients LIKE %s
            ORDER BY r.created_at DESC
            LIMIT 50
        """, [search_pattern, search_pattern, search_pattern])
        
        recipes = cur.fetchall()
        
        # Format dates for JSON
        for recipe in recipes:
            recipe['created_at'] = recipe['created_at'].strftime('%b %d, %Y')
            recipe['updated_at'] = recipe['updated_at'].strftime('%b %d, %Y')
        
        cur.close()
        
        return jsonify(recipes)
        
    except Exception as e:
        print(f"Error searching recipes: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
def admin_delete_user(user_id):
    # Check if user is logged in as admin
    if 'logged_in' in session and session['user_type'] == 'admin':
        try:
            # Create cursor
            cur = mysql.connection.cursor()
            
            # First, delete all recipes created by the user
            # This will handle cascading deletes for recipe comments, likes, etc.
            cur.execute("DELETE FROM recipes WHERE user_id = %s", [user_id])
            
            # Delete from other related tables that might have user_id as foreign key
            # These are tables that might not have ON DELETE CASCADE set
            try:
                cur.execute("DELETE FROM recipe_likes WHERE user_id = %s", [user_id])
                cur.execute("DELETE FROM recipe_comments WHERE user_id = %s", [user_id])
                cur.execute("DELETE FROM recipe_saves WHERE user_id = %s", [user_id])
                cur.execute("DELETE FROM follows WHERE follower_id = %s OR followed_id = %s", [user_id, user_id])
            except Exception as e:
                print(f"Warning while cleaning up user data: {str(e)}")
                # Continue even if some tables don't exist or have errors
                pass
            
            # Now delete the user
            cur.execute("DELETE FROM users WHERE id = %s", [user_id])
            
            # Commit to DB
            mysql.connection.commit()
            
            # Close connection
            cur.close()
            
            flash('User has been deleted successfully', 'success')
        except Exception as e:
            flash(f'Error deleting user: {str(e)}', 'danger')
            
        return redirect(url_for('admin_manage_users'))
    
    return redirect(url_for('login'))

@app.route('/admin/suspend-user/<int:user_id>', methods=['POST'])
def admin_suspend_user(user_id):
    # Check if user is logged in as admin
    if 'logged_in' in session and session['user_type'] == 'admin':
        try:
            # Get current status
            cur = mysql.connection.cursor()
            
            # First, ensure the is_suspended column exists
            try:
                cur.execute("SELECT is_suspended FROM users LIMIT 1")
            except Exception:
                # Column doesn't exist, create it
                cur.execute("ALTER TABLE users ADD COLUMN is_suspended TINYINT(1) DEFAULT 0")
                mysql.connection.commit()
            
            cur.execute("SELECT is_suspended FROM users WHERE id = %s", [user_id])
            user = cur.fetchone()
            
            if not user:
                flash('User not found', 'danger')
                return redirect(url_for('admin_manage_users'))
            
            # Toggle suspension status
            new_status = 0 if user['is_suspended'] else 1
            status_text = "suspended" if new_status else "unsuspended"
            
            # Update user status
            cur.execute("UPDATE users SET is_suspended = %s WHERE id = %s", [new_status, user_id])
            
            # Commit to DB
            mysql.connection.commit()
            
            # Close connection
            cur.close()
            
            flash(f'User has been {status_text} successfully', 'success')
        except Exception as e:
            flash(f'Error updating user status: {str(e)}', 'danger')
            
        return redirect(url_for('admin_manage_users'))
    
    return redirect(url_for('login'))

@app.route('/admin/search-users', methods=['GET'])
def admin_search_users():
    # Check if user is logged in as admin
    if 'logged_in' in session and session['user_type'] == 'admin':
        search_term = request.args.get('q', '')
        exact_search = request.args.get('exact', 'false').lower() == 'true'
        
        if not search_term:
            return jsonify([])
        
        # Create cursor
        cur = mysql.connection.cursor()
        
        # Ensure is_suspended column exists
        try:
            cur.execute("SELECT is_suspended FROM users LIMIT 1")
        except Exception:
            # Column doesn't exist, create it
            cur.execute("ALTER TABLE users ADD COLUMN is_suspended TINYINT(1) DEFAULT 0")
            mysql.connection.commit()
        
        # Handle different search modes
        if exact_search:
            # Try to parse user ID for exact match
            try:
                user_id = int(search_term)
                
                # Search exact user ID
                search_query = """
                    SELECT 
                        u.*,
                        (SELECT COUNT(*) FROM recipes WHERE user_id = u.id) as recipes_count,
                        (SELECT COUNT(*) FROM recipe_comments WHERE user_id = u.id) as comments_count,
                        (SELECT COUNT(*) FROM recipe_likes WHERE user_id = u.id) as likes_count
                    FROM users u
                    WHERE u.id = %s
                """
                
                cur.execute(search_query, [user_id])
            except ValueError:
                # If not a valid number, return empty
                cur.close()
                return jsonify([])
        else:
            # Regular search with LIKE
            search_query = """
                SELECT 
                    u.*,
                    (SELECT COUNT(*) FROM recipes WHERE user_id = u.id) as recipes_count,
                    (SELECT COUNT(*) FROM recipe_comments WHERE user_id = u.id) as comments_count,
                    (SELECT COUNT(*) FROM recipe_likes WHERE user_id = u.id) as likes_count
                FROM users u
                WHERE u.first_name LIKE %s 
                    OR u.last_name LIKE %s 
                    OR u.email LIKE %s 
                    OR u.display_name LIKE %s
                ORDER BY u.created_at DESC
                LIMIT 20
            """
            
            # Add wildcards to search term
            search_pattern = f"%{search_term}%"
            
            cur.execute(search_query, [search_pattern, search_pattern, search_pattern, search_pattern])
        
        # Fetch users
        users = []
        for user in cur.fetchall():
            users.append({
                'id': user['id'],
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'email': user['email'],
                'phone': user['phone'],
                'display_name': user['display_name'],
                'profile_pic': user['profile_pic'],
                'created_at': user['created_at'].strftime('%b %d, %Y'),
                'recipes_count': user['recipes_count'],
                'comments_count': user['comments_count'],
                'likes_count': user['likes_count'],
                'is_suspended': user.get('is_suspended', 0)
            })
        
        cur.close()
        
        return jsonify(users)
    
    return jsonify({'error': 'Unauthorized'}), 401

@app.route('/user-dashboard')
def user_dashboard():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
        
    try:
        cur = mysql.connection.cursor()
        
        # Ensure the recipe_likes table exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS recipe_likes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                recipe_id INT NOT NULL,
                user_id INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_like (recipe_id, user_id),
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # First, update all recipes' comments_count to ensure accuracy
        cur.execute("""
            UPDATE recipes r 
            SET comments_count = (
                SELECT COUNT(*) 
                FROM recipe_comments 
                WHERE recipe_id = r.id
            )
        """)
        
        # Update all recipes' likes_count to ensure accuracy
        cur.execute("""
            UPDATE recipes r 
            SET likes_count = (
                SELECT COUNT(*) 
                FROM recipe_likes 
                WHERE recipe_id = r.id
            )
        """)
        
        mysql.connection.commit()
        
        # Get all recipes with user info and interaction flags
        cur.execute("""
            SELECT 
                r.*,
                u.first_name,
                u.last_name,
                u.profile_pic,
                EXISTS(SELECT 1 FROM recipe_likes WHERE recipe_id = r.id AND user_id = %s) as user_has_liked,
                EXISTS(SELECT 1 FROM saved_recipes WHERE recipe_id = r.id AND user_id = %s) as user_has_saved,
                r.comments_count,
                r.likes_count
            FROM recipes r
            JOIN users u ON r.user_id = u.id
            ORDER BY r.created_at DESC
        """, [session['user_id'], session['user_id']])
        
        recipes = []
        for row in cur.fetchall():
            recipe = dict(row)
            recipe['user_name'] = f"{recipe['first_name']} {recipe['last_name']}"
            recipes.append(recipe)
            
        # Get trending recipes (most likes in last 7 days)
        cur.execute("""
            SELECT 
                r.*,
                u.first_name,
                u.last_name,
                u.profile_pic,
                COUNT(DISTINCT rl.id) as recent_likes_count,
                r.comments_count,
                r.likes_count
            FROM recipes r
            JOIN users u ON r.user_id = u.id
            LEFT JOIN recipe_likes rl ON r.id = rl.recipe_id 
                AND rl.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            GROUP BY r.id, u.first_name, u.last_name, u.profile_pic
            ORDER BY recent_likes_count DESC
            LIMIT 5
        """)
        
        trending_recipes = []
        for row in cur.fetchall():
            recipe = dict(row)
            recipe['user_name'] = f"{recipe['first_name']} {recipe['last_name']}"
            trending_recipes.append(recipe)
            
        cur.close()
        
        return render_template('user/user_dashboard.html', 
                             recipes=recipes,
                             trending_recipes=trending_recipes)
                             
    except Exception as e:
        print(f"Error loading dashboard: {str(e)}")
        return render_template('error.html', 
                             error_message="Sorry, we encountered an error loading the dashboard. Please try again later.",
                             error_details=str(e)), 500

@app.route('/user-profile')
def user_profile():
    # Check if user is logged in as user
    if 'logged_in' in session and session['user_type'] == 'user':
        try:
            cur = mysql.connection.cursor()
            
            # Get user stats
            cur.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM recipes WHERE user_id = %s) as recipe_count,
                    (SELECT COUNT(*) FROM follows WHERE followed_id = %s) as followers_count,
                    (SELECT COUNT(*) FROM follows WHERE follower_id = %s) as following_count
                FROM dual
            """, [session['user_id'], session['user_id'], session['user_id']])
            
            stats = cur.fetchone()
            
            # Get user's recipes
            cur.execute("""
                SELECT r.*, 
                       (SELECT COUNT(*) FROM recipe_likes WHERE recipe_id = r.id) as likes_count,
                       (SELECT COUNT(*) FROM recipe_comments WHERE recipe_id = r.id) as comments_count
                FROM recipes r
                WHERE r.user_id = %s
                ORDER BY r.created_at DESC
                LIMIT 6
            """, [session['user_id']])
            
            user_recipes = cur.fetchall()
            
            # Get user's recent activity (likes, comments, recipe creations)
            cur.execute("""
                (SELECT 
                    'recipe_created' as activity_type,
                    r.id as entity_id,
                    r.title as entity_name,
                    NULL as related_user_id,
                    NULL as related_user_name,
                    NULL as related_user_pic,
                    r.created_at as activity_time
                FROM recipes r
                WHERE r.user_id = %s
                ORDER BY r.created_at DESC
                LIMIT 5)
                
                UNION ALL
                
                (SELECT 
                    'recipe_comment' as activity_type,
                    c.recipe_id as entity_id,
                    r.title as entity_name,
                    r.user_id as related_user_id,
                    CONCAT(u.first_name, ' ', u.last_name) as related_user_name,
                    u.profile_pic as related_user_pic,
                    c.created_at as activity_time
                FROM recipe_comments c
                JOIN recipes r ON c.recipe_id = r.id
                JOIN users u ON r.user_id = u.id
                WHERE c.user_id = %s
                ORDER BY c.created_at DESC
                LIMIT 5)
                
                UNION ALL
                
                (SELECT 
                    'recipe_like' as activity_type,
                    l.recipe_id as entity_id,
                    r.title as entity_name,
                    r.user_id as related_user_id,
                    CONCAT(u.first_name, ' ', u.last_name) as related_user_name,
                    u.profile_pic as related_user_pic,
                    l.created_at as activity_time
                FROM recipe_likes l
                JOIN recipes r ON l.recipe_id = r.id
                JOIN users u ON r.user_id = u.id
                WHERE l.user_id = %s
                ORDER BY l.created_at DESC
                LIMIT 5)
                
                UNION ALL
                
                (SELECT 
                    'follow_user' as activity_type,
                    f.followed_id as entity_id,
                    NULL as entity_name,
                    f.followed_id as related_user_id,
                    CONCAT(u.first_name, ' ', u.last_name) as related_user_name,
                    u.profile_pic as related_user_pic,
                    f.created_at as activity_time
                FROM follows f
                JOIN users u ON f.followed_id = u.id
                WHERE f.follower_id = %s
                ORDER BY f.created_at DESC
                LIMIT 5)
                
                ORDER BY activity_time DESC
                LIMIT 10
            """, [session['user_id'], session['user_id'], session['user_id'], session['user_id']])
            
            activities = cur.fetchall()
            
            # Process activities with human-readable time
            for activity in activities:
                activity['relative_time'] = get_relative_time(activity['activity_time'])
            
            # Close cursor
            cur.close()
            
            return render_template('user/dashboard_profile.html', 
                                  title='User Profile',
                                  stats=stats,
                                  user_recipes=user_recipes,
                                  activities=activities,
                                  now=datetime.now())
                                  
        except Exception as e:
            print(f"Error fetching profile data: {str(e)}")
            flash('Error loading profile data', 'danger')
            return render_template('user/dashboard_profile.html', 
                                  title='User Profile',
                                  now=datetime.now())
    
    return redirect(url_for('login'))

@app.route('/user-settings')
def user_settings():
    # Check if user is logged in as user
    if 'logged_in' in session and session['user_type'] == 'user':
        return render_template('user/dashboard_settings.html', title='User Settings', now=datetime.now())
    return redirect(url_for('login'))

@app.route('/discover')
def discover():
    # Check if user is logged in as user
    if 'logged_in' in session and session['user_type'] == 'user':
        # Get selected cuisine type filter
        selected_cuisine = request.args.get('cuisine_type', 'all')
        
        # Fetch all available cuisine types
        cur = mysql.connection.cursor()
        cur.execute("SELECT DISTINCT cuisine_type FROM recipes WHERE cuisine_type IS NOT NULL ORDER BY cuisine_type")
        cuisine_types = [row['cuisine_type'] for row in cur.fetchall()]
        
        # Fetch recipes based on cuisine type filter
        if selected_cuisine and selected_cuisine != 'all':
            cur.execute("""
                SELECT r.*, CONCAT(u.first_name, ' ', u.last_name) as author_name, u.profile_pic,
                (SELECT COUNT(*) FROM recipe_likes WHERE recipe_id = r.id) as likes_count,
                (SELECT COUNT(*) FROM recipe_comments WHERE recipe_id = r.id) as comments_count,
                (SELECT COUNT(*) FROM saved_recipes WHERE recipe_id = r.id AND user_id = %s) > 0 as is_saved
                FROM recipes r
                JOIN users u ON r.user_id = u.id
                WHERE r.privacy = 'public' AND r.cuisine_type = %s
                ORDER BY r.created_at DESC
                LIMIT 20
            """, [session['user_id'], selected_cuisine])
        else:
            cur.execute("""
                SELECT r.*, CONCAT(u.first_name, ' ', u.last_name) as author_name, u.profile_pic,
                (SELECT COUNT(*) FROM recipe_likes WHERE recipe_id = r.id) as likes_count,
                (SELECT COUNT(*) FROM recipe_comments WHERE recipe_id = r.id) as comments_count,
                (SELECT COUNT(*) FROM saved_recipes WHERE recipe_id = r.id AND user_id = %s) > 0 as is_saved
                FROM recipes r
                JOIN users u ON r.user_id = u.id
                WHERE r.privacy = 'public'
                ORDER BY r.created_at DESC
                LIMIT 20
            """, [session['user_id']])
        
        recipes = cur.fetchall()
        
        # Fetch popular cooks (users with most recipes)
        cur.execute("""
            SELECT u.id, u.first_name, u.last_name, u.profile_pic, u.bio,
            (SELECT COUNT(*) FROM recipes WHERE user_id = u.id) as recipe_count,
            (SELECT COUNT(*) FROM follows WHERE followed_id = u.id) as followers_count,
            (SELECT COUNT(*) FROM follows WHERE follower_id = %s AND followed_id = u.id) > 0 as is_following
            FROM users u
            WHERE u.id != %s
            ORDER BY recipe_count DESC, followers_count DESC
            LIMIT 4
        """, [session['user_id'], session['user_id']])
        
        popular_cooks = cur.fetchall()
        
        # Fetch trending recipes (most liked recently)
        cur.execute("""
            SELECT r.*, CONCAT(u.first_name, ' ', u.last_name) as author_name, u.profile_pic,
            (SELECT COUNT(*) FROM recipe_likes WHERE recipe_id = r.id) as likes_count,
            (SELECT COUNT(*) FROM recipe_comments WHERE recipe_id = r.id) as comments_count,
            (SELECT COUNT(*) FROM saved_recipes WHERE recipe_id = r.id AND user_id = %s) > 0 as is_saved
            FROM recipes r
            JOIN users u ON r.user_id = u.id
            WHERE r.privacy = 'public'
            ORDER BY r.likes_count DESC, r.comments_count DESC
            LIMIT 4
        """, [session['user_id']])
        
        trending_recipes = cur.fetchall()
        
        cur.close()
        
        return render_template('user/discover.html', 
                              title='Discover Recipes', 
                              now=datetime.now(),
                              recipes=recipes,
                              trending_recipes=trending_recipes,
                              popular_cooks=popular_cooks,
                              cuisine_types=cuisine_types,
                              selected_cuisine=selected_cuisine)
    return redirect(url_for('login'))

@app.route('/saved-recipes')
@app.route('/saved-recipes/<collection>')
def saved_recipes(collection=None):
    # Check if user is logged in as user
    if 'logged_in' in session and session['user_type'] == 'user':
        try:
            cur = mysql.connection.cursor()
            
            # Check if saved_recipes table exists, create if it doesn't
            cur.execute("SHOW TABLES LIKE 'saved_recipes'")
            if not cur.fetchone():
                # Create saved_recipes table if it doesn't exist
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS saved_recipes (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id INT NOT NULL,
                        recipe_id INT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE KEY unique_save (user_id, recipe_id),
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                        FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
                    )
                """)
                mysql.connection.commit()
            
            # Determine collection filter
            collection_filter = ""
            collection_name = "All Saved"
            params = [session['user_id']]
            
            # Map collection parameter to cuisine types
            if collection:
                if collection == 'international':
                    collection_filter = "AND r.cuisine_type = 'International'"
                    collection_name = "International"
                elif collection == 'luzon':
                    collection_filter = "AND r.cuisine_type = 'Luzon'"
                    collection_name = "Luzon"
                elif collection == 'visayas':
                    collection_filter = "AND r.cuisine_type = 'Visayas'"
                    collection_name = "Visayas"
                elif collection == 'mindanao':
                    collection_filter = "AND r.cuisine_type = 'Mindanao'"
                    collection_name = "Mindanao"
            
            # Get all saved recipes for the current user with recipe and author details
            query = f"""
                SELECT 
                    r.*, 
                    sr.created_at as saved_at,
                    u.first_name, 
                    u.last_name, 
                    u.profile_pic,
                    (SELECT COUNT(*) FROM recipe_likes WHERE recipe_id = r.id) as likes_count
                FROM saved_recipes sr
                JOIN recipes r ON sr.recipe_id = r.id
                JOIN users u ON r.user_id = u.id
                WHERE sr.user_id = %s
                {collection_filter}
                ORDER BY sr.created_at DESC
            """
            
            cur.execute(query, params)
            
            saved_recipes = []
            for row in cur.fetchall():
                saved_recipes.append({
                    'id': row['id'],
                    'title': row['title'],
                    'description': row['description'],
                    'photo_path': row['photo_path'],
                    'prep_time': row['prep_time'],
                    'cook_time': row['cook_time'],
                    'servings': row['servings'],
                    'calories': row['calories'],
                    'cuisine_type': row['cuisine_type'],
                    'author_name': f"{row['first_name']} {row['last_name']}",
                    'author_pic': row['profile_pic'],
                    'likes_count': row['likes_count'],
                    'saved_at': row['saved_at']
                })
            
            # Get recently viewed recipes (for now just get some random recipes as placeholder)
            cur.execute("""
                SELECT 
                    r.*, 
                    u.first_name, 
                    u.last_name, 
                    u.profile_pic,
                    (SELECT COUNT(*) FROM recipe_likes WHERE recipe_id = r.id) as likes_count,
                    EXISTS(SELECT 1 FROM saved_recipes WHERE recipe_id = r.id AND user_id = %s) as is_saved
                FROM recipes r
                JOIN users u ON r.user_id = u.id
                WHERE r.id NOT IN (SELECT recipe_id FROM saved_recipes WHERE user_id = %s)
                ORDER BY r.created_at DESC
                LIMIT 4
            """, [session['user_id'], session['user_id']])
            
            recent_recipes = []
            for row in cur.fetchall():
                recent_recipes.append({
                    'id': row['id'],
                    'title': row['title'],
                    'description': row['description'],
                    'photo_path': row['photo_path'],
                    'prep_time': row['prep_time'],
                    'cook_time': row['cook_time'],
                    'servings': row['servings'],
                    'calories': row['calories'],
                    'cuisine_type': row['cuisine_type'],
                    'author_name': f"{row['first_name']} {row['last_name']}",
                    'author_pic': row['profile_pic'],
                    'likes_count': row['likes_count'],
                    'is_saved': row['is_saved']
                })
            
            # Get counts for each cuisine type
            cur.execute("""
                SELECT 
                    COALESCE(r.cuisine_type, 'Other') as cuisine_type,
                    COUNT(*) as count
                FROM saved_recipes sr
                JOIN recipes r ON sr.recipe_id = r.id
                WHERE sr.user_id = %s
                GROUP BY r.cuisine_type
            """, [session['user_id']])
            
            cuisine_counts = {
                'all': 0,
                'international': 0,
                'luzon': 0,
                'visayas': 0,
                'mindanao': 0
            }
            
            for row in cur.fetchall():
                cuisine_type = row['cuisine_type'].lower() if row['cuisine_type'] else 'other'
                count = row['count']
                cuisine_counts['all'] += count
                
                if cuisine_type == 'international':
                    cuisine_counts['international'] = count
                elif cuisine_type == 'luzon':
                    cuisine_counts['luzon'] = count
                elif cuisine_type == 'visayas':
                    cuisine_counts['visayas'] = count
                elif cuisine_type == 'mindanao':
                    cuisine_counts['mindanao'] = count
            
            cur.close()
            
            return render_template('user/saved_recipes.html', 
                                title='Saved Recipes', 
                                saved_recipes=saved_recipes,
                                recent_recipes=recent_recipes,
                                collection_counts=cuisine_counts,
                                selected_collection=collection or 'all',
                                collection_name=collection_name,
                                now=datetime.now())
        except Exception as e:
            flash(f"Error loading saved recipes: {str(e)}", 'danger')
            return redirect(url_for('user_dashboard'))
            
    return redirect(url_for('login'))

@app.route('/following')
def following():
    # Check if user is logged in as user
    if 'logged_in' in session and session['user_type'] == 'user':
        try:
            cur = mysql.connection.cursor()
            
            # Check if the follows table exists, create if it doesn't
            cur.execute("SHOW TABLES LIKE 'follows'")
            if not cur.fetchone():
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS follows (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        follower_id INT NOT NULL,
                        followed_id INT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE KEY unique_follow (follower_id, followed_id),
                        FOREIGN KEY (follower_id) REFERENCES users(id) ON DELETE CASCADE,
                        FOREIGN KEY (followed_id) REFERENCES users(id) ON DELETE CASCADE
                    )
                """)
                mysql.connection.commit()
            
            # Fetch users being followed by the current user
            cur.execute("""
                SELECT 
                    u.id, 
                    u.first_name, 
                    u.last_name, 
                    u.profile_pic, 
                    u.bio,
                    f.created_at as followed_at,
                    (SELECT COUNT(*) FROM recipes WHERE user_id = u.id) as recipe_count,
                    (SELECT COUNT(*) FROM follows WHERE followed_id = u.id) as followers_count
                FROM follows f
                JOIN users u ON f.followed_id = u.id
                WHERE f.follower_id = %s
                ORDER BY f.created_at DESC
            """, [session['user_id']])
            
            followed_users = cur.fetchall()
            
            # Fetch suggested users (users not followed yet, with most followers/recipes)
            cur.execute("""
                SELECT 
                    u.id, 
                    u.first_name, 
                    u.last_name, 
                    u.profile_pic, 
                    u.bio,
                    (SELECT COUNT(*) FROM recipes WHERE user_id = u.id) as recipe_count,
                    (SELECT COUNT(*) FROM follows WHERE followed_id = u.id) as followers_count
                FROM users u
                WHERE u.id != %s
                AND u.id NOT IN (SELECT followed_id FROM follows WHERE follower_id = %s)
                ORDER BY followers_count DESC, recipe_count DESC
                LIMIT 6
            """, [session['user_id'], session['user_id']])
            
            suggested_users = cur.fetchall()
            
            cur.close()
            
            return render_template('user/following.html', 
                                title='Following', 
                                followed_users=followed_users,
                                suggested_users=suggested_users,
                                now=datetime.now())
        except Exception as e:
            flash(f"Error loading following page: {str(e)}", 'danger')
            return redirect(url_for('user_dashboard'))
            
    return redirect(url_for('login'))

@app.route('/update-profile', methods=['POST'])
def update_profile():
    # Check if user is logged in as user
    if 'logged_in' not in session or session['user_type'] != 'user':
        flash('You must be logged in to update your profile', 'danger')
        return redirect(url_for('login'))
    
    # Get form data
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    phone = request.form['phone']
    location = request.form['location']
    birthday = request.form.get('birthday', None)
    bio = request.form.get('bio', None)
    
    # Create cursor
    cur = mysql.connection.cursor()
    
    try:
        # Update the user's information
        update_query = """
        UPDATE users SET 
            first_name = %s, 
            last_name = %s, 
            phone = %s, 
            location = %s, 
            birthday = %s, 
            bio = %s 
        WHERE id = %s
        """
        
        cur.execute(update_query, [
            first_name, 
            last_name, 
            phone, 
            location, 
            birthday if birthday else None, 
            bio, 
            session['user_id']
        ])
        
        # Commit the changes
        mysql.connection.commit()
        
        # Close cursor
        cur.close()
        
        flash('Profile updated successfully', 'success')
        return redirect(url_for('user_profile'))
    
    except Exception as e:
        # If there's an error, roll back and show error message
        mysql.connection.rollback()
        cur.close()
        flash(f'Error updating profile: {str(e)}', 'danger')
        return redirect(url_for('user_profile'))

@app.route('/update-profile-picture', methods=['POST'])
def update_profile_picture():
    # Check if user is logged in as user
    if 'logged_in' not in session or session['user_type'] != 'user':
        flash('You must be logged in to update your profile picture', 'danger')
        return redirect(url_for('login'))
    
    # Check if a file was uploaded
    if 'profile_pic' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('user_profile'))
    
    profile_pic = request.files['profile_pic']
    
    # If user does not select a file, browser also
    # submit an empty part without filename
    if profile_pic.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('user_profile'))
    
    # Check if the file is allowed
    if profile_pic and allowed_file(profile_pic.filename):
        try:
            # Secure the filename
            filename = secure_filename(profile_pic.filename)
            # Create a unique filename with timestamp
            timestamp = int(datetime.now().timestamp())
            unique_filename = f"user_{session['user_id']}_{timestamp}_{filename}"
            profile_pic_path = f"uploads/profile_photos/{unique_filename}"
            
            # Save the file
            full_path = os.path.join(app.static_folder, 'uploads/profile_photos', unique_filename)
            profile_pic.save(full_path)
            
            # Update user's profile_pic in database
            cur = mysql.connection.cursor()
            cur.execute("UPDATE users SET profile_pic = %s WHERE id = %s", [profile_pic_path, session['user_id']])
            mysql.connection.commit()
            cur.close()
            
            flash('Profile picture updated successfully', 'success')
        except Exception as e:
            flash(f'Error updating profile picture: {str(e)}', 'danger')
    else:
        flash('Invalid file type. Allowed types are: png, jpg, jpeg, gif', 'danger')
    
    return redirect(url_for('user_profile'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('login'))

@app.route('/create-recipe', methods=['POST'])
def create_recipe():
    # Check if user is logged in
    if 'logged_in' not in session or 'user_id' not in session:
        flash('Please log in to create a recipe', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            # Get form data
            title = request.form.get('title')
            description = request.form.get('description', '')
            prep_time = request.form.get('prep_time')
            cook_time = request.form.get('cook_time')
            servings = request.form.get('servings')
            ingredients = request.form.get('ingredients')
            instructions = request.form.get('instructions')
            calories = request.form.get('calories')
            privacy = request.form.get('privacy', 'public')
            cuisine_type = request.form.get('cuisine_type', 'Other')
            
            # Handle photo upload
            photo_path = None
            if 'photo' in request.files and request.files['photo'].filename != '':
                photo = request.files['photo']
                if photo and allowed_file(photo.filename):
                    # Create recipe photos directory if it doesn't exist
                    recipe_upload_folder = 'static/uploads/recipe_photos'
                    os.makedirs(recipe_upload_folder, exist_ok=True)
                    
                    # Generate unique filename
                    unique_filename = f"{uuid.uuid4().hex}_{secure_filename(photo.filename)}"
                    
                    # Use absolute path for saving the file
                    full_photo_path = os.path.join(app.static_folder, 'uploads/recipe_photos', unique_filename)
                    
                    # Save the file
                    photo.save(full_photo_path)
                    
                    # Store the relative path in the database
                    photo_path = f"uploads/recipe_photos/{unique_filename}"
            
            # Convert empty strings to None for integer fields
            prep_time = int(prep_time) if prep_time and prep_time.isdigit() else None
            cook_time = int(cook_time) if cook_time and cook_time.isdigit() else None
            servings = int(servings) if servings and servings.isdigit() else None
            calories = int(calories) if calories and calories.isdigit() else None
            
            # Insert recipe into database
            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO recipes (
                    user_id, title, description, prep_time, cook_time, 
                    servings, ingredients, instructions, photo_path, 
                    calories, privacy, cuisine_type
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                session['user_id'], title, description, prep_time, cook_time,
                servings, ingredients, instructions, photo_path,
                calories, privacy, cuisine_type
            ))
            
            # Get the ID of the newly created recipe
            recipe_id = cur.lastrowid
            
            # Commit to DB
            mysql.connection.commit()
            
            # Close connection
            cur.close()
            
            flash('Recipe created successfully!', 'success')
            return redirect(url_for('user_dashboard'))
            
        except Exception as e:
            flash(f'Error creating recipe: {str(e)}', 'danger')
            print(f"Database error: {str(e)}")
            return redirect(url_for('user_dashboard'))
    
    # If not POST method (should not happen with form)
    return redirect(url_for('user_dashboard'))

@app.route('/create-follows-table')
def create_follows_table():
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS follows (
                id INT AUTO_INCREMENT PRIMARY KEY,
                follower_id INT NOT NULL,
                followed_id INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_follow (follower_id, followed_id),
                FOREIGN KEY (follower_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (followed_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        mysql.connection.commit()
        cur.close()
        return "Follows table created successfully!"
    except Exception as e:
        return f"Error creating follows table: {str(e)}"

@app.route('/recipe/<int:recipe_id>/data')
def get_recipe_data(recipe_id):
    # Check if user is logged in
    if 'logged_in' not in session or 'user_id' not in session:
        return jsonify({"success": False, "error": "Login required"}), 401
    
    try:
        cur = mysql.connection.cursor()
        
        # Get recipe data with author info
        query = """
            SELECT 
                r.*,
                u.id as author_id,
                u.first_name,
                u.last_name,
                u.profile_pic as author_pic,
                (SELECT COUNT(*) FROM recipe_likes WHERE recipe_id = r.id) as likes_count,
                EXISTS(SELECT 1 FROM recipe_likes WHERE recipe_id = r.id AND user_id = %s) as is_liked,
                EXISTS(SELECT 1 FROM saved_recipes WHERE recipe_id = r.id AND user_id = %s) as is_saved
            FROM recipes r
            JOIN users u ON r.user_id = u.id
            WHERE r.id = %s
        """
        cur.execute(query, [session['user_id'], session['user_id'], recipe_id])
        recipe = cur.fetchone()
        
        # Check if recipe exists
        if not recipe:
            cur.close()
            return jsonify({"success": False, "error": "Recipe not found"}), 404
        
        # Prepare user-friendly data
        recipe_data = {
            'id': recipe['id'],
            'title': recipe['title'],
            'description': recipe['description'],
            'ingredients': recipe['ingredients'].split('\n') if recipe['ingredients'] else [],
            'instructions': recipe['instructions'].split('\n') if recipe['instructions'] else [],
            'prep_time': recipe['prep_time'],
            'cook_time': recipe['cook_time'],
            'servings': recipe['servings'],
            'calories': recipe['calories'],
            'cuisine_type': recipe['cuisine_type'],
            'photo_path': recipe['photo_path'],
            'privacy': recipe['privacy'],
            'author': {
                'id': recipe['author_id'],
                'name': f"{recipe['first_name']} {recipe['last_name']}",
                'profile_pic': recipe['author_pic']
            },
            'created_at': recipe['created_at'],
            'relative_time': get_relative_time(recipe['created_at']),
            'likes_count': recipe['likes_count'],
            'is_liked': bool(recipe['is_liked']),
            'is_saved': bool(recipe['is_saved'])
        }
        
        cur.close()
        
        return jsonify({
            "success": True,
            "recipe": recipe_data
        })
        
    except Exception as e:
        print(f"Error getting recipe data: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/edit-recipe', methods=['POST'])
def edit_recipe():
    # Check if user is logged in
    if 'logged_in' not in session or 'user_id' not in session:
        flash('Please log in to edit a recipe', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            # Get form data
            recipe_id = request.form.get('recipe_id')
            title = request.form.get('title')
            description = request.form.get('description', '')
            prep_time = request.form.get('prep_time')
            cook_time = request.form.get('cook_time')
            servings = request.form.get('servings')
            ingredients = request.form.get('ingredients')
            instructions = request.form.get('instructions')
            calories = request.form.get('calories')
            privacy = request.form.get('privacy', 'public')
            cuisine_type = request.form.get('cuisine_type', 'Other')
            
            # Verify that the recipe exists and belongs to the current user
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM recipes WHERE id = %s", [recipe_id])
            recipe = cur.fetchone()
            
            if not recipe:
                flash('Recipe not found', 'danger')
                return redirect(url_for('user_dashboard'))
            
            if recipe['user_id'] != session['user_id']:
                flash('You do not have permission to edit this recipe', 'danger')
                return redirect(url_for('user_dashboard'))
            
            # Handle photo upload
            photo_path = recipe['photo_path']  # Keep existing photo by default
            if 'photo' in request.files and request.files['photo'].filename != '':
                photo = request.files['photo']
                if photo and allowed_file(photo.filename):
                    # Create recipe photos directory if it doesn't exist
                    recipe_upload_folder = 'static/uploads/recipe_photos'
                    os.makedirs(recipe_upload_folder, exist_ok=True)
                    
                    # Generate unique filename
                    unique_filename = f"{uuid.uuid4().hex}_{secure_filename(photo.filename)}"
                    
                    # Use absolute path for saving the file
                    full_photo_path = os.path.join(app.static_folder, 'uploads/recipe_photos', unique_filename)
                    
                    # Save the file
                    photo.save(full_photo_path)
                    
                    # Store the relative path in the database
                    photo_path = f"uploads/recipe_photos/{unique_filename}"
            
            # Convert empty strings to None for integer fields
            prep_time = int(prep_time) if prep_time and prep_time.isdigit() else None
            cook_time = int(cook_time) if cook_time and cook_time.isdigit() else None
            servings = int(servings) if servings and servings.isdigit() else None
            calories = int(calories) if calories and calories.isdigit() else None
            
            # Update the recipe in the database
            cur.execute("""
                UPDATE recipes 
                SET title = %s, description = %s, prep_time = %s, cook_time = %s, 
                    servings = %s, ingredients = %s, instructions = %s, 
                    photo_path = %s, calories = %s, privacy = %s, cuisine_type = %s,
                    updated_at = NOW()
                WHERE id = %s AND user_id = %s
            """, (
                title, description, prep_time, cook_time, servings,
                ingredients, instructions, photo_path, calories, privacy, cuisine_type,
                recipe_id, session['user_id']
            ))
            
            # Commit to DB
            mysql.connection.commit()
            
            # Close connection
            cur.close()
            
            flash('Recipe updated successfully!', 'success')
            return redirect(url_for('user_dashboard'))
            
        except Exception as e:
            flash(f'Error updating recipe: {str(e)}', 'danger')
            print(f"Database error: {str(e)}")
            return redirect(url_for('user_dashboard'))
    
    # If not POST method
    return redirect(url_for('user_dashboard'))

@app.route('/delete-recipe', methods=['POST'])
def delete_recipe():
    # Check if user is logged in
    if 'logged_in' not in session or 'user_id' not in session:
        flash('Please log in to delete a recipe', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            recipe_id = request.form.get('recipe_id')
            
            # Verify that the recipe exists and belongs to the current user
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM recipes WHERE id = %s", [recipe_id])
            recipe = cur.fetchone()
            
            if not recipe:
                flash('Recipe not found', 'danger')
                return redirect(url_for('user_dashboard'))
            
            if recipe['user_id'] != session['user_id']:
                flash('You do not have permission to delete this recipe', 'danger')
                return redirect(url_for('user_dashboard'))
            
            # Delete the recipe
            cur.execute("DELETE FROM recipes WHERE id = %s AND user_id = %s", [recipe_id, session['user_id']])
            
            # Commit to DB
            mysql.connection.commit()
            
            # Delete the photo file if it exists
            if recipe['photo_path']:
                photo_path = os.path.join(app.static_folder, recipe['photo_path'])
                if os.path.exists(photo_path):
                    try:
                        os.remove(photo_path)
                    except Exception as e:
                        print(f"Error deleting photo file: {str(e)}")
            
            # Close connection
            cur.close()
            
            flash('Recipe deleted successfully!', 'success')
            return redirect(url_for('user_dashboard'))
            
        except Exception as e:
            flash(f'Error deleting recipe: {str(e)}', 'danger')
            print(f"Database error: {str(e)}")
            return redirect(url_for('user_dashboard'))
    
    # If not POST method
    return redirect(url_for('user_dashboard'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', title='Page Not Found', now=datetime.now()), 404

# Backend routes for recipe interactions

@app.route('/recipe/<int:recipe_id>/like', methods=['POST'])
def like_recipe(recipe_id):
    # Check if user is logged in
    if 'logged_in' not in session:
        return jsonify({"success": False, "error": "You must be logged in to like recipes"}), 401
    
    try:
        user_id = session['user_id']
        
        # Create cursor
        cur = mysql.connection.cursor()
        
        # Check if the recipe exists
        cur.execute("SELECT id, user_id FROM recipes WHERE id = %s", [recipe_id])
        recipe = cur.fetchone()
        
        if not recipe:
            cur.close()
            return jsonify({"success": False, "error": "Recipe not found"}), 404
        
        # Check if the user has already liked this recipe
        cur.execute("SELECT id FROM recipe_likes WHERE recipe_id = %s AND user_id = %s", [recipe_id, user_id])
        existing_like = cur.fetchone()
        
        if existing_like:
            # User already liked this recipe, so unlike it
            cur.execute("DELETE FROM recipe_likes WHERE recipe_id = %s AND user_id = %s", [recipe_id, user_id])
            action = "unliked"
        else:
            # User hasn't liked this recipe yet, so like it
            cur.execute("INSERT INTO recipe_likes (recipe_id, user_id, created_at) VALUES (%s, %s, NOW())", [recipe_id, user_id])
            action = "liked"
            
            # Create notification (only when liking, not unliking)
            create_like_notification(recipe_id, user_id)
        
        # Get the updated like count
        cur.execute("SELECT COUNT(*) as likes_count FROM recipe_likes WHERE recipe_id = %s", [recipe_id])
        likes_result = cur.fetchone()
        likes_count = likes_result['likes_count'] if likes_result else 0
        
        # Commit the changes
        mysql.connection.commit()
        
        # Close the cursor
        cur.close()
        
        return jsonify({
            "success": True,
            "action": action,
            "likes_count": likes_count
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")
        if 'cur' in locals():
            mysql.connection.rollback()
            cur.close()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/recipe/<int:recipe_id>/save', methods=['POST'])
def save_recipe(recipe_id):
    # Check if user is logged in
    if 'logged_in' not in session or 'user_id' not in session:
        return jsonify({"success": False, "error": "Login required"}), 401
    
    try:
        cur = mysql.connection.cursor()
        
        # Check if recipe exists
        cur.execute("SELECT * FROM recipes WHERE id = %s", [recipe_id])
        recipe = cur.fetchone()
        if not recipe:
            cur.close()
            return jsonify({"success": False, "error": "Recipe not found"}), 404
        
        # Check if the saved_recipes table exists
        cur.execute("SHOW TABLES LIKE 'saved_recipes'")
        if not cur.fetchone():
            # Create saved_recipes table if it doesn't exist
            cur.execute("""
                CREATE TABLE IF NOT EXISTS saved_recipes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    recipe_id INT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY unique_save (user_id, recipe_id),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
                )
            """)
            mysql.connection.commit()
        
        # Check if user already saved the recipe
        cur.execute("SELECT * FROM saved_recipes WHERE recipe_id = %s AND user_id = %s", 
                   [recipe_id, session['user_id']])
        existing_save = cur.fetchone()
        
        if existing_save:
            # User already saved, so unsave
            cur.execute("DELETE FROM saved_recipes WHERE recipe_id = %s AND user_id = %s", 
                       [recipe_id, session['user_id']])
            action = "unsaved"
            is_saved = False
        else:
            # User hasn't saved, so save
            cur.execute("INSERT INTO saved_recipes (recipe_id, user_id) VALUES (%s, %s)", 
                       [recipe_id, session['user_id']])
            action = "saved"
            is_saved = True
        
        mysql.connection.commit()
        cur.close()
        
        return jsonify({
            "success": True, 
            "action": action,
            "is_saved": is_saved
        })
        
    except Exception as e:
        print(f"Error saving recipe: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/recipe/<int:recipe_id>/comments', methods=['GET'])
def get_recipe_comments(recipe_id):
    if 'user_id' not in session:
        return jsonify({"success": False, "error": "Please login to view comments"}), 401
        
    try:
        cur = mysql.connection.cursor()
        
        # First check if recipe exists
        cur.execute("SELECT id FROM recipes WHERE id = %s", [recipe_id])
        if not cur.fetchone():
            cur.close()
            return jsonify({"success": False, "error": "Recipe not found"}), 404

        # Ensure tables exist
        cur.execute("""
            CREATE TABLE IF NOT EXISTS recipe_comments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                recipe_id INT NOT NULL,
                user_id INT NOT NULL,
                comment_text TEXT NOT NULL,
                parent_comment_id INT NULL,
                reactions_count INT DEFAULT 0,
                replies_count INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Check if comment_reactions table exists, create if it doesn't
        cur.execute("""
            CREATE TABLE IF NOT EXISTS comment_reactions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                comment_id INT NOT NULL,
                user_id INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_reaction (comment_id, user_id),
                FOREIGN KEY (comment_id) REFERENCES recipe_comments(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        mysql.connection.commit()
            
        # Initialize replies_count for all comments
        cur.execute("""
            UPDATE recipe_comments c
            SET replies_count = (
                SELECT COUNT(*) 
                FROM recipe_comments 
                WHERE parent_comment_id = c.id
            )
            WHERE recipe_id = %s
        """, [recipe_id])
            
        # Update all comments' reactions_count to ensure accuracy
        cur.execute("""
            UPDATE recipe_comments rc 
            SET reactions_count = (
                SELECT COUNT(*) 
                FROM comment_reactions 
                WHERE comment_id = rc.id
            )
            WHERE recipe_id = %s
        """, [recipe_id])
        mysql.connection.commit()
        
        # Get top-level comments with user info and reactions count
        query = """
            SELECT 
                c.*,
                u.first_name,
                u.last_name,
                u.profile_pic,
                c.reactions_count,
                (SELECT COUNT(*) FROM recipe_comments WHERE parent_comment_id = c.id) as replies_count,
                EXISTS(SELECT 1 FROM comment_reactions WHERE comment_id = c.id AND user_id = %s) as user_has_reacted
            FROM recipe_comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.recipe_id = %s AND c.parent_comment_id IS NULL
            ORDER BY c.created_at DESC
        """
        
        cur.execute(query, [session['user_id'], recipe_id])
        
        comments = []
        for row in cur.fetchall():
            comments.append({
                "id": row['id'],
                "user_id": row['user_id'],
                "user_name": f"{row['first_name']} {row['last_name']}",
                "user_profile_pic": row['profile_pic'],
                "text": row['comment_text'],
                "created_at": get_relative_time(row['created_at']),
                "reactions_count": row['reactions_count'] or 0,
                "user_has_reacted": bool(row['user_has_reacted']),
                "replies_count": row['replies_count'] or 0
            })
            
        cur.close()
        
        return jsonify({
            "success": True,
            "comments": comments
        })
        
    except Exception as e:
        print(f"Error loading comments: {str(e)}")
        if 'cur' in locals():
            cur.close()
        return jsonify({"success": False, "error": "Failed to load comments"}), 500

@app.route('/recipe/<int:recipe_id>/comment', methods=['POST'])
def add_comment(recipe_id):
    if 'user_id' not in session:
        return jsonify({"success": False, "error": "Please login to comment"}), 401
        
    try:
        data = request.json
        comment_text = data.get('comment', '').strip()
        
        if not comment_text:
            return jsonify({"success": False, "error": "Comment cannot be empty"}), 400
            
        cur = mysql.connection.cursor()
        
        # Check if recipe exists
        cur.execute("SELECT id FROM recipes WHERE id = %s", [recipe_id])
        if not cur.fetchone():
            cur.close()
            return jsonify({"success": False, "error": "Recipe not found"}), 404
            
        # Ensure recipe_comments table exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS recipe_comments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                recipe_id INT NOT NULL,
                user_id INT NOT NULL,
                comment_text TEXT NOT NULL,
                parent_comment_id INT NULL,
                reactions_count INT DEFAULT 0,
                replies_count INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        mysql.connection.commit()
        
        # Check if recipes table has comments_count column
        cur.execute("""
            SELECT COUNT(*) as count 
            FROM information_schema.columns 
            WHERE table_name = 'recipes' 
            AND column_name = 'comments_count'
        """)
        
        if cur.fetchone()['count'] == 0:
            # Add comments_count column if it doesn't exist
            cur.execute("ALTER TABLE recipes ADD COLUMN comments_count INT DEFAULT 0")
            mysql.connection.commit()
            
        # Insert comment
        current_time = datetime.now()
        cur.execute("""
            INSERT INTO recipe_comments (recipe_id, user_id, comment_text, created_at)
            VALUES (%s, %s, %s, %s)
        """, [recipe_id, session['user_id'], comment_text, current_time])
        
        comment_id = cur.lastrowid
        
        # Update recipe comments count
        cur.execute("""
            UPDATE recipes 
            SET comments_count = COALESCE(comments_count, 0) + 1 
            WHERE id = %s
        """, [recipe_id])
        
        # Get comment details with user info
        cur.execute("""
            SELECT 
                c.*,
                u.first_name,
                u.last_name,
                u.profile_pic
            FROM recipe_comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.id = %s
        """, [comment_id])
        
        comment = cur.fetchone()
        
        mysql.connection.commit()
        cur.close()
        
        return jsonify({
            "success": True,
            "comment": {
                "id": comment['id'],
                "user_id": comment['user_id'],
                "user_name": f"{comment['first_name']} {comment['last_name']}",
                "user_profile_pic": comment['profile_pic'],
                "text": comment['comment_text'],
                "created_at": "just now",
                "reactions_count": 0,
                "user_has_reacted": False,
                "replies_count": 0
            }
        })
        
    except Exception as e:
        print(f"Error adding comment: {str(e)}")
        if 'cur' in locals():
            cur.close()
        return jsonify({"success": False, "error": "Failed to add comment"}), 500

@app.route('/recipe/comment/<int:comment_id>/react', methods=['POST'])
def react_to_comment(comment_id):
    if 'user_id' not in session:
        return jsonify({"success": False, "error": "Please login to react to comments"}), 401
        
    try:
        cur = mysql.connection.cursor()
        
        # Check if comment exists
        cur.execute("SELECT id FROM recipe_comments WHERE id = %s", [comment_id])
        if not cur.fetchone():
            cur.close()
            return jsonify({"success": False, "error": "Comment not found"}), 404
        
        # Ensure comment_reactions table exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS comment_reactions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                comment_id INT NOT NULL,
                user_id INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_reaction (comment_id, user_id),
                FOREIGN KEY (comment_id) REFERENCES recipe_comments(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Check if reactions_count column exists in recipe_comments table
        cur.execute("""
            SELECT COUNT(*) as count 
            FROM information_schema.columns 
            WHERE table_name = 'recipe_comments' 
            AND column_name = 'reactions_count'
        """)
        
        if cur.fetchone()['count'] == 0:
            # Add reactions_count column if it doesn't exist
            cur.execute("ALTER TABLE recipe_comments ADD COLUMN reactions_count INT DEFAULT 0")
            mysql.connection.commit()
        
        # Check if user already reacted to the comment
        cur.execute("""
            SELECT id FROM comment_reactions 
            WHERE comment_id = %s AND user_id = %s
        """, [comment_id, session['user_id']])
        
        existing_reaction = cur.fetchone()
        
        if existing_reaction:
            # Remove reaction
            cur.execute("""
                DELETE FROM comment_reactions 
                WHERE comment_id = %s AND user_id = %s
            """, [comment_id, session['user_id']])
            
            # Decrease reactions_count in recipe_comments table
            cur.execute("""
                UPDATE recipe_comments 
                SET reactions_count = GREATEST(reactions_count - 1, 0)
                WHERE id = %s
            """, [comment_id])
            reacted = False
        else:
            # Add reaction
            cur.execute("""
                INSERT INTO comment_reactions (comment_id, user_id)
                VALUES (%s, %s)
            """, [comment_id, session['user_id']])
            
            # Increase reactions_count in recipe_comments table
            cur.execute("""
                UPDATE recipe_comments 
                SET reactions_count = COALESCE(reactions_count, 0) + 1 
                WHERE id = %s
            """, [comment_id])
            reacted = True
        
        # Get updated reactions count
        cur.execute("""
            SELECT COUNT(*) as count
            FROM comment_reactions 
            WHERE comment_id = %s
        """, [comment_id])
        
        reactions_count = cur.fetchone()['count']
        
        # Make sure the reactions_count in the table matches the actual count
        cur.execute("""
            UPDATE recipe_comments 
            SET reactions_count = %s
            WHERE id = %s
        """, [reactions_count, comment_id])
        
        mysql.connection.commit()
        cur.close()
        
        return jsonify({
            "success": True,
            "reacted": reacted,
            "reactions_count": reactions_count
        })
        
    except Exception as e:
        print(f"Error handling comment reaction: {str(e)}")
        if 'cur' in locals():
            cur.close()
        return jsonify({"success": False, "error": "Failed to update reaction"}), 500

@app.route('/recipe/<int:recipe_id>', methods=['GET'])
def view_recipe(recipe_id):
    try:
        cur = mysql.connection.cursor()
        
        # Check if tables exist
        cur.execute("SHOW TABLES LIKE 'recipe_likes'")
        likes_table_exists = cur.fetchone() is not None
        
        cur.execute("SHOW TABLES LIKE 'recipe_comments'")
        comments_table_exists = cur.fetchone() is not None
        
        # Construct the likes and comments count subqueries
        if likes_table_exists:
            likes_count_subquery = "(SELECT COUNT(*) FROM recipe_likes WHERE recipe_id = r.id)"
        else:
            likes_count_subquery = "0"
            
        if comments_table_exists:
            comments_count_subquery = "(SELECT COUNT(*) FROM recipe_comments WHERE recipe_id = r.id)"
        else:
            comments_count_subquery = "0"
        
        # Get recipe details with proper count handling
        query = f"""
            SELECT r.*, u.first_name, u.last_name, u.profile_pic,
                   {likes_count_subquery} as likes_count,
                   {comments_count_subquery} as comments_count
            FROM recipes r
            JOIN users u ON r.user_id = u.id
            WHERE r.id = %s
        """
        
        cur.execute(query, [recipe_id])
        recipe = cur.fetchone()
        cur.close()
        
        if not recipe:
            flash('Recipe not found', 'danger')
            return redirect(url_for('user_dashboard'))
        
        # Check if private recipe access is allowed
        if recipe['privacy'] == 'private' and recipe['user_id'] != session.get('user_id'):
            flash('You do not have permission to view this recipe', 'danger')
            return redirect(url_for('user_dashboard'))
        
        # For friends-only recipes, check if the user follows the creator
        if recipe['privacy'] == 'friends' and recipe['user_id'] != session.get('user_id'):
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM follows WHERE follower_id = %s AND followed_id = %s", 
                       [session.get('user_id'), recipe['user_id']])
            is_following = cur.fetchone()
            cur.close()
            
            if not is_following:
                flash('You need to follow the creator to view this recipe', 'danger')
                return redirect(url_for('user_dashboard'))
        
        # Render the recipe page
        return render_template('recipe_detail.html', 
                              title=recipe['title'],
                              recipe=recipe,
                              now=datetime.now())
        
    except Exception as e:
        flash(f'Error viewing recipe: {str(e)}', 'danger')
        return redirect(url_for('user_dashboard'))

@app.route('/recipe/comment/<int:comment_id>', methods=['DELETE'])
def delete_comment(comment_id):
    # Check if user is logged in
    if 'logged_in' not in session or 'user_id' not in session:
        return jsonify({"success": False, "error": "Login required"}), 401
    
    try:
        cur = mysql.connection.cursor()
        
        # Get the comment and check ownership
        cur.execute("""
            SELECT recipe_id, user_id 
            FROM recipe_comments 
            WHERE id = %s
        """, [comment_id])
        comment = cur.fetchone()
        
        if not comment:
            cur.close()
            return jsonify({"success": False, "error": "Comment not found"}), 404
            
        # Only allow comment owner to delete
        if comment['user_id'] != session['user_id']:
            cur.close()
            return jsonify({"success": False, "error": "Unauthorized"}), 403
            
        # Delete the comment
        cur.execute("DELETE FROM recipe_comments WHERE id = %s", [comment_id])
        
        # Decrement comments_count in recipes table
        cur.execute("UPDATE recipes SET comments_count = comments_count - 1 WHERE id = %s", [comment['recipe_id']])
        
        # Get updated comments count
        cur.execute("SELECT comments_count FROM recipes WHERE id = %s", [comment['recipe_id']])
        recipe = cur.fetchone()
        
        mysql.connection.commit()
        cur.close()
        
        return jsonify({
            "success": True,
            "comments_count": recipe['comments_count']
        })
        
    except Exception as e:
        print(f"Error deleting comment: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/recipe/comment/<int:comment_id>/reply', methods=['POST'])
def reply_to_comment(comment_id):
    if 'user_id' not in session:
        return jsonify({"success": False, "error": "Please login to reply to comments"}), 401
    
    try:
        data = request.get_json()
        reply_text = data.get('reply', '').strip()
        reference_reply_id = data.get('reference_reply_id')
        
        if not reply_text:
            return jsonify({"success": False, "error": "Reply text cannot be empty"}), 400
        
        # Get parent comment info
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, recipe_id FROM recipe_comments WHERE id = %s", [comment_id])
        parent_comment = cur.fetchone()
        
        if not parent_comment:
            cur.close()
            return jsonify({"success": False, "error": "Parent comment not found"}), 404
        
        # If we're replying to a reply, get that reply's information to include the username
        if reference_reply_id:
            cur.execute("""
                SELECT rc.id, u.first_name, u.last_name 
                FROM recipe_comments rc
                JOIN users u ON rc.user_id = u.id
                WHERE rc.id = %s
            """, [reference_reply_id])
            reference_reply = cur.fetchone()
            
            if reference_reply:
                # Format reply text to indicate it's a reply to another user
                referenced_username = f"{reference_reply['first_name']} {reference_reply['last_name']}"
                if not reply_text.startswith(f"@{referenced_username}"):
                    reply_text = f"@{referenced_username} {reply_text}"
        
        # Insert reply
        current_time = datetime.now()
        recipe_id = parent_comment['recipe_id']
        insert_query = """
            INSERT INTO recipe_comments 
            (recipe_id, user_id, comment_text, parent_comment_id, created_at) 
            VALUES (%s, %s, %s, %s, %s)
        """
        cur.execute(insert_query, [recipe_id, session['user_id'], reply_text, comment_id, current_time])
        mysql.connection.commit()
        
        # Get the new reply ID
        reply_id = cur.lastrowid
        
        # Get user info
        cur.execute("""
            SELECT u.first_name, u.last_name, u.profile_pic
            FROM users u
            WHERE u.id = %s
        """, [session['user_id']])
        user_info = cur.fetchone()
        
        # Update parent comment's replies count
        cur.execute("UPDATE recipe_comments SET replies_count = (SELECT COUNT(*) FROM recipe_comments WHERE parent_comment_id = %s) WHERE id = %s", 
            [comment_id, comment_id])
        
        # Get updated replies count
        cur.execute("SELECT COUNT(*) as count FROM recipe_comments WHERE parent_comment_id = %s", [comment_id])
        replies_count = cur.fetchone()['count']
        
        mysql.connection.commit()
        cur.close()
        
        # Construct reply object for the response
        reply = {
            "id": reply_id,
            "user_id": session['user_id'],
            "user_name": f"{user_info['first_name']} {user_info['last_name']}",
            "user_profile_pic": user_info['profile_pic'],
            "text": reply_text,
            "created_at": "just now",  # Special case for new replies
            "reactions_count": 0,
            "user_has_reacted": False,
            "replies_count": 0,  # New replies start with 0 replies
            "reference_reply_id": reference_reply_id
        }
        
        return jsonify({
            "success": True, 
            "reply": reply,
            "replies_count": replies_count
        })
        
    except Exception as e:
        print(f"Error replying to comment: {str(e)}")
        if 'cur' in locals():
            cur.close()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/recipe/comment/<int:comment_id>/replies', methods=['GET'])
def get_comment_replies(comment_id):
    if 'user_id' not in session:
        return jsonify({"success": False, "error": "Please login to view replies"}), 401
        
    try:
        cur = mysql.connection.cursor()
        
        # Check if comment exists
        cur.execute("SELECT id FROM recipe_comments WHERE id = %s", [comment_id])
        if not cur.fetchone():
            cur.close()
            return jsonify({"success": False, "error": "Comment not found"}), 404
        
        # Make sure the comment_reactions table exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS comment_reactions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                comment_id INT NOT NULL,
                user_id INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_reaction (comment_id, user_id),
                FOREIGN KEY (comment_id) REFERENCES recipe_comments(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        mysql.connection.commit()
            
        # Update reactions count for all replies
        cur.execute("""
            UPDATE recipe_comments rc 
            SET reactions_count = (
                SELECT COUNT(*) 
                FROM comment_reactions 
                WHERE comment_id = rc.id
            )
            WHERE parent_comment_id = %s
        """, [comment_id])
        
        # Update replies_count for all replies (for nested replies)
        cur.execute("""
            UPDATE recipe_comments rc 
            SET replies_count = (
                SELECT COUNT(*) 
                FROM recipe_comments 
                WHERE parent_comment_id = rc.id
            )
            WHERE parent_comment_id = %s
        """, [comment_id])
        
        mysql.connection.commit()
        
        # Get all replies for the comment with user info and reaction status
        cur.execute("""
            SELECT 
                c.*,
                u.first_name,
                u.last_name,
                u.profile_pic,
                COALESCE(c.reactions_count, 0) as reactions_count,
                (SELECT COUNT(*) FROM recipe_comments WHERE parent_comment_id = c.id) as replies_count,
                EXISTS(SELECT 1 FROM comment_reactions WHERE comment_id = c.id AND user_id = %s) as user_has_reacted
            FROM recipe_comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.parent_comment_id = %s
            ORDER BY c.created_at ASC
        """, [session['user_id'], comment_id])
        
        replies = []
        for row in cur.fetchall():
            replies.append({
                "id": row['id'],
                "user_id": row['user_id'],
                "user_name": f"{row['first_name']} {row['last_name']}",
                "user_profile_pic": row['profile_pic'],
                "text": row['comment_text'],
                "created_at": get_relative_time(row['created_at']),
                "reactions_count": row['reactions_count'] or 0,
                "user_has_reacted": bool(row['user_has_reacted']),
                "replies_count": row['replies_count'] or 0  # Include replies count for nested replies
            })
            
        cur.close()
        
        return jsonify({
            "success": True,
            "replies": replies
        })
        
    except Exception as e:
        print(f"Error getting comment replies: {str(e)}")
        if 'cur' in locals():
            cur.close()
        return jsonify({"success": False, "error": "Failed to load replies"}), 500

@app.route('/recipe/comments/init_tables', methods=['GET'])
def init_comments_tables():
    if 'user_id' not in session:
        return jsonify({"success": False, "error": "Please login"}), 401
        
    try:
        cur = mysql.connection.cursor()
        
        # Create recipe_comments table if not exists with replies_count column
        cur.execute("""
            CREATE TABLE IF NOT EXISTS recipe_comments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                recipe_id INT NOT NULL,
                user_id INT NOT NULL,
                comment_text TEXT NOT NULL,
                parent_comment_id INT NULL,
                reactions_count INT DEFAULT 0,
                replies_count INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Create comment_reactions table if not exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS comment_reactions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                comment_id INT NOT NULL,
                user_id INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_reaction (comment_id, user_id),
                FOREIGN KEY (comment_id) REFERENCES recipe_comments(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Check if we need to add replies_count column to recipe_comments
        cur.execute("""
            SELECT COUNT(*) as count 
            FROM information_schema.columns 
            WHERE table_name = 'recipe_comments' 
            AND column_name = 'replies_count'
        """)
        if cur.fetchone()['count'] == 0:
            cur.execute("""
                ALTER TABLE recipe_comments 
                ADD COLUMN replies_count INT DEFAULT 0
            """)
            
        mysql.connection.commit()
        cur.close()
        
        return jsonify({"success": True, "message": "Comment tables initialized successfully"})
    
    except Exception as e:
        print(f"Error initializing comment tables: {str(e)}")
        if 'cur' in locals():
            cur.close()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/admin/suspend_user', methods=['POST'])
def suspend_user_api():
    # Check if user is logged in as admin
    if 'logged_in' in session and session['user_type'] == 'admin':
        try:
            # Get JSON data from request
            data = request.get_json()
            user_id = data.get('user_id')
            suspend = data.get('suspend', True)
            
            if not user_id:
                return jsonify({'success': False, 'message': 'User ID is required'}), 400
            
            # Create cursor
            cur = mysql.connection.cursor()
            
            # First, ensure the is_suspended column exists
            try:
                cur.execute("SELECT is_suspended FROM users LIMIT 1")
            except Exception:
                # Column doesn't exist, create it
                cur.execute("ALTER TABLE users ADD COLUMN is_suspended TINYINT(1) DEFAULT 0")
                mysql.connection.commit()
            
            # Check if user exists
            cur.execute("SELECT * FROM users WHERE id = %s", [user_id])
            user = cur.fetchone()
            
            if not user:
                return jsonify({'success': False, 'message': 'User not found'}), 404
            
            # Set suspension status
            new_status = 1 if suspend else 0
            
            # Update user status
            cur.execute("UPDATE users SET is_suspended = %s WHERE id = %s", [new_status, user_id])
            
            # Commit to DB
            mysql.connection.commit()
            
            # Close connection
            cur.close()
            
            return jsonify({'success': True, 'message': 'User status updated successfully'})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    
    return jsonify({'success': False, 'message': 'Unauthorized'}), 401

@app.route('/user/<int:user_id>/profile', methods=['GET'])
def get_user_profile(user_id):
    try:
        cur = mysql.connection.cursor()
        
        # Get user details
        cur.execute("""
            SELECT 
                u.id, 
                u.first_name, 
                u.last_name, 
                u.email, 
                u.profile_pic, 
                u.bio, 
                u.location,
                u.created_at,
                (SELECT COUNT(*) FROM recipes WHERE user_id = u.id) as recipe_count,
                (SELECT COUNT(*) FROM follows WHERE followed_id = u.id) as followers_count,
                EXISTS(SELECT 1 FROM follows WHERE follower_id = %s AND followed_id = u.id) as is_following
            FROM users u
            WHERE u.id = %s
        """, [session.get('user_id', 0), user_id])
        
        user_data = cur.fetchone()
        
        if not user_data:
            cur.close()
            return jsonify({"success": False, "error": "User not found"}), 404
        
        # Get user's top recipes
        cur.execute("""
            SELECT 
                r.id, 
                r.title, 
                r.photo_path,
                (SELECT COUNT(*) FROM recipe_likes WHERE recipe_id = r.id) as likes_count
            FROM recipes r
            WHERE r.user_id = %s
            ORDER BY likes_count DESC, r.created_at DESC
            LIMIT 5
        """, [user_id])
        
        recipes = cur.fetchall()
        
        # Format the response
        user = {
            "id": user_data['id'],
            "first_name": user_data['first_name'],
            "last_name": user_data['last_name'],
            "email": user_data['email'],
            "profile_pic": user_data['profile_pic'],
            "bio": user_data['bio'],
            "location": user_data['location'],
            "created_at": user_data['created_at'].isoformat() if user_data['created_at'] else None,
            "recipe_count": user_data['recipe_count'],
            "followers_count": user_data['followers_count'],
            "is_following": bool(user_data['is_following']),
            "recipes": [{
                "id": recipe['id'],
                "title": recipe['title'],
                "photo_path": recipe['photo_path'],
                "likes_count": recipe['likes_count']
            } for recipe in recipes]
        }
        
        cur.close()
        
        return jsonify({
            "success": True,
            "user": user
        })
        
    except Exception as e:
        print(f"Error getting user profile: {str(e)}")
        if 'cur' in locals():
            cur.close()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/user/<int:user_id>/follow', methods=['POST'])
def follow_user(user_id):
    # Check if user is logged in
    if 'logged_in' not in session or 'user_id' not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    if user_id == session['user_id']:
        return jsonify({"success": False, "error": "Cannot follow yourself"}), 400
    
    try:
        cur = mysql.connection.cursor()
        
        # Check if user exists
        cur.execute("SELECT id FROM users WHERE id = %s", [user_id])
        if not cur.fetchone():
            cur.close()
            return jsonify({"success": False, "error": "User not found"}), 404
        
        # Check if already following
        cur.execute("SELECT id FROM follows WHERE follower_id = %s AND followed_id = %s", 
                   [session['user_id'], user_id])
        if cur.fetchone():
            cur.close()
            return jsonify({"success": True, "message": "Already following user"})
        
        # Add follow relationship
        cur.execute("INSERT INTO follows (follower_id, followed_id, created_at) VALUES (%s, %s, NOW())",
                   [session['user_id'], user_id])
        
        mysql.connection.commit()
        cur.close()
        
        return jsonify({"success": True})
        
    except Exception as e:
        print(f"Error following user: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/user/<int:user_id>/unfollow', methods=['POST'])
def unfollow_user(user_id):
    # Check if user is logged in
    if 'logged_in' not in session or 'user_id' not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    try:
        cur = mysql.connection.cursor()
        
        # Delete follow relationship
        cur.execute("DELETE FROM follows WHERE follower_id = %s AND followed_id = %s", 
                   [session['user_id'], user_id])
        
        mysql.connection.commit()
        cur.close()
        
        return jsonify({"success": True})
        
    except Exception as e:
        print(f"Error unfollowing user: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/recipe/<int:recipe_id>/update-cuisine', methods=['POST'])
def update_recipe_cuisine(recipe_id):
    # Check if user is logged in
    if 'logged_in' not in session or 'user_id' not in session:
        return jsonify({"success": False, "error": "Login required"}), 401
    
    try:
        data = request.json
        cuisine_type = data.get('cuisine_type')
        
        if not cuisine_type:
            return jsonify({"success": False, "error": "Cuisine type is required"}), 400
        
        cur = mysql.connection.cursor()
        
        # Check if recipe exists
        cur.execute("SELECT * FROM recipes WHERE id = %s", [recipe_id])
        recipe = cur.fetchone()
        if not recipe:
            cur.close()
            return jsonify({"success": False, "error": "Recipe not found"}), 404
        
        # Check if the user has saved this recipe
        cur.execute("SELECT * FROM saved_recipes WHERE recipe_id = %s AND user_id = %s", 
                   [recipe_id, session['user_id']])
        if not cur.fetchone():
            cur.close()
            return jsonify({"success": False, "error": "Recipe not in your saved list"}), 403
        
        # Update the cuisine type
        cur.execute("UPDATE recipes SET cuisine_type = %s WHERE id = %s", 
                   [cuisine_type, recipe_id])
        
        mysql.connection.commit()
        cur.close()
        
        return jsonify({
            "success": True, 
            "message": f"Recipe moved to {cuisine_type} collection"
        })
        
    except Exception as e:
        print(f"Error updating recipe cuisine: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/user/notifications/mark-read', methods=['POST'])
def mark_notifications_read():
    # Check if user is logged in
    if 'logged_in' not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    
    try:
        notification_id = request.json.get('notification_id')
        mark_all = request.json.get('mark_all', False)  # New parameter to explicitly mark all as read
        
        # Create cursor
        cur = mysql.connection.cursor()
        
        # Ensure the is_read column exists in notifications table
        try:
            cur.execute("""
                SELECT COUNT(*) as count 
                FROM information_schema.columns 
                WHERE table_name = 'notifications' 
                AND column_name = 'is_read'
            """)
            if cur.fetchone()['count'] == 0:
                cur.execute("ALTER TABLE notifications ADD COLUMN is_read TINYINT(1) DEFAULT 0")
                mysql.connection.commit()
        except Exception as e:
            print(f"Error checking notifications table: {str(e)}")
        
        if notification_id:
            # Mark specific notification as read
            cur.execute("""
                UPDATE notifications
                SET is_read = 1
                WHERE id = %s AND user_id = %s
            """, [notification_id, session['user_id']])
        else:
            # Mark all notifications as read
            cur.execute("""
                UPDATE notifications
                SET is_read = 1
                WHERE user_id = %s AND is_read = 0
            """, [session['user_id']])
        
        # Commit the changes
        mysql.connection.commit()
        
        # Get updated unread count
        cur.execute("""
            SELECT COUNT(*) as unread_count
            FROM notifications
            WHERE user_id = %s AND is_read = 0
        """, [session['user_id']])
        
        unread_result = cur.fetchone()
        unread_count = unread_result['unread_count'] if unread_result else 0
        
        # Create a persistent record of the read status for this user session
        if mark_all or not notification_id:
            # Get timestamp of last notification to track what's been read
            cur.execute("""
                SELECT MAX(id) as last_id
                FROM notifications
                WHERE user_id = %s
            """, [session['user_id']])
            result = cur.fetchone()
            last_notification_id = result['last_id'] if result and result['last_id'] else 0
            
            # Store this in a session record
            session['last_read_notification'] = last_notification_id
            session['notifications_read_at'] = datetime.now().timestamp()
            
        cur.close()
        
        return jsonify({
            "success": True,
            "unread_count": unread_count,
            "all_read": mark_all or not notification_id,
            "read_timestamp": datetime.now().timestamp() if (mark_all or not notification_id) else None
        })
    
    except Exception as e:
        print(f"Error marking notifications as read: {str(e)}")
        if 'cur' in locals():
            mysql.connection.rollback()
            cur.close()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/user/notifications')
def get_user_notifications():
    # Check if user is logged in
    if 'logged_in' not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    
    try:
        # Create cursor
        cur = mysql.connection.cursor()
        
        # Ensure the notifications table exists
        try:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    sender_id INT,
                    notification_type VARCHAR(50) NOT NULL,
                    entity_id INT NOT NULL,
                    entity_type VARCHAR(50) NOT NULL,
                    message TEXT NOT NULL,
                    is_read TINYINT(1) DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            mysql.connection.commit()
        except Exception as e:
            print(f"Error checking notifications table: {str(e)}")
        
        # Get notifications for current user, limit to 10 most recent
        cur.execute("""
            SELECT 
                n.*,
                u.id as sender_id,
                u.first_name as sender_first_name,
                u.last_name as sender_last_name,
                u.profile_pic as sender_profile_pic
            FROM notifications n
            LEFT JOIN users u ON n.sender_id = u.id
            WHERE n.user_id = %s
            ORDER BY n.created_at DESC
            LIMIT 10
        """, [session['user_id']])
        
        notifications_data = cur.fetchall()
        
        # Get unread count
        cur.execute("""
            SELECT COUNT(*) as unread_count
            FROM notifications
            WHERE user_id = %s AND is_read = 0
        """, [session['user_id']])
        
        unread_result = cur.fetchone()
        unread_count = unread_result['unread_count'] if unread_result else 0
        
        # Process notifications with relative time and format for JSON response
        notifications = []
        for n in notifications_data:
            notification = {
                'id': n['id'],
                'type': n['notification_type'],
                'entity_id': n['entity_id'],
                'entity_type': n['entity_type'],
                'is_read': bool(n['is_read']),
                'message': n['message'],
                'relative_time': get_relative_time(n['created_at']),
                'created_at': n['created_at'].isoformat() if n['created_at'] else None
            }
            
            # Add sender info if available
            if n['sender_id']:
                notification['sender'] = {
                    'id': n['sender_id'],
                    'name': f"{n['sender_first_name']} {n['sender_last_name']}",
                    'profile_pic': n['sender_profile_pic']
                }
            
            notifications.append(notification)
        
        cur.close()
        
        # Get last notification read status from session
        has_read_all = False
        if 'last_read_notification' in session and 'notifications_read_at' in session:
            last_read_id = session.get('last_read_notification', 0)
            read_timestamp = session.get('notifications_read_at', 0)
            
            if notifications and last_read_id >= notifications[0]['id']:
                has_read_all = True
        
        return jsonify({
            "success": True,
            "notifications": notifications,
            "unread_count": 0 if has_read_all else unread_count,
            "all_read": has_read_all
        })
    
    except Exception as e:
        print(f"Error fetching notifications: {str(e)}")
        if 'cur' in locals():
            cur.close()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/user/notifications/all')
def view_all_notifications():
    # Check if user is logged in
    if 'logged_in' not in session:
        flash('You must be logged in to view notifications', 'danger')
        return redirect(url_for('login'))
    
    try:
        # Create cursor
        cur = mysql.connection.cursor()
        
        # Get all notifications
        cur.execute("""
            SELECT 
                n.id,
                n.notification_type,
                n.entity_id,
                n.entity_type,
                n.is_read,
                n.message,
                n.created_at,
                u.id as sender_id,
                u.first_name as sender_first_name,
                u.last_name as sender_last_name,
                u.profile_pic as sender_profile_pic
            FROM notifications n
            LEFT JOIN users u ON n.sender_id = u.id
            WHERE n.user_id = %s
            ORDER BY n.created_at DESC
        """, [session['user_id']])
        
        notifications_data = cur.fetchall()
        
        # Process notifications with relative time
        for n in notifications_data:
            n['relative_time'] = get_relative_time(n['created_at'])
        
        cur.close()
        
        # Mark all as read
        mark_all_read = request.args.get('mark_read', 'false').lower() == 'true'
        if mark_all_read:
            cur = mysql.connection.cursor()
            cur.execute("""
                UPDATE notifications
                SET is_read = 1
                WHERE user_id = %s
            """, [session['user_id']])
            mysql.connection.commit()
            cur.close()
        
        return render_template('user/notifications.html', 
                              title='All Notifications',
                              notifications=notifications_data)
    
    except Exception as e:
        print(f"Error fetching all notifications: {str(e)}")
        if 'cur' in locals():
            cur.close()
        flash('Error loading notifications', 'danger')
        return redirect(url_for('user_dashboard'))

# Utility function to create notifications
def create_notification(user_id, sender_id, notification_type, entity_id, entity_type, message):
    try:
        # Don't create notification if sender is the same as recipient
        if sender_id == user_id:
            return True
        
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO notifications (user_id, sender_id, notification_type, entity_id, entity_type, message, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
        """, [user_id, sender_id, notification_type, entity_id, entity_type, message])
        
        mysql.connection.commit()
        cur.close()
        return True
    except Exception as e:
        print(f"Error creating notification: {str(e)}")
        if 'cur' in locals():
            mysql.connection.rollback()
            cur.close()
        return False

# Create like notification
def create_like_notification(recipe_id, liker_id):
    try:
        cur = mysql.connection.cursor()
        
        # Get recipe owner and title
        cur.execute("""
            SELECT r.user_id, r.title, 
                   CONCAT(u.first_name, ' ', u.last_name) as liker_name
            FROM recipes r
            JOIN users u ON u.id = %s
            WHERE r.id = %s
        """, [liker_id, recipe_id])
        
        result = cur.fetchone()
        cur.close()
        
        if result:
            recipe_owner_id = result['user_id']
            recipe_title = result['title']
            liker_name = result['liker_name']
            
            message = f"<strong>{liker_name}</strong> liked your recipe <strong>{recipe_title}</strong>"
            
            return create_notification(
                user_id=recipe_owner_id,
                sender_id=liker_id,
                notification_type='recipe_like',
                entity_id=recipe_id,
                entity_type='recipe',
                message=message
            )
        
        return False
    except Exception as e:
        print(f"Error creating like notification: {str(e)}")
        if 'cur' in locals():
            cur.close()
        return False

# Create comment notification
def create_comment_notification(recipe_id, comment_id, commenter_id):
    try:
        cur = mysql.connection.cursor()
        
        # Get recipe owner and title, commenter name
        cur.execute("""
            SELECT r.user_id, r.title, 
                   CONCAT(u.first_name, ' ', u.last_name) as commenter_name
            FROM recipes r
            JOIN users u ON u.id = %s
            WHERE r.id = %s
        """, [commenter_id, recipe_id])
        
        result = cur.fetchone()
        
        if result:
            recipe_owner_id = result['user_id']
            recipe_title = result['title']
            commenter_name = result['commenter_name']
            
            message = f"<strong>{commenter_name}</strong> commented on your recipe <strong>{recipe_title}</strong>"
            
            return create_notification(
                user_id=recipe_owner_id,
                sender_id=commenter_id,
                notification_type='recipe_comment',
                entity_id=recipe_id,
                entity_type='recipe',
                message=message
            )
        
        cur.close()
        return False
    except Exception as e:
        print(f"Error creating comment notification: {str(e)}")
        if 'cur' in locals():
            cur.close()
        return False

# Create follow notification
def create_follow_notification(follower_id, followed_id):
    try:
        cur = mysql.connection.cursor()
        
        # Get follower name
        cur.execute("""
            SELECT CONCAT(first_name, ' ', last_name) as follower_name
            FROM users
            WHERE id = %s
        """, [follower_id])
        
        result = cur.fetchone()
        cur.close()
        
        if result:
            follower_name = result['follower_name']
            
            message = f"<strong>{follower_name}</strong> started following you"
            
            return create_notification(
                user_id=followed_id,
                sender_id=follower_id,
                notification_type='new_follower',
                entity_id=follower_id,
                entity_type='user',
                message=message
            )
        
        return False
    except Exception as e:
        print(f"Error creating follow notification: {str(e)}")
        if 'cur' in locals():
            cur.close()
        return False

@app.route('/search', methods=['GET'])
def search():
    # Check if user is logged in
    if 'logged_in' not in session or 'user_id' not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    search_term = request.args.get('q', '')
    search_type = request.args.get('type', 'all')  # 'all', 'users', or 'recipes'
    
    if len(search_term) < 2:
        return jsonify({"success": True, "users": [], "recipes": []})
    
    try:
        cur = mysql.connection.cursor()
        results = {"success": True}
        
        # Search for users if type is 'all' or 'users'
        if search_type in ['all', 'users']:
            search_pattern = f"%{search_term}%"
            cur.execute("""
                SELECT u.id, u.first_name, u.last_name, u.display_name, u.profile_pic,
                (SELECT COUNT(*) FROM recipes WHERE user_id = u.id) as recipes_count,
                (SELECT COUNT(*) FROM recipe_likes WHERE user_id = u.id) as likes_count
                FROM users u
                WHERE u.first_name LIKE %s 
                    OR u.last_name LIKE %s 
                    OR u.display_name LIKE %s
                ORDER BY u.display_name
                LIMIT 10
            """, [search_pattern, search_pattern, search_pattern])
            
            users = []
            for user in cur.fetchall():
                users.append({
                    'id': user['id'],
                    'name': f"{user['first_name']} {user['last_name']}",
                    'display_name': user['display_name'],
                    'profile_pic': user['profile_pic'],
                    'recipes_count': user['recipes_count'],
                    'likes_count': user['likes_count'],
                    'type': 'user'
                })
            
            results['users'] = users
        
        # Search for recipes if type is 'all' or 'recipes'
        if search_type in ['all', 'recipes']:
            search_pattern = f"%{search_term}%"
            cur.execute("""
                SELECT r.id, r.title, r.description, r.photo_path, r.cuisine_type,
                       u.id as user_id, u.first_name, u.last_name, u.profile_pic,
                       (SELECT COUNT(*) FROM recipe_likes WHERE recipe_id = r.id) as likes_count,
                       (SELECT COUNT(*) FROM recipe_comments WHERE recipe_id = r.id) as comments_count
                FROM recipes r
                JOIN users u ON r.user_id = u.id
                WHERE r.title LIKE %s 
                    OR r.description LIKE %s 
                    OR r.ingredients LIKE %s
                    OR r.cuisine_type LIKE %s
                ORDER BY r.created_at DESC
                LIMIT 10
            """, [search_pattern, search_pattern, search_pattern, search_pattern])
            
            recipes = []
            for recipe in cur.fetchall():
                recipes.append({
                    'id': recipe['id'],
                    'title': recipe['title'],
                    'description': recipe['description'][:100] + '...' if recipe['description'] and len(recipe['description']) > 100 else recipe['description'],
                    'photo_path': recipe['photo_path'],
                    'cuisine_type': recipe['cuisine_type'],
                    'author': {
                        'id': recipe['user_id'],
                        'name': f"{recipe['first_name']} {recipe['last_name']}",
                        'profile_pic': recipe['profile_pic']
                    },
                    'likes_count': recipe['likes_count'],
                    'comments_count': recipe['comments_count'],
                    'type': 'recipe'
                })
            
            results['recipes'] = recipes
        
        cur.close()
        return jsonify(results)
        
    except Exception as e:
        print(f"Error searching: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/user/<int:user_id>/profile-data')
def get_user_profile_data(user_id):
    # Check if user is logged in
    if 'logged_in' not in session or 'user_id' not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    try:
        cur = mysql.connection.cursor()
        
        # Fetch user data
        cur.execute("""
            SELECT u.id, u.first_name, u.last_name, u.email, u.display_name, u.profile_pic, u.bio,
                   (SELECT COUNT(*) FROM recipes WHERE user_id = u.id) as recipes_count,
                   (SELECT COUNT(*) FROM follows WHERE followed_id = u.id) as followers_count,
                   (SELECT COUNT(*) FROM follows WHERE follower_id = u.id) as following_count,
                   (EXISTS(SELECT 1 FROM follows WHERE follower_id = %s AND followed_id = u.id)) as is_following
            FROM users u
            WHERE u.id = %s
        """, [session['user_id'], user_id])
        
        user = cur.fetchone()
        
        if not user:
            return jsonify({"success": False, "error": "User not found"}), 404
        
        # Fetch recent recipes
        cur.execute("""
            SELECT r.id, r.title, r.photo_path, r.created_at
            FROM recipes r 
            WHERE r.user_id = %s AND r.privacy = 'public'
            ORDER BY r.created_at DESC
            LIMIT 4
        """, [user_id])
        
        recent_recipes = []
        for recipe in cur.fetchall():
            recent_recipes.append({
                'id': recipe['id'],
                'title': recipe['title'],
                'photo_path': recipe['photo_path'],
                'created_at': recipe['created_at'].strftime('%b %d, %Y')
            })
        
        # Format user data for response
        user_data = {
            'id': user['id'],
            'name': f"{user['first_name']} {user['last_name']}",
            'display_name': user['display_name'] or user['first_name'],
            'profile_pic': user['profile_pic'],
            'bio': user['bio'],
            'recipes_count': user['recipes_count'],
            'followers_count': user['followers_count'],
            'following_count': user['following_count'],
            'is_following': bool(user['is_following']),
            'is_current_user': user['id'] == session['user_id'],
            'recent_recipes': recent_recipes
        }
        
        cur.close()
        
        return jsonify({
            "success": True,
            "user": user_data
        })
        
    except Exception as e:
        print(f"Error getting user profile data: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 