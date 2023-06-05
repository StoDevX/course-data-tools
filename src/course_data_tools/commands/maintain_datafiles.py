import click

from course_data_tools.maintain_lists_of_entries import maintain_lists_of_entries
from course_data_tools.load_courses import load_all_courses


@click.command()
def maintain_datafiles():
    all_courses = load_all_courses()
    maintain_lists_of_entries(all_courses)
