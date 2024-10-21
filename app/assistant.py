from typing import Literal
from hooks.oai_hook import oai_client
from tools.definitions import tools_specs
from tools.action_server import execute_tool_function
from openai.types.beta import AssistantStreamEvent
from openai.types.beta.threads.run import Run

CUSTOMER_SERVICE_ASSISTANT_ID = "asst_j0DFtTHWX9lD4FWTxAURJNwp"

SYSTEM_PROMPT = """
You are a customer service chatbot. Your job is to respond to customer queries and help them resolve their issues. You have access to different tools which allow you to
fetch relevant content or perform necessary actions to assist the customer. You can use the tools:
- get_order_details to fetch the details of an order
- raise_support_ticket to raise and escalate an issue to the support team if you are unable to resolve it.
- issue_refund to initiate a refund for an order if the order is refundable
If you need some additional info from the user before performing action, ask the user first. Once you perform some action using the tools, you should inform the customer and continue the conversation further.
You should be polite, helpful, and succinct in your responses. Do not give more information that what has been asekd to you.
If you don't know the answer to any query, you can reply that you don't know and offer to escalate the issue to support.
"""


def create_thread():
    thread = oai_client.beta.threads.create()
    print(f"Created a new thread with ID: {thread.id}")
    return thread.id


def delete_thread(thread_id: str):
    oai_client.beta.threads.delete(thread_id)
    print(f"Deleted the thread with ID: {thread_id}")


def create_message(
    thread_id: str, content: str, role: Literal["user"] | Literal["assistant"] = "user"
):
    message = oai_client.beta.threads.messages.create(
        thread_id=thread_id, content=content, role=role
    )
    print(f"Created message from [{role}]")
    return message


def handle_tool_execution(run_event_data: Run):
    if not run_event_data.required_action:
        return

    tool_calls = run_event_data.required_action.submit_tool_outputs.tool_calls
    print(">> Calling tools...")
    print(tool_calls)

    tool_outputs = []

    for tool_call in tool_calls:
        function_name = tool_call.function.name
        function_args = tool_call.function.arguments
        tool_response = execute_tool_function(function_name, function_args)
        tool_outputs.append({"tool_call_id": tool_call.id, "output": tool_response})

    # Submit the tool outputs to the assistant
    stream = oai_client.beta.threads.runs.submit_tool_outputs(
        thread_id=run_event_data.thread_id,
        run_id=run_event_data.id,
        tool_outputs=tool_outputs,
        stream=True,
    )

    for run_event in stream:
        yield from handle_run_event(run_event)


def handle_run_event(event: AssistantStreamEvent):
    if event.event == "thread.message.created":
        print(f"Received run event: {event.event}")
    elif event.event == "thread.message.delta":
        # print(f"Received run event: {event.event}")
        deltas = event.data.delta.content
        for delta in deltas or []:
            if delta.type == "text" and delta.text and delta.text.value:
                message = delta.text.value
                yield message
    elif event.event == "thread.message.completed":
        print(f"Received run event: {event.event}")
    elif event.event == "thread.run.requires_action":
        # This means that the assistant is requesting a tool call.
        yield from handle_tool_execution(event.data)
        pass

    pass


def get_chatbot_response(thread_id: str):
    # Choose the assistant to run the thread with
    assistant_id = CUSTOMER_SERVICE_ASSISTANT_ID

    stream = oai_client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id,
        model="gpt-4o-mini",
        instructions=SYSTEM_PROMPT,
        tools=tools_specs,
        stream=True,
    )

    for run_event in stream:
        yield from handle_run_event(run_event)
