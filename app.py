from flask import Flask, request, render_template_string, session
import pdfplumber
from transformers import pipeline
import stripe

app = Flask(__name__)
app.secret_key = "your-secret-key"  # Replace with a random string
summarizer = pipeline("summarization", model="distilbart-cnn-6-6")
question_generator = pipeline("text2text-generation", model="valhalla/t5-small-qg-hl")
stripe.api_key = "your-stripe-secret-key"  # Replace with Stripe key

def extract_text_from_pdf(pdf_file):
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        if not text.strip():
            return "No text found in PDF"
        return text
    except Exception as e:
        return f"Error reading PDF: {e}"

def generate_study_notes(text):
    max_chunk_length = 300
    words = text.split()
    chunks = [" ".join(words[i:i + max_chunk_length]) for i in range(0, len(words), max_chunk_length)]
    summaries = []
    for chunk in chunks:
        if chunk.strip():
            try:
                summary = summarizer(chunk, max_length=100, min_length=20, do_sample=False)[0]["summary_text"]
                summaries.append(summary)
            except:
                summaries.append("Error summarizing chunk")
    return "\n\n".join(summaries)

def generate_flashcards(text):
    summary = generate_study_notes(text)
    try:
        questions = question_generator(summary, max_length=80, num_return_sequences=2)
        return [q["generated_text"] for q in questions]
    except:
        return ["Error generating flashcards"]

def check_usage_limit():
    if "uploads" not in session:
        session["uploads"] = 0
    if session["uploads"] >= 1 and not is_premium_user():
        return False
    session["uploads"] += 1
    return True

def is_premium_user():
    return False  # Update with Stripe logic later

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>Study Notes App</title>
<style>
    body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
    button { padding: 10px; background-color: #007bff; color: white; border: none; cursor: pointer; }
    button:hover { background-color: #0056b3; }
</style>
</head>
<body>
    <h1>Upload a PDF to Generate Study Notes and Flashcards</h1>
    <form method="post" enctype="multipart/form-data">
        <input type="file" name="file" accept=".pdf">
        <input type="submit" value="Generate">
    </form>
    <button onclick="subscribe()">Upgrade to Premium ($5/month)</button>
    {% if notes %}
        <h2>Study Notes</h2>
        <p>{{ notes | replace('\n', '<br>') }}</p>
        <h2>Flashcards</h2>
        <ul>
        {% for card in flashcards %}
            <li>{{ card }}</li>
        {% endfor %}
        </ul>
    {% endif %}
    <script>
    async function subscribe() {
        const response = await fetch('/subscribe', { method: 'POST' });
        const data = await response.json();
        window.location = data.url;
    }
    </script>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    notes = ""
    flashcards = []
    if request.method == "POST":
        if not check_usage_limit():
            return render_template_string(HTML_TEMPLATE, notes="Upgrade to premium for more uploads!", flashcards=[])
        file = request.files["file"]
        if file and file.filename.endswith(".pdf"):
            file.save("uploaded.pdf")
            text = extract_text_from_pdf("uploaded.pdf")
            if not text.startswith("Error"):
                notes = generate_study_notes(text)
                flashcards = generate_flashcards(text)
            else:
                notes = text
    return render_template_string(HTML_TEMPLATE, notes=notes, flashcards=flashcards)

@app.route("/subscribe", methods=["POST"])
def subscribe():
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price": "your-stripe-price-id",  # Replace with Stripe price ID
            "quantity": 1,
        }],
        mode="subscription",
        success_url="https://your-render-url/success",
        cancel_url="https://your-render-url/cancel",
    )
    return {"url": session.url}

if __name__ == "__main__":
    app.run(debug=True)