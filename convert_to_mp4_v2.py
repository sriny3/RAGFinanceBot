import imageio.v3 as iio
import numpy as np

try:
    print("Loading demo_recording.webp...")
    # Read animated webp
    frames = iio.imread('demo_recording.webp', plugin='pillow', index=None)
    
    # Ensure frames are in the right format (H, W, C) and uint8
    if frames.ndim == 4:
        print(f"Extracted {len(frames)} frames. Writing to demo_recording.mp4...")
        # Write as mp4 using imageio-ffmpeg
        iio.imwrite('demo_recording.mp4', frames, fps=10)
        print("Successfully created MP4!")
    else:
        print(f"Unexpected shape: {frames.shape}")
except Exception as e:
    print("Error during conversion:")
    print(e)
