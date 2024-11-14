from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableWithMessageHistory

from assistants import AssistantsRepository
from assistants.Assistant import Assistant
from assistants.ToolManager import ToolManager, ToolName
from chat.azure_openai import chat_gpt_4o, chat_gpt_4, chat_gpt_4o_mini
from message import MessageRepository
from message.SqlMessageHistory import build_agent_memory


class AssistantManager:

    def __init__(self, message_repository: MessageRepository,
                 assistants_repository: AssistantsRepository,
                 tool_manager: ToolManager):
        self.message_repository = message_repository
        self.assistants_repository = assistants_repository
        self.tool_manager = tool_manager

    def execute_command(self, conversation_id: str, command: str):
        assistant: Assistant = self.assistants_repository.get_assistant_by_conversation_id(conversation_id)
        return self.execute_command_documents(conversation_id, command, assistant.id,
                                              assistant.description,
                                              assistant.use_documents, assistant.gpt_model_number)

    def execute_command_vba(self, conversation_id: str, command: str, use_documents: bool,
                            use_memory: bool):
        assistant: Assistant = self.assistants_repository.get_assistant_by_conversation_id(conversation_id)
        return self.execute_command_documents(conversation_id, command, assistant.id,
                                              assistant.description,
                                              use_documents, assistant.gpt_model_number, use_memory)

    def execute_powerpoint_command_vba(self, conversation_id: str, command: str, use_documents: bool):
        assistant: Assistant = self.assistants_repository.get_assistant_by_conversation_id(conversation_id)
        local_chat = chat_gpt_4o

        if use_documents:
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "You are a vba specialist helping me to create a json representation of a PowerPoint presentation."
                        "First, create a summary based on the user documentation, then make sure to call the tool to "
                        "create the powerpoint based on this content"
                        "The Assistant id is  {}. If you don't know, do not invent, just say it.".format(assistant.id)

                    ),
                    ("placeholder", "{messages}"),
                    ("placeholder", "{agent_scratchpad}"),
                ]
            )
            power_point_doc_tools = self.tool_manager.get_tools([ToolName.SUMMARIZE, ToolName.POWERPOINT])
            agent = create_openai_tools_agent(llm=local_chat, tools=power_point_doc_tools, prompt=prompt)
            agent_executor = AgentExecutor(agent=agent, tools=power_point_doc_tools, verbose=True)
        else:
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "You are a vba specialist helping me to create a PowerPoint presentation."
                        "Use the user input to help you creating the content and then make sure to call the tool to "
                        "create the powerpoint based on this content"
                        "If you don't know, do not invent, just say it."

                    ),
                    ("placeholder", "{messages}"),
                    ("placeholder", "{agent_scratchpad}"),
                ]
            )
            power_point_tool = self.tool_manager.get_tools(
                [ToolName.POWERPOINT, ToolName.WEB_SEARCH])
            agent = create_openai_tools_agent(llm=local_chat, tools=power_point_tool, prompt=prompt)
            agent_executor = AgentExecutor(agent=agent, tools=power_point_tool, verbose=True)

        result = agent_executor.invoke(
            {"messages": [HumanMessage(command)]}
        )

        return result["output"]

    def execute_command_documents(self, conversation_id: str, command: str, id: int,
                                  description: str,
                                  use_document: bool,
                                  gpt_model_number: str,
                                  use_memory: bool = True):
        # Get the current conversation and build document memory

        if gpt_model_number == "4":
            local_chat = chat_gpt_4
        elif gpt_model_number == "4o":
            local_chat = chat_gpt_4o
        else:
            local_chat = chat_gpt_4o_mini

        memory = build_agent_memory(self.message_repository, conversation_id)

        if use_document:

            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system", "{description}"),
                    (
                        "system",
                        """
                        Access and utilize the documents stored in the user's library for any information or data you 
                        need.
                        Employ the summarization tool to search the user’s library. Extract and condense information 
                        from relevant documents to craft your responses. Ensure your responses are well-informed by 
                        these documents. 
                        \n
                        The Assistant ID for this session is {id}.'
                        If unsure about any details, explicitly state that the information is not available in the 
                        documents within the library instead of making assumptions. 
                        
                        Do not provide urls given by tools in your answer!
                        """

                    ),
                    ("placeholder", "{messages}"),
                    ("placeholder", "{agent_scratchpad}"),
                ]
            ).partial(description=description, id=str(id))
            full_tools = self.tool_manager.get_tools([ToolName.SUMMARIZE, ToolName.WEB_SEARCH])
            agent = create_openai_tools_agent(llm=local_chat, tools=full_tools, prompt=prompt)
            agent_executor = AgentExecutor(agent=agent, tools=full_tools,
                                           return_intermediate_steps=True,
                                           return_source_documents=True, verbose=True)

            if use_memory:
                conversational_agent_executor = RunnableWithMessageHistory(
                    agent_executor,
                    lambda session_id: memory,
                    input_messages_key="messages",
                    return_source_documents=True,
                    output_messages_key="output",
                )

                result = conversational_agent_executor.invoke(
                    {"messages": [HumanMessage(command)]},
                    {"configurable": {"session_id": "unused"}},
                )
            else:
                result = agent_executor.invoke(
                    {"messages": [HumanMessage(command)]}
                )

        else:

            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """Make sure to you use the tools and do not provide urls given by tools in your answer!\n\n 
                        {description}.\n\n 
                        The Assistant id is :\n\n 
                        {id}.\n\n
                        If you don't know, do not invent, just say it.
                        """

                    ),
                    ("placeholder", "{messages}"),
                    ("placeholder", "{agent_scratchpad}"),
                ]
            ).partial(description=description, id=id)
            no_doc_tools = self.tool_manager.get_tools([ToolName.WEB_SEARCH])
            agent = create_openai_tools_agent(llm=local_chat, tools=no_doc_tools, prompt=prompt)

            agent_executor = AgentExecutor(agent=agent, tools=no_doc_tools,
                                           return_intermediate_steps=True,
                                           return_source_documents=True, verbose=True)

            if use_memory:
                conversational_agent_executor = RunnableWithMessageHistory(
                    agent_executor,
                    lambda session_id: memory,
                    return_source_documents=True,
                    input_messages_key="messages",
                    output_messages_key="output",
                )
                result = conversational_agent_executor.invoke(
                    {"messages": [HumanMessage(command)]},
                    {"configurable": {"session_id": "unused"}},
                )
            else:
                result = agent_executor.invoke(
                    {"messages": [HumanMessage(command)]}
                )

        sources = []
        if "intermediate_steps" in result:
            for res in result["intermediate_steps"]:
                if res[0].tool == ToolName.WEB_SEARCH:
                    for body in res[1]:
                        try:
                            source = {"blob_id": body["title"], "file_name": body["href"], "page": "number",
                                      "perimeter": "string",
                                      "text": body["body"], "type": "href"}
                            sources.append(source)
                        except Exception as e:
                            print(e)
                            continue
                elif res[0].tool == ToolName.SUMMARIZE:
                    for body in res[1]:
                        try:
                            source = {"blob_id": body.metadata["blob_id"], "file_name": body.metadata["file_name"],
                                      "page": body.metadata["page"],
                                      "perimeter": body.metadata["perimeter"], "text": body.metadata["text"], "type": "document"}
                            sources.append(source)
                        except Exception as e:
                            print(e)
                            continue

            return {"output": result["output"], "sources": sources}
        else:
            return {"output": result["output"]}

    def save(self, assistant):
        return self.assistants_repository.save(assistant)

    def update(self, assistant):
        return self.assistants_repository.update(assistant)

    def get_all_assistant_by_user_id(self, user_id):
        return self.assistants_repository.get_all_assistant_by_user_id(user_id)

    def delete_by_assistant_id(self, assistant_id):
        return self.assistants_repository.delete_by_assistant_id(assistant_id)
