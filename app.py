import base64
import os, json

import streamlit as st
from PIL import Image

from guide_builder import build_guide, split_front_matter
from pdf_generator import PDFGenerator, hex_to_rgb, safe_filename

HERE = os.path.dirname(os.path.abspath(__file__))
DRAFT_DIR = os.environ.get("PDF_CREATOR_DRAFTS", os.path.join(HERE, "drafts"))
SAMPLE_GUIDE = os.path.join(HERE, "guides", "claude-code-starter.md")

# Function to load data from JSON file
def load_language_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data

def get_text(lang):
    try:
        file_path = os.path.join(HERE, 'data', 'languages.json')
        data = load_language_data(file_path)
        # Return the specific text based on language and key
        return data[lang]

    except Exception as e:
        # Return a default message
        return f"Error {e} occured in loading {lang} language."

# Dil Seçimi
st.sidebar.title("Dil Seçimi / Language Selection")
lang = st.sidebar.selectbox("Dilinizi Seçin / Select Your Language", ["Türkçe", "English"])

# Seçilen dile göre metinleri al. Every label on every page comes from here.
text = get_text(lang)
if isinstance(text, str):
    st.error(text)
    st.stop()
ui = text["ui"]

# The dark theme is set in .streamlit/config.toml; headings keep their sky blue.
st.markdown(
    """
    <style>
    h1, h2, h3, h4, h5, h6 {
        color: #87CEEB;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# İletişim Sayfası Fonksiyonu
def contact_page():
    st.title(text["contact_title"])
    st.write(text["contact_description"])

    # Profil fotoğrafını gösterme
    developer_photo = os.path.join(HERE, text["developer_photo"])
    if text["developer_photo"] and os.path.exists(developer_photo):
        st.image(developer_photo, width=200)
    else:
        st.write(ui["photo_missing"])

# Otomatik Kaydetme ve Taslak Yönetimi
def draft_path(draft_name):
    return os.path.join(DRAFT_DIR, safe_filename(draft_name, "draft")[:-4] + ".txt")

def auto_save_draft(content, draft_name="draft"):
    """Saves the content box when it changed. Returns True when it wrote the file."""
    if not content.strip() or st.session_state.get("saved_draft") == content:
        return False
    os.makedirs(DRAFT_DIR, exist_ok=True)
    with open(draft_path(draft_name), "w", encoding="utf-8") as f:
        f.write(content)
    st.session_state["saved_draft"] = content
    return True

def restore_draft(path):
    with open(path, encoding="utf-8") as f:
        st.session_state["pdf_content"] = f.read()
    st.session_state["saved_draft"] = st.session_state["pdf_content"]

# PDF Önizleme fonksiyonu
def show_pdf(pdf_bytes):
    base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="900" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

def pdf_creator_page():
    st.title(text["pdf_creator"])
    st.write(text["pdf_creator_details"])

    # Otomatik kaydetme ve çoklu sayfa desteği
    document_name = st.text_input(ui["document_name"], key="document_name")
    saved = draft_path(document_name or "draft")
    if not st.session_state.get("pdf_content") and os.path.exists(saved):
        st.info(ui["draft_found"])
        st.button(ui["draft_restore"], on_click=restore_draft, args=(saved,))
    content = st.text_area(ui["pdf_content"], key="pdf_content", height=160)
    if auto_save_draft(content, document_name or "draft"):
        st.caption(ui["draft_saved"])

    # Yazı tipi ve boyutu seçimi
    font_name = st.selectbox(ui["font"], ["DejaVu"])
    font_size = st.slider(ui["font_size"], 8, 24, 12)
    styles = {ui["style_normal"]: "", ui["style_bold"]: "B", ui["style_italic"]: "I"}
    font_style = styles[st.selectbox(ui["font_style"], list(styles))]
    # Black by default: the old white default made every first PDF look blank.
    text_color = hex_to_rgb(st.color_picker(ui["text_color"], "#000000"))

    # Kullanıcıdan birden fazla metin girişi al
    text_entry_count = st.number_input(ui["entry_count"], min_value=0, max_value=10, value=3)
    text_entries = [st.text_input(ui["entry"].format(n=i + 1), key=f"entry_{i}") for i in range(text_entry_count)]

    # Görsel yükleme
    image_file = st.file_uploader(ui["image_upload"], type=["jpg", "jpeg", "png"])
    img_width = st.slider(ui["image_width"], 10, 190, 100)
    img_x = st.slider(ui["image_x"], 0, 190, 10)

    # Tablo ekleme
    st.write(ui["table_intro"])
    cols = st.columns(3)
    data = [[cols[c].text_input(ui["cell"].format(row=r + 1, col=c + 1), key=f"cell_{r}_{c}") for c in range(3)]
            for r in range(3)]
    table_style = st.selectbox(ui["table_style"], [ui["border"], ui["no_border"]])

    # PDF oluşturma butonu
    if st.button(ui["create_pdf"]):
        if content.strip() or any(entry.strip() for entry in text_entries):
            pdf_gen = PDFGenerator()
            if document_name.strip():
                pdf_gen.add_title(document_name.strip(), text_color=text_color)

            # Metin ekleme: the big content box first, then the extra lines
            if content.strip():
                pdf_gen.add_text(content, font_name, font_size, font_style, text_color)
                pdf_gen.ln(2)
            pdf_gen.add_multiple_texts(text_entries, font_name, font_size, font_style, text_color)

            # Görseli PDF'ye ekle
            if image_file is not None:
                pdf_gen.add_image(Image.open(image_file), x=img_x, w=img_width)

            # Tabloyu PDF'ye ekle: only when a cell has something in it
            pdf_gen.add_table(data, [40, 40, 40], border=table_style == ui["border"], text_color=text_color)

            # PDF'yi oluştur ve önizleme. It stays in memory, so two people never share one file.
            pdf_bytes = pdf_gen.to_bytes()
            st.success(ui["created"])
            show_pdf(pdf_bytes)

            # İndirme düğmesi
            st.download_button(
                label=ui["download"],
                data=pdf_bytes,
                file_name=safe_filename(document_name),
                mime="application/pdf"
            )
        else:
            st.warning(ui["need_text"])

def guide_builder_page():
    st.title(text["guide_builder"])
    st.write(text["guide_builder_details"])

    if st.button(ui["load_sample"]):
        with open(SAMPLE_GUIDE, encoding="utf-8") as f:
            st.session_state["guide_md"] = f.read()
    markdown = st.text_area(ui["markdown"], key="guide_md", height=360)
    page_size = st.selectbox(ui["page_size"], ["A5", "A4", "Letter"])

    if st.button(ui["build_guide"]):
        if markdown.strip():
            pdf_bytes, pages = build_guide(markdown, page_size=page_size, base_dir=os.path.dirname(SAMPLE_GUIDE))
            st.success(ui["guide_ready"].format(pages=pages))
            show_pdf(pdf_bytes)
            title = split_front_matter(markdown)[0].get("title", "guide").replace("|", " ")
            st.download_button(
                label=ui["download_guide"],
                data=pdf_bytes,
                file_name=safe_filename(title, "guide"),
                mime="application/pdf"
            )
        else:
            st.warning(ui["need_markdown"])

# Streamlit arayüzü
def main():
    # Menü Yapısı
    menu = [text["project_title"], text["pdf_creator"], text["guide_builder"], text["system_info_title"],
            text["feedback"], text["contact_title"]]
    choice = st.sidebar.selectbox(ui["menu"], menu)

    if choice == text["project_title"]:
        st.title(text["project_title"])
        st.subheader(text["project_goal"])
        st.write(text["project_details"])

    elif choice == text["pdf_creator"]:
        pdf_creator_page()

    elif choice == text["guide_builder"]:
        guide_builder_page()

    elif choice == text["system_info_title"]:
        st.title(text["system_info_title"])
        st.write(text["system_info_details"])

    elif choice == text["feedback"]:
        st.title(text["feedback"])
        st.write(text["feedback_description"])
        for question in text["feedback_questions"]:
            feedback_response = st.radio(question, ui["feedback_options"])
            st.write(ui["feedback_answer"].format(question=question, answer=feedback_response))

    elif choice == text["contact_title"]:
        contact_page()  # İletişim sayfasını göster

if __name__ == "__main__":
    main()
