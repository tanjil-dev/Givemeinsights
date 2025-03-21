import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from .forms import UploadFileForm
import docx
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import io
import base64


def upload_excel(request):
    form = UploadFileForm()
    return render(request, 'upload_excel.html', {'form': form})

@csrf_exempt
def upload_docx(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            docx_file = request.FILES['file']
            doc_text = extract_text_from_docx(docx_file)
            
            # Generate word cloud
            wordcloud_img = generate_wordcloud(doc_text)

            return render(request, 'upload_docx.html', {'form': form, 'wordcloud_img': wordcloud_img})
    else:
        form = UploadFileForm()
    return render(request, 'upload_docx.html', {'form': form})

def extract_text_from_docx(docx_file):
    doc = docx.Document(docx_file)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)

def generate_wordcloud(text):
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
    img_io = io.BytesIO()
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis('off')
    plt.savefig(img_io, format='png')
    img_io.seek(0)
    
    # Convert image to base64 to embed in HTML
    wordcloud_img = base64.b64encode(img_io.getvalue()).decode()
    return wordcloud_img
