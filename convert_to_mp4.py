import moviepy as mp

try:
    print("Loading demo_recording.webp...")
    clip = mp.VideoFileClip("demo_recording.webp")
    print("Writing to demo_recording.mp4...")
    clip.write_videofile("demo_recording.mp4", codec="libx264", audio=False)
    print("Successfully created MP4!")
except Exception as e:
    print("Error during conversion:")
    print(e)
