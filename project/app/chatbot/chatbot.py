import dash
from dash import dcc, html, Input, Output, callback, State, clientside_callback, Dash
import pandas as pd
import plotly.express as px
from dash.dependencies import Input, Output
import openai
import os
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import random
from dotenv import load_dotenv
from dash_socketio import DashSocketIO
import time
from flask_socketio import SocketIO, emit
import dash_bootstrap_components as dbc

# Load environment variables
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

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
#faiss_index.add(np.array(embeddings))
faiss_index.add(embeddings.astype('float32'))
global_chat_histories=[]

# 4. Retrieval function
def retrieve(user_input, top_k=5):
    """Retrieve the top_k most relevant entries based on the query."""
    query_embedding = model.encode([user_input])
    #distances, indices = faiss_index.search(np.array(query_embedding), top_k)
    distances, indices = faiss_index.search(query_embedding.astype('float32'), top_k)
    results = data.iloc[indices[0]]
    return results

def chatbox():
    return dbc.Container([
        # Area chat dengan scroll
        html.Div([
            html.H2("Chatbot"),
        ], style={
            'backgroundColor': '#007BFF',
            'border': '1px solid #ddd', 
            'borderRadius': '10px',
            'color': 'white',
            'textAlign': 'center'}
            ),
        #dcc.Store(id="chat-history", storage_type="session"),
        dcc.Store(id="chat-history", data=global_chat_histories),
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Div(id='chat-box'),
                    html.Div(id="streaming-process", style={
                                                        'backgroundColor': '#f1f1f1', 'color': 'black', 'padding': '8px', 'borderRadius': '10px', 'marginBottom': '5px',
                                                        'alignSelf': 'flex-start', 'maxWidth': '80%', 'margin-right': 'auto', 'whiteSpace': 'pre-wrap', 'fontFamily': 'Helvetica', 
                                                        'textAlign': 'left', 'margin-left': '5px'}),
                ], style={
                        'height': '250px', 'overflowY': 'scroll', 'border': '1px solid #ddd', 'padding': '10px', 'borderRadius': '10px',
                        'backgroundColor': '#f9f9f9', 'marginBottom': '20px'}),
                html.Div(id="notification_wrapper"),
                DashSocketIO(id='socketio', eventNames=["notification", "stream"]),
            ]),
        ]),
        # Input text untuk pesan
        dcc.Input(id='user-input', 
                  type='text', 
                  placeholder=random.choice([
                      'what product that i should sell to avoid overstock?',
                      'what product that i should restock based on current season?',
                      'produk apa yang saya jual untuk menghindari overstock?',
                      'produk apa yang harus saya restock berdasarkan musim yang sedang berjalan?'
                  ]), 
                  style={
            'width' : '95%', 'padding': '10px', 'borderRadius': '5px', 'border': '1px solid #ddd'
        }),
        # Tombol kirim pesan
        html.Button('Send', id='send-button', n_clicks=0, style={
            'padding': '10px 20px', 'backgroundColor': '#007bff', 'border': 'none', 'color': 'white', 'borderRadius': '5px'
        }),
    ], style={'width': '400px', 'margin': '0 auto', 'padding': '10px', 'border': '1px solid #ddd', 'borderRadius': '10px', 'fontFamily': 'Helvetica', 'marginTop': '10px',
              "boxShadow": "0px 4px 6px rgba(0,0,0,0.1)", 'backgroundColor': '#f9f9f9'})


clientside_callback(
    """connected => !connected""",
    Output("send-button", "disabled"),
    Input("socketio", "connected"),
)

clientside_callback(
    """(notification) => {
        if (!notification) return dash_clientside.no_update
        return notification
    }""",
    Output("notification_wrapper", "children", allow_duplicate=True),
    Input("socketio", "data-notification"),
    prevent_initial_call=True,
)

clientside_callback(
    """(word, text) => {
        if (text == null) return word

        let combinedText = text + word

        combinedText = combinedText.replace(/\*/g, '')
        combinedText = combinedText.replace(/\-/g, '')

        return combinedText
    }""",
    Output("streaming-process", "children", allow_duplicate=True),
    Input("socketio", "data-stream"),
    State("streaming-process", "children"),
    prevent_initial_call=True,
)