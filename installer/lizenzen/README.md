# Licence texts for packages without their own licence file

Some packages that go into the Windows build ship native libraries but no licence file.
Their licences still require the copyright notice and licence text to be distributed with
the program, so the texts are kept here. `tools/lizenzen_sammeln.py` copies them into the
`licenses/` folder of the build (see `MITGELIEFERT` there).

| File | Library | Package | Source of the text |
|---|---|---|---|
| `GLEW-LICENSE.txt` | GLEW (OpenGL Extension Wrangler), `glew32.dll` | `kivy_deps.glew` | https://github.com/nigels-com/glew/blob/master/LICENSE.txt |
| `ANGLE-LICENSE.txt` | ANGLE, `libEGL.dll`, `libGLESv2.dll` | `kivy_deps.angle` | https://github.com/google/angle/blob/main/LICENSE |

The texts are copied unchanged from the projects' repositories.
