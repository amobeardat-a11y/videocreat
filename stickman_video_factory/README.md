# Bộ dựng video người que dùng cho nhiều kịch bản

Bộ này giữ phong cách của video giá ship: người que ở nửa trái, bảng/đồ thị/hình minh họa ở nửa phải, chữ thoại ở dưới, giọng tiếng Việt, chuyển pose mềm, video 1280×720 và phụ đề SRT. Nội dung video nằm trong JSON; model nhỏ chỉ cần tạo kế hoạch JSON, không phải sửa mã dựng. Nếu AI có quyền thao tác trên máy, dùng [AGENT_TASK.md](AGENT_TASK.md) để giao toàn bộ việc từ kịch bản đến video.

## Dùng với Gemini Flash hoặc GPT Luna

1. Lưu kịch bản gốc thành `my_script.md`. Mở [MODEL_PROMPT.md](MODEL_PROMPT.md), dán kịch bản vào cuối prompt và gửi cho model. Lưu JSON mà model trả về thành `my_plan.json`.
2. Kiểm tra trước khi tạo giọng/video:

   ```powershell
   python stickman_video_factory/build.py my_plan.json --source my_script.md --validate-only
   ```

3. Khi JSON hợp lệ, chạy một lệnh:

   ```powershell
   python stickman_video_factory/build.py my_plan.json --source my_script.md --out my_video
   ```

4. Mở `my_video/contact_sheet.png` để xem nhanh bố cục, rồi xem `my_video/video.mp4`. Nếu cần sửa, đổi JSON và chạy lại lệnh. Giọng của những câu không thay đổi được lấy từ bộ đệm.

Thử với kịch bản mẫu khác chủ đề:

```powershell
python stickman_video_factory/build.py stickman_video_factory/examples/discount_story.json --source stickman_video_factory/examples/discount_script.md --out stickman_video_factory/examples/discount_output
```

Thử chuỗi diễn xuất nhiều pose trong một câu thoại:

```powershell
python stickman_video_factory/build.py stickman_video_factory/examples/acting_sequence_story.json --source stickman_video_factory/examples/acting_sequence_script.md --out stickman_video_factory/examples/acting_sequence_output
```

Trong một `line`, dùng `"acting_sequence":"search_and_discover"` thay cho `pose` và `expression`. Bộ dựng lấy các nhịp từ JSON trong `stickman_assets/sequences/`, co giãn theo thời lượng thoại, chừa tối thiểu khoảng diễn cho câu ngắn và giữ vị trí cuối chuỗi cho câu sau. Nhân vật còn lại tiếp tục ở tư thế lắng nghe. Có thể kết hợp `move_x` để đặt vị trí bắt đầu; chỉ dùng một chuỗi khi lời thoại thật sự có nhiều nhịp diễn.

Có thể thêm `"effect":"question"` vào một `line` để đặt VFX chuyển động lên nhân vật đang nói. Thư viện có 10 hiệu ứng trong `stickman_assets/manifest.json`; sáu hiệu ứng mới là `sparkle`, `sweat`, `question`, `impact`, `anger`, `rain`. Hiệu ứng trong `acting_sequence` chạy theo từng mốc diễn; `effect` ở câu thoại sẽ ghi đè hiệu ứng của chuỗi. Bỏ trường này nếu cảnh không cần VFX.

## Đầu ra

- `video.mp4`: video có thoại và animation.
- `subtitles.srt`: phụ đề rời.
- `contact_sheet.png`: một khung tiêu biểu từ mỗi đoạn để xem nhanh.
- `timed_plan.json`: mốc thoại và hình đã căn theo giọng đọc.
- `qa_report.json`: kiểm tra luồng âm thanh, hình ảnh, thời lượng, số đoạn/câu và các kiểu hình được dùng.
- `dialogue.wav`, `audio_lines/`: âm thanh để dựng lại hoặc sửa riêng.

## Khả năng hiện tại

Hỗ trợ một hoặc hai nhân vật và 12 kiểu hình: chữ, bảng, biểu đồ điểm/đường thẳng, công thức, so sánh, các bước, điện thoại, thung lũng sai số, cửa hàng, hình minh họa có sẵn, ảnh ngoài và màn hình kết. Có thể chọn từ 88 pose, 27 biểu cảm, 10 VFX và 6 hình minh họa trong `../stickman_assets/manifest.json`. ZIP kèm 12 chuỗi diễn xuất WebP/JSON trong `stickman_assets/sequences/` để dùng trực tiếp trong plan hoặc ghép riêng. Với hình có sẵn, dùng `{"type":"illustration","name":"parcel_route"}`. `image` nhận PNG/JPG đã có khi một kịch bản cần ảnh riêng. Lệnh kiểm tra sẽ báo thiếu ảnh trước khi dựng.

Chất lượng hình thức và nhịp dựng được giữ cố định bằng mã. `--source` đối chiếu các lượt thoại có nhãn người nói để bắt lỗi bỏ sót hoặc viết lại câu; nếu kịch bản không có nhãn thoại, có thể bỏ tùy chọn này. Nội dung mới vẫn cần xem lại số liệu, phép tính, hình được model chọn và phát âm thuật ngữ. Bộ kiểm tra không thể chứng minh một lời giải thích khoa học là đúng.

## Môi trường

Máy hiện tại đã có hai môi trường Python: Python mặc định chạy Pillow và `resvg-py` để dựng hình; Python 3.11 chạy VieNeu, NumPy và SoundFile để tạo giọng. `build.py` tự gọi cả hai. FFmpeg/FFprobe phải ở `PATH`. Rig được đọc từ `../stickman_assets/stickman.py`; font Noto Sans đọc từ `../phan_tram_stickman_video/NotoSans.ttf` với giấy phép SIL OFL trong cùng thư mục.
