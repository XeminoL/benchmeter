# benchmeter

Đo xem một câu lệnh có thật sự nhanh hơn câu lệnh khác, hay ta chỉ đang nhìn vào nhiễu.

Phần lớn các trường hợp là nhiễu. Đó chính là lý do công cụ này tồn tại.

## Câu chuyện quen thuộc

Một người sửa đoạn mã, chạy thử hai lần, rồi báo lại: "bản mới nhanh hơn 15%, triển khai thôi."

Ta chạy lại và nhận kết quả ngược. Không ai nói dối cả. Chỉ là cái máy lúc ấy đang ở một tâm trạng khác.

Tôi đã nghe câu chuyện đó quá nhiều lần, nên quyết định đo xem nó xảy ra thường xuyên đến đâu. Trên một chiếc laptop bình thường, đem một câu lệnh so với **bản sao y hệt của chính nó**, cách đo thông thường kết luận rằng chúng khác nhau trong **62% số lần thử**. Cùng một câu lệnh. Cùng một cái máy. Hai phần ba câu trả lời là sai.

Công cụ này kéo con số đó xuống còn khoảng 4%. Và khi vẫn chưa đủ cơ sở để kết luận, nó nói thẳng ra điều đó thay vì bốc một con số cho có.

## Mở bằng trình duyệt

Nhấn đúp vào `launchers/benchmeter.cmd` nếu dùng Windows, hoặc `launchers/benchmeter.sh` nếu dùng macOS và Linux. Một trang web mở ra ngay trên máy.

Gõ hai câu lệnh, bấm nút, đọc kết quả. Không cần tài khoản, không có gì rời khỏi máy. Nếu chưa có Python, nó chỉ luôn chỗ tải về.

Ai quen dòng lệnh hơn:

```
python -m benchmeter.cli --web
```

Trang sẽ đo máy, chạy lệnh của ta, rồi đưa ra một con số hoặc nói rõ là không thể. Kết quả sao chép được thành văn bản thuần, in ra giấy cũng được.

## Hoặc dùng thẳng dòng lệnh

```bash
python -m benchmeter.cli "python cu.py" "python moi.py"
```

Chỉ có hai loại câu trả lời.

Khi khác biệt là thật:

```
  variant is 12.4% faster than baseline
  95% confidence interval: -15.1% to -9.7%
  confidence: high
```

Khi không phải:

```
  NO CONCLUSION
  Observed difference 3.1%, but the confidence interval runs
  from -1.2% to +7.4%
  -> that interval includes zero, so equal speed has not been ruled out.

  What to do next:
    - Machine is drifting 22%. Close other applications and measure again.
    - About 180 more rounds would likely settle it.
```

Câu trả lời thứ hai mới là câu đáng giá. Những công cụ khác sẽ thả cho ta con số "nhanh hơn 3,1%" rồi để ta tự tin hành động theo nó.

## Biết giới hạn của cái thước

```
python -m benchmeter.cli --check-machine
```

```
  grade           : noisy
  drift           : 40.4%
  resolves from   : 2.6%
```

Dòng cuối là giới hạn của dụng cụ đo. Trên chiếc máy này, mọi khác biệt nhỏ hơn 2,6% đều nằm dưới sàn nhiễu, và đo bao nhiêu lần cũng không tìm ra được. Biết điều đó trước sẽ đỡ mất một buổi chiều đi truy một con số 1%.

## Đừng tin lời tôi

```
python -m benchmeter.cli --self-proof
```

Lệnh này đo **đúng một tác vụ duy nhất**, chia đôi số mẫu thu được, rồi đem hai nửa so với nhau. Chúng vốn là một, nên mọi kết luận "khác biệt có ý nghĩa" đều là lời nói dối, theo định nghĩa. Nó đếm số lời nói dối đó.

Kết quả trên chiếc laptop tôi viết công cụ này:

```
                        Python       C
máy trôi                 29.8%   106.8%
đo tuần tự → báo sai     62.2%    40.7%
đo xen kẽ  → báo sai      4.1%     0.0%
```

Cột C có mặt ở đây vì ai cũng sẽ nghĩ ngay: "chắc do bộ dọn rác của Python thôi." Không phải. Trong C câu chuyện y hệt.

## Vì sao nó hoạt động

Không nhờ thống kê tinh vi nào. Chỉ là đổi thứ tự làm việc.

Người ta thường đo A một trăm lần, rồi đo B một trăm lần. Trong khoảng giữa đó, máy nóng lên, Windows quyết định lập chỉ mục thứ gì đó, CPU hạ tần vì laptop đang chạy pin. Toàn bộ chênh lệch ấy đổ lên đầu B, và B bị quy tội.

Công cụ này chạy **xen kẽ** — A, B, A, B — và xáo thứ tự mỗi vòng. Máy đang làm gì ở thời điểm nào thì cả hai câu lệnh cùng ngồi trong đó.

Ba điều nhỏ hơn xây thêm trên nền ấy:

- Dùng trung vị, nên một lần chạy bất hạnh đúng lúc phần mềm diệt virus thức giấc sẽ không kéo lệch mọi thứ.
- Giữ nguyên từng cặp A/B khi tính khoảng tin cậy, bởi chúng chạy cách nhau vài giây dưới cùng một điều kiện.
- Từ chối báo một khác biệt nhỏ hơn mức máy thật sự phân biệt được, kể cả khi phép thống kê nghe rất thuyết phục.

## Những gì nó còn làm

```bash
# đặt tên cho dễ đọc kết quả
python -m benchmeter.cli "python a.py" "python b.py" --label cu --label moi

# so nhiều hơn hai
python -m benchmeter.cli "a.py" "b.py" "c.py"

# cho thêm thời gian, dành cho khác biệt nhỏ mà thật
python -m benchmeter.cli "a" "b" -t 60

# dùng trong kịch bản và CI
python -m benchmeter.cli "a" "b" --json

# cùng hạt giống, cùng kết quả, hữu ích khi ai đó không tin số của ta
python -m benchmeter.cli "a" "b" --seed 42

# ghi lại và so với lần trước
python -m benchmeter.cli "a" "b" --save --note "truoc khi them cache"
```

Mã thoát: `0` có khác biệt, `1` có lỗi, `2` không kết luận được. Cái cuối quan trọng nếu ta dựng cổng chặn cho bản build — một lần thất bại phải nghĩa là "cái này chậm đi", không phải "máy chạy CI lúc đó đang bận".

Bản ghi lưu kèm cả tình trạng máy. Đem so với tuần trước mà máy đang ở trạng thái khác, nó sẽ nói ra, thay vì quy tội cho đoạn mã.

## Những gì nó không làm

**Nó không làm máy ta yên tĩnh lại.** Tôi đã thử. Ghim tiến trình vào một nhân, nâng độ ưu tiên, tắt bộ dọn rác — cả ba đều hoặc thất bại thẳng vì không có quyền quản trị, hoặc chẳng thay đổi gì đo được. Nên nó chọn phát hiện và báo, thay vì hứa hẹn.

**Nó chậm hơn cách đếm lệnh.** Muốn một con số y hệt nhau mọi lần thì `cachegrind` đếm số lệnh CPU với phương sai gần như bằng không. Nhưng nó chậm, và nó bỏ qua những gì phần cứng thật sự làm, như dự đoán nhánh. Câu hỏi khác thì dùng dụng cụ khác.

**Cái mẹo xen kẽ không phải của tôi.** Trong tài liệu nghiên cứu nó có tên là RMIT. Việc tôi làm là đóng gói để dùng được, và dạy nó im lặng khi không biết.

**Nó chạy bất cứ thứ gì ta gõ vào.** Máy chủ chỉ lắng nghe trên loopback và từ chối những yêu cầu không đến từ trang của chính nó, nhưng nó vẫn thực thi câu lệnh ta đưa. Đừng dán vào đó thứ mà ta không dám tự chạy.

**Một cái máy, một hệ điều hành.** Mọi con số phía trên đo trên duy nhất một chiếc laptop Windows. Số của ta sẽ khác. Chạy `--self-proof` rồi biết.

## Chạy kiểm thử

```
python -m unittest discover tests
```

31 bài. Đáng chú ý nhất nằm trong `test_false_positives.py` — nó nạp vào những trường hợp đã biết trước đáp án: các mẫu sinh từ cùng một nguồn thì tuyệt đối không được gọi là khác nhau, và một khác biệt gấp đôi thì tuyệt đối không được bỏ sót. Rồi đếm số lần trả lời sai.

Một công cụ tự chấm bài mình thì không phải bằng chứng.

## Nó đến từ đâu

Từ môn thí nghiệm vật lý đại cương. Mọi phép đo đều phải kèm sai số; một con số trần trụi thì bị trừ điểm.

Rồi bước vào ngành phần mềm và thấy người ta công bố kết quả đo hiệu năng không kèm thanh sai số nào, mà chẳng ai thấy có vấn đề.

Hóa ra chuyện này đã được biết. Mytkowicz và cộng sự rà 133 bài báo từ bốn hội nghị hệ thống lớn và không tìm được bài nào xử lý độ chệch phép đo cho đúng. Sinh viên năm nhất ngành vật lý đang làm việc này chặt chẽ hơn các nhà khoa học máy tính.
