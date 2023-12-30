import os
import datetime
from typing import Annotated

import requests
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse, Response

from instigpt import config, db
from . import helpers

router = APIRouter()


@router.get("/login")
def login(code: str, response: Response):
    if code == "":
        return JSONResponse({"message": "code is empty"}, status_code=400)

    # Get access token
    token_res = requests.post(
        os.environ["SSO_TOKEN_URL"],
        data={
            "code": code,
            "redirect_uri": os.environ["SSO_REDIRECT_URL"],
            "grant_type": "authorization_code",
        },
        headers={
            "Authorization": "Basic " + os.environ["SSO_AUTHORIZATION_HEADER_B64"],
            "Content-Type": "application/x-www-form-urlencoded",
        },
        timeout=10,
    )
    token_res = token_res.json()

    # Ensure we have the access token
    if "access_token" not in token_res:
        response.status_code = 400
        return {"error": "unable to retrieve access token"}

    # Get the user's profile
    profile_res = requests.get(
        os.environ["SSO_PROFILE_URL"],
        headers={"Authorization": "Bearer " + token_res["access_token"]},
        timeout=10,
    )
    profile_res = profile_res.json()

    # Ensure we have all the required fields
    if not all(
        field in profile_res
        for field in [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "roll_number",
        ]
    ):
        response.status_code = 400
        return {"error": "all field were not present in the response"}

    user = db.user.get_user_by_id(profile_res["id"])
    if user is None:
        user = db.user.User(
            id=profile_res["id"],
            username=profile_res["username"],
            name=profile_res["first_name"] + " " + profile_res["last_name"],
            email=profile_res["email"],
            roll_number=profile_res["roll_number"],
        )
        db.user.create_user(user)

    session = db.session.Session(
        user_id=user.id,
        expires_at=datetime.datetime.now() + datetime.timedelta(days=7),
    )
    db.session.create(session)

    response.set_cookie(
        config.COOKIE_NAME,
        str(session.id),
        max_age=60 * 60 * 24 * 7,
        httponly=True,
    )
    return {"user": user}


@router.get("/logout")
def logout(req: Request, res: Response):
    session_id = req.cookies[config.COOKIE_NAME]
    if session_id is None:
        raise HTTPException(status_code=401, detail="Unauthorized")

    db.session.delete(session_id)
    res.delete_cookie(config.COOKIE_NAME)
    return {"message": "logged out"}


@router.get("/me")
def me(user: Annotated[db.user.User, Depends(helpers.get_user)]):
    return {"user": user}
