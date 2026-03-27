import os
import re

AWS_BUCKET = os.getenv('AWS_BUCKET', 'deloai-mathquest')
AWS_REGION = os.getenv('AWS_REGION', 'ap-south-1')
CLOUDFRONT_DOMAIN = os.getenv('CLOUDFRONT_DOMAIN', '')

# Matches both URL styles S3 uses
_S3_PATTERN = re.compile(
    rf'https?://{re.escape(AWS_BUCKET)}\.s3[^/]*\.amazonaws\.com'
)


def cdn_url(url: str) -> str:
    """Replace S3 origin URL with CloudFront URL. Pass-through if no CF domain set."""
    if not url or not CLOUDFRONT_DOMAIN:
        return url
    return _S3_PATTERN.sub(f'https://{CLOUDFRONT_DOMAIN}', url)
