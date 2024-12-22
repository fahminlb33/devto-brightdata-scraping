from collections.abc import Iterable

import pandas as pd


def proba_encode_map(series: pd.Series) -> dict:
    return {k: v / len(series) for k, v in series.value_counts().to_dict().items()}


def partition(iter: Iterable, n: int):
    temp_batch = []

    for line in iter:
        # skip empty line
        if line is None or (isinstance(line, str) and len(line.strip()) == 0):
            continue

        # if the batch is filled, yield
        if len(temp_batch) == n:
            yield temp_batch
            temp_batch = []

        # add to batch
        temp_batch.append(line.strip())

    # if the batch has remaining data, yield it
    if len(temp_batch) > 0:
        yield temp_batch
