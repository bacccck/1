import streamlit as st
import requests
import urllib.parse  # مكتبة لتجهيز الروابط الحقيقية بشكل سليم

# 🔐 جلب المفتاح السري بأمان من خزنة Streamlit
SERPAPI_KEY = st.secrets["SERPAPI_KEY"]

# 🖥️ إعداد الصفحة وتحديد العنوان والأيقونة
st.set_page_config(page_title="وكيل السفر الذكي", page_icon="✈️")

# 🖥️ كود CSS لتغيير اتجاه الصفحة ليصبح من اليمين إلى اليسار (RTL)
st.markdown("""
<style>
    .stApp {
        direction: rtl;
    }
    p, div, input, select, label, h1, h2, h3 {
        text-align: right !important;
    }
    .stButton>button {
        display: block;
        margin-right: 0;
        margin-left: auto;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 🧠 قاموس ترجمة المدن العربية إلى أكواد المطارات العالمية
# ==========================================
CITY_TO_IATA = {
    "الرياض": "RUH", "رياض": "RUH",
    "دبي": "DXB", "دبى": "DXB",
    "جدة": "JED", "جده": "JED",
    "القاهرة": "CAI", "قاهره": "CAI",
    "الدمام": "DMM", "دمام": "DMM",
    "الدوحة": "DOH", "دوحه": "DOH",
    "الكويت": "KWI",
    "المنامة": "BAH", "منامة": "BAH",
    "مسقط": "MCT",
    "عمان": "AMM",
    "لندن": "LHR",
    "باريس": "CDG",
    "اسطنبول": "IST", "إسطنبول": "IST"
}

def clean_and_get_iata(city_input):
    """دالة تحول اسم المدينة بالعربي إلى كود مطار، وإذا كُتب الكود بالإنجليزي تتركه كما هو"""
    city = city_input.strip()
    # البحث في القاموس، إذا لم يجد الاسم، يحول النص لحروف إنجليزية كبيرة
    return CITY_TO_IATA.get(city, city.upper())

# ==========================================
# 🛠️ القسم الأول: الأدوات (Tools) - نسخة حقيقية بالكامل 🌐
# ==========================================

def fetch_all_flights_from_google(origin_iata, destination_iata, date_out, date_return, trip_type):
    """أداة رئيسية تتصل بـ SerpApi مرة واحدة لتجلب كل البيانات الحية"""
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
    
    if type_code == "1" and date_return:
        params["return_date"] = str(date_return)
        
    response = requests.get(url, params=params)
    return response.json()

def generate_real_google_flight_url(origin_iata, destination_iata, date_out, date_return, trip_type):
    """أداة عبقرية تولد رابط بحث حقيقي ومباشر على موقع قوقل فلايت الرسمي"""
    if trip_type == "ذهاب وعودة" and date_return:
        query = f"Flights from {origin_iata} to {destination_iata} on {date_out} returning {date_return}"
    else:
        query = f"Flights from {origin_iata} to {destination_iata} on {date_out}"
    
    encoded_query = urllib.parse.quote(query)
    return f"https://www.google.com/travel/flights?q={encoded_query}"


# ==========================================
# 🧠 القسم الثاني: المنطق (Logic)
# وظيفته الفرز الذكي للبيانات الحقيقية المستلمة
# ==========================================

def process_flight_search(origin, destination, date_out, date_return, trip_type, cabin_class):
    # 1. تحويل أسماء المدن العربية إلى أكواد مطارات
    origin_iata = clean_and_get_iata(origin)
    destination_iata = clean_and_get_iata(destination)
    
    try:
        # 2. جلب البيانات الحية لمرة واحدة
        data = fetch_all_flights_from_google(origin_iata, destination_iata, date_out, date_return, trip_type)
        
        if "error" in data:
            return [{"type": "رسالة من النظام ⚠️", "airline": data["error"], "price": 0, "duration": "0", "url": "#"}]
            
        # تجميع كل الرحلات القادمة من قوقل (الأفضل والأخرى)
        all_flights_raw = []
        if "best_flights" in data:
            all_flights_raw.extend(data["best_flights"])
        if "other_flights" in data:
            all_flights_raw.extend(data["other_flights"])
            
        if not all_flights_raw:
            return [{"type": "تنبيه ⚠️", "airline": "لا توجد رحلات متوفرة في هذا اليوم", "price": 0, "duration": "0", "url": "#"}]
            
        direct_flights = []
        transit_flights = []
        
        # 3. المنطق يقوم بفرز وتصنيف الرحلات حقيقياً
        for flight in all_flights_raw:
            airline = flight["flights"][0].get("airline", "غير معروف")
            price = flight.get("price", 0)
            duration_mins = flight.get("total_duration", 0)
            duration_hours = round(duration_mins / 60, 1)
            
            # معرفة هل الرحلة ترانزيت أم مباشرة من خلال التحقق من وجود توقفات
            is_transit = "layovers" in flight and len(flight["layovers"]) > 0
            
            flight_info = {
                "airline": airline,
                "price": price,
                "duration": f"{duration_hours} ساعة",
                "duration_mins": duration_mins,
                "type": "مباشرة (حقيقية 🌐)" if not is_transit else "ترانزيت (حقيقية 🌐)"
            }
            
            if is_transit:
                transit_flights.append(flight_info)
            else:
                direct_flights.append(flight_info)
                
        # 4. تفعيل جميع الأدوات والطلبات من القائمة الحقيقية
        results = []
        
        # أداة الرحلات المباشرة (تأخذ أفضل سعرين مباشرين)
        if direct_flights:
            results.extend(sorted(direct_flights, key=lambda x: x['price'])[:2])
            
        # أداة رحلات الترانزيت (تأخذ أفضل سعر ترانزيت)
        if transit_flights:
            results.extend(sorted(transit_flights, key=lambda x: x['price'])[:1])
            
        # أداة أقصر وقت ترانزيت (تأخذ الرحلة الأسرع في الترانزيت وتغير نوعها)
        if transit_flights:
            fastest_transit = sorted(transit_flights, key=lambda x: x['duration_mins'])[0].copy()
            fastest_transit["type"] = "ترانزيت سريع (حقيقية 🌐)"
            # نضيفها فقط إذا لم تكن هي نفسها رحلة الترانزيت الأرخص التي أضفناها سابقاً
            if fastest_transit not in results:
                results.append(fastest_transit)
                
        # ترتيب الخيارات النهائية حسب السعر واختيار أفضل 3 خيارات للمستخدم
        final_top_3 = sorted(results, key=lambda x: x['price'])[:3]
        
        # توليد روابط الحجز الحقيقية لكل رحلة
        for flight in final_top_3:
            flight["url"] = generate_real_google_flight_url(origin_iata, destination_iata, date_out, date_return, trip_type)
            
        return final_top_3
        
    except Exception as e:
        return [{"type": "خطأ تقني", "airline": f"فشل في تحليل البيانات: {e}", "price": 0, "duration": "0", "url": "#"}]


# ==========================================
# 🖥️ القسم الثالث: الواجهة (Interface)
# ==========================================

st.title("✈️ وكيل السفر الذكي المتكامل")
st.write("ابحث باللغة العربية عن أفضل الرحلات المباشرة، الترانزيت، والأسرع وقتاً بروابط حجز حقيقية.")

col1, col2 = st.columns(2)
with col1:
    origin = st.text_input("مدينة الانطلاق 🛫", placeholder="مثال: الرياض أو دبي")
    date_out = st.date_input("تاريخ الذهاب 📅")
    trip_type = st.selectbox("نوع الرحلة 🔄", ["ذهاب فقط", "ذهاب وعودة"])
with col2:
    destination = st.text_input("مدينة الوصول 🛬", placeholder="مثال: دبي أو القاهرة")
    if trip_type == "ذهاب وعودة":
        date_return = st.date_input("تاريخ العودة 📅")
    else:
        date_return = None
    cabin_class = st.selectbox("درجة الركوب 💺", ["الدرجة السياحية", "درجة الأعمال", "الدرجة الأولى"])

if st.button("ابحث عن أفضل 3 خيارات ذكية 🔍"):
    if origin and destination:
        with st.spinner("الإيجنت يترجم المدن، ويتصل بقوقل فلايت، ويحلل الخيارات الآن... ⏳"):
            final_results = process_flight_search(origin, destination, date_out, date_return, trip_type, cabin_class)
            
            st.success("🎉 إليك أفضل النتائج الحقيقية التي تم العثور عليها وتصنيفها:")
            for i, flight in enumerate(final_results, 1):
                st.subheader(f"الخيار رقم {i}: {flight['type']}")
                st.write(f"🏢 **الشركة:** {flight['airline']}")
                st.write(f"💰 **السعر:** {flight['price']} ريال")
                st.write(f"⏱️ **المدة الإجمالية:** {flight['duration']}")
                st.link_button("اضغط هنا للحجز مباشرة عبر Google Flights 🔗", flight['url'])
                st.divider()
    else:
        st.error("يرجى إدخال مدينتي الانطلاق والوصول أولاً.")
