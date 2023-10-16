from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from .. import models, schema, utils
from ..database import engine, get_db
from sqlalchemy.orm import Session

router = APIRouter(
    tags=['Warp Users']
)

#   Create a User

@router.post("/users", status_code=status.HTTP_201_CREATED, response_model=schema.UserOut)
async def create_user(user: schema.UserCreate, db:Session = Depends(get_db)):
    user.password = utils.hash(user.password)
    new_user = models.User(**user.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user