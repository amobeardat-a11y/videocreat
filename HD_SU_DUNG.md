# HƯỚNG DẪN TỔNG HỢP: STICKMAN VIDEO DIRECTOR + VIET TTS + GOOGLE FLOW (VEO 3)

Hệ thống đã được trang bị đầy đủ 2 quy trình làm video:
1. **Mode B (Code Engine):** Render hoạt hình người que 2D hoàn toàn cục bộ bằng máy tính (Miễn phí 100%, không cần API).
2. **Mode A (Model Engine - Google Flow / Veo 3):** Tận dụng sức mạnh AI tạo video điện ảnh của Google Veo trên [Google Flow](https://flow.google.com/) kết hợp lồng tiếng và phụ đề Tiếng Việt tự động.

---

## 🎬 QUY TRÌNH 1: MODE A - GOOGLE FLOW (VEO 3) + VIET TTS

Sử dụng công cụ: `viet_flow_director.py`

### Bước 1: Soạn kịch bản, xuất Prompt Veo & Lồng tiếng Việt
Chạy lệnh khởi tạo dự án:
```powershell
py -3.11 viet_flow_director.py plan --project-dir "du_an_flow" --style "A6" --voice "Anh Khôi" --ratio "16:9" --script "Chào các bạn. Hôm nay chúng ta sẽ tìm hiểu về trí tuệ nhân tạo. AI đang thay đổi cách chúng ta sáng tạo nội dung mỗi ngày!"
```
*Tùy chọn phong cách (`--style`):*
- `A1`: Classic Minimalist (Người que trắng đen tối giản, điểm nhấn neon).
- `A2`: Modern Pop Beanie Zeke (Chàng trai mũ len đỏ, phòng lab công nghệ, giao diện holographic).
- `A4`: Cozy Storytelling (Hoạt hình đời thường, quán cafe, đường phố ấm áp).
- `A6`: Amber Noir (Phong cách điện ảnh, áo hoodie cam, ánh đèn vàng ấm & bóng đêm đô thị).
- `A7`: Rubber Hose (Hoạt hình thập niên 1930 cổ điển, tay chân uốn lượn).

*Kết quả sinh ra trong thư mục dự án:*
- `FLOW_PROMPTS.md`: Danh sách prompt tiếng Anh chi tiết cho từng cảnh chuẩn Veo để bạn copy vào Google Flow.
- `voice.wav`: File âm thanh lồng tiếng tiếng Việt hoàn chỉnh.
- `subtitles.srt`: File phụ đề tiếng Việt khớp từng mili-giây.
- `clips/`: Thư mục để chứa các video tải về từ Google Flow.

### Bước 2: Tạo video trên Google Flow
1. Mở [flow.google.com](https://flow.google.com/) (đăng nhập tài khoản Google).
2. Mở file `FLOW_PROMPTS.md` trong thư mục dự án, copy lần lượt từng prompt vào Google Flow để sinh video (khoảng 4-6 giây mỗi cảnh).
3. Tải các video clip về và lưu vào thư mục `clips/` theo đúng tên:
   - Cảnh 1: `scene_1.mp4`
   - Cảnh 2: `scene_2.mp4`
   - Cảnh 3: `scene_3.mp4`
   - ...

### Bước 3: Hậu kỳ tự động chỉ với 1 lệnh
Khi đã thả đủ các clips vào thư mục `clips/`, chạy lệnh:
```powershell
py -3.11 viet_flow_director.py assemble --project-dir "du_an_flow"
```
Hệ thống sẽ tự động ghép nối các cảnh, hòa âm lời bình tiếng Việt, đốt phụ đề tiếng Việt chuẩn nét và xuất ra video hoàn chỉnh:
`du_an_flow/final_flow_video.mp4`

---

## ⚡ QUY TRÌNH 2: MODE B - CODE ENGINE (RENDER OFFLINE 100% MIỄN PHÍ)

Sử dụng công cụ: `viet_tts_director.py`

### 1. Xem danh sách giọng đọc tiếng Việt (25+ giọng):
```powershell
py -3.11 viet_tts_director.py voices
```

### 2. Tạo video người que tự động từ dòng lệnh:
```powershell
py -3.11 viet_tts_director.py create --voice "Trúc Ly" --output-dir "video_offline" --script "Chào các bạn. Video này được render hoàn toàn bằng CPU máy tính của bạn!"
```
Video xuất ra tại: `video_offline/output/preview.mp4`

---

## 📁 Các dự án mẫu đã dựng thành công trên máy bạn
- 🌟 **Dự án Google Flow Demo:** [demo_flow_project/final_flow_video.mp4](file:///c:/Users/dat/Downloads/video%20genflow/demo_flow_project/final_flow_video.mp4)
- 🌟 **File hướng dẫn Prompt Veo mẫu:** [FLOW_PROMPTS.md](file:///c:/Users/dat/Downloads/video%20genflow/demo_flow_project/FLOW_PROMPTS.md)
- 🌟 **Dự án Code Engine B1 Demo:** [viet_demo/output/preview.mp4](file:///c:/Users/dat/Downloads/video%20genflow/viet_demo/output/preview.mp4)
