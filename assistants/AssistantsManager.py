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
    """
    Manage and facilitate interactions with the assistant agents.

    This class provides mechanisms to manage conversations with assistant agents,
    execute commands, create prompts and tools for the agent, and handle document
    sources within a session.

    :ivar message_repository: Repository for storing and retrieving messages.
    :type message_repository: MessageRepository
    :ivar assistants_repository: Repository for accessing assistant instances.
    :type assistants_repository: AssistantsRepository
    :ivar tool_manager: Manager for accessing and utilizing tools.
    :type tool_manager: ToolManager
    """
    SYSTEM_PROMPT_DOCS = """
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

    SYSTEM_PROMPT_NO_DOCS = """Make sure to you use the tools and do not provide urls given by tools in your answer!\n\n 
                            {description}.\n\n 
                            The Assistant id is :\n\n 
                            {id}.\n\n
                            If you don't know, do not invent, just say it.
                            """

    def __init__(self, message_repository: MessageRepository,
                 assistants_repository: AssistantsRepository,
                 tool_manager: ToolManager):
        """
        Initializes the AssistantsManager with the provided repositories and tool manager.

        :param message_repository: Manages the storage and retrieval of messages.
        :type message_repository: MessageRepository
        :param assistants_repository: Manages the information and operations related
            to assistants.
        :type assistants_repository: AssistantsRepository
        :param tool_manager: Handles the different tools used by assistants.
        :type tool_manager: ToolManager
        """
        self.message_repository = message_repository
        self.assistants_repository = assistants_repository
        self.tool_manager = tool_manager

    def execute_command(self, conversation_id: str, command: str):
        """
        Executes a command for a given conversation by retrieving the corresponding
        assistant and using its attributes.

        :param conversation_id: Unique identifier for the conversation
        :type conversation_id: str
        :param command: Command to be executed within the context of the conversation
        :type command: str
        :return: Result of the command execution
        :rtype: varies
        """
        assistant: Assistant = self.assistants_repository.get_assistant_by_conversation_id(conversation_id)
        return self.execute_command_documents(conversation_id, command, assistant.id,
                                              assistant.description,
                                              assistant.use_documents, assistant.gpt_model_number)

    def execute_command_documents(self, conversation_id: str, command: str, assistant_id: int,
                                  assistant_description: str,
                                  use_document: bool,
                                  gpt_model_number: str):
        """
        Executes the given command documents within the context of a conversation
        and returns the output along with sources if intermediate steps are present.

        :param conversation_id: str - The identifier for the conversation
        :param command: str - The command to be processed
        :param assistant_id: int - The identifier for the assistant being used
        :param assistant_description: str - A description of the assistant
        :param use_document: bool - Indicator whether to use a document
        :param gpt_model_number: str - The model number of the GPT to be used
        :return: dict - A dictionary containing the output and optionally the sources
        """
        # Get the current conversation and build document memory

        chat_models = {"4": chat_gpt_4, "4o": chat_gpt_4o, "4om": chat_gpt_4o_mini}
        local_chat = chat_models.get(gpt_model_number, chat_gpt_4o_mini)

        memory = build_agent_memory(self.message_repository, conversation_id)

        prompt, tools = self.create_prompt_and_tools(assistant_id, assistant_description, use_document)
        agent = create_openai_tools_agent(llm=local_chat, tools=tools, prompt=prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools,
                                       return_intermediate_steps=True,
                                       return_source_documents=True, verbose=True)

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

        if "intermediate_steps" in result:
            sources = self.extract_sources(result)
            return {"output": result["output"], "sources": sources}
        else:
            return {"output": result["output"]}

    def create_prompt_and_tools(self, assistant_id: int, assistant_description: str, use_document: bool):
        """
        Generates a chat prompt template and retrieves the appropriate tools based
        on the provided parameters. The prompt template is created using the system
        message and placeholder parts, and it is customized with a description and
        ID. Tools are selected based on whether document use is specified.

        :param assistant_id: The unique identifier for the assistant
        :type assistant_id: int
        :param assistant_description: A detailed description of the assistant
        :type assistant_description: str
        :param use_document: Flag indicating whether document should be used to
                             create the prompt
        :type use_document: bool
        :return: A tuple containing the configured chat prompt template and the
                 selected tools
        :rtype: tuple
        """
        if use_document:
            prompt = ChatPromptTemplate.from_messages([
                ("system", self.SYSTEM_PROMPT_DOCS),
                ("placeholder", "{messages}"),
                ("placeholder", "{agent_scratchpad}")
            ]).partial(description=assistant_description, id=str(assistant_id))
            tools = self.tool_manager.get_tools([ToolName.SUMMARIZE, ToolName.WEB_SEARCH])
        else:
            prompt = ChatPromptTemplate.from_messages([
                ("system", self.SYSTEM_PROMPT_NO_DOCS),
                ("placeholder", "{messages}"),
                ("placeholder", "{agent_scratchpad}")
            ]).partial(description=assistant_description, id=assistant_id)
            tools = self.tool_manager.get_tools([ToolName.WEB_SEARCH])
        return prompt, tools

    def extract_sources(self, result):
        """
        Extracts source information from the given result dictionary. The method iterates
        over the "intermediate_steps" section of the result and categorizes the sources
        into either "web search" or "summarize" based on the tool used. It then extracts
        relevant information from each source and appends it to the sources list.

        :param result: Dictionary containing intermediate steps and corresponding data.
        :type result: dict
        :return: List of extracted sources with specific information fields.
        :rtype: list
        """
        sources = []
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
                                  "perimeter": body.metadata["perimeter"], "text": body.metadata["text"],
                                  "type": "document"}
                        sources.append(source)
                    except Exception as e:
                        print(e)
                        continue
        return sources

    def save(self, assistant):
        """
        Saves the provided assistant object to the repository.

        This method allows storing the assistant object to the repository by delegating
        the save call to the assistants_repository.

        :param assistant: The assistant object to be saved.
        :type assistant: Assistant
        :return: The result of the save operation, usually the saved assistant object.
        :rtype: Assistant
        """
        return self.assistants_repository.save(assistant)

    def update(self, assistant):
        """
        Update an assistant record in the repository.

        This method updates an existing assistant record in the assistants repository.
        The assistant object provided as an argument replaces the existing record with
        the same identifier.

        :param assistant: The assistant object to be updated
        :type assistant: Assistant
        :return: The updated assistant object
        :rtype: Assistant
        """
        return self.assistants_repository.update(assistant)

    def get_all_assistant_by_user_id(self, user_id):
        """
        Retrieves all assistants associated with a given user ID.

        This method interacts with the assistants repository to fetch all
        the assistant objects tied to the specified user. It leverages the
        user_id to filter the results.

        :param user_id: The unique identifier of the user whose assistants
                        are to be retrieved.
        :type user_id: int
        :return: A list of assistant objects associated with the user.
        :rtype: list
        """
        return self.assistants_repository.get_all_assistant_by_user_id(user_id)

    def delete_by_assistant_id(self, assistant_id):
        """
        Remove an assistant based on the provided assistant_id from the repository.

        This method interacts with the assistants repository to delete an entry
        corresponding to the given assistant_id.

        :param assistant_id: Unique identifier of the assistant to be removed
        :type assistant_id: int
        :return: True if deletion was successful, otherwise False
        :rtype: bool
        """
        return self.assistants_repository.delete_by_assistant_id(assistant_id)
