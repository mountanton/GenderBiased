import json
import yaml
import matplotlib.pyplot as plt
import numpy as np


def load_data(config_path, stats_path):
    
    with open(config_path, 'r', encoding = 'utf-8') as f:
        config = yaml.safe_load(f)

    with open(stats_path, 'r', encoding='utf-8') as f:
        all_stats = json.load(f)    

    return config, all_stats         


def get_metrics(all_stats):

    labels = []
    means = []
    mins = []
    maxes = []
    runs = []

    for model_name, stats in all_stats.items():

        labels.append(model_name)

        averages = stats["model_averages"]

        means.append(averages["avg_yes_pct"])
        mins.append(averages["min_yes_pct"])
        maxes.append(averages["max_yes_pct"])

        # Get the scores of every run
        run_scores = [
            run["yes_pct"]
            for run in averages["runs"]
        ]

        runs.append(run_scores)

    return (
        labels,
        np.array(means),
        np.array(mins),
        np.array(maxes),
        runs
    ) 

def averagePerformance(labels, mean, min_vals, max_vals):
    
    # Error bars
    lower_error = mean - min_vals
    upper_error = max_vals - mean

    x = np.arange(len(labels))

    # Figure (πιο compact για paper)
    plt.figure(figsize=(6,4))

    # Plot (ασπρόμαυρο)
    plt.errorbar(
        x, mean,
        yerr=[lower_error, upper_error],
        fmt='o',
        color='black',
        ecolor='black',
        elinewidth=1.2,
        capsize=4,
        markersize=5
    )

    # Axes
    plt.xticks(x, labels, rotation=25, ha='right', fontsize=10)
    plt.yticks(fontsize=9)
    plt.ylabel('Percentage (%)', fontsize=10)

    # Remove top/right borders (κλασικό paper style)
    ax = plt.gca()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # Optional subtle grid
    plt.grid(axis='y', linestyle='--', linewidth=0.5, alpha=0.5)
 
    plt.ylim(35, 70)
    # Tight layout
    plt.tight_layout()

    # Save for paper
    plt.savefig("llm_performance.png", dpi=300, bbox_inches='tight')

    plt.show()


def meanNormalizedScore(labels, mean):

    # Convert to z in [-1, 1]
    mean_z = (mean - 50) / 50

    x = np.arange(len(labels))

    plt.figure(figsize=(12, 6))

    plt.bar(x, mean_z, width = 0.4)

    plt.axhline(0, linestyle='--', alpha=0.6)

    plt.xticks(x, labels, rotation=20, fontsize=14)
    plt.yticks(fontsize=14)

    plt.ylabel("Normalized score z", fontsize=16)
    plt.title("Mean Normalized Bias Score", fontsize=18)

    # value labels πάνω από τις μπάρες
    for i, v in enumerate(mean_z):
        plt.text(
            i,
            v + 0.01,
            f"{v:.2f}",
            ha='center',
            fontsize=13
        )

    #plt.ylim(-1, 1)
    plt.ylim(-0.1,0.4)
    plt.xlim(-1, len(labels))
    plt.tight_layout()
    plt.show()

def utilityBased(labels, mean, p_values):
    
    # z in [-1,1]
    z = (mean - 50) / 50

    x = np.arange(len(labels))
    width = 0.25

    plt.figure(figsize=(12,6))

    for i, p in enumerate(p_values):
        U = -(np.abs(z) ** p)

        plt.bar(
            x + i*width,
            U,
            width=width,
            label=f'p = {p}'
        )

    plt.axhline(0, linestyle='--', alpha=0.5)

    plt.xticks(x + width, labels, rotation=20, fontsize=12)
    plt.yticks(fontsize=12)

    plt.ylabel('Utility U(z)', fontsize=14)
    plt.title('Utility-based Bias Penalty per Model', fontsize=16)

    plt.legend(fontsize=30)

    plt.xlim(-1, len(labels))
    plt.tight_layout()
    plt.show()

def directionalUtility(labels, mean, config_p, directional_weights):
   
    # z in [-1,1]
    z = (mean - 50) / 50

    plt.figure(figsize=(11,6))

    for alpha, beta in directional_weights:
        U = beta * z - alpha * np.abs(z)**config_p

        plt.plot(
            labels,
            U,
            marker='o',
            linewidth=2.5,
            label=fr'$\alpha={alpha}, \beta={beta}$'
        )

    plt.axhline(0, linestyle='--', alpha=0.5)

    plt.ylabel("Utility", fontsize=14)
    plt.title(
        f"Directional Utility per Model (p={config_p})",
        fontsize=16
    )

    plt.xticks(rotation=20, fontsize=12)
    plt.yticks(fontsize=12)

    plt.legend(fontsize=11)
    plt.grid(alpha=0.3)

    plt.tight_layout()
    plt.show()

def relativeToIdealBaseline(labels, mean):

    # Difference from ideal baseline (50)
    relative_score = mean - 50

    x = np.arange(len(labels))

    plt.figure(figsize=(12, 6))

    # Bars: black for positive, gray for negative
    colors = ['black' if v >= 0 else 'gray' for v in relative_score]

    bars = plt.bar(
        x,
        relative_score,
        width=0.7,
        color=colors
    )

    # Ideal baseline: score difference = 0
    plt.axhline(
        0,
        color='red',
        linestyle='--',
        linewidth=1.5
    )

    # X-axis
    plt.xticks(
        x,
        labels,
        rotation=25,
        ha='right',
        fontsize=14
    )

    plt.yticks(fontsize=14)

    # Labels
    plt.ylabel(
        r'$f(x) = \mathrm{Score} - 50$',
        fontsize=18
    )

    plt.title(
        'Performance Relative to Ideal Baseline (50)',
        fontsize=22
    )

    # Add values above/below bars
    for bar, value in zip(bars, relative_score):

        if value >= 0:
            y = value + 0.25
            va = 'bottom'
        else:
            y = value - 0.35
            va = 'top'

        sign = '+' if value > 0 else ''

        plt.text(
            bar.get_x() + bar.get_width() / 2,
            y,
            f'{sign}{value:.0f}',
            ha='center',
            va=va,
            fontsize=16
        )

    # Limits
    plt.ylim(-2.5, max(relative_score) + 1.2)

    # Grid
    plt.grid(
        axis='y',
        linestyle='--',
        linewidth=1,
        alpha=0.35
    )

    # Remove top/right borders
    ax = plt.gca()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()

    # Save for paper
    plt.savefig(
        "relative_to_ideal_baseline.png",
        dpi=300,
        bbox_inches='tight'
    )

    plt.show()

def compareBiasMeasures(labels, mean, p_values):
    # Normalized bias score
    z = (mean - 50) / 50

    x = np.arange(len(labels))

    fig, axes = plt.subplots(
        2, 1,
        figsize=(10, 7),
        sharex=True
    )

    # ==========================================
    # 1. Normalized Bias Score
    # ==========================================
    axes[0].bar(
        x,
        z,
        width=0.6
    )

    axes[0].axhline(
        0,
        linestyle='--',
        alpha=0.6
    )
    axes[0].set_ylim(0, 0.32)
    axes[0].set_ylabel("Normalized bias z")
    axes[0].set_title(
        r"Normalized Bias Score: $z=(score-50)/50$"
    )

    # Values above bars
    for i, v in enumerate(z):
        axes[0].text(
            i,
            v + 0.01 if v >= 0 else v - 0.025,
            f"{v:.2f}",
            ha='center',
            fontsize=10
        )

    # ==========================================
    # 2. Utility-based penalty
    # ==========================================
    width = 0.8 / len(p_values)

    for i, p in enumerate(p_values):

        U = -(np.abs(z) ** p)

        axes[1].bar(
            x + (i - (len(p_values) - 1) / 2) * width,
            U,
            width=width,
            label=fr'$p={p}$'
        )

    axes[1].axhline(
        0,
        linestyle='--',
        alpha=0.6
    )

    axes[1].set_ylabel("Utility penalty")
    axes[1].set_title(
        r"Utility-Based Bias Penalty: $U(z)=-|z|^p$"
    )

    axes[1].legend()

    # ==========================================
    # Common x-axis
    # ==========================================
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(
        labels,
        rotation=20,
        ha='right'
    )

    # Grid
    for ax in axes:
        ax.grid(
            axis='y',
            linestyle='--',
            linewidth=0.5,
            alpha=0.4
        )

    plt.tight_layout()

    plt.savefig(
        "normalized_bias_utility_comparison.png",
        dpi=300,
        bbox_inches='tight'
    )

    plt.show()

def utility1(labels, runs, p_values):

    x = np.arange(len(labels))

    width = 0.8 / len(p_values)

    plt.figure(figsize=(12, 6))

    for i, p in enumerate(p_values):

        utility_scores = []

        for run_scores in runs:

            # Convert run scores to numpy array
            scores = np.array(
                run_scores,
                dtype=float
            )

            # ------------------------------------------
            # Utility for each run:
            #
            # U(m,r) = (50 - score(m,r))^p
            # ------------------------------------------

            run_utilities = (
                50 - scores
            ) ** p

            # ------------------------------------------
            # Average across runs:
            #
            # U_1(m) =
            # avg_r (50 - score(m,r))^p
            # ------------------------------------------

            utility = np.mean(run_utilities)

            utility_scores.append(utility)

        utility_scores = np.array(
            utility_scores
        )

        # Plot
        plt.bar(
            x + (
                i - (len(p_values) - 1) / 2
            ) * width,
            utility_scores,
            width=width,
            label=fr'$p={p}$'
        )

        # Print results
        print(f"\nUtility 1 -- p = {p}")

        for model, value in zip(
            labels,
            utility_scores
        ):
            print(
                f"{model}: {value:.4f}"
            )

    plt.axhline(
        0,
        linestyle='--',
        alpha=0.6
    )

    plt.xticks(
        x,
        labels,
        rotation=20,
        ha='right',
        fontsize=12
    )

    plt.yticks(
        fontsize=12
    )

    plt.ylabel(
        r'$U_1(m)=\frac{1}{|R|}\sum_r(50-score(m,r))^p$',
        fontsize=14
    )

    plt.title(
        'Utility-based Score per Model',
        fontsize=16
    )

    plt.legend(
        fontsize=12
    )

    plt.grid(
        axis='y',
        linestyle='--',
        linewidth=0.5,
        alpha=0.4
    )

    plt.xlim(
        -0.6,
        len(labels) - 0.4
    )

    plt.tight_layout()

    plt.savefig(
        "utility1.png",
        dpi=300,
        bbox_inches='tight'
    )

    plt.show()

if __name__ == "__main__":

    config, all_stats = load_data(
        'conf.yaml',
        'all_stats.json'
    )

    labels, mean, min_vals, max_vals, runs = get_metrics(
        all_stats
    )

    p = config['penalty_p']
    p_dir = config['penalty_p_dir']
    weights = config['directional_weights']

 

    averagePerformance(
        labels,
        mean,
        min_vals,
        max_vals
    )

    relativeToIdealBaseline(
        labels,
        mean
    )

    meanNormalizedScore(
        labels,
        mean
    )

    utility1(
            labels,
            runs,
            p
    )

   # utilityBased(
   #     labels,
  #      mean,
  #      p
  #  )

   # directionalUtility(
   #     labels,
   #     mean,
   #     p_dir,
   #     weights
   # )

   # compareBiasMeasures(
    #    labels,
    #    mean,
    #    p
   # )
