import csv
from datetime import datetime, timedelta
from math import ceil, floor
from pathlib import Path
from statistics import mean

import streamlit as st


st.set_page_config(
    page_title="VND → AUD Transfer Optimiser",
    page_icon="💱",
    layout="wide",
)

st.markdown(
    """
    <style>
        .block-container {
            max-width: 1180px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }
        .hero {
            background: linear-gradient(125deg, #0b5d57 0%, #0f766e 55%, #0891b2 100%);
            border-radius: 22px;
            color: white;
            padding: 2.2rem 2.4rem;
            margin-bottom: 1.4rem;
            box-shadow: 0 14px 35px rgba(15, 118, 110, 0.18);
        }
        .hero h1 {
            color: white;
            font-size: clamp(2rem, 4vw, 3.25rem);
            line-height: 1.08;
            margin: 0 0 0.65rem 0;
        }
        .hero p {
            color: rgba(255, 255, 255, 0.88);
            font-size: 1.05rem;
            margin: 0;
            max-width: 760px;
        }
        .eyebrow {
            color: #99f6e4;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            margin-bottom: 0.65rem;
            text-transform: uppercase;
        }
        [data-testid="stMetric"] {
            border-radius: 14px;
        }
        [data-testid="stSidebar"] {
            border-right: 1px solid rgba(128, 128, 128, 0.18);
        }
    </style>
    """,
    unsafe_allow_html=True,
)


translations = {
    "English": {
        "sidebar_settings": "Transfer settings",
        "aud_amount": "AUD amount to transfer",
        "deadline": "Days until transfer deadline",
        "set_budget": "Set a maximum VND budget",
        "maximum_budget": "Maximum VND budget",
        "data_caption": "Data source: Vietcombank AUD selling-rate history",
        "data_error": "At least 31 valid daily rates are required.",
        "eyebrow": "Exchange-rate decision dashboard",
        "title": "VND → AUD Transfer Optimiser",
        "subtitle": "Historical context, budget planning and a transparent short-term forecast in one place.",
        "updated": "Updated",
        "lower_better": "Lower is better when buying AUD with VND.",
        "tab_overview": "Overview",
        "tab_planner": "Transfer planner",
        "tab_forecast": "Analysis & forecast",
        "current_rate": "Current rate",
        "vs_previous": "vs previous day",
        "vs_7": "Vs 7-day average",
        "vs_30": "Vs 30-day average",
        "range_30": "30-day range",
        "market_read": "Market read",
        "favourable": "Relatively favourable",
        "favourable_text": "The current rate is below both recent averages. AUD is relatively cheaper than its recent trend.",
        "expensive": "Relatively expensive",
        "expensive_text": "The current rate is above both recent averages. AUD is relatively more expensive than its recent trend.",
        "mixed": "Mixed conditions",
        "mixed_text": "The 7-day and 30-day signals disagree, so the recent trend is not decisive.",
        "decision_above": "**Rate is {value:.1f}% above its previous 30-day average.** Waiting hasn't reliably helped — historical testing showed timing strategies performed slightly worse than transferring immediately.",
        "decision_below": "**Rate is {value:.1f}% below its previous 30-day average.** That is relatively favourable, but historical testing still found no reliable advantage from trying to time the transfer.",
        "decision_equal": "**Rate is in line with its previous 30-day average.** Historical testing found no reliable advantage from waiting for a better day.",
        "percentile_text": "Today's rate is better than **{all_value:.0f}%** of earlier days and **{recent_value:.0f}%** of the previous 90 days.",
        "history": "Rate history",
        "history_help": "A falling line is favourable because fewer VND are needed for each AUD.",
        "window": "History window",
        "window_30": "30 days",
        "window_90": "90 days",
        "window_all": "All data",
        "chart_rate": "VND per AUD",
        "date": "Date",
        "change": "Change",
        "change_pct": "Change (%)",
        "explore_date": "Explore a date",
        "selected_date": "Selected date",
        "selected_rate": "Selected rate",
        "selected_direction": "Direction",
        "lower_direction": "Lower (better)",
        "higher_direction": "Higher",
        "unchanged_direction": "Unchanged",
        "interactive_tip": "On a phone, move the date slider to explore the trend. On a laptop, you can also hover anywhere along the line for the date, rate, movement and percentage change.",
        "planner_title": "Plan your transfer",
        "planner_intro": "Use the current rate to estimate cost, compare it with recent history and test an optional budget.",
        "current_cost": "Current transfer cost",
        "aud_received": "AUD received",
        "average_cost": "At 30-day average",
        "difference": "Difference",
        "vnd_calculator": "Quick VND → AUD calculator",
        "vnd_amount": "VND amount available",
        "estimated_receive": "Estimated amount received",
        "cost_less": "Today's transfer would cost approximately **{value:,.0f} VND less** than at the previous 30-day average.",
        "cost_more": "Today's transfer would cost approximately **{value:,.0f} VND more** than at the previous 30-day average.",
        "maximum_rate": "Maximum affordable rate",
        "within_budget": "Within budget by **{value:,.0f} VND**.",
        "over_budget": "Over budget by **{value:,.0f} VND**.",
        "no_budget": "No maximum budget is set. Turn on the option above to test a spending limit.",
        "deadline_warning": "Your deadline is close. Historical testing found no reliable advantage from waiting.",
        "forecast_title": "Short-term rate outlook",
        "forecast_intro": "The most reliable tested next-day baseline is the latest observed daily rate. The range below applies historical daily movements to that baseline.",
        "point_forecast": "Next-day estimate",
        "forecast_cost": "Estimated transfer cost",
        "historical_range": "80% historical range",
        "historical_coverage": "Backtested interval coverage",
        "baseline_mae": "Baseline MAE",
        "tolerance_accuracy": "Within ±0.5%",
        "range_caption": "Forecast interval: **{low:,.2f}–{high:,.2f} VND/AUD**. Its radius is the 80th percentile of the latest {count} absolute daily movements.",
        "accuracy_caption": "Across historical next-day tests, the point forecast was within ±0.5% of the actual rate **{tolerance:.1f}%** of the time. The rolling 80% interval contained the actual next daily rate **{coverage:.1f}%** of the time. These are backtested hit rates, not guaranteed future accuracy.",
        "direction_title": "Recent direction profile",
        "lower_next": "Lower",
        "unchanged_next": "Unchanged",
        "higher_next": "Higher",
        "direction_caption": "Share of the latest {count} day-to-day changes. Lower is favourable for buying AUD.",
        "direction_verdict": "Movements are close to a coin flip, which is why tested timing strategies did not beat transferring immediately.",
        "trend_title": "Trend and risk indicators",
        "average_move": "Average daily move (30)",
        "best_30": "Best rate (30)",
        "worst_30": "Worst rate (30)",
        "spread_30": "30-day spread",
        "factors_title": "External factors to monitor",
        "factors_intro": "These drivers can affect AUD/VND, but they are not included in the numerical forecast until aligned historical data passes walk-forward testing.",
        "interest_title": "Interest-rate differentials",
        "interest_text": "RBA policy relative to the US and other major economies can change demand for AUD-denominated assets.",
        "commodity_title": "Commodities and China",
        "commodity_text": "Iron ore, energy prices and Chinese demand affect Australia's terms of trade and often the AUD.",
        "risk_title": "Global risk sentiment",
        "risk_text": "Equity-market stress and risk aversion can weaken demand for AUD over short horizons.",
        "vietnam_title": "Vietnam-side pricing",
        "vietnam_text": "USD/VND conditions, domestic policy and Vietcombank's customer spread affect the final VND/AUD selling rate.",
        "factors_source": "Background: [Reserve Bank of Australia — Drivers of the AUD exchange rate](https://www.rba.gov.au/education/resources/explainers/drivers-of-the-aud-exchange-rate.html).",
        "forecast_note": "Forecasts are uncertain. This baseline previously achieved a mean absolute error of about {mae:,.2f} VND/AUD, while more complex regression and timing models performed worse and were discarded.",
        "evaluation": "Model evaluation details",
        "naive_result": "Naive next-day forecast MAE: **{mae:,.2f} VND/AUD** across {count} historical daily predictions.",
        "regression_result": "Walk-forward regression MAE: **56.51 VND**, compared with **53.06 VND** for its baseline test. The regression model was discarded.",
        "strategy_result": "The tested 14-day timing strategy was **5.79 VND/AUD worse** than transferring immediately on average, so it was discarded.",
        "disclaimer": "Educational decision support only — not financial advice or a guaranteed forecast. Transfer fees and provider spreads are not included.",
    },
    "Tiếng Việt": {
        "sidebar_settings": "Thiết lập chuyển tiền",
        "aud_amount": "Số AUD cần chuyển",
        "deadline": "Số ngày còn lại đến hạn chuyển",
        "set_budget": "Đặt ngân sách VND tối đa",
        "maximum_budget": "Ngân sách VND tối đa",
        "data_caption": "Nguồn dữ liệu: lịch sử tỷ giá bán AUD của Vietcombank",
        "data_error": "Cần ít nhất 31 tỷ giá theo ngày hợp lệ.",
        "eyebrow": "Bảng hỗ trợ quyết định tỷ giá",
        "title": "Công cụ tối ưu chuyển tiền VND → AUD",
        "subtitle": "Bối cảnh lịch sử, lập ngân sách và dự báo ngắn hạn minh bạch trong cùng một nơi.",
        "updated": "Cập nhật",
        "lower_better": "Tỷ giá càng thấp càng có lợi khi mua AUD bằng VND.",
        "tab_overview": "Tổng quan",
        "tab_planner": "Lập kế hoạch",
        "tab_forecast": "Phân tích & dự báo",
        "current_rate": "Tỷ giá hiện tại",
        "vs_previous": "so với ngày trước",
        "vs_7": "So với TB 7 ngày",
        "vs_30": "So với TB 30 ngày",
        "range_30": "Khoảng 30 ngày",
        "market_read": "Nhận định thị trường",
        "favourable": "Tương đối thuận lợi",
        "favourable_text": "Tỷ giá hiện tại thấp hơn cả hai mức trung bình gần đây. AUD đang tương đối rẻ hơn xu hướng gần đây.",
        "expensive": "Tương đối đắt",
        "expensive_text": "Tỷ giá hiện tại cao hơn cả hai mức trung bình gần đây. AUD đang tương đối đắt hơn xu hướng gần đây.",
        "mixed": "Tín hiệu trái chiều",
        "mixed_text": "Tín hiệu 7 ngày và 30 ngày không đồng thuận, vì vậy xu hướng gần đây chưa rõ ràng.",
        "decision_above": "**Tỷ giá cao hơn {value:.1f}% so với mức trung bình 30 ngày trước.** Việc chờ đợi chưa cho thấy lợi ích đáng tin cậy — kiểm định lịch sử cho thấy các chiến lược chọn thời điểm hơi kém hơn so với chuyển ngay.",
        "decision_below": "**Tỷ giá thấp hơn {value:.1f}% so với mức trung bình 30 ngày trước.** Đây là mức tương đối thuận lợi, nhưng kiểm định lịch sử vẫn không cho thấy lợi ích đáng tin cậy từ việc cố chọn thời điểm.",
        "decision_equal": "**Tỷ giá đang gần bằng mức trung bình 30 ngày trước.** Kiểm định lịch sử không cho thấy lợi ích đáng tin cậy từ việc chờ một ngày tốt hơn.",
        "percentile_text": "Tỷ giá hôm nay tốt hơn **{all_value:.0f}%** các ngày trước đây và **{recent_value:.0f}%** trong 90 ngày gần nhất.",
        "history": "Lịch sử tỷ giá",
        "history_help": "Đường đi xuống là thuận lợi vì cần ít VND hơn cho mỗi AUD.",
        "window": "Khoảng thời gian",
        "window_30": "30 ngày",
        "window_90": "90 ngày",
        "window_all": "Toàn bộ dữ liệu",
        "chart_rate": "VND trên mỗi AUD",
        "date": "Ngày",
        "change": "Mức thay đổi",
        "change_pct": "Thay đổi (%)",
        "explore_date": "Chọn ngày để xem chi tiết",
        "selected_date": "Ngày đã chọn",
        "selected_rate": "Tỷ giá đã chọn",
        "selected_direction": "Hướng biến động",
        "lower_direction": "Giảm (tốt hơn)",
        "higher_direction": "Tăng",
        "unchanged_direction": "Không đổi",
        "interactive_tip": "Trên điện thoại, kéo thanh ngày để xem xu hướng. Trên máy tính, bạn cũng có thể di chuột dọc theo đường biểu đồ để xem ngày, tỷ giá, mức thay đổi và phần trăm thay đổi.",
        "planner_title": "Lập kế hoạch chuyển tiền",
        "planner_intro": "Dùng tỷ giá hiện tại để ước tính chi phí, so sánh với lịch sử gần đây và kiểm tra ngân sách tùy chọn.",
        "current_cost": "Chi phí chuyển hiện tại",
        "aud_received": "AUD nhận được",
        "average_cost": "Theo TB 30 ngày",
        "difference": "Chênh lệch",
        "vnd_calculator": "Quy đổi nhanh VND → AUD",
        "vnd_amount": "Số VND hiện có",
        "estimated_receive": "Số tiền ước tính nhận được",
        "cost_less": "Chuyển hôm nay sẽ rẻ hơn khoảng **{value:,.0f} VND** so với mức trung bình 30 ngày trước.",
        "cost_more": "Chuyển hôm nay sẽ đắt hơn khoảng **{value:,.0f} VND** so với mức trung bình 30 ngày trước.",
        "maximum_rate": "Tỷ giá tối đa có thể chi trả",
        "within_budget": "Thấp hơn ngân sách **{value:,.0f} VND**.",
        "over_budget": "Vượt ngân sách **{value:,.0f} VND**.",
        "no_budget": "Chưa đặt ngân sách tối đa. Bật tùy chọn phía trên để kiểm tra giới hạn chi tiêu.",
        "deadline_warning": "Thời hạn chuyển tiền đã gần. Kiểm tra lịch sử không cho thấy chờ đợi mang lại lợi thế đáng tin cậy.",
        "forecast_title": "Triển vọng tỷ giá ngắn hạn",
        "forecast_intro": "Mô hình cơ sở cho ngày tiếp theo đáng tin cậy nhất đã kiểm tra dùng tỷ giá ngày mới nhất. Khoảng dưới đây áp dụng biến động hằng ngày trong lịch sử vào mức cơ sở đó.",
        "point_forecast": "Ước tính ngày tiếp theo",
        "forecast_cost": "Chi phí chuyển ước tính",
        "historical_range": "Khoảng lịch sử 80%",
        "historical_coverage": "Độ bao phủ khi kiểm định",
        "baseline_mae": "MAE mô hình cơ sở",
        "tolerance_accuracy": "Nằm trong ±0,5%",
        "range_caption": "Khoảng dự báo: **{low:,.2f}–{high:,.2f} VND/AUD**. Bán kính khoảng bằng phân vị thứ 80 của {count} biến động tuyệt đối hằng ngày gần nhất.",
        "accuracy_caption": "Trong các kiểm định lịch sử cho ngày tiếp theo, dự báo điểm nằm trong ±0,5% so với tỷ giá thực tế **{tolerance:.1f}%** số lần. Khoảng dự báo cuốn chiếu 80% chứa tỷ giá thực tế của ngày tiếp theo **{coverage:.1f}%** số lần. Đây là tỷ lệ đạt trong kiểm định quá khứ, không bảo đảm độ chính xác tương lai.",
        "direction_title": "Phân bố hướng biến động gần đây",
        "lower_next": "Giảm",
        "unchanged_next": "Không đổi",
        "higher_next": "Tăng",
        "direction_caption": "Tỷ trọng trong {count} thay đổi giữa các ngày gần nhất. Giảm là có lợi khi mua AUD.",
        "direction_verdict": "Biến động gần giống tung đồng xu, vì vậy các chiến lược chọn thời điểm đã kiểm tra không tốt hơn việc chuyển ngay.",
        "trend_title": "Chỉ báo xu hướng và rủi ro",
        "average_move": "Biến động TB mỗi ngày (30)",
        "best_30": "Tỷ giá tốt nhất (30)",
        "worst_30": "Tỷ giá xấu nhất (30)",
        "spread_30": "Biên độ 30 ngày",
        "factors_title": "Các yếu tố bên ngoài cần theo dõi",
        "factors_intro": "Các yếu tố này có thể ảnh hưởng AUD/VND, nhưng chưa được đưa vào dự báo số cho đến khi dữ liệu lịch sử đồng bộ vượt qua kiểm định cuốn chiếu.",
        "interest_title": "Chênh lệch lãi suất",
        "interest_text": "Chính sách RBA so với Mỹ và các nền kinh tế lớn có thể thay đổi nhu cầu đối với tài sản định giá bằng AUD.",
        "commodity_title": "Hàng hóa và Trung Quốc",
        "commodity_text": "Giá quặng sắt, năng lượng và nhu cầu từ Trung Quốc ảnh hưởng điều kiện thương mại của Úc và thường tác động đến AUD.",
        "risk_title": "Tâm lý rủi ro toàn cầu",
        "risk_text": "Căng thẳng trên thị trường cổ phiếu và tâm lý né tránh rủi ro có thể làm giảm nhu cầu AUD trong ngắn hạn.",
        "vietnam_title": "Định giá phía Việt Nam",
        "vietnam_text": "Điều kiện USD/VND, chính sách trong nước và biên giá khách hàng của Vietcombank ảnh hưởng tỷ giá bán VND/AUD cuối cùng.",
        "factors_source": "Thông tin nền: [Ngân hàng Dự trữ Úc — Các yếu tố chi phối tỷ giá AUD](https://www.rba.gov.au/education/resources/explainers/drivers-of-the-aud-exchange-rate.html).",
        "forecast_note": "Dự báo luôn có độ bất định. Mô hình cơ sở này trước đây có sai số tuyệt đối trung bình khoảng {mae:,.2f} VND/AUD; các mô hình hồi quy và chọn thời điểm phức tạp hơn cho kết quả kém hơn nên đã bị loại.",
        "evaluation": "Chi tiết đánh giá mô hình",
        "naive_result": "MAE dự báo đơn giản cho ngày tiếp theo: **{mae:,.2f} VND/AUD** trên {count} dự báo lịch sử theo ngày.",
        "regression_result": "MAE hồi quy cuốn chiếu là **56.51 VND**, so với **53.06 VND** của mô hình cơ sở trong cùng bài kiểm tra. Mô hình hồi quy đã bị loại.",
        "strategy_result": "Chiến lược chọn thời điểm trong 14 ngày tệ hơn trung bình **5.79 VND/AUD** so với chuyển ngay, nên đã bị loại.",
        "disclaimer": "Chỉ nhằm hỗ trợ quyết định và mục đích giáo dục — không phải tư vấn tài chính hay dự báo được bảo đảm. Chưa bao gồm phí chuyển và chênh lệch giá của nhà cung cấp.",
    },
}


def percentile(values, fraction):
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(ordered) - 1)
    weight = position - lower_index
    return (
        ordered[lower_index] * (1 - weight)
        + ordered[upper_index] * weight
    )


def compact_vnd(value):
    absolute_value = abs(value)
    if absolute_value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.1f}B VND"
    if absolute_value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M VND"
    if absolute_value >= 1_000:
        return f"{value / 1_000:.1f}K VND"
    return f"{value:,.0f} VND"


language = st.sidebar.selectbox(
    "Language / Ngôn ngữ",
    ("English", "Tiếng Việt"),
    key="language",
)
t = translations[language]

st.sidebar.divider()
st.sidebar.caption(t["data_caption"])

data_file = Path(__file__).parent / "data" / "vcb_aud_daily.csv"
with data_file.open(newline="", encoding="utf-8") as file:
    valid_rows = [
        row
        for row in csv.DictReader(file)
        if row.get("date") and row.get("sell")
    ]

daily_rows = {}
for row in valid_rows:
    date_key = row["date"][:10]
    daily_rows[date_key] = {
        "date": date_key,
        "sell": row["sell"],
    }
rows = [daily_rows[date_key] for date_key in sorted(daily_rows)]
if len(rows) < 31:
    st.error(t["data_error"])
    st.stop()

dates = [datetime.fromisoformat(row["date"]) for row in rows]
date_labels = [row["date"] for row in rows]
rates = [float(row["sell"]) for row in rows]
latest = rates[-1]
previous = rates[-2]
previous_30_rates = rates[-31:-1]
average_7 = mean(previous_30_rates[-7:])
average_30 = mean(previous_30_rates)
latest_30 = rates[-30:]
daily_changes = [
    current - prior
    for prior, current in zip(rates, rates[1:])
]
baseline_mae = mean(abs(change) for change in daily_changes)
recent_change_window = daily_changes[-180:]
forecast_radius = percentile(
    [abs(change) for change in recent_change_window],
    0.80,
)
range_low = latest - forecast_radius
range_high = latest + forecast_radius
average_move_30 = mean(abs(change) for change in daily_changes[-30:])

tolerance_hits = sum(
    abs(current - prior) / prior <= 0.005
    for prior, current in zip(rates, rates[1:])
)
tolerance_accuracy = tolerance_hits / len(daily_changes) * 100

coverage_hits = 0
coverage_count = 0
for target_index in range(61, len(rates)):
    prior_errors = [
        abs(change)
        for change in daily_changes[
            max(0, target_index - 181):target_index - 1
        ]
    ]
    interval_radius = percentile(prior_errors, 0.80)
    actual_error = abs(daily_changes[target_index - 1])
    coverage_hits += actual_error <= interval_radius
    coverage_count += 1

interval_coverage = coverage_hits / coverage_count * 100

historical_rates = rates[:-1]
better_than = sum(rate > latest for rate in historical_rates)
all_percentile = better_than / len(historical_rates) * 100
recent_rates = rates[-91:-1]
better_recent = sum(rate > latest for rate in recent_rates)
recent_percentile = better_recent / len(recent_rates) * 100

lower_count = sum(change < 0 for change in recent_change_window)
unchanged_count = sum(change == 0 for change in recent_change_window)
higher_count = sum(change > 0 for change in recent_change_window)
direction_count = len(recent_change_window)

st.markdown(
    f"""
    <div class="hero">
        <div class="eyebrow">{t["eyebrow"]}</div>
        <h1>{t["title"]}</h1>
        <p>{t["subtitle"]}</p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.caption(f"{t['updated']}: {date_labels[-1]} · {t['lower_better']}")

average_30_difference_pct = (latest / average_30 - 1) * 100
if average_30_difference_pct > 0.05:
    st.warning(
        t["decision_above"].format(
            value=abs(average_30_difference_pct)
        )
    )
elif average_30_difference_pct < -0.05:
    st.success(
        t["decision_below"].format(
            value=abs(average_30_difference_pct)
        )
    )
else:
    st.info(t["decision_equal"])

overview_tab, planner_tab, forecast_tab = st.tabs(
    [
        f"📊 {t['tab_overview']}",
        f"🧮 {t['tab_planner']}",
        f"🔎 {t['tab_forecast']}",
    ]
)

with overview_tab:
    metric_1, metric_2, metric_3 = st.columns(3)
    metric_1.metric(
        t["current_rate"],
        f"{latest:,.0f} VND/AUD",
        delta=f"{latest - previous:+,.2f} {t['vs_previous']}",
        delta_color="inverse",
        border=True,
    )
    metric_2.metric(
        t["vs_30"],
        f"{latest - average_30:+,.0f} VND",
        delta=f"{(latest / average_30 - 1) * 100:+.2f}%",
        delta_color="inverse",
        border=True,
    )
    metric_3.metric(
        t["range_30"],
        f"{min(latest_30) / 1_000:.1f}K–{max(latest_30) / 1_000:.1f}K",
        delta=f"{max(latest_30) - min(latest_30):,.0f} VND",
        delta_color="off",
        border=True,
    )

    st.write(
        t["percentile_text"].format(
            all_value=all_percentile,
            recent_value=recent_percentile,
        )
    )

    chart_header, window_column = st.columns([3, 1])
    with chart_header:
        st.subheader(t["history"])
        st.caption(t["history_help"])
    with window_column:
        history_window = st.selectbox(
            t["window"],
            (30, 90, 0),
            index=0,
            format_func=lambda value: {
                30: t["window_30"],
                90: t["window_90"],
                0: t["window_all"],
            }[value],
            key="history_window",
        )

    if history_window == 30:
        start_index = -30
    elif history_window == 90:
        start_index = -90
    else:
        start_index = 0

    chart_rate_label = t["chart_rate"]
    start_position = (
        len(rates) + start_index
        if start_index < 0
        else start_index
    )
    target_date = dates[-1] - timedelta(days=30)
    meaningful_indices = [
        index
        for index in range(start_position, len(rates))
        if index > 0 and rates[index] != rates[index - 1]
    ]
    default_selected_index = min(
        meaningful_indices or range(start_position, len(rates)),
        key=lambda index: abs(dates[index] - target_date),
    )
    selected_index = st.select_slider(
        t["explore_date"],
        options=list(range(start_position, len(rates))),
        value=default_selected_index,
        format_func=lambda index: date_labels[index],
        key=f"selected_day_{history_window}",
    )
    selected_change = (
        rates[selected_index] - rates[selected_index - 1]
        if selected_index > 0
        else 0
    )
    selected_change_pct = (
        (rates[selected_index] / rates[selected_index - 1] - 1) * 100
        if selected_index > 0
        else 0
    )
    if selected_change < 0:
        selected_direction = t["lower_direction"]
    elif selected_change > 0:
        selected_direction = t["higher_direction"]
    else:
        selected_direction = t["unchanged_direction"]

    selected_rates = rates[start_position:]
    y_axis_min = min(
        15_000,
        floor(min(selected_rates) / 1_000) * 1_000,
    )
    y_axis_max = max(
        25_000,
        ceil(max(selected_rates) / 1_000) * 1_000,
    )
    chart_data = [
        {
            "date": dates[index].isoformat(),
            "rate": rates[index],
            "change": (
                rates[index] - rates[index - 1]
                if index > 0
                else 0
            ),
            "change_pct": (
                (rates[index] / rates[index - 1] - 1) * 100
                if index > 0
                else 0
            ),
            "direction": (
                "Decrease"
                if index > 0 and rates[index] < rates[index - 1]
                else "Increase"
                if index > 0 and rates[index] > rates[index - 1]
                else "Unchanged"
            ),
            "selected": index == selected_index,
        }
        for index in range(start_position, len(rates))
    ]
    chart_spec = {
        "encoding": {
            "x": {
                "field": "date",
                "type": "temporal",
                "title": t["date"],
                "axis": {
                    "grid": False,
                    "format": "%d %b",
                    "labelAngle": -30,
                    "labelOverlap": "greedy",
                    "tickCount": 6,
                },
            },
            "y": {
                "field": "rate",
                "type": "quantitative",
                "title": chart_rate_label,
                "scale": {
                    "domain": [y_axis_min, y_axis_max],
                    "nice": False,
                },
                "axis": {"format": ",.0f"},
            },
        },
        "layer": [
            {
                "mark": {
                    "type": "line",
                    "color": "#14b8a6",
                    "strokeWidth": 2.5,
                }
            },
            {
                "transform": [{"filter": "datum.selected"}],
                "mark": {
                    "type": "point",
                    "filled": True,
                    "size": 150,
                    "opacity": 1,
                    "stroke": "white",
                    "strokeWidth": 2,
                },
                "encoding": {
                    "color": {
                        "field": "direction",
                        "type": "nominal",
                        "scale": {
                            "domain": [
                                "Decrease",
                                "Unchanged",
                                "Increase",
                            ],
                            "range": [
                                "#16a34a",
                                "#94a3b8",
                                "#dc2626",
                            ],
                        },
                        "legend": None,
                    },
                },
            },
            {
                "mark": {
                    "type": "point",
                    "filled": True,
                    "size": 280,
                    "opacity": 0,
                },
                "encoding": {
                    "tooltip": [
                        {
                            "field": "date",
                            "type": "temporal",
                            "title": t["date"],
                            "format": "%Y-%m-%d",
                        },
                        {
                            "field": "rate",
                            "type": "quantitative",
                            "title": chart_rate_label,
                            "format": ",.2f",
                        },
                        {
                            "field": "change",
                            "type": "quantitative",
                            "title": t["change"],
                            "format": "+,.2f",
                        },
                        {
                            "field": "change_pct",
                            "type": "quantitative",
                            "title": t["change_pct"],
                            "format": "+.2f",
                        },
                    ],
                },
            },
        ],
    }
    st.vega_lite_chart(
        chart_data,
        chart_spec,
        height=400,
        width="stretch",
    )
    st.caption(t["interactive_tip"])

    detail_1, detail_2 = st.columns(2)
    detail_1.metric(
        t["selected_date"],
        date_labels[selected_index],
        border=True,
    )
    detail_2.metric(
        t["selected_rate"],
        f"{rates[selected_index]:,.2f}",
        border=True,
    )
    detail_3, detail_4 = st.columns(2)
    detail_3.metric(
        t["change"],
        f"{selected_change:+,.2f} VND",
        border=True,
    )
    detail_4.metric(
        t["change_pct"],
        f"{selected_change_pct:+.2f}%",
        border=True,
    )
    st.caption(f"{t['selected_direction']}: **{selected_direction}**")

with planner_tab:
    st.subheader(t["planner_title"])
    st.write(t["planner_intro"])

    input_1, input_2 = st.columns(2)
    with input_1:
        aud_amount = st.number_input(
            t["aud_amount"],
            min_value=1.0,
            value=3000.0,
            step=100.0,
            key="aud_amount",
        )
    with input_2:
        days_remaining = st.number_input(
            t["deadline"],
            min_value=0,
            value=14,
            step=1,
            key="days_remaining",
        )

    use_budget = st.checkbox(t["set_budget"], key="use_budget")
    maximum_budget_vnd = None
    if use_budget:
        maximum_budget_vnd = st.number_input(
            t["maximum_budget"],
            min_value=1_000_000,
            value=57_000_000,
            step=100_000,
            key="maximum_budget_vnd",
        )

    current_cost = aud_amount * latest
    average_30_cost = aud_amount * average_30
    average_cost_difference = average_30_cost - current_cost

    plan_1, plan_2, plan_3 = st.columns(3)
    plan_1.metric(
        t["current_cost"],
        compact_vnd(current_cost),
        border=True,
    )
    plan_2.metric(
        t["average_cost"],
        compact_vnd(average_30_cost),
        border=True,
    )
    plan_3.metric(
        t["difference"],
        compact_vnd(abs(average_cost_difference)),
        delta=compact_vnd(average_cost_difference),
        delta_color="normal",
        border=True,
    )

    if average_cost_difference >= 0:
        st.success(t["cost_less"].format(value=average_cost_difference))
    else:
        st.warning(
            t["cost_more"].format(
                value=abs(average_cost_difference)
            )
        )

    if maximum_budget_vnd is not None:
        maximum_affordable_rate = maximum_budget_vnd / aud_amount
        budget_difference = maximum_budget_vnd - current_cost
        st.write(
            f"{t['maximum_rate']}: "
            f"**{maximum_affordable_rate:,.2f} VND/AUD**"
        )
        if budget_difference >= 0:
            st.success(t["within_budget"].format(value=budget_difference))
        else:
            st.error(
                t["over_budget"].format(
                    value=abs(budget_difference)
                )
            )
    else:
        st.info(t["no_budget"])

    if days_remaining <= 2:
        st.warning(t["deadline_warning"])

    st.divider()
    calculator_1, calculator_2 = st.columns([2, 1])
    with calculator_1:
        st.subheader(t["vnd_calculator"])
        vnd_amount = st.number_input(
            t["vnd_amount"],
            min_value=1_000_000,
            value=56_000_000,
            step=1_000_000,
            key="vnd_amount",
        )
    with calculator_2:
        st.metric(
            t["estimated_receive"],
            f"AUD {vnd_amount / latest:,.2f}",
            border=True,
        )

with forecast_tab:
    st.subheader(t["forecast_title"])
    st.write(t["forecast_intro"])

    forecast_cost = aud_amount * latest
    forecast_1, forecast_2 = st.columns(2)
    forecast_1.metric(
        t["point_forecast"],
        f"{latest:,.2f} VND/AUD",
        border=True,
    )
    forecast_2.metric(
        t["forecast_cost"],
        compact_vnd(forecast_cost),
        border=True,
    )
    forecast_3, forecast_4 = st.columns(2)
    forecast_3.metric(
        t["historical_range"],
        f"{range_low / 1_000:.1f}K–{range_high / 1_000:.1f}K",
        border=True,
    )
    forecast_4.metric(
        t["historical_coverage"],
        f"{interval_coverage:.1f}%",
        border=True,
    )
    st.caption(
        t["range_caption"].format(
            low=range_low,
            high=range_high,
            count=len(recent_change_window),
        )
    )

    quality_1, quality_2 = st.columns(2)
    quality_1.metric(
        t["tolerance_accuracy"],
        f"{tolerance_accuracy:.1f}%",
        border=True,
    )
    quality_2.metric(
        t["baseline_mae"],
        f"{baseline_mae:,.2f} VND/AUD",
        border=True,
    )
    st.caption(
        t["accuracy_caption"].format(
            tolerance=tolerance_accuracy,
            coverage=interval_coverage,
        )
    )

    st.subheader(t["direction_title"])
    direction_1, direction_2, direction_3 = st.columns(3)
    direction_1.metric(
        t["lower_next"],
        f"{lower_count / direction_count * 100:.1f}%",
        border=True,
    )
    direction_2.metric(
        t["unchanged_next"],
        f"{unchanged_count / direction_count * 100:.1f}%",
        border=True,
    )
    direction_3.metric(
        t["higher_next"],
        f"{higher_count / direction_count * 100:.1f}%",
        border=True,
    )
    st.caption(t["direction_caption"].format(count=direction_count))
    st.info(t["direction_verdict"])

    st.subheader(t["trend_title"])
    trend_1, trend_2 = st.columns(2)
    trend_1.metric(
        t["average_move"],
        f"{average_move_30:,.2f} VND",
        border=True,
    )
    trend_2.metric(
        t["best_30"],
        f"{min(latest_30):,.2f}",
        border=True,
    )
    trend_3, trend_4 = st.columns(2)
    trend_3.metric(
        t["worst_30"],
        f"{max(latest_30):,.2f}",
        border=True,
    )
    trend_4.metric(
        t["spread_30"],
        f"{max(latest_30) - min(latest_30):,.2f}",
        border=True,
    )

    st.subheader(t["factors_title"])
    st.write(t["factors_intro"])
    factor_1, factor_2 = st.columns(2)
    with factor_1:
        with st.container(border=True):
            st.markdown(f"**{t['interest_title']}**")
            st.write(t["interest_text"])
        with st.container(border=True):
            st.markdown(f"**{t['risk_title']}**")
            st.write(t["risk_text"])
    with factor_2:
        with st.container(border=True):
            st.markdown(f"**{t['commodity_title']}**")
            st.write(t["commodity_text"])
        with st.container(border=True):
            st.markdown(f"**{t['vietnam_title']}**")
            st.write(t["vietnam_text"])
    st.caption(t["factors_source"])

    st.info(t["forecast_note"].format(mae=baseline_mae))
    with st.expander(t["evaluation"]):
        st.write(
            t["naive_result"].format(
                mae=baseline_mae,
                count=len(daily_changes),
            )
        )
        st.write(t["regression_result"])
        st.write(t["strategy_result"])

st.divider()
st.caption(t["disclaimer"])
