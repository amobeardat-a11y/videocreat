# Giao một kịch bản mới cho Gemini Flash / GPT Luna có quyền dùng máy

Thay hai đường dẫn trong khối dưới rồi gửi nguyên khối cho AI làm video. AI cần quyền đọc/ghi thư mục dự án và chạy Python/FFmpeg.

```text
Bạn đang làm việc trong thư mục "video genflow". Hãy dựng video người que từ kịch bản <ĐƯỜNG_DẪN_KỊCH_BẢN.md>, xuất vào <THƯ_MỤC_ĐẦU_RA>.

Đọc stickman_video_factory/README.md và MODEL_PROMPT.md. Dùng bộ dựng có sẵn để giữ đúng phong cách video giá ship: nhân vật bên trái, hình giải thích bên phải, chữ thoại dưới, hai giọng tiếng Việt, chuyển động mềm. Không viết lại trình dựng cho từng kịch bản.

1. Chuyển toàn bộ thoại và chỉ dẫn sân khấu thành một plan JSON theo MODEL_PROMPT.md. Giữ nguyên số liệu, thứ tự lời thoại và các khoảng im lặng có chủ ý. Dùng `acting_sequence` thay cho `pose` khi một câu cần nhiều nhịp diễn liên tiếp; thêm `effect` nếu hiệu ứng giúp làm rõ phản ứng hoặc bối cảnh. Đặt plan cạnh kịch bản; dùng hình code có sẵn, hoặc tạo file ảnh minh họa rồi tham chiếu bằng visual.type=image khi cần.
2. Chạy: python stickman_video_factory/build.py <PLAN.json> --source <ĐƯỜNG_DẪN_KỊCH_BẢN.md> --validate-only. Sửa plan cho đến khi hợp lệ và đối chiếu thoại khớp.
3. Chạy: python stickman_video_factory/build.py <PLAN.json> --source <ĐƯỜNG_DẪN_KỊCH_BẢN.md> --out <THƯ_MỤC_ĐẦU_RA>.
4. Xem contact_sheet.png và các đoạn đầu/giữa/cuối của video.mp4. Kiểm tra số liệu, công thức, hình, tên nhân vật, thời gian và phát âm thuật ngữ. Sửa plan hoặc spoken nếu cần, chạy lại. Kiểm tra qa_report.json và file MP4 phát được.
5. Giao video.mp4, subtitles.srt, contact_sheet.png và plan JSON. Nêu rõ nếu có hình nào chỉ là minh họa giả định hoặc nội dung chưa xác minh.

Hỏi tôi chỉ khi kịch bản không rõ nhân vật nào nói câu nào, có hơn hai nhân vật, hoặc cần hình tư liệu thật mà không có nguồn/asset. Các lựa chọn pose, biểu cảm, nhịp và kiểu minh họa còn lại hãy tự quyết định rồi làm đến bản video xem được.
```

Nếu kịch bản là lời dẫn một người, vẫn dùng cùng bộ dựng với một nhân vật trong `cast`. Bộ dựng hiện hỗ trợ tối đa hai nhân vật trong một video.
