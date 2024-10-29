from collections import defaultdict
TRANSCRIBERS = defaultdict(dict)

# TODO: Add more transcribers

def transcribe_with_whisper(audio_path, model):
    import whisper

    whisper_models = TRANSCRIBERS["whisper"]

    if model in whisper_models:
        transcriber = whisper_models[model]
    else:
        transcriber = whisper.load_model(model)
        TRANSCRIBERS["whisper"][model] = transcriber
    return transcriber.transcribe(audio_path)
