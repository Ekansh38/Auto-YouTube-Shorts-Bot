import os

import requests
from gtts import gTTS
from openai import OpenAI

topic = input("Enter the topic: ")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")


client = OpenAI(api_key=OPENAI_API_KEY)

prompt = (
    "Write a very short YouTube Shorts video script without any quotes or what the camera will do or anything and exactly what you send will be said without any changes about the topic: "
    + topic
    + " Please remeber not to add quotes (') or double quotes (\") Also dont add new lines that are not needed. Also remeber to give a fun fact about the topic."
)

response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": prompt}],
    stream=False,
)

response = response.choices[0].message.content
script = response
print(response)


language = "en"

myobj = gTTS(text=response, lang=language, slow=False)

myobj.save("audio.mp3")


PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")
prompt = f"I need to find stock video to match this script: {response}. I need a one to two word search term to find the video. Please return 5 spesific search terms sperated by commas one to two word long each. Keep in mind that this is the script to a youtube video so the vvideos should related in some way to the general topic of the script. If you can't think of all five you can repeat some in a worest case scenario. One last thing to keep in mind is your search term is being searched in a stock video library so try to keep it more general."
search_term_response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": prompt}],
    stream=False,
)
search_term_response = search_term_response.choices[0].message.content
search_terms = search_term_response.split(",")[:5]
print(search_terms)


headers = {"Authorization": PEXELS_API_KEY}
names = ["video1.mp4", "video2.mp4", "video3.mp4", "video4.mp4", "video5.mp4"]
i = 0

for search_term in search_terms:
    url = f"https://api.pexels.com/videos/search?query={search_term}&per_page=1"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if data["videos"]:
            video_url = data["videos"][0]["video_files"][0]["link"]
            video_response = requests.get(video_url, stream=True)
            if video_response.status_code == 200:
                with open("videos/" + names[i], "wb") as f:
                    for chunk in video_response.iter_content(chunk_size=1024):
                        f.write(chunk)
                print("Video saved successfully!")
            else:
                print("Failed to download the video.")
        else:
            print("No videos found for the search term.")
    else:
        print("Failed to retrieve videos from Pexels API.")
    i += 1


import cv2
import numpy as np
from moviepy.editor import AudioFileClip, VideoFileClip, concatenate_videoclips


# Function to resize video frames to a target size
def resize_frame(frame, target_size):
    return cv2.resize(frame, target_size, interpolation=cv2.INTER_AREA)


# Function to overlay text on a frame
def add_text_to_frame(
    frame,
    text,
    position,
    font=cv2.FONT_HERSHEY_SIMPLEX,
    font_scale=1,
    font_color=(255, 255, 255),
    font_thickness=2,
):
    if not isinstance(text, str):
        text = str(text)  # Ensure the text is a string
    return cv2.putText(
        frame, text, position, font, font_scale, font_color, font_thickness
    )


# Function to split text into chunks with a maximum number of words
def split_text(text, max_words_per_chunk):
    words = text.split()
    chunks = [
        " ".join(words[i : i + max_words_per_chunk])
        for i in range(0, len(words), max_words_per_chunk)
    ]
    return chunks


# Function to read, resize, trim, and add text to videos
def read_resize_trim_and_add_text(
    video_path, target_size, text_chunks, text_position, text_chunk_duration, fps
):
    cap = cv2.VideoCapture(video_path)
    frames = []
    text_chunk_index = 0
    current_text_chunk = text_chunks[text_chunk_index]
    text_chunk_frames = 0
    text_frames_per_chunk = int(fps * text_chunk_duration)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        resized_frame = resize_frame(frame, target_size)
        frame_with_text = add_text_to_frame(
            resized_frame, current_text_chunk, text_position
        )
        frames.append(frame_with_text)

        text_chunk_frames += 1
        if text_chunk_frames >= text_frames_per_chunk:
            text_chunk_frames = 0
            text_chunk_index += 1
            if text_chunk_index < len(text_chunks):
                current_text_chunk = text_chunks[text_chunk_index]
            else:
                break

    cap.release()

    return frames


# Define the text and its position
overlay_text = script
text_position = (50, 50)  # Position of the text on the frame

# Load audio clip to get its duration
audio = AudioFileClip("audio.mp3")
total_audio_duration = audio.duration

# Split text into chunks with a maximum of 7 words each
max_words_per_chunk = 5
text_chunks = split_text(overlay_text, max_words_per_chunk)

# Calculate text chunk duration based on the number of text chunks
text_chunk_duration = total_audio_duration / len(text_chunks)

# Calculate video segment duration based on the number of video clips
num_clips = 5
video_segment_duration = total_audio_duration / num_clips

# Load and resize videos
video_paths = [
    "videos/video1.mp4",
    "videos/video2.mp4",
    "videos/video3.mp4",
    "videos/video4.mp4",
    "videos/video5.mp4",
]

# Determine target size from the first video
cap = cv2.VideoCapture(video_paths[0])
ret, frame = cap.read()
target_size = (frame.shape[1], frame.shape[0])
fps = cap.get(cv2.CAP_PROP_FPS)
cap.release()

# Read, resize, trim, and add text to all videos
videos = []
for video_path in video_paths:
    video_frames = read_resize_trim_and_add_text(
        video_path, target_size, text_chunks, text_position, text_chunk_duration, fps
    )
    videos.extend(video_frames)

# Write the concatenated frames to a new video file
fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # Codec for .mp4 files
output = cv2.VideoWriter("temp_video_with_text.mp4", fourcc, fps, target_size)

for frame in videos:
    output.write(frame)

output.release()

# Add audio to the concatenated video using MoviePy
final_video = VideoFileClip("temp_video_with_text.mp4")
final_video = final_video.set_audio(audio)
final_video.write_videofile("final_video_with_audio_and_text.mp4", codec="libx264")
