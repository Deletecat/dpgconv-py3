# dpgconv-py3

A python script to transcode video files to DPG format suitable for Nintendo DS (tm).
This is a fork of [dpgconv](https://github.com/artm/dpgconv/) which aims to port the script to Python 3.

Copyright 2007-2011 Anton Romanov <theli (a@t) theli.is-a-geek.org>

TODO:
- Bring setup.py up to speed with Python 3.13

Requirements:
- MPlayer/MEncoder
- SoX (with libsox-fmt-mp3)
- Python Pillow library

If you are on Debian, you can install all of the requirements with these commands:

```
apt update && apt install mplayer mencoder sox libsox-fmt-mp3 python3-pil
```

The software is released under the terms of 
[GPL v.2](http://www.gnu.org/licenses/gpl-2.0.html)

Original homepage: http://theli.is-a-geek.org/blog/static/dpgconv


