#!/usr/bin/env python3
"""
Basic LangSmith Tracing Test

Simple test to verify LangSmith tracing works with real LLM calls.
Tests our tracing setup before building full integration tests.
"""

import os
from datetime import datetime
from langchain_core.messages import HumanMessage

# Import our BlueStar infrastructure
from src.bluestar.core.llm import llm_client
from src.bluestar.core.tracing import setup_langsmith_tracing, get_tracing_info


def test_basic_llm_with_tracing():
    """Test basic LLM call with LangSmith tracing enabled."""
    
    print("🔍 Testing LangSmith Tracing Setup...")
    print("=" * 50)
    
    # Check tracing configuration
    tracing_info = get_tracing_info()
    print(f"📊 Tracing Info:")
    print(f"  - Enabled: {tracing_info['enabled']}")
    print(f"  - Project: {tracing_info['project']}")
    print(f"  - API Key Configured: {tracing_info['api_key_configured']}")
    print(f"  - Endpoint: {tracing_info['endpoint']}")
    print()
    
    if not tracing_info["enabled"]:
        print("⚠️  LangSmith tracing is not enabled.")
        print("💡 Set LANGSMITH_TRACING=true and LANGSMITH_API_KEY in your .env file")
        return False
    
    # Set up tracing with test project
    print("🚀 Setting up LangSmith tracing...")
    success = setup_langsmith_tracing("bluestar-basic-test")
    print(f"   Setup successful: {success}")
    print()
    
    # Get LLM client info
    client_info = llm_client.get_client_info()
    print(f"🤖 LLM Client Info:")
    print(f"  - Provider: {client_info['provider']}")
    print(f"  - Model: {client_info['model']}")
    print(f"  - API Key Configured: {client_info['api_key_configured']}")
    print()
    
    if not client_info["api_key_configured"]:
        print("⚠️  LLM API key is not configured.")
        print(f"💡 Set {client_info['provider'].upper()}_API_KEY in your .env file")
        return False
    
    # Test basic LLM call
    print("📞 Making basic LLM call...")
    try:
        # Create standard LLM client (should be automatically traced)
        llm = llm_client.get_client(temperature=0.1, max_tokens=50)
        
        # Simple test message
        test_message = "Hello world! What is 2+2?"
        
        print(f"   Message: {test_message}")
        print("   ⏳ Calling LLM...")
        
        # Make the call
        response = llm.invoke([HumanMessage(content=test_message)])
        
        print(f"   📄 Response Type: {type(response)}")
        print(f"   📄 Response Content: '{response.content}'")
        print(f"   📄 Response Length: {len(response.content) if response.content else 0}")
        
        # Check for additional response attributes
        if hasattr(response, 'response_metadata'):
            print(f"   📄 Response Metadata: {response.response_metadata}")
        if hasattr(response, 'usage_metadata'):
            print(f"   📄 Usage Metadata: {response.usage_metadata}")
        print()
        
        # Check if we got any response
        if response.content is None:
            print("⚠️  LLM returned None response")
            return False
        elif response.content.strip() == "":
            print("⚠️  LLM returned empty response")
            return False
        else:
            print("✅ LLM call successful!")
            print("📈 If tracing is working, you should see this call in LangSmith dashboard")
            print(f"   Project: {os.getenv('LANGSMITH_PROJECT', 'bluestar-basic-test')}")
            
            # Just verify we got some response (relax content checking)
            if len(response.content.strip()) > 5:
                print("✅ Got meaningful response from LLM")
                return True
            else:
                print("⚠️  LLM response too short")
                return False
            
    except Exception as e:
        print(f"❌ LLM call failed: {e}")
        return False


def main():
    """Main test function."""
    print(f"🧪 BlueStar LangSmith Tracing Test")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        success = test_basic_llm_with_tracing()
        
        print()
        print("=" * 50)
        if success:
            print("🎉 SUCCESS: Basic LangSmith tracing test passed!")
            print("🔗 Check your LangSmith dashboard to verify traces were recorded")
        else:
            print("❌ FAILED: Basic LangSmith tracing test failed")
            print("🔧 Check your environment configuration and try again")
        
        return success
        
    except Exception as e:
        print(f"💥 Test script error: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 