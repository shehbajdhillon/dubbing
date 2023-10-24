## Simple Program for Performing AI Dubbing

A Python script for dubbing videos using ChatGPT, ElevenLabs, and Whisper

Prerequisites:
1. Latest version of Python.
2. API keys for [OpenAI](https://platform.openai.com/) and [ElevenLabs](https://elevenlabs.io/).
3. [FFmpeg](https://ffmpeg.org/).

## Setup and Usage:

1. Clone the repository
```
$ git clone git@github.com:shehbajdhillon/dubbing.git && cd dubbing
```

2. Setup Python Virtual Enviroment and Install Dependencies
```
$ python3 -m venv env && source ./env/bin/activate 
(env) $ pip3 install -r requirements.txt
```
3. Make API keys from OpenAI and ElevenLabs available in your current environment
```
(env) $ export OPENAI_API_KEY=<API_KEY>
(env) $ export ELEVENLABS_API_KEY=<API_KEY>
```
4. Run the Python program and pass it an input video (not included in the repository) and [a language currently supported by ElevenLabs](https://help.elevenlabs.io/hc/en-us/articles/13313366263441-What-languages-do-you-support-).
```
(env) $ python3 main.py example_clip.mp4 hindi
```

## Resources
* Python Virtual Environments: https://docs.python.org/3/library/venv.html
* Whisper documentation: https://platform.openai.com/docs/guides/speech-to-text
* GPT-4 Documentation: https://platform.openai.com/docs/guides/gpt
* ElevenLabs Documentation: https://docs.elevenlabs.io/introduction
* FFmpeg Documentation: https://ffmpeg.org/ffmpeg.html (Or just ask ChatGPT for help with FFmpeg 😆)
