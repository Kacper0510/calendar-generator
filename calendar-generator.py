from sys import argv
from os import path, listdir, makedirs
from datetime import date, timedelta
import json
from PIL import UnidentifiedImageError
from PIL.Image import Image, open as image_open, new as image_new
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
TITLE_FONT_SIZE: int = 56
WEEKDAY_ROW_FONT: str = "arial.ttf"
WEEKDAY_ROW_FONT_SIZE: int = 20
NUMBER_FONT: str = "arial.ttf"
DAY_NUMBER_FONT_SIZE: int = 32
WEEK_NUMBER_FONT_SIZE: int = 16
NAMES_FONT: str = "arial.ttf"
NAMES_FONT_SIZE: int = 16

# Colors
TITLE_FG: str = "black"
WEEK_INFO_FG: str = "black"
WEEK_INFO_BG: str = "gray"
NORMAL_DAY_FG: str = "black"
SATURDAY_FG: str = "gray"
SUNDAY_FG: str = "red"
EXTRA_DAY_FG: str = "gray"
NAMES_FG: str = "gray"
LINE_FG: str = "gray"

# Dimensions
TITLE_Y_OFFSET: int = 70
FULL_CALENDAR_Y_OFFSET: int = 600
FULL_CALENDAR_WIDTH: int = 750
WEEKDAY_ROW_HEIGHT: int = 50
CALENDAR_ROW_HEIGHT: int = 90
WEEK_NUMBER_WIDTH: int = 46
ROUNDING_RADIUS: int = 10
LINE_WIDTH: int = 3

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
    """Returns cached font or loads it if necessary"""
    try:
        return truetype(font_file, font_size)
    except OSError:
        print(f"Specified font could not be loaded: {font_file}")
        raise ValueError


def generate_day_matrix(year: int, month: int) -> list[list[date]]:
    """Generates 5-week 2D-array of days in the selected month"""
    matrix = [[], [], [], [], []]
    row = 0
    current_date = date(year, month, 1)
    while row != 5:
        matrix[row].append(current_date)
        if current_date.weekday() == 6:
            row += 1
        current_date += timedelta(days=1)
    current_date = date(year, month, 1) - timedelta(days=1)
    while len(matrix[0]) != 7:
        matrix[0].insert(0, current_date)
        current_date -= timedelta(days=1)
    return matrix


def generate_month_table(matrix: list[list[date]]) -> Image:
    """Generates an image containing the main part of the calendar in a table"""
    full_calendar_height = WEEKDAY_ROW_HEIGHT + 5 * CALENDAR_ROW_HEIGHT
    main_column_width = (FULL_CALENDAR_WIDTH - WEEK_NUMBER_WIDTH) // 7
    image = image_new("RGB", (FULL_CALENDAR_WIDTH, full_calendar_height), (255, 255, 255))
    draw = image_draw(image)

    # Week numbers
    draw.rounded_rectangle(
        (0, WEEKDAY_ROW_HEIGHT, WEEK_NUMBER_WIDTH, full_calendar_height), ROUNDING_RADIUS, WEEK_INFO_BG
    )

    # Main table
    for column in range(7):
        # Weekday
        draw.rounded_rectangle(
            (
                WEEK_NUMBER_WIDTH + column * main_column_width + 1,
                0,
                WEEK_NUMBER_WIDTH + (column + 1) * main_column_width - LINE_WIDTH,
                WEEKDAY_ROW_HEIGHT,
            ),
            ROUNDING_RADIUS,
            WEEK_INFO_BG,
        )
        draw.rectangle(
            (
                WEEK_NUMBER_WIDTH + (column + 1) * main_column_width - LINE_WIDTH + 1,
                WEEKDAY_ROW_HEIGHT,
                WEEK_NUMBER_WIDTH + (column + 1) * main_column_width,
                full_calendar_height,
            ),
            LINE_FG,
        )

    return image


def generate_calendar_page(base_image: Image, year: int, month: int) -> Image:
    """Generates singular month page of the calendar"""
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

    matrix = generate_day_matrix(year, month)
    table_xy = ((image.width - FULL_CALENDAR_WIDTH) // 2, FULL_CALENDAR_Y_OFFSET)
    image.paste(generate_month_table(matrix), table_xy)

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

    generated_pages = [generate_calendar_page(base_image, year, m + 1) for m in range(12)]
    makedirs(OUTPUT_DIRECTORY, exist_ok=True)
    output_file = path.join(OUTPUT_DIRECTORY, f"calendar_{year}.pdf")
    generated_pages[0].save(
        output_file,
        save_all=True,
        append_images=generated_pages[1:],
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
