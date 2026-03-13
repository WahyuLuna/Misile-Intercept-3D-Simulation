import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# Data simulasi (contoh)
x = [0, 500, 1000, 1500]
y = [0, 200, 400, 600]
z = [0, 300, 450, 400]

ax.plot(x, y, z, label='Lintasan Misil')
ax.scatter(1500, 600, 400, color='blue', label='Target') # Titik Target
ax.set_xlabel('X (meter)')
ax.set_ylabel('Y (meter)')
ax.set_zlabel('Z (meter)')
plt.legend()
plt.show()