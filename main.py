from uuid import UUID
import hashlib
import json
import boto3
from botocore.exceptions import ClientError
from datetime import datetime

def generate_uuid(value: str):
    if value and isinstance(value, str):
        value = value.lower()
        hex_str = hashlib.md5(value.encode('utf-8')).hexdigest()
        asset_id = str(UUID(hex=hex_str))
        return asset_id
    else:
        return None

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('paste-clip-note')

    


def query(userid):
    try:
        # 从 DynamoDB 获取数据
        print(userid)
        response = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('userid').eq(userid)
        )
        print(response)
    except ClientError as e:
        print(e.response['Error']['Message'])
        return {
            'statusCode': 400,
            'headers': {
        			'Content-Type': 'application/json',
        			'Access-Control-Allow-Origin': '*'
        		},
            'body': e.response['Error']['Message']
        }
    else:
        try:
            item_list = response['Items']
            clipboard = {}
            
            for item in item_list:
                
                note = item.get("note")
                create_date = item.get("createdate")
                note_id = item.get("noteid")

                total_content = clipboard.get(create_date) if clipboard.get(create_date) else []
                total_content.append({
                    "note_id": note_id,
                    "note": note
                })
                print(create_date)
                clipboard[create_date] = total_content
            
            print(clipboard)
            
            return {
                "isBase64Encoded": False,
                "statusCode": 200,
                'headers': {
        			'Content-Type': 'application/json',
        			'Access-Control-Allow-Origin': '*'
        		},
                "body": json.dumps(clipboard)
            }
            
        except Exception as e:
            return {
            'statusCode': 401,
            'headers': {
        			'Content-Type': 'application/json',
        			'Access-Control-Allow-Origin': '*'
        		},
            'body': json.dumps(e.response['Error']['Message'])
        }
        
def set(userid, clipboard, index_date):

    current_date = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
    noteid = generate_uuid(f"{current_date}:{userid}:{clipboard}")

    try:
        # 更新 DynamoDB 数据
        
        new_note = {
            "userid": userid,
            "noteid": noteid,
            "note": clipboard,
            "createdate": index_date
        }
        response = table.put_item(Item=new_note)

    except ClientError as e:
        print(e.response['Error']['Message'])
        return {
            'statusCode': 400,
            'headers': {
        			'Content-Type': 'application/json',
        			'Access-Control-Allow-Origin': '*'
        		},
            'body': json.dumps(e.response['Error']['Message'])
        }

    return {
        'statusCode': 200,
        'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
        'body': json.dumps(noteid)
    }

def deleteItem(userid, note_id):
    
    try:
        response = table.delete_item(
            Key={
                "userid": userid,
                "noteid":note_id
            }
        )

        return {
            'statusCode': 200,
            'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
            'body': json.dumps(note_id)
        }
    except Exception as e:

        print(e.response['Error']['Message'])
        return {
            'statusCode': 400,
            'headers': {
        			'Content-Type': 'application/json',
        			'Access-Control-Allow-Origin': '*'
        		},
            'body': json.dumps(e.response['Error']['Message'])
        }

def lambda_handler(event, context):
    # 获取表名
    
    print(event)
    # 从 API Gateway 事件中获取 userid
    userid = event['queryStringParameters']['userid'] 
    method = event['queryStringParameters']['method'] 
    
    if method == "query":
        return query(userid)
    if method == "set":
        clipboard = event['queryStringParameters']['clipboard'] 
        index_date = event['queryStringParameters']['index_date']
        if not clipboard:
            return {
            'statusCode': 401,
            'headers': {
        			'Content-Type': 'application/json',
        			'Access-Control-Allow-Origin': '*'
        		},
            'body': "Not exist in params"
        }
        else:
            return set(userid, clipboard)
    if method == "delete":
        note_id = event["queryStringParameters"]["noteid"]
        return deleteItem(userid, note_id)

