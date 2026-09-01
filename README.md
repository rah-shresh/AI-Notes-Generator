# 📝 AI Notes Generator

An AI-powered web application that transforms any topic into structured, easy-to-understand study notes using Large Language Models (LLMs).

---

## 🚀 Features

- ✨ Generate high-quality notes from any topic
- 🧠 Multiple note styles:
  - Short Summary
  - Detailed Explanation
  - Exam Notes
- 💾 Save notes locally with history tracking
- 📄 Download notes as PDF
- 📋 One-click copy to clipboard
- ⚡ Fast AI responses using Groq API
- 🎨 Clean and responsive UI built with Streamlit
- ⚠️ Robust error handling and validation

---

## 🛠 Tech Stack

- **Python**
- **Streamlit**
- **Groq API (LLM)**
- **JSON (local storage)**
- **python-dotenv**

---

## 📂 Project Structure

```
ai-notes-generator/
│
├── app.py                 # Main Streamlit application
├── data/
│   └── notes_history.json # Stored notes history
│
├── utils/
│   ├── ai_helper.py       # AI API integration
│   ├── pdf_helper.py      # PDF generation logic
│   └── storage.py         # Local storage management
│
├── requirements.txt
├── .env.example
└── README.md
```

---

## ⚙️ How It Works

1. User enters a topic  
2. Selects a note style  
3. The app sends a request to the Groq LLM API  
4. AI generates structured notes in Markdown  
5. Notes are:
   - Displayed in the UI  
   - Saved locally  
   - Available for download as PDF  

---

## ▶️ Run Locally

### 1. Clone the repository
```bash
git clone https://github.com/rah-shresh/AI-Notes-Generator.git
cd AI-Notes-Generator
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Setup environment variables

Create a `.env` file and add your API key:

```env
GROQ_API_KEY=your_api_key_here
```

---

### 4. Run the application
```bash
streamlit run app.py
```

---



## 🧠 What I Learned

- Integrating LLM APIs into real-world applications  
- Managing environment variables securely  
- Handling API failures gracefully  
- Designing modular and maintainable Python code  
- Building interactive UI with Streamlit  
- Implementing local persistence using JSON  

---

## 🎯 Future Improvements

- 📚 Flashcards generation from notes  
- 🧪 Quiz generation for self-testing  
- 🌍 Multi-language support  
- ☁️ Cloud database integration  
- 🔐 User authentication system  

---

## 🤝 Contributing

Contributions are welcome! Feel free to fork this repository and submit a pull request.

---

## ⭐ Acknowledgements

- Groq for fast LLM inference  
- Streamlit for rapid UI development  
