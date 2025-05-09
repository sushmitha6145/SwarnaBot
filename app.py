#code with all the links proper code with only chat 
from flask import Flask, request, jsonify, render_template
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.prompts import PromptTemplate
from langchain_together import Together
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains import ConversationalRetrievalChain

app = Flask(__name__)

# Set up your embeddings and vector store
embeddings = HuggingFaceEmbeddings(
    model_name="nomic-ai/nomic-embed-text-v1",
    model_kwargs={"trust_remote_code": True, "revision": "289f532e14dbbbd5a04753fa58739e9ba766f3c7"}
)
db = FAISS.load_local("swrn_vector_db", embeddings, allow_dangerous_deserialization=True)
db_retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": 4})

# Conversational template
prompt_template = """<s>[INST]You are Swrn Bot, an AI assistant specialized in providing helpful, accurate, and conversational responses related to the college.
Your responses should focus only on the college's academic programs, admissions process, tuition, campus life, faculty, and other college-related topics.
Please answer the question clearly, without referencing previous questions or answers. Provide a fresh and self-contained response.

CONTEXT: {context}
QUESTION: {question}
Please provide a detailed, conversational response:
</s>[INST]
"""
prompt = PromptTemplate(template=prompt_template, input_variables=['context', 'question'])

# LLM Setup
TOGETHER_AI_API = '488d9538dd3cfbf08816cca9ae559157f252c3daf6356eb4e10dd965ff589ddb'
llm = Together(
    model="mistralai/Mistral-7B-Instruct-v0.2",
    temperature=0.7,
    max_tokens=1024,
    together_api_key=TOGETHER_AI_API
)

# Conversational Retrieval QA
qa = ConversationalRetrievalChain.from_llm(
    llm=llm,
    memory=ConversationBufferWindowMemory(
        k=1,
        memory_key="chat_history",
        return_messages=True
    ),
    retriever=db_retriever,
    combine_docs_chain_kwargs={'prompt': prompt}
)

# Syllabus and curriculum links
SYLLABUS_LINKS = {
    "UG": {
        "R14": "https://www.swarnandhra.ac.in/swarnandhraexaminationportal/r14syllabusug.php",
        "R16": "https://www.swarnandhra.ac.in/swarnandhraexaminationportal/r16syllabusug.php",
        "R19": "https://www.swarnandhra.ac.in/swarnandhraexaminationportal/r19syllabusug.php",
        "R20": "https://www.swarnandhra.ac.in/swarnandhraexaminationportal/r20syllabusug.php",
        "R23": "https://www.swarnandhra.ac.in/r23syllabusug.php",
        "R24": "https://www.swarnandhra.ac.in/swarnandhraexaminationportal/r24syllabusug.php"
    },
    "PG": {
        "R14": "https://www.swarnandhra.ac.in/swarnandhraexaminationportal/r14syllabuspg.php",
        "R16": "https://www.swarnandhra.ac.in/swarnandhraexaminationportal/r16syllabuspg.php",
        "R19": "https://www.swarnandhra.ac.in/swarnandhraexaminationportal/r19syllabuspg.php",
        "R20": "https://www.swarnandhra.ac.in/swarnandhraexaminationportal/r20syllabuspg.php",
        "R24": "https://www.swarnandhra.ac.in/swarnandhraexaminationportal/r24syllabuspg.php"
    }
}


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    question = data.get("question", "").strip().lower()

    # Enforce the minimum word requirement for questions
    if len(question.split()) < 5:
        return jsonify({"error": "Your question must contain at least 5 words!"}), 400

    try:
        # Check for syllabus/curriculum-related keywords
        if any(keyword in question for keyword in ["syllabus", "curriculum", "subject", "subjects"]):
            # Prepare the links in table format
            syllabus_table = "<h2>All Syllabus Links (Choose according to the regulation):</h2>"
            syllabus_table += "<h3>Undergraduate (UG) Curriculum and Syllabus Links</h3><ul>"
            for reg, link in SYLLABUS_LINKS["UG"].items():
                syllabus_table += f"<li><strong>{reg}:</strong> <a href='{link}' target='_blank'>{link}</a></li>"
            syllabus_table += "</ul><h3>Postgraduate (PG) Syllabus and Curriculum Links</h3><ul>"
            for reg, link in SYLLABUS_LINKS["PG"].items():
                syllabus_table += f"<li><strong>{reg}:</strong> <a href='{link}' target='_blank'>{link}</a></li>"
            syllabus_table += "</ul>"

            syllabus_table += (
                "<br><br><strong>Click Here to Contact Us:</strong> "
                "<a href='https://www.swarnandhra.ac.in/swarnandhraexaminationportal/contactus.php' target='_blank'>"
                "Contact Us</a>"
            )
            return jsonify({"answer": syllabus_table})

        # Otherwise, use the LLM to process the question
        result = qa({"question": question})
        answer = result.get("answer", "I couldn't find an answer. Please try rephrasing your question.")
        
        # Append the Contact Us link to the answer
        answer += (
            "<br><br><strong>Click Here to Contact Us:</strong> "
            "<a href='https://www.swarnandhra.ac.in/swarnandhraexaminationportal/contactus.php' target='_blank'>"
            "Contact Us</a>"
        )

        # Add spacing for clear separation between questions
        formatted_answer = f"{answer}<br><br>-----------------------------------------<br><br>"
        return jsonify({"answer": formatted_answer})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
