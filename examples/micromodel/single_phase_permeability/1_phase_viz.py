import matplotlib.pyplot as plt
import numpy as np
import pyvista as pv
import os
import glob
import mplbm_utils as mplbm


def get_velocity_files(inputs):

    tmp_folder = inputs["input output"]["output folder"]

    # Get all the velocity files
    vel_files_regex = rf"{tmp_folder}vtk_vel*.vti"
    vel_files = glob.glob(vel_files_regex)

    # Sort for correct order
    vel_files_list = sorted(vel_files)

    return vel_files_list


def get_slice_of_medium(inputs, slice):

    output_folder = inputs["input output"]["output folder"]
    nx = inputs["domain"]["domain size"]["nx"]
    ny = inputs["domain"]["domain size"]["ny"]
    nz = inputs["domain"]["domain size"]["nz"]
    n_slices = inputs["domain"]["inlet and outlet layers"]

    medium = pv.read(f"{output_folder}PorousMedium000001.vti")
    grains = medium.get_array("tag").reshape([nz, ny, nx + n_slices * 2])
    grains = grains[slice, :, n_slices : nx + n_slices]

    return grains


def get_slice_of_velocity(inputs, vel_file, slice):

    nx = inputs["domain"]["domain size"]["nx"]
    ny = inputs["domain"]["domain size"]["ny"]
    nz = inputs["domain"]["domain size"]["nz"]
    n_slices = inputs["domain"]["inlet and outlet layers"]

    vel_mesh = pv.read(vel_file)
    vel_data = vel_mesh.get_array("velocityNorm").reshape([nz, ny, nx + n_slices * 2])
    vel_data = vel_data[slice, :, n_slices : nx + n_slices]

    return vel_data


def plot_velocity(inputs, vel, medium):

    nx = inputs["domain"]["domain size"]["nx"]
    ny = inputs["domain"]["domain size"]["ny"]

    x = np.arange(0, nx, 1)
    y = np.arange(0, ny, 1)
    X, Y = np.meshgrid(x, y)

    vel_masked = np.where(medium > 0.5, np.nan, vel)
    plt.contourf(X, Y, medium, levels=[0.5, 2], alpha=1, colors="gray")
    cf = plt.contourf(X, Y, vel_masked, levels=20, cmap="turbo", alpha=0.9)
    plt.colorbar(cf, label="Velocity [LBM Units]")

    plt.gca().set_aspect("equal", adjustable="box")


if __name__ == "__main__":
    # Get inputs
    print(os.getcwd())
    input_file = "input.yml"

    inputs = mplbm.parse_input_file(input_file)  # Parse inputs
    inputs["input output"][
        "simulation directory"
    ] = os.getcwd()  # Store current working directory

    # Get velocity files
    vel_files_list = get_velocity_files(inputs)

    index = -1  # Choose last simulation output

    # Slice index (middle z-slice)
    nz = inputs["domain"]["domain size"]["nz"]
    slice_idx = nz // 2

    # Get slices
    medium = get_slice_of_medium(inputs, slice_idx)
    vel = get_slice_of_velocity(inputs, vel_file=vel_files_list[index], slice=slice_idx)

    # Plot
    plt.figure()
    plot_velocity(inputs, vel, medium)
    plt.axis("off")
    plt.savefig("velocity_viz.png", dpi=300, bbox_inches="tight")
    plt.show()
