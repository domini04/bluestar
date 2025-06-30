"""
Specific Example: How Mock replaces ChatOpenAI in your actual LLM code

This demonstrates the exact mechanism used in your test suite.
"""

from unittest.mock import Mock, patch
from langchain_core.messages import HumanMessage

# Let's simulate your actual LLM code
class LLMClient:
    """Simplified version of your LLMClient"""
    
    def __init__(self):
        self.provider = "openai"
        self.model = "gpt-4.1-2025-04-14"
        self.api_key = "test_key"
    
    def get_client(self):
        """This would normally import and create real ChatOpenAI"""
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=self.model,
            api_key=self.api_key,
            temperature=0.7
        )
    
    def test_connection(self):
        """Test method that uses the client"""
        client = self.get_client()
        response = client.invoke([
            HumanMessage(content="Say 'Hello from BlueStar'")
        ])
        return "Hello from BlueStar" in response.content

print("=" * 60)
print("HOW MOCK REPLACES ChatOpenAI IN YOUR ACTUAL CODE")
print("=" * 60)

# =============================================================================
# PART 1: WITHOUT MOCK (This would fail if langchain_openai isn't installed)
# =============================================================================

print("\n1. WITHOUT MOCK - What normally happens:")
print("-" * 50)

try:
    llm = LLMClient()
    print("✗ This would normally try to create a real ChatOpenAI client")
    print("✗ It would need real API keys and internet connection")
    print("✗ Tests would be slow and unreliable")
except Exception as e:
    print(f"✗ Real code might fail: {e}")

# =============================================================================
# PART 2: WITH MOCK - How your tests work
# =============================================================================

print("\n2. WITH MOCK - How your tests work:")
print("-" * 50)

# Step 1: Create a mock that behaves like ChatOpenAI
mock_chatgpt_client = Mock()

# Step 2: Configure the mock to return what we expect
class MockResponse:
    def __init__(self, content):
        self.content = content

mock_chatgpt_client.invoke.return_value = MockResponse("Hello from BlueStar")

# Step 3: Use patch to replace the real ChatOpenAI with our mock
with patch('langchain_openai.ChatOpenAI', return_value=mock_chatgpt_client):
    print("✓ Inside patch context - ChatOpenAI is now our mock")
    
    # Now when LLMClient creates a "ChatOpenAI", it gets our mock instead
    llm = LLMClient()
    result = llm.test_connection()
    
    print(f"✓ Test connection result: {result}")
    print(f"✓ Mock was called: {mock_chatgpt_client.invoke.called}")
    print(f"✓ Mock call args: {mock_chatgpt_client.invoke.call_args}")

print("✓ Outside patch context - ChatOpenAI is back to normal")

# =============================================================================
# PART 3: DETAILED BREAKDOWN - What happens step by step
# =============================================================================

print("\n3. STEP-BY-STEP BREAKDOWN:")
print("-" * 50)

print("""
Here's exactly what happens when your test runs:

1. BEFORE PATCH:
   - Your code: from langchain_openai import ChatOpenAI
   - Python imports the REAL ChatOpenAI class

2. DURING PATCH:
   - patch('langchain_openai.ChatOpenAI', return_value=mock_client)
   - Python REPLACES ChatOpenAI with a function that returns your mock
   - Your code: ChatOpenAI(model="gpt-4", api_key="test")
   - Instead of real ChatOpenAI, you get: mock_client

3. YOUR CODE EXECUTES:
   - client = ChatOpenAI(...)  # Returns mock_client
   - response = client.invoke(...)  # Calls mock_client.invoke()
   - mock returns: MockResponse("Hello from BlueStar")

4. AFTER PATCH:
   - ChatOpenAI is restored to the real class
   - No side effects remain
""")

# =============================================================================
# PART 4: Why the path matters for patch()
# =============================================================================

print("\n4. WHY PATCH NEEDS THE CORRECT PATH:")
print("-" * 50)

print("""
patch('langchain_openai.ChatOpenAI') tells patch:
"Find the module 'langchain_openai', find the object 'ChatOpenAI' in it,
and replace it with my mock"

In your tests, you use:
patch('src.bluestar.core.llm.ChatOpenAI')

This means: "In the module src.bluestar.core.llm, replace ChatOpenAI"

This works because your llm.py has:
from langchain_openai import ChatOpenAI

So patch replaces the ChatOpenAI that your llm.py imported.
""")

# =============================================================================
# PART 5: Advanced Mock configurations
# =============================================================================

print("\n5. ADVANCED MOCK CONFIGURATIONS:")
print("-" * 50)

# Mock that behaves differently based on input
smart_mock = Mock()

def smart_response(messages):
    message_text = str(messages).lower()
    if "hello" in message_text:
        return MockResponse("Hello from BlueStar")
    elif "error" in message_text:
        raise Exception("Simulated API error")
    else:
        return MockResponse("Generic response")

smart_mock.invoke.side_effect = smart_response

# Test different scenarios
test_cases = [
    "Say hello",
    "Cause an error", 
    "Just normal text"
]

for test_input in test_cases:
    try:
        result = smart_mock.invoke(test_input)
        print(f"Input: '{test_input}' → Output: '{result.content}'")
    except Exception as e:
        print(f"Input: '{test_input}' → Error: {e}")

print("\n6. MOCK TRACKING - What makes it powerful for testing:")
print("-" * 50)

tracking_mock = Mock()
tracking_mock.invoke.return_value = MockResponse("Response")

# Simulate some calls
tracking_mock.invoke("First call")
tracking_mock.invoke("Second call", temperature=0.5)
tracking_mock.some_other_method("Different method")

print(f"Total method calls: {len(tracking_mock.method_calls)}")
print(f"invoke() called {tracking_mock.invoke.call_count} times")
print(f"All invoke() calls: {tracking_mock.invoke.call_args_list}")

# You can assert specific calls were made
print(f"Was invoke called with 'First call'? {('First call',) in [call.args for call in tracking_mock.invoke.call_args_list]}") 