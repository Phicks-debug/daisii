import boto3
from boto3.dynamodb.conditions import Key


class DynamoDBService:
    def __init__(self, region_name: str, table: str):
        self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
        self.table_name = table
        self.table = self.dynamodb.Table(table)


    def create_table(self, conversation_id):
        table_name = f"{self.table_name}_{conversation_id}"
        try:
            table = self.dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {
                        'AttributeName': 'conversation_id',
                        'KeyType': 'HASH'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'conversation_id',
                        'AttributeType': 'S'
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            table.meta.client.get_waiter('table_exists').wait(TableName=table_name)
            self.table = self.dynamodb.Table(table_name)
        except self.dynamodb.meta.client.exceptions.ResourceInUseException:
            # If the table already exists, just use it
            self.table = self.dynamodb.Table(table_name)


    def get_chat_history(self, userid, conversation_id):
        response = self.table.query(
            KeyConditionExpression=Key('conversation_id').eq(conversation_id)
        )
        return response.get('Items', [])


    async def save_chat_history(self, conversation_id, userid, messages):
        result = self.table.put_item(
            Item={
                'userid': userid,
                'conversation_id': conversation_id,
                'messages': messages
            }
        )
        
    
if __name__ == "__main__":
    dynamodb_service = DynamoDBService("us-east-1", "daisy-chat-history")
    # conversation_id = uuid.uuid4().hex
    # dynamodb_service.create_table(conversation_id)
    dynamodb_service.save_chat_history("e34509c50d3d421990aa861b52c0881d", [{"role": "user", "content": "What is your name?"}])
    print(dynamodb_service.get_chat_history("e34509c50d3d421990aa861b52c0881d"))