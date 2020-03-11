# ten-h-looper
[![license](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/AleksaC/ten-h-looper/blob/master/LICENSE)
<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>

Create 10h loops of video excerpts.

## About

This is a simple cli tool that lets you create 10 hour videos either from 
YouTube videos or videos you have stored locally. This exists because I wanted 
to make a [10 hour loop](https://knowyourmeme.com/memes/10-hour-videos)  of 
chorus of an old local song and the easiest way for me to do that was to write a
python script. Later on I added a cli on top of it and made it into a package.

## Usage

To use this tool you need to have `python >=3.4` as well as [`ffmpeg`](https://www.ffmpeg.org/) installed.
`ffmpeg` also needs to be in `PATH` so it can be called from the script.

### Installation

1. `git clone https://github.com/AleksaC/ten-h-looper`
2. `cd ten-h-looper`
3. `python -m pip install .`

If you don't want to you don't need to install the package to be able to use the
script. If you just install [youtube-dl](https://github.com/ytdl-org/youtube-dl) 
and replace `create_loop` with `python ten_h_looper/create_loop.py` 
(assuming you are in `ten-h-looper` directory) in the example below the script
will work the same way as if you installed the package.

### Example

```shell script
create_loop -s 01:14 -e 01:24 -d rockstar.mp4 "https://www.youtube.com/watch?v=L_jWHffIx5E"
```

This creates a 10h video loop of 10s chorus from *Smash Mouth - All Star* and 
saves it as `rockstar.mp4`. `-s` and `-e` are the starting and ending point of 
the video to be looped and can be omitted. They default to *0* and *length of the 
video* respectively. You can use a path to a local video instead of the YouTube
link. The destination filename `-d` can also be omitted.

**Note**: This may not work on Windows as I haven't tested it or made any 
special effort to make it work there.

**Note 2**: Depending on the video quality and your hardware resources the 
script may take a while. 

**Note 3**: The resulting video may be a little longer than 10 hours depending
on the length of the source video.

**Note 4**: The script currently downloads the whole video and cuts the part 
needed from it to create the final video. This could've been done more 
efficiently by working with streams directly but I didn't do it initially and 
saw little value in doing it later as the videos this would normally be used on
are relatively short and not of the highest quality.
