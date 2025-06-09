# Whisper Transcription Service

A production-ready FastAPI service for audio transcription using OpenAI's Whisper model via the faster-whisper library.

## Features

- 🎵 **Multi-format Audio Support**: WAV, MP3, M4A, OGG, FLAC, WMA, AAC
- 🔄 **Automatic Format Conversion**: FFmpeg-powered audio preprocessing
- 🧠 **Multiple Whisper Models**: Support for all Whisper model sizes
- 🌍 **Language Detection**: Automatic language detection or forced language selection
- ⏱️ **Detailed Timestamps**: Segment-level transcription with timing information
- 🏥 **Health Monitoring**: Built-in health checks and comprehensive logging
- 📝 **Typed Responses**: Pydantic models for structured API responses
- 🐳 **Docker Ready**: Containerized deployment with health checks

## Quick Start

### Using Docker (Recommended)

```bash
# Build the image
docker build -t whisper-service .

# Run with default settings
docker run -p 9000:9000 whisper-service

# Run with custom model
docker run -e WHISPER_MODEL=small -p 9000:9000 whisper-service
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Install FFmpeg (Ubuntu/Debian)
sudo apt-get install ffmpeg

# Install FFmpeg (macOS)
brew install ffmpeg

# Run the service
python app.py
```

## API Endpoints

### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "model": "base",
  "version": "1.0.0"
}
```

### Transcribe Audio
```http
POST /transcribe
```

**Parameters:**
- `audio` (file, required): Audio file to transcribe
- `model` (query, optional): Whisper model to use (default: "base")
- `language` (query, optional): Force specific language (e.g., "en", "es", "fr")

**Example Request:**
```bash
curl -X POST \
  -F "audio=@speech.mp3" \
  "http://localhost:9000/transcribe?model=small&language=en"
```

**Response:**
```json
{
  "text": "Hello, this is a test transcription.",
  "segments": [
    {
      "start": 0.0,
      "end": 2.5,
      "text": "Hello, this is a test transcription.",
      "confidence": -0.45
    }
  ],
  "language": "en",
  "duration": 2.5
}
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WHISPER_MODEL` | `base` | Default Whisper model to load |
| `PYTHONUNBUFFERED` | `1` | Python output buffering |
| `PYTHONDONTWRITEBYTECODE` | `1` | Prevent .pyc file creation |

### Available Whisper Models

| Model | Size | VRAM | Speed | Accuracy |
|-------|------|------|-------|----------|
| `tiny` | 39 MB | ~1 GB | Fastest | Lowest |
| `base` | 74 MB | ~1 GB | Fast | Good |
| `small` | 244 MB | ~2 GB | Medium | Better |
| `medium` | 769 MB | ~5 GB | Slower | High |
| `large-v1` | 1550 MB | ~10 GB | Slowest | Highest |
| `large-v2` | 1550 MB | ~10 GB | Slowest | Highest |
| `large-v3` | 1550 MB | ~10 GB | Slowest | Highest |

### Supported Audio Formats

- **WAV** - Uncompressed audio
- **MP3** - MPEG Audio Layer III
- **M4A** - MPEG-4 Audio
- **OGG** - Ogg Vorbis
- **FLAC** - Free Lossless Audio Codec
- **WMA** - Windows Media Audio
- **AAC** - Advanced Audio Coding

## Docker Deployment

### Basic Deployment
```bash
docker run -d \
  --name whisper-service \
  -p 9000:9000 \
  whisper-service
```

### Production Deployment
```bash
docker run -d \
  --name whisper-service \
  --restart unless-stopped \
  -p 9000:9000 \
  -e WHISPER_MODEL=small \
  -v whisper-logs:/app/logs \
  whisper-service
```

### Docker Compose
```yaml
version: '3.8'
services:
  whisper:
    build: .
    ports:
      - "9000:9000"
    environment:
      - WHISPER_MODEL=small
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## Performance Optimization

### Memory Usage
- **tiny/base**: ~1-2 GB RAM
- **small**: ~2-4 GB RAM  
- **medium**: ~4-8 GB RAM
- **large**: ~8-16 GB RAM

### CPU vs GPU
The service automatically detects available compute:
- **CPU**: Works on any system, slower transcription
- **GPU**: Requires CUDA-compatible GPU, much faster

For GPU support, modify the Dockerfile to include CUDA runtime.

## Monitoring and Logging

### Log Files
- Application logs: `whisper_service.log`
- Console output for Docker containers
- Structured JSON logging available

### Health Monitoring
```bash
# Check service health
curl http://localhost:9000/health

# Docker health status
docker ps  # Shows health status
```

### Metrics to Monitor
- Response times for transcription requests
- Memory usage (varies by model)
- Error rates and types
- Audio file processing success rates

## Error Handling

The service provides structured error responses:

```json
{
  "error": "Unsupported audio format: .xyz",
  "detail": "Supported formats: .wav, .mp3, .m4a, .ogg, .flac, .wma, .aac"
}
```

Common error scenarios:
- Unsupported audio formats
- Model loading failures
- Audio conversion issues
- File size limitations
- Memory constraints

## Development

### Project Structure
```
.
├── app.py              # Main application
├── requirements.txt    # Python dependencies
├── Dockerfile         # Container configuration
├── README.md          # This file
└── logs/              # Application logs
```

### Running Tests
```bash
# Install test dependencies
pip install pytest httpx

# Run basic health check test
python -c "
import requests
response = requests.get('http://localhost:9000/health')
print(f'Status: {response.status_code}')
print(f'Response: {response.json()}')
"
```

### API Documentation
Once running, visit:
- Swagger UI: `http://localhost:9000/docs`
- ReDoc: `http://localhost:9000/redoc`

## Troubleshooting

### Common Issues

**1. FFmpeg not found**
```bash
# Ubuntu/Debian
sudo apt-get update && sudo apt-get install ffmpeg

# Alpine (for smaller Docker images)
apk add --no-cache ffmpeg
```

**2. Model loading fails**
- Check available memory
- Verify model name is correct
- Try smaller model (e.g., "tiny" or "base")

**3. Audio conversion fails**
- Verify FFmpeg installation
- Check audio file is not corrupted
- Ensure sufficient disk space for temp files

**4. High memory usage**
- Use smaller models for production
- Monitor Docker memory limits
- Consider processing files sequentially vs parallel

### Performance Tuning

**For CPU-only environments:**
```bash
# Use smaller, faster models
docker run -e WHISPER_MODEL=tiny -p 9000:9000 whisper-service
```

**For high-accuracy needs:**
```bash
# Use larger models with more resources
docker run -e WHISPER_MODEL=large-v3 -m 8g -p 9000:9000 whisper-service
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) - Original Whisper model
- [faster-whisper](https://github.com/guillaumekln/faster-whisper) - Optimized Whisper implementation
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework