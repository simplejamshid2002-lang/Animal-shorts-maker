
import os
import textwrap
import requests
from pathlib import Path
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
    ImageClip,
    CompositeVideoClip,
)

API_KEY = os.getenv("PIXABAY_API_KEY", "")
OUTPUT_DIR = Path("output")
SHORTS_DIR = OUTPUT_DIR / "shorts"
OUTPUT_DIR.mkdir(exist_ok=True)
SHORTS_DIR.mkdir(exist_ok=True)

FACTS = [
    ("A cheetah can run faster than most cars in a short sprint.",
     "Amazing cheetahs can reach incredible speeds!"),
    ("Elephants can recognize themselves in a mirror.",
     "Elephants are highly intelligent animals!"),
    ("Octopuses have three hearts.",
     "An octopus has three hearts and blue blood!"),
    ("A tiger's stripes are unique, like human fingerprints.",
     "Every tiger has its own unique stripes!"),
    ("Dolphins use special sounds to communicate.",
     "Dolphins communicate using clicks and whistles!"),
    ("Giraffes have the same number of neck bones as humans.",
     "Giraffes have seven neck bones, just like us!"),
    ("An owl can turn its head up to about 270 degrees.",
     "Owls can turn their heads remarkably far!"),
    ("Penguins are excellent swimmers.",
     "Penguins are birds built for life in the water!"),
]


def download_videos():
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
    downloaded = []

    for video in videos[:3]:
        files = video.get("videos", {})
        item = files.get("medium") or files.get("small") or files.get("large")

        if not item or not item.get("url"):
            continue

        path = OUTPUT_DIR / f"animal_{video['id']}.mp4"

        if not path.exists():
            with requests.get(
                item["url"], stream=True, timeout=90
            ) as result:
                result.raise_for_status()
                with open(path, "wb") as output:
                    for chunk in result.iter_content(256 * 1024):
                        if chunk:
                            output.write(chunk)

        downloaded.append((path, int(video["id"])))
        print(f"Video tayyor: {path}")

    return downloaded


def make_text_image(text, path):
    width, height = 900, 520
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    font = ImageFont.truetype(font_path, 48)

    lines = textwrap.wrap(text, width=27)
    line_height = 65
    total_height = len(lines) * line_height + 50
    top = (height - total_height) // 2

    draw.rounded_rectangle(
        (20, top, width - 20, top + total_height),
        radius=30,
        fill=(0, 0, 0, 175),
    )

    for line in lines:
        box = draw.textbbox((0, 0), line, font=font, stroke_width=1)
        text_width = box[2] - box[0]
        x = (width - text_width) // 2

        draw.text(
            (x, top + 25),
            line,
            font=font,
            fill="white",
            stroke_width=1,
            stroke_fill="black",
        )
        top += line_height

    image.save(path)


def make_short(video_path, video_id):
    fact, narration = FACTS[video_id % len(FACTS)]
    audio_path = OUTPUT_DIR / f"voice_{video_id}.mp3"
    text_path = OUTPUT_DIR / f"text_{video_id}.png"
    final_path = SHORTS_DIR / f"short_{video_id}.mp4"

    if final_path.exists():
        print(f"Short avval tayyorlangan: {final_path}")
        return

    gTTS(text=narration, lang="en").save(str(audio_path))
    make_text_image(fact, text_path)

    with VideoFileClip(str(video_path)) as source:
        with AudioFileClip(str(audio_path)) as voice:
            duration = min(source.duration, max(voice.duration + 2, 10))

            clip = source.subclip(0, duration)
            clip = clip.resize(height=1920)

            if clip.w < 1080:
                clip = clip.resize(width=1080)

            x_center = clip.w / 2
            y_center = clip.h / 2
            clip = clip.crop(
                x1=x_center - 540,
                y1=y_center - 960,
                x2=x_center + 540,
                y2=y_center + 960,
            )

            overlay = (
                ImageClip(str(text_path))
                .set_duration(duration)
                .resize(width=1000)
                .set_position(("center", 1250))
            )

            final = CompositeVideoClip(
                [clip, overlay], size=(1080, 1920)
            ).set_audio(voice.set_duration(min(voice.duration, duration)))

            final.write_videofile(
                str(final_path),
                fps=24,
                codec="libx264",
                audio_codec="aac",
                preset="ultrafast",
                logger=None,
            )

            final.close()
            overlay.close()
            clip.close()

    print(f"Short tayyor: {final_path}")


def main():
    if not API_KEY:
        raise RuntimeError("PIXABAY_API_KEY sozlanmagan.")

    videos = download_videos()

    for path, video_id in videos:
        try:
            make_short(path, video_id)
        except Exception as error:
            print(f"Bu video tayyorlanmadi: {error}")

    print("Jarayon tugadi. output/shorts papkasini tekshiring.")


if __name__ == "__main__":
    main()
