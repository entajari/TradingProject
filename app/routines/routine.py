import time
import itertools
import datetime
import logging
import logging.config

# Internal imports
import settings
from common import Config
from setups import StaticSetup, RollingWindowSetup

logging.config.dictConfig(settings.LOGGING_CONFIG)


ROUTINE_DEFAULT = {
    "setup": "rolling",
    "assets": settings.AVAILABLE_DATA.keys(),
    "tcs": settings.TRANSACTION_COSTS,
    "frequencies": settings.FREQUENCIES,
    "reward_functions": settings.REWARD_FUNCTIONS,
}


class Routine(object):
    def __init__(self, routine_name, target_episodes=[50]):
        self.logger = logging.getLogger(__name__)

        self.routine_name = routine_name

        self.config_name = None
        self.setup = "rolling"
        self.assets = settings.AVAILABLE_DATA.keys()
        self.tcs = settings.TRANSACTION_COSTS
        self.frequencies = settings.FREQUENCIES
        self.reward_functions = settings.REWARD_FUNCTIONS
        self.stgs = settings.STGS_ALGO
        # self.stgs = settings.STGS_BASE
        self.seeds = [42, 1, 6888, 13, 17]
        self.episodes = target_episodes
        self.load_model = False

        if self.routine_name == "load_model":
            self.episodes = target_episodes
            self.load_model = True

    def run(self):
        self.logger.info("### Routine option selected ###")
        self.logger.info("------- Routine Summary -------")
        self.logger.info(f"Assets: {self.assets}")
        self.logger.info(f"Transaction Costs: {self.tcs}")
        self.logger.info(f"Frequencies: {self.frequencies}")
        self.logger.info(f"Reward Functions: {self.reward_functions}")
        self.logger.info(f"Seed: {self.seeds}")
        self.logger.info(f"Episodes: {self.episodes}")

        current_time = datetime.datetime.now()
        self.logger.info(f">>> Starting routine `{self.routine_name}` <<<")

        specs = list(
            itertools.product(
                *[
                    self.frequencies,
                    self.tcs,
                    self.assets,
                    self.reward_functions,
                    self.seeds,
                    self.stgs,
                    self.episodes,
                ]
            )
        )
        total_runs = remaining_runs = len(specs)

        initial_p_time = time.process_time()
        run_count = 1
        elapsed_t = []
        for frequency, tc, asset, reward_function, seed, stg, episode in specs:
            self.config_name = "min-sent-5" if stg == "sentarl" else "default"
            cfg = Config(
                name=self.config_name,
                seed=seed,
                stg=stg,
                asset=asset,
                episodes=episode,
                setup=self.setup,
                frequency=frequency,
                reward_function=reward_function,
                transaction_cost=tc,
                sb_verbose=False,
                ep_verbose=False,
            )

            initial_run_t = time.process_time()
            self.logger.info(
                f"\n--- Starting run {run_count}/{total_runs} for: {stg}, \
                    {asset}, tc {tc}, {frequency}, {reward_function}, \
                    seed {seed}, episode {episode} ---"
            )

            setup = (
                StaticSetup(cfg)
                if cfg.setup == "static"
                else RollingWindowSetup(cfg, self.load_model)
            )

            setup.run()

            t = time.process_time()
            elapsed_t.append(t - initial_run_t)
            self.logger.info(
                f"--- Finishing run #{run_count} for: {stg}, {asset}, \
                    tc {tc}, {frequency}, {reward_function} \
                    with elapsed time {elapsed_t[0]:.2f}s ---"
            )

            run_count += 1

            remaining_runs -= 1
            mean_elapsed_t = sum(elapsed_t) / len(elapsed_t)
            remaining_time = datetime.timedelta(
                seconds=remaining_runs * mean_elapsed_t
            )
            current_time = datetime.datetime.now()
            estimated_end_time = current_time + remaining_time
            if remaining_runs > 0:
                self.logger.info(
                    f"Estimated time of finish: {estimated_end_time}; \
                        remaining ({remaining_time})"
                )

        current_time = datetime.datetime.now()
        elapsed_t = t - initial_p_time
        self.logger.info(
            f">>> Ending routine {self.routine_name} \
                with a total runtime of {elapsed_t:.2f}s <<<"
        )
