import streamlit as st

# ==========================================
# 🛠️ القسم الأول: الأدوات (Tools)
# وظيفتها: جلب البيانات فقط (هنا نستخدم بيانات وهمية للتجربة)
# ==========================================

def get_best_direct_flights(origin, destination, date_out):
    """أداة تجلب أفضل سعرين للرحلات المباشرة"""
    return [
        {"id": "D1", "type": "مباشرة", "airline": "الخطوط السعودية", "price": 1200, "duration": "ساعتان"},
        {"id": "D2", "type": "مباشرة", "airline": "طيران ناس", "price": 1350, "duration": "ساعتان"}
    ]

def get_best_transit_flights(origin, destination, date_out):
    """أداة تجلب أفضل سعرين لرحلات الترانزيت"""
    return [
        {"id": "T1", "type": "ترانزيت", "airline": "فلاي دبي", "price": 850, "duration": "6 ساعات"},
        {"id": "T2", "type": "ترانزيت", "airline": "طيران الخليج", "price": 900, "duration": "5 ساعات"}
    ]

def get_shortest_transit_flight(origin, destination, date_out):
    """أداة تجلب الرحلة ذات أقصر وقت ترانزيت"""
    return {"id": "T3", "type": "ترانزيت سريع", "airline": "الخطوط القطرية", "price": 1500, "duration": "4 ساعات"}

def generate_google_flight_url(flight_id, origin, destination, date_out):
    """أداة تولد رابط حجز (ديناميكي) وهمي للتجربة"""
    return f"https://www.google.com/travel/flights?q={origin}-to-{destination}-on-{date_out}"


# ==========================================
# 🧠 القسم الثاني: المنطق (Logic)
# وظيفته: استلام الطلب، تشغيل الأدوات، فلترة النتائج
# ==========================================

def process_flight_search(origin, destination, date_out, date_return, trip_type, cabin_class):
    results = []
    
    # 1. تشغيل الأدوات
    direct_flights = get_best_direct_flights(origin, destination, date_out)
    transit_flights = get_best_transit_flights(origin, destination, date_out)
    fastest_transit = get_shortest_transit_flight(origin, destination, date_out)
    
    # 2. تجميع النتائج
    results.extend(direct_flights)
    results.extend(transit_flights)
    results.append(fastest_transit)
    
    # 3. اختيار أفضل 3 نتائج (نرتبها حسب السعر الأقل)
    top_3_flights = sorted(results, key=lambda x: x['price'])[:3]
    
    # 4. جلب الروابط لكل رحلة
    for flight in top_3_flights:
        url = generate_google_flight_url(flight['id'], origin, destination, date_out)
        flight['booking_url'] = url
        
    return top_3_flights


# ==========================================
# 🖥️ القسم الثالث: الواجهة (Interface)
# وظيفتها: أخذ المدخلات من المستخدم وعرض النتائج
# ==========================================

st.set_page_config(page_title="وكيل السفر الذكي", page_icon="✈️")
st.title("✈️ وكيل السفر الذكي المتقدم")
st.write("ابحث عن أفضل الرحلات المباشرة والترانزيت في مكان واحد.")

# أخذ المعلومات من المستخدم
col1, col2 = st.columns(2)
with col1:
    origin = st.text_input("مدينة الانطلاق 🛫", placeholder="مثال: الرياض")
    date_out = st.date_input("تاريخ الذهاب 📅")
    trip_type = st.selectbox("نوع الرحلة 🔄", ["ذهاب وعودة", "ذهاب فقط"])
with col2:
    destination = st.text_input("مدينة الوصول 🛬", placeholder="مثال: دبي")
    if trip_type == "ذهاب وعودة":
        date_return = st.date_input("تاريخ العودة 📅")
    else:
        date_return = None
    cabin_class = st.selectbox("درجة الركوب 💺", ["الدرجة السياحية", "درجة الأعمال", "الدرجة الأولى"])

# زر البحث
if st.button("ابحث عن أفضل 3 خيارات 🔍"):
    if origin and destination:
        with st.spinner("الإيجنت يبحث ويحلل البيانات الآن... ⏳"):
            # إرسال البيانات للمنطق
            final_results = process_flight_search(origin, destination, date_out, date_return, trip_type, cabin_class)
            
            # عرض النتائج
            st.success("🎉 تم العثور على أفضل الخيارات لك:")
            for i, flight in enumerate(final_results, 1):
                st.subheader(f"الخيار رقم {i}: {flight['type']}")
                st.write(f"🏢 **الشركة:** {flight['airline']}")
                st.write(f"💰 **السعر:** {flight['price']} ريال")
                st.write(f"⏱️ **المدة:** {flight['duration']}")
                st.link_button("احجز الآن عبر Google Flights 🔗", flight['booking_url'])
                st.divider()
    else:
        st.error("يرجى إدخال مدينتي الانطلاق والوصول.")
