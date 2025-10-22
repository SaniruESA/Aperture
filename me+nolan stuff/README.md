[project name]

Currently, a high volume of accessibility solutions for blind or deaf people rely on reverse engineering -- for example, subtitles, text-to-speech, and more. These solutions try to work *on top* of software, not *with* it. To address this, we made [project name], which intends to engineer solutions to accessibility and directly address accessibility issues within software.

How it works:
1) Python Library - we developed a Python library to provide an easy-to-use API that facilitates the development of accessibility features needed by blind and/or deaf people.
2) GenAI Code Implentation - we developed an ML model to identify accessibility gaps in the *source code* of software -- this differs from existing solutions, which often look at the output/end result of software to (possibly inaccurately) gauge accessibility quality. After identifying accessibility gaps, we implement solutions to these problems in the software's code using another ML model and our own Python library.