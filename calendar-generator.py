from sys import argv
from datetime import datetime, timedelta
import json

# Parameters to tweak

NAME_DAYS_FILE: str = "polish_name_days.json"

# Script code

NAME_DAYS: dict[tuple[int, int], list[str]]  # (day, month) -> [name1, name2, ...]


def read_name_days() -> None:
    """Reads name days from a JSON file into a global variable"""
    global NAME_DAYS
    with open(NAME_DAYS_FILE, "r", encoding="UTF-8") as file:
        names: dict[str, list[str]] = json.load(file)
        NAME_DAYS = {tuple(map(int, key.split("."))): value for key, value in names.items()}


def main(year: int) -> None:
    """Main function"""
    read_name_days()


if __name__ == "__main__":
    if len(argv) != 2:
        print("Usage: python calendar-generator.py <year>")
    else:
        main(int(argv[1]))
