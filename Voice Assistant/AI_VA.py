import pyttsx3  # pip install pyttsx3
import speech_recognition as sr  # pip install speech_recognition
import datetime
import webbrowser
import requests  # pip install requests

# Initialize text-to-speech engine
engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
if voices:
    engine.setProperty('voice', voices[0].id)
else:
    print("No voices available for text-to-speech.")
    exit(1)

def speak(audio):
    engine.say(audio)
    engine.runAndWait()

def wishMe():
    hour = int(datetime.datetime.now().hour)
    if 0 <= hour < 12:
        speak("Good Morning!")
    elif 12 <= hour < 18:
        speak("Good Afternoon!")
    else:
        speak("Good Evening!")
    speak("I am Eureka, your voice assistant. Tell me what you want to search or do. You can say 'search', 'open YouTube', 'open Google', or 'exit'.")

def takeCommand():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        r.pause_threshold = 2  # Increased for better input capture
        audio = r.listen(source)
    try:
        print("Recognizing...")
        query = r.recognize_google(audio, language='en-in')
        print(f"User said: {query}\n")
    except sr.UnknownValueError:
        print("Please say that again...")
        speak("Please say that again...")
        return "None"
    except sr.RequestError:
        print("Network error: Could not connect to Google Speech Recognition service.")
        speak("Network error. Please check your internet connection.")
        return "None"
    return query

def process_command(query):
    query = query.lower()
    if 'search' in query:
        speak('Searching in MyHealthfinder...')
        query = query.replace("search", "").strip()
        if not query:
            speak("Please provide a search term.")
            return True
        try:
            # Request to MyHealthfinder API for topic search
            url = f"https://health.gov/myhealthfinder/api/v3/topicsearch.json?Keyword={query}"
            response = requests.get(url)
            response.raise_for_status()  # Check for HTTP errors
            data = response.json()

            # Extract information from JSON response
            if data.get('Result', {}).get('Resources', {}).get('Resource'):
                # Get the first result
                result = data['Result']['Resources']['Resource'][0]
                title = result.get('Title', 'No title')
                content = result.get('Sections', [{}])[0].get('Content', 'No content')[:200]  # Limit to 200 characters
                speak(f"According to MyHealthfinder, about {title}")
                print(f"Title: {title}\nContent: {content}")
                speak(content)
            else:
                speak("No results found.")
        except requests.exceptions.RequestException as e:
            print(f"Search error: {e}")
            speak("There was an issue with the search. Please try again.")
    elif 'open youtube' in query:
        webbrowser.open("https://youtube.com")
        speak("Opening YouTube")
    elif 'open google' in query:
        webbrowser.open("https://google.com")
        speak("Opening Google")
    elif 'exit' in query or 'stop' in query:
        speak("Goodbye!")
        return False
    else:
        speak("Command not recognized. Please try again.")
    return True

if __name__ == "__main__":
    wishMe()
    while True:
        query = takeCommand()
        if query == "None":
            continue
        if not process_command(query):
            break