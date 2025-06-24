import matplotlib
matplotlib.use('Agg')
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from .forms import UploadFileForm
import seaborn as sns
import docx, itertools
from wordcloud import WordCloud
import pandas as pd
import matplotlib.pyplot as plt
import io, spacy, re, unicodedata
import numpy as np
import base64, string
from collections import Counter
from datetime import datetime
from io import StringIO, BytesIO
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from .forms import *

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

nlp = spacy.load("en_core_web_sm")

def extract_text(file):
    doc = docx.Document(file)
    return "\n".join([para.text for para in doc.paragraphs if para.text.strip() != ""])

@csrf_exempt
def phrases_used_view(request):
    form = DocumentUploadForm()
    grouped_phrases_by_count = []

    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            text = extract_text(request.FILES['file'])
            word_list = text.split()
            grouped_words = []

            for group_size in range(1, 5):  # 1 to 4-word phrases
                for k in range(len(word_list) - group_size + 1):
                    group_slice = word_list[k:k + group_size]
                    phrase = " ".join(group_slice)
                    grouped_words.append(phrase)

            df = pd.DataFrame(grouped_words, columns=['phrase'])

            # Count phrase occurrences
            phrase_counts = df['phrase'].value_counts().reset_index()
            phrase_counts.columns = ['phrase', 'count']  # ✅ Explicit rename
            phrase_counts = phrase_counts[phrase_counts['count'] > 1]  # ✅ Use correct column name

            phrase_counts['number_of_words'] = phrase_counts['phrase'].apply(lambda x: len(x.split()))

            # Group and limit top 15 for each word count
            for i in range(1, 5):  # word counts from 1 to 4
                subset = phrase_counts[phrase_counts['number_of_words'] == i].copy()
                if not subset.empty:
                    grouped_phrases_by_count.append({
                        'word_count': i,
                        'phrases': subset.head(15).to_dict('records')
                    })

    return render(request, 'phrases_used.html', {
        'form': form,
        'grouped_phrases_by_count': grouped_phrases_by_count
    })


# Normalize special characters and quotes
def normalize_text(text):
    text = unicodedata.normalize("NFKD", text)
    text = text.replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'")
    text = text.replace("′", "'").replace("″", '"')  # Prime and double-prime to ASCII
    return text.strip()

def is_valid_entity(text):
    text = normalize_text(text)

    # Reject very short or non-alphabetic
    if len(text) <= 2 or not any(c.isalpha() for c in text):
        return False

    # Clean punctuation for blacklist checking
    clean_text = re.sub(r"[^\w\s]", "", text.lower())  # remove punctuation
    banned = {"nt", "n", "itt", "i", "s", "ll", "ve"}

    if clean_text in banned:
        return False

    # Filter coordinates or broken patterns
    if re.search(r"\d+[a-zA-Z]*[\s′″\"']+", text):  # like 62o 17′ 20″
        return False

    # Filter initials or single-letter followed by punctuation or quote
    if re.match(r"^[A-Z]\.\s*[\"']?$", text):
        return False

    return True

@csrf_exempt
def labels_view(request):
    form = DocumentUploadForm()
    grouped_labels = {}

    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            text = extract_text(request.FILES['file'])
            nlp.max_length = 2030000  # set max length if needed for large docs
            doc = nlp(text)

            entity_counter = Counter(
                (ent.label_, ent.text) for ent in doc.ents
                if is_valid_entity(ent.text)
            )

            # Group by entity label
            grouped_labels = {}
            for (label, ent_text), count in entity_counter.items():
                grouped_labels.setdefault(label, []).append((ent_text, count))

            # Sort entities within each group by count
            for label in grouped_labels:
                grouped_labels[label] = sorted(grouped_labels[label], key=lambda x: -x[1])

    return render(request, 'labels.html', {
        'form': form,
        'grouped_labels': grouped_labels
    })


def home(request):
    return render(request, 'home.html')

@csrf_exempt
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

@csrf_exempt
def titanic_view(request):
    if request.method == 'POST' and request.FILES['csv_file']:
        # Get the uploaded file
        uploaded_file = request.FILES['csv_file']
        
        # Read the file into a pandas DataFrame without saving to disk
        file_content = uploaded_file.read().decode('utf-8')  # Read the file in memory
        titanic_df = pd.read_csv(StringIO(file_content))  # Read it as CSV directly into a DataFrame

        # Data Processing Logic: Get the data types of the columns
        data_dtypes = titanic_df.dtypes.to_frame(name='Data Type')  # Get the data types of the columns

        # Calculate null values for each column
        null_values = titanic_df.isnull().sum()

        # Create histogram for 'Age' column, excluding null values
        fig, ax = plt.subplots(figsize=(8, 6))
        titanic_df.loc[-titanic_df.Age.isnull(), 'Age'].plot.hist(ax=ax, bins=30, color='#2577B4', edgecolor='black')
        ax.set_title('Histogram of Age (Excluding Null Values)')
        ax.set_xlabel('Age')
        ax.set_ylabel('Frequency')

        # Convert plot to PNG image and encode it in base64 for embedding in HTML
        canvas = FigureCanvas(fig)
        image_stream = io.BytesIO()
        canvas.print_png(image_stream)
        image_stream.seek(0)
        plot_data1 = base64.b64encode(image_stream.read()).decode('utf-8')
        
        # Data Processing Logic: Fill missing 'Age' values with mean Age by 'Sex'
        titanic_df['Age'] = titanic_df['Age'].fillna(titanic_df.groupby('Sex')['Age'].transform('mean'))

        # Create histogram for 'Age' column after filling missing values
        fig, ax = plt.subplots(figsize=(8, 6))
        titanic_df['Age'].hist(ax=ax, bins=30, color='#2577B4', edgecolor='black')
        ax.set_title('Histogram of Age (After Filling Missing Values with Grouped Mean by Sex)')
        ax.set_xlabel('Age')
        ax.set_ylabel('Frequency')

        # Convert plot to PNG image and encode it in base64 for embedding in HTML
        canvas = FigureCanvas(fig)
        image_stream = io.BytesIO()
        canvas.print_png(image_stream)
        image_stream.seek(0)
        plot_data2 = base64.b64encode(image_stream.read()).decode('utf-8')

        # Render to HTML
        return render(request, 'titanic.html', {
            'null_values': null_values.to_frame(name='Null Values').to_html(classes='table table-striped'),
            'data_dtypes': data_dtypes.to_html(classes='table table-striped'),  # Passing dtypes to template
            'plot_data1': plot_data1,
            'plot_data2': plot_data2,
        })
    
    return render(request, 'titanic.html')

@csrf_exempt
def heatmap_view(request):
    eda_html = None
    heatmap_image = None

    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']

        try:
            # Read uploaded Excel file into DataFrame
            df = pd.read_excel(excel_file)

            # Prepare correlation heatmap
            numeric_df = df.select_dtypes(include=['number'])
            correlation_matrix = numeric_df.corr()

            plt.figure(figsize=(10, 5))
            sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm')
            plt.title("Correlations Table")

            # Save image to memory
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight')
            buf.seek(0)
            heatmap_image = base64.b64encode(buf.read()).decode('utf-8')
            buf.close()
            plt.close()

            # Optional EDA table (describe numeric columns)
            eda_html = numeric_df.describe().to_html(classes='table table-bordered')

        except Exception as e:
            eda_html = f"<p class='text-danger'>Error processing file: {e}</p>"

    return render(request, 'heatmap.html', {
        'eda_html': eda_html,
        'heatmap_image': heatmap_image
    })

@csrf_exempt
def scatter_plots_view(request):
    scatter_plots = []

    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']
        df = pd.read_excel(excel_file)

        numeric_df = df.select_dtypes(include=['number'])
        columns = numeric_df.columns
        pairs = list(itertools.combinations(columns, 2))

        for x, y in pairs:
            plt.figure(figsize=(6, 4))
            plt.scatter(numeric_df[x], numeric_df[y], alpha=0.7)
            plt.xlabel(x)
            plt.ylabel(y)
            plt.title(f"{x} vs {y}")

            buffer = BytesIO()
            plt.savefig(buffer, format='png')
            plt.close()
            buffer.seek(0)
            image_png = buffer.getvalue()
            buffer.close()

            image_base64 = base64.b64encode(image_png).decode('utf-8')
            image_uri = f'data:image/png;base64,{image_base64}'
            scatter_plots.append(image_uri)

    return render(request, 'scatter_plots.html', {'scatter_plots': scatter_plots})

def plot_to_base64():
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    string = base64.b64encode(buf.read())
    return f'data:image/png;base64,{string.decode()}'

@csrf_exempt
def handle_excel_upload(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        df = pd.read_excel(request.FILES['excel_file'])
        numeric_df = df.select_dtypes(include='number')
        return df, numeric_df
    return None, None

@csrf_exempt
def eda_line_graphs(request):
    df, numeric_df = handle_excel_upload(request)
    images = []

    if numeric_df is not None:
        for column in numeric_df.columns:
            plt.figure()
            plt.plot(numeric_df[column], marker='o', linestyle='-')
            plt.title(f'Graph for {column}')
            plt.xlabel('Index')
            plt.ylabel(column)
            plt.grid(True)
            images.append(plot_to_base64())
            plt.close()
    return render(request, 'line_graphs.html', {'line_graphs': images})

@csrf_exempt
def eda_box_plots(request):
    df, numeric_df = handle_excel_upload(request)
    images = []

    if numeric_df is not None:
        for column in numeric_df.columns:
            plt.figure(figsize=(5, 4))
            sns.boxplot(y=numeric_df[column].dropna(), color='skyblue')
            plt.title(f'Boxplot of {column}')
            plt.ylabel('Values')
            plt.grid(True, linestyle='--', alpha=0.3)
            images.append(plot_to_base64())
            plt.close()
    return render(request, 'box_plots.html', {'box_plots': images})

@csrf_exempt
def eda_pair_plot(request):
    df, numeric_df = handle_excel_upload(request)
    image = None

    if numeric_df is not None:
        numeric_df2 = numeric_df.replace([np.inf, -np.inf], np.nan)
        numeric_df2 = numeric_df2.dropna(thresh=2)  # Only drop rows that are almost empty

        if len(numeric_df2.columns) >= 2 and not numeric_df2.empty:
            sns_plot = sns.pairplot(numeric_df2)
            fig = sns_plot.fig
            image = pair_plot_to_base64(fig)
            plt.close(fig)

    return render(request, 'pair_plot.html', {'pair_plot': image})

def pair_plot_to_base64(fig):
    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    return f"data:image/png;base64,{image_base64}"