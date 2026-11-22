import html
import json
import uuid
import streamlit as st
import streamlit.components.v1 as components
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage

from chatbot_backend import chatbot, get_all_threads, get_thread_title

st.set_page_config(
    page_title="Returns & Loss Assistant",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --- Session State Setup ---
if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"
if "chat_threads" not in st.session_state:
    st.session_state["chat_threads"] = get_all_threads()
if "thread_id" not in st.session_state:
    if st.session_state["chat_threads"]:
        st.session_state["thread_id"] = st.session_state["chat_threads"][0]
    else:
        tid = str(uuid.uuid4())
        st.session_state["thread_id"] = tid
        st.session_state["chat_threads"].insert(0, tid)
if "message_history" not in st.session_state:
    state = chatbot.get_state(
        config={"configurable": {"thread_id": st.session_state["thread_id"]}}
    )
    st.session_state["message_history"] = [
        {"role": "user" if isinstance(m, HumanMessage) else "assistant", "content": m.content}
        for m in state.values.get("messages", [])
        if isinstance(m, (HumanMessage, AIMessage))
    ]
if "edit_idx" not in st.session_state:
    st.session_state["edit_idx"] = None

# --- Theme Colors ---
is_dark = st.session_state["theme"] == "dark"
colors = {
    "bg": "#0D0F10" if is_dark else "#FFFFFF",
    "sidebar": "#14171A" if is_dark else "#F6F7F8",
    "surface": "#181B1F" if is_dark else "#F3F4F6",
    "table_header": "#161A1E" if is_dark else "#F3F4F6",
    "text": "#F5F5F5" if is_dark else "#111827",
    "muted": "#9CA3AF" if is_dark else "#6B7280",
    "border": "#262A2E" if is_dark else "#E5E7EB",
    "teal": "#0D9488",
    "teal_bright": "#14B8A6",
    "teal_hover": "#0F766E",
    "user_bubble": "#0F2D30" if is_dark else "#134E4A",
    "user_border": "#1B4D52" if is_dark else "#0F766E",
}

st.markdown(
    f"""
    <style>
        /* Hide Rerun, Print, Screen Record, Clear Cache, Deploy */
        #MainMenu,
        [data-testid="stMainMenu"],
        [data-testid="stToolbarActions"],
        [data-testid="stStatusWidget"],
        .stAppDeployButton,
        footer {{
            display: none !important;
        }}

        /* Always show sidebar close & open buttons */
        [data-testid="stSidebarCollapseButton"],
        [data-testid="stSidebarCollapseButton"] button,
        [data-testid="stExpandSidebarButton"],
        [data-testid="collapsedControl"] {{
            opacity: 1 !important;
            visibility: visible !important;
        }}
        [data-testid="stSidebarCollapseButton"] svg,
        [data-testid="stExpandSidebarButton"] svg {{
            color: {colors["text"]} !important;
            fill: {colors["text"]} !important;
        }}

        /* Page & Sidebar backgrounds */
        .stApp,
        [data-testid="stHeader"],
        [data-testid="stBottom"],
        [data-testid="stBottomBlockContainer"] {{
            background-color: {colors["bg"]} !important;
            color: {colors["text"]} !important;
        }}
        [data-testid="stSidebar"] {{
            background-color: {colors["sidebar"]} !important;
            border-right: 1px solid {colors["border"]} !important;
        }}

        /* Soft dividers in both themes */
        hr {{
            border-color: {colors["border"]} !important;
        }}

        /* Readable text everywhere (headings, lists, bold, tables, code) */
        .stApp p, .stApp li, .stApp h1, .stApp h2, .stApp h3, .stApp h4,
        .stApp label, .stApp strong, .stApp em, .stApp blockquote,
        [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {{
            color: {colors["text"]};
        }}
        .muted-text {{
            color: {colors["muted"]} !important;
            font-size: 0.9rem;
        }}

        /* Tables fix for Light & Dark theme */
        [data-testid="stChatMessage"] table {{
            width: 100%;
            border-collapse: collapse;
            margin: 0.6rem 0;
        }}
        [data-testid="stChatMessage"] th,
        [data-testid="stChatMessage"] td {{
            color: {colors["text"]} !important;
            border: 1px solid {colors["border"]} !important;
            padding: 0.55rem 0.75rem !important;
        }}
        [data-testid="stChatMessage"] th {{
            background-color: {colors["table_header"]} !important;
            font-weight: 600 !important;
        }}
        [data-testid="stChatMessage"] td {{
            background-color: {colors["bg"]} !important;
        }}
        [data-testid="stChatMessage"] code,
        [data-testid="stChatMessage"] pre {{
            background-color: {colors["surface"]} !important;
            color: {colors["text"]} !important;
            border: 1px solid {colors["border"]} !important;
        }}

        .block-container {{
            padding-top: 4.5rem;
            max-width: 860px;
        }}

        /* Main area buttons (Theme switch, Starter prompts, Edit buttons) */
        [data-testid="stMain"] button[kind="secondary"] {{
            background-color: {colors["surface"]} !important;
            border: 1px solid {colors["border"]} !important;
        }}
        [data-testid="stMain"] button[kind="secondary"]:hover {{
            border-color: {colors["teal"]} !important;
        }}
        [data-testid="stMain"] button[kind="secondary"] p,
        [data-testid="stMain"] button[kind="secondary"] span {{
            color: {colors["text"]} !important;
        }}
        [data-testid="stMain"] button[kind="primary"] {{
            background-color: {colors["teal"]} !important;
            border: none !important;
        }}
        [data-testid="stMain"] button[kind="primary"] p,
        [data-testid="stMain"] button[kind="primary"] span {{
            color: #FFFFFF !important;
        }}

        /* Sidebar past chats (plain) */
        [data-testid="stSidebar"] button[kind="secondary"] {{
            justify-content: flex-start;
            text-align: left;
            background-color: transparent !important;
            border: 1px solid transparent !important;
        }}
        [data-testid="stSidebar"] button[kind="secondary"]:hover {{
            background-color: {colors["surface"]} !important;
            border-color: {colors["border"]} !important;
        }}

        /* Active sidebar chat (left teal border only) */
        [data-testid="stSidebar"] button[kind="primary"] {{
            justify-content: flex-start;
            text-align: left;
            background-color: {colors["surface"]} !important;
            border: 1px solid {colors["border"]} !important;
            border-left: 3px solid {colors["teal"]} !important;
        }}
        [data-testid="stSidebar"] button[kind="primary"] p,
        [data-testid="stSidebar"] button[kind="primary"] span {{
            color: {colors["text"]} !important;
        }}

        /* + New Chat button ONLY in solid teal */
        [data-testid="stSidebar"] .st-key-new_chat_btn button {{
            justify-content: center !important;
            text-align: center !important;
            background-color: {colors["teal"]} !important;
            border: none !important;
        }}
        [data-testid="stSidebar"] .st-key-new_chat_btn button:hover {{
            background-color: {colors["teal_hover"]} !important;
        }}
        [data-testid="stSidebar"] .st-key-new_chat_btn button p,
        [data-testid="stSidebar"] .st-key-new_chat_btn button span {{
            color: #FFFFFF !important;
            font-weight: 600 !important;
        }}

        /* Details Popover in Light & Dark theme */
        [data-testid="stPopoverBody"],
        [data-baseweb="popover"] > div {{
            background-color: {colors["bg"]} !important;
            border: 1px solid {colors["border"]} !important;
            color: {colors["text"]} !important;
        }}
        [data-testid="stPopoverBody"] p,
        [data-testid="stPopoverBody"] li,
        [data-testid="stPopoverBody"] strong,
        [data-testid="stPopoverBody"] code {{
            color: {colors["text"]} !important;
            background-color: transparent !important;
        }}

        /* Clean chat rows */
        [data-testid="stChatMessage"] {{
            background-color: transparent !important;
            border: none !important;
            padding: 0.45rem 0;
        }}

        /* Default user avatar (neutral) */
        [data-testid="stChatMessageAvatarCustom"] {{
            background-color: {colors["surface"]} !important;
            border: 1px solid {colors["border"]} !important;
        }}
        [data-testid="stChatMessageAvatarCustom"] [data-testid="stIconMaterial"] {{
            color: {colors["text"]} !important;
        }}

   /* Hide assistant icon completely */
        [data-testid="stElementContainer"]:has(.agent-marker) {{
            display: none !important;
        }}
        [data-testid="stChatMessage"]:has(.agent-marker) [data-testid="stChatMessageAvatarCustom"],
        [data-testid="stChatMessage"]:has(.agent-marker) [data-testid="stChatMessageAvatarAssistant"] {{
            display: none !important;
        }}

        /* Human prompt dark teal container */
        .user-prompt-bubble {{
            background-color: {colors["user_bubble"]};
            border: 1px solid {colors["user_border"]};
            color: #FFFFFF !important;
            padding: 0.7rem 1rem;
            border-radius: 12px;
            display: inline-block;
            max-width: 100%;
            line-height: 1.5;
            margin-bottom: 0.2rem;
        }}

        /* Smaller, balanced headings inside agent responses */
        [data-testid="stChatMessage"] h1 {{
            font-size: 1.2rem !important;
            margin: 0.75rem 0 0.35rem 0 !important;
            line-height: 1.35 !important;
        }}
        [data-testid="stChatMessage"] h2 {{
            font-size: 1.08rem !important;
            margin: 0.7rem 0 0.3rem 0 !important;
            line-height: 1.35 !important;
        }}
        [data-testid="stChatMessage"] h3,
        [data-testid="stChatMessage"] h4 {{
            font-size: 1rem !important;
            margin: 0.6rem 0 0.25rem 0 !important;
            line-height: 1.35 !important;
        }}

        /* Chat input box fix for Light & Dark theme */
        [data-testid="stChatInput"] {{
            background-color: transparent !important;
            border: none !important;
        }}
        [data-testid="stChatInput"] > div {{
            background-color: {colors["surface"]} !important;
            border: 1px solid {colors["border"]} !important;
            border-radius: 12px !important;
        }}
        [data-testid="stChatInput"] [data-baseweb="textarea"],
        [data-testid="stChatInput"] [data-baseweb="base-input"] {{
            background-color: transparent !important;
            border: none !important;
        }}
        [data-testid="stChatInput"] textarea {{
            background-color: transparent !important;
            color: {colors["text"]} !important;
            caret-color: {colors["text"]} !important;
        }}
        [data-testid="stChatInput"] textarea::placeholder {{
            color: {colors["muted"]} !important;
        }}
        [data-testid="stChatInputSubmitButton"] {{
            background-color: {colors["border"]} !important;
            color: {colors["text"]} !important;
        }}
        [data-testid="stChatInputSubmitButton"]:hover {{
            background-color: {colors["teal"]} !important;
            color: #FFFFFF !important;
        }}

        /* Edit box textarea */
        [data-testid="stTextArea"] textarea {{
            background-color: {colors["surface"]} !important;
            color: {colors["text"]} !important;
            border: 1px solid {colors["border"]} !important;
        }}

        /* Subtle action icons & Like/Dislike thumbs */
        button[kind="tertiary"] {{
            color: {colors["muted"]} !important;
            padding: 0.2rem 0.4rem !important;
        }}
        button[kind="tertiary"]:hover {{
            color: {colors["text"]} !important;
            background-color: {colors["surface"]} !important;
        }}
        [data-testid="stFeedback"] button {{
            background-color: transparent !important;
        }}
        [data-testid="stFeedback"] button [data-testid="stIconMaterial"] {{
            color: {colors["muted"]} !important;
        }}
        [data-testid="stFeedback"] button[aria-pressed="true"] [data-testid="stIconMaterial"],
        [data-testid="stFeedback"] button[kind="pillsActive"] [data-testid="stIconMaterial"] {{
            color: {colors["teal"]} !important;
        }}
      /* Left-align sidebar chat names (works on all Streamlit versions) */
        [data-testid="stSidebar"] button[data-testid^="stBaseButton"] {{
            display: flex !important;
            justify-content: flex-start !important;
            text-align: left !important;
            padding-left: 0.75rem !important;
        }}
        [data-testid="stSidebar"] button[data-testid^="stBaseButton"] div,
        [data-testid="stSidebar"] button[data-testid^="stBaseButton"] p {{
            width: 100% !important;
            justify-content: flex-start !important;
            text-align: left !important;
        }}

        /* Keep ONLY + New Chat centered */
        [data-testid="stSidebar"] .st-key-new_chat_btn button {{
            justify-content: center !important;
            text-align: center !important;
        }}
        [data-testid="stSidebar"] .st-key-new_chat_btn button div,
        [data-testid="stSidebar"] .st-key-new_chat_btn button p {{
            width: auto !important;
            justify-content: center !important;
            text-align: center !important;
        }}

        /* Move Human prompt (avatar + dark teal box) to the RIGHT side */
        [data-testid="stElementContainer"]:has(.user-edit-marker) {{
            display: none !important;
        }}
        [data-testid="stChatMessage"]:has(.user-prompt-bubble),
        [data-testid="stChatMessage"]:has(.user-edit-marker) {{
            flex-direction: row-reverse !important;
        }}
        .user-bubble-row {{
            display: flex;
            justify-content: flex-end;
            width: 100%;
        }}
        .user-prompt-bubble {{
            max-width: 78% !important;
            text-align: left !important;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)


# --- Helper Functions ---
def load_messages(thread_id: str) -> list[dict]:
    state = chatbot.get_state(config={"configurable": {"thread_id": thread_id}})
    return [
        {"role": "user" if isinstance(m, HumanMessage) else "assistant", "content": m.content}
        for m in state.values.get("messages", [])
        if isinstance(m, (HumanMessage, AIMessage))
    ]


def start_new_chat():
    new_tid = str(uuid.uuid4())
    st.session_state["thread_id"] = new_tid
    st.session_state["chat_threads"].insert(0, new_tid)
    st.session_state["message_history"] = []
    st.session_state["edit_idx"] = None
    st.rerun()


def stream_reply(user_text: str, thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    for chunk, _ in chatbot.stream(
        {"messages": [HumanMessage(content=user_text)]},
        config=config,
        stream_mode="messages",
    ):
        if isinstance(chunk, AIMessageChunk) and chunk.content:
            if isinstance(chunk.content, str):
                yield chunk.content
            elif isinstance(chunk.content, list):
                for part in chunk.content:
                    if isinstance(part, dict) and part.get("text"):
                        yield part["text"]


def render_user_bubble(text: str):
    safe_html = html.escape(text).replace("\n", "<br>")
    st.markdown(
        f'<div class="user-bubble-row"><div class="user-prompt-bubble">{safe_html}</div></div>',
        unsafe_allow_html=True,
    )

def render_copy_icon(text: str, key: str):
    """One-click clipboard copy icon that turns into a teal checkmark briefly."""
    safe_text = json.dumps(text).replace("</", "<\\/")
    icon_color = colors["muted"]
    hover_color = colors["text"]
    hover_bg = colors["surface"]

    components.html(
        f"""
        <style>
            body {{ margin: 0; background: transparent; display: flex; align-items: center; }}
            button {{
                background: transparent;
                border: none;
                border-radius: 6px;
                color: {icon_color};
                cursor: pointer;
                padding: 5px 7px;
                display: inline-flex;
                align-items: center;
            }}
            button:hover {{
                background: {hover_bg};
                color: {hover_color};
            }}
        </style>
        <button id="copy_{key}" onclick="copyText_{key}()">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="9" y="9" width="13" height="13" rx="2"></rect>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
            </svg>
        </button>
        <script>
            function copyText_{key}() {{
                const text = {safe_text};
                const showDone = () => {{
                    const btn = document.getElementById("copy_{key}");
                    const old = btn.innerHTML;
                    btn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#14B8A6" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>';
                    setTimeout(() => btn.innerHTML = old, 1500);
                }};
                if (navigator.clipboard && navigator.clipboard.writeText) {{
                    navigator.clipboard.writeText(text).then(showDone).catch(() => fallbackCopy(text, showDone));
                }} else {{
                    fallbackCopy(text, showDone);
                }}
            }}
            function fallbackCopy(text, done) {{
                const ta = document.createElement("textarea");
                ta.value = text;
                document.body.appendChild(ta);
                ta.select();
                document.execCommand("copy");
                document.body.removeChild(ta);
                done();
            }}
        </script>
        """,
        height=32,
    )


# --- Sidebar ---
with st.sidebar:
    st.markdown("###  Returns & Loss AI")

    if st.button("New Chat", key="new_chat_btn", icon=":material/add:", width="stretch"):
        start_new_chat()

    st.divider()
    st.caption("Chats")

    for tid in st.session_state["chat_threads"]:
        is_active = tid == st.session_state["thread_id"]
        if st.button(
            get_thread_title(tid),
            key=f"chat_{tid}",
            width="stretch",
            type="primary" if is_active else "secondary",
        ):
            st.session_state["thread_id"] = tid
            st.session_state["message_history"] = load_messages(tid)
            st.session_state["edit_idx"] = None
            st.rerun()

    st.divider()
    with st.popover("Details", icon=":material/info:", width="stretch"):
        st.markdown(
            f"""
            **About this Assistant**
            - Helps check why products are being returned and estimate losses.
            - Chats are saved automatically on your computer.

            **Current Chat**
            - Messages: `{len(st.session_state["message_history"])}`
            - Chat ID: `{st.session_state["thread_id"][:8]}`

            **Focus Areas**
            - Faulty supplier batches
            - Misleading product pages
            - Delivery problems
            - Unusual customer returns
            """
        )
        theme_label = "Light Mode" if is_dark else "Dark Mode"
        theme_icon = ":material/light_mode:" if is_dark else ":material/dark_mode:"
    if st.button(theme_label, key="theme_toggle_btn", icon=theme_icon, width="stretch"):
        st.session_state["theme"] = "light" if is_dark else "dark"
        st.rerun()



# --- Empty Chat Welcome & Starter Questions (Disappears once user sends a prompt) ---
selected_prompt = None
if not st.session_state["message_history"]:
    st.markdown(
        """
        <div style="text-align: center; margin-top: 12vh; margin-bottom: 1.8rem;">
            <h2 style="margin-bottom: 0.4rem;">Returns & Loss Assistant</h2>
            <p class="muted-text" style="font-size: 1rem;">
                Ask about product returns, supplier issues, or financial loss.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    starters = [
        "Our wireless earbuds return rate jumped to 18%. Where should we check first?",
        "How can we tell a faulty supplier batch from a delivery problem?",
        "What numbers do we need to calculate total money lost from returns?",
    ]
    cols = st.columns(3)
    for i, (col, text) in enumerate(zip(cols, starters)):
        if col.button(text, key=f"starter_{i}", width="stretch"):
            selected_prompt = text


# --- Display Messages + Action Icons ---
AVATARS = {"user": ":material/person:", "assistant": ":material/shield:"}
tid = st.session_state["thread_id"]

for i, msg in enumerate(st.session_state["message_history"]):
    role = msg["role"]
    with st.chat_message(role, avatar=AVATARS[role]):

        # User Prompt (Dark teal container + Edit & Copy icons)
       # User Prompt (Right-aligned dark teal box + Edit & Copy icons)
        if role == "user":
            if st.session_state["edit_idx"] == i:
                st.markdown('<span class="user-edit-marker"></span>', unsafe_allow_html=True)
                edited_text = st.text_area(
                    "Edit your message",
                    value=msg["content"],
                    key=f"edit_box_{i}",
                    label_visibility="collapsed",
                )
                _, c1, c2 = st.columns([6, 1.2, 1.2])
                if c1.button("Send", key=f"save_edit_{i}", type="primary"):
                    st.session_state["message_history"] = st.session_state["message_history"][:i]
                    st.session_state["queued_prompt"] = edited_text
                    st.session_state["edit_idx"] = None
                    st.rerun()
                if c2.button("Cancel", key=f"cancel_edit_{i}"):
                    st.session_state["edit_idx"] = None
                    st.rerun()
            else:
                render_user_bubble(msg["content"])
                _, c_edit, c_copy = st.columns([11, 0.6, 0.6], gap="small", vertical_alignment="center")
                with c_edit:
                    if st.button("", key=f"edit_{i}", icon=":material/edit:", type="tertiary"):
                        st.session_state["edit_idx"] = i
                        st.rerun()
                with c_copy:
                    render_copy_icon(msg["content"], key=f"u_{i}")

        # Assistant Response (Black & White + Teal avatar + Copy, Run Again, Filled Like/Dislike)
        else:
            st.markdown('<span class="agent-marker"></span>', unsafe_allow_html=True)
            st.markdown(msg["content"])

            c_copy, c_redo, c_fb, _ = st.columns(
                [0.6, 0.6, 2.0, 9.5],
                gap="small",
                vertical_alignment="center",
            )
            with c_copy:
                render_copy_icon(msg["content"], key=f"a_{i}")

            with c_redo:
                if st.button("", key=f"redo_{i}", icon=":material/refresh:", type="tertiary"):
                    if i > 0 and st.session_state["message_history"][i - 1]["role"] == "user":
                        prev_prompt = st.session_state["message_history"][i - 1]["content"]
                        st.session_state["message_history"] = st.session_state["message_history"][: i - 1]
                        st.session_state["queued_prompt"] = prev_prompt
                        st.rerun()

            with c_fb:
                st.feedback("thumbs", key=f"fb_{tid}_{i}")


# --- Send New, Edited, or Retried Message ---
user_input = (
    st.session_state.pop("queued_prompt", None)
    or selected_prompt
    or st.chat_input("Message Returns & Loss Assistant...")
)

if user_input:
    if tid not in st.session_state["chat_threads"]:
        st.session_state["chat_threads"].insert(0, tid)

    st.session_state["message_history"].append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar=AVATARS["user"]):
        render_user_bubble(user_input)

    with st.chat_message("assistant", avatar=AVATARS["assistant"]):
        st.markdown('<span class="agent-marker"></span>', unsafe_allow_html=True)
        reply = st.write_stream(stream_reply(user_input, tid))

    st.session_state["message_history"].append({"role": "assistant", "content": reply})
    st.rerun()