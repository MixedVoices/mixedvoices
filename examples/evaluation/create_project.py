import mixedvoices as mv
from examples.evaluation.agent import AGENT_PROMPT

project = mv.create_project("dental_clinic")
version = project.create_version("v1", prompt=AGENT_PROMPT)
version.add_recording("/Users/abhinavtuli/Documents/MixedVoices/data/call1.wav")
version.add_recording("/Users/abhinavtuli/Documents/MixedVoices/data/call2.wav")
