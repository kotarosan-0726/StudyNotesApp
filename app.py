from flask import Flask, request, render_template_string, send_file
import os
import uuid

try:
    from pdf2docx import Converter
except ImportError:
    raise ImportError("Please install pdf2docx: pip install pdf2docx")

app = Flask(__name__)
app.secret_key = "any-string-you-like"  # You can use any string here

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>PDF to Word Converter</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; max-width: 700px; margin: 40px auto; padding: 20px; background: #f8f9fa; color: #333; }
        h1 { color: #007bff; }
        form { margin-bottom: 30px; }
        input[type="file"] { margin-bottom: 10px; }
        input[type="submit"] { padding: 10px 20px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
        input[type="submit"]:hover { background-color: #0056b3; }
        .message { margin-top: 20px; padding: 10px; background: #e2e3e5; border-radius: 4px; }
        .footer { margin-top: 40px; font-size: 13px; color: #888; text-align: center; }
    </style>
</head>
<body>
    <h1>PDF to Word Converter</h1>
    <form method="post" enctype="multipart/form-data">
        <input type="file" name="file" accept=".pdf" required>
        <br>
        <input type="submit" value="Convert to Word">
    </form>
    {% if message %}
        <div class="message">{{ message }}</div>
    {% endif %}
    <div class="footer">
        <p>For best results, use text-based PDFs. Complex layouts may not convert perfectly.<br>
        After conversion, your Word file will be downloaded automatically.</p>
    </div>
</body>
</html>
"""

def pdf_to_word(pdf_path, docx_path):
    try:
        cv = Converter(pdf_path)
        # You can tweak these options for better results if needed
        cv.convert(docx_path, start=0, end=None)
        cv.close()
    except Exception as e:
        return f"Error converting PDF: {e}"
    return None

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files.get("file")
        if file and file.filename.lower().endswith(".pdf"):
            pdf_filename = f"uploaded_{uuid.uuid4().hex}.pdf"
            docx_filename = f"converted_{uuid.uuid4().hex}.docx"
            file.save(pdf_filename)
            error = pdf_to_word(pdf_filename, docx_filename)
            os.remove(pdf_filename)
            if error:
                if os.path.exists(docx_filename):
                    os.remove(docx_filename)
                return render_template_string(HTML_TEMPLATE, message=error)
            response = send_file(docx_filename, as_attachment=True)
            # Clean up after sending
            try:
                os.remove(docx_filename)
            except Exception:
                pass
            return response
        else:
            return render_template_string(HTML_TEMPLATE, message="Please upload a valid PDF file.")
    return render_template_string(HTML_TEMPLATE, message="")

if __name__ == "__main__":
    # Use host='0.0.0.0' for external access, remove debug for production
    app.run(debug=True)