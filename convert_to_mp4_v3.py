import imageio.v3 as iio
import numpy as np

try:
    print("Loading demo_recording.webp...")
    # Read frames one by one if index=None is behaving unexpectedly
    frames = []
    for frame in iio.imiter('demo_recording.webp', plugin='pillow'):
        frames.append(frame)
    
    frames = np.stack(frames)
    print(f"Extracted {len(frames)} frames. Shape: {frames.shape}")
    
    print(f"Writing to demo_recording.mp4...")
    # Write as mp4
    iio.imwrite('demo_recording.mp4', frames, fps=10)
    print("Successfully created MP4!")
except Exception as e:
    print("Error during conversion:")
    print(e)
