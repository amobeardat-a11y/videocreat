# Stickman Assets v6

Bộ người que và hình minh họa vector để dựng video. Gói có **88 động tác** dạng SVG tĩnh và WebP động, **27 biểu cảm**, **10 VFX**, **12 chuỗi diễn xuất** và **6 hình minh họa** dạng SVG/PNG. Tám động tác mới gồm nhìn xa, cúi kiểm tra, đo khoảng rộng, trấn an, từ chối, đi suy nghĩ, gọi lớn và mừng nhẹ. ZIP chỉ chứa asset sử dụng được và mã dựng; không chứa ảnh thử hoặc contact sheet.

## Cấu trúc

- `animations/*.webp`: vòng lặp 2 giây, 18 fps, rộng 400 px, nền trong suốt. Một số động tác nhanh lặp nhiều nhịp trong clip. Có thể đưa vào trình dựng video hoặc chuyển sang chuỗi PNG.
- `svg/poses/*.svg`: một frame vector sạch cho mỗi động tác.
- `svg/expressions/*.svg`: khuôn mặt vector độc lập. Dùng `--expression` để thay biểu cảm trên bất kỳ động tác nào.
- `manifest.json`: danh mục tên, nhịp chuyển động và thông số xuất.
- `CATALOG.md`: danh sách động tác theo nhóm.
- `stickman.py`: rig, các nhịp chuyển động và công cụ xuất video.
- `story_animation.py`: ghép pose thành một cảnh liên tục, điều khiển vị trí, hướng nhìn, biểu cảm và hiệu ứng phản ứng.
- `vfx.py`: vẽ hiệu ứng vector theo thời gian; mỗi VFX là một lớp riêng và có thể ghép lên bất kỳ pose nào.
- `illustrations.py` và `illustrations/{svg,png}/*`: sáu hình minh họa không chứa chữ, dùng lại ở nhiều kịch bản.
- `sequences/*.json` và `sequences/*.webp`: mười hai chuỗi diễn xuất ngắn, nền trong suốt, có thể dùng ngay hoặc sửa theo cảnh.
- `story_demo.json`: ví dụ dài với đi, bất ngờ, suy nghĩ, chạy và ăn mừng trong một lượt diễn.

## Sử dụng

Từ thư mục `stickman_assets`:

```powershell
python -m pip install -r requirements.txt
python stickman.py package --zip ../stickman_assets.zip
python stickman.py loop wave wave.mp4 --format mp4 --fps 24 --duration 3 --width 800
python stickman.py loop talk frames --format png --fps 24 --expression excited
python stickman.py transition idle wave idle_to_wave.webp --duration 0.5
python stickman.py frame think --phase 0.35 --expression curious > frame.svg
```

`webp` và `png` giữ alpha để ghép lên cảnh khác; `mp4` xuất nền trắng và cần `ffmpeg` trong PATH. `--format png` ghi `frame_0000.png`... vào thư mục chỉ định. `phase` từ 0 đến 1, animation lặp mượt ở điểm nối. Có thể import `frame_svg`, `transition_svg`, `motion_state` để kết hợp với timeline video của bạn.

Các động tác di chuyển như `walk`, `run`, `march`, `tiptoe`, `side_step` và `pace` là chu kỳ **tại chỗ**; khi dựng cảnh, hãy dịch chuyển nhân vật trên timeline riêng. Pose `sit` chỉ có người, bạn có thể ghép ghế ở lớp cảnh riêng. Biểu cảm có thể đổi ở từng frame, kể cả nháy mắt hoặc khẩu hình nói. File WebP không có âm thanh.

## Chuỗi animation cho cảnh truyện

Mỗi tệp trong `sequences/` có bản WebP nền trong suốt để ghép ngay và bản JSON để đổi nhịp diễn. Bản này thêm `spot_and_measure` (tìm rồi đo đạc) và `calm_after_conflict` (tranh cãi rồi hòa giải). Danh sách đủ 12 chuỗi nằm trong `manifest.json`. Nhân vật ở phía trái hoặc di chuyển theo cảnh, chừa khoảng trống cho hình minh họa và chữ.

```powershell
python story_animation.py story_demo.json story_motion_demo.mp4 --format mp4 --fps 24 --width 1280
python story_animation.py sequences/arrival_greeting.json greeting.webp --format webp --fps 18 --width 960 --transparent
python story_animation.py sequences/confusion_to_idea.json frames --format png --fps 24 --width 960 --transparent
```

Trong JSON, `canvas` là kích thước cảnh; `initial_x`, `ground_y`, `scale` đặt người que. Mỗi mốc trong `beats` có `pose`, `duration`, `to_x`, `transition` (đơn vị giây); có thể thêm `facing` (`1` hoặc `-1`), `expression`, `effect` (một trong 10 tên trong `manifest.json`). `pose` và `expression` cũng lấy tên trong manifest. MP4 có màu nền của cảnh; PNG/WebP dùng `--transparent` để ghép lớp.
