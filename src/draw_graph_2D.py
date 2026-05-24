import math
import random
import matplotlib.pyplot as plt

COLOR_DICT_GREY_LIME_ORANGE = {
    "background_window": "dimgrey",
    "background_plot": "grey",
    "line_1": "lime",
    "line_2": "orange",
    "line_difference": "cyan",
    "line_plot": "white",
}

COLOR_DICT_GREY_GREEN_RED = {
    "background_window": "dimgrey",
    "background_plot": "grey",
    "line_1": "green",
    "line_2": "red",
    "line_difference": "blue",
    "line_plot": "white",
}

def generate_demo_data(t_start=0, t_end=100, dt=0.1, start_pos=(100, 50, 400)):
    """Generates demo data: a list of robot and target positions over time.
    Each coordinate changes randomly at every step.
    """
    t = []
    robot = []
    target = []

    x, y, z = start_pos
    tx, ty, tz = start_pos  # target starts at the same position

    t_curr = t_start
    while t_curr <= t_end:
        t.append(t_curr)

        # robot movement
        x += random.uniform(-5, 5)
        y += random.uniform(-5, 5)
        z += random.uniform(-5, 5)

        # target movement
        tx += random.uniform(-5, 5)
        ty += random.uniform(-5, 5)
        tz += random.uniform(-5, 5)

        robot.append((x, y, z))
        target.append((tx, ty, tz))

        t_curr += dt

    return t, robot, target

def safe_plot(ax, t, values, label, color, linewidth=1):
    """Plots a line only if data is valid."""
    if values is None:
        return
    if len(values) != len(t):
        return
    if len(values) == 0:
        return

    ax.plot(t, values, label=label, color=color, linewidth=linewidth)

def plot_data(t, robot, target, color_dict=COLOR_DICT_GREY_GREEN_RED, 
                robot_label="robot", target_label="target", title="robot vs target"):
    """Plots robot and target trajectories along with coordinate differences.

    This function creates a figure consisting of six vertically stacked subplots.
    The first three subplots show the robot and target positions (x, y, z) over
    time. The next three subplots show the coordinate differences (dx, dy, dz)
    between the robot and the target.

    Args:
        t (list[float]):
            A list of time values in seconds, sampled at a constant interval.
        robot (list[tuple[float, float, float]]):
            A list of (x, y, z) coordinates representing the robot's position at each time step.
        target (list[tuple[float, float, float]]):
            A list of (x, y, z) coordinates representing the target's position at each time step.
    """
    # unpack coordinates
    rx = [p[0] for p in robot]
    ry = [p[1] for p in robot]
    rz = [p[2] for p in robot]

    tx = [p[0] for p in target]
    ty = [p[1] for p in target]
    tz = [p[2] for p in target]

    # differences
    dx = [r - c for r, c in zip(rx, tx)]
    dy = [r - c for r, c in zip(ry, ty)]
    dz = [r - c for r, c in zip(rz, tz)]

    # total error
    er = [math.sqrt(rx*rx + ry*ry + rz*rz) for rx, ry, rz in zip(dx, dy, dz)]

    fig, axs = plt.subplots(7, 1, figsize=(10, 10), sharex=True) # figsize=(w, h)

    # set grey background for all subplots
    for ax in axs:
        ax.set_facecolor(color_dict["background_plot"])
        ax.tick_params(colors="white")
        ax.yaxis.label.set_color("white")
        ax.xaxis.label.set_color("white")
        
        # make the frame (spines) white
        for spine in ax.spines.values():
            spine.set_color("white")

    # position plots
    # safe_plot(axs[0], t...
    axs[0].plot(t, rx, label=f"{robot_label} x", color=color_dict["line_1"], linewidth=1)
    axs[0].plot(t, tx, label=f"{target_label} x", color=color_dict["line_2"], linewidth=1)
    axs[0].set_ylabel("x")
    axs[0].legend(facecolor=color_dict["background_window"], labelcolor=color_dict["line_plot"])

    axs[1].plot(t, ry, label=f"{robot_label} y", color=color_dict["line_1"], linewidth=1)
    axs[1].plot(t, ty, label=f"{target_label} y", color=color_dict["line_2"], linewidth=1)
    axs[1].set_ylabel("y")
    axs[1].legend(facecolor=color_dict["background_window"], labelcolor=color_dict["line_plot"])

    axs[2].plot(t, rz, label=f"{robot_label} z", color=color_dict["line_1"], linewidth=1)
    axs[2].plot(t, tz, label=f"{target_label} z", color=color_dict["line_2"], linewidth=1)
    axs[2].set_ylabel("z")
    axs[2].legend(facecolor=color_dict["background_window"], labelcolor=color_dict["line_plot"])

    # differences plots
    axs[3].plot(t, dx, label="dx", color=color_dict["line_difference"], linewidth=1)
    axs[3].set_ylabel("dx")
    axs[3].legend(facecolor=color_dict["background_window"], labelcolor=color_dict["line_plot"])
    axs[3].axhline(0, color=color_dict["line_plot"], linewidth=1) # horizontal line

    axs[4].plot(t, dy, label="dy", color=color_dict["line_difference"], linewidth=1)
    axs[4].set_ylabel("dy")
    axs[4].legend(facecolor=color_dict["background_window"], labelcolor=color_dict["line_plot"])
    axs[4].axhline(0, color=color_dict["line_plot"], linewidth=1) # horizontal line

    axs[5].plot(t, dz, label="dz", color=color_dict["line_difference"], linewidth=1)
    axs[5].set_ylabel("dz")
    axs[5].legend(facecolor=color_dict["background_window"], labelcolor=color_dict["line_plot"])
    axs[5].axhline(0, color=color_dict["line_plot"], linewidth=1) # horizontal line

    axs[6].plot(t, er, label="error", color=color_dict["line_2"], linewidth=1)
    axs[6].set_ylabel("error")
    axs[6].legend(facecolor=color_dict["background_window"], labelcolor=color_dict["line_plot"])
    axs[6].axhline(0, color=color_dict["line_plot"], linewidth=1) # horizontal line

    axs[6].set_xlabel("time [s]")

    fig.patch.set_facecolor(color_dict["background_window"])
    fig.suptitle(title, color=color_dict["line_plot"], fontsize=16)
    plt.tight_layout()
    plt.show()
    

if __name__ == "__main__":
    t, robot, target = generate_demo_data()
    plot_data(t, robot, target, COLOR_DICT_GREY_LIME_ORANGE)
