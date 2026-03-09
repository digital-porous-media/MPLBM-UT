import subprocess
import os
import sys
import mplbm_utils as mplbm
import skimage.transform as skit
import numpy as np
import matplotlib.pyplot as plt
import mplbm_utils as mplbm

def download_geometry(filename, url):

    download_command = f'wget {url} -O {filename}'
    try:
        subprocess.run(download_command.split(' '))
    except FileNotFoundError:
        raise InterruptedError(f'wget was not found. Please make sure it is installed on your system.')
    return

def create_micromodel(geom, nx, ny, nz, slice_index, x_offset, y_offset):

    # Get slice of interest
    slice = geom[slice_index, y_offset:ny+y_offset, x_offset:nx+x_offset]

    num_slices = nz
    micromodel = np.repeat(slice[np.newaxis, :, :], num_slices, axis=0)

    print(f"Micromodel size = {micromodel.shape}")

    # Check micromodel
    #plt.figure()
    #plt.imshow(micromodel[0,:,:])
    #plt.gca().invert_yaxis()
    #plt.show()

    return micromodel

def run_1_phase_sim(inputs):

    if inputs['simulation type'] == '2-phase':
        raise KeyError('Simulation type set to 2-phase...please change to 1-phase.')
    sim_directory = inputs['input output']['simulation directory']

    # 2) Create Palabos geometry
    print('Creating efficient geometry for Palabos...')
    mplbm.create_geom_for_palabos(inputs)

    # 3) Create simulation input file
    print('Creating input file...')
    mplbm.create_palabos_input_file(inputs)

    # 4) Run 1-phase simulation
    print('Running 1-phase simulation...')
    num_procs = inputs['simulation']['num procs']
    input_dir = inputs['input output']['input folder']
    simulation_command = f"mpirun -np {num_procs} ../../../src/1-phase_LBM/permeability {input_dir}1_phase_sim_input.xml"
    file = open(f'{sim_directory}/{input_dir}run_single_phase_sim.sh', 'w')
    file.write(f'{simulation_command}')
    file.close()
    simulation_command_subproc = f'bash {sim_directory}/{input_dir}run_single_phase_sim.sh'
    subprocess.run(simulation_command_subproc.split(' '))

    return

input_folder = '../input'
micromodel_name = 'rg_theta30_phi30_micromodel.raw'
data_type = 'uint8'
drp_url = 'https://web.corral.tacc.utexas.edu/digitalporousmedia/DRP-65/Solid%20comprised%20of%20irregular%20grains/theta%20=%2030,%20irregular%20grains/RG_theta30por3000.raw'
file_name = f'{input_folder}/rg_theta30_phi30.raw'
download_geometry(file_name, drp_url)

print("Rescaling geometry...")
geom = np.fromfile(file_name, dtype=data_type).reshape([501, 501, 501])
scaled_geom = mplbm.scale_geometry(geom, 0.599, data_type)
print(f"New geometry size = {scaled_geom.shape}")

# Create micromodel
print("Creating micromodel...")
micromodel = create_micromodel(scaled_geom, nx=200, ny=150, nz=5, slice_index=234, x_offset=0, y_offset=130)
geom_file = f"{input_folder}/{micromodel_name}"
micromodel.flatten().tofile(geom_file)  # Note, use flatten() before writing! Otherwise, data not saved in correct order

input_file = 'input.yml'
inputs = mplbm.parse_input_file(input_file)  # Parse inputs
inputs['simulation']['fluid init'] = None 
inputs['input output']['simulation directory'] = os.getcwd()  # Store current working directory
run_1_phase_sim(inputs)  # Run 1 phase sim

