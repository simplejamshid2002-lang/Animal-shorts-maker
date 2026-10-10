
import os
import requests
from pathlib import Path

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


def search_animal_video(query="amazing wild animals"):
    if not PEXELS_API_KEY:
        raise RuntimeError(
            "PEXELS_API_KEY sozlanmagan. "
            "GitHub Secrets orqali API kalitini qo'shing."
        )

    response = requests.get(
        "https://api.pexels.com/v1/videos/search",
        headers={"Authorization": PEXELS_API_KEY},
        params={
            "query": query,
            "per_page": 5,
            "orientation": "portrait"
        },
        timeout=30
    )
    response.raise_for_status()
    return response.json().get("videos", [])


def download_video(video):
    files = video.get("video_files", [])
    suitable = [
        item for item in files
        if item.get("file_type") == "video/mp4"
        and item.get("link")
    ]

    if not suitable:
        print("Bu videoda mos MP4 fayl topilmadi.")
        return None

    # Prefer a smaller file to reduce download time.
    suitable.sort(key=lambda item: item.get("width", 99999))
    url = suitable[0]["link"]
    path = OUTPUT_DIR / f"animal_{video['id']}.mp4"

    with requests.get(url, stream=True, timeout=90) as response:
        response.raise_for_status()
        with open(path, "wb") as file:
            for chunk in response.iter_content(chunk_size=1024 * 256):
                if chunk:
                    file.write(chunk)

    print(f"Video yuklandi: {path}")
    return path


def main():
    videos = search_animal_video()
    if not videos:
        print("Video topilmadi. Boshqa qidiruv so'zini sinab ko'ring.")
        return

    for video in videos[:3]:
        try:
            download_video(video)
        except Exception as error:
            print(f"Video yuklanmadi: {error}")

    print("Qidiruv yakunlandi. Yuklangan videolar output papkasida.")


if __name__ == "__main__":
    main()
