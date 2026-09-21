"""Temporary in-memory storage shared by the API routers."""


from app.schemas.books import BookResponse
from app.schemas.members import MemberResponse


# Using dictionaries for O(1) ID-based lookups instead of lists
# which would require iterating through the collection each time.
books: dict[int, BookResponse] = {
    1: BookResponse(
        id=1,
        title="The Great Gatsby",
        author="F. Scott Fitzgerald",
        isbn="9780743273565",
        published_year=1925,
        member_id=1
    )
}


members: dict[int, MemberResponse] = {
    1: MemberResponse(
        id=1,
        name="John Doe",
        email="john@example.com",
        membership_id="MEM001",
        phone="555-1234"
    )
}