import os

from gtts import gTTS
from openai import OpenAI

topic = input("Enter the topic: ")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")


client = OpenAI(api_key=OPENAI_API_KEY)

prompt = (
    "Write a pretty short YouTube Shorts video script without any quotes or what the camera will do or anything and exactly what you send will be said without any changes about the topic: "
    + topic
    + " Please remeber not to add quotes (') or double quotes (\"). Also remeber to give a fun fact about the topic."
)

response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": prompt}],
    stream=False,
)

response = response.choices[0].message.content
print(response)


language = "en"

myobj = gTTS(text=response, lang=language, slow=False)

myobj.save("audio.mp3")

os.system("vlc audio.mp3")


import requests

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
