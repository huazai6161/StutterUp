# README.md

# StutterUp

## Overview
StutterUp is a Python-based tool designed to support speech analysis and script optimization. By combining speech-to-text technology with powerful language models, it generates helpful diagnostics and suggestions to enhance speech fluency and clarity.

## Requirements
Ensure Python is installed on your machine. All required libraries are listed in `/requirements.txt`.

## Setup Instructions
1. Clone the repository:
   ```
   git clone <repository-url>
   cd StutterUp
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate
   ```

3. Install the required packages:
   ```
   pip install -r src/requirements.txt
   ```

4. Set up your API keys:
   - Create a `.env` file in the root directory and add your API keys:
     ```
     ELEVENLABS_API_KEY=<your-elevenlabs-api-key>
     API_KEY_302=<your-302-api-key>
     ```

## Running the Application
To run the application, execute the following command:
```
python app.py
```

## How to Use
Once the application is running, you can access the user interface through your web browser. Follow the on-screen instructions to transcribe audio and analyze speech scripts.

## License
Distributed under the MIT License.