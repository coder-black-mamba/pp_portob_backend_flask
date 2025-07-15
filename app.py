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
CORS(app)

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

def call_groq_api(messages: List[Dict]) -> str:
    """Call Groq API using official Python library"""
    if not groq_client:
        raise Exception("Groq client not initialized. Please check your API key.")
    
    try:
        print(f"Making API request using Groq Python library")
        print(f"Using model: {GROQ_MODEL}")
        print(f"Message count: {len(messages)}")
        
        # Create chat completion using Groq client
        chat_completion = groq_client.chat.completions.create(
            messages=messages,
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
        
        if not data or 'message' not in data:
            return jsonify(ChatResponse(
                response="",
                error="Message is required"
            ).to_dict()), 400
        
        user_message = data['message']
        conversation_id = data.get('conversation_id')
        user_email = data.get('user_email')  # Optional user email
        
        # Create new conversation if not provided
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            conversations[conversation_id] = []
            conversation_metadata[conversation_id] = {
                'created_at': datetime.now().isoformat(),
                'user_email': user_email,
                'model': GROQ_MODEL
            }
        
        # Check if user wants to contact admin
        if detect_contact_intent(user_message):
            contact_message = extract_contact_message(user_message)
            
            # Send email to admin
            subject = f"User Contact Request - Conversation {conversation_id}"
            body = f"""
A user wants to contact you through the chat application.

Conversation ID: {conversation_id}
Model Used: {GROQ_MODEL}
Message: {contact_message}

Full conversation history:
{json.dumps(conversations.get(conversation_id, []), indent=2)}
            """
            
            email_sent = send_email(subject, body, user_email)
            
            if email_sent:
                response_msg = "Thank you for your message! I've forwarded it to the admin and they'll get back to you soon."
            else:
                response_msg = "I understand you want to contact the admin, but there was an issue sending your message. Please try again later."
            
            return jsonify(ChatResponse(
                response=response_msg,
                conversation_id=conversation_id
            ).to_dict())
        
        # Add user message to conversation
        conversations[conversation_id].append({
            'role': 'user',
            'content': user_message,
            'timestamp': datetime.now().isoformat()
        })
        
        # Prepare messages for API call
        messages = [
            {
                'role': 'system', 
                'content': f'You are a helpful AI assistant powered by {GROQ_MODEL}. You are fast, efficient, and knowledgeable. If a user wants to contact the developer or admin, let them know they can say something like "I want to contact you" or "send message to admin".'
            }
        ]
        
        # Add conversation history (limit to last 10 messages to avoid token limits)
        conversation_history = conversations[conversation_id][-10:]
        for msg in conversation_history:
            messages.append({
                'role': msg['role'],
                'content': msg['content']
            })
        
        # Make API call to Groq
        ai_response = call_groq_api(messages)
        
        # Add AI response to conversation
        conversations[conversation_id].append({
            'role': 'assistant',
            'content': ai_response,
            'timestamp': datetime.now().isoformat(),
            'model': GROQ_MODEL
        })
        
        return jsonify(ChatResponse(
            response=ai_response,
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

@app.route('/api/models', methods=['GET'])
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