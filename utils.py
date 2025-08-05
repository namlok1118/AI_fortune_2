import os
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, trim_messages
from typing_extensions import Annotated, TypedDict
from typing import Sequence
from langgraph.graph.message import add_messages
from langgraph.graph import START, MessagesState, StateGraph


os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_API_KEY"] = "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"
os.environ["XAI_API_KEY"] = st.secrets["XAI_API_KEY"]

model = init_chat_model("grok-3-mini", model_provider="xai", tiktoken_model_name="gpt-3.5-turbo", temperature=0.7)

def read_file_as_string(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return content
    except FileNotFoundError:
        print(f"Error: The file at {file_path} was not found.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
def refine_question(question: str) -> str:
    refine_prompt = read_file_as_string("refine_prompt.txt")
    prompt_template = ChatPromptTemplate.from_messages(
        [
            (
                "system", refine_prompt,
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    trimmer = trim_messages(
        max_tokens=1000,
        strategy="last",
        token_counter=model,
        include_system=True,
        allow_partial=False,
    )
    workflow = StateGraph(state_schema=State)
    workflow.add_edge(START, "model")
    def call_model(state: State):
        trimmed_messages = trimmer.invoke(state["messages"])
        prompt = prompt_template.invoke({"messages": trimmed_messages})
        response = model.invoke(prompt)
        return {"messages": [response]}
    workflow.add_node("model", call_model)
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    config = {"configurable": {"thread_id": "trial_1"}}
    query = question
    input_messages = [HumanMessage(query)]
    output = app.invoke(
        {"messages": input_messages},
        config,
    )
    return output["messages"][-1].content