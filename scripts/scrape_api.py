import os
import json
import glob
import argparse
from typing import Any

import tqdm

from magic.extras import partition
from magic.brightdata import BrightDataClient

LAZADA_DOMAIN = "https://www.lazada.co.id"
ENGINE_DATASET_ID = {
    "tokopedia": "gd_lxk24yba297r8qd3tp",
    "lazada": "gd_lk14r4zxuiw2uxpk6",
}


def run_discover(args: dict[str, Any], client: BrightDataClient):
    # open input file
    with (
        open(args["terms_file"], "r") as input_file,
        open(args["output_file"], "a+") as output_file,
    ):
        # batch data
        jobs = list(partition(input_file, args["batch_size"]))

        # parse line
        for keywords in tqdm.tqdm(jobs):
            # create body
            body = [{"keyword": x} for x in keywords]
            if args["engine"] == "lazada":
                body = [{**x, "domain": LAZADA_DOMAIN} for x in body]

            # trigger scraping
            res = client.trigger_data_collection(
                ENGINE_DATASET_ID[args["engine"]],
                args["limit"],
                True,
                body,
                "discover_new",
                "keyword",
            )

            # save to output
            job = {
                "snapshot_id": res["snapshot_id"],
                "engine": args["engine"],
                "keywords": keywords,
            }

            json.dump(job, output_file)
            output_file.write("\n")


def run_collect(args: dict[str, Any], client: BrightDataClient):
    # open input file
    with (
        open(args["urls_file"], "r") as input_file,
        open(args["output_file"], "a+") as output_file,
    ):
        # process each URL
        for url in tqdm.tqdm(input_file.readlines()):
            # create body
            body = [{"url": x} for x in url]

            # trigger scraping
            res = client.trigger_data_collection(
                ENGINE_DATASET_ID[args["engine"]], args["limit"], True, body
            )

            # save to output
            job = {
                "snapshot_id": res["snapshot_id"],
                "engine": args["engine"],
                "keywords": url,
            }

            json.dump(job, output_file)
            output_file.write("\n")


def run_download(args: dict[str, Any], client: BrightDataClient):
    # make sure output directory is exists
    os.makedirs(args["output_path"], exist_ok=True)

    # glob downloaded files
    downloaded_files = glob.glob(os.path.join(args["output_path"], "*.jsonl"))

    # to store stats
    stats = {
        "downloaded": 0,
        "skipped": 0,
        "running": 0,
        "failed": 0,
    }

    # open input file
    with open(args["snapshots_file"], "r") as f:
        # process each job
        for line in tqdm.tqdm(f.readlines()):
            # parse job
            job = json.loads(line.strip())

            # check if this file is already downloaded
            if job["snapshot_id"] + ".jsonl" in downloaded_files:
                stats["skipped"] += 1
                continue

            # check status
            res = client.monitor_progress(job["snapshot_id"])

            # process response
            if res["status"] == "ready":
                stats["downloaded"] += 1

                # open save file
                with open(
                    os.path.join(args["output_path"], job["snapshot_id"] + ".jsonl"),
                    "w",
                ) as output_file:
                    # download the data
                    res = client.download(job["snapshot_id"])

                    # save to file
                    output_file.write(res)
            elif res["status"] == "running":
                stats["running"] += 1
            elif res["status"] == "failed":
                stats["failed"] += 1

    # print statistics
    print("Downloaded:", stats["downloaded"])
    print("Skipped:", stats["skipped"])
    print("Running:", stats["running"])
    print("Failed:", stats["failed"])


def run_extract_extras(args: dict[str, Any]):
    # find all files
    files = glob.glob(os.path.join(args["output_path"], "*.jsonl"))

    # open output file
    with open(args["output_file"], "a+") as output_file:
        # process each file
        for result_file in tqdm.tqdm(files, position=0, desc="Results Files"):
            # read result file
            with open(result_file, "r") as input_file:
                # process each result
                for line in tqdm.tqdm(
                    input_file.readlines(), position=1, leave=False, desc="Result Entry"
                ):
                    # parse
                    entry = json.loads(line.strip())

                    # if this has error, output it
                    if "error" in entry:
                        output_file.write(entry["input"]["url"])
                        output_file.write("\n")

                    # if this product has variation URL, output it
                    if "variations" in entry and len(entry["variations"]) > 0:
                        for variation in entry["variations"]:
                            if "url" not in variation:
                                continue

                            output_file.write(variation["url"])
                            output_file.write("\n")


def main(args: dict[str, Any]):
    print(args)

    # create API client
    client = BrightDataClient(args["api_key"])

    # run
    if args["mode"] == "discover":
        run_discover(args, client)
    elif args["mode"] == "collect":
        run_collect(args, client)
    elif args["mode"] == "download":
        run_download(args, client)
    elif args["mode"] == "extract-extras":
        run_extract_extras(args)


if __name__ == "__main__":
    # --- create main argparser
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", type=str, required=True)

    # --- register subparsers
    subparsers = parser.add_subparsers(dest="mode")

    # trigger scraping by keyword
    discover = subparsers.add_parser("discover")
    discover.add_argument("--terms-file", type=str, required=True)
    discover.add_argument("--output-file", type=str, required=True)
    discover.add_argument(
        "--engine", type=str, choices=["tokopedia", "lazada"], required=True
    )
    discover.add_argument("--batch-size", type=int, default=3)
    discover.add_argument("--limit", type=int, default=50)

    # trigger scraping by URL collection
    collect = subparsers.add_parser("collect")
    collect.add_argument("--urls-file", type=str, required=True)
    collect.add_argument("--output-file", type=str, required=True)
    collect.add_argument(
        "--engine", type=str, choices=["tokopedia", "lazada"], required=True
    )
    collect.add_argument("--batch-size", type=int, default=5)
    collect.add_argument("--limit", type=int, default=20)

    # download snapshots
    download = subparsers.add_parser("download")
    download.add_argument("--snapshots-file", type=str, required=True)
    download.add_argument("--output-path", type=str, required=True)

    # extract failed URLs and variants
    extract_extras = subparsers.add_parser("extract-extras")
    extract_extras.add_argument("--output-path", type=str, required=True)
    extract_extras.add_argument("--output-file", type=str, required=True)

    # run app
    main(vars(parser.parse_args()))
