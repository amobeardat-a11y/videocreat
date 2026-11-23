# Video thử: AI không biết giá ship, nhưng lại dám dự đoán?

Video 16:9, 1280×720, 18 fps, dựng từ sáu cảnh trong kịch bản người dùng cung cấp. Nam và Minh dùng hai giọng tổng hợp tiếng Việt khác nhau; đồ họa và animation người que được vẽ bằng mã. Thời lượng thực tế khoảng 4 phút 20 giây.

## Tệp sử dụng

- `linear_regression_stickman.mp4`: video hoàn chỉnh có tiếng và chữ thoại trên màn hình.
- `subtitles.srt`: phụ đề rời cho trình phát hoặc phần mềm dựng.
- `dialogue.json`: thoại, nhân vật và tín hiệu hình ảnh theo từng cảnh.
- `timed_dialogue.json`: mốc thời gian thực tế của từng câu sau khi căn giọng đọc.
- `dialogue.wav`: bản âm thanh ghép từ giọng Nam và Minh.
- `prepare_audio.py`, `build_timeline.py`, `render_video.py`: mã tạo lại video.

Video minh họa bảng dữ liệu, bốn điểm trên đồ thị, đường hồi quy, sai số, MSE, gradient descent, dự đoán 28.000đ và tình huống giá thực tế 55.000đ. Với bốn điểm (1,15), (2,19), (3,21), (4,25), nghiệm bình phương tối thiểu là `ŷ = 3,2x + 12`, nên tại 5 km mô hình dự đoán 28 nghìn đồng. Giá 55 nghìn trong câu chuyện là tình huống hư cấu để giải thích ảnh hưởng của biến còn thiếu.

## Dựng lại

Chạy từ thư mục dự án này, trên máy đã cài VieNeu, NumPy, SoundFile, Pillow, `resvg-py` và FFmpeg:

```powershell
py -3.11 prepare_audio.py
py -3.11 build_timeline.py
python render_video.py
```

Mã dựng hình dùng rig `../stickman_assets/stickman.py` và font Noto Sans trong `../phan_tram_stickman_video/`. Font được cung cấp theo giấy phép SIL OFL ở thư mục video trước.
