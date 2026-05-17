# plot.py

import os
import json
from collections import Counter, OrderedDict
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import MaxNLocator, MultipleLocator
import numpy as np
import matplotlib.colors as mcolors


# ==============================
# Helper Functions
# ==============================

def transform_analysis_to_stats(analysis_data):
    """Transform analysis metrics to stats format expected by generate_plots.
    
    Args:
        analysis_data (dict): Metrics from calculate_analysis_metrics in app.py
        
    Returns:
        dict: Stats dictionary with distribution Counters for plotting
    """
    stats = {
        'turn_distribution': Counter(),
        'steps_per_turn_distribution': Counter(),
        'tool_calls_per_turn_distribution': Counter(),
        'steps_per_conversation_distribution': Counter(),
        'user_interactions_per_turn_distribution': Counter(),
        'mcp_server_distribution': analysis_data.get('mcp_server_distribution', Counter()),
    }
    
    # Convert turns_per_conversation list to distribution Counter
    for item in analysis_data.get('turns_per_conversation', []):
        count = item.get('count', 0)
        if count > 0:
            stats['turn_distribution'][count] += 1
    
    # Convert steps_per_turn list to distribution Counter (THIS IS DIFFERENT FROM tool_calls_per_turn!)
    for item in analysis_data.get('steps_per_turn', []):
        count = item.get('count', 0)
        if count > 0:
            stats['steps_per_turn_distribution'][count] += 1
    
    # Convert tool_calls_per_turn list to distribution Counter
    for item in analysis_data.get('tool_calls_per_turn', []):
        count = item.get('count', 0)
        if count > 0:
            stats['tool_calls_per_turn_distribution'][count] += 1
    
    # Convert steps_per_conversation list to distribution Counter
    for item in analysis_data.get('steps_per_conversation', []):
        count = item.get('count', 0)
        if count > 0:
            stats['steps_per_conversation_distribution'][count] += 1
    
    # Convert user_interactions_per_turn list to distribution Counter
    for item in analysis_data.get('user_interactions_per_turn', []):
        count = item.get('count', 0)
        if count > 0:
            stats['user_interactions_per_turn_distribution'][count] += 1
    
    return stats


def generate_analysis_plots(analysis_data, plot_dir):
    """Generate all plots from analysis metrics.
    
    This is the main entry point for app.py - simply pass the analysis_data
    from calculate_analysis_metrics and this function handles the rest.
    
    Args:
        analysis_data (dict): Metrics dictionary from calculate_analysis_metrics
        plot_dir (str): Directory to save plots
    """
    # Transform analysis metrics to stats format
    stats = transform_analysis_to_stats(analysis_data)
    
    # Generate all plots
    generate_plots(stats, plot_dir)


# ==============================
# Domain to MCP Mapping (as provided)
# ==============================
DOMAIN_TO_MCP = {
    "Commerce": [
        "PriceComparison",
        "Retail",
        "CarPrice",
        "AmazonProduct",
        "AttomRealEstate",
        "FakeStoreServer",
        "BestBuyServer",
        "EbayServer",
        "EtsyServer",
        "RentCast",
        "ShopifyEcommerce",
        "ZillowRealEstate"
    ],
    "Finance": [
        "CryptoPrice",
        "FinancialDatasets",
        "KospiKosdaqStock",
        "TradingBot",
        "YahooFinance",
        "PayPalPaymentProcessor",
        "StripePaymentServer"
    ],
    "Travel": [
        "AirDNA",
        "Airline",
        "ChinaRailway",
        "Didi",
        "HKBus",
        "HotelBooking",
        "TravelBooking",
        "UUPaoTui"
    ],
    "Office": [
        "Calendar",
        "Canvas",
        "ExcelServer",
        "GoogleSheets",
        "GoogleTasks",
        "Notion",
        "TickTick",
        "AdobePDFServices",
        "AmazonSES",
        "GoogleDrive",
        "MailgunCommunication",
        "OneDrive",
        "ResendEmailService",
        "ZoomMeetingServer",
        "PostmarkEmailService",
        "AirtableMcpServer",
        "SlackServer",
        "TicketManagementSystem",
        "LinkedInJobs",
        "Dice",
    ],
    "Lifestyle": [
        "GameTrending",
        "LeagueOfLegends",
        "MovieRecommender",
        "Valorant",
        "WuWa",
        "TFTServer",
        "HowToCook",
        "MetMuseum",
        "FruityviceServer",
        "CampusCard",
        "FatSecretPlatform",
        "MeditationServer",
        "Message",
        "Posting",
        "SanvelloMentalHealthServer",
        "NationalParks",
        "WhatsApp",
        "VehicleControl"
    ],
    "Academia": [
        "ClinicalTrialsGov",
        "DrugBank",
        "GitServer",
        "GitHubServer",
        "GithubTrending",
        "HackerNews",
        "OpenLibrary",
        "SimpleArxiv",
        "PubMedServer",
        "WikipediaServer"
    ],
    "Utilities": [
        "Maps",
        "Weather",
        "Kuaidi100",
        "Telecom",
        "Filesystem",
        "GorillaFileSystem",
        "HugeiconsServer",
        "MemoryKnowledgeGraph",
        "MongoDBServer",
        "Whois",
    ]
}

# ==============================
# Sunburst Plot Helper Functions
# ==============================
def lighten(color: str, amount: float):
    r, g, b = mcolors.to_rgb(color)
    r = r + (1 - r) * amount
    g = g + (1 - g) * amount
    b = b + (1 - b) * amount
    return (r, g, b)

def build_parents(raw_topics: OrderedDict, aggregate_duplicates: bool = True):
    parents = []
    for topic, subs in raw_topics.items():
        if not aggregate_duplicates:
            parents.append((topic, [(s, 1) for s in subs]))
            continue
        counter = OrderedDict()
        for s in subs:
            counter[s] = counter.get(s, 0) + 1
        parents.append((topic, [(s, c) for s, c in counter.items()]))
    return parents

def plot_sunburst(
    raw_topics: OrderedDict,
    base_colors: dict,
    save_path: str,
    font_family=None,
    show: bool = False,
):
    if font_family is None:
        font_family = ["Calibri", "Aptos", "DejaVu Sans"]
    
    plt.rcParams.update({"font.family": font_family})

    PARENTS = build_parents(raw_topics, aggregate_duplicates=True)
    total_count = sum(sum(v for _, v in children) for _, children in PARENTS)

    # Inner ring
    parent_names = [p for p, _ in PARENTS]
    parent_sizes = [sum(v for _, v in children) for _, children in PARENTS]
    parent_colors = [base_colors.get(p, "#888888") for p in parent_names]

    # Outer ring
    child_sizes, child_colors = [], []
    for parent, children in PARENTS:
        base = base_colors.get(parent, "#888888")
        k = len(children)
        amounts = np.linspace(0.35, 0.65, max(k, 1))
        for (_, val), amt in zip(children, amounts):
            child_sizes.append(val)
            child_colors.append(lighten(base, float(amt)))

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 12), subplot_kw=dict(aspect="equal"))
    startangle = 90

    # Outer ring
    wedges_outer, _ = ax.pie(
        child_sizes,
        radius=1.3,
        startangle=startangle,
        counterclock=False,
        colors=child_colors,
        wedgeprops=dict(width=0.4, edgecolor="white", linewidth=1.5),
    )

    # Inner ring
    wedges_inner, _ = ax.pie(
        parent_sizes,
        radius=0.85,
        startangle=startangle,
        counterclock=False,
        colors=parent_colors,
        wedgeprops=dict(width=0.5, edgecolor="white", linewidth=3.0),
    )

    # Center hole
    ax.add_artist(plt.Circle((0, 0), 0.35, color="white", zorder=10))

    # Inner labels (domains) – radial orientation, baseline follows spoke
    for w, name, total in zip(wedges_inner, parent_names, parent_sizes):
        ang = 0.5 * (w.theta1 + w.theta2)
        theta = np.deg2rad(ang)
        r = 0.6
        x, y = r * np.cos(theta), r * np.sin(theta)
        pct = 100.0 * total / total_count if total_count > 0 else 0

        # Normalize rotation to (-90, 90] so text is always upright
        rotation = ang % 360
        while rotation > 90:
            rotation -= 180

        ax.text(
            x, y, f"{name}\n({pct:.1f}%)",
            ha="center", va="center",
            color="white",
            fontsize=12,
            fontweight="bold",
            rotation=rotation,
            rotation_mode="anchor",
        )

    # Outer labels (MCP servers) – inside ring, radial orientation
    MIN_RATIO = 0.05
    current_idx = 0

    for parent, children in PARENTS:
        for child_name, child_count in children:
            w = wedges_outer[current_idx]
            ratio = child_count / total_count if total_count > 0 else 0

            if ratio >= MIN_RATIO and len(child_name) <= 14:
                ang = 0.5 * (w.theta1 + w.theta2)
                theta = np.deg2rad(ang)

                r = 1.1
                x, y = r * np.cos(theta), r * np.sin(theta)
                pct = 100.0 * child_count / total_count if total_count > 0 else 0
                label_text = f"{child_name}({pct:.1f}%)"

                # Normalize rotation to (-90, 90] so text is always upright
                rotation = ang % 360
                while rotation > 90:
                    rotation -= 180

                ax.text(
                    x, y, label_text,
                    ha="center", va="center", fontsize=8, color="white", fontweight="normal",
                    rotation=rotation,
                    rotation_mode="anchor",
                )
            current_idx += 1

    ax.set_xlim(-1.8, 1.8)
    ax.set_ylim(-1.8, 1.8)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(save_path, dpi=600, bbox_inches="tight")
    if show:
        plt.show()
    plt.close(fig)


def plot_sunburst_with_counts(
    raw_topics: OrderedDict,
    base_colors: dict,
    save_path: str,
    font_family=None,
    show: bool = False,
):
    """Plot a sunburst chart where outer segments are sized by pre-computed counts.

    Args:
        raw_topics: OrderedDict mapping domain -> list of (server_name, count) tuples.
        base_colors: dict mapping domain -> color string.
        save_path: file path to save the figure.
        font_family: list of font family names.
        show: whether to display the plot interactively.
    """
    if font_family is None:
        font_family = ["Calibri", "Aptos", "DejaVu Sans"]

    plt.rcParams.update({"font.family": font_family})

    PARENTS = [(topic, subs) for topic, subs in raw_topics.items()]
    total_count = sum(sum(v for _, v in children) for _, children in PARENTS)

    # Inner ring
    parent_names = [p for p, _ in PARENTS]
    parent_sizes = [sum(v for _, v in children) for _, children in PARENTS]
    parent_colors = [base_colors.get(p, "#888888") for p in parent_names]

    # Outer ring
    child_sizes, child_colors = [], []
    for parent, children in PARENTS:
        base = base_colors.get(parent, "#888888")
        k = len(children)
        amounts = np.linspace(0.35, 0.65, max(k, 1))
        for (_, val), amt in zip(children, amounts):
            child_sizes.append(val)
            child_colors.append(lighten(base, float(amt)))

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 12), subplot_kw=dict(aspect="equal"))
    startangle = 90

    # Outer ring
    wedges_outer, _ = ax.pie(
        child_sizes,
        radius=1.3,
        startangle=startangle,
        counterclock=False,
        colors=child_colors,
        wedgeprops=dict(width=0.4, edgecolor="white", linewidth=1.5),
    )

    # Inner ring
    wedges_inner, _ = ax.pie(
        parent_sizes,
        radius=0.85,
        startangle=startangle,
        counterclock=False,
        colors=parent_colors,
        wedgeprops=dict(width=0.5, edgecolor="white", linewidth=3.0),
    )

    # Inner labels (domains) – radial orientation, baseline follows spoke
    for w, name, total in zip(wedges_inner, parent_names, parent_sizes):
        ang = 0.5 * (w.theta1 + w.theta2)
        theta = np.deg2rad(ang)
        r = 0.6
        x, y = r * np.cos(theta), r * np.sin(theta)
        pct = 100.0 * total / total_count if total_count > 0 else 0

        # Normalize rotation to (-90, 90] so text is always upright
        rotation = ang % 360
        while rotation > 90:
            rotation -= 180

        ax.text(
            x, y, f"{name}\n({pct:.1f}%)",
            ha="center", va="center",
            color="white",
            fontsize=11,
            fontweight="bold",
            rotation=rotation,
            rotation_mode="anchor",
        )

    # Outer labels (MCP servers) – inside ring, radial orientation
    MIN_RATIO = 0.006
    current_idx = 0

    for parent, children in PARENTS:
        for child_name, child_count in children:
            w = wedges_outer[current_idx]
            ratio = child_count / total_count if total_count > 0 else 0

            if ratio >= MIN_RATIO and len(child_name) <= 14:
                ang = 0.5 * (w.theta1 + w.theta2)
                theta = np.deg2rad(ang)

                r = 1.1
                x, y = r * np.cos(theta), r * np.sin(theta)
                label_text = f"{child_name}({child_count})"

                # Normalize rotation to (-90, 90] so text is always upright
                rotation = ang % 360
                while rotation > 90:
                    rotation -= 180

                ax.text(
                    x, y, label_text,
                    ha="center", va="center", fontsize=9, color="black", fontweight="normal",
                    rotation=rotation,
                    rotation_mode="anchor",
                )
            current_idx += 1

    ax.set_xlim(-1.8, 1.8)
    ax.set_ylim(-1.8, 1.8)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(save_path, dpi=600, bbox_inches="tight")
    if show:
        plt.show()
    plt.close(fig)

def generate_plots(stats, plot_dir, plot_types=None):
    """
    Generate all plots from conversation statistics.

    Args:
        stats (dict): Statistics dictionary with keys like 'turn_distribution', etc.
        plot_dir (str): Directory to save plots.
        plot_types (list, optional): List of plot types to generate.
            Options: 'turns_steps', 'tool_calls_user_interactions', 'accuracy', 'sunburst', 'sunburst_tools'.
            If None, generates all original plots.
    """
    os.makedirs(plot_dir, exist_ok=True)
    sns.set_style("whitegrid")
    plt.rcParams.update({'font.size': 11})
    
    if plot_types is None:
        plot_types = ['turns_steps', 'tool_calls_user_interactions', 'accuracy', 'sunburst']

    # Helper function to calculate mean and median from Counter
    def calculate_stats_from_counter(counter):
        """Calculate mean and median from a Counter {value: frequency}."""
        if not counter:
            return 0.0, 0.0
        
        # Create list of values repeated by frequency
        values = []
        for val, freq in counter.items():
            values.extend([val] * freq)
        
        if not values:
            return 0.0, 0.0
        
        mean = np.mean(values)
        median = np.median(values)
        return mean, median

    # Bar plots
    color_turns = "#A0C4E8"
    color_steps_turn = "#B8E0C5"
    color_tool_calls = "#F5B041"
    color_user_interactions = "#AF7AC5"
    color_mean = "#E11313"
    color_median = "#1345EC"

    if 'turns_steps' in plot_types:
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        turns = sorted(stats['turn_distribution'].keys())
        counts1 = [stats['turn_distribution'][t] for t in turns]
        
        mean_turns, median_turns = calculate_stats_from_counter(stats['turn_distribution'])
        
        axes[0].bar(turns, counts1, color=color_turns, edgecolor="white", linewidth=0.8)
        axes[0].axvline(x=mean_turns, color=color_mean, linestyle='--', linewidth=2, alpha=0.8, label=f'Mean: {mean_turns:.2f}')
        axes[0].axvline(x=median_turns, color=color_median, linestyle='--', linewidth=2, alpha=0.8, label=f'Median: {median_turns:.1f}')
        
        axes[0].set_title('(a) Turns per Conversation', fontsize=18, pad=12)
        axes[0].set_xlabel('Number of Turns', fontsize=14)
        axes[0].set_ylabel('Number of Conversations', fontsize=14)
        axes[0].tick_params(axis='both', which='major', labelsize=12)
        if len(turns) > 15:
            axes[0].xaxis.set_major_locator(MultipleLocator(2))
        else:
            axes[0].xaxis.set_major_locator(MultipleLocator(1))
        if turns:
            axes[0].set_xlim(-0.5, max(turns) + 0.5)
        axes[0].legend(loc='upper right', fontsize=10)
        
        for i, v in enumerate(counts1):
            if v > 0 and (len(turns) <= 15 or turns[i] % 2 == 0):
                axes[0].text(turns[i], v + max(counts1)*0.01, str(v), ha='center', va='bottom', fontsize=11)

        steps_turn = sorted(stats['steps_per_turn_distribution'].keys())
        counts2 = [stats['steps_per_turn_distribution'][s] for s in steps_turn]
        
        mean_steps_turn, median_steps_turn = calculate_stats_from_counter(stats['steps_per_turn_distribution'])
        
        axes[1].bar(steps_turn, counts2, color=color_steps_turn, edgecolor="white", linewidth=0.8)
        axes[1].axvline(x=mean_steps_turn, color=color_mean, linestyle='--', linewidth=2, alpha=0.8, label=f'Mean: {mean_steps_turn:.2f}')
        axes[1].axvline(x=median_steps_turn, color=color_median, linestyle='--', linewidth=2, alpha=0.8, label=f'Median: {median_steps_turn:.1f}')
        
        axes[1].set_title('(b) Steps per Turn', fontsize=18, pad=12)
        axes[1].set_xlabel('Number of Steps', fontsize=14)
        axes[1].set_ylabel('Number of Turns', fontsize=14)
        axes[1].tick_params(axis='both', which='major', labelsize=12)
        if len(steps_turn) > 15:
            axes[1].xaxis.set_major_locator(MultipleLocator(2))
        else:
            axes[1].xaxis.set_major_locator(MultipleLocator(1))
        if steps_turn:
            axes[1].set_xlim(-0.5, max(steps_turn) + 0.5)
        axes[1].legend(loc='upper right', fontsize=10)
        
        for i, v in enumerate(counts2):
            if v > 0 and (len(steps_turn) <= 15 or steps_turn[i] % 2 == 0):
                axes[1].text(steps_turn[i], v + max(counts2)*0.01, str(v), ha='center', va='bottom', fontsize=11)

        plt.tight_layout()
        plt.savefig(os.path.join(plot_dir, 'data_statistic_1.svg'), dpi=600, bbox_inches='tight')
        plt.close()

    if 'tool_calls_user_interactions' in plot_types:
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        tool_calls = sorted(stats['tool_calls_per_turn_distribution'].keys())
        counts3 = [stats['tool_calls_per_turn_distribution'][s] for s in tool_calls]
        
        mean_tool_calls, median_tool_calls = calculate_stats_from_counter(stats['tool_calls_per_turn_distribution'])
        
        axes[0].bar(tool_calls, counts3, color=color_tool_calls, edgecolor="white", linewidth=0.8)
        axes[0].axvline(x=mean_tool_calls, color=color_mean, linestyle='--', linewidth=2, alpha=0.8, label=f'Mean: {mean_tool_calls:.2f}')
        axes[0].axvline(x=median_tool_calls, color=color_median, linestyle='--', linewidth=2, alpha=0.8, label=f'Median: {median_tool_calls:.1f}')
        
        axes[0].set_title('(a) Tool Calls per Turn', fontsize=18, pad=12)
        axes[0].set_xlabel('Number of Tool Calls', fontsize=14)
        axes[0].set_ylabel('Number of Turns', fontsize=14)
        axes[0].tick_params(axis='both', which='major', labelsize=12)
        if len(tool_calls) > 15:
            axes[0].xaxis.set_major_locator(MultipleLocator(2))
        else:
            axes[0].xaxis.set_major_locator(MultipleLocator(1))
        if tool_calls:
            axes[0].set_xlim(-0.5, max(tool_calls) + 0.5)
        axes[0].legend(loc='upper right', fontsize=10)
        
        for i, v in enumerate(counts3):
            if v > 0 and (len(tool_calls) <= 15 or tool_calls[i] % 2 == 0):
                axes[0].text(tool_calls[i], v + max(counts3)*0.01, str(v), ha='center', va='bottom', fontsize=11)

        user_interactions = sorted(stats['user_interactions_per_turn_distribution'].keys())
        counts4 = [stats['user_interactions_per_turn_distribution'][u] for u in user_interactions]
        
        mean_user_interactions, median_user_interactions = calculate_stats_from_counter(stats['user_interactions_per_turn_distribution'])
        
        axes[1].bar(user_interactions, counts4, color=color_user_interactions, edgecolor="white", linewidth=0.8)
        axes[1].axvline(x=mean_user_interactions, color=color_mean, linestyle='--', linewidth=2, alpha=0.8, label=f'Mean: {mean_user_interactions:.2f}')
        axes[1].axvline(x=median_user_interactions, color=color_median, linestyle='--', linewidth=2, alpha=0.8, label=f'Median: {median_user_interactions:.1f}')
        
        axes[1].set_title('(b) User Interactions per Turn', fontsize=18, pad=12)
        axes[1].set_xlabel('Number of User Interactions', fontsize=14)
        axes[1].set_ylabel('Number of Turns', fontsize=14)
        axes[1].tick_params(axis='both', which='major', labelsize=12)
        if len(user_interactions) > 15:
            axes[1].xaxis.set_major_locator(MultipleLocator(2))
        else:
            axes[1].xaxis.set_major_locator(MultipleLocator(1))
        if user_interactions:
            axes[1].set_xlim(-0.5, max(user_interactions) + 0.5)
        axes[1].legend(loc='upper right', fontsize=10)
        
        for i, v in enumerate(counts4):
            if v > 0 and (len(user_interactions) <= 15 or user_interactions[i] % 2 == 0):
                axes[1].text(user_interactions[i], v + max(counts4)*0.01, str(v), ha='center', va='bottom', fontsize=11)

        plt.tight_layout()
        plt.savefig(os.path.join(plot_dir, 'data_statistic_2.svg'), dpi=600, bbox_inches='tight')
        plt.close()

    if 'accuracy' in plot_types:
        if stats.get('node_accuracy_vs_length') and len(stats['node_accuracy_vs_length']) > 0:
            node_data = stats['node_accuracy_vs_length']
            
            import pandas as pd
            df = pd.DataFrame(node_data)
            
            df = df[df['accuracy'].notna()]
            
            if not df.empty:
                fig, ax = plt.subplots(figsize=(12, 7))
                
                tool_lengths = sorted(df['tool_call_length'].unique())
                box_data = [df[df['tool_call_length'] == length]['accuracy'].values for length in tool_lengths]
                
                boxes = ax.boxplot(box_data, positions=tool_lengths, widths=0.6,
                                patch_artist=True, showfliers=False,
                                medianprops={'color': 'black', 'linewidth': 1.5},
                                boxprops={'facecolor': '#4DA6FF', 'alpha': 0.7, 'linewidth': 1.2},
                                whiskerprops={'linewidth': 1.2},
                                capprops={'linewidth': 1.2})
                
                means = [df[df['tool_call_length'] == length]['accuracy'].mean() for length in tool_lengths]
                ax.plot(tool_lengths, means, 'o-', color='#FF6B6B', linewidth=2.5, markersize=8,
                        markerfacecolor='#FF6B6B', markeredgecolor='white', markeredgewidth=1.5,
                        label=f'Mean Accuracy (n={len(df)})')
                
                for i, length in enumerate(tool_lengths):
                    n = len(df[df['tool_call_length'] == length])
                    ax.text(length, 0.05, f'n={n}', ha='center', va='bottom', 
                        fontsize=10, bbox=dict(facecolor='white', alpha=0.8, edgecolor='#4DA6FF', boxstyle='round,pad=0.3'))
                
                ax.set_xlabel('Number of Tool Calls per Turn', fontsize=14, fontweight='bold', labelpad=10)
                ax.set_ylabel('Accuracy (pass_k_accuracy)', fontsize=14, fontweight='bold', labelpad=10)
                ax.set_title('Tool Call Length vs. Accuracy Distribution', fontsize=16, fontweight='bold', pad=20)
                ax.set_ylim(-0.05, 1.05)
                ax.set_xticks(tool_lengths)
                ax.set_xticklabels([str(int(x)) for x in tool_lengths], fontsize=12)
                ax.grid(True, linestyle='--', alpha=0.7, axis='y')
                ax.legend(loc='upper right', fontsize=12)
                
                if len(tool_lengths) > 1:
                    correlation = df['tool_call_length'].corr(df['accuracy'])
                    trend = "negative" if correlation < 0 else "positive"
                    ax.annotate(f'Correlation: {correlation:.3f} ({trend})', 
                            xy=(0.05, 0.92), xycoords='axes fraction',
                            bbox=dict(boxstyle="round,pad=0.3", fc="yellow", ec="black", alpha=0.8),
                            fontsize=12, fontweight='bold')
                
                if correlation < -0.3:
                    ax.annotate('Longer tool sequences\nshow reduced accuracy', 
                            xy=(0.7, 0.8), xycoords='axes fraction',
                            arrowprops=dict(arrowstyle='->', color='red', lw=1.5),
                            bbox=dict(boxstyle="round,pad=0.3", fc="lightyellow", ec="orange", alpha=0.9),
                            fontsize=11, fontweight='bold', color='darkred')
                
                plt.tight_layout()
                plt.savefig(os.path.join(plot_dir, 'accuracy_vs_tool_call_length.svg'), dpi=600, bbox_inches='tight')
                plt.close(fig)
                
                print("\n" + "="*60)
                print("TOOL CALL LENGTH vs ACCURACY ANALYSIS")
                print("="*60)
                summary_df = df.groupby('tool_call_length')['accuracy'].agg(
                    mean='mean', 
                    median='median',
                    std='std',
                    count='count'
                ).round(4)
                print(summary_df.to_string())
                print(f"\nOverall correlation: {correlation:.4f}")
                print("="*60)
            else:
                print("[WARNING] No valid accuracy data available after filtering NaN values.")
        else:
            print("[WARNING] No node accuracy data available for visualization.")

    if 'sunburst' in plot_types:
        mcp_to_domain = {}
        for domain, mcps in DOMAIN_TO_MCP.items():
            for mcp in mcps:
                mcp_to_domain[mcp] = domain

        domain_counts = Counter()
        domain_mcp_lists = {domain: [] for domain in DOMAIN_TO_MCP}
        domain_mcp_lists["Other"] = []

        for mcp, count in stats['mcp_server_distribution'].items():
            domain = mcp_to_domain.get(mcp, "Other")
            domain_counts[domain] += count
            domain_mcp_lists[domain].extend([mcp] * count)

        sorted_domains = [d for d, _ in domain_counts.most_common() if domain_counts[d] > 0]

        sunburst_data = OrderedDict()
        for domain in sorted_domains:
            if domain_counts[domain] > 0:
                sunburst_data[domain] = domain_mcp_lists[domain]

        num_domains = len(sorted_domains)
        if num_domains > 0:
            colors = sns.color_palette("husl", num_domains).as_hex()
            domain_colors = {domain: colors[i] for i, domain in enumerate(sorted_domains)}
        else:
            domain_colors = {}

        plot_sunburst(
            raw_topics=sunburst_data,
            base_colors=domain_colors,
            save_path=os.path.join(plot_dir, 'domain_sunburst.svg'),
            font_family=plt.rcParams['font.family'],
            show=False
        )

    if 'sunburst_tools' in plot_types:
        from src.manager.mcp_client_manager import MCPManager

        mcp_tool_counts = {}
        for domain, mcps in DOMAIN_TO_MCP.items():
            for mcp in mcps:
                tools = MCPManager.filter_tools([mcp])
                assert len(tools) > 0, f"No tools found for MCP server '{mcp}' in domain '{domain}'."
                mcp_tool_counts[mcp] = len(tools)

        domain_tool_counts = Counter()
        domain_mcp_tool_map = {domain: {} for domain in DOMAIN_TO_MCP}

        for mcp, count in mcp_tool_counts.items():
            for domain, mcps in DOMAIN_TO_MCP.items():
                if mcp in mcps:
                    domain_tool_counts[domain] += count
                    domain_mcp_tool_map[domain][mcp] = count
                    break

        sorted_domains = [d for d, _ in domain_tool_counts.most_common() if domain_tool_counts[d] > 0]

        sunburst_data = OrderedDict()
        for domain in sorted_domains:
            mcp_counts = domain_mcp_tool_map[domain]
            sunburst_data[domain] = list(mcp_counts.items())

        num_domains = len(sorted_domains)
        if num_domains > 0:
            colors = sns.color_palette("husl", num_domains).as_hex()
            domain_colors = {domain: colors[i] for i, domain in enumerate(sorted_domains)}
        else:
            domain_colors = {}

        plot_sunburst_with_counts(
            raw_topics=sunburst_data,
            base_colors=domain_colors,
            save_path=os.path.join(plot_dir, 'domain_sunburst_tools.svg'),
            font_family=plt.rcParams['font.family'],
            show=False
        )