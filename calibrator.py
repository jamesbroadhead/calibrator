#!/usr/bin/env python2
from __future__ import print_function

from collections import defaultdict
import csv
import re
import shlex
import shutil
import subprocess
import sys
import tempfile

from os.path import basename, dirname, expanduser
from os.path import join as pjoin

DEFAULT_LIBRARY_PATH = expanduser('~/checkouts/ebooks/')

EXTRA_TITLES = 'Extra titles'
EXTRA_BOOK_FORMATS = 'Extra book formats'
EXTRA_AUTHORS = 'Extra authors'

RAW_TITLE = 'raw_title'
DIRPATH = 'dirpath'
FILEPATH = 'filepath'

to_skip = {
    'Invalid titles',
    'Invalid authors',
    'Missing book formats',
}


def run(cmd):
    proc = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    # TODO: make calibredb use stderr
    stdout, _ = proc.communicate()

    if proc.returncode != 0:
        print(stdout)
        raise subprocess.CalledProcessError(proc.returncode, cmd, output=stdout)
    return stdout


def calibredb(subcommand, args):
    cmd = 'calibredb {} {}'.format(subcommand, args)
    return run(cmd)


def parse_check_library_output(unparsed):
    out = defaultdict(list)

    for line in unparsed:
        if not line:
            continue

        linetype = line[0]

        if linetype == 'Extra book formats':
            parsed = {RAW_TITLE: line[1], FILEPATH: line[2]}

        elif linetype == 'Extra authors':
            parsed = {RAW_TITLE: line[1], 'dirpath': line[2]}

        elif linetype == EXTRA_TITLES:
            parsed = {RAW_TITLE: line[1], DIRPATH: line[2]}
        elif linetype in to_skip:
            parsed = line
        else:
            raise Exception('Unknown type! {}'.format(linetype))
        out[linetype].append(parsed)

    return out


def raw_title_to_title(raw_title):
    """
    foo (1234)  => foo
    foo (1234) (3234) => foo (1234)
    """
    return re.sub(r'\(\d*\)$', '', raw_title).strip()


def raw_title_to_book_id(raw_title):
    """
    foo (1234)  => 1234
    foo (1234) (3234) => 3234
    """
    return re.findall(r'\(\d*\)$', raw_title)[0].strip(' () ')


def dirpath_to_author(dirpath):
    return basename(dirname(dirpath))


def filepath_to_book_id(filepath):
    raw_title = basename(dirname(filepath))
    return raw_title_to_book_id(raw_title)


def process_extra_authors(_library_path, extra_authors_data):
    from pprint import pprint
    if extra_authors_data:
        print('Extra authors is unimplemented - please add & file a PR :)')
        pprint(extra_authors_data)


def process_extra_titles(library_path, extra_titles_data):
    for data in extra_titles_data:
        raw_title = data[RAW_TITLE]
        dirpath = pjoin(library_path, data[DIRPATH])

        title = raw_title_to_title(raw_title)
        author = dirpath_to_author(dirpath)

        print("Attempting to add: {title} by {author} found here: {dirpath}".format(
            title=title, author=author, dirpath=dirpath))

        # If the book isn't moved out of the dir first, it'll create a new tracked
        #   dir, but remain as an untracked dir
        temp_dir_path = tempfile.mkdtemp(prefix='calibrator-tmp')
        new_path = pjoin(temp_dir_path, title)
        shutil.move(dirpath, new_path)

        cmd = '--library-path={library_path} --duplicates --title="{title}" --authors="{author}" --recurse --one-book-per-directory "{dirpath}"'.format(
            title=title, author=author, dirpath=new_path, library_path=library_path)
        stdout = calibredb('add', cmd)
        print('Result: {stdout}'.format(stdout=stdout))

        # TODO: make `calibredb` support exit codes, then clear temp dirs
        #shutil.rmtree(temp_dir_path)
        print(
            'If you are happy with the above output, you should delete this temporary directory: {path}'.
            format(path=temp_dir_path))


def process_extra_formats(library_path, extra_formats_data):

    for data in extra_formats_data:
        filepath = pjoin(library_path, data['filepath'])

        book_id = filepath_to_book_id(filepath)

        print("Attempting to add_format: to {book_id}, adding: {filepath}".format(
            book_id=book_id, filepath=filepath))

        temp_dir_path = tempfile.mkdtemp(prefix='calibrator-tmp')
        filename = basename(filepath)
        new_path = pjoin(temp_dir_path, filename)
        shutil.move(filepath, new_path)

        cmd = '--library-path={library_path} --dont-replace "{book_id}" "{filepath}"'.format(
            filepath=new_path, library_path=library_path, book_id=book_id)
        stdout = calibredb('add_format', cmd)
        print('Result: {stdout}'.format(stdout=stdout))

        # TODO: make `calibredb` support exit codes, then clear temp dirs
        #shutil.rmtree(temp_dir_path)
        print(
            'If you are happy with the above output, you should delete this temporary directory: {path}'.
            format(path=temp_dir_path))


def main(library_path):
    check_library_output = run_check_library(library_path)
    reader = csv.reader(check_library_output.split('\n'))
    data = parse_check_library_output(reader)

    process_extra_titles(library_path, data[EXTRA_TITLES])
    process_extra_authors(library_path, data[EXTRA_AUTHORS])
    process_extra_formats(library_path, data[EXTRA_BOOK_FORMATS])


def run_check_library(library_path):
    stdout = calibredb('check_library',
                       '--csv --library-path={} --ignore_names=.git'.format(library_path))
    return stdout


if __name__ == '__main__':
    if len(sys.argv) == 2:
        library_path_arg = sys.argv[1]
    else:
        library_path_arg = DEFAULT_LIBRARY_PATH
    main(library_path_arg)
