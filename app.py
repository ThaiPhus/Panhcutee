import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import warnings
warnings.filterwarnings('ignore')

# Set page configuration
st.set_page_config(
    page_title="Stock Price Prediction AI",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .bullish {
        color: #27ae60;
        font-weight: bold;
    }
    .bearish {
        color: #e74c3c;
        font-weight: bold;
    }
    .info-box {
        background-color: #d1ecf1;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #17a2b8;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #ffc107;
    }
    </style>
    """, unsafe_allow_html=True)

# Title
st.title("📈 Stock Price Prediction AI Model")
st.markdown("Mô hình dự đoán giá cổ phiếu sử dụng Machine Learning & Technical Analysis")

# Sidebar
st.sidebar.header("⚙️ Cấu Hình")

# Stock selection
stock_symbol = st.sidebar.text_input("Mã cổ phiếu (VN30, FPT, TCB, etc.)", value="FPT.VN", help="Nhập mã cổ phiếu")

# Time period
lookback_days = st.sidebar.slider("Số ngày dữ liệu lịch sử (Lookback)", min_value=30, max_value=365, value=180, step=30)

# Prediction days
prediction_days = st.sidebar.slider("Dự đoán cho bao nhiêu ngày tới", min_value=1, max_value=30, value=10, step=1)

# Model selection
model_type = st.sidebar.selectbox("Chọn mô hình AI", 
                                   ["Random Forest", "Linear Regression", "Combined (Ensemble)"])

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Dữ Liệu & Phân Tích", "🤖 Mô Hình ML", "🔮 Dự Đoán", "📈 Chỉ Báo Kỹ Thuật", "❓ Hướng Dẫn"])

# ========== LOAD DATA ==========
@st.cache_data
def load_stock_data(symbol, days):
    """Load stock data from yfinance"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        data = yf.download(symbol, start=start_date, end=end_date, progress=False)
        
        if len(data) == 0:
            return None
        
        return data
    except Exception as e:
        st.error(f"Lỗi khi tải dữ liệu: {e}")
        return None

def calculate_technical_indicators(df):
    """Calculate technical indicators with proper NaN handling"""
    df = df.copy()
    
    try:
        # Simple Moving Averages
        df['SMA_5'] = df['Close'].rolling(window=5, min_periods=1).mean()
        df['SMA_20'] = df['Close'].rolling(window=20, min_periods=1).mean()
        df['SMA_50'] = df['Close'].rolling(window=50, min_periods=1).mean()
        
        # Exponential Moving Averages
        df['EMA_12'] = df['Close'].ewm(span=12, adjust=False).mean()
        df['EMA_26'] = df['Close'].ewm(span=26, adjust=False).mean()
        
        # MACD
        df['MACD'] = df['EMA_12'] - df['EMA_26']
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Hist'] = df['MACD'] - df['Signal']
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
        
        # Avoid division by zero
        rs = np.where(loss != 0, gain / loss, 0)
        df['RSI'] = 100 - (100 / (1 + rs))
        df['RSI'] = df['RSI'].fillna(50)  # Fill NaN with neutral value
        
        # Bollinger Bands
        df['BB_Middle'] = df['Close'].rolling(window=20, min_periods=1).mean()
        bb_std = df['Close'].rolling(window=20, min_periods=1).std()
        bb_std = bb_std.fillna(0)  # Fill NaN std with 0
        
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
        
        # Average True Range (ATR)
        df['High-Low'] = df['High'] - df['Low']
        df['High-Close'] = abs(df['High'] - df['Close'].shift())
        df['Low-Close'] = abs(df['Low'] - df['Close'].shift())
        df['TR'] = df[['High-Low', 'High-Close', 'Low-Close']].max(axis=1)
        df['ATR'] = df['TR'].rolling(window=14, min_periods=1).mean()
        
        # Volume indicators
        df['Volume_MA'] = df['Volume'].rolling(window=20, min_periods=1).mean()
        df['Volume_MA'] = df['Volume_MA'].fillna(df['Volume'].mean())
        df['Volume_Signal'] = df['Volume'] / df['Volume_MA']
        df['Volume_Signal'] = df['Volume_Signal'].fillna(1)
        
        # Daily returns
        df['Daily_Return'] = df['Close'].pct_change().fillna(0)
        df['Price_Change'] = df['Close'].diff().fillna(0)
        
        # Volatility
        df['Volatility'] = df['Daily_Return'].rolling(window=20, min_periods=1).std().fillna(0)
        
        return df
    
    except Exception as e:
        st.error(f"Lỗi khi tính toán chỉ báo kỹ thuật: {e}")
        return df

def prepare_ml_data(df, lookback=20):
    """Prepare data for machine learning"""
    df = df.copy()
    
    # Drop any remaining NaN rows
    df = df.dropna()
    
    if len(df) < lookback + 1:
        return None, None, None
    
    # Create features from past prices
    X = []
    y = []
    
    for i in range(len(df) - lookback - 1):
        # Features: past 20 days of close prices
        X.append(df['Close'].iloc[i:i+lookback].values)
        # Target: next day's close price
        y.append(df['Close'].iloc[i+lookback])
    
    if len(X) == 0 or len(y) == 0:
        return None, None, None
    
    X = np.array(X)
    y = np.array(y)
    
    # Normalize features
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X.reshape(-1, lookback)).reshape(X.shape)
    
    return X_scaled, y, scaler

def train_ml_models(X, y, model_type):
    """Train machine learning models"""
    if X is None or y is None or len(X) < 10:
        return None, None
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    if model_type == "Random Forest":
        model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
        model.fit(X_train, y_train)
    elif model_type == "Linear Regression":
        model = LinearRegression()
        model.fit(X_train, y_train)
    else:  # Combined
        model1 = RandomForestRegressor(n_estimators=50, random_state=42, n_jobs=-1)
        model2 = LinearRegression()
        model1.fit(X_train, y_train)
        model2.fit(X_train, y_train)
        model = (model1, model2)
    
    # Predictions
    if model_type == "Combined (Ensemble)":
        y_pred_train = (model[0].predict(X_train) + model[1].predict(X_train)) / 2
        y_pred_test = (model[0].predict(X_test) + model[1].predict(X_test)) / 2
    else:
        y_pred_train = model.predict(X_train)
        y_pred_test = model.predict(X_test)
    
    # Metrics
    train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
    test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
    test_r2 = r2_score(y_test, y_pred_test)
    test_mae = mean_absolute_error(y_test, y_pred_test)
    
    return model, {
        'train_rmse': train_rmse,
        'test_rmse': test_rmse,
        'test_r2': test_r2,
        'test_mae': test_mae,
        'X_test': X_test,
        'y_test': y_test,
        'y_pred_test': y_pred_test
    }

def predict_future_prices(model, last_sequence, scaler, num_days, model_type):
    """Predict future prices"""
    predictions = []
    current_sequence = last_sequence.copy()
    
    for _ in range(num_days):
        if model_type == "Combined (Ensemble)":
            pred = (model[0].predict(current_sequence.reshape(1, -1))[0] + 
                   model[1].predict(current_sequence.reshape(1, -1))[0]) / 2
        else:
            pred = model.predict(current_sequence.reshape(1, -1))[0]
        
        predictions.append(pred)
        
        # Update sequence for next prediction
        current_sequence = np.append(current_sequence[1:], pred)
    
    return np.array(predictions)

def calculate_signal_strength(df):
    """Calculate buy/sell signal strength"""
    signals = []
    
    try:
        # RSI Signal
        rsi_val = df['RSI'].iloc[-1]
        if not np.isnan(rsi_val):
            if rsi_val < 30:
                signals.append(("RSI", 1, "Quá bán (Oversold)"))
            elif rsi_val > 70:
                signals.append(("RSI", -1, "Quá mua (Overbought)"))
            else:
                signals.append(("RSI", 0, "Trung lập"))
        else:
            signals.append(("RSI", 0, "Không có dữ liệu"))
        
        # MACD Signal
        if not np.isnan(df['MACD'].iloc[-1]) and not np.isnan(df['Signal'].iloc[-1]):
            if df['MACD'].iloc[-1] > df['Signal'].iloc[-1]:
                signals.append(("MACD", 1, "Tích cực (Bullish)"))
            else:
                signals.append(("MACD", -1, "Tiêu cực (Bearish)"))
        else:
            signals.append(("MACD", 0, "Không có dữ liệu"))
        
        # Moving Average Signal
        close = df['Close'].iloc[-1]
        sma20 = df['SMA_20'].iloc[-1]
        sma50 = df['SMA_50'].iloc[-1]
        
        if not np.isnan(close) and not np.isnan(sma20) and not np.isnan(sma50):
            if close > sma20 > sma50:
                signals.append(("MA", 1, "Uptrend"))
            elif close < sma20 < sma50:
                signals.append(("MA", -1, "Downtrend"))
            else:
                signals.append(("MA", 0, "Trung lập"))
        else:
            signals.append(("MA", 0, "Không có dữ liệu"))
        
        # Price vs Bollinger Bands
        if not np.isnan(df['BB_Upper'].iloc[-1]) and not np.isnan(df['BB_Lower'].iloc[-1]):
            if close > df['BB_Upper'].iloc[-1]:
                signals.append(("BB", -1, "Trên dải trên (Overbought)"))
            elif close < df['BB_Lower'].iloc[-1]:
                signals.append(("BB", 1, "Dưới dải dưới (Oversold)"))
            else:
                signals.append(("BB", 0, "Trong dải"))
        else:
            signals.append(("BB", 0, "Không có dữ liệu"))
        
    except Exception as e:
        st.warning(f"Lỗi khi tính toán tín hiệu: {e}")
    
    return signals

# ========== TAB 1: DATA & ANALYSIS ==========
with tab1:
    st.subheader("📊 Dữ Liệu & Phân Tích Cổ Phiếu")
    
    # Load data
    with st.spinner(f"Đang tải dữ liệu cho {stock_symbol}..."):
        stock_data = load_stock_data(stock_symbol, lookback_days)
    
    if stock_data is not None:
        # Calculate indicators
        stock_data = calculate_technical_indicators(stock_data)
        
        if len(stock_data) > 0:
            # Display metrics
            current_price = stock_data['Close'].iloc[-1]
            prev_price = stock_data['Close'].iloc[-2] if len(stock_data) > 1 else current_price
            price_change = current_price - prev_price
            price_change_pct = (price_change / prev_price) * 100 if prev_price != 0 else 0
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("Giá Hiện Tại", f"{current_price:,.2f} đ", f"{price_change:+.2f} ({price_change_pct:+.2f}%)")
            
            with col2:
                st.metric("Cao Nhất (52 tuần)", f"{stock_data['High'].tail(252).max():,.2f} đ")
            
            with col3:
                st.metric("Thấp Nhất (52 tuần)", f"{stock_data['Low'].tail(252).min():,.2f} đ")
            
            with col4:
                st.metric("Khối Lượng TB (20 ngày)", f"{stock_data['Volume'].tail(20).mean():,.0f}")
            
            with col5:
                volatility = stock_data['Volatility'].iloc[-1]
                st.metric("Volatility (20 ngày)", f"{volatility*100:.2f}%")
            
            st.divider()
            
            # Price chart
            st.markdown("### 📈 Biểu Đồ Giá Cổ Phiếu")
            
            fig, ax = plt.subplots(figsize=(14, 6))
            
            ax.plot(stock_data.index, stock_data['Close'], label='Close Price', linewidth=2, color='#2E86AB')
            ax.plot(stock_data.index, stock_data['SMA_20'], label='SMA 20', alpha=0.7, linestyle='--')
            ax.plot(stock_data.index, stock_data['SMA_50'], label='SMA 50', alpha=0.7, linestyle='--')
            
            # Bollinger Bands
            ax.fill_between(stock_data.index, stock_data['BB_Upper'], stock_data['BB_Lower'], alpha=0.1, color='gray')
            
            ax.set_xlabel('Ngày', fontsize=11)
            ax.set_ylabel('Giá (VNĐ)', fontsize=11)
            ax.set_title(f'Biểu Đồ Giá {stock_symbol}', fontsize=13, fontweight='bold')
            ax.legend(loc='best')
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            st.pyplot(fig)
            
            # Data table
            st.markdown("### 📋 Dữ Liệu Gần Đây (10 Ngày)")
            
            display_columns = ['Close', 'Volume', 'SMA_20', 'SMA_50', 'RSI', 'MACD']
            display_data = stock_data[display_columns].tail(10).copy()
            display_data = display_data.round(2)
            
            st.dataframe(display_data, use_container_width=True)
        else:
            st.error("Không có dữ liệu sau khi tính toán chỉ báo kỹ thuật")
    else:
        st.error(f"Không thể tải dữ liệu cho {stock_symbol}. Vui lòng kiểm tra mã cổ phiếu.")

# ========== TAB 2: ML MODEL ==========
with tab2:
    st.subheader("🤖 Mô Hình Machine Learning")
    
    if stock_data is not None and len(stock_data) > 0:
        st.markdown("### Thông Tin Mô Hình")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"📊 Loại Mô Hình: **{model_type}**")
        with col2:
            st.info(f"📈 Dữ Liệu Huấn Luyện: **{lookback_days} ngày**")
        with col3:
            st.info(f"🔮 Dự Đoán: **{prediction_days} ngày tới**")
        
        st.divider()
        
        # Train model
        with st.spinner("Đang huấn luyện mô hình..."):
            X, y, scaler = prepare_ml_data(stock_data, lookback=20)
            
            if X is not None:
                model, metrics = train_ml_models(X, y, model_type)
                
                if model is not None:
                    st.success("✅ Huấn luyện mô hình thành công!")
                    
                    # Display metrics
                    st.markdown("### 📊 Hiệu Suất Mô Hình")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("R² Score (Test)", f"{metrics['test_r2']:.4f}")
                    
                    with col2:
                        st.metric("RMSE (Test)", f"{metrics['test_rmse']:,.2f}")
                    
                    with col3:
                        st.metric("MAE (Test)", f"{metrics['test_mae']:,.2f}")
                    
                    with col4:
                        accuracy = (1 - (metrics['test_mae'] / stock_data['Close'].mean())) * 100
                        st.metric("Độ Chính Xác Ước Tính", f"{max(0, min(100, accuracy)):.2f}%")
                    
                    st.divider()
                    
                    # Actual vs Predicted
                    st.markdown("### 📈 Giá Thực Tế vs Dự Đoán (Test Set)")
                    
                    fig, ax = plt.subplots(figsize=(14, 6))
                    
                    ax.plot(range(len(metrics['y_test'])), metrics['y_test'], label='Giá Thực Tế', marker='o', markersize=3)
                    ax.plot(range(len(metrics['y_pred_test'])), metrics['y_pred_test'], label='Dự Đoán', marker='s', markersize=3, alpha=0.7)
                    
                    ax.set_xlabel('Thời Gian (ngày)', fontsize=11)
                    ax.set_ylabel('Giá (VNĐ)', fontsize=11)
                    ax.set_title('So Sánh Giá Thực Tế và Dự Đoán', fontsize=13, fontweight='bold')
                    ax.legend(loc='best')
                    ax.grid(True, alpha=0.3)
                    
                    plt.tight_layout()
                    st.pyplot(fig)
                    
                    # Residuals
                    st.markdown("### 📊 Phân Tích Sai Số (Residuals)")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        residuals = metrics['y_test'] - metrics['y_pred_test']
                        
                        fig, ax = plt.subplots(figsize=(10, 6))
                        ax.hist(residuals, bins=30, edgecolor='black', alpha=0.7, color='#2E86AB')
                        ax.axvline(residuals.mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {residuals.mean():.2f}')
                        ax.set_xlabel('Sai Số (Residuals)', fontsize=11)
                        ax.set_ylabel('Tần Suất', fontsize=11)
                        ax.set_title('Phân Phối Sai Số', fontsize=12, fontweight='bold')
                        ax.legend()
                        ax.grid(True, alpha=0.3)
                        plt.tight_layout()
                        st.pyplot(fig)
                    
                    with col2:
                        fig, ax = plt.subplots(figsize=(10, 6))
                        ax.scatter(metrics['y_pred_test'], residuals, alpha=0.6, color='#2E86AB')
                        ax.axhline(y=0, color='red', linestyle='--', linewidth=2)
                        ax.set_xlabel('Giá Dự Đoán (VNĐ)', fontsize=11)
                        ax.set_ylabel('Sai Số (VNĐ)', fontsize=11)
                        ax.set_title('Biểu Đồ Sai Số', fontsize=12, fontweight='bold')
                        ax.grid(True, alpha=0.3)
                        plt.tight_layout()
                        st.pyplot(fig)
                else:
                    st.error("Không thể huấn luyện mô hình. Dữ liệu có thể không đủ.")
            else:
                st.error("Không đủ dữ liệu để huấn luyện mô hình. Vui lòng chọn kỳ hạn lâu hơn.")
    else:
        st.error("Không có dữ liệu cổ phiếu. Vui lòng kiểm tra lại mã cổ phiếu.")

# ========== TAB 3: PREDICTIONS ==========
with tab3:
    st.subheader("🔮 Dự Đoán Giá 10 Ngày Tới")
    
    if stock_data is not None and len(stock_data) > 0:
        # Train model again for predictions
        with st.spinner("Đang tính toán dự đoán..."):
            X, y, scaler = prepare_ml_data(stock_data, lookback=20)
            
            if X is not None:
                model, metrics = train_ml_models(X, y, model_type)
                
                if model is not None:
                    # Get last sequence for prediction
                    last_sequence = X[-1]
                    
                    # Predict future prices
                    future_predictions = predict_future_prices(model, last_sequence, scaler, prediction_days, model_type)
                    
                    # Create prediction dataframe
                    today = datetime.now()
                    future_dates = [today + timedelta(days=i) for i in range(1, prediction_days + 1)]
                    
                    predictions_df = pd.DataFrame({
                        'Ngày': future_dates,
                        'Dự Đoán Giá': future_predictions,
                        'Thay Đổi': [future_predictions[i] - (future_predictions[i-1] if i > 0 else stock_data['Close'].iloc[-1]) 
                                    for i in range(len(future_predictions))],
                    })
                    
                    predictions_df['Thay Đổi %'] = (predictions_df['Thay Đổi'] / 
                                                    stock_data['Close'].iloc[-1]) * 100
                    
                    current_price = stock_data['Close'].iloc[-1]
                    final_price = future_predictions[-1]
                    price_change = final_price - current_price
                    price_change_pct = (price_change / current_price) * 100 if current_price != 0 else 0
                    
                    # Display prediction summary
                    st.markdown("### 📈 Tóm Tắt Dự Đoán")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Giá Hiện Tại", f"{current_price:,.2f} đ")
                    
                    with col2:
                        st.metric("Giá Dự Đoán (Ngày 10)", f"{final_price:,.2f} đ")
                    
                    with col3:
                        if price_change >= 0:
                            st.markdown(f"<div class='bullish'>📈 Thay Đổi: +{price_change:,.2f} đ (+{price_change_pct:.2f}%)</div>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<div class='bearish'>📉 Thay Đổi: {price_change:,.2f} đ ({price_change_pct:.2f}%)</div>", unsafe_allow_html=True)
                    
                    with col4:
                        signal = "🟢 TĂNG" if price_change_pct > 0 else "🔴 GIẢM"
                        st.markdown(f"<div style='font-size: 18px; font-weight: bold;'>{signal}</div>", unsafe_allow_html=True)
                    
                    st.divider()
                    
                    # Predictions table
                    st.markdown("### 📋 Chi Tiết Dự Đoán Theo Ngày")
                    
                    display_pred = predictions_df.copy()
                    display_pred['Ngày'] = display_pred['Ngày'].dt.strftime('%d/%m/%Y')
                    display_pred['Dự Đoán Giá'] = display_pred['Dự Đoán Giá'].apply(lambda x: f"{x:,.2f} đ")
                    display_pred['Thay Đổi'] = display_pred['Thay Đổi'].apply(lambda x: f"{x:+,.2f} đ")
                    display_pred['Thay Đổi %'] = display_pred['Thay Đổi %'].apply(lambda x: f"{x:+.2f}%")
                    
                    st.dataframe(display_pred, use_container_width=True, hide_index=True)
                    
                    st.divider()
                    
                    # Chart: Historical + Predictions
                    st.markdown("### 📈 Biểu Đồ: Lịch Sử + Dự Đoán")
                    
                    fig, ax = plt.subplots(figsize=(14, 7))
                    
                    # Historical data (last 30 days)
                    hist_data = stock_data['Close'].tail(30)
                    ax.plot(range(len(hist_data)), hist_data.values, 
                           label='Giá Lịch Sử', linewidth=2.5, color='#2E86AB', marker='o', markersize=4)
                    
                    # Predictions
                    pred_x_range = range(len(hist_data) - 1, len(hist_data) - 1 + len(future_predictions))
                    ax.plot(pred_x_range, future_predictions, 
                           label='Dự Đoán', linewidth=2.5, color='#A23B72', marker='s', markersize=6, linestyle='--')
                    
                    # Confidence interval
                    residuals_std = (metrics['y_test'] - metrics['y_pred_test']).std()
                    upper_bound = future_predictions + (1.96 * residuals_std)
                    lower_bound = future_predictions - (1.96 * residuals_std)
                    
                    ax.fill_between(pred_x_range, upper_bound, lower_bound, alpha=0.2, color='#A23B72', label='Khoảng tin cậy 95%')
                    
                    ax.set_xlabel('Ngày', fontsize=11)
                    ax.set_ylabel('Giá (VNĐ)', fontsize=11)
                    ax.set_title(f'Dự Đoán Giá {stock_symbol} - {prediction_days} Ngày Tới', fontsize=13, fontweight='bold')
                    ax.legend(loc='best', fontsize=10)
                    ax.grid(True, alpha=0.3)
                    
                    plt.tight_layout()
                    st.pyplot(fig)
                    
                    # Recommendation
                    st.divider()
                    st.markdown("### 💡 Khuyến Nghị")
                    
                    if price_change_pct > 3:
                        st.success(f"🟢 **TĂNG MẠNH**: Dự kiến giá sẽ tăng {price_change_pct:.2f}% trong {prediction_days} ngày tới")
                    elif price_change_pct > 1:
                        st.info(f"🟢 **TĂNG**: Dự kiến giá sẽ tăng {price_change_pct:.2f}% trong {prediction_days} ngày tới")
                    elif price_change_pct > -1:
                        st.info(f"🟡 **TRUNG LẬP**: Dự kiến giá sẽ đi ngang, thay đổi {price_change_pct:.2f}% trong {prediction_days} ngày tới")
                    elif price_change_pct > -3:
                        st.warning(f"🔴 **GIẢM**: Dự kiến giá sẽ giảm {abs(price_change_pct):.2f}% trong {prediction_days} ngày tới")
                    else:
                        st.error(f"🔴 **GIẢM MẠNH**: Dự kiến giá sẽ giảm {abs(price_change_pct):.2f}% trong {prediction_days} ngày tới")
                else:
                    st.error("Không thể huấn luyện mô hình")
            else:
                st.error("Không đủ dữ liệu để dự đoán")
    else:
        st.error("Không có dữ liệu cổ phiếu")

# ========== TAB 4: TECHNICAL INDICATORS ==========
with tab4:
    st.subheader("📈 Chỉ Báo Kỹ Thuật & Tín Hiệu Giao Dịch")
    
    if stock_data is not None and len(stock_data) > 0:
        # Calculate signals
        signals = calculate_signal_strength(stock_data)
        
        st.markdown("### 📊 Tín Hiệu Kỹ Thuật")
        
        col1, col2 = st.columns(2)
        
        with col1:
            for signal_name, signal_value, signal_text in signals:
                if signal_value > 0:
                    emoji = "🟢"
                elif signal_value < 0:
                    emoji = "🔴"
                else:
                    emoji = "🟡"
                
                st.markdown(f"{emoji} **{signal_name}**: {signal_text}")
        
        # Overall signal strength
        signal_sum = sum([s[1] for s in signals])
        
        with col2:
            if signal_sum > 0:
                st.success(f"### 🟢 Tín Hiệu MẠNH TĂNG\nĐiểm: {signal_sum}")
            elif signal_sum < 0:
                st.error(f"### 🔴 Tín Hiệu MẠNH GIẢM\nĐiểm: {signal_sum}")
            else:
                st.info(f"### 🟡 Tín Hiệu TRUNG LẬP\nĐiểm: {signal_sum}")
        
        st.divider()
        
        # Technical indicators charts
        col1, col2 = st.columns(2)
        
        # RSI
        with col1:
            st.markdown("### RSI (Relative Strength Index)")
            
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(range(len(stock_data['RSI'].tail(60))), stock_data['RSI'].tail(60), linewidth=2, color='#2E86AB')
            ax.axhline(y=70, color='red', linestyle='--', label='Quá Mua (70)')
            ax.axhline(y=30, color='green', linestyle='--', label='Quá Bán (30)')
            ax.fill_between(range(len(stock_data['RSI'].tail(60))), 70, 100, alpha=0.1, color='red')
            ax.fill_between(range(len(stock_data['RSI'].tail(60))), 0, 30, alpha=0.1, color='green')
            ax.set_ylabel('RSI', fontsize=10)
            ax.set_title('RSI(14)', fontsize=11, fontweight='bold')
            ax.legend(fontsize=9)
            ax.set_ylim([0, 100])
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            st.pyplot(fig)
        
        # MACD
        with col2:
            st.markdown("### MACD (Moving Average Convergence Divergence)")
            
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(range(len(stock_data['MACD'].tail(60))), stock_data['MACD'].tail(60), label='MACD', linewidth=2, color='#2E86AB')
            ax.plot(range(len(stock_data['Signal'].tail(60))), stock_data['Signal'].tail(60), label='Signal', linewidth=2, color='#A23B72')
            ax.bar(range(len(stock_data['MACD_Hist'].tail(60))), stock_data['MACD_Hist'].tail(60), label='Histogram', alpha=0.3, color='gray')
            ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
            ax.set_ylabel('MACD', fontsize=10)
            ax.set_title('MACD', fontsize=11, fontweight='bold')
            ax.legend(fontsize=9)
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            st.pyplot(fig)
        
        # Bollinger Bands
        st.markdown("### Bollinger Bands")
        
        fig, ax = plt.subplots(figsize=(14, 6))
        hist_60 = stock_data.tail(60)
        ax.plot(range(len(hist_60)), hist_60['Close'], label='Close Price', linewidth=2, color='#2E86AB')
        ax.plot(range(len(hist_60)), hist_60['BB_Middle'], label='Middle Band', linestyle='--', alpha=0.5)
        ax.fill_between(range(len(hist_60)), hist_60['BB_Upper'], hist_60['BB_Lower'], 
                        alpha=0.2, color='gray', label='Bollinger Bands')
        ax.set_xlabel('Ngày', fontsize=10)
        ax.set_ylabel('Giá (VNĐ)', fontsize=10)
        ax.set_title('Bollinger Bands (20, 2)', fontsize=11, fontweight='bold')
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        st.pyplot(fig)
        
        # Volume
        st.markdown("### Khối Lượng Giao Dịch (Volume)")
        
        fig, ax = plt.subplots(figsize=(14, 5))
        hist_60 = stock_data.tail(60)
        colors = ['green' if hist_60['Close'].iloc[i] >= hist_60['Close'].iloc[i-1] else 'red' 
                 for i in range(1, len(hist_60))]
        ax.bar(range(len(colors)), hist_60['Volume'].tail(59), color=colors, alpha=0.6)
        ax.plot(range(len(hist_60)), hist_60['Volume_MA'], label='MA(20)', linewidth=2, color='blue')
        ax.set_xlabel('Ngày', fontsize=10)
        ax.set_ylabel('Khối Lượng', fontsize=10)
        ax.set_title('Volume & Moving Average', fontsize=11, fontweight='bold')
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        st.pyplot(fig)

# ========== TAB 5: GUIDE ==========
with tab5:
    st.subheader("❓ Hướng Dẫn & Thông Tin")
    
    st.markdown("""
    ### 📚 Giới Thiệu Mô Hình
    
    Ứng dụng này sử dụng **Machine Learning** và **Technical Analysis** để dự đoán giá cổ phiếu
    trong 10 ngày tới. Mô hình kết hợp nhiều chỉ báo kỹ thuật để đưa ra dự báo chính xác.
    
    ### 🤖 Các Mô Hình ML Được Sử Dụng
    
    #### 1. **Random Forest**
    - Sử dụng nhiều cây quyết định để dự đoán
    - Tốt cho dữ liệu không tuyến tính
    - Ít bị overfitting hơn
    
    #### 2. **Linear Regression**
    - Mô hình đơn giản, dễ hiểu
    - Tốt khi giá có xu hướng tuyến tính
    - Huấn luyện nhanh
    
    #### 3. **Combined (Ensemble)**
    - Kết hợp cả Random Forest và Linear Regression
    - Lấy trung bình của 2 mô hình
    - Kết quả đa chiều và ổn định
    
    ### 📊 Chỉ Báo Kỹ Thuật
    
    **RSI (Relative Strength Index)**
    - Giá trị: 0-100
    - Quá bán: < 30 (tín hiệu mua)
    - Quá mua: > 70 (tín hiệu bán)
    
    **MACD (Moving Average Convergence Divergence)**
    - Gồm: MACD line, Signal line, Histogram
    - MACD > Signal: Tín hiệu tăng
    - MACD < Signal: Tín hiệu giảm
    
    **Bollinger Bands**
    - Gồm: Middle (MA), Upper (MA + 2σ), Lower (MA - 2σ)
    - Giá > Upper: Quá mua
    - Giá < Lower: Quá bán
    
    **Moving Averages**
    - SMA: Simple Moving Average
    - EMA: Exponential Moving Average
    - Giá > MA: Uptrend
    - Giá < MA: Downtrend
    
    ### 📈 Cách Đọc Kết Quả
    
    1. **Tín Hiệu Giao Dịch**: Kết hợp từ 4 chỉ báo kỹ thuật
    2. **Điểm Tín Hiệu**: 
       - > 0: Tín hiệu tăng
       - = 0: Trung lập
       - < 0: Tín hiệu giảm
    
    3. **Khoảng Tin Cậy (Confidence Interval)**:
       - Đường trên/dưới cho thấy phạm vi dự báo
       - Càng hẹp = càng chính xác
    
    ### ⚠️ Lưu Ý & Tuyên Bố Miễn Trừ
    
    ✓ **Ứng dụng dành cho mục đích giáo dục và phân tích**
    
    ✗ **KHÔNG phải lời khuyên đầu tư chuyên nghiệp**
    
    ⚠️ **Rủi ro đầu tư cao - Bạn chịu toàn bộ trách nhiệm**
    
    💡 **Luôn tham khảo chuyên gia tư vấn tài chính trước khi quyết định**
    
    ### 🎯 Cách Sử Dụng An Toàn
    
    1. **Không dựa 100% vào mô hình**
        - Kết hợp với phân tích cơ bản (P/E, EPS, v.v.)
        - Xem xét tin tức và sự kiện thị trường
    
    2. **Quản lý rủi ro**
        - Chỉ đầu tư số tiền bạn chấp nhận mất
        - Sử dụng stop-loss
        - Đa dạng hóa danh mục
    
    3. **Kiểm tra độ chính xác**
        - So sánh dự báo với giá thực tế
        - Điều chỉnh mô hình nếu cần
        - Theo dõi thường xuyên
    
    ### 📞 Liên Hệ & Hỗ Trợ
    
    - **Model Performance**: Xem R² Score (càng cao càng tốt, tối đa 1.0)
    - **MAE**: Sai số trung bình tuyệt đối
    - **RMSE**: Căn bậc hai sai số bình phương trung bình
    
    Hãy áp dụng mô hình này một cách thông minh!
    """)
    
    st.warning("⚠️ **TUYÊN BỐ MIỄN TRỪ TRÁCH NHIỆM**: Ứng dụng này chỉ dành cho mục đích giáo dục. Không phải lời khuyên đầu tư. Luôn tham khảo chuyên gia tài chính trước khi đầu tư.")

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>📈 Stock Price Prediction AI Model | Developed for Educational Purposes Only</p>
    <p>⚠️ This model is not financial advice. Invest at your own risk.</p>
</div>
""", unsafe_allow_html=True)
