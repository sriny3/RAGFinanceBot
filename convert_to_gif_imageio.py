import imageio.v3 as iio

try:
    print("Loading demo_recording.webp...")
    # Read animated webp
    frames = iio.imread('demo_recording.webp', plugin='pillow', index=None)
    print(f"Extracted {len(frames)} frames. Writing to demo_recording.gif...")
    
    # Write as gif
    iio.imwrite('demo_recording.gif', frames, plugin='pillow', loop=0, duration=100)
    print("Successfully created GIF!")
except Exception as e:
    print("Error during conversion:")
    print(e)
