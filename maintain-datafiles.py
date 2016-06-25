#!/usr/bin/env python3

from lib.maintain_lists_of_entries import maintain_lists_of_entries
from lib.load_courses import load_all_courses


def main():
    all_courses = load_all_courses()
    maintain_lists_of_entries(all_courses)


if __name__ == '__main__':
    main()
