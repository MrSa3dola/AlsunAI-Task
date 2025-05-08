## WhatsApp AI Math Assistant

This project integrates a WhatsApp Business API with an AI-powered backend to handle math-related queries in both Arabic and English. It features:

- **Language Detection & Translation**: Automatically detects the message language and translates Arabic to English using the OpenL Free API.
- **Math Evaluation**: Utilizes Sympy for evaluating mathematical expressions.
- **AI Agent**: Employs OpenAI's GPT-3.5-Turbo via LangGraph to determine if a query is math-related.
- **Voice Response**: Sends a predefined Arabic audio response for voice messages using ElevenLabs TTS.
- **Webhook Integration**: FastAPI server with GET and POST endpoints to handle WhatsApp webhook verification and message processing.

---

### 📂 Repository Structure

```
AlsunAI-Task/
├── math_agent.py # LangGraph agent setup with GPT-3.5-Turbo
├── translation.py # Language detection and translation logic
├── webhook.py # FastAPI server with webhook endpoints
├── tools/
│ └── calculator.py # Sympy-based calculator tool
├── static/
│ └── Arabic.mp3 # Predefined Arabic audio response
├── requirements.txt # Python dependencies
├── README.md # Project documentation
└── Demo.mp4 # Demonstration video
```
---

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Ngrok (for tunneling localhost)
- WhatsApp Business API credentials
- OpenAI API key
- OpenL Free API credentials

### Installation

1. **Clone the repository**:

   ```bash
   git clone https://github.com/MrSa3dola/AlsunAI-Task.git
   cd AlsunAI-Task```
2. **Install dependencies**:

  ```pip install -r requirements.txt```
3. Set up environment variables:

Create a .env file in the root directory and add your API keys:

```OPENAI_API_KEY=your_openai_api_key
OPENAI_API_KEY=
OPENL_API_KEY=
VERSION=
WA_TOKEN=
PHONE_NUMBER_ID=
WA_ACCOUNT_ID=
WA_VERIFY_TOKEN=
```
4. Run the FastAPI server:
```uvicorn webhook:app --reload```
5. Expose the server using Ngrok:
```ngrok http 8000```
Use the generated Ngrok URL to set up your WhatsApp webhook.

### Demo
[Link](https://drive.google.com/file/d/1QeX22nkI43vnqoZLoZlfdsJ7LL1hI9Ia/view?usp=drive_link)

### Documentation
[Link](https://docs.google.com/document/d/19q1rY2hQGqxTH7jtdlaXQjX6JyABcnTUuAJyUsbmLFU/edit?usp=drive_link)
