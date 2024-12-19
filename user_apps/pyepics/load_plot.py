#!/usr/bin/env python

import numpy as np
import matplotlib.pyplot as plt

data = np.load('data.npy')
#print(data)
plt.suptitle('Delta Times')
plt.title(f'len:{len(data)} mean:{np.mean(data):.4} max:{np.max(data):.4} min:{np.min(data):.4}')
plt.plot(data)
plt.show()

