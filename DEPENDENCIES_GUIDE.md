# Hướng dẫn sử dụng Dependencies (Phụ thuộc)

## Tính năng mới: Step Dependencies

Bây giờ bạn có thể tạo các bước có điều kiện - một bước chỉ chạy sau khi các bước khác đã hoàn thành.

## Cách hoạt động

### 1. Step ID
Mỗi bước cần có một **ID duy nhất** để các bước khác có thể tham chiếu đến nó.

### 2. Depends On
Danh sách các Step ID mà bước này phụ thuộc vào.

### 3. Depends Mode
- **any**: Chỉ cần **1 trong các** bước phụ thuộc hoàn thành
- **all**: Cần **TẤT CẢ** các bước phụ thuộc hoàn thành

## Ví dụ thực tế

### Ví dụ 1: Click 3.png sau khi click 1.png HOẶC 2.png

```json
{
  "script_name": "Example with OR condition",
  "steps": [
    {
      "id": "step1",
      "template": "1.png",
      "wait_after_click": 2,
      "description": "Click nút 1"
    },
    {
      "id": "step2",
      "template": "2.png",
      "wait_after_click": 2,
      "description": "Click nút 2"
    },
    {
      "id": "step3",
      "template": "3.png",
      "wait_after_click": 1,
      "description": "Chỉ click sau khi đã click 1.png HOẶC 2.png",
      "depends_on": ["step1", "step2"],
      "depends_mode": "any"
    }
  ]
}
```

**Kết quả**: 
- Tool sẽ tìm và click `1.png` hoặc `2.png`
- Sau khi click được 1 trong 2, tool mới tìm và click `3.png`

### Ví dụ 2: Click 4.png sau khi click CẢ 1.png VÀ 2.png

```json
{
  "script_name": "Example with AND condition",
  "steps": [
    {
      "id": "btn1",
      "template": "1.png",
      "wait_after_click": 1
    },
    {
      "id": "btn2",
      "template": "2.png",
      "wait_after_click": 1
    },
    {
      "id": "btn4",
      "template": "4.png",
      "wait_after_click": 2,
      "depends_on": ["btn1", "btn2"],
      "depends_mode": "all"
    }
  ]
}
```

**Kết quả**:
- Tool phải click được CẢ `1.png` VÀ `2.png`
- Sau đó mới click `4.png`

### Ví dụ 3: Chuỗi phụ thuộc phức tạp

```json
{
  "script_name": "Complex Dependencies",
  "steps": [
    {
      "id": "login",
      "template": "login_btn.png",
      "wait_after_click": 5
    },
    {
      "id": "accept_terms",
      "template": "accept.png",
      "wait_after_click": 2,
      "depends_on": ["login"],
      "depends_mode": "any"
    },
    {
      "id": "start_game",
      "template": "start.png",
      "wait_after_click": 10,
      "depends_on": ["accept_terms"],
      "depends_mode": "any"
    },
    {
      "id": "collect_reward",
      "template": "reward.png",
      "wait_after_click": 2,
      "depends_on": ["start_game"],
      "depends_mode": "any"
    }
  ]
}
```

**Kết quả**: Các bước chạy tuần tự theo chuỗi phụ thuộc.

## Sử dụng trong Script Editor

### Thêm Dependencies:

1. **Step ID**: Nhập ID cho bước (ví dụ: `step1`, `login_btn`)
2. **Depends On (IDs)**: Nhập các ID phụ thuộc, cách nhau bởi dấu phẩy
   - Ví dụ: `step1, step2`
3. **Depends Mode**: Chọn `any` hoặc `all`
   - `any` = HOẶC (chỉ cần 1)
   - `all` = VÀ (cần tất cả)

### Hiển thị trong danh sách:

Các bước có dependencies sẽ hiển thị như sau:
```
step3: 3.png (wait: 1s) [depends: step1, step2]
```

## Lưu ý quan trọng

1. **Step ID phải duy nhất**: Không được trùng ID giữa các bước
2. **Depends On phải tồn tại**: ID trong `depends_on` phải là ID của các bước khác trong script
3. **Tránh vòng lặp**: Không tạo phụ thuộc vòng tròn (A phụ thuộc B, B phụ thuộc A)
4. **Tracking trong mỗi vòng lặp**: Trạng thái "đã hoàn thành" được reset sau mỗi vòng lặp (sau Loop Delay)
5. **Bước không phụ thuộc**: Nếu không có `depends_on`, bước sẽ chạy ngay lập tức

## Các trường hợp sử dụng

### ✅ Tốt:
- Click nút confirm sau khi click nút action
- Collect reward sau khi battle xong
- Next step sau khi popup xuất hiện

### ❌ Tránh:
- Phụ thuộc vòng tròn
- Phụ thuộc vào step không tồn tại
- Quá nhiều dependencies phức tạp (khó debug)

## Troubleshooting

**Q: Bước không bao giờ chạy?**
- Kiểm tra dependencies có được hoàn thành chưa
- Kiểm tra `depends_mode` đúng chưa (any vs all)
- Kiểm tra ID trong `depends_on` có đúng không

**Q: Muốn reset dependencies giữa các vòng lặp?**
- Dependencies tự động reset sau mỗi vòng lặp (Loop Delay)

**Q: Làm sao biết bước nào đã hoàn thành?**
- Hiện tại chưa có log, nhưng bạn có thể thêm description để dễ theo dõi
