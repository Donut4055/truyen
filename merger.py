import os
import re
import zipfile
import uuid
import datetime
from typing import List, Dict, Tuple

# Natural sort for chapters (chap1, chap2, ..., chap10)
def natural_sort_key(s: str):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]


def get_chapter_title_from_file(file_path: str, default_index: int = 1) -> Tuple[str, str]:
    """
    Đọc file chương và trích xuất tiêu đề chương (dòng đầu tiên nếu hợp lý) cùng nội dung.
    """
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read().strip()
    
    filename_base = os.path.splitext(os.path.basename(file_path))[0]
    filename_clean = filename_base.replace("_VIET", "").replace("_vietnamese", "")
    
    # Chuẩn hóa tên chương
    title = filename_clean
    # Nếu dòng đầu ngắn và giống tiêu đề thì có thể dùng làm tên chương
    lines = [line.strip() for line in content.split("\n") if line.strip()]
    if lines and len(lines[0]) < 80 and any(kw in lines[0].lower() for kw in ["chương", "chap", "hồi", "phần", "tiết", "tập"]):
        title = lines[0]
    else:
        title = f"Chương {default_index}: {filename_clean}"
        
    return title, content


def merge_to_txt(file_paths: List[str], output_path: str, novel_title: str = "Tuyển Tập Truyện Dịch") -> str:
    """Ghép danh sách các file chương thành 1 file TXT duy nhất."""
    sorted_files = sorted(file_paths, key=natural_sort_key)
    full_text_parts = [f"═══════════════════════════════════════════════════════════════\n   {novel_title.upper()}\n═══════════════════════════════════════════════════════════════\n"]

    for idx, fpath in enumerate(sorted_files, 1):
        title, content = get_chapter_title_from_file(fpath, default_index=idx)
        full_text_parts.append(f"\n\n{'═'*50}\n📖 {title.upper()}\n{'═'*50}\n\n{content}\n")

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(full_text_parts))

    return output_path


import html

def merge_to_epub(
    file_paths: List[str],
    output_path: str,
    novel_title: str = "Tuyển Tập Truyện Dịch",
    author: str = "AI Story Translator"
) -> str:
    """
    Tạo file EPUB chuẩn tương thích Kindle, Kobo, Apple Books, Android/iOS Moon+ Reader.
    Sử dụng zipfile thuần, không phụ thuộc thư viện bên ngoài.
    """
    sorted_files = sorted(file_paths, key=natural_sort_key)
    book_id = str(uuid.uuid4())
    date_str = datetime.date.today().isoformat()
    safe_novel_title = html.escape(novel_title)
    safe_author = html.escape(author)
    
    # Danh sách các chương
    chapters = []
    for idx, fpath in enumerate(sorted_files, 1):
        title, content = get_chapter_title_from_file(fpath, default_index=idx)
        safe_title = html.escape(title)
        
        # Chuyển text thành các thẻ <p>...</p> HTML
        paragraphs = []
        for p in content.split("\n"):
            p_clean = p.strip()
            if p_clean:
                paragraphs.append(f"<p>{html.escape(p_clean)}</p>")
            else:
                paragraphs.append("<p class='empty-line'>&#160;</p>")
        body_html = "\n".join(paragraphs)
        chapters.append({
            "id": f"chap_{idx}",
            "filename": f"chapter_{idx}.xhtml",
            "title": safe_title,
            "html": body_html
        })

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as epub:
        # 1. Mimetype (phải là file đầu tiên và không nén)
        epub.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)

        # 2. META-INF/container.xml
        container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>"""
        epub.writestr("META-INF/container.xml", container_xml)

        # 3. CSS Style
        style_css = """@charset "utf-8";
body {
    font-family: serif, "Times New Roman", "DejaVu Serif";
    margin: 5%;
    line-height: 1.6;
    text-align: justify;
}
h1, h2 {
    text-align: center;
    color: #2c3e50;
    margin-top: 1.5em;
    margin-bottom: 1em;
}
p {
    text-indent: 1.5em;
    margin-top: 0.3em;
    margin-bottom: 0.3em;
}
.empty-line {
    text-indent: 0;
    margin: 0.5em 0;
}
"""
        epub.writestr("OEBPS/style.css", style_css)

        # 4. Từng file chương XHTML
        for ch in chapters:
            ch_content = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="vi">
<head>
    <title>{ch['title']}</title>
    <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
    <h2>{ch['title']}</h2>
    {ch['html']}
</body>
</html>"""
            epub.writestr(f"OEBPS/{ch['filename']}", ch_content.encode("utf-8"))

        # 5. content.opf (Manifest, Spine, Metadata)
        manifest_items = [
            '<item id="style" href="style.css" media-type="text/css"/>',
            '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>'
        ]
        spine_items = []
        for ch in chapters:
            manifest_items.append(f'<item id="{ch["id"]}" href="{ch["filename"]}" media-type="application/xhtml+xml"/>')
            spine_items.append(f'<itemref idref="{ch["id"]}"/>')

        content_opf = f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookId" version="2.0">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
        <dc:title>{safe_novel_title}</dc:title>
        <dc:creator>{safe_author}</dc:creator>
        <dc:language>vi</dc:language>
        <dc:identifier id="BookId">urn:uuid:{book_id}</dc:identifier>
        <dc:date>{date_str}</dc:date>
    </metadata>
    <manifest>
        {''.join(manifest_items)}
    </manifest>
    <spine toc="ncx">
        {''.join(spine_items)}
    </spine>
</package>"""
        epub.writestr("OEBPS/content.opf", content_opf.encode("utf-8"))

        # 6. toc.ncx (Table of Contents cho máy đọc sách)
        nav_points = []
        for idx, ch in enumerate(chapters, 1):
            nav_points.append(f"""
        <navPoint id="navpoint-{idx}" playOrder="{idx}">
            <navLabel><text>{ch['title']}</text></navLabel>
            <content src="{ch['filename']}"/>
        </navPoint>""")

        toc_ncx = f"""<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
    <head>
        <meta name="dtb:uid" content="urn:uuid:{book_id}"/>
        <meta name="dtb:depth" content="1"/>
        <meta name="dtb:totalPageCount" content="0"/>
        <meta name="dtb:maxPageNumber" content="0"/>
    </head>
    <docTitle><text>{safe_novel_title}</text></docTitle>
    <navMap>
        {''.join(nav_points)}
    </navMap>
</ncx>"""
        epub.writestr("OEBPS/toc.ncx", toc_ncx.encode("utf-8"))

    return output_path


def merge_to_pdf(
    file_paths: List[str],
    output_path: str,
    novel_title: str = "Tuyển Tập Truyện Dịch",
    author: str = "AI Story Translator"
) -> str:
    """Tạo file PDF chuẩn tiếng Việt với ReportLab và ngắt trang theo chương."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
        from reportlab.lib import colors
    except ImportError:
        raise RuntimeError("Chưa cài đặt thư viện reportlab! Hãy chạy: pip install reportlab")

    # Đăng ký font tiếng Việt từ hệ thống Windows
    font_registered = False
    for font_path in [r"C:\Windows\Fonts\times.ttf", r"C:\Windows\Fonts\arial.ttf"]:
        if os.path.exists(font_path):
            font_name = "TimesVN" if "times" in font_path.lower() else "ArialVN"
            pdfmetrics.registerFont(TTFont(font_name, font_path))
            # Đăng ký font đậm nếu có
            bold_path = font_path.replace(".ttf", "bd.ttf")
            if os.path.exists(bold_path):
                pdfmetrics.registerFont(TTFont(f"{font_name}-Bold", bold_path))
            else:
                pdfmetrics.registerFont(TTFont(f"{font_name}-Bold", font_path))
            font_registered = True
            main_font = font_name
            bold_font = f"{font_name}-Bold"
            break

    if not font_registered:
        main_font = "Helvetica"
        bold_font = "Helvetica-Bold"

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=50,
        bottomMargin=50
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name="BookTitle",
        fontName=bold_font,
        fontSize=24,
        leading=28,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#1a365d"),
        spaceAfter=15
    )
    author_style = ParagraphStyle(
        name="BookAuthor",
        fontName=main_font,
        fontSize=12,
        leading=16,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#718096"),
        spaceAfter=30
    )
    chapter_style = ParagraphStyle(
        name="ChapTitle",
        fontName=bold_font,
        fontSize=16,
        leading=20,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#2b6cb0"),
        spaceBefore=15,
        spaceAfter=15
    )
    body_style = ParagraphStyle(
        name="NovelBody",
        fontName=main_font,
        fontSize=11,
        leading=16,
        alignment=TA_JUSTIFY,
        firstLineIndent=20,
        spaceAfter=4
    )

    story = []
    # Trang bìa / Tiêu đề
    story.append(Spacer(1, 100))
    story.append(Paragraph(novel_title, title_style))
    story.append(Paragraph(f"Tác giả: {author}", author_style))
    story.append(Spacer(1, 40))
    story.append(PageBreak())

    sorted_files = sorted(file_paths, key=natural_sort_key)
    for idx, fpath in enumerate(sorted_files, 1):
        title, content = get_chapter_title_from_file(fpath, default_index=idx)
        story.append(Paragraph(title, chapter_style))
        story.append(Spacer(1, 10))

        for line in content.split("\n"):
            line_clean = line.strip()
            if line_clean:
                line_safe = (line_clean.replace("&", "&amp;")
                                       .replace("<", "&lt;")
                                       .replace(">", "&gt;"))
                story.append(Paragraph(line_safe, body_style))
            else:
                story.append(Spacer(1, 4))
        
        if idx < len(sorted_files):
            story.append(PageBreak())

    doc.build(story)
    return output_path
