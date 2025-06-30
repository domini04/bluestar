"""
Demonstration: How unittest.mock.Mock works to fake objects like ChatOpenAI

This file demonstrates the mechanics of how Mock fakes real objects.
"""

from unittest.mock import Mock, patch, MagicMock
import sys

print("=" * 60)
print("HOW MOCK FAKES ACTUAL OBJECTS - DETAILED EXPLANATION")
print("=" * 60)

# =============================================================================
# PART 1: How Mock Creates Fake Objects WITHOUT Needing Real Object Paths
# =============================================================================

print("\n1. MOCK DOESN'T NEED REAL OBJECT PATHS TO CREATE FAKES")
print("-" * 50)

# Mock is a "universal faker" - it can pretend to be ANY object
fake_chatgpt = Mock()

# Mock automatically creates ANY attribute or method you access
print(f"fake_chatgpt.invoke: {fake_chatgpt.invoke}")
print(f"fake_chatgpt.some_random_method: {fake_chatgpt.some_random_method}")
print(f"fake_chatgpt.anything.you.want.deeply.nested: {fake_chatgpt.anything.you.want.deeply.nested}")

# All of these return new Mock objects automatically!
print(f"Type of invoke: {type(fake_chatgpt.invoke)}")

print("\n2. HOW MOCK HANDLES METHOD CALLS")
print("-" * 50)

# When you call a method on Mock, it returns another Mock by default
result1 = fake_chatgpt.invoke("Hello")
result2 = fake_chatgpt.invoke("Different input")

print(f"First call result: {result1}")
print(f"Second call result: {result2}")
print(f"Are they the same? {result1 is result2}")  # No! Each call creates new Mock

# =============================================================================
# PART 2: CONFIGURING MOCK TO BEHAVE LIKE ChatOpenAI
# =============================================================================

print("\n3. CONFIGURING MOCK TO MIMIC ChatOpenAI BEHAVIOR")
print("-" * 50)

# Create a mock that behaves like ChatOpenAI
mock_chatgpt = Mock()

# Method 1: Set return_value for the method
mock_chatgpt.invoke.return_value.content = "Hello from BlueStar"

# Now when we call invoke(), it returns a mock with .content = "Hello from BlueStar"
response = mock_chatgpt.invoke("Any input")
print(f"Response content: {response.content}")

# Method 2: Create a more realistic response object
class MockResponse:
    def __init__(self, content):
        self.content = content

mock_chatgpt.invoke.return_value = MockResponse("Realistic response")
response2 = mock_chatgpt.invoke("Another input")
print(f"Realistic response: {response2.content}")

# Method 3: Using side_effect for dynamic behavior
def dynamic_response(messages):
    if "hello" in str(messages).lower():
        return MockResponse("Hi there!")
    else:
        return MockResponse("I don't understand")

mock_chatgpt.invoke.side_effect = dynamic_response

print(f"Hello response: {mock_chatgpt.invoke('Hello world').content}")
print(f"Other response: {mock_chatgpt.invoke('Calculate 2+2').content}")

# =============================================================================
# PART 3: HOW PATCH WORKS - REPLACING REAL IMPORTS
# =============================================================================

print("\n4. HOW PATCH REPLACES REAL OBJECT IMPORTS")
print("-" * 50)

# This is where the "path" comes in - patch needs to know WHERE to replace
# Let's simulate what happens in your tests

print("Before patch:")
print(f"What your code imports: {sys.modules.get('langchain_openai', 'Not imported yet')}")

# When you do: patch('src.bluestar.core.llm.ChatOpenAI')
# You're telling patch: "In the module src.bluestar.core.llm, 
# replace the ChatOpenAI object with my mock"

with patch('sys.path') as mock_syspath:  # Simple example
    print(f"During patch, sys.path is: {type(mock_syspath)}")
    print(f"It's a Mock pretending to be sys.path: {mock_syspath}")

print("After patch: sys.path is back to normal")

# =============================================================================
# PART 4: COMPLETE EXAMPLE LIKE YOUR TESTS
# =============================================================================

print("\n5. COMPLETE EXAMPLE: MOCKING ChatOpenAI IN YOUR TESTS")
print("-" * 50)

# This simulates your fixture pattern
def create_mock_chatgpt():
    """Simulate your mock_openai_client fixture"""
    mock = Mock()
    
    # Configure it to behave like ChatOpenAI
    mock.invoke.return_value.content = "Hello from BlueStar"
    
    # Add some tracking capabilities
    mock.model = "gpt-4.1-2025-04-14"
    mock.temperature = 0.7
    
    return mock

# Create the mock
mock_client = create_mock_chatgpt()

# Simulate using it in your code
print(f"Mock client model: {mock_client.model}")
response = mock_client.invoke("Test prompt")
print(f"Mock response: {response.content}")

# Check if it was called (this is what makes Mock powerful for testing)
print(f"Was invoke called? {mock_client.invoke.called}")
print(f"Call count: {mock_client.invoke.call_count}")
print(f"Called with: {mock_client.invoke.call_args}")

# =============================================================================
# PART 6: WHY YOUR CURRENT SETUP WORKS
# =============================================================================

print("\n6. HOW YOUR CURRENT TEST SETUP WORKS")
print("-" * 50)

print("""
In your conftest.py:

@pytest.fixture
def mock_openai_client():
    mock = Mock()
    mock.invoke.return_value.content = "Hello from BlueStar"
    return mock

@pytest.fixture  
def mock_all_langchain_clients(mock_openai_client, ...):
    with patch('src.bluestar.core.llm.ChatOpenAI', return_value=mock_openai_client):
        yield mock_openai_client

What happens:
1. Mock() creates a fake object that can pretend to be anything
2. You configure it to return specific values when methods are called
3. patch() replaces the real ChatOpenAI import with your mock
4. When your code does: ChatOpenAI(...), it gets your mock instead
5. When code calls client.invoke(), it gets your configured response

The magic is:
- Mock doesn't need to know about ChatOpenAI to fake it
- Mock creates attributes/methods on-demand
- patch() handles the "switching" of real object with fake
- You configure the Mock to return what you want for testing
""")

print("\n7. ADVANCED: Mock can even track complex interactions")
print("-" * 50)

advanced_mock = Mock()
advanced_mock.invoke.return_value.content = "Advanced response"

# Simulate multiple calls
advanced_mock.invoke("First call")
advanced_mock.invoke("Second call") 
advanced_mock.some_other_method("Different method")

print(f"All method calls made to this mock:")
for call in advanced_mock.method_calls:
    print(f"  {call}")

print(f"\nSpecifically invoke() calls:")
for call in advanced_mock.invoke.call_args_list:
    print(f"  invoke{call}") 