import asyncio
from langchain import PromptTemplate
from langchain.embeddings import SentenceTransformerEmbeddings  
from langchain.vectorstores import FAISS
from langchain.llms import CTransformers
from langchain.chains import RetrievalQA
import chainlit as cl
import openai
# Define the paths and variables
DB_FAISS_PATH = r'C:\Users\Niama Maghrane\Desktop\New folder\CPUMedicalChatbot\vectorestores\db_faiss'
CUSTOM_PROMPT_TEMPLATE = """
Use the following pieces of information to answer the user's question.
If you don't know the answer, just say that you don't know, don't try to make up an answer.

Context: {context}
Question: {question}

Only return the helpful answer below and nothing else.
Helpful answer:
"""

# Function to set the custom prompt
def set_custom_prompt():
    prompt = PromptTemplate(template=CUSTOM_PROMPT_TEMPLATE, input_variables=['context', 'question'])
    return prompt

# Function to load the Openchat llm model
def load_llm():
   
    lm = CTransformers(
        model="TheBloke/openchat-3.5-0106-GGUF",
        max_tokens=512,
        temperature=0.5,
    )
    return lm

# Function to initialize the QA bot
def qa_bot():
    embeddings = SentenceTransformerEmbeddings(model_name="paraphrase-MiniLM-L6-v2")  
    db = FAISS.load_local(DB_FAISS_PATH, embeddings)
    llm = load_llm()
    qa_prompt = set_custom_prompt()
    qa_chain = RetrievalQA.from_chain_type(llm=llm,
                                           chain_type='stuff',
                                           retriever=db.as_retriever(search_kwargs={'k': 2}),
                                           return_source_documents=True,
                                           chain_type_kwargs={'prompt': qa_prompt}
                                           )
    return qa_chain

# Function to get the final result
async def final_result(query):
    qa_result = qa_bot()
    response = await qa_result({'query': query})
    return response

# chainlit code
@cl.on_chat_start
async def start():
    chain = qa_bot()
    msg = cl.Message(content="Starting the bot...")
    await msg.send()
    msg.content = "Hi, Welcome to the Medical Bot. What is your query?"
    await msg.update()

    cl.user_session.set("chain", chain)

@cl.on_message
async def main(message):
    chain = cl.user_session.get("chain")
    cb = cl.AsyncLangchainCallbackHandler(
        stream_final_answer=True, answer_prefix_tokens=["FINAL", "ANSWER"]
    )
    cb.answer_reached = True
    res = await chain.acall(message, callbacks=[cb])
    answer = res["result"]
    sources = res["source_documents"]

    if sources:
        answer += f"\nSources:" + str(sources)
    else:
        answer += "\nNo sources found"

    await cl.Message(content=answer).send()

if __name__ == "__main__":
    asyncio.run(cl.main())
