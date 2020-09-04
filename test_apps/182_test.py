#!/usr/bin/python

import MDSplus
import numpy as np
import matplotlib.pyplot as plt


uut = "acq2106_182"
shot = 290
first_run = 1


def create_time_base(data):
	# data is 1 dimensional, surely ?
	# tb is a field in MDS TREE, 1:1 mapping with raw data
	tb = np.bitwise_and(data, [0b00000011])

	# decims is a field in MDS TREE, 1:1 mapping with hardware settings. 2: is variable
	decims = { 0: 2, 1: 1, 2: 32}
	# dt is a field in MDS TREE, 1:1 mapping with MBCLOCK setting
	dt = 25.0

	# tb_final is a TEMPORARY value, created on demand from MDS VALUE actions (gets) on TREE
	# tb_final does NOT have a field (ideally, the MDS server will cache it to avoid recalc over N chan..)
	tb_final = np.zeros(len(data))
	ttime = 0
	for ix, idec in enumerate(tb):
		tb_final[ix] = ttime 
		ttime += decims[idec] * dt

	return tb_final

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

	if not True: #np.allclose(model, data, rtol=1, atol=1500):
	#if np.allclose(model, data, rtol=1, atol=1500):
		print("Please check shot {} visually.".format(shot))
		close = np.isclose(model, data, rtol=1, atol=1000)
		plt.plot(model)
		plt.plot(data)
		plt.plot(close * 1000)
		plt.grid(1)
		plt.show()
	shot += 1
