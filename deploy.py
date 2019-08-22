import subprocess
import mpy_cross
import os

PORT = '/dev/ttyUSB0'
OUT_DIR = './build'

FILES = [
    ('main.py', 'main.py'),
    ('wrap.py', 'wrap.py'),
    # ('umqttsimple.py', 'umqttsimple.py'),
]


def cross_compile(file):
    print('cross_compile {}'.format(file))
    name, ext = os.path.splitext(file)
    out = os.path.join(OUT_DIR, name + '.mpy')

    try:
        os.makedirs(os.path.dirname(out))
    except FileExistsError:
        pass

    p = mpy_cross.run(file, '-o', out)
    p.wait()
    return out


def upload(file, destination):
    print('Uploading', file, destination)
    subprocess.call(['ampy', '-p', PORT, 'put', file, destination])


ensured_dirs = []


def ensure_dir_exists(path):
    global ensured_dirs
    current_path = ''
    for directory in os.path.dirname(path).split('/'):
        current_path = os.path.join(current_path, directory)
        if current_path in ensured_dirs or len(current_path) == 0:
            continue

        subprocess.call(['ampy', '-p', PORT, 'mkdir', current_path])

        ensured_dirs.append(current_path)


def main():
    try:
        os.makedirs(OUT_DIR)
    except FileExistsError:
        pass

    for file in FILES:
        if isinstance(file, str):
            path = file
            destination = file
        else:
            path, destination = file

        ext = os.path.splitext(destination)[1]
        ensure_dir_exists(destination)

        if ext == '.mpy':
            path = cross_compile(path)

        upload(path, destination)


main()
