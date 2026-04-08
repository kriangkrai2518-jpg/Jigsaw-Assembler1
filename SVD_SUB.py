import streamlit as st
import os
import numpy as np
import PIL.Image, PIL.ImageDraw, PIL.ImageFont
from moviepy.editor import VideoFileClip, concatenate_videoclips, ImageClip, CompositeVideoClip

# --- FIX PILLOW 10+ ANTIALIAS ---
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

# --- CONFIGURATION ---
st.set_page_config(page_title="Jigsaw Assembler Pro", layout="wide")
st.title("🎬 Jigsaw Assembler: Thai Subtitle Support")

# --- UI LAYOUT ---
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📁 Upload & Subtitles")
    uploaded_files = st.file_uploader("Add MP4 Files", type=["mp4"], accept_multiple_files=True)
    
    # ส่วนรับคำบรรยายภาษาไทยแยกแต่ละไฟล์
    custom_captions = {}
    if uploaded_files:
        st.subheader("📝 Edit Thai Captions")
        for i, file in enumerate(uploaded_files):
            custom_captions[file.name] = st.text_input(f"Subtitle for: {file.name}", f"ส่วนที่ {i+1}")

    start_btn = st.button("🚀 Start Assembly")

with col2:
    st.header("📟 Terminal Output")
    terminal_log = st.empty()
    log_content = ""

def write_to_terminal(text):
    global log_content
    log_content += text + "\n"
    terminal_log.code(log_content)

# --- THAI SUBTITLE ENGINE (PILLOW) ---
def create_subtitle_image(text, width, height):
    img = PIL.Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = PIL.ImageDraw.Draw(img)
    
    # ระบุชื่อไฟล์ฟอนต์ที่คุณอัปโหลดขึ้น GitHub (เช่น Kanit-Bold.ttf)
    font_path = "Kanit-Bold.ttf" 
    
    try:
        if os.path.exists(font_path):
            font = PIL.ImageFont.truetype(font_path, 65)
        else:
            font = PIL.ImageFont.load_default()
    except:
        font = PIL.ImageFont.load_default()

    text_bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]
    
    # วาดแถบดำโปร่งแสง (Background)
    padding = 20
    bg_x0, bg_y0 = (width-tw)//2 - padding, height - 150 - padding
    bg_x1, bg_y1 = (width+tw)//2 + padding, height - 150 + th + padding
    draw.rectangle([bg_x0, bg_y0, bg_x1, bg_y1], fill=(0, 0, 0, 180))
    
    # วาดตัวอักษรภาษาไทยสีขาว
    draw.text(((width - tw) // 2, height - 150), text, font=font, fill=(255, 255, 255, 255))
    return np.array(img)

# --- MAIN PROCESSING ENGINE ---
if start_btn and uploaded_files:
    write_to_terminal("📌 เริ่มต้นระบบประกอบวิดีโอ (Thai Language Support Enabled)")
    clips = []
    temp_files = []

    try:
        for uploaded_file in uploaded_files:
            write_to_terminal(f"📥 กำลังดึงข้อมูล: {uploaded_file.name}")
            
            temp_path = f"temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            temp_files.append(temp_path)

            clip = VideoFileClip(temp_path).resize(height=1080)
            w, h = clip.size

            thai_text = custom_captions.get(uploaded_file.name, "")
            
            txt_img = create_subtitle_image(thai_text, w, h)
            txt_clip = ImageClip(txt_img).set_duration(clip.duration).set_position('center')

            combined = CompositeVideoClip([clip, txt_clip])
            clips.append(combined)
            write_to_terminal(f"✅ ใส่ซับไทย: '{thai_text}' เรียบร้อย")

        if clips:
            write_to_terminal("🎬 กำลัง Render วิดีโอรวม...")
            final = concatenate_videoclips(clips, method="compose")
            
            output_file = "Jigsaw_Result.mp4"
            final.write_videofile(output_file, fps=24, codec="libx264", audio_codec="aac")

            write_to_terminal("🎊 การประกอบวิดีโอเสร็จสมบูรณ์!")
            st.success("✅ รวมวิดีโอพร้อมซับไทยเรียบร้อย!")
            
            with open(output_file, 'rb') as v:
                st.video(v.read())
                st.download_button("📥 Download Video", data=v, file_name=output_file, mime="video/mp4")

    except Exception as e:
        write_to_terminal(f"❌ ERROR: {str(e)}")
        st.error(f"เกิดข้อผิดพลาด: {e}")

    finally:
        write_to_terminal("🧹 กำลังล้างหน่วยความจำ...")
        for c in clips:
            try: c.close()
            except: pass
        
        for f in temp_files:
            try:
                if os.path.exists(f): os.remove(f)
            except: pass
        write_to_terminal("✨ ระบบพร้อมรับงานใหม่")

else:
    if start_btn:
        st.warning("กรุณาเลือกไฟล์วิดีโอก่อนกดปุ่ม Start ครับ")
