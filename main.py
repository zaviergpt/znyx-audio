import io
import wave
from flask import Flask, Response, request
import audiotools
from audiotools.cdio import CDDAReader

app = Flask(__name__)

@app.route('/stream')
def stream_cd():
    # Replace with your CD device path (e.g., '/dev/cdrom' on Linux, 'D:' on Windows)
    device = '/dev/cdrom'
    reader = CDDAReader(device, perform_logging=False)

    track_offsets = reader.track_offsets  # dict {1: offset_frames, ...}
    track_lengths = reader.track_lengths  # dict {1: length_frames, ...}

    track_str = request.args.get('track')
    if track_str:
        try:
            track = int(track_str)
            if track not in track_lengths:
                return "Invalid track number", 400
            total_frames = track_lengths[track]
            # Seek to the start of the track (sector-aligned)
            actual_seek = reader.seek(track_offsets[track])
            # Adjust total_frames if seek didn't land exactly (unlikely for track offsets)
            total_frames -= (actual_seek - track_offsets[track])
        except ValueError:
            return "Invalid track parameter", 400
    else:
        track = None
        total_frames = sum(track_lengths.values())

    sample_rate = reader.sample_rate  # 44100
    channels = reader.channels  # 2
    bits_per_sample = reader.bits_per_sample  # 16

    # Generate WAV header with correct sizes
    buf = io.BytesIO()
    wav = wave.open(buf, 'wb')
    wav.setnchannels(channels)
    wav.setsampwidth(bits_per_sample // 8)
    wav.setframerate(sample_rate)
    wav.setnframes(total_frames)
    wav.writeframes(b'')
    buf.seek(0)
    header = buf.read()

    def generate():
        yield header
        # Read in chunks (multiple of 588 frames per sector for efficiency; ~1 second)
        chunk_size = 588 * 100
        remaining = total_frames
        while remaining > 0:
            to_read = min(chunk_size, remaining)
            framelist = reader.read(to_read)
            if len(framelist) == 0:
                break
            # Convert to little-endian signed bytes (WAV format)
            yield framelist.to_bytes(signed=True, big_endian=False)
            remaining -= len(framelist)
        reader.close()

    return Response(generate(), mimetype='audio/wav')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
