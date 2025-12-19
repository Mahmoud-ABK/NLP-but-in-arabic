import matplotlib.pyplot as plt

def boxplot_token_counts(
    data,
    columns=('page1_token_count', 'page2_token_count', 'total_tokens'),
    labels=('page1', 'page2', 'total'),
    figsize=(8, 6),
    title='Boxplot of Token Counts for Each Page',
    ylabel='Token Count'
):
    plt.figure(figsize=figsize)

    plt.boxplot(
        [data[col] for col in columns],
        labels=labels,
        patch_artist=True,
        showmeans=True
    )

    # Annotate median, mean, min, max for each box
    for i, col in enumerate(columns):
        col_data = data[col].dropna()
        median = col_data.median()
        mean = col_data.mean()
        min_val = col_data.min()
        max_val = col_data.max()

        x = i + 1
        plt.text(x, median, f'Median: {median:.0f}', ha='center', va='bottom', fontsize=9, color='blue')
        plt.text(x, mean, f'Mean: {mean:.0f}', ha='center', va='top', fontsize=9, color='red')
        plt.text(x, min_val, f'Min: {min_val:.0f}', ha='center', va='top', fontsize=8, color='green')
        plt.text(x, max_val, f'Max: {max_val:.0f}', ha='center', va='bottom', fontsize=8, color='purple')

    plt.ylabel(ylabel)
    plt.title(title)
    plt.show()
