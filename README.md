# doluong

Đo phần mềm chạy nhanh hay chậm — và biết khi nào không đủ tin để trả lời.

```
$ python -m doluong.giaodien "cach_cu.py" "cach_moi.py"

  CHUA KET LUAN DUOC
  Do duoc chenh lech 3.1%, nhung khoang tin cay tu -1.2% den +7.4%
  -> khoang nay bao gom ca 0, tuc chua loai tru duoc kha nang
     hai lenh nhanh nhu nhau.

  Lam gi tiep:
    - May dang troi 22%. Dong bot ung dung roi do lai.
    - Do them khoang 180 vong nua co the du.
```

## Vấn đề

Máy tính lúc nhanh lúc chậm. Đo cùng một tác vụ hai lần sẽ ra hai số khác nhau.

Công cụ đo hiện tại vẫn đưa ra con số, kể cả khi con số đó không phân biệt được với nhiễu. Người dùng tin theo, rồi chọn sai cách viết, tối ưu nhầm chỗ.

Chạy thử trên máy bất kỳ:

```
python -m doluong.giaodien --tu-chung-minh
```

Nó đo **cùng một tác vụ** rồi tự chia đôi để so. Mọi kết luận "hai bên khác nhau" đều sai, vì chúng vốn là một.

Kết quả đo trên một laptop thường:

```
                        Python       C
máy trôi trong lúc đo    29.8%   106.8%
đo tuần tự → báo sai     62.2%    40.7%
đo xen kẽ  → báo sai      4.1%     0.0%
```

Cột C có ở [`loinhan/`](loinhan/) — viết lại bằng C để loại trừ khả năng nhiễu đến từ bộ dọn rác của Python. Vẫn thấy máy trôi, vẫn thấy báo sai. Nhiễu là do **máy**, không do ngôn ngữ.

## Cách làm

**Đo xen kẽ.** Không đo hết A rồi mới đo B. Chạy `A, B, A, B...` và xáo thứ tự mỗi vòng, để cả hai cùng chịu một điều kiện máy tại mọi thời điểm.

**Ghép đôi từng cặp.** Lần thứ *i* của A và lần thứ *i* của B chạy sát nhau nên chịu cùng trạng thái máy. Bootstrap giữ nguyên sự ghép đó thay vì trộn lẫn.

**Dùng trung vị.** Chống được giá trị lạc do hệ điều hành chen ngang.

**Từ chối trả lời khi khoảng tin cậy còn chứa số 0.** Chưa loại trừ được khả năng hai bên nhanh như nhau thì không kết luận.

**Từ chối luôn khi chênh lệch nằm dưới ngưỡng phân giải của máy.** Máy trôi 48% mà báo "chậm hơn 1,9%" là kết luận nằm dưới mức máy có thể phân biệt — khoảng tin cậy không biết điều đó, vì nó chỉ nói về đám mẫu đã thu được.

## Dùng

```bash
# so hai lệnh
python -m doluong.giaodien "lenh A" "lenh B"

# đặt tên cho dễ đọc
python -m doluong.giaodien "python cu.py" "python moi.py" \
    --nhan "cách cũ" --nhan "cách mới"

# so nhiều hơn hai
python -m doluong.giaodien "a.py" "b.py" "c.py"

# giới hạn thời gian đo (giây)
python -m doluong.giaodien "a" "b" -t 60

# kiểm máy trước khi đo
python -m doluong.giaodien --kiem-may

# xuất json để đưa vào chỗ khác
python -m doluong.giaodien "a" "b" --json

# lặp lại y hệt lần trước
python -m doluong.giaodien "a" "b" --hat-giong 42
```

Mã thoát: `0` có kết luận · `1` lỗi · `2` không đủ tin để kết luận.

## Kiểm máy

```
$ python -m doluong.giaodien --kiem-may

  xep loai        : on ao
  do troi         : 40.4%
  phan biet duoc  : tu 2.6% tro len
```

Dòng cuối là giới hạn của máy: chênh lệch nhỏ hơn ngưỡng đó thì máy này không phân biệt được, đo bao nhiêu lần cũng vậy.

## Chạy kiểm thử

```
python -m unittest discover kiemthu
```

15 bài kiểm, trong đó có bộ nghiệm giả: đưa vào trường hợp biết trước đáp án rồi đếm tỉ lệ báo sai.

## Vì sao không cố làm máy ổn định

Có ba cách quen thuộc: ghim tiến trình vào một nhân CPU, nâng độ ưu tiên, tắt bộ dọn rác. Đã thử cả ba (`--on-dinh`), kết quả trên máy thường không có quyền quản trị:

```
ghim nhân CPU  → thất bại, hệ điều hành từ chối
nâng ưu tiên   → thất bại
tắt dọn rác    → làm được, nhưng độ trôi KHÔNG giảm
                 (trung vị 28.8% → 83.8% qua 5 lần đo mỗi bên)
```

Nên công cụ chọn hướng **phát hiện và báo** thay vì hứa làm máy ổn định. Cờ `--on-dinh` vẫn còn cho máy có quyền đầy đủ, nhưng mặc định tắt và thất bại thì báo rõ.

## Giới hạn

- Đo thời gian thật nên chậm hơn đếm lệnh CPU. Cần chính xác tuyệt đối thì dùng `cachegrind`.
- Không sửa được máy trôi, chỉ phát hiện và báo.
- Cách xen kẽ đã có trong nghiên cứu với tên RMIT (Randomized Multiple Interleaved Trials). Phần mới ở đây là đóng gói thành công cụ dùng được và **biết từ chối trả lời**.
- Chưa hỗ trợ đo trên nhiều máy.

## Nguồn gốc

Bắt đầu từ một câu hỏi trong môn thí nghiệm vật lý đại cương: môn học dạy mọi phép đo phải kèm sai số — vậy tại sao đo hiệu năng phần mềm lại không?

Hoá ra ngành phần mềm đã biết vấn đề này. Mytkowicz và cộng sự khảo sát 133 bài báo từ ASPLOS, PACT, PLDI, CGO và không tìm thấy bài nào xét đúng độ chệch phép đo.
