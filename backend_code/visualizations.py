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

    for model_name, stats in all_stats.items():
        labels.append(model_name)

        averages = stats["model_averages"]

        means.append(averages["avg_yes_pct"])
        mins.append(averages["min_yes_pct"])
        maxes.append(averages["max_yes_pct"])

    return labels, np.array(means), np.array(mins), np.array(maxes)    

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
 
    plt.ylim(0, 100)
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

    plt.ylim(-1, 1)
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

if __name__ == "__main__":
    
    config, all_stats = load_data('conf.yaml', 'all_stats.json')

    labels, mean, min_vals, max_vals = get_metrics(all_stats)

    p = config['penalty_p']
    p_dir = config['penalty_p_dir']
    weights = config['directional_weights']
    
    averagePerformance(labels, mean, min_vals, max_vals)
    meanNormalizedScore(labels, mean)
    utilityBased(labels, mean, p)
    directionalUtility(labels, mean, p_dir, weights)