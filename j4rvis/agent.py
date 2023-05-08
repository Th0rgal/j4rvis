import re
import openai
from prompt import get_prompt_template
from typing import List, Union, Dict, Any, Tuple
from langchain.agents import (
    Tool,
    AgentExecutor,
    BaseSingleActionAgent,
    AgentOutputParser,
)
from langchain.callbacks.manager import Callbacks
from langchain import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.prompts import BaseChatPromptTemplate
from langchain.schema import AgentAction, AgentFinish, HumanMessage
from tools import define_tools


class CustomPromptTemplate(BaseChatPromptTemplate):
    template: str
    tools: List[Tool]

    def format_messages(self, **kwargs) -> str:
        intermediate_steps = kwargs.pop("intermediate_steps")
        thoughts = ""
        for action, observation in intermediate_steps:
            thoughts += action.log
            thoughts += f"\nObservation: {observation}\nThought: "
        kwargs["agent_scratchpad"] = thoughts
        kwargs["tools"] = "\n".join(
            [f"{tool.name}: {tool.description}" for tool in self.tools]
        )
        kwargs["tool_names"] = ", ".join([tool.name for tool in self.tools])
        formatted = self.template.format(**kwargs)
        return [HumanMessage(content=formatted)]


class CustomOutputParser(AgentOutputParser):
    def parse(self, llm_output: str) -> Union[AgentAction, AgentFinish]:
        # Check if agent should finish
        if "Final Answer:" in llm_output:
            return AgentFinish(
                # Return values should be a dictionary with an `output` key
                # It is not recommended to try anything else at the moment :)
                return_values={"output": llm_output.split("Final Answer:")[-1].strip()},
                log=llm_output,
            )
        # Parse out the action and action input
        regex = r"Action\s*\d*\s*:(.*?)\nAction\s*\d*\s*Input\s*\d*\s*:[\s]*(.*)"
        match = re.search(regex, llm_output, re.DOTALL)
        if not match:
            return AgentFinish(
                return_values={"output": llm_output},
                log=llm_output,
            )

        action = match.group(1).strip()
        action_input = match.group(2)
        # Return the action and action input
        return AgentAction(
            tool=action, tool_input=action_input.strip(" ").strip('"'), log=llm_output
        )


class LLMSingleActionAgent(BaseSingleActionAgent):
    llm_chain: LLMChain
    output_parser: AgentOutputParser
    stop: List[str]

    @property
    def input_keys(self) -> List[str]:
        return list(set(self.llm_chain.input_keys) - {"intermediate_steps"})

    def plan(
        self,
        intermediate_steps: List[Tuple[AgentAction, str]],
        callbacks: Callbacks = None,
        **kwargs: Any,
    ) -> Union[AgentAction, AgentFinish]:
        """Given input, decided what to do.

        Args:
            intermediate_steps: Steps the LLM has taken to date,
                along with observations
            callbacks: Callbacks to run.
            **kwargs: User inputs.

        Returns:
            Action specifying what tool to use.
        """
        try:
            output = self.llm_chain.run(
                intermediate_steps=intermediate_steps,
                stop=self.stop,
                callbacks=callbacks,
                **kwargs,
            )
        except openai.error.InvalidRequestError:
            return "Your request is invalid, it might exceed my capabilities."
        try:
            return self.output_parser.parse(output)
        except ValueError:
            return "A parsing error happened, sorry"

    async def aplan(
        self,
        intermediate_steps: List[Tuple[AgentAction, str]],
        callbacks: Callbacks = None,
        **kwargs: Any,
    ) -> Union[AgentAction, AgentFinish]:
        pass

    def tool_run_logging_kwargs(self) -> Dict:
        return {
            "llm_prefix": "",
            "observation_prefix": "" if len(self.stop) == 0 else self.stop[0],
        }


def create_agent(config: dict[str, Any]) -> AgentExecutor:
    tools = define_tools(config)
    prompt = CustomPromptTemplate(
        template=get_prompt_template(config),
        tools=tools,
        # This omits the `agent_scratchpad`, `tools`, and `tool_names` variables because those are generated dynamically
        # This includes the `intermediate_steps` variable because that is needed
        input_variables=["input", "intermediate_steps"],
    )
    output_parser = CustomOutputParser()
    gpt4_llm = ChatOpenAI(model_name="gpt-4", temperature=0.25)
    llm_chain = LLMChain(llm=gpt4_llm, prompt=prompt)
    tool_names = [tool.name for tool in tools]
    agent = LLMSingleActionAgent(
        llm_chain=llm_chain,
        output_parser=output_parser,
        stop=["\nObservation:"],
        allowed_tools=tool_names,
    )
    agent_executor = AgentExecutor.from_agent_and_tools(
        agent=agent, tools=tools, verbose=True
    )

    return agent_executor
