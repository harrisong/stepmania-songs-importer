# StepMania Songs Importer

A Python tool to convert MP3 files or YouTube videos into StepMania song packages with automatically generated `.sm` files.

## Features

- **YouTube Download Support**: Download songs directly from YouTube URLs with metadata preservation
- Extracts metadata (title, artist) from MP3 ID3 tags, YouTube info, or filename
- Auto-detects BPM using audio analysis
- Generates valid StepMania `.sm` format files
- Creates proper directory structure for StepMania
- Supports single file or batch directory import
- Includes five difficulty levels (Beginner to Expert)

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Install FFmpeg (required for YouTube downloads):
```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

## Usage

### Download from YouTube:
```bash
python importer.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

### Import a single MP3 file:
```bash
python importer.py song.mp3
```

### Import all MP3 files from a directory:
```bash
python importer.py /path/to/music/folder/
```

### Specify custom output directory:
```bash
python importer.py song.mp3 -o ~/StepMania-5.1/Songs
```

### Specify difficulty level:
```bash
python importer.py song.mp3 -d Medium
# Or with YouTube:
python importer.py "https://youtube.com/watch?v=..." -d Hard
```

Available difficulty levels: `Beginner`, `Easy`, `Medium`, `Hard`, `Expert`

### Make the script executable (optional):
```bash
chmod +x importer.py
./importer.py song.mp3
```

## Output Structure

The importer creates the following structure:

```
Songs/
└── Artist Name - Song Title/
    ├── song.mp3
    └── song.sm
```

## How It Works

1. **YouTube Download** (if URL provided):
   - Downloads audio from YouTube using yt-dlp
   - Extracts metadata (title, artist, album, year) from YouTube video info
   - Embeds thumbnail as album art
   - Converts to MP3 with preserved metadata

2. **Metadata Extraction**: 
   - Reads ID3 tags from MP3 files or YouTube metadata
   - Falls back to parsing artist and title from filename (expects "Artist - Title.mp3" format)

3. **BPM Detection**: Uses librosa's beat tracking to automatically detect the song's tempo.

4. **SM File Generation**: Creates a StepMania `.sm` file with:
   - Song metadata (title, artist, BPM)
   - Auto-generated chart patterns based on difficulty level
   - Proper timing and offset information

5. **File Organization**: Copies the MP3 and creates the `.sm` file in a properly named directory.

## Generated Charts

The importer can create charts at five difficulty levels:

- **Beginner** (rating 1): Single arrows with spacing between steps
- **Easy** (rating 3): Single arrows with some consecutive steps
- **Medium** (rating 6): Mix of single arrows in faster sequences
- **Hard** (rating 8): Double arrows and complex patterns
- **Expert** (rating 10): Dense double arrow combinations with 8th note patterns

These are automatically generated patterns. For polished charts, you'll want to open them in a StepMania editor (like ArrowVortex or SM5's editor) to refine and customize the patterns.

## Requirements

- Python 3.7+
- FFmpeg (for YouTube downloads)
- mutagen (MP3 metadata reading)
- librosa (BPM detection)
- numpy (audio processing)
- yt-dlp (YouTube downloading)

## Notes

- The generated charts are very basic and intended as starting templates
- BPM detection works best with songs that have consistent tempo
- You may need to adjust the `#OFFSET` value in the `.sm` file to sync the steps with the music
- YouTube downloads automatically preserve metadata (title, artist, album art)
- For MP3 files, proper ID3 tags will be used if available

## Next Steps

After importing:
1. Copy the generated `Songs/` folder to your StepMania installation directory
2. Open StepMania and your songs should appear in the song selection menu
3. Use a chart editor to create proper step charts for different difficulty levels

## License

MIT License - feel free to modify and use as needed.
