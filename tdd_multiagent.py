

from __future__ import annotations

from providers.base import Provider, Response, ToolCall
from tools.base import Tool
from display import Display


class TDD_MultiAgent:

    # have 2 separate messages arr for the 2 llms, 
    # 2 loops - test llm and code llm
    # add refereence to the test file for code llm
    # test llm doesnt need to know responses of code llm
    # have another debugging llm?

    """
    An agent that extends the original to incorporate Test-Driven Development (TDD) principles.

    The agent follows a loop:
    1. THINK - Ask the LLM what to do next
    2. CHECK - Is the task complete? If so, stop
    3. ACT - Execute any tool calls the LLM requested
    4. OBSERVE - Add results to conversation and loop back
    """

    def __init__(self, test_provider: Provider, code_provider: Provider, tools: list[Tool], transcript_path: str | None = None):
        self.test_provider = test_provider
        self.code_provider = code_provider
        self.tools = tools
        self.display = Display(transcript_path=transcript_path)

        # Create a lookup dict for quick tool access
        self._tool_map = {tool.name: tool for tool in tools}

    def run(self, task: str) -> str:

        # Show the task to the user
        self.display.show_task(task)

        # Initialize the conversation with the user's task
        test_messages = [{"role": "system", "content": TEST_SYSTEM_PROMPT}]
        test_messages.append({"role": "user", "content": task})
        code_messages = [{"role": "system", "content": CODE_SYSTEM_PROMPT}]
        code_messages.append({"role": "user", "content": task})


        # Test llm loop
        while True:
            # ============================================
            # STEP 1: THINK - Ask the LLM what to do next
            # ============================================
            # Show what we're sending to the LLM
            self.display.show_llm_request(test_messages, self.tools, "Test")

            self.display.show_thinking()

            try:
                response = self.test_provider.chat(test_messages, self.tools)
            except Exception as e:
                self.display.show_error(f"Test LLM error: {e} \nAttempting to retry...")
                test_messages.append({
                    "role": "user",
                    "content": f"Error encountered: {e} \nPlease try again."
                })
                self.display.hide_thinking()
                continue

            # try:
            #     response = self.test_provider.chat(test_messages, self.tools)
            # except Exception as e:
            #     self.display.show_error(f"Test LLM error: {e}")
            #     return f"Error: {e}"

            self.display.hide_thinking()

            # Show what the LLM returned
            self.display.show_llm_response(response, "Test")

            # ============================================
            # STEP 2: CHECK - Is the task complete?
            # ============================================
            # If the LLM didn't request any tool calls, we're done
            if response.is_final:
                if response.content == "":
                    response.content = "Tests generated successfully"
                self.display.show_answer(response.content)
                break

            # ============================================
            # STEP 3: ACT - Execute the tool calls
            # ============================================
            # Add the assistant's response to the conversation
            # (This preserves any text content plus the tool calls)
            
            test_messages.append({
                "role": "assistant",
                "content": response.content,
                "tool_calls": [
                    {"id": tc.id, "name": tc.name, "parameters": tc.parameters}
                    for tc in response.tool_calls
                ],
            })
            code_messages.append({
                "role": "assistant",
                "content": response.content,
                "tool_calls": [
                    {"id": tc.id, "name": tc.name, "parameters": tc.parameters}
                    for tc in response.tool_calls
                ],
            })


            # Execute each tool call
            for tool_call in response.tool_calls:
                self.display.show_tool_call(tool_call)

                # Find and execute the tool
                result = self._execute_tool(tool_call)

                self.display.show_tool_result(result)

                # ============================================
                # STEP 4: OBSERVE - Add result to conversation
                # ============================================
                # The result becomes part of the conversation,
                # so the LLM can see what happened 
                test_messages.append({
                    "role": "tool",
                    "tool_use_id": tool_call.id,
                    "name": tool_call.name,
                    "content": result,
                })

            # Loop back to THINK with the new information
        
        # Code llm loop
        while True:
            # ============================================
            # STEP 1: THINK - Ask the LLM what to do next
            # ============================================
            # Show what we're sending to the LLM
            self.display.show_llm_request(code_messages, self.tools, "Code")

            self.display.show_thinking()

            try:
                response = self.code_provider.chat(code_messages, self.tools)
            except Exception as e:
                self.display.show_error(f"Code LLM error: {e} \nAttempting to retry...")
                code_messages.append({
                    "role": "user",
                    "content": f"Error encountered: {e} \nPlease try again."
                })
                self.display.hide_thinking()
                continue

            # try:
            #     response = self.code_provider.chat(code_messages, self.tools)
            # except Exception as e:
            #     self.display.show_error(f"Code LLM error: {e}")
            #     return f"Error: {e}"

            self.display.hide_thinking()

            # Show what the LLM returned
            self.display.show_llm_response(response, "Code")

            # ============================================
            # STEP 2: CHECK - Is the task complete?
            # ============================================
            # If the LLM didn't request any tool calls, we're done
            if response.is_final:
                if response.content == "":
                    response.content = "Code implemented successfully"
                self.display.show_answer(response.content)
                break

            # ============================================
            # STEP 3: ACT - Execute the tool calls
            # ============================================
            # Add the assistant's response to the conversation
            # (This preserves any text content plus the tool calls)
            
            code_messages.append({
                "role": "assistant",
                "content": response.content,
                "tool_calls": [
                    {"id": tc.id, "name": tc.name, "parameters": tc.parameters}
                    for tc in response.tool_calls
                ],
            })


            # Execute each tool call
            for tool_call in response.tool_calls:
                self.display.show_tool_call(tool_call)

                # Find and execute the tool
                result = self._execute_tool(tool_call)

                self.display.show_tool_result(result)

                # ============================================
                # STEP 4: OBSERVE - Add result to conversation
                # ============================================
                # The result becomes part of the conversation,
                # so the LLM can see what happened 
                code_messages.append({
                    "role": "tool",
                    "tool_use_id": tool_call.id,
                    "name": tool_call.name,
                    "content": result,
                })

            # Loop back to THINK with the new information

    def _execute_tool(self, tool_call: ToolCall) -> str:
        tool = self._tool_map.get(tool_call.name)

        if tool is None:
            return f"Error: Unknown tool '{tool_call.name}'"

        try:
            return tool.execute(**tool_call.parameters)
        except TypeError as e:
            return f"Error: Invalid parameters for {tool_call.name}: {e}"
        except Exception as e:
            return f"Error executing {tool_call.name}: {e}"


TEST_SYSTEM_PROMPT = """
    You are an expert software engineer practicing Test-Driven Development.

    Create a new test file (e.g., test_module.py for module.py) and write comprehensive Python unit tests BEFORE implementation.

    Rules:
    - Create a new test file for the tests (e.g., test_module.py for module.py).
    - Use pytest.
    - Only write tests, not the implementation.
    - Import the function being tested, which should exist in the same directory.
    - Include edge cases.
    - Include normal cases.
    - Ensure tests clearly define expected behaviour.

    Write the tests using the provided tools.
"""

CODE_SYSTEM_PROMPT = """
    You are an expert Python developer implementing code using Test-Driven Development.

    Your task is to implement code so that ALL provided unit tests pass.

    Rules:
    - Refer to the test file to understand what to implement (e.g., test_module.py for module.py).
    - Do not modify the tests.
    - Only write the implementation.
    - Run all tests and edit the implementation until all tests pass.

    Write the code using the provided tools.
"""