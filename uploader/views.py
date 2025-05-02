import matplotlib
matplotlib.use('Agg')
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from .forms import UploadFileForm
import seaborn as sns
import docx
from wordcloud import WordCloud
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64, string
from collections import Counter
from datetime import datetime

#list of common stopwords
stop_words = set([
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours", 
    "yourself", "yourselves", "he", "him", "his", "himself", "she", "her", "hers", "herself", 
    "it", "its", "itself", "they", "them", "their", "theirs", "themselves", "what", "which", 
    "who", "whom", "this", "that", "these", "those", "am", "is", "are", "was", "were", 
    "be", "been", "being", "have", "has", "had", "having", "do", "does", "did", "doing", "a", 
    "an", "the", "and", "but", "if", "or", "because", "as", "until", "while", "of", "at", 
    "by", "for", "with", "about", "against", "between", "into", "through", "during", 
    "before", "after", "above", "below", "to", "from", "up", "down", "in", "out", 
    "on", "off", "over", "under", "again", "further", "then", "once", "here", "there", 
    "when", "where", "why", "how", "all", "any", "both", "each", "few", "more", "most", 
    "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than", 
    "too", "very", "s", "t", "can", "will", "just", "don", "should", "now", "d", "ll", 
    "m", "o", "re", "ve", "y", "ain", "aren", "couldn", "didn", "doesn", "hadn", 
    "hasn", "haven", "isn", "ma", "mightn", "mustn", "needn", "shan", "shouldn", 
    "wasn", "weren", "won", "wouldn", "like"
])

def upload_excel(request):
    form = UploadFileForm()
    return render(request, 'upload_excel.html', {'form': form})


@csrf_exempt
def upload_docx(request):
    start_time = datetime.now()
    error_message = None
    full_wordcloud_img = None
    top_wordcloud_img = None
    time_taken = None

    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            docx_file = request.FILES['file']

            if not docx_file.name.endswith('.docx'):
                error_message = "Invalid file type. Please upload a .docx file."
            else:
                doc_text = extract_text_from_docx(docx_file)
                full_wordcloud_img, top_wordcloud_img, time_taken = generate_wordcloud(doc_text, start_time)
    else:
        form = UploadFileForm()
    end_time = datetime.now()
    return render(request, 'word_cloud.html', {
        'form': form,
        'full_wordcloud_img': full_wordcloud_img,
        'top_wordcloud_img': top_wordcloud_img,
        'error_message': error_message,
        'time_taken': time_taken,
        'start_time': start_time,
        'end_time': end_time,
    })


def extract_text_from_docx(docx_file):
    doc = docx.Document(docx_file)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)

def generate_wordcloud(text, start_time):
    # Convert text to lowercase and remove punctuation
    text = text.lower()
    translator = str.maketrans('', '', string.punctuation)
    text = text.translate(translator)
    
    # Tokenize the text and remove stopwords manually
    word_tokens = text.split()
    
    # Remove stopwords from the word tokens
    filtered_words = [word for word in word_tokens if word not in stop_words]

    # Count word frequencies
    word_counts = Counter(filtered_words)
    
    # Get the top 10 most common words
    top_10_words = word_counts.most_common(10)
    
    # Prepare the text for the top 10 words word cloud
    top_10_words_text = ' '.join([word[0] for word in top_10_words])
    
    # Generate the full word cloud from filtered words (after removing stopwords)
    full_wordcloud = WordCloud(width=800, height=400, background_color='white', max_words=200).generate(' '.join(filtered_words))
    
    # Generate the top 10 word cloud
    top_wordcloud = WordCloud(width=800, height=400, background_color='white', max_words=10, min_font_size=20).generate(top_10_words_text)
    
    # Save the full word cloud image to a BytesIO object
    full_img_io = io.BytesIO()
    plt.figure(figsize=(10, 5))
    plt.imshow(full_wordcloud, interpolation="bilinear")
    plt.axis('off')
    plt.savefig(full_img_io, format='png')
    full_img_io.seek(0)
    
    # Save the top 10 word cloud image to a BytesIO object
    top_img_io = io.BytesIO()
    plt.figure(figsize=(10, 5))
    plt.imshow(top_wordcloud, interpolation="bilinear")
    plt.axis('off')
    plt.savefig(top_img_io, format='png')
    top_img_io.seek(0)
    
    # Convert images to base64 to embed in HTML
    full_wordcloud_img = base64.b64encode(full_img_io.getvalue()).decode()
    top_wordcloud_img = base64.b64encode(top_img_io.getvalue()).decode()
    
    #calculate total time taken        
    end_time = datetime.now()    
    total_seconds = (end_time - start_time).total_seconds()    
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    time_taken = f"{int(minutes)} minutes and {int(seconds)} seconds"
    return full_wordcloud_img, top_wordcloud_img, time_taken



# Helper function to process the CSV and generate both the boxplot and time series plot
def process_csv_and_generate_plots(csv_file, start_time):
    # Load the CSV file into a DataFrame
    df = pd.read_csv(csv_file, parse_dates=['date'])
    
    # Drop unnecessary columns (store, item)
    df_sales_only = df.drop(['store', 'item'], axis=1)

    # Extract day, month, year, and dayofweek from the 'date' column
    df_sales_only['day'] = df_sales_only['date'].dt.day
    df_sales_only['month'] = df_sales_only['date'].dt.month
    df_sales_only['year'] = df_sales_only['date'].dt.year
    df_sales_only['dayofweek'] = df_sales_only['date'].dt.dayofweek
    day_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2']

    
    # Boxplot for sales by day of the week
    plt.figure(figsize=(10, 6))
    sns.boxplot(x='dayofweek', y='sales', data=df_sales_only, palette=day_colors)
    plt.title('Sales Distribution by Day of the Week')
    plt.xlabel('Day of the Week')
    plt.ylabel('Sales')
    plt.xticks(ticks=range(7), labels=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'])

    # Save the boxplot to a BytesIO object and convert to base64
    img_io = io.BytesIO()
    plt.savefig(img_io, format='png')
    img_io.seek(0)
    boxplot_img = base64.b64encode(img_io.getvalue()).decode()

    # Time Series Plot for sales by store and item (filtering for store == 1 and item == 1)
    store_item_df = df[(df['store'] == 1) & (df['item'] == 1)]
    
    plt.figure(figsize=(10, 6))
    store_item_df.set_index('date')['sales'].plot()
    plt.title('Sales Time Series for Store 1, Item 1')
    plt.xlabel('Date')
    plt.ylabel('Sales')

    # Save the time series plot to a BytesIO object and convert to base64
    ts_img_io = io.BytesIO()
    plt.savefig(ts_img_io, format='png')
    ts_img_io.seek(0)
    ts_img = base64.b64encode(ts_img_io.getvalue()).decode()

    #calculate total time taken        
    end_time = datetime.now()    
    total_seconds = (end_time - start_time).total_seconds()    
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    time_taken = f"{int(minutes)} minutes and {int(seconds)} seconds"
    return boxplot_img, ts_img, time_taken

@csrf_exempt
def upload_csv(request):
    start_time = datetime.now()
    error_message = None
    boxplot_img = None
    ts_img = None
    time_taken = None

    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['file']
        
            # Check if the uploaded file is a CSV
            if not csv_file.name.endswith('.csv'):
                error_message = "Invalid file type. Please upload a .csv file."
            else:
                # Process the CSV file and generate both plots
                boxplot_img, ts_img, time_taken = process_csv_and_generate_plots(csv_file=csv_file, start_time=start_time)

    else:
        form = UploadFileForm()
    end_time = datetime.now()
    return render(request, 'upload_csv.html', {
        'form': form,
        'boxplot_img': boxplot_img,
        'ts_img': ts_img,
        'error_message': error_message,
        'time_taken': time_taken,
        'start_time': start_time,
        'end_time': end_time,
    })