from genie.setup.file import create_genie_folder


def after_migrate():
    create_genie_folder()
