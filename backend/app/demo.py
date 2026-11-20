DEMO = {
    "summary": "Khám phá cách thuật toán Harris phát hiện góc từ sự thay đổi cường độ ảnh và ma trận cấu trúc.",
    "slides": [
        {
            "title": "Vì sao chúng ta cần phát hiện góc?",
            "key_point": "Góc là các đặc trưng ảnh dễ nhận biết lại khi góc nhìn thay đổi.",
            "bullets": [
                "Vùng phẳng: cường độ ảnh ít thay đổi theo mọi hướng.",
                "Cạnh: thay đổi mạnh theo một hướng.",
                "Góc: thay đổi mạnh theo hai hướng độc lập."
            ],
            "speaker_notes": "So sánh một ô bàn cờ trống, ranh giới hai ô và giao điểm của bốn ô."
        },
        {
            "title": "Structure tensor",
            "key_point": "Ma trận M tóm tắt độ biến thiên gradient trong một vùng lân cận.",
            "bullets": [
                "Tính đạo hàm ảnh Ix và Iy.",
                "Trong một cửa sổ, tích lũy Ix², IxIy và Iy² có trọng số.",
                "Hai trị riêng lớn của M biểu thị thay đổi mạnh theo hai hướng."
            ],
            "speaker_notes": "Liên hệ các trị riêng với hình dạng vùng ảnh: phẳng, cạnh và góc."
        },
        {
            "title": "Harris response",
            "key_point": "R = det(M) − k · trace(M)²",
            "bullets": [
                "Nếu R lớn và dương, điểm có xu hướng là góc.",
                "Nếu R âm, điểm có xu hướng là cạnh.",
                "Nếu |R| nhỏ, điểm thường thuộc vùng phẳng.",
                "Dùng threshold và non-maximum suppression để chọn điểm góc."
            ],
            "speaker_notes": "Mở Harris Lab bên cạnh để thử thay đổi hệ số k."
        }
    ],
    "quiz": [
        {
            "question": "Điểm góc có đặc trưng gradient như thế nào?",
            "options": ["Không thay đổi ở mọi hướng", "Thay đổi mạnh ở hai hướng", "Chỉ thay đổi theo một hướng", "Luôn có cường độ bằng 0"],
            "correct_index": 1,
            "explanation": "Góc thay đổi rõ rệt khi dịch chuyển cửa sổ theo cả hai hướng."
        },
        {
            "question": "Structure tensor sử dụng những đại lượng nào?",
            "options": ["Ix, Iy và tích của chúng", "Tọa độ GPS", "Chỉ giá trị màu đỏ", "Chỉ kích thước ảnh"],
            "correct_index": 0,
            "explanation": "M được xây từ bình phương và tích chéo các đạo hàm không gian của ảnh."
        },
        {
            "question": "Công thức phản hồi Harris là gì?",
            "options": ["R = trace(M)", "R = det(M) + k", "R = det(M) − k·trace(M)²", "R = Ix + Iy"],
            "correct_index": 2,
            "explanation": "Harris kết hợp định thức và bình phương vết của structure tensor."
        }
    ],
    "flashcards": [
        {"front": "Gradient ảnh", "back": "Mức độ thay đổi cường độ ảnh theo các hướng x và y."},
        {"front": "Structure tensor", "back": "Ma trận 2×2 biểu diễn thống kê gradient trong vùng lân cận."},
        {"front": "Non-maximum suppression", "back": "Giữ cực đại cục bộ của phản hồi góc, loại các điểm lân cận yếu hơn."}
    ]
}
