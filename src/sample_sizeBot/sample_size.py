# sample_size_bot.py
from math import ceil
from scipy.stats import norm

class SampleSizeBot:
    def __init__(self, confidence=0.95):
        self.confidence = confidence
        self.z = norm.ppf(1 - (1 - confidence) / 2)

    def prevalence(self, p=0.5, d=0.05, population=None):
        """
        Sample size for prevalence study
        """
        # initial (infinite population) estimate
        n0 = (self.z ** 2 * p * (1 - p)) / (d ** 2)

        if population:
            try:
                N = int(population)
            except Exception:
                N = None
            if N and N > 0:
                n_corr = n0 / (1 + (n0 - 1) / N)
                return ceil(n_corr)

        return ceil(n0)

    def mean_estimation(self, std_dev, d):
        """
        Sample size for mean estimation
        """
        n = (self.z ** 2 * std_dev ** 2) / (d ** 2)
        return ceil(n)

    def regression(self, predictors, power=0.80):
        """
        Rule-of-thumb regression sample size
        """
        return predictors * 15


if __name__ == "__main__":
    bot = SampleSizeBot()
    print("Prevalence:", bot.prevalence(p=0.3, d=0.05))
    print("Mean:", bot.mean_estimation(std_dev=10, d=2))
    print("Regression:", bot.regression(predictors=5))
