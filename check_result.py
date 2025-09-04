import h5py
import numpy as np
import matplotlib.pyplot as plt
# Load the .jld file using h5py
jld_file_path = r"C:\Users\yoavy\Downloads\tomo-guides-main\tomo-guides-main\data\tomogram_guide_b.jld"
with h5py.File(jld_file_path, 'r') as jld_file:
 # Extract data from keys
 if 'I' in jld_file:
  I_data = jld_file['I'][()]
  print(f"Intensity Data (I): {I_data}")
  print(I_data.shape) # Shape of the data for reference
 if 'dx' in jld_file:
  dx_value = jld_file['dx'][()]
  print(f"Spatial Resolution (dx): {dx_value}")
 if 'θ_l' in jld_file:
  theta_values = jld_file['θ_l'][()]
  print(f"Illumination Angles (θ_l): {theta_values}")
# Plot the intensity data to visualize it
plt.figure(figsize=(10, 6))
plt.imshow(I_data, cmap='gray', aspect='auto')
plt.title('Intensity Data (I)')
plt.xlabel('Lateral Position')
plt.ylabel('Depth')
plt.colorbar(label='Intensity')
plt.show()