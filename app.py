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
    layout="wide"
)

DB = Path("hotel.db")


# =========================================================
# DATABASE
# =========================================================
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def execute(sql, params=(), fetch=False):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(sql, params)

    result = cur.fetchall() if fetch else None

    conn.commit()
    conn.close()

    return result


def init_database():

    conn = get_db()
    cur = conn.cursor()

    # PHÒNG
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

    # KHÁCH
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

    # ĐẶT PHÒNG
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
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # DỊCH VỤ
    cur.execute("""
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            price REAL NOT NULL
        )
    """)

    # DỊCH VỤ ĐÃ SỬ DỤNG
    cur.execute("""
        CREATE TABLE IF NOT EXISTS service_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER NOT NULL,
            service_id INTEGER NOT NULL,
            quantity INTEGER DEFAULT 1
        )
    """)

    # THANH TOÁN
    cur.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            method TEXT NOT NULL,
            note TEXT,
            paid_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()

    # -----------------------------------------------------
# DỮ LIỆU PHÒNG MẪU
    # -----------------------------------------------------

    count = cur.execute(
        "SELECT COUNT(*) FROM rooms"
    ).fetchone()[0]

    if count == 0:

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
                        "Trống"
                    )
                )

        cur.executemany("""
            INSERT INTO rooms
            (room_number, room_type, price, floor, status)
            VALUES (?, ?, ?, ?, ?)
        """, rooms)

    # -----------------------------------------------------
    # DỊCH VỤ MẪU
    # -----------------------------------------------------

    count = cur.execute(
        "SELECT COUNT(*) FROM services"
    ).fetchone()[0]

    if count == 0:

        services = [
            ("Bữa sáng", 120000),
            ("Nước suối", 20000),
            ("Giặt ủi", 80000),
            ("Thuê xe máy", 150000),
            ("Taxi", 350000),
            ("Spa", 400000)
        ]

        cur.executemany("""
            INSERT INTO services
            (name, price)
            VALUES (?, ?)
        """, services)

    conn.commit()
    conn.close()


# =========================================================
# HÀM TIỆN ÍCH
# =========================================================
def money(value):

    return f"{value:,.0f} ₫"


def calculate_nights(check_in, check_out):

    start = datetime.strptime(
        check_in, "%Y-%m-%d"
    ).date()

    end = datetime.strptime(
        check_out, "%Y-%m-%d"
    ).date()

    return max((end - start).days, 1)


def update_room_status():

    # Đưa phòng không còn khách về trống
    execute("""
        UPDATE rooms
        SET status = 'Trống'
        WHERE id NOT IN (
            SELECT room_id
            FROM bookings
            WHERE status = 'Đang ở'
        )
        AND status != 'Bảo trì'
    """)

    # Phòng đang ở
    execute("""
        UPDATE rooms
        SET status = 'Đang ở'
        WHERE id IN (
            SELECT room_id
            FROM bookings
            WHERE status = 'Đang ở'
        )
    """)

    # Phòng đã đặt
    execute("""
        UPDATE rooms
        SET status = 'Đã đặt'
        WHERE id IN (
            SELECT room_id
FROM bookings
            WHERE status = 'Đã đặt'
        )
        AND status != 'Đang ở'
    """)


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
            booking["check_out"]
        )
    )

    service_total = execute("""
        SELECT COALESCE(
            SUM(so.quantity * s.price), 0
        ) AS total
        FROM service_orders so
        JOIN services s
        ON so.service_id = s.id
        WHERE so.booking_id = ?
    """, (booking_id,), True)[0]["total"]

    return room_total + service_total


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
        "📈 Báo cáo"
    ]
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
        "SELECT * FROM rooms",
        fetch=True
    )

    total_rooms = len(rooms)

    empty_rooms = sum(
        r["status"] == "Trống"
        for r in rooms
    )

    occupied_rooms = sum(
        r["status"] == "Đang ở"
        for r in rooms
    )

    booked_rooms = sum(
        r["status"] == "Đã đặt"
        for r in rooms
    )

    today = date.today().isoformat()

    revenue = execute("""
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM payments
        WHERE DATE(paid_at) = DATE(?)
    """, (today,), True)[0]["total"]

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric(
        "🏨 Tổng phòng",
        total_rooms
    )

    c2.metric(
        "🟢 Phòng trống",
        empty_rooms
    )

    c3.metric(
        "🔴 Đang ở",
        occupied_rooms
    )

    c4.metric(
        "🟡 Đã đặt",
        booked_rooms
    )

    c5.metric(
        "💰 Doanh thu hôm nay",
        money(revenue)
    )

    st.divider()

    st.subheader("Tình trạng phòng")

    data = []

    for r in rooms:

        data.append({
            "Phòng": r["room_number"],
"Loại phòng": r["room_type"],
            "Giá / đêm": money(r["price"]),
            "Tầng": r["floor"],
            "Trạng thái": r["status"]
        })

    st.dataframe(
        pd.DataFrame(data),
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# QUẢN LÝ PHÒNG
# =========================================================
elif menu == "🛏️ Quản lý phòng":

    st.title("🛏️ QUẢN LÝ PHÒNG")

    tab1, tab2 = st.tabs(
        ["📋 Danh sách phòng", "➕ Thêm phòng"]
    )

    # -----------------------------------------------------
    # DANH SÁCH
    # -----------------------------------------------------

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
                "Trạng thái": r["status"]
            })

        st.dataframe(
            pd.DataFrame(data),
            use_container_widt
