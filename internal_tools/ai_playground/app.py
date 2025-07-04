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
import re

# --- Page Configuration & ENV Loading ---
st.set_page_config(page_title="LongSorn AI Demo", page_icon="🖊️", layout="wide")
load_dotenv()

# --- Backend Functions (AI Calls) ---

def convert_audio_with_ffmpeg(input_bytes):
    """ใช้ FFmpeg เพื่อแปลงไฟล์เสียงที่รับเข้ามาให้เป็นรูปแบบที่ STT ต้องการ"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".tmp") as temp_in:
            temp_in.write(input_bytes)
            input_filename = temp_in.name
        
        output_filename = input_filename + ".wav"
        command = ["ffmpeg", "-i", input_filename, "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", "-y", output_filename]
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
    """ฟังก์ชันสำหรับเรียกใช้ Google STT API จริง"""
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

def find_timestamp_for_phrase(phrase, word_timestamps):
    """ค้นหาเวลาเริ่มต้นของวลีจาก word_timestamps"""
    words_in_phrase = phrase.split()
    if not words_in_phrase:
        return "0:00"

    for i in range(len(word_timestamps) - len(words_in_phrase) + 1):
        match = True
        for j in range(len(words_in_phrase)):
            if word_timestamps[i+j]['Word'] != words_in_phrase[j]:
                match = False
                break
        if match:
            start_seconds = float(word_timestamps[i]['Start (s)'])
            minutes = int(start_seconds // 60)
            seconds = int(start_seconds % 60)
            return f"{minutes:01d}:{seconds:02d}"
    return "N/A"

def run_real_nlp_analysis(transcript: str, word_timestamps: list, description: str):
    """ฟังก์ชันสำหรับเรียกใช้ Gemini และ Typhoon API เพื่อวิเคราะห์ Transcript จริง"""
    context_prompt = f"Context for the presentation: {description}\n\n" if description else ""

    # ---- Gemini Analysis for General Feedback & Recommendations ----
    gemini_feedback = "Not available"
    try:
        genai.configure(api_key=os.getenv("GOOGLE_GEMINI_API_KEY"))
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        {context_prompt}Analyze the following teaching transcript:
        "{transcript}"
        
        First, provide an evaluation on two metrics in this exact format:
        Pace: [Your Result: Good, Too fast, or Too slow]
        Clarity: [Your Score: 1-10]
        
        Second, identify up to 3 specific phrases that could be improved. For each, provide the original phrase, a brief reason, and a suggestion. Use this exact format for each, separated by a new line:
        ORIGINAL: [original phrase] | REASON: [reason for improvement] | SUGGESTION: [suggested alternative]
        """
        response = model.generate_content(prompt)
        gemini_feedback = response.text
    except Exception as e:
        st.warning(f"Could not connect to Gemini API: {e}")

    # ---- Typhoon API Analysis for Filler Words ----
    filler_word_count = 0
    try:
        api_url = os.getenv("TYPHOON_API_URL")
        api_key = os.getenv("TYPHOON_API_KEY")
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "typhoon-v2.1-12b-instruct",
            "messages": [{"role": "user", "content": f"จากข้อความต่อไปนี้: \"{transcript}\" ช่วยนับจำนวนคำฟุ่มเฟือยของภาษาไทย (เช่น เอ่อ, อ่า, แบบว่า, คือว่า, นะครับ) ว่ามีทั้งหมดกี่คำ ตอบเป็นตัวเลขเท่านั้น"}],
            "max_tokens": 10
        }
        response = requests.post(api_url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        response_json = response.json()
        raw_response = response_json.get("choices", [{}])[0].get("message", {}).get("content", "0")
        filler_word_count = int("".join(filter(str.isdigit, raw_response)))
    except Exception as e:
        st.warning(f"Could not connect to Typhoon API: {e}")

    # ---- Combine and Process Results ----
    pace = "N/A"
    clarity = 0.0
    timeline_feedback = []
    ai_recommendations = []

    for line in gemini_feedback.splitlines():
        if "Pace:" in line:
            pace = line.split("Pace:")[1].strip()
        elif "Clarity:" in line:
            try:
                clarity = float(line.split("Clarity:")[1].strip())
            except:
                clarity = 0.0
        elif "ORIGINAL:" in line:
            parts = [p.strip() for p in line.split('|')]
            if len(parts) == 3:
                original = parts[0].replace("ORIGINAL:", "").strip()
                reason = parts[1].replace("REASON:", "").strip()
                suggestion = parts[2].replace("SUGGESTION:", "").strip()
                
                # สร้าง AI Recommendations
                ai_recommendations.append({"original": original, "suggestion": suggestion})
                
                # สร้าง Timeline Feedback
                timestamp = find_timestamp_for_phrase(original, word_timestamps)
                timeline_feedback.append({"timestamp": timestamp, "type": reason, "suggestion": suggestion})

    return {
        "speech_analysis": {"Filler Words Detected": filler_word_count, "Speaking Pace": pace, "Clarity Score": clarity},
        "timeline_feedback": timeline_feedback if timeline_feedback else [{"timestamp": "N/A", "type": "General", "suggestion": "No specific suggestions found."}],
        "ai_recommendations": ai_recommendations if ai_recommendations else [{"original": "N/A", "suggestion": "No specific recommendations found."}]
    }

# --- Main UI and Processing Logic ---
st.title("🖊️ LongSorn AI Demo")
st.caption("เครื่องมือสาธิตการทำงานของ AI Pipeline ที่มี UI ใกล้เคียงกับผลิตภัณฑ์จริง")
st.divider()

if 'results_ready' in st.session_state and st.session_state.results_ready:
    # --- แสดงหน้าผลลัพธ์ ---
    st.header("AI Analysis Results")
    st.write("Here's what our AI discovered about your presentation")
    
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
            st.metric("Clarity Score", f"{analysis['Clarity Score']:.1f} / 10")
        
        st.subheader("AI Recommendations")
        with st.container(border=True):
            for rec in nlp_res["ai_recommendations"]:
                if rec['original'] != "N/A":
                    st.write("**Original:**")
                    st.error(f"_{rec['original']}_")
                    st.write("**Suggestion:**")
                    st.success(f"_{rec['suggestion']}_")
                    st.divider()
                else:
                    st.write(rec['suggestion'])

        st.subheader("Transcript & Word Timestamps")
        with st.expander("คลิกเพื่อดู Transcript และข้อมูลเวลาของแต่ละคำ"):
            st.dataframe(st.session_state.word_timestamps)

    if st.button("Analyze Another"):
        st.session_state.clear()
        st.rerun()

elif 'analysis_triggered' in st.session_state and st.session_state.analysis_triggered:
    # --- แสดงหน้ากำลังประมวลผล ---
    with st.container(border=True):
        st.subheader("กำลังประมวลผล")
        progress_bar = st.progress(0, text="Starting...")
        
        progress_bar.progress(10, text="กำลังแปลงไฟล์เสียง...")
        converted_audio, ffmpeg_error = convert_audio_with_ffmpeg(st.session_state.uploaded_file_content)
        if ffmpeg_error: st.error(f"FFmpeg Error: {ffmpeg_error}"); st.stop()

        progress_bar.progress(40, text="กำลังแปลงเสียงเป็นข้อความ (STT)...")
        stt_response, stt_error = run_stt_transcription(converted_audio)
        if stt_error: st.error(f"STT Error: {stt_error}"); st.stop()
        
        full_transcript = " ".join([res.alternatives[0].transcript for res in stt_response.results if res.alternatives])
        word_timestamps = []
        for result in stt_response.results:
            for word_info in result.alternatives[0].words:
                word_timestamps.append({"Word": word_info.word, "Start (s)": f"{word_info.start_time.total_seconds():.2f}"})
        st.session_state.word_timestamps = word_timestamps

        progress_bar.progress(70, text="กำลังวิเคราะห์ด้วยโมเดลภาษา (NLP)...")
        nlp_results = run_real_nlp_analysis(full_transcript, word_timestamps, st.session_state.get("user_description", ""))
        st.session_state.nlp_results = nlp_results
        
        progress_bar.progress(100, text="การวิเคราะห์เสร็จสิ้น!")
        time.sleep(1)
        
        st.session_state.analysis_triggered = False
        st.session_state.results_ready = True
        st.rerun()

else:
    # --- แสดงหน้าอัปโหลด ---
    with st.container(border=True):
        st.header("Upload Your Content")
        
        # --- ช่องใส่ Description ที่เพิ่มเข้ามา ---
        st.subheader("1. (Optional) Provide context for AI")
        st.text_area(
            "บอก AI ว่าการสอนนี้เกี่ยวกับอะไร หรืออยากให้เน้นเรื่องไหนเป็นพิเศษ",
            key="user_description",
            placeholder="เช่น: นี่คือการสอนเรื่องการตลาดสำหรับผู้เริ่มต้น, อยากให้ช่วยดูการใช้ศัพท์เทคนิค"
        )
        
        st.subheader("2. Upload your file")
        uploaded_file = st.file_uploader(
            "Click to upload or drag and drop",
            type=["mp4", "avi", "mov", "mp3", "wav", "m4a"],
            label_visibility="collapsed"
        )

        if uploaded_file:
            if uploaded_file.size / (1024 * 1024) > 100:
                st.error("ไฟล์มีขนาดใหญ่เกิน 100MB กรุณาเลือกไฟล์ใหม่")
            else:
                st.info(f"Selected File: **{uploaded_file.name}**")
                if st.button("Upload & Analyze", type="primary", use_container_width=True):
                    st.session_state.analysis_triggered = True
                    st.session_state.uploaded_file_content = uploaded_file.getvalue()
                    st.rerun()