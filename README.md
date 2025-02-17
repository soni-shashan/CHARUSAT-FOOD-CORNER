# CHARUSAT FOOD CORNER 🍽️

Welcome to the CHARUSAT FOOD CORNER project! This web application is designed to provide users with a seamless experience for browsing and ordering food items. 

## Table of Contents
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)

## Features ✨
- User-friendly interface for browsing food items.
- Admin panel for managing menu items and orders.
- Image gallery for showcasing food items.
- Responsive design for mobile and desktop users.
- Easy checkout process.

## Installation 🛠️

To set up the project locally, follow these steps:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/soni-shashan/CHARUSAT-FOOD-CORNER.git
   cd CHARUSAT-FOOD-CORNER
  
2. **Install dependencies: Make sure you have Python and pip installed. Then run:**
  ```bash
  pip install -r requirements.txt
  ```

3. **Set up the database: Ensure you have a database set up (e.g., SQLite, PostgreSQL) and configure the connection in your settings.**
4. **Run the application:**
   ```bash
   python app.py

## Usage 🚀
Once the application is running, you can access it via your web browser at `http://localhost:5000`.

**Example Usage**

- Browse the menu to view available food items.
- Add items to your cart and proceed to checkout.
- Admin users can log in to manage the menu and view orders.

## Configuration ⚙️

**You may need to configure certain settings in a credential.py file. Common configurations include:**
  ```python
  from firebase_admin import credentials
  import firebase_admin

  # Razorpay configuration
    RAZORPAY_KEY_ID = ""
    RAZORPAY_KEY_SECRET = ""
    
    # Google OAuth 2.0 configuration
    GOOGLE_CLIENT_ID = ''
    GOOGLE_CLIENT_SECRET = ''
    REDIRECT_URI = 'https://127.0.0.1:5000/callback' 
    
    
    # Firebase configuration
    cred = credentials.Certificate('./credentials.json')  # Path to your Firebase service account key
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://your-databse-default-rtdb.firebaseio.com/'  # Use Firestore URL if using Firestore
    })
  ```
