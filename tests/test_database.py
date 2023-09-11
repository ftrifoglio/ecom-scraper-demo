import os

import pandas as pd

from webscraper.database import TableHandler

# Sample data for testing
TEST_TABLE = "pages_urls"
# PAGES_URLS_TABLE = """
# id INTEGER,
# page_url TEXT PRIMARY KEY
# """
TEST_DATA = [
    {"id": 1, "page_url": "http://www.example.com/page1"},
    {"id": 2, "page_url": "http://www.example.com/page2"},
]
TEST_DATABASE = "test.db"


class TestTableHandler:
    @classmethod
    def setup_class(cls):
        cls.table_handler = TableHandler(TEST_TABLE, TEST_DATABASE)

    @classmethod
    def teardown_class(cls):
        if os.path.exists(TEST_DATABASE):
            os.remove(TEST_DATABASE)

    def test_create_table(self):
        self.table_handler.create_table()

        with self.table_handler._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT 1 FROM {TEST_TABLE} LIMIT 1")
            conn.commit()

    def test_insert_into(self):
        self.table_handler.insert_into(TEST_DATA)

        with self.table_handler._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {TEST_TABLE}")
            fetched_data = cursor.fetchall()
            conn.commit()
        assert fetched_data == [
            (1, "http://www.example.com/page1"),
            (2, "http://www.example.com/page2"),
        ]

    def test_read(self, capsys):
        self.table_handler.read()
        captured = capsys.readouterr()
        assert (
            captured.out.strip()
            == "[(1, 'http://www.example.com/page1'), (2, 'http://www.example.com/page2')]"
        )

    def test_to_pandas(self):
        df = self.table_handler.to_pandas()
        expected_df = pd.DataFrame(TEST_DATA)
        pd.testing.assert_frame_equal(df, expected_df)
