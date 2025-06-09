import sqlite3
import os

# Path to the database
DB_PATH = os.path.join(os.path.dirname(__file__), 'database.db')

def update_image_paths():
    try:
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # Update image_path to replace backslashes with forward slashes
        c.execute("UPDATE food_logs SET image_path = REPLACE(image_path, '\\', '/') WHERE image_path IS NOT NULL")

        # Commit the changes
        conn.commit()
        print("Image paths updated successfully.")

        # Verify the update (optional)
        c.execute("SELECT image_path FROM food_logs WHERE image_path IS NOT NULL")
        updated_paths = c.fetchall()
        if updated_paths:
            print("Updated image paths:")
            for path in updated_paths:
                print(path[0])
        else:
            print("No image paths found to verify.")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    update_image_paths()