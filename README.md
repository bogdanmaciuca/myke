# myke
A simple C/C++ build tool for small and medium sized projects

```
> py myke.py -h
usage: Myke [-h] [-r] [-v] filename

Simple C/C++ build tool

positional arguments:
  filename

options:
  -h, --help     show this help message and exit
  -r, --run      Runs the program after compilation completes
  -v, --verbose
```

## Myke makefile example
```
Compiler: clang++
Target: MyApp.exe
Sources: main.cpp myImpl.cpp mySecondImpl.cpp
IncPath: my/include/dir my/other/include/dir
Libs: opengl32 glfw3 glew32s
LibPath: my/lib/dir my/second/lib/dir
```
Build by running in the terminal: `py myke.py myMakefile.myke`
