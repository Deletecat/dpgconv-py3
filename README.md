# dpgconv-py3

A python script to transcode video files to DPG format suitable for Nintendo DS (tm).
This fork aims to port [dpgconv](https://github.com/artm/dpgconv/) to Python 3.

Copyright 2007-2011 Anton Romanov <theli (a@t) theli.is-a-geek.org>

TODO:
- Fix audio encoding
    - Some videos I have tested will have no sound when played.
- Fix seeking issue within Moonshell
  - Not entirely sure what's causing this. Moonshell will crash if you skip forward while playing a video.
  - Possibly something to do with the GOP part of the header?
- Replace mpeg_stat with appropriate equivalent
  - mpeg_stat is ancient and the only places I can find it still being packaged are within OpenMandriva and FreeBSD ports.
  It is unlikely that people will have this on their devices.

The software is released under the terms of 
[GPL v.2](http://www.gnu.org/licenses/gpl-2.0.html)

Original homepage: http://theli.is-a-geek.org/blog/static/dpgconv


