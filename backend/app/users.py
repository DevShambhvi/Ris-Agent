from sqlalchemy import text

from .database import engine


# ============================================================
# CREATE USER
# ============================================================

def create_user(
    name: str,
    email: str
):
    query = text("""
        INSERT INTO users (
            name,
            email
        )
        VALUES (
            :name,
            :email
        )
        RETURNING
            id,
            name,
            email,
            account_created_at
    """)

    with engine.begin() as connection:

        result = connection.execute(
            query,
            {
                "name": name,
                "email": email
            }
        ).mappings().first()

    if not result:
        raise ValueError("Failed to create user.")

    return dict(result)


# ============================================================
# GET USER
# ============================================================

def get_user(user_id: int):

    query = text("""
        SELECT
            id,
            name,
            email,
            account_created_at
        FROM users
        WHERE id = :user_id
    """)

    with engine.connect() as connection:

        result = connection.execute(
            query,
            {
                "user_id": user_id
            }
        ).mappings().first()

    if not result:
        raise ValueError(
            f"User {user_id} not found."
        )

    return dict(result)


# ============================================================
# GET ALL USERS
# ============================================================

def get_users(limit: int = 100):

    query = text("""
        SELECT
            id,
            name,
            email,
            account_created_at
        FROM users
        ORDER BY id DESC
        LIMIT :limit
    """)

    with engine.connect() as connection:

        results = connection.execute(
            query,
            {
                "limit": limit
            }
        ).mappings().all()

    return [
        dict(row)
        for row in results
    ]