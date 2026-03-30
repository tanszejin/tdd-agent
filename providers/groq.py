
from __future__ import annotations

from groq import Groq
import json
import json_repair

from .base import Provider, Response, ToolCall
from tools.base import Tool


class GroqProvider:
    def __init__(self, api_key: str, model: str = "openai/gpt-oss-120b"):
        self.client = Groq(
            api_key=api_key,
        )
        self.model = model

        # self.messages = [
        #     SystemMessage(content="""You are a helpful coding assistant. 
        #                 You will be given a task by the user, and you will respond with what 
        #                   you think the AI agent should do next to complete the task."""),
        # ]

    def chat(self, messages: list[dict], tools: list[Tool]) -> Response:

        ai_tools = [self._convert_tool(tool) for tool in tools]

        parsed_messages = self._convert_messages(messages)

        response = self.client.chat.completions.create(
            model=self.model,
            # max_tokens=4096,
            messages=parsed_messages,
            tools=ai_tools,
        )

        return self._parse_response(response)

    def _convert_tool(self, tool: Tool) -> dict:
        # check if this needs to be edited to be more descriptive 
        return {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.get_schema(),
                    }
                }

    def _convert_messages(self, messages: list[dict]) -> list[dict]:
        parsed_messages = []

        for msg in messages:
            if msg["role"] == "tool":
                parsed_messages.append({
                    "role": "tool",
                    "tool_call_id": msg["tool_use_id"],
                    "name": msg["name"],
                    "content": msg["content"],
                })
            elif msg["role"] == "assistant" and "tool_calls" in msg:
                tool_calls = []
                for tc in msg["tool_calls"]:
                    tool_calls.append({
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": json.dumps(tc["parameters"]),
                        }
                    })
                parsed_messages.append({"role": "assistant", "tool_calls": tool_calls})
            else:
                parsed_messages.append(msg)

        return parsed_messages

    def _parse_response(self, response) -> Response:
        tool_calls = []

        if response.choices[0].message.tool_calls:
            for tool_call in response.choices[0].message.tool_calls:
                # print(tool_call)
                tool_calls.append(
                    ToolCall(
                        name=tool_call.function.name,
                        # TODO: USE JSON REPAIR HERE
                        parameters=json_repair.loads(tool_call.function.arguments),
                        id=tool_call.id,
                    )
                )
        
        return Response(content=response.choices[0].message.content, tool_calls=tool_calls)
    
    def get_name(self) -> str:
        return "groq"