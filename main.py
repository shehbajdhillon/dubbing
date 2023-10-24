import os
import sys
import subprocess

import openai
openai.api_key = os.getenv("OPENAI_API_KEY")

import elevenlabs
elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
elevenlabs.set_api_key(elevenlabs_api_key)


def transcribe_audio(file_path):
    file = open(file_path, "rb")
    transcript = openai.Audio.transcribe(
        model="whisper-1",
        file=file,
        response_format="verbose_json"
    )
    return transcript


def translate_segment(input_text, input_language):

    systemMessage = '''
        You are an expert translator that can translate texts to and from different languages.
        You will translate the input text and will only output the translation
    '''

    userMessage = f'''
        Translate the following text to colloquial {input_language}: {input_text}
    '''

    completion = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            { "role": "system", "content": systemMessage },
            { "role": "user", "content": userMessage }
        ]
    )

    return completion.choices[0].message.content


def clone_voice(file_path):
    voice = elevenlabs.clone(
        name="Cloned Voice",
        files=[file_path],
    )
    return voice


def generate_speech(input_text, voice_object, output_file_path):
    audio = elevenlabs.generate(
        text=input_text,
        voice=voice_object,
        model="eleven_multilingual_v2"
    )

    with open(output_file_path, "wb") as f:
        f.write(audio)


def get_file_name_and_format(file_path):
    file_tokens = file_path.split(".")
    return ".".join(file_tokens[:-1]), file_tokens[-1]


def get_video_segment_path(file_path, segment):
    file_name, file_format = get_file_name_and_format(file_path)
    segment_id = segment['id']
    return f"{file_name}_segment_{segment_id}.{file_format}"


def get_audio_file_path(file_path, segment, input_language):
    file_name, _ = get_file_name_and_format(file_path)
    segment_id = segment['id']
    return f"{file_name}_segment_{segment_id}_{input_language}.mp3"


def get_stretched_audio_file_path(file_path):
    file_name, file_format = get_file_name_and_format(file_path)
    return f"{file_name}_stretched.{file_format}"


def get_dubbed_video_segment_path(file_path):
    file_name, file_format = get_file_name_and_format(file_path)
    return f"{file_name}_dubbed.{file_format}"


def get_dubbed_video_file_path(file_path, input_language):
    file_name, file_format = get_file_name_and_format(file_path)
    return f"{file_name}_dubbed_{input_language}.{file_format}"


def get_before_video_segment_path(file_path):
    file_name, file_format = get_file_name_and_format(file_path)
    return f"{file_name}_before.{file_format}"


def get_after_video_segment_path(file_path):
    file_name, file_format = get_file_name_and_format(file_path)
    return f"{file_name}_after.{file_format}"


def cut_segment(file_path, start, end, segment_path, mute=True):
    # The following ffmpeg command will slice the input video using the specified start and end times
    volume = 'volume=0' if mute else 'volume=1'
    ffmpeg_cmd = f"ffmpeg -i file:{file_path} -ss {start} -to {end} -af '{volume}' file:{segment_path}"
    return os.system(ffmpeg_cmd)


def delete_files(files):
    # Utility function to help us delete files written to disk
    delete_cmd = f"rm -rf {' '.join(files)}"
    os.system(delete_cmd)


def get_media_file_length(file_path):
    # The following ffprobe (part of ffmpeg) command will help us get the duration of a media file.
    ffmpeg_cmd = \
        f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 file:{file_path}"
    cmd_tokens = ffmpeg_cmd.split(" ")
    output = subprocess.run(cmd_tokens, text=True, capture_output=True, check=True)
    return float(output.stdout.strip())


def layer_video_audio(video_segment_path, audio_file_path):

    video_length = get_media_file_length(video_segment_path)
    audio_length = get_media_file_length(audio_file_path)

    # Calculate the stretching ratio for the audio file so that it fits over the video segment properly.
    audio_stretching_ratio = round(audio_length / video_length, 3)

    stretched_audio_file_path = get_stretched_audio_file_path(audio_file_path)
    dubbed_video_segment_path = get_dubbed_video_segment_path(video_segment_path)

    # Ffmpeg command to stretch audio file
    audio_stretch_cmd = \
        f"ffmpeg -i file:{audio_file_path} -filter:a 'atempo={audio_stretching_ratio}' file:{stretched_audio_file_path}"
    os.system(audio_stretch_cmd)

    # Ffmpeg command to layer over an audio file over a video file
    layer_elements_cmd = \
        f"ffmpeg -i file:{video_segment_path} -i file:{stretched_audio_file_path} -c:v copy -map 0:v:0 -map 1:a:0 file:{dubbed_video_segment_path}"
    os.system(layer_elements_cmd)

    delete_files([stretched_audio_file_path])

    return dubbed_video_segment_path


def combine_segments(segment_files, output_file_path):

    # How to concatenate files in FFMPEG: https://trac.ffmpeg.org/wiki/Concatenate

    input_list = []
    filter_list = []

    for idx, file_name in enumerate(segment_files):
        input_list.append(f"-i file:{file_name}")
        filter_list.append(f"[{idx}:v][{idx}:a]")

    filter_list.append(f"concat=n={len(segment_files)}:v=1:a=1[v][a]")

    input_args = " ".join(input_list)
    filter_ags = "".join(filter_list)

    ffmpeg_cmd = \
        f"ffmpeg {input_args} -filter_complex '{filter_ags}' -map '[v]' -map '[a]' -vsync 2 file:{output_file_path}"

    return os.system(ffmpeg_cmd)


def main():
    file_path, input_language = sys.argv[1:]
    input_language = str(input_language).lower()
    transcript = transcribe_audio(file_path=file_path)
    segments = transcript.segments

    # Cut out the first segment from the input video for voice cloning
    initial_segment = segments[0]
    initial_segment_path = get_video_segment_path(file_path, initial_segment)
    cut_segment(file_path, initial_segment.start, initial_segment.end, initial_segment_path, mute=False)
    voice_object = clone_voice(initial_segment_path)
    delete_files([initial_segment_path])

    processed_segments = []

    for idx, segment in enumerate(segments):
        translated_text = translate_segment(segment.text, input_language)

        audio_file_path = get_audio_file_path(file_path, segment, input_language)
        generate_speech(translated_text, voice_object, audio_file_path)

        video_segment_path = get_video_segment_path(file_path, segment)
        cut_segment(file_path, segment.start, segment.end, video_segment_path)

        before_segment_path = get_before_video_segment_path(video_segment_path)
        if idx == 0 and segment.start > 0.00:
            cut_segment(file_path, 0.00, segment.start, before_segment_path)
            processed_segments.append(before_segment_path)
        elif idx > 0:
            cut_segment(file_path, segments[idx - 1].end, segment.start, before_segment_path)
            processed_segments.append(before_segment_path)

        dubbed_video_segment = layer_video_audio(video_segment_path, audio_file_path)
        processed_segments.append(dubbed_video_segment)

        if idx == len(segments) - 1 and segment.end < get_media_file_length(file_path):
            after_segment_path = get_after_video_segment_path(video_segment_path)
            cut_segment(file_path, segment.end, get_media_file_length(file_path), after_segment_path)
            processed_segments.append(after_segment_path)

        delete_files([audio_file_path, video_segment_path])


    dubbed_video_file_path = get_dubbed_video_file_path(file_path, input_language)
    combine_segments(processed_segments, dubbed_video_file_path)
    delete_files(processed_segments)

    return dubbed_video_file_path


if __name__ == "__main__":
    main()

