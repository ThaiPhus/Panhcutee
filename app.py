import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

# Set page configuration
st.set_page_config(
    page_title="Personal Income Tax Calculator",
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
st.title("💰 Personal Income Tax Calculator")
st.markdown("Calculate your income tax liability with 2024 US federal tax brackets")

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["📝 Income Input", "🧮 Calculations", "📊 Analysis", "💾 Results"])

# ========== TAB 1: INCOME INPUT ==========
with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("👤 Personal Information")
        filing_status = st.selectbox(
            "Filing Status",
            ["Single", "Married Filing Jointly", "Married Filing Separately", "Head of Household"],
            help="Select your filing status for the tax year"
        )
        
        num_dependents = st.number_input("Number of Dependents", min_value=0, max_value=20, value=0)
    
    with col2:
        st.subheader("📅 Tax Year")
        tax_year = st.selectbox("Tax Year", [2024, 2023, 2022])
        
        age = st.number_input("Your Age", min_value=0, max_value=120, value=30, help="For potential additional deductions")
    
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("💼 Employment Income")
        w2_wages = st.number_input("W-2 Wages/Salary", value=50000.0, min_value=0.0, step=1000.0)
        tips = st.number_input("Tips (non-taxable portion)", value=0.0, min_value=0.0, step=100.0)
    
    with col2:
        st.subheader("🏢 Self-Employment")
        se_income = st.number_input("Net Self-Employment Income", value=0.0, min_value=0.0, step=1000.0)
        se_expenses = st.number_input("SE Tax Adjustment (Auto-calculated)", value=0.0, disabled=True)
    
    with col3:
        st.subheader("📈 Investment Income")
        capital_gains = st.number_input("Long-term Capital Gains", value=0.0, min_value=0.0, step=1000.0)
        qualified_dividends = st.number_input("Qualified Dividends", value=0.0, min_value=0.0, step=100.0)
    
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("📊 Other Income")
        interest_income = st.number_input("Interest Income", value=0.0, min_value=0.0, step=100.0)
        ordinary_dividends = st.number_input("Ordinary Dividends", value=0.0, min_value=0.0, step=100.0)
        other_income = st.number_input("Other Income", value=0.0, min_value=0.0, step=100.0)
    
    with col2:
        st.subheader("🎓 Adjustments to Income")
        student_loan_interest = st.number_input("Student Loan Interest Paid", value=0.0, min_value=0.0, max_value=2500.0, step=100.0)
        ira_contributions = st.number_input("Traditional IRA Contributions", value=0.0, min_value=0.0, step=100.0)
        educator_expenses = st.number_input("Educator Expenses", value=0.0, min_value=0.0, max_value=300.0, step=50.0)
    
    with col3:
        st.subheader("💰 Deductions")
        use_standard = st.radio("Deduction Type", ["Standard Deduction", "Itemized Deductions"])
        
        standard_deductions = {
            "Single": 14600,
            "Married Filing Jointly": 29200,
            "Married Filing Separately": 14600,
            "Head of Household": 21900
        }
        
        if use_standard == "Standard Deduction":
            deduction = standard_deductions[filing_status]
            st.info(f"Standard Deduction: **${deduction:,.0f}**")
        else:
            deduction = st.number_input("Itemized Deductions Amount", value=0.0, min_value=0.0, step=100.0)
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💳 Tax Credits")
        child_tax_credit = st.number_input("Child Tax Credit (per child)", value=0.0, min_value=0.0, step=100.0)
        child_tax_credit_total = child_tax_credit * num_dependents
        
        dependent_care_credit = st.number_input("Dependent Care Credit", value=0.0, min_value=0.0, step=100.0)
        education_credit = st.number_input("Education Credits (AOTC/LLC)", value=0.0, min_value=0.0, step=100.0)
    
    with col2:
        st.subheader("📋 Additional Credits")
        earned_income_credit = st.number_input("Earned Income Credit", value=0.0, min_value=0.0, step=100.0)
        retirement_savings_credit = st.number_input("Retirement Savings Credit", value=0.0, min_value=0.0, step=100.0)
        other_credits = st.number_input("Other Credits", value=0.0, min_value=0.0, step=100.0)

# ========== TAB 2: CALCULATIONS ==========
with tab2:
    st.subheader("🧮 Tax Calculation Process")
    
    # Tax brackets for 2024
    tax_brackets = {
        "Single": [
            (11600, 0.10), (47150, 0.12), (100525, 0.22), (191950, 0.24),
            (243725, 0.32), (609350, 0.35), (float('inf'), 0.37)
        ],
        "Married Filing Jointly": [
            (23200, 0.10), (94300, 0.12), (201050, 0.22), (383900, 0.24),
            (487450, 0.32), (731200, 0.35), (float('inf'), 0.37)
        ],
        "Married Filing Separately": [
            (11600, 0.10), (47150, 0.12), (100525, 0.22), (191950, 0.24),
            (243725, 0.32), (365600, 0.35), (float('inf'), 0.37)
        ],
        "Head of Household": [
            (16550, 0.10), (63100, 0.12), (100500, 0.22), (191950, 0.24),
            (243700, 0.32), (609350, 0.35), (float('inf'), 0.37)
        ]
    }
    
    # Capital gains brackets for 2024
    capital_gains_brackets = {
        "Single": [(47025, 0.0), (518900, 0.15), (float('inf'), 0.20)],
        "Married Filing Jointly": [(94050, 0.0), (583750, 0.15), (float('inf'), 0.20)],
        "Married Filing Separately": [(47025, 0.0), (291875, 0.15), (float('inf'), 0.20)],
        "Head of Household": [(62800, 0.0), (551350, 0.15), (float('inf'), 0.20)]
    }
    
    def calculate_federal_tax(taxable_income, filing_status):
        """Calculate federal income tax"""
        brackets = tax_brackets[filing_status]
        tax = 0
        previous_limit = 0
        
        for limit, rate in brackets:
            if taxable_income <= previous_limit:
                break
            taxable_in_bracket = min(taxable_income, limit) - previous_limit
            tax += taxable_in_bracket * rate
            previous_limit = limit
        
        return tax
    
    def calculate_capital_gains_tax(gains, filing_status, ordinary_taxable_income):
        """Calculate tax on capital gains"""
        brackets = capital_gains_brackets[filing_status]
        tax = 0
        
        for limit, rate in brackets:
            if gains <= 0:
                break
            
            room_in_bracket = max(0, limit - max(0, ordinary_taxable_income))
            gains_in_bracket = min(gains, room_in_bracket)
            
            if gains_in_bracket > 0:
                tax += gains_in_bracket * rate
                gains -= gains_in_bracket
                ordinary_taxable_income += gains_in_bracket
        
        return tax
    
    def calculate_se_tax(se_income):
        """Calculate self-employment tax"""
        return se_income * 0.9235 * 0.153
    
    # Perform calculations
    se_tax_amount = calculate_se_tax(se_income)
    se_tax_deduction = se_tax_amount / 2
    
    # Total income
    total_ordinary_income = w2_wages + tips + se_income + interest_income + ordinary_dividends + other_income
    total_investment_income = capital_gains + qualified_dividends
    total_income = total_ordinary_income + total_investment_income
    
    # AGI
    agi = total_income - se_tax_deduction - student_loan_interest - ira_contributions - educator_expenses
    
    # Taxable income
    taxable_income = max(0, agi - deduction)
    taxable_ordinary = max(0, total_ordinary_income - deduction)
    taxable_gains = total_investment_income
    
    # Federal income tax
    federal_income_tax = calculate_federal_tax(taxable_ordinary, filing_status)
    federal_gains_tax = calculate_capital_gains_tax(taxable_gains, filing_status, taxable_ordinary)
    total_federal_tax = federal_income_tax + federal_gains_tax
    
    # Total credits
    total_credits = (child_tax_credit_total + dependent_care_credit + education_credit + 
                     earned_income_credit + retirement_savings_credit + other_credits)
    
    # Net tax liability
    net_tax = max(0, total_federal_tax + se_tax_amount - total_credits)
    
    # Display step-by-step
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Income Calculation")
        income_calc = {
            "Item": [
                "W-2 Wages",
                "Tips",
                "SE Income",
                "Interest",
                "Ordinary Dividends",
                "Capital Gains",
                "Qualified Dividends",
                "Other Income",
                "**Total Income**"
            ],
            "Amount": [
                w2_wages,
                tips,
                se_income,
                interest_income,
                ordinary_dividends,
                capital_gains,
                qualified_dividends,
                other_income,
                total_income
            ]
        }
        income_df = pd.DataFrame(income_calc)
        st.dataframe(income_df, use_container_width=True, hide_index=True)
    
    with col2:
        st.markdown("### Deductions & AGI")
        deductions_calc = {
            "Item": [
                "Total Income",
                "SE Tax Deduction (50%)",
                "Student Loan Interest",
                "IRA Contributions",
                "Educator Expenses",
                "**AGI**",
                "Less: Deductions",
                "**Taxable Income**"
            ],
            "Amount": [
                total_income,
                -se_tax_deduction,
                -student_loan_interest,
                -ira_contributions,
                -educator_expenses,
                agi,
                -deduction,
                taxable_income
            ]
        }
        deductions_df = pd.DataFrame(deductions_calc)
        st.dataframe(deductions_df, use_container_width=True, hide_index=True)
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Tax Liability")
        tax_calc = {
            "Item": [
                "Ordinary Income Tax",
                "Capital Gains Tax",
                "Self-Employment Tax",
                "**Total Tax Before Credits**",
                "Tax Credits",
                "**Net Tax Liability**"
            ],
            "Amount": [
                federal_income_tax,
                federal_gains_tax,
                se_tax_amount,
                total_federal_tax + se_tax_amount,
                -total_credits,
                net_tax
            ]
        }
        tax_df = pd.DataFrame(tax_calc)
        st.dataframe(tax_df, use_container_width=True, hide_index=True)
    
    with col2:
        st.markdown("### Summary Metrics")
        
        if total_income > 0:
            effective_rate = (net_tax / total_income) * 100
            marginal_rate = None
            
            for limit, rate in tax_brackets[filing_status]:
                if taxable_ordinary < limit:
                    marginal_rate = rate * 100
                    break
        else:
            effective_rate = 0
            marginal_rate = 0
        
        metrics_data = {
            "Metric": [
                "Total Income",
                "AGI",
                "Taxable Income",
                "Net Tax Liability",
                "Effective Tax Rate",
                "Marginal Tax Rate",
                "Take-Home Pay"
            ],
            "Value": [
                f"${total_income:,.2f}",
                f"${agi:,.2f}",
                f"${taxable_income:,.2f}",
                f"${net_tax:,.2f}",
                f"{effective_rate:.2f}%",
                f"{marginal_rate:.0f}%" if marginal_rate else "0%",
                f"${total_income - net_tax:,.2f}"
            ]
        }
        metrics_df = pd.DataFrame(metrics_data)
        st.dataframe(metrics_df, use_container_width=True, hide_index=True)

# ========== TAB 3: ANALYSIS ==========
with tab3:
    st.subheader("📊 Visual Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Income vs Tax")
        if total_income > 0:
            fig, ax = plt.subplots(figsize=(8, 6))
            labels = [f'Tax\n${net_tax:,.0f}', f'Take-Home\n${total_income - net_tax:,.0f}']
            sizes = [net_tax, total_income - net_tax]
            colors = ['#ff6b6b', '#51cf66']
            wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%', 
                                                colors=colors, startangle=90, textprops={'fontsize': 10})
            ax.set_title("Income Distribution", fontsize=12, fontweight='bold')
            st.pyplot(fig)
    
    with col2:
        st.markdown("### Tax Composition")
        if (federal_income_tax + federal_gains_tax + se_tax_amount) > 0:
            fig, ax = plt.subplots(figsize=(8, 6))
            tax_types = [federal_income_tax, federal_gains_tax, se_tax_amount]
            labels = [
                f'Income Tax\n${federal_income_tax:,.0f}',
                f'Capital Gains\n${federal_gains_tax:,.0f}',
                f'SE Tax\n${se_tax_amount:,.0f}'
            ]
            colors = ['#4ecdc4', '#95e1d3', '#f38181']
            wedges, texts, autotexts = ax.pie(tax_types, labels=labels, autopct='%1.1f%%',
                                                colors=colors, startangle=90, textprops={'fontsize': 10})
            ax.set_title("Tax Breakdown", fontsize=12, fontweight='bold')
            st.pyplot(fig)
    
    st.divider()
    
    # Tax brackets visualization
    st.markdown("### 📈 Your Position in Tax Brackets")
    
    brackets = tax_brackets[filing_status]
    bracket_list = []
    previous = 0
    
    for limit, rate in brackets[:-1]:
        bracket_list.append({
            "Tax Rate": f"{rate*100:.0f}%",
            "Income Range": f"${previous:,.0f} - ${limit:,.0f}",
            "Your Status": "← Currently here" if previous <= taxable_ordinary < limit else ""
        })
        previous = limit
    
    bracket_df = pd.DataFrame(bracket_list)
    st.dataframe(bracket_df, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # Income sources breakdown
    st.markdown("### 💰 Income Sources Breakdown")
    
    income_sources = {
        "Wages & Salary": w2_wages,
        "Self-Employment": se_income,
        "Capital Gains": capital_gains,
        "Dividends": qualified_dividends + ordinary_dividends,
        "Interest": interest_income,
        "Other": other_income
    }
    
    income_sources = {k: v for k, v in income_sources.items() if v > 0}
    
    if income_sources:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.barh(list(income_sources.keys()), list(income_sources.values()), color='#4ecdc4')
        ax.set_xlabel('Amount ($)', fontsize=10)
        ax.set_title('Income Sources', fontsize=12, fontweight='bold')
        for i, v in enumerate(income_sources.values()):
            ax.text(v, i, f' ${v:,.0f}', va='center')
        st.pyplot(fig)

# ========== TAB 4: RESULTS ==========
with tab4:
    st.subheader("💾 Final Results & Export")
    
    # Summary cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Gross Income", f"${total_income:,.0f}")
    
    with col2:
        st.metric("Taxable Income", f"${taxable_income:,.0f}")
    
    with col3:
        st.metric("Total Tax", f"${net_tax:,.0f}")
    
    with col4:
        if total_income > 0:
            rate = (net_tax / total_income) * 100
        else:
            rate = 0
        st.metric("Effective Rate", f"{rate:.2f}%")
    
    st.divider()
    
    # Detailed summary
    st.markdown("### 📋 Detailed Tax Summary")
    
    summary_sections = {
        "Income Summary": {
            "W-2 Wages": w2_wages,
            "Self-Employment Income": se_income,
            "Capital Gains": capital_gains,
            "Dividends": qualified_dividends + ordinary_dividends,
            "Interest Income": interest_income,
            "Other Income": other_income,
            "Total Gross Income": total_income,
        },
        "Deductions & AGI": {
            "SE Tax Deduction": se_tax_deduction,
            "Student Loan Interest": student_loan_interest,
            "IRA Contributions": ira_contributions,
            "Educator Expenses": educator_expenses,
            "Adjusted Gross Income (AGI)": agi,
            "Deductions": deduction,
            "Taxable Income": taxable_income,
        },
        "Tax Calculation": {
            "Ordinary Income Tax": federal_income_tax,
            "Capital Gains Tax": federal_gains_tax,
            "Self-Employment Tax": se_tax_amount,
            "Total Tax Before Credits": federal_income_tax + federal_gains_tax + se_tax_amount,
            "Tax Credits": total_credits,
            "NET TAX LIABILITY": net_tax,
        }
    }
    
    for section_name, section_data in summary_sections.items():
        with st.expander(section_name, expanded=True):
            for item, value in section_data.items():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(item)
                with col2:
                    if item in ["Total Gross Income", "Adjusted Gross Income (AGI)", "Taxable Income", "NET TAX LIABILITY"]:
                        st.write(f"**${value:,.2f}**")
                    else:
                        st.write(f"${value:,.2f}")
    
    st.divider()
    
    # Export options
    st.markdown("### 📥 Export Results")
    
    # Create export text
    export_text = f"""
PERSONAL INCOME TAX CALCULATION REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

═══════════════════════════════════════════════════════════

TAXPAYER INFORMATION
Filing Status: {filing_status}
Tax Year: {tax_year}
Number of Dependents: {num_dependents}

═══════════════════════════════════════════════════════════

INCOME SUMMARY
W-2 Wages/Salary: ${w2_wages:,.2f}
Tips: ${tips:,.2f}
Self-Employment Income: ${se_income:,.2f}
Capital Gains (Long-term): ${capital_gains:,.2f}
Qualified Dividends: ${qualified_dividends:,.2f}
Ordinary Dividends: ${ordinary_dividends:,.2f}
Interest Income: ${interest_income:,.2f}
Other Income: ${other_income:,.2f}
─────────────────────────────────────────────────────────
TOTAL GROSS INCOME: ${total_income:,.2f}

═══════════════════════════════════════════════════════════

DEDUCTIONS & AGI CALCULATION
Total Gross Income: ${total_income:,.2f}
Self-Employment Tax Deduction (50%): -${se_tax_deduction:,.2f}
Student Loan Interest Deduction: -${student_loan_interest:,.2f}
IRA Contributions: -${ira_contributions:,.2f}
Educator Expenses: -${educator_expenses:,.2f}
─────────────────────────────────────────────────────────
ADJUSTED GROSS INCOME (AGI): ${agi:,.2f}

Standard/Itemized Deduction: -${deduction:,.2f}
────────��────────────────────────────────────────────────
TAXABLE INCOME: ${taxable_income:,.2f}

═══════════════════════════════════════════════════════════

TAX LIABILITY CALCULATION
Ordinary Income Tax: ${federal_income_tax:,.2f}
Capital Gains Tax: ${federal_gains_tax:,.2f}
Self-Employment Tax: ${se_tax_amount:,.2f}
─────────────────────────────────────────────────────────
Total Tax Before Credits: ${federal_income_tax + federal_gains_tax + se_tax_amount:,.2f}

Tax Credits Applied:
  - Child Tax Credit: ${child_tax_credit_total:,.2f}
  - Dependent Care Credit: ${dependent_care_credit:,.2f}
  - Education Credits: ${education_credit:,.2f}
  - Earned Income Credit: ${earned_income_credit:,.2f}
  - Retirement Savings Credit: ${retirement_savings_credit:,.2f}
  - Other Credits: ${other_credits:,.2f}
─────────────────────────────────────────────────────────
Total Credits: -${total_credits:,.2f}

═══════════════════════════════════════════════════════════

FINAL RESULTS
Total Gross Income: ${total_income:,.2f}
Total Tax Liability: ${net_tax:,.2f}
Take-Home Pay: ${total_income - net_tax:,.2f}

Effective Tax Rate: {(net_tax / total_income * 100) if total_income > 0 else 0:.2f}%

═══════════════════════════════════════════════════════════

DISCLAIMER:
This calculation is for educational purposes only. It is based on 
2024 federal tax information and does not account for:
- State and local taxes
- Complex tax situations
- All possible credits and deductions
- Alternative Minimum Tax (AMT)

Please consult a qualified tax professional for accurate tax advice.

═══════════════════════════════════════════════════════════
"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.download_button(
            label="📄 Download as Text File",
            data=export_text,
            file_name=f"tax_calculation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )
    
    with col2:
        # Create CSV export
        csv_data = f"Item,Amount\n"
        for section_name, section_data in summary_sections.items():
            csv_data += f"\n{section_name},\n"
            for item, value in section_data.items():
                csv_data += f"{item},${value:,.2f}\n"
        
        st.download_button(
            label="📊 Download as CSV",
            data=csv_data,
            file_name=f"tax_calculation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

# Footer
st.divider()
st.markdown("""
<div class="warning-box">
<strong>⚠️ Important Disclaimer:</strong>
This calculator is for educational and estimation purposes only. It provides general information based on 2024 federal tax brackets and does not constitute tax advice. Tax situations vary widely and may include:
- State and local taxes
- Alternative Minimum Tax (AMT)
- Net Investment Income Tax (NIIT)
- Earned Income Tax Credit (EITC) phase-outs
- Various phase-outs for credits and deductions
- Complex business structures

<strong>Always consult with a qualified tax professional (CPA or tax attorney) for accurate tax preparation and advice.</strong>
</div>
""", unsafe_allow_html=True)
