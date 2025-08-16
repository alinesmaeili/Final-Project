# Eureka Health Assistant 🧠🏥  
An AI-powered, modular healthcare assistant designed to enhance accessibility, streamline hospital operations, and support intelligent symptom analysis.

## Overview  
Eureka Health Assistant is a multi-component digital health project developed for educational and practical use in clinical and low-resource settings. It integrates three core modules:

1. **Voice Assistant** – Enables natural interaction via speech for health queries and basic commands.  
2. **Hospital Management System** – Facilitates patient, doctor, and appointment management using Excel-based data storage.  
3. **Symptom Checker** – Leverages language models and semantic search to analyze user symptoms and generate structured diagnostic insights.

---

## Project Goals  
- Improve access to medical information for elderly, low-literacy, and visually impaired users.  
- Provide lightweight hospital management tools for small clinics and underserved regions.  
- Support medical education through AI-assisted symptom analysis and decision-making.  
- Demonstrate practical integration of NLP, voice processing, and structured data management in healthcare.

---

## Real-World Use Cases  
- Rural clinics with limited infrastructure  
- Psychological counseling centers for initial triage  
- Health apps for elderly populations  
- Medical education and student training  
- Remote or underserved healthcare environments

---

## Technologies Used  

### `VA.docx` – Voice Assistant  
- `pyttsx3` – Text-to-speech  
- `speech_recognition` – Speech-to-text  
- `datetime` – Time-based greetings  
- `webbrowser` – Web navigation  
- `requests` – API calls to MyHealthFinder

### `main.docx` – Hospital Management System  
- `ReadHospitalExcel_Sheet` / `WriteHospitalExcel_Sheet` – Excel I/O  
- No external dependencies; fully Python-native

### `symptom_checker.docx` – Symptom Analysis  
- `openai`, `chromadb`, `rank_bm25`, `pypdf`, `dotenv`, `requests`, `json`, `os`, `re`, `typing`, `time`, `random`  
- Combines GPT-based reasoning with semantic and keyword search

---

## Strengths  
- Multimodal interaction (voice + text)  
- Modular and scalable architecture  
- Educational and clinical relevance  
- Simple deployment using Excel and local APIs  
- Designed for inclusivity and low-resource adaptability

---

## Limitations  
- Requires internet for API-based modules  
- Text-based interface may limit usability for non-technical users  
- Basic authentication and limited data scalability  
- Voice assistant handles only simple commands  
- Not suitable for high-risk clinical decision-making without supervision

---

## Future Development  
- GUI integration using Tkinter or PyQt  
- Migration to professional databases (e.g., SQLite, PostgreSQL)  
- Enhanced security and access control  
- Support for multi-turn conversational AI  
- Offline functionality for remote deployment

---

## Academic Context  
This project was developed as part of a university initiative in medical informatics and AI in healthcare. It demonstrates practical applications of artificial intelligence, natural language processing, and data-driven decision support in clinical environments.

---

## License  
This project is intended for academic and educational use. For clinical deployment, further validation and regulatory compliance are required.

---

## Contributors  
Developed by [Eureka AI]  
Medical Informatics Lab – [Abzums Ai]
