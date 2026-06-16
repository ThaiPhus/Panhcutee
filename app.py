import streamlit as st

# Tiêu đề ứng dụng
st.title("💰 Ứng dụng tính tiền gửi tiết kiệm")

# Nhập dữ liệu
C = st.number_input(
    "Nhập số tiền khách hàng gửi tiết kiệm (triệu đồng)",
    min_value=0.0,
    value=100.0
)

i = st.number_input(
    "Nhập lãi suất gửi tiết kiệm theo năm (%)",
    min_value=0.0,
    value=6.0
)

n = st.number_input(
    "Nhập số tháng khách hàng gửi tiết kiệm",
    min_value=1,
    value=12
)

# Đổi lãi suất từ % sang số thập phân
i = i / 100

# Nút tính toán
if st.button("Tính toán"):
    
    # Lãi đơn
    An = C * (1 + (i / 12) * n)

    # Lãi kép
    Bn = C * (1 + i / 12) ** n

    st.success("Kết quả tính toán")

    st.write(
        f"📌 Số tiền khách hàng nhận được theo lãi đơn: **{An:,.2f} triệu đồng**"
    )

    st.write(
        f"📌 Số tiền khách hàng nhận được theo lãi kép: **{Bn:,.2f} triệu đồng**"
    )
