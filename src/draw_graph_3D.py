import matplotlib.pyplot as plt
# from mpl_toolkits.mplot3d import Axes3D
import numpy as np

from draw_graph_2D import generate_demo_data

def plot_3d_trajectories(trajectories):
    """
    Plot multiple 3D trajectories.

    Parameters:
        trajectories: list of tuples
            [
                (positions, color, label),
                (positions2, color2, label2),
                ...
            ]
            where positions = [[x, y, z], ...]
    """

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    for positions, color, label in trajectories:
        positions = np.array(positions)
        x = positions[:, 0]
        y = positions[:, 1]
        z = positions[:, 2]

        # Draw trajectory
        ax.plot(x, y, z, label=label, color=color)

        # Mark starting and ending point
        ax.scatter(x[0], y[0], z[0], color=color, s=80, marker="o", label="Start")
        ax.scatter(x[-1], y[-1], z[-1], color=color, s=80, marker="X", label="End")

    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_zlabel("z")
    ax.set_title("3D Motion Plot")
    ax.legend()

    plt.show()

if __name__ == "__main__":
    t, robot, target = generate_demo_data()
    plot_3d_trajectories([
        (robot, "blue", "Robot trajectory"),
        (target, "orange", "Target trajectory"),
    ])