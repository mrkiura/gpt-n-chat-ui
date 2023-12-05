from openai import OpenAI
import streamlit as st

st.title("GPT-N CHAT UI")

client = OpenAI()

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-3.5-turbo"

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "How can I help, Your Techcellency?"},
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("What is up?"):
    if prompt == "clear":

        st.session_state.messages = [{"role": "assistant", "content": "How can I help, Your Techcellency?"}]
        for message in st.session_state.messages:
            with st.chat_message("assistant"):
                st.markdown(message["content"])
        st.rerun()
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            messages = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ]
            messages.append({"role": "system", "content": "When I ask for help, you will respond in a well formatted markdown document"})
            for response in client.chat.completions.create(
                model=st.session_state["openai_model"],
                messages=messages,
                stream=True,
            ):
                full_response += (response.choices[0].delta.content or "")
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})
