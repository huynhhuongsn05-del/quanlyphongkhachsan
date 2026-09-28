import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime
from pathlib import Path

# =========================================================
# CẤU HÌNH
# =========================================================
st.set_page_config(
    page_title="Hotel Management",
    page_icon="🏨",
    layout="wide",
)

DB = Path("hotel.db")


# =========================================================
# DATABASE
# =========================================================
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def execute(sql, params=(), fetch=False, many=False):
    conn = get_db()
    cur = conn.cursor()

    try:
        if many:
            cur.executemany(sql, params)
        else:
            cur.execute(sql, params)

        result = cur.fetchall() if fetch else None
        conn.commit()
        return result
    finally:
        conn.close()


def execute_insert(sql, params=()):
    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute(sql, params)
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def init_database():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_number TEXT UNIQUE NOT NULL,
            room_type TEXT NOT NULL,
            price REAL NOT NULL,
            floor INTEGER NOT NULL,
            status TEXT DEFAULT 'Trống'
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS guests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            id_card TEXT,
            phone TEXT,
            email TEXT,
            address TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guest_id INTEGER NOT NULL,
            room_id INTEGER NOT NULL,
            check_in TEXT NOT NULL,
            check_out TEXT NOT NULL,
            adults INTEGER DEFAULT 1,
            children INTEGER DEFAULT 0,
            deposit REAL DEFAULT 0,
            status TEXT DEFAULT 'Đã đặt',
            note TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (guest_id) REFERENCES guests(id),
            FOREIGN KEY (room_id) REFERENCES rooms(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            price REAL NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS service_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER NOT NULL,
            service_id INTEGER NOT NULL,
            quantity INTEGER DEFAULT 1,
            FOREIGN KEY (booking_id) REFERENCES bookings(id),
            FOREIGN KEY (service_id) REFERENCES services(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            method TEXT NOT NULL,
            note TEXT,
            paid_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (booking_id) REFERENCES bookings(id)
        )
    """)

    conn.commit()

    # Dữ liệu phòng mẫu
    room_count = cur.execute(
        "SELECT COUNT(*) FROM rooms"
    ).fetchone()[0]

    if room_count == 0:
        rooms = []

        for floor in range(1, 4):
            for number in range(1, 7):
                room_number = f"{floor}{number:02d}"

                if number <= 2:
                    room_type = "Standard"
                    price = 650000
                elif number <= 4:
                    room_type = "Deluxe"
                    price = 850000
                elif number == 5:
                    room_type = "Suite"
                    price = 1200000
                else:
                    room_type = "Villa"
                    price = 1800000

                rooms.append(
                    (
                        room_number,
                        room_type,
                        price,
                        floor,
                        "Trống",
                    )
                )

        cur.executemany("""
            INSERT INTO rooms
            (room_number, room_type, price, floor, status)
            VALUES (?, ?, ?, ?, ?)
        """, rooms)

    # Dịch vụ mẫu
    service_count = cur.execute(
        "SELECT COUNT(*) FROM services"
    ).fetchone()[0]

    if service_count == 0:
        services = [
            ("Bữa sáng", 120000),
            ("Nước suối", 20000),
            ("Giặt ủi", 80000),
            ("Thuê xe máy", 150000),
            ("Taxi", 350000),
            ("Spa", 400000),
        ]

        cur.executemany("""
            INSERT INTO services (name, price)
            VALUES (?, ?)
        """, services)

    conn.commit()
    conn.close()


# =========================================================
# HÀM TIỆN ÍCH
# =========================================================
def money(value):
    value = float(value or 0)
    return f"{value:,.0f} ₫"


def calculate_nights(check_in, check_out):
    start = datetime.strptime(check_in, "%Y-%m-%d").date()
    end = datetime.strptime(check_out, "%Y-%m-%d").date()
    return max((end - start).days, 1)


def update_room_status():
    today = date.today().isoformat()

    # Phòng đang bảo trì giữ nguyên
    execute("""
        UPDATE rooms
        SET status = 'Trống'
        WHERE status != 'Bảo trì'
    """)

    # Booking đang ở
    execute("""
        UPDATE rooms
        SET status = 'Đang ở'
        WHERE id IN (
            SELECT room_id
            FROM bookings
            WHERE status = 'Đang ở'
        )
        AND status != 'Bảo trì'
    """)

    # Booking đã đặt và thời gian chưa kết thúc
    execute("""
        UPDATE rooms
        SET status = 'Đã đặt'
        WHERE id IN (
            SELECT room_id
            FROM bookings
            WHERE status = 'Đã đặt'
              AND check_in >= ?
        )
        AND status != 'Đang ở'
        AND status != 'Bảo trì'
    """, (today,))


def get_booking_total(booking_id):
    booking = execute("""
        SELECT b.*, r.price
        FROM bookings b
        JOIN rooms r ON b.room_id = r.id
        WHERE b.id = ?
    """, (booking_id,), True)

    if not booking:
        return 0

    booking = booking[0]

    room_total = (
        booking["price"]
        * calculate_nights(
            booking["check_in"],
            booking["check_out"],
        )
    )

    service_total = execute("""
        SELECT COALESCE(
            SUM(so.quantity * s.price), 0
        ) AS total
        FROM service_orders so
        JOIN services s ON so.service_id = s.id
        WHERE so.booking_id = ?
    """, (booking_id,), True)[0]["total"]

    return room_total + service_total


def get_booking_paid(booking_id):
    result = execute("""
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM payments
        WHERE booking_id = ?
    """, (booking_id,), True)

    return result[0]["total"] if result else 0


def get_available_rooms(check_in, check_out):
    # Hai khoảng thời gian giao nhau nếu:
    # booking.check_in < requested.check_out
    # và booking.check_out > requested.check_in
    return execute("""
        SELECT *
        FROM rooms r
        WHERE r.status != 'Bảo trì'
          AND NOT EXISTS (
              SELECT 1
              FROM bookings b
              WHERE b.room_id = r.id
                AND b.status IN ('Đã đặt', 'Đang ở')
                AND b.check_in < ?
                AND b.check_out > ?
          )
        ORDER BY r.floor, r.room_number
    """, (check_out, check_in), True)


def guest_label(guest):
    return f'{guest["name"]} - {guest["phone"] or "Không có SĐT"}'


def booking_status_options():
    return ["Đã đặt", "Đang ở", "Đã trả phòng", "Đã hủy"]


# =========================================================
# KHỞI TẠO
# =========================================================
init_database()
update_room_status()


# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.title("🏨 HOTEL SYSTEM")

menu = st.sidebar.radio(
    "MENU",
    [
        "📊 Dashboard",
        "🛏️ Quản lý phòng",
        "👤 Khách hàng",
        "📅 Đặt phòng",
        "🛎️ Check-in / Check-out",
        "🧾 Dịch vụ",
        "💰 Thanh toán",
        "📈 Báo cáo",
    ],
)

st.sidebar.divider()

st.sidebar.info(
    "Hotel Management\n\n"
    "Python + Streamlit + SQLite"
)


# =========================================================
# DASHBOARD
# =========================================================
if menu == "📊 Dashboard":
    st.title("📊 DASHBOARD")

    rooms = execute(
        "SELECT * FROM rooms ORDER BY floor, room_number",
        fetch=True,
    )

    total_rooms = len(rooms)
    empty_rooms = sum(r["status"] == "Trống" for r in rooms)
    occupied_rooms = sum(r["status"] == "Đang ở" for r in rooms)
    booked_rooms = sum(r["status"] == "Đã đặt" for r in rooms)
    maintenance_rooms = sum(
        r["status"] == "Bảo trì" for r in rooms
    )

    today = date.today().isoformat()

    revenue = execute("""
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM payments
        WHERE DATE(paid_at) = DATE(?)
    """, (today,), True)[0]["total"]

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("🏨 Tổng phòng", total_rooms)
    c2.metric("🟢 Phòng trống", empty_rooms)
    c3.metric("🔴 Đang ở", occupied_rooms)
    c4.metric("🟡 Đã đặt", booked_rooms)
    c5.metric("💰 Thu hôm nay", money(revenue))

    st.divider()

    st.subheader("Tình trạng phòng")

    data = []

    for r in rooms:
        data.append({
            "Phòng": r["room_number"],
            "Loại phòng": r["room_type"],
            "Giá / đêm": money(r["price"]),
            "Tầng": r["floor"],
            "Trạng thái": r["status"],
        })

    st.dataframe(
        pd.DataFrame(data),
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        f"Phòng bảo trì: {maintenance_rooms}"
    )


# =========================================================
# QUẢN LÝ PHÒNG
# =========================================================
elif menu == "🛏️ Quản lý phòng":
    st.title("🛏️ QUẢN LÝ PHÒNG")

    tab1, tab2, tab3 = st.tabs(
        [
            "📋 Danh sách phòng",
            "➕ Thêm phòng",
            "🔧 Cập nhật phòng",
        ]
    )

    with tab1:
        rooms = execute("""
            SELECT *
            FROM rooms
            ORDER BY floor, room_number
        """, fetch=True)

        data = []

        for r in rooms:
            data.append({
                "ID": r["id"],
                "Phòng": r["room_number"],
                "Loại": r["room_type"],
                "Giá": money(r["price"]),
                "Tầng": r["floor"],
                "Trạng thái": r["status"],
            })

        st.dataframe(
            pd.DataFrame(data),
            use_container_width=True,
            hide_index=True,
        )

    with tab2:
        with st.form("add_room"):
            col1, col2 = st.columns(2)

            room_number = col1.text_input("Số phòng")
            room_type = col2.selectbox(
                "Loại phòng",
                ["Standard", "Deluxe", "Suite", "Villa"],
            )

            price = col1.number_input(
                "Giá / đêm",
                min_value=0,
                value=650000,
                step=50000,
            )

            floor = col2.number_input(
                "Tầng",
                min_value=1,
                max_value=100,
                value=1,
                step=1,
            )

            submit = st.form_submit_button(
                "➕ Thêm phòng",
                use_container_width=True,
            )

            if submit:
                if not room_number.strip():
                    st.error("Vui lòng nhập số phòng.")
                else:
                    try:
                        execute_insert("""
                            INSERT INTO rooms
                            (room_number, room_type, price, floor, status)
                            VALUES (?, ?, ?, ?, 'Trống')
                        """, (
                            room_number.strip(),
                            room_type,
                            price,
                            floor,
                        ))

                        st.success(
                            f"Đã thêm phòng {room_number}."
                        )
                        st.rerun()

                    except sqlite3.IntegrityError:
                        st.error("Số phòng đã tồn tại.")

    with tab3:
        rooms = execute("""
            SELECT *
            FROM rooms
            ORDER BY room_number
        """, fetch=True)

        if rooms:
            room_map = {
                f'{r["room_number"]} - {r["room_type"]}': r
                for r in rooms
            }

            selected = st.selectbox(
                "Chọn phòng",
                list(room_map.keys()),
            )

            room = room_map[selected]

            with st.form("edit_room"):
                col1, col2 = st.columns(2)

                new_type = col1.selectbox(
                    "Loại phòng",
                    ["Standard", "Deluxe", "Suite", "Villa"],
                    index=[
                        "Standard",
                        "Deluxe",
                        "Suite",
                        "Villa",
                    ].index(room["room_type"]),
                )

                new_price = col2.number_input(
                    "Giá / đêm",
                    min_value=0,
                    value=int(room["price"]),
                    step=50000,
                )

                new_floor = col1.number_input(
                    "Tầng",
                    min_value=1,
                    value=int(room["floor"]),
                    step=1,
                )

                new_status = col2.selectbox(
                    "Trạng thái",
                    ["Trống", "Bảo trì"],
                    index=0 if room["status"] != "Bảo trì" else 1,
                )

                submit = st.form_submit_button(
                    "💾 Lưu thay đổi",
                    use_container_width=True,
                )

                if submit:
                    execute("""
                        UPDATE rooms
                        SET room_type = ?,
                            price = ?,
                            floor = ?,
                            status = ?
                        WHERE id = ?
                    """, (
                        new_type,
                        new_price,
                        new_floor,
                        new_status,
                        room["id"],
                    ))

                    st.success("Đã cập nhật phòng.")
                    st.rerun()


# =========================================================
# KHÁCH HÀNG
# =========================================================
elif menu == "👤 Khách hàng":
    st.title("👤 QUẢN LÝ KHÁCH HÀNG")

    tab1, tab2 = st.tabs(
        ["📋 Danh sách", "➕ Thêm khách"]
    )

    with tab1:
        guests = execute("""
            SELECT *
            FROM guests
            ORDER BY id DESC
        """, fetch=True)

        search = st.text_input(
            "🔎 Tìm kiếm",
            placeholder="Tên, CCCD hoặc số điện thoại...",
        )

        data = []

        for g in guests:
            text = " ".join([
                str(g["name"] or ""),
                str(g["id_card"] or ""),
                str(g["phone"] or ""),
            ]).lower()

            if search.lower() in text:
                data.append({
                    "ID": g["id"],
                    "Họ tên": g["name"],
                    "CCCD": g["id_card"] or "",
                    "Điện thoại": g["phone"] or "",
                    "Email": g["email"] or "",
                    "Địa chỉ": g["address"] or "",
                })

        st.dataframe(
            pd.DataFrame(data),
            use_container_width=True,
            hide_index=True,
        )

    with tab2:
        with st.form("add_guest"):
            name = st.text_input("Họ và tên *")
            id_card = st.text_input("CCCD / CMND")
            phone = st.text_input("Số điện thoại")
            email = st.text_input("Email")
            address = st.text_area("Địa chỉ")

            submit = st.form_submit_button(
                "➕ Thêm khách",
                use_container_width=True,
            )

            if submit:
                if not name.strip():
                    st.error("Vui lòng nhập họ tên.")
                else:
                    execute("""
                        INSERT INTO guests
                        (name, id_card, phone, email, address)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        name.strip(),
                        id_card.strip(),
                        phone.strip(),
                        email.strip(),
                        address.strip(),
                    ))

                    st.success("Đã thêm khách hàng.")
                    st.rerun()


# =========================================================
# ĐẶT PHÒNG
# =========================================================
elif menu == "📅 Đặt phòng":
    st.title("📅 ĐẶT PHÒNG")

    guests = execute("""
        SELECT *
        FROM guests
        ORDER BY name
    """, fetch=True)

    if not guests:
        st.warning(
            "Chưa có khách hàng. Hãy thêm khách hàng trước."
        )
    else:
        col1, col2 = st.columns(2)

        check_in_date = col1.date_input(
            "Ngày nhận phòng",
            value=date.today(),
            min_value=date.today(),
        )

        check_out_date = col2.date_input(
            "Ngày trả phòng",
            value=date.today(),
            min_value=date.today(),
        )

        if check_out_date <= check_in_date:
            st.error(
                "Ngày trả phòng phải sau ngày nhận phòng."
            )
        else:
            available_rooms = get_available_rooms(
                check_in_date.isoformat(),
                check_out_date.isoformat(),
            )

            if not available_rooms:
                st.warning(
                    "Không còn phòng trống trong khoảng thời gian này."
                )
            else:
                with st.form("booking_form"):
                    guest_options = {
                        guest_label(g): g["id"]
                        for g in guests
                    }

                    selected_guest = st.selectbox(
                        "Khách hàng",
                        list(guest_options.keys()),
                    )

                    room_options = {
                        (
                            f'{r["room_number"]} - '
                            f'{r["room_type"]} - '
                            f'{money(r["price"])} / đêm'
                        ): r["id"]
                        for r in available_rooms
                    }

                    selected_room = st.selectbox(
                        "Phòng",
                        list(room_options.keys()),
                    )

                    c1, c2 = st.columns(2)

                    adults = c1.number_input(
                        "Người lớn",
                        min_value=1,
                        value=1,
                        step=1,
                    )

                    children = c2.number_input(
                        "Trẻ em",
                        min_value=0,
                        value=0,
                        step=1,
                    )

                    deposit = st.number_input(
                        "Tiền cọc",
                        min_value=0,
                        value=0,
                        step=100000,
                    )

                    note = st.text_area("Ghi chú")

                    submit = st.form_submit_button(
                        "📅 XÁC NHẬN ĐẶT PHÒNG",
                        use_container_width=True,
                    )

                    if submit:
                        guest_id = guest_options[selected_guest]
                        room_id = room_options[selected_room]

                        booking_id = execute_insert("""
                            INSERT INTO bookings
                            (
                                guest_id,
                                room_id,
                                check_in,
                                check_out,
                                adults,
                                children,
                                deposit,
                                status,
                                note
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?, 'Đã đặt', ?)
                        """, (
                            guest_id,
                            room_id,
                            check_in_date.isoformat(),
                            check_out_date.isoformat(),
                            adults,
                            children,
                            deposit,
                            note.strip(),
                        ))

                        if deposit > 0:
                            execute("""
                                INSERT INTO payments
                                (booking_id, amount, method, note)
                                VALUES (?, ?, ?, ?)
                            """, (
                                booking_id,
                                deposit,
                                "Tiền cọc",
                                "Tiền cọc khi đặt phòng",
                            ))

                        update_room_status()

                        st.success(
                            f"Đặt phòng thành công! "
                            f"Mã booking: #{booking_id}"
                        )
                        st.rerun()


# =========================================================
# CHECK-IN / CHECK-OUT
# =========================================================
elif menu == "🛎️ Check-in / Check-out":
    st.title("🛎️ CHECK-IN / CHECK-OUT")

    today = date.today().isoformat()

    bookings = execute("""
        SELECT
            b.*,
            g.name AS guest_name,
            g.phone,
            r.room_number,
            r.room_type,
            r.price
        FROM bookings b
        JOIN guests g ON b.guest_id = g.id
        JOIN rooms r ON b.room_id = r.id
        WHERE b.status IN ('Đã đặt', 'Đang ở')
        ORDER BY b.check_in, r.room_number
    """, fetch=True)

    if not bookings:
        st.info("Hiện không có booking cần xử lý.")
    else:
        data = []

        for b in bookings:
            data.append({
                "Booking": b["id"],
                "Khách": b["guest_name"],
                "SĐT": b["phone"] or "",
                "Phòng": b["room_number"],
                "Nhận": b["check_in"],
                "Trả": b["check_out"],
                "Trạng thái": b["status"],
                "Tổng tiền": money(get_booking_total(b["id"])),
            })

        st.dataframe(
            pd.DataFrame(data),
            use_container_width=True,
            hide_index=True,
        )

        st.divider()

        booking_map = {
            f'#{b["id"]} - {b["guest_name"]} - Phòng {b["room_number"]}':
                b["id"]
            for b in bookings
        }

        selected = st.selectbox(
            "Chọn booking",
            list(booking_map.keys()),
        )

        booking_id = booking_map[selected]

        booking = execute("""
            SELECT
                b.*,
                g.name AS guest_name,
                g.phone,
                r.room_number,
                r.room_type,
                r.price
            FROM bookings b
            JOIN guests g ON b.guest_id = g.id
            JOIN rooms r ON b.room_id = r.id
            WHERE b.id = ?
        """, (booking_id,), True)[0]

        total = get_booking_total(booking_id)
        paid = get_booking_paid(booking_id)
        remaining = max(total - paid, 0)

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("Khách", booking["guest_name"])
        c2.metric("Phòng", booking["room_number"])
        c3.metric("Tổng tiền", money(total))
        c4.metric("Còn lại", money(remaining))

        col1, col2 = st.columns(2)

        # Check-in
        with col1:
            st.subheader("🟢 Check-in")

            if booking["status"] == "Đã đặt":
                if booking["check_in"] == today:
                    if st.button(
                        "🟢 XÁC NHẬN CHECK-IN",
                        use_container_width=True,
                    ):
                        execute("""
                            UPDATE bookings
                            SET status = 'Đang ở'
                            WHERE id = ?
                        """, (booking_id,))

                        update_room_status()
                        st.success("Check-in thành công.")
                        st.rerun()
                elif booking["check_in"] > today:
                    st.info(
                        f"Ngày nhận phòng là {booking['check_in']}."
                    )
                else:
                    if st.button(
                        "🟢 CHECK-IN TRỄ",
                        use_container_width=True,
                    ):
                        execute("""
                            UPDATE bookings
                            SET status = 'Đang ở'
                            WHERE id = ?
                        """, (booking_id,))

                        update_room_status()
                        st.success("Đã check-in.")
                        st.rerun()
            else:
                st.success("Khách đang ở.")

        # Check-out
        with col2:
            st.subheader("🔴 Check-out")

            if booking["status"] == "Đang ở":
                if remaining > 0:
                    st.warning(
                        f"Khách còn nợ {money(remaining)}."
                    )

                if st.button(
                    "🔴 XÁC NHẬN CHECK-OUT",
                    use_container_width=True,
                ):
                    execute("""
                        UPDATE bookings
                        SET status = 'Đã trả phòng'
                        WHERE id = ?
                    """, (booking_id,))

                    update_room_status()

                    if remaining > 0:
                        st.info(
                            "Đã check-out. Booking vẫn còn số tiền "
                            "chưa thanh toán."
                        )
                    else:
                        st.success(
                            "Check-out thành công và đã thanh toán đủ."
                        )

                    st.rerun()
            else:
                st.info("Booking chưa ở trạng thái đang ở.")


# =========================================================
# DỊCH VỤ
# =========================================================
elif menu == "🧾 Dịch vụ":
    st.title("🧾 QUẢN LÝ DỊCH VỤ")

    tab1, tab2 = st.tabs(
        ["🛎️ Sử dụng dịch vụ", "📋 Danh sách dịch vụ"]
    )

    with tab1:
        active_bookings = execute("""
            SELECT
                b.id,
                g.name AS guest_name,
                r.room_number
            FROM bookings b
            JOIN guests g ON b.guest_id = g.id
            JOIN rooms r ON b.room_id = r.id
            WHERE b.status = 'Đang ở'
            ORDER BY r.room_number
        """, fetch=True)

        services = execute("""
            SELECT *
            FROM services
            ORDER BY name
        """, fetch=True)

        if not active_bookings:
            st.info("Hiện không có khách đang ở.")
        elif not services:
            st.info("Chưa có dịch vụ.")
        else:
            booking_options = {
                f'#{b["id"]} - {b["guest_name"]} - Phòng {b["room_number"]}':
                    b["id"]
                for b in active_bookings
            }

            service_options = {
                f'{s["name"]} - {money(s["price"])}':
                    s["id"]
                for s in services
            }

            with st.form("service_order"):
                booking_selected = st.selectbox(
                    "Booking",
                    list(booking_options.keys()),
                )

                service_selected = st.selectbox(
                    "Dịch vụ",
                    list(service_options.keys()),
                )

                quantity = st.number_input(
                    "Số lượng",
                    min_value=1,
                    value=1,
                    step=1,
                )

                submit = st.form_submit_button(
                    "🛎️ THÊM DỊCH VỤ",
                    use_container_width=True,
                )

                if submit:
                    execute("""
                        INSERT INTO service_orders
                        (booking_id, service_id, quantity)
                        VALUES (?, ?, ?)
                    """, (
                        booking_options[booking_selected],
                        service_options[service_selected],
                        quantity,
                    ))

                    st.success("Đã thêm dịch vụ.")
                    st.rerun()

        st.divider()

        orders = execute("""
            SELECT
                so.id,
                so.booking_id,
                g.name AS guest_name,
                r.room_number,
                s.name AS service_name,
                s.price,
                so.quantity,
                so.quantity * s.price AS total
            FROM service_orders so
            JOIN bookings b ON so.booking_id = b.id
            JOIN guests g ON b.guest_id = g.id
            JOIN rooms r ON b.room_id = r.id
            JOIN services s ON so.service_id = s.id
            ORDER BY so.id DESC
        """, fetch=True)

        data = []

        for o in orders:
            data.append({
                "ID": o["id"],
                "Booking": o["booking_id"],
                "Khách": o["guest_name"],
                "Phòng": o["room_number"],
                "Dịch vụ": o["service_name"],
                "Đơn giá": money(o["price"]),
                "SL": o["quantity"],
                "Thành tiền": money(o["total"]),
            })

        st.subheader("Các dịch vụ đã sử dụng")

        st.dataframe(
            pd.DataFrame(data),
            use_container_width=True,
            hide_index=True,
        )

    with tab2:
        services = execute("""
            SELECT *
            FROM services
            ORDER BY id
        """, fetch=True)

        data = [
            {
                "ID": s["id"],
                "Tên dịch vụ": s["name"],
                "Giá": money(s["price"]),
            }
            for s in services
        ]

        st.dataframe(
            pd.DataFrame(data),
            use_container_width=True,
            hide_index=True,
        )

        with st.form("add_service"):
            name = st.text_input("Tên dịch vụ")
            price = st.number_input(
                "Giá",
                min_value=0,
                value=100000,
                step=10000,
            )

            submit = st.form_submit_button(
                "➕ Thêm dịch vụ",
                use_container_width=True,
            )

            if submit:
                if not name.strip():
                    st.error("Vui lòng nhập tên dịch vụ.")
                else:
                    try:
                        execute_insert("""
                            INSERT INTO services (name, price)
                            VALUES (?, ?)
                        """, (name.strip(), price))

                        st.success("Đã thêm dịch vụ.")
                        st.rerun()

                    except sqlite3.IntegrityError:
                        st.error("Dịch vụ này đã tồn tại.")


# =========================================================
# THANH TOÁN
# =========================================================
elif menu == "💰 Thanh toán":
    st.title("💰 THANH TOÁN")

    bookings = execute("""
        SELECT
            b.id,
            b.status,
            g.name AS guest_name,
            r.room_number
        FROM bookings b
        JOIN guests g ON b.guest_id = g.id
        JOIN rooms r ON b.room_id = r.id
        WHERE b.status != 'Đã hủy'
        ORDER BY b.id DESC
    """, fetch=True)

    if not bookings:
        st.info("Chưa có booking.")
    else:
        booking_options = {
            f'#{b["id"]} - {b["guest_name"]} - Phòng {b["room_number"]}':
                b["id"]
            for b in bookings
        }

        selected = st.selectbox(
            "Chọn booking",
            list(booking_options.keys()),
        )

        booking_id = booking_options[selected]

        total = get_booking_total(booking_id)
        paid = get_booking_paid(booking_id)
        remaining = max(total - paid, 0)

        c1, c2, c3 = st.columns(3)
        c1.metric("Tổng tiền", money(total))
        c2.metric("Đã thanh toán", money(paid))
        c3.metric("Còn lại", money(remaining))

        if remaining > 0:
            with st.form("payment_form"):
                amount = st.number_input(
                    "Số tiền thanh toán",
                    min_value=1,
                    max_value=int(remaining),
                    value=int(remaining),
                    step=10000,
                )

                method = st.selectbox(
                    "Phương thức",
                    [
                        "Tiền mặt",
                        "Chuyển khoản",
                        "Thẻ",
                        "Ví điện tử",
                    ],
                )

                note = st.text_input("Ghi chú")

                submit = st.form_submit_button(
                    "💰 XÁC NHẬN THANH TOÁN",
                    use_container_width=True,
                )

                if submit:
                    execute("""
                        INSERT INTO payments
                        (booking_id, amount, method, note)
                        VALUES (?, ?, ?, ?)
                    """, (
                        booking_id,
                        amount,
                        method,
                        note.strip(),
                    ))

                    st.success(
                        f"Đã thanh toán {money(amount)}."
                    )
                    st.rerun()
        else:
            st.success("Booking đã thanh toán đủ.")

        st.divider()

        payments = execute("""
            SELECT
                p.id,
                p.booking_id,
                g.name AS guest_name,
                r.room_number,
                p.amount,
                p.method,
                p.note,
                p.paid_at
            FROM payments p
            JOIN bookings b ON p.booking_id = b.id
            JOIN guests g ON b.guest_id = g.id
            JOIN rooms r ON b.room_id = r.id
            ORDER BY p.id DESC
        """, fetch=True)

        data = []

        for p in payments:
            data.append({
                "ID": p["id"],
                "Booking": p["booking_id"],
                "Khách": p["guest_name"],
                "Phòng": p["room_number"],
                "Số tiền": money(p["amount"]),
                "Phương thức": p["method"],
                "Ghi chú": p["note"] or "",
                "Thời gian": p["paid_at"],
            })

        st.subheader("Lịch sử thanh toán")

        st.dataframe(
            pd.DataFrame(data),
            use_container_width=True,
            hide_index=True,
        )


# =========================================================
# BÁO CÁO
# =========================================================
elif menu == "📈 Báo cáo":
    st.title("📈 BÁO CÁO")

    tab1, tab2, tab3 = st.tabs(
        [
            "💰 Doanh thu",
            "📅 Booking",
            "🛏️ Công suất phòng",
        ]
    )

    with tab1:
        payments = execute("""
            SELECT
                DATE(paid_at) AS payment_date,
                SUM(amount) AS total
            FROM payments
            GROUP BY DATE(paid_at)
            ORDER BY payment_date
        """, fetch=True)

        if payments:
            df = pd.DataFrame([
                {
                    "Ngày": p["payment_date"],
                    "Doanh thu": p["total"],
                }
                for p in payments
            ])

            st.dataframe(
                df.assign(
                    Doanh_thu=df["Doanh thu"].map(money)
                ).drop(columns=["Doanh thu"]),
                use_container_width=True,
                hide_index=True,
            )

            chart_df = df.set_index("Ngày")
            st.line_chart(chart_df["Doanh thu"])
        else:
            st.info("Chưa có dữ liệu thanh toán.")

    with tab2:
        bookings = execute("""
            SELECT
                b.id,
                g.name AS guest_name,
                r.room_number,
                r.room_type,
                b.check_in,
                b.check_out,
                b.adults,
                b.children,
                b.status
            FROM bookings b
            JOIN guests g ON b.guest_id = g.id
            JOIN rooms r ON b.room_id = r.id
            ORDER BY b.id DESC
        """, fetch=True)

        data = []

        for b in bookings:
            data.append({
                "Booking": b["id"],
                "Khách": b["guest_name"],
                "Phòng": b["room_number"],
                "Loại phòng": b["room_type"],
                "Check-in": b["check_in"],
                "Check-out": b["check_out"],
                "Người lớn": b["adults"],
                "Trẻ em": b["children"],
                "Trạng thái": b["status"],
                "Tổng tiền": money(get_booking_total(b["id"])),
                "Đã thu": money(get_booking_paid(b["id"])),
            })

        st.dataframe(
            pd.DataFrame(data),
            use_container_width=True,
            hide_index=True,
        )

    with tab3:
        rooms = execute(
            "SELECT * FROM rooms",
            fetch=True,
        )

        status_data = {}

        for r in rooms:
            status = r["status"]
            status_data[status] = (
                status_data.get(status, 0) + 1
            )

        if status_data:
            df_status = pd.DataFrame(
                {
                    "Trạng thái": list(status_data.keys()),
                    "Số phòng": list(status_data.values()),
                }
            )

            st.dataframe(
                df_status,
                use_container_width=True,
                hide_index=True,
            )

            st.bar_chart(
                df_status.set_index("Trạng thái")
            )

    st.divider()

    st.subheader("📊 Tổng quan tài chính")

    total_paid = execute("""
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM payments
    """, fetch=True)[0]["total"]

    total_bookings = execute("""
        SELECT COUNT(*) AS total
        FROM bookings
        WHERE status != 'Đã hủy'
    """, fetch=True)[0]["total"]

    total_outstanding = 0

    all_bookings = execute("""
        SELECT id
        FROM bookings
        WHERE status != 'Đã hủy'
    """, fetch=True)

    for b in all_bookings:
        total = get_booking_total(b["id"])
        paid = get_booking_paid(b["id"])
        total_outstanding += max(total - paid, 0)

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "💰 Tổng đã thu",
        money(total_paid),
    )

    c2.metric(
        "📅 Tổng booking",
        total_bookings,
    )

    c3.metric(
        "⚠️ Công nợ",
        money(total_outstanding),
    )

