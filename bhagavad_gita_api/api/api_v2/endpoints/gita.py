import os
import logging
import random
from datetime import date
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session, joinedload

from bhagavad_gita_api.api import deps
from bhagavad_gita_api.models import gita as models
from bhagavad_gita_api.models import schemas

logger = logging.getLogger("api")
logger.setLevel(logging.DEBUG)

router = APIRouter()

sanskrit_recitation_host=os.getenv("SANSKRIT_RECITATION_HOST")

@router.get("/chapters/", response_model=List[schemas.GitaChapter], tags=["chapters"])
async def get_all_chapters(
    skip: int = 0,
    limit: int = 18,
    db: Session = Depends(deps.get_db),
):
    chapters = (
        db.query(models.GitaChapter)
        .with_entities(
            models.GitaChapter.id,
            models.GitaChapter.slug,
            models.GitaChapter.name,
            models.GitaChapter.name_transliterated,
            models.GitaChapter.name_translated,
            models.GitaChapter.verses_count,
            models.GitaChapter.chapter_number,
            models.GitaChapter.name_meaning,
            models.GitaChapter.chapter_summary,
        )
        .order_by(models.GitaChapter.id.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return chapters


@router.get(
    "/chapters/{chapter_number}/", response_model=schemas.GitaChapter, tags=["chapters"]
)
async def get_particular_chapter(
    chapter_number: int, db: Session = Depends(deps.get_db)
):
    chapter = (
        db.query(models.GitaChapter)
        .filter(models.GitaChapter.chapter_number == chapter_number)
        .with_entities(
            models.GitaChapter.id,
            models.GitaChapter.slug,
            models.GitaChapter.name,
            models.GitaChapter.name_transliterated,
            models.GitaChapter.name_translated,
            models.GitaChapter.verses_count,
            models.GitaChapter.chapter_number,
            models.GitaChapter.name_meaning,
            models.GitaChapter.chapter_summary,
        )
        .first()
    )
    if chapter is None:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return chapter


# @router.get("/verses/", response_model=List[schemas.GitaVerse], tags=["verses"])
# def get_all_verses_from_all_chapters(
#     skip: int = 0, limit: int = 10, db: Session = Depends(deps.get_db)
# ):
#     verses = (
#         db.query(models.GitaVerse)
#         .options(
#             joinedload(models.GitaVerse.commentaries),
#             joinedload(models.GitaVerse.translations),
#         )
#         .order_by(models.GitaVerse.id.asc())
#         .offset(skip)
#         .limit(limit)
#         .all()
#     )
#     return verses


@router.get(
    "/chapters/{chapter_number}/verses/",
    response_model=List[schemas.GitaVerse],
    tags=["verses"],
)
async def get_all_verses_from_particular_chapter(
    chapter_number: int, db: Session = Depends(deps.get_db)
):
    verses = (
        db.query(models.GitaVerse)
        .options(
            joinedload(models.GitaVerse.commentaries),
            joinedload(models.GitaVerse.translations),
        )
        .order_by(models.GitaVerse.id.asc())
        .filter(models.GitaVerse.chapter_number == chapter_number)
        .all()
    )

    for verse in verses:
        verse.sanskrit_recitation_url= f"{sanskrit_recitation_host}{verse.chapter_number}/{verse.verse_number}.mp3"

    if verses is None:
        raise HTTPException(status_code=404, detail="Verse not found")
    return verses


@router.get(
    "/chapters/{chapter_number}/verses/{verse_number}/",
    response_model=schemas.GitaVerse,
    tags=["verses"],
)
async def get_particular_verse_from_chapter(
    chapter_number: int, verse_number: int, db: Session = Depends(deps.get_db)
):
    verse = (
        db.query(models.GitaVerse)
        .options(
            joinedload(models.GitaVerse.commentaries),
            joinedload(models.GitaVerse.translations),
        )
        .filter(
            models.GitaVerse.chapter_number == chapter_number,
            models.GitaVerse.verse_number == verse_number,
        )
        .first()
    )
    
    verse.sanskrit_recitation_url= f"{sanskrit_recitation_host}{verse.chapter_number}/{verse.verse_number}.mp3"

    if verse is None:
        raise HTTPException(status_code=404, detail="Verse not found")
    return verse


@router.post("/set-daily-verse/", tags=["verses"])
async def set_daily_verse(db: Session = Depends(deps.get_db)):

    verse_order = random.randint(1, 700)

    verse = (
        db.query(models.VerseOfDay)
        .filter(
            models.VerseOfDay.date == date.today(),
        )
        .first()
    )

    if verse is None:
        verse_of_day = models.VerseOfDay(verse_order=verse_order, date=date.today())
        db.add(verse_of_day)
        db.commit()

        return Response(status_code=201, content="Verse of the day has been set.")

    else:
        return Response(
            status_code=200, content="Verse of the day has already been set."
        )


@router.get(
    "/get-daily-verse/",
    response_model=schemas.GitaVerse,
    tags=["verses"],
)
async def get_daily_verse(db: Session = Depends(deps.get_db)):
    verse_of_day = (
        db.query(models.VerseOfDay)
        .filter(
            models.VerseOfDay.date == date.today(),
        )
        .first()
    )

    if verse_of_day:
        verse = (
            db.query(models.GitaVerse)
            .options(
                joinedload(models.GitaVerse.commentaries),
                joinedload(models.GitaVerse.translations),
            )
            .filter(models.GitaVerse.id == verse_of_day.verse_order)
            .first()
        )

        if verse:
            return verse

    raise HTTPException(status_code=404, detail="Verse of the day not found.")
