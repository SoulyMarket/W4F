"""section 6.4: every route has an explicit role requirement via
require_roles(...), so no route is accidentally public. This test walks
every registered route's dependency tree looking for the marker
require_roles() leaves on the dependency it returns, and fails loudly for
any route that doesn't have one and isn't on the hand-reviewed exemption
list below.

Adding a route to EXEMPT_ROUTES should be rare and deliberate: it means
"this route is intentionally public", which today is true only for login,
refresh (both need to work before the caller has a token) and health.

Route discovery walks app.routes recursively rather than assuming a flat
list of APIRoute: FastAPI mounts an included APIRouter as a wrapper object
(an internal routing-table entry, not an APIRoute itself) whose real routes
live one level down and whose .path doesn't include the router's prefix —
found by inspecting the actual object at test-writing time rather than
assuming the shape from memory. Resolving the full mounted path (prefix
included) goes through app.url_path_for(route.name), which is what's
actually asked for a path's elsewhere in the app anyway.
"""

from fastapi import FastAPI
from fastapi.routing import APIRoute

from app.main import app


def _iter_api_routes(app: FastAPI):
    """Yield every APIRoute reachable from app.routes, however deeply an
    include_router(...) call nested it."""

    def walk(routes):
        for route in routes:
            if isinstance(route, APIRoute):
                yield route
            elif hasattr(route, "original_router"):
                yield from walk(route.original_router.routes)
            elif hasattr(route, "routes"):
                yield from walk(route.routes)

    yield from walk(app.routes)


def _full_path(app: FastAPI, route: APIRoute) -> str:
    try:
        return app.url_path_for(route.name)
    except Exception:
        return route.path


EXEMPT_ROUTES: set[tuple[str, str]] = {
    ("/api/v1/health", "GET"),
    ("/api/v1/auth/login", "POST"),
    ("/api/v1/auth/refresh", "POST"),
}


def _dependant_declares_roles(dependant) -> bool:
    if getattr(dependant.call, "__w4f_required_roles__", None) is not None:
        return True
    return any(_dependant_declares_roles(sub) for sub in dependant.dependencies)


def test_at_least_the_known_routes_are_discovered():
    """Sanity check on _iter_api_routes itself: if route discovery breaks
    (e.g. a future FastAPI version reshapes routing again), both coverage
    tests below would vacuously pass over zero routes. Fail loudly instead."""
    paths = {_full_path(app, r) for r in _iter_api_routes(app)}
    assert "/api/v1/health" in paths
    assert "/api/v1/auth/login" in paths
    assert "/api/v1/auth/me" in paths


def test_every_route_declares_roles_except_the_exempt_list():
    uncovered: list[str] = []
    for route in _iter_api_routes(app):
        full_path = _full_path(app, route)
        for method in route.methods - {"HEAD", "OPTIONS"}:
            if (full_path, method) in EXEMPT_ROUTES:
                continue
            if not _dependant_declares_roles(route.dependant):
                uncovered.append(f"{method} {full_path}")

    assert not uncovered, (
        "Routes with no explicit require_roles(...) and not on the "
        f"exemption list: {uncovered}"
    )


def test_detection_logic_actually_flags_an_unguarded_route():
    """Proves the coverage test isn't vacuously green: build a throwaway
    app with one route that has no require_roles(...) anywhere in its
    dependency tree, and confirm the same detection logic used above
    flags it. Without this, a bug that made _dependant_declares_roles
    always return True would pass the real coverage test silently."""
    from fastapi import Depends

    from app.api.deps import require_roles
    from app.models.enums import UserRole

    probe = FastAPI()

    @probe.get("/guarded")
    def guarded(_: None = Depends(require_roles(UserRole.ADMIN))) -> dict:
        return {}

    @probe.get("/unguarded")
    def unguarded() -> dict:
        return {}

    results = {
        route.path: _dependant_declares_roles(route.dependant)
        for route in _iter_api_routes(probe)
    }
    assert results["/guarded"] is True
    assert results["/unguarded"] is False


def test_exempt_routes_still_exist():
    """Guards against the exemption list silently going stale (e.g. a
    renamed path) by requiring every entry to match a real route."""
    all_routes = {
        (_full_path(app, route), method)
        for route in _iter_api_routes(app)
        for method in route.methods - {"HEAD", "OPTIONS"}
    }
    missing = EXEMPT_ROUTES - all_routes
    assert not missing, f"Exempt routes that no longer exist: {missing}"
