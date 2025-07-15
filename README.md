# Flask Chat Server with Groq API

A powerful Flask-based chat server that integrates with Groq's API for fast LLM responses, featuring conversation management, email notifications, and a comprehensive testing interface.

## 🚀 Features

- **Fast LLM Integration** - Powered by Groq's high-performance API
- **Multiple Llama Models** - Support for various Llama 3.1 and 3.2 models
- **Conversation Management** - Persistent conversation history with metadata
- **Email Notifications** - Contact admin feature with automatic email forwarding
- **Model Switching** - Runtime model switching for testing
- **Health Monitoring** - Built-in health checks and API testing
- **CORS Support** - Ready for frontend integration
- **Comprehensive API** - RESTful endpoints for all functionality

## 📋 Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [API Endpoints](#api-endpoints)
- [Usage Examples](#usage-examples)
- [Testing](#testing)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- Groq API key (get from [Groq Console](https://console.groq.com/keys))
- Email account with app password (for Gmail)

### Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd flask-chat-server
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install flask flask-cors groq python-dotenv
```

4. **Create environment file**
```bash
cp .env.example .env
```

5. **Configure environment variables** (see Configuration section)

6. **Run the server**
```bash
python app.py
```

## ⚙️ Configuration

Create a `.env` file in the project root with the following variables:

### Required Variables

```env
# Groq API Configuration
GROQ_API_KEY=your_groq_api_key_here

# Email Configuration
EMAIL_USER=your.email@gmail.com
EMAIL_PASSWORD=your_app_password_here
ADMIN_EMAIL=admin@example.com
```

### Optional Variables

```env
# Model Configuration
GROQ_MODEL=llama-3.1-70b-versatile

# Email Server Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
```

### Getting Your Groq API Key

1. Visit [Groq Console](https://console.groq.com/keys)
2. Sign up or log in
3. Create a new API key
4. Copy the key to your `.env` file

### Email Setup (Gmail)

1. Enable 2-factor authentication on your Gmail account
2. Generate an app password:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
   - Use this password in `EMAIL_PASSWORD`

## 📡 API Endpoints

### Chat Endpoints

#### POST `/api/chat`
Send a message to the AI assistant.

**Request Body:**
```json
{
  "message": "Hello, how are you?",
  "conversation_id": "optional-conversation-id",
  "user_email": "optional@email.com"
}
```

**Response:**
```json
{
  "response": "AI response here",
  "conversation_id": "uuid-conversation-id"
}
```

**Error Response:**
```json
{
  "response": "",
  "error": "Error message here"
}
```

### Conversation Management

#### GET `/api/conversation/<conversation_id>`
Retrieve conversation history.

**Response:**
```json
{
  "conversation_id": "uuid",
  "messages": [
    {
      "role": "user",
      "content": "Message content",
      "timestamp": "2024-01-01T00:00:00"
    }
  ],
  "metadata": {
    "created_at": "2024-01-01T00:00:00",
    "user_email": "user@example.com",
    "model": "llama-3.1-70b-versatile"
  }
}
```

#### DELETE `/api/conversation/<conversation_id>`
Delete a conversation.

**Response:**
```json
{
  "message": "Conversation deleted successfully"
}
```

#### GET `/api/conversations`
List all conversations.

**Response:**
```json
[
  {
    "conversation_id": "uuid",
    "message_count": 5,
    "last_message": {
      "role": "assistant",
      "content": "Last message content",
      "timestamp": "2024-01-01T00:00:00"
    },
    "metadata": {
      "created_at": "2024-01-01T00:00:00",
      "user_email": "user@example.com",
      "model": "llama-3.1-70b-versatile"
    }
  }
]
```

### System Endpoints

#### GET `/api/health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00",
  "model": "llama-3.1-70b-versatile",
  "groq_client_ready": true
}
```

#### GET `/api/test-api`
Test Groq API connection.

**Response:**
```json
{
  "status": "success",
  "response": "API test successful",
  "model": "llama-3.1-70b-versatile"
}
```

#### GET `/api/models`
List available Groq models.

**Response:**
```json
{
  "current_model": "llama-3.1-70b-versatile",
  "available_models": [
    "llama-3.1-70b-versatile",
    "llama-3.1-8b-instant",
    "llama-3.2-90b-text-preview"
  ],
  "llama_models": ["..."],
  "note": "Update GROQ_MODEL to llama-4 when available"
}
```

#### POST `/api/switch-model`
Switch to a different model (for testing).

**Request Body:**
```json
{
  "model": "llama-3.1-8b-instant"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Successfully switched to llama-3.1-8b-instant",
  "test_response": "Hello",
  "old_model": "llama-3.1-70b-versatile",
  "new_model": "llama-3.1-8b-instant"
}
```

## 💡 Usage Examples

### Basic Chat

```python
import requests

# Send a message
response = requests.post('http://localhost:5000/api/chat', json={
    'message': 'Explain quantum computing in simple terms'
})

data = response.json()
print(f"AI: {data['response']}")
print(f"Conversation ID: {data['conversation_id']}")
```

### Continue Conversation

```python
# Continue the conversation
response = requests.post('http://localhost:5000/api/chat', json={
    'message': 'Can you give me a practical example?',
    'conversation_id': data['conversation_id']
})

print(f"AI: {response.json()['response']}")
```

### Contact Admin Feature

```python
# User wants to contact admin
response = requests.post('http://localhost:5000/api/chat', json={
    'message': 'I want to contact you about this amazing chat feature!',
    'user_email': 'user@example.com'
})

# This will automatically send an email to the admin
print(f"AI: {response.json()['response']}")
```

### JavaScript Frontend Integration

```javascript
class ChatClient {
    constructor(serverUrl = 'http://localhost:5000') {
        this.serverUrl = serverUrl;
        this.conversationId = null;
    }
    
    async sendMessage(message, userEmail = null) {
        const response = await fetch(`${this.serverUrl}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message,
                conversation_id: this.conversationId,
                user_email: userEmail
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            this.conversationId = data.conversation_id;
            return data.response;
        } else {
            throw new Error(data.error);
        }
    }
    
    async getConversationHistory() {
        if (!this.conversationId) return null;
        
        const response = await fetch(`${this.serverUrl}/api/conversation/${this.conversationId}`);
        return await response.json();
    }
}

// Usage
const chat = new ChatClient();
const response = await chat.sendMessage('Hello!');
console.log(response);
```

## 🧪 Testing

### Using the HTML Test Interface

1. **Start the server**
```bash
python app.py
```

2. **Open the test interface**
```bash
# Save the provided HTML file as chat_tester.html
open chat_tester.html  # or double-click to open in browser
```

3. **Run tests**
   - Health check
   - API connectivity
   - Model switching
   - Conversation management
   - Contact intent detection

### Manual Testing with curl

```bash
# Health check
curl -X GET http://localhost:5000/api/health

# Send a message
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, world!"}'

# Test API connection
curl -X GET http://localhost:5000/api/test-api

# List available models
curl -X GET http://localhost:5000/api/models
```

### Python Testing Script

```python
import requests
import json

def test_chat_server():
    base_url = 'http://localhost:5000'
    
    # Health check
    response = requests.get(f'{base_url}/api/health')
    print(f"Health: {response.json()}")
    
    # Test API
    response = requests.get(f'{base_url}/api/test-api')
    print(f"API Test: {response.json()}")
    
    # Send message
    response = requests.post(f'{base_url}/api/chat', json={
        'message': 'Hello, how are you?'
    })
    print(f"Chat: {response.json()}")

if __name__ == '__main__':
    test_chat_server()
```

## 🚀 Deployment

### Local Development

```bash
# Run with debug mode
python app.py
```

### Production Deployment

#### Using Gunicorn

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

#### Using Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

#### Environment Variables for Production

```env
# Production settings
FLASK_ENV=production
GROQ_API_KEY=your_production_key
EMAIL_USER=production@email.com
EMAIL_PASSWORD=production_password
ADMIN_EMAIL=admin@production.com
```

### Reverse Proxy (Nginx)

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## 🔧 Troubleshooting

### Common Issues

#### 1. "Groq client not initialized"
```bash
# Check your API key
echo $GROQ_API_KEY

# Verify API key is valid
curl -H "Authorization: Bearer $GROQ_API_KEY" https://api.groq.com/openai/v1/models
```

#### 2. "Invalid API key"
- Ensure your Groq API key is correct
- Check if the key has expired
- Verify you're using the correct environment variable name

#### 3. "Rate limit exceeded"
- Groq has rate limits on API calls
- Implement exponential backoff
- Consider upgrading your Groq plan

#### 4. "Email sending failed"
- Check email credentials
- Ensure app password is used for Gmail
- Verify SMTP settings

#### 5. "Model not found"
- Check available models: `GET /api/models`
- Update `GROQ_MODEL` to a valid model name
- Some models may be region-specific

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Performance Tips

1. **Use faster models** for development (`llama-3.1-8b-instant`)
2. **Implement caching** for repeated requests
3. **Use connection pooling** for database connections
4. **Implement rate limiting** to prevent abuse
5. **Monitor API usage** to optimize costs

## 📝 API Response Examples

### Successful Chat Response
```json
{
  "response": "Hello! I'm an AI assistant powered by Llama 3.1 70B. I'm here to help you with questions, tasks, and conversations. How can I assist you today?",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Error Response
```json
{
  "response": "",
  "error": "Invalid API key. Please check your GROQ_API_KEY."
}
```

### Contact Intent Response
```json
{
  "response": "Thank you for your message! I've forwarded it to the admin and they'll get back to you soon.",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Clone and setup
git clone <repository-url>
cd flask-chat-server
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install development dependencies
pip install pytest black flake8

# Run tests
pytest

# Format code
black .

# Lint code
flake8 .
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Groq](https://groq.com/) for providing fast LLM inference
- [Flask](https://flask.palletsprojects.com/) for the web framework
- [Llama Models](https://llama.meta.com/) for the language models

## 📞 Support

- **Issues**: Open an issue on GitHub
- **Documentation**: Check this README
- **API Reference**: See the API endpoints section
- **Testing**: Use the provided HTML test interface

---

**Made with ❤️ for the AI community**