import streamlit as st
import requests

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
# 🛠️ القسم الأول: الأدوات (Tools)
# ==========================================

def get_best_direct_flights(origin, destination, date_out):
    """أداة تتصل بـ SerpApi لجلب أسعار حقيقية من قوقل فلايت 🌐 مع خاصية اكتشاف الأخطاء"""
    url = "https://serpapi.com/search"
    params = {
        "engine": "google_flights",
        "departure_id": origin,      
        "arrival_id": destination,   
        "outbound_date": str(date_out), 
        "currency": "SAR",           
        "hl": "ar", 
        "api_key": SERPAPI_KEY       
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        real_flights = []
        
        # 1. إذا وجد رحلات حقيقية
        if "best_flights" in data:
            for flight in data["best_flights"][:2]: # نأخذ أفضل نتيجتين
                airline = flight["flights"][0].get("airline", "غير معروف")
                price = flight.get("price", 0)
                duration_mins = flight.get("total_duration", 0)
                duration_hours = round(duration_mins / 60, 1)
                
                real_flights.append({
                    "id": flight.get("departure_token", "N/A"),
                    "type": "مباشرة (حقيقية 🌐)",
                    "airline": airline,
                    "price": price,
                    "duration": f"{duration_hours} ساعة"
                })
            return real_flights
            
        # 2. إذا رفض SerpApi المفتاح أو أرسل خطأ
        elif "error" in data:
            return [{"id": "Error", "type": "رسالة من SerpApi ⚠️", "airline": data["error"], "price": 0, "duration": "0"}]
            
        # 3. إذا لم يجد رحلات في هذا اليوم
        else:
            return [{"id": "Empty", "type": "تنبيه ⚠️", "airline": "لا توجد رحلات مباشرة في هذا اليوم", "price": 0, "duration": "0"}]
            
    except Exception as e:
        return [{"id": "Error", "type": "خطأ تقني", "airline": f"فشل الاتصال: {e}", "price": 0, "duration": "0"}]

# أداة وهمية مؤقتاً
def get_best_transit_flights(origin, destination, date_out):
    return [
        {"id": "T1", "type": "ترانزيت (وهمي)", "airline": "فلاي دبي", "price": 850, "duration": "6 ساعات"}
    ]

# أداة وهمية مؤقتاً
def get_shortest_transit_flight(origin, destination, date_out):
    return {"id": "T3", "type": "ترانزيت سريع (وهمي)", "airline": "الخطوط القطرية", "price": 1500, "duration": "4 ساعات"}

# أداة توليد رابط وهمي مؤقتاً
def generate_google_flight_url(flight_id, origin, destination, date_out):
    return f"https://www.google.com/travel/flights"


# ==========================================
# 🧠 القسم الثاني: المنطق (Logic)
# ==========================================

def process_flight_search(origin, destination, date_out, date_return, trip_type, cabin_class):
    results = []
    
    # 1. استدعاء الأدوات
    direct_flights = get_best_direct_flights(origin, destination, date_out)
    transit_flights = get_best_transit_flights(origin, destination, date_out)
    fastest_transit = get_shortest_transit_flight(origin, destination, date_out)
    
    # 2. تجميع النتائج
    results.extend(direct_flights)
    results.extend(transit_flights)
    results.append(fastest_transit)
    
    # 3. اختيار أفضل 3 نتائج
    top_3_flights = sorted(results, key=lambda x: x['price'])[:3]
    
    # 4. توليد الروابط
    for flight in top_3_flights:
        url = generate_google_flight_url(flight['id'], origin, destination, date_out)
        flight['booking_url'] = url
        
    return top_3_flights


# ==========================================
# 🖥️ القسم الثالث: الواجهة (Interface)
# ==========================================

st.title("✈️ وكيل السفر الذكي المتقدم")
st.write("ابحث عن أفضل الرحلات المباشرة والترانزيت في مكان واحد.")

st.info("💡 **تلميح:** يرجى استخدام أكواد المطارات العالمية. مثال: **RUH** للرياض، **DXB** لدبي، **JED** لجدة، **CAI** للقاهرة.")

col1, col2 = st.columns(2)
with col1:
    origin = st.text_input("كود مطار الانطلاق 🛫", placeholder="مثال: RUH")
    date_out = st.date_input("تاريخ الذهاب 📅")
    trip_type = st.selectbox("نوع الرحلة 🔄", ["ذهاب وعودة", "ذهاب فقط"])
with col2:
    destination = st.text_input("كود مطار الوصول 🛬", placeholder="مثال: DXB")
    if trip_type == "ذهاب وعودة":
        date_return = st.date_input("تاريخ العودة 📅")
    else:
        date_return = None
    cabin_class = st.selectbox("درجة الركوب 💺", ["الدرجة السياحية", "درجة الأعمال", "الدرجة الأولى"])

if st.button("ابحث عن أفضل 3 خيارات 🔍"):
    if origin and destination:
        with st.spinner("الإيجنت يبحث في قوقل فلايت ويحلل البيانات الآن... ⏳"):
            final_results = process_flight_search(origin, destination, date_out, date_return, trip_type, cabin_class)
            
            st.success("🎉 تم العثور على أفضل الخيارات لك:")
            for i, flight in enumerate(final_results, 1):
                st.subheader(f"الخيار رقم {i}: {flight['type']}")
                st.write(f"🏢 **الشركة:** {flight['airline']}")
                st.write(f"💰 **السعر:** {flight['
