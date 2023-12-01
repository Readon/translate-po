import argparse
import os
import asyncio

import polib
from granslate import Translator

from .utilities.constants import UNTRANSLATED_PATH, TRANSLATED_PATH, LANGUAGE_SOURCE, LANGUAGE_DESTINATION
from .utilities.io import read_lines, save_lines
from .utilities.match import recognize_po_file


async def translate(line: polib.POEntry, arguments) -> str:
    """ Translates a single string into target language. """
    translator = Translator()
    source = polib.escape(line.msgid)
    translated = await asyncio.gather(translator.translate(source, dest=arguments.to, src=arguments.fro))
    line.msgstr = polib.unescape(translated[0].text)
    return line


def create_close_string(line: str) -> str:
    """ Creates single .po file translation target sting. """
    return r"msgstr " + '"' + line + '"' + "\n"


async def solve(new_file: str, old_file: str, arguments):
    """ Translates single file. """
    lines = read_lines(old_file)
    try:
        tasks = [translate(line, arguments) for line in lines]
        await asyncio.gather(*tasks)
        save_lines(new_file, lines)
    except:
        print(f"Timeout, Translate {new_file} error.")
        return new_file, old_file
    print(f"Translated and write file: {new_file}.")
    return None


def run(**kwargs):
    """ Core process that translates all files in a directory.
     :parameter fro:
     :parameter to:
     :parameter src:
     :parameter dest:
     """
    found_files = False

    parser = argparse.ArgumentParser(description='Automatically translate PO files using Google translate.')
    parser.add_argument('--fro', type=str, help='Source language you want to translate from to (Default: en)',
                        default=kwargs.get('fro', LANGUAGE_SOURCE))
    parser.add_argument('--to', type=str, help='Destination language you want to translate to (Default: et)',
                        default=kwargs.get('to', LANGUAGE_DESTINATION))
    parser.add_argument('--src', type=str, help='Source directory or the files you want to translate',
                        default=kwargs.get('src', UNTRANSLATED_PATH))
    parser.add_argument('--dest', type=str, help='Destination directory you want to translated files to end up in',
                        default=kwargs.get('dest', TRANSLATED_PATH))
    arguments = parser.parse_args()

    for root, dirs, files in os.walk(arguments.src):
        rel_path = os.path.relpath(root, arguments.src)
        for file in files:
            if recognize_po_file(file):
                if not os.path.exists(os.path.join(arguments.dest, rel_path)):
                    os.makedirs(os.path.join(arguments.dest, rel_path))
                found_files = True
                task = solve(os.path.join(arguments.dest, rel_path, file), os.path.join(arguments.src, rel_path, file), arguments)
                asyncio.run(task)

    if not found_files:
        raise Exception(f"Couldn't find any .po files at: '{arguments.src}'")


if __name__ == '__main__':
    run()
