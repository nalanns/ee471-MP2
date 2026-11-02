from custom_classes import Book, DVD, LibraryCollection, ItemNotFoundError, ItemStateError

library = LibraryCollection()

# add_item
dune_id = library.add_item(Book("Dune", "Frank Herbert", 412))
matrix_id = library.add_item(DVD("The Matrix", "Wachowskis", 136))
hobbit_id = library.add_item(Book("The Hobbit", "J.R.R. Tolkien", 310))
interstellar_id = library.add_item(DVD("Interstellar", "Christopher Nolan", 169))
print("Added ids:", dune_id, matrix_id, hobbit_id, interstellar_id)

# get_item
print("get_item:", library.get_item(dune_id))

# update_item
print("update_item:", library.update_item(hobbit_id, title="The Hobbit (Illustrated)", page_count=320))

# checkout (Book and DVD)
print("checkout book:", library.get_item(dune_id).checkout())
print("checkout dvd:", library.get_item(matrix_id).checkout())

# list_items
print("list_items():", [item.title for item in library.list_items()])
print("list_items(available=True):", [item.title for item in library.list_items(available=True)])
print("list_items(item_type='dvd'):", [item.title for item in library.list_items(item_type="dvd")])

# return_item
print("return_item:", library.get_item(dune_id).return_item())

# to_dict
print("to_dict book:", library.get_item(dune_id).to_dict())
print("to_dict dvd:", library.get_item(matrix_id).to_dict())

# remove_item
library.remove_item(interstellar_id)
print("remove_item:", [item.id for item in library.list_items()])

# Removed ids are not reused
new_id = library.add_item(Book("Neuromancer", "William Gibson", 271))
print(f"New item got id {new_id}, removed id {interstellar_id} was not reused")

print("\n--- Errors ---")

try:
    library.get_item(999)
except ItemNotFoundError as e:
    print("ItemNotFoundError:", e)

try:
    library.get_item(matrix_id).checkout()  # already checked out above
except ItemStateError as e:
    print("ItemStateError (checkout twice):", e)

try:
    library.get_item(dune_id).return_item()  # already returned above
except ItemStateError as e:
    print("ItemStateError (return available item):", e)

try:
    library.remove_item(matrix_id)  # still checked out
except ItemStateError as e:
    print("ItemStateError (remove checked-out item):", e)

try:
    library.update_item(dune_id, id=42)
except ValueError as e:
    print("ValueError (update id):", e)

try:
    library.update_item(dune_id, is_available=False)
except ValueError as e:
    print("ValueError (update is_available):", e)

try:
    library.list_items(item_type="magazine")
except ValueError as e:
    print("ValueError (invalid item_type):", e)
