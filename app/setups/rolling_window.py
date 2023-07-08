import logging
import settings
from .base_setup import BaseSetup
from common import split_data
from models import train_model, load_model
import itertools
from common import Config


class RollingWindowSetup(BaseSetup):
    def __init__(self, config: Config, load_model: bool = False):
        super(RollingWindowSetup, self).__init__(config=config)
        self.logger = logging.getLogger(__name__)

        self.load_model = load_model
        self.k_rolls = 5
        self.use_val = False

        (
            self.train_size,
            self.test_size,
            self.val_size,
        ) = self._get_dataset_sizes()
        self.dfs = self._get_dfs()

        if self.config.stg in settings.STGS_ALGO:
            self.total_timesteps = self.config.episodes * (
                self.train_size - self.pivot_window_size
            )
            self.logger.info(
                f"Total training timesteps: {self.total_timesteps}"
            )

    def run(self):
        for roll, df_item in enumerate(self.dfs):
            additional_info = dict(
                {
                    "window_roll": roll,
                    "seed": self.config.seed
                    if self.config.stg in settings.STGS_ALGO
                    else None,
                    "config": self.config.name
                    if self.config.stg in settings.STGS_ALGO
                    else None,
                    "train_episodes": self.config.episodes,
                }
            )
            overwrite_file = True if roll == 0 else False

            envs = {}
            for window in self.window_types:
                if (
                    self.load_model
                    and self.config.stg in settings.STGS_ALGO
                    and window in ["train", "val"]
                ):
                    continue

                frame_bound = (
                    self.pivot_window_size,
                    len(df_item[window].index),
                )
                envs[window] = self._prepare_env(
                    df_item[window],
                    frame_bound,
                    window,
                    additional_info=additional_info,
                    overwrite_file=overwrite_file,
                )

            if self.config.stg in settings.STGS_BASE:
                for window in self.window_types:
                    self._run_window(envs[window])
            else:
                if self.load_model:
                    model = load_model(
                        self.total_timesteps, self.config, window, roll
                    )
                else:
                    model = train_model(
                        envs["train"],
                        self.total_timesteps,
                        envs["val"],
                        self.config,
                        roll,
                    )

                self._run_window(envs["test"], model)

    def _run_window(self, env, model=None):

        test_runs = 1

        for k in range(test_runs):
            observation = env.reset()

            while True:
                action = self._get_stg_action(env, observation, model)
                observation, reward, done, info = env.step(action)

                if done:
                    if self.config.ep_verbose:
                        self.logger.info("info")
                    break

        env.close()

    def _get_dataset_sizes(self, min_train_size=3000, min_train_ratio=0.9):
        total_size = len(self.df.index)

        for i in itertools.count(start=min_train_size):

            train_size = i
            train_size_adjusted = train_size + self.pivot_window_size

            total_size_available = total_size - train_size_adjusted

            k_rolls_offset = self.k_rolls + 1 if self.use_val else self.k_rolls

            test_size = total_size_available / k_rolls_offset

            val_size = test_size if self.use_val else 0
            complete_size = (
                train_size + val_size + test_size
                if self.use_val
                else train_size + test_size
            )
            train_ratio = train_size / complete_size

            if test_size.is_integer() and train_ratio >= min_train_ratio:
                break

        return train_size_adjusted, int(test_size), int(val_size)

    def _get_dfs(self):
        dfs = []
        df_remaining = self.df.copy()

        adopted_size = (
            self.train_size + 2 * self.test_size
            if self.use_val
            else self.train_size + self.test_size
        )
        roll_size = self.test_size
        for k in range(self.k_rolls):
            df_roll = df_remaining.iloc[:adopted_size]
            df_remaining = df_remaining.iloc[roll_size:]

            df_train, df_test, df_val = split_data(
                df_roll,
                self.pivot_window_size,
                self.test_size,
                self.val_size,
                False,
            )

            dfs.append({"train": df_train, "val": df_val, "test": df_test})

        return dfs
