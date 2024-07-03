# YouTubeDownloader

## Description

*YouTubeDownloader* is a CLI based script, which is capable to download a *YouTube* content in high quality and save it locally for further offline use.

### Dependencies

- [*FFmpeg*](https://ffmpeg.org/)
- [*pytube*](https://github.com/pytube/pytube/tree/master)

### Installation

1. Prepare Linux-based machine with at least 1.4 GB of RAM memory.
2. Make sure, that machine has web access.
3. Install *Python 3*:
    > \> apt install python3
4. Install *FFmpeg*:
    > \> apt install ffmpeg
5. Prepare *Python* virtual environment and activate it (optional):
    > \> python3 -m venv venv
    >
    > \> source venv/bin/activate
6. Install necessary *Python* modules listed in *requirements.txt* file from project repository:
    > \> pip install -r requirements.txt

If Your use package manager other than *APT*, please adjust above mentioned commands accordingly.

### Usage

1. Print script version:
    > \> python3 YouTubeDownloader.py --version
2. Print help prompt:
    > \> python3 YouTubeDownloader.py --help
3. Downloading a *YouTube* video:
    > \> python3 YouTubeDownloader.py \<link to YouTube video\> \<path to \*.webm output file\>
    - Quality of downloaded audio is best as possible (basing on bit rate) and is chosen automatically.
    - Quality of downloaded video is best as possible (basing on resolution as a primary criteria and FPS as secondary) and is chosen automatically.
    - Video and auto contained by output file will be encoded with codecs default  for *WEBM* container - *VP9* for video and *Opus* for audio.
    - If other encoding or container type is required, file can be reformatted using *FFmpeg*.
4. Downloading only auto content of *YouTube* video:
    > \> python3 YouTubeDownloader.py \<link to *YouTube* video\> \<path to \*.opus or \*.mp3 output file\> --audio_only
    - Quality of downloaded audio is best as possible (basing on bit rate) and is chosen automatically.
    - Content of output \*.opus file will be encoded using *Opus* coded.
    - Content of output \*.mp3 file will be encoded using *MP3* coded.

Shortened version of all above mentioned script arguments are available - please check script help prompt for more information.

## Authors

- Jakub Miodunka

## License

This project is licensed under the MIT License - see the LICENSE.md file for details
