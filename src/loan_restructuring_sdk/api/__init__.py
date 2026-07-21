"""FastAPI HTTP layer: exposes the SDK over REST.

Kept fully separate from business logic -- routers only translate HTTP <->
`LoanRestructuringSDK.process_case()`; `dependencies.py` is where the
object graph is wired via Dependency Injection.
"""
