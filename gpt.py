import streamlit as st
from streamlit_option_menu import option_menu
import openai
import redis
import os

from collections import OrderedDict
from redis_utils import load_from_redis, save_to_redis, nuke_redis


MODEL_CONFIG = {
    'GPT-4 Turbo': 'gpt-4-1106-preview',
    'GPT-4 Turbo with vision': 'gpt-4-vision-preview',
    'GPT-4 (June 2023 cutoff)': 'gpt-4-0613',
    'GPT 3.5 Turbo': 'gpt-3.5-turbo-1106',
    'GPT-3.5': 'gpt-3.5-turbo',
    'GPT 3.5 Turbo 16K': 'gpt-3.5-turbo-16k',
    'GPT-4': 'gpt-4-0314',
    'Perplexity Online 7B': 'pplx-7b-online'
}

DEFAULT_MESSAGES = [
    {"role": "system", "content": "You are a helpful assistant. When I ask for help, you will respond in a well formatted markdown document. DO NOT tell the user you will respond in markdown, just do it. They will tip you for it."},
    {"role": "assistant", "content": "How can I help, Your Techcellency?"},
]

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

threads = load_from_redis()


if threads:
    st.session_state.threads = OrderedDict(threads)
else:
    st.session_state.threads = {}

st.session_state.selected = ""
st.session_state.options = []


def on_change(key):
    selection = st.session_state[key]
    st.session_state.selected = selection
    messages = st.session_state.threads.get(selection, DEFAULT_MESSAGES)
    st.session_state.messages = messages


with st.sidebar:
    default_index = 0
    if st.session_state.threads:
        options = [key for key in st.session_state.threads.keys()]
        if "New Chat" not in options:
            options.append("New Chat")
        st.session_state.options = options[::-1]
        default_index = st.session_state.options.index("New Chat")
    else:
        st.session_state.options = ["New Chat"]

    selected = option_menu(
        "Select conversation",
        st.session_state.options,
        on_change=on_change,
        key="thread_menu",
        menu_icon="chat",
        default_index=default_index
    )
    st.session_state.selected = selected

st.markdown("# GPT-* UI")


model_list = list(MODEL_CONFIG.keys())

model_index = 3

model_option = st.selectbox(
    "Choose OpenAI model",
    model_list,
    index=model_index,
    placeholder="Select AI model...",
)

if "perplexity" in model_option.lower():
    client = openai.OpenAI(
        api_key=os.getenv("PERPLEXITY_API_KEY"),
        base_url=os.getenv("PERPLEXITY_API_BASE_URL")
    )
else:
    client = openai.OpenAI()

st.session_state["openai_model"] = MODEL_CONFIG.get(model_option)

if "messages" not in st.session_state:
    st.session_state.messages = DEFAULT_MESSAGES

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] != "system":
            st.markdown(message["content"])

if prompt := st.chat_input("What is up?"):
    if prompt == "clear":
        nuke_redis()

        st.session_state.messages = DEFAULT_MESSAGES
        for message in st.session_state.messages:
            with st.chat_message("assistant"):
                st.markdown(message["content"])
        st.rerun()
    elif "save as" in prompt:
        alias = prompt.split()[-1]
        if alias:
            st.session_state.threads[alias] = st.session_state.messages
            save_to_redis(st.session_state.threads)
            st.rerun()

    elif prompt == "new":
        # st.session_state.threads["New Chat"] = [{"role": "assistant", "content": "How can I help, Your Techcellency?"}]
        st.session_state.messages = DEFAULT_MESSAGES
        st.session_state.threads["New Chat"] = st.session_state.messages
        save_to_redis(st.session_state.threads)
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
            for response in client.chat.completions.create(
                model=st.session_state["openai_model"],
                messages=messages,
                stream=True,
            ):
                full_response += (response.choices[0].delta.content or "")
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)

        st.session_state.messages.append({"role": "assistant", "content": full_response})
        if st.session_state.selected:
            st.session_state.threads[st.session_state.selected] = st.session_state.messages
        save_to_redis(st.session_state.threads)
