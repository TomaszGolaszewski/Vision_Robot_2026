import random
import matplotlib.pyplot as plt

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

def safe_diff(a, b):
    if a is None or b is None:
        return None
    if len(a) != len(b):
        return None
    return [x - y for x, y in zip(a, b)]

def safe_plot(ax, t, values, label, color, linewidth=1):
    """Plots a line only if data is valid."""
    if values is None:
        return
    if len(values) != len(t):
        return
    if len(values) == 0:
        return

    ax.plot(t, values, label=label, color=color, linewidth=linewidth)

def plot_data(t, robot, target):
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
    # dx = safe_diff(rx, tx)
    # dy = safe_diff(ry, ty)
    # dz = safe_diff(rz, tz)
    dx = [r - c for r, c in zip(rx, tx)]
    dy = [r - c for r, c in zip(ry, ty)]
    dz = [r - c for r, c in zip(rz, tz)]

    fig, axs = plt.subplots(6, 1, figsize=(10, 12), sharex=True)

    # set grey background for all subplots
    for ax in axs:
        ax.set_facecolor("grey")
        ax.tick_params(colors="white")
        ax.yaxis.label.set_color("white")
        ax.xaxis.label.set_color("white")
        
        # make the frame (spines) white
        for spine in ax.spines.values():
            spine.set_color("white")

    # position plots
    # safe_plot(axs[0], t...
    axs[0].plot(t, rx, label="robot x", color="lime", linewidth=1)
    axs[0].plot(t, tx, label="target x", color="orange", linewidth=1)
    axs[0].set_ylabel("X")
    axs[0].legend(facecolor="dimgrey", labelcolor="white")

    axs[1].plot(t, ry, label="robot y", color="lime", linewidth=1)
    axs[1].plot(t, ty, label="target y", color="orange", linewidth=1)
    axs[1].set_ylabel("Y")
    axs[1].legend(facecolor="dimgrey", labelcolor="white")

    axs[2].plot(t, rz, label="robot z", color="lime", linewidth=1)
    axs[2].plot(t, tz, label="target z", color="orange", linewidth=1)
    axs[2].set_ylabel("Z")
    axs[2].legend(facecolor="dimgrey", labelcolor="white")

    # differences plots
    axs[3].plot(t, dx, label="dx", color="cyan", linewidth=1)
    axs[3].set_ylabel("dx")
    axs[3].legend(facecolor="dimgrey", labelcolor="white")
    axs[3].axhline(0, color="white", linewidth=1) # horizontal line

    axs[4].plot(t, dy, label="dy", color="cyan", linewidth=1)
    axs[4].set_ylabel("dy")
    axs[4].legend(facecolor="dimgrey", labelcolor="white")
    axs[4].axhline(0, color="white", linewidth=1) # horizontal line

    axs[5].plot(t, dz, label="dz", color="cyan", linewidth=1)
    axs[5].set_ylabel("dz")
    axs[5].legend(facecolor="dimgrey", labelcolor="white")
    axs[5].axhline(0, color="white", linewidth=1) # horizontal line

    axs[5].set_xlabel("time [s]")

    fig.patch.set_facecolor("dimgrey")
    plt.tight_layout()
    plt.show()
    

if __name__ == "__main__":
    t, robot, target = generate_demo_data()
    plot_data(t, robot, target)
