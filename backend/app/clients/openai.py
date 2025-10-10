from typing import TypeVar, cast

from openai import AsyncOpenAI
from openai.types import ChatModel
from openai.types.beta import Thread
from openai.types.beta.threads import Message, TextContentBlock
from openai.types.chat import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from openai.types.responses import EasyInputMessageParam, WebSearchToolParam
from pydantic import BaseModel

M = TypeVar("M", bound=BaseModel)


class OpenAIClient:
    def __init__(self, openai_session: AsyncOpenAI, thread: Thread):
        self.openai_session = openai_session
        self.thread = thread

    @staticmethod
    def parse_json_from_message(message: Message, model: type[M]) -> M:
        for content in message.content:
            if isinstance(content, TextContentBlock) and content.text.value:
                return model.model_validate_json(content.text.value)
        raise ValueError

    @staticmethod
    def get_text_from_message(message: Message) -> str:
        texts = [
            content.text.value
            for content in message.content
            if isinstance(content, TextContentBlock)
        ]
        return "\n".join(texts)

    async def get_quick_assistant_answer(
        self,
        content: str,
        assistant_id: str,
        additional_instructions: str | None = None,
    ) -> Message | None:
        await self.openai_session.beta.threads.messages.create(
            thread_id=self.thread.id,
            content=content,
            role="user",
        )
        run = await self.openai_session.beta.threads.runs.create_and_poll(
            assistant_id=assistant_id,
            thread_id=self.thread.id,
            model=self.gpt_model,
            poll_interval_ms=self.poll_interval_ms,
            additional_instructions=additional_instructions,
        )
        last_messages = await self.openai_session.beta.threads.messages.list(
            thread_id=self.thread.id,
            run_id=run.id,
            order="desc",
        )
        async for message in last_messages:
            return cast(Message, message)
        return None

    async def get_chat_completion_in_text(
        self,
        user_prompt: str,
        system_prompt: str,
    ) -> str | None:
        user_message = ChatCompletionUserMessageParam(
            content=user_prompt,
            role="user",
            name="user",
        )
        system_message = ChatCompletionSystemMessageParam(
            content=system_prompt,
            role="system",
            name="system",
        )

        completion = await self.openai_session.chat.completions.create(
            model=self.gpt_model,
            messages=[
                system_message,
                user_message,
            ],
        )
        for choice in completion.choices:
            return choice.message.content
        return None

    async def get_model_response_in_text(
        self,
        user_prompt: str,
        system_prompt: str,
        *,
        web_search: bool = False,
    ) -> str | None:
        user_message = EasyInputMessageParam(
            content=user_prompt,
            role="user",
            type="message",
        )
        system_message = EasyInputMessageParam(
            content=system_prompt,
            role="system",
            type="message",
        )
        tools = []
        if web_search:
            tools.append(
                WebSearchToolParam(
                    type="web_search_preview",
                    search_context_size="high",
                ),
            )
        response = await self.openai_session.responses.create(
            model=self.gpt_model,
            input=[
                system_message,
                user_message,
            ],
            tools=tools,
        )
        return response.output_text

    @property
    def gpt_model(self) -> ChatModel:
        return "gpt-4o"

    @property
    def poll_interval_ms(self):
        return 3500
