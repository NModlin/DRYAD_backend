"""
Helper script for setting up Microsoft Teams webhook
"""

import sys
import os
import httpx
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_webhook(webhook_url: str) -> bool:
    """
    Test if webhook URL is valid.
    
    Args:
        webhook_url: Teams webhook URL
    
    Returns:
        True if valid, False otherwise
    """
    try:
        # Send test message
        test_card = {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": {
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "type": "AdaptiveCard",
                        "version": "1.4",
                        "body": [
                            {
                                "type": "TextBlock",
                                "text": "✅ DRYAD.AI Self-Healing System",
                                "weight": "bolder",
                                "size": "large",
                                "color": "good"
                            },
                            {
                                "type": "TextBlock",
                                "text": "Webhook connection test successful!",
                                "wrap": True
                            },
                            {
                                "type": "TextBlock",
                                "text": "Your self-healing system is ready to send notifications.",
                                "wrap": True,
                                "isSubtle": True
                            }
                        ]
                    }
                }
            ]
        }
        
        response = httpx.post(
            webhook_url,
            json=test_card,
            headers={"Content-Type": "application/json"},
            timeout=10.0
        )
        
        if response.status_code == 200:
            print("✅ Webhook test successful!")
            print("   Check your Teams channel for the test message.")
            return True
        else:
            print(f"❌ Webhook test failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    
    except Exception as e:
        print(f"❌ Error testing webhook: {e}")
        return False


def update_env_file(webhook_url: str, callback_url: str = None):
    """
    Update .env file with webhook URL.
    
    Args:
        webhook_url: Teams webhook URL
        callback_url: Public callback URL (optional)
    """
    try:
        env_path = Path(".env")
        
        if not env_path.exists():
            print("❌ .env file not found")
            return False
        
        # Read current content
        with open(env_path, 'r') as f:
            lines = f.readlines()
        
        # Update or add webhook URL
        webhook_found = False
        callback_found = False
        
        for i, line in enumerate(lines):
            if line.startswith("TEAMS_WEBHOOK_URL="):
                lines[i] = f'TEAMS_WEBHOOK_URL="{webhook_url}"\n'
                webhook_found = True
            elif callback_url and line.startswith("PUBLIC_CALLBACK_URL="):
                lines[i] = f'PUBLIC_CALLBACK_URL="{callback_url}"\n'
                callback_found = True
        
        # Add if not found
        if not webhook_found:
            lines.append(f'\nTEAMS_WEBHOOK_URL="{webhook_url}"\n')
        
        if callback_url and not callback_found:
            lines.append(f'PUBLIC_CALLBACK_URL="{callback_url}"\n')
        
        # Write back
        with open(env_path, 'w') as f:
            f.writelines(lines)
        
        print("✅ .env file updated successfully")
        return True
    
    except Exception as e:
        print(f"❌ Error updating .env file: {e}")
        return False


def setup_ngrok():
    """Guide user through ngrok setup."""
    print("\n📡 Setting up ngrok for public callback URL")
    print("=" * 60)
    print("\nngrok provides a public URL for your local backend,")
    print("allowing Teams to send callbacks for approve/reject actions.")
    print("\nSteps:")
    print("1. Download ngrok from: https://ngrok.com/download")
    print("2. Extract and run: ngrok http 8000")
    print("3. Copy the HTTPS URL (e.g., https://abc123.ngrok.io)")
    print("4. Paste it below")
    print("\nNote: The ngrok URL changes each time you restart it.")
    print("For production, use your actual domain.")
    
    ngrok_url = input("\nEnter ngrok HTTPS URL (or press Enter to skip): ").strip()
    
    if ngrok_url:
        if not ngrok_url.startswith("https://"):
            print("⚠️  Warning: URL should start with https://")
            ngrok_url = "https://" + ngrok_url.replace("http://", "")
        
        return ngrok_url
    
    return None


def main():
    """Main entry point."""
    print("\n🔧 DRYAD.AI Self-Healing - Teams Webhook Setup")
    print("=" * 60)
    
    # Check if already configured
    current_webhook = os.getenv("TEAMS_WEBHOOK_URL", "")
    current_callback = os.getenv("PUBLIC_CALLBACK_URL", "")
    
    if current_webhook:
        print(f"\n📋 Current webhook URL: {current_webhook[:50]}...")
        reconfigure = input("Reconfigure? (y/n): ").strip().lower()
        if reconfigure != 'y':
            print("Keeping current configuration.")
            return
    
    # Get webhook URL
    print("\n📝 Step 1: Get Teams Webhook URL")
    print("-" * 60)
    print("1. Open your Teams channel (e.g., #gremlins-monitoring)")
    print("2. Click '...' → 'Connectors'")
    print("3. Search for 'Incoming Webhook'")
    print("4. Click 'Configure'")
    print("5. Name it 'DRYAD.AI Self-Healing'")
    print("6. Copy the webhook URL")
    
    webhook_url = input("\nPaste webhook URL: ").strip()
    
    if not webhook_url:
        print("❌ No webhook URL provided. Exiting.")
        return
    
    if not webhook_url.startswith("https://"):
        print("❌ Invalid webhook URL. Must start with https://")
        return
    
    # Test webhook
    print("\n🧪 Testing webhook connection...")
    if not test_webhook(webhook_url):
        print("\n⚠️  Webhook test failed. Continue anyway? (y/n): ", end="")
        if input().strip().lower() != 'y':
            return
    
    # Get callback URL
    print("\n📝 Step 2: Setup Public Callback URL")
    print("-" * 60)
    
    if current_callback and current_callback != "http://localhost:8000":
        print(f"Current callback URL: {current_callback}")
        use_current = input("Use current URL? (y/n): ").strip().lower()
        if use_current == 'y':
            callback_url = current_callback
        else:
            callback_url = setup_ngrok()
    else:
        callback_url = setup_ngrok()
    
    # Update .env file
    print("\n💾 Updating .env file...")
    if update_env_file(webhook_url, callback_url):
        print("\n✅ Setup complete!")
        print("\n📋 Configuration:")
        print(f"   Webhook URL: {webhook_url[:50]}...")
        if callback_url:
            print(f"   Callback URL: {callback_url}")
        
        print("\n🚀 Next steps:")
        print("1. Enable self-healing in .env:")
        print("   ENABLE_SELF_HEALING=\"true\"")
        print("\n2. Start the backend:")
        print("   python start.py basic")
        print("\n3. Test the system:")
        print("   python scripts/test_self_healing.py inject-error")
        print("\n4. Check Teams for notification!")
    else:
        print("\n❌ Setup failed. Please check the errors above.")


if __name__ == "__main__":
    main()

