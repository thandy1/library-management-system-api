"""Temporary in-memory storage shared by the API routers."""


from app.schemas.books import BookResponse
from app.schemas.members import MemberResponse


# Using dictionaries for O(1) ID-based lookups instead of lists
# which would require iterating through the collection each time.
members: dict[int, MemberResponse] = {
    1: MemberResponse(
        id=1,
        name="John Doe",
        email="john@example.com",
        membership_id="MEM001",
        phone="555-123-4567"
    ),
    2: MemberResponse(
        id=2,
        name="Jane Smith",
        email="jane@example.com",
        membership_id="MEM002",
        phone="555-234-5678"
    ),
    3: MemberResponse(
        id=3,
        name="Bob Johnson",
        email="bob@example.com",
        membership_id="MEM003",
        phone="555-345-6789"
    )
}


books: dict[int, BookResponse] = {
    1: BookResponse(
        id=1,
        title="The Great Gatsby",
        author="F. Scott Fitzgerald",
        isbn="9780743273565",
        published_year=1925,
        member_id=1
    ),
    2: BookResponse(
        id=2,
        title="1984",
        author="George Orwell",
        isbn="9780451524935",
        published_year=1949,
        member_id=1
    ),
    3: BookResponse(
        id=3,
        title="To Kill a Mockingbird",
        author="Harper Lee",
        isbn="9780061120084",
        published_year=1960,
        member_id=2
    ),
    4: BookResponse(
        id=4,
        title="Pride and Prejudice",
        author="Jane Austen",
        isbn="9780141439518",
        published_year=1813,
        member_id=3
    )
}