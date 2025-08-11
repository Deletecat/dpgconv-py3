#!/usr/bin/env python3
# -*- coding: utf-8-*-
#
# DPG Converter for linux
# released under GPL-2
# 
"""A script to transcode video files to DPG format suitable for
   Nintendo DS (tm)
   
dpgconv.py file1 file2 file3 ... fileN
command line options:
	--dpg
		0,1,2,3,4 sets DPG version.. default is DPG4

	-2,--tp 
		extra high quality 2-pass encoded video
	-q,--hq
		high quality video
	-l,--lq
		low quality video(takes no effect when --hq,-q is set)]
	default is normal quality
	
	-v,--vbps xxx
		sets video stream bps in kb/s(default: 256)
	-a,--abps xxx
		sets audio stream bps kb/s (default: 128)
	-f,--fps xx
		sets video frames per second (default:15)
	-z,--hz
		sets audio frequency (default:32000)
	-c,--channels
		2 - stereo, 1 - mono
		default is to leave as is unless input audio channels
		number is bigger then 2 ... then default is stereo
	--aid n
		use audio track n
	--volnorm
		normalize volume
	
	--height xxx
		destination video height (default: 192)
	--width xxx
		destination video width (default: 256)
	--keep-aspect
		try to keep aspect ratio
	
	NOTE:	width/height have no effect when --keep-aspect is set

	Video Thumbnail
	--thumb xxx
		you can use this option if you convert only one video, or if
		you want the same preview for all videos.
		thumbnails are only in DPG4 videos.
		all formats supported by python imaging library can be used.
		the image will be resized and converted automically.
		
		NOTE: thumbnail will be generated autimatically
		from input video if you won't set this parameter

	Hardcoding subtitles
	--nosub
		do no try autoloading of subtitles
		(default is to try to load subtitle with matching filename)
	--sub,-s xxx
		Specify subtitles for hardcoding into video output
		(is obviously only usable if you specify one file at a time)
	--sid n
		use subtitle track n
	--subcp xxx
		specify subtitles encoding
	--font xxx
		specify font for subtitles
  EXAMPLE:
    --font ~/arial-14/font.desc
    --font ~/arialuni.ttf
    --font 'Bitstream Vera Sans'

  You can specify font, subcp and other additional mencoder parameters in
	~/.mplayer/mencoder.conf
  EXAMPLE:
	font=/usr/local/share/fonts/msfonts/comic.ttf
	subcp=cp1251

"""

import sys
import os
import mmap
from PIL import Image
import tempfile
from optparse import OptionParser
import re
import shutil
import stat
import struct
import subprocess

#Print a help message if requested.
if "-h" in sys.argv or "-help" in sys.argv or "--help" in sys.argv:
	print(__doc__)
	sys.exit(0)

def conv_vid(file):
	ident = subprocess.run(["mplayer", "-frames", "1", "-vo", "null", "-ao", "null", "-identify", "-nolirc", file], shell=False, capture_output=True, encoding="utf-8")
	frames = float(re.compile("ID_VIDEO_FPS=(.*)").search(ident.stdout).group(1))
	if options.tp and frames < 24:
		# videos lower than 24FPS will result in duplicate frames and other issues without interpolation
		print("Input video framerate below what is required for double pass encoding (24FPS). Selecting high quality video encoding instead.")
		options.tp = False
		options.hq = True

	if options.aspect:
		# calculate aspect ratio from width/height values
		# fixes issue with mplayer where some videos show as having 0.0000 aspect ratio
		width = float(re.compile("ID_VIDEO_WIDTH=(.*)").search(ident.stdout).group(1))
		height = float(re.compile("ID_VIDEO_HEIGHT=(.*)").search(ident.stdout).group(1))
		aspect_ratio = width/height

		print(f"Aspect ratio = {aspect_ratio}")
		if int(256.0/aspect_ratio) <= 192:
			options.width=256
			options.height=int(256.0/aspect_ratio)
		else:
			options.height=192
			options.width=int(aspect_ratio*192.0)
		print(f"Target size set to {options.width}x{options.height}.")

	v_cmd = ["mencoder"]
	if options.tp:
		two_pass_log = tempfile.NamedTemporaryFile()
		if options.fps < 24:
			print("mencoder won't work with double pass and fps < 24, forcing fps = 24")
			options.fps = 24
		v_cmd.extend([file, "-v", "-ofps", str(options.fps), "-sws", "9", "-vf", f"scale={options.width}:{options.height}:::3,expand=256:192,harddup", "-passlogfile", two_pass_log.name, "-nosound", "-ovc", "lavc", "-lavcopts", f"vcodec=mpeg1video:vstrict=-2:mbd=2:trell:o=mpv_flags=+mv0:vmax_b_frames=2:cmp=6:subcmp=6:precmp=6:dia=4:predia=4:bidir_refine=4:mv0_threshold=0:last_pred=3:vbitrate={options.vbps}"])
	elif options.hq:
		v_cmd.extend([file, "-v", "-ofps", str(options.fps), "-sws", "9", "-vf", f"scale={options.width}:{options.height}:::3,expand=256:192,harddup", "-nosound", "-ovc", "lavc", "-lavcopts", f"vcodec=mpeg1video:vstrict=-2:mbd=2:trell:o=mpv_flags=+mv0:keyint=10:cmp=6:subcmp=6:precmp=6:dia=3:predia=3:last_pred=3:vbitrate={options.vbps}", "-o", MPGTMP.name, "-of", "rawvideo"])
	elif options.lq:
		v_cmd.extend([file, "-v", "-ofps", str(options.fps), "-vf", f"scale={options.width}:{options.height},expand=256:192,harddup", "-nosound", "-ovc", "lavc", "-lavcopts", f"vcodec=mpeg1video:vstrict=-2:keyint=10:vbitrate={options.vbps}", "-o", MPGTMP.name, "-of", "rawvideo"])
	else:
		v_cmd.extend([file, "-v", "-ofps", str(options.fps), "-sws", "9", "-vf", f"scale={options.width}:{options.height}:::3,expand=256:192,harddup", "-nosound", "-ovc", "lavc", "-lavcopts", f"vcodec=mpeg1video:vstrict=-2:keyint=10:mbd=2:trell:o=mpv_flags=+mv0:cmp=2:subcmp=2:precmp=2:vbitrate={options.vbps}", "-o", MPGTMP.name, "-of", "rawvideo"])
	
	if options.nosub:
		if options.sub is not None:
			v_cmd.extend(["-sub",options.sub])
	else:
		basename = os.path.splitext ( file )[0]
		if options.sid is not None:
			v_cmd.extend(["-sid", str(options.sid)])
		if options.sub is not None:
			v_cmd.extend(["-sub", options.sub])
		elif os.path.exists ( basename + ".ass" ):
			v_cmd.extend(["-sub", f"{basename}.ass"])
		elif os.path.exists ( basename + ".srt" ):
			v_cmd.extend(["-sub", f"{basename}.srt"])
		elif os.path.exists ( basename + ".sub" ):
			v_cmd.extend(["-sub", f"{basename}.sub"])
		elif os.path.exists ( basename + ".ssa" ):
			v_cmd.extend(["-sub", f"{basename}.ssa"])
	
	if options.subcp is not None:
		v_cmd.extend["-subcp", options.subcp]
	if options.font is not None:
		v_cmd.extend(["-font", f'"{options.font}"'])

	if options.tp:
		v_cmd_two = v_cmd.copy()
		v_cmd[-1] += ':vpass=1:turbo:vb_strategy=2:vrc_maxrate=500:vrc_minrate=0:vrc_buf_size=327:intra_matrix=8,9,12,22,26,27,29,34,9,10,14,26,27,29,34,37,12,14,18,27,29,34,37,38,22,26,27,31,36,37,38,40,26,27,29,36,39,38,40,48,27,29,34,37,38,40,48,58,29,34,37,38,40,48,58,69,34,37,38,40,48,58,69,79:inter_matrix=16,18,20,22,24,26,28,30,18,20,22,24,26,28,30,32,20,22,24,26,28,30,32,34,22,24,26,30,32,32,34,36,24,26,28,32,34,34,36,38,26,28,30,32,34,36,38,40,28,30,32,34,36,38,42,42,30,32,34,36,38,40,42,44'
		v_cmd.extend(["-o", MPGTMP.name, "-of", "rawvideo"])
		v_cmd_two[-1] += ':vpass=2:vrc_maxrate=500:vrc_minrate=0:vrc_buf_size=327:keyint=10:intra_matrix=8,9,12,22,26,27,29,34,9,10,14,26,27,29,34,37,12,14,18,27,29,34,37,38,22,26,27,31,36,37,38,40,26,27,29,36,39,38,40,48,27,29,34,37,38,40,48,58,29,34,37,38,40,48,58,69,34,37,38,40,48,58,69,79:inter_matrix=16,18,20,22,24,26,28,30,18,20,22,24,26,28,30,32,20,22,24,26,28,30,32,34,22,24,26,30,32,32,34,36,24,26,28,32,34,34,36,38,26,28,30,32,34,36,38,40,28,30,32,34,36,38,42,42,30,32,34,36,38,40,42,44'
		v_cmd_two.extend(["-o", MPGTMP.name, "-of", "rawvideo"])

	print("Transcoding video: ...",end="\r")
	proc = subprocess.run(v_cmd,shell=False,universal_newlines=True,capture_output=True)

	print("Transcoding video: done")
	if options.tp:
		print("Transcoding video, pass 2: ...", end="\r")
		proc = subprocess.run(v_cmd_two,shell=False,universal_newlines=True,capture_output=True)
		print("Transcoding video, pass 2: done")


def conv_aud(file):
	vol=''
	if options.volnorm:
		vol="volnorm,"
	identify = subprocess.run(["mplayer","-frames","0","-vo","null","-ao","null","nolirc","-identify",file], shell=False, capture_output=True, encoding="utf-8").stdout
	m = re.compile("([0-9]*)( ch)").search(identify)
	if m:
		a_cmd = ["mencoder",file,"-v","-of","rawaudio","-oac","twolame","-ovc","copy","-twolameopts",f"br={options.abps}"]
		c = int(m.group(1))
		if options.channels is None and options.dpg != 0:
			if c >= 2:
				a_cmd[-1] += ':mode=stereo'
				a_cmd.extend(["-o", MP2TMP.name, "-af", f"{vol}channels=2,resample={options.hz}:1:2"])
			else:
				a_cmd[-1] += ':mode=mono'
				a_cmd.extend(["-o", MP2TMP.name, "-af", f"{vol}channels=1,resample={options.hz}:1:2"])
		elif options.channels >= 2 and options.dpg != 0:
			a_cmd[-1] += ':mode=stereo'
			a_cmd.extend(["-o", MP2TMP.name, "-af", f"{vol}channels=2,resample={options.hz}:1:2"])
		else:
			a_cmd[-1] += ':mode=mono'
			a_cmd.extend(["-o", MP2TMP.name, "-af", f"{vol}channels=1,resample={options.hz}:1:2"])
	else:
		# This condition will only be true if the video does not have an audio stream, or if mplayer errors out for some other reason.
		# Having no audio stream will crash Moonshell as it's expecting something that doesn't exist
		vid_length = re.compile("ID_LENGTH=([0-9]*.[0-9]*)").search(identify) # ID_LENGTH corresponds to the video length in seconds
		if vid_length:
			seconds = float(vid_length.group(1))
			# use sox with the mp3 libsox format to generate a silent mp2 file
			a_cmd = ["sox", "-n", "-r", "48000", "-c", "1", MP2TMP.name, "trim", "0.0", str(seconds)]
		else:
			# this shouldn't occur if the user is passing an actual video file to the script
			print(f"Error! See Mplayer output below:\n{identify}")
			sys.exit(1)

	if options.aid is not None:
		a_cmd.extend(["-aid", str(options.aid)])

	print("Transcoding audio: ...",end="\r")
	proc = subprocess.run(a_cmd,shell=False,universal_newlines=True,capture_output=True)
	print("Transcoding audio: done")

def write_header(frames):
	print("Creating header")

	audiostart=36
	if options.dpg == 1:
		audiostart += 4
	elif (options.dpg == 2) | (options.dpg == 3):
		audiostart += 12
	elif options.dpg == 4:
		audiostart += 98320
	audiosize = os.stat(MP2TMP.name)[stat.ST_SIZE]
	videosize = os.stat(MPGTMP.name)[stat.ST_SIZE]
	videostart = audiostart + audiosize
	videoend = videostart + videosize
	pixel_format = 3
	f=open(HEADERTMP.name, 'wb')
	DPG = f'DPG{options.dpg}'.encode('utf-8')
	headerValues = [ DPG, int(frames), options.fps, 0, options.hz , 0 ,int(audiostart), int(audiosize), int(videostart), int(videosize) ]
	
	f.write (struct.pack( "4s" , headerValues[0]))
	f.write (struct.pack ( "<l" , headerValues[1]))
	f.write (struct.pack ( ">h" , headerValues[2]))
	f.write (struct.pack ( ">h" , headerValues[3]))
	f.write (struct.pack ( "<l" , headerValues[4]))
	f.write (struct.pack ( "<l" , headerValues[5]))
	f.write (struct.pack ( "<l" , headerValues[6]))
	f.write (struct.pack ( "<l" , headerValues[7]))
	f.write (struct.pack ( "<l" , headerValues[8]))
	f.write (struct.pack ( "<l" , headerValues[9]))

	if options.dpg >= 2:
		gopsize = os.stat(GOPTMP.name)[stat.ST_SIZE]
		f.write (struct.pack ( "<l" , videoend ))
		f.write (struct.pack ( "<l" , gopsize))
	if options.dpg != 1:
		f.write (struct.pack ( "<l" , pixel_format ))
	if options.dpg == 4:
		f.write (struct.pack ( "4s" , b"THM0"))

	f.close()

def mpeg_stat():
	"""
	from mpeg_stat source and mpeg header reference:
	 - picture start code: 0x00000100
	 - sequence start code: 0x000001b3
	 - GOP start code: 0x000001b8
	For every sequence, there's 10 pictures, due to the keyframe interval used during the transcoding stage being 10 frames.
	If the keyframe interval is tweaked, the for loop will have to be tweaked as well.
	These pictures continue to the end of the file, so if there's less than 10 pictures in a sequence (or no sequence after 10 pictures), we've reached EOF.
	Despite the GOP start code being a thing, DPG2+ doesn't seem to use it?
	"""
	picture_start_code = b'\x00\x00\x01\x00'
	sequence_start_code = b'\x00\x00\x01\xb3'
	last_index = 0
	frames = 0

	with open(MPGTMP.name, "rb") as reader:
		# DPG2+ uses GOP for faster seeking
		if options.dpg >= 2:
			gop = open(GOPTMP.name,"wb")

		# use mmap so we don't have to read chunks of the video in
		file_mmap = mmap.mmap(reader.fileno(),0,access=mmap.ACCESS_READ)

		# loop until end of file reached
		while True:
			# check for the start of a sequence - returns -1 if EOF
			last_index = file_mmap.find(sequence_start_code,last_index)
			if(last_index == -1):
				break	# EOF
			elif options.dpg >= 2:
				# write info required for GOP if DPG2 or above
				gop.write(struct.pack("<l",frames))
				gop.write(struct.pack("<l",last_index))
			# increment last index so as to not find the same start code again
			last_index += 1

			# loop 10 times for each picture
			for i in range(10):
				# check if next picture exists - returns -1 if EOF
				last_index = file_mmap.find(picture_start_code,last_index)
				if(last_index == -1):
					break	# EOF
				# increment frame counter and last index
				frames += 1
				last_index += 1

		# we need to close the GOP file manually
		if options.dpg >= 2:
			gop.close()

	return frames

def conv_file(file):
	if not os.path.lexists(file):
		print(f"File {file} doesn't exist")
	print("Converting " + file)
	conv_vid (file)
	conv_aud(file)
	frames = mpeg_stat()
	if frames == 0:
		print("Error getting frame count. Please open an issue: https://github.com/Deletecat/dpgconv-py3")
		return
	if options.dpg == 4:
		conv_thumb(options.thumb,frames)
	write_header(frames)
	dpgname = os.path.basename(os.path.splitext(file)[0]) + ".dpg"
	
	print("Creating " + dpgname)
	
	if options.dpg == 4:
		concat(dpgname,HEADERTMP,THUMBTMP,MP2TMP,MPGTMP,GOPTMP)
	elif (options.dpg == 2) | (options.dpg == 3):
		concat(dpgname,HEADERTMP,MP2TMP,MPGTMP,GOPTMP)
	else:
		concat(dpgname,HEADERTMP,MP2TMP,MPGTMP)
	
	print(f"Done converting {file} to {dpgname}")

def conv_thumb(file, frames):
	"""Converts PIL internal (24 or 32bit per pixel RGB) image
  	to 16 bit per pixel thumbnail.
	Takes a PNG screenshot if no file given.
	"""
	shot_file = None
	if not os.path.lexists(file):
		print("Preview file will be generated from video file.")
		shot_file = SHOTTMP.name +"/00000001.png"
		s_cmd = ["mplayer", MPGTMP.name, "-nosound", "-vo", f"png:outdir={SHOTTMP.name}", "-frames", "1", "-ss", f"{int((int(frames)/options.fps)/10)}"]
		subprocess.run(s_cmd,shell=False,capture_output=True)
		file = shot_file
	
	im = Image.open(file)
	width, height = im.size
	size = (256, 192)
	dest_w, dest_h = size

	if (width*dest_h<height*dest_w):
		matrix=[ height/dest_h, 0.0, -(dest_w -(width*dest_h/height))//2,
				0.0, height/dest_h, 0.0 ]
	else:
		matrix=[ width/dest_w, 0.0, 0.0,
				0.0, width/dest_w, -(dest_h -(height*dest_w/width))//2 ]
	thumbim = im.transform(size, Image.AFFINE, matrix , Image.BICUBIC).getdata()

	data = []
	for i in range(dest_h):
		row = []
		for j in range(dest_w):
			red, green, blue = thumbim[i*dest_w+j][0], thumbim[i*dest_w+j][1], thumbim[i*dest_w+j][2]
			pixel = (( 1 << 15)
				| ((blue >> 3) << 10)
				| ((green >> 3) << 5)
				| (red >> 3))
			row.append(pixel)
		data.append(row)
	row_fmt=('H'*dest_w)
	thumb_data = b''.join(struct.pack(row_fmt, *row) for row in data)

	thumb_file=open(THUMBTMP.name, 'wb')
	thumb_file.write(thumb_data)
	thumb_file.close()

	#must be sure shot_file is always named 00000001.png
	#for batch processing
	if shot_file is not None:
		if os.path.lexists(shot_file) :
			os.unlink(shot_file)

def init_names():
	global MPGTMP,MP2TMP,HEADERTMP,GOPTMP,THUMBTMP,SHOTTMP
	MP2TMP=tempfile.NamedTemporaryFile(suffix=".mp2")
	MPGTMP=tempfile.NamedTemporaryFile()
	HEADERTMP=tempfile.NamedTemporaryFile()
	GOPTMP=tempfile.NamedTemporaryFile()
	THUMBTMP=tempfile.NamedTemporaryFile()
	SHOTTMP=tempfile.TemporaryDirectory()

def concat(out,*files):
	outfile = open(out,'wb')
	for name in files:
		outfile.write(open(name.name,"rb").read())
	outfile.close()

parser = OptionParser()
parser.add_option("-f","--fps", type="int", dest="fps" , default=15)
parser.add_option("-q","--hq", action="store_true", dest="hq", default=False)
parser.add_option("-l","--lq", action="store_true", dest="lq", default=False)
parser.add_option("-v","--vbps", type="int", dest="vbps", default=256)
parser.add_option("-a","--abps", type="int", dest="abps", default=128)
parser.add_option("--volnorm", action="store_true", dest="volnorm", default=False)
parser.add_option("--keep-aspect", action="store_true", dest="aspect", default=False)
parser.add_option("--height", type="int", dest="height", default=192)
parser.add_option("--width", type="int", dest="width", default=256)
parser.add_option("-z","--hz", type="int", dest="hz", default=32000)
parser.add_option("-c","--channels", type="int", dest="channels")
parser.add_option("--subcp", dest="subcp")
parser.add_option("-s","--sub", dest="sub")
parser.add_option("--font", dest="font")
parser.add_option("-t", "--thumb", dest="thumb", default="")
parser.add_option("--nosub", action="store_true", dest="nosub", default=False)
parser.add_option("--dpg", type="int" , dest="dpg", default=4)
parser.add_option("--sid", type="int" , dest="sid")
parser.add_option("--aid", type="int" , dest="aid")
parser.add_option("-2","--tp",action="store_true", dest="tp", default=False)
(options, args) = parser.parse_args()

if options.dpg > 4 or options.dpg < 0:
	print("Error, invalid DPG version selection! Defaulting to DPG4...")
	options.dpg = 4

# check requirements
# we don't need to check for pillow as that would trigger earlier in the script
requirements = ["mplayer","mencoder","sox"]
missing_requirement = False

for i in range(len(requirements)):
	if shutil.which(requirements[i]) is None:
		print(f"Error, {requirements[i]} is missing!")
		missing_requirement = True

# check if sox has mp3/mp2 format extension
sox_test = subprocess.run(['sox', '-h'], shell=False, capture_output=True, encoding="utf-8")
mp2_test = re.compile("mp2").search(sox_test.stdout)
if mp2_test is None:
	print("Error, libsox-fmt-mp3 is missing!")
	missing_requirement = True

# exit the script if a requirement isn't met
if missing_requirement:
	exit(1)

init_names()
for file in args:
	conv_file(file)
