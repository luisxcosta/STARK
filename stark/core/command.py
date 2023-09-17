from __future__ import annotations
from types import GeneratorType, AsyncGeneratorType
from typing import Callable, Awaitable, Any, Protocol
from functools import wraps
import warnings
from uuid import UUID, uuid4
from enum import auto, Enum
from datetime import datetime
import inspect

from pydantic import BaseModel, Field
import asyncer

from general.classproperty import classproperty
from .patterns import Pattern


AwaitResponse = Awaitable['Response | None']
AsyncCommandRunner = Callable[..., AwaitResponse]
CommandRunner = Callable[..., 'Response | None'] | AsyncCommandRunner

class Command:
    name: str
    pattern: Pattern
    _runner: CommandRunner

    def __init__(self, name: str, pattern: Pattern, runner: CommandRunner):
        assert isinstance(pattern, Pattern)
        self.name = name
        self.pattern = pattern
        self._runner = runner

    def run(self, parameters_dict: dict[str, Any] | None = None, / , **kwparameters: dict[str, Any]) -> AwaitResponse:
        # allow call both with and without dict unpacking 
        # e.g. command.run(foo = bar, lorem = ipsum), command.run(**parameters) and command.run(parameters)
        # where parameters is dict {'foo': bar, 'lorem': ipsum}
        
        parameters = parameters_dict or {}
        parameters.update(kwparameters)
        
        runner: AsyncCommandRunner
        
        if inspect.iscoroutinefunction(self._runner) or isinstance(self._runner, AsyncGeneratorType):
             # async functions (coroutines) and async generators are remain as is
            runner = self._runner
        else:
            # sync functions are wrapped with asyncer.asyncify to make them async (coroutines)
            # async generators are not supported yet by asyncer.asyncify (https://github.com/tiangolo/asyncer/discussions/86)
            runner = asyncer.asyncify(self._runner) # type: ignore
            
        if any(p.kind == p.VAR_KEYWORD for p in inspect.signature(self._runner).parameters.values()):
            # if command runner accepts **kwargs, pass all parameters
            coroutine = runner(**parameters)
        else:
            # otherwise pass only parameters that are in command runner signature to prevent TypeError: got an unexpected keyword argument
            coroutine = runner(**{k: v for k, v in parameters.items() if k in self._runner.__annotations__})
            
        @wraps(runner)
        async def coroutine_wrapper() -> Response | None:
            response = await coroutine
            if isinstance(response, GeneratorType):
                message = f'[WARNING] Command {self} is a sync GeneratorType that is not fully supported and may block the main thread. ' + \
                            'Consider using the ResponseHandler.respond() or async approach instead.'
                warnings.warn(message, UserWarning)
            return response
            
        return coroutine_wrapper()
    
    def __call__(self, *args, **kwargs) -> AwaitResponse:
        # just syntactic sugar for command(...) instead of command.run(...)
        return self.run(*args, **kwargs)
    
    def __repr__(self):
        return f'<Command {self.name}>'

class ResponseStatus(Enum):
    none = auto()
    not_found = auto()
    failed = auto()
    success = auto()
    info = auto()
    error = auto()

class Response(BaseModel):
    voice: str = ''
    text: str = ''
    status: ResponseStatus = ResponseStatus.success
    needs_user_input: bool = False
    commands: list[Command] = []
    parameters: dict[str, Any] = {}
    
    id: UUID = Field(default_factory=uuid4)
    time: datetime = Field(default_factory=datetime.now)
    
    _repeat_last: Response | None = None # static instance
    
    @classproperty
    def repeat_last(cls) -> Response:
        if not Response._repeat_last:
            Response._repeat_last = Response()
            return Response._repeat_last
        return Response._repeat_last
    
    class Config:
        arbitrary_types_allowed = True
    
    def __eq__(self, other):
        return self.id == other.id
        
class ResponseHandler(Protocol):
    def respond(self, response: Response): pass
    def unrespond(self, response: Response): pass
    def pop_context(self): pass

class AsyncResponseHandler(Protocol):
    async def respond(self, response: Response): pass
    async def unrespond(self, response: Response): pass
    async def pop_context(self): pass
