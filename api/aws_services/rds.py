import boto3
import os
import logging

from botocore.exceptions import ClientError


class AuroraPostgres:
    
    def __init__(self, region_name):
        """
        Initialize the Aurora PostgreSQL database connection.
        """
        session = boto3.Session(region_name=region_name)
        self.db = session.client('rds-data')
        self.create_table_if_not_exists()
        
    
    def create_table_if_not_exists(self):
        """
        Create the user database if it doesn't exist yet.
        """
        create_table_sql = """
            CREATE TABLE IF NOT EXISTS users (
                userID uuid DEFAULT uuid_generate_v4(),
                email VARCHAR(255) UNIQUE,
                username VARCHAR(255),
                password VARCHAR(255),
                disabled BOOLEAN DEFAULT FALSE
            );
        """
        
        try:
            result = self.db.execute_statement(
                secretArn=os.environ.get('AURORA_DATABASE_SECRET_ARN'),
                database=os.environ.get('AURORA_DATABASE_NAME'),
                resourceArn=os.environ.get('AURORA_DATABASE_RESOURCE_ARN'),
                sql="""CREATE EXTENSION IF NOT EXISTS "uuid-ossp";"""
            ) 
            result = self.db.execute_statement(
                secretArn=os.environ.get('AURORA_DATABASE_SECRET_ARN'),
                database=os.environ.get('AURORA_DATABASE_NAME'),
                resourceArn=os.environ.get('AURORA_DATABASE_RESOURCE_ARN'),
                sql=create_table_sql
            ) 
            
        except ClientError as e:
            logging.error(e)
            return {"status": "Error", "message": str(e)}
        return {"status": "Success", "message": result}
    
    
    async def create_new_user(self, email: str, username: str, password: str):
        """
        Insert new user into the Aurora PostgreSQL database.
        """
        
        insert_sql = """
            INSERT INTO users (email, username, password)
            VALUES (:email, :username, :password)
        """

        try:
            result = self.db.execute_statement(
                secretArn=os.environ.get('AURORA_DATABASE_SECRET_ARN'),
                database=os.environ.get('AURORA_DATABASE_NAME'),
                resourceArn=os.environ.get('AURORA_DATABASE_RESOURCE_ARN'),
                sql=insert_sql,
                parameters=[
                    {'name': 'email', 'value': {'stringValue': email}},
                    {'name': 'username', 'value': {'stringValue': username}},
                    {'name': 'password', 'value': {'stringValue': password}}
                ]
            )

        except ClientError as e:
            logging.error(e)
            return {"status": "Error", "message": str(e)}
        return {"status": "Success", "message": result}


    async def get_user(self, email: str):
        """
        Get user from the Aurora PostgreSQL database.
        """

        select_sql = """
            SELECT * FROM users WHERE email = :email
        """

        try:
            result = self.db.execute_statement(
                secretArn=os.environ.get('AURORA_DATABASE_SECRET_ARN'),
                database=os.environ.get('AURORA_DATABASE_NAME'),
                resourceArn=os.environ.get('AURORA_DATABASE_RESOURCE_ARN'),
                sql=select_sql,
                parameters=[
                    {'name': 'email', 'value': {'stringValue': email}}
                ]
            )
            
            # Assuming `records` is part of the result structure that returns the data.
            return {"status": "Success", "message": result['records']}

        except ClientError as e:
            logging.error(e)
            return {"status": "Error", "message": str(e)}
