import os
import chardet
import ffmpeg
from django.conf import settings
from django.shortcuts import render, redirect
from .forms import VideoUploadForm
from .models import Video, Subtitle

def upload_video(request):
    if request.method == 'POST':
        form = VideoUploadForm(request.POST, request.FILES)
        if form.is_valid():
            video = form.save()
            # Call a function to process the video and extract subtitles
            process_video(video)
            return redirect('video_list')
    else:
        form = VideoUploadForm()
    return render(request, 'app/upload.html', {'form': form})

def process_video(video):
    video_path = video.video_file.path
    subtitle_dir = os.path.join(settings.MEDIA_ROOT, 'subtitles')

    # Ensure the directory exists
    os.makedirs(subtitle_dir, exist_ok=True)

    try:
        # Probe the video for all subtitle streams
        probe = ffmpeg.probe(video_path, select_streams='s', show_entries='stream=index:stream_tags=language', format='json')
        subtitle_streams = probe['streams']

        if not subtitle_streams:
            print("No subtitle streams found.")
            return

        # Extract and save each subtitle stream in WebVTT format
        for stream in subtitle_streams:
            index = stream['index']
            # Try to get the correct language tag; fallback if unavailable
            language = stream.get('tags', {}).get('language', f'sub_{index}')  
            # Ensure language tag is lowercase for correct integration with the <track> element
            language = language.lower()

            # Save subtitles in WebVTT format
            output_subtitle_path = os.path.join(subtitle_dir, f"{video.id}_sub_{index}_{language}.vtt")
            try:
                # Extract subtitle stream using ffmpeg and convert it to WebVTT format
                print(f"Extracting subtitle stream {index} ({language}) to {output_subtitle_path}")
                
                # Adding '?' to the stream map to ignore missing streams
                ffmpeg.input(video_path).output(output_subtitle_path, map=f'0:s:{index}?', format='webvtt').run(capture_stdout=True, capture_stderr=True)

                if os.path.exists(output_subtitle_path) and os.path.getsize(output_subtitle_path) > 0:
                    # Detect the encoding of the extracted file
                    with open(output_subtitle_path, 'rb') as subtitle_file:
                        raw_data = subtitle_file.read()
                        result = chardet.detect(raw_data)
                        encoding = result['encoding'] or 'utf-8'  # Fallback to utf-8

                    # Read the subtitle file using the detected encoding
                    try:
                        with open(output_subtitle_path, 'r', encoding=encoding) as subtitle_file:
                            subtitle_text = subtitle_file.read()

                            # Save the subtitle text in the database
                            Subtitle.objects.create(video=video, language=language, subtitle_file=subtitle_text)
                    except UnicodeDecodeError:
                        print(f"Error decoding subtitle file: {output_subtitle_path}. Retrying with utf-8 encoding.")
                        with open(output_subtitle_path, 'r', encoding='utf-8') as subtitle_file:
                            subtitle_text = subtitle_file.read()
                            Subtitle.objects.create(video=video, language=language, subtitle_file=subtitle_text)

                else:
                    print(f"Subtitle file is empty: {output_subtitle_path}")

            except ffmpeg.Error as e:
                print(f"ffmpeg error for stream {index}: {e.stderr.decode()}")

    except ffmpeg.Error as e:
        print(f"ffmpeg probe error: {e.stderr.decode()}")

def video_list(request):
    videos = Video.objects.all()
    return render(request, 'app/list.html', {'videos': videos})

def video_detail(request, video_id):
    video = Video.objects.get(id=video_id)
    subtitles = video.subtitles.all()  # Retrieve all subtitles for the video
    return render(request, 'app/detail.html', {'video': video, 'subtitles': subtitles})

