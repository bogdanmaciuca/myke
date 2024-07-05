"""
TODO:
- add support for building libraries: linux and mingw
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

# CLI arguments parser
argParser = argparse.ArgumentParser(prog='Myke', description='Simple C/C++ build tool')
argParser.add_argument('filename', type=str)
argParser.add_argument('-r', '--run', action='store_true', help='runs the program after compilation completes')
argParser.add_argument('-v', '--verbose', action='store_true')
argParser.add_argument('-b', '--build', action='store_true', help='builds the target even if no changes have been made since last build')
argParser.add_argument('-w', '--warnings', action='store_true', help='builds everything with all warnings enabled')
cliArgs = argParser.parse_args()

BUILD_DIR = 'build/'

# Create build directory if doesn't already exist
makefile = open(sys.argv[1], 'r').read()
if not os.path.isdir(BUILD_DIR):
    os.makedirs(BUILD_DIR)

# Parse the makefile
contents = {}
try:
    contents = Parse()
except ParserException as e:
    print(e)
    print("Myke: Could not compile, there were parsing errors in the configuration file.")
    exit(1)

# Error checking and more parsing 
errors = False

# Compiler
if 'Compiler' in contents:
    if len(contents['Compiler']) != 1:
        print('Myke: error: Expected to have a single element in the [Compiler] field.')
        errors = True
else:
    print('Myke: error: Could not find the [Compiler] field in the configuration file.')
    errors = True

# Target
targetIsLib = False
targetName = ''
if 'Target' in contents:
    if len(contents['Target']) != 1:
        print('Myke: error: Expected to have a single element in the [Target] field.')
        errors = True
    targetName = contents['Target'][0]
elif 'TargetLib' in contents:
    targetIsLib = True
    if len(contents['TargetLib']) != 1:
        print('Myke: error: Expected to have a single element in the [TargetLib] field.')
        errors = True
    targetName = contents['TargetLib'][0]
else:
    print('Myke: error: Could not find the [Target] nor the [TargetLib] field in the configuration file.')
    errors = True
if 'Target' in contents and 'TargetLib' in contents:
    print('Myke: error: Build configuration file can have either [Target] or [TargetLib], not both at the same time.')
    errors = True

# C/C++ sources
sources = []
if 'Sources' in contents:
    if len(contents['Sources']) == 0:
        print('Myke: error: Expected at least one element in the [Sources] field.')
        errors = True
    else:
        # If the script is run with the --build option, rebuild everything
        if cliArgs.build:
            sources = contents['Sources']
        else:
            for file in contents['Sources']:
                srcLastModTime = 0
                objLastModTime = 0
                try: srcLastModTime = os.path.getmtime(file)
                except OSError: print('Myke error: Could not find file:', file)
                try: objLastModTime = os.path.getmtime(BUILD_DIR + file.split('.')[0] + '.o')
                except OSError: pass
                if srcLastModTime > objLastModTime:
                    sources.append(file)
        sources = [s.replace('\\', '/') for s in sources]
else:
    print('Myke: error: Could not find the [Sources] field.')
    errors = True
    pass

# Include and libraries path
incPaths = []
for path in contents.get('IncPath', []):
    if os.path.isabs(path): libPaths.append('-I' + path)
    else: libPaths.append('-I../' + path)
incPaths.append('-I../') # Clang runs in a different directory so we need to append the running directory of the myke makefile 
libPaths = []
for path in contents.get('LibPath', []):
    if os.path.isabs(path): libPaths.append('-L' + path)
    else: libPaths.append('-L../' + path)
libPaths.append('-L../') # Clang runs in a different directory so we need to append the running directory of the myke makefile 

# Libraries
libraries = ['-l' + p for p in contents.get('Libs', [])]

# Additional arguments
additionalArgs = contents.get('Arguments', [])
linkerAdditionalArgs = contents.get('LinkerArgs', [])

if errors == True:
    print('Myke: Could not compile, there were semantic errors in the configuration file')
    exit(1)

# Running the compiler
# Only compile if there are changes in the source code
if len(sources) != 0:
    print('Myke: Compiling object files...')
    # Running the compiler
    # The compiler will be run in the build directory, not in the working directory
    sourcesPaths = ['../' + s for s in sources]
    args = [contents['Compiler'][0], '-c'] + sourcesPaths + incPaths + additionalArgs
    if cliArgs.verbose: args.append('-v')
    if cliArgs.warnings: args.append('-Wall')
    procCompleted = subprocess.run(args, cwd=BUILD_DIR)
    
    if procCompleted.returncode == 0:
        print('Myke: Recompiled:', ', '.join(sources))
    else:
        print('Mike: Compilation failed.')
        exit(1)
else:
    print('Myke: Object files are up-to-date.')

# Delete .o files that are no longer necesary
for file in os.listdir(BUILD_DIR):
    filename = os.fsdecode(file)
    if filename.split('.')[0] not in [source.split('.')[0] for source in contents['Sources']] and filename != targetName:
        os.remove(BUILD_DIR + filename)

# Linking
print('Myke: Linking...')
objectsPaths = [p.split('/')[-1].split('.')[0] + '.o' for p in contents['Sources']]
args = [contents['Compiler'][0], '-o', targetName]
args += objectsPaths + libPaths + libraries + linkerAdditionalArgs
if targetIsLib:
    # Get the compiler used
    if 'casdlang' in contents['Compiler'][0]:
        args.append('-fuse-ld=llvm-lib')
    else:
        print('Myke: error: compiler not supported for linking. Use the [LinkerArgs] field to supply the compiler with the appropriate options for linking and use [Target] instead of [TargetLib].')
        exit(1)
if cliArgs.verbose: args.append('-v')
if cliArgs.warnings: args.append('-Wall')
procCompleted = subprocess.run(args, cwd=BUILD_DIR)
if procCompleted.returncode != 0:
    print('Myke: Linking failed.')
    exit(1)

print("Myke: Compilation finished")

if cliArgs.run:
    if targetIsLib:
        print('Myke: Cannot run target as it is a library.')
        exit(1)
    else:
        procCompleted = subprocess.run([BUILD_DIR + targetName])
        print('Myke: Process exited with code ' + str(procCompleted.returncode) + '.')

exit(0)
