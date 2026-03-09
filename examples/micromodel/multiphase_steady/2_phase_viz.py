import matplotlib.pyplot as plt
import numpy as np
import pyvista as pv
import glob
import os
import mplbm_utils as mplbm
from create_gif_and_mp4 import create_gif, create_mp4


def get_rho_files(inputs):

    tmp_folder = inputs["input output"]["output folder"]

    # Get all the density files
    f1_files_regex = rf"{tmp_folder}rho_f1*.vti"
    f1_files = glob.glob(f1_files_regex)

    # Sort for correct order
    rho_files_list = sorted(f1_files)

    return rho_files_list


def get_slice_of_medium(inputs, slice):

    output_folder = inputs["input output"]["output folder"]
    nx = inputs["domain"]["domain size"]["nx"]
    ny = inputs["domain"]["domain size"]["ny"]
    nz = inputs["domain"]["domain size"]["nz"]
    n_slices = inputs["domain"]["inlet and outlet layers"]

    medium = pv.read(f"{output_folder}porousMedium.vti")
    medium = medium.get_array("tag").reshape([nz, ny, nx + n_slices * 2])
    medium = medium[slice, :, n_slices : nx + n_slices]

    return medium


def get_slice_of_fluid(inputs, rho_file, slice):

    nx = inputs["domain"]["domain size"]["nx"]
    ny = inputs["domain"]["domain size"]["ny"]
    nz = inputs["domain"]["domain size"]["nz"]
    n_slices = inputs["domain"]["inlet and outlet layers"]

    f1_mesh = pv.read(rho_file)
    f1_density = f1_mesh.get_array("Density").reshape([nz, ny, nx + n_slices * 2])
    f1_density = f1_density[slice, :, n_slices : nx + n_slices]

    return f1_density


def plot_sim_contours(inputs, rho, medium):

    nx = inputs["domain"]["domain size"]["nx"]
    ny = inputs["domain"]["domain size"]["ny"]

    x = np.arange(0, nx, 1)
    y = np.arange(0, ny, 1)
    X, Y = np.meshgrid(x, y)

    plt.contourf(X, Y, rho, levels=[0, 1], alpha=1, colors="lightblue")
    plt.contourf(X, Y, rho, levels=[1, 3], alpha=1, colors="orangered")
    plt.contourf(X, Y, medium, levels=[0.5, 2], alpha=1, colors="gray")

    plt.gca().set_aspect("equal", adjustable="box")


def create_animation(inputs, rho_files_list, slice_idx, restart):

    print("Creating animation...")

    sim_dir = inputs["input output"]["simulation directory"]
    output_dir = inputs["input output"]["output folder"]
    anim_dir = f"{sim_dir}/{output_dir}animation"
    if not os.path.isdir(anim_dir):
        os.makedirs(anim_dir)

    grains = get_slice_of_medium(inputs, slice_idx)

    # Loop through all rho files
    for i in range(len(rho_files_list)):

        if not restart:
            current_image = f"{anim_dir}/image_{i}.png"
            if os.path.isfile(current_image):
                continue

        print(f"Image {i + 1} of {len(rho_files_list)}...")
        rho = get_slice_of_fluid(inputs, rho_file=rho_files_list[i], slice=slice_idx)
        plt.figure()
        plot_sim_contours(inputs, rho, grains)
        plt.axis("off")
        plt.savefig(f"{anim_dir}/image_{i}.png", dpi=300, bbox_inches="tight")
        plt.close()

    anim_dir_rel = inputs["input output"]["output folder"] + "animation/"
    save_name = inputs["domain"]["geom name"]
    create_gif(anim_dir_rel, save_name)
    create_mp4(
        anim_dir_rel, save_name, speed_factor=0.5
    )  # speed_factor = 1 means no slow down or speed up


def create_combined_animation(inputs, sim_counter, slice_idx, restart):
    """Create one animation stitching all steady-state simulation directories in order."""

    print("Creating combined animation...")

    sim_dir = inputs["input output"]["simulation directory"]
    anim_dir = f"{sim_dir}/animation/"
    if not os.path.isdir(anim_dir):
        os.makedirs(anim_dir)

    original_output_folder = inputs["input output"]["output folder"]

    # Read medium once from the first valid sim directory
    inputs["input output"]["output folder"] = f"tmp_{sim_counter[0]}/"
    grains = get_slice_of_medium(inputs, slice_idx)

    image_counter = 0
    for sim_idx in sim_counter:
        inputs["input output"]["output folder"] = f"tmp_{sim_idx}/"
        rho_files_list = get_rho_files(inputs)

        if len(rho_files_list) == 0:
            print(f"No rho files found in tmp_{sim_idx}/, skipping.")
            continue

        print(f"Processing tmp_{sim_idx}/ ({len(rho_files_list)} frames)...")

        for rho_file in rho_files_list:
            if not restart:
                current_image = f"{anim_dir}image_{image_counter}.png"
                if os.path.isfile(current_image):
                    image_counter += 1
                    continue

            rho = get_slice_of_fluid(inputs, rho_file=rho_file, slice=slice_idx)
            plt.figure()
            plot_sim_contours(inputs, rho, grains)
            plt.axis("off")
            plt.savefig(
                f"{anim_dir}image_{image_counter}.png", dpi=300, bbox_inches="tight"
            )
            plt.close()
            image_counter += 1

    inputs["input output"]["output folder"] = original_output_folder

    save_name = inputs["domain"]["geom name"]
    create_gif(anim_dir, save_name)
    create_mp4(anim_dir, save_name, speed_factor=0.5)


# Get inputs
input_file = "input.yml"
inputs = mplbm.parse_input_file(input_file)  # Parse inputs
inputs["input output"][
    "simulation directory"
] = os.getcwd()  # Store current working directory

# update output directory
which_sim = 2  # Choose which steady state sim you'd like to visualize (corresponds to tmp folder numbers)
sim_counter = np.array([1, 2, 3, 4])
inputs["input output"]["output folder"] = f"tmp_{sim_counter[which_sim]}/"

# Get density files
rho_files_list = get_rho_files(inputs)

# Slice index (middle z-slice)
nz = inputs["domain"]["domain size"]["nz"]
slice_idx = nz // 2

# For combined animation across all steady-state simulations
create_combined_animation(inputs, sim_counter, slice_idx, restart=True)


# For single frame
rho = get_slice_of_fluid(inputs, rho_file=rho_files_list[-1], slice=slice_idx)
grains = get_slice_of_medium(inputs, slice_idx)
plt.figure()
plot_sim_contours(inputs, rho, grains)
plt.axis("off")
plt.show()


# Visualize PoreSpy Drainage (visualize the initial conditions)
porespy_satn_geom = np.load(f"../input/rg_theta30_phi30_satn_image.npy")

Snw = np.load(f"../input/rg_theta30_phi30_snwp_data.npy")
remove_ind = np.where(Snw <= 0.01)[0]
Snw = np.delete(
    Snw, remove_ind
)  # skip grains, uninvaded marker, and Snw values less than 1%
satn_threshold = (
    0.01  # Remove values closer than 1% together to remove redundant points
)
Snw = np.delete(Snw, np.argwhere(np.ediff1d(Snw) <= satn_threshold) + 1)

mplbm_geom = mplbm.convert_porespy_drainage_to_mplbm(porespy_satn_geom, Snw[which_sim])

# Take middle z-slice
geom_slice = mplbm_geom[mplbm_geom.shape[0] // 2, :, :]
nx_geom = mplbm_geom.shape[2]
ny_geom = mplbm_geom.shape[1]

x = np.arange(0, nx_geom, 1)
y = np.arange(0, ny_geom, 1)
X, Y = np.meshgrid(x, y)

plt.figure()
plt.contourf(X, Y, geom_slice, levels=[0.5, 1.5], alpha=1, colors="gray")  # grains
plt.contourf(X, Y, geom_slice, levels=[1.5, 3], alpha=1, colors="orangered")  # NW fluid
plt.gca().set_aspect("equal", adjustable="box")
plt.axis("off")
plt.title(
    f"PoreSpy Drainage {which_sim+1}, Snw = {np.round(Snw[which_sim], decimals=3)}"
)
sim_dir = inputs["input output"]["simulation directory"]
output_dir = inputs["input output"]["output folder"]
anim_dir = f"{sim_dir}/{output_dir}animation"
plt.savefig(f"{anim_dir}/porespy_init_{which_sim+1}.png", dpi=300, bbox_inches="tight")
plt.show()
