"""
TODO:
- add support for building libraries and maybe multiple targets at once
"""

import argparse
import sys
import os
import time
import subprocess

# Makefile parser
class ParserException(Exception):
    pass

def Advance(i):
    while makefile[i] == ' ':
        i += 1
    return i

def ParseElement(i):
    element = ''
    while makefile[i] not in ' \n':
        element += makefile[i]
        i += 1
    return (element, i)

def ParseKey(i):
    key = ''
    while makefile[i] != ':' or makefile[i] == ' ':
        if i >= len(makefile) - 1:
            raise ParserException("Myke: error: Expected ':' instead of <EOF>")
        elif makefile[i] == '\n':
            raise ParserException("Myke: error: Expected ':' instead of '\\n'")
        key += makefile[i]
        i += 1
    i = Advance(i)
    i += 1 # Pass the ':' character
    i = Advance(i)
    values = []
    while makefile[i] != '\n':
        (element, i) = ParseElement(i)
        values.append(element)
        i = Advance(i)
    return (key, values, i)

def Parse():
    fileIdx = 0
    cont = {}
    while fileIdx < len(makefile):
        if makefile[fileIdx] in ' \n':
            fileIdx += 1
        else:
            (key, values, fileIdx) = ParseKey(fileIdx)
            cont[key] = values
    return cont

def ParseCache():
    table = {}
    for line in cacheLines:
        tokens = line.split(' ')
        table[tokens[0]] = float(tokens[1])
    return table

# CLI arguments parser
argParser = argparse.ArgumentParser(prog='Myke', description='Simple C/C++ build tool')
argParser.add_argument('filename', type=str)
argParser.add_argument('-r', '--run', action='store_true', help='Runs the program after compilation completes')
argParser.add_argument('-v', '--verbose', action='store_true')
cliArgs = argParser.parse_args()

BUILD_DIR = 'build/'
CACHE_PATH = BUILD_DIR + 'myke_cache.txt'

# Create build directory if doesn't already exist
makefile = open(sys.argv[1], 'r').read()
if not os.path.isdir(BUILD_DIR):
    os.makedirs(BUILD_DIR)

# Read cache file if it exists
cacheLines = []
try:
    cacheLines = open(CACHE_PATH, 'r').readlines()
except FileNotFoundError:
    pass


# Parse the makefile
contents = {}
try:
    contents = Parse()
except ParserException as e:
    print(e)
    print("Myke: Could not compile, there were parsing errors in the configuration file.")
    exit(1)

# Parse the cache file
cacheTable = ParseCache()

# Error checking and more parsing 
errors = False

# Compiler
if 'Compiler' in contents:
    if len(contents['Compiler']) != 1:
        print('Myke error: Expected to have a single element in the [Compiler] field.')
        errors = True
    else:
        compiler = contents['Compiler'][0]
else:
    print('Myke error: Could not find the [Compiler] field in the configuration file.')
    errors = True

# Target (TODO: support both executables and library files)
if 'Target' in contents:
    if len(contents['Target']) != 1:
        print('Myke error: Expected to have a single element in the [Target] field.')
        errors = True
    else:
        compiler = contents['Target'][0]
else:
    print('Myke error: Could not find the [Target] field in the configuration file.')
    errors = True

# C/C++ sources
sources = []
if 'Sources' in contents:
    if len(contents['Sources']) == 0:
        print('Myke: error: Expected at least one element in the [Sources] field.')
        errors = True
    else:
        for file in contents['Sources']:
            try:
                lastModTime = os.path.getmtime(file)
                lastCompileTime = cacheTable.get(file, 0)
                if lastModTime > lastCompileTime:
                    sources.append(file)
            except OSError:
                print('Myke error: Could not find file:', file)
else:
    print('Myke: error: Could not find the [Sources] field.')
    errors = True
    pass

# Include and libraries path
incPaths = ['-I' + p for p in contents.get('IncPath', [])]
libPaths = ['-L' + p for p in contents.get('LibPath', [])]

# Libraries
libraries = ['-l' + p for p in contents.get('Libs', [])]

if errors == True:
    print('Myke: Could not compile, there were semantic errors in the configuration file')
    exit(1)

cacheFile = open(CACHE_PATH, 'w')
# Running the compiler
# Only compile if there are changes in the source code
if len(sources) != 0:
    print('Myke: Compiling object files...')
    # Running the compiler
    # The compiler will be run in the build directory, not in the working directory
    sourcesPaths = ['../' + s for s in sources]
    args = [contents['Compiler'][0], '-c'] + sourcesPaths
    if cliArgs.verbose:
        args.append('-v')
    procCompleted = subprocess.run(args, cwd=BUILD_DIR)
    # If compilation was successful update cache
    if procCompleted.returncode == 0:
        for source in sources:
            cacheFile.write(source + ' ' + str(time.time()) + '\n')
        print('Myke: Recompiled:', ', '.join(sources))
    else:
        print('Mike: Compilation failed.')
        exit(1)
else:
    print('Myke: Object files are up-to-date.')
# Delete .o files that are no longer necesary
for source in cacheTable:
    if source not in contents['Sources']:
        os.remove(BUILD_DIR + source.split('.')[0] + '.o')

# Only add the sources if they haven't been recompiled and their
# compile times remained the same but don't add the sources which
# were deleted from the makefile
for source in cacheTable:
    if source not in sources and source in contents['Sources']:
        cacheFile.write(source + ' ' + str(cacheTable[source]) + '\n')

# Linking
print('Myke: Linking...')
objectsPaths = [p.split('.')[0] + '.o' for p in contents['Sources']]
args = [contents['Compiler'][0], '-o', contents['Target'][0]]
args += objectsPaths + libPaths + libraries
if cliArgs.verbose:
    args.append('-v')
procCompleted = subprocess.run(args, cwd=BUILD_DIR)
if procCompleted.returncode != 0:
    print('Myke: Linking failed.')
    exit(1)

print("Myke: Compilation finished")

if cliArgs.run:
    procCompleted = subprocess.run([BUILD_DIR + contents['Target'][0]])
    print('Process exited with code ' + str(procCompleted.returncode) + '.')

exit(0)
