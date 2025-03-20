import os
import uuid
from typing import Annotated, TypedDict, Literal, Optional

from langchain_groq import ChatGroq
from langgraph.graph import MessagesState
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.tools import tool
from langgraph.managed import RemainingSteps
from langchain_core.messages import HumanMessage
import requests
from langgraph.types import Command


def trigger_jenkis(param: str):
    JENKINS_URL = "http://localhost:8080"
    JOB_NAME = "Test_AI_Agent"
    API_TOKEN = "1179c4a777d7cebd76fe4ea4e576c73514"
    USERNAME = "inviul"

    # Step 1: Get the Crumb Token
    crumb_response = requests.get(
        f"{JENKINS_URL}/crumbIssuer/api/json",
        auth=(USERNAME, API_TOKEN)
    )
    crumb_data = crumb_response.json()
    crumb = crumb_data["crumb"]

    # Step 2: Trigger the Job
    headers = {"Jenkins-Crumb": crumb, "Content-Type": "application/x-www-form-urlencoded"}
    params = {"MY_PARAM": param}
    trigger_url = f"{JENKINS_URL}/job/{JOB_NAME}/buildWithParameters?token=1179c4a777d7cebd76fe4ea4e576c73514"

    response = requests.post(trigger_url, headers=headers, data=params, auth=(USERNAME, API_TOKEN))

    if response.status_code == 201:
        print("Jenkins job triggered successfully!")
    else:
        print(f"Failed to trigger job: {response.status_code}, {response.text}")

    return str(response.status_code)


# Create the LLM
GROQ_API_KEY = "enter_your_token"
llm = ChatGroq(model="llama3-8b-8192", groq_api_key=GROQ_API_KEY)

# Define the tools
@tool
def deployment_tool(query:str):
    """A tool to call an LLM model to search for a query"""
    try:
        result = trigger_jenkis(query)
    except BaseException as e:
        return f"Failed to execute. Error: {repr(e)}"
    return result

@tool
def monitoring_tool(query:str):
    """A tool to call an LLM model to search for a query"""
    try:
        result = trigger_jenkis(query)
    except BaseException as e:
        return f"Failed to execute. Error: {repr(e)}"
    return result

@tool
def troubleshooting_tool(query:str):
    """A tool to call an LLM model to search for a query"""
    try:
        result = trigger_jenkis(query)
    except BaseException as e:
        return f"Failed to execute. Error: {repr(e)}"
    return result

@tool
def security_tool(query:str):
    """A tool to call an LLM model to search for a query"""
    try:
        result = trigger_jenkis(query)
    except BaseException as e:
        return f"Failed to execute. Error: {repr(e)}"
    return result



# The agent state is the input to each node in the graph
class AgentState(MessagesState):
    # The 'next' field indicates where to route to next
    next: str
    last_worker: str = ""
    loop_count: int = 0
    is_last_step: Optional[bool] = False
    remaining_steps: Optional[RemainingSteps] = 0

# Member agent names
members = ["deployment", "troubleshoot", "security", "monitoring"]

# Our team supervisor is an LLM node. It just picks the next agent to process and decides when the work is completed
options = members + ["FINISH"]

system_prompt = (
    f"""You are a supervisor tasked with managing a conversation between the following workers: {members}. 
    Given the following user request, respond with the worker to act next. 
    Each worker will perform a task and respond with their results and status. When finished, respond with FINISH. 
    If user mentions about deployment then route to deployment member, 
    if user mentions about security then route to security member,
    if user mentions about monitoring then route to monitoring member,
    if user mentions about troubleshooting then route to troubleshoot member."""
)

class SupervisorState(TypedDict):
    """Worker to route to next. If no workers needed, route to FINISH."""
    next: Literal[*options]

# Nodes
def supervisor_node(state: AgentState) -> Command[Literal[*members, "__end__"]]:
    print("----------------- SUPERVISOR NODE START -----------------\n")
    messages = [
        {"role": "system", "content": system_prompt},
    ] + state["messages"]
    response = llm.with_structured_output(SupervisorState).invoke(messages)
    next_ = response["next"]

    last_worker = state.get("last_worker", None)
    loop_count = state.get("loop_count", 0)

    if next_ == last_worker:
        if loop_count >= 1:
            return Command(goto="__end__")
        else:
            loop_count +=1

    if next_ == "FINISH":
        next_ = END

    print(f"Routing to {next_}")
    print("----------------- SUPERVISOR NODE END -----------------\n")
    return Command(goto=next_,
                   update={"loop_count":loop_count, "last_worker": last_worker})


def deployment_node(state: AgentState) -> AgentState:
    result = deployment_tool.invoke({"query": "Query from deployment agent"})
    return Command(goto="supervisor", update={"messages": [HumanMessage(content=result, name="troubleshoot")], "loop_count":1, "last_worker":"deployment"})

def troubleshoot_node(state: AgentState) -> AgentState:
    result = deployment_tool.invoke({"query": "Query from troubleshoot agent"})
    return Command(goto="supervisor", update={"messages": [HumanMessage(content=result, name="troubleshoot")], "loop_count":1, "last_worker":"troubleshoot"})

def security_node(state: AgentState) -> AgentState:
    result = deployment_tool.invoke({"query": "Query from security agent"})
    return Command(goto="supervisor", update={"messages": [HumanMessage(content=result, name="troubleshoot")], "loop_count":1, "last_worker":"security"})

def monitoring_node(state: AgentState) -> AgentState:
    result = deployment_tool.invoke({"query": "Query from monitoring agent"})
    return Command(goto="supervisor", update={"messages": [HumanMessage(content=result, name="troubleshoot")], "loop_count":1, "last_worker":"monitoring"})


builder = StateGraph(AgentState)
builder.add_node("supervisor", supervisor_node)
builder.add_edge(START, "supervisor")
builder.add_node("deployment", deployment_node)
builder.add_node("troubleshoot", troubleshoot_node)
builder.add_node("security", security_node)
builder.add_node("monitoring", monitoring_node)

memory = MemorySaver()

# Compile the graph
graph = builder.compile(checkpointer=memory)


# def main_loop():
#     # Run the chatbot
#     while True:
#         user_input = input(">> ")
#         if user_input.lower() in ["quit", "exit", "q"]:
#             print("Goodbye!")
#             break
#
#         for s in graph.stream(
#             {
#                 "messages": [
#                     (
#                         "user", user_input
#                     )
#                 ]
#             },
#             config=config,
#         ):
#             print(s)
#             print("----")
import streamlit as st

# Assuming `graph` and `config` are defined elsewhere in your code
# graph = ...
# config = ...

def main_loop():
    st.title("ChatOps: Demo by Avinash Kumar")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user input
    if user_input := st.chat_input("Enter your query."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)

        config = {"configurable": {"thread_id": str(uuid.uuid1())}}
        print(config)

        # Stream the chatbot's response
        with st.chat_message("assistant"):
            response_placeholder = st.empty()  # Placeholder for assistant response

            for s in graph.stream(
                    {
                        "loop_count": 0,
                        "messages": [("user", user_input)]
                    },
                    config=config,
            ):
                print(s)

                # Instantly update UI based on value type
                if isinstance(s, dict):
                    response_placeholder.json(s)  # Show structured JSON output
                    st.session_state.messages.append({"role": "assistant", "content": str(s)})
                elif isinstance(s, str):
                    response_placeholder.markdown(s)  # Show string response
                    st.session_state.messages.append({"role": "assistant", "content": s})
                else:
                    response_placeholder.markdown(str(s))  # Show any other response format
                    st.session_state.messages.append({"role": "assistant", "content": str(s)})

# Run the main loop
if __name__ == "__main__":
    # Draw the graph
    try:
        graph.get_graph(xray=True).draw_mermaid_png(output_file_path="graph.png")
    except Exception:
        pass
    main_loop()