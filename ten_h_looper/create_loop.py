import argparse
import math
import os
import re
import subprocess
import sys
import uuid
from time import strftime, gmtime

import youtube_dl

TEMPFILE_PREFIX = "tenxlooper-temp"


def video_time(s):
    units = s.split(":")
    seconds = [1, 60, 3600, 86400]
    try:
        return sum(int(x) * seconds[len(units) - i - 1] for i, x in enumerate(units))
    except (ValueError, IndexError):
        raise ValueError("Invalid time value: {}".format(s))


def start_time(s):
    return video_time(s)


def end_time(s):
    return video_time(s)


# used to make argument parser error more readable
start_time.__name__ = "start time"
end_time.__name__ = "end time"


def parse_args(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "uri", help="URL of a YouTube video or path to a local video file"
    )
    parser.add_argument(
        "-s", "--start", help="Starting point in a video (dd:hh:mm:ss)", type=start_time
    )
    parser.add_argument(
        "-e", "--end", help="Ending point in a video (dd:hh:mm:ss)", type=end_time
    )
    parser.add_argument(
        "-d",
        "--destination",
        help="Where to store a resulting file (can be absolute or relative path)",
    )

    args = parser.parse_args(args)

    is_url = not os.path.exists(args.uri)

    if is_url and "youtube.com" not in args.uri:
        parser.error(
            "{} is not a path to a local path or YouTube video URL.".format(args.uri)
        )

    if is_url:
        with youtube_dl.YoutubeDL({"quiet": True}) as ydl:
            info = ydl.extract_info(args.uri, download=False)
            duration = info["duration"]
            title = info["title"]
    else:
        try:
            duration = get_video_duration(args.uri)
        except OSError:
            parser.error(
                "{} does not seem to be a path to a proper video file".format(args.uri)
            )

    if args.start is None:
        args.start = 0
    if args.start < 0:
        args.start = duration + args.start
    if args.end is None:
        args.end = duration
    if args.end < 0:
        args.end = duration + args.end

    if args.start > duration or args.start < 0:
        parser.error("Start time is greater than duration of the video.")
    if args.end > duration or args.end < 0:
        parser.error(
            "End time is greater than video duration. Do not specify it if you "
            "want it to be the end of the video."
        )
    if args.start > args.end:
        parser.error("Start time is greater than end time.")

    args.full_video = args.end - args.start == duration

    if args.destination is None:
        if is_url:
            args.destination = "ten-hours-of-" + title
        else:
            args.destination = "ten-hours-of-" + os.path.basename(args.uri)

        args.destination = os.path.abspath(args.destination)

    return args


def get_video_duration(path):
    proc = subprocess.run(
        ["ffprobe", "-loglevel", "1", "-i", path, "-show_format"],
        stdout=subprocess.PIPE,
        universal_newlines=True,
    )

    info = proc.stdout
    res = re.search(r"(?<=duration=)\d+", info)

    if res:
        return int(res.group(0))
    else:
        print("Couldn't get the duration of the video {}".format(path))
        sys.exit(1)


def download_video(url):
    with youtube_dl.YoutubeDL({"consoletitle": True}) as ydl:
        filename = ydl.prepare_filename(ydl.extract_info(url))
    return filename


def cut(filename, start, end):
    duration = end - start
    start = strftime("%H:%M:%S", gmtime(start))
    duration = strftime("%H:%M:%S", gmtime(duration))

    dest = "{}-subvideo-{}-{}".format(TEMPFILE_PREFIX, uuid.uuid4(), filename)

    command = [
        "ffmpeg",
        "-nostats",
        "-loglevel",
        "1",
        "-ss",
        start,
        "-i",
        filename,
        "-t",
        duration,
        dest,
    ]

    return subprocess.run(command).returncode, dest


def concat(input_file, destination):
    command = [
        "ffmpeg",
        "-nostats",
        "-loglevel",
        "1",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        input_file,
        "-acodec",
        "copy",
        "-vcodec",
        "copy",
        destination,
    ]

    return subprocess.run(command).returncode


def concatenate(source_video, destination):
    source_extension = os.path.splitext(source_video)[1]
    if not destination.endswith(os.path.splitext(source_video)[1]):
        print("Destination file must have the same extension as the input file!")
        dest_extension = os.path.splitext(destination)[1]
        if dest_extension == "":
            destination += source_extension
        else:
            destination = destination.replace(dest_extension, source_extension)
        print("Changed destination filename to {}".format(destination))

    input_file = "{}-inputs.txt".format(TEMPFILE_PREFIX)
    duration = get_video_duration(source_video)

    # If the video is shorter than 5 minutes we concatenate it with itself until
    # it reaches ~5 minutes. We then concatenate this longer video along with a few
    # shorter ones until we reach desired length. This provides a decent speedup,
    # especially if the source video is a few seconds long
    if duration < 300:
        temp_video = os.path.join(
            os.path.dirname(source_video),
            "{}-{}-{}".format(
                TEMPFILE_PREFIX, uuid.uuid4(), os.path.basename(source_video)
            ),
        )

        with open(input_file, "w") as f:
            f.write("file '{}'\n".format(source_video) * (300 // duration))

        concat(input_file, temp_video)

        s, t = divmod(36000, (300 // duration) * duration)

        long = "file '{}'\n".format(temp_video) * s
        short = "file '{}'\n".format(source_video) * math.ceil(t / duration)

        with open(input_file, "w") as f:
            f.write(long + short)
    else:
        with open(input_file, "w") as f:
            f.write("file '{}'\n".format(source_video) * math.ceil(36000 / duration))

    return concat(input_file, destination), destination


def clean_up():
    print("\nCleaning up...\n")
    for file in os.listdir("."):
        if file.startswith(TEMPFILE_PREFIX):
            try:
                os.remove(file)
            except Exception:
                print(
                    "Error occured while trying to clean up file {}. "
                    "Try removing it manually.".format(file)
                )


def main():
    args = parse_args()

    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL)
        subprocess.run(["ffprobe", "-version"], stdout=subprocess.DEVNULL)
    except FileNotFoundError:
        print("\nffmpeg and/or ffprobe don't seem to be installed!\n")
        sys.exit(1)

    filename = args.uri if os.path.exists(args.uri) else download_video(args.uri)

    # Case when youtube downloader fails to merge streams into format originally
    # intended so it opts for .mkv instead
    if not os.path.exists(filename):
        name = os.path.splitext(filename)[0]
        for file in os.listdir("."):
            if name in file:
                filename = file
                break

    if not args.full_video:
        print("Cutting video...")
        status, filename = cut(filename, args.start, args.end)
        if status != 0:
            print("\nSomething went wrong while cutting the video!\n")
            sys.exit(status)

    print("Concatenating videos...")
    status, _ = concatenate(filename, args.destination)

    try:
        clean_up()
    except KeyboardInterrupt:
        print(
            "Interrupted before cleanup was done. There are probably some "
            "temporary files left over."
        )
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nStopped by user! \n")
        sys.exit(1)
