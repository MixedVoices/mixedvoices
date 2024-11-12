# MixedVoices 🎙️

MixedVoices is an analytics platform for voice agents - think Mixpanel for conversational AI. It helps you track, visualize, and optimize your voice agent's performance by analyzing conversation flows, identifying bottlenecks, and measuring success rates across different versions.

## Features

### Core Capabilities
- 📊 **Flow Visualization**: Interactive flowcharts showing conversation paths and patterns
- 🔄 **Version Control**: Track and compare agent behavior across different iterations
- 📈 **Success Rate Analytics**: Measure and optimize performance metrics
- 🔍 **Conversation Analysis**: Deep dive into individual interactions
- 📝 **Metadata Tracking**: Store and analyze version-specific configurations
- 🖥️ **Interactive Dashboard**: User-friendly interface for all operations

### Dashboard Features
- **Project Management**
  - Create and manage multiple projects
  - Version control with metadata tracking
  - Easy navigation between versions
- **Flow Visualization**
  - Interactive flowcharts of conversation paths
  - Success rate indicators for each step
  - Click-through analysis of specific paths
- **Recording Analysis**
  - Detailed view of individual recordings
  - Transcripts and audio playback
  - Success/failure tracking
  - Path visualization for each conversation
- **Upload Interface**
  - Easy upload of new recordings
  - Automatic processing and analysis

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

### Using Python API
```python
import mixedvoices as mv

# Create a new project
project = mv.create_project("receptionist")

# or load existing project
project = mv.load_project("receptionist")

# Create a version with metadata
version = project.create_version("v1", metadata={
    "prompt": "You are a friendly receptionist.",
    "silence_threshold": 0.1
})

# or load an existing version
version = project.load_version("v1")

# Add recording to analyze, by default this is non blocking and runs on a separate thread
version.add_recording("path/to/recording.wav", is_successful=True)

# run in blocking mode
version.add_recording("path/to/recording2.wav", blocking=True, is_successful=False)
```

### Using Dashboard
Launch the interactive dashboard:
```bash
mixedvoices
```

This will start:
- API server at http://localhost:8000
- Dashboard at http://localhost:8501

## Technical Requirements

### Core Dependencies
- Python ≥ 3.8
- FastAPI
- Streamlit
- OpenAI API access
- Plotly
- NetworkX

## Troubleshooting

### Common Issues
1. **API Connection Errors**
   - Verify your OpenAI API key is correctly set
   - Check your internet connection
   - Ensure you're not exceeding API rate limits

2. **Dashboard Not Loading**
   - Confirm both API server and dashboard ports are available
   - Check if required dependencies are installed
   - Verify Python version compatibility

3. **Recording Upload Issues**
   - Ensure audio files are in supported formats (.wav, .mp3)
   - Check file size limits
   - Verify storage permissions

<!-- ## API Documentation

Detailed API documentation is available at:
- Python API: `https://docs.mixedvoices.ai/api`
- REST API: `https://docs.mixedvoices.ai/rest` -->

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Setup
```bash
git clone https://github.com/yourusername/mixedvoices.git
pip install -e ".[dev]"
```

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

<!-- ## Support

- Documentation: `https://docs.mixedvoices.ai`
- Issues: `https://github.com/mixedvoices/issues`
- Email: support@mixedvoices.ai
- Discord: [Join our community](https://discord.gg/mixedvoices)

## Security

Please report security vulnerabilities to security@mixedvoices.ai -->

## Roadmap
- [ ] Unit Tests
- [ ] Async recording analysis
- [ ] Support other APIs and Open Source LLMs
- [ ] Team collaboration features
- [ ] Custom analytics plugins
- [ ] Enhanced visualization options

---
Made with ❤️ by the MixedVoices Team
