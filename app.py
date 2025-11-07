import os
import time
from flask import Flask, render_template, request, url_for
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pyttsx3 # Offline TTS engine

# --- Configuration ---
app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'static/audio'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
analyzer = SentimentIntensityAnalyzer()

# --- Core Logic Functions (Fulfilling Must-Haves 2, 3, 4) ---

def classify_emotion(text):
    """
    Analyze text and classify it into at least three distinct emotional categories.
    Uses VADER's compound score for Positive/Negative/Neutral classification.
    """
    vs = analyzer.polarity_scores(text)
    compound_score = vs['compound']

    if compound_score >= 0.2:
        return "Positive"  # Happy/Enthusiastic
    elif compound_score <= -0.2:
        return "Negative" # Frustrated/Serious
    else:
        return "Neutral"  # Calm/Informative

def map_emotion_to_params(emotion):
    """
    Programmatically alter at least two distinct vocal parameters (Rate and Volume).
    Varying Rate (words/min) and Volume (0.0–1.0) based on emotion.
    """
    if emotion == "Positive":
        # Enthusiastic: Faster rate, High volume
        return {"rate": 200, "volume": 1.0, "text_label": "Enthusiastic (+Fast Rate, High Volume)"}
    elif emotion == "Negative":
        # Serious/Calm: Slower rate, Lower volume (for patient, non-aggressive tone)
        return {"rate": 120, "volume": 0.75, "text_label": "Serious/Calm (-Slow Rate, Lower Volume)"}
    else:  # Neutral
        # Informative: Standard rate, Medium volume
        return {"rate": 150, "volume": 0.9, "text_label": "Neutral (Standard Rate, Medium Volume)"}

def generate_tts_file(text, rate, volume, filename):
    """
    Generate a playable audio file .
    """
    engine = pyttsx3.init()
    
    # Apply parameters
    engine.setProperty('rate', rate)
    engine.setProperty('volume', volume)

    voices = engine.getProperty('voices')
    try:
        # Use a stable voice
        engine.setProperty('voice', voices[0].id)
    except IndexError:
        pass

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    # Save to file (pyttsx3 defaults to WAV/AIFF which is fine for local playback)
    engine.save_to_file(text, file_path)
    engine.runAndWait() 
    
    return file_path

# --- Flask Routes ---

@app.route('/', methods=['GET', 'POST'])
def index():
    audio_url = None
    emotion_text = None
    
    if request.method == 'POST':
        # 1. Text Input (Must-Have 1)
        text_input = request.form.get('text_input', '').strip()
        
        if text_input:
            # 2. Emotion Detection
            emotion = classify_emotion(text_input)
            
            # 3. Vocal Parameter Modulation
            params = map_emotion_to_params(emotion)
            emotion_text = params['text_label']
            
            # Create a unique filename for the audio output (FIXED: use .wav extension)
            timestamp = int(time.time())
            # Ensure file is saved as .wav as pyttsx3 defaults to it anyway
            filename = f"output_{emotion.lower()}_{timestamp}.wav" 
            
            # 4. Audio Output
            try:
                generate_tts_file(
                    text=text_input, 
                    rate=params['rate'], 
                    volume=params['volume'], 
                    filename=filename
                )
                audio_url = url_for('static', filename=f'audio/{filename}')
            except Exception as e:
                print(f"TTS Error: {e}")
                emotion_text = f"Error generating audio: {e}"
                
    return render_template('index.html', audio_url=audio_url, emotion_text=emotion_text)

if __name__ == '__main__':
    # Default Flask port 5000 is used, consistent with instructions
    app.run(debug=True)