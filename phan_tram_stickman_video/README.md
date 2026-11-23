# Đừng để dấu % thao túng bạn

Video giải thích 5 phút, 16:9, 1280×720, 18 fps, dựng theo `source_script.txt`. Người que đứng bên trái, hình minh họa và công thức ở bên phải.

## Tệp chính

- `final_video.mp4`: phim hoàn chỉnh có giọng đọc tiếng Việt và phụ đề cháy hình.
- `subtitles.srt`: phụ đề rời, 127 câu ngắn căn theo âm thanh.
- `narration.wav`: giọng kể tổng hợp bằng preset **Anh Khôi** của VieNeu.
- `illustrations/`: bảy hình minh họa riêng dùng cùng đồ họa với phim.
- `video_assets.zip`: bảy hình, sáu animation mới (SVG và WebP), phụ đề và hướng dẫn.
- `video_actions_preview.mp4`: video xem nhanh sáu animation mới.
- `timed_script.json`: mốc câu thoại và phụ đề sau khi căn đúng sáu phần.
- `render_video.py`: mã dựng video, gồm bảng giảm giá, áo, bài kiểm tra, điện thoại, biểu đồ, bảng công thức và thử thách cuối.

Video sử dụng sáu animation stickman mới trong `../stickman_assets/`: `spot_sale`, `calculate_discount`, `pay_cashier`, `compare_prices`, `write_formula`, `empty_wallet`.

Hình minh họa và các phép tính được vẽ bằng mã trong `render_video.py`; font Noto Sans và Nunito đi kèm giấy phép OFL trong thư mục này.

## Dựng lại

Trên máy đã cài VieNeu, Pillow, resvg-py, numpy, soundfile và FFmpeg:

```powershell
py -3.11 prepare_narration.py
py -3.11 build_audio_timeline.py
python render_video.py
```

Để xem thử 15 giây: `python render_video.py --preview-seconds 15 --output preview_15s.mp4`.

Các mốc phần là 0:00–0:40, 0:40–1:35, 1:35–2:30, 2:30–3:35, 3:35–4:25 và 4:25–5:00. Ở thử thách cuối, cửa hàng A có giá 60.000đ; cửa hàng B có giá 64.000đ.
