import streamlit as st
import os
from dotenv import load_dotenv
from google.cloud import speech
import time
import pandas as pd

# --- Page Configuration ---
st.set_page_config(
    page_title="LongSorn AI Playground",
    page_icon="🤖",
    layout="wide"
)

# --- Load Environment Variables ---
load_dotenv()

# --- Backend Functions AI Calls ---

@st.cache_data
def run_stt_transcription(audio_file_content):
    """
    ฟังก์ชันสำหรับเรียกใช้ Google STT API จริง
    """
    try:
        client = speech.SpeechClient()
        audio = speech.RecognitionAudio(content=audio_file_content)
        
        # --- ส่วนที่แก้ไข ---
        # เราจะสร้าง config แบบ "โล่งๆ" เพื่อให้ API ตรวจจับ encoding และ sample rate โดยอัตโนมัติ
        # ซึ่งเป็นวิธีที่ยืดหยุ่นกว่าสำหรับไฟล์หลายประเภท
        config = speech.RecognitionConfig(
            language_code="th-TH",
            enable_automatic_punctuation=True,
            enable_word_time_offsets=True,
        )
        
        response = client.recognize(config=config, audio=audio)
        return response, None
    except Exception as e:
        # เพิ่มการแสดงผล error ที่ละเอียดขึ้น
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
        status.update(label="กำลังประมวลผลเสียง (Speech-to-Text)...")
        stt_response, error = run_stt_transcription(st.session_state.uploaded_file_content)
        
        if error:
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