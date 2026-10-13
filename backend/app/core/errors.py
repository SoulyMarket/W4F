"""Section 5's error contract: every error response is
`{"error": {"code": "...", "message": "..."}}` — `code` a stable English
string, `message` localized. `ApiError` carries both pieces (the i18n key
doubles as the stable code, since both are already stable English
identifiers) and the registered exception handler shapes the envelope, so
every route just raises one exception type instead of hand-building the
envelope at each call site.
"""

from typing import Any

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from app.i18n import t


class ApiError(HTTPException):
    def __init__(self, status_code: int, key: str, lang: str, **params: Any) -> None:
        self.code = key.rsplit(".", 1)[-1]
        message = t(key, lang, **params)
        super().__init__(status_code=status_code, detail=message)


async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.detail}},
    )
