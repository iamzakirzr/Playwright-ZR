from db.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository):
    def find_by_username(self, username: str) -> dict | None:
        return self.fetch_one("SELECT * FROM users WHERE username = ?", (username,))

    def create(self, username: str, email: str, is_locked: bool = False) -> int:
        return self.execute(
            "INSERT INTO users (username, email, is_locked) VALUES (?, ?, ?)",
            (username, email, int(is_locked)),
        )

    def lock(self, username: str) -> None:
        self.execute("UPDATE users SET is_locked = 1 WHERE username = ?", (username,))

    def delete(self, user_id: int) -> None:
        self.execute("DELETE FROM users WHERE id = ?", (user_id,))

    def count(self) -> int:
        return self.scalar("SELECT COUNT(*) FROM users")

    def locked_usernames(self) -> list[str]:
        return [r["username"] for r in self.fetch_all("SELECT username FROM users WHERE is_locked = 1")]
