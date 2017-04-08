import os
import json
from datetime import date

from simple_database.exceptions import ValidationError
from simple_database.config import BASE_DB_FILE_PATH


class Row(object):
    def __init__(self, row):
        for key, value in row.items():
            setattr(self, key, value)


class Table(object):

    def __init__(self, db, name, columns=None):
        self.db = db
        self.name = name
        self.table_filepath = os.path.join(BASE_DB_FILE_PATH, self.db.name,
                                           '{}.json'.format(self.name))

        # In case the table JSON file doesn't exist already, you must
        # initialize it as an empty table, with this JSON structure:
        # {'columns': columns, 'rows': []}
        
        if not os.path.exists(self.table_filepath):
            table_dict = {'columns': columns, 'rows': []}
            with open(self.table_filepath, 'w') as f:
                f.write(json.dumps(table_dict))

        self.columns = columns or self._read_columns()

    def _read_columns(self):
        # Read the columns configuration from the table's JSON file
        # and return it.
        pass

    def insert(self, *args):
        # Validate that the provided row data is correct according to the
        # columns configuration.
        # If there's any error, raise ValidationError exception.
        # Otherwise, serialize the row as a string, and write to the
        # table's JSON file.
        
        if len(args) != len(self.columns):
            raise ValidationError("Invalid amount of field")

        # columns_length = len(self.columns)
        # arguments_length = len(args)
        
        for i, item in enumerate(args):
            if type(item).__name__ != self.columns[i]['type']:
                column_name = self.columns[i]['name']
                column_type = self.columns[i]['type']
                item_type = type(item).__name__
                error_msg = 'Invalid type of field "{}": Given "{}", expected "{}"'.format(
                    column_name, item_type, column_type)
                raise ValidationError(error_msg)
        else:
            with open(self.table_filepath, 'r+') as f:
                table_data = json.load(f)
                serialized_args = []
                for each_arg in args:
                    if type(each_arg).__name__ == 'date':
                        serialized_args.append(each_arg.isoformat())
                    else:
                        serialized_args.append(each_arg)
                
                new_row = {}
                for idx, column in enumerate(self.columns):
                    new_row[column['name']] = serialized_args[idx]
                
                table_data['rows'].append(new_row)
                f.seek(0)
                f.write(json.dumps(table_data))

    def query(self, **kwargs):
        # Read from the table's JSON file all the rows in the current table
        # and return only the ones that match with provided arguments.
        # We would recomment to  use the `yield` statement, so the resulting
        # iterable object is a generator.
        
        with open(self.table_filepath, 'r') as f:
            all_rows = json.load(f)['rows']
            k, v = kwargs.items()[0]
            for i in all_rows:
                if i['nationality'] == v:
                    yield Row(i)
                    

        # IMPORTANT: Each of the rows returned in each loop of the generator
        # must be an instance of the `Row` class, which contains all columns
        # as attributes of the object.

    def all(self):
        # Similar to the `query` method, but simply returning all rows in
        # the table.
        # Again, each element must be an instance of the `Row` class, with
        # the proper dynamic attributes.
        with open(self.table_filepath, 'r') as f:
            all_rows = json.load(f)['rows']
            for i in all_rows:
                yield Row(i)

    def count(self):
        # Read the JSON file and return the counter of rows in the table
        
        with open(self.table_filepath, 'r') as f:
            return len(json.load(f)['rows'])

    def describe(self):
        # Read the columns configuration from the JSON file, and return it.
        return self.columns


class DataBase(object):
    def __init__(self, name):
        self.name = name
        self.db_filepath = os.path.join(BASE_DB_FILE_PATH, self.name)
        self.tables = self._read_tables()

    @classmethod
    def create(cls, name):
        db_filepath = os.path.join(BASE_DB_FILE_PATH, name)
        # if the db directory already exists, raise ValidationError
        # otherwise, create the proper db directory
        if os.path.exists(db_filepath):
            error_msg = 'Database with name "{}" already exists.'.format(name)
            raise ValidationError(error_msg)
        else:
            os.makedirs(db_filepath)

    def _read_tables(self):
        # Gather the list of tables in the db directory looking for all files
        # with .json extension.
        # For each of them, instatiate an object of the class `Table` and
        # dynamically assign it to the current `DataBase` object.
        # Finally return the list of table names.
        # Hint: You can use `os.listdir(self.db_filepath)` to loop through
        #       all files in the db directory
        all_files = os.listdir(self.db_filepath)
        database_files = [file.split('.')[0] for file in all_files if file.endswith('.json')]
        
        table_names = []
        
        for database_file in database_files:
            table = Table(db=self, name=database_file)
            setattr(self, database_file, table)

        return database_files
            
            

    def create_table(self, table_name, columns):
        # Check if a table already exists with given name. If so, raise
        # ValidationError exception.
        # Otherwise, create an instance of the `Table` class and assign
        # it to the current db object.
        # Make sure to also append it to `self.tables`
        

        if table_name in self._read_tables():
            raise ValidationError
        else:
            table = Table(db=self, name=table_name, columns=columns)
            setattr(self, table_name, table)
            self.tables.append(table_name)
            
            
            
    def show_tables(self):
        # Return the current list of tables.
        return self.tables


def create_database(db_name):
    """
    Creates a new DataBase object and returns the connection object
    to the brand new database.
    """
    DataBase.create(db_name)
    return connect_database(db_name)


def connect_database(db_name):
    """
    Connectes to an existing database, and returns the connection object.
    """
    return DataBase(name=db_name)