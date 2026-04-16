from PIL import Image
import sys

def convert_webp_to_gif(webp_path, gif_path):
    print(f"Loading {webp_path}...")
    img = Image.open(webp_path)
    frames = []
    
    try:
        while True:
            frames.append(img.copy())
            img.seek(len(frames))
    except EOFError:
        pass
        
    print(f"Extracted {len(frames)} frames. Saving as {gif_path}...")
    if frames:
        frames[0].save(
            gif_path,
            save_all=True,
            append_images=frames[1:],
            duration=img.info.get('duration', 100),
            loop=0
        )
        print("Conversion successful!")
    else:
        print("No frames found!")

if __name__ == '__main__':
    convert_webp_to_gif('demo_recording.webp', 'demo_recording.gif')
