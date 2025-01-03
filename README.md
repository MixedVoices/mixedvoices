<h1 align="center">MixedVoices: Analytics and Evals for Voice Agents</h1>
<p align="center">
<a href="https://pypi.org/project/mixedvoices/"><img src="https://badge.fury.io/py/mixedvoices.svg" alt="PyPI version" height="18"></a>
<a href="https://mixedvoices.gitbook.io/docs"><img src="https://img.shields.io/badge/docs-GitBook-blue" alt="Documentation" height="18"></a>
</p>

[MixedVoices](https://www.mixedvoices.xyz) is an analytics and evaluation tool for voice agents. Track, visualize, and optimize agent performance through conversation analysis, call quality metrics and call flow charts. Run simulations to test the agent before pushing to production.

## Features

### Core Capabilities
- 🌐 **Effortless Integration**: Python API designed for quick integration, get started in minutes
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

# Quick Start

## Analytics
### Using Python API to analyze recordings
```python
import mixedvoices as mv
from mixedvoices.metrics import Metric, empathy

custom_metric = Metric(name="...", definition="...", scoring="binary")
my_metrics = [empathy, custom_metric]
project = mv.create_project("receptionist", metrics=my_metrics) # Create a new project
project = mv.load_project("receptionist") # or load existing project

v1 = project.create_version("v1", prompt="You are a ...") # Create a version
v1 = project.load_version("v1") # or load existing version

# Analyze call, this is blocking, takes a few seconds
v1.add_recording("path/to/call.wav") 

# non blocking mode in a separate thread, instantaneous
v1.add_recording("path/to/call.wav", blocking=False) 

```

## Evaluation
### Evaluate custom agent
```python
import mixedvoices as mv

# inherits from `BaseAgent`. Must implement respond
class ReceptionAgent(mv.BaseAgent):
   def __init__(self, model="gpt-4", temperature=0.7):
        self.agent = YourAgentImplementation(
            model=model,
            temperature=temperature
        )

    def respond(self, input_text: str) -> Tuple[str, bool]:
        response = self.agent.get_response(input_text)
        has_conversation_ended = check_conversation_ended(response)
        return response, has_conversation_ended

project = mv.load_project("receptionist")
v1 = project.load_version("v1")

# Generate test cases
test_generator = mv.TestCaseGenerator(v1.prompt)
test_generator.add_from_descriptions(["..."]).add_edge_cases(5).add_from_recordings(["call1.wav"]
test_cases = test_generator.generate()

evaluator = project.create_evaluator(test_cases)
evaluator.run(v1, ReceptionAgent, agent_starts=False, model="gpt-4-turbo", temperature=0.9)
```

### Evaluate Bland AI Agent
```python
# same as above, except instead of defining custom agent, can directly use mv.BlandAgent
evaluator.run(v1, mv.BlandAgent, agent_starts=True, auth_token="", pathway_id="", start_node_id="") 
```

## Using Dashboard
Launch the interactive dashboard from the Command Line:
```bash
mixedvoices dashboard
```

### Choosing Models
You can configure the models being used for different tasks from the Command Line
```bash
mixedvoices config
```

## Development Setup
```bash
git clone https://github.com/MixedVoices/MixedVoices.git
pip install -e ".[dev]"
```

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

## Roadmap
- [ ] Support other APIs and Open Source LLMs
- [ ] Team collaboration features
- [ ] Custom analytics plugins
- [ ] Advanced evaluation scenarios
- [ ] Custom metric definitions for evaluation

---
Made with ❤️ by the MixedVoices Team
