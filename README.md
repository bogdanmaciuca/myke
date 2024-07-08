# myke
A simple C/C++ build tool for small MinGW/Clang projects

```
> py myke.py -h
usage: Myke [-h] [-r] [-v] [-b] [-w] [-c] filename

Simple C/C++ build tool

positional arguments:
  filename

options:
  -h, --help      show this help message and exit
  -r, --run       runs the program after compilation completes
  -v, --verbose
  -b, --build     builds the target even if no changes have been made since last build
  -w, --warnings  builds everything with all warnings enabled
  -c, --clean     clean the build folder before doing anything else
```

## Myke makefile example
```
Compiler: clang++
Target: MyApp.exe
Sources: main.cpp myImpl.cpp mySecondImpl.cpp
```
Build by running in the terminal: `py myke.py myMakefile.myke`

## Myke makefile fields
- `Compiler`: a path to the compiler you wish to use
- `Target`: executable name (must include extension)
- `TargetLib`: static library name (must include extension and be prefixed with 'lib' e.g. libMYLIB.a)
- `Sources`: paths to all C/C++ files
- `IncPath`: paths of include directories
- `LibPath`: paths of library directories
- `Libs`: libraries to link against
- `Args`: additional arguments to pass to the compiler for building the object files
- `LinkerArgs`: additional arguments to pass to the compiler for linking

## Features
- easy to use, lightweight, works out of the box
- faster compilation times by only compiling modified files

## Notes
- only one target is supported per makefile
- can only compile source files from the current directory
- can only build static libraries (support for dynamic libraries will be added in the near future)
- should work with any compiler that shares the most common CLI arguments with MinGW and Clang
