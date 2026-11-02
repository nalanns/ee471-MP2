class ItemNotFoundError(Exception):
    """Raised when no item with the given id exists in the collection."""


class ItemStateError(Exception):
    """Raised when an action is not allowed in the item's current state."""


class MediaItem:
    """A generic item in a library that can be checked out and returned."""

    TYPE = "media"
    EDITABLE_FIELDS = ("title", "author")

    def __init__(self, title, author, is_available=True):
        """Create an item with a title, an author and an availability status."""
        self.id = None
        self.title = title
        self.author = author
        self.is_available = is_available

    def checkout(self):
        """Check the item out and return a success message, or raise ItemStateError if it is already out."""
        if not self.is_available:
            raise ItemStateError(f"Item {self.id} is already checked out.")
        self.is_available = False
        return "Successful checkout"

    def return_item(self):
        """Mark the item as available again, or raise ItemStateError if it is not checked out."""
        if self.is_available:
            raise ItemStateError(f"Item {self.id} is not checked out.")
        self.is_available = True
        return "Successful return"

    def to_dict(self):
        """Return the item as a dictionary."""
        return {
            "id": self.id,
            "type": self.TYPE,
            "title": self.title,
            "author": self.author,
            "is_available": self.is_available,
        }

    def __str__(self):
        """Return the item as 'Title by Author [Available/Checked Out]'."""
        status = "Available" if self.is_available else "Checked Out"
        return f"{self.title} by {self.author} [{status}]"


class Book(MediaItem):
    """A library item that also keeps its page count."""

    TYPE = "book"
    EDITABLE_FIELDS = MediaItem.EDITABLE_FIELDS + ("page_count",)

    def __init__(self, title, author, page_count, is_available=True):
        """Create a book with a title, an author and a page count."""
        super().__init__(title, author, is_available)
        self.page_count = page_count

    def to_dict(self):
        """Return the item as a dictionary including the page count."""
        data = super().to_dict()
        data["page_count"] = self.page_count
        return data

    def __str__(self):
        """Return the item description followed by the page count."""
        return f"{super().__str__()} - {self.page_count} pages"


class DVD(MediaItem):
    """A library item that also keeps its duration and needs careful handling."""

    TYPE = "dvd"
    EDITABLE_FIELDS = MediaItem.EDITABLE_FIELDS + ("duration",)

    def __init__(self, title, author, duration, is_available=True):
        """Create a DVD with a title, an author and a duration in minutes."""
        super().__init__(title, author, is_available)
        self.duration = duration

    def checkout(self):
        """Check the DVD out and return the success message with a care reminder."""
        result = super().checkout()
        return f"{result}. Handle with care: Do not scratch the disc."

    def to_dict(self):
        """Return the item as a dictionary including the duration."""
        data = super().to_dict()
        data["duration"] = self.duration
        return data


class LibraryCollection:
    """A container that holds library items."""

    ITEM_TYPES = ("book", "dvd")

    def __init__(self):
        """Create an empty collection."""
        self.items = []
        self._next_id = 1

    def add_item(self, item):
        """Add a MediaItem or any of its subclasses to the collection and return its new id."""
        item.id = self._next_id
        self._next_id += 1
        self.items.append(item)
        return item.id

    def get_item(self, item_id):
        """Return the item with the given id, or raise ItemNotFoundError."""
        for item in self.items:
            if item.id == item_id:
                return item
        raise ItemNotFoundError(f"Item {item_id} not found.")

    def list_items(self, available=None, item_type=None):
        """Return the items, optionally filtered by availability and/or type ('book' or 'dvd')."""
        if item_type is not None and item_type not in self.ITEM_TYPES:
            raise ValueError(f"Invalid item_type '{item_type}'. Use one of: {', '.join(self.ITEM_TYPES)}.")
        if available is not None and not isinstance(available, bool):
            raise ValueError("available must be true or false.")
        result = self.items
        if available is not None:
            result = [item for item in result if item.is_available == available]
        if item_type is not None:
            result = [item for item in result if item.TYPE == item_type]
        return list(result)

    def list_available(self):
        """Return the titles of all items that are currently available."""
        return [item.title for item in self.list_items(available=True)]

    @staticmethod
    def _clean_value(name, value):
        """Return the cleaned value of an editable field, or raise ValueError if it is invalid."""
        if name in ("title", "author"):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string.")
            return value.strip()
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(f"{name} must be a positive integer.")
        return value

    def create_item(self, data):
        """Build a Book or DVD from a dict with type, title, author and page_count or duration, add it and return it."""
        if not isinstance(data, dict):
            raise ValueError("Item data must be an object.")
        classes = {"book": Book, "dvd": DVD}
        item_type = data.get("type")
        if item_type not in classes:
            raise ValueError(f"type must be one of: {', '.join(classes)}.")
        item_class = classes[item_type]
        fields = {name: value for name, value in data.items() if name != "type"}
        unknown = [name for name in fields if name not in item_class.EDITABLE_FIELDS]
        if unknown:
            raise ValueError(f"Field '{unknown[0]}' is not allowed on a {item_type}.")
        missing = [name for name in item_class.EDITABLE_FIELDS if name not in fields]
        if missing:
            raise ValueError(f"Missing required field(s): {', '.join(missing)}.")
        cleaned = {name: self._clean_value(name, value) for name, value in fields.items()}
        item = item_class(**cleaned)
        self.add_item(item)
        return item

    def update_item(self, item_id, **fields):
        """Update the editable fields of an item and return it, or raise ValueError for invalid changes."""
        item = self.get_item(item_id)
        if not fields:
            raise ValueError("No fields to update.")
        # Validate every field first so a bad field leaves the item unchanged.
        cleaned = {}
        for name, value in fields.items():
            if name not in item.EDITABLE_FIELDS:
                raise ValueError(f"Field '{name}' cannot be updated on a {item.TYPE}.")
            cleaned[name] = self._clean_value(name, value)
        for name, value in cleaned.items():
            setattr(item, name, value)
        return item

    def replace_item(self, item_id, **fields):
        """Replace all editable fields of an item and return it, or raise ValueError if any is missing or invalid."""
        item = self.get_item(item_id)
        missing = [name for name in item.EDITABLE_FIELDS if name not in fields]
        if missing:
            raise ValueError(f"Missing required field(s): {', '.join(missing)}.")
        return self.update_item(item_id, **fields)

    def remove_item(self, item_id):
        """Remove the item with the given id, or raise ItemStateError if it is checked out."""
        item = self.get_item(item_id)
        if not item.is_available:
            raise ItemStateError(f"Item {item_id} is checked out and cannot be removed.")
        self.items.remove(item)
