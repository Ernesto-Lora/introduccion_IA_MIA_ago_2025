import matplotlib.pyplot as plt

# Define the tree as nested tuples (node, children)
T = (1, [
        (2, [
            (4, [
                (8, []),
                (9, [])
            ]),
            (5, [
                (10, []),
                (11, [])
            ])
        ]),
        (3, [
            (6, [
                (12, []),
                (13, [])
            ]),
            (7, [
                (14, []),
                (15, [])
            ])
        ])
    ])

def draw_tree(node, x=0, y=0, dx=1, ax=None, fontsize=14):
    """
    Recursively draw a binary tree using matplotlib.
    node = (value, children)
    """
    value, children = node
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))

    # Draw current node with larger text
    ax.text(x, y, str(value), ha='center', va='center',
            fontsize=fontsize,
            bbox=dict(boxstyle="circle,pad=0.5", fc="lightblue", ec="black"))

    # Draw children
    if children:
        n = len(children)
        width = dx * (n - 1)  # span for children
        child_x = x - width/2
        for child in children:
            child_y = y - 2
            ax.plot([x, child_x], [y, child_y], 'k-')
            draw_tree(child, child_x, child_y, dx/2, ax, fontsize)
            child_x += dx

    return ax

# Draw and save
ax = draw_tree(T, dx=8, fontsize=16)  # fontsize set to 16 here
ax.set_axis_off()
plt.savefig("tree.pdf", format="pdf", bbox_inches="tight")
plt.close()

print("Tree saved as tree.pdf")

