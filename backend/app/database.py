import os

from dotenv import load_dotenv  # type: ignore[reportMissingImports]
from sqlalchemy import create_engine  # type: ignore[reportMissingImports]
from sqlalchemy.orm import sessionmaker  # type: ignore[reportMissingImports]

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)