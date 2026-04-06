"""
SQL Task definitions for the SQL Query Environment.

Each task has:
- A natural language question
- A database schema (created via SQL DDL + INSERT statements)
- An expected SQL query (reference solution)
- Difficulty level: easy, medium, hard
"""

SCHEMA_DDL = """
-- Employees table
CREATE TABLE employees (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    department TEXT NOT NULL,
    salary REAL NOT NULL,
    hire_date TEXT NOT NULL,
    manager_id INTEGER,
    FOREIGN KEY (manager_id) REFERENCES employees(id)
);

-- Products table
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    price REAL NOT NULL,
    stock_quantity INTEGER NOT NULL
);

-- Orders table
CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    customer_name TEXT NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    order_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Customers table
CREATE TABLE customers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    city TEXT NOT NULL,
    signup_date TEXT NOT NULL
);
"""

SEED_DATA = """
-- Employees
INSERT INTO employees VALUES (1, 'Alice Johnson', 'Engineering', 95000, '2020-01-15', NULL);
INSERT INTO employees VALUES (2, 'Bob Smith', 'Engineering', 85000, '2020-06-01', 1);
INSERT INTO employees VALUES (3, 'Carol White', 'Marketing', 75000, '2019-03-20', NULL);
INSERT INTO employees VALUES (4, 'David Brown', 'Engineering', 90000, '2021-02-10', 1);
INSERT INTO employees VALUES (5, 'Eve Davis', 'Marketing', 70000, '2021-08-15', 3);
INSERT INTO employees VALUES (6, 'Frank Wilson', 'Sales', 80000, '2018-11-01', NULL);
INSERT INTO employees VALUES (7, 'Grace Lee', 'Sales', 72000, '2022-01-20', 6);
INSERT INTO employees VALUES (8, 'Henry Taylor', 'Engineering', 88000, '2020-09-05', 1);
INSERT INTO employees VALUES (9, 'Ivy Martinez', 'Marketing', 68000, '2023-04-12', 3);
INSERT INTO employees VALUES (10, 'Jack Anderson', 'Sales', 76000, '2021-07-30', 6);

-- Products
INSERT INTO products VALUES (1, 'Laptop Pro', 'Electronics', 1299.99, 50);
INSERT INTO products VALUES (2, 'Wireless Mouse', 'Electronics', 29.99, 200);
INSERT INTO products VALUES (3, 'Standing Desk', 'Furniture', 499.99, 30);
INSERT INTO products VALUES (4, 'Monitor 4K', 'Electronics', 599.99, 75);
INSERT INTO products VALUES (5, 'Keyboard Mech', 'Electronics', 149.99, 120);
INSERT INTO products VALUES (6, 'Office Chair', 'Furniture', 349.99, 45);
INSERT INTO products VALUES (7, 'Webcam HD', 'Electronics', 79.99, 150);
INSERT INTO products VALUES (8, 'Desk Lamp', 'Furniture', 39.99, 100);
INSERT INTO products VALUES (9, 'USB Hub', 'Electronics', 24.99, 300);
INSERT INTO products VALUES (10, 'Notebook Pack', 'Stationery', 12.99, 500);

-- Orders
INSERT INTO orders VALUES (1, 'John Doe', 1, 1, '2024-01-10', 'completed');
INSERT INTO orders VALUES (2, 'Jane Roe', 2, 3, '2024-01-12', 'completed');
INSERT INTO orders VALUES (3, 'John Doe', 4, 1, '2024-01-15', 'completed');
INSERT INTO orders VALUES (4, 'Sam Fox', 3, 1, '2024-02-01', 'pending');
INSERT INTO orders VALUES (5, 'Jane Roe', 5, 2, '2024-02-05', 'completed');
INSERT INTO orders VALUES (6, 'Amy Lin', 1, 1, '2024-02-10', 'shipped');
INSERT INTO orders VALUES (7, 'Sam Fox', 7, 2, '2024-02-15', 'completed');
INSERT INTO orders VALUES (8, 'John Doe', 9, 5, '2024-03-01', 'pending');
INSERT INTO orders VALUES (9, 'Amy Lin', 6, 1, '2024-03-05', 'completed');
INSERT INTO orders VALUES (10, 'Jane Roe', 10, 10, '2024-03-10', 'shipped');
INSERT INTO orders VALUES (11, 'Tom Ray', 2, 2, '2024-03-15', 'completed');
INSERT INTO orders VALUES (12, 'Tom Ray', 8, 3, '2024-03-20', 'pending');
INSERT INTO orders VALUES (13, 'Sam Fox', 4, 1, '2024-04-01', 'completed');
INSERT INTO orders VALUES (14, 'Amy Lin', 5, 1, '2024-04-05', 'shipped');
INSERT INTO orders VALUES (15, 'John Doe', 3, 1, '2024-04-10', 'completed');

-- Customers
INSERT INTO customers VALUES (1, 'John Doe', 'john@example.com', 'New York', '2023-01-15');
INSERT INTO customers VALUES (2, 'Jane Roe', 'jane@example.com', 'San Francisco', '2023-02-20');
INSERT INTO customers VALUES (3, 'Sam Fox', 'sam@example.com', 'Chicago', '2023-05-10');
INSERT INTO customers VALUES (4, 'Amy Lin', 'amy@example.com', 'New York', '2023-08-01');
INSERT INTO customers VALUES (5, 'Tom Ray', 'tom@example.com', 'San Francisco', '2024-01-05');
"""

SCHEMA_DESCRIPTION = """Database Schema:

TABLE employees (
  id INTEGER PRIMARY KEY,
  name TEXT,
  department TEXT,       -- e.g., 'Engineering', 'Marketing', 'Sales'
  salary REAL,
  hire_date TEXT,        -- format: 'YYYY-MM-DD'
  manager_id INTEGER     -- references employees(id), NULL if no manager
)

TABLE products (
  id INTEGER PRIMARY KEY,
  name TEXT,
  category TEXT,         -- e.g., 'Electronics', 'Furniture', 'Stationery'
  price REAL,
  stock_quantity INTEGER
)

TABLE orders (
  id INTEGER PRIMARY KEY,
  customer_name TEXT,
  product_id INTEGER,    -- references products(id)
  quantity INTEGER,
  order_date TEXT,       -- format: 'YYYY-MM-DD'
  status TEXT            -- 'pending', 'shipped', 'completed'
)

TABLE customers (
  id INTEGER PRIMARY KEY,
  name TEXT,
  email TEXT,
  city TEXT,
  signup_date TEXT       -- format: 'YYYY-MM-DD'
)
"""


# ─── TASK DEFINITIONS ───────────────────────────────────────────────────────────

TASKS = [
    # ── EASY TASKS (single table, basic SELECT/WHERE/ORDER BY) ───────────────
    {
        "task_id": "easy_1",
        "difficulty": "easy",
        "question": "List all employees in the Engineering department, ordered by salary descending.",
        "reference_query": """
            SELECT name, salary
            FROM employees
            WHERE department = 'Engineering'
            ORDER BY salary DESC;
        """,
        "max_attempts": 5,
    },
    {
        "task_id": "easy_2",
        "difficulty": "easy",
        "question": "Find all products in the 'Electronics' category with a price greater than $100. Return the product name and price.",
        "reference_query": """
            SELECT name, price
            FROM products
            WHERE category = 'Electronics' AND price > 100
            ORDER BY price;
        """,
        "max_attempts": 5,
    },
    {
        "task_id": "easy_3",
        "difficulty": "easy",
        "question": "Count the total number of orders with status 'completed'.",
        "reference_query": """
            SELECT COUNT(*) as completed_count
            FROM orders
            WHERE status = 'completed';
        """,
        "max_attempts": 5,
    },

    # ── MEDIUM TASKS (JOINs, GROUP BY, HAVING, aggregation) ─────────────────
    {
        "task_id": "medium_1",
        "difficulty": "medium",
        "question": "Find the total revenue (price * quantity) for each product category from completed orders. Show category and total revenue, ordered by revenue descending.",
        "reference_query": """
            SELECT p.category, SUM(p.price * o.quantity) as total_revenue
            FROM orders o
            JOIN products p ON o.product_id = p.id
            WHERE o.status = 'completed'
            GROUP BY p.category
            ORDER BY total_revenue DESC;
        """,
        "max_attempts": 5,
    },
    {
        "task_id": "medium_2",
        "difficulty": "medium",
        "question": "Find customers who have placed more than 2 orders. Show the customer name and their order count, ordered by order count descending.",
        "reference_query": """
            SELECT customer_name, COUNT(*) as order_count
            FROM orders
            GROUP BY customer_name
            HAVING COUNT(*) > 2
            ORDER BY order_count DESC;
        """,
        "max_attempts": 5,
    },
    {
        "task_id": "medium_3",
        "difficulty": "medium",
        "question": "Find the average salary per department, but only for departments with more than 2 employees. Show department name and average salary.",
        "reference_query": """
            SELECT department, AVG(salary) as avg_salary
            FROM employees
            GROUP BY department
            HAVING COUNT(*) > 2
            ORDER BY avg_salary DESC;
        """,
        "max_attempts": 5,
    },

    # ── HARD TASKS (subqueries, window functions, complex JOINs) ─────────────
    {
        "task_id": "hard_1",
        "difficulty": "hard",
        "question": "For each department, find the employee with the highest salary. Show department, employee name, and salary. If there's a tie, include all tied employees.",
        "reference_query": """
            SELECT department, name, salary
            FROM employees
            WHERE salary = (
                SELECT MAX(salary)
                FROM employees e2
                WHERE e2.department = employees.department
            )
            ORDER BY department;
        """,
        "max_attempts": 5,
    },
    {
        "task_id": "hard_2",
        "difficulty": "hard",
        "question": "Find the top 3 customers by total spending (price * quantity) across all their orders, regardless of order status. Show customer name and total spent.",
        "reference_query": """
            SELECT o.customer_name, SUM(p.price * o.quantity) as total_spent
            FROM orders o
            JOIN products p ON o.product_id = p.id
            GROUP BY o.customer_name
            ORDER BY total_spent DESC
            LIMIT 3;
        """,
        "max_attempts": 5,
    },
    {
        "task_id": "hard_3",
        "difficulty": "hard",
        "question": "Find products that have never been ordered. Show product name and category.",
        "reference_query": """
            SELECT p.name, p.category
            FROM products p
            LEFT JOIN orders o ON p.id = o.product_id
            WHERE o.id IS NULL
            ORDER BY p.name;
        """,
        "max_attempts": 5,
    },
]
