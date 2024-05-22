from sys import argv
from os import path, listdir
from datetime import datetime, timedelta
import json
from PIL import Image, UnidentifiedImageError
from itertools import cycle, islice

# Parameters to tweak

NAME_DAYS_FILE: str = "polish_name_days.json"
IMAGES_DIRECTORY: str = "images"

AUTHOR_NAME: str = "Kacper Wojciuch"
PDF_DPI: int = 75  # DPI 75, so the default image should be 842x1191 for A3

# Script code


def read_name_days() -> dict[tuple[int, int], list[str]]:
    """
    Reads name days from a JSON file into a dict with the following structure:
    (day, month) -> [name1, name2, ...]
    """
    with open(NAME_DAYS_FILE, "r", encoding="UTF-8") as file:
        names: dict[str, list[str]] = json.load(file)
        return {tuple(map(int, key.split("."))): value for key, value in names.items()}  # type: ignore


def read_embedded_images() -> list[Image.Image]:
    """
    Reads images to be embedded into the calendar from the selected directory
    and produces a list of exactly 12 elements, one for each month.
    """
    image_names = [file for f in listdir(IMAGES_DIRECTORY) if path.isfile(file := path.join(IMAGES_DIRECTORY, f))]
    images: list[Image.Image] = []
    for image in image_names:
        try:
            images.append(Image.open(image).convert("RGB"))
        except UnidentifiedImageError:
            print(f"Could not open image: {image}")
    if len(images) == 0:
        print("No images found in the selected directory!")
        raise ValueError
    return list(islice(cycle(images), 12))


def main(year: int) -> None:
    """Main function"""
    name_days = read_name_days()
    embedded_images = read_embedded_images()
    embedded_images[0].save(
        f"calendar_{year}.pdf",
        save_all=True,
        append_images=embedded_images[1:],
        author=AUTHOR_NAME,
        producer="Kacper0510/calendar-generator",
        title=f"{year} - {AUTHOR_NAME}",
        resolution=PDF_DPI,
    )


if __name__ == "__main__":
    if len(argv) != 2:
        print("Usage: python calendar-generator.py <year>")
    else:
        main(int(argv[1]))
