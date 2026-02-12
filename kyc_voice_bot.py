import speech_recognition as sr
import pyttsx3
import json
import re
from datetime import datetime
import time


class KYCVoiceBot:
    def __init__(self):
        """Initialize the voice bot with speech recognition and TTS engines."""
        self.recognizer = sr.Recognizer()
        
        # KYC data storage
        self.kyc_data = {
            "name": "",
            "phone": "",
            "pan": "",
            "consent": False,
            "timestamp": ""
        }
        
        # Maximum retry attempts
        self.max_retries = 2
        
        print("Voice bot initialized successfully")
    
    def speak(self, text):
        """Convert text to speech - creates fresh engine each time to avoid Windows bug."""
        print(f"\nBot: {text}")
        
        try:
            # Create a fresh engine for each speech
            engine = pyttsx3.init()
            engine.setProperty('rate', 150)
            engine.setProperty('volume', 0.9)
            engine.say(text)
            engine.runAndWait()
            engine.stop()
            del engine  # Clean up
            time.sleep(0.3)  # Small pause between speeches
        except Exception as e:
            print(f"TTS Error: {e}")
            print("(Please read the text above)")
    
    def listen(self):
        """Capture user speech and convert to text."""
        with sr.Microphone() as source:
            print("\n[LISTENING] (speak now)")
            # Adjust for ambient noise
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            
            try:
                audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=10)
                print("Processing...")
                text = self.recognizer.recognize_google(audio)
                print(f"You: {text}")
                return text.strip()
            except sr.WaitTimeoutError:
                print("No speech detected (timeout)")
                return None
            except sr.UnknownValueError:
                print("Could not understand audio")
                return None
            except sr.RequestError as e:
                print(f"Speech recognition error: {e}")
                return None
    
    def validate_name(self, name):
        """Validate name is non-empty and contains only letters and spaces."""
        if not name or len(name.strip()) < 2:
            return False
        # Checking if name contains at least some alphabetic characters
        if not re.search(r'[a-zA-Z]', name):
            return False
        return True
    
    def validate_phone(self, phone):
        """Validate phone number is exactly 10 digits."""
        # Remove spaces and common words
        phone_cleaned = re.sub(r'[^\d]', '', phone)
        return len(phone_cleaned) == 10 and phone_cleaned.isdigit()
    
    def validate_pan(self, pan):
        """Validate PAN is 10 alphanumeric characters (format: ABCDE1234F)."""
        # Remove spaces
        pan_cleaned = pan.replace(" ", "").upper()
        # PAN format: 5 letters, 4 digits, 1 letter
        pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]$'
        return len(pan_cleaned) == 10 and bool(re.match(pattern, pan_cleaned))
    
    def extract_phone(self, text):
        """Extract 10-digit phone number from text."""
        digits = re.sub(r'[^\d]', '', text)
        if len(digits) >= 10:
            return digits[:10]
        return digits
    
    def extract_pan(self, text):
        """Extract PAN from text."""
        # Remove spaces and convert to uppercase
        return text.replace(" ", "").upper()
    
    def get_input_with_retry(self, prompt, validation_func, extract_func=None, field_name="input"):
        """Get user input with validation and retry logic"""
        # First attempt - use full prompt
        self.speak(prompt)
        user_input = self.listen()
        
        if user_input is None:
            # First retry - friendly reprompt
            self.speak("I didn't catch that. Please say it again.")
            user_input = self.listen()
            
            if user_input is None:
                # Second retry - more encouraging
                self.speak("I'm still having trouble hearing you. Let's try one more time.")
                user_input = self.listen()
                
                if user_input is None:
                    # Final failure
                    self.speak(f"I'm sorry, I couldn't hear your {field_name}.")
                    return None
        
        # Now we have input, validate it
        processed_input = extract_func(user_input) if extract_func else user_input
        
        if validation_func(processed_input):
            return processed_input
        
        # Validation failed - retry with shorter prompts
        for attempt in range(self.max_retries):
            self.speak(f"That {field_name} doesn't seem valid. Please try again.")
            user_input = self.listen()
            
            if user_input is None:
                if attempt < self.max_retries - 1:
                    self.speak("I didn't catch that. Let's try again.")
                    continue
                else:
                    self.speak("I'm sorry, I couldn't hear your response.")
                    return None
            
            processed_input = extract_func(user_input) if extract_func else user_input
            
            if validation_func(processed_input):
                return processed_input
        
        # All retries exhausted
        self.speak(f"I was unable to verify your {field_name}.")
        return None
    
    def get_consent(self):
        """Get user consent with yes/no validation"""
        # First attempt
        self.speak("Do you consent to this KYC verification? Please say yes or no.")
        response = self.listen()
        
        if response is None:
            # First retry
            self.speak("I didn't catch that. Do you consent? Say yes or no.")
            response = self.listen()
            
            if response is None:
                # Second retry
                self.speak("Please say yes or no for consent.")
                response = self.listen()
                
                if response is None:
                    # Final failure
                    self.speak("I couldn't get your consent. Verification cannot proceed.")
                    return False
        
        # Check the response
        response_lower = response.lower()
        
        if "yes" in response_lower or "yeah" in response_lower or "sure" in response_lower:
            return True
        elif "no" in response_lower or "nope" in response_lower:
            self.speak("You have declined consent. Verification cannot proceed.")
            return False
        
        # If Invalid response - retry with shorter prompts
        for attempt in range(self.max_retries):
            self.speak("Please say yes or no.")
            response = self.listen()
            
            if response is None:
                if attempt < self.max_retries - 1:
                    self.speak("I didn't hear you. Say yes or no.")
                    continue
                else:
                    self.speak("I couldn't get your consent. Verification cannot proceed.")
                    return False
            
            response_lower = response.lower()
            
            if "yes" in response_lower or "yeah" in response_lower or "sure" in response_lower:
                return True
            elif "no" in response_lower or "nope" in response_lower:
                self.speak("You have declined consent. Verification cannot proceed.")
                return False
        
        # All retries exhausted with invalid responses
        self.speak("I couldn't understand your response. Verification cannot proceed.")
        return False
    
    def run_kyc_session(self):
        """Main KYC verification flow."""
        print("\n" + "="*50)
        print("DECENTRO KYC VOICE VERIFICATION")
        print("="*50 + "\n")
        
        # Welcome message
        self.speak("Welcome to Decentro KYC verification. I will guide you through a quick verification process.")
        
        # Step 1: Get Name
        name = self.get_input_with_retry(
            "May I have your full name please?",
            self.validate_name,
            field_name="name"
        )
        
        if name:
            self.kyc_data["name"] = name
        else:
            self.speak("Unable to proceed without a valid name. Ending verification.")
            return False
        
        # Step 2: Get Phone Number
        phone = self.get_input_with_retry(
            "Thank you. Now, please provide your 10-digit mobile number.",
            self.validate_phone,
            self.extract_phone,
            field_name="phone number"
        )
        
        if phone:
            self.kyc_data["phone"] = phone
        else:
            self.speak("Unable to proceed without a valid phone number. Ending verification.")
            return False
        
        # Step 3: Get PAN
        pan = self.get_input_with_retry(
            "Great. Now, please say your PAN number. That's 10 characters: 5 letters, 4 numbers, and 1 letter.",
            self.validate_pan,
            self.extract_pan,
            field_name="PAN"
        )
        
        if pan:
            self.kyc_data["pan"] = pan
        else:
            self.speak("Unable to proceed without a valid PAN. Ending verification.")
            return False
        
        # Step 4: Get Consent
        consent = self.get_consent()
        self.kyc_data["consent"] = consent
        
        if not consent:
            return False
        
        # Step 5: Summary and Confirmation
        self.speak("Thank you. Let me confirm your details.")
        time.sleep(0.5)
        self.speak(f"Name: {self.kyc_data['name']}")
        time.sleep(0.5)
        self.speak(f"Phone: {self.kyc_data['phone']}")
        time.sleep(0.5)
        self.speak(f"PAN: {self.kyc_data['pan']}")
        time.sleep(0.5)
        self.speak("Consent: Provided")
        
        # Add timestamp
        self.kyc_data["timestamp"] = datetime.now().isoformat()
        
        # Final confirmation & thank you message
        self.speak("Your KYC verification is complete. Thank you for using Decentro services.")
        
        return True
    
    def save_to_json(self, filename="kyc_session.json"):
        """Saving KYC data to JSON file."""
        try:
            with open(filename, 'w') as f:
                json.dump(self.kyc_data, f, indent=2)
            print(f"\nKYC data saved to {filename}")
            return True
        except Exception as e:
            print(f"Error saving JSON: {e}")
            return False


def main():
    """Main function to run the KYC voice bot."""
    print("\n" + "="*50)
    print("SETUP INSTRUCTIONS")
    print("="*50)
    print("1. Make sure your microphone is working")
    print("2. Speak clearly when you see ' [LISTENING]'")
    print("3. The bot will SPEAK to you - LISTEN for voice prompts")
    print("4. Wait for the listening indicator before speaking")
    print("5. Turn up your volume if you can't hear the bot")
    print("="*50 + "\n")
    
    input("Press Enter when you're ready to start...")
    
    bot = KYCVoiceBot()
    
    # Run the KYC session
    success = bot.run_kyc_session()
    
    if success:
        # Save data to JSON
        bot.save_to_json("kyc_session.json")
        
        # Display final data
        print("\n" + "="*50)
        print("KYC SESSION DATA")
        print("="*50)
        print(json.dumps(bot.kyc_data, indent=2))
    else:
        print("\nKYC verification was not completed successfully.")
        print("Partial data collected:")
        print(json.dumps(bot.kyc_data, indent=2))


if __name__ == "__main__":
    main()

'''--------------------------------fully local version below with Sphinx------------------------------------'''

# import speech_recognition as sr
# import pyttsx3
# import json
# import re
# from datetime import datetime
# import time


# class KYCVoiceBot:
#     def __init__(self):
#         """Initialize the voice bot with speech recognition and TTS engines."""
#         self.recognizer = sr.Recognizer()
        
#         # KYC data storage
#         self.kyc_data = {
#             "name": "",
#             "phone": "",
#             "pan": "",
#             "consent": False,
#             "timestamp": ""
#         }
        
#         # Maximum retry attempts
#         self.max_retries = 2
        
#         print("Voice bot initialized successfully")
#         print("Using OFFLINE speech recognition (Sphinx)")
#         print("Using LOCAL text-to-speech (pyttsx3)")
    
#     def speak(self, text):
#         """Convert text to speech - creates fresh engine each time to avoid Windows bug."""
#         print(f"\n Bot: {text}")
        
#         try:
#             # Create a fresh engine for each speech (fixes Windows bug)
#             engine = pyttsx3.init()
#             engine.setProperty('rate', 150)
#             engine.setProperty('volume', 0.9)
#             engine.say(text)
#             engine.runAndWait()
#             engine.stop()
#             del engine  # Clean up
#             time.sleep(0.3)  # Small pause between speeches
#         except Exception as e:
#             print(f"TTS Error: {e}")
#             print("(Please read the text above)")
    
#     def listen(self):
#         """Capture user speech and convert to text using offline recognition."""
#         with sr.Microphone() as source:
#             print("\n [LISTENING] (speak now)")
#             # Adjust for ambient noise
#             self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            
#             try:
#                 audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=10)
#                 print("Processing offline...")
                
#                 # Using offline Sphinx recognition instead of Google
#                 text = self.recognizer.recognize_sphinx(audio)
                
#                 print(f"You: {text}")
#                 return text.strip()
#             except sr.WaitTimeoutError:
#                 print("No speech detected (timeout)")
#                 return None
#             except sr.UnknownValueError:
#                 print("Could not understand audio")
#                 return None
#             except sr.RequestError as e:
#                 print(f"Speech recognition error: {e}")
#                 return None
    
#     def validate_name(self, name):
#         """Validating name is non-empty and contains only letters and spaces."""
#         if not name or len(name.strip()) < 2:
#             return False
#         # Check if name contains at least some alphabetic characters
#         if not re.search(r'[a-zA-Z]', name):
#             return False
#         return True
    
#     def validate_phone(self, phone):
#         """Validating phone number is exactly 10 digits."""
#         # Remove spaces and common words
#         phone_cleaned = re.sub(r'[^\d]', '', phone)
#         return len(phone_cleaned) == 10 and phone_cleaned.isdigit()
    
#     def validate_pan(self, pan):
#         """Validating PAN is 10 alphanumeric characters (format: ABCDE1234F)."""
#         # Remove spaces
#         pan_cleaned = pan.replace(" ", "").upper()
#         # PAN format: 5 letters, 4 digits, 1 letter
#         pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]$'
#         return len(pan_cleaned) == 10 and bool(re.match(pattern, pan_cleaned))
    
#     def extract_phone(self, text):
#         """Extract 10-digit phone number from text."""
#         digits = re.sub(r'[^\d]', '', text)
#         if len(digits) >= 10:
#             return digits[:10]
#         return digits
    
#     def extract_pan(self, text):
#         """Extract PAN from text."""
#         # Remove spaces and convert to uppercase
#         return text.replace(" ", "").upper()
    
#     def get_input_with_retry(self, prompt, validation_func, extract_func=None, field_name="input"):
#         """Get user input with validation and retry logic."""
#         for attempt in range(self.max_retries + 1):
#             self.speak(prompt)
#             user_input = self.listen()
            
#             if user_input is None:
#                 if attempt < self.max_retries:
#                     self.speak("I didn't catch that. Let me try again.")
#                     continue
#                 else:
#                     self.speak("I'm having trouble hearing you.")
#                     return None
            
#             # Extract data if extraction function provided
#             processed_input = extract_func(user_input) if extract_func else user_input
            
#             # Validate
#             if validation_func(processed_input):
#                 return processed_input
#             else:
#                 if attempt < self.max_retries:
#                     self.speak(f"That {field_name} doesn't seem valid. Please try again.")
#                 else:
#                     self.speak("I couldn't validate your input.")
#                     return None
        
#         return None
    
#     def get_consent(self):
#         """Get user consent with yes/no validation."""
#         for attempt in range(self.max_retries + 1):
#             self.speak("Do you consent to this KYC verification? Please say yes or no.")
#             response = self.listen()
            
#             if response is None:
#                 if attempt < self.max_retries:
#                     self.speak("I didn't catch that. Let me try again.")
#                     continue
#                 else:
#                     self.speak("I couldn't get your consent. Verification cannot proceed.")
#                     return False
            
#             response_lower = response.lower()
            
#             if "yes" in response_lower or "yeah" in response_lower or "sure" in response_lower:
#                 return True
#             elif "no" in response_lower or "nope" in response_lower:
#                 self.speak("You have declined consent. Verification cannot proceed.")
#                 return False
#             else:
#                 if attempt < self.max_retries:
#                     self.speak("Please say yes or no.")
#                 else:
#                     self.speak("I couldn't understand your response. Verification cannot proceed.")
#                     return False
        
#         return False
    
#     def run_kyc_session(self):
#         """Main KYC verification flow."""
#         print("\n" + "="*50)
#         print("DECENTRO KYC VOICE VERIFICATION")
#         print("="*50 + "\n")
        
#         # Welcome message
#         self.speak("Welcome to Decentro KYC verification. I will guide you through a quick verification process.")
        
#         # Step 1: Get Name
#         name = self.get_input_with_retry(
#             "May I have your full name please?",
#             self.validate_name,
#             field_name="name"
#         )
        
#         if name:
#             self.kyc_data["name"] = name
#         else:
#             self.speak("Unable to proceed without a valid name. Ending verification.")
#             return False
        
#         # Step 2: Get Phone Number
#         phone = self.get_input_with_retry(
#             "Thank you. Now, please provide your 10-digit mobile number.",
#             self.validate_phone,
#             self.extract_phone,
#             field_name="phone number"
#         )
        
#         if phone:
#             self.kyc_data["phone"] = phone
#         else:
#             self.speak("Unable to proceed without a valid phone number. Ending verification.")
#             return False
        
#         # Step 3: Get PAN
#         pan = self.get_input_with_retry(
#             "Great. Now, please say your PAN number. That's 10 characters - 5 letters, 4 numbers, and 1 letter.",
#             self.validate_pan,
#             self.extract_pan,
#             field_name="PAN"
#         )
        
#         if pan:
#             self.kyc_data["pan"] = pan
#         else:
#             self.speak("Unable to proceed without a valid PAN. Ending verification.")
#             return False
        
#         # Step 4: Get Consent
#         consent = self.get_consent()
#         self.kyc_data["consent"] = consent
        
#         if not consent:
#             return False
        
#         # Step 5: Summary and Confirmation
#         self.speak("Thank you. Let me confirm your details.")
#         time.sleep(0.5)
#         self.speak(f"Name: {self.kyc_data['name']}")
#         time.sleep(0.5)
#         self.speak(f"Phone: {self.kyc_data['phone']}")
#         time.sleep(0.5)
#         self.speak(f"PAN: {self.kyc_data['pan']}")
#         time.sleep(0.5)
#         self.speak("Consent: Provided")
        
#         # Add timestamp
#         self.kyc_data["timestamp"] = datetime.now().isoformat()
        
#         # Final confirmation
#         self.speak("Your KYC verification is complete. Thank you for using Decentro services.")
        
#         return True
    
#     def save_to_json(self, filename="kyc_session.json"):
#         """Save KYC data to JSON file."""
#         try:
#             with open(filename, 'w') as f:
#                 json.dump(self.kyc_data, f, indent=2)
#             print(f"\n KYC data saved to {filename}")
#             return True
#         except Exception as e:
#             print(f"Error saving JSON: {e}")
#             return False


# def main():
#     """Main function to run the KYC voice bot."""
#     print("\n" + "="*50)
#     print("FULLY LOCAL KYC VOICE BOT")
#     print("="*50)
#     print("No internet connection required")
#     print("All processing happens locally")
#     print("Privacy-focused implementation")
#     print("="*50 + "\n")
    
#     print("SETUP INSTRUCTIONS:")
#     print("1. Make sure your microphone is working")
#     print("2. Speak CLEARLY and LOUDLY (offline recognition is less accurate)")
#     print("3. The bot will SPEAK to you - LISTEN for voice prompts")
#     print("4. Wait for the listening indicator before speaking")
#     print("5. Turn up your volume if you can't hear the bot")
#     print("="*50 + "\n")
    
#     input("Press Enter when you're ready to start...")
    
#     bot = KYCVoiceBot()
    
#     # Run the KYC session
#     success = bot.run_kyc_session()
    
#     if success:
#         # Save data to JSON
#         bot.save_to_json("kyc_session.json")
        
#         # Display final data
#         print("\n" + "="*50)
#         print("KYC SESSION DATA")
#         print("="*50)
#         print(json.dumps(bot.kyc_data, indent=2))
#     else:
#         print("\n KYC verification was not completed successfully.")
#         print("Partial data collected:")
#         print(json.dumps(bot.kyc_data, indent=2))


# if __name__ == "__main__":
#     main()
