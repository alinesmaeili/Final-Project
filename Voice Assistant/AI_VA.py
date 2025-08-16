# -*- coding: utf-8 -*-
"""
This script implements a simple voice assistant named "Eureka".

The assistant is capable of performing a variety of tasks based on voice commands,
including:
- Greeting the user based on the time of day.
- Listening for and recognizing spoken commands in English.
- Searching for health-related topics using the MyHealthfinder API.
- Opening popular websites like Google and YouTube.
- Exiting the application gracefully.

It utilizes text-to-speech for vocal responses and speech recognition for
interpreting user input.
"""

# --- Third-Party Libraries ---
# pyttsx3 is used for text-to-speech (TTS) conversion.
import pyttsx3
# speech_recognition is used to capture microphone input and convert it to text.
import speech_recognition as sr
# requests is used to make HTTP requests to external APIs (e.g., MyHealthfinder).
import requests

# --- Standard Python Libraries ---
# datetime is used to determine the current time for personalized greetings.
import datetime
# webbrowser is used to open web pages in the user's default browser.
import webbrowser


# --- Initialization of the Text-to-Speech (TTS) Engine ---
# This section sets up the voice for the assistant. 'sapi5' is the Microsoft
# Speech API, commonly used on Windows. The script selects the first available
# voice.
engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
if voices:
    engine.setProperty('voice', voices[0].id)
else:
    # Handle the case where no TTS voices are found on the system.
    print("No voices available for text-to-speech.")
    exit(1)


def speak(audio: str):
    """
    Converts a given text string into speech and speaks it out loud.

    This function uses the initialized pyttsx3 engine to vocalize the provided
    text, blocking execution until the speech is complete.

    Args:
        audio: The text string to be spoken by the assistant.
    """
    engine.say(audio)
    engine.runAndWait()


def wishMe():
    """
    Provides a greeting to the user based on the current time of day.

    It also introduces the assistant and gives the user a brief overview of the
    available commands to get started.
    """
    hour = int(datetime.datetime.now().hour)
    if 0 <= hour < 12:
        speak("Good Morning!")
    elif 12 <= hour < 18:
        speak("Good Afternoon!")
    else:
        speak("Good Evening!")
    speak("I am Eureka, your voice assistant. Tell me what you want to search or do. You can say 'search', 'open YouTube', 'open Google', or 'exit'.")


def takeCommand() -> str:
    """
    Listens for a user's voice command and converts it into a text string.

    This function uses the microphone to capture audio input and sends it to the
    Google Speech Recognition service for transcription. It includes error handling
    for unrecognized speech and network issues.

    Returns:
        The transcribed text of the user's command as a string, or "None" if
        the command could not be recognized or if an error occurred.
    """
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        # A longer pause threshold allows the user more time to pause between words.
        r.pause_threshold = 2
        audio = r.listen(source)

    try:
        print("Recognizing...")
        # Use Google's speech recognition service to convert audio to text.
        query = r.recognize_google(audio, language='en-in')
        print(f"User said: {query}\n")
    except sr.UnknownValueError:
        # This error occurs if the speech recognizer cannot understand the audio.
        print("Please say that again...")
        speak("Please say that again...")
        return "None"
    except sr.RequestError:
        # This error occurs if there's a problem with the network or the API service.
        print("Network error: Could not connect to Google Speech Recognition service.")
        speak("Network error. Please check your internet connection.")
        return "None"
    return query


def process_command(query: str) -> bool:
    """
    Parses the user's command and executes the corresponding action.

    This is the main logic hub of the assistant. It checks the transcribed query
    for keywords and triggers the appropriate function, such as performing a web
    search, opening a website, or exiting the program.

    Args:
        query: The string command received from the user.

    Returns:
        False if the user has requested to exit, True otherwise.
    """
    query = query.lower()  # Normalize the query to lowercase for easier matching.

    if 'search' in query:
        speak('Searching in MyHealthfinder...')
        # Isolate the search term by removing the "search" keyword.
        query = query.replace("search", "").strip()
        if not query:
            speak("Please provide a search term.")
            return True
        try:
            # Construct and send an API request to the MyHealthfinder service.
            url = f"https://health.gov/myhealthfinder/api/v3/topicsearch.json?Keyword={query}"
            response = requests.get(url)
            response.raise_for_status()  # This will raise an error for bad responses (4xx or 5xx).
            data = response.json()

            # Safely parse the JSON response to find the relevant information.
            if data.get('Result', {}).get('Resources', {}).get('Resource'):
                result = data['Result']['Resources']['Resource'][0]  # Get the first result.
                title = result.get('Title', 'No title found')
                # Get a snippet of the content to read back to the user.
                content_snippet = result.get('Sections', [{}])[0].get('Content', 'No content found')[:200]
                
                speak(f"According to MyHealthfinder, on the topic of {title}")
                print(f"Title: {title}\nContent: {content_snippet}")
                speak(content_snippet)
            else:
                speak("No results were found for your search.")
        except requests.exceptions.RequestException as e:
            # Handle network or API errors during the search.
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
        return False  # Signal to the main loop to terminate.

    else:
        speak("Command not recognized. Please try again.")
    
    return True  # Signal to continue the loop.


if __name__ == "__main__":
    # This is the main entry point of the script.
    
    # Greet the user and provide initial instructions.
    wishMe()
    
    # Start the main loop to continuously listen for and process commands.
    while True:
        query = takeCommand()
        # If no command was recognized, loop again.
        if query == "None":
            continue
        # Process the command and check if it's time to exit.
        if not process_command(query):
            break
