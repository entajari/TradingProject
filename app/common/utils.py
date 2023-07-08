import os
from pathlib import Path
from typing import Dict, Tuple, Union, List
import csv
import inspect

import pandas as pd

# internal imports
import settings
from .config import Config

_color2num = dict(
    gray=30,
    red=31,
    green=32,
    yellow=33,
    blue=34,
    magenta=35,
    cyan=36,
    white=37,
    crimson=38,
)


def generate_filename(
    config: Config, window: str = None, filetype: str = "result"
) -> str:
    config_dict = dict(inspect.getmembers(config))
    filename_fields = settings.BASE_FILENAME_FIELDS.copy()

    if config_dict["stg"] in settings.STGS_ALGO:
        config_dict["config"] = config_dict[
            "name"
        ] 
        ending_fields = (
            ["algo", "episodes"] if filetype == "result" else ["algo"]
        )
        filename_fields = (
            ["config"] + filename_fields + ending_fields
        ) 
    if config_dict["stg"] not in settings.STGS_BASE:
        filename_fields.extend(["reward_function", "seed"])


    fields = [[field, str(config_dict[field])] for field in filename_fields]

    if filetype != "model":
        fields.append([window])

    return "-".join("_".join(field) for field in fields)


def prepare_folder_structure(
    abs_origin_path,
    config: Config = None,
    foldertype: str = "result",
    window_roll: int = 0,
):
    folder_path = abs_origin_path

    if config:
        folder_list = dict(inspect.getmembers(config))
        folder_list["seed"] = "seed_" + str(config.seed)

        folder_levels = settings.FOLDER_LEVELS_RESULTS
        if foldertype == "model":
            folder_levels = settings.FOLDER_LEVELS_MODELS
            folder_list["window_roll"] = "roll_" + str(window_roll)

        if not all(k in folder_list for k in folder_levels):
            raise ValueError(
                "Some of the following entries not found in config: ",
                folder_levels,
            )

        folder_path = os.path.join(
            abs_origin_path, *[str(folder_list[k]) for k in folder_levels]
        )

    Path(folder_path).mkdir(parents=True, exist_ok=True)

    return folder_path


def load_dataset(name, index_name):
    path = os.path.join(settings.DATA_DIR, name + ".csv")
    return pd.read_csv(path, index_col=index_name)


def split_data(df, window_size, test_size, val_size=0, use_ratio=True):
 
    expected_type = float if use_ratio else int
    if not isinstance(test_size, expected_type) or (
        val_size and not isinstance(val_size, expected_type)
    ):
        raise ValueError(
            "use_ratio={} while size args are of type {}".format(
                use_ratio, expected_type
            )
        )

    df_size = len(df.index)

    train_size = 1 - test_size if use_ratio else df_size - test_size
    idx_mark = int(train_size * df_size) if use_ratio else train_size
    slice_idx = idx_mark - window_size
    df_train, df_test = (
        df.iloc[:idx_mark],
        df.iloc[slice_idx:],
    )  # adjust to window size

    df_val = df_test
    if val_size > 0:
        if use_ratio:
            val_factor = (
                val_size / train_size
            )  # val_factor x train_ratio = val_ratio
            train_factor = 1 - val_factor
        idx_mark = (
            int(train_factor * idx_mark) if use_ratio else idx_mark - val_size
        )
        slice_idx = idx_mark - window_size
        df_train, df_val = (
            df_train.iloc[:idx_mark],
            df_train.iloc[slice_idx:],
        )  # adjust to window size

    return df_train, df_test, df_val

def colorize(string, color, bold=False, highlight=False):

    attr = []
    num = _color2num[color]
    if highlight:
        num += 10
    attr.append(str(num))

    if bold:
        attr.append("1")
    attrs = ";".join(attr)
    return "\x1b[%sm%s\x1b[0m" % (attrs, string)


class CSVOutput(object):

    def __init__(
        self,
        config: Config,
        fieldnames: List,
        abs_filename: str,
        overwrite_file: bool = True,
        delimiter: str = ";",
    ):
        self.config = config

        mode = (
            "w" if overwrite_file else "a"
        ) 
        self.file_handler = open(os.path.join(abs_filename + ".csv"), mode)

        self.csv_writer = csv.DictWriter(
            self.file_handler,
            delimiter=delimiter,
            fieldnames=fieldnames,
            extrasaction="ignore",
        )

        if overwrite_file:
            self.csv_writer.writeheader()
            self.file_handler.flush()

    def write(self, row: Dict[str, Union[str, Tuple[str, ...]]]) -> None:
        self.csv_writer.writerow(row)
        self.file_handler.flush()

    def close(self) -> None:
        self.file_handler.close()
