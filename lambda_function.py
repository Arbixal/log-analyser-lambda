import json
import platform
import asyncio
import re
import wcl_parser
import boto3
import os
from botocore.errorfactory import ClientError
from exceptions import NotFoundException


S3_BUCKET = os.environ['S3_BUCKET']
API_VERSION = 'v1.1'
CONTENT_TYPE_PREFIX = "application/vnd.bixnpieces.logsummary-"
CONTENT_TYPE_PATTERN = CONTENT_TYPE_PREFIX + "%s+json"


def lambda_handler(event, context):
    params = event['pathParameters']
    report_id = ''
    fight_id = -1
    request_version = API_VERSION

    if 'headers' in event and 'Accept' in event['headers']:
        content_type = event['headers']['Accept']
        if content_type.startswith(CONTENT_TYPE_PREFIX):
            request_version = content_type[len(CONTENT_TYPE_PREFIX):len(CONTENT_TYPE_PREFIX)+4]

    if 'id' in params:
        report_id = params['id']

    if 'fight' in params:
        fight_id = int(params['fight'])

    if re.fullmatch('(?a:[a-zA-Z0-9]{16})', report_id) is None:
        return {
            "statusCode": 400,
            "body": '%s is not a valid identifier.' % report_id
        }

    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # check s3 bucket
    s3_client = boto3.resource("s3", region_name='ap-southeast-2')

    # try requested version
    object_key = '%s/%s/fight%d.json' % (report_id, request_version, fight_id) # replace object key
    try:
        file_content = s3_client.Object(S3_BUCKET, object_key).get()["Body"].read()
        file_json = json.loads(file_content)
        return {
            "statusCode": 200,
            "headers": {"content-type": CONTENT_TYPE_PATTERN % request_version},
            "body": json.dumps(file_json)
        }
    except ClientError as e:
        print("Did not read %s from cache %s - %s" % (request_version, object_key, e))

    # if different from current version, try get cached current version
    if request_version != API_VERSION:
        object_key = '%s/%s/fight%d.json' % (report_id, API_VERSION, fight_id) # replace object key
        try:
            file_content = s3_client.Object(S3_BUCKET, object_key).get()["Body"].read()
            file_json = json.loads(file_content)
            return {
                "statusCode": 200,
                "headers": {"content-type": CONTENT_TYPE_PATTERN % API_VERSION},
                "body": json.dumps(file_json)
            }
        except ClientError as e:
            print("Did not read %s from cache %s - %s" % (API_VERSION, object_key, e))

    try:
        response = asyncio.run(async_handler(report_id))
    except NotFoundException as ex:
        return {
            "statusCode": 404,
            "body": ex.message
        }

    # save to s3 bucket
    fight_response = None
    fight_ids = [x['id'] for x in response.fights.values() if x['boss'] > 0]
    fight_ids.append(-1)    # summary
    fight_ids.append(0)     # trash
    for fight in fight_ids:
        fight_data = response.to_json(fight)
        if fight == fight_id:
            fight_response = fight_data

        # save to s3 bucket
        save_key = '%s/%s/fight%d.json' % (report_id, API_VERSION, fight)
        s3_client.Object(S3_BUCKET, save_key).put(Body=json.dumps(fight_data))

    if fight_response is None:
        return {
            "statusCode": 404,
            "body": '%d is not a valid boss fight or summary identifier.' % fight_id
        }

    return {
        "statusCode": 200,
        "headers": {"contentType": CONTENT_TYPE_PATTERN % API_VERSION},
        "body": json.dumps(fight_response)
    }


async def async_handler(report_id):
    async with wcl_parser.WCLParser(report_id) as parser:
        return await parser.parse_report()

if __name__ == '__main__':
    # print(lambda_handler({"pathParameters": {"id": "MhmWRGb23rJ4DX9F", "fight": "-1"}}, {}))
    # print(lambda_handler({"pathParameters": {"id": "aH7DNdKTjZMRfVyb", "fight": "-1"},
    #                       "headers": {"Accept": "application/vnd.bixnpieces.logsummary-v0.9+json"}}, {}))
    # print(lambda_handler({"pathParameters": {"id": "p2AZhyBCH4xb9t8Y", "fight": "-1"}}, {}))
    print(lambda_handler({"pathParameters": {"id": "J3VZBXgTCFpyhdG9", "fight": "-1"}}, {}))
