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
TITLE_FONT: str = path.join("fonts", "Merienda.ttf")
TITLE_FONT_SIZE: int = 200
WEEKDAY_ROW_FONT: str = path.join("fonts", "Bitter-Bold.ttf")
WEEKDAY_ROW_FONT_SIZE: int = 55
NUMBER_FONT: str = path.join("fonts", "Bitter.ttf")
DAY_NUMBER_FONT_SIZE: int = 200
WEEK_NUMBER_FONT_SIZE: int = 90
NAMES_FONT: str = path.join("fonts", "Rajdhani-Bold.ttf")
NAMES_FONT_SIZE: int = 45

# Colors
TITLE_FG: str = "black"
WEEK_INFO_FG: str = "black"
WEEK_INFO_BG: str = "#f5de0b"
NORMAL_DAY_FG: str = "black"
SATURDAY_FG: str = "#696969"
SUNDAY_FG: str = "red"
EXTRA_DAY_FG: str = "#9e9e9e"
NAMES_FG: str = "#9e9e9e"
LINE_FG: str = "#f5de0b"

# Dimensions
TITLE_Y_OFFSET: int = 150
FULL_CALENDAR_Y_OFFSET: int = 2350
FULL_CALENDAR_WIDTH: int = 3000
EMBEDDED_IMAGE_OFFSET: int = 480
EMBEDDED_IMAGE_HEIGHT: int = 1700
WEEKDAY_ROW_HEIGHT: int = 120
CALENDAR_ROW_HEIGHT: int = 400
WEEK_NUMBER_WIDTH: int = 180
ROUNDING_RADIUS: int = 40
LINE_WIDTH: int = 12
DAY_CELL_SPACING: int = 38

# Export options
AUTHOR_NAME: str = "Kacper Wojciuch"
PDF_DPI: int = 300  # base image should be 3508x4961 for A3

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
WEEKDAY_NAMES = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota", "Niedziela"]

# -------------- Script code -------------- #


@cache
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
    """Generates 4/5/6-week 2D-array of days in the selected month"""

    matrix = [[], [], [], [], [], [], []]
    row = 0
    current_date = date(year, month, 1)
    while current_date.weekday() != 0 or current_date.month == month:
        matrix[row].append(current_date)
        if current_date.weekday() == 6:
            row += 1
        current_date += timedelta(days=1)
    current_date = date(year, month, 1) - timedelta(days=1)
    while len(matrix[0]) != 7:
        matrix[0].insert(0, current_date)
        current_date -= timedelta(days=1)
    return matrix[: matrix.index([])]


def generate_month_table(matrix: list[list[date]], month: int) -> Image:
    """Generates an image containing the main part of the calendar in a table"""

    full_calendar_height = WEEKDAY_ROW_HEIGHT + len(matrix) * CALENDAR_ROW_HEIGHT
    main_column_width = (FULL_CALENDAR_WIDTH - WEEK_NUMBER_WIDTH) // 7
    image = image_new("RGB", (FULL_CALENDAR_WIDTH, full_calendar_height), (255, 255, 255))
    draw = image_draw(image)

    # Week numbers
    draw.rounded_rectangle(
        (0, WEEKDAY_ROW_HEIGHT, WEEK_NUMBER_WIDTH - LINE_WIDTH, full_calendar_height), ROUNDING_RADIUS, WEEK_INFO_BG
    )
    for row in range(len(matrix)):
        draw.text(
            (WEEK_NUMBER_WIDTH // 2, WEEKDAY_ROW_HEIGHT + row * CALENDAR_ROW_HEIGHT + CALENDAR_ROW_HEIGHT // 2),
            str(matrix[row][0].isocalendar()[1]),
            font=get_cached_font(NUMBER_FONT, WEEK_NUMBER_FONT_SIZE),
            anchor="mm",
            fill=WEEK_INFO_FG,
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
        draw.text(
            (WEEK_NUMBER_WIDTH + column * main_column_width + main_column_width // 2, WEEKDAY_ROW_HEIGHT // 2),
            WEEKDAY_NAMES[column],
            font=get_cached_font(WEEKDAY_ROW_FONT, WEEKDAY_ROW_FONT_SIZE),
            anchor="mm",
            fill=WEEK_INFO_FG,
        )
        # Line
        draw.rectangle(
            (
                WEEK_NUMBER_WIDTH + (column + 1) * main_column_width - LINE_WIDTH + 1,
                WEEKDAY_ROW_HEIGHT,
                WEEK_NUMBER_WIDTH + (column + 1) * main_column_width,
                full_calendar_height,
            ),
            LINE_FG,
        )
        # Days
        for row in range(len(matrix)):
            # Line
            line_y = WEEKDAY_ROW_HEIGHT + (row + 1) * CALENDAR_ROW_HEIGHT
            draw.rectangle(
                (
                    WEEK_NUMBER_WIDTH + column * main_column_width + 1,
                    line_y - LINE_WIDTH,
                    WEEK_NUMBER_WIDTH + (column + 1) * main_column_width,
                    line_y - 1,
                ),
                LINE_FG,
            )
            # Day number
            current_date = matrix[row][column]
            is_extra_day = current_date.month != month
            day_number_xy = (
                WEEK_NUMBER_WIDTH + column * main_column_width + main_column_width // 2,
                WEEKDAY_ROW_HEIGHT
                + row * CALENDAR_ROW_HEIGHT
                + (CALENDAR_ROW_HEIGHT // 2 if is_extra_day else DAY_CELL_SPACING),
            )
            if is_extra_day:
                day_color = EXTRA_DAY_FG
            elif current_date.weekday() == 5:
                day_color = SATURDAY_FG
            elif current_date.weekday() == 6:
                day_color = SUNDAY_FG
            else:
                day_color = NORMAL_DAY_FG
            draw.text(
                xy=day_number_xy,
                text=str(current_date.day),
                font=get_cached_font(NUMBER_FONT, DAY_NUMBER_FONT_SIZE),
                anchor="mm" if is_extra_day else "mt",
                fill=day_color,
            )
            # Names
            if is_extra_day:
                continue
            names_params = {
                "xy": (0, 0),  # just to measure the bounding box
                "text": "\n".join(read_name_days()[(current_date.day, current_date.month)]),
                "font": get_cached_font(NAMES_FONT, NAMES_FONT_SIZE),
                "align": "center",
            }
            names_box = draw.multiline_textbbox(**names_params)
            names_params["xy"] = (
                day_number_xy[0] - (names_box[2] - names_box[0]) // 2,
                WEEKDAY_ROW_HEIGHT
                + (row + 1) * CALENDAR_ROW_HEIGHT
                - LINE_WIDTH
                - DAY_CELL_SPACING
                - (names_box[3] - names_box[1]),
            )
            draw.text(**names_params, fill=NAMES_FG)

    return image


def scale_embedded_image(image: Image) -> Image:
    """Crops and scales selected image to match the required size"""
    ratio = image.size[0] / image.size[1]
    expected_ratio = FULL_CALENDAR_WIDTH / EMBEDDED_IMAGE_HEIGHT
    if ratio > expected_ratio:
        width = image.size[1] * expected_ratio
        return image.resize(
            (FULL_CALENDAR_WIDTH, EMBEDDED_IMAGE_HEIGHT),
            box=((image.size[0] - width) // 2, 0, (image.size[0] + width) // 2, image.size[1]),
        )
    else:
        height = image.size[0] / expected_ratio
        return image.resize(
            (FULL_CALENDAR_WIDTH, EMBEDDED_IMAGE_HEIGHT),
            box=(0, (image.size[1] - height) // 2, image.size[0], (image.size[1] + height) // 2),
        )


def generate_calendar_page(base_image: Image, year: int, month: int, embed: Image) -> Image:
    """Generates singular month page of the calendar"""

    image = base_image.copy()
    draw = image_draw(image)
    draw.text(
        (image.width // 2, TITLE_Y_OFFSET),
        f"{MONTH_NAMES[month - 1]} {year}",
        font=get_cached_font(TITLE_FONT, TITLE_FONT_SIZE),
        anchor="mt",
        fill=TITLE_FG,
    )

    scaled_embed = scale_embedded_image(embed)
    content_x = (image.width - FULL_CALENDAR_WIDTH) // 2
    image.paste(scaled_embed, (content_x, EMBEDDED_IMAGE_OFFSET))

    matrix = generate_day_matrix(year, month)
    image.paste(generate_month_table(matrix, month), (content_x, FULL_CALENDAR_Y_OFFSET))

    return image


def main(year: int) -> None:
    """Main function"""

    try:
        base_image = image_open(BASE_IMAGE).convert("RGB")
    except (UnidentifiedImageError, FileNotFoundError):
        print(f"Could not open base image!")
        raise ValueError
    embedded_images = read_embedded_images()

    generated_pages = []
    for month in range(12):
        generated_pages.append(generate_calendar_page(base_image, year, month + 1, embedded_images[month]))
        print(f"Generated page number {month + 1}!")

    makedirs(OUTPUT_DIRECTORY, exist_ok=True)
    output_file = path.join(OUTPUT_DIRECTORY, f"calendar_{year}.pdf")
    print("Saving...")
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
        main(int(argv[1]))
