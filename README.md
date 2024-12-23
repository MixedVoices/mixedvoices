# MixedVoices 🎙️

[MixedVoices](https://www.mixedvoices.xyz) is a comprehensive analytics and evaluation tool for voice agents - think Mixpanel for conversational AI. It helps you track, visualize, and optimize your voice agent's performance through detailed conversation analysis, ML metrics, and call quality measurements. Use MixedVoices to analyze conversation flows, identify bottlenecks, measure success rates across versions, and evaluate agent performance through simulated scenarios.

## Features

### Core Capabilities
- 🌐 **Effortless Integration**: Python API designed for quick and seamless integration, ensuring developers can get started in minutes
- 🖥️ **Interactive Dashboard**: User-friendly interface for all operations
- 📊 **Call Flow Analysis**: Interactive flowcharts showing conversation paths, patterns and success rates
- 🔄 **Version Control**: Track and compare agent behavior across different iterations
- 🎯 **ML Performance Metrics**: Track hallucinations, call scheduling, conciseness, and empathy scores
- 📱 **Call Quality Analysis**: Monitor interruptions, latency, signal-to-noise ratio, and words per minute
- 🧪 **Agent Evaluation**: Test and validate agent performance through simulations and stress testing

## Installation

```bash
pip install mixedvoices
```

### Prerequisites
1. Python 3.8 or higher
2. OpenAI API key (set in your environment variables)

```bash
export OPENAI_API_KEY='your-api-key'
```

## Quick Start

### Using Python API to analyze recordings
```python
import mixedvoices as mv

# Create a new project
project = mv.create_project("receptionist")

# or load existing project
project = mv.load_project("receptionist")

# Create a version with prompt and metadata (optional)
version = project.create_version(
    "v1", prompt="You are a friendly receptionist", metadata={"silence_threshold": 0.1}
)

# or load an existing version
version = project.load_version("v1")

# Add recording to analyze, by default this is blocking and may take a few seconds
version.add_recording("path/to/recording.wav", is_successful=True)

# run in non blocking mode in a separate thread
version.add_recording("path/to/recording2.wav", blocking=False, is_successful=False)
```

### Using Python API to run simulations to evaluate agent
```python
import mixedvoices as mv

# create a new class that inherits from `BaseAgent`. Must implement respond and starts_conversation
class ReceptionAgent(mv.BaseAgent):
    def __init__(self):
        self.assistant = ReceptionistAssistant(model="gpt-4o")

    def respond(self, input_text: str) -> Tuple[str, bool]:
        response = self.assistant.get_assistant_response(input_text)
        has_conversation_ended = check_conversation_ended(response)
        return response, has_conversation_ended

    @property
    def starts_conversation(self):
        return True


project = mv.load_project("receptionist")
version = project.load_version("v1")
evaluator = version.create_evaluator()
evaluator.run(ReceptionAgent) # can specify which metrics to measure
```

### Using Dashboard
Launch the interactive dashboard:
```bash
mixedvoices
```

This will start:
- API server at http://localhost:7760
- Dashboard at http://localhost:7761

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Setup
```bash
git clone https://github.com/MixedVoices/MixedVoices.git
pip install -e ".[dev]"
```

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

## Roadmap
- [ ] Unit Tests
- [ ] Support other APIs and Open Source LLMs
- [ ] Team collaboration features
- [ ] Custom analytics plugins
- [ ] Enhanced visualization options
- [ ] Advanced evaluation scenarios
- [ ] Custom metric definitions for evaluation

---
Made with ❤️ by the MixedVoices Team
