from flask import Flask, request, jsonify
import asyncio
import cloudinary
import cloudinary.uploader
import soundfile as sf
import numpy as np
import requests
import os
import time

# Configure Cloudinary
cloudinary.config(
    cloud_name="dbvmd8poq",
    api_key="969116766564839",
    api_secret="rqdqu0ohOqQnM3gR6EzaPqnTWDI"
)

app = Flask(__name__)

async def save_and_upload_audio(audio_data):
    # Convert audio bytes to NumPy array and save as WAV
    audio_array = np.frombuffer(audio_data, dtype=np.int16)
    wav_file_path = "temp_audio.wav"
    sf.write(wav_file_path, audio_array, 16000)

    # Upload to Cloudinary
    response = cloudinary.uploader.upload(
        wav_file_path,
        resource_type="raw",
        format="wav",
        folder="audio_files"
    )
    os.remove(wav_file_path)  # Clean up the temporary file

    return response["url"]

async def transcribe_audio(audio_url):
    # Call the API to convert audio to text
    api_url = "https://api.on-demand.io/services/v1/public/service/execute/speech_to_text"
    payload = {"audioUrl": audio_url}
    headers = {
        "Content-Type": "application/json",
        "apikey": "njTpVEIgU7eRrvDpF7kD0Mru31LRZCtf"  # Replace with your actual API key
    }

    response = requests.post(api_url, json=payload, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data['data']['text']  # Return transcribed text
    else:
        print("Error in audio-to-text service:", response.text)
        return None

def detect_keywords(transcribed_text):
    keywords = ['help', 'save', 'please']
    for keyword in keywords:
        if keyword in transcribed_text.lower():
            with open("detected_keyword.txt", "w") as file:
                file.write(f"Keyword detected: {keyword}")
            return keyword  # Return detected keyword
    return "none"

@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    # Get the audio file from the request
    file = request.files.get('file')
    if not file:
        return jsonify({"error": "No audio file provided"}), 400

    # Read and process audio data
    audio_data = file.read()
    start_time = time.time()

    # Save, upload, and transcribe audio asynchronously
    audio_url = asyncio.run(save_and_upload_audio(audio_data))
    transcribed_text = asyncio.run(transcribe_audio(audio_url))

    if transcribed_text:
        detected_keyword = detect_keywords(transcribed_text)
        response_message = {"detected_keyword": detected_keyword}
    else:
        response_message = {"error": "Failed to transcribe audio"}

    print(f"Processing time: {time.time() - start_time} seconds")
    return jsonify(response_message)

if __name__ == "__main__":
    app.run(debug=True)
