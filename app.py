import pandas as pd
import streamlit as st

from datetime import datetime, date, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


# ============================================================
# 1. CẤU HÌNH STREAMLIT
# ============================================================

st.set_page_config(
    page_title="Melia TwoChanel - Quản lý khách sạn",
    page_icon="🏨",
    layout="wide"
)


# ============================================================
# 2. THÔNG TIN KHÁCH SẠN
# ============================================================

HOTEL_NAME = "Melia TwoChanel"
HOTEL_ADDRESS = "Vũng Tàu, Việt Nam"
HOTEL_PHONE = "0254 123 4567"
HOTEL_EMAIL = "info@meliatwochannel.com"


# ============================================================
# 3. KẾT NỐI AIVEN MYSQL
# ============================================================

DB = {
    "user": "avnadmin",

    # ⚠️ THAY BẰNG MẬT KHẨU AIVEN CỦA EM
    "password": "AVNS_zBDlzsF9I5fC-EdWcl0",

    "host": "mysql-19728385-npmaihuong-927f.b.aivencloud.com",
    "port": 27942,
    "database": "defaultdb"
}


DATABASE_URL = URL.create(
    drivername="mysql+pymysql",
    username=DB["user"],
    password=DB["password"],
    host=DB["host"],
    port=DB["port"],
    database=DB["database"]
)


# ============================================================
# 4. DATABASE ENGINE
# ============================================================

@st.cache_resource
def get_db_engine():

    return create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=1800,
        connect_args={
            "connect_timeout": 15
        }
    )


# ============================================================
# 5. KIỂM TRA DATABASE
# ============================================================

def test_database_connection():

    try:

        engine = get_db_engine()

        with engine.connect() as conn:

            conn.execute(
                text("SELECT 1")
            )

        return True, "Kết nối MySQL thành công."

    except Exception as e:

        return False, str(e)


db_connected, db_message = test_database_connection()


# ============================================================
# 6. CSS
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 38px;
        font-weight: 800;
        text-align: center;
        margin-top: 10px;
        margin-bottom: 5px;
    }

    .sub-title {
        text-align: center;
        font-size: 17px;
        margin-bottom: 25px;
    }

    .hotel-card {
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #dddddd;
        margin-bottom: 15px;
    }

    .room-card {
        padding: 15px;
        border-radius: 15px;
        border: 1px solid #dddddd;
        margin-bottom: 15px;
    }

    .section-title {
        font-size: 26px;
        font-weight: 700;
        margin-top: 20px;
        margin-bottom: 15px;
    }

    .big-number {
        font-size: 30px;
        font-weight: 800;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# 7. HIỂN THỊ THÔNG TIN DATABASE
# ============================================================

with st.expander("🔧 Kiểm tra kết nối MySQL"):

    st.write("**Khách sạn:**", HOTEL_NAME)
    st.write("**Host:**", DB["host"])
    st.write("**Port:**", DB["port"])
    st.write("**Database:**", DB["database"])
    st.write("**User:**", DB["user"])

    if db_connected:

        st.success(
            "🟢 MySQL đã kết nối thành công."
        )

    else:

        st.error(
            "🔴 Không thể kết nối MySQL."
        )

        st.code(db_message)


if not db_connected:

    st.stop()


# ============================================================
# 8. HÀM ĐỌC DATABASE
# ============================================================

def read_query(sql, params=None):

    try:

        engine = get_db_engine()

        with engine.connect() as conn:

            return pd.read_sql(
                text(sql),
                conn,
                params=params or {}
            )

    except Exception as e:

        st.error("❌ Lỗi đọc dữ liệu.")
        st.code(str(e))

        return pd.DataFrame()


# ============================================================
# 9. HÀM GHI DATABASE
# ============================================================

def execute_query(sql, params=None):

    try:

        engine = get_db_engine()

        with engine.begin() as conn:

            conn.execute(
                text(sql),
                params or {}
            )

        return True

    except Exception as e:

        st.error("❌ Lỗi lưu dữ liệu.")
        st.code(str(e))

        return False


# ============================================================
# 10. KHỞI TẠO DATABASE
# ============================================================

def init_db():

    engine = get_db_engine()

    # --------------------------------------------------------
    # LOẠI PHÒNG
    # --------------------------------------------------------

    create_room_types = """

    CREATE TABLE IF NOT EXISTS room_types (

        id INT AUTO_INCREMENT PRIMARY KEY,

        type_name VARCHAR(100) NOT NULL,

        description TEXT,

        max_adults INT NOT NULL,

        max_children INT DEFAULT 0,

        price_per_night DECIMAL(12,2) NOT NULL,

        bed_type VARCHAR(100),

        area VARCHAR(100),

        amenities TEXT,

        created_at DATETIME NOT NULL

    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

    """


    # --------------------------------------------------------
    # PHÒNG
    # --------------------------------------------------------

    create_rooms = """

    CREATE TABLE IF NOT EXISTS rooms (

        id INT AUTO_INCREMENT PRIMARY KEY,

        room_number VARCHAR(20) NOT NULL UNIQUE,

        room_type_id INT NOT NULL,

        floor INT,

        status VARCHAR(50) NOT NULL DEFAULT 'Trống',

        housekeeping_status VARCHAR(50) DEFAULT 'Sạch',

        maintenance_status VARCHAR(50) DEFAULT 'Hoạt động',

        note TEXT,

        created_at DATETIME NOT NULL,

        FOREIGN KEY (room_type_id)
            REFERENCES room_types(id)

    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

    """


    # --------------------------------------------------------
    # KHÁCH HÀNG
    # --------------------------------------------------------

    create_guests = """

    CREATE TABLE IF NOT EXISTS guests (

        id INT AUTO_INCREMENT PRIMARY KEY,

        full_name VARCHAR(150) NOT NULL,

        gender VARCHAR(30),

        date_of_birth DATE,

        nationality VARCHAR(100),

        id_number VARCHAR(100),

        phone VARCHAR(30),

        email VARCHAR(150),

        address VARCHAR(255),

        note TEXT,

        created_at DATETIME NOT NULL

    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

    """


    # --------------------------------------------------------
    # ĐẶT PHÒNG
    # --------------------------------------------------------

    create_reservations = """

    CREATE TABLE IF NOT EXISTS reservations (

        id INT AUTO_INCREMENT PRIMARY KEY,

        booking_code VARCHAR(50) NOT NULL UNIQUE,

        guest_id INT NOT NULL,

        room_id INT NOT NULL,

        check_in DATE NOT NULL,

        check_out DATE NOT NULL,

        adults INT NOT NULL,

        children INT DEFAULT 0,

        room_price DECIMAL(12,2) NOT NULL,

        nights INT NOT NULL,

        room_total DECIMAL(12,2) NOT NULL,

        deposit DECIMAL(12,2) DEFAULT 0,

        payment_status VARCHAR(50) NOT NULL,

        reservation_status VARCHAR(50) NOT NULL,

        special_request TEXT,

        created_at DATETIME NOT NULL,

        FOREIGN KEY (guest_id)
            REFERENCES guests(id),

        FOREIGN KEY (room_id)
            REFERENCES rooms(id)

    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

    """


    # --------------------------------------------------------
    # DỊCH VỤ KHÁCH SẠN
    # --------------------------------------------------------

    create_services = """

    CREATE TABLE IF NOT EXISTS services (

        id INT AUTO_INCREMENT PRIMARY KEY,

        service_name VARCHAR(150) NOT NULL,

        category VARCHAR(100),

        unit VARCHAR(50),

        price DECIMAL(12,2) NOT NULL,

        description TEXT,

        active BOOLEAN DEFAULT TRUE,

        created_at DATETIME NOT NULL

    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

    """


    # --------------------------------------------------------
    # SỬ DỤNG DỊCH VỤ
    # --------------------------------------------------------

    create_service_usages = """

    CREATE TABLE IF NOT EXISTS service_usages (

        id INT AUTO_INCREMENT PRIMARY KEY,

        reservation_id INT NOT NULL,

        service_id INT NOT NULL,

        quantity INT NOT NULL,

        unit_price DECIMAL(12,2) NOT NULL,

        total_price DECIMAL(12,2) NOT NULL,

        used_at DATETIME NOT NULL,

        note TEXT,

        FOREIGN KEY (reservation_id)
            REFERENCES reservations(id),

        FOREIGN KEY (service_id)
            REFERENCES services(id)

    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

    """


    # --------------------------------------------------------
    # HÓA ĐƠN
    # --------------------------------------------------------

    create_invoices = """

    CREATE TABLE IF NOT EXISTS invoices (

        id INT AUTO_INCREMENT PRIMARY KEY,

        invoice_code VARCHAR(50) NOT NULL UNIQUE,

        reservation_id INT NOT NULL,

        room_total DECIMAL(12,2) DEFAULT 0,

        service_total DECIMAL(12,2) DEFAULT 0,

        discount DECIMAL(12,2) DEFAULT 0,

        tax DECIMAL(12,2) DEFAULT 0,

        grand_total DECIMAL(12,2) DEFAULT 0,

        paid_amount DECIMAL(12,2) DEFAULT 0,

        payment_method VARCHAR(50),

        payment_status VARCHAR(50),

        created_at DATETIME NOT NULL,

        FOREIGN KEY (reservation_id)
            REFERENCES reservations(id)

    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

    """


    # --------------------------------------------------------
    # HOUSEKEEPING
    # --------------------------------------------------------

    create_housekeeping = """

    CREATE TABLE IF NOT EXISTS housekeeping (

        id INT AUTO_INCREMENT PRIMARY KEY,

        room_id INT NOT NULL,

        task_type VARCHAR(100),

        status VARCHAR(50),

        assigned_to VARCHAR(150),

        started_at DATETIME,

        completed_at DATETIME,

        note TEXT,

        created_at DATETIME NOT NULL,

        FOREIGN KEY (room_id)
            REFERENCES rooms(id)

    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

    """


    # --------------------------------------------------------
    # BẢO TRÌ
    # --------------------------------------------------------

    create_maintenance = """

    CREATE TABLE IF NOT EXISTS maintenance (

        id INT AUTO_INCREMENT PRIMARY KEY,

        room_id INT NOT NULL,

        issue VARCHAR(255) NOT NULL,

        description TEXT,

        priority VARCHAR(50),

        status VARCHAR(50),

        technician VARCHAR(150),

        start_date DATE,

        end_date DATE,

        cost DECIMAL(12,2) DEFAULT 0,

        note TEXT,

        created_at DATETIME NOT NULL,

        FOREIGN KEY (room_id)
            REFERENCES rooms(id)

    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

    """


    with engine.begin() as conn:

        conn.exec_driver_sql(
            create_room_types
        )

        conn.exec_driver_sql(
            create_rooms
        )

        conn.exec_driver_sql(
            create_guests
        )

        conn.exec_driver_sql(
            create_reservations
        )

        conn.exec_driver_sql(
            create_services
        )

        conn.exec_driver_sql(
            create_service_usages
        )

        conn.exec_driver_sql(
            create_invoices
        )

        conn.exec_driver_sql(
            create_housekeeping
        )

        conn.exec_driver_sql(
            create_maintenance
        )


try:

    init_db()

except Exception as e:

    st.error(
        "❌ Không thể khởi tạo Database."
    )

    st.code(str(e))

    st.stop()


# ============================================================
# 11. THÊM DỮ LIỆU MẪU
# ============================================================

def create_sample_data():

    # --------------------------------------------------------
    # LOẠI PHÒNG MẪU
    # --------------------------------------------------------

    room_type_count = read_query(
        "SELECT COUNT(*) AS total FROM room_types"
    )


    if (
        not room_type_count.empty
        and int(room_type_count.iloc[0]["total"]) == 0
    ):

        room_types = [

            (
                "Standard Room",
                "Phòng tiêu chuẩn phù hợp cho khách cá nhân hoặc cặp đôi.",
                2,
                1,
                1200000,
                "1 giường đôi",
                "28 m²",
                "TV, WiFi, máy lạnh, minibar, máy sấy"
            ),

            (
                "Deluxe Room",
                "Phòng cao cấp với không gian rộng và tiện nghi tốt.",
                2,
                2,
                1800000,
                "1 giường King",
                "35 m²",
                "TV, WiFi, minibar, máy lạnh, két an toàn, ban công"
            ),

            (
                "Family Room",
                "Phòng dành cho gia đình.",
                4,
                2,
                2600000,
                "2 giường đôi",
                "45 m²",
                "TV, WiFi, minibar, máy lạnh, két an toàn"
            ),

            (
                "Suite",
                "Phòng Suite cao cấp với phòng khách riêng.",
                2,
                2,
                3500000,
                "1 giường King",
                "60 m²",
                "Phòng khách, TV, minibar, bồn tắm, ban công, két an toàn"
            )
        ]


        for room_type in room_types:

            execute_query(
                """
                INSERT INTO room_types
                (
                    type_name,
                    description,
                    max_adults,
                    max_children,
                    price_per_night,
                    bed_type,
                    area,
                    amenities,
                    created_at
                )

                VALUES
                (
                    :type_name,
                    :description,
                    :max_adults,
                    :max_children,
                    :price,
                    :bed_type,
                    :area,
                    :amenities,
                    :created_at
                )
                """,
                {
                    "type_name": room_type[0],
                    "description": room_type[1],
                    "max_adults": room_type[2],
                    "max_children": room_type[3],
                    "price": room_type[4],
                    "bed_type": room_type[5],
                    "area": room_type[6],
                    "amenities": room_type[7],
                    "created_at": datetime.now()
                }
            )


    # --------------------------------------------------------
    # PHÒNG MẪU
    # --------------------------------------------------------

    room_count = read_query(
        "SELECT COUNT(*) AS total FROM rooms"
    )


    if (
        not room_count.empty
        and int(room_count.iloc[0]["total"]) == 0
    ):

        room_types_df = read_query(
            """
            SELECT id, type_name
            FROM room_types
            ORDER BY id
            """
        )


        room_type_ids = {
            row["type_name"]: int(row["id"])
            for _, row in room_types_df.iterrows()
        }


        sample_rooms = [

            ("101", "Standard Room", 1),
            ("102", "Standard Room", 1),
            ("103", "Standard Room", 1),
            ("104", "Standard Room", 1),

            ("201", "Deluxe Room", 2),
            ("202", "Deluxe Room", 2),
            ("203", "Deluxe Room", 2),
            ("204", "Deluxe Room", 2),

            ("301", "Family Room", 3),
            ("302", "Family Room", 3),

            ("401", "Suite", 4),
            ("402", "Suite", 4)
        ]


        for room in sample_rooms:

            type_id = room_type_ids.get(
                room[1]
            )


            if type_id:

                execute_query(
                    """
                    INSERT INTO rooms
                    (
                        room_number,
                        room_type_id,
                        floor,
                        status,
                        housekeeping_status,
                        maintenance_status,
                        note,
                        created_at
                    )

                    VALUES
                    (
                        :room_number,
                        :room_type_id,
                        :floor,
                        'Trống',
                        'Sạch',
                        'Hoạt động',
                        '',
                        :created_at
                    )
                    """,
                    {
                        "room_number": room[0],
                        "room_type_id": type_id,
                        "floor": room[2],
                        "created_at": datetime.now()
                    }
                )


    # --------------------------------------------------------
    # DỊCH VỤ MẪU
    # --------------------------------------------------------

    service_count = read_query(
        "SELECT COUNT(*) AS total FROM services"
    )


    if (
        not service_count.empty
        and int(service_count.iloc[0]["total"]) == 0
    ):

        services = [

            (
                "Nước suối",
                "Minibar",
                "chai",
                20000,
                "Nước suối 500ml"
            ),

            (
                "Coca Cola",
                "Minibar",
                "lon",
                25000,
                "Nước ngọt"
            ),

            (
                "Bia",
                "Minibar",
                "lon",
                35000,
                "Bia lon"
            ),

            (
                "Giặt ủi",
                "Laundry",
                "kg",
                60000,
                "Dịch vụ giặt ủi"
            ),

            (
                "Ăn sáng",
                "Ẩm thực",
                "suất",
                150000,
                "Buffet sáng"
            ),

            (
                "Đưa đón sân bay",
                "Vận chuyển",
                "chuyến",
                500000,
                "Dịch vụ xe đưa đón"
            ),

            (
                "Extra Bed",
                "Phòng",
                "giường",
                400000,
                "Giường phụ"
            )
        ]


        for service in services:

            execute_query(
                """
                INSERT INTO services
                (
                    service_name,
                    category,
                    unit,
                    price,
                    description,
                    active,
                    created_at
                )

                VALUES
                (
                    :name,
                    :category,
                    :unit,
                    :price,
                    :description,
                    1,
                    :created_at
                )
                """,
                {
                    "name": service[0],
                    "category": service[1],
                    "unit": service[2],
                    "price": service[3],
                    "description": service[4],
                    "created_at": datetime.now()
                }
            )


try:

    create_sample_data()

except Exception as e:

    st.warning(
        "⚠️ Không thể tạo dữ liệu mẫu."
    )


# ============================================================
# 12. SESSION STATE
# ============================================================

if "admin_logged_in" not in st.session_state:

    st.session_state.admin_logged_in = False


# ============================================================
# 13. SIDEBAR
# ============================================================

st.sidebar.title(
    "🏨 MELIA TWOCHANEL"
)

st.sidebar.caption(
    "Hệ thống quản lý khách sạn"
)


page = st.sidebar.radio(
    "📋 Chọn chức năng",
    [
        "🏠 Tổng quan",
        "🛏️ Quản lý phòng",
        "🏷️ Loại phòng",
        "👤 Khách hàng",
        "📅 Đặt phòng",
        "🛎️ Check-in",
        "🚪 Check-out",
        "🧹 Housekeeping",
        "🔧 Bảo trì",
        "🍽️ Dịch vụ",
        "🧾 Hóa đơn",
        "📊 Báo cáo",
        "🔑 Admin"
    ]
)


# ============================================================
# 14. TỔNG QUAN
# ============================================================

if page == "🏠 Tổng quan":

    st.markdown(
        '<div class="main-title">'
        '🏨 MELIA TWOCHANEL'
        '</div>',
        unsafe_allow_html=True
    )


    st.markdown(
        '<div class="sub-title">'
        'Hệ thống quản lý phòng • khách lưu trú • đặt phòng • dịch vụ • doanh thu'
        '</div>',
        unsafe_allow_html=True
    )


    st.success(
        "🟢 Hệ thống khách sạn đang hoạt động"
    )


    # --------------------------------------------------------
    # THỐNG KÊ PHÒNG
    # --------------------------------------------------------

    rooms_df = read_query(
        """
        SELECT
            r.id,
            r.room_number,
            r.floor,
            r.status,
            r.housekeeping_status,
            r.maintenance_status,
            rt.type_name,
            rt.price_per_night
        FROM rooms r
        JOIN room_types rt
            ON r.room_type_id = rt.id
        ORDER BY r.room_number
        """
    )


    total_rooms = len(rooms_df)


    available_rooms = len(
        rooms_df[
            rooms_df["status"] == "Trống"
        ]
    ) if not rooms_df.empty else 0


    occupied_rooms = len(
        rooms_df[
            rooms_df["status"] == "Đang ở"
        ]
    ) if not rooms_df.empty else 0


    reserved_rooms = len(
        rooms_df[
            rooms_df["status"] == "Đã đặt"
        ]
    ) if not rooms_df.empty else 0


    maintenance_rooms = len(
        rooms_df[
            rooms_df["maintenance_status"] == "Bảo trì"
        ]
    ) if not rooms_df.empty else 0


    col1, col2, col3, col4, col5 = st.columns(5)


    with col1:

        st.metric(
            "🏨 Tổng phòng",
            total_rooms
        )


    with col2:

        st.metric(
            "🟢 Phòng trống",
            available_rooms
        )


    with col3:

        st.metric(
            "🔴 Đang ở",
            occupied_rooms
        )


    with col4:

        st.metric(
            "🟡 Đã đặt",
            reserved_rooms
        )


    with col5:

        st.metric(
            "🔧 Bảo trì",
            maintenance_rooms
        )


    st.markdown("---")


    # --------------------------------------------------------
    # BẢNG PHÒNG
    # --------------------------------------------------------

    st.subheader(
        "🛏️ Tình trạng phòng"
    )


    if not rooms_df.empty:

        display_rooms = rooms_df.copy()


        display_rooms = display_rooms[
            [
                "room_number",
                "floor",
                "type_name",
                "price_per_night",
                "status",
                "housekeeping_status",
                "maintenance_status"
            ]
        ]


        display_rooms.columns = [
            "Phòng",
            "Tầng",
            "Loại phòng",
            "Giá/đêm",
            "Trạng thái",
            "Housekeeping",
            "Bảo trì"
        ]


        display_rooms["Giá/đêm"] = (
            pd.to_numeric(
                display_rooms["Giá/đêm"],
                errors="coerce"
            )
            .fillna(0)
            .apply(lambda x: f"{x:,.0f} VNĐ")
        )


        st.dataframe(
            display_rooms,
            use_container_width=True,
            hide_index=True
        )


    st.markdown("---")


    st.subheader(
        "🏨 Thông tin khách sạn"
    )


    col1, col2 = st.columns(2)


    with col1:

        st.write(
            f"**Tên:** {HOTEL_NAME}"
        )

        st.write(
            f"**Địa chỉ:** {HOTEL_ADDRESS}"
        )


    with col2:

        st.write(
            f"**Điện thoại:** {HOTEL_PHONE}"
        )

        st.write(
            f"**Email:** {HOTEL_EMAIL}"
        )


# ============================================================
# 15. QUẢN LÝ PHÒNG
# ============================================================

elif page == "🛏️ Quản lý phòng":

    st.title(
        "🛏️ QUẢN LÝ PHÒNG"
    )


    tab1, tab2 = st.tabs(
        [
            "📋 Sơ đồ phòng",
            "➕ Thêm phòng"
        ]
    )


    # ========================================================
    # SƠ ĐỒ PHÒNG
    # ========================================================

    with tab1:

        df_rooms = read_query(
            """
            SELECT
                r.id,
                r.room_number,
                r.floor,
                rt.type_name,
                rt.price_per_night,
                r.status,
                r.housekeeping_status,
                r.maintenance_status,
                r.note
            FROM rooms r
            JOIN room_types rt
                ON r.room_type_id = rt.id
            ORDER BY r.floor, r.room_number
            """
        )


        if df_rooms.empty:

            st.info(
                "📭 Chưa có phòng."
            )

        else:

            selected_status = st.selectbox(
                "🔎 Lọc trạng thái",
                [
                    "Tất cả",
                    "Trống",
                    "Đã đặt",
                    "Đang ở",
                    "Chờ dọn",
                    "Khóa phòng"
                ]
            )


            filtered = df_rooms.copy()


            if selected_status != "Tất cả":

                filtered = filtered[
                    filtered["status"] == selected_status
                ]


            for _, room in filtered.iterrows():

                col1, col2, col3, col4 = st.columns(4)


                with col1:

                    st.markdown(
                        f"### 🛏️ Phòng {room['room_number']}"
                    )

                    st.write(
                        f"Tầng: **{room['floor']}**"
                    )


                with col2:

                    st.write(
                        f"🏷️ {room['type_name']}"
                    )

                    st.write(
                        f"💰 {float(room['price_per_night']):,.0f} VNĐ/đêm"
                    )


                with col3:

                    if room["status"] == "Trống":

                        st.success(
                            f"🟢 {room['status']}"
                        )

                    elif room["status"] == "Đang ở":

                        st.error(
                            f"🔴 {room['status']}"
                        )

                    elif room["status"] == "Đã đặt":

                        st.warning(
                            f"🟡 {room['status']}"
                        )

                    else:

                        st.info(
                            f"🔵 {room['status']}"
                        )


                with col4:

                    st.write(
                        f"🧹 {room['housekeeping_status']}"
                    )

                    st.write(
                        f"🔧 {room['maintenance_status']}"
                    )


                with st.expander(
                    "⚙️ Quản lý phòng"
                ):

                    new_status = st.selectbox(
                        "Trạng thái phòng",
                        [
                            "Trống",
                            "Đã đặt",
                            "Đang ở",
                            "Chờ dọn",
                            "Khóa phòng"
                        ],
                        index=[
                            "Trống",
                            "Đã đặt",
                            "Đang ở",
                            "Chờ dọn",
                            "Khóa phòng"
                        ].index(room["status"]),
                        key=f"status_{room['id']}"
                    )


                    new_housekeeping = st.selectbox(
                        "Tình trạng vệ sinh",
                        [
                            "Sạch",
                            "Đang dọn",
                            "Bẩn",
                            "Kiểm tra"
                        ],
                        index=[
                            "Sạch",
                            "Đang dọn",
                            "Bẩn",
                            "Kiểm tra"
                        ].index(room["housekeeping_status"]),
                        key=f"house_{room['id']}"
                    )


                    note = st.text_area(
                        "Ghi chú",
                        value=room["note"] or "",
                        key=f"note_{room['id']}"
                    )


                    if st.button(
                        "💾 Cập nhật phòng",
                        key=f"update_room_{room['id']}"
                    ):

                        execute_query(
                            """
                            UPDATE rooms
                            SET
                                status = :status,
                                housekeeping_status = :housekeeping,
                                note = :note
                            WHERE id = :id
                            """,
                            {
                                "status": new_status,
                                "housekeeping": new_housekeeping,
                                "note": note,
                                "id": int(room["id"])
                            }
                        )


                        st.success(
                            "✅ Đã cập nhật phòng."
                        )

                        st.rerun()


                st.markdown("---")


    # ========================================================
    # THÊM PHÒNG
    # ========================================================

    with tab2:

        room_types = read_query(
            """
            SELECT
                id,
                type_name
            FROM room_types
            ORDER BY type_name
            """
        )


        if room_types.empty:

            st.warning(
                "⚠️ Hãy tạo loại phòng trước."
            )

        else:

            with st.form(
                "add_room_form"
            ):

                room_number = st.text_input(
                    "🛏️ Số phòng",
                    placeholder="501"
                )


                floor = st.number_input(
                    "🏢 Tầng",
                    min_value=1,
                    value=1
                )


                room_type_options = [
                    f"{row.type_name}"
                    for row in room_types.itertuples()
                ]


                selected_type = st.selectbox(
                    "🏷️ Loại phòng",
                    room_type_options
                )


                type_index = room_type_options.index(
                    selected_type
                )


                room_type_id = int(
                    room_types.iloc[type_index]["id"]
                )


                note = st.text_area(
                    "📝 Ghi chú"
                )


                submit = st.form_submit_button(
                    "💾 THÊM PHÒNG",
                    use_container_width=True
                )


                if submit:

                    if not room_number.strip():

                        st.warning(
                            "⚠️ Vui lòng nhập số phòng."
                        )

                    else:

                        success = execute_query(
                            """
                            INSERT INTO rooms
                            (
                                room_number,
                                room_type_id,
                                floor,
                                status,
                                housekeeping_status,
                                maintenance_status,
                                note,
                                created_at
                            )

                            VALUES
                            (
                                :room_number,
                                :room_type_id,
                                :floor,
                                'Trống',
                                'Sạch',
                                'Hoạt động',
                                :note,
                                :created_at
                            )
                            """,
                            {
                                "room_number": room_number.strip(),
                                "room_type_id": room_type_id,
                                "floor": floor,
                                "note": note.strip(),
                                "created_at": datetime.now()
                            }
                        )


                        if success:

                            st.success(
                                "🎉 Thêm phòng thành công!"
                            )

                            st.rerun()


# ============================================================
# 16. LOẠI PHÒNG
# ============================================================

elif page == "🏷️ Loại phòng":

    st.title(
        "🏷️ QUẢN LÝ LOẠI PHÒNG"
    )


    tab1, tab2 = st.tabs(
        [
            "📋 Danh sách loại phòng",
            "➕ Thêm loại phòng"
        ]
    )


    with tab1:

        df_types = read_query(
            """
            SELECT
                id,
                type_name,
                description,
                max_adults,
                max_children,
                price_per_night,
                bed_type,
                area,
                amenities
            FROM room_types
            ORDER BY price_per_night
            """
        )


        if df_types.empty:

            st.info(
                "📭 Chưa có loại phòng."
            )

        else:

            for _, room_type in df_types.iterrows():

                with st.expander(
                    f"🏷️ {room_type['type_name']}"
                ):

                    col1, col2 = st.columns(2)


                    with col1:

                        st.write(
                            f"👨 Người lớn tối đa: **{room_type['max_adults']}**"
                        )

                        st.write(
                            f"👶 Trẻ em tối đa: **{room_type['max_children']}**"
                        )

                        st.write(
                            f"🛏️ Giường: **{room_type['bed_type']}**"
                        )


                    with col2:

                        st.write(
                            f"📐 Diện tích: **{room_type['area']}**"
                        )

                        st.write(
                            f"💰 Giá: **{float(room_type['price_per_night']):,.0f} VNĐ/đêm**"
                        )


                    st.write(
                        "📝 **Mô tả:**"
                    )

                    st.write(
                        room_type["description"]
                    )


                    st.write(
                        "✨ **Tiện nghi:**"
                    )

                    st.write(
                        room_type["amenities"]
                    )


    with tab2:

        with st.form(
            "room_type_form"
        ):

            type_name = st.text_input(
                "🏷️ Tên loại phòng",
                placeholder="Deluxe Room"
            )


            description = st.text_area(
                "📝 Mô tả"
            )


            col1, col2 = st.columns(2)


            with col1:

                max_adults = st.number_input(
                    "👨 Số người lớn tối đa",
                    min_value=1,
                    value=2
                )


                max_children = st.number_input(
                    "👶 Số trẻ em tối đa",
                    min_value=0,
                    value=1
                )


                price = st.number_input(
                    "💰 Giá phòng / đêm",
                    min_value=0,
                    value=1500000,
                    step=100000
                )


            with col2:

                bed_type = st.text_input(
                    "🛏️ Loại giường",
                    placeholder="1 giường King"
                )


                area = st.text_input(
                    "📐 Diện tích",
                    placeholder="35 m²"
                )


                amenities = st.text_area(
                    "✨ Tiện nghi",
                    placeholder="TV, WiFi, minibar..."
                )


            submit = st.form_submit_button(
                "💾 LƯU LOẠI PHÒNG",
                use_container_width=True
            )


            if submit:

                if not type_name.strip():

                    st.warning(
                        "⚠️ Vui lòng nhập tên loại phòng."
                    )

                else:

                    success = execute_query(
                        """
                        INSERT INTO room_types
                        (
                            type_name,
                            description,
                            max_adults,
                            max_children,
                            price_per_night,
                            bed_type,
                            area,
                            amenities,
                            created_at
                        )

                        VALUES
                        (
                            :type_name,
                            :description,
                            :max_adults,
                            :max_children,
                            :price,
                            :bed_type,
                            :area,
                            :amenities,
                            :created_at
                        )
                        """,
                        {
                            "type_name": type_name.strip(),
                            "description": description.strip(),
                            "max_adults": max_adults,
                            "max_children": max_children,
                            "price": price,
                            "bed_type": bed_type.strip(),
                            "area": area.strip(),
                            "amenities": amenities.strip(),
                            "created_at": datetime.now()
                        }
                    )


                    if success:

                        st.success(
                            "🎉 Đã thêm loại phòng!"
                        )

                        st.rerun()


# ============================================================
# 17. KHÁCH HÀNG
# ============================================================

elif page == "👤 Khách hàng":

    st.title(
        "👤 QUẢN LÝ KHÁCH HÀNG"
    )


    tab1, tab2 = st.tabs(
        [
            "➕ Thêm khách",
            "📋 Danh sách khách"
        ]
    )


    with tab1:

        with st.form(
            "guest_form"
        ):

            full_name = st.text_input(
                "👤 Họ và tên"
            )


            col1, col2 = st.columns(2)


            with col1:

                gender = st.selectbox(
                    "⚧ Giới tính",
                    [
                        "Nam",
                        "Nữ",
                        "Khác"
                    ]
                )


                date_of_birth = st.date_input(
                    "🎂 Ngày sinh",
                    date(1995, 1, 1)
                )


                nationality = st.text_input(
                    "🌎 Quốc tịch",
                    value="Việt Nam"
                )


                id_number = st.text_input(
                    "🪪 CCCD / Hộ chiếu"
                )


            with col2:

                phone = st.text_input(
                    "📱 Số điện thoại"
                )


                email = st.text_input(
                    "📧 Email"
                )


                address = st.text_input(
                    "🏠 Địa chỉ"
                )


                note = st.text_area(
                    "📝 Ghi chú"
                )


            submit = st.form_submit_button(
                "💾 LƯU KHÁCH HÀNG",
                use_container_width=True
            )


            if submit:

                if not full_name.strip():

                    st.warning(
                        "⚠️ Vui lòng nhập họ tên."
                    )

                elif not phone.strip():

                    st.warning(
                        "⚠️ Vui lòng nhập số điện thoại."
                    )

                else:

                    success = execute_query(
                        """
                        INSERT INTO guests
                        (
                            full_name,
                            gender,
                            date_of_birth,
                            nationality,
                            id_number,
                            phone,
                            email,
                            address,
                            note,
                            created_at
                        )

                        VALUES
                        (
                            :full_name,
                            :gender,
                            :date_of_birth,
                            :nationality,
                            :id_number,
                            :phone,
                            :email,
                            :address,
                            :note,
                            :created_at
                        )
                        """,
                        {
                            "full_name": full_name.strip(),
                            "gender": gender,
                            "date_of_birth": date_of_birth,
                            "nationality": nationality.strip(),
                            "id_number": id_number.strip(),
                            "phone": phone.strip(),
                            "email": email.strip(),
                            "address": address.strip(),
                            "note": note.strip(),
                            "created_at": datetime.now()
                        }
                    )


                    if success:

                        st.success(
                            "🎉 Thêm khách hàng thành công!"
                        )

                        st.rerun()


    with tab2:

        guests_df = read_query(
            """
            SELECT
                id,
                full_name,
                gender,
                nationality,
                id_number,
                phone,
                email,
                address,
                created_at
            FROM guests
            ORDER BY created_at DESC
            """
        )


        if guests_df.empty:

            st.info(
                "📭 Chưa có khách hàng."
            )

        else:

            guests_display = guests_df.copy()


            guests_display.columns = [
                "ID",
                "Họ tên",
                "Giới tính",
                "Quốc tịch",
                "CCCD/Hộ chiếu",
                "Điện thoại",
                "Email",
                "Địa chỉ",
                "Ngày tạo"
            ]


            st.dataframe(
                guests_display,
                use_container_width=True,
                hide_index=True
            )


# ============================================================
# 18. ĐẶT PHÒNG
# ============================================================

elif page == "📅 Đặt phòng":

    st.title(
        "📅 ĐẶT PHÒNG KHÁCH SẠN"
    )


    guests = read_query(
        """
        SELECT
            id,
            full_name,
            phone
        FROM guests
        ORDER BY full_name
        """
    )


    room_options_df = read_query(
        """
        SELECT
            r.id,
            r.room_number,
            r.floor,
            r.status,
            r.housekeeping_status,
            rt.type_name,
            rt.price_per_night,
            rt.max_adults,
            rt.max_children
        FROM rooms r
        JOIN room_types rt
            ON r.room_type_id = rt.id
        WHERE r.status = 'Trống'
        AND r.housekeeping_status = 'Sạch'
        AND r.maintenance_status = 'Hoạt động'
        ORDER BY r.room_number
        """
    )


    if guests.empty:

        st.warning(
            "⚠️ Chưa có khách hàng."
        )

        st.info(
            "Hãy vào mục 👤 Khách hàng để thêm khách trước."
        )


    elif room_options_df.empty:

        st.warning(
            "⚠️ Hiện không có phòng sạch và sẵn sàng để đặt."
        )


    else:

        with st.form(
            "reservation_form"
        ):

            col1, col2 = st.columns(2)


            with col1:

                guest_options = [
                    f"{row.full_name} - {row.phone}"
                    for row in guests.itertuples()
                ]


                selected_guest = st.selectbox(
                    "👤 Khách hàng",
                    guest_options
                )


                guest_index = guest_options.index(
                    selected_guest
                )


                guest_id = int(
                    guests.iloc[guest_index]["id"]
                )


                check_in = st.date_input(
                    "📅 Ngày nhận phòng",
                    date.today()
                )


                check_out = st.date_input(
                    "📅 Ngày trả phòng",
                    date.today() + timedelta(days=1)
                )


            with col2:

                room_options = [
                    f"Phòng {row.room_number} - "
                    f"{row.type_name} - "
                    f"{float(row.price_per_night):,.0f} VNĐ"
                    for row in room_options_df.itertuples()
                ]


                selected_room = st.selectbox(
                    "🛏️ Chọn phòng",
                    room_options
                )


                room_index = room_options.index(
                    selected_room
                )


                room = room_options_df.iloc[
                    room_index
                ]


                room_id = int(
                    room["id"]
                )


                adults = st.number_input(
                    "👨 Số người lớn",
                    min_value=1,
                    max_value=int(room["max_adults"]),
                    value=1
                )


                children = st.number_input(
                    "👶 Số trẻ em",
                    min_value=0,
                    max_value=int(room["max_children"]),
                    value=0
                )


            special_request = st.text_area(
                "📝 Yêu cầu đặc biệt",
                placeholder="Phòng không hút thuốc, giường phụ..."
            )


            submit = st.form_submit_button(
                "📅 XÁC NHẬN ĐẶT PHÒNG",
                use_container_width=True
            )


            if submit:

                if check_out <= check_in:

                    st.error(
                        "❌ Ngày trả phòng phải sau ngày nhận phòng."
                    )

                else:

                    nights = (
                        check_out - check_in
                    ).days


                    room_price = float(
                        room["price_per_night"]
                    )


                    room_total = (
                        room_price * nights
                    )


                    booking_code = (
                        "MT"
                        + datetime.now().strftime(
                            "%Y%m%d%H%M%S"
                        )
                    )


                    # Kiểm tra phòng có bị đặt trùng không

                    conflict = read_query(
                        """
                        SELECT COUNT(*) AS total
                        FROM reservations
                        WHERE room_id = :room_id
                        AND reservation_status IN
                            ('Đã đặt', 'Đã check-in')
                        AND check_in < :check_out
                        AND check_out > :check_in
                        """,
                        {
                            "room_id": room_id,
                            "check_in": check_in,
                            "check_out": check_out
                        }
                    )


                    conflict_count = int(
                        conflict.iloc[0]["total"]
                    )


                    if conflict_count > 0:

                        st.error(
                            "❌ Phòng này đã có booking trong khoảng thời gian trên."
                        )

                    else:

                        success = execute_query(
                            """
                            INSERT INTO reservations
                            (
                                booking_code,
                                guest_id,
                                room_id,
                                check_in,
                                check_out,
                                adults,
                                children,
                                room_price,
                                nights,
                                room_total,
                                deposit,
                                payment_status,
                                reservation_status,
                                special_request,
                                created_at
                            )

                            VALUES
                            (
                                :booking_code,
                                :guest_id,
                                :room_id,
                                :check_in,
                                :check_out,
                                :adults,
                                :children,
                                :room_price,
                                :nights,
                                :room_total,
                                0,
                                'Chưa thanh toán',
                                'Đã đặt',
                                :special_request,
                                :created_at
                            )
                            """,
                            {
                                "booking_code": booking_code,
                                "guest_id": guest_id,
                                "room_id": room_id,
                                "check_in": check_in,
                                "check_out": check_out,
                                "adults": adults,
                                "children": children,
                                "room_price": room_price,
                                "nights": nights,
                                "room_total": room_total,
                                "special_request": special_request.strip(),
                                "created_at": datetime.now()
                            }
                        )


                        if success:

                            execute_query(
                                """
                                UPDATE rooms
                                SET status = 'Đã đặt'
                                WHERE id = :room_id
                                """,
                                {
                                    "room_id": room_id
                                }
                            )


                            st.success(
                                "🎉 Đặt phòng thành công!"
                            )


                            st.info(
                                f"🔖 Mã đặt phòng: **{booking_code}**"
                            )


                            st.info(
                                f"💰 Tiền phòng: "
                                f"**{room_total:,.0f} VNĐ**"
                            )


                            st.rerun()


# ============================================================
# 19. CHECK-IN
# ============================================================

elif page == "🛎️ Check-in":

    st.title(
        "🛎️ CHECK-IN KHÁCH"
    )


    reservations = read_query(
        """
        SELECT
            r.id,
            r.booking_code,
            g.full_name,
            g.phone,
            ro.room_number,
            rt.type_name,
            r.check_in,
            r.check_out,
            r.adults,
            r.children,
            r.room_total,
            r.reservation_status
        FROM reservations r
        JOIN guests g
            ON r.guest_id = g.id
        JOIN rooms ro
            ON r.room_id = ro.id
        JOIN room_types rt
            ON ro.room_type_id = rt.id
        WHERE r.reservation_status = 'Đã đặt'
        ORDER BY r.check_in
        """
    )


    if reservations.empty:

        st.info(
            "📭 Không có booking nào đang chờ check-in."
        )

    else:

        for _, booking in reservations.iterrows():

            with st.expander(
                f"🔖 {booking['booking_code']} - "
                f"{booking['full_name']} - "
                f"Phòng {booking['room_number']}"
            ):

                col1, col2, col3 = st.columns(3)


                with col1:

                    st.write(
                        f"👤 Khách: **{booking['full_name']}**"
                    )

                    st.write(
                        f"📱 Điện thoại: **{booking['phone']}**"
                    )


                with col2:

                    st.write(
                        f"🛏️ Phòng: **{booking['room_number']}**"
                    )

                    st.write(
                        f"🏷️ Loại: **{booking['type_name']}**"
                    )


                with col3:

                    st.write(
                        f"📅 Check-in: **{booking['check_in']}**"
                    )

                    st.write(
                        f"📅 Check-out: **{booking['check_out']}**"
                    )


                st.write(
                    f"👥 {booking['adults']} người lớn - "
                    f"{booking['children']} trẻ em"
                )


                st.write(
                    f"💰 Tiền phòng: "
                    f"**{float(booking['room_total']):,.0f} VNĐ**"
                )


                if st.button(
                    "🛎️ XÁC NHẬN CHECK-IN",
                    key=f"checkin_{booking['id']}",
                    use_container_width=True
                ):

                    execute_query(
                        """
                        UPDATE reservations
                        SET reservation_status = 'Đã check-in'
                        WHERE id = :id
                        """,
                        {
                            "id": int(booking["id"])
                        }
                    )


                    execute_query(
                        """
                        UPDATE rooms
                        SET status = 'Đang ở'
                        WHERE id = (
                            SELECT room_id
                            FROM reservations
                            WHERE id = :id
                        )
                        """,
                        {
                            "id": int(booking["id"])
                        }
                    )


                    st.success(
                        "🎉 Check-in thành công!"
                    )

                    st.rerun()


# ============================================================
# 20. CHECK-OUT
# ============================================================

elif page == "🚪 Check-out":

    st.title(
        "🚪 CHECK-OUT KHÁCH"
    )


    reservations = read_query(
        """
        SELECT
            r.id,
            r.booking_code,
            g.full_name,
            ro.room_number,
            rt.type_name,
            r.check_in,
            r.check_out,
            r.room_total
        FROM reservations r
        JOIN guests g
            ON r.guest_id = g.id
        JOIN rooms ro
            ON r.room_id = ro.id
        JOIN room_types rt
            ON ro.room_type_id = rt.id
        WHERE r.reservation_status = 'Đã check-in'
        ORDER BY r.check_out
        """
    )


    if reservations.empty:

        st.info(
            "📭 Hiện không có khách đang lưu trú."
        )

    else:

        for _, booking in reservations.iterrows():

            with st.expander(
                f"🚪 {booking['booking_code']} - "
                f"{booking['full_name']} - "
                f"Phòng {booking['room_number']}"
            ):

                st.write(
                    f"👤 Khách: **{booking['full_name']}**"
                )

                st.write(
                    f"🛏️ Phòng: **{booking['room_number']}**"
                )

                st.write(
                    f"📅 {booking['check_in']} → "
                    f"{booking['check_out']}"
                )

                st.write(
                    f"💰 Tiền phòng: "
                    f"**{float(booking['room_total']):,.0f} VNĐ**"
                )


                if st.button(
                    "🚪 XÁC NHẬN CHECK-OUT",
                    key=f"checkout_{booking['id']}",
                    use_container_width=True
                ):

                    execute_query(
                        """
                        UPDATE reservations
                        SET reservation_status = 'Đã check-out'
                        WHERE id = :id
                        """,
                        {
                            "id": int(booking["id"])
                        }
                    )


                    execute_query(
                        """
                        UPDATE rooms
                        SET
                            status = 'Chờ dọn',
                            housekeeping_status = 'Bẩn'
                        WHERE id = (
                            SELECT room_id
                            FROM reservations
                            WHERE id = :id
                        )
                        """,
                        {
                            "id": int(booking["id"])
                        }
                    )


                    st.success(
                        "✅ Check-out thành công."
                    )


                    st.info(
                        "🧹 Phòng đã chuyển sang trạng thái 'Chờ dọn'."
                    )


                    st.rerun()


# ============================================================
# 21. HOUSEKEEPING
# ============================================================

elif page == "🧹 Housekeeping":

    st.title(
        "🧹 QUẢN LÝ HOUSEKEEPING"
    )


    rooms = read_query(
        """
        SELECT
            r.id,
            r.room_number,
            rt.type_name,
            r.status,
            r.housekeeping_status,
            r.note
        FROM rooms r
        JOIN room_types rt
            ON r.room_type_id = rt.id
        ORDER BY r.room_number
        """
    )


    if rooms.empty:

        st.info(
            "📭 Chưa có phòng."
        )

    else:

        for _, room in rooms.iterrows():

            col1, col2, col3 = st.columns(3)


            with col1:

                st.markdown(
                    f"### 🛏️ Phòng {room['room_number']}"
                )

                st.write(
                    room["type_name"]
                )


            with col2:

                st.write(
                    f"Trạng thái phòng: **{room['status']}**"
                )

                st.write(
                    f"Vệ sinh: **{room['housekeeping_status']}**"
                )


            with col3:

                options = [
                    "Sạch",
                    "Đang dọn",
                    "Bẩn",
                    "Kiểm tra"
                ]


                current = room[
                    "housekeeping_status"
                ]


                selected = st.selectbox(
                    "Tình trạng mới",
                    options,
                    index=options.index(current)
                    if current in options else 0,
                    key=f"hk_{room['id']}"
                )


                if st.button(
                    "💾 Cập nhật",
                    key=f"save_hk_{room['id']}"
                ):

                    new_room_status = room["status"]


                    if selected == "Sạch":

                        if room["status"] == "Chờ dọn":

                            new_room_status = "Trống"


                    execute_query(
                        """
                        UPDATE rooms
                        SET
                            housekeeping_status = :housekeeping,
                            status = :status
                        WHERE id = :id
                        """,
                        {
                            "housekeeping": selected,
                            "status": new_room_status,
                            "id": int(room["id"])
                        }
                    )


                    st.success(
                        "✅ Đã cập nhật housekeeping."
                    )

                    st.rerun()


            st.markdown("---")


# ============================================================
# 22. BẢO TRÌ
# ============================================================

elif page == "🔧 Bảo trì":

    st.title(
        "🔧 QUẢN LÝ BẢO TRÌ PHÒNG"
    )


    tab1, tab2 = st.tabs(
        [
            "➕ Tạo phiếu bảo trì",
            "📋 Danh sách bảo trì"
        ]
    )


    rooms = read_query(
        """
        SELECT
            id,
            room_number
        FROM rooms
        ORDER BY room_number
        """
    )


    with tab1:

        if rooms.empty:

            st.warning(
                "⚠️ Chưa có phòng."
            )

        else:

            with st.form(
                "maintenance_form"
            ):

                room_options = [
                    f"Phòng {row.room_number}"
                    for row in rooms.itertuples()
                ]


                selected_room = st.selectbox(
                    "🛏️ Phòng",
                    room_options
                )


                room_index = room_options.index(
                    selected_room
                )


                room_id = int(
                    rooms.iloc[room_index]["id"]
                )


                issue = st.text_input(
                    "⚠️ Vấn đề",
                    placeholder="Máy lạnh không hoạt động"
                )


                description = st.text_area(
                    "📝 Mô tả chi tiết"
                )


                priority = st.selectbox(
                    "🚨 Mức độ ưu tiên",
                    [
                        "Thấp",
                        "Trung bình",
                        "Cao",
                        "Khẩn cấp"
                    ]
                )


                technician = st.text_input(
                    "👨‍🔧 Nhân viên kỹ thuật"
                )


                cost = st.number_input(
                    "💰 Chi phí dự kiến",
                    min_value=0,
                    value=0,
                    step=50000
                )


                submit = st.form_submit_button(
                    "🔧 TẠO PHIẾU BẢO TRÌ",
                    use_container_width=True
                )


                if submit:

                    if not issue.strip():

                        st.warning(
                            "⚠️ Vui lòng nhập vấn đề."
                        )

                    else:

                        success = execute_query(
                            """
                            INSERT INTO maintenance
                            (
                                room_id,
                                issue,
                                description,
                                priority,
                                status,
                                technician,
                                start_date,
                                cost,
                                created_at
                            )

                            VALUES
                            (
                                :room_id,
                                :issue,
                                :description,
                                :priority,
                                'Đang xử lý',
                                :technician,
                                :start_date,
                                :cost,
                                :created_at
                            )
                            """,
                            {
                                "room_id": room_id,
                                "issue": issue.strip(),
                                "description": description.strip(),
                                "priority": priority,
                                "technician": technician.strip(),
                                "start_date": date.today(),
                                "cost": cost,
                                "created_at": datetime.now()
                            }
                        )


                        if success:

                            execute_query(
                                """
                                UPDATE rooms
                                SET maintenance_status = 'Bảo trì',
                                    status = 'Khóa phòng'
                                WHERE id = :id
                                """,
                                {
                                    "id": room_id
                                }
                            )


                            st.success(
                                "✅ Đã tạo phiếu bảo trì."
                            )

                            st.rerun()


    with tab2:

        maintenance_df = read_query(
            """
            SELECT
                m.id,
                r.room_number,
                m.issue,
                m.description,
                m.priority,
                m.status,
                m.technician,
                m.start_date,
                m.end_date,
                m.cost,
                m.note
            FROM maintenance m
            JOIN rooms r
                ON m.room_id = r.id
            ORDER BY m.created_at DESC
            """
        )


        if maintenance_df.empty:

            st.info(
                "📭 Chưa có phiếu bảo trì."
            )

        else:

            for _, item in maintenance_df.iterrows():

                with st.expander(
                    f"🔧 Phòng {item['room_number']} - "
                    f"{item['issue']}"
                ):

                    st.write(
                        f"🚨 Ưu tiên: **{item['priority']}**"
                    )

                    st.write(
                        f"📋 Trạng thái: **{item['status']}**"
                    )

                    st.write(
                        f"👨‍🔧 Kỹ thuật: **{item['technician']}**"
                    )

                    st.write(
                        f"💰 Chi phí: "
                        f"**{float(item['cost']):,.0f} VNĐ**"
                    )

                    st.write(
                        item["description"]
                    )


                    options = [
                        "Đang xử lý",
                        "Hoàn thành",
                        "Hủy"
                    ]


                    new_status = st.selectbox(
                        "Cập nhật trạng thái",
                        options,
                        index=options.index(item["status"])
                        if item["status"] in options else 0,
                        key=f"maintenance_status_{item['id']}"
                    )


                    if st.button(
                        "💾 Cập nhật",
                        key=f"maintenance_save_{item['id']}"
                    ):

                        execute_query(
                            """
                            UPDATE maintenance
                            SET
                                status = :status,
                                end_date = CASE
                                    WHEN :status = 'Hoàn thành'
                                    THEN :end_date
                                    ELSE end_date
                                END
                            WHERE id = :id
                            """,
                            {
                                "status": new_status,
                                "end_date": date.today(),
                                "id": int(item["id"])
                            }
                        )


                        if new_status == "Hoàn thành":

                            execute_query(
                                """
                                UPDATE rooms
                                SET
                                    maintenance_status = 'Hoạt động',
                                    status = 'Chờ dọn',
                                    housekeeping_status = 'Kiểm tra'
                                WHERE id = (
                                    SELECT room_id
                                    FROM maintenance
                                    WHERE id = :id
                                )
                                """,
                                {
                                    "id": int(item["id"])
                                }
                            )


                        st.success(
                            "✅ Đã cập nhật."
                        )

                        st.rerun()


# ============================================================
# 23. DỊCH VỤ
# ============================================================

elif page == "🍽️ Dịch vụ":

    st.title(
        "🍽️ QUẢN LÝ DỊCH VỤ KHÁCH SẠN"
    )


    tab1, tab2, tab3 = st.tabs(
        [
            "📋 Danh sách dịch vụ",
            "➕ Thêm dịch vụ",
            "🧾 Ghi nhận sử dụng"
        ]
    )


    # ========================================================
    # DANH SÁCH DỊCH VỤ
    # ========================================================

    with tab1:

        services_df = read_query(
            """
            SELECT
                id,
                service_name,
                category,
                unit,
                price,
                description,
                active
            FROM services
            ORDER BY category, service_name
            """
        )


        if services_df.empty:

            st.info(
                "📭 Chưa có dịch vụ."
            )

        else:

            display = services_df.copy()


            display["price"] = (
                pd.to_numeric(
                    display["price"],
                    errors="coerce"
                )
                .fillna(0)
                .apply(lambda x: f"{x:,.0f} VNĐ")
            )


            display.columns = [
                "ID",
                "Tên dịch vụ",
                "Danh mục",
                "Đơn vị",
                "Giá",
                "Mô tả",
                "Hoạt động"
            ]


            st.dataframe(
                display,
                use_container_width=True,
                hide_index=True
            )


    # ========================================================
    # THÊM DỊCH VỤ
    # ========================================================

    with tab2:

        with st.form(
            "service_form"
        ):

            service_name = st.text_input(
                "🍽️ Tên dịch vụ"
            )


            category = st.text_input(
                "📂 Danh mục",
                placeholder="Ẩm thực / Minibar / Laundry..."
            )


            unit = st.text_input(
                "📏 Đơn vị",
                placeholder="suất / chai / kg..."
            )


            price = st.number_input(
                "💰 Đơn giá",
                min_value=0,
                value=50000,
                step=10000
            )


            description = st.text_area(
                "📝 Mô tả"
            )


            submit = st.form_submit_button(
                "💾 LƯU DỊCH VỤ",
                use_container_width=True
            )


            if submit:

                if not service_name.strip():

                    st.warning(
                        "⚠️ Vui lòng nhập tên dịch vụ."
                    )

                else:

                    execute_query(
                        """
                        INSERT INTO services
                        (
                            service_name,
                            category,
                            unit,
                            price,
                            description,
                            active,
                            created_at
                        )

                        VALUES
                        (
                            :name,
                            :category,
                            :unit,
                            :price,
                            :description,
                            1,
                            :created_at
                        )
                        """,
                        {
                            "name": service_name.strip(),
                            "category": category.strip(),
                            "unit": unit.strip(),
                            "price": price,
                            "description": description.strip(),
                            "created_at": datetime.now()
                        }
                    )


                    st.success(
                        "🎉 Đã thêm dịch vụ."
                    )

                    st.rerun()


    # ========================================================
    # GHI NHẬN SỬ DỤNG DỊCH VỤ
    # ========================================================

    with tab3:

        reservations_df = read_query(
            """
            SELECT
                r.id,
                r.booking_code,
                g.full_name,
                ro.room_number
            FROM reservations r
            JOIN guests g
                ON r.guest_id = g.id
            JOIN rooms ro
                ON r.room_id = ro.id
            WHERE r.reservation_status = 'Đã check-in'
            ORDER BY r.id DESC
            """
        )


        active_services = read_query(
            """
            SELECT
                id,
                service_name,
                price,
                unit
            FROM services
            WHERE active = 1
            ORDER BY service_name
            """
        )


        if reservations_df.empty:

            st.info(
                "📭 Chưa có khách đang lưu trú."
            )

        elif active_services.empty:

            st.info(
                "📭 Chưa có dịch vụ."
            )

        else:

            with st.form(
                "service_usage_form"
            ):

                reservation_options = [
                    f"{row.booking_code} - "
                    f"{row.full_name} - "
                    f"Phòng {row.room_number}"
                    for row in reservations_df.itertuples()
                ]


                selected_reservation = st.selectbox(
                    "👤 Khách / Booking",
                    reservation_options
                )


                reservation_index = reservation_options.index(
                    selected_reservation
                )


                reservation_id = int(
                    reservations_df.iloc[
                        reservation_index
                    ]["id"]
                )


                service_options = [
                    f"{row.service_name} - "
                    f"{float(row.price):,.0f} VNĐ/{row.unit}"
                    for row in active_services.itertuples()
                ]


                selected_service = st.selectbox(
                    "🍽️ Dịch vụ",
                    service_options
                )


                service_index = service_options.index(
                    selected_service
                )


                service = active_services.iloc[
                    service_index
                ]


                service_id = int(
                    service["id"]
                )


                quantity = st.number_input(
                    "🔢 Số lượng",
                    min_value=1,
                    value=1
                )


                usage_total = (
                    float(service["price"])
                    * quantity
                )


                st.metric(
                    "💰 Thành tiền",
                    f"{usage_total:,.0f} VNĐ"
                )


                note = st.text_area(
                    "📝 Ghi chú"
                )


                submit = st.form_submit_button(
                    "🍽️ GHI NHẬN DỊCH VỤ",
                    use_container_width=True
                )


                if submit:

                    execute_query(
                        """
                        INSERT INTO service_usages
                        (
                            reservation_id,
                            service_id,
                            quantity,
                            unit_price,
                            total_price,
                            used_at,
                            note
                        )

                        VALUES
                        (
                            :reservation_id,
                            :service_id,
                            :quantity,
                            :unit_price,
                            :total_price,
                            :used_at,
                            :note
                        )
                        """,
                        {
                            "reservation_id": reservation_id,
                            "service_id": service_id,
                            "quantity": quantity,
                            "unit_price": float(service["price"]),
                            "total_price": usage_total,
                            "used_at": datetime.now(),
                            "note": note.strip()
                        }
                    )


                    st.success(
                        "✅ Đã ghi nhận dịch vụ."
                    )

                    st.rerun()


# ============================================================
# 24. HÓA ĐƠN
# ============================================================

elif page == "🧾 Hóa đơn":

    st.title(
        "🧾 HÓA ĐƠN KHÁCH SẠN"
    )


    reservations_df = read_query(
        """
        SELECT
            r.id,
            r.booking_code,
            g.full_name,
            ro.room_number,
            r.room_total,
            r.payment_status,
            r.deposit,
            r.reservation_status
        FROM reservations r
        JOIN guests g
            ON r.guest_id = g.id
        JOIN rooms ro
            ON r.room_id = ro.id
        ORDER BY r.created_at DESC
        """
    )


    if reservations_df.empty:

        st.info(
            "📭 Chưa có đặt phòng."
        )

    else:

        reservation_options = [
            f"{row.booking_code} - "
            f"{row.full_name} - "
            f"Phòng {row.room_number}"
            for row in reservations_df.itertuples()
        ]


        selected_reservation = st.selectbox(
            "🔖 Chọn booking",
            reservation_options
        )


        reservation_index = reservation_options.index(
            selected_reservation
        )


        reservation = reservations_df.iloc[
            reservation_index
        ]


        reservation_id = int(
            reservation["id"]
        )


        room_total = float(
            reservation["room_total"]
        )


        # ----------------------------------------------------
        # DỊCH VỤ
        # ----------------------------------------------------

        service_total_df = read_query(
            """
            SELECT
                COALESCE(
                    SUM(total_price),
                    0
                ) AS total
            FROM service_usages
            WHERE reservation_id = :reservation_id
            """,
            {
                "reservation_id": reservation_id
            }
        )


        service_total = float(
            service_total_df.iloc[0]["total"]
        )


        col1, col2, col3 = st.columns(3)


        with col1:

            st.metric(
                "🛏️ Tiền phòng",
                f"{room_total:,.0f} VNĐ"
            )


        with col2:

            st.metric(
                "🍽️ Dịch vụ",
                f"{service_total:,.0f} VNĐ"
            )


        with col3:

            st.metric(
                "💰 Tổng cộng",
                f"{room_total + service_total:,.0f} VNĐ"
            )


        st.markdown("---")


        # ----------------------------------------------------
        # CHI TIẾT DỊCH VỤ
        # ----------------------------------------------------

        usage_df = read_query(
            """
            SELECT
                s.service_name AS `Dịch vụ`,
                su.quantity AS `Số lượng`,
                su.unit_price AS `Đơn giá`,
                su.total_price AS `Thành tiền`,
                su.used_at AS `Thời gian`
            FROM service_usages su
            JOIN services s
                ON su.service_id = s.id
            WHERE su.reservation_id = :reservation_id
            ORDER BY su.used_at DESC
            """,
            {
                "reservation_id": reservation_id
            }
        )


        st.subheader(
            "🍽️ Chi tiết dịch vụ"
        )


        if usage_df.empty:

            st.info(
                "Chưa sử dụng dịch vụ."
            )

        else:

            st.dataframe(
                usage_df,
                use_container_width=True,
                hide_index=True
            )


        st.markdown("---")


        # ----------------------------------------------------
        # TẠO HÓA ĐƠN
        # ----------------------------------------------------

        discount = st.number_input(
            "🏷️ Giảm giá",
            min_value=0,
            value=0,
            step=50000
        )


        tax_percent = st.number_input(
            "🧾 Thuế (%)",
            min_value=0.0,
            max_value=100.0,
            value=0.0,
            step=1.0
        )


        subtotal = (
            room_total
            + service_total
            - discount
        )


        tax = (
            subtotal
            * tax_percent
            / 100
        )


        grand_total = (
            subtotal
            + tax
        )


        st.metric(
            "💰 TỔNG THANH TOÁN",
            f"{grand_total:,.0f} VNĐ"
        )


        payment_method = st.selectbox(
            "💳 Phương thức thanh toán",
            [
                "Tiền mặt",
                "Chuyển khoản",
                "Thẻ",
                "Ví điện tử"
            ]
        )


        paid_amount = st.number_input(
            "💵 Số tiền khách thanh toán",
            min_value=0,
            value=int(grand_total),
            step=50000
        )


        if paid_amount >= grand_total:

            invoice_status = "Đã thanh toán"

        elif paid_amount > 0:

            invoice_status = "Thanh toán một phần"

        else:

            invoice_status = "Chưa thanh toán"


        if st.button(
            "🧾 TẠO HÓA ĐƠN",
            use_container_width=True
        ):

            invoice_code = (
                "HD"
                + datetime.now().strftime(
                    "%Y%m%d%H%M%S"
                )
            )


            success = execute_query(
                """
                INSERT INTO invoices
                (
                    invoice_code,
                    reservation_id,
                    room_total,
                    service_total,
                    discount,
                    tax,
                    grand_total,
                    paid_amount,
                    payment_method,
                    payment_status,
                    created_at
                )

                VALUES
                (
                    :invoice_code,
                    :reservation_id,
                    :room_total,
                    :service_total,
                    :discount,
                    :tax,
                    :grand_total,
                    :paid_amount,
                    :payment_method,
                    :payment_status,
                    :created_at
                )
                """,
                {
                    "invoice_code": invoice_code,
                    "reservation_id": reservation_id,
                    "room_total": room_total,
                    "service_total": service_total,
                    "discount": discount,
                    "tax": tax,
                    "grand_total": grand_total,
                    "paid_amount": paid_amount,
                    "payment_method": payment_method,
                    "payment_status": invoice_status,
                    "created_at": datetime.now()
                }
            )


            if success:

                execute_query(
                    """
                    UPDATE reservations
                    SET
                        payment_status = :status
                    WHERE id = :id
                    """,
                    {
                        "status": invoice_status,
                        "id": reservation_id
                    }
                )


                st.success(
                    f"🎉 Tạo hóa đơn thành công: **{invoice_code}**"
                )

                st.balloons()


# ============================================================
# 25. BÁO CÁO
# ============================================================

elif page == "📊 Báo cáo":

    st.title(
        "📊 BÁO CÁO & THỐNG KÊ KHÁCH SẠN"
    )


    # --------------------------------------------------------
    # DOANH THU
    # --------------------------------------------------------

    invoices_df = read_query(
        """
        SELECT
            id,
            invoice_code,
            grand_total,
            paid_amount,
            payment_status,
            payment_method,
            created_at
        FROM invoices
        ORDER BY created_at DESC
        """
    )


    if invoices_df.empty:

        total_revenue = 0
        paid_revenue = 0

    else:

        invoices_df["grand_total"] = pd.to_numeric(
            invoices_df["grand_total"],
            errors="coerce"
        ).fillna(0)


        invoices_df["paid_amount"] = pd.to_numeric(
            invoices_df["paid_amount"],
            errors="coerce"
        ).fillna(0)


        total_revenue = (
            invoices_df["grand_total"].sum()
        )


        paid_revenue = (
            invoices_df["paid_amount"].sum()
        )


    # --------------------------------------------------------
    # BOOKING
    # --------------------------------------------------------

    booking_count_df = read_query(
        """
        SELECT COUNT(*) AS total
        FROM reservations
        """
    )


    booking_count = int(
        booking_count_df.iloc[0]["total"]
    )


    # --------------------------------------------------------
    # KHÁCH
    # --------------------------------------------------------

    guest_count_df = read_query(
        """
        SELECT COUNT(*) AS total
        FROM guests
        """
    )


    guest_count = int(
        guest_count_df.iloc[0]["total"]
    )


    col1, col2, col3, col4 = st.columns(4)


    with col1:

        st.metric(
            "💰 Doanh thu",
            f"{total_revenue:,.0f} VNĐ"
        )


    with col2:

        st.metric(
            "💵 Đã thu",
            f"{paid_revenue:,.0f} VNĐ"
        )


    with col3:

        st.metric(
            "📅 Booking",
            booking_count
        )


    with col4:

        st.metric(
            "👤 Khách hàng",
            guest_count
        )


    st.markdown("---")


    # --------------------------------------------------------
    # DOANH THU THEO NGÀY
    # --------------------------------------------------------

    st.subheader(
        "📅 Doanh thu theo ngày"
    )


    daily = read_query(
        """
        SELECT
            DATE(created_at) AS day,
            SUM(grand_total) AS revenue
        FROM invoices
        GROUP BY DATE(created_at)
        ORDER BY day
        """
    )


    if not daily.empty:

        daily["revenue"] = pd.to_numeric(
            daily["revenue"],
            errors="coerce"
        ).fillna(0)


        st.bar_chart(
            daily.set_index("day")["revenue"]
        )

    else:

        st.info(
            "Chưa có dữ liệu doanh thu."
        )


    st.markdown("---")


    # --------------------------------------------------------
    # CÔNG SUẤT PHÒNG
    # --------------------------------------------------------

    st.subheader(
        "🛏️ Tình trạng phòng"
    )


    room_status = read_query(
        """
        SELECT
            status,
            COUNT(*) AS quantity
        FROM rooms
        GROUP BY status
        ORDER BY quantity DESC
        """
    )


    if not room_status.empty:

        st.bar_chart(
            room_status.set_index(
                "status"
            )["quantity"]
        )


    st.markdown("---")


    # --------------------------------------------------------
    # DOANH THU THEO LOẠI PHÒNG
    # --------------------------------------------------------

    st.subheader(
        "🏷️ Doanh thu theo loại phòng"
    )


    room_type_revenue = read_query(
        """
        SELECT
            rt.type_name,
            SUM(r.room_total) AS revenue
        FROM reservations r
        JOIN rooms ro
            ON r.room_id = ro.id
        JOIN room_types rt
            ON ro.room_type_id = rt.id
        WHERE r.reservation_status <> 'Đã hủy'
        GROUP BY rt.type_name
        ORDER BY revenue DESC
        """
    )


    if not room_type_revenue.empty:

        room_type_revenue["revenue"] = pd.to_numeric(
            room_type_revenue["revenue"],
            errors="coerce"
        ).fillna(0)


        st.bar_chart(
            room_type_revenue.set_index(
                "type_name"
            )["revenue"]
        )


# ============================================================
# 26. ADMIN
# ============================================================

elif page == "🔑 Admin":

    st.title(
        "🔑 QUẢN TRỊ HỆ THỐNG"
    )


    if not st.session_state.admin_logged_in:

        with st.form(
            "admin_login"
        ):

            password = st.text_input(
                "🔐 Mật khẩu Admin",
                type="password"
            )


            login = st.form_submit_button(
                "🔑 ĐĂNG NHẬP"
            )


            if login:

                if password == "123456":

                    st.session_state.admin_logged_in = True

                    st.success(
                        "✅ Đăng nhập thành công."
                    )

                    st.rerun()

                else:

                    st.error(
                        "❌ Mật khẩu không chính xác."
                    )


        st.stop()


    st.success(
        "🟢 Bạn đang đăng nhập với quyền Admin."
    )


    if st.button(
        "🔒 Đăng xuất"
    ):

        st.session_state.admin_logged_in = False

        st.rerun()


    st.markdown("---")


    st.subheader(
        "📋 Toàn bộ booking"
    )


    all_reservations = read_query(
        """
        SELECT
            r.booking_code AS `Mã booking`,
            g.full_name AS `Khách`,
            g.phone AS `Điện thoại`,
            ro.room_number AS `Phòng`,
            rt.type_name AS `Loại phòng`,
            r.check_in AS `Check-in`,
            r.check_out AS `Check-out`,
            r.nights AS `Số đêm`,
            r.room_total AS `Tiền phòng`,
            r.payment_status AS `Thanh toán`,
            r.reservation_status AS `Trạng thái`
        FROM reservations r
        JOIN guests g
            ON r.guest_id = g.id
        JOIN rooms ro
            ON r.room_id = ro.id
        JOIN room_types rt
            ON ro.room_type_id = rt.id
        ORDER BY r.created_at DESC
        """
    )


    if all_reservations.empty:

        st.info(
            "Chưa có booking."
        )

    else:

        st.dataframe(
            all_reservations,
            use_container_width=True,
            hide_index=True
        )


    st.markdown("---")


    st.subheader(
        "🏨 Toàn bộ phòng"
    )


    all_rooms = read_query(
        """
        SELECT
            r.room_number AS `Phòng`,
            r.floor AS `Tầng`,
            rt.type_name AS `Loại phòng`,
            rt.price_per_night AS `Giá/đêm`,
            r.status AS `Trạng thái`,
            r.housekeeping_status AS `Housekeeping`,
            r.maintenance_status AS `Bảo trì`,
            r.note AS `Ghi chú`
        FROM rooms r
        JOIN room_types rt
            ON r.room_type_id = rt.id
        ORDER BY r.floor, r.room_number
        """
    )


    st.dataframe(
        all_rooms,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# 27. FOOTER
# ============================================================

st.sidebar.markdown("---")

st.sidebar.caption(
    "🏨 Melia TwoChanel"
)

st.sidebar.caption(
    "Hệ thống quản lý khách sạn"
)

st.sidebar.caption(
    "BVU - Quản trị dịch vụ du lịch và lữ hành"
)
