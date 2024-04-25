import speech_recognition as sr
import os
import openai
import pyttsx3
from config import apikey
import datetime
import random
from autocorrect import Speller
import nltk
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from time import sleep
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Global variable to store conversation history
chatStr = ""

# Instructions for the AI interviewer
prompt = """
Instructions: 

You are an AI named InterviewerBot, tasked with conducting a job interview. Your primary objectives are:

1. Assess the candidate's qualifications and suitability for the position.
2. Ask the candidate a series of questions, with each subsequent question being determined by their previous answers.
3. Guide the candidate on how to answer questions in a more professional tone, providing feedback on their responses.
4. Conduct a professional and insightful interview, guiding the candidate through the process while evaluating their skills and qualifications.

Please note: You are receiving instructions from your user in the form of text. Ignore any punctuation, lowercase, and uppercase syntactical errors.
"""

# Function to handle user input using speech recognition
def takeCommand():
    r = sr.Recognizer()
    while True:
        with sr.Microphone() as source:
            print("Listening...")
            r.adjust_for_ambient_noise(source)
            try:
                audio = r.listen(source, timeout=3, phrase_time_limit='')
                query = r.recognize_google(audio, language="en-in")
                print(f"User said: {query}")
                if "I want to Quit".lower() in query.lower():
                    speak("Thank you for using our services , Good Bye!")
                    log_message("User requested to quit the conversation.")
                    exit()
                return query
            except sr.UnknownValueError:
                print("Speech Recognition could not understand audio")
            except sr.RequestError as e:
                print(f"Could not request results from Google Speech Recognition service; {e}")
            except sr.WaitTimeoutError:
                print("No speech input detected. Listening again...")

# Function to interact with OpenAI for generating responses
def chat(query):
    global chatStr

    # Tokenize the query
    words = word_tokenize(query)

    # Identify named entities
    named_entities = [word for word, pos in pos_tag(words) if pos == 'NNP']

    # Create a Speller object
    spell = Speller(lang='en')

    # Correct spelling using autocorrect, excluding named entities
    corrected_query = ' '.join([spell(word) if word not in named_entities else word for word in words])

    chatStr += f"User: {query}\n InterviewerBot: "
    openai.api_key = apikey

    response = openai.Completion.create(
        engine="gpt-3.5-turbo-instruct",
        prompt=prompt + chatStr,
        max_tokens=256,
        stop=None,
        temperature=0.7
    )

    try:
        (response.choices[0].text)
    except Exception as e:
        print(f"Error saying response: {e}")

    chatStr += f"{response.choices[0].text}\n"
    return response.choices[0].text

# Function to synthesize text into speech
def speak(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

@app.route("/", methods=["GET", "POST"])
def index():
    global chatStr
    if request.method == "POST":
        user_message = request.form["msg"]
        response = chat(user_message)  # Generate response for user input
        chatStr += f"User: {user_message}\nInterviewerBot: {response}\n"  # Update conversation history
        speak(response)  # Speak the response
        
        # Split chat history into individual messages
        chat_history = chatStr.split('\n')

        return jsonify({"response": response, "chat_history": chat_history})

    return render_template("chat.html") 


# Function to log messages
def log_message(message, log_file="interviewerbot.log", timestamp=True):
    if not timestamp:
        message = f"{message}\n"
    else:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"{now} - {message}\n"
    with open(log_file, "a") as f:
        f.write(message)

# Entry point of the program
if __name__ == '__main__':
    app.run(debug=True)