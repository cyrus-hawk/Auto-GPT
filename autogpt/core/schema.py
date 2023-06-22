import enum
import uuid
from typing import Any, Callable, Dict, List, Literal, MutableSet, Optional, Sequence

import numpy as np
import pydantic


class PolyBaseModel(pydantic.BaseModel):
    """
    A Pydantic base model designed to handle polymorphic deserialization.

    The purpose of this model is to allow dynamic parsing of subclasses based on input data.
    This model should be subclassed by all models that need to support dynamic parsing,
    and those subclasses should be added as nested models to other Pydantic models.
    The subclasses should have a unique 'type' field in the input data to identify them.

    The class uses the 'type' field in the input data to determine which subclass to parse the data into.
    If 'type' field is not present in the data, it will attempt to parse the data into each subclass
    until successful validation, or raise a ValueError if no subclasses validate successfully.

    :method __get_validators__: Pydantic models use this method to get a list of validators for the model.
    This method is overridden to yield the custom validate method defined in the class.

    :method validate: This method is used to validate the input data. The method checks if the input is a dict,
    checks for 'type' field in the dict and if present, parses the data into the corresponding subclass.
    If 'type' field is not present, it tries to parse the data into each of the subclasses until it succeeds.
    """

    @classmethod
    def __get_validators__(cls):
        # __get_validators__ should yield all validator functions for the model.
        # In this case, we are just using the custom `validate` method below.
        yield cls.validate

    @classmethod
    def validate(cls, v: dict) -> Any:
        """
        Validate that the input can be parsed into one of the subclasses.

        :param v: The input data to validate.
        :return: An instance of one of the subclasses.
        :raise ValueError: Raised if the input data is not a dict or if it doesn't match any subclass.
        """

        # # Input data should be a dict.
        # if not isinstance(v, dict):
        #     raise ValueError("Must be a dict")

        # Check all subclasses to find a match.
        for subclass in cls.__subclasses__():
            # If 'type' field is present, and it matches the subclass name,
            # parse the data into that subclass.
            if "type" in v:
                type_value = v.get("type")
                if type_value == subclass.__name__:
                    # Remove 'type' from dict as it's not a field of the subclass model.
                    del v["type"]
                    return subclass(**v)
            else:
                # If 'type' is not present, try parsing the data into the subclass.
                # If it fails, continue to the next subclass.
                try:
                    return subclass(**v)
                except pydantic.ValidationError:
                    # Suppressing the error as we are brute force trying
                    # all subclasses until one fits
                    pass

        # If the data doesn't match any subclass, raise an error.
        raise ValueError("None of the subclasses match")


############################
####### Mind Schema ########
############################
class BasePlanStep(PolyBaseModel):
    """A class for plan steps."""

    name: str
    prompt: str


class BaseStepResults(PolyBaseModel):
    """A class for plan step results."""

    prompt: str
    variables: Dict[str, str]


class BasePlan(PolyBaseModel):
    """A class for plans."""

    steps: List[BasePlanStep]
    deliverables: List[str]


class BaseGoal(PolyBaseModel):
    """A class for goals."""

    name: str
    objectives: List[str]


class BaseIntrospection(PolyBaseModel):
    """A class for introspection on a plan."""

    plan_efficiency: float
    plan_effectiveness: float
    success_probability: float


class BaseMind(PolyBaseModel):
    """
    The mind is the core of the agent. It is responsible for planning, executing, and introspecting on a goal.

    params:
        goal: The goal to achieve.
        plan: The plan to achieve the goal, as calculated by the agent.
        introspection: The introspection on the plan, as calculated by the agent.

        prompt_loader: The prompt loader to use to load the planning, step execution and introspection prompts

        id: The id of the mind.
        name: The name of the mind.
        description: The description of the mind.

        memory: The memory system for the mind.
        workspace: The workspace system for the mind.
        message_broker: The message broker for the mind.

    methods:

        plan: Generates a plan given a goal loading the prompt using the prompt loader.
        execute: Executes a plan, the details of which are implementation specific.
        introspect: Introspects on a plan given a goal loading the prompt using the prompt loader.
        spawn_sub_mind: Spawns a sub mind.
    """

    goal: BaseGoal
    plan: Optional[BasePlan] = None

    prompt_loader: "BasePromptEngine"

    id: str
    name: str
    description: str

    memory: str
    workspace: str
    message_broker: "BaseMessageBroker"

    sub_minds: List["BaseMind"] = []

    async def plan(self) -> BasePlan:
        """Implement logic to generate a plan given a goal."""
        raise NotImplementedError

    async def execute(self) -> None:
        """Implement logic to execute a plan."""
        raise NotImplementedError

    async def introspect(self) -> BaseIntrospection:
        """Implement logic to introspect on a plan given a goal."""
        raise NotImplementedError

    async def spawn_sub_mind(self, goal: BaseGoal, channel_id: str) -> None:
        """Spawns a sub mind with the given goal and channel id."""
        raise NotImplementedError


############################
##### Memory Schema ########
############################
## copied from @Pwuts work #
############################

# Embedding = list[np.float32] | np.ndarray[Any, np.dtype[np.float32]]
# MemoryDocType = Literal["webpage", "text_file", "code_file", "agent_history"]

# class Message(PolyBaseModel):
#     """OpenAI Message object containing a role and the message content"""
#     role: str
#     content: str

# class MemoryItem(PolyBaseModel):
#     """Memory object containing raw content as well as embeddings"""

#     raw_content: str
#     summary: str
#     chunks: list[str]
#     chunk_summaries: list[str]
#     e_summary: Embedding
#     e_chunks: list[Embedding]
#     metadata: dict

#     async def get_relevance(self, query: str, e_query: Embedding) -> "MemoryItemRelevance":
#         """Get the relevance of a memory item to a query"""
#         raise NotImplementedError

#     # @staticmethod
#     # async def from_text(
#     #     text: str,
#     #     source_type: MemoryDocType,
#     #     metadata: Optional[dict] = None,
#     #     how_to_summarize: Optional[str] = None,
#     #     question_for_summary: Optional[str] = None,
#     # ) -> "MemoryItem":
#     #     """Create a memory item from text"""
#     #     raise NotImplementedError

#     # @staticmethod
#     # async def from_text_file(content: str, path: str) -> "MemoryItem":
#     #     """Create a memory item from a text file"""
#     #     return MemoryItem.from_text(content, "text_file", {"location": path})

#     # @staticmethod
#     # async def from_code_file(content: str, path: str) -> "MemoryItem":
#     #     """Create a memory item from a code file"""
#     #     # TODO: implement tailored code memories
#     #     return MemoryItem.from_text(content, "code_file", {"location": path})

#     # @staticmethod
#     # async def from_ai_action(ai_message: Message, result_message: Message) -> "MemoryItem":
#     #     """
#     #     The result_message contains either user feedback
#     #     or the result of the command specified in ai_message
#     #     """
#     #     return NotImplementedError

#     # @staticmethod
#     # async def from_webpage(content: str, url: str, question: Optional[str]= None) -> "MemoryItem":
#     #     """Create a memory item from a webpage"""
#     #     return MemoryItem.from_text(
#     #         text=content,
#     #         source_type="webpage",
#     #         metadata={"location": url},
#     #         question_for_summary=question,
#     #     )

#     def __str__(self) -> str:
#         """String representation of a memory item"""
#         raise NotImplementedError

# class MemoryItemRelevance:
#     """
#     Class that encapsulates memory relevance search functionality and data.
#     Instances contain a MemoryItem and its relevance scores for a given query.
#     """

#     memory_item: MemoryItem
#     for_query: str
#     summary_relevance_score: float
#     chunk_relevance_scores: list[float]

#     # @staticmethod
#     # def of(
#     #     memory_item: MemoryItem, for_query: str, e_query: Embedding | None = None
#     # ) -> "MemoryItemRelevance":
#     #     """Create a MemoryItemRelevance instance for a given query"""
#     #     return NotImplementedError

#     # @staticmethod
#     # def calculate_scores(
#     #     memory: MemoryItem, compare_to: Embedding
#     # ) -> tuple[float, float, list[float]]:
#     #     """
#     #     Calculates similarity between given embedding and all embeddings of the memory
#     #     Returns:
#     #         float: the aggregate (max) relevance score of the memory
#     #         float: the relevance score of the memory summary
#     #         list: the relevance scores of the memory chunks
#     #     """
#     #     return NotImplementedError

#     @property
#     def score(self) -> float:
#         """The aggregate relevance score of the memory item for the given query"""
#         return NotImplementedError

#     @property
#     def most_relevant_chunk(self) -> tuple[str, float]:
#         """The most relevant chunk of the memory item + its score for the given query"""
#         return NotImplementedError


# class BaseMemoryProvider(PolyBaseModel):
#     """Base class for memory systems."""

#     def get(self, query: str) -> Optional[MemoryItemRelevance]:
#         """
#         Gets the data from the memory that is most relevant to the given query.
#         Args:
#             data: The data to compare to.
#         Returns: The most relevant Memory
#         """
#         return NotImplementedError

#     def get_relevant(self, query: str, k: int) -> Sequence[MemoryItemRelevance]:
#         """
#         Returns the top-k most relevant memories for the given query
#         Args:
#             query: the query to compare stored memories to
#             k: the number of relevant memories to fetch
#         Returns:
#             list[MemoryItemRelevance] containing the top [k] relevant memories
#         """
#         return NotImplementedError

#     def score_memories_for_relevance(
#         self, for_query: str,
#     ) -> Sequence[MemoryItemRelevance]:
#         """
#         Returns MemoryItemRelevance for every memory in the index.
#         Implementations may override this function for performance purposes.
#         """
#         return NotImplementedError

#     def get_stats(self) -> tuple[int, int]:
#         """
#         Returns:
#             tuple (n_memories: int, n_chunks: int): the stats of the memory index
#         """
#         return NotImplementedError

#     def add(self, memory: MemoryItem) -> None:
#         """
#         Adds a memory to the memory index
#         Args:
#             memory: the memory to add
#         """
#         return NotImplementedError

#     def discard(self, memory: MemoryItem) -> None:
#         """
#         Removes a memory from the memory index
#         Args:
#             memory: the memory to remove
#         """
#         return NotImplementedError

#     def clear(self) -> None:
#         """Clears the memory index"""
#         return NotImplementedError


############################
### Prompt Loader Schema ###
############################


class BasePromptEngine(PolyBaseModel):
    """A base class for prompt loaders."""

    directory: str

    def load_prompt(self, prompt_name: str) -> str:
        """Loads a prompt."""
        raise NotImplementedError

    def generate_prompt(self, prompt_template: str, data: dict) -> str:
        """Generates a prompt."""
        raise NotImplementedError


############################
### LLM Provider Schema ####
############################


class BaseLLMProvider(PolyBaseModel):
    """The base class for all LLM providers."""

    async def chat(self, messages: list) -> str:
        """Send a query to the LLM provider"""
        raise NotImplementedError


class BaseEmbeddingProvider(PolyBaseModel):
    """The base class for Embedding Providers."""

    async def get_embedding(self, messages: list) -> str:
        """Create a chat completion"""
        raise NotImplementedError


############################
##### Abilities Schema #####
############################
class AbilityResult(PolyBaseModel):
    """A result from an ability execution."""

    ok: bool
    message: str


class BaseAbility(PolyBaseModel):
    """Base class for abilities the agent can perform."""

    name: str
    description: str
    # abstract concept of cost for agent planning
    # High values make ability less likely to be chosen
    initiative_cost: int
    method: Callable[..., Any]
    signature: str
    enabled: bool

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        raise NotImplementedError


class BaseAbilityRegistry(PolyBaseModel):
    """A registry for abilities."""

    AUTO_GPT_ABILITY_IDENTIFIER: str = "auto_gpt_ability"
    abilities: dict[str, BaseAbility] = {}

    def register_ability(self, ability: BaseAbility) -> None:
        """Registers a ability with the ability registry."""
        self.abilities[ability.name] = ability

    def list_abilities(self) -> None:
        """Lists all the abilities in the ability registry."""
        raise NotImplementedError

    def get_ability(self, ability_name: str) -> BaseAbility:
        """Gets a ability from the ability registry."""
        raise NotImplementedError

    def execute_ability(self, ability_name: str, **kwargs) -> AbilityResult:
        """Executes a ability from the ability registry."""
        raise NotImplementedError

    def import_abilities(self, module_name: str) -> None:
        """Imports abilities from a module."""
        raise NotImplementedError


############################
##### Messaging Schema #####
############################


class BaseMessage(PolyBaseModel):
    """Base class for a message that can be sent and received on a channel."""

    from_uid: str
    to_uid: str
    timestamp: int


class BaseMessageChannel(PolyBaseModel):
    """Base class for a channel that messages can be sent and received on"""

    id: str
    name: str
    host: str
    port: int

    # Channel statistics
    sent_message_count: int = 0
    sent_bytes_count: int = 0
    received_message_count: int = 0
    received_bytes_count: int = 0

    def __str__(self) -> str:
        f"Channel {self.name}:({self.id}) on {self.host}:{self.port}"
        return f"Channel {self.name}:({self.id}) on {self.host}:{self.port}"

    async def get(self) -> None:
        """Gets a message from the channel."""
        raise NotImplementedError

    async def send(self) -> None:
        """Sends a message to the channel."""
        raise NotImplementedError


class BaseMessageBroker(PolyBaseModel):
    """Base class for message brokers that holds all the channels an agent can communicate on."""

    channels: list[BaseMessageChannel] = []

    class Config:
        """
        Config class is a configuration class for Pydantic models.
        """

        arbitrary_types_allowed = True

    def list_channels(self) -> None:
        """Lists all the channels."""
        raise NotImplementedError

    def get_channel(self, channel_uid: str) -> BaseMessageChannel:
        """Gets a channel."""
        raise NotImplementedError

    def get_channel_by_name(self, channel_name: str) -> BaseMessageChannel:
        """Gets a channel by name."""
        raise NotImplementedError

    def add_channel(self, channel: BaseMessageChannel) -> None:
        """Adds a channel."""
        raise NotImplementedError

    async def get_from_channel(self, channel_uid: str) -> BaseMessage:
        """Gets a message from a channel."""
        raise NotImplementedError

    async def send_to_channel(self, channel_uid: str, message: BaseMessage) -> None:
        """Sends a message to a channel."""
        raise NotImplementedError


############################
####### Agent Schema #######
############################


class BaseAgent(PolyBaseModel):
    """A Base Agent Class"""

    name: str
    uid: str = str(uuid.uuid4())
    session_id: str = str(uuid.uuid4())
    message_broker: BaseMessageBroker

    async def run(self) -> None:
        """Runs the agent"""
        raise NotImplementedError

    async def stop(self) -> None:
        """Stops the agent"""
        raise NotImplementedError
