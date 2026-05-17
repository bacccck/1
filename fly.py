import streamlit as st
import requests
import urllib.parse
from datetime import date, timedelta
import re

# 🔐 جلب المفتاح السري 
SERPAPI_KEY = st.secrets["SERPAPI_KEY"]

# 🖥️ إعداد الصفحة
st.set_page_config(page_title="وكيل السفر الذكي", page_icon="✈️", layout="wide")

st.markdown("""
<style>
    .stApp { direction: rtl; }
    p, div, input, select, label, h1, h2, h3, .stTabs { text-align: right !important; }
    .stButton>button { display: block; margin-right: 0; margin-left: auto; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 🧠 قواميس المدن
# ==========================================
CITY_TO_IATA = {
    "الرياض": "RUH", "دبي": "DXB", "جدة": "JED", "القاهرة": "CAI",
    "الدمام": "DMM", "الدوحة": "DOH", "الكويت": "KWI", "المنامة": "BAH",
    "مسقط": "MCT", "عمان": "AMM", "لندن": "LHR", "باريس": "CDG", "اسطنبول": "IST"
}
cities_list = list(CITY_TO_IATA.keys())

# قائمة الوجهات التي سيستكشفها الإيجنت تلقائياً
EXPLORE_DESTINATIONS = {"دبي": "DXB", "القاهرة": "CAI", "اسطنبول": "IST", "عمان": "AMM", "الدوحة": "DOH"}

def clean_and_get_iata(city_input):
    city = city_input.strip()
    return CITY_TO_IATA.get(city, city.upper())

def has_good_legroom(flight):
    """تحليل مساحة الساقين (79 سم / 31 بوصة فأعلى)"""
    legroom_str = flight["flights"][0].get("legroom", "")
    if not legroom_str: return False 
    numbers = re.findall(r'\d+', legroom_str)
    if numbers:
        value = int(numbers[0])
        # تعديل الشرط ليصبح 79 سم أو 31 بوصة فأكثر
        if "cm" in legroom_str.lower() or "سم" in legroom_str: return value >= 79
        elif "in" in legroom_str.lower() or "بوصة" in legroom_str: return value >= 31 
    return False

# ==========================================
# 🛠️ القسم الأول: الأدوات 
# ==========================================
def fetch_all_flights_from_google(origin_iata, destination_iata, date_out, date_return=None, trip_type="ذهاب فقط"):
    url = "https://serpapi.com/search"
    type_code = "1" if trip_type == "ذهاب وعودة" else "2"
    
    params = {
        "engine": "google_flights",
        "departure_id": origin_iata,      
        "arrival_id": destination_iata,   
        "outbound_date": str(date_out), 
        "type": type_code,           
        "currency": "SAR",           
        "hl": "ar", 
        "api_key": SERPAPI_KEY       
    }
    
    if type_code == "1" and date_return: params["return_date"] = str(date_return)
        
    try:
        response = requests.get(url, params=params)
        return response.json()
    except:
        return {}

def generate_real_google_flight_url(origin_iata, destination_iata, date_out, date_return=None, trip_type="ذهاب فقط"):
    if trip_type == "ذهاب وعودة" and date_return:
        query = f"Flights from {origin_iata} to {destination_iata} on {date_out} returning {date_return}"
    else:
        query = f"Flights from {origin_iata} to {destination_iata} on {date_out}"
    encoded_query = urllib.parse.quote(query)
    return f"https://www.google.com/travel/flights?q={encoded_query}&hl=ar&curr=SAR"


# ==========================================
# 🧠 القسم الثاني: المنطق
# ==========================================
def process_flight_search(origin, destination, date_out, date_return, trip_type, require_legroom=False):
    origin_iata = clean_and_get_iata(origin)
    destination_iata = clean_and_get_iata(destination)
    
    data = fetch_all_flights_from_google(origin_iata, destination_iata, date_out, date_return, trip_type)
    if "error" in data: return [{"type": "خطأ", "airline": data["error"], "price": 0, "duration": "", "url": "#"}]
        
    all_flights_raw = data.get("best_flights", []) + data.get("other_flights", [])
    if not all_flights_raw: return []
        
    processed_flights = []
    for flight in all_flights_raw:
        price = flight.get("price")
        if not price or price <= 0: continue
        if require_legroom and not has_good_legroom(flight): continue
            
        airline = flight["flights"][0].get("airline", "غير معروف")
        duration_mins = flight.get("total_duration", 0)
        dep_time = flight["flights"][0].get("departure_airport", {}).get("time", "غير متوفر")
        arr_time = flight["flights"][-1].get("arrival_airport", {}).get("time", "غير متوفر")
        is_transit = "layovers" in flight and len(flight["layovers"]) > 0
        
        processed_flights.append({
            "airline": airline,
            "price": price,
            "duration": f"{round(duration_mins / 60, 1)} ساعة",
            "departure_time": dep_time,
            "arrival_time": arr_time,
            "type": "ترانزيت" if is_transit else "مباشرة",
            "date": str(date_out),
            "url": generate_real_google_flight_url(origin_iata, destination_iata, date_out, date_return, trip_type)
        })
        
    return sorted(processed_flights, key=lambda x: x['price'])[:3]


def process_price_first_search_anywhere(origin, approx_date):
    origin_iata = clean_and_get_iata(origin)
    best_deals = []
    
    dates_to_check = [
        approx_date - timedelta(days=1),
        approx_date,
        approx_date + timedelta(days=1)
    ]
    
    for dest_name, dest_iata in EXPLORE_DESTINATIONS.items():
        for check_date in dates_to_check:
            if check_date < date.today(): continue 
                
            data = fetch_all_flights_from_google(origin_iata, dest_iata, check_date)
            all_flights = data.get("best_flights", [])
            
            is_price_low = False
            if "price_insights" in data and data["price_insights"].get("level") == "low":
                is_price_low = True
                    
            for flight in all_flights:
                price = flight.get("price")
                if not price or price <= 0: continue
                
                if is_price_low:
                    dep_time = flight["flights"][0].get("departure_airport", {}).get("time", "غير متوفر")
                    arr_time = flight["flights"][-1].get("arrival_airport", {}).get("time", "غير متوفر")
                    
                    best_deals.append({
                        "destination": dest_name,
                        "airline": flight["flights"][0].get("airline", "غير معروف"),
                        "price": price,
                        "date": str(check_date),
                        "departure_time": dep_time,
                        "arrival_time": arr_time,
                        "url": generate_real_google_flight_url(origin_iata, dest_iata, check_date)
                    })
                    break 
                    
    return sorted(best_deals, key=lambda x: x['price'])


# ==========================================
# 🖥️ القسم الثالث: الواجهة
# ==========================================
st.title("✈️ وكيل السفر الذكي المتكامل")
today = date.today()

tab1, tab2 = st.tabs(["البحث الذكي المخصص 💺", "السعر أولاً 💰 (أينما كان)"])

# ----------------- التبويب الأول -----------------
with tab1:
    st.write("ابحث عن رحلتك المحددة مع خيار الراحة الإضافية.")
    col1, col2 = st.columns(2)
    with col1:
        origin1 = st.selectbox("من 🛫", options=cities_list, index=None, key="orig1")
        date_out1 = st.date_input("تاريخ الذهاب 📅", min_value=today, key="do1")
        trip_type = st.selectbox("النوع 🔄", ["ذهاب فقط", "ذهاب وعودة"])
    with col2:
        dest1 = st.selectbox("إلى 🛬", options=cities_list, index=None, key="dest1")
        date_return1 = st.date_input("العودة 📅", min_value=date_out1) if trip_type == "ذهاب وعودة" else None
        # 👈 تحديث النص هنا
        require_leg = st.checkbox("💺 أظهر فقط الطائرات ذات مساحة الساقين المريحة (79 سم فأعلى)")

    if st.button("ابحث 🔍", key="btn1"):
        if origin1 and dest1:
            if origin1 == dest1:
                 st.error("⚠️ لا يمكن أن تكون مدينة الانطلاق هي نفسها مدينة الوصول!")
            else:
                with st.spinner("جاري البحث... ⏳"):
                    results = process_flight_search(origin1, dest1, date_out1, date_return1, trip_type, require_leg)
                    if not results:
                        st.warning("⚠️ لم نجد رحلات تطابق شروطك.")
                    else:
                        for i, f in enumerate(results, 1):
                            st.info(f"**الخيار {i}: {f['airline']}** | {f['type']}")
                            st.write(f"💰 **السعر:** {f['price']} ريال")
                            st.write(f"🕒 **المغادرة:** {f['departure_time']} | 🛬 **الوصول:** {f['arrival_time']} | ⏱️ **المدة:** {f['duration']}")
                            st.link_button("احجز الآن 🔗", f['url'])
        else:
            st.error("اختر المدن أولاً.")

# ----------------- التبويب الثاني -----------------
with tab2:
    st.write("🌍 **لا يهمك المكان؟** اختر الانطلاق والتاريخ التقريبي، وسنبحر في أشهر الوجهات لنجلب لك 'لقطة' السعر!")
    
    col3, col4 = st.columns(2)
    with col3:
        origin2 = st.selectbox("من 🛫", options=cities_list, index=None, key="orig2")
    with col4:
        approx_date = st.date_input("تاريخ السفر التقريبي 📅", min_value=today, key="do2")
        
    st.info("💡 سيبحث الإيجنت تلقائياً في: دبي، القاهرة، اسطنبول، عمان، والدوحة.")
    
    if st.button("صِد لي أفضل سعر لأي مكان! 🎯", key="btn2"):
        if origin2:
            with st.spinner("نقوم بمسح الأسعار في عدة دول لعدة أيام... استرخِ قليلاً ⏳"):
                deals = process_price_first_search_anywhere(origin2, approx_date)
                
                if deals:
                    st.success("🎉 وجدنا لك هذه الوجهات بأسعار تعتبر 'أقل من المتوسط'!")
                    for deal in deals:
                        st.success(f"✈️ **الوجهة: إلى {deal['destination']}** | 📅 التاريخ: {deal['date']}")
                        st.write(f"🏢 {deal['airline']} | 💰 **{deal['price']} ريال**")
                        st.write(f"🕒 **المغادرة:** {deal['departure_time']} | 🛬 **الوصول:** {deal['arrival_time']}")
                        st.link_button(f"احجز رحلتك إلى {deal['destination']} 🔗", deal['url'])
                        st.divider()
                else:
                    st.warning("لم نجد أسعاراً 'أقل من المتوسط' في وجهات الاستكشاف لهذه الأيام. الأسعار تبدو عادية حالياً.")
        else:
            st.error("اختر مدينة الانطلاق أولاً.")
