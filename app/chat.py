from openai import OpenAI
from config import openai_api_key, openai_org_id, openai_project_id
from tools.definitions import tools_specs
from app.tools.action_server import execute_tool_function

client = OpenAI(
    api_key=openai_api_key, organization=openai_org_id, project=openai_project_id
)

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

# SYSTEM_PROMPT = """
# You are a customer service chatbot. Your job is to respond to customer queries and help them resolve their issues. You should pretend that you have access to company's internal documentation
# and tools to assist the customer. You can ask for more info from the customer if needed. You should be polite, helpful, and informative in your responses.
# If you don't know the answer to any query, you can reply that you don't know and offer to escalate the issue to support.
# Make sure to generate your response in markdown format with proper formatting for bullet points whenever applicable.
# """


class LLMMessageStore:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMMessageStore, cls).__new__(cls)
            cls._instance.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        return cls._instance

    def add_message(
        self,
        role: str,
        content: str | None,
        tool_calls: list | None = None,
        tool_call_id=None,
    ):
        message = {"role": role}
        if content:
            message["content"] = content
        if tool_calls:
            message["tool_calls"] = tool_calls
        if tool_call_id:
            message["tool_call_id"] = tool_call_id
        self.messages.append(message)

        system, user, assistant, tool = 0, 0, 0, 0
        for message in self.messages:
            if message["role"] == "system":
                system += 1
            elif message["role"] == "user":
                user += 1
            elif message["role"] == "assistant":
                assistant += 1
            elif message["role"] == "tool":
                tool += 1
        print(
            f"[{role}] message || (Count: System: {system}| User: {user}| Assistant: {assistant}| Tool: {tool})"
        )

    def get_messages(self, last_n=20):
        # Get the last n messages from the chat history and prefix it with the system prompt message
        if len(self.messages) > last_n:
            last_nth_message = self.messages[-last_n]
            if last_nth_message.get("role") == "tool":
                return [self.messages[0], *self.messages[-(last_n + 1) :]]
            return [self.messages[0], *self.messages[-last_n:]]
        else:
            return self.messages

    def reset(self):
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]


message_store = LLMMessageStore()


def get_chatbot_response(user_message: str | None = None):

    if user_message:
        message_store.add_message("user", user_message)

    # Get the last 5 messages from the chat history
    conversation_messages = message_store.get_messages()

    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=conversation_messages,
        tools=tools_specs,
        stream=True,
    )

    response_text = ""
    tool_calls = []

    for chunk in stream:
        # Get the first choice
        msg = chunk.choices[0]

        # If there is still more content to be generated
        if delta := msg.delta:
            if delta.content:
                response_text += delta.content
                # Send to streamlit
                yield delta.content
            elif delta.tool_calls:
                tcchunklist = delta.tool_calls
                for tcchunk in tcchunklist:
                    if len(tool_calls) <= tcchunk.index:
                        tool_calls.append(
                            {
                                "id": "",
                                "type": "function",
                                "function": {"name": "", "arguments": ""},
                            }
                        )
                    tc = tool_calls[tcchunk.index]

                    if tcchunk.id:
                        tc["id"] += tcchunk.id
                    if tcchunk.function.name:
                        tc["function"]["name"] += tcchunk.function.name
                    if tcchunk.function.arguments:
                        tc["function"]["arguments"] += tcchunk.function.arguments

        # print(msg.delta)
        # print(msg.finish_reason)

        # If it's the end of the response and it's a text response, update the messages array with it
        if msg.finish_reason == "stop":
            message_store.add_message("assistant", response_text)
        # If it's the end of the response and it's a tool call, call the tools, update the messages array
        # and recursively call this function so GPT can respond to the function call output
        elif msg.finish_reason == "tool_calls":
            message_store.add_message("assistant", content=None, tool_calls=tool_calls)
            print(">> Calling tools...")
            print(tool_calls)
            # Call the tools
            for tool_call in tool_calls:
                tool_call_id = tool_call["id"]
                function_name = tool_call["function"]["name"]
                function_args = tool_call["function"].get("arguments")
                tool_response = execute_tool_function(function_name, function_args)

                message_store.add_message(
                    "tool", tool_response, tool_call_id=tool_call_id
                )

            yield from get_chatbot_response()
