from fastapi import Response, status, HTTPException, Depends, APIRouter
from typing import List, Optional

from sqlalchemy import func
from .. import models, schema, oauth2
from ..database import engine, get_db
from sqlalchemy.orm import Session


router = APIRouter(
    tags=['Warp Posts']
)

#   Get Post by id

@router.get("/posts/{id}", response_model=schema.PostOut)
async def get_post(id: int, db:Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):

    #   Using RAW SQL

    # cursor.execute('''SELECT * FROM warp_db WHERE id = %s''', (str(id),))
    # post = cursor.fetchone()

    # if not post:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post with id {id} does not exist !!!")
    
    # return post    


    #   Using SQL Alchemy ORM

    post = db.query(models.Post).filter(models.Post.id == id).first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post with id {id} does not exist !!!")
    
    result = db.query(models.Post, func.count(models.Vote.post_id).label("votes")).join(
        models.Vote, models.Vote.post_id == models.Post.id, isouter=True).group_by(
            models.Post.id).filter(models.Post.id == id).first()

    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post with id {id} does not exist !!!")    
        
    return result


#   Get All Posts    

@router.get("/posts", response_model=List[schema.PostOut])
async def get_posts(db:Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user),
                    limit: int = 10, skip: int = 0, search: Optional[str]=""):

    #   Using RAW SQL

    # cursor.execute('''SELECT * FROM warp_db''')
    # posts = cursor.fetchall()
    # return posts


    #   Using SQL Alchemy ORM

    posts = db.query(models.Post).filter(models.Post.title.contains(
        search)).limit(limit).offset(skip).all()
    
    results = db.query(models.Post, func.count(models.Vote.post_id).label("votes")).join(
        models.Vote, models.Vote.post_id == models.Post.id, isouter=True).group_by(models.Post.id).filter(models.Post.title.contains(
        search)).limit(limit).offset(skip).all()
    
    return results


#   Create a Post

@router.post("/posts", status_code=status.HTTP_201_CREATED, response_model=schema.Post)
async def create_post(post: schema.PostCreate, db:Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):

    #   Using RAW SQL

    # cursor.execute('''INSERT INTO warp_db (title, content, published) VALUES (%s, %s, %s) RETURNING *''', 
    #                (post.title, post.content, post.published))
    # post = cursor.fetchone()
    # conn.commit()
    # return post


    #   Using SQL Alchemy ORM

    new_post = models.Post(owner_id = current_user.id, **post.dict())
    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    return new_post


#   Update a Post

@router.put("/posts", status_code=status.HTTP_202_ACCEPTED, response_model=schema.Post)
async def update_post(post: schema.Post, id: int, db:Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):

    #   Using RAW SQL

    # cursor.execute('''UPDATE warp_db SET title=%s, content=%s, published=%s WHERE id=%s RETURNING *''', 
    #                (post.title, post.content, post.published, str(id),))
    # post = cursor.fetchone()
    # conn.commit()

    # if not post:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post with id {id} does not exist !!!")
    
    # return post


    #   Using SQL Alchemy ORM

    post_query = db.query(models.Post).filter(models.Post.id == id)

    if not post_query.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post with id {id} does not exist !!!")
    
    if post_query.first().owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Not authorized to perform requested action")    
    
    post_query.update(post.dict(), synchronize_session=False)
    db.commit()

    return post_query.first()


#   Delete a Post

@router.delete("/posts", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(id: int, db:Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):

    #   Using RAW SQL

    # cursor.execute('''DELETE FROM warp_db WHERE id = %s RETURNING *''', 
    #                (str(id),))
    # post = cursor.fetchone()
    # conn.commit()

    # if not post:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post wth id {id} does not exist !!!")
    
    # return Response(status_code=status.HTTP_204_NO_CONTENT)


    #   Using SQL Alchemy ORM

    post = db.query(models.Post).filter(models.Post.id == id)

    if not post.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post with id {id} does not exist !!!")
    
    if post.first().owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Not authorized to perform requested action")
        
    post.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)