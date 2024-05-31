from sys import argv
from os import path, listdir, makedirs
from datetime import datetime, timedelta
import json
from PIL import UnidentifiedImageError
from PIL.Image import Image, open as image_open
from PIL.ImageDraw import Draw as image_draw
from PIL.ImageFont import FreeTypeFont, truetype
from itertools import cycle, islice
from functools import cache

# ---------- Parameters to tweak ---------- #

# Files/directories
NAME_DAYS_FILE: str = "polish_name_days.json"
BASE_IMAGE: str = path.join("template", "base.png")
EMBEDDED_IMAGES_DIRECTORY: str = "images"
OUTPUT_DIRECTORY: str = "output"

# Fonts
TITLE_FONT: str = "arial.ttf"
WEEKDAY_ROW_FONT: str = "arial.ttf"
DAY_NUMBER_FONT: str = "arial.ttf"
NAMES_FONT: str = "arial.ttf"

# Colors
TITLE_FG: str = "black"
WEEKDAY_ROW_FG: str = "black"
WEEKDAY_ROW_BG: str = "gray"
NORMAL_DAY_FG: str = "black"
SATURDAY_FG: str = "gray"
SUNDAY_FG: str = "red"
EXTRA_DAY_FG: str = "gray"
NAMES_FG: str = "gray"

# Dimensions
TITLE_Y_OFFSET: int = 70
TITLE_FONT_SIZE: int = 64
FULL_CALENDAR_Y_OFFSET: int = 600
FULL_CALENDAR_WIDTH: int = 750
CALENDAR_WEEKDAY_ROW_HEIGHT: int = 50
CALENDAR_ROW_HEIGHT: int = 90

# Export options
AUTHOR_NAME: str = "Kacper Wojciuch"
PDF_DPI: int = 75  # DPI 75, so the base image should be 842x1191 for A3

# Localization
MONTH_NAMES = [
    "Styczeń",
    "Luty",
    "Marzec",
    "Kwiecień",
    "Maj",
    "Czerwiec",
    "Lipiec",
    "Sierpień",
    "Wrzesień",
    "Październik",
    "Listopad",
    "Grudzień",
]

# -------------- Script code -------------- #


def read_name_days() -> dict[tuple[int, int], list[str]]:
    """
    Reads name days from a JSON file into a dict with the following structure:
    (day, month) -> [name1, name2, ...]
    """
    with open(NAME_DAYS_FILE, "r", encoding="UTF-8") as file:
        names: dict[str, list[str]] = json.load(file)
        return {tuple(map(int, key.split("."))): value for key, value in names.items()}  # type: ignore


def read_embedded_images() -> list[Image]:
    """
    Reads images to be embedded into the calendar from the selected directory
    and produces a list of exactly 12 elements, one for each month.
    """
    image_names = [
        file for f in listdir(EMBEDDED_IMAGES_DIRECTORY) if path.isfile(file := path.join(EMBEDDED_IMAGES_DIRECTORY, f))
    ]
    images: list[Image] = []
    for image in image_names:
        try:
            images.append(image_open(image).convert("RGB"))
        except UnidentifiedImageError:
            print(f"Could not open image: {image}")
    if len(images) == 0:
        print("No images found in the selected directory!")
        raise ValueError
    return list(islice(cycle(images), 12))


@cache
def get_cached_font(font_file: str, font_size: int) -> FreeTypeFont:
    try:
        return truetype(font_file, font_size)
    except OSError:
        print(f"Specified font could not be loaded: {font_file}")
        raise ValueError


def generate_calendar_month(base_image: Image, year: int, month: int) -> Image:
    image = base_image.copy()
    draw = image_draw(image)
    draw.text(
        (image.width // 2, TITLE_Y_OFFSET),
        f"{MONTH_NAMES[month - 1]} {year}",
        font=get_cached_font(TITLE_FONT, TITLE_FONT_SIZE),
        font_size=TITLE_FONT_SIZE,
        anchor="mt",
        fill=TITLE_FG,
    )
    return image


def main(year: int) -> None:
    """Main function"""
    name_days = read_name_days()
    try:
        base_image = image_open(BASE_IMAGE).convert("RGB")
    except (UnidentifiedImageError, FileNotFoundError):
        print(f"Could not open base image!")
        raise ValueError
    # embedded_images = read_embedded_images()

    generated_months = [generate_calendar_month(base_image, year, m + 1) for m in range(12)]
    makedirs(OUTPUT_DIRECTORY, exist_ok=True)
    output_file = path.join(OUTPUT_DIRECTORY, f"calendar_{year}.pdf")
    generated_months[0].save(
        output_file,
        save_all=True,
        append_images=generated_months[1:],
        author=AUTHOR_NAME,
        producer="Kacper0510/calendar-generator",
        title=f"{year} - {AUTHOR_NAME}",
        resolution=PDF_DPI,
    )
    print(f"Success, saved results to: {path.abspath(output_file)}")


if __name__ == "__main__":
    if len(argv) != 2:
        print("Usage: python calendar-generator.py <year>")
    else:
        try:
            main(int(argv[1]))
        except ValueError:
            print("Exiting...")
