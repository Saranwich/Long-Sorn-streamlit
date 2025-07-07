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
    ฟังก์ชันสำหรับเรียกใช้ Gemini และ Typhoon API เพื่อวิเคราะห์ Transcript จริง
    (เวอร์ชันปรับปรุง แก้ไขปัญหา Filler Words, Speaking Pace, และ Clarity Score)
    """
    context_prompt = f"User's context for this presentation: {description}\n\n" if description else ""
    
    word_count = len(word_timestamps)
    # FIXED: Ensure duration is at least 1 second to prevent division by zero for very short audio.
    duration_seconds = float(word_timestamps[-1]['Start (s)']) if word_timestamps and float(word_timestamps[-1]['Start (s)']) > 0 else 1.0
    wpm = (word_count / duration_seconds) * 60 if duration_seconds > 0 else 0
    
    # ---- Language Handling ----
    detected_language = lang_code_for_stt.split('-')[0].lower()

    # ---- Gemini Analysis (with Improved Prompting) ----
    gemini_feedback = "Not available"
    try:
        genai.configure(api_key=os.getenv("GOOGLE_GEMINI_API_KEY"))
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        clarity_prompt_rubric = """
        Analyze the following transcript. Your persona is a helpful speaking coach who understands that this is a spoken transcript, not a written essay, so you should allow for some natural speech patterns.

        1. Provide a Clarity Score (1-10) based on the following rubric. You MUST provide a brief justification for your score.
           - 1-3 (Needs Major Improvement): The message is very unclear, rambling, or hard to follow.
           - 4-6 (Needs Improvement): The message is generally understandable but contains significant awkward phrasing, poor word choice, or unclear sentence structures.
           - 7-8 (Good): The message is clear and well-structured with only minor issues. The core ideas are easy to follow.
           - 9-10 (Excellent): The message is exceptionally clear, concise, engaging, and well-articulated.
           Use this exact format:
           Clarity: [Your Score] | Justification: [Your brief reason for the score]
        """

        if "th" in detected_language:
            prompt = f"""
            {context_prompt}{clarity_prompt_rubric}
            The speaker's pace is approximately {wpm:.0f} words per minute.
            Transcript (Thai): "{transcript}"
            
            2. Identify up to 5 specific Thai phrases that could be improved. You MUST find at least 3 points of improvement, even if the transcript is good. If there are no clear errors, suggest ways to make good sentences even better or more impactful. For each, provide the original phrase, a brief reason, and a suggestion for improvement. Use this exact format, with each entry on a new line:
            ORIGINAL: [original phrase] | REASON: [reason for improvement] | SUGGESTION: [suggested alternative]
            
            3. Extract up to 5 main keywords or topics from the transcript based on frequency and relevance. Use this exact format:
            KEYWORDS: [keyword1, keyword2, keyword3]
            """
        else: # English or other languages
            # FIXED TYPO HERE
            prompt = f"""
            {context_prompt}{clarity_prompt_rubric}
            The speaker's pace is approximately {wpm:.0f} words per minute.
            Transcript (English): "{transcript}"

            2. Identify up to 5 specific phrases that could be improved. You MUST find at least 3 points of improvement. For each, provide the original phrase, a brief reason, and a suggestion. Use this format:
            ORIGINAL: [original phrase] | REASON: [reason for improvement] | SUGGESTION: [suggested alternative]

            3. Extract up to 5 main keywords. Use this format:
            KEYWORDS: [keyword1, keyword2, keyword3]
            """
            
        response = model.generate_content(prompt)
        gemini_feedback = response.text
    except Exception as e:
        st.warning(f"Could not connect to Gemini API: {e}")

    # ---- Filler Word Analysis (CHANGED: More reliable direct counting) ----
    filler_word_count = 0
    words_in_transcript = transcript.lower().split()

    if "th" in detected_language:
        # Define a list of common Thai filler words
        thai_fillers = ['เอ่อ', 'อ่า', 'คือ', 'แบบว่า', 'แบบ', 'ก็คือ', 'นะครับ', 'นะคะ', 'อะ', 'เอิ่ม', 'อืม']
        filler_word_count = sum(1 for word in words_in_transcript if word in thai_fillers)
    else:
        # Expanded list for English
        english_fillers = ['um', 'uh', 'er', 'ah', 'like', 'actually', 'basically', 'so', 'you know', 'i mean', 'right']
        filler_word_count = sum(1 for word in words_in_transcript if word in english_fillers)

    # ---- Combine and Process Results ----
    clarity = 0.0
    clarity_justification = "N/A"
    keywords = []
    timeline_feedback = []
    ai_recommendations = []
    
    # CHANGED: More nuanced speaking pace criteria
    if wpm < 100: pace = "Very Slow"
    elif wpm < 120: pace = "A bit slow"
    elif wpm <= 160: pace = "Good Pace"
    elif wpm <= 180: pace = "A bit fast"
    else: pace = "Very Fast"

    for line in gemini_feedback.splitlines():
        # CHANGED: Logic to parse the new Clarity format with justification
        if "Clarity:" in line and "Justification:" in line:
            try:
                parts = line.split('|')
                clarity_str = parts[0].replace("Clarity:", "").strip()
                clarity = float(clarity_str)
                clarity_justification = parts[1].replace("Justification:", "").strip()
            except:
                clarity = 0.0
                clarity_justification = "Could not parse score."
        elif "KEYWORDS:" in line:
            keywords_str = line.split("KEYWORDS:")[1].strip().replace('[', '').replace(']', '')
            keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]
        elif "ORIGINAL:" in line:
            parts = [p.strip() for p in line.split('|')]
            if len(parts) == 3:
                original = parts[0].replace("ORIGINAL:", "").strip()
                reason = parts[1].replace("REASON:", "").strip()
                suggestion = parts[2].replace("SUGGESTION:", "").strip()
                ai_recommendations.append({"original": original, "suggestion": suggestion})
                timestamp = find_timestamp_for_phrase(original, word_timestamps)
                timeline_feedback.append({"timestamp": timestamp, "type": reason, "suggestion": suggestion})

    return {
        "speech_analysis": {
            "Filler Words Detected": filler_word_count, 
            "Speaking Pace": pace, 
            "Clarity Score": clarity,
            "Clarity Justification": clarity_justification
        },
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
            # MODIFIED: Display the justification below the score
            st.metric("Clarity Score", f"{analysis.get('Clarity Score', 0.0):.1f} / 10", help=analysis.get('Clarity Justification', 'No justification provided.'))
        
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