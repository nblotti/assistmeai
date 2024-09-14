from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableWithMessageHistory

from ToolManager import ToolManager, ToolName
from assistants import AssistantsRepository
from assistants.Assistant import Assistant
from chat.azure_openai import chat_gpt_35, chat_gpt_4o, chat_gpt_4
from memories.SqlMessageHistory import build_agent_memory
from message import MessageRepository


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
                [ToolName.POWERPOINT, ToolName.WEB_SEARCH, ToolName.GET_DATE])
            agent = create_openai_tools_agent(llm=local_chat, tools=power_point_tool, prompt=prompt)
            agent_executor = AgentExecutor(agent=agent, tools=power_point_tool, verbose=True)

        result = agent_executor.invoke(
            {"messages": [HumanMessage(f"'''{command}'''")]}
        )

        return result["output"]

    def execute_command_documents(self, conversation_id: str, command: str, id: str,
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
            local_chat = chat_gpt_35

        memory = build_agent_memory(self.message_repository, conversation_id)



        if use_document:

            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "Make sure to use the summarize tool to search the user's library and summarize relevant "
                        "documents to respond and make sure to you use the tool when you can !\n\n {}.\n\n The Assistant id is {}.\n\n"
                        "If you don't know, do not invent, just say it.".format(description, id)

                    ),
                    ("placeholder", "{messages}"),
                    ("placeholder", "{agent_scratchpad}"),
                ]
            )
            full_tools = self.tool_manager.get_tools([ToolName.SUMMARIZE, ToolName.GET_DATE, ToolName.WEB_SEARCH])
            agent = create_openai_tools_agent(llm=local_chat, tools=full_tools, prompt=prompt)
            agent_executor = AgentExecutor(agent=agent, tools=full_tools, verbose=True)

            if use_memory:
                conversational_agent_executor = RunnableWithMessageHistory(
                    agent_executor,
                    lambda session_id: memory,
                    input_messages_key="messages",
                    output_messages_key="output",
                )

                result = conversational_agent_executor.invoke(
                    {"messages": [HumanMessage(f"'''{command}'''")]},
                    {"configurable": {"session_id": "unused"}},
                )
            else:
                result = agent_executor.invoke(
                    {"messages": [HumanMessage(f"'''{command}'''")]}
                )

        else:

            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "Make sure to you use the tool when you can !\n\n {}.\n\n The Assistant id is {}.\n\n"
                        "If you don't know, do not invent, just say it.".format(description, id)

                    ),
                    ("placeholder", "{messages}"),
                    ("placeholder", "{agent_scratchpad}"),
                ]
            )
            no_doc_tools = self.tool_manager.get_tools([ToolName.GET_DATE, ToolName.WEB_SEARCH])
            agent = create_openai_tools_agent(llm=local_chat, tools=no_doc_tools, prompt=prompt)
            agent_executor = AgentExecutor(agent=agent, tools=no_doc_tools, verbose=True)

            if use_memory:
                conversational_agent_executor = RunnableWithMessageHistory(
                    agent_executor,
                    lambda session_id: memory,
                    input_messages_key="messages",
                    output_messages_key="output",
                )

                result = conversational_agent_executor.invoke(
                    {"messages": [HumanMessage(f"'''{command}'''")]},
                    {"configurable": {"session_id": "unused"}},
                )
            else:
                result = agent_executor.invoke(
                    {"messages": [HumanMessage(f"'''{command}'''")]}
                )

        return result["output"]

    def save(self, assistant):
        return self.assistants_repository.save(assistant)

    def update(self, assistant):
        return self.assistants_repository.update(assistant)

    def get_all_assistant_by_user_id(self, user_id):
        return self.assistants_repository.get_all_assistant_by_user_id(user_id)

    def delete_by_assistant_id(self, assistant_id):
        return self.assistants_repository.delete_by_assistant_id(assistant_id)
