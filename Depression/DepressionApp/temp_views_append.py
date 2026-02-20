
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
            1. Validate their feelings (make them feel heard and safe).
            2. Gently guide them from sadness to stability, then to motivation.
            3. Use the "Emotional Recovery" flow:
               - Phase 1: Gentle Check-in & Validation ("It makes sense you feel that way").
               - Phase 2: Shift to Motivation (Reframe negative thoughts, highlight resilience).
               - Phase 3: Emotional Strengthening (Suggest small goals, gratitude, hope).
            
            Tone: Warm, gentle, understanding, encouraging, non-judgmental. NOT robotic or overly clinical.
            Safety: Do NOT provide medical diagnoses. If self-harm is mentioned, gently suggest professional help.
            """
        else:
            system_prompt = """
            You are Dr. MindScan, a supportive and positive mental wellness coach. 
            The user seems to be in a good or neutral mood.
            Encourage them to maintain their positive state, spread happiness, and practice self-care.
            """

        try:
            # GROQ API CALL
            api_key = os.environ.get("GROQ_API_KEY")
            if not api_key:
                 # Fallback if key missing
                 response_text = "I'm sorry, my connection to the brain server (API Key) is missing. Please ask the admin to configure it."
            else:
                client = Groq(api_key=api_key)
                
                # Construct messages for API
                messages = [{'role': 'system', 'content': system_prompt}]
                # Add simplified history (last 10 messages to save context/tokens)
                for msg in history[-10:]:
                    messages.append({'role': msg['role'], 'content': msg['content']})
                
                chat_completion = client.chat.completions.create(
                    messages=messages,
                    model="llama3-8b-8192", # Or mixed-7b, whatever is standard for Groq free tier
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
