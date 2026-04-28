"""One-time script to add UI_TEXT entries for new languages to translations.py"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

NEW_LANGS = {
    "Punjabi": {
        "select_language": "ਭਾਸ਼ਾ ਚੁਣੋ", "welcome": "ਸਮਾਰਟ ATM ਵਿੱਚ ਤੁਹਾਡਾ ਸੁਆਗਤ ਹੈ! ਮੈਂ ਤੁਹਾਡੀ ਕਿਵੇਂ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ?",
        "enter_pin": "ਕਿਰਪਾ ਕਰਕੇ ਕੀਪੈਡ ਤੇ 4 ਅੰਕਾਂ ਦਾ PIN ਦਾਖਲ ਕਰੋ", "pin_correct": "PIN ਪ੍ਰਮਾਣਿਤ! ਤੁਸੀਂ ਲੌਗ ਇਨ ਹੋ।",
        "pin_incorrect": "ਗਲਤ PIN।", "pin_locked": "ਬਹੁਤ ਸਾਰੀਆਂ ਕੋਸ਼ਿਸ਼ਾਂ। ਕਿਰਪਾ ਕਰਕੇ ਉਡੀਕ ਕਰੋ।",
        "withdraw": "ਪੈਸੇ ਕਢਵਾਓ", "balance": "ਬੈਲੰਸ ਚੈੱਕ ਕਰੋ", "mini_statement": "ਮਿਨੀ ਸਟੇਟਮੈਂਟ",
        "insert_card": "ਕਾਰਡ ਪਾਓ", "help_faq": "ਮਦਦ / FAQ", "exit_session": "ਸੈਸ਼ਨ ਖਤਮ ਕਰੋ",
        "enter_amount": "ਰਕਮ ਦਰਜ ਕਰੋ:", "withdraw_success": "ਕਿਰਪਾ ਕਰਕੇ ਆਪਣੇ ਪੈਸੇ ਲਓ। {amount} ਕਢਵਾਏ ਗਏ।",
        "balance_result": "ਤੁਹਾਡਾ ਬੈਲੰਸ {balance} ਹੈ", "insufficient_funds": "ਨਾਕਾਫ਼ੀ ਬੈਲੰਸ। ਬੈਲੰਸ {balance}",
        "exceed_limit": "ਰਕਮ {limit} ਸੀਮਾ ਤੋਂ ਵੱਧ ਹੈ", "invalid_amount": "ਕਿਰਪਾ ਕਰਕੇ 100 ਦਾ ਗੁਣਾ ਦਰਜ ਕਰੋ",
        "session_timeout": "ਸੁਰੱਖਿਆ ਲਈ ਸੈਸ਼ਨ ਖਤਮ ਹੋ ਗਿਆ।", "goodbye": "ਸਮਾਰਟ ATM ਵਰਤਣ ਲਈ ਧੰਨਵਾਦ!",
        "type_message": "ਇੱਥੇ ਆਪਣਾ ਸੁਨੇਹਾ ਲਿਖੋ...", "mic_button": "🎙️ ਬੋਲੋ", "listening": "ਸੁਣ ਰਿਹਾ...",
        "collect_cash": "ਕਿਰਪਾ ਕਰਕੇ ਆਪਣੇ ਪੈਸੇ ਲਓ।", "collect_card": "ਕਿਰਪਾ ਕਰਕੇ ਆਪਣਾ ਕਾਰਡ ਲਓ।",
        "transaction_receipt": "ਲੈਣ-ਦੇਣ ਦੀ ਰਸੀਦ", "date_time": "ਮਿਤੀ ਅਤੇ ਸਮਾਂ",
        "transaction_type": "ਲੈਣ-ਦੇਣ ਦੀ ਕਿਸਮ", "amount": "ਰਕਮ", "available_balance": "ਉਪਲਬਧ ਬੈਲੰਸ",
        "ask_anything": "ATM ਸੇਵਾਵਾਂ ਬਾਰੇ ਕੁਝ ਵੀ ਪੁੱਛੋ!", "card_number": "ਕਾਰਡ ਨੰਬਰ",
        "attempts_remaining": "ਬਾਕੀ ਕੋਸ਼ਿਸ਼ਾਂ: {n}", "pin_security_note": "🔒 PIN ਸਿਰਫ਼ ਕੀਪੈਡ ਨਾਲ",
        "quick_actions": "ਤੇਜ਼ ਕਾਰਵਾਈਆਂ", "voice_input": "ਆਵਾਜ਼ ਇਨਪੁਟ", "text_input": "ਟੈਕਸਟ ਇਨਪੁਟ",
        "session_status": "ਸੈਸ਼ਨ ਸਥਿਤੀ", "no_card_status": "ਕੋਈ ਕਾਰਡ ਨਹੀਂ",
        "card_inserted_status": "ਕਾਰਡ ਪਾਇਆ ਗਿਆ", "authenticated_status": "ਪ੍ਰਮਾਣਿਤ",
        "header_subtitle": "RAG-ਸੰਚਾਲਿਤ ਬਹੁ-ਭਾਸ਼ਾਈ ਵੌਇਸ ਸਹਾਇਕ",
        "insert_card_subtitle": "ਸ਼ੁਰੂ ਕਰਨ ਲਈ ਇੱਥੇ ਟੈਪ ਕਰੋ",
        "pin_title": "🔐 PIN ਦਰਜ ਕਰੋ", "cancel": "ਰੱਦ ਕਰੋ", "speak_now": "🎤 ਹੁਣ ਬੋਲੋ...", "or_type": "ਜਾਂ ਟਾਈਪ ਕਰੋ:",
        "processing": "ਪ੍ਰੋਸੈਸ ਹੋ ਰਿਹਾ..."
    },
    "Malayalam": {
        "select_language": "ഭാഷ തിരഞ്ഞെടുക്കുക", "welcome": "സ്മാർട്ട് ATM-ലേക്ക് സ്വാഗതം!",
        "enter_pin": "കീപാഡിൽ 4 അക്ക PIN നൽകുക", "pin_correct": "PIN സ്ഥിരീകരിച്ചു!",
        "pin_incorrect": "തെറ്റായ PIN.", "pin_locked": "നിരവധി ശ്രമങ്ങൾ. കാത്തിരിക്കുക.",
        "withdraw": "പിൻവലിക്കുക", "balance": "ബാലൻസ്", "mini_statement": "മിനി സ്റ്റേറ്റ്‌മെന്റ്",
        "insert_card": "കാർഡ് ഇടുക", "help_faq": "സഹായം", "exit_session": "സെഷൻ അവസാനിപ്പിക്കുക",
        "enter_amount": "തുക നൽകുക:", "withdraw_success": "നിങ്ങളുടെ പണം എടുക്കുക. {amount} പിൻവലിച്ചു.",
        "balance_result": "നിങ്ങളുടെ ബാലൻസ് {balance}", "insufficient_funds": "അപര്യാപ്തമായ ബാലൻസ്. {balance}",
        "exceed_limit": "പരിധി {limit} കവിഞ്ഞു", "invalid_amount": "100-ന്റെ ഗുണിതം നൽകുക",
        "session_timeout": "സുരക്ഷയ്ക്കായി സെഷൻ കാലഹരണപ്പെട്ടു.", "goodbye": "നന്ദി! വിട!",
        "type_message": "സന്ദേശം ടൈപ്പ് ചെയ്യുക...", "mic_button": "🎙️ സംസാരിക്കുക", "listening": "കേൾക്കുന്നു...",
        "collect_cash": "പണം എടുക്കുക.", "transaction_receipt": "രസീത്", "amount": "തുക",
        "available_balance": "ലഭ്യമായ ബാലൻസ്", "ask_anything": "ATM സേവനങ്ങളെക്കുറിച്ച് ചോദിക്കൂ!",
        "card_number": "കാർഡ് നമ്പർ", "attempts_remaining": "ശേഷിക്കുന്ന ശ്രമങ്ങൾ: {n}",
        "quick_actions": "ദ്രുത പ്രവർത്തനങ്ങൾ", "session_status": "സെഷൻ സ്ഥിതി",
        "no_card_status": "കാർഡ് ഇല്ല", "card_inserted_status": "കാർഡ് ഇട്ടു", "authenticated_status": "സ്ഥിരീകരിച്ചു",
        "cancel": "റദ്ദാക്കുക", "pin_title": "🔐 PIN നൽകുക",
    },
    "Kannada": {
        "select_language": "ಭಾಷೆ ಆರಿಸಿ", "welcome": "ಸ್ಮಾರ್ಟ್ ATM ಗೆ ಸ್ವಾಗತ!",
        "enter_pin": "ಕೀಪ್ಯಾಡ್‌ನಲ್ಲಿ 4 ಅಂಕಿ PIN ನಮೂದಿಸಿ", "pin_correct": "PIN ಪರಿಶೀಲಿಸಲಾಗಿದೆ!",
        "pin_incorrect": "ತಪ್ಪು PIN.", "pin_locked": "ಹಲವು ಪ್ರಯತ್ನಗಳು. ದಯವಿಟ್ಟು ನಿರೀಕ್ಷಿಸಿ.",
        "withdraw": "ಹಿಂಪಡೆಯಿರಿ", "balance": "ಬ್ಯಾಲೆನ್ಸ್", "mini_statement": "ಮಿನಿ ಸ್ಟೇಟ್‌ಮೆಂಟ್",
        "insert_card": "ಕಾರ್ಡ್ ಹಾಕಿ", "help_faq": "ಸಹಾಯ", "exit_session": "ಸೆಶನ್ ಕೊನೆಗೊಳಿಸಿ",
        "enter_amount": "ಮೊತ್ತ ನಮೂದಿಸಿ:", "withdraw_success": "{amount} ಹಿಂಪಡೆಯಲಾಗಿದೆ.",
        "balance_result": "ನಿಮ್ಮ ಬ್ಯಾಲೆನ್ಸ್ {balance}", "insufficient_funds": "ಸಾಕಷ್ಟು ಬ್ಯಾಲೆನ್ಸ್ ಇಲ್ಲ. {balance}",
        "session_timeout": "ಸೆಶನ್ ಸಮಯ ಮೀರಿದೆ.", "goodbye": "ಧನ್ಯವಾದ! ವಿದಾಯ!",
        "ask_anything": "ATM ಸೇವೆಗಳ ಬಗ್ಗೆ ಕೇಳಿ!", "card_number": "ಕಾರ್ಡ್ ಸಂಖ್ಯೆ",
        "quick_actions": "ತ್ವರಿತ ಕ್ರಿಯೆಗಳು", "session_status": "ಸೆಶನ್ ಸ್ಥಿತಿ",
        "no_card_status": "ಕಾರ್ಡ್ ಇಲ್ಲ", "card_inserted_status": "ಕಾರ್ಡ್ ಹಾಕಲಾಗಿದೆ",
        "cancel": "ರದ್ದುಗೊಳಿಸಿ", "pin_title": "🔐 PIN ನಮೂದಿಸಿ",
    },
    "Odia": {
        "select_language": "ଭାଷା ବାଛନ୍ତୁ", "welcome": "ସ୍ମାର୍ଟ ATM ରେ ସ୍ୱାଗତ!",
        "enter_pin": "କୀପ୍ୟାଡରେ 4 ଅଙ୍କ PIN ଦିଅନ୍ତୁ", "pin_correct": "PIN ଯାଞ୍ଚ ହୋଇଛି!",
        "pin_incorrect": "ଭୁଲ PIN.", "withdraw": "ଉଠାନ୍ତୁ", "balance": "ବ୍ୟାଲେନ୍ସ",
        "mini_statement": "ମିନି ଷ୍ଟେଟମେଣ୍ଟ", "insert_card": "କାର୍ଡ ପକାନ୍ତୁ",
        "exit_session": "ସେସନ ଶେଷ", "goodbye": "ଧନ୍ୟବାଦ! ବିଦାୟ!",
        "ask_anything": "ATM ସେବା ବିଷୟରେ ପଚାରନ୍ତୁ!", "cancel": "ବାତିଲ",
        "session_status": "ସେସନ ସ୍ଥିତି", "no_card_status": "କାର୍ଡ ନାହିଁ",
        "card_inserted_status": "କାର୍ଡ ପକାଯାଇଛି", "pin_title": "🔐 PIN ଦିଅନ୍ତୁ",
    },
    "Nepali": {
        "select_language": "भाषा छान्नुहोस्", "welcome": "स्मार्ट ATM मा स्वागत छ!",
        "enter_pin": "कीप्याडमा 4 अंकको PIN हाल्नुहोस्", "pin_correct": "PIN प्रमाणित!",
        "pin_incorrect": "गलत PIN.", "withdraw": "निकाल्नुहोस्", "balance": "ब्यालेन्स",
        "mini_statement": "मिनी स्टेटमेन्ट", "insert_card": "कार्ड हाल्नुहोस्",
        "exit_session": "सत्र अन्त्य", "goodbye": "धन्यवाद! बिदा!",
        "ask_anything": "ATM सेवाहरू बारे सोध्नुहोस्!", "cancel": "रद्द",
        "session_status": "सत्र स्थिति", "no_card_status": "कार्ड छैन",
        "card_inserted_status": "कार्ड हालियो", "pin_title": "🔐 PIN हाल्नुहोस्",
    },
    "Assamese": {
        "select_language": "ভাষা বাছক", "welcome": "স্মাৰ্ট ATM লৈ স্বাগতম!",
        "enter_pin": "কীপেডত 4 সংখ্যাৰ PIN দিয়ক", "pin_correct": "PIN সত্যাপিত!",
        "pin_incorrect": "ভুল PIN.", "withdraw": "উলিয়াওক", "balance": "বেলেঞ্চ",
        "mini_statement": "মিনি ষ্টেটমেণ্ট", "insert_card": "কাৰ্ড সুমুৱাওক",
        "exit_session": "চেচন শেষ", "goodbye": "ধন্যবাদ! বিদায়!",
        "ask_anything": "ATM সেৱাৰ বিষয়ে সুধিব পাৰে!", "cancel": "বাতিল",
        "session_status": "চেচন স্থিতি", "no_card_status": "কাৰ্ড নাই",
        "card_inserted_status": "কাৰ্ড সুমুৱাই দিয়া হৈছে", "pin_title": "🔐 PIN দিয়ক",
    },
    "Konkani": {
        "select_language": "भास निवडात", "welcome": "स्मार्ट ATM चेर येवकार!",
        "enter_pin": "कीपॅडाचेर 4 अंकी PIN घालात", "pin_correct": "PIN तपासलो!",
        "pin_incorrect": "चुकीचो PIN.", "withdraw": "काडात", "balance": "बॅलन्स",
        "mini_statement": "मिनी स्टेटमेंट", "insert_card": "कार्ड घालात",
        "exit_session": "सत्र सोंपयात", "goodbye": "देव बरें करूं! उपकार!",
        "ask_anything": "ATM सेवां विशीं विचारात!", "cancel": "रद्द करात",
        "session_status": "सत्र स्थिती", "no_card_status": "कार्ड ना",
        "card_inserted_status": "कार्ड घाललां", "pin_title": "🔐 PIN घालात",
    },
    "Kashmiri": {
        "select_language": "زبان چُنِو", "welcome": "!سمارٹ ATM مَنٛز خوش آمدید",
        "enter_pin": "کیپیڈ پیٹھ 4 ہندسہٕ PIN ٹایپ کرِو", "pin_correct": "!PIN درست",
        "pin_incorrect": ".PIN غلط", "withdraw": "رقم کھسِو", "balance": "بیلنس",
        "insert_card": "کارڈ ہیرِو", "exit_session": "سیشن بند", "goodbye": "!شکریہ! خدا حافظ",
        "cancel": "منسوخ", "session_status": "سیشن حالت", "no_card_status": "کارڈ نیٚ",
        "card_inserted_status": "کارڈ ہیٚریتھ", "pin_title": "🔐 PIN ٹایپ کرِو",
    },
    "Manipuri": {
        "select_language": "লোন খনবীয়ু", "welcome": "Smart ATM দা তরাম্না ওকচিল্লি!",
        "enter_pin": "কীপেদতা 4 মশিং PIN থাবীয়ু", "pin_correct": "PIN ফংখ্রে!",
        "pin_incorrect": "PIN অচুম্বা নত্তে.", "withdraw": "লৌথোকউ", "balance": "ব্যালেন্স",
        "insert_card": "কার্ড থাবীয়ু", "exit_session": "সেশন লোয়শিন্নবা",
        "goodbye": "থাগৎচরি! নুংশিরবশিং!", "cancel": "মুৎথৎ",
        "session_status": "সেশন ফিভম", "no_card_status": "কার্ড লৈতবা",
        "card_inserted_status": "কার্ড থাখ্রে", "pin_title": "🔐 PIN থাবীয়ু",
    },
}
# Ao, Nissi, Khasi, Ladakhi use English fallback (no standard digital script)

# Read current file
with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src', 'translations.py'), 'r', encoding='utf-8') as f:
    content = f.read()

# Build insertion text
insertion = ""
for lang, texts in NEW_LANGS.items():
    insertion += f'    "{lang}": {{\n'
    for k, v in texts.items():
        insertion += f'        "{k}": "{v}",\n'
    insertion += '    },\n'

# Insert before the closing }
marker = '    },\n}\n\n\ndef get_text'
content = content.replace(marker, '    },\n' + insertion + '}\n\n\ndef get_text')

with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src', 'translations.py'), 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Added {len(NEW_LANGS)} language UI_TEXT entries. Ao/Nissi/Khasi/Ladakhi use English fallback.")
