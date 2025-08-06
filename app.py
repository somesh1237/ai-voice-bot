import streamlit as st
import requests
import json
import base64
import io

# Page configuration
st.set_page_config(
    page_title="AI Engineer Voice Bot",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS for better UI with darker message colors
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
    background-color: #2c3e50;
    color: white;
    padding: 15px;
    border-radius: 15px;
    margin: 10px 0;
    border-left: 4px solid #3498db;
}
.bot-message {
    background-color: #34495e;
    color: white;
    padding: 15px;
    border-radius: 15px;
    margin: 10px 0;
    border-left: 4px solid #e74c3c;
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

if 'message_counter' not in st.session_state:
    st.session_state.message_counter = 0

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

def transcribe_audio(audio_base64):
    """Transcribe audio using OpenAI Whisper API"""
    try:
        # Decode base64 audio
        audio_data = base64.b64decode(audio_base64)
        
        # Create a file-like object
        audio_file = io.BytesIO(audio_data)
        audio_file.name = "audio.wav"
        
        # Prepare the request for Whisper API
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
        }
        
        files = {
            "file": ("audio.wav", audio_file, "audio/wav"),
            "model": (None, "whisper-1"),
        }
        
        response = requests.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers=headers,
            files=files,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("text", "Could not transcribe audio")
        else:
            return f"Transcription failed: {response.status_code}"
            
    except Exception as e:
        return f"Error transcribing audio: {str(e)}"

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
    """Get response from OpenAI API using requests"""
    try:
        # Using requests instead of OpenAI library for better compatibility
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": BOT_PERSONA},
                {"role": "user", "content": user_input}
            ],
            "max_tokens": 150,
            "temperature": 0.7
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
        else:
            error_info = response.json() if response.content else {"error": "Unknown error"}
            return f"API Error ({response.status_code}): {error_info.get('error', {}).get('message', 'Unknown error')}"
            
    except requests.exceptions.Timeout:
        return "Request timed out. Please try again."
    except requests.exceptions.RequestException as e:
        return f"Network error: {str(e)}"
    except Exception as e:
        return f"Sorry, I encountered an error: {str(e)}"

def text_to_speech_web(text):
    """Generate text-to-speech using browser's Speech Synthesis API"""
    # Clean text - remove emojis and special characters
    clean_text = ''.join(char for char in text if ord(char) < 127 and char.isprintable())
    # Remove extra spaces
    clean_text = ' '.join(clean_text.split())
    
    # Return JavaScript code to use browser's built-in TTS
    js_code = f"""
    <script>
    function speakText() {{
        const text = `{clean_text.replace('`', '\\`').replace('\\', '\\\\').replace('"', '\\"')}`;
        
        // Stop any currently playing speech to prevent overlapping
        speechSynthesis.cancel();
        
        const utterance = new SpeechSynthesisUtterance(text);

        // Find a male voice (prioritize male voices)
        const voices = speechSynthesis.getVoices();
        const maleVoice = voices.find(voice => 
            voice.name.toLowerCase().includes('male') ||
            voice.name.toLowerCase().includes('david') ||
            voice.name.toLowerCase().includes('alex') ||
            voice.name.toLowerCase().includes('daniel') ||
            (voice.lang.includes('en') && voice.name.toLowerCase().includes('indian')) ||
            (voice.lang.includes('en-IN'))
        );

        if (maleVoice) {{
            utterance.voice = maleVoice;
        }}

        utterance.rate = 1.2;  // Faster speech
        utterance.pitch = 0.8;  // Lower pitch for more masculine sound
        
        // Ensure it only plays once
        utterance.onend = function() {{
            console.log('Speech finished');
        }};
        
        utterance.onerror = function(event) {{
            console.log('Speech error:', event.error);
        }};
        
        speechSynthesis.speak(utterance);
    }}

    // Load voices and speak - only once
    if (speechSynthesis.getVoices().length > 0) {{
        speakText();
    }} else {{
        speechSynthesis.addEventListener('voiceschanged', function() {{
            speakText();
        }}, {{ once: true }});
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
        <button id="sendVoiceBtn" onclick="sendVoiceMessage()" style="
            background: linear-gradient(45deg, #27AE60, #2ECC71);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 15px;
            font-size: 14px;
            cursor: pointer;
            margin-top: 10px;
            display: none;
        ">
            📤 Send Voice Message
        </button>
    </div>

    <script>
    let mediaRecorder;
    let audioChunks = [];
    let isRecording = false;
    let recordedAudioData = null;

    async function toggleRecording() {
        const recordBtn = document.getElementById('recordBtn');
        const status = document.getElementById('status');
        const sendBtn = document.getElementById('sendVoiceBtn');

        if (!isRecording) {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];

                mediaRecorder.ondataavailable = event => {
                    audioChunks.push(event.data);
                };

                mediaRecorder.onstop = async () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    const audioUrl = URL.createObjectURL(audioBlob);

                    const audioPlayback = document.getElementById('audioPlayback');
                    audioPlayback.src = audioUrl;
                    audioPlayback.style.display = 'block';

                    // Convert to base64 for transcription
                    const reader = new FileReader();
                    reader.onload = function() {
                        recordedAudioData = reader.result.split(',')[1];
                        status.textContent = 'Audio recorded! Click Send Voice Message to process.';
                        sendBtn.style.display = 'block';
                    };
                    reader.readAsDataURL(audioBlob);
                };

                mediaRecorder.start();
                isRecording = true;
                recordBtn.textContent = '⏹️ Stop Recording';
                recordBtn.style.background = 'linear-gradient(45deg, #e74c3c, #c0392b)';
                status.textContent = 'Recording... Click to stop';
                sendBtn.style.display = 'none';

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

    async function sendVoiceMessage() {
        const status = document.getElementById('status');
        const sendBtn = document.getElementById('sendVoiceBtn');
        
        if (!recordedAudioData) {
            status.textContent = 'No audio recorded!';
            return;
        }

        status.textContent = 'Sending audio for transcription...';
        sendBtn.disabled = true;

        try {
            // Send the audio data to Streamlit for processing
            const hiddenInput = document.querySelector('input[data-testid*="hidden_audio_data"]');
            if (hiddenInput) {
                hiddenInput.value = recordedAudioData;
                hiddenInput.dispatchEvent(new Event('input', { bubbles: true }));
                hiddenInput.dispatchEvent(new Event('change', { bubbles: true }));
            }

            status.textContent = 'Voice message sent for processing!';
            sendBtn.style.display = 'none';
            recordedAudioData = null;
            
            // Hide the audio playback
            document.getElementById('audioPlayback').style.display = 'none';
            
        } catch (error) {
            status.textContent = 'Error sending voice message: ' + error.message;
        } finally {
            sendBtn.disabled = false;
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
        for i, message in enumerate(st.session_state.messages):
            if message["role"] == "user":
                st.markdown(f"<div class='user-message'><strong>👤 You:</strong> {message['content']}</div>",
                            unsafe_allow_html=True)
            else:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"<div class='bot-message'><strong>🤖 AI Engineer:</strong> {message['content']}</div>",
                                unsafe_allow_html=True)
                with col2:
                    # Use message index for unique keys to avoid duplicate widget IDs
                    if st.button("🔊", key=f"speak_btn_{i}"):
                        st.components.v1.html(text_to_speech_web(message['content']), height=0)

    # Input methods
    st.markdown("### 📝 Send a Message")

    # Text input
    user_input = st.text_input("Type your message here:", key="text_input",
                               placeholder="Ask me anything about my background, skills, or projects!")

    # Voice recorder
    st.markdown("### 🎤 Or Record Your Voice")
    st.components.v1.html(create_voice_recorder(), height=200)
    
    # Handle voice message processing
    if 'pending_audio' in st.session_state and st.session_state.pending_audio:
        audio_data = st.session_state.pending_audio
        st.session_state.pending_audio = None  # Clear the pending audio
        
        with st.spinner("🎧 Transcribing your voice message..."):
            transcribed_text = transcribe_audio(audio_data)
        
        if transcribed_text and not transcribed_text.startswith("Error") and not transcribed_text.startswith("Transcription failed"):
            # Add user message to history
            st.session_state.messages.append({"role": "user", "content": transcribed_text})
            
            # Get bot response
            with st.spinner("Thinking..."):
                bot_response = get_bot_response(transcribed_text)
            
            # Add bot response to history
            st.session_state.messages.append({"role": "assistant", "content": bot_response})
            
            # Increment message counter
            st.session_state.message_counter += 1
            
            st.rerun()
        else:
            st.error(f"Failed to transcribe audio: {transcribed_text}")
    
    # Check for audio data from JavaScript
    audio_data_js = st.text_input("", key="hidden_audio_data", label_visibility="hidden")
    if audio_data_js and audio_data_js != "":
        # Process the audio data
        st.session_state.pending_audio = audio_data_js
        st.rerun()

    # Send button
    send_clicked = st.button("Send Message", type="primary")
    
    if send_clicked:
        message_text = user_input.strip() if user_input else ""

        if message_text:
            # Add user message to history
            st.session_state.messages.append({"role": "user", "content": message_text})

            # Get bot response
            with st.spinner("Thinking..."):
                bot_response = get_bot_response(message_text)

            # Add bot response to history
            st.session_state.messages.append({"role": "assistant", "content": bot_response})

            # Increment message counter
            st.session_state.message_counter += 1

            # Clear the text input and rerun to update interface
            st.rerun()

    # Auto-speak the latest bot message if it's new
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
        # Check if we just added a new message (after rerun)
        if len(st.session_state.messages) > 0:
            latest_message = st.session_state.messages[-1]["content"]
            # Create a unique key for auto-speaking to avoid duplicates
            auto_speak_key = f"auto_speak_{len(st.session_state.messages)}"
            
            # Only auto-speak if we haven't spoken this message yet
            if auto_speak_key not in st.session_state:
                st.session_state[auto_speak_key] = True
                st.components.v1.html(text_to_speech_web(latest_message), height=0)

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
            if st.button(question, key=f"sample_question_{i}"):
                # Add question to messages
                st.session_state.messages.append({"role": "user", "content": question})

                # Get response
                with st.spinner("Thinking..."):
                    bot_response = get_bot_response(question)

                # Add response
                st.session_state.messages.append({"role": "assistant", "content": bot_response})

                # Increment message counter
                st.session_state.message_counter += 1

                st.rerun()

    # Clear chat button
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.session_state.message_counter = 0
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
