from django.shortcuts import render
from django.template import RequestContext
from django.contrib import messages
import sqlite3
from django.http import HttpResponse
from django.conf import settings
from django.core.files.storage import FileSystemStorage
import datetime
import joblib
import os
import PIL.Image
import pytesseract
# DeepFace is imported lazily inside analyzeImageForDepression() to avoid slow startup
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import re
import numpy as np
from groq import Groq
from django.http import JsonResponse
import json
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'db.sqlite3')

svm_classifier = joblib.load(os.path.join(BASE_DIR, 'svmClassifier.pkl'))

def get_db_connection():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    """Create tables if they don't exist."""
    con = get_db_connection()
    cur = con.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        contact_no TEXT,
        email TEXT,
        address TEXT
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS postdata (
        username TEXT,
        post_data TEXT,
        post_time TEXT,
        depression TEXT,
        motivate_post TEXT
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS experience_posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        title TEXT,
        experience TEXT,
        created_at TEXT,
        likes INTEGER DEFAULT 0
    )''')
    con.commit()
    con.close()

# Initialize database tables on startup
init_db()

def index(request):
    if request.method == 'GET':
       return render(request, 'index.html', {})

def UploadPost(request):
    if request.method == 'GET':
       return render(request, 'UploadPost.html', {})

def Register(request):
    if request.method == 'GET':
       return render(request, 'Register.html', {})

def Admin(request):
    if request.method == 'GET':
       return render(request, 'Admin.html', {})

def Login(request):
    if request.method == 'GET':
       return render(request, 'Login.html', {})

def SendMotivatedPost(request):
    if request.method == 'GET':
       return render(request, 'SendMotivatedPost.html', {})


def predict(textdata,classifier):
   text_processed = textdata
   X =  [text_processed]
   sentiment = classifier.predict(X)
   return (sentiment[0])


def predictSentiment(textdata):
    result = predict(textdata, svm_classifier)
    predicts = ""
    if result == 0:
      predicts = "Negative"
    if result == 1:
      predicts = "Positive"
    return predicts


def analyzeImageForDepression(image_path):
    """Analyze facial expression in image using DeepFace.
    Returns 'Negative' (depressed) or 'Positive' (not depressed).
    """
    from deepface import DeepFace  # Lazy import to avoid slow server startup
    
    # ---------------------------------------------------------
    # TODO: If a custom .h5 model is provided later, replace this 
    # logic with model.load_model() and prediction code.
    # ---------------------------------------------------------

    try:
        results = DeepFace.analyze(
            img_path=image_path,
            actions=['emotion'],
            enforce_detection=False
        )
        # DeepFace returns a list of dicts (one per face)
        if isinstance(results, list):
            result = results[0]
        else:
            result = results

        emotions = result.get('emotion', {})
        dominant = result.get('dominant_emotion', 'neutral')
        print(f"[DeepFace] Full emotion dict: {emotions}")
        print(f"[DeepFace] Dominant emotion: {dominant}")

        # Emotions indicating depression/negative state
        negative_emotions = ['sad', 'angry', 'fear', 'disgust']
        # 'neutral' is tricky. A flat affect can be depression, but also just a neutral face.
        # We will track it separately but NOT count it as positive to avoid hiding depression.
        positive_emotions = ['happy', 'surprise'] 

        # Calculate weighted score
        negative_score = sum(emotions.get(e, 0) for e in negative_emotions)
        positive_score = sum(emotions.get(e, 0) for e in positive_emotions)
        neutral_score = emotions.get('neutral', 0)

        print(f"[DeepFace] Scores - Neg: {negative_score:.2f}, Pos: {positive_score:.2f}, Neu: {neutral_score:.2f}")

        # LOGIC ADJUSTMENT:
        # 1. If happy is dominant or very strong, it's Positive.
        # 2. If negative score outweighs positive score (ignoring neutral), it's Negative.
        # 3. If neutral is dominant: 
        #    - In a clinical depression context, persistent neutral might be flagged.
        #    - But for general photo upload, we usually default to Positive unless there is distinct negativity.
        
        # FIX for "Happy predicted as Depressed":
        # Ensure 'happy' carries enough weight. 
        if dominant == 'happy' or positive_score > 40: # If 40% happy, likely happy
             print("[Logic] Dominant happy or >40% happy -> Positive")
             return "Positive"

        # FIX for "Depressed predicted as Happy":
        # Often occurs if 'neutral' was counting as positive, drowning out 'sad'.
        # We removed 'neutral' from positive_score above.
        if negative_score > positive_score:
            print("[Logic] Negative score > Positive score -> Negative")
            return "Negative"
        
        # Fallback for dominant neutral or low intensity
        if dominant == 'neutral':
             # If there is SOME negative signal (e.g. sad > happy), lean Negative?
             # For now, keep as Positive to avoid false alarms on ID photos etc.
             # UNLESS the user explicitly wants 'neutral' -> 'Depressed'.
             # Given "Depressed predicted as Happy" complaint, let's be stricter.
             if emotions.get('sad', 0) > emotions.get('happy', 0):
                 print("[Logic] Neutral dominant but Sad > Happy -> Negative")
                 return "Negative"
             
             print("[Logic] Default Neutral -> Positive")
             return "Positive"

        print("[Logic] Default Fallback -> Positive")
        return "Positive"

    except Exception as e:
        print(f"DeepFace analysis error: {e}")
        return "Positive"

def SendMotivatedPostData(request):
     if request.method == 'POST':
        username = request.POST.get('t1', False)
        time = request.POST.get('t2', False) 
        text = request.POST.get('t3', False) 
        con = get_db_connection()
        cur = con.cursor()
        cur.execute("UPDATE postdata SET motivate_post=? WHERE username=? AND post_time=? AND motivate_post='Pending'",
                    (text, username, time))
        con.commit()
        print(cur.rowcount, "Record Updated")
        con.close()
        context= {'data':'Your motivated text sent to user '+username}
        return render(request, 'SendMotivatedPost.html', context)
        
def UploadPostData(request):
     if request.method == 'POST' and request.FILES['t1']:
        output = ''
        myfile = request.FILES['t1']
        # Save uploaded file to MEDIA_ROOT
        media_root = os.path.join(BASE_DIR, 'media')
        if not os.path.exists(media_root):
            os.makedirs(media_root)
        fs = FileSystemStorage(location=media_root)
        original_name = str(myfile)
        
        # Strictly allow only images
        if not original_name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
           context_data = {'data': 'Invalid file type. Please upload an image file.', 'sentiment': 'None'}
           return render(request, 'UploadPost.html', context_data)

        save_name = 'img.jpg' 
        # Delete old file if exists to avoid Django appending suffix
        saved_path = os.path.join(media_root, save_name)
        if os.path.exists(saved_path):
            os.remove(saved_path)
            
        filename = fs.save(save_name, myfile)
        full_path = os.path.join(media_root, filename)
        
        # Read logged-in user from session file
        user = ''
        session_path = os.path.join(BASE_DIR, "session.txt")
        if os.path.exists(session_path):
            with open(session_path, "r") as file:
              for line in file:
                 user = line.strip('\n')
        now = datetime.datetime.now()
        option = 'Pending'
        current_time = now.strftime("%Y-%m-%d %H:%M:%S")
        
        # Process image
        sentiment = analyzeImageForDepression(full_path)
        output = 'image analyzed for facial expression'
        
        con = get_db_connection()
        cur = con.cursor()
        cur.execute("INSERT INTO postdata(username,post_data,post_time,depression,motivate_post) VALUES(?,?,?,?,?)",
                    (user, output, current_time, sentiment, option))
        con.commit()
        print(cur.rowcount, "Record Inserted")
        con.close()
        
        # Store sentiment in session for Chatbot "Psychiatrist Mode"
        request.session['detected_sentiment'] = sentiment
        # Reset chat history on new upload to start fresh context
        if 'chat_history' in request.session:
            del request.session['chat_history']
        
        context_data = {'data': 'Detected Depression From Uploaded Image : ' + sentiment, 'sentiment': sentiment}
        
        if sentiment == 'Negative':
            import random
            supportive_lines = [
                "It’s not whether you get knocked down; it’s whether you get up.",
                "Champions keep playing until they get it right.",
                "The more difficult the victory, the greater the happiness in winning.",
                "You are never a loser until you quit trying.",
                "Pain is temporary. Greatness lasts forever.",
                "Your current situation is not your final destination. Keep playing!",
            ]
            selected_lines = random.sample(supportive_lines, k=2)
            context_data['support_messages'] = selected_lines
            context_data['suggestion'] = "Suggestion: Take a deep breath, listen to your favorite song, or go for a short walk. You've got this!"
        else:
            context_data['suggestion'] = "Keep making others happy and maintain that beautiful smile!"

        return render(request, 'UploadPost.html', context_data)
        

def ViewUsers(request):
    if request.method == 'GET':
       strdata = '<table><thead><tr><th>Username</th><th>Password</th><th>Contact No</th><th>Email ID</th><th>Address</th></tr></thead><tbody>'
       con = get_db_connection()
       cur = con.cursor()
       cur.execute("SELECT * FROM users")
       rows = cur.fetchall()
       for row in rows: 
          strdata+='<tr><td>'+str(row[0])+'</td><td>'+str(row[1])+'</td><td>'+str(row[2])+'</td><td>'+str(row[3])+'</td><td>'+str(row[4])+'</td></tr>'
       con.close()
    strdata += '</tbody></table>'
    context= {'data':strdata}
    return render(request, 'ViewUsers.html', context)

def ViewPosts(request):
    if request.method == 'GET':
       positive = 0
       negative = 0        
       strdata = '<table><thead><tr><th>Username</th><th>Post Data</th><th>Post Time</th><th>Depression</th><th>Motivated Post</th></tr></thead><tbody>'
       con = get_db_connection()
       cur = con.cursor()
       cur.execute("SELECT * FROM postdata")
       rows = cur.fetchall()
       for row in rows: 
          if row[3] == 'Negative':
             negative = negative + 1
          else:
             positive = positive + 1
          strdata+='<tr><td>'+str(row[0])+'</td><td>'+str(row[1])+'</td><td>'+str(row[2])+'</td><td>'+str(row[3])+'</td><td>'+str(row[4])+'</td></tr>'
       con.close()
    height = [positive,negative]
    bars = ('Depression Posts', 'Non Depression Post')
    y_pos = np.arange(len(bars))
    plt.figure()
    plt.bar(y_pos, height)
    plt.xticks(y_pos, bars)
    chart_path = os.path.join(BASE_DIR, 'DepressionApp', 'static', 'images', 'chart.png')
    plt.savefig(chart_path)
    plt.close()
    strdata += '</tbody></table>'
    context= {'data':strdata}
    return render(request, 'ViewPosts.html', context)

def MotivatedText(request):
    # Path to the motivation images directory
    images_dir = os.path.join(BASE_DIR, 'DepressionApp', 'static', 'motivation_images')
    print(f"Scanning images in: {images_dir}")
    
    image_files = []
    try:
        if os.path.exists(images_dir):
            for filename in os.listdir(images_dir):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                    image_files.append(filename)
        else:
             print(f"Directory not found: {images_dir}")
    except Exception as e:
        print(f"Error listing images: {e}")
       
    context = {'images': image_files}
    return render(request, 'MotivatedText.html', context)

def ViewMotivatedPost(request):
    if request.method == 'GET':
       strdata = '<table class="table table-striped"><thead><tr class="thead-dark"><th>Username</th><th>Post Data</th><th>Post Time</th><th>Depression</th><th>Motivated Post</th></tr></thead><tbody>'
       con = get_db_connection()
       cur = con.cursor()
       cur.execute("SELECT * FROM postdata")
       rows = cur.fetchall()
       for row in rows: 
          if row[4] != 'Pending':
             strdata+='<tr><td>'+str(row[0])+'</td><td>'+str(row[1])+'</td><td>'+str(row[2])+'</td><td>'+str(row[3])+'</td><td>'+str(row[4])+'</td></tr>'
       con.close()
    strdata += '</tbody></table>'
    context= {'data':strdata}
    return render(request, 'ViewMotivatedPost.html', context)

def SearchFriends(request):
    if request.method == 'GET':
       user = ''
       session_path = os.path.join(BASE_DIR, "session.txt")
       if os.path.exists(session_path):
           with open(session_path, "r") as file:
              for line in file:
                 user = line.strip('\n')
       strdata = '<table class="table table-striped"><thead><tr class="thead-dark"><th>User ID / Name</th></tr></thead><tbody>'
       con = get_db_connection()
       cur = con.cursor()
       cur.execute("SELECT * FROM users")
       rows = cur.fetchall()
       for row in rows: 
          if row[0] != user:
             strdata+='<tr><td>'+str(row[0])+'</td></tr>'
       con.close()
    strdata += '</tbody></table>'
    context= {'data':strdata}
    return render(request, 'SearchFriends.html', context)


def UserLogin(request):
    if request.method == 'POST':
      username = request.POST.get('t1', False)
      password = request.POST.get('t2', False)
      index = 0
      con = get_db_connection()
      cur = con.cursor()
      cur.execute("SELECT * FROM users")
      rows = cur.fetchall()
      for row in rows: 
         if row[0] == username and password == row[1]:
            index = 1
            break		
      con.close()
      if index == 1:
       session_path = os.path.join(BASE_DIR, "session.txt")
       file = open(session_path,'w')
       file.write(username)
       file.close()   
       context= {'data':'welcome '+username}
       return render(request, 'UserScreen.html', context)
      else:
       context= {'data':'login failed'}
       return render(request, 'Login.html', context)

def Signup(request):
    if request.method == 'POST':
      username = request.POST.get('t1', False)
      password = request.POST.get('t2', False)
      contact = request.POST.get('t3', False)
      email = request.POST.get('t4', False)
      address = request.POST.get('t5', False)
      con = get_db_connection()
      cur = con.cursor()
      cur.execute("INSERT INTO users(username,password,contact_no,email,address) VALUES(?,?,?,?,?)",
                  (username, password, contact, email, address))
      con.commit()
      print(cur.rowcount, "Record Inserted")
      if cur.rowcount == 1:
       con.close()
       context= {'data':'Signup Process Completed'}
       return render(request, 'Register.html', context)
      else:
       con.close()
       context= {'data':'Error in signup process'}
       return render(request, 'Register.html', context)


def AdminLogin(request):
    if request.method == 'POST':
      username = request.POST.get('t1', False)
      password = request.POST.get('t2', False)
      if username == 'admin' and password == 'admin':
       context= {'data':'welcome '+username}
       return render(request, 'AdminScreen.html', context)
      else:
       context= {'data':'login failed'}
       return render(request, 'Admin.html', context)

def Chatbot(request):
    if request.method == 'GET':
        # Initialize chat history if not present
        if 'chat_history' not in request.session:
            request.session['chat_history'] = []
            
            # Initial greeting based on detected sentiment
            sentiment = request.session.get('detected_sentiment', 'Neutral')
            if sentiment == 'Negative':
                initial_msg = "Hello. I noticed from your recent upload that you might be feeling down. I'm here as a safe space for you. How are you feeling right now?"
            else:
                initial_msg = "Hello! I'm Dr. MindScan. How can I help you today?"
            
            request.session['chat_history'].append({'role': 'assistant', 'content': initial_msg})
            request.session.modified = True
            
        return render(request, 'Chatbot.html', {'chat_history': request.session['chat_history']})

def ChatBotResponse(request):
    if request.method == 'POST':
        user_message = request.POST.get('message')
        if not user_message:
            return JsonResponse({'response': "Please say something."})
        
        # Get history
        history = request.session.get('chat_history', [])
        history.append({'role': 'user', 'content': user_message})
        
        # Determine Persona based on detected sentiment
        sentiment = request.session.get('detected_sentiment', 'Neutral')
        
        system_prompt = "You are a helpful AI assistant."
        if sentiment == 'Negative':
            system_prompt = """
            You are a caring, empathetic psychiatrist and mental health guide named Dr. MindScan.
            The user has been detected as potentially depressed or emotionally distressed.
            
            Your Goals:
            1. Validate their feelings briefly.
            2. Gently guide them towards motivation and emotional strengthening.
            
            Guidelines:
            - Keep responses CONCISE, CLEAR, and IMPACTFUL (approx. 2-3 short paragraphs).
            - Do not overwhelm the user with long text.
            - Focus on simple, comforting words.
            
            Tone: Warm, gentle, encouraging, non-judgmental.
            Safety: Do NOT provide medical diagnoses. If self-harm is mentioned, gently suggest professional help.
            """
        else:
            system_prompt = """
            You are Dr. MindScan, a supportive and positive mental wellness coach. 
            The user seems to be in a good or neutral mood.
            
            Guidelines:
            - Encourage them to maintain their positive state and spread happiness.
            - Keep responses short, sweet, and motivating (max 2 paragraphs).
            """

        try:
            # GROQ API CALL
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                 # Fallback if key missing
                 response_text = "I'm sorry, my connection to the brain server (API Key) is missing."
            else:
                client = Groq(api_key=api_key)
                
                # Construct messages for API
                messages = [{'role': 'system', 'content': system_prompt}]
                # Add simplified history (last 10 messages to save context/tokens)
                for msg in history[-10:]:
                    messages.append({'role': msg['role'], 'content': msg['content']})
                
                chat_completion = client.chat.completions.create(
                    messages=messages,
                    model="llama-3.3-70b-versatile",
                )
                response_text = chat_completion.choices[0].message.content

        except Exception as e:
            print(f"Groq API Error: {e}")
            response_text = "I'm having trouble thinking right now. Please try again later."

        # Update history
        history.append({'role': 'assistant', 'content': response_text})
        request.session['chat_history'] = history
        request.session.modified = True
        
        return JsonResponse({'response': response_text})
    return JsonResponse({'error': 'Invalid request'}, status=400)


def ShareExperience(request):
    """Display form to share positive experience"""
    if request.method == 'GET':
        return render(request, 'ShareExperience.html', {})


def SaveExperience(request):
    """Save user's positive experience to database"""
    if request.method == 'POST':
        title = request.POST.get('experience_title', '').strip()
        experience = request.POST.get('experience_text', '').strip()
        
        # Validate input
        if not title or not experience:
            context = {'error': 'Please fill in both title and experience', 'data': 'Title and experience are required.'}
            return render(request, 'ShareExperience.html', context)
        
        # Get logged-in user from session
        user = ''
        session_path = os.path.join(BASE_DIR, "session.txt")
        if os.path.exists(session_path):
            with open(session_path, "r") as file:
                user = file.read().strip()
        
        if not user:
            context = {'error': 'User not logged in.'}
            return render(request, 'ShareExperience.html', context)
        
        # Save to database
        con = get_db_connection()
        cur = con.cursor()
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cur.execute(
            "INSERT INTO experience_posts (username, title, experience, created_at) VALUES (?, ?, ?, ?)",
            (user, title, experience, current_time)
        )
        con.commit()
        con.close()
        
        context = {'success': 'Your positive experience has been shared! Others will find it helpful.'}
        return render(request, 'ShareExperience.html', context)


def BrowseHelpfulExperiences(request):
    """Display all shared positive experiences for people seeking help"""
    if request.method == 'GET':
        # Get current user
        session_path = os.path.join(BASE_DIR, "session.txt")
        current_viewer = ""
        if os.path.exists(session_path):
            with open(session_path, "r") as file:
                current_viewer = file.read().strip()

        con = get_db_connection()
        cur = con.cursor()

        # Get all experiences ordered by creation date (newest first)
        cur.execute(
            "SELECT id, username, title, experience, created_at FROM experience_posts ORDER BY created_at DESC"
        )
        rows = cur.fetchall()
        con.close()
        
        experiences = []
        for row in rows:
            experiences.append({
                'id': row[0],
                'username': row[1],
                'title': row[2],
                'experience': row[3],
                'created_at': row[4]
            })
        
        context = {'experiences': experiences, 'current_viewer': current_viewer}
        return render(request, 'BrowseHelpfulExperiences.html', context)

def UserProfile(request):
    """View logged-in user's profile and post history"""
    session_path = os.path.join(BASE_DIR, "session.txt")
    user = ""
    if os.path.exists(session_path):
        with open(session_path, "r") as file:
            user = file.read().strip()
    
    if not user:
        return render(request, 'Login.html', {'data': 'Please login to view your profile'})

    con = get_db_connection()
    cur = con.cursor()
    
    # Get image posts
    cur.execute("SELECT rowid, post_data, post_time, depression FROM postdata WHERE username=?", (user,))
    image_posts = cur.fetchall()
    
    # Get experiences
    cur.execute("SELECT id, title, experience, created_at FROM experience_posts WHERE username=?", (user,))
    experience_posts = cur.fetchall()
    
    con.close()
    
    context = {
        'username': user,
        'image_posts': image_posts,
        'experience_posts': experience_posts
    }
    return render(request, 'UserProfile.html', context)

def DeletePost(request):
    """Delete an image post from postdata"""
    if request.method == 'POST':
        post_id = request.POST.get('post_id')
        session_path = os.path.join(BASE_DIR, "session.txt")
        user = ""
        if os.path.exists(session_path):
            with open(session_path, "r") as file:
                user = file.read().strip()
        
        con = get_db_connection()
        cur = con.cursor()
        # Ensure user owns the post
        cur.execute("DELETE FROM postdata WHERE rowid=? AND username=?", (post_id, user))
        con.commit()
        con.close()
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)

def DeleteExperience(request):
    """Delete a text experience from experience_posts"""
    if request.method == 'POST':
        exp_id = request.POST.get('exp_id')
        session_path = os.path.join(BASE_DIR, "session.txt")
        user = ""
        if os.path.exists(session_path):
            with open(session_path, "r") as file:
                user = file.read().strip()
        
        con = get_db_connection()
        cur = con.cursor()
        # Ensure user owns the experience
        cur.execute("DELETE FROM experience_posts WHERE id=? AND username=?", (exp_id, user))
        con.commit()
        con.close()
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)
