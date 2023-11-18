from genie.setup.file import create_genie_folder


def after_install():
    create_genie_folder()
