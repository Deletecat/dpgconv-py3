# dpgconv-py3

A python script to transcode video files to DPG format suitable for Nintendo DS (tm).
This fork aims to port [dpgconv](https://github.com/artm/dpgconv/) to Python 3.

Copyright 2007-2011 Anton Romanov <theli (a@t) theli.is-a-geek.org>

TODO:
- Replace mpeg_stat with appropriate equivalent
  - mpeg_stat is ancient and the only places I can find it still being packaged are within OpenMandriva and FreeBSD ports.
  It is unlikely that people will have this on their devices.
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


