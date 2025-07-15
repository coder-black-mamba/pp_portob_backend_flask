from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import uuid
from datetime import datetime
import json
from typing import Dict, List, Optional
import dotenv

dotenv.load_dotenv()

app = Flask(__name__)
# Allow all origins and common HTTP methods for frontend running on localhost or file://
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True, methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

# Configuration - Add these to your environment variables
GROQ_API_KEY = os.getenv('GROQ_API_KEY', 'your-groq-api-key')

# Using the latest Llama model available - update to llama-4 when available
GROQ_MODEL = os.getenv('GROQ_MODEL', 'llama-3.1-70b-versatile')

# Email configuration
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USER = os.getenv('EMAIL_USER', 'your-email@gmail.com')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', 'your-app-password')
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@example.com')

# Initialize Groq client
try:
    groq_client = Groq(api_key=GROQ_API_KEY)
    print(GROQ_API_KEY)
    print("✅ Groq client initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize Groq client: {e}")
    groq_client = None

# In-memory storage for conversations (use database in production)
conversations: Dict[str, List[Dict]] = {}
conversation_metadata: Dict[str, Dict] = {}

class ChatResponse:
    def __init__(self, response: str, conversation_id: Optional[str] = None, error: Optional[str] = None):
        self.response = response
        self.conversation_id = conversation_id
        self.error = error
    
    def to_dict(self):
        result = {"response": self.response}
        if self.conversation_id:
            result["conversation_id"] = self.conversation_id
        if self.error:
            result["error"] = self.error
        return result

def call_groq_api(message):
    """Call Groq API using official Python library"""
    if not groq_client:
        raise Exception("Groq client not initialized. Please check your API key.")
    
    try:
        print(f"Making API request using Groq Python library")
        print(f"Using model: {GROQ_MODEL}")
        # Log the type and size of the incoming message for easier debugging
        if isinstance(message, list):
            print(f"Incoming message is a list with {len(message)} item(s)")
        else:
            print(f"Incoming message is a str of length {len(message)}")
        
        # Create chat completion using Groq client
        chat_completion = groq_client.chat.completions.create(
            # Build the prompt. If `message` is already a list of chat dictionaries, we
            # append it after the system prompt. Otherwise we wrap the single user
            # message in the expected format.
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an assistant for Abu Sayed's developer portfolio. "
                        "You are talking to a potential HR, manager, or developer who "
                        "is visiting the portfolio and helping them with their queries. "
                        "You should be professional and provide accurate information. "
                        "Return responses in markdown format."
                    ),
                }
            ] + (
                message if isinstance(message, list) else [{"role": "user", "content": message}]
            ),
            model=GROQ_MODEL,
            max_tokens=1000,
            temperature=0.7,
            top_p=1,
            stream=False
        )
        
        response_content = chat_completion.choices[0].message.content
        print(f"✅ API call successful, response length: {len(response_content)}")
        
        return response_content
    
    except Exception as e:
        print(f"❌ Groq API error: {e}")
        
        # Handle specific error types
        if "invalid_api_key" in str(e).lower():
            raise Exception("Invalid API key. Please check your GROQ_API_KEY.")
        elif "rate_limit" in str(e).lower():
            raise Exception("Rate limit exceeded. Please try again later.")
        elif "model_not_found" in str(e).lower():
            raise Exception(f"Model '{GROQ_MODEL}' not found. Please check available models.")
        elif "insufficient_quota" in str(e).lower():
            raise Exception("Insufficient quota. Please check your Groq account.")
        else:
            raise Exception(f"Groq API error: {str(e)}")

def get_available_models() -> List[str]:
    """Get list of available Groq models"""
    try:
        if not groq_client:
            return []
        
        models = groq_client.models.list()
        return [model.id for model in models.data if 'llama' in model.id.lower()]
    except Exception as e:
        print(f"Failed to fetch models: {e}")
        # Return known Llama models as fallback
        return [
            'llama-3.1-70b-versatile',
            'llama-3.1-8b-instant',
            'llama-3.2-90b-text-preview',
            'llama-3.2-11b-text-preview',
            'llama-3.2-3b-preview',
            'llama-3.2-1b-preview'
        ]

def send_contact_email(from_email: str, message: str, name: str | None = None):
    """Wrapper around send_email to send portfolio contact."""
    subject = "Portfolio contact from {}".format(name or from_email or "visitor")
    body = f"Message from {name or 'visitor'} (email: {from_email}):\n\n{message}"
    return send_email(subject, body, user_email=from_email)


def send_email(subject: str, body: str, user_email: str = None):
    """Send email notification to admin"""
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = ADMIN_EMAIL
        msg['Subject'] = subject
        
        # Add user email to body if provided
        if user_email:
            body = f"From: {user_email}\n\n{body}"
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_USER, ADMIN_EMAIL, text)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Email sending failed: {str(e)}")
        return False

def detect_contact_intent(message: str) -> bool:
    """Detect if user wants to contact the admin"""
    contact_keywords = [
        "contact you", "reach out", "send message", "talk to developer",
        "speak to admin", "feedback", "report issue", "suggestion",
        "contact admin", "message you", "get in touch", "talk to you",
        "want to tell you", "need to contact", "reach admin"
    ]
    
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in contact_keywords)

import re

def extract_contact_info(message: str) -> dict:
    """Extract basic contact info such as email and name from the message."""
    info = {}
    # Email regex
    email_match = re.search(r"[\w\.-]+@[\w\.-]+", message)
    if email_match:
        info["email"] = email_match.group(0)

    # Very naive name extraction – looks for patterns like "my name is X" or "I am X"
    name_match = re.search(r"(?:my name is|i am|this is)\s+([A-Za-z\s]{2,40})", message, re.IGNORECASE)
    if name_match:
        info["name"] = name_match.group(1).strip()
    return info


def extract_contact_message(message: str) -> str:
    """Extract the actual message user wants to send"""
    # Simple extraction - in production, you might want more sophisticated parsing
    contact_indicators = ["tell you", "message:", "say:", "feedback:", "report:", "contact you about"]
    
    for indicator in contact_indicators:
        if indicator in message.lower():
            parts = message.lower().split(indicator)
            if len(parts) > 1:
                return parts[1].strip()
    
    return message

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        print(data)

        message=data.get("message")
        conversation_id=data.get("conversation_id")
        user_email=data.get("user_email")

        if not message:
            return jsonify(ChatResponse(
                response="",
                error="Message is required"
            ).to_dict()), 400
        
        
        chat_response = call_groq_api(message)
        

        # --- Persist conversation ----
        if not conversation_id:
            conversation_id = str(uuid.uuid4())

        # Initialise conversation list if new
        conv_history = conversations.setdefault(conversation_id, [])
        conv_history.append({"role": "user", "content": message})
        conv_history.append({"role": "assistant", "content": chat_response})

        # Store some lightweight metadata (timestamp of last activity)
        conversation_metadata[conversation_id] = {
            "updated_at": datetime.now()
        }

        # Handle contact intent – ensure we have enough info before sending email
        if detect_contact_intent(message):
            contact_info = extract_contact_info(message)
            contact_message = extract_contact_message(message)
            visitor_email = contact_info.get("email") or user_email
            visitor_name = contact_info.get("name")

            if not visitor_email:
                chat_response = (
                    "I'd be happy to pass your message along to Abu Sayed. "
                    "Could you please provide your email address or other info so he can get back to you?"
                )
            else:
                send_contact_email(visitor_email, contact_message, name=visitor_name)
                chat_response += (
                    "\n\nYour message has been sent to Abu Sayed. "
                    "Thank you for reaching out - he will respond as soon as possible."
                )

        return jsonify(ChatResponse(
            response=chat_response ,
            conversation_id=conversation_id
        ).to_dict())
    except Exception as e:
        print(f"Chat endpoint error: {str(e)}")
        return jsonify(ChatResponse(
            response="",
            error=f"An error occurred: {str(e)}"
        ).to_dict()), 500

@app.route('/api/conversation/<conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    """Get conversation history"""
    try:
        if conversation_id not in conversations:
            return jsonify({'error': 'Conversation not found'}), 404
        
        return jsonify({
            'conversation_id': conversation_id,
            'messages': conversations[conversation_id],
            'metadata': conversation_metadata.get(conversation_id, {})
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/conversation/<conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    """Delete a conversation"""
    try:
        if conversation_id in conversations:
            del conversations[conversation_id]
        if conversation_id in conversation_metadata:
            del conversation_metadata[conversation_id]
        
        return jsonify({'message': 'Conversation deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/conversations', methods=['GET'])
def format_conversation_snapshot(conv_id: str) -> str:
    """Return a plain-text snapshot of the full conversation."""
    messages = conversations.get(conv_id, [])
    lines = [f"Conversation ID: {conv_id}", "="*40]
    for idx, msg in enumerate(messages, 1):
        role = msg.get("role", "unknown").title()
        content = msg.get("content", "")
        lines.append(f"{idx}. [{role}] {content}")
    return "\n".join(lines)


@app.route('/api/end-conversation', methods=['POST'])
def end_conversation():
    """Mark a conversation as finished and email snapshot to admin."""
    try:
        print("End conversation endpoint called")
        data = request.get_json()
        conv_id = data.get("conversation_id")
        visitor_email = data.get("user_email")
        print(conv_id, visitor_email)

        if not conv_id or conv_id not in conversations:
            return jsonify({"error": "Conversation not found"}), 404

        snapshot_text = format_conversation_snapshot(conv_id)
        send_email(
            subject=f"Conversation snapshot {conv_id}",
            body=snapshot_text,
            user_email=visitor_email,
        )
        # Optionally mark as archived/finished
        conversation_metadata.setdefault(conv_id, {})["ended_at"] = datetime.now()

        return jsonify({"status": "snapshot_sent"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def list_conversations():
    """List all conversations"""
    try:
        result = []
        for conv_id, messages in conversations.items():
            last_message = messages[-1] if messages else None
            result.append({
                'conversation_id': conv_id,
                'message_count': len(messages),
                'last_message': last_message,
                'metadata': conversation_metadata.get(conv_id, {})
            })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'model': GROQ_MODEL,
        'groq_client_ready': groq_client is not None
    })

@app.route('/api/test-api', methods=['GET'])
def test_api():
    """Test Groq API connection"""
    try:
        test_messages = [
            {'role': 'user', 'content': 'Hello, can you respond with just "API test successful"?'}
        ]
        
        response = call_groq_api(test_messages)
        
        return jsonify({
            'status': 'success',
            'response': response,
            'model': GROQ_MODEL
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/models', methods=['POST'])
def list_models():
    """List available Groq models"""
    try:
        available_models = get_available_models()
        
        return jsonify({
            'current_model': GROQ_MODEL,
            'available_models': available_models,
            'llama_models': [model for model in available_models if 'llama' in model.lower()],
            'note': 'Update GROQ_MODEL to llama-4 when available'
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'current_model': GROQ_MODEL
        }), 500

@app.route('/api/switch-model', methods=['POST'])
def switch_model():
    """Switch to a different model (for testing)"""
    try:
        data = request.get_json()
        new_model = data.get('model')
        
        if not new_model:
            return jsonify({'error': 'Model name is required'}), 400
        
        # Test the new model
        test_messages = [{'role': 'user', 'content': 'Hello'}]
        
        # Temporarily switch model for testing
        global GROQ_MODEL
        old_model = GROQ_MODEL
        GROQ_MODEL = new_model
        
        try:
            response = call_groq_api(test_messages)
            return jsonify({
                'status': 'success',
                'message': f'Successfully switched to {new_model}',
                'test_response': response,
                'old_model': old_model,
                'new_model': new_model
            })
        except Exception as e:
            # Revert back to old model if test fails
            GROQ_MODEL = old_model
            return jsonify({
                'status': 'error',
                'error': f'Failed to switch to {new_model}: {str(e)}',
                'current_model': GROQ_MODEL
            }), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Print configuration info
    print("=" * 60)
    print("Flask LLM Chat App Configuration (Groq Python Library)")
    print("=" * 60)
    print(f"Groq Model: {GROQ_MODEL}")
    print(f"Email Host: {EMAIL_HOST}")
    print(f"Admin Email: {ADMIN_EMAIL}")
    print(f"Groq Client Ready: {groq_client is not None}")
    print("=" * 60)
    print("Required Environment Variables:")
    print("- GROQ_API_KEY: Your Groq API key (get from https://console.groq.com/keys)")
    print("- EMAIL_USER: Email address for sending notifications")
    print("- EMAIL_PASSWORD: App password for email")
    print("- ADMIN_EMAIL: Email address to receive notifications")
    print("=" * 60)
    print("Optional Environment Variables:")
    print("- GROQ_MODEL: Model to use (default: llama-3.1-70b-versatile)")
    print("  * Change to 'llama-4' when available")
    print("  * Available: llama-3.1-70b-versatile, llama-3.1-8b-instant, etc.")
    print("=" * 60)
    
    # Test API connection on startup
    if groq_client:
        try:
            test_messages = [{'role': 'user', 'content': 'Hello'}]
            response = call_groq_api(test_messages)
            print("✅ Groq API connection successful!")
            print(f"Test response: {response[:100]}...")
        except Exception as e:
            print(f"❌ Groq API connection failed: {e}")
            print("Please check your API key and configuration.")
            print("Get your API key from: https://console.groq.com/keys")
    else:
        print("❌ Groq client not initialized. Please check your API key.")
    
    # Show available models
    try:
        models = get_available_models()
        print(f"Available Llama models: {models}")
    except Exception as e:
        print(f"Could not fetch models: {e}")
    
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)