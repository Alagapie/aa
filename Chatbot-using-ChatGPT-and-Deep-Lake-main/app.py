import os 
from langchain.document_loaders import DirectoryLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import DeepLake
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA
from dotenv import load_dotenv 
import streamlit as st 
from streamlit_chat import message

load_dotenv()

os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
ACTIVELOOP_TOKEN ="eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJpZCI6ImFsYWdhcGllb2ZmaWNpYWwiLCJhcGlfa2V5IjoiMkd6Y3NDbzhXUEIyZ3BENFlzTnJvWkl6ZjFPakRwVHp0S2x0WTJ1VE5Td0pmIn0."
DEEPLAKE_ACCOUNT_NAME=alagapieofficial
gemini_api_key=AIzaSyAf8HqQEmwg8JGPYt_kym-P6Vivz9wWlG8
@st.cache_data
def doc_preprocessing():
    loader = DirectoryLoader(
        'data/',
        glob='**/*.pdf',     # only the PDFs
        show_progress=True
    )
    docs = loader.load()
    text_splitter = CharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=0
    )
    docs_split = text_splitter.split_documents(docs)
    return docs_split

@st.cache_resource
def embeddings_store():
    embeddings =GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    print(embeddings)
    texts = doc_preprocessing()
    db = DeepLake.from_documents(texts, embeddings, dataset_path=f"hub://alagapieofficial/text_embedding")
    print(db)
    db = DeepLake(
    dataset_path=f"hub://alagapieofficial/text_embedding",
    read_only=True,
    embedding_function=embeddings,
    )
    return db

@st.cache_resource
def search_db():
    db = embeddings_store()
    retriever = db.as_retriever()
    retriever.search_kwargs['distance_metric'] = 'cos'
    retriever.search_kwargs['fetch_k'] = 100
    retriever.search_kwargs['maximal_marginal_relevance'] = True
    retriever.search_kwargs['k'] = 10
    model = ChatGoogleGenerativeAI(model='gemini-1.5-flash',gemini_api_key=gemini_api_key)
    qa = RetrievalQA.from_llm(model, retriever=retriever, return_source_documents=True)
    return qa

qa = search_db()

# Display conversation history using Streamlit messages
def display_conversation(history):
    for i in range(len(history["generated"])):
        message(history["past"][i], is_user=True, key=str(i) + "_user")
        message(history["generated"][i],key=str(i))

def main():
    # Initialize Streamlit app with a title
    st.title("LLM Powered Chatbot")

    # Get user input from text input
    user_input = st.text_input("", key="input")

    # Initialize session state for generated responses and past messages
    if "generated" not in st.session_state:
        st.session_state["generated"] = ["I am ready to help you"]
    if "past" not in st.session_state:
        st.session_state["past"] = ["Hey there!"]
        
    # Search the database for a response based on user input and update session state
    if user_input:
        output = qa({'query': user_input})
        # print(output['source_documents'])
        st.session_state.past.append(user_input)
        response = str(output["result"])
        st.session_state.generated.append(response)

    # Display conversation history using Streamlit messages
    if st.session_state["generated"]:
        display_conversation(st.session_state)

if __name__ == "__main__":
    main()








