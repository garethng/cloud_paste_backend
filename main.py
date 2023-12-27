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
table = dynamodb['paste-clip-note']

    


def query(userid):
    try:
        # 从 DynamoDB 获取数据
        print(userid)
        response = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('userid').eq('userid')
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
            item_list = response['Item']
            clipboard = {}
            
            for item in item_list:
                note = item.get("note")
                create_date = item.get("createdate")
                note_id = item.get("noteid")

                total_content = clipboard[create_date]
                total_content.append({
                    "note_id": note_id,
                    "note": note
                })
                clipboard[item.get("datetime")] = total_content
            
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
            'body': e
        }
        
def set(userid, clipboard):
    # 创建一个timezone对象
    # tz = pytz.timezone('Asia/Shanghai')

    current_date = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
    index_date = datetime.now().strftime('%Y-%m-%d')
    note_id = generate_uuid(f"{current_date}:{userid}:{clipboard}")

    try:
        # 更新 DynamoDB 数据
        response = table.get_item(
            Key={'userid': userid}
        )
        content = response['Item']['content']
        new_note = {
            "userid": userid,
            "noteid": noteid,
            "note": clipboard,
            "createdate": index_date
        }
        response = table.put_item(new_note)
        # 找到新 clipboard 应该插入的位置

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
        'body': json.dumps(note_id)
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
        index_date = event["queryStringParameters"]["datetime"]
        childIndex = event["queryStringParameters"]["index"]
        return deleteItem(userid, index_date, childIndex)

