import typing

from fastapi import FastAPI

class AsgiApp(FastAPI):

    def __init__(self):
        super().__init__()
        self.app: typing.Callable = None

    def _register_app(self, app):
        self.app = app