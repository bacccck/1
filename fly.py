import streamlit as st

# --- إعداد البيانات والأدوات ---
available_flights = ["dubai", "cairo", "london"]
nearby_alternatives = {"sharjah": "dubai", "abu dhabi": "dubai", "giza": "cairo"}

def flight_search_tool(destination):
    available_flights_data = {
        "dubai": [
            {"flight": "الخطوط السعودية", "price": 1200, "type": "مباشرة"},
            {"flight": "طيران فلاي دبي", "price": 800, "type": "ترانزيت (4 ساعات)"}
        ],
        "cairo": [
            {"flight": "مصر للطيران", "price": 1500, "type": "مباشرة"},
            {"flight": "طيران أديل", "price": 1100, "type": "ترانزيت (ساعتين)"}
        ]
    }
    return available_flights_data.get(destination.lower(), [])

# --- واجهة الموقع باستخدام Streamlit ---
st.set_page_config(page_title="مساعد السفر الذكي", page_icon="✈️")
st.title("✈️ مساعد السفر الذكي (AI Flight Agent)")
st.write("اكتب وجهتك بالإنجليزية وسيبحث الإيجنت عن الخيار الأرخص ويجهز لك رابط الحجز.")

user_request = st.text_input("أين تريد السفر؟", placeholder="مثال: i want to go to abu dhabi")

if st.button("ابحث عن الرحلات 🔍"):
    if user_request:
        detected_city = None
        words = user_request.lower().split()
        for word in words:
            if word in available_flights or word in nearby_alternatives:
                detected_city = word
                break
        
        if not detected_city:
            st.error("❌ لم يتمكن الإيجنت من تحديد المدينة.")
        else:
            if detected_city in nearby_alternatives:
                alternative = nearby_alternatives[detected_city]
                st.warning(f"⚠️ يقترح الإيجنت البحث في: {alternative}")
                destination = alternative
            else:
                destination = detected_city
            
            flights = flight_search_tool(destination)
            if flights:
                cheapest_flight = min(flights, key=lambda x: x['price'])
                
                st.subheader("📊 أفضل خيار عثر عليه الإيجنت:")
                st.metric(label="السعر الأقل", value=f"{cheapest_flight['price']} ريال")
                st.write(f"✈️ **الشركة:** {cheapest_flight['flight']}")
                st.write(f"ℹ️ **النوع:** {cheapest_flight['type']}")
                
                # --- التعديل الجديد: رابط قوقل فلايت ---
                # هذا الرابط يفتح صفحة البحث في قوقل فلايت للوجهة المختارة
                google_url = f"https://www.google.com/travel/flights?q=Flights%20to%20{destination}"
                st.link_button("احجز الآن عبر Google Flights 🔗", google_url)
            else:
                st.error("عذراً، لم نجد رحلات حالياً.")
