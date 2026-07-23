# My Doubts

## 1. Pydantic, Literal, and Enum
- **Pydantic (`BaseModel`)**: A library that validates data. You define a class with types, and Pydantic makes sure the data you put in matches those types.
  *Example*: If you define `age: int` and try to pass `age="twenty"`, Pydantic will throw a loud error instead of letting the bug slip into the database.
- **Literal**: A typing feature that restricts a variable to exact specific values. 
  *Example*:
  ```python
  from typing import Literal
  def set_status(status: Literal["success", "failed"]):
      pass
  
  set_status("success") # Works!
  set_status("pending") # ERROR: "pending" is not allowed.
  ```
- **Enum (Enumeration)**: A way to create a set of named constants. Similar to `Literal`, but you define it as a class.
  *Example*:
  ```python
  from enum import Enum
  class Color(Enum):
      RED = "red"
      BLUE = "blue"

  my_color = Color.RED
  ```
  *Why use it?* When typing `Color.`, your code editor will auto-complete `RED` or `BLUE`, preventing you from accidentally typing `"rad"` or `"blu"`.

## 2. check_same_thread=False
- **What it is**: By default, Python's `sqlite3` library only lets the thread (the specific sequence of instructions) that created the database connection use that connection. If another thread tries to use it, it throws an error. Setting it to `False` disables this safety check.
- **Why we need it**: In modern apps (like web servers or MCP servers), the app might receive a request on one thread, and then handle a second request on a different thread. If both need the database, `sqlite3` would crash without this setting.

### How to explain it in an interview:
"By default, SQLite in Python is protective and binds the database connection to the specific thread that opened it. If you're building a web app or an API where different requests are handled by different threads, they'll all need to talk to the database. By passing `check_same_thread=False`, we tell SQLite it's okay for multiple threads to share this single connection. However, we still need to be careful with writing data concurrently, so we usually pair this with a lock or rely on SQLite's own write-locking mechanism to prevent data corruption."

**Example for Interview**: 
"Imagine a restaurant where only the waiter who opened the cash register is allowed to put money in it. That's `check_same_thread=True`. If it gets busy and other waiters need to use the register, they can't. Setting it to `False` is like telling the manager, 'Any waiter can use this register.' But, to avoid mistakes, only one waiter can actually put money in at the exact same moment."

## 3. row_factory = sqlite3.Row
- **What it is**: By default, when you get data out of an SQLite database in Python, it comes back as a plain "tuple" (a list of values like `(1, "git", "fixed bug", ...)`). You have to remember which index corresponds to which column (e.g., `row[1]` is the source). `sqlite3.Row` changes this so the database returns an object that acts like a dictionary.
- **Why we need it**: It lets you access columns by their name! Instead of `row[1]`, you can write `row["source"]` or `row["summary"]`. This makes the code much easier to read and prevents bugs. 

### How to explain it in an interview:
"By default, Python's SQLite library returns rows as tuples, meaning you have to access data by index, like `row[0]` or `row[1]`. Setting `connection.row_factory = sqlite3.Row` tells SQLite to return rows as dictionary-like objects instead. This allows us to access columns by their name, like `row['summary']`, which makes the code more readable and less prone to off-by-one errors."

**Example**:
```python
# WITHOUT row_factory
row = cursor.fetchone()
print(row[3])  # Is index 3 the summary? Or the reasoning? Hard to tell.

# WITH row_factory
row = cursor.fetchone()
print(row["summary"])  # Very clear!
```

## 4. `self._init_db()` and the underscore convention
- **What it means**: Yes! `self._init_db()` is exactly how we call the function we wrote earlier. 
- **The Underscore (`_`)**: In Python, when you name a function starting with an underscore (like `_init_db`), it's a signal to other developers that this is a **"private"** method. It means, "This function is only meant to be used internally inside this class. Don't call this function from outside the class."
- **Why we call it in `__init__`**: We call it inside `__init__` so that the very moment someone creates an `SQLiteStore` object, the database tables are automatically set up. The developer using our class doesn't have to remember to call it themselves.

## 5. `mkdir(parents=True, exist_ok=True)`
When we do `self.db_path.parent.mkdir(parents=True, exist_ok=True)`, we are telling Python to create the folder where our database file will live. 
- **`parents=True`**: This tells Python to create any missing folders in the path. For example, if we want to save our database at `~/.devmemory/store.db`, Python will first try to find the `.devmemory` folder. If it doesn't exist, `parents=True` tells Python to create it for us. If this was `False`, Python would crash saying "Folder not found".
- **`exist_ok=True`**: This tells Python, "If the folder already exists, just ignore this command and move on." If this was `False`, Python would crash with a "Folder already exists" error every time we ran the code after the first time.

## 6. What is `self` in Python classes?
- **What it is**: `self` is simply a reference to the **specific object** you are currently working with. 
- **The Analogy**: Imagine a blueprint for a house. The blueprint is the `class`. Now imagine you use that blueprint to build three actual houses. `self` is like saying "my own". If you say "paint the front door red", which house do you paint? If you say `self.paint_door("red")`, it means "paint the door of **this specific house** red."
- **When to use it**: 
  1. Whenever you are defining a method inside a class, the first parameter must always be `self`. E.g., `def _init_db(self):`. 
  2. Whenever you want to save a variable so that it belongs to the whole object (and can be used in other methods later), you attach it to `self`. E.g., `self.conn = sqlite3.connect(...)`.
  3. Whenever you want to call a method from within the same class, you use `self`. E.g., `self._init_db()`.
- **When NOT to use it**: You do not use `self` for temporary variables that you only need inside one single function. For example, in `cursor = self.conn.cursor()`, we don't say `self.cursor` because we only need the cursor for a split second to run a command, and then we throw it away. We don't need the whole house to remember it.

### How to explain it in an interview:
"In Python, `self` represents the instance of the class. It allows us to access the attributes and methods of that specific object. While some languages like Java or C++ pass `this` implicitly under the hood, Python requires us to pass `self` explicitly as the first argument to instance methods. It's how Python distinguishes between a local variable in a function and a state variable that belongs to the object."

## 7. What is an "Object" (Class vs. Object)?
- **The Class (The Blueprint)**: When you write `class SQLiteStore:`, you are writing a blueprint. It's just a set of instructions. Think of it like a **recipe for a cake** or the **design for a car**. You can't eat a recipe, and you can't drive a design.
- **The Object (The Real Thing)**: When you actually use the class in your code by writing `my_store = SQLiteStore("my_database.db")`, Python takes your blueprint and builds the real thing. That real thing is called an **Object** (or an **Instance**). Think of it as the **actual cake** you baked, or the **actual car** you built.
- **How it connects to `self`**: You can build many cars from one design. `Car A` might be painted Red, and `Car B` might be painted Blue. Inside the blueprint's code, `self` means "the specific car we are currently looking at". If you say `self.color = "Red"`, it changes the color of the specific object you are working with, not all cars everywhere.

## 8. What is a Database Index (`CREATE INDEX`)?
- **What it is**: An index in a database is exactly like the **Index at the back of a large textbook**. 
- **The Analogy**: Imagine you have a 1,000-page history textbook, and I ask you to find every page that mentions "Abraham Lincoln". 
  - **Without an Index (Table Scan)**: You have to start at page 1 and read every single word on every single page until you reach page 1,000. This is very slow! In a database, this is called a "Full Table Scan".
  - **With an Index**: You flip to the back of the book, look for "L", find "Lincoln, Abraham", and it tells you exactly where to look: "Pages 42, 87, 212". You jump straight to those pages instantly.
- **Why we use them**: As our `devmemory` database gets huge, we might want to find all memories of a certain `type` (like "bug_fix") or within a certain `timestamp` range (like "last week"). By creating an index on those two columns, SQLite creates a hidden "back-of-the-book index" for them. It makes our searches lightning fast!

### How to explain it in an interview:
"An index is a data structure that improves the speed of data retrieval operations on a database table. It works just like an index in a book. Instead of doing a full table scan (reading every row one by one), the database engine uses the index to quickly locate the exact rows we are looking for. However, indices come with a small trade-off: they take up extra disk space, and they make `INSERT` and `UPDATE` operations slightly slower because the database has to update the index every time new data is added."

## 9. How do Pydantic models (like `RawEvent`) get actual data?
- **The Question**: In `models.py`, `RawEvent` just defines the datatypes (like `id: str`). But in `save_raw_event(self, event: RawEvent)`, we access actual data like `event.id`. How did the data get there?
- **The Answer**: Remember the Blueprint vs Object analogy from above! `class RawEvent` is just the blueprint. It says, *"If you want to build a RawEvent, you MUST give me an ID, a source, and text."*
- When another part of our program actually runs, it will take real data and push it into the blueprint to create a real Object.
  - **Example of creating the object**:
    ```python
    # We build the actual object using the blueprint
    my_event = RawEvent(
        id="123", 
        source="manual", 
        raw_text="I fixed a bug",
        metadata={},
        timestamp=datetime.now()
    )
    
    # NOW we pass that real object to our database class
    store.save_raw_event(my_event)
    ```
- **Type Hinting (`event: RawEvent`)**: When we write `def save_raw_event(self, event: RawEvent):`, the `: RawEvent` part is called a **Type Hint**. We are telling Python, *"The variable `event` coming into this function will be a fully built RawEvent object."* This allows our code editor (like VSCode) to know that `event` has an `.id` and `.source`, so it can auto-complete it for us when we type `event.`!

## 10. What does `cursor.fetchone()` mean?
- **The cursor**: The `cursor` is like a pointer that moves through the database to read or write data. Think of it like a little robotic arm inside the database.
- **Fetching data**: When you run a `SELECT` command, the database might find 0 results, 1 result, or 1,000 results. The robotic arm (the cursor) lines up all those results in a queue, but it doesn't immediately give them all to Python (because downloading 1,000 results all at once might crash your computer).
- **`fetchone()` vs `fetchall()`**:
  - `cursor.fetchone()` tells the robotic arm: *"Just give me the very first result in the queue, and stop."* Since we are looking up an event by its unique `id`, we know there will only ever be a maximum of 1 match. So `fetchone()` is perfect here! If no match is found, it simply returns `None`.
  - `cursor.fetchall()` tells the robotic arm: *"Give me every single result you found, as a big list."* We will use this later when we want to search for multiple memories!

### How to explain it in an interview:
"`cursor.fetchone()` retrieves the next row of a query result set and returns a single sequence, or `None` when no more data is available. It's efficient for queries where we expect a single unique result (like looking up by a primary key), because it prevents the database from allocating memory for a larger list of results."

## 11. What is the `__init__` function inside a Class?
- **What it is**: `__init__` stands for "initialize". In Python, it is a special function called a **Constructor**. 
- **When does it run?**: You never call `__init__` yourself! Python runs this function *automatically*, the exact millisecond that a new Object is created from the Class blueprint.
- **The Analogy**: 
  - The `Class` is the blueprint for a car. 
  - `__init__` is the **factory assembly line**. 
  - The moment you say "build me a new car" (`my_car = Car()`), the assembly line (`__init__`) fires up. It paints the car, installs the engine, and fills the tires before driving it out the door.
- **Why we need it**: In our `SQLiteStore`, we use `__init__` to do all the setup work: figuring out the file path, connecting to the database, and calling `_init_db()` to build the tables. This way, whenever someone creates an `SQLiteStore` object, it is 100% ready to be used immediately. They don't have to remember to connect to the database themselves.

### How to explain it in an interview:
"The `__init__` method in Python is the class constructor. It is automatically invoked when a new instance of the class is created. Its primary purpose is to initialize the object's state by assigning values to instance variables (using `self`) or performing any necessary setup operations, like opening a database connection, so that the object is in a valid and usable state immediately upon creation."

## 12. Why did `sqlite3.ProgrammingError: Incorrect number of bindings` happen?
- **The Error**: When running our test, we got `Incorrect number of bindings supplied. The current statement uses 1, and there are 36 supplied.`
- **The Cause**: In Python, putting parentheses around a single variable doesn't make it a list (tuple). For example, `(event_id)` is treated exactly the same as just `event_id` (a string). 
- Because `event_id` is a UUID string with 36 characters, SQLite thought we were giving it a list of 36 separate letters, instead of 1 single variable!
- **The Fix**: To create a tuple with only *one* item in Python, you **must include a trailing comma**. We have to change `(event_id)` to `(event_id,)`. That tiny little comma tells Python, "This is a list containing exactly one item."

## 13. What is `Protocol` in Python?
- **What it is**: `Protocol` is Python's way of defining an **Interface**. It lets you write a "contract" that other classes must follow.
- **The Analogy**: Imagine you are a manager hiring a "Driver". You don't care if the person is 20 years old, 50 years old, tall, or short. Your only rule (your *Protocol*) is: *"The person must have a function called `drive_car()`"*. 
- **Why we use it here**: Right now, we want to build our memory extraction pipeline. But we don't know if the user wants to use OpenAI (ChatGPT), Anthropic (Claude), or a free local AI. 
- By using `Protocol`, we tell Python: *"I don't care which AI the user brings. As long as their AI class has a function exactly named `extract_memory_record`, my code will accept it and work perfectly!"* This makes our code incredibly flexible and easy to swap out later.

### How to explain it in an interview:
"In Python, `Protocol` is used for **structural subtyping** (often called static duck typing). It allows us to define an interface or a 'contract' of methods that a class must implement. Instead of forcing a class to explicitly inherit from a base class, any class that happens to have the matching methods is automatically considered valid. This keeps our system loosely coupled and makes it very easy to swap out dependencies (like swapping an OpenAI client for a Gemini client) without changing the core business logic."
