# MindScan: Depression Detection Using Facial Expressions

MindScan is an AI-powered mental wellness application designed to help identify potential signs of depression through facial expression analysis. It provides users with a safe space to track their emotional journey, share experiences, and receive AI-driven support.

## 🌟 Key Features

- **Facial Expression Analysis**: Uses DeepFace to analyze uploaded photos for dominant emotions associated with depression.
- **AI Psychiatrist (Dr. MindScan)**: An intelligent chatbot powered by Groq API that provides empathetic support and guidance.
- **Personalized Motivation**: Receives curated motivational messages and suggestions based on analysis results.
- **Community Stories**: Share your own success stories and browse experiences from others to find hope and inspiration.
- **User Profile**: A central hub to view your analysis history and manage your shared content.
- **Secure Data**: Personal password protection and user-specific content management.

## 🛠️ Technology Stack

- **Backend**: Python / Django
- **Database**: SQLite3
- **AI/ML**: 
  - DeepFace (Facial Recognition)
  - Groq API (NLP/Chatbot)
  - Scikit-Learn (SVM Sentiment Analysis)
- **Frontend**: HTML5, Vanilla CSS3 (Modern Glassmorphism UI), Javascript

## 🚀 Setup Instructions

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd "DEPRESSION DETECTION USING ECG"
   ```

2. **Install Dependencies**:
   ```bash
   pip install django groq deepface joblib numpy matplotlib pillow python-dotenv
   ```

3. **Configure Environment**:
   Create a `.env` file in the root directory and add your API keys:
   ```env
   GROQ_API_KEY=your_actual_key_here
   ```

4. **Run the Application**:
   ```bash
   cd Depression
   python manage.py runserver
   ```

## 🔒 Security & Privacy
Analysis is performed using state-of-the-art AI. While MindScan offers support and detection, it is NOT a replacement for professional medical diagnosis. We encourage users to seek help from certified professionals for mental health concerns.
