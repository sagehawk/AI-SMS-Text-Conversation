import openai
import os
import google.oauth2.service_account
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import google.auth
from google.auth.transport import requests
from datetime import datetime
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from twilio.base.exceptions import TwilioRestException
from dateutil.parser import parse
import dateutil.parser as parser
import json

OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"

TWILIO_ACCOUNT_SID = "YOUR_TWILIO_ACCOUNT_SID"
TWILIO_AUTH_TOKEN = "YOUR_TWILIO_AUTH_TOKEN"
TWILIO_PHONE_NUMBER = "YOUR_TWILIO_PHONE_NUMBER"

app = Flask(__name__)

sessions = {}

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Create dictionary for each placeholder
bot_name = "Ava"
school_name = "Dojo School"
coach_phone_number = "+12345678910"
website = "yourschool.com"
location = "National Karate & Martial Arts"
#appointment_confirmation = "Your class has been scheduled for "
school_programs = ["Tiny Warriors (ages 4-6), Little Warriors Karate (ages 7-10), Junior Warriors (ages 11-14), Warriors Karate (ages 7-14), Beginners Karate (15+), Advanced Karate,Women's Karate"]
program_schedules = {
  "Tiny Warriors (Ages 4 - 6)": ["Monday 4:30PM", "Monday 5:15PM", "Tuesday 12:00PM", "Tuesday 4:30PM", "Tuesday 6:15PM", "Wednesday 4:30PM", "Wednesday 5:15PM", "Thursday 12:00PM", "Thursday 4:30PM", "Thursday 6:15PM", "Friday 4:30PM", "Saturday 10:50AM"],
  "Little Warriors Karate (Ages 7 - 10)": ["Tuesday 4:30PM", "Thursday 4:30PM"],
  "Junior Warriors (Ages 11 - 14)": ["Monday 6:10PM", "Tuesday 6:10PM", "Wednesday 6:10PM", "Thursday 6:10PM", "Friday 6:10PM", "Saturday 10:00AM"],
  "Warriors Karate (Ages 7 - 14)": ["Monday 7:00PM", "Tuesday 7:00PM", "Wednesday 7:00PM", "Thursday 7:00PM", "Friday 7:00PM", "Saturday 9:00AM"],
  "Beginners Karate (Ages 15+)": ["Monday 7:00PM", "Tuesday 7:00PM", "Wednesday 7:00PM", "Thursday 7:00PM", "Friday 7:00PM", "Saturday 11:00AM"],
  "Women's Karate": ["Friday 5:30PM", "Saturday 8:00AM"]
}
pricing = "The basic membership is $179 per month, or I can choose a three month membership for $597 (paid in full). Both memberships offer unlimited classes and include a uniform as a gift for joining us."
objection_price_issue = "If the price is an issue for me or if I ask for any special requests like trial extensions or lower price, you can tell me that I may be able to work something out with your manager, be sure to give {coach_name} and tell me that I can call the coach at {coach_phone_number} {"
objection_school_uniqueness = "If I ask how your school is different from other schools you can tell me that {school_name} is dedicated to helping me or my child reach our full potential, achieve my goals, and improve my physical and mental well-being through martial arts training. No matter what my goals or current situation, you are here to help me learn the skills I need to feel confident and strong in my everyday life."
special_offer = "As you may know, we're excited to offer you a special deal to help you get started on your martial arts journey. For a limited time, we're offering a first class free, complete with a loaner karate uniform for you to wear during the class. This is a great opportunity for you to try out our program, meet our instructors, and see if martial arts is the right fit for you. To take advantage of this offer, I can help you schedule your first class right now. We have a variety of classes available, which one would you like to schedule?"

@app.route("/handlecall", methods=["POST"])
def handle_call():
    response = VoiceResponse()
    response.say("")
    response.hangup()

    # Get the caller's phone number from the incoming request
    caller = request.form["From"]

    # Send an SMS message to the caller with a follow-up message
    message = client.messages.create(
      body="Hi there! Thank you for reaching out to {school_name}. If you're interested in learning {martial_art_type}, please don't hesitate to call us back during our open hours at [School Phone Number] or reply to this text. You'll be speaking with our AI assistant, {bot_name}, who can help answer any questions you may have and assist you in getting started on your martial arts journey. We hope to hear from you soon!",
      from_=TWILIO_PHONE_NUMBER,
      to=caller
    )
    print(f"SMS message sent to {caller}")
    return str(response)

@app.route("/sms", methods=["POST"])
def sms():
    # Get the message from the incoming text
    message = request.form["Body"]
    sender = request.form["From"]
    
    if sender not in sessions:
      # If it's a new session, create a new dictionary to store the session information
      sessions[sender] = {
        "prev_messages": [],
        "user_data": {},
        "conversation_history": ""
    }
    
    # Get the session information for the user
    session_info = sessions[sender]
    prev_messages = session_info["prev_messages"]
    user_data = session_info["user_data"]
    conversation_history = session_info["conversation_history"]
    
    #Save the current message in the session
    last_message = message
    
    #Update the conversation history with the latest message
    conversation_history += message + " "
    session_info["conversation_history"] = conversation_history

    #Update last message (new)
    session_info["conversation_history"] += last_message + " "

    # Get the previous messages from the session
    prev_messages = [message]

    openai.api_key = OPENAI_API_KEY
    response = openai.Completion.create(
      engine="text-davinci-003",
      prompt=f"You are {bot_name}, the appointment setter for {school_name}. Firstly, If you haven't build rapport with me yet, first Build rapport with me by greeting me in a friendly and professional manner. Secondly, if you don't know my needs or interest yet, try to understand my needs and interests in martial arts and how {school_name} can meet those needs. Thirdly, if you haven't provided me the school's programs, provide clear and accurate information about the school's programs: {school_programs}, schedules {program_schedules}, and pricing {pricing}. Fourthly, If you haven't addressed any of my concerns or objections, address any concerns or objections I may have. {objection_price_issue} {objection_school_uniqueness}. Fifthy, if you haven't set an appointment for me, bring the conversation to a close by scheduling an appointment for me to visit the school based on the schedule of the program that fits me and come for a one day free class, include in your words: {special_offer} Sixthly, if you haven't confirmed the appointment details, Confirm the appointment details with me including the location, {location}. Lastly, if you have complete all of the previous objectives, feel free to answer any questions I may have. It's also important to pay attention to your tone and the way you phrase your questions, as you want to come across as friendly and helpful, rather than pushy or aggressive. Here's the message you already gave a reply to: {session_info['conversation_history']} | Reply to this text -> Me: {last_message} | You: ",
      max_tokens=100,
      temperature=0.5,
      top_p=1,
      frequency_penalty=2,
      presence_penalty=2
    )

    response_text = response["choices"][0]["text"]

    # Update the list of previous messages in the session
    sessions[sender]["prev_messages"] = prev_messages

    #Update the session information
    session_info["user_data"] = user_data
    session_info["conversation_history"] = conversation_history

    # Create a Twilio response object
    twiml = MessagingResponse()
    twiml.message(response_text)
    print(twiml)
    # Return the response
    return str(twiml)

if __name__ == "__main__":
  app.run(port=5000)
