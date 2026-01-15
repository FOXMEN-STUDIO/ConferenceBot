# statistical_test_selector_bot.py

class StatisticalTestSelectorBot:

    def select_test(self, iv_type, dv_type, groups=None):
        """
        iv_type: categorical / continuous
        dv_type: categorical / continuous
        """
        if iv_type == "categorical" and dv_type == "categorical":
            return "Chi-square Test"

        if iv_type == "categorical" and dv_type == "continuous":
            return "Independent t-test" if groups == 2 else "ANOVA"

        if iv_type == "continuous" and dv_type == "continuous":
            return "Pearson Correlation"

        return "Logistic Regression"

    def assumptions(self, test):
        assumptions_map = {
            "Chi-square Test": [
                "Expected frequency > 5",
                "Independence of observations"
            ],
            "Independent t-test": [
                "Normality",
                "Homogeneity of variance"
            ],
            "ANOVA": [
                "Normality",
                "Equal variances",
                "Independent samples"
            ],
            "Pearson Correlation": [
                "Linearity",
                "Normality"
            ],
            "Logistic Regression": [
                "Binary outcome",
                "No multicollinearity"
            ]
        }
        return assumptions_map.get(test, [])

if __name__ == "__main__":
    bot = StatisticalTestSelectorBot()
    test = bot.select_test(
        iv_type="categorical",
        dv_type="continuous",
        groups=3
    )
    print("Recommended Test:", test)
    print("Assumptions:", bot.assumptions(test))
