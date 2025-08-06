import streamlit as st
import openai
import requests
import json
import base64

# Page configuration
st.set_page_config(
    page_title="AI Engineer Voice Bot",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS for better UI
st.markdown("""
<style>
.main-header {
    text-align: center;
    color: #2E86AB;
    margin-bottom: 30px;
}
.chat-container {
    background-color: #f0f2f6;
    padding: 20px;
    border-radius: 10px;
    margin: 10px 0;
}
.user-message {
    background-color: #DCF8C6;
    padding: 10px;
    border-radius: 10px;
    margin: 5px 0;
}
.bot-message {
    background-color: #E3F2FD;
    padding: 10px;
    border-radius: 10px;
    margin: 5px 0;
}
.stButton > button {
    background-color: #2E86AB;
    color: white;
    border-radius: 10px;
}
.audio-recorder {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
    padding: 20px;
    border: 2px dashed #ccc;
    border-radius: 10px;
    margin: 10px 0;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []


OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]


# Bot persona and context
BOT_PERSONA = """You are a 23-year-old enthusiastic AI engineer from India. Here are your key characteristics:

BACKGROUND: Just graduated 2 months ago, new to corporate world, passionate about AI and new technologies, compassionate, curious, sometimes emotional but very professional at work.

PERSONALITY TRAITS:
- Casual and understanding communication style
- Give chill vibes, funny at times
- Reliable and can push yourself for work
- Passionate (sometimes mistaken for attitude)
- Curious and willing to take risks with unknown projects to learn

KEY DETAILS:
- Superpower: Always there to back up your team
- Growth area: Building deeper knowledge in AI
- Challenge yourself by: Taking on projects you don't know about to learn new tech
- Recent project: Automated data mining system using Deepseek LLM model
- Common misconception: People think you have attitude at first glance, but it's just your passion

RESPONSE STYLE:
- Keep answers short and crisp
- Be conversational and friendly
- Show enthusiasm about AI and technology
- Avoid NSFW topics
- Be professional but approachable
- Show your Indian background naturally in your responses
"""


def get_bot_response(user_input):
    """Get response from OpenAI API"""
    try:
        openai.api_key = OPENAI_API_KEY

        messages = [
            {"role": "system", "content": BOT_PERSONA},
            {"role": "user", "content": user_input}
        ]

        response = openai.ChatCompletion.create(
            model="gpt-4o-transcribe",
            messages=messages,
            max_tokens=150,
            temperature=0.7
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"Sorry, I encountered an error: {str(e)}"


def text_to_speech_web(text):
    """Generate text-to-speech using browser's Speech Synthesis API"""
    # Return JavaScript code to use browser's built-in TTS
    js_code = f"""
    <script>
    function speakText() {{
        const text = `{text.replace('`', '/`')}`;
        const utterance = new SpeechSynthesisUtterance(text);

        // Try to find an Indian or male voice
        const voices = speechSynthesis.getVoices();
        const indianVoice = voices.find(voice => 
            voice.lang.includes('en-IN') || 
            voice.name.toLowerCase().includes('indian') ||
            (voice.name.toLowerCase().includes('male') && voice.lang.includes('en'))
        );

        if (indianVoice) {{
            utterance.voice = indianVoice;
        }}

        utterance.rate = 0.9;
        utterance.pitch = 1;
        speechSynthesis.speak(utterance);
    }}

    // Load voices and speak
    if (speechSynthesis.getVoices().length > 0) {{
        speakText();
    }} else {{
        speechSynthesis.addEventListener('voiceschanged', speakText, {{ once: true }});
    }}
    </script>
    """
    return js_code


def create_voice_recorder():
    """Create a voice recorder using HTML5 and JavaScript"""
    recorder_html = """
    <div class="audio-recorder">
        <button id="recordBtn" onclick="toggleRecording()" style="
            background: linear-gradient(45deg, #2E86AB, #A23B72);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 25px;
            font-size: 16px;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            transition: all 0.3s ease;
        ">
            🎤 Start Recording
        </button>
        <div id="status" style="margin-top: 10px; font-weight: bold;"></div>
        <audio id="audioPlayback" controls style="margin-top: 10px; display: none;"></audio>
    </div>

    <script>
    let mediaRecorder;
    let audioChunks = [];
    let isRecording = false;

    async function toggleRecording() {
        const recordBtn = document.getElementById('recordBtn');
        const status = document.getElementById('status');

        if (!isRecording) {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];

                mediaRecorder.ondataavailable = event => {
                    audioChunks.push(event.data);
                };

                mediaRecorder.onstop = () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    const audioUrl = URL.createObjectURL(audioBlob);

                    const audioPlayback = document.getElementById('audioPlayback');
                    audioPlayback.src = audioUrl;
                    audioPlayback.style.display = 'block';

                    // Convert to base64 and store in session state
                    const reader = new FileReader();
                    reader.onload = function() {
                        const base64Audio = reader.result.split(',')[1];
                        // You would send this to your backend for processing
                        status.textContent = 'Audio recorded! Click Send to process.';

                        // Store the audio data
                        window.recordedAudio = base64Audio;
                    };
                    reader.readAsDataURL(audioBlob);
                };

                mediaRecorder.start();
                isRecording = true;
                recordBtn.textContent = '⏹️ Stop Recording';
                recordBtn.style.background = 'linear-gradient(45deg, #e74c3c, #c0392b)';
                status.textContent = 'Recording... Click to stop';

            } catch (err) {
                status.textContent = 'Error: Could not access microphone';
                console.error('Error accessing microphone:', err);
            }
        } else {
            mediaRecorder.stop();
            mediaRecorder.stream.getTracks().forEach(track => track.stop());
            isRecording = false;
            recordBtn.textContent = '🎤 Start Recording';
            recordBtn.style.background = 'linear-gradient(45deg, #2E86AB, #A23B72)';
            status.textContent = 'Processing...';
        }
    }
    </script>
    """
    return recorder_html


# Main app
def main():
    st.markdown("<h1 class='main-header'>🤖 AI Engineer Voice Bot</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align: center; color: #666;'>Chat with an enthusiastic 23-year-old AI engineer from India!</p>",
        unsafe_allow_html=True)

    # Instructions
    with st.sidebar.expander("📋 How to Use"):
        st.markdown("""
        1. **Type your message** in the text box, OR
        2. **Record audio** using the voice recorder
        3. **Click Send** to get a response
        4. **Click the speaker button** to hear responses

        **Sample Questions:**
        - What should we know about your life story?
        - What's your #1 superpower?
        - What are your growth areas?
        - How do you challenge yourself?
        - Tell me about your recent projects
        - What misconceptions do people have about you?
        """)

    # Chat interface
    st.markdown("### 💬 Chat Interface")

    # Display chat history
    chat_container = st.container()

    with chat_container:
        for message in st.session_state.messages:
            if message["role"] == "user":
                st.markdown(f"<div class='user-message'><strong>You:</strong> {message['content']}</div>",
                            unsafe_allow_html=True)
            else:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"<div class='bot-message'><strong>AI Engineer:</strong> {message['content']}</div>",
                                unsafe_allow_html=True)
                with col2:
                    if st.button(f"🔊", key=f"speak_{len(st.session_state.messages)}_{message['content'][:10]}"):
                        st.components.v1.html(text_to_speech_web(message['content']), height=0)

    # Input methods
    st.markdown("### 📝 Send a Message")

    # Text input
    user_input = st.text_input("Type your message here:", key="text_input",
                               placeholder="Ask me anything about my background, skills, or projects!")

    # Voice recorder
    st.markdown("### 🎤 Or Record Your Voice")
    st.components.v1.html(create_voice_recorder(), height=200)

    # Send button
    if st.button("Send Message", type="primary") or user_input:
        message_text = user_input.strip() if user_input else ""

        if message_text:
            # Add user message to history
            st.session_state.messages.append({"role": "user", "content": message_text})

            # Get bot response
            with st.spinner("Thinking..."):
                bot_response = get_bot_response(message_text)

            # Add bot response to history
            st.session_state.messages.append({"role": "assistant", "content": bot_response})

            # Auto-speak the response
            st.components.v1.html(text_to_speech_web(bot_response), height=0)

            # Rerun to update the interface
            st.rerun()

    # Sample questions buttons
    st.markdown("### 🎯 Try These Sample Questions")
    sample_questions = [
        "What should we know about your life story?",
        "What's your #1 superpower?",
        "What are the top 3 areas you'd like to grow in?",
        "What misconception do your coworkers have about you?",
        "How do you push your boundaries and limits?"
    ]

    cols = st.columns(2)
    for i, question in enumerate(sample_questions):
        with cols[i % 2]:
            if st.button(question, key=f"sample_{i}"):
                # Add question to messages
                st.session_state.messages.append({"role": "user", "content": question})

                # Get response
                with st.spinner("Thinking..."):
                    bot_response = get_bot_response(question)

                # Add response
                st.session_state.messages.append({"role": "assistant", "content": bot_response})

                # Auto-speak the response
                st.components.v1.html(text_to_speech_web(bot_response), height=0)

                st.rerun()

    # Clear chat button
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

    # Footer
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: #666; font-size: 12px;'>"
        "Built by Somesh Nagar using Streamlit | Powered by OpenAI GPT-3.5 | Voice powered by Web Speech API"
        "</p>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":

    main()

