import click

from course_data_tools.commands.maintain_datafiles import maintain_datafiles
from course_data_tools.commands.download import download
from course_data_tools.commands.bundle import bundle


@click.group()
def cli():
    pass


cli.add_command(bundle)
cli.add_command(download)
cli.add_command(maintain_datafiles)
