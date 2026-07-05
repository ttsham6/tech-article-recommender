from fastapi import Header, HTTPException, status


async def verify_authorization(authorization: str | None = Header(default=None)) -> None:
    """Placeholder auth dependency.

    Replace with LINE ID token or session verification in the next PR.
    """
    if authorization is None:
        return
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
        )
