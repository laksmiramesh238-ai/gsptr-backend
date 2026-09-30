"""
One-time cross-account S3 backfill copy: copies every object from the old
account's 'azad' bucket to the new account's 'gsptr-media-prod' bucket,
as part of the AWS account migration.

Uses boto3's high-level copy() (server-side S3-to-S3 transfer, handles the
5GB single-copy limit transparently via multipart copy for large files —
no data ever leaves AWS's network, none of it flows through this process).

Resumable / idempotent: skips any key that already exists at the
destination with a matching size, so re-running after an interruption
only copies what's left.

Requires credentials for BOTH accounts:
  OLD_KEY / OLD_SECRET   - source account (read access to 'azad' bucket)
  NEW_KEY / NEW_SECRET   - destination account (write access to new bucket)

Usage:
  python migrate_s3_bucket.py                 # copies everything
  python migrate_s3_bucket.py --dry-run        # lists what would be copied, no writes
"""
import os, sys, boto3
from concurrent.futures import ThreadPoolExecutor, as_completed
from boto3.s3.transfer import TransferConfig

try: sys.stdout.reconfigure(encoding='utf-8')
except Exception: pass

SRC_BUCKET = "azad"
DST_BUCKET = "gsptr-media-prod"
CONCURRENCY = 12

OLD = dict(
    aws_access_key_id=os.environ["OLD_KEY"],
    aws_secret_access_key=os.environ["OLD_SECRET"],
    region_name="us-east-1",
)
NEW = dict(
    aws_access_key_id=os.environ["NEW_KEY"],
    aws_secret_access_key=os.environ["NEW_SECRET"],
    region_name="us-east-1",
)

old_s3 = boto3.client("s3", **OLD)
new_s3 = boto3.client("s3", **NEW)

TRANSFER_CONFIG = TransferConfig(
    multipart_threshold=1024 * 1024 * 1024,   # 1GB — anything bigger uses multipart copy
    max_concurrency=4,
    multipart_chunksize=256 * 1024 * 1024,    # 256MB parts
)


def list_all(client, bucket):
    out = {}
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket):
        for obj in page.get("Contents", []):
            out[obj["Key"]] = obj["Size"]
    return out


def copy_one(key, size):
    try:
        new_s3.copy(
            CopySource={"Bucket": SRC_BUCKET, "Key": key},
            Bucket=DST_BUCKET,
            Key=key,
            Config=TRANSFER_CONFIG,
        )
        return (key, size, "ok", None)
    except Exception as e:
        return (key, size, "failed", str(e))


def human(n):
    for unit in ["B", "KB", "MB", "GB"]:
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}TB"


def main():
    dry_run = "--dry-run" in sys.argv

    print("Listing source bucket...")
    src = list_all(old_s3, SRC_BUCKET)
    print(f"  {len(src)} objects, {human(sum(src.values()))}")

    print("Listing destination bucket (to figure out what's already copied)...")
    dst = list_all(new_s3, DST_BUCKET)
    print(f"  {len(dst)} objects already present, {human(sum(dst.values()))}")

    todo = [(k, sz) for k, sz in src.items() if dst.get(k) != sz]
    print(f"\n{len(todo)} object(s) to copy ({human(sum(sz for _, sz in todo))})")

    if dry_run:
        for k, sz in todo[:20]:
            print(f"  would copy: {human(sz):>10s}  {k}")
        if len(todo) > 20:
            print(f"  ... and {len(todo) - 20} more")
        return

    if not todo:
        print("Nothing to do — destination is already fully in sync.")
        return

    done = 0
    failed = []
    total_bytes = sum(sz for _, sz in todo)
    copied_bytes = 0

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
        futures = {pool.submit(copy_one, k, sz): (k, sz) for k, sz in todo}
        for fut in as_completed(futures):
            key, size, status, err = fut.result()
            done += 1
            if status == "ok":
                copied_bytes += size
                print(f"[{done}/{len(todo)}] OK   {human(size):>10s}  {key}  (total copied: {human(copied_bytes)}/{human(total_bytes)})")
            else:
                failed.append((key, err))
                print(f"[{done}/{len(todo)}] FAIL {human(size):>10s}  {key}  -> {err}")

    print()
    print("=== SUMMARY ===")
    print(f"  copied: {done - len(failed)}")
    print(f"  failed: {len(failed)}")
    if failed:
        print("\nFailed keys (re-run this script to retry — it's resumable):")
        for k, err in failed[:20]:
            print(f"  {k}: {err}")


if __name__ == "__main__":
    main()
