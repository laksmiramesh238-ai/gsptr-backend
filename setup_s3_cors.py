"""Run once to configure CORS on the S3 bucket."""
import boto3
import os
from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION', 'ap-south-1'),
)

BUCKET = os.getenv('AWS_BUCKET', 'deloai-mathquest')

cors_config = {
    'CORSRules': [
        {
            'AllowedOrigins': ['*'],
            'AllowedMethods': ['GET', 'POST', 'PUT'],
            'AllowedHeaders': ['*'],
            'ExposeHeaders': ['ETag'],
            'MaxAgeSeconds': 3000,
        }
    ]
}

s3.put_bucket_cors(Bucket=BUCKET, CORSConfiguration=cors_config)
print(f"✓ CORS configured on bucket: {BUCKET}")
