# 📖 Tool Dịch Truyện AI Chuyên Nghiệp (AI Novel & Comic Translator)

Công cụ dịch truyện, tiểu thuyết, Webnovel, Light Novel, Manga, Manhwa chuyên sâu với **System Prompt được thiết kế chuyên biệt** nhằm đạt được văn phong thuần Việt mượt mà, cảm xúc và hệ thống **từ tượng thanh, tượng hình** chuẩn xác bậc nhất.

---

## 🌟 Tính Năng Nổi Bật

1. **Bộ Nhớ Ngữ Cảnh Tích Lũy & Lưu File Local (Persistent Context Cache)**:
   - **Duy trì liên tục cho toàn bộ truyện**: Sơ đồ quan hệ & bảng xưng hô được lưu và duy trì xuyên suốt mọi chương của tác phẩm mà không bị mất đi.
   - **Tự động Micro-Scan khi gặp nhân vật mới**: Khi dịch gặp một nhân vật chưa có trong sơ đồ, AI sẽ tự động quét nhanh đoạn nhỏ đó và bổ sung ngay nhân vật cùng quan hệ xưng hô vào sơ đồ trong Cache.
   - **Tự động lưu ra file Local (`data/story_context_cache.json`)**: Khi kết thúc phiên dịch hoặc thoát chương trình, toàn bộ sơ đồ được lưu an toàn xuống ổ đĩa.
   - **Tự động nạp lại khi dịch tiếp**: Khi mở tool để dịch các chương tiếp theo, hệ thống tự động nạp lại toàn bộ sơ đồ đã tích lũy từ trước, đảm bảo sự nhất quán xưng hô 100% từ chương 1 đến chương 1000+.

2. **System Prompt Đỉnh Cao (prompts/system_prompt.py)**:
   - **Xử lý triệt để bệnh "convert sượng / dịch máy thô ráp"**: Tái cấu trúc câu văn mượt mà, tự nhiên như văn phong do tác giả/dịch giả người Việt chắp bút.
   - **Chuyển hóa từ tượng thanh (Onomatopoeia) & tượng hình (Mimetic words)**: Tự động chuyển các âm thanh va chạm, xé gió, kiếm khí, bước chân, tiếng lòng sang từ vựng tiếng Việt sống động (*ầm ầm, loảng xoảng, vùn vụt, lảo đảo, chớp nhoáng, run rẩy, lách tách...*).
   - **Đại từ nhân xưng chuẩn chỉ**: Tự động linh hoạt theo từng thể loại và mối quan hệ nhân vật (*ta - ngươi, đệ - huynh, anh - em, tôi - cậu, trẫm - ái khanh...*).

2. **6 Preset Phong Cách Độc Quyền**:
   - ⚔️ **Tiên Hiệp / Huyền Huyễn / Tu Chân / Kiếm Hiệp**: Hào hùng, cổ phong, chuẩn Hán-Việt tinh tế, chiêu thức uy mãnh.
   - 🌸 **Light Novel / Anime / Isekai / Rom-Com**: Trẻ trung, thoại sinh động, nội tâm dí dỏm sâu lắng.
   - 💖 **Ngôn Tình / Đô Thị Tình Cảm / Nữ Cường**: Trau chuốt, giàu nhạc điệu và cảm xúc rung động.
   - ⚡ **Manhwa / Webtoon / Action Hunter**: Tiết tấu dồn dập, gãy gọn, combat nảy lửa, định dạng Hệ thống (System) trực quan.
   - 🕯️ **Kinh Dị / Huyền Bí / Trinh Thám / Cthulhu**: Không khí u ám, ma mị, miêu tả cảm giác rợn ngáy và hồi hộp tột độ.
   - 📚 **Tiểu Thuyết Tiêu Chuẩn**: Trung tính, chuẩn mực văn học phổ thông.

3. **Từ Điển Thuật Ngữ Cố Định (Glossary `glossary.json`)**:
   - Cho phép định nghĩa tên nhân vật, địa danh, chiêu thức để bản dịch đồng nhất 100% xuyên suốt toàn bộ tác phẩm.

4. **Tùy Chọn Gộp & Xuất Bản Ebook / PDF / TXT Tự Động**:
   - Tự động sắp xếp các chương theo đúng thứ tự tự nhiên (Chương 1, 2, ..., 10).
   - **Ebook EPUB (.epub)**: Đọc chuẩn trên Apple Books, Kindle, Kobo, Moon+ Reader (tự sinh Table of Contents / Mục lục số).
   - **PDF (.pdf)**: Tạo file PDF phân trang chuẩn tiếng Việt, có bìa và mục lục chương.
   - **TXT (.txt)**: Gộp toàn bộ thành 1 file duy nhất với tiêu đề phân cách rõ ràng.
   - **Hoặc để nguyên từng file TXT riêng lẻ** trong thư mục `output/`.

---

## 🚀 Hướng Dẫn Cài Đặt & Sử Dụng

### Bước 1: Cài đặt các thư viện cần thiết
```powershell
pip install -r requirements.txt
```

### Bước 2: Tạo file cấu hình `.env` từ file mẫu `.env.example`
Chạy lệnh tạo file `.env` theo hệ điều hành của bạn:

- **Windows PowerShell**:
  ```powershell
  Copy-Item .env.example .env
  ```
- **Windows Command Prompt (CMD)**:
  ```cmd
  copy .env.example .env
  ```
- **Linux / macOS**:
  ```bash
  cp .env.example .env
  ```

> Mở file `.env` vừa tạo và điền API Key của bạn (`DEEPSEEK_API_KEY`, `GEMINI_API_KEY` hoặc `GROK_API_KEY`).

---

### Bước 3: Khởi chạy công cụ

- **Cách 1 (Windows 1-Click)**: Nhấp đúp vào file 👉 run_dich_truyen.bat
- **Cách 2 (Terminal / Command Line)**:
  ```powershell
  python cli.py
  ```

---

### Các Chế Độ Dịch:
1. **Dịch trực tiếp**: Dán đoạn văn bản thô bất kỳ và nhận kết quả tức thì.
2. **Dịch 1 file**: Chọn file `.txt`, `.md` trong thư mục `input/` hoặc gõ đường dẫn. Kết quả xuất ra tại `output/`.
3. **Dịch hàng loạt (Batch)**: Tự động dịch toàn bộ các chương/file có trong `input/` và xuất ra `output/`.

---

## 🛠️ Cấu Trúc Thư Mục

```
dịch truyện/
├── cli.py                  # Giao diện dòng lệnh tương tác trực quan
├── translator_engine.py    # Bộ xử lý dịch thuật, chia đoạn & kết nối AI
├── run_dich_truyen.bat     # Phím tắt chạy nhanh trên Windows
├── glossary.json           # Bảng thuật ngữ / Tên riêng tùy biến
├── prompts/
│   └── system_prompt.py    # Bộ System Prompt & Preset văn phong chuyên sâu
├── input/                  # Thư mục để file truyện gốc (.txt, .md)
├── output/                 # Thư mục chứa kết quả sau khi dịch
└── README.md               # Tài liệu hướng dẫn
```

---

## 💡 Mẹo Thêm Thuật Ngữ Vào `glossary.json`

Mở file `glossary.json` và thêm các cặp `Từ gốc`: `Từ dịch chuẩn`:
```json
{
  "terms": {
    "Xiao Yan": "Tiêu Viêm",
    "Yun Yun": "Vân Vận",
    "Shadow Monarch": "Quân Vương Bóng Tối",
    "Heavenly Flame": "Dị Hỏa"
  }
}
```
Tool sẽ tự động đưa các từ này vào ngữ cảnh ép buộc AI phải tuân thủ chuẩn xác 100%!
