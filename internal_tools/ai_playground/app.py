import streamlit as st
import os
from dotenv import load_dotenv
from google.cloud import speech
import time
import pandas as pd
import subprocess # สำหรับเรียกใช้ FFmpeg
import tempfile # สำหรับสร้างไฟล์ชั่วคราว

# --- Page Configuration ---
st.set_page_config(
    page_title="LongSorn AI Playground",
    page_icon="🤖",
    layout="wide"
)

# --- Load Environment Variables ---
load_dotenv()

# --- Backend Functions (AI Calls) ---

def convert_audio_with_ffmpeg(input_bytes):
    """
    ใช้ FFmpeg เพื่อแปลงไฟล์เสียงที่รับเข้ามาให้เป็นรูปแบบที่ STT ต้องการ
    (WAV, 16-bit PCM, 16000 Hz, Mono)
    """
    try:
        # สร้างไฟล์ชั่วคราวสำหรับ Input และ Output
        with tempfile.NamedTemporaryFile(delete=False, suffix=".tmp") as temp_in:
            temp_in.write(input_bytes)
            input_filename = temp_in.name
        
        output_filename = input_filename + ".wav"

        # รันคำสั่ง FFmpeg
        command = [
            "ffmpeg",
            "-i", input_filename,      # Input file
            "-acodec", "pcm_s16le",    # Audio codec: 16-bit signed little-endian PCM
            "-ar", "16000",            # Audio sample rate: 16000 Hz
            "-ac", "1",                # Audio channels: 1 (Mono)
            "-y",                      # Overwrite output file if it exists
            output_filename
        ]
        
        process = subprocess.run(command, check=True, capture_output=True, text=True)
        
        # อ่านข้อมูลจากไฟล์ Output ที่แปลงแล้ว
        with open(output_filename, "rb") as f:
            output_bytes = f.read()
            
        # ลบไฟล์ชั่วคราว
        os.remove(input_filename)
        os.remove(output_filename)
        
        return output_bytes, None
    except subprocess.CalledProcessError as e:
        # กรณี FFmpeg ทำงานผิดพลาด
        error_message = f"FFmpeg error: {e.stderr}"
        st.error(error_message)
        return None, error_message
    except Exception as e:
        return None, str(e)


@st.cache_data
def run_stt_transcription(audio_file_content):
    """
    ฟังก์ชันสำหรับเรียกใช้ Google STT API จริง
    """
    try:
        client = speech.SpeechClient()
        audio = speech.RecognitionAudio(content=audio_file_content)
        
        # ตอนนี้รับประกันได้ว่าไฟล์เป็น WAV 16kHz แล้ว จึงสามารถระบุ config ได้
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="th-TH",
            enable_automatic_punctuation=True,
            enable_word_time_offsets=True,
        )
        
        response = client.recognize(config=config, audio=audio)
        return response, None
    except Exception as e:
        st.error(f"Google STT API Error: {e}")
        return None, str(e)

def run_mock_nlp_analysis(transcript: str):
    """
    ฟังก์ชันจำลองการทำงานของ NLP (Gemini/Typhoon)
    """
    time.sleep(1) # ลดเวลาจำลอง
    filler_word_count = transcript.lower().count("เอ่อ") + transcript.lower().count("แบบว่า") + transcript.lower().count("อืม")
    return {
        "speech_analysis": {
            "Filler Words Detected": filler_word_count,
            "Speaking Pace": "Good",
            "Clarity Score": 8.2
        },
        "timeline_feedback": [
            {"timestamp": "0:01", "type": "Filler Word", "suggestion": "พบคำว่า 'เอ่อ' ลองเว้นจังหวะแทน"},
            {"timestamp": "0:06", "type": "Filler Word", "suggestion": "พบคำว่า 'แบบว่า' ซึ่งเป็นคำฟุ่มเฟือย"},
        ],
        "ai_recommendations": [
            {"original": "เอ่อ... วันนี้เราก็จะมาเรียนเรื่องการ...", "suggestion": "วันนี้เราจะมาเรียนเรื่อง..."},
            {"original": "ซึ่งแบบว่ามันเป็นเรื่องที่สำคัญมาก", "suggestion": "ซึ่งเป็นเรื่องที่สำคัญมาก"}
        ]
    }

# --- Main UI ---

st.title("🤖 LongSorn AI Playground")
st.caption("เครื่องมือสาธิตการทำงานของ AI Pipeline ที่มี UI ใกล้เคียงกับผลิตภัณฑ์จริง")
st.divider()

# --- Upload ---
st.header("Upload Your Content")
uploaded_file = st.file_uploader(
    "อัปโหลดไฟล์วิดีโอหรือไฟล์เสียง (จำกัด 1 ไฟล์, สูงสุด 100MB)",
    type=["mp4", "mov", "mp3", "wav", "m4a", "flac"],
    label_visibility="collapsed"
)

if uploaded_file is not None:
    file_size_mb = uploaded_file.size / (1024 * 1024)
    if file_size_mb > 100:
        st.error("ไฟล์มีขนาดใหญ่เกิน 100MB กรุณาเลือกไฟล์ใหม่")
    else:
        st.info(f"Selected File: **{uploaded_file.name}** ({file_size_mb:.2f} MB)")
        st.audio(uploaded_file)
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("Upload & Analyze", type="primary", use_container_width=True):
                st.session_state.clear()
                st.session_state.analysis_triggered = True
                st.session_state.uploaded_file_content = uploaded_file.getvalue()
        with col2:
            if st.button("Clear", use_container_width=True):
                st.session_state.clear()
                st.rerun()

# --- Processing ---
if 'analysis_triggered' in st.session_state and st.session_state.analysis_triggered:
    with st.status("AI is analyzing your content...", expanded=True) as status:
        
        status.update(label="กำลังแปลงไฟล์เสียงให้อยู่ในรูปแบบมาตรฐาน...")
        # --- แปลงไฟล์ด้วย FFmpeg ก่อน ---
        converted_audio_content, ffmpeg_error = convert_audio_with_ffmpeg(st.session_state.uploaded_file_content)
        
        if ffmpeg_error:
            status.update(label="เกิดข้อผิดพลาดในการแปลงไฟล์!", state="error", expanded=True)
            st.stop()
        
        status.update(label="กำลังประมวลผลเสียง (Speech-to-Text)...")
        # --- เรียกใช้ STT ด้วยไฟล์ที่แปลงแล้ว ---
        stt_response, stt_error = run_stt_transcription(converted_audio_content)
        
        if stt_error:
            status.update(label="เกิดข้อผิดพลาด!", state="error", expanded=True)
            st.stop()
        
        st.session_state.stt_response = stt_response
        status.update(label="กำลังวิเคราะห์ด้วยโมเดลภาษา (AI Analysis)...")
        
        full_transcript = " ".join(
            [result.alternatives[0].transcript for result in stt_response.results if result.alternatives]
        ) if stt_response and stt_response.results else ""

        nlp_results = run_mock_nlp_analysis(full_transcript)
        st.session_state.nlp_results = nlp_results
        
        status.update(label="การวิเคราะห์เสร็จสิ้น!", state="complete", expanded=False)

    st.session_state.analysis_triggered = False
    st.session_state.results_ready = True

# --- Results ---
if 'results_ready' in st.session_state and st.session_state.results_ready:
    st.divider()
    st.header("AI Analysis Results")
    stt_res = st.session_state.stt_response
    nlp_res = st.session_state.nlp_results
    
    left_col, right_col = st.columns(2, gap="large")
    with left_col:
        st.subheader("Presentation Playback")
        st.video("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        st.subheader("Timeline Feedback")
        for feedback in nlp_res["timeline_feedback"]:
            with st.container(border=True):
                r1_col1, r1_col2 = st.columns([1, 4])
                with r1_col1:
                    st.write(f"**{feedback['timestamp']}**")
                with r1_col2:
                    st.write(f"**{feedback['type']}**")
                st.info(f"**Suggestion:** {feedback['suggestion']}")
    
    with right_col:
        st.subheader("Speech Analysis")
        with st.container(border=True):
            analysis = nlp_res["speech_analysis"]
            st.metric("Filler Words Detected", f"{analysis['Filler Words Detected']} times")
            st.metric("Speaking Pace", analysis['Speaking Pace'])
            st.metric("Clarity Score", f"{analysis['Clarity Score']} / 10")
        
        st.subheader("Transcript & Word Timestamps")
        with st.expander("คลิกเพื่อดู Transcript และข้อมูลเวลาของแต่ละคำ"):
            if not stt_res or not stt_res.results or not stt_res.results[0].alternatives:
                st.warning("ไม่พบข้อความในไฟล์เสียง")
            else:
                full_transcript = " ".join([res.alternatives[0].transcript for res in stt_res.results])
                st.text_area("Full Transcript", full_transcript, height=150)
                word_data = []
                for result in stt_res.results:
                    for word_info in result.alternatives[0].words:
                        word_data.append({
                            "Word": word_info.word,
                            "Start (s)": f"{word_info.start_time.total_seconds():.2f}",
                            "End (s)": f"{word_info.end_time.total_seconds():.2f}"
                        })
                st.dataframe(word_data)

    if st.button("Analyze Another"):
        st.session_state.clear()
        st.rerun()