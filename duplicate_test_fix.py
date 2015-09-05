#!/usr/bin/python3

import os, shutil, datetime

DIR = 'db/marking'

# Backup first
timestamp = str(datetime.datetime.now()).replace(':', '-').replace(' ', '_')
shutil.make_archive("db-marking-{}".format(timestamp), "zip", DIR)

scripts = []

for base, _, files in os.walk(DIR):
    scripts.extend([os.path.join(base, file) for file in files if file.endswith('.py')])

print("Successfully removed any duplicate error output:")
for script in scripts:
    lines = []
    in_dup = False
    with open(script, 'r') as in_file:
        for line in in_file.readlines():
            if line.startswith('/------------\\'):
                line = line.replace('\\', '--\\')
            if line.startswith('END TEST'):
                in_dup = not in_dup

            if not in_dup:
                lines.append(line)

    with open(script, 'w') as out_file:
        out_file.writelines(lines)


    print(script)

print('-' * 78)
print("Processed {} files".format(len(scripts)))
