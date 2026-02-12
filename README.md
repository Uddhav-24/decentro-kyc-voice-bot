# KYC Voice Verification Bot

A Python voice bot for Decentro fintech platform for KYC verification that collects user details through speech interaction.

## Demo Video

[Watch Demo Video on Google Drive](https://drive.google.com/file/d/1RjvmE1DrgV1fOuFDhIY6gd-W_4uPvdO2/view?usp=sharing)

## Setup Instructions

### Prerequisites
- Python 3.7+
- Microphone

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/YOUR-USERNAME/decentro-kyc-voice-bot.git
cd decentro-kyc-voice-bot
```

2. **Create virtual environment**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

**If PyAudio fails:**
- Windows: `pip install pipwin` then `pipwin install pyaudio`
- Mac: `brew install portaudio` then `pip install pyaudio`
- Linux: `sudo apt-get install portaudio19-dev python3-pyaudio`

## How to Run
```bash
python kyc_voice_bot.py
```

Follow the voice prompts:
1. **Name:** Say your full name
2. **Phone:** Say 10-digit number (e.g., "9876543210")
3. **PAN:** Say each character (e.g., "A B C D E 1 2 3 4 F")
4. **Consent:** Say "yes" or "no"

The bot will confirm your details and save to `kyc_session.json`.

## Sample Output
```json
{
  "name": "Uddhav Davey",
  "phone": "9876543210",
  "pan": "ABCDE1234F",
  "consent": true,
  "timestamp": "2025-02-12T14:30:45.123456"
}
```

## Features

- Speech recognition for user input
- Text-to-speech for bot prompts
- Input validation (name, 10-digit phone, PAN format, consent)
- Retry logic (up to 2 retries per field)
- JSON output for backend integration
- Error handling for invalid/missing input

## Technical Details

**Libraries:**
- `SpeechRecognition` - Speech-to-text (recognize_google)
- `pyttsx3` - Text-to-speech (local)
- `PyAudio` - Microphone input

**Validation:**
- Name: Min 2 characters, alphabetic
- Phone: Exactly 10 digits
- PAN: 10 alphanumeric (ABCDE1234F format)
- Consent: yes/no

## Notes

This implementation uses Google Speech Recognition for accuracy. An offline version using CMU Sphinx is available by replacing `recognize_google()` with `recognize_sphinx()` in the code (requires `pip install pocketsphinx`).

## Author

Uddhav Davey 
uddhavdavey2410@gmail.com
[GitHub: https://github.com/Uddhav-24]