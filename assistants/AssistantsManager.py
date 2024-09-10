from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableWithMessageHistory
from starlette.responses import JSONResponse

from assistants import AssistantsRepository
from assistants.Assistant import Assistant
from chat.azure_openai import chat_gpt_35, chat_gpt_4o, chat_gpt_4
from memories.SqlMessageHistory import build_agent_memory
from message import MessageRepository


class AssistantManager:

    def __init__(self, message_repository: MessageRepository,
                 assistants_repository: AssistantsRepository,
                 full_tools: [],
                 no_doc_tools: []):
        self.message_repository = message_repository
        self.assistants_repository = assistants_repository
        self.full_tools = full_tools
        self.no_doc_tools = no_doc_tools

    def execute_command(self, conversation_id: str, command: str) -> JSONResponse:
        # Get the current conversation and build document memory
        assistant: Assistant = self.assistants_repository.get_assistant_by_conversation_id(conversation_id)

        if assistant.gpt_model_number == "4":
            local_chat = chat_gpt_4
        elif assistant.gpt_model_number == "4o":
            local_chat = chat_gpt_4o
        else:
            local_chat = chat_gpt_35

        memory = build_agent_memory(self.message_repository, assistant.conversation_id)

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "{}.\n Make sure you use the tool when you can !\n The Assistant id is {}."
                    "If you don't know, do not invent, just say it.".format(assistant.description, assistant.id)

                ),
                ("placeholder", "{messages}"),
                ("placeholder", "{agent_scratchpad}"),
            ]
        )

        if assistant.use_documents:

            agent = create_openai_tools_agent(llm=local_chat, tools=self.full_tools, prompt=prompt)
            agent_executor = AgentExecutor(agent=agent, tools=self.full_tools, verbose=True)

            conversational_agent_executor = RunnableWithMessageHistory(
                agent_executor,
                lambda session_id: memory,
                input_messages_key="messages",
                output_messages_key="output",
            )


        else:
            agent = create_openai_tools_agent(llm=local_chat, tools=self.no_doc_tools, prompt=prompt)
            agent_executor = AgentExecutor(agent=agent, tools=self.no_doc_tools, verbose=True)

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
        return result["output"]

    def save(self, assistant):
        return self.assistants_repository.save(assistant)

    def update(self, assistant):
        return self.assistants_repository.update(assistant)

    def get_all_assistant_by_user_id(self, user_id):
        return self.assistants_repository.get_all_assistant_by_user_id(user_id)

    def delete_by_assistant_id(self, assistant_id):
        return self.assistants_repository.delete_by_assistant_id(assistant_id)
