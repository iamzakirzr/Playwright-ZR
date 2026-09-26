"""Repository for the ``users`` table."""

from db.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository):
    """Reads and writes store users."""

    def find_by_username(self, username: str) -> dict | None:
        """The user row for ``username``, or None."""
        return self.fetch_one("SELECT * FROM users WHERE username = ?", (username,))

    def create(self, username: str, email: str, is_locked: bool = False) -> int:
        """Insert a user and return its id. Constraint violations raise ``sqlite3.IntegrityError``."""
        return self.execute(
            "INSERT INTO users (username, email, is_locked) VALUES (?, ?, ?)",
            (username, email, int(is_locked)),
        )

    def lock(self, username: str) -> None:
        """Mark a user as locked out."""
        self.execute("UPDATE users SET is_locked = 1 WHERE username = ?", (username,))

    def delete(self, user_id: int) -> None:
        """Delete a user; their orders cascade (ON DELETE CASCADE)."""
        self.execute("DELETE FROM users WHERE id = ?", (user_id,))

    def count(self) -> int:
        """Total number of users."""
        return self.scalar("SELECT COUNT(*) FROM users")

    def locked_usernames(self) -> list[str]:
        """Usernames of every locked account."""
        return [r["username"] for r in self.fetch_all("SELECT username FROM users WHERE is_locked = 1")]
