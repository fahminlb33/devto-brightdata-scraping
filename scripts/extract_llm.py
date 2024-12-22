import json
import argparse
from typing import Any

import dspy
import mlflow

from rich import print
from magic.extractor import StructuredDataExtractor


def run_product_category(args: dict[str, Any], extractor: StructuredDataExtractor):
    with (
        open(args["products_file"], "r") as input_file,
        open(args["output_file"], "a+") as output_file,
    ):
        # process each file
        for line in input_file:
            # parse file
            row = json.loads(line)

            # perform extraction
            predicted_category = extractor.extract_product_type(row["product_name"])

            # write to file
            json.dump(
                {
                    "id": row["id"],
                    "category": predicted_category,
                    "product_name": row["product_name"],
                },
                output_file,
            )
            output_file.write("\n")


def run_spec_extraction(args: dict[str, Any], extractor: StructuredDataExtractor):
    with (
        open(args["products_file"], "r") as input_file,
        open(args["output_file"], "a+") as output_file,
    ):
        # process each file
        for line in input_file:
            # parse file
            row = json.loads(line)

            # build product desc
            product_desc = row["product_name"]
            if "description" in row and row["description"] is not None:
                product_desc += "\n" + row["description"]

            product_extra = ""
            if "extra_description" in row and row["extra_description"] is not None:
                product_extra = row["extra_description"]

            # extract specs
            try:
                res = extractor.extract_specs(product_desc, product_extra).toDict()
                res.pop("reasoning")

                data = {"id": row["id"], "product_name": row["product_name"], **res}
                print(data)

                # write to file
                json.dump(data, output_file)
                output_file.write("\n")
            except:
                print(dspy.inspect_history(n=5))
                break


def main(args: dict[str, str]):
    # setup MLflow tracing
    if args["tracing_url"] is not None and args["tracing_url"].startswith("http"):
        mlflow.set_tracking_uri(args["tracing_url"])
        mlflow.set_experiment(args["tracing_experiment"])
        mlflow.dspy.autolog()

    # setup dspy
    dspy.configure(
        lm=dspy.LM(
            f"ollama_chat/{args['ollama_model']}",
            api_base=args["ollama_url"],
            api_key="",
        )
    )

    # create extractor
    extractor = StructuredDataExtractor(args["few_shot_file"])

    # run
    if args["mode"] == "product-category":
        run_product_category(args, extractor)
    elif args["mode"] == "product-specs":
        run_spec_extraction(args, extractor)


if __name__ == "__main__":
    # --- create main argparser
    parser = argparse.ArgumentParser()
    parser.add_argument("--ollama-url", type=str, default="http://localhost:7869")
    parser.add_argument("--ollama-model", type=str, default="llama3.1:latest")
    parser.add_argument(
        "--few-shot-file",
        type=str,
        default="./data/inputs/fewshot-product-category.jsonl",
    )
    parser.add_argument("--tracing-url", type=str)
    parser.add_argument("--tracing-experiment", type=str)

    # --- register subparsers
    subparsers = parser.add_subparsers(dest="mode")

    # categorize products
    product_category = subparsers.add_parser("product-category")
    product_category.add_argument("--products-file", type=str, required=True)
    product_category.add_argument("--output-file", type=str, required=True)

    # extract specification
    product_spec = subparsers.add_parser("product-specs")
    product_spec.add_argument("--products-file", type=str, required=True)
    product_spec.add_argument("--output-file", type=str, required=True)

    # run app
    main(vars(parser.parse_args()))
