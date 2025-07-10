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
    """
    ฟังก์ชันสำหรับเรียกใช้ Gemini วิเคราะห์ Transcript
    (เวอร์ชัน 4 - Upgraded with Statistical Summary & Pause Analysis)
    """
    context_prompt = f"User's context for this presentation: {description}\n\n" if description else ""
    
    # --- Pre-calculation of all statistics ---
    word_count = len(word_timestamps)
    duration_seconds = float(word_timestamps[-1]['End (s)']) if word_timestamps and float(word_timestamps[-1]['End (s)']) > 0 else 1.0
    wpm = (word_count / duration_seconds) * 60 if duration_seconds > 0 else 0
    detected_language = lang_code_for_stt.split('-')[0].lower()

    # Filler word calculation
    if "th" in detected_language:
        fillers_list = ['เอ่อ', 'อ่า', 'คือ', 'แบบว่า', 'แบบ', 'ก็คือ', 'นะครับ', 'นะคะ', 'อะ', 'เอิ่ม', 'อืม']
    else:
        fillers_list = ['um', 'uh', 'er', 'ah', 'like', 'actually', 'basically', 'so', 'you know', 'i mean', 'right']
    filler_word_count = sum(1 for word in transcript.lower().split() if word in fillers_list)

    # NEW: Pause Analysis
    long_pauses = 0
    pause_threshold = 2.0  # วินาที
    for i in range(1, len(word_timestamps)):
        pause_duration = word_timestamps[i]['Start (s)'] - word_timestamps[i-1]['End (s)']
        if pause_duration >= pause_threshold:
            long_pauses += 1
            
    # --- Construct the Data Summary for the AI ---
    data_summary = f"""
    Here is a statistical summary of the speech delivery:
    - Speaking Pace: {wpm:.0f} words per minute.
    - Filler Words Count: {filler_word_count} times.
    - Long Pauses (>{pause_threshold}s): {long_pauses} times.
    """

    # --- Create the new "Smarter" Prompt ---
    gemini_feedback = "Not available"
    try:
        genai.configure(api_key=os.getenv("GOOGLE_GEMINI_API_KEY"))
        model = genai.GenerativeModel('gemini-1.5-flash')

        # NEW: The prompt now instructs the AI to use the data summary
        smarter_prompt = f"""
        {context_prompt}
        You are an expert speech coach reviewing a presentation. Your analysis MUST be based on BOTH the provided statistical summary and the full transcript.

        {data_summary}

        Based on ALL the information above (statistics and transcript), perform the following analysis:

        1. Overall Clarity Score (1-10): Provide a score and a justification that REFERENCES the statistical data. For example, if the pace is too fast or there are many pauses, mention it as a reason for a lower score.
           - A clear, competent speaker should score 7-8. Reserve scores below 5 for speakers who are genuinely hard to follow.
           Use this exact format:
           Clarity: [Your Score] | Justification: [Your brief reason for the score, referencing the statistics]

        2. Key Improvement Suggestions: Identify up to 5 specific phrases or moments from the transcript that could be improved.
           Use this exact format, with each entry on a new line:
           ORIGINAL: [original phrase] | REASON: [reason for improvement] | SUGGESTION: [suggested alternative]

        3. Main Keywords: Extract up to 5 main keywords or topics.
           Use this exact format:
           KEYWORDS: [keyword1, keyword2, keyword3]
        """
        
        full_prompt = f"{smarter_prompt}\n\nFull Transcript:\n\"\"\"\n{transcript}\n\"\"\""
        
        response = model.generate_content(full_prompt)
        gemini_feedback = response.text
    except Exception as e:
        st.warning(f"Could not connect to Gemini API: {e}")

    # --- Parsing the results (mostly the same) ---
    clarity = 0.0
    clarity_justification = "N/A"
    keywords = []
    timeline_feedback = []
    ai_recommendations = []
    
    if wpm < 60: pace = "Very Slow"
    elif wpm < 100: pace = "Relaxed Pace"
    elif wpm <= 140: pace = "Good Conversational Pace"
    elif wpm <= 180: pace = "Energetic Pace"
    else: pace = "Very Fast"

    for line in gemini_feedback.splitlines():
        if "Clarity:" in line and "Justification:" in line:
            try:
                parts = line.split('|'); clarity_str = parts[0].replace("Clarity:", "").strip(); clarity = float(clarity_str)
                clarity_justification = parts[1].replace("Justification:", "").strip()
            except:
                clarity = 0.0; clarity_justification = "Could not parse score."
        elif "KEYWORDS:" in line:
            keywords_str = line.split("KEYWORDS:")[1].strip().replace('[', '').replace(']', ''); keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]
        elif "ORIGINAL:" in line:
            parts = [p.strip() for p in line.split('|')]
            if len(parts) == 3:
                original = parts[0].replace("ORIGINAL:", "").strip(); reason = parts[1].replace("REASON:", "").strip(); suggestion = parts[2].replace("SUGGESTION:", "").strip()
                ai_recommendations.append({"original": original, "suggestion": suggestion})
                timestamp = find_timestamp_for_phrase(original, word_timestamps)
                timeline_feedback.append({"timestamp": timestamp, "type": reason, "suggestion": suggestion})

    return {
        "speech_analysis": {
            "Filler Words Detected": filler_word_count, "Speaking Pace": pace, "Clarity Score": clarity,
            "Clarity Justification": clarity_justification, "Long Pauses": long_pauses
        },
        "keywords": keywords, "timeline_feedback": timeline_feedback, "ai_recommendations": ai_recommendations
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
            col1, col2, col3 = st.columns(3)
            col1.metric("Speaking Pace", analysis.get('Speaking Pace', 'N/A'))
            col2.metric("Filler Words", f"{analysis.get('Filler Words Detected', 0)} times")
            col3.metric("Long Pauses (>2s)", f"{analysis.get('Long Pauses', 0)} times")
            
            st.metric("Clarity Score", f"{analysis.get('Clarity Score', 0.0):.1f} / 10", help=analysis.get('Clarity Justification', 'No justification provided.'))
        
        st.subheader("Content Analysis")
        with st.container(border=True):
            st.write("**Main Keywords:**")
            if nlp_res["keywords"]:
                st.text(", ".join(nlp_res["keywords"]))
    
        st.subheader("AI Recommendations")
        if nlp_res["ai_recommendations"]:
            with st.expander("คลิกเพื่อดูคำแนะนำในการปรับปรุงประโยคทั้งหมด", expanded=True): # สามารถเปลี่ยน expanded=False ถ้าต้องการให้มันถูกซ่อนไว้ก่อน
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
        # --- NEW: Add this check for empty transcript ---
        if not full_transcript.strip():
            st.error("Error: ไม่สามารถตรวจจับคำพูดใดๆ ในไฟล์เสียงได้ กรุณาตรวจสอบไฟล์แล้วลองอีกครั้ง")
            st.stop() # Stop the execution
        word_timestamps = []
        for result in stt_response.results:
            for word_info in result.alternatives[0].words:
                word_timestamps.append({
                    "Word": word_info.word,
                    "Start (s)": word_info.start_time.total_seconds(),
                    "End (s)": word_info.end_time.total_seconds()
                })
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