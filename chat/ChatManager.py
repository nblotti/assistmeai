from http.client import HTTPException

from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.documents.base import Blob
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableWithMessageHistory, RunnablePassthrough

from assistants.ToolManager import ToolManager, ToolName
from chat.azure_openai import chat_gpt_4o, whisper
from conversation.Conversation import ConversationCreate
from conversation.ConversationRepository import ConversationRepository
from document.Document import DocumentCreate, DocumentType
from document.DocumentManager import DocumentManager
from embeddings.CustomAzurePGVectorRetriever import CustomAzurePGVectorRetriever
from embeddings.QueryType import QueryType
from message.MessageRepository import MessageRepository
from message.SqlMessageHistory import SqlMessageHistory, build_agent_memory


def format_docs(docs):
    return [doc.metadata for doc in docs]


class ChatManager:

    def __init__(self, message_repository: MessageRepository,
                 document_manager: DocumentManager,
                 conversation_repository: ConversationRepository):

        self.message_repository = message_repository
        self.document_manager = document_manager
        self.conversation_repository = conversation_repository

    def message(self, command: str, conversation_id: str, perimeter: str):
        # Get the current conversation and build document memory
        cur_conversation: ConversationCreate = self.conversation_repository.get_conversation_by_id(int(conversation_id))
        memory = build_agent_memory(self.message_repository, conversation_id)

        # Determine the appropriate retriever based on the perimeter or conversation PDF ID
        if cur_conversation.pdf_id is not None and cur_conversation.pdf_id != 0:
            document: DocumentCreate = self.document_manager.get_by_id(cur_conversation.pdf_id)
            if document.document_type == DocumentType.TEMPLATE:
                return self.do_template(memory, command, cur_conversation, document)
            else:
                rag_retriever = CustomAzurePGVectorRetriever(QueryType.DOCUMENT, str(cur_conversation.pdf_id))

        elif perimeter:
            rag_retriever = CustomAzurePGVectorRetriever(QueryType.PERIMETER, perimeter)
        else:
            raise HTTPException(status_code=400, detail="You need to set a document search perimeter")

        return self.do_rag(rag_retriever, memory, command)

    def do_focus(self, memory: SqlMessageHistory, command: str, cur_conversation: ConversationCreate,
                 document: DocumentCreate):
        # Get the current conversation and build document memory

        tool_manager = ToolManager()
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
                    Please answer the user on the following questions using the provided focus only file.

                    The document id is : {document_id}

                    """,
                ),
                ("placeholder", "{messages}"),
                ("placeholder", "{agent_scratchpad}"),
            ]
        ).partial(document_id=cur_conversation.pdf_id)
        memory = build_agent_memory(self.message_repository, cur_conversation.id)
        focus_doc_tools = tool_manager.get_tools([ToolName.FOCUS_ONLY])
        agent = create_openai_tools_agent(llm=chat_gpt_4o, tools=focus_doc_tools, prompt=prompt)
        agent_executor = AgentExecutor(agent=agent, tools=focus_doc_tools, verbose=True)

        conversational_agent_executor = RunnableWithMessageHistory(
            agent_executor,
            lambda session_id: memory,
            input_messages_key="messages",
            output_messages_key="output",
        )

        result = conversational_agent_executor.invoke(
            {"messages": [HumanMessage(command)]},
            {"configurable": {"session_id": "unused"}},
        )
        result["answer"] = result["output"]
        return result
        # Return response with results and possibly source metadata

    def do_template(self,
                    memory: SqlMessageHistory,
                    command: str,
                    conversation: ConversationCreate,
                    document: DocumentCreate):
        tool_manager = ToolManager()
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
                    You have been assigned the task of updating a template by substituting a designated placeholder text with new 
                    content. To ensure this is done accurately and effectively, follow the structured guidelines below:

                    Steps for Updating the Template:

                    -Read and carefully follow the user instruction or any response he may have given. 
                    - The placeholders to replace are surrounded with @@@, locate them within the template provided. 
                    - Carefully read the text surrounding the boilerplates in the template to fully grasp the context. 
                    Understanding the context is crucial to ensure the new text will integrate smoothly.

                    - If you need more info, ask the user all the question required.



                    The document id is : {document_id}

                    """,
                ),
                ("placeholder", "{messages}"),
                ("placeholder", "{agent_scratchpad}"),
            ]
        ).partial(document_id=document.id)
        memory = build_agent_memory(self.message_repository, conversation.id)
        template_doc_tools = tool_manager.get_tools([ToolName.TEMPLATE])
        agent = create_openai_tools_agent(llm=chat_gpt_4o, tools=template_doc_tools, prompt=prompt)
        agent_executor = AgentExecutor(agent=agent, tools=template_doc_tools, verbose=True)

        conversational_agent_executor = RunnableWithMessageHistory(
            agent_executor,
            lambda session_id: memory,
            input_messages_key="messages",
            output_messages_key="output",
        )

        result = conversational_agent_executor.invoke(
            {"messages": [HumanMessage(command)]},
            {"configurable": {"session_id": "unused"}},
        )
        return result

    def do_rag(self,
               rag_retriever: CustomAzurePGVectorRetriever,
               memory: SqlMessageHistory,
               command: str):
        system_prompt = (
            "You are an assistant for question-answering tasks. "
            "Use the following pieces of retrieved context to answer "
            "the question. If you don't know the answer, say that you "
            "don't know. Use three sentences maximum and keep the "
            "answer concise."
            "\n\n"
            "{context}"
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", "{input}"),
            ]
        )
        rag_chain_from_docs = (
                {
                    "input": lambda x: x["input"],  # input query
                    "context": lambda x: format_docs(x["context"]),  # context
                }
                | prompt  # format query and context into prompt
                | chat_gpt_4o  # generate response
                | StrOutputParser()  # coerce to string
        )

        # Pass input query to retriever
        retrieve_docs = (lambda x: x["input"]) | rag_retriever

        # Below, we chain `.assign` calls. This takes a dict and successively
        # adds keys-- "context" and "answer"-- where the value for each key
        # is determined by a Runnable. The Runnable operates on all existing
        # keys in the dict.
        rag_chain = RunnablePassthrough.assign(context=retrieve_docs).assign(
            answer=rag_chain_from_docs,
        )
        conversational_rag_chain = RunnableWithMessageHistory(
            rag_chain,
            lambda session_id: memory,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer",
        )
        # Invoke the chain with the command/query
        try:
            # result = chain.invoke({"query": command})

            result = conversational_rag_chain.invoke({"input": command}, {"configurable": {"session_id": "unused"}})
            # print(result)  # Or whatever logging mechanism you prefer
        except Exception as e:
            print(f"Error occurred: {e}")
            raise
        return result
        # Return response with results and possibly source metadata

    def execute_voice_command(self, conversation_id, perimeter, tmp_path):
        audio_blob = Blob(path=tmp_path)
        documents = whisper.lazy_parse(blob=audio_blob)

        content = ""
        for document in documents:
            content += document.page_content

        result: dict = self.message(content, conversation_id, perimeter)

        result["question"] = content
        return result
