import streamlit as st
import os
import json
import requests
from dotenv import load_dotenv
from google.cloud import speech
import google.generativeai as genai
import time
import pandas as pd
import subprocess
import tempfile

# --- Page Configuration & ENV Loading ---
st.set_page_config(page_title="LongSorn AI", page_icon="🤖", layout="wide")
load_dotenv()

# --- Backend Functions (AI Calls) ---

def convert_audio_with_ffmpeg(input_bytes):
    """
    ใช้ FFmpeg เพื่อแปลงไฟล์เสียงที่รับเข้ามาให้เป็นรูปแบบที่ STT ต้องการ
    """
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".tmp") as temp_in:
            temp_in.write(input_bytes)
            input_filename = temp_in.name
        
        output_filename = input_filename + ".wav"
        command = [
            "ffmpeg", "-i", input_filename, "-acodec", "pcm_s16le",
            "-ar", "16000", "-ac", "1", "-y", output_filename
        ]
        subprocess.run(command, check=True, capture_output=True, text=True)
        
        with open(output_filename, "rb") as f:
            output_bytes = f.read()
            
        os.remove(input_filename)
        os.remove(output_filename)
        return output_bytes, None
    except Exception as e:
        st.error(f"FFmpeg Error: {e}")
        return None, str(e)

@st.cache_data
def run_stt_transcription(audio_file_content):
    """
    ฟังก์ชันสำหรับเรียกใช้ Google STT API จริง
    """
    try:
        client = speech.SpeechClient()
        audio = speech.RecognitionAudio(content=audio_file_content)
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

def run_real_nlp_analysis(transcript: str):
    """
    ฟังก์ชันสำหรับเรียกใช้ Gemini และ Typhoon API เพื่อวิเคราะห์ Transcript จริง
    """
    # ---- 1. Gemini Analysis for General Feedback ----
    gemini_feedback = "Not available"
    try:
        genai.configure(api_key=os.getenv("GOOGLE_GEMINI_API_KEY"))
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        Analyze the following teaching transcript:
        "{transcript}"
        
        Provide an evaluation on two metrics:
        1. Speaking Pace: Is the pace Good, Too fast, or Too slow?
        2. Clarity Score: Rate the clarity of communication on a scale from 1 to 10.

        Please respond only in this exact format:
        Pace: [Your Result]
        Clarity: [Your Score]
        """
        response = model.generate_content(prompt)
        gemini_feedback = response.text
    except Exception as e:
        st.warning(f"Could not connect to Gemini API: {e}")

    # ---- 2. Typhoon API Analysis for Thai-specific Filler Words ----
    filler_word_count = 0
    try:
        api_url = os.getenv("TYPHOON_API_URL")
        api_key = os.getenv("TYPHOON_API_KEY")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "typhoon-v2.1-12b-instruct", # ชื่อโมเดลตามที่ผู้ให้บริการกำหนด
            "prompt": f"จากข้อความต่อไปนี้: \"{transcript}\" ช่วยนับจำนวนคำฟุ่มเฟือยของภาษาไทย (เช่น เอ่อ, อ่า, แบบว่า, คือว่า, นะครับ) ว่ามีทั้งหมดกี่คำ ตอบเป็นตัวเลขเท่านั้น",
            "max_tokens": 10
        }
        
        response = requests.post(api_url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        response_json = response.json()
        
        # การดึงผลลัพธ์อาจจะต้องปรับตาม Response จริงของผู้ให้บริการ
        # สมมติว่าผลลัพธ์อยู่ใน response_json['choices'][0]['text']
        raw_response = response_json.get("choices", [{}])[0].get("text", "0")
        filler_word_count = int("".join(filter(str.isdigit, raw_response)))

    except Exception as e:
        st.warning(f"Could not connect to Typhoon API: {e}")

    # ---- Combine Results ---
    pace = "N/A"
    clarity = 0.0
    for line in gemini_feedback.splitlines():
        if "Pace:" in line:
            pace = line.split("Pace:")[1].strip()
        if "Clarity:" in line:
            try:
                clarity = float(line.split("Clarity:")[1].strip())
            except:
                clarity = 0.0

    return {
        "speech_analysis": {
            "Filler Words Detected": filler_word_count,
            "Speaking Pace": pace,
            "Clarity Score": clarity
        },
        "timeline_feedback": [{"timestamp": "N/A", "type": "Mock", "suggestion": "Real timeline feedback requires further logic."}],
        "ai_recommendations": [{"original": "N/A", "suggestion": "Mock recommendation."}]
    }

# --- Main UI and Processing Logic ---
st.title("🤖 LongSorn AI")
if 'analysis_triggered' in st.session_state and st.session_state.analysis_triggered:
    with st.status("AI is analyzing your content...", expanded=True) as status:
        status.update(label="กำลังแปลงไฟล์เสียงให้อยู่ในรูปแบบมาตรฐาน...")
        converted_audio_content, ffmpeg_error = convert_audio_with_ffmpeg(st.session_state.uploaded_file_content)
        
        if ffmpeg_error:
            status.update(label="เกิดข้อผิดพลาดในการแปลงไฟล์!", state="error", expanded=True)
            st.stop()
        
        status.update(label="กำลังประมวลผลเสียง (Speech-to-Text)...")
        stt_response, stt_error = run_stt_transcription(converted_audio_content)
        
        if stt_error:
            status.update(label="เกิดข้อผิดพลาด!", state="error", expanded=True)
            st.stop()
        
        st.session_state.stt_response = stt_response
        status.update(label="กำลังวิเคราะห์ด้วยโมเดลภาษา (AI Analysis)...")
        
        full_transcript = " ".join(
            [result.alternatives[0].transcript for result in stt_response.results if result.alternatives]
        ) if stt_response and stt_response.results else ""

        nlp_results = run_real_nlp_analysis(full_transcript)
        st.session_state.nlp_results = nlp_results
        
        status.update(label="การวิเคราะห์เสร็จสิ้น!", state="complete", expanded=False)

    st.session_state.analysis_triggered = False
    st.session_state.results_ready = True

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
                st.write(f"**Suggestion:** {feedback['suggestion']}")
    
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