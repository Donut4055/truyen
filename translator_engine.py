import os
import sys
import json
import time
import re
import datetime
from typing import List, Dict, Optional, Generator, Tuple

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Chỉ tải file .env nằm trực tiếp trong thư mục 'dịch truyện'
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(CURRENT_DIR, ".env"), override=True)

# Import system prompt builder
from prompts.system_prompt import build_system_prompt, STYLE_PRESETS

# Import các client AI
from openai import OpenAI
try:
    from google import genai
    from google.genai import types as genai_types
    HAS_GOOGLE_GENAI = True
except ImportError:
    HAS_GOOGLE_GENAI = False

try:
    import google.generativeai as legacy_genai
    HAS_LEGACY_GENAI = True
except ImportError:
    HAS_LEGACY_GENAI = False

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DEFAULT_CACHE_FILE = os.path.join(CACHE_DIR, "story_context_cache.json")


class StoryTranslator:
    def __init__(
        self,
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        genre: str = "tien_hiep",
        glossary_path: Optional[str] = None,
        extra_instruction: str = "",
        cache_file: Optional[str] = None
    ):
        self.provider = (provider or os.getenv("AI_PROVIDER", "gemini")).lower().strip()
        self.genre = genre
        self.extra_instruction = extra_instruction
        self.glossary = self._load_glossary(glossary_path)
        self.cache_file = cache_file or DEFAULT_CACHE_FILE
        
        # Cấu hình Model & API Key
        if self.provider == "deepseek":
            self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY", "")
            self.base_url = base_url or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
            self.model_name = model_name or os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=120.0) if self.api_key else None
        elif self.provider in ["grok", "openai", "openrouter"]:
            self.api_key = api_key or os.getenv("GROK_API_KEY", "")
            self.base_url = base_url or os.getenv("GROK_BASE_URL", "https://api.x.ai/v1")
            self.model_name = model_name or os.getenv("GROK_MODEL", "grok-beta")
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=120.0) if self.api_key else None
        else: # Default Gemini
            self.provider = "gemini"
            self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
            self.model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
            self.gemini_client = None
            if self.api_key:
                if HAS_GOOGLE_GENAI:
                    try:
                        self.gemini_client = genai.Client(api_key=self.api_key)
                    except Exception:
                        self.gemini_client = None
                if not self.gemini_client and HAS_LEGACY_GENAI:
                    legacy_genai.configure(api_key=self.api_key)

        # Quản lý Persistent Context Cache
        os.makedirs(CACHE_DIR, exist_ok=True)
        self.story_context_cache = ""
        self.scanned_chapters = []
        self.load_context_cache()

    def _load_glossary(self, path: Optional[str]) -> dict:
        """Tải bảng thuật ngữ từ file json."""
        default_path = path or os.path.join(os.path.dirname(os.path.abspath(__file__)), "glossary.json")
        if os.path.exists(default_path):
            try:
                with open(default_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data.get("terms", data)
            except Exception as e:
                print(f"[Cảnh báo]: Không thể đọc file glossary.json ({e})")
        return {}

    def load_context_cache(self, file_path: Optional[str] = None) -> bool:
        """Đọc và nạp sơ đồ ngữ cảnh đã lưu từ file local vào bộ nhớ cache."""
        target_file = file_path or self.cache_file
        if os.path.exists(target_file):
            try:
                with open(target_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self.story_context_cache = data.get("context_diagram", "")
                        self.scanned_chapters = data.get("scanned_chapters", [])
                        if self.story_context_cache:
                            print(f"📖 [Context Cache]: Đã nạp sơ đồ ngữ cảnh ({len(self.story_context_cache)} ký tự) từ {os.path.basename(target_file)}!")
                            return True
            except Exception as e:
                print(f"[Cảnh báo]: Không thể tải cache ngữ cảnh ({e})")
        return False

    def save_context_cache(self, file_path: Optional[str] = None):
        """Lưu sơ đồ ngữ cảnh & xưng hô tích lũy xuống file local để tiếp tục sử dụng cho các lần sau."""
        target_file = file_path or self.cache_file
        os.makedirs(os.path.dirname(os.path.abspath(target_file)), exist_ok=True)
        try:
            payload = {
                "updated_at": datetime.datetime.now().isoformat(),
                "genre": self.genre,
                "scanned_chapters": list(set(self.scanned_chapters)),
                "context_diagram": self.story_context_cache
            }
            with open(target_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            print(f"💾 [Context Cache]: Đã lưu sơ đồ ngữ cảnh vào file local: {target_file}")
        except Exception as e:
            print(f"[Lỗi lưu cache ngữ cảnh]: {e}")

    def clear_context_cache(self):
        """Xóa trắng cache trong bộ nhớ và xóa file cache local."""
        self.story_context_cache = ""
        self.scanned_chapters = []
        if os.path.exists(self.cache_file):
            try:
                os.remove(self.cache_file)
                print("🧹 Đã xóa file cache local!")
            except Exception:
                pass

    def get_system_prompt(self, relationship_context: str = "") -> str:
        """Lấy system prompt hoàn chỉnh theo thể loại, glossary và sơ đồ xưng hô đã lưu trong cache."""
        effective_context = relationship_context or self.story_context_cache
        return build_system_prompt(
            genre=self.genre,
            custom_glossary=self.glossary,
            extra_instruction=self.extra_instruction,
            relationship_context=effective_context
        )

    def scan_initial_or_batch_context(self, chapters_data: List[Tuple[str, str]]) -> str:
        """
        Quét cụm chương ban đầu để tạo nền tảng Sơ đồ quan hệ & bảng xưng hô cho toàn bộ tác phẩm.
        Nếu đã có cache, sẽ thực hiện cập nhật bổ sung (Merge) thay vì xóa trắng.
        """
        combined_text_parts = []
        for idx, (ch_name, ch_text) in enumerate(chapters_data, 1):
            excerpt = ch_text[:3500] if len(ch_text) > 3500 else ch_text
            combined_text_parts.append(f"--- [CHƯƠNG {idx}: {ch_name}] ---\n{excerpt}\n")
            if ch_name not in self.scanned_chapters:
                self.scanned_chapters.append(ch_name)

        full_content = "\n".join(combined_text_parts)

        if self.story_context_cache:
            # Chế độ bổ sung / cập nhật vào sơ đồ hiện tại
            prompt = f"""Bạn là một chuyên gia phân tích kịch bản và biên tập dịch thuật tiểu thuyết hàng đầu.
Dưới đây là SƠ ĐỒ QUAN HỆ & BẢNG XƯNG HÔ HIỆN TẠI của bộ truyện:
════════════ SƠ ĐỒ ĐANG CÓ TRONG CACHE ════════════
{self.story_context_cache}
═══════════════════════════════════════════════════

Và đây là nội dung của các chương tiếp theo vừa nạp:
════════════ CÁC CHƯƠNG MỚI ════════════
{full_content[:18000]}
════════════════════════════════════════

HÃY BỔ SUNG & CẬP NHẬT SƠ ĐỒ:
1. Giữ nguyên các nhân vật và quy ước xưng hô cũ đã có.
2. Thêm toàn bộ các nhân vật mới xuất hiện (Tên, vai trò, môn phái, mối quan hệ với các nhân vật cũ).
3. Cập nhật bảng quy ước xưng hô 2 chiều cho các cặp nhân vật mới.
4. Trả về BẢN SƠ ĐỒ TỔNG HỢP TOÀN DIỆN MỚI NHẤT (bao gồm cả nhân vật cũ + mới)."""
        else:
            # Chế độ khởi tạo sơ đồ mới từ đầu
            prompt = f"""Bạn là một chuyên gia phân tích kịch bản và biên tập dịch thuật tiểu thuyết hàng đầu.
Dưới đây là nội dung của {len(chapters_data)} chương truyện đầu tiên.

Nhiệm vụ của bạn là xây dựng SƠ ĐỒ QUAN HỆ & BẢNG XƯNG HÔ NỀN TẢNG để phục vụ việc dịch toàn bộ tác phẩm:
1. XÁC ĐỊNH DANH SÁCH NHÂN VẬT XUẤT HIỆN HOẶC ĐƯỢC NHẮC TỚI (Tên, vai trò, môn phái/tổ chức, tính cách, bối cảnh).
2. VẼ SƠ ĐỒ QUAN HỆ NHÂN VẬT TỔNG THỂ (dạng Mermaid graph và bảng đối chiếu quan hệ).
3. BẢNG QUY ƯỚC ĐẠI TỪ XƯNG HÔ BẤT BIẾN (Ai gọi ai là gì? Xưng hô trong đối thoại trực tiếp, xưng hô trước đám đông, và xưng hô khi độc thoại nội tâm).
4. TÓM TẮT MẠCH TRUYỆN & CÁC BƯỚC NGOẶT CHÍNH.

════════════ NỘI DUNG {len(chapters_data)} CHƯƠNG NỀN TẢNG ════════════
{full_content[:20000]}
═════════════════════════════════════════════════════════════════════"""

        result = self._call_llm_for_analysis(prompt)
        if result:
            self.story_context_cache = result
            self.save_context_cache()
        return self.story_context_cache

    def incremental_scan_for_new_characters(self, chunk_text: str) -> bool:
        """
        Quét vi mô (Micro-scan) một đoạn văn ngắn khi phát hiện có nhân vật mới chưa có trong sơ đồ,
        để bổ sung ngay nhân vật đó vào sơ đồ quan hệ trong Cache.
        """
        if not self.story_context_cache:
            return False

        prompt = f"""Dưới đây là SƠ ĐỒ QUAN HỆ NHÂN VẬT HIỆN TẠI của tác phẩm:
════════════ SƠ ĐỒ HIỆN TẠI ════════════
{self.story_context_cache}
════════════════════════════════════════

Đoạn văn sau đây vừa xuất hiện trong chương truyện:
════════════ ĐOẠN VĂN CẦN KIỂM TRA ════════════
{chunk_text}
═══════════════════════════════════════════════

KIỂM TRA & BỔ SUNG:
Nếu trong đoạn văn trên CÓ XUẤT HIỆN NHÂN VẬT MỚI (chưa có tên trong sơ đồ hiện tại), hãy:
1. Xác định nhân vật mới, vai vế và mối quan hệ xưng hô với các nhân vật hiện có.
2. Thêm nhân vật đó vào sơ đồ và trả về BẢN SƠ ĐỒ ĐÃ CẬP NHẬT.
Nếu KHÔNG CÓ nhân vật mới nào, chỉ trả về đúng 2 chữ: "NO_CHANGE"."""

        res = self._call_llm_for_analysis(prompt, max_tokens=2048)
        if res and "NO_CHANGE" not in res and len(res) > 200:
            print(f"✨ [Micro-Scan]: Đã phát hiện và cập nhật nhân vật mới vào Cache!")
            self.story_context_cache = res
            self.save_context_cache()
            return True
        return False

    def _call_llm_for_analysis(self, prompt: str, max_tokens: int = 4096) -> str:
        """Hàm nội bộ gọi LLM cho tác vụ phân tích ngữ cảnh / quan hệ."""
        if self.provider == "gemini":
            if HAS_GOOGLE_GENAI and self.gemini_client:
                response = self.gemini_client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=genai_types.GenerateContentConfig(temperature=0.3, max_output_tokens=max_tokens)
                )
                return (response.text or "").strip()
            elif HAS_LEGACY_GENAI:
                model = legacy_genai.GenerativeModel(model_name=self.model_name)
                response = model.generate_content(prompt, generation_config={"temperature": 0.3, "max_output_tokens": max_tokens})
                return (response.text or "").strip()
        else:
            if not self.client:
                raise RuntimeError(f"Chưa cấu hình API Key cho {self.provider}!")
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "Bạn là chuyên gia phân tích kịch bản và quan hệ nhân vật tiểu thuyết."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=max_tokens
            )
            return (response.choices[0].message.content or "").strip()
        return ""

    def scan_relationships(self, text: str) -> str:
        """Quét và phân tích sơ đồ quan hệ của một văn bản / chương."""
        return self.scan_initial_or_batch_context([("Chương hiện tại", text)])

    def chunk_text(self, text: str, max_chunk_size: int = 3500) -> List[str]:
        """Chia văn bản thành các đoạn hợp lý theo paragraph."""
        paragraphs = text.split("\n")
        chunks = []
        current_chunk = []
        current_length = 0

        for p in paragraphs:
            p_len = len(p) + 1
            if current_length + p_len > max_chunk_size and current_chunk:
                chunks.append("\n".join(current_chunk).strip())
                current_chunk = [p]
                current_length = p_len
            else:
                current_chunk.append(p)
                current_length += p_len

        if current_chunk:
            final_text = "\n".join(current_chunk).strip()
            if final_text:
                chunks.append(final_text)

        return chunks if chunks else [text]

    def translate_chunk(self, chunk: str, relationship_context: str = "", max_retries: int = 3) -> str:
        """Dịch 1 đoạn văn bản bằng LLM với cơ chế tự động thử lại (Retry & Backoff)."""
        system_instruction = self.get_system_prompt(relationship_context=relationship_context)
        
        user_prompt = f"""Dưới đây là đoạn văn bản gốc cần dịch. Hãy dịch sang tiếng Việt văn phong chuẩn mực nhất theo đúng System Prompt:

════════════ VĂN BẢN GỐC ════════════
{chunk}
═════════════════════════════════════"""

        for attempt in range(1, max_retries + 1):
            try:
                if self.provider == "gemini":
                    if HAS_GOOGLE_GENAI and self.gemini_client:
                        response = self.gemini_client.models.generate_content(
                            model=self.model_name,
                            contents=user_prompt,
                            config=genai_types.GenerateContentConfig(
                                system_instruction=system_instruction,
                                temperature=0.7,
                                max_output_tokens=8192
                            )
                        )
                        return (response.text or "").strip()
                    elif HAS_LEGACY_GENAI:
                        model = legacy_genai.GenerativeModel(
                            model_name=self.model_name,
                            system_instruction=system_instruction
                        )
                        response = model.generate_content(
                            user_prompt,
                            generation_config={"temperature": 0.7, "max_output_tokens": 8192}
                        )
                        return (response.text or "").strip()
                    else:
                        raise RuntimeError("Chưa cài đặt thư viện Google GenAI!")

                else: # OpenAI / DeepSeek / Grok
                    if not self.client:
                        raise RuntimeError(f"Chưa cấu hình API Key cho nhà cung cấp {self.provider}!")
                    response = self.client.chat.completions.create(
                        model=self.model_name,
                        messages=[
                            {"role": "system", "content": system_instruction},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=0.7,
                        max_tokens=4096
                    )
                    return (response.choices[0].message.content or "").strip()

            except Exception as e:
                print(f"[Lỗi dịch lần {attempt}/{max_retries}]: {e}")
                if attempt == max_retries:
                    raise e
                time.sleep(2 * attempt)
        return ""

    def translate_text(
        self,
        text: str,
        chunk_size: int = 3500,
        auto_scan_relationships: bool = True,
        check_incremental_characters: bool = True,
        progress_callback: Optional[callable] = None
    ) -> str:
        """Dịch toàn bộ văn bản hoặc chương truyện dài, tự động áp dụng và cập nhật sơ đồ xưng hô."""
        if auto_scan_relationships and not self.story_context_cache and len(text.strip()) > 500:
            try:
                if progress_callback:
                    progress_callback(0, 1, "Đang quét khởi tạo sơ đồ quan hệ nhân vật và khóa đại từ xưng hô...")
                self.scan_relationships(text)
            except Exception as e:
                print(f"[Cảnh báo]: Khởi tạo sơ đồ thất bại ({e})")

        chunks = self.chunk_text(text, max_chunk_size=chunk_size)
        total_chunks = len(chunks)
        translated_parts = []

        for i, chunk in enumerate(chunks, 1):
            if progress_callback:
                progress_callback(i, total_chunks, chunk)
            
            # Kiểm tra xem đoạn này có xuất hiện nhân vật mới cần cập nhật vào sơ đồ không
            if check_incremental_characters and len(chunk) > 300:
                try:
                    # Chạy micro-scan nhanh nếu cần
                    self.incremental_scan_for_new_characters(chunk)
                except Exception:
                    pass

            translated = self.translate_chunk(chunk)
            translated_parts.append(translated)
            
            if i < total_chunks:
                time.sleep(0.5)

        return "\n\n".join(translated_parts)

    def translate_file(
        self,
        input_file: str,
        output_file: Optional[str] = None,
        auto_scan_relationships: bool = True,
        progress_callback: Optional[callable] = None
    ) -> str:
        """Đọc file nguồn (.txt, .md), dịch và ghi ra file đích."""
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Không tìm thấy file: {input_file}")

        with open(input_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        if not output_file:
            base, ext = os.path.splitext(input_file)
            output_file = f"{base}_vietnamese{ext}"

        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)

        translated_content = self.translate_text(
            text=content,
            auto_scan_relationships=auto_scan_relationships,
            progress_callback=progress_callback
        )

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(translated_content)

        # Lưu lại cache sau khi dịch xong file
        self.save_context_cache()
        return output_file

    def translate_batch_files(
        self,
        input_files: List[str],
        output_dir: str,
        initial_scan_count: int = 5,
        progress_callback: Optional[callable] = None
    ) -> List[str]:
        """
        Dịch danh sách các file chương truyện với cơ chế Persistent Context Cache:
        - Nếu chưa có Cache: Quét cụm chương ban đầu (VD: 5 chương đầu) để lập nền tảng sơ đồ.
        - Nếu đã có Cache từ phiên trước: Tự động nạp và giữ nguyên sơ đồ để tiếp tục dịch.
        - Xuyên suốt quá trình dịch: Tự động phát hiện nhân vật mới để bổ sung vào sơ đồ.
        - Khi kết thúc: Lưu toàn bộ Cache ra file local để phiên dịch sau có thể tiếp tục ngay lập tức!
        """
        successful_outputs = []
        total_files = len(input_files)

        # 1. Khởi tạo hoặc cập nhật Sơ đồ nền tảng nếu Cache trống
        if not self.story_context_cache and input_files:
            sample_batch = input_files[:initial_scan_count]
            chapters_data = []
            for fpath in sample_batch:
                fname = os.path.basename(fpath)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        chapters_data.append((fname, f.read()))
                except Exception as e:
                    print(f"[Lỗi đọc file {fname}]: {e}")

            if chapters_data:
                if progress_callback:
                    progress_callback(
                        0, total_files,
                        f"⚡ Đang quét thiết lập Sơ đồ quan hệ & bảng xưng hô nền tảng ({len(chapters_data)} chương đầu)..."
                    )
                self.scan_initial_or_batch_context(chapters_data)

        # 2. Dịch lần lượt từng file trong danh sách
        for idx, fpath in enumerate(input_files, 1):
            fname = os.path.basename(fpath)
            base, ext = os.path.splitext(fname)
            output_file = os.path.join(output_dir, f"{base}_VIET{ext}")

            if progress_callback:
                progress_callback(
                    idx, total_files,
                    f"🚀 [{idx}/{total_files}] Đang dịch: {fname} (Áp dụng Sơ đồ xưng hô trong Cache)..."
                )

            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                translated = self.translate_text(
                    text=content,
                    auto_scan_relationships=False, # Đã có Persistent Cache
                    check_incremental_characters=True, # Bật phát hiện nhân vật mới
                    progress_callback=lambda i, total, chunk: progress_callback(
                        idx, total_files, f"   ➔ Đoạn {i}/{total} ({len(chunk)} ký tự)..."
                    ) if progress_callback else None
                )

                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(translated)

                successful_outputs.append(output_file)

            except Exception as e:
                print(f"❌ Lỗi khi dịch {fname}: {e}")

        # 3. END TASK: Lưu toàn bộ Cache ra file local
        self.save_context_cache()
        if progress_callback:
            progress_callback(
                total_files, total_files,
                f"💾 Đã hoàn tất phiên dịch và lưu Sơ đồ quan hệ vào Cache Local ({os.path.basename(self.cache_file)})!"
            )

        return successful_outputs
