import os
try:
    os.system("pip install pdfplumber flask transformers torch gunicorn stripe")
    print("Installation attempted! Check Output or Terminal for details.")
except Exception as e:
    print(f"Error during installation: {e}")