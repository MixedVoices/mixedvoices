import mixedvoices


project = mixedvoices.create_project("receptionist2")
# or if already exists
project = mixedvoices.load_project("receptionist2")

# metadata can be any json serializable object
version = project.create_version("v1", metadata={"prompt": "You are a friendly receptionist.", "silence_threshold": 0.1})
# or if already exists
version = project.load_version("v1")

version.add_recording("hello.mp3")