# MixedVoices

## Quick Start with Docker

1. Install Docker and Docker Compose
2. Clone this repository
3. Make .sh files executable
```bash
chmod +x dev.sh prod.sh
```
3. For dev build, run:
```bash
# Start development environment
./dev.sh up --build -d

# View logs
./dev.sh logs -f

# Stop development environment
./dev.sh down
```
4. For prod build, run:
```bash
# Start production environment
./prod.sh up --build -d

# View logs
./prod.sh logs -f

# Stop production environment
./prod.sh down
```

The server will be available at http://localhost:5001

## Usage

```python
import mixedvoices

# Create a new project
project = mixedvoices.create_project("receptionist")

# Create a version with metadata
version = project.create_version("v1", metadata={
    "prompt": "You are a friendly receptionist.",
    "silence_threshold": 0.1
})

# Add a recording
version.add_recording("hello.mp3")
```

## Development

To run locally without Docker:

1. Install PostgreSQL
2. Install the package:
```bash
pip install -e .
```

3. Set up the database:
```bash
python start_db.py
```

4. Run the server:
```bash
python run_server.py
```