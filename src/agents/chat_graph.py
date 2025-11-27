"""LangGraph with add_messages reducer - Chatbot"""

from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage
from src.utils.config import settings


# State with add_messages reducer
class ChatState(TypedDict):
    """
    Chat state with conversation history
    
    add_messages automatically:
    1. Appends new messages to the list
    2. Maintains conversation order
    3. Handles duplicates intelligently
    """
    messages: Annotated[list, add_messages]  # Magic annotation!


# Nodes
def chatbot_node(state: ChatState) -> dict:
    """
    Chatbot node: Responds to user message
    """
    # Get conversation history
    messages = state["messages"]
    
    print(f"💬 Received {len(messages)} messages in history")
    print(f"   Latest: {messages[-1].content}")
    
    # Initialize LLM
    llm = ChatGoogleGenerativeAI(
        model=settings.llm_model,
        google_api_key=settings.google_api_key,
        convert_system_message_to_human=True
    )
    
    # Get response
    response = llm.invoke(messages)
    
    print(f"🤖 Generated response: {response.content}")
    
    # add_messages automatically appends this to conversation!
    return {"messages": [response]}


# Create graph
def create_chatbot_graph():
    """Simple chatbot with memory"""
    
    workflow = StateGraph(ChatState)
    
    # Single node
    workflow.add_node("chatbot", chatbot_node)
    
    # Simple flow
    workflow.add_edge(START, "chatbot")
    workflow.add_edge("chatbot", END)
    
    return workflow.compile()


# Test function
def test_chatbot_graph():
    """Test multi-turn conversation"""
    
    print("\n" + "="*60)
    print("🧪 TESTING CHATBOT WITH add_messages")
    print("="*60 + "\n")
    
    app = create_chatbot_graph()
    
    # Turn 1
    print("--- Turn 1 ---")
    state1 = app.invoke({
        "messages": [HumanMessage(content="What is 2+2?")]
    })
    print(f"User: What is 2+2?")
    print(f"Bot: {state1['messages'][-1].content}\n")
    
    # Turn 2 - add_messages automatically maintains history!
    print("--- Turn 2 ---")
    state2 = app.invoke({
        "messages": state1["messages"] + [HumanMessage(content="What about 3+3?")]
    })
    print(f"User: What about 3+3?")
    print(f"Bot: {state2['messages'][-1].content}")
    print(f"\n📜 Total messages in history: {len(state2['messages'])}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    test_chatbot_graph()
