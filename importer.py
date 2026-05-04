#!/usr/bin/env python3
"""
StepMania Song Importer
Converts MP3 files into StepMania song packages with .sm files
Supports YouTube downloads with metadata preservation
"""

import os
import sys
import shutil
import argparse
import re
import tempfile
from pathlib import Path
from typing import Optional, Tuple
import librosa
import numpy as np
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC
import yt_dlp


class StepManiaImporter:
    def __init__(self, output_dir: str = "./Songs", group_name: str = "Imported", difficulty: str = "Beginner"):
        self.output_dir = Path(output_dir)
        self.group_name = group_name
        self.difficulty = difficulty
        self.output_dir.mkdir(exist_ok=True)
        self.temp_dir = Path(tempfile.gettempdir()) / "stepmania_importer"
        self.temp_dir.mkdir(exist_ok=True)

    def is_youtube_url(self, url: str) -> bool:
        """Check if string is a YouTube URL"""
        youtube_regex = (
            r'(https?://)?(www\.)?'
            r'(youtube|youtu|youtube-nocookie)\.(com|be)/'
            r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
        )
        return bool(re.match(youtube_regex, url))

    def check_ffmpeg(self) -> bool:
        """Check if FFmpeg is installed"""
        return shutil.which('ffmpeg') is not None and shutil.which('ffprobe') is not None

    def download_from_youtube(self, url: str) -> Optional[str]:
        """Download audio from YouTube and return path to MP3 file with metadata"""
        if not self.check_ffmpeg():
            print("Error: FFmpeg is not installed or not in PATH")
            print("\nPlease install FFmpeg:")
            print("  Ubuntu/Debian/WSL: sudo apt install ffmpeg")
            print("  macOS: brew install ffmpeg")
            print("  Windows: Download from https://ffmpeg.org/download.html")
            return None

        print(f"Downloading from YouTube: {url}")

        output_template = str(self.temp_dir / '%(title)s.%(ext)s')

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'postprocessor_args': [
                '-ar', '44100',
            ],
            'writethumbnail': True,
            'embedthumbnail': True,
            'add_metadata': True,
            'quiet': False,
            'no_warnings': False,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

                title = info.get('title', 'Unknown Title')
                artist = info.get('artist') or info.get('uploader', 'Unknown Artist')
                album = info.get('album', '')
                release_year = info.get('release_year') or info.get('upload_date', '')[:4] if info.get('upload_date') else ''

                safe_filename = ydl.prepare_filename(info)
                mp3_path = Path(safe_filename).with_suffix('.mp3')

                if not mp3_path.exists():
                    print(f"Error: Downloaded file not found at {mp3_path}")
                    return None

                audio = MP3(mp3_path)
                if audio.tags is None:
                    audio.add_tags()

                audio.tags['TIT2'] = TIT2(encoding=3, text=title)
                audio.tags['TPE1'] = TPE1(encoding=3, text=artist)
                if album:
                    audio.tags['TALB'] = TALB(encoding=3, text=album)
                if release_year:
                    audio.tags['TDRC'] = TDRC(encoding=3, text=str(release_year))

                audio.save()

                print(f"  Downloaded: {title}")
                print(f"  Artist: {artist}")

                return str(mp3_path)

        except Exception as e:
            error_msg = str(e)
            print(f"Error downloading from YouTube: {error_msg}")

            if 'ffmpeg' in error_msg.lower() or 'ffprobe' in error_msg.lower():
                print("\nFFmpeg is required for YouTube downloads but was not found.")
                print("Please install FFmpeg:")
                print("  Ubuntu/Debian/WSL: sudo apt install ffmpeg")
                print("  macOS: brew install ffmpeg")
                print("  Windows: Download from https://ffmpeg.org/download.html")

            return None

    def detect_bpm(self, audio_path: str) -> float:
        """Detect BPM using librosa"""
        try:
            y, sr = librosa.load(audio_path, duration=60)
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            if isinstance(tempo, np.ndarray):
                tempo = tempo[0] if len(tempo) > 0 else 120.0
            return float(tempo)
        except Exception as e:
            print(f"Warning: Could not detect BPM: {e}")
            return 120.0

    def get_song_length(self, mp3_path: str) -> float:
        """Get song duration in seconds"""
        try:
            audio = MP3(mp3_path)
            return audio.info.length
        except Exception:
            return 180.0

    def extract_metadata(self, mp3_path: str) -> Tuple[str, str, str, float]:
        """Extract title, artist, album, and BPM from MP3"""
        audio = MP3(mp3_path)

        title = "Unknown Title"
        artist = "Unknown Artist"
        album = ""

        try:
            tags = ID3(mp3_path)
            if 'TIT2' in tags:
                title = str(tags['TIT2'])
            if 'TPE1' in tags:
                artist = str(tags['TPE1'])
            if 'TALB' in tags:
                album = str(tags['TALB'])
        except Exception:
            filename = Path(mp3_path).stem
            if ' - ' in filename:
                parts = filename.split(' - ', 1)
                artist = parts[0].strip()
                title = parts[1].strip()
            else:
                title = filename

        bpm = self.detect_bpm(mp3_path)

        return title, artist, album, bpm

    def generate_chart(self, bpm: float, duration: float) -> str:
        """Generate a chart pattern based on song length and difficulty"""
        beats_per_measure = 4
        measures_needed = int((duration / 60.0) * bpm / beats_per_measure) + 1

        # Define patterns for different difficulties
        patterns = {
            "Beginner": [
                "0100\n0000\n0000\n0000",
                "0000\n0010\n0000\n0000",
                "0000\n0000\n0001\n0000",
                "0000\n0000\n0000\n1000"
            ],
            "Easy": [
                "0100\n0000\n0010\n0000",
                "0001\n0000\n1000\n0000",
                "0010\n0000\n0100\n0000",
                "1000\n0000\n0001\n0000"
            ],
            "Medium": [
                "0100\n0010\n0001\n1000",
                "1000\n0001\n0010\n0100",
                "0010\n0100\n1000\n0001",
                "0001\n1000\n0100\n0010"
            ],
            "Hard": [
                "1100\n0011\n1001\n0110",
                "0110\n1001\n0011\n1100",
                "1010\n0101\n1010\n0101",
                "0101\n1010\n0101\n1010"
            ],
            "Expert": [
                "1100\n0110\n1001\n0110\n1100\n0011\n1001\n0011",
                "0011\n1100\n0110\n1001\n0011\n1100\n0110\n1001",
                "1010\n0101\n1010\n0101\n1100\n0011\n1100\n0011",
                "1001\n0110\n1001\n0110\n1010\n0101\n1010\n0101"
            ]
        }

        # Use selected difficulty or default to Beginner
        pattern = patterns.get(self.difficulty, patterns["Beginner"])

        measures = []
        for i in range(measures_needed):
            pattern_index = i % len(pattern)
            measures.append(pattern[pattern_index])

        return ",\n".join(measures) + "\n"

    def generate_sm_file(self, title: str, artist: str, music_file: str,
                        bpm: float, duration: float, offset: float = 0.0) -> str:
        """Generate StepMania .sm file content"""
        chart_data = self.generate_chart(bpm, duration)

        # Map difficulty names to numeric ratings
        difficulty_ratings = {
            "Beginner": 1,
            "Easy": 3,
            "Medium": 6,
            "Hard": 8,
            "Expert": 10
        }
        rating = difficulty_ratings.get(self.difficulty, 1)

        sm_content = f"""#TITLE:{title};
#SUBTITLE:;
#ARTIST:{artist};
#TITLETRANSLIT:;
#SUBTITLETRANSLIT:;
#ARTISTTRANSLIT:;
#GENRE:;
#CREDIT:Imported via StepMania Importer;
#BANNER:;
#BACKGROUND:;
#LYRICSPATH:;
#CDTITLE:;
#MUSIC:{music_file};
#OFFSET:{offset:.3f};
#SAMPLESTART:30.000;
#SAMPLELENGTH:12.000;
#SELECTABLE:YES;
#BPMS:0.000={bpm:.3f};
#STOPS:;
#BGCHANGES:;
#KEYSOUNDS:;

#NOTES:
     dance-single:
     :
     {self.difficulty}:
     {rating}:
     0.100,0.100,0.100,0.100,0.100:
{chart_data};
"""
        return sm_content

    def sanitize_dirname(self, name: str) -> str:
        """Sanitize directory name for filesystem"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        return name.strip()

    def import_song(self, mp3_path: str, cleanup_temp: bool = False) -> bool:
        """Import a single MP3 file into StepMania format"""
        mp3_path = Path(mp3_path)

        if not mp3_path.exists():
            print(f"Error: File not found: {mp3_path}")
            return False

        if mp3_path.suffix.lower() != '.mp3':
            print(f"Error: Not an MP3 file: {mp3_path}")
            return False

        print(f"Importing: {mp3_path.name}")

        title, artist, album, bpm = self.extract_metadata(str(mp3_path))
        duration = self.get_song_length(str(mp3_path))

        print(f"  Title: {title}")
        print(f"  Artist: {artist}")
        print(f"  BPM: {bpm:.2f}")
        print(f"  Duration: {int(duration // 60)}:{int(duration % 60):02d}")

        group_dir = self.output_dir / self.group_name
        group_dir.mkdir(exist_ok=True)

        song_dir_name = self.sanitize_dirname(f"{artist} - {title}")
        song_dir = group_dir / song_dir_name
        song_dir.mkdir(exist_ok=True)

        music_filename = f"{mp3_path.stem}.mp3"
        dest_music = song_dir / music_filename
        shutil.copy2(mp3_path, dest_music)

        sm_content = self.generate_sm_file(title, artist, music_filename, bpm, duration)
        sm_file = song_dir / f"{mp3_path.stem}.sm"
        sm_file.write_text(sm_content, encoding='utf-8')

        print(f"  Created: {song_dir}/")
        print(f"  ✓ Imported successfully\n")

        if cleanup_temp and str(mp3_path).startswith(str(self.temp_dir)):
            try:
                mp3_path.unlink()
                print(f"  Cleaned up temporary file")
            except Exception:
                pass

        return True

    def import_from_youtube(self, url: str) -> bool:
        """Download from YouTube and import into StepMania format"""
        mp3_path = self.download_from_youtube(url)
        if not mp3_path:
            return False

        return self.import_song(mp3_path, cleanup_temp=True)

    def import_directory(self, input_dir: str) -> int:
        """Import all MP3 files from a directory"""
        input_path = Path(input_dir)

        if not input_path.exists():
            print(f"Error: Directory not found: {input_dir}")
            return 0

        mp3_files = list(input_path.glob("*.mp3"))

        if not mp3_files:
            print(f"No MP3 files found in {input_dir}")
            return 0

        print(f"Found {len(mp3_files)} MP3 file(s)\n")

        success_count = 0
        for mp3_file in mp3_files:
            if self.import_song(str(mp3_file)):
                success_count += 1

        return success_count


def main():
    parser = argparse.ArgumentParser(
        description="Import MP3 files or YouTube videos into StepMania song format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s song.mp3                              Import a single MP3 file
  %(prog)s /path/to/music/                       Import all MP3s from a directory
  %(prog)s "https://youtube.com/watch?v=..."     Download and import from YouTube
  %(prog)s song.mp3 -o ~/StepMania-5.1/Songs     Specify custom output directory
  %(prog)s "https://youtube.com/..." -d Medium   Download with Medium difficulty
        """
    )

    parser.add_argument(
        'input',
        help='MP3 file, directory containing MP3 files, or YouTube URL'
    )

    parser.add_argument(
        '-o', '--output',
        default='./Songs',
        help='Output directory for StepMania songs (default: ./Songs)'
    )

    parser.add_argument(
        '-g', '--group',
        default='Imported',
        help='Group folder name (default: Imported)'
    )

    parser.add_argument(
        '-d', '--difficulty',
        choices=['Beginner', 'Easy', 'Medium', 'Hard', 'Expert'],
        default='Beginner',
        help='Chart difficulty level (default: Beginner)'
    )

    args = parser.parse_args()

    importer = StepManiaImporter(args.output, args.group, args.difficulty)

    if importer.is_youtube_url(args.input):
        success = importer.import_from_youtube(args.input)
        if success:
            print(f"\nOutput directory: {importer.output_dir.absolute()}")
        sys.exit(0 if success else 1)

    input_path = Path(args.input)

    if input_path.is_file():
        success = importer.import_song(args.input)
        sys.exit(0 if success else 1)
    elif input_path.is_dir():
        count = importer.import_directory(args.input)
        print(f"\nImported {count} song(s) successfully")
        print(f"Output directory: {importer.output_dir.absolute()}")
        sys.exit(0 if count > 0 else 1)
    else:
        print(f"Error: {args.input} is not a valid file, directory, or YouTube URL")
        sys.exit(1)


if __name__ == "__main__":
    main()
