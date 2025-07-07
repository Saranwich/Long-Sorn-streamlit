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
from collections import Counter

# --- Page Configuration & ENV Loading ---
st.set_page_config(page_title="LongSorn AI Demo", page_icon="🖊️", layout="wide")
load_dotenv()

# --- Backend Functions (AI Calls) ---
def get_audio_duration(file_path):
    """ใช้ ffprobe เพื่อหาความยาวของไฟล์เสียง/วิดีโอ"""
    command = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        return float(result.stdout.strip())
    except Exception as e:
        st.warning(f"Could not get audio duration: {e}")
        return 0

def convert_audio_with_ffmpeg(input_bytes, suffix, trim_duration=None):
    """ใช้ FFmpeg เพื่อแปลงไฟล์ที่รับเข้ามาให้เป็นรูปแบบ WAV และจำกัดความยาว"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_in:
            temp_in.write(input_bytes)
            input_filename = temp_in.name
        
        output_filename = input_filename + ".wav"
        command = ["ffmpeg", "-i", input_filename, "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", "-y"]
        if trim_duration:
            command.extend(["-t", str(trim_duration)])
        command.append(output_filename)

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
def run_stt_transcription(audio_file_content, language_code="th-TH"):
    """ฟังก์ชันสำหรับเรียกใช้ Google STT API จริง (สำหรับไฟล์สั้น < 1 นาที)"""
    try:
        client = speech.SpeechClient()
        audio = speech.RecognitionAudio(content=audio_file_content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code=language_code,
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
    clean_phrase = phrase.replace("...", "").strip()
    words_in_phrase = clean_phrase.lower().split()
    if not words_in_phrase: return "N/A"
    for i in range(len(word_timestamps) - len(words_in_phrase) + 1):
        match = True
        for j in range(len(words_in_phrase)):
            if word_timestamps[i+j]['Word'].lower() != words_in_phrase[j]:
                match = False; break
        if match:
            start_seconds = float(word_timestamps[i]['Start (s)'])
            minutes = int(start_seconds // 60); seconds = int(start_seconds % 60)
            return f"{minutes:01d}:{seconds:02d}"
    return "N/A"

def run_real_nlp_analysis(transcript: str, word_timestamps: list, description: str, lang_code_for_stt: str):
    """ฟังก์ชันสำหรับเรียกใช้ Gemini และ Typhoon API เพื่อวิเคราะห์ Transcript จริง"""
    context_prompt = f"User's context for this presentation: {description}\n\n" if description else ""
    
    word_count = len(word_timestamps)
    duration_seconds = float(word_timestamps[-1]['Start (s)']) if word_timestamps else 0
    wpm = (word_count / duration_seconds) * 60 if duration_seconds > 0 else 0
    
    # ---- Language Handling ----
    # ใช้รหัสภาษาที่ส่งมาจากขั้นตอน STT (เช่น "th-TH" -> "th")
    detected_language = lang_code_for_stt.split('-')[0].lower()

    # ---- Gemini Analysis ----
    gemini_feedback = "Not available"
    try:
        genai.configure(api_key=os.getenv("GOOGLE_GEMINI_API_KEY"))
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        if "th" in detected_language:
            prompt = f"""
            {context_prompt}You are an expert teaching coach. Analyze the following teaching transcript in Thai. The speaker's pace is approximately {wpm:.0f} words per minute.
            Transcript: "{transcript}"
            
            1. Provide a Clarity Score (1-10), where 1 is very unclear and 10 is perfectly clear. Base the score on sentence structure, word choice, and conciseness. Use this exact format:
            Clarity: [Your Score]
            
            2. Identify up to 5 specific Thai phrases that could be improved. You MUST find at least 3 points of improvement, even if the transcript is good. If there are no clear errors, suggest ways to make good sentences even better or more impactful. For each, provide the original phrase, a brief reason, and a suggestion for improvement. Use this exact format, with each entry on a new line:
            ORIGINAL: [original phrase] | REASON: [reason for improvement] | SUGGESTION: [suggested alternative]
            
            3. Extract up to 5 main keywords or topics from the transcript based on frequency and relevance. Use this exact format:
            KEYWORDS: [keyword1, keyword2, keyword3]
            """
        else: # English or other languages
            prompt = f"""
            {context_prompt}You are an expert public speaking coach. Analyze the following transcript in English. The speaker's pace is approximately {wpm:.0f} words per minute.
            Transcript: "{transcript}"

            1. Provide a Clarity Score (1-10). Use this format:
            Clarity: [Your Score]

            2. Identify up to 5 specific phrases that could be improved. You MUST find at least 3 points of improvement. For each, provide the original phrase, a brief reason, and a suggestion. Use this format:
            ORIGINAL: [original phrase] | REASON: [reason for improvement] | SUGGESTION: [suggested alternative]

            3. Extract up to 5 main keywords. Use this format:
            KEYWORDS: [keyword1, keyword2, keyword3]
            """
            
        response = model.generate_content(prompt)
        gemini_feedback = response.text
    except Exception as e:
        st.warning(f"Could not connect to Gemini API: {e}")

    # ---- Typhoon API Analysis (Only for Thai) ----
    filler_word_count = 0
    if "th" in detected_language:
        try:
            api_url = os.getenv("TYPHOON_API_URL")
            api_key = os.getenv("TYPHOON_API_KEY")
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            payload = {"model": "typhoon-v2.1-12b-instruct", "messages": [{"role": "user", "content": f"จากข้อความภาษาไทยต่อไปนี้: \"{transcript}\" ช่วยนับจำนวนคำฟุ่มเฟือย (เช่น เอ่อ, อ่า, แบบว่า, คือว่า, นะครับ) ว่ามีทั้งหมดกี่คำ ตอบเป็นตัวเลขเท่านั้น"}], "max_tokens": 10}
            response = requests.post(api_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            response_json = response.json()
            raw_response = response_json.get("choices", [{}])[0].get("message", {}).get("content", "0")
            filler_word_count = int("".join(filter(str.isdigit, raw_response)))
        except Exception as e:
            st.warning(f"Could not connect to Typhoon API: {e}")
    else:
        # Simple filler word count for English
        english_fillers = ['um', 'uh', 'er', 'ah', 'like', 'actually', 'basically', 'so', 'you know']
        words = transcript.lower().split()
        filler_word_count = sum(1 for word in words if word in english_fillers)


    # ---- Combine and Process Results ----
    clarity = 0.0
    keywords = []
    timeline_feedback = []
    ai_recommendations = []
    
    if wpm < 110: pace = "Too slow"
    elif wpm > 160: pace = "Too fast"
    else: pace = "Good"

    for line in gemini_feedback.splitlines():
        if "Clarity:" in line:
            try: clarity = float(line.split("Clarity:")[1].strip())
            except: clarity = 0.0
        elif "KEYWORDS:" in line:
            keywords_str = line.split("KEYWORDS:")[1].strip().replace('[', '').replace(']', '')
            keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]
        elif "ORIGINAL:" in line:
            parts = [p.strip() for p in line.split('|')]
            if len(parts) == 3:
                original = parts[0].replace("ORIGINAL:", "").strip(); reason = parts[1].replace("REASON:", "").strip(); suggestion = parts[2].replace("SUGGESTION:", "").strip()
                ai_recommendations.append({"original": original, "suggestion": suggestion})
                timestamp = find_timestamp_for_phrase(original, word_timestamps)
                timeline_feedback.append({"timestamp": timestamp, "type": reason, "suggestion": suggestion})

    return {
        "speech_analysis": {"Filler Words Detected": filler_word_count, "Speaking Pace": pace, "Clarity Score": clarity},
        "keywords": keywords,
        "timeline_feedback": timeline_feedback,
        "ai_recommendations": ai_recommendations
    }

# --- Main UI and Processing Logic ---
st.title("🖊️ LongSorn AI Demo")
st.caption("เครื่องมือสาธิตการทำงานของ AI รีวิวการสอนที่มี UI ใกล้เคียงกับผลิตภัณฑ์จริง")
st.divider()

if 'results_ready' in st.session_state and st.session_state.results_ready:
    # --- UI: แสดงหน้าผลลัพธ์ ---
    st.header("AI Analysis Results")
    if st.session_state.get("is_trimmed", False):
        st.warning("⚠️ ไฟล์ของคุณมีความยาวเกิน 1 นาที ระบบได้ทำการวิเคราะห์เฉพาะ 60 วินาทีแรกเท่านั้น หากต้องการวิเคราะห์ไฟล์เต็ม กรุณาอัปเกรดแพ็กเกจ")

    nlp_res = st.session_state.nlp_results
    
    left_col, right_col = st.columns(2, gap="large")

    with left_col:
        st.subheader("Video Playback")
        st.video(st.session_state.uploaded_file_content)
        
        st.subheader("Timeline Feedback")
        if nlp_res["timeline_feedback"]:
            for feedback in nlp_res["timeline_feedback"]:
                with st.container(border=True):
                    r1_col1, r1_col2 = st.columns([1, 4])
                    with r1_col1: st.write(f"**{feedback['timestamp']}**")
                    with r1_col2: st.write(f"**{feedback['type']}**")
                    st.info(f"**Suggestion:** {feedback['suggestion']}")

    with right_col:
        st.subheader("Speech Analysis")
        with st.container(border=True):
            analysis = nlp_res["speech_analysis"]
            st.metric("Filler Words Detected", f"{analysis['Filler Words Detected']} times")
            st.metric("Speaking Pace", analysis['Speaking Pace'])
            st.metric("Clarity Score", f"{analysis['Clarity Score']:.1f} / 10")
        
        st.subheader("Content Analysis")
        with st.container(border=True):
            st.write("**Main Keywords:**")
            if nlp_res["keywords"]:
                st.text(", ".join(nlp_res["keywords"]))
    
        st.subheader("AI Recommendations")
        with st.container(border=True):
            if nlp_res["ai_recommendations"]:
                for rec in nlp_res["ai_recommendations"]:
                    st.error(f"**Original:** \"_{rec['original']}_\"")
                    st.success(f"**Suggestion:** \"_{rec['suggestion']}_\"")
                    st.divider()

    if st.button("Analyze Another"): st.session_state.clear(); st.rerun()

elif 'analysis_triggered' in st.session_state and st.session_state.analysis_triggered:
    # --- UI: แสดงหน้ากำลังประมวลผล ---
    with st.container(border=True):
        st.subheader("กำลังประมวลผล...")
        progress_bar = st.progress(0, text="Starting...")
        
        progress_bar.progress(10, text="กำลังตรวจสอบและแปลงไฟล์เสียง...")
        file_suffix = os.path.splitext(st.session_state.file_name)[1]
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_suffix) as temp_in:
            temp_in.write(st.session_state.uploaded_file_content); input_filename = temp_in.name
        
        duration = get_audio_duration(input_filename)
        is_trimmed = duration > 60
        st.session_state.is_trimmed = is_trimmed
        os.remove(input_filename)

        trim_duration = 60 if is_trimmed else None
        if is_trimmed: progress_bar.progress(20, text="ไฟล์ยาวเกิน 1 นาที กำลังตัดให้เหลือ 60 วินาที...")
        
        converted_audio, ffmpeg_error = convert_audio_with_ffmpeg(st.session_state.uploaded_file_content, file_suffix, trim_duration)
        if ffmpeg_error: st.error(f"FFmpeg Error: {ffmpeg_error}"); st.stop()
        
        # --- Language Detection Step ---
        progress_bar.progress(30, text="กำลังตรวจสอบภาษา...")
        # A simple heuristic for language detection
        lang_code_for_stt = "th-TH" # Default to Thai
        if st.session_state.get("user_description", "").lower().strip() == "english":
             lang_code_for_stt = "en-US"

        progress_bar.progress(40, text=f"กำลังแปลงเสียงเป็นข้อความ... ({lang_code_for_stt})...")
        stt_response, stt_error = run_stt_transcription(converted_audio, lang_code_for_stt)
        if stt_error: st.error(f"STT Error: {stt_error}"); st.stop()
        
        full_transcript = " ".join([res.alternatives[0].transcript for res in stt_response.results if res.alternatives])
        word_timestamps = []
        for result in stt_response.results:
            for word_info in result.alternatives[0].words:
                word_timestamps.append({"Word": word_info.word, "Start (s)": f"{word_info.start_time.total_seconds():.2f}"})
        st.session_state.word_timestamps_df = pd.DataFrame(word_timestamps)

        progress_bar.progress(70, text="กำลังวิเคราะห์ด้วยโมเดลภาษา...")
        nlp_results = run_real_nlp_analysis(full_transcript, word_timestamps, st.session_state.get("user_description", ""), lang_code_for_stt)
        st.session_state.nlp_results = nlp_results
        
        progress_bar.progress(100, text="การวิเคราะห์เสร็จสิ้น!")
        time.sleep(1)
        
        st.session_state.analysis_triggered = False
        st.session_state.results_ready = True
        st.rerun()

else:
    # --- UI: แสดงหน้าอัปโหลด ---
    with st.container(border=True):
        st.header("Upload Your Content")
        st.subheader("Provide context for AI")
        st.text_area("บอก AI ว่าการสอนนี้เกี่ยวกับอะไร หรืออยากให้เน้นเรื่องไหนเป็นพิเศษ (หากเป็นภาษาอังกฤษ ให้พิมพ์ 'english' ที่นี่)", key="user_description", placeholder="e.g. นี่คือการสอนเรื่องการตลาดสำหรับผู้เริ่มต้น, ช่วยวิเคราะห์การใช้ศัพท์เทคนิค")
        
        st.subheader("Upload your file")
        uploaded_file = st.file_uploader("Click to upload or drag and drop", type=["mp4", "mov", "mp3", "wav", "m4a"], label_visibility="collapsed")

        if uploaded_file:
            st.info(f"Selected File: **{uploaded_file.name}**")
            if st.button("Upload & Analyze", type="primary", use_container_width=True):
                st.session_state.analysis_triggered = True
                st.session_state.uploaded_file_content = uploaded_file.getvalue()
                st.session_state.file_name = uploaded_file.name
                st.rerun()