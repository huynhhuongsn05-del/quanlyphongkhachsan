import streamlit as st
import pandas as pd
from datetime import datetime, date
import plotly.express as px

# -----------------------------------------------------------------------------
# CONFIG & STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Hotel Management System",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Khởi tạo dữ liệu mẫu trong Session State nếu chưa có
if "rooms" not in st.cookies and "rooms" not in st.session_state:
    st.session_state.rooms = pd.DataFrame([
        {"room_num": "101", "type": "Standard", "price": 500000, "status": "Trống", "clean_status": "Sạch"},
        {"room_num": "102", "type": "Standard", "price": 500000, "status": "Có khách", "clean_status": "Sạch"},
        {"room_num": "103", "type": "Deluxe", "price": 800000, "status": "Trống", "clean_status": "Bẩn"},
        {"room_num": "201", "type": "Deluxe", "price": 800000, "status": "Đã đặt", "clean_status": "Sạch"},
        {"room_num": "202", "type": "Suite", "price": 1500000, "status": "Có khách", "clean_status": "Sạch"},
        {"room_num": "203", "type": "Suite", "price": 1500000, "status": "Bảo trì", "clean_status": "Bẩn"},
    ])

if "bookings" not in st.session_state:
    st.session_state.bookings = pd.DataFrame([
        {
            "booking_id": "BK001",
            "guest_name": "Nguyễn Văn A",
            "phone": "0901234567",
            "room_num": "102",
            "check_in": date.today(),
            "check_out": date.today(),
            "status": "Check-in",
            "total_price": 500000
        },
        {
            "booking_id": "BK002",
            "guest_name": "Trần Thị B",
            "phone": "0987654321",
            "room_num": "202",
            "check_in": date.today(),
            "check_out": date.today(),
            "status": "Check-in",
            "total_price": 1500000
        }
    ])

if "revenue_history" not in st.session_state:
    st.session_state.revenue_history = pd.DataFrame([
        {"date": date.today(), "amount": 2000000, "room_num": "102", "guest_name": "Nguyễn Văn A"},
    ])

# -----------------------------------------------------------------------------
# SIDEBAR NAVIGATION
# -----------------------------------------------------------------------------
st.sidebar.title("🏨 HOTEL PMS")
st.sidebar.caption("Hệ thống Quản lý Khách sạn Vận hành")

menu = st.sidebar.radio(
    "Danh mục quản lý",
    ["Sơ đồ phòng (Room Rack)", "Lễ tân & Đặt phòng", "Buồng phòng (Housekeeping)", "Báo cáo Doanh thu & KPIs"]
)

# -----------------------------------------------------------------------------
# MODULE 1: SƠ ĐỒ PHÒNG (ROOM RACK)
# -----------------------------------------------------------------------------
if menu == "Sơ đồ phòng (Room Rack)":
    st.title("📌 Sơ đồ phòng Realtime")
    st.caption("Tổng quan trạng thái tất cả các phòng trong khách sạn")

    # Filter
    filter_status = st.selectbox("Lọc theo trạng thái phòng", ["Tất cả", "Trống", "Có khách", "Đã đặt", "Bảo trì"])
    
    rooms_df = st.session_state.rooms.copy()
    if filter_status != "Tất cả":
        rooms_df = rooms_df[rooms_df["status"] == filter_status]

    # Grid Display
    cols = st.columns(3)
    status_colors = {
        "Trống": "#28a745",
        "Có khách": "#dc3545",
        "Đã đặt": "#ffc107",
        "Bảo trì": "#6c757d"
    }

    for idx, row in rooms_df.iterrows():
        col = cols[idx % 3]
        color = status_colors.get(row["status"], "#333")
        
        with col:
            st.markdown(
                f"""
                <div style="border: 2px solid {color}; border-radius: 8px; padding: 12px; margin-bottom: 12px; background-color: #f8f9fa;">
                    <h3 style="margin: 0; color: {color};">Phòng {row['room_num']} - {row['type']}</h3>
                    <p style="margin: 4px 0;"><b>Trạng thái:</b> <span style="color: {color}; font-weight: bold;">{row['status']}</span></p>
                    <p style="margin: 4px 0;"><b>Vệ sinh:</b> {row['clean_status']}</p>
                    <p style="margin: 4px 0;"><b>Giá phòng:</b> {row['price']:,} VNĐ/đêm</p>
                </div>
                """,
                unsafe_allow_html=True
            )

# -----------------------------------------------------------------------------
# MODULE 2: LỄ TÂN & ĐẶT PHÒNG
# -----------------------------------------------------------------------------
elif menu == "Lễ tân & Đặt phòng":
    st.title("🛎️ Nghiệp vụ Lễ tân")
    
    tab1, tab2, tab3 = st.tabs(["Tạo Đặt phòng / Check-in", "Danh sách Đặt phòng", "Thực hiện Check-out"])

    with tab1:
        st.subheader("Tạo lượt Đặt phòng mới")
        
        # Chỉ lấy phòng Trống
        available_rooms = st.session_state.rooms[st.session_state.rooms["status"] == "Trống"]["room_num"].tolist()
        
        if not available_rooms:
            st.warning("Hiện tại không có phòng trống để đặt!")
        else:
            with st.form("booking_form"):
                col1, col2 = st.columns(2)
                with col1:
                    guest_name = st.text_input("Tên khách hàng")
                    phone = st.text_input("Số điện thoại")
                    room_num = st.selectbox("Chọn phòng trống", available_rooms)
                
                with col2:
                    check_in = st.date_input("Ngày Check-in", value=date.today())
                    check_out = st.date_input("Ngày Check-out", value=date.today())
                    action_type = st.radio("Hành động", ["Đặt trước (Reservation)", "Check-in ngay"])

                submit = st.form_submit_button("Xác nhận")
                
                if submit:
                    if not guest_name or not phone:
                        st.error("Vui lòng nhập đầy đủ thông tin khách hàng.")
                    elif check_out < check_in:
                        st.error("Ngày Check-out phải lớn hơn hoặc bằng ngày Check-in.")
                    else:
                        nights = (check_out - check_in).days or 1
                        room_price = st.session_state.rooms.loc[st.session_state.rooms["room_num"] == room_num, "price"].values[0]
                        total_price = room_price * nights

                        new_id = f"BK{len(st.session_state.bookings) + 1:03d}"
                        status_str = "Check-in" if action_type == "Check-in ngay" else "Đã đặt"
                        
                        # Thêm booking mới
                        new_booking = pd.DataFrame([{
                            "booking_id": new_id,
                            "guest_name": guest_name,
                            "phone": phone,
                            "room_num": room_num,
                            "check_in": check_in,
                            "check_out": check_out,
                            "status": status_str,
                            "total_price": total_price
                        }])
                        st.session_state.bookings = pd.concat([st.session_state.bookings, new_booking], ignore_index=True)
                        
                        # Cập nhật trạng thái phòng
                        new_room_status = "Có khách" if action_type == "Check-in ngay" else "Đã đặt"
                        st.session_state.rooms.loc[st.session_state.rooms["room_num"] == room_num, "status"] = new_room_status
                        
                        st.success(f"Tạo thành công booking {new_id} cho phòng {room_num}!")
                        st.rerun()

    with tab2:
        st.subheader("Danh sách Đặt phòng")
        st.dataframe(st.session_state.bookings, use_container_width=True)

    with tab3:
        st.subheader("Thực hiện Check-out & Thanh toán")
        active_bookings = st.session_state.bookings[st.session_state.bookings["status"] == "Check-in"]
        
        if active_bookings.empty:
            st.info("Không có phòng nào đang sử dụng cần Check-out.")
        else:
            selected_bk = st.selectbox("Chọn mã đặt phòng Check-out", active_bookings["booking_id"].tolist())
            bk_info = active_bookings[active_bookings["booking_id"] == selected_bk].iloc[0]
            
            st.write(f"**Khách hàng:** {bk_info['guest_name']}")
            st.write(f"**Phòng:** {bk_info['room_num']}")
            st.write(f"**Tổng tiền thanh toán:** {bk_info['total_price']:,} VNĐ")
            
            if st.button("Xác nhận Check-out & Thanh toán"):
                # Cập nhật trạng thái Booking
                st.session_state.bookings.loc[st.session_state.bookings["booking_id"] == selected_bk, "status"] = "Đã trả phòng"
                
                # Cập nhật trạng thái Phòng
                st.session_state.rooms.loc[st.session_state.rooms["room_num"] == bk_info["room_num"], "status"] = "Trống"
                st.session_state.rooms.loc[st.session_state.rooms["room_num"] == bk_info["room_num"], "clean_status"] = "Bẩn"
                
                # Lưu lịch sử doanh thu
                new_rev = pd.DataFrame([{
                    "date": date.today(),
                    "amount": bk_info["total_price"],
                    "room_num": bk_info["room_num"],
                    "guest_name": bk_info["guest_name"]
                }])
                st.session_state.revenue_history = pd.concat([st.session_state.revenue_history, new_rev], ignore_index=True)
                
                st.success(f"Phòng {bk_info['room_num']} đã Check-out thành công. Trạng thái phòng chuyển thành 'Trống' và 'Bẩn'.")
                st.rerun()

# -----------------------------------------------------------------------------
# MODULE 3: BUỒNG PHÒNG (HOUSEKEEPING)
# -----------------------------------------------------------------------------
elif menu == "Buồng phòng (Housekeeping)":
    st.title("🧹 Quản lý Buồng phòng")
    st.caption("Cập nhật tình trạng vệ sinh phòng cho nhân viên Housekeeping")

    hk_df = st.session_state.rooms[["room_num", "type", "status", "clean_status"]].copy()
    
    for idx, row in hk_df.iterrows():
        col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
        col1.write(f"**Phòng {row['room_num']}** ({row['type']})")
        col2.write(f"Trạng thái: **{row['status']}**")
        col3.write(f"Vệ sinh: **{row['clean_status']}**")
        
        with col4:
            if row["clean_status"] == "Bẩn":
                if st.button(f"Đánh dấu Sạch - Phòng {row['room_num']}", key=f"clean_{row['room_num']}"):
                    st.session_state.rooms.loc[st.session_state.rooms["room_num"] == row["room_num"], "clean_status"] = "Sạch"
                    st.rerun()
            else:
                if st.button(f"Đánh dấu Bẩn - Phòng {row['room_num']}", key=f"dirty_{row['room_num']}"):
                    st.session_state.rooms.loc[st.session_state.rooms["room_num"] == row["room_num"], "clean_status"] = "Bẩn"
                    st.rerun()
        st.divider()

# -----------------------------------------------------------------------------
# MODULE 4: BÁO CÁO DOANH THU & KPIS
# -----------------------------------------------------------------------------
elif menu == "Báo cáo Doanh thu & KPIs":
    st.title("📊 Báo cáo Quản trị Khách sạn")
    
    # 1. KPIs
    total_rooms = len(st.session_state.rooms)
    occupied_rooms = len(st.session_state.rooms[st.session_state.rooms["status"] == "Có khách"])
    occupancy_rate = (occupied_rooms / total_rooms) * 100 if total_rooms > 0 else 0
    total_revenue = st.session_state.revenue_history["amount"].sum()
    revpar = total_revenue / total_rooms if total_rooms > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Tổng số phòng", f"{total_rooms} phòng")
    col2.metric("Số phòng đang có khách", f"{occupied_rooms} phòng")
    col3.metric("Công suất phòng (Occupancy)", f"{occupancy_rate:.1f}%")
    col4.metric("RevPAR (Doanh thu/Phòng sẵn có)", f"{revpar:,.0f} VNĐ")

    st.divider()

    # 2. Charts
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("Cơ cấu Trạng thái Phòng")
        status_counts = st.session_state.rooms["status"].value_counts().reset_index()
        status_counts.columns = ["Trạng thái", "Số lượng"]
        fig_pie = px.pie(status_counts, values="Số lượng", names="Trạng thái", color="Trạng thái",
                         color_discrete_map={"Trống": "#28a745", "Có khách": "#dc3545", "Đã đặt": "#ffc107", "Bảo trì": "#6c757d"})
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_chart2:
        st.subheader("Nhật ký Lịch sử Doanh thu")
        st.dataframe(st.session_state.revenue_history, use_container_width=True)
