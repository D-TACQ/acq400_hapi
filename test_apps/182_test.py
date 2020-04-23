#!/usr/bin/python

import MDSplus
import numpy as np
import matplotlib.pyplot as plt


uut = "acq2106_182"
shot = 290
first_run = 1


def create_time_base(data):
	tb = np.bitwise_and(data, [0b00000011])

	indices = np.where(np.diff(tb) != 0)[0] # Where there is ANY change in timebase
	vals = tb[indices] # The value at the point where there is a change
	#rates = {0: 50, 1: 25, 2: 200}
	#rates = {0: 50, 1: 25, 2: 800}
	rates = {0: 2, 1: 1, 2: 32}
	dt = 25.0
	
	tb_final = np.zeros(data.shape[-1])
	for num, entry in enumerate(indices):
		step = rates[vals[num]]
		prev_time = tb_final[indices[num-1]-1]
		current_time = prev_time + (indices[num] - indices[num-1]) * step

		if num == 0:
			tb_final[0:indices[num]] = np.arange(0, indices[num] * rates[vals[num]], rates[vals[num]])
		else:
			tb_final[indices[num-1]:indices[num]] = np.arange(prev_time, current_time, step)
	
	step = rates[tb[entry+1]]
	prev_time = tb_final[indices[num]-1]
	current_time = prev_time + (data.shape[-1] - indices[num]) * step
	tb_final[indices[num]:] = np.arange(prev_time, current_time, step)

	return tb_final * 1e-9

def error_check(data):
	result = np.bitwise_and(data, [0b00000011])
	if 3 in result:
		return False
	else:
		return True


while True:
	#print("hello world")
	print(shot)
	tree = MDSplus.Tree(uut, shot)
	try:
		data = np.array(tree.TRANSIENT1.INPUT_001.data())
	except Exception:
		print("No data for this node. Please check shot {}".format(shot))
		shot += 1
		continue
	
	if first_run:
		# Set the model to a shot that has been visually checked.
		model = data
		first_run = 0
		continue
	
	if not error_check(data):
		print("0b00000011 found in shot {}.".format(shot))

	tb_final = create_time_base(data)
	#for item in tb_final:
	#	print(item)
	#plt.plot(data)
	plt.plot(tb_final, data, 'r+')
	plt.plot(tb_final, np.arange(0, data.shape[-1], 1))
	
	#plt.plot(tb_final, model)
	plt.show()

	if not np.allclose(model, data, rtol=1, atol=1500):
	#if np.allclose(model, data, rtol=1, atol=1500):
		print("Please check shot {} visually.".format(shot))
		close = np.isclose(model, data, rtol=1, atol=1000)
		plt.plot(model)
		plt.plot(data)
		plt.plot(close * 1000)
		plt.grid(1)
		plt.show()
	shot += 1
