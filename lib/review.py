from __init__ import CURSOR, CONN
from employee import Employee

class Review:
    # Dictionary of objects saved to the database.
    all = {}

    def __init__(self, year, summary, employee_id, id=None):
        self.id = id
        self.year = year
        self.summary = summary
        self.employee_id = employee_id  # This will trigger validation

    def __repr__(self):
        return (
            f"<Review {self.id}: {self.year}, {self.summary}, "
            + f"Employee: {self.employee_id}>"
        )

    @classmethod
    def create_table(cls):
        """Create a new table to persist the attributes of Review instances."""
        sql = """
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY,
                year INTEGER,
                summary TEXT,
                employee_id INTEGER,
                FOREIGN KEY (employee_id) REFERENCES employees(id)
            )
        """
        try:
            CURSOR.execute(sql)
            CONN.commit()
        except Exception as e:
            CONN.rollback()
            raise e

    @classmethod
    def drop_table(cls):
        """Drop the table that persists Review instances."""
        sql = "DROP TABLE IF EXISTS reviews;"
        try:
            CURSOR.execute(sql)
            CONN.commit()
        except Exception as e:
            CONN.rollback()
            raise e

    def save(self):
        """Insert or update the Review instance in the database."""
        try:
            if self.id is None:
                sql = """
                    INSERT INTO reviews (year, summary, employee_id)
                    VALUES (?, ?, ?)
                """
                CURSOR.execute(sql, (self.year, self.summary, self.employee_id))
                self.id = CURSOR.lastrowid
            else:
                sql = """
                    UPDATE reviews
                    SET year = ?, summary = ?, employee_id = ?
                    WHERE id = ?
                """
                CURSOR.execute(sql, (self.year, self.summary, self.employee_id, self.id))
            CONN.commit()
            Review.all[self.id] = self
        except Exception as e:
            CONN.rollback()
            raise e

    @classmethod
    def create(cls, year, summary, employee_id):
        """Initialize a new Review instance and save it to the database. Return the new instance."""
        if not isinstance(year, int):
            raise ValueError("Year must be an integer")
        if year < 2000:
            raise ValueError("Year must be >= 2000")
        if not isinstance(summary, str) or len(summary) == 0:
            raise ValueError("Summary must be a non-empty string")
        
        # Validate employee_id
        employee = Employee.find_by_id(employee_id)
        if not employee:
            raise ValueError("Invalid employee_id")
        
        review = cls(year, summary, employee_id)
        review.save()
        return review

    @classmethod
    def instance_from_db(cls, row):
        """Return a Review instance having the attribute values from the table row."""
        id, year, summary, employee_id = row
        review = cls(year, summary, employee_id, id)
        cls.all[id] = review
        return review

    @classmethod
    def find_by_id(cls, id):
        """Return a Review instance with the given id."""
        if id in cls.all:
            return cls.all[id]
        sql = "SELECT * FROM reviews WHERE id = ?"
        row = CURSOR.execute(sql, (id,)).fetchone()
        if row:
            review = cls.instance_from_db(row)
            return review
        return None

    def update(self):
        """Update the table row corresponding to the current Review instance."""
        self.save()

    def delete(self):
        """Delete the table row corresponding to the current Review instance,
        delete the dictionary entry, and reassign id attribute."""
        if self.id:
            try:
                sql = "DELETE FROM reviews WHERE id = ?"
                CURSOR.execute(sql, (self.id,))
                CONN.commit()
                if self.id in Review.all:
                    del Review.all[self.id]
                self.id = None
            except Exception as e:
                CONN.rollback()
                raise e

    @classmethod
    def get_all(cls):
        """Return a list containing one Review instance per table row."""
        sql = "SELECT * FROM reviews"
        rows = CURSOR.execute(sql).fetchall()
        reviews = [cls.instance_from_db(row) for row in rows]
        return reviews

    @property
    def employee_id(self):
        return self._employee_id

    @employee_id.setter
    def employee_id(self, value):
        if not Employee.find_by_id(value):
            raise ValueError("Invalid employee_id")
        self._employee_id = value
