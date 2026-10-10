
import os
import requests
from pathlib import Path

API_KEY = os.getenv("PIXABAY_API_KEY", "")
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


def main():
    if not API_KEY:
        raise RuntimeError("PIXABAY_API_KEY topilmadi.")

    response = requests.get(
        "https://pixabay.com/api/videos/",
        params={
            "key": API_KEY,
            "q": "wild animals",
            "per_page": 5,
            "safesearch": "true",
        },
        timeout=30,
    )
    response.raise_for_status()
    videos = response.json().get("hits", [])

    if not videos:
        print("Video topilmadi.")
        return

    for video in videos[:3]:
        files = video.get("videos", {})
        item = files.get("medium") or files.get("small") or files.get("large")

        if not item or not item.get("url"):
            continue

        path = OUTPUT_DIR / f"animal_{video['id']}.mp4"

        with requests.get(item["url"], stream=True, timeout=90) as result:
            result.raise_for_status()
            with open(path, "wb") as output:
                for chunk in result.iter_content(256 * 1024):
                    if chunk:
                        output.write(chunk)

        print(f"Yuklandi: {path}")

    print("Tugadi. Videolar output papkasida.")


if __name__ == "__main__":
    main()
