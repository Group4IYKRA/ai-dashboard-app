import dash
from dash import dcc, html, Input, Output, callback, State
import plotly.express as px
from dash.dependencies import Input, Output
import openai
import os
import pandas as pd
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
load_dotenv(env_path)

openai.api_key = os.getenv("OPENAI_API_KEY")

def chatbox():
    return html.Div([
        # Area chat dengan scroll
        html.H1("CHATBOT FOR INVENTORY OPTIMIZATION"),
        #dcc.Store(id="chat-history", storage_type="session"),
        dcc.Store(id="chat-history", data=[]),
        dcc.Loading(
            id='loading-chat',
            type='circle',
            children=[
                html.Div(id='chat-box', style={
                    'height': '650px', 'overflowY': 'scroll', 'border': '1px solid #ddd', 'padding': '10px', 'borderRadius': '10px',
                    'backgroundColor': '#f9f9f9', 'marginBottom': '20px'
                })
            ]
        ),

        # Input text untuk pesan
        dcc.Input(id='user-input', type='text', placeholder='Write message...', style={
            'width': '80%', 'padding': '10px', 'borderRadius': '5px', 'border': '1px solid #ddd', 'marginRight': '10px'
        }),

        # Tombol kirim pesan
        html.Button('Send', id='send-button', n_clicks=0, style={
            'padding': '10px 20px', 'backgroundColor': '#007bff', 'border': 'none', 'color': 'white', 'borderRadius': '5px'
        }),
    ], style={'width': '1200px', 'margin': '0 auto', 'padding': '10px', 'border': '1px solid #ddd', 'borderRadius': '10px', 'fontFamily': 'Helvetica', 'marginTop': '10px'})

# callback untuk chatbot
@callback(
    [Output('chat-box', 'children'), Output('chat-history', 'data')],
    [Input('send-button', 'n_clicks')],
    [State('user-input', 'value'), State('chat-history', 'data')],
    prevent_initial_call=True
    )
def update_chatbot_output(n_clicks, user_input, chat_history):
    if not user_input:
        return dash.no_update, chat_history

    # Jika tidak ada, inisialisasi sebagai list kosong
    if chat_history is None:
        chat_history = []
    
        # Pesan dari pengguna
    user_message = {
        "role": "user",
        "content": user_input,
        "style":{
            'backgroundColor': '#007bff', 'color': 'white', 'padding': '8px', 'borderRadius': '10px', 'marginBottom': '5px',
            'alignSelf': 'flex-end', 'maxWidth': '80%', 'margin-left': 'auto', 'fontFamily': 'Helvetica', 'width' : 'fit-content', 'margin-right': '20px'
        }
    }

    # Menggunakan OpenAI untuk chatbot (menggunakan GPT-3 atau GPT-4)
    # 1. Load and preprocess data
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    chatbot_table_file = os.path.join(project_root, "data/query_result/chatbot_table_data.pkl")
    data = pd.read_pickle(chatbot_table_file)

    # Select relevant columns for embedding
    data['combined_text'] = data['Category'] + ' ' + data['Brand'] + ' ' + data['Seasonality']

    # 2. Generate embeddings
    model = SentenceTransformer('all-MiniLM-L6-v2')  # Load a pre-trained embedding model
    embeddings = model.encode(data['combined_text'].tolist())

    # 3. Initialize FAISS index
    embedding_dim = embeddings.shape[1]
    faiss_index = faiss.IndexFlatL2(embedding_dim)
    faiss_index.add(np.array(embeddings))

    # 4. Retrieval function
    def retrieve(user_input, top_k=5):
        """Retrieve the top_k most relevant entries based on the query."""
        query_embedding = model.encode([user_input])
        distances, indices = faiss_index.search(np.array(query_embedding), top_k)
        results = data.iloc[indices[0]]
        return results

    df = retrieve(user_input, top_k=3)

    # Generate insights
    insights = []

    # Basic DataFrame Information
    insights.append(
        f"The DataFrame contains {len(df)} rows and {len(df.columns)} columns."
    )
    insights.append("Here are the first 5 rows of the DataFrame:\n")
    insights.append(df.head().to_string(index=False))

    # Summary Statistics
    insights.append("\nSummary Statistics:")
    insights.append(df.describe().to_string())

    # Column Information
    insights.append("\nColumn Information:")
    for col in df.columns:
        insights.append(f"- Column '{col}' has {df[col].nunique()} unique values.")

    # Missing Values
    missing_values = df.isnull().sum()
    insights.append("\nMissing Values:")
    for col, count in missing_values.items():
        if count > 0:
            insights.append(f"- Column '{col}' has {count} missing values.")

    # Most Common Values in Categorical Columns
    categorical_columns = df.select_dtypes(include=["object"]).columns
    for col in categorical_columns:
        top_value = df[col].mode().iloc[0]
        insights.append(f"\nMost common value in '{col}' column: {top_value}")

    insights_text = "\n".join(insights)

    prompt = (
        "Objective: Provide insights for inventory optimization."
        "Instructions: You will be given a dataset containing inventory information from a company, including product data, stock levels, demand rates, lead times, and other relevant data. Your task is to provide insights that can help optimize the company's inventory management. The insights should be based on the available data and aim to improve efficiency, reduce waste, and ensure optimal stock levels."
        "Possible areas to explore:"
        "1.Identify Overstocked and Understocked Products: Find products that are overstocked or understocked and recommend adjustments in ordering or stock management."
        "2.Demand Forecasting: Use historical data to predict future demand and recommend changes in procurement strategies."
        "3.Inventory Turnover Analysis: Identify products with slow turnover rates and provide suggestions to increase sales or reduce order quantities."
        "4.Lead Time Optimization: Analyze the lead time for specific products and recommend when to reorder to ensure stock availability without overstocking."
        "5.Storage Space Management: Provide suggestions on how to optimize storage space usage based on inventory data."
        "6.Cost Analysis: Identify high-cost products that are not moving or selling well, and suggest ways to reduce storage costs or find alternative suppliers."
        "Provide data-driven insights to improve inventory management, making it more efficient and cost-effective. Ensure that the recommendations align with the goal of optimization and cost savings for the company."
        #"In addition to the insights, generate visualizations that help better understand and communicate the data."
    )
    prompt = f"{prompt}\n\nContext:\n\n{insights_text}"
    prompt = f"""{prompt}\n\nUser's Question: {user_input}"""

    response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}]
    )
    bot_response = response.choices[0].message.content  # Mengembalikan respons dari chatbot
    bot_message = {
        "role": "bot",
        "content": bot_response,
        "style":{
            'backgroundColor': '#f1f1f1', 'color': 'black', 'padding': '8px', 'borderRadius': '10px', 'marginBottom': '5px',
            'alignSelf': 'flex-start', 'maxWidth': '80%', 'margin-right': 'auto', 'whiteSpace': 'pre-wrap', 'fontFamily': 'Helvetica', 'textAlign': 'left', 'margin-left': '20px'
        }
    }
    # Perbarui chat_history
    chat_history.append(user_message)
    chat_history.append(bot_message)

    chat_elements = [
        html.Div(message["content"], style=message["style"])
        for message in chat_history
    ]

    return chat_elements, chat_history