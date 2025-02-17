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