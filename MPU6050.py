import smbus
import math
import time
import matplotlib.pyplot as plt

power_mgmt_1 = 0x6b
power_mgmt_2 = 0x6c

def read_byte(reg):
	return bus.read_byte_data(address, reg)
	
def read_word(reg):
	h = bus.read_byte_data(address, reg)
	l = bus.read_byte_data(address, reg + 1)
	value = (h << 8) + l
	return value
	
def read_word_2c(reg):
	val = read_word(reg)
	if (val >= 0x8000):
		return -((65535 - val) + 1)
	else:
		return val
		
def dist(a, b):
	return math.sqrt((a * a) + (b * b))
		
def get_y_rotation(x, y, z):
	radians = math.atan2(x, dist(y, z))
	return -math.degrees(radians)
	
def get_x_rotation(x, y, z):
	radians = math.atan2(y, dist(x, z))
	return math.degrees(radians)
	
def round_multiple(p, *args):
	return [round(i, p) for i in args]
	
def calibrate():
	x, y, z = 0, 0, 0
	ttl = 1000
	for i in range(ttl): 
		x += read_word_2c(0x43) / 131
		y += read_word_2c(0x45) / 131
		z += read_word_2c(0x47) / 131
	gyro_x_cal, gyro_y_cal, gyro_z_cal = x / ttl, y / ttl, z / ttl
	
	#x, y, z = 0, 0, 0
	#ttl = 500
	#for i in range(ttl): 
	#	x += read_word_2c(0x3b) / 16384
	#	y += read_word_2c(0x3d) / 16384
	#	z += read_word_2c(0x3f) / 16384
	accel_x_cal, accel_y_cal, accel_z_cal = 0, 0, 0# x / ttl, y / ttl, z / ttl
	
	return gyro_x_cal, gyro_y_cal, gyro_z_cal, accel_x_cal, accel_y_cal, accel_z_cal
	
	
def read_gyro():
	global gx_cal, gy_cal, gz_cal

	gyro_x = read_word_2c(0x43) / 131 - gx_cal
	gyro_y = read_word_2c(0x45) / 131 - gy_cal
	gyro_z = read_word_2c(0x47) / 131 - gz_cal
	
	return gyro_x, gyro_y, gyro_z

bus = smbus.SMBus(1)
address = 0x68

bus.write_byte_data(address, power_mgmt_1, 0)

gx_cal, gy_cal, gz_cal, ax_cal, ay_cal, az_cal = calibrate()

if __name__ == '__main__':
	X, Y, Z = 0, 0, 0
	x, y, z = 0, 0, 0
	theta, phi = 0, 0

	t = time.time()

	x_axis = [0 for i in range(100)]
	y_axisx, y_axisy, y_axisz = [[0 for i in range(100)] for l in range(3)]

	plt.ion()

	fig = plt.figure()
	ax = fig.add_subplot(111)
	line1, = ax.plot(x_axis, y_axisx)
	line2, = ax.plot(x_axis, y_axisy)
	line3, = ax.plot(x_axis, y_axisz)
	ax.set_ylim(-10, 10)
	ax.set_xlim(0, 20)

	start = time.time()

	while True:
		dt = time.time() - t
		t = time.time()
		
		x_axis = x_axis[1: 100] + [round(t - start, 2)]
		
		print('Time: ', round(dt, 2))
		temp = 36.53 + read_word_2c(0x41) / 340.0
		print('Temp: ', round(temp, 1))
		
		gyro_x = read_word_2c(0x43) / 131 - gx_cal
		gyro_y = read_word_2c(0x45) / 131 - gy_cal
		gyro_z = read_word_2c(0x47) / 131 - gz_cal
		
		accel_x = read_word_2c(0x3b) / 16384.0 - ax_cal
		accel_y = read_word_2c(0x3d) / 16384.0 - ay_cal
		accel_z = read_word_2c(0x3f) / 16384.0 - az_cal
		
		y_axisx = y_axisx[1:100] + [round(accel_x, 2)]
		y_axisy = y_axisy[1:100] + [round(accel_y, 2)]
		y_axisz = y_axisz[1:100] + [round(accel_z, 2)]
		
		rot_x = get_x_rotation(accel_x, accel_y, accel_z)
		rot_y = get_y_rotation(accel_x, accel_y, accel_z)
		
		print('Gyro: ', round_multiple(1, gyro_x, gyro_y, gyro_z))
		print('Accel: ', round_multiple(1, accel_x, accel_y, accel_z))
		print('Rotation: ', round_multiple(1, rot_x, rot_y))
		
		X, Y, Z = X + gyro_x * dt, Y + gyro_y * dt, Z + gyro_z * dt
		x, y, z = x + accel_x * dt, y + accel_y * dt, z + accel_z * dt
		theta, phi = theta + rot_x * dt, phi + rot_y * dt
		
		print()
		print('Angular Displacement: ', round_multiple(1, X, Y, Z))
		print('Spacial Displacement: ', round_multiple(1, x, y, z))
		print('Angular Vector: ', round_multiple(1, theta, phi))
		print('-------------------------')
		
		line1.set_xdata(x_axis)
		line1.set_ydata(y_axisx)
		line2.set_xdata(x_axis)
		line2.set_ydata(y_axisy)
		line3.set_xdata(x_axis)
		line3.set_ydata(y_axisz)
		ax.set_xlim(min(x_axis), max(x_axis))
		
		fig.canvas.draw()
		fig.canvas.flush_events()
		
		time.sleep(0.1)
	
	
	