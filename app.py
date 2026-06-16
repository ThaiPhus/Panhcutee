import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

# Set page configuration
st.set_page_config(
    page_title="Tính Thuế Thu Nhập Cá Nhân - Việt Nam",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .metric-value {
        font-size: 2em;
        font-weight: bold;
        color: #1f77b4;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #ffc107;
    }
    .success-box {
        background-color: #d4edda;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #28a745;
    }
    </style>
    """, unsafe_allow_html=True)

# Title and Description
st.title("💰 Tính Thuế Thu Nhập Cá Nhân - Việt Nam")
st.markdown("Tính toán thuế thu nhập cá nhân theo luật thuế hiện hành của Việt Nam (năm 2024)")

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["📝 Nhập Thông Tin", "🧮 Tính Toán", "📊 Phân Tích", "💾 Kết Quả"])

# ========== TAB 1: INPUT INFORMATION ==========
with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("👤 Thông Tin Cá Nhân")
        full_name = st.text_input("Họ và tên", value="")
        citizen_id = st.text_input("CMND/CCCD", value="")
        tax_code = st.text_input("Mã số thuế (nếu có)", value="")
    
    with col2:
        st.subheader("📅 Thời Gian & Loại Thu Nhập")
        tax_year = st.selectbox("Năm tính thuế", [2024, 2023, 2022, 2021])
        calc_type = st.radio("Loại tính thuế", ["Hàng tháng", "Hàng năm"])
    
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("💼 Thu Nhập Từ Lao Động")
        salary = st.number_input("Lương/Thu nhập từ công việc chính", value=0.0, min_value=0.0, step=100000.0)
        allowance = st.number_input("Phụ cấp (cấp bậc, vị trí, khu vực...)", value=0.0, min_value=0.0, step=100000.0)
        bonus = st.number_input("Thưởng, tiền hoa hồng", value=0.0, min_value=0.0, step=100000.0)
    
    with col2:
        st.subheader("🏢 Thu Nhập Khác")
        part_time_income = st.number_input("Thu nhập từ công việc thêm", value=0.0, min_value=0.0, step=100000.0)
        rental_income = st.number_input("Thu nhập cho thuê bất động sản", value=0.0, min_value=0.0, step=100000.0)
        business_income = st.number_input("Thu nhập từ hoạt động kinh doanh", value=0.0, min_value=0.0, step=100000.0)
    
    with col3:
        st.subheader("📈 Thu Nhập Từ Vốn")
        dividend_income = st.number_input("Cổ tức, lợi tức từ cổ phần", value=0.0, min_value=0.0, step=100000.0)
        transfer_income = st.number_input("Lãi suất, tiền lãi", value=0.0, min_value=0.0, step=100000.0)
        capital_gain = st.number_input("Lãi từ chuyển nhượng tài sản", value=0.0, min_value=0.0, step=100000.0)
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎓 Các Khoản Giảm Trừ")
        
        st.markdown("**Giảm trừ gia cảnh:**")
        is_minor_child = st.checkbox("Có con dưới 18 tuổi (mỗi con: 4,800,000 đ/năm)")
        num_minor_children = 0
        if is_minor_child:
            num_minor_children = st.number_input("Số lượng con dưới 18 tuổi", min_value=0, max_value=10, value=0)
        
        is_dependent_child = st.checkbox("Có con từ 18-24 tuổi đang học tập (mỗi con: 4,800,000 đ/năm)")
        num_dependent_children = 0
        if is_dependent_child:
            num_dependent_children = st.number_input("Số lượng con 18-24 tuổi", min_value=0, max_value=10, value=0)
        
        st.markdown("**Khoản giảm trừ khác:**")
        insurance_contribution = st.number_input("Bảo hiểm xã hội, y tế, thất nghiệp", value=0.0, min_value=0.0, step=100000.0, 
                                                  help="Bao gồm BHXH, BHYT, BHTN (nếu không có, sẽ được tính tự động)")
    
    with col2:
        st.subheader("💰 Chi Phí & Khoản Khác")
        
        st.markdown("**Chi phí cho hoạt động kinh doanh/HĐKD:**")
        business_expense_ratio = st.selectbox("Tỷ lệ chi phí kinh doanh (%)", 
                                               [0, 5, 10, 15, 20, 25, 30],
                                               help="Tỷ lệ chi phí hợp lý so với thu nhập kinh doanh")
        
        st.markdown("**Khoản khác:**")
        charitable_donation = st.number_input("Tài trợ, quyên góp từ thiện", value=0.0, min_value=0.0, step=100000.0,
                                              help="Không quá 10% thu nhập chịu thuế")
        
        st.markdown("**Thuế đã nộp/đã khấu trừ:**")
        personal_income_tax_paid = st.number_input("Thuế TNCN đã nộp/khấu trừ", value=0.0, min_value=0.0, step=100000.0)

# ========== TAB 2: CALCULATIONS ==========
with tab2:
    st.subheader("🧮 Chi Tiết Tính Toán Thuế TNCN")
    
    # Vietnamese tax brackets for personal income (2024)
    # Based on Decree 124/2020/ND-CP and current regulations
    
    tax_brackets_2024 = [
        (5000000, 0.05),
        (10000000, 0.10),
        (18000000, 0.15),
        (32000000, 0.20),
        (52000000, 0.25),
        (80000000, 0.30),
        (float('inf'), 0.35)
    ]
    
    # Special tax rates
    DIVIDEND_TAX_RATE = 0.10  # 10% for dividends
    CAPITAL_GAIN_TAX_RATE = 0.20  # 20% for capital gains
    RENTAL_INCOME_TAX_RATE = 0.10  # 10% for rental income
    INTEREST_TAX_RATE = 0.10  # 10% for interest income
    
    def calculate_insurance_contribution(base_income):
        """Calculate social insurance contributions (8% BHXH, 1.5% BHYT, 0.5% BHTN)"""
        if base_income > 0:
            bhxh = base_income * 0.08
            bhyt = base_income * 0.015
            bhtn = base_income * 0.005
            return bhxh + bhyt + bhtn
        return 0
    
    def calculate_dependent_deduction(num_minor, num_dependent):
        """Calculate deduction for dependents"""
        # 4,800,000 VND per child per year
        annual_deduction = (num_minor + num_dependent) * 4800000
        return annual_deduction
    
    def calculate_income_tax(taxable_income):
        """Calculate progressive income tax using Vietnamese tax brackets"""
        if taxable_income <= 0:
            return 0
        
        tax = 0
        previous_limit = 0
        
        for limit, rate in tax_brackets_2024:
            if taxable_income <= previous_limit:
                break
            
            income_in_bracket = min(taxable_income, limit) - previous_limit
            tax += income_in_bracket * rate
            previous_limit = limit
        
        return tax
    
    # Collect all income sources
    labor_income = salary + allowance + bonus
    part_time = part_time_income
    other_business_income = business_income
    
    # Investment income - separate tax treatment
    dividend_income_tax = dividend_income * DIVIDEND_TAX_RATE
    transfer_income_tax = transfer_income * INTEREST_TAX_RATE
    capital_gain_tax = capital_gain * CAPITAL_GAIN_TAX_RATE
    rental_income_tax = rental_income * RENTAL_INCOME_TAX_RATE
    
    # Calculate insurance contributions
    if insurance_contribution == 0:
        # Auto-calculate if not provided (typically 10% of salary)
        calculated_insurance = calculate_insurance_contribution(labor_income)
    else:
        calculated_insurance = insurance_contribution
    
    # Calculate dependent deductions
    dependent_deduction = calculate_dependent_deduction(num_minor_children, num_dependent_children)
    
    # Total taxable income (for progressive tax)
    total_labor_income = labor_income + part_time + other_business_income
    
    # Business expenses
    business_expenses = (business_income * business_expense_ratio) / 100
    
    # Personal income after expenses (before deductions and special income)
    labor_income_after_expenses = total_labor_income - business_expenses
    
    # Standard personal deduction (11 million VND per month, 132 million per year)
    if calc_type == "Hàng tháng":
        standard_deduction = 11000000
        period_text = "tháng"
    else:
        standard_deduction = 132000000
        period_text = "năm"
    
    # Calculate taxable income for progressive tax
    taxable_income_progressive = max(0, labor_income_after_expenses - standard_deduction - dependent_deduction - calculated_insurance)
    
    # Calculate progressive income tax
    progressive_income_tax = calculate_income_tax(taxable_income_progressive)
    
    # Charitable donation (max 10% of taxable income, can reduce tax)
    max_charitable = taxable_income_progressive * 0.10
    actual_charitable = min(charitable_donation, max_charitable)
    
    # Total tax liability
    total_tax = progressive_income_tax + dividend_income_tax + transfer_income_tax + capital_gain_tax + rental_income_tax
    
    # Tax to pay (after considering paid tax)
    tax_to_pay = max(0, total_tax - personal_income_tax_paid)
    tax_refund = max(0, personal_income_tax_paid - total_tax)
    
    # Display calculation steps
    st.markdown("### 📊 Bước 1: Thu Nhập Từ Lao Động")
    
    col1, col2 = st.columns(2)
    
    with col1:
        income_detail = {
            "Lương cơ bản": salary,
            "Phụ cấp": allowance,
            "Thưởng": bonus,
            "Thu nhập công việc thêm": part_time_income,
            "Thu nhập kinh doanh": business_income,
            "**Tổng thu nhập từ lao động**": total_labor_income
        }
        
        for item, value in income_detail.items():
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.write(item)
            with col_b:
                if "**" in item:
                    st.write(f"**{value:,.0f} đ**")
                else:
                    st.write(f"{value:,.0f} đ" if value > 0 else "-")
    
    with col2:
        st.markdown("### Chi Phí & Giảm Trừ")
        
        deduction_detail = {
            "Chi phí kinh doanh": business_expenses,
            "Bảo hiểm (BHXH, BHYT, BHTN)": calculated_insurance,
            "Giảm trừ gia cảnh": dependent_deduction,
            "Giảm trừ cá nhân": standard_deduction,
            "**Tổng khoản giảm trừ**": business_expenses + calculated_insurance + dependent_deduction + standard_deduction
        }
        
        for item, value in deduction_detail.items():
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.write(item)
            with col_b:
                if "**" in item:
                    st.write(f"**{value:,.0f} đ**")
                else:
                    st.write(f"{value:,.0f} đ" if value > 0 else "-")
    
    st.divider()
    
    st.markdown("### 📊 Bước 2: Tính Thuế Thu Nhập Từ Lao Động")
    
    # Show tax calculation details
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Thu Nhập Chịu Thuế Lũy Tiến:**")
        st.write(f"```")
        st.write(f"Tổng thu nhập lao động:     {total_labor_income:>18,.0f} đ")
        st.write(f"Trừ chi phí kinh doanh:     {business_expenses:>18,.0f} đ")
        st.write(f"Trừ bảo hiểm:               {calculated_insurance:>18,.0f} đ")
        st.write(f"Trừ giảm trừ gia cảnh:      {dependent_deduction:>18,.0f} đ")
        st.write(f"Trừ giảm trừ cá nhân:       {standard_deduction:>18,.0f} đ")
        st.write(f"─────────────────────────────────────────")
        st.write(f"Thu nhập chịu thuế:         {taxable_income_progressive:>18,.0f} đ")
        st.write(f"```")
    
    with col2:
        st.markdown("**Tính Thuế Lũy Tiến:**")
        
        # Show bracket calculation
        temp_income = taxable_income_progressive
        running_tax = 0
        bracket_text = "```\n"
        
        for limit, rate in tax_brackets_2024:
            if temp_income <= 0:
                break
            
            prev_limit = sum([b[0] - (tax_brackets_2024[i-1][0] if i > 0 else 0) for i, b in enumerate(tax_brackets_2024[:tax_brackets_2024.index((limit, rate))])])
            
            if temp_income <= limit - prev_limit:
                income_in_bracket = temp_income
            else:
                income_in_bracket = limit - prev_limit if prev_limit > 0 else limit
            
            tax_in_bracket = income_in_bracket * rate
            bracket_text += f"{income_in_bracket:>15,.0f} × {rate*100:>3.0f}% = {tax_in_bracket:>15,.0f} đ\n"
            
            temp_income -= income_in_bracket
            running_tax += tax_in_bracket
            
            if temp_income <= 0:
                break
        
        bracket_text += f"─────────────────────────────────────────\n"
        bracket_text += f"Thuế TNCN lũy tiến:  {progressive_income_tax:>18,.0f} đ\n"
        bracket_text += "```"
        
        st.write(bracket_text)
    
    st.divider()
    
    st.markdown("### 📊 Bước 3: Thu Nhập Và Thuế Khác")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Thu Nhập Từ Vốn (Thuế Suất Cố Định):**")
        
        capital_detail = {
            f"Cổ tức, lợi tức (@{DIVIDEND_TAX_RATE*100:.0f}%)": (dividend_income, dividend_income_tax),
            f"Tiền lãi (@{INTEREST_TAX_RATE*100:.0f}%)": (transfer_income, transfer_income_tax),
            f"Lãi chuyển nhượng tài sản (@{CAPITAL_GAIN_TAX_RATE*100:.0f}%)": (capital_gain, capital_gain_tax),
            f"Cho thuê bất động sản (@{RENTAL_INCOME_TAX_RATE*100:.0f}%)": (rental_income, rental_income_tax),
        }
        
        total_capital_income = 0
        total_capital_tax = 0
        
        for item, (income, tax) in capital_detail.items():
            if income > 0:
                st.write(f"{item}")
                st.write(f"  Thu nhập: {income:>25,.0f} đ")
                st.write(f"  Thuế:     {tax:>25,.0f} đ")
                total_capital_income += income
                total_capital_tax += tax
                st.write("---")
        
        if total_capital_income > 0:
            st.write(f"**Tổng cộng:**")
            st.write(f"  Thu nhập: {total_capital_income:>25,.0f} đ")
            st.write(f"  Thuế:     {total_capital_tax:>25,.0f} đ")
    
    with col2:
        st.markdown("**Tổng Hợp Thuế TNCN:**")
        
        tax_summary = f"""