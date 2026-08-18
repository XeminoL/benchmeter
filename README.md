# benchmeter

Công cụ so sánh thời gian chạy của hai câu lệnh, có kèm đánh giá độ tin cậy của kết quả.

## Vấn đề

Thời gian chạy của một chương trình không phải hằng số. Cùng một câu lệnh, cùng một máy, hai lần đo cho hai kết quả khác nhau: tần số CPU thay đổi theo nhiệt độ và nguồn điện, hệ điều hành chen tiến trình khác vào, bộ nhớ đệm nóng lên rồi nguội đi.

Hệ quả là phần lớn khác biệt quan sát được giữa hai phiên bản mã nằm trong khoảng nhiễu của phép đo, chứ không phản ánh khác biệt thật.

Thử nghiệm trên một laptop thông thường: lấy một câu lệnh, so nó với bản sao y hệt của chính nó, dùng cách đo phổ biến (chạy hết A rồi chạy hết B, so trung bình bằng công thức sai số chuẩn chia căn N). Kết quả báo hai bên khác nhau trong **62% số lần thử**, dù chúng là một.

Cách đo mà công cụ này dùng hạ tỉ lệ đó xuống khoảng **4%**, và không kết luận khi dữ liệu chưa đủ.

## Cài đặt và chạy

Yêu cầu Python 3.9 trở lên, không cần thư viện ngoài.

Giao diện web, chạy hoàn toàn trên máy cục bộ:

```
python -m benchmeter.cli --web
```

Trên Windows có thể nhấn đúp `launchers/benchmeter.cmd`; trên macOS và Linux là `launchers/benchmeter.sh`. Hai tệp này tự tìm trình thông dịch phù hợp và chỉ dẫn nếu chưa có Python.

Dòng lệnh:

```bash
python -m benchmeter.cli "python cu.py" "python moi.py"
```

## Kết quả

Có hai dạng đầu ra.

Khi khoảng tin cậy nằm hẳn một phía của mốc không:

```
  variant is 12.4% faster than baseline
  95% confidence interval: -15.1% to -9.7%
  confidence: high
```

Khi chưa loại trừ được khả năng hai bên bằng nhau:

```
  NO CONCLUSION
  Observed difference 3.1%, but the confidence interval runs
  from -1.2% to +7.4%
  -> that interval includes zero, so equal speed has not been ruled out.

  What to do next:
    - Machine is drifting 22%. Close other applications and measure again.
    - About 180 more rounds would likely settle it.
```

Trường hợp thứ hai là phần khác biệt chính so với các công cụ tương tự: thay vì trả về con số 3,1% để người dùng tự diễn giải, nó nêu rõ dữ liệu chưa đủ và cần làm gì tiếp.

## Đo đặc tính máy

```
python -m benchmeter.cli --check-machine
```

```
  grade           : noisy
  drift           : 40.4%
  resolves from   : 2.6%
```

Công cụ chạy một tác vụ có khối lượng cố định nhiều lần. Vì tác vụ không đổi, mọi biến động quan sát được đều đến từ máy.

Dòng cuối là sàn phân giải: trên máy này, khác biệt nhỏ hơn 2,6% nằm dưới mức nhiễu và không xác định được, bất kể số lần đo.

## Kiểm chứng độc lập

```
python -m benchmeter.cli --self-proof
```

Lệnh này đo một tác vụ duy nhất, chia số mẫu thành hai nửa theo thứ tự thu được, rồi so hai nửa với nhau bằng cả hai phương pháp. Vì hai nửa cùng một tác vụ, mọi kết luận "khác biệt có ý nghĩa" đều là dương tính giả và đếm được.

Số liệu trên máy tham chiếu (Intel i7-1185G7, Windows, không GPU rời):

```
                        Python       C
biến động của máy        29.8%   106.8%
đo tuần tự → sai         62.2%    40.7%
đo xen kẽ  → sai          4.1%     0.0%
```

Cột C nhằm loại trừ giả thuyết nhiễu đến từ bộ dọn rác và lớp thông dịch của Python. Mã nguồn ở `native/verify.c`.

## Phương pháp

**Đo xen kẽ.** Mỗi vòng chạy cả hai câu lệnh một lần, thứ tự xáo ngẫu nhiên. Cách đo tuần tự đặt toàn bộ số mẫu của B vào một khoảng thời gian khác với A, nên mọi biến động của máy trong khoảng giữa được quy hết cho B. Đo xen kẽ phân bố biến động đều cho cả hai.

**Trung vị thay trung bình.** Giá trị lạc do hệ điều hành chen ngang không kéo lệch kết quả.

**Bootstrap theo cặp.** Lần chạy thứ *i* của A và thứ *i* của B diễn ra cách nhau vài giây dưới cùng điều kiện. Lấy mẫu lại theo cặp giữ nguyên quan hệ đó thay vì trộn lẫn hai chuỗi.

**Chặn dưới theo sàn phân giải.** Khoảng tin cậy chỉ mô tả tập mẫu đã thu, không biết máy đang biến động. Công cụ yêu cầu khác biệt vượt sàn phân giải của máy mới kết luận.

Cách đo xen kẽ nhiều tầng có tên trong tài liệu nghiên cứu là *randomised multiple interleaved trials* (RMIT).

## Tuỳ chọn

```bash
# đặt tên hiển thị
python -m benchmeter.cli "python a.py" "python b.py" --label cu --label moi

# so nhiều hơn hai câu lệnh
python -m benchmeter.cli "a.py" "b.py" "c.py"

# giới hạn thời gian đo, tính bằng giây
python -m benchmeter.cli "a" "b" -t 60

# đầu ra JSON
python -m benchmeter.cli "a" "b" --json

# cố định hạt giống để lặp lại đúng phép đo
python -m benchmeter.cli "a" "b" --seed 42

# lưu và so với lần đo trước
python -m benchmeter.cli "a" "b" --save --note "truoc khi them cache"
```

Mã thoát: `0` có khác biệt, `1` lỗi, `2` không kết luận được. Phân biệt `0` và `2` cần thiết khi dùng trong CI, để một lần thất bại nghĩa là hiệu năng giảm chứ không phải máy chạy CI đang tải cao.

Bản ghi lưu kèm đặc tính máy tại thời điểm đo. Khi so với lần trước mà máy ở trạng thái khác, công cụ nêu rõ điều này.

## Giới hạn

**Không giảm biến động của máy.** Đã thử ghim tiến trình vào một nhân CPU, nâng độ ưu tiên và tắt bộ dọn rác. Trên máy không có quyền quản trị, hai biện pháp đầu bị hệ điều hành từ chối, biện pháp thứ ba không làm biến động giảm. Công cụ chuyển sang phát hiện và báo.

**Chậm hơn đếm lệnh CPU.** `cachegrind` đếm số lệnh với phương sai gần bằng không, nhưng chạy chậm và không phản ánh các đặc tính phần cứng như dự đoán nhánh hay thực thi song song. Hai công cụ trả lời hai câu hỏi khác nhau.

**Thực thi câu lệnh người dùng nhập.** Máy chủ chỉ lắng nghe trên loopback và từ chối yêu cầu không phát sinh từ trang của chính nó, nhưng vẫn chạy câu lệnh nhận được.

**Số liệu từ một máy.** Mọi con số trong tài liệu này đo trên một laptop Windows. Kết quả trên máy khác sẽ khác; `--self-proof` cho phép tự đo lại.

**Chưa hỗ trợ đo phân tán trên nhiều máy.**

## Kiểm thử

```
python -m unittest discover tests
```

31 bài kiểm thử. Phần chính nằm trong `test_false_positives.py`: nạp các trường hợp đã biết trước đáp án — mẫu sinh từ cùng một phân bố không được báo là khác nhau, khác biệt gấp đôi không được bỏ sót — rồi đếm tỉ lệ trả lời sai.

## Nguồn gốc

Xuất phát từ nguyên tắc trong môn thí nghiệm vật lý đại cương: mọi kết quả đo phải kèm sai số, và phải biết giới hạn phân giải của dụng cụ trước khi tin vào số đo.

Nguyên tắc này ít được áp dụng khi đo hiệu năng phần mềm. Mytkowicz và cộng sự khảo sát 133 bài báo từ ASPLOS, PACT, PLDI và CGO, không tìm thấy bài nào xử lý độ chệch phép đo một cách đầy đủ.