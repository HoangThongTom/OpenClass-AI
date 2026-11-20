# Harris Corner Detection — Ghi chú mẫu

## Mục tiêu

- Phân biệt vùng phẳng, cạnh và góc trong một ảnh xám.
- Hiểu gradient ảnh Ix, Iy và cấu trúc tensor M.
- Mô tả công thức Harris response.

## Trực giác

- Vùng phẳng: dịch chuyển cửa sổ theo bất kỳ hướng nào hầu như không đổi cường độ.
- Cạnh: dịch chuyển cửa sổ vuông góc với cạnh gây biến thiên lớn.
- Góc: dịch chuyển theo hai phương độc lập đều làm thay đổi cường độ.

## Ma trận cấu trúc

M = [[sum(w Ix^2), sum(w Ix Iy)], [sum(w Ix Iy), sum(w Iy^2)]]

Tổng lấy trong một cửa sổ và w là trọng số Gaussian tùy chọn.

## Harris response

R = det(M) - k * trace(M)^2

Trong thực nghiệm k thường gần 0.04 đến 0.06, nhưng cần hiệu chỉnh cho ảnh và phương pháp tính gradient.

- R lớn, dương: khả năng là góc.
- R âm: khả năng là cạnh.
- |R| nhỏ: vùng phẳng hoặc tín hiệu yếu.

Để chọn điểm góc, ta ngưỡng hóa R và dùng non-maximum suppression (NMS).
