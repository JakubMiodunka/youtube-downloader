from argparse import ArgumentParser, Namespace
from datetime import datetime
from pathlib import Path
from pytube import YouTube, Stream
import shlex
import subprocess

__version__ = "1"
__description__ = """
YouTubeDownloader is a CLI based script, that is capable to download high quality content from Youtube.
To work property it require installed ffmpeg and a chunk of RAM memory.

Memory usage is highly dependent on video quality - here are some references:
 400 MB of RAM when processing FULL HD 30 FPS video,
 1.4 GB of RAM when processing 4K 60 FPS video,

Currently supported output file formats are *.mp3 (encoded using MP3 codec, stores only audio content),
*.opus (encoded using Opus codec, stores only audio content) and *.webm (stores both video and audio
encoded using VP9 and Opus codecs respectively).

Keep in mind that processing long, high quality videos may take a long time to finish.
"""


class YouTubeVideo:
    """
    Class meant to be used as downloader of high quality/resolution content present on YouTube.

    To work properly it requires pytube module (developed on version 15.0.0)
    along with ffmpeg (developed on version 4.3.6-0+deb11u1). Should be launched preferably in Linux-based systems.

    When dealing with high-resolution videos (i.e. 4K 60 FPS) it is recommended to have available at least 1.4 GB
    of free RAM memory - it will be needed to process them using ffmpeg.
    Otherwise, ffmpeg runtime will end up with 'out of memory' error.

    Memory usage for typical FULL HD 30 FPS video osculates around 400 MB.

    Above memory values were trial-determined on Debian 11.7.0, that used 4 core CPU
    and maybe different in other operating systems and hardware configurations.
    """

    def __init__(self, hyperlink: str):
        """
        Args:
            hyperlink: YouTube video hyperlink.
        """

        # Properties init
        self.video = YouTube(hyperlink)

    @staticmethod
    def __validate_target(target: Path, *extensions: str) -> None:
        """
        Validates file path, that will be used as target path for other utilities implemented in this class.
        If one of performed checks fail, according exception will be raised.

        Args:
            target: File path, that will be validated.
            extensions: Pool of extensions valid for given target path.
        """

        # Performing checks
        if not target.parent.exists():
            raise FileNotFoundError(f"Parent directory of '{target}' does not exist.")

        if target.exists():
            raise FileExistsError(f"'{target}' already exist.")

        if target.suffix not in extensions:
            raise TypeError(
                f"'{target}' has invalid extension - expected one of the following: {', '.join(extensions)}")

    def save_video_as(self, target: Path) -> None:
        """
        Downloads the best quality video stream (basing on resolution as a primary criteria and FPS as secondary)
        and saves it to given target file.
        Video will be encoded using VP9 or V9.2 codec as those are native for YouTube DASH.

        Args:
            target: Path to target *.webm file.
        """

        # Validation of provided target file
        YouTubeVideo.__validate_target(target, ".webm")

        # Extracting only DASH video streams encoded using VP9 or VP9.2 codec
        def check_if_dash_stream(stream: Stream) -> bool:
            # Should be a video WEBM stream
            if stream.mime_type != "video/webm":
                return False

            # Should be 'adaptive', which means, that it is not store audio and video combined
            if not stream.is_adaptive:
                return False

            # Should be encoded using VP9-family coded
            if stream.video_codec not in ("vp9", "vp9.2"):
                return False

            return True

        dash_streams = tuple(filter(check_if_dash_stream, self.video.streams))

        # Searching for highest quality stream basing on resolution as a primary criteria and FPS as secondary
        def sort_criteria(stream: Stream) -> tuple[int, int]:
            # Stream resolution in int format ('resolution' property stores str values like "144p", "480p" etc.)
            resolution: int = int(stream.resolution[:-1])

            # Stream FPS added as secondary criteria
            return resolution, stream.fps

        # First stream in sorted stream list should be the one with the best quality
        best_quality_stream, *_ = sorted(dash_streams, key=sort_criteria, reverse=True)

        # Preparing temporary file
        tmp_video_file = Path(__file__).parent / f"tmp_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.webm"

        try:
            # Downloading the stream
            best_quality_stream.download(output_path=str(tmp_video_file.parent), filename=tmp_video_file.name)

            # Renaming temporary file if download was successful
            tmp_video_file.rename(target)

        finally:
            # Removing temporary file if necessary
            tmp_video_file.unlink(missing_ok=True)

    def save_audio_as(self, target: Path) -> None:
        """
        Downloads the best quality audio stream (basing on bit rate) and saves it to given *.opus or *.mp3 file.
        If output file is *.opus, audio will be encoded using Opus codec (native for YouTube DASH).
        If output file is *.mp3, audio will be transcoded to MP3 codec using ffmpeg.

        Args:
            target: Path to target *.opus or *.mp3 file.
        """

        # Validation of provided target file
        YouTubeVideo.__validate_target(target, ".opus", ".mp3")

        # Extracting only DASH audio streams encoded using Opus codec
        dash_streams = list(self.video.streams.filter(mime_type="audio/webm", audio_codec="opus", adaptive=True))

        # Searching for the best quality stream basing on bit rate
        best_quality_stream, *_ = sorted(dash_streams, key=lambda stream: stream.bitrate, reverse=True)

        # Preparing temporary file
        tmp_audio_file = Path(__file__).parent / f"tmp_audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.opus"

        try:
            # Downloading the stream
            best_quality_stream.download(output_path=str(tmp_audio_file.parent), filename=tmp_audio_file.name)

            # Performing transcoding if given target is *.mp3 file
            if target.suffix == ".mp3":
                # Preparing ffmpeg command
                command = f"ffmpeg -i {tmp_audio_file} -c:a libmp3lame -q:a 0 {target}"

                # Executing prepared command
                subprocess.run(shlex.split(command), check=True)
            else:
                # Renaming temporary *.opus file if output is also *.opus file
                tmp_audio_file.rename(target)
        finally:
            # Removing temporary file if necessary
            tmp_audio_file.unlink(missing_ok=True)

    def save_as(self, target: Path) -> None:
        """
        Downloads the best quality video and audio stream and merge it together using ffmpeg into one *.webm file.
        Video in output file will be encoded using VP9 codec and audio will be encoded
        using Opus (default codecs for WEBM container).

        WEBM container was chosen to be the output format over MP4 due to the fact,
        that it is well standardised - during trials with MP4 (H264/AAC encoded video and AAC audio) unexpected
        compatibility issues with Windows Media Player occurred - program was not able to play 4K 60 FPS videos
        (with FULL HD 30 FPS worked fine). When switched to WEBM problem disappear.

        As YouTube utilise Dynamic Adaptive Streaming over HTTP (DASH), streams containing the best available
        audio and video in a single file (referred in pytube documentation as “progressive" streams) are not available.
        The only way to download the best available quality content is to download video and audio separately
        and then post-process them with software like ffmpeg (suggestion available in pytube documentation).

        Args:
            target: Path to output *.webm file.
        """

        # Validation of provided target file
        YouTubeVideo.__validate_target(target, ".webm")

        # Preparing temporary files
        parent_dir = Path(__file__).parent
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        tmp_video_file = parent_dir / f"tmp_video_{timestamp}.webm"
        tmp_audio_file = parent_dir / f"tmp_audio_{timestamp}.opus"

        try:
            # Downloading video and audio separately
            self.save_video_as(tmp_video_file)
            self.save_audio_as(tmp_audio_file)

            # Preparing a ffmpeg command, that will merge downloaded audio and video
            command = f"ffmpeg -i {tmp_video_file} -i {tmp_audio_file} {target}"

            # Executing prepared command
            subprocess.run(shlex.split(command), check=True)

        finally:
            # Removing temporary files if necessary
            tmp_video_file.unlink(missing_ok=True)
            tmp_audio_file.unlink(missing_ok=True)


def main(arguments: Namespace) -> None:
    """
    Main part of the script.

    Args:
        arguments: Script arguments.
    """

    # Printing version of the script and exiting
    if arguments.version:
        print(f"Version: {__version__}")
        return

    # Initialising necessary variables
    youtube_video = YouTubeVideo(arguments.hyperlink)
    target = Path(arguments.target)

    # Downloading YouTube content according to given arguments
    if arguments.audio_only:
        youtube_video.save_audio_as(target)
    else:
        youtube_video.save_as(target)


if __name__ == "__main__":
    # Paging arguments
    argument_parser = ArgumentParser(description=__description__)
    argument_parser.add_argument("hyperlink", help="Hyperlink to YouTube video, that will be downloaded.")
    argument_parser.add_argument("target", help="File to which downloaded content will be saved.")
    argument_parser.add_argument("-a", "--audio_only", action="store_true", help="Download only audio.")
    argument_parser.add_argument("-v", "--version", action="store_true", help="Print the version of the script.")

    # Passing arguments to main function
    main(argument_parser.parse_args())
