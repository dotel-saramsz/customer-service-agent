import streamlit as st

# from chat import get_chatbot_response, message_store
from assistant import create_thread, delete_thread, create_message, get_chatbot_response


def initialize_conversation():
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Create a thread in openai and get the thread_id
    if "thread_id" not in st.session_state:
        openai_thread_id = create_thread()
        st.session_state.thread_id = openai_thread_id


def reset_conversation():
    st.session_state.messages = []
    # message_store.reset()
    if "thread_id" in st.session_state:
        delete_thread(st.session_state.thread_id)
    openai_thread_id = create_thread()
    st.session_state.thread_id = openai_thread_id
    st.rerun()


def main():
    # Create two columns for the title and button
    col1, col2 = st.columns([3, 1])

    initialize_conversation()

    # Add the title to the left column
    with col1:
        st.title("Yeti AI")

    # Add the "New Conversation" button to the right column
    with col2:
        if st.button("Reset Conversation"):
            reset_conversation()

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input
    if prompt := st.chat_input("What is your question?"):
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Add user message to the openai thread
        create_message(st.session_state.thread_id, prompt)

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            assistant_response = get_chatbot_response(st.session_state.thread_id)

            # Simulate stream of response with milliseconds delay
            for chunk in assistant_response:
                full_response += chunk + " "
                # time.sleep(0.05)
                # Add a blinking cursor to simulate typing
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)

        # Add assistant response to chat history
        st.session_state.messages.append(
            {"role": "assistant", "content": full_response}
        )


if __name__ == "__main__":
    main()
