#!/usr/bin/env python3
import numpy as np
import matplotlib.pyplot as plt


def _load_data(fname):
    """Loads data from file (shorts / 16-bit values)"""
    data = np.fromfile(fname, dtype="<i2")
    return data


def load_all_data(n_files, path="acq1001_694/000001/"):
    """Loads all data files from 0 - n_files at path"""
    all_data = []
    for f in range(n_files):
        fname = f"{f:04d}"
        print(path + fname)
        all_data.append(_load_data(path + fname))
    return np.array(all_data, dtype="<i2").ravel()


def plot_channel(data, ch):
    """Plots a channel from a 32-channel dataset"""
    plt.plot(data[ch::32])


def plot_all_axes(data):
    """Plots first three channels of 32 channel dataset"""
    fig = plt.figure(figsize=(10, 8))
    plt.plot(data[0::32])
    plt.plot(data[1::32])
    plt.plot(data[2::32])

    plt.savefig("three_axes.png")
    plt.close()


def plot_3d_axes(
    data,
    end=32 * 180244,
    s=10,
    alpha=0.5,
    figname="3d_scatter.png",
    start=0,
    elev=30,
    azim=45,
):
    """Plots first three channels of 32 channel dataset in 3D.
    Saves to disk."""
    fig = plt.figure(figsize=(20, 16))
    ax = fig.add_subplot(111, projection="3d")
    timesteps = np.arange(end // 32)
    ax.scatter(
        data[0:end:32],
        data[1:end:32],
        data[2:end:32],
        c=timesteps,
        cmap="viridis",
        s=s,
        alpha=alpha,
    )
    # formatting axes
    fixed_min = 7100
    fixed_max = 7700
    step_size = 200
    tick_locations = np.arange(fixed_min, fixed_max + 1, step_size)

    ax.set_xlim(fixed_min, fixed_max)
    ax.set_ylim(fixed_min, fixed_max)
    ax.set_zlim(fixed_min, fixed_max)

    ax.set_xticks(tick_locations)
    ax.set_yticks(tick_locations)
    ax.set_zticks(tick_locations)

    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.view_init(elev=elev, azim=azim)
    plt.savefig(figname)
    plt.close()


def plot_3d_axes_animation(
    data,
    end=32 * 180244,
    s=10,
    alpha=0.5,
    figname="3d_scatter",
    nframes=30,
    chosen_elev=30,
    start_azim=45,
    rotate=True,
):
    """Creates a series of 3D plots which can be strung together in an animation.
    Saves them to disk."""
    step_size = 1875  # 15000 / 8
    azim_step_size = 360 // nframes
    next_step = 0
    next_azim = start_azim
    chosen_elev = 30
    for frame in range(nframes):
        plot_3d_axes(
            data,
            end=32 * step_size * frame,
            s=s,
            alpha=alpha,
            figname=figname + f"_frame_{frame}.png",
            start=next_step,
            elev=chosen_elev,
            azim=next_azim,
        )
        next_step += step_size
        if rotate:
            next_azim += azim_step_size


if __name__ == "__main__":
    all_data = load_all_data(11, path="acq1001_694/000001/")
    plot_3d_axes_animation(all_data)
