# -*- coding: utf-8 -*-
import os
import types
import shutil
import unittest
from datetime import date

from simple_database import create_database, connect_database
from simple_database.config import BASE_DB_FILE_PATH
from simple_database.exceptions import ValidationError


class SimpleDatabaseTestCase(unittest.TestCase):

    def setUp(self):
        # initial clean up
        if os.path.exists(BASE_DB_FILE_PATH):
            shutil.rmtree(BASE_DB_FILE_PATH)

        self.db = create_database('library')
        self.db.create_table('authors', columns=[
            {'name': 'id', 'type': 'int'},
            {'name': 'name', 'type': 'str'},
            {'name': 'birth_date', 'type': 'date'},
            {'name': 'nationality', 'type': 'str'},
            {'name': 'alive', 'type': 'bool'},
        ])
        self.db.authors.insert(1, 'Jorge Luis Borges', date(1899, 8, 24), 'ARG', False)
        self.db.authors.insert(2, 'Edgard Alan Poe', date(1809, 1, 19), 'USA', False)

    def tearDown(self):
        if os.path.exists(BASE_DB_FILE_PATH):
            shutil.rmtree(BASE_DB_FILE_PATH)

    def test_create_database(self):
        db = create_database('test-db')
        self.assertEqual(db.show_tables(), [])
        db.create_table('authors', columns=[
            {'name': 'id', 'type': 'int'},
            {'name': 'name', 'type': 'str'},
            {'name': 'birth_date', 'type': 'date'},
            {'name': 'nationality', 'type': 'str'},
            {'name': 'alive', 'type': 'bool'},
        ])
        self.assertTrue(hasattr(db, 'authors'))
        self.assertEqual(db.show_tables(), ['authors'])
        db.authors.insert(1, 'Jorge Luis Borges', date(1899, 8, 24), 'ARG', False)
        self.assertEqual(db.authors.count(), 1)
        db.authors.insert(2, 'Edgard Alan Poe', date(1809, 1, 19), 'USA', False)
        self.assertEqual(db.authors.count(), 2)

    def test_create_database_duplicated_name(self):
        with self.assertRaisesRegexp(ValidationError,
                                     'Database with name "library" already exists.'):
            create_database('library')

    def test_connect_existing_database(self):
        db = create_database('test-db')
        db.create_table('authors', columns=[
            {'name': 'id', 'type': 'int'},
            {'name': 'name', 'type': 'str'},
            {'name': 'birth_date', 'type': 'date'},
            {'name': 'nationality', 'type': 'str'},
            {'name': 'alive', 'type': 'bool'},
        ])
        db.authors.insert(1, 'Jorge Luis Borges', date(1899, 8, 24), 'ARG', False)
        self.assertEqual(db.authors.count(), 1)

        new_db = connect_database('test-db')
        self.assertEqual(new_db.show_tables(), ['authors'])
        self.assertEqual(new_db.authors.count(), 1)

    def test_create_two_db_with_same_table(self):
        db1 = create_database('db1')
        db1.create_table('table1', columns=[
            {'name': 'id', 'type': 'int'},
            {'name': 'name', 'type': 'str'},
            {'name': 'birth_date', 'type': 'date'},
            {'name': 'nationality', 'type': 'str'},
            {'name': 'alive', 'type': 'bool'},
        ])
        db1.table1.insert(1, 'Jorge Luis Borges', date(1899, 8, 24), 'ARG', False)
        self.assertEqual(db1.show_tables(), ['table1'])
        self.assertEqual(db1.table1.count(), 1)

        db2 = create_database('db2')
        db2.create_table('table1', columns=[
            {'name': 'id', 'type': 'int'},
            {'name': 'name', 'type': 'str'},
            {'name': 'birth_date', 'type': 'date'},
            {'name': 'nationality', 'type': 'str'},
            {'name': 'alive', 'type': 'bool'},
        ])
        self.assertEqual(db2.show_tables(), ['table1'])
        self.assertEqual(db2.table1.count(), 0)

    def test_insert(self):
        self.db.authors.insert(3, 'Julio Cortázar', date(1914, 8, 26), 'ARG', False)
        self.assertEqual(self.db.authors.count(), 3)

    def test_insert_more_columns(self):
        with self.assertRaisesRegexp(ValidationError, 'Invalid amount of field'):
            self.db.authors.insert(1, 'Jorge Luis Borges', date(1899, 8, 24), 'ARG', False, 'something-else')

    def test_insert_less_columns(self):
        with self.assertRaisesRegexp(ValidationError, 'Invalid amount of field'):
            self.db.authors.insert(3, 'Julio Cortázar')

    def tests_insert_invalid_type(self):
        error_msg = 'Invalid type of field "birth_date": Given "str", expected "date"'
        with self.assertRaisesRegexp(ValidationError, error_msg):
            self.db.authors.insert(3, 'Julio Cortázar', '1914-8-26', 'ARG', False)  # must be a date object

    def test_query(self):
        self.db.authors.insert(3, 'Julio Cortázar', date(1914, 8, 26), 'ARG', False)
        self.assertEqual(self.db.authors.count(), 3)
        gen = self.db.authors.query(nationality='ARG')
        count = 0
        for author in gen:
            self.assertEqual(author.nationality, 'ARG')
            count += 1
        self.assertEqual(count, 2)

    def test_query_not_match(self):
        gen = self.db.authors.query(nationality='UYU')
        self.assertEqual(len([author for author in gen]), 0)

    def test_all(self):
        gen = self.db.authors.all()
        self.assertTrue(isinstance(gen, types.GeneratorType))
        borges = next(gen)
        self.assertEqual(borges.id, 1)
        self.assertEqual(borges.name, 'Jorge Luis Borges')
        self.assertEqual(borges.nationality, 'ARG')

    def test_table_describe(self):
        columns = self.db.authors.describe()
        expected = [
            {'name': 'id', 'type': 'int'},
            {'name': 'name', 'type': 'str'},
            {'name': 'birth_date', 'type': 'date'},
            {'name': 'nationality', 'type': 'str'},
            {'name': 'alive', 'type': 'bool'},
        ]
        self.assertEqual(columns, expected)
