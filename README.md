# dpgconv-py3

A python script to transcode video files to DPG format suitable for Nintendo DS (tm).
This fork aims to port [dpgconv](https://github.com/artm/dpgconv/) to Python 3.

Copyright 2007-2011 Anton Romanov <theli (a@t) theli.is-a-geek.org>

TODO:
- Ensure audio encoding and seeking work for all videos
    - Some videos I have tested will have no sound when played, and will crash Moonshell if you skip ahead. Both of these appear to be linked.
- Replace mpeg_stat with appropriate equivalent
  - mpeg_stat is ancient and the only places I can find it still being packaged are within OpenMandriva and FreeBSD ports.
  It is unlikely that people will have this on their devices.
- Bring setup.py up to speed with Python 3.13

The software is released under the terms of 
[GPL v.2](http://www.gnu.org/licenses/gpl-2.0.html)

Original homepage: http://theli.is-a-geek.org/blog/static/dpgconv


