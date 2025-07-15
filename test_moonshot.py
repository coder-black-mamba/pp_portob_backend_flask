import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test configurations
CONFIGS = [
    {
        'name': 'Official Moonshot API',
        'base_url': 'https://api.moonshot.ai/v1',
        'model': 'moonshot-v1-8k'
    },
    {
        'name': 'Alternative Moonshot API',
        'base_url': 'https://api.moonshot.cn/v1',
        'model': 'moonshot-v1-8k'
    },
    {
        'name': 'Moonshot with different model',
        'base_url': 'https://api.moonshot.ai/v1',
        'model': 'moonshot-v1-32k'
    }
]

def test_api_config(config):
    """Test a specific API configuration"""
    api_key = os.getenv('MOONSHOT_API_KEY')
    
    if not api_key:
        print("❌ MOONSHOT_API_KEY not found in environment variables")
        return False
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'model': config['model'],
        'messages': [
            {'role': 'user', 'content': 'Hello, please respond with "API test successful"'}
        ],
        'max_tokens': 100,
        'temperature': 0.7
    }
    
    try:
        print(f"\n🔍 Testing {config['name']}...")
        print(f"   URL: {config['base_url']}/chat/completions")
        print(f"   Model: {config['model']}")
        print(f"   API Key: {api_key[:10]}...")
        
        response = requests.post(
            f"{config['base_url']}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            message = data['choices'][0]['message']['content']
            print(f"   ✅ Success: {message}")
            return True
        else:
            print(f"   ❌ Failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def main():
    print("=" * 60)
    print("🌙 Moonshot API Configuration Test")
    print("=" * 60)
    
    # Check if API key is provided
    api_key = os.getenv('MOONSHOT_API_KEY')
    if not api_key:
        print("❌ Please set MOONSHOT_API_KEY in your .env file")
        return
    
    print(f"API Key: {api_key[:10]}...")
    
    # Test different configurations
    successful_configs = []
    
    for config in CONFIGS:
        if test_api_config(config):
            successful_configs.append(config)
    
    print("\n" + "=" * 60)
    print("📊 Test Results")
    print("=" * 60)
    
    if successful_configs:
        print("✅ Working configurations:")
        for config in successful_configs:
            print(f"   - {config['name']}")
            print(f"     URL: {config['base_url']}")
            print(f"     Model: {config['model']}")
        
        print(f"\n🎯 Recommended configuration:")
        best_config = successful_configs[0]
        print(f"MOONSHOT_BASE_URL={best_config['base_url']}")
        print(f"MOONSHOT_MODEL={best_config['model']}")
        
    else:
        print("❌ No working configurations found")
        print("\n🔧 Troubleshooting steps:")
        print("1. Check if your API key is valid")
        print("2. Verify your account has API access")
        print("3. Check if your account has sufficient credits")
        print("4. Try a different model or endpoint")
        print("5. Contact Moonshot support if issues persist")

if __name__ == "__main__":
    main()