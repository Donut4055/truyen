import os
import sys
import glob

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Thêm đường dẫn hiện tại vào sys.path để import
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from translator_engine import StoryTranslator
from prompts.system_prompt import STYLE_PRESETS
from merger import merge_to_txt, merge_to_epub, merge_to_pdf, natural_sort_key

INPUT_DIR = os.path.join(CURRENT_DIR, "input")
OUTPUT_DIR = os.path.join(CURRENT_DIR, "output")
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


def print_banner(translator: StoryTranslator = None):
    print("=" * 65)
    print("      📖 TOOL DỊCH TRUYỆN CHUYÊN NGHIỆP - AI NOVEL TRANSLATOR     ")
    print("   (Văn phong mượt mà - Tượng thanh/hình - Persistent Cache)    ")
    print("=" * 65)
    if translator:
        if translator.story_context_cache:
            print(f"💡 [Context Cache]: ĐANG CÓ SƠ ĐỒ NGỮ CẢNH ({len(translator.story_context_cache)} ký tự) - Sẵn sàng dịch!")
        else:
            print("💡 [Context Cache]: Chưa có dữ liệu (Sẽ tự động quét khi bắt đầu dịch).")


def select_genre() -> str:
    print("\n--- CHỌN THỂ LOẠI & VĂN PHONG DỊCH ---")
    keys = list(STYLE_PRESETS.keys())
    for idx, key in enumerate(keys, 1):
        preset = STYLE_PRESETS[key]
        print(f" [{idx}] {preset['name']}")
        print(f"     ➔ {preset['description']}")
    
    while True:
        choice = input("\nNhập số tương ứng thể loại (Mặc định: 1 - Tiên hiệp): ").strip()
        if not choice:
            return "tien_hiep"
        try:
            val = int(choice)
            if 1 <= val <= len(keys):
                return keys[val - 1]
        except ValueError:
            pass
        print("❌ Lựa chọn không hợp lệ, vui lòng chọn lại!")


def select_provider() -> str:
    print("\n--- CHỌN NHÀ CUNG CẤP AI (AI PROVIDER) ---")
    print(" [1] Gemini (Mặc định - Khuyên dùng dịch văn học & tiểu thuyết dài)")
    print(" [2] DeepSeek (DeepSeek-Chat)")
    print(" [3] Grok / OpenAI / OpenRouter")
    
    choice = input("\nNhập số (Mặc định: 1): ").strip()
    if choice == "2":
        return "deepseek"
    elif choice == "3":
        return "grok"
    return "gemini"


def ask_and_merge_outputs(translated_files: list):
    """Hỏi người dùng và thực hiện gộp các file đã dịch thành định dạng mong muốn."""
    if not translated_files:
        return

    print("\n" + "═" * 50)
    print("📦 TÙY CHỌN XUẤT BẢN & GỘP FILE SAU KHI DỊCH")
    print("═" * 50)
    print(" [1] Để nguyên các file TXT riêng lẻ trong thư mục output/")
    print(" [2] Gộp thành 1 file Ebook EPUB (.epub) đọc trên Kindle / điện thoại")
    print(" [3] Gộp thành 1 file PDF (.pdf) in ấn & đọc trang chuẩn")
    print(" [4] Gộp thành 1 file TXT (.txt) tổng hợp duy nhất")
    print(" [5] Xuất TẤT CẢ (Giữ TXT riêng + EPUB + PDF + TXT gộp)")

    choice = input("\nChọn hình thức xuất (Mặc định: 1): ").strip()
    if choice not in ["2", "3", "4", "5"]:
        print("✅ Đã lưu các file TXT riêng lẻ trong thư mục output/.")
        return

    book_title = input("\nNhập tên truyện / tác phẩm (VD: Dau Pha Thuong Khung): ").strip() or "Truyen_Dich_Tong_Hop"
    author_name = input("Nhập tên tác giả / dịch giả (Enter để bỏ qua): ").strip() or "AI Story Translator"

    safe_title = "".join(c for c in book_title if c.isalnum() or c in ("-", "_", " ")).strip().replace(" ", "_")

    if choice in ["2", "5"]:
        epub_path = os.path.join(OUTPUT_DIR, f"{safe_title}.epub")
        try:
            merge_to_epub(translated_files, epub_path, novel_title=book_title, author=author_name)
            print(f"🎉 Đã xuất Ebook EPUB: {epub_path}")
        except Exception as e:
            print(f"❌ Lỗi xuất EPUB: {e}")

    if choice in ["3", "5"]:
        pdf_path = os.path.join(OUTPUT_DIR, f"{safe_title}.pdf")
        try:
            merge_to_pdf(translated_files, pdf_path, novel_title=book_title, author=author_name)
            print(f"🎉 Đã xuất file PDF: {pdf_path}")
        except Exception as e:
            print(f"❌ Lỗi xuất PDF: {e}")

    if choice in ["4", "5"]:
        txt_path = os.path.join(OUTPUT_DIR, f"{safe_title}_FULL.txt")
        try:
            merge_to_txt(translated_files, txt_path, novel_title=book_title)
            print(f"🎉 Đã xuất file TXT tổng hợp: {txt_path}")
        except Exception as e:
            print(f"❌ Lỗi xuất TXT tổng hợp: {e}")


def merge_existing_output_files():
    """Gộp các file đã có sẵn trong thư mục output/ mà không cần dịch lại."""
    files = glob.glob(os.path.join(OUTPUT_DIR, "*.*"))
    text_files = [f for f in files if f.endswith((".txt", ".md")) and not f.endswith("_FULL.txt")]

    if not text_files:
        print(f"⚠️ Thư mục '{OUTPUT_DIR}' chưa có file đã dịch nào.")
        return

    sorted_files = sorted(text_files, key=natural_sort_key)
    print(f"\n⚡ Tìm thấy {len(sorted_files)} file đã dịch trong output/:")
    for idx, f in enumerate(sorted_files, 1):
        print(f" [{idx}] {os.path.basename(f)}")

    ask_and_merge_outputs(sorted_files)


def translate_direct_text(translator: StoryTranslator):
    print("\n" + "=" * 50)
    print("📝 CHẾ ĐỘ DỊCH TRỰC TIẾP TỪ BÀN PHÍM / CLIPBOARD")
    print("Dán hoặc gõ đoạn văn bản cần dịch bên dưới.")
    print("Nhập 'END' trên một dòng riêng để bắt đầu dịch:")
    print("=" * 50)
    
    lines = []
    while True:
        try:
            line = input()
            if line.strip() == "END":
                break
            lines.append(line)
        except EOFError:
            break
            
    content = "\n".join(lines).strip()
    if not content:
        print("⚠️ Nội dung trống!")
        return

    print("\n⏳ Đang tiến hành chuyển ngữ và tối ưu văn phong...")
    def progress(i, total, chunk):
        if i == 0:
            print(f" 🔍 {chunk}")
        else:
            print(f" ➔ Đang dịch đoạn {i}/{total} ({len(chunk)} ký tự)...")

    result = translator.translate_text(content, progress_callback=progress)
    print("\n" + "═" * 25 + " KẾT QUẢ BẢN DỊCH " + "═" * 25)
    print(result)
    print("═" * 68)

    save_opt = input("\nBạn có muốn lưu kết quả vào file output? (y/n): ").strip().lower()
    if save_opt == "y":
        filename = input("Nhập tên file (VD: chapter_1.txt): ").strip() or "translated_output.txt"
        out_path = os.path.join(OUTPUT_DIR, filename)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"✅ Đã lưu kết quả tại: {out_path}")


def translate_single_file(translator: StoryTranslator):
    print(f"\n📂 Thư mục chứa file gốc: {INPUT_DIR}")
    files = glob.glob(os.path.join(INPUT_DIR, "*.*"))
    text_files = [f for f in files if f.endswith((".txt", ".md", ".raw"))]

    if not text_files:
        print(f"⚠️ Chưa có file nào trong thư mục 'input/'.")
        custom_path = input("\nNhập đường dẫn file tuyệt đối: ").strip('"').strip("'").strip()
        if custom_path and os.path.exists(custom_path):
            target_file = custom_path
        else:
            return
    else:
        print("\nDanh sách file trong thư mục input/:")
        sorted_input = sorted(text_files, key=natural_sort_key)
        for idx, f in enumerate(sorted_input, 1):
            print(f" [{idx}] {os.path.basename(f)}")
        
        while True:
            choice = input(f"\nChọn số file cần dịch (1-{len(sorted_input)}): ").strip()
            try:
                val = int(choice)
                if 1 <= val <= len(sorted_input):
                    target_file = sorted_input[val - 1]
                    break
            except ValueError:
                pass
            print("❌ Số thứ tự không hợp lệ!")

    file_name = os.path.basename(target_file)
    base, ext = os.path.splitext(file_name)
    output_file = os.path.join(OUTPUT_DIR, f"{base}_VIET{ext}")

    print(f"\n🚀 Đang bắt đầu dịch: {file_name}")
    print(f"📁 Đầu ra sẽ được lưu tại: {output_file}")
    
    def progress(i, total, chunk):
        if i == 0:
            print(f" 🔍 {chunk}")
        else:
            print(f" ➔ Đang xử lý đoạn {i}/{total} ({len(chunk)} ký tự)...")

    try:
        translator.translate_file(
            input_file=target_file,
            output_file=output_file,
            progress_callback=progress
        )
        print(f"\n🎉 DỊCH HOÀN TẤT! File đã lưu tại: {output_file}")
    except Exception as e:
        print(f"\n❌ Có lỗi xảy ra trong quá trình dịch: {e}")


def translate_all_in_folder(translator: StoryTranslator):
    files = glob.glob(os.path.join(INPUT_DIR, "*.*"))
    text_files = [f for f in files if f.endswith((".txt", ".md", ".raw"))]

    if not text_files:
        print(f"⚠️ Thư mục '{INPUT_DIR}' trống! Hãy thêm file vào trước.")
        return

    sorted_input_files = sorted(text_files, key=natural_sort_key)
    print(f"\n⚡ Tìm thấy {len(sorted_input_files)} file cần dịch trong thư mục input:")
    for idx, f in enumerate(sorted_input_files, 1):
        print(f" [{idx}] {os.path.basename(f)}")

    print("\n💡 CƠ CHẾ CACHE TÍCH LŨY: Sơ đồ xưng hô sẽ được lưu và duy trì liên tục cho bộ truyện.")
    print("   Khi gặp nhân vật mới, tool sẽ tự động Micro-Scan và bổ sung vào Cache!")
    confirm = input("Bạn có muốn bắt đầu dịch toàn bộ? (y/n): ").strip().lower()
    if confirm != "y":
        return

    def batch_progress(cur_idx, total_count, msg):
        print(f"\n{msg}")

    successful_outputs = translator.translate_batch_files(
        input_files=sorted_input_files,
        output_dir=OUTPUT_DIR,
        initial_scan_count=5,
        progress_callback=batch_progress
    )

    print("\n🎉 HOÀN TẤT DỊCH TẤT CẢ FILE TRONG THƯ MỤC INPUT!")
    if successful_outputs:
        ask_and_merge_outputs(successful_outputs)


def view_or_scan_context(translator: StoryTranslator):
    print("\n" + "=" * 50)
    print("🔍 SƠ ĐỒ QUAN HỆ & BẢNG XƯNG HÔ TRONG CACHE")
    print("=" * 50)
    if translator.story_context_cache:
        print(translator.story_context_cache)
    else:
        print("⚠️ Hiện tại chưa có sơ đồ trong Cache.")

    opt = input("\nBạn có muốn quét cập nhật thêm từ các file trong input/ không? (y/n): ").strip().lower()
    if opt == "y":
        files = glob.glob(os.path.join(INPUT_DIR, "*.*"))
        text_files = [f for f in files if f.endswith((".txt", ".md", ".raw"))]
        if not text_files:
            print("⚠️ Không có file nào trong input/ để quét.")
            return

        sorted_files = sorted(text_files, key=natural_sort_key)
        chapters_data = []
        for fpath in sorted_files[:5]:
            fname = os.path.basename(fpath)
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                chapters_data.append((fname, f.read()))

        print("\n⏳ Đang tiến hành quét phân tích...")
        res = translator.scan_initial_or_batch_context(chapters_data)
        print("\n" + "═" * 25 + " SƠ ĐỒ ĐÃ CẬP NHẬT " + "═" * 25)
        print(res)
        print("═" * 68)


def main():
    genre = "tien_hiep"
    provider = "gemini"
    
    translator = StoryTranslator(
        provider=provider,
        genre=genre
    )

    while True:
        print_banner(translator)
        print("\n" + "=" * 50)
        print("          CHỨC NĂNG DỊCH THUẬT")
        print("=" * 50)
        print(" [1] Dịch trực tiếp từ bàn phím / dán đoạn văn")
        print(" [2] Dịch 1 file cụ thể (từ thư mục input/ hoặc đường dẫn)")
        print(" [3] 🚀 Dịch hàng loạt toàn bộ file trong input/ (Tự động cập nhật Cache)")
        print(" [4] 🔍 Xem / Cập nhật Sơ đồ quan hệ & bảng xưng hô trong Cache")
        print(" [5] 🧹 Xóa trắng Cache ngữ cảnh (Để bắt đầu bộ truyện mới)")
        print(" [6] 📚 Gộp các file đã dịch trong output/ thành PDF / EPUB / TXT")
        print(" [7] Đổi thể loại văn phong hoặc cấu hình AI")
        print(" [0] Thoát (Tự động lưu Cache)")

        choice = input("\nChọn thao tác (0-7): ").strip()
        if choice == "1":
            translate_direct_text(translator)
        elif choice == "2":
            translate_single_file(translator)
        elif choice == "3":
            translate_all_in_folder(translator)
        elif choice == "4":
            view_or_scan_context(translator)
        elif choice == "5":
            translator.clear_context_cache()
            print("✅ Đã xóa trắng Cache ngữ cảnh!")
        elif choice == "6":
            merge_existing_output_files()
        elif choice == "7":
            genre = select_genre()
            provider = select_provider()
            extra_req = input("\nGhi chú thêm (Enter để bỏ qua): ").strip()
            translator = StoryTranslator(
                provider=provider,
                genre=genre,
                extra_instruction=extra_req
            )
            print("✅ Đã cập nhật cấu hình!")
        elif choice == "0":
            translator.save_context_cache()
            print("\nĐã lưu Cache. Tạm biệt!")
            break
        else:
            print("❌ Lựa chọn không hợp lệ!")


if __name__ == "__main__":
    main()
