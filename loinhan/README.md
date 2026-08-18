# Đo lại bằng C

Python có bộ dọn rác và lớp thông dịch — bản thân chúng tạo nhiễu. Nếu con số đo trong C vẫn giống trong Python thì nhiễu là do **máy**, không phải do ngôn ngữ.

```bash
gcc -O2 -Wall -o dolai dolai.c -lm
./dolai 20000
```

## Kết quả trên máy thử (i7-1185G7, không GPU rời)

```
                        Python      C
máy trôi trong lúc đo    29,8%    106,8%
tuần tự báo sai          62,2%     40,7%
xen kẽ  báo sai           4,1%      0,0%
```

Kết luận: nhiễu không đến từ Python. Đổi sang C không cứu được — chỉ đổi **cách đo** mới cứu được.

## Ba cái bẫy gặp phải khi viết file này

Cả ba đều là bẫy kinh điển khi đo hiệu năng bằng C, và cả ba đều làm kết quả ra `0 ns`:

**1. Trình biên dịch xoá vòng lặp.** Với `-O2`, nếu kết quả tính ra không ai dùng thì gcc xoá sạch vòng lặp. Chữa bằng cách ghi kết quả vào biến `volatile`.

**2. Trình biên dịch tính sẵn kết quả.** Nếu mọi lần gọi đều cho cùng một giá trị, gcc chỉ chạy một lần rồi tái dùng. Chữa bằng cách truyền tham số thay đổi mỗi lần gọi.

**3. Tác vụ nhanh hơn độ phân giải đồng hồ.** Đồng hồ bước 100 ns mà tác vụ mất 50 ns thì phần lớn phép đo ra 0. Chữa bằng cách lặp tác vụ nhiều lần trong một phép đo rồi chia ra.

Cái thứ ba đúng là bài học "biết giới hạn dụng cụ đo" của môn thí nghiệm vật lý — thước chia tới milimet thì không đo được vật nhỏ hơn milimet.
